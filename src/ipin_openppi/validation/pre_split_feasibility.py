"""Independent validation for the aggregate pre-split leakage audit."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import numpy as np
import pyarrow
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import git_provenance, project_root_from, require_apptainer
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.pre_split_audit import AUDIT_VERSION
from ipin_openppi.pre_split_audit.support import (
    load_json,
    load_yaml,
    require_hash,
    resolve_inside,
    validate_config,
    verify_manifest_table,
)
from ipin_openppi.validation.staging import Checks, _write_report


TABLES = (
    "network_degree_summaries",
    "source_composition_summaries",
    "similarity_sensitivity_summaries",
    "leakage_graph_summaries",
    "allocation_feasibility_summaries",
    "claim_assessments",
)
PARTITIONS = ("train", "development", "test")


class IndependentDisjointSet:
    def __init__(self, nodes: Iterable[str]) -> None:
        self.parent = {node: node for node in sorted(set(nodes))}
        self.size = {node: 1 for node in self.parent}

    def find(self, node: str) -> str:
        trail = []
        while self.parent[node] != node:
            trail.append(node)
            node = self.parent[node]
        for child in trail:
            self.parent[child] = node
        return node

    def union(self, endpoint_a: str, endpoint_b: str) -> None:
        root_a = self.find(endpoint_a)
        root_b = self.find(endpoint_b)
        if root_a == root_b:
            return
        if self.size[root_a] < self.size[root_b] or (
            self.size[root_a] == self.size[root_b] and root_b < root_a
        ):
            root_a, root_b = root_b, root_a
        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]


def _components(
    nodes: Sequence[str], edges: set[tuple[str, str]]
) -> tuple[dict[str, str], dict[str, int]]:
    dsu = IndependentDisjointSet(nodes)
    for endpoint_a, endpoint_b in sorted(edges):
        dsu.union(endpoint_a, endpoint_b)
    groups: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        groups[dsu.find(node)].append(node)
    memberships: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for members in groups.values():
        representative = min(members)
        sizes[representative] = len(members)
        memberships.update({member: representative for member in members})
    return memberships, sizes


def _rank(values: Sequence[int], fraction: float) -> int:
    ordered = sorted(map(int, values))
    if not ordered:
        return 0
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def _distribution(values: Sequence[int]) -> str:
    observed = list(map(int, values))
    result = {
        "minimum": min(observed, default=0),
        "q05": _rank(observed, 0.05),
        "q50": _rank(observed, 0.50),
        "q95": _rank(observed, 0.95),
        "maximum": max(observed, default=0),
    }
    return json.dumps(result, sort_keys=True)


def _gini(values: Sequence[int]) -> float:
    ordered = sorted(map(int, values))
    total = sum(ordered)
    if not ordered or total == 0:
        return 0.0
    weighted = sum(index * value for index, value in enumerate(ordered, start=1))
    count = len(ordered)
    return (2.0 * weighted) / (count * total) - (count + 1.0) / count


def _top_share(values: Sequence[int], fraction: float) -> float:
    ordered = sorted(map(int, values), reverse=True)
    total = sum(ordered)
    if not ordered or total == 0:
        return 0.0
    return sum(ordered[: max(1, math.ceil(fraction * len(ordered)))]) / total


def _histogram(values: Sequence[int]) -> str:
    counts = Counter()
    for value in map(int, values):
        if value == 0:
            label = "0"
        elif value == 1:
            label = "1"
        elif value == 2:
            label = "2"
        elif value <= 4:
            label = "3-4"
        elif value <= 9:
            label = "5-9"
        elif value <= 19:
            label = "10-19"
        elif value <= 49:
            label = "20-49"
        elif value <= 99:
            label = "50-99"
        else:
            label = "100+"
        counts[label] += 1
    labels = ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")
    return json.dumps({label: int(counts[label]) for label in labels}, sort_keys=True)


def _degree_values(values: Sequence[int]) -> dict[str, Any]:
    observed = list(map(int, values))
    return {
        "population_entity_count": len(observed),
        "positive_exposed_entity_count": sum(value > 0 for value in observed),
        "degree_sum": sum(observed),
        "degree_q50": _rank(observed, 0.50),
        "degree_q90": _rank(observed, 0.90),
        "degree_q95": _rank(observed, 0.95),
        "degree_q99": _rank(observed, 0.99),
        "maximum_degree": max(observed, default=0),
        "top_1_percent_degree_share": _top_share(observed, 0.01),
        "top_5_percent_degree_share": _top_share(observed, 0.05),
        "top_10_percent_degree_share": _top_share(observed, 0.10),
        "degree_gini": _gini(observed),
        "degree_histogram_json": _histogram(observed),
    }


def _check_sidecar(checks: Checks, path: Path, check_id: str) -> str:
    sidecar = path.with_name(path.name + ".sha256")
    expected_line = sidecar.read_text(encoding="utf-8").strip().split()
    digest = sha256_file(path)
    checks.require(
        check_id,
        len(expected_line) == 2 and expected_line[0] == digest and expected_line[1] == path.name,
        observed={"digest": digest, "sidecar": expected_line},
        expected={"digest": digest, "filename": path.name},
    )
    return digest


def _verify_run_inventory(
    checks: Checks, project_root: Path, run_root: Path, manifest: Mapping[str, Any]
) -> None:
    recorded = manifest.get("files", [])
    expected_names = {
        "MMSEQS_COMMANDS.json",
        "full_length_sensitivity_alignments.tsv",
        "full_length_sensitivity_edges.parquet",
        "local_domain_sensitivity_alignments.tsv",
        "local_domain_sensitivity_edges.parquet",
    }
    observed_names: set[str] = set()
    errors = 0
    for record in recorded:
        path = Path(str(record["path"])).resolve(strict=True)
        try:
            path.relative_to(run_root)
        except ValueError:
            errors += 1
            continue
        observed_names.add(path.name)
        errors += int(path.is_symlink() or not path.is_file())
        errors += int(path.stat().st_size != int(record["bytes"]))
        errors += int(sha256_file(path) != str(record["sha256"]))
        errors += int(bool(path.stat().st_mode & 0o222))
    actual_names = {
        path.name
        for path in run_root.iterdir()
        if path.name not in {"RUN_MANIFEST.json", "RUN_MANIFEST.json.sha256"}
    }
    checks.require(
        "inventory.run_files_exact_hashed_read_only",
        errors == 0 and observed_names == expected_names and actual_names == expected_names,
        observed={"errors": errors, "recorded": sorted(observed_names), "actual": sorted(actual_names)},
        expected={"errors": 0, "files": sorted(expected_names)},
    )


def _verify_inputs_independently(
    *,
    project_root: Path,
    config: Mapping[str, Any],
) -> tuple[dict[str, list[Path]], dict[str, Path], dict[str, Any]]:
    inputs = config["inputs"]
    document_keys = (
        "parent_config", "parent_canonical_manifest", "parent_run_manifest",
        "parent_fasta", "parent_normalized_edges", "parent_audit_report",
        "parent_validation_report", "primary_reconciliation_manifest",
        "benchmark_estimand_policy", "accepted_blueprint_amendment",
        "parent_acceptance_decision", "authorization_decision", "active_gate",
    )
    paths: dict[str, Path] = {}
    documents: dict[str, Any] = {}
    for key in document_keys:
        path = resolve_inside(project_root, str(inputs[key]), project_root, strict=True)
        paths[key] = path
        documents[key] = require_hash(path, str(inputs[f"{key}_sha256"]))
    schema = resolve_inside(project_root, str(inputs["audit_schema"]), project_root / "schemas", strict=True)
    paths["audit_schema"] = schema
    documents["audit_schema"] = {
        "path": schema.as_posix(), "bytes": schema.stat().st_size, "sha256": sha256_file(schema)
    }
    parent_manifest = load_json(paths["parent_canonical_manifest"])
    parent_root = resolve_inside(
        project_root, str(inputs["parent_canonical_root"]), project_root / "data/canonical", strict=True
    )
    reconciliation_manifest = load_json(paths["primary_reconciliation_manifest"])
    reconciliation_root = resolve_inside(
        project_root, str(inputs["primary_reconciliation_root"]), project_root / "data/canonical", strict=True
    )
    files: dict[str, list[Path]] = {}
    tables: dict[str, Any] = {}
    for key in ("eligible_reference_sequences", "space_iii_gene_eligibility", "sequence_component_assignments"):
        name = str(config["parent_tables"][key])
        files[key], tables[key] = verify_manifest_table(
            project_root=project_root,
            manifest=parent_manifest,
            table_name=name,
            expected_root=parent_root / name,
            verify_hashes=True,
        )
    key = "huri_evidence_gene_pair_projections"
    name = str(config["parent_tables"][key])
    files[key], tables[key] = verify_manifest_table(
        project_root=project_root,
        manifest=reconciliation_manifest,
        table_name=name,
        expected_root=reconciliation_root / name,
        verify_hashes=True,
    )
    return files, paths, {"documents": documents, "tables": tables}


def _read_outputs(
    *,
    checks: Checks,
    project_root: Path,
    canonical_root: Path,
    manifest: Mapping[str, Any],
    contract: Any,
) -> dict[str, list[dict[str, Any]]]:
    outputs: dict[str, list[dict[str, Any]]] = {}
    errors = 0
    for table in TABLES:
        files, summary = verify_manifest_table(
            project_root=project_root,
            manifest=manifest,
            table_name=table,
            expected_root=canonical_root / table,
            verify_hashes=True,
        )
        manifest_summary = manifest["tables"][table]
        errors += int(summary["rows"] != int(manifest_summary["rows"]))
        schema_names = pq.read_schema(files[0]).names
        expected_names = [column["name"] for column in contract.document["tables"][table]["columns"]]
        errors += int(schema_names != expected_names)
        outputs[table] = pq.read_table(files).to_pylist()
    actual_tables = {path.name for path in canonical_root.iterdir() if path.is_dir()}
    checks.require(
        "inventory.canonical_tables_exact_schema_and_hashes",
        errors == 0 and actual_tables == set(TABLES),
        observed={"errors": errors, "tables": sorted(actual_tables)},
        expected={"errors": 0, "tables": sorted(TABLES)},
    )
    return outputs


def _load_parent_state(
    connection: duckdb.DuckDBPyConnection, config: Mapping[str, Any]
) -> tuple[list[str], dict[str, int], dict[int, dict[str, str]], dict[int, dict[str, int]]]:
    rows = connection.execute(
        "SELECT reference_sequence_sha256, sequence_length FROM eligible_reference_sequences ORDER BY 1"
    ).fetchall()
    nodes = [str(row[0]) for row in rows]
    lengths = {str(row[0]): int(row[1]) for row in rows}
    expected = config["frozen_parent_expectations"]
    if len(nodes) != int(expected["eligible_reference_sequences"]):
        raise RuntimeError("Parent endpoint inventory mismatch")
    memberships: dict[int, dict[str, str]] = defaultdict(dict)
    sizes: dict[int, dict[str, int]] = defaultdict(dict)
    for threshold, node, component, size in connection.execute(
        "SELECT identity_threshold_percent, reference_sequence_sha256, component_id, component_size "
        "FROM sequence_component_assignments"
    ).fetchall():
        threshold = int(threshold)
        memberships[threshold][str(node)] = str(component)
        sizes[threshold][str(component)] = int(size)
    for threshold in (40, 30, 20):
        if set(memberships[threshold]) != set(nodes):
            raise RuntimeError("Parent component membership mismatch")
        if dict(Counter(memberships[threshold].values())) != sizes[threshold]:
            raise RuntimeError("Parent component size mismatch")
    return nodes, lengths, dict(memberships), dict(sizes)


def _positive_pairs(
    connection: duckdb.DuckDBPyConnection, config: Mapping[str, Any]
) -> tuple[dict[str, set[tuple[str, str]]], dict[tuple[str, str], frozenset[str]]]:
    mappings = {
        str(gene): (str(state), None if selected is None or not bool(usable) else str(selected))
        for gene, state, selected, usable in connection.execute(
            "SELECT ensembl_gene_id, mapping_state, selected_sequence_sha256, eligibility_usable "
            "FROM space_iii_gene_eligibility"
        ).fetchall()
    }
    pairs = {"HI-II-14": set(), "HuRI": set()}
    for source, unique, gene_a, gene_b, authorized in connection.execute(
        "SELECT source_dataset, unique_gene_pair, gene_a, gene_b, label_authorized "
        "FROM huri_evidence_gene_pair_projections"
    ).fetchall():
        source = str(source)
        if source not in pairs or bool(authorized):
            raise RuntimeError("Unexpected positive source scope")
        if not bool(unique) or gene_a is None or gene_b is None:
            continue
        mapped_a = mappings.get(str(gene_a))
        mapped_b = mappings.get(str(gene_b))
        if not mapped_a or not mapped_b or mapped_a[1] is None or mapped_b[1] is None:
            continue
        if mapped_a[1] == mapped_b[1]:
            continue
        pairs[source].add(tuple(sorted((mapped_a[1], mapped_b[1]))))
    pairs["ALL"] = pairs["HI-II-14"] | pairs["HuRI"]
    expected = config["frozen_parent_expectations"]
    observed = (len(pairs["ALL"]), len(pairs["HI-II-14"]), len(pairs["HuRI"]))
    required = (
        int(expected["distinct_positive_pairs_all"]),
        int(expected["distinct_positive_pairs_hi_ii_14"]),
        int(expected["distinct_positive_pairs_huri"]),
    )
    if observed != required:
        raise RuntimeError(f"Positive pair counts differ: {observed} != {required}")
    sources = {
        pair: frozenset(source for source in ("HI-II-14", "HuRI") if pair in pairs[source])
        for pair in pairs["ALL"]
    }
    return pairs, sources


def _parse_search_independently(
    *,
    raw_path: Path,
    normalized_path: Path,
    lengths: Mapping[str, int],
    minimum_identity: float,
    minimum_coverage: float,
    minimum_span: int,
    maximum_evalue: float,
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    raw_count = invalid = below_identity = below_coverage = below_span = above_evalue = 0
    self_queries: set[str] = set()
    aggregates: dict[tuple[str, str], dict[str, Any]] = {}
    with raw_path.open("rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw_count += 1
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 12:
                raise RuntimeError(f"Malformed alignment row {line_number}")
            query, target = fields[0], fields[1]
            mismatch, alnlen, qstart, qend, qlen, tstart, tend, tlen = map(int, fields[2:10])
            evalue, bits = map(float, fields[10:12])
            qspan = abs(qend - qstart) + 1
            tspan = abs(tend - tstart) + 1
            identical = qspan + tspan - alnlen - mismatch
            structural = (
                query not in lengths or target not in lengths or alnlen <= 0
                or mismatch < 0 or mismatch > alnlen or qlen != lengths.get(query)
                or tlen != lengths.get(target) or min(qstart, qend, tstart, tend) < 1
                or max(qstart, qend) > qlen or max(tstart, tend) > tlen
                or identical < 0 or identical > alnlen
                or not math.isfinite(evalue) or not math.isfinite(bits)
            )
            invalid += int(structural)
            if structural:
                continue
            identity = identical / alnlen
            coverage = min(qspan / qlen, tspan / tlen)
            span = min(qspan, tspan)
            below_identity += int(identity + 1e-12 < minimum_identity)
            below_coverage += int(coverage + 1e-12 < minimum_coverage)
            below_span += int(span < minimum_span)
            above_evalue += int(evalue > maximum_evalue)
            if query == target:
                self_queries.add(query)
                continue
            if (
                identity + 1e-12 < minimum_identity
                or coverage + 1e-12 < minimum_coverage
                or span < minimum_span
                or evalue > maximum_evalue
            ):
                continue
            pair = tuple(sorted((query, target)))
            current = aggregates.setdefault(
                pair,
                {
                    "maximum_identity": identity,
                    "maximum_minimum_endpoint_coverage": coverage,
                    "maximum_minimum_aligned_span": span,
                    "minimum_evalue": evalue,
                    "maximum_bits": bits,
                    "supporting_alignment_records": 0,
                },
            )
            current["maximum_identity"] = max(current["maximum_identity"], identity)
            current["maximum_minimum_endpoint_coverage"] = max(
                current["maximum_minimum_endpoint_coverage"], coverage
            )
            current["maximum_minimum_aligned_span"] = max(
                current["maximum_minimum_aligned_span"], span
            )
            current["minimum_evalue"] = min(current["minimum_evalue"], evalue)
            current["maximum_bits"] = max(current["maximum_bits"], bits)
            current["supporting_alignment_records"] += 1
    if invalid:
        raise RuntimeError(f"Independent parser found {invalid} structurally invalid rows")

    normalized = {
        (str(row["sequence_a_sha256"]), str(row["sequence_b_sha256"])): row
        for row in pq.read_table(normalized_path).to_pylist()
    }
    if set(normalized) != set(aggregates):
        raise RuntimeError("Normalized sensitivity edge identities differ")
    for pair, expected in aggregates.items():
        row = normalized[pair]
        for key in (
            "maximum_identity", "maximum_minimum_endpoint_coverage", "minimum_evalue", "maximum_bits"
        ):
            if not math.isclose(float(row[key]), float(expected[key]), rel_tol=1e-12, abs_tol=1e-12):
                raise RuntimeError(f"Normalized value differs for {pair}: {key}")
        for key in ("maximum_minimum_aligned_span", "supporting_alignment_records"):
            if int(row[key]) != int(expected[key]):
                raise RuntimeError(f"Normalized integer differs for {pair}: {key}")
    metrics = {
        "raw_alignment_records": raw_count,
        "structurally_invalid_records": invalid,
        "below_exact_identity_records": below_identity,
        "below_minimum_endpoint_coverage_records": below_coverage,
        "below_minimum_aligned_span_records": below_span,
        "above_maximum_evalue_records": above_evalue,
        "self_match_query_sequences": len(self_queries),
        "normalized_nonself_edges": len(aggregates),
        "raw_alignment_sha256": sha256_file(raw_path),
        "normalized_edges_sha256": sha256_file(normalized_path),
        "minimum_identity": minimum_identity,
        "minimum_endpoint_coverage": minimum_coverage,
        "minimum_aligned_endpoint_span": minimum_span,
        "maximum_evalue": maximum_evalue,
        "identity_uses_integer_derived_identical_over_alnlen": True,
    }
    return aggregates, metrics


def _parent_edges(path: Path, config: Mapping[str, Any]) -> dict[int, set[tuple[str, str]]]:
    rows = pq.read_table(path).to_pylist()
    return {
        threshold: {
            (str(row["sequence_a_sha256"]), str(row["sequence_b_sha256"]))
            for row in rows
            if float(row["maximum_identity"]) + 1e-12 >= threshold / 100.0
        }
        for threshold in map(int, config["leakage_graphs"]["identity_thresholds_percent"])
    }


def _edge_sets(
    parsed: Mapping[tuple[str, str], Mapping[str, Any]], thresholds: Sequence[int]
) -> dict[int, set[tuple[str, str]]]:
    return {
        threshold: {
            pair for pair, values in parsed.items()
            if float(values["maximum_identity"]) + 1e-12 >= threshold / 100.0
        }
        for threshold in thresholds
    }


def _row_map(rows: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> dict[tuple[Any, ...], Mapping[str, Any]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def _compare_fields(
    observed: Mapping[str, Any], expected: Mapping[str, Any], fields: Sequence[str]
) -> bool:
    for field in fields:
        left = observed[field]
        right = expected[field]
        if isinstance(right, float):
            if not math.isclose(float(left), right, rel_tol=1e-12, abs_tol=1e-12):
                return False
        elif left != right:
            return False
    return True


def _independent_allocation(
    *,
    definition: str,
    threshold: int,
    nodes: Sequence[str],
    memberships: Mapping[str, str],
    component_sizes: Mapping[str, int],
    positive_pairs: set[tuple[str, str]],
    pair_sources: Mapping[tuple[str, str], frozenset[str]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    policy = config["allocation_feasibility"]
    trial_count = int(policy["trial_count"])
    seed = f"{policy['deterministic_seed']}:{definition}:{threshold}"
    targets = np.array([float(policy["target_fractions"][name]) for name in PARTITIONS])
    tolerance = float(policy["maximum_absolute_sequence_fraction_deviation"])
    pair_floor = int(policy["minimum_released_positive_pairs"])
    component_floor = int(policy["minimum_independent_components"])
    source_floor = int(policy["minimum_pairs_per_source_for_meaningful_diversity"])
    robust = float(policy["robust_feasibility_trial_fraction"])

    component_ids = sorted(component_sizes)
    component_to_index = {component: index for index, component in enumerate(component_ids)}
    sizes = np.array([int(component_sizes[component]) for component in component_ids], dtype=np.int64)
    base_components = sorted(
        component_ids,
        key=lambda component: hashlib.sha256(f"{seed}:component:{component}".encode()).digest(),
    )
    base_indices = np.array([component_to_index[component] for component in base_components], dtype=np.int64)
    node_to_index = {node: index for index, node in enumerate(nodes)}
    node_components = np.array([component_to_index[memberships[node]] for node in nodes], dtype=np.int64)
    ordered_pairs = sorted(positive_pairs)
    a = np.array([node_to_index[pair[0]] for pair in ordered_pairs], dtype=np.int64)
    b = np.array([node_to_index[pair[1]] for pair in ordered_pairs], dtype=np.int64)
    hi = np.array(["HI-II-14" in pair_sources[pair] for pair in ordered_pairs], dtype=bool)
    huri = np.array(["HuRI" in pair_sources[pair] for pair in ordered_pairs], dtype=bool)
    desired_counts = targets * len(nodes)
    metric_names = (
        "c1_pairs", "c2_pairs", "c3_pairs", "c1_components", "c2_components",
        "c3_components", "c3_hi_ii_14_pairs", "c3_huri_pairs",
    )
    collected = {name: [] for name in metric_names}
    valid_count = pass_c1 = pass_c2 = pass_c3 = pass_source = pass_joint = 0
    component_count = len(component_ids)
    for trial in range(trial_count):
        digest = hashlib.sha256(f"{seed}:trial:{trial}".encode()).digest()
        offset = int.from_bytes(digest[:8], "big") % component_count
        stride = max(1, int.from_bytes(digest[8:16], "big") % component_count)
        while math.gcd(stride, component_count) != 1:
            stride = (stride + 1) % component_count or 1
        allocation = np.empty(component_count, dtype=np.int8)
        counts = np.zeros(3, dtype=np.int64)
        for position in range(component_count):
            component = int(base_indices[(offset + position * stride) % component_count])
            chosen = int(np.argmax((desired_counts - counts) / np.maximum(desired_counts, 1.0)))
            allocation[component] = chosen
            counts[chosen] += sizes[component]
        valid = bool(np.all(np.abs(counts / len(nodes) - targets) <= tolerance + 1e-12))
        valid_count += int(valid)
        node_partition = allocation[node_components]
        pa = node_partition[a]
        pb = node_partition[b]
        train = (pa == 0) & (pb == 0)
        degrees = np.bincount(np.concatenate((a[train], b[train])), minlength=len(nodes))
        c1 = train & (degrees[a] >= 2) & (degrees[b] >= 2)
        c2 = ((pa == 0) & (pb == 2) & (degrees[a] >= 1)) | (
            (pb == 0) & (pa == 2) & (degrees[b] >= 1)
        )
        c3 = (pa == 2) & (pb == 2)
        values = {
            "c1_pairs": int(c1.sum()),
            "c2_pairs": int(c2.sum()),
            "c3_pairs": int(c3.sum()),
            "c1_components": int(len(np.unique(np.concatenate((node_components[a[c1]], node_components[b[c1]]))))) if c1.any() else 0,
            "c2_components": int(len(np.unique(np.concatenate((node_components[a[c2]], node_components[b[c2]]))))) if c2.any() else 0,
            "c3_components": int(len(np.unique(np.concatenate((node_components[a[c3]], node_components[b[c3]]))))) if c3.any() else 0,
            "c3_hi_ii_14_pairs": int((c3 & hi).sum()),
            "c3_huri_pairs": int((c3 & huri).sum()),
        }
        for name in metric_names:
            collected[name].append(values[name])
        ok1 = values["c1_pairs"] >= pair_floor and values["c1_components"] >= component_floor
        ok2 = values["c2_pairs"] >= pair_floor and values["c2_components"] >= component_floor
        ok3 = values["c3_pairs"] >= pair_floor and values["c3_components"] >= component_floor
        diverse = values["c3_hi_ii_14_pairs"] >= source_floor and values["c3_huri_pairs"] >= source_floor
        pass_c1 += int(valid and ok1)
        pass_c2 += int(valid and ok2)
        pass_c3 += int(valid and ok3)
        pass_source += int(valid and diverse)
        pass_joint += int(valid and ok1 and ok2 and ok3 and diverse)
    joint_fraction = pass_joint / trial_count
    status = "robustly_feasible" if joint_fraction + 1e-12 >= robust else (
        "conditionally_feasible" if pass_joint else "not_demonstrated"
    )
    return {
        "trial_count": trial_count,
        "target_fraction_valid_trial_count": valid_count,
        "target_fraction_valid_trial_fraction": valid_count / trial_count,
        "c1_pair_distribution_json": _distribution(collected["c1_pairs"]),
        "c2_pair_distribution_json": _distribution(collected["c2_pairs"]),
        "c3_pair_distribution_json": _distribution(collected["c3_pairs"]),
        "c1_component_distribution_json": _distribution(collected["c1_components"]),
        "c2_component_distribution_json": _distribution(collected["c2_components"]),
        "c3_component_distribution_json": _distribution(collected["c3_components"]),
        "c3_hi_ii_14_pair_distribution_json": _distribution(collected["c3_hi_ii_14_pairs"]),
        "c3_huri_pair_distribution_json": _distribution(collected["c3_huri_pairs"]),
        "c1_floor_pass_trial_fraction": pass_c1 / trial_count,
        "c2_floor_pass_trial_fraction": pass_c2 / trial_count,
        "c3_floor_pass_trial_fraction": pass_c3 / trial_count,
        "c3_source_diversity_pass_trial_fraction": pass_source / trial_count,
        "joint_floor_pass_trial_fraction": joint_fraction,
        "feasibility_status": status,
    }


def _validate_aggregate_counts(
    *,
    checks: Checks,
    outputs: Mapping[str, Sequence[Mapping[str, Any]]],
    nodes: Sequence[str],
    pairs: Mapping[str, set[tuple[str, str]]],
    pair_sources: Mapping[tuple[str, str], frozenset[str]],
    accepted_edges: Mapping[int, set[tuple[str, str]]],
    sensitivity_edges: Mapping[int, set[tuple[str, str]]],
    local_edges: Mapping[int, set[tuple[str, str]]],
    accepted_memberships: Mapping[int, Mapping[str, str]],
    accepted_sizes: Mapping[int, Mapping[str, int]],
    config: Mapping[str, Any],
) -> None:
    degree_rows = _row_map(outputs["network_degree_summaries"], ("source_dataset", "summary_unit", "leakage_definition", "identity_threshold_percent"))
    source_rows = _row_map(outputs["source_composition_summaries"], ("source_membership_stratum", "leakage_definition", "identity_threshold_percent"))
    similarity_rows = _row_map(outputs["similarity_sensitivity_summaries"], ("identity_threshold_percent",))
    leakage_rows = _row_map(outputs["leakage_graph_summaries"], ("leakage_definition", "identity_threshold_percent"))
    allocation_rows = _row_map(outputs["allocation_feasibility_summaries"], ("leakage_definition", "identity_threshold_percent"))
    errors = Counter()

    for source in ("ALL", "HI-II-14", "HuRI"):
        degrees = Counter(endpoint for pair in pairs[source] for endpoint in pair)
        expected = {**_degree_values([degrees[node] for node in nodes]), "positive_pair_count": len(pairs[source])}
        row = degree_rows[(source, "endpoint", "positive_network", 0)]
        errors["degree"] += int(not _compare_fields(row, expected, tuple(expected)))

    strata = {
        "HI-II-14_only": pairs["HI-II-14"] - pairs["HuRI"],
        "HuRI_only": pairs["HuRI"] - pairs["HI-II-14"],
        "both": pairs["HI-II-14"] & pairs["HuRI"],
    }
    total = len(pairs["ALL"])
    for name, values in strata.items():
        expected = {
            "positive_pair_count": len(values),
            "positive_pair_fraction": len(values) / total,
            "within_component_pair_count": 0,
            "cross_component_pair_count": len(values),
        }
        errors["source"] += int(
            not _compare_fields(source_rows[(name, "positive_network", 0)], expected, tuple(expected))
        )

    graphs: dict[tuple[str, int], tuple[set[tuple[str, str]], Mapping[str, str], Mapping[str, int]]] = {}
    for threshold in (40, 30, 20):
        accepted = accepted_edges[threshold]
        sensitivity = sensitivity_edges[threshold]
        union = accepted | sensitivity
        sensitive_memberships, sensitive_sizes = _components(nodes, union)
        local_union = union | local_edges[threshold]
        local_memberships, local_sizes = _components(nodes, local_union)
        graphs[("frozen_fl80", threshold)] = (accepted, accepted_memberships[threshold], accepted_sizes[threshold])
        graphs[("sensitive_fl80_union", threshold)] = (union, sensitive_memberships, sensitive_sizes)
        graphs[("local_domain_union", threshold)] = (local_union, local_memberships, local_sizes)
        expected_similarity = {
            "accepted_edge_count": len(accepted),
            "sensitivity_edge_count": len(sensitivity),
            "rediscovered_accepted_edge_count": len(accepted & sensitivity),
            "accepted_edges_not_rediscovered": len(accepted - sensitivity),
            "newly_recovered_qualifying_edges": len(sensitivity - accepted),
            "union_edge_count": len(union),
            "accepted_edge_rediscovery_fraction": len(accepted & sensitivity) / len(accepted),
            "exhaustive_completeness_proven": False,
            "accepted_graph_modified": False,
        }
        errors["similarity"] += int(
            not _compare_fields(similarity_rows[(threshold,)], expected_similarity, tuple(expected_similarity))
        )

    for (definition, threshold), (edges, memberships, sizes_by_component) in graphs.items():
        component_sizes = list(sizes_by_component.values())
        added = edges - accepted_edges[threshold]
        within = sum(memberships[a] == memberships[b] for a, b in pairs["ALL"])
        exposed = {memberships[endpoint] for pair in pairs["ALL"] for endpoint in pair}
        expected_leakage = {
            "sequence_count": len(nodes),
            "edge_count": len(edges),
            "added_edge_count_vs_accepted": len(added),
            "added_edges_crossing_accepted_components": sum(
                accepted_memberships[threshold][a] != accepted_memberships[threshold][b] for a, b in added
            ),
            "component_count": len(component_sizes),
            "singleton_component_count": sum(size == 1 for size in component_sizes),
            "largest_component_size": max(component_sizes),
            "component_size_q50": _rank(component_sizes, 0.50),
            "component_size_q90": _rank(component_sizes, 0.90),
            "component_size_q95": _rank(component_sizes, 0.95),
            "component_size_q99": _rank(component_sizes, 0.99),
            "positive_pair_count": len(pairs["ALL"]),
            "within_component_positive_pairs": within,
            "cross_component_positive_pairs": len(pairs["ALL"]) - within,
            "positive_exposed_components": len(exposed),
            "component_membership_rows_emitted": False,
            "split_assignment_constructed": False,
        }
        errors["leakage"] += int(
            not _compare_fields(leakage_rows[(definition, threshold)], expected_leakage, tuple(expected_leakage))
        )
        for source in ("ALL", "HI-II-14", "HuRI"):
            loads = Counter()
            for endpoint_a, endpoint_b in pairs[source]:
                component_a = memberships[endpoint_a]
                component_b = memberships[endpoint_b]
                loads[component_a] += 1
                if component_b != component_a:
                    loads[component_b] += 1
            expected_degree = {
                **_degree_values([loads[component] for component in sorted(sizes_by_component)]),
                "positive_pair_count": len(pairs[source]),
            }
            errors["degree"] += int(
                not _compare_fields(
                    degree_rows[(source, "component", definition, threshold)],
                    expected_degree,
                    tuple(expected_degree),
                )
            )
        for stratum, values in strata.items():
            stratum_within = sum(memberships[a] == memberships[b] for a, b in values)
            expected_source = {
                "positive_pair_count": len(values),
                "positive_pair_fraction": len(values) / total,
                "within_component_pair_count": stratum_within,
                "cross_component_pair_count": len(values) - stratum_within,
            }
            errors["source"] += int(
                not _compare_fields(
                    source_rows[(stratum, definition, threshold)], expected_source, tuple(expected_source)
                )
            )
        expected_allocation = _independent_allocation(
            definition=definition,
            threshold=threshold,
            nodes=nodes,
            memberships=memberships,
            component_sizes=sizes_by_component,
            positive_pairs=pairs["ALL"],
            pair_sources=pair_sources,
            config=config,
        )
        errors["allocation"] += int(
            not _compare_fields(
                allocation_rows[(definition, threshold)], expected_allocation, tuple(expected_allocation)
            )
        )

    expected_counts = {
        "degree": 30,
        "source": 30,
        "similarity": 3,
        "leakage": 9,
        "allocation": 9,
    }
    checks.require(
        "metrics.all_consequential_aggregate_counts_independently_recomputed",
        not any(errors.values())
        and len(degree_rows) == expected_counts["degree"]
        and len(source_rows) == expected_counts["source"]
        and len(similarity_rows) == expected_counts["similarity"]
        and len(leakage_rows) == expected_counts["leakage"]
        and len(allocation_rows) == expected_counts["allocation"],
        observed={"errors": dict(errors), "row_counts": {
            "degree": len(degree_rows), "source": len(source_rows),
            "similarity": len(similarity_rows), "leakage": len(leakage_rows),
            "allocation": len(allocation_rows),
        }},
        expected={"errors": {}, "row_counts": expected_counts},
    )


def _scope_guards(
    checks: Checks,
    outputs: Mapping[str, Sequence[Mapping[str, Any]]],
    manifest: Mapping[str, Any],
    report: Mapping[str, Any],
) -> None:
    forbidden_columns = {
        "reference_sequence_sha256", "component_id", "pair_id", "partition", "split_id",
        "interaction_label", "negative_label", "unlabeled_indicator",
    }
    observed_columns = {key for rows in outputs.values() for row in rows for key in row}
    guards_false = all(
        row.get(field) is False
        for rows in outputs.values()
        for row in rows
        for field in (
            "entity_rows_emitted", "pair_rows_emitted", "evidence_indicator_constructed",
            "component_membership_rows_emitted", "split_assignment_constructed",
            "selected_trial_emitted", "component_assignment_rows_emitted",
            "pair_assignment_rows_emitted", "c1_c2_c3_labels_constructed",
            "split_constructed", "model_performance_claimed", "experimental_validation_claimed",
        )
        if field in row
    )
    manifest_false = all(
        manifest.get(field) is False
        for field in (
            "parent_audit_modified", "candidate_pair_materialization_performed",
            "candidate_sampling_performed", "positive_pair_rows_emitted",
            "endpoint_or_component_metric_rows_emitted", "evidence_indicator_construction_performed",
            "interaction_label_construction_performed", "negative_label_construction_performed",
            "pseudo_negative_sampling_performed", "selected_allocation_emitted",
            "c1_c2_c3_assignment_performed", "split_construction_performed",
            "structural_mapping_performed", "model_work_performed",
            "prevalence_estimation_performed", "calibration_performed", "external_panel_inputs_used",
        )
    )
    claims = _row_map(outputs["claim_assessments"], ("claim_name",))
    claim_guard = (
        claims[("unseen_biological_family",)]["supported_by_audit"] is False
        and claims[("unseen_biological_family",)]["claim_status"] == "prohibited"
        and claims[("exhaustive_absence_of_homology",)]["supported_by_audit"] is False
        and claims[("exhaustive_absence_of_homology",)]["claim_status"] == "prohibited"
        and report["scientific_interpretation"]["unseen_family_claim_supported"] is False
    )
    checks.require(
        "scope.no_pair_label_split_model_external_or_family_claim_output",
        not (observed_columns & forbidden_columns) and guards_false and manifest_false and claim_guard,
        observed={
            "forbidden_columns": sorted(observed_columns & forbidden_columns),
            "row_guards_false": guards_false,
            "manifest_guards_false": manifest_false,
            "claim_guard": claim_guard,
        },
        expected={"forbidden_columns": [], "all_guards_false": True, "claim_guard": True},
    )


def validate_audit(
    *,
    project_root: Path,
    config_path: Path,
    run_root: Path | None = None,
    canonical_root: Path | None = None,
    audit_report_path: Path | None = None,
) -> dict[str, Any]:
    require_apptainer()
    config_path = resolve_inside(project_root, config_path, project_root / "configs", strict=True)
    config = load_yaml(config_path)
    validate_config(config)
    run_root = resolve_inside(
        project_root, run_root or str(config["outputs"]["run_root"]), project_root / "artifacts/runs", strict=True
    )
    canonical_root = resolve_inside(
        project_root, canonical_root or str(config["outputs"]["canonical_root"]), project_root / "data/canonical", strict=True
    )
    audit_report_path = resolve_inside(
        project_root, audit_report_path or str(config["outputs"]["audit_report"]), project_root / "artifacts/validation", strict=True
    )
    checks = Checks()
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    container_sha = sha256_file(active_container)
    checks.require(
        "runtime.pinned_container_and_architecture",
        container_sha == str(config["runtime"]["container_sha256"])
        and platform.machine() == str(config["runtime"]["architecture"]),
        observed={"sha256": container_sha, "architecture": platform.machine()},
        expected={"sha256": str(config["runtime"]["container_sha256"]), "architecture": str(config["runtime"]["architecture"])},
    )
    run_manifest_path = run_root / "RUN_MANIFEST.json"
    canonical_manifest_path = canonical_root / "AUDIT_MANIFEST.json"
    run_sha = _check_sidecar(checks, run_manifest_path, "inventory.run_manifest_sidecar")
    canonical_sha = _check_sidecar(checks, canonical_manifest_path, "inventory.canonical_manifest_sidecar")
    audit_sha = _check_sidecar(checks, audit_report_path, "inventory.audit_report_sidecar")
    run_manifest = load_json(run_manifest_path)
    canonical_manifest = load_json(canonical_manifest_path)
    audit_report = load_json(audit_report_path)
    _verify_run_inventory(checks, project_root, run_root, run_manifest)

    input_files, input_paths, verified_inputs = _verify_inputs_independently(
        project_root=project_root, config=config
    )
    contract = load_contract(input_paths["audit_schema"])
    outputs = _read_outputs(
        checks=checks,
        project_root=project_root,
        canonical_root=canonical_root,
        manifest=canonical_manifest,
        contract=contract,
    )
    production_clean = all(
        document.get("git", {}).get("tracked_worktree_clean") is True
        and document.get("git", {}).get("status") == ""
        for document in (run_manifest, canonical_manifest)
    )
    production_same_commit = (
        bool(run_manifest.get("git", {}).get("commit"))
        and run_manifest.get("git", {}).get("commit") == canonical_manifest.get("git", {}).get("commit")
    )
    checks.require(
        "provenance.production_clean_single_commit",
        production_clean and production_same_commit,
        observed={"clean": production_clean, "same_commit": production_same_commit},
        expected={"clean": True, "same_commit": True},
    )
    provenance_ok = (
        audit_report["outputs"]["run_manifest_sha256"] == run_sha
        and audit_report["outputs"]["canonical_manifest_sha256"] == canonical_sha
        and canonical_manifest["inputs"]["run_manifest_sha256"] == run_sha
        and canonical_manifest["inputs"]["documents"] == verified_inputs["documents"]
        and canonical_manifest["inputs"]["tables"] == verified_inputs["tables"]
        and run_manifest["config"]["sha256"] == sha256_file(config_path)
        and canonical_manifest["inputs"]["config_sha256"] == sha256_file(config_path)
        and audit_report["inputs"]["config_sha256"] == sha256_file(config_path)
    )
    checks.require(
        "provenance.parent_inputs_config_and_manifests_match",
        provenance_ok,
        observed={"all_match": provenance_ok},
        expected={"all_match": True},
    )

    connection = duckdb.connect(":memory:")
    connection.execute(f"SET memory_limit='{str(config['runtime']['duckdb_memory_limit']).replace(chr(39), chr(39)*2)}'")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    try:
        for name, paths in input_files.items():
            connection.read_parquet([path.as_posix() for path in paths]).create_view(name)
        nodes, lengths, accepted_memberships, accepted_sizes = _load_parent_state(connection, config)
        pairs, pair_sources = _positive_pairs(connection, config)
    finally:
        connection.close()
    checks.require(
        "parent.frozen_endpoint_component_and_positive_counts",
        len(nodes) == 17000 and len(pairs["ALL"]) == 58049
        and {threshold: len(accepted_sizes[threshold]) for threshold in (40, 30, 20)}
        == {40: 12467, 30: 11311, 20: 10497},
        observed={
            "endpoints": len(nodes), "positive_pairs": len(pairs["ALL"]),
            "components": {threshold: len(accepted_sizes[threshold]) for threshold in (40, 30, 20)},
        },
        expected={"endpoints": 17000, "positive_pairs": 58049, "components": {40: 12467, 30: 11311, 20: 10497}},
    )

    full_parsed, full_metrics = _parse_search_independently(
        raw_path=run_root / "full_length_sensitivity_alignments.tsv",
        normalized_path=run_root / "full_length_sensitivity_edges.parquet",
        lengths=lengths,
        minimum_identity=0.20,
        minimum_coverage=0.80,
        minimum_span=0,
        maximum_evalue=1e100,
    )
    local_policy = config["leakage_graphs"]["local_domain_union_definition"]
    local_parsed, local_metrics = _parse_search_independently(
        raw_path=run_root / "local_domain_sensitivity_alignments.tsv",
        normalized_path=run_root / "local_domain_sensitivity_edges.parquet",
        lengths=lengths,
        minimum_identity=0.20,
        minimum_coverage=float(local_policy["minimum_endpoint_coverage"]),
        minimum_span=int(local_policy["minimum_aligned_endpoint_span"]),
        maximum_evalue=float(local_policy["maximum_evalue"]),
    )
    search_metrics = {"full_length_sensitivity": full_metrics, "local_domain_sensitivity": local_metrics}
    checks.require(
        "similarity.raw_alignment_exact_independent_reparse",
        run_manifest["search_metrics"] == search_metrics
        and audit_report["search_metrics"] == search_metrics,
        observed={
            "run_matches": run_manifest["search_metrics"] == search_metrics,
            "report_matches": audit_report["search_metrics"] == search_metrics,
        },
        expected={"run_matches": True, "report_matches": True},
    )
    thresholds = [40, 30, 20]
    accepted_edges = _parent_edges(input_paths["parent_normalized_edges"], config)
    sensitivity_edges = _edge_sets(full_parsed, thresholds)
    local_edges = _edge_sets(local_parsed, thresholds)
    _validate_aggregate_counts(
        checks=checks,
        outputs=outputs,
        nodes=nodes,
        pairs=pairs,
        pair_sources=pair_sources,
        accepted_edges=accepted_edges,
        sensitivity_edges=sensitivity_edges,
        local_edges=local_edges,
        accepted_memberships=accepted_memberships,
        accepted_sizes=accepted_sizes,
        config=config,
    )
    actual_metrics = {table: list(outputs[table]) for table in TABLES}
    checks.require(
        "metrics.canonical_manifest_and_audit_report_match_tables",
        canonical_manifest["metrics"] == actual_metrics and audit_report["metrics"] == actual_metrics,
        observed={
            "manifest_matches": canonical_manifest["metrics"] == actual_metrics,
            "report_matches": audit_report["metrics"] == actual_metrics,
        },
        expected={"manifest_matches": True, "report_matches": True},
    )
    _scope_guards(checks, outputs, canonical_manifest, audit_report)

    current_git = git_provenance(project_root)
    return {
        "schema_version": 1,
        "gate_id": "pre_split_feasibility_and_leakage_stress_test_v1_validation",
        "audit_id": config["audit_id"],
        "audit_version": AUDIT_VERSION,
        "status": "pass" if checks.passed else "fail",
        "scope": "production_full_independent_validation",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {
            "container_sif_sha256": container_sha,
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "duckdb": duckdb.__version__,
            "pyarrow": pyarrow.__version__,
            "numpy": np.__version__,
        },
        "validator_git": current_git,
        "production_git": run_manifest["git"],
        "run_manifest": run_manifest_path.as_posix(),
        "run_manifest_sha256": run_sha,
        "canonical_manifest": canonical_manifest_path.as_posix(),
        "canonical_manifest_sha256": canonical_sha,
        "audit_report": audit_report_path.as_posix(),
        "audit_report_sha256": audit_sha,
        "config": config_path.as_posix(),
        "config_sha256": sha256_file(config_path),
        "search_metrics": search_metrics,
        "validated_table_row_counts": {table: len(outputs[table]) for table in TABLES},
        "check_counts": checks.counts(),
        "checks": checks.records,
        "interpretation": (
            "Pass independently reparses both raw MMseqs2 searches, reconstructs every "
            "40/30/20 leakage graph and released-positive aggregate, repeats all ephemeral "
            "allocation trials, and confirms that no endpoint/pair/component assignment, "
            "C1/C2/C3 label, split, external panel, structure, or model output exists."
        ),
        "authorizations": {
            "audit_technical_validation_passed": checks.passed,
            "candidate_pair_materialization": False,
            "evidence_indicator_construction": False,
            "negative_label_construction": False,
            "pseudo_negative_sampling": False,
            "c1_c2_c3_assignment": False,
            "split_construction": False,
            "structural_mapping": False,
            "model_work": False,
            "return_to_governance_required": True,
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path,
        default=Path("configs/pre_split_feasibility_and_leakage_stress_test_v1.yaml"),
    )
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())

    def absolute(path: Path | None) -> Path | None:
        if path is None or path.is_absolute():
            return path
        return project_root / path

    result = validate_audit(
        project_root=project_root,
        config_path=absolute(args.config) or args.config,
        run_root=absolute(args.run_root),
        canonical_root=absolute(args.canonical_root),
        audit_report_path=absolute(args.audit_report),
    )
    report_path = absolute(args.report) or project_root / str(
        load_yaml(absolute(args.config) or args.config)["outputs"]["validation_report"]
    )
    _write_report(report_path, result, project_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
