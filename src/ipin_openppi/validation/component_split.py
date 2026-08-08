"""Independent validation for the frozen benchmark component split."""

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

from ipin_openppi.component_split import SPLIT_VERSION
from ipin_openppi.component_split.support import (
    load_json,
    load_yaml,
    require_hash,
    resolve_inside,
    validate_config,
    verify_manifest_table,
)
from ipin_openppi.ingestion.common import git_provenance, project_root_from, require_apptainer
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.validation.staging import Checks, _write_report


TABLES = (
    "component_partition_assignments",
    "endpoint_partition_assignments",
    "partition_summaries",
    "partition_degree_summaries",
    "opportunity_summaries",
    "leakage_validation_summaries",
    "selection_summaries",
    "claim_assessments",
)
PARTITIONS = ("train", "development", "test")
POOL_KEYS = (
    "C1:training_pool",
    "C2:development",
    "C2:test",
    "C3:development",
    "C3:test",
)


class IndependentDisjointSet:
    def __init__(self, nodes: Iterable[str]) -> None:
        self.parent = {node: node for node in sorted(set(nodes))}
        self.rank = {node: 0 for node in self.parent}

    def find(self, node: str) -> str:
        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while node != root:
            parent = self.parent[node]
            self.parent[node] = root
            node = parent
        return root

    def union(self, a: str, b: str) -> None:
        a = self.find(a)
        b = self.find(b)
        if a == b:
            return
        if self.rank[a] < self.rank[b] or (self.rank[a] == self.rank[b] and b < a):
            a, b = b, a
        self.parent[b] = a
        if self.rank[a] == self.rank[b]:
            self.rank[a] += 1


def _components(
    nodes: Sequence[str], edges: set[tuple[str, str]]
) -> tuple[dict[str, str], dict[str, int]]:
    dsu = IndependentDisjointSet(nodes)
    for a, b in sorted(edges):
        if a != b:
            dsu.union(a, b)
    groups: dict[str, list[str]] = defaultdict(list)
    for node in sorted(nodes):
        groups[dsu.find(node)].append(node)
    memberships: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for members in groups.values():
        representative = min(members)
        sizes[representative] = len(members)
        memberships.update({member: representative for member in members})
    return memberships, sizes


def _component_id(
    split_id: str, definition: str, representative: str, size: int
) -> str:
    payload = f"{split_id}:{definition}:30:{representative}:{size}"
    return "component:" + hashlib.sha256(payload.encode()).hexdigest()[:32]


def _quantize(numerator: int, denominator: int, scale: int) -> int:
    if numerator < 0 or denominator <= 0:
        raise ValueError("Invalid nonnegative ratio")
    return (2 * numerator * scale + denominator) // (2 * denominator)


def _nearest(values: Sequence[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(map(int, values))
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def _histogram(values: Sequence[int]) -> str:
    counts = Counter()
    for value in map(int, values):
        label = (
            "0" if value == 0 else "1" if value == 1 else "2" if value == 2
            else "3-4" if value <= 4 else "5-9" if value <= 9
            else "10-19" if value <= 19 else "20-49" if value <= 49
            else "50-99" if value <= 99 else "100+"
        )
        counts[label] += 1
    labels = ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")
    return json.dumps({label: counts[label] for label in labels}, sort_keys=True)


def _check_sidecar(checks: Checks, path: Path, check_id: str) -> str:
    sidecar = path.with_name(path.name + ".sha256")
    tokens = sidecar.read_text(encoding="utf-8").split()
    digest = sha256_file(path)
    checks.require(
        check_id,
        tokens == [digest, path.name],
        observed=tokens,
        expected=[digest, path.name],
    )
    return digest


def _verify_run_inventory(
    checks: Checks, run_root: Path, manifest: Mapping[str, Any]
) -> None:
    expected = {"SELECTION_EXECUTION.json"}
    observed: set[str] = set()
    errors = 0
    for record in manifest.get("files", []):
        path = Path(str(record["path"])).resolve(strict=True)
        try:
            path.relative_to(run_root)
        except ValueError:
            errors += 1
            continue
        observed.add(path.name)
        errors += int(path.is_symlink() or not path.is_file())
        errors += int(path.stat().st_size != int(record["bytes"]))
        errors += int(sha256_file(path) != str(record["sha256"]))
        errors += int(bool(path.stat().st_mode & 0o222))
    actual = {
        path.name
        for path in run_root.iterdir()
        if path.name not in {"RUN_MANIFEST.json", "RUN_MANIFEST.json.sha256"}
    }
    checks.require(
        "inventory.run_files_exact_hashed_read_only",
        errors == 0 and observed == expected and actual == expected,
        observed={"errors": errors, "recorded": sorted(observed), "actual": sorted(actual)},
        expected={"errors": 0, "files": sorted(expected)},
    )


def _verify_inputs(
    project_root: Path, config: Mapping[str, Any]
) -> tuple[dict[str, list[Path]], dict[str, Path], dict[str, Any]]:
    inputs = config["inputs"]
    keys = (
        "parent_config",
        "parent_canonical_manifest",
        "parent_run_manifest",
        "parent_fasta",
        "parent_normalized_edges",
        "primary_reconciliation_manifest",
        "pre_split_config",
        "pre_split_run_manifest",
        "pre_split_canonical_manifest",
        "pre_split_audit_report",
        "pre_split_validation_report",
        "full_length_sensitivity_edges",
        "local_domain_sensitivity_edges",
        "benchmark_estimand_policy",
        "accepted_blueprint_amendment",
        "parent_sequence_acceptance_decision",
        "parent_pre_split_acceptance_decision",
        "authorization_decision",
        "active_gate",
        "active_status",
        "split_schema",
    )
    paths: dict[str, Path] = {}
    documents: dict[str, Any] = {}
    for key in keys:
        paths[key] = resolve_inside(project_root, str(inputs[key]), project_root, strict=True)
        documents[key] = require_hash(paths[key], str(inputs[f"{key}_sha256"]))
    parent_manifest = load_json(paths["parent_canonical_manifest"])
    reconciliation_manifest = load_json(paths["primary_reconciliation_manifest"])
    parent_root = resolve_inside(
        project_root, str(inputs["parent_canonical_root"]), project_root / "data/canonical", strict=True
    )
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
        expected_names = [column["name"] for column in contract.table_spec(table)["columns"]]
        errors += int(pq.read_schema(files[0]).names != expected_names)
        rows = pq.read_table(files).to_pylist()
        contract.normalize_and_validate_rows(table, rows)
        key = tuple(contract.table_spec(table).get("primary_key", []))
        if key:
            errors += int(len({tuple(row[name] for name in key) for row in rows}) != len(rows))
        errors += int(len(rows) != int(summary["rows"]))
        outputs[table] = rows
    actual = {path.name for path in canonical_root.iterdir() if path.is_dir()}
    checks.require(
        "inventory.canonical_tables_exact_contract_hashes_and_keys",
        errors == 0 and actual == set(TABLES),
        observed={"errors": errors, "tables": sorted(actual)},
        expected={"errors": 0, "tables": sorted(TABLES)},
    )
    return outputs


def _load_state(
    connection: duckdb.DuckDBPyConnection, config: Mapping[str, Any]
) -> tuple[list[str], dict[str, int], dict[str, set[tuple[str, str]]], dict[tuple[str, str], frozenset[str]]]:
    endpoint_rows = connection.execute(
        "SELECT reference_sequence_sha256, sequence_length FROM eligible_reference_sequences ORDER BY 1"
    ).fetchall()
    nodes = [str(row[0]) for row in endpoint_rows]
    lengths = {str(row[0]): int(row[1]) for row in endpoint_rows}
    if len(nodes) != 17_000 or len(set(nodes)) != 17_000:
        raise RuntimeError("Independent endpoint reconstruction differs")
    component_counts = {
        int(threshold): int(count)
        for threshold, count in connection.execute(
            "SELECT identity_threshold_percent, count(DISTINCT component_id) "
            "FROM sequence_component_assignments GROUP BY 1"
        ).fetchall()
    }
    if component_counts != {20: 10497, 30: 11311, 40: 12467}:
        raise RuntimeError("Independent accepted component counts differ")
    mapping = {
        str(gene): str(sequence) if bool(usable) and sequence is not None else None
        for gene, sequence, usable in connection.execute(
            "SELECT ensembl_gene_id, selected_sequence_sha256, eligibility_usable "
            "FROM space_iii_gene_eligibility"
        ).fetchall()
    }
    if sum(value is not None for value in mapping.values()) != 17_172:
        raise RuntimeError("Independent eligible gene count differs")
    pairs: dict[str, set[tuple[str, str]]] = {"HI-II-14": set(), "HuRI": set()}
    for source, unique, gene_a, gene_b, label_authorized in connection.execute(
        "SELECT source_dataset, unique_gene_pair, gene_a, gene_b, label_authorized "
        "FROM huri_evidence_gene_pair_projections"
    ).fetchall():
        source = str(source)
        if source not in pairs or bool(label_authorized):
            raise RuntimeError("Independent positive source scope differs")
        if not bool(unique) or gene_a is None or gene_b is None:
            continue
        a = mapping.get(str(gene_a))
        b = mapping.get(str(gene_b))
        if a is not None and b is not None and a != b:
            pairs[source].add(tuple(sorted((a, b))))
    pairs["ALL"] = pairs["HI-II-14"] | pairs["HuRI"]
    if {source: len(values) for source, values in pairs.items()} != {
        "HI-II-14": 12353,
        "HuRI": 50545,
        "ALL": 58049,
    }:
        raise RuntimeError("Independent released-positive counts differ")
    pair_sources = {
        pair: frozenset(source for source in ("HI-II-14", "HuRI") if pair in pairs[source])
        for pair in pairs["ALL"]
    }
    return nodes, lengths, pairs, pair_sources


def _edges(path: Path) -> set[tuple[str, str]]:
    rows = pq.read_table(
        path, columns=["sequence_a_sha256", "sequence_b_sha256", "maximum_identity"]
    ).to_pylist()
    return {
        tuple(sorted((str(row["sequence_a_sha256"]), str(row["sequence_b_sha256"]))))
        for row in rows
        if float(row["maximum_identity"]) + 1e-12 >= 0.30
        and str(row["sequence_a_sha256"]) != str(row["sequence_b_sha256"])
    }


def _prepare(
    *,
    nodes: Sequence[str],
    memberships: Mapping[str, str],
    sizes: Mapping[str, int],
    positive_pairs: set[tuple[str, str]],
    pair_sources: Mapping[tuple[str, str], frozenset[str]],
) -> dict[str, Any]:
    ordered_nodes = tuple(sorted(nodes))
    representatives = tuple(sorted(sizes))
    node_index = {node: index for index, node in enumerate(ordered_nodes)}
    component_index = {component: index for index, component in enumerate(representatives)}
    node_components = np.array(
        [component_index[memberships[node]] for node in ordered_nodes], dtype=np.int64
    )
    pairs = sorted(positive_pairs)
    endpoint_a = np.array([node_index[pair[0]] for pair in pairs], dtype=np.int64)
    endpoint_b = np.array([node_index[pair[1]] for pair in pairs], dtype=np.int64)
    degrees = np.bincount(
        np.concatenate((endpoint_a, endpoint_b)), minlength=len(ordered_nodes)
    ).astype(np.int64)
    ranked = np.array(
        sorted(range(len(ordered_nodes)), key=lambda index: (-int(degrees[index]), ordered_nodes[index])),
        dtype=np.int64,
    )
    return {
        "nodes": ordered_nodes,
        "representatives": representatives,
        "sizes": dict(sizes),
        "node_components": node_components,
        "endpoint_a": endpoint_a,
        "endpoint_b": endpoint_b,
        "component_a": node_components[endpoint_a],
        "component_b": node_components[endpoint_b],
        "hi": np.array(["HI-II-14" in pair_sources[pair] for pair in pairs], dtype=bool),
        "huri": np.array(["HuRI" in pair_sources[pair] for pair in pairs], dtype=bool),
        "degrees": degrees,
        "hubs": {
            fraction: ranked[: max(1, math.ceil(fraction * len(ordered_nodes)))]
            for fraction in (0.01, 0.05, 0.10)
        },
    }


def _allocate(
    prepared: Mapping[str, Any],
    definition: str,
    candidate_index: int,
    config: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    salt = str(config["allocation"]["public_hash_salt"])
    seed = str(config["allocation"]["deterministic_seed"])
    representatives = prepared["representatives"]
    index = {component: position for position, component in enumerate(representatives)}
    base = sorted(
        representatives,
        key=lambda component: (
            hashlib.sha256(f"{salt}:{definition}:component:{component}".encode()).digest(),
            component,
        ),
    )
    digest = hashlib.sha256(
        f"{salt}:{seed}:{definition}:candidate:{candidate_index}".encode()
    ).digest()
    count = len(base)
    offset = int.from_bytes(digest[:8], "big") % count
    stride = int.from_bytes(digest[8:16], "big") % count or 1
    while math.gcd(stride, count) != 1:
        stride = (stride + 1) % count or 1
    assignments = np.empty(count, dtype=np.int8)
    endpoint_counts = np.zeros(3, dtype=np.int64)
    weights = (70, 15, 15)
    for position in range(count):
        component = base[(offset + position * stride) % count]
        chosen = 0
        for candidate_partition in (1, 2):
            if (
                int(endpoint_counts[candidate_partition]) * weights[chosen]
                < int(endpoint_counts[chosen]) * weights[candidate_partition]
            ):
                chosen = candidate_partition
        assignments[index[component]] = chosen
        endpoint_counts[chosen] += int(prepared["sizes"][component])
    return assignments, endpoint_counts


def _opportunity_masks(
    prepared: Mapping[str, Any], assignments: np.ndarray
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    node_partitions = assignments[prepared["node_components"]]
    part_a = node_partitions[prepared["endpoint_a"]]
    part_b = node_partitions[prepared["endpoint_b"]]
    train = (part_a == 0) & (part_b == 0)
    training_degree = np.bincount(
        np.concatenate((prepared["endpoint_a"][train], prepared["endpoint_b"][train])),
        minlength=len(prepared["nodes"]),
    )
    masks = {
        "C1:training_pool": train
        & (training_degree[prepared["endpoint_a"]] >= 2)
        & (training_degree[prepared["endpoint_b"]] >= 2)
    }
    for name, code in (("development", 1), ("test", 2)):
        masks[f"C2:{name}"] = (
            ((part_a == 0) & (part_b == code) & (training_degree[prepared["endpoint_a"]] >= 1))
            | ((part_b == 0) & (part_a == code) & (training_degree[prepared["endpoint_b"]] >= 1))
        )
        masks[f"C3:{name}"] = (part_a == code) & (part_b == code)
    return masks, node_partitions


def _evaluate(
    prepared: Mapping[str, Any],
    assignments: np.ndarray,
    endpoint_counts: np.ndarray,
    candidate_index: int,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    scale = int(config["allocation"]["score_quantization_scale"])
    criteria = config["acceptance_criteria"]
    masks, node_partitions = _opportunity_masks(prepared, assignments)
    source_masks = {
        "ALL": np.ones(len(prepared["endpoint_a"]), dtype=bool),
        "HI-II-14": prepared["hi"],
        "HuRI": prepared["huri"],
    }
    pools: dict[str, dict[str, int]] = {}
    for pool, mask in masks.items():
        components = (
            np.unique(
                np.concatenate((prepared["component_a"][mask], prepared["component_b"][mask]))
            ).size
            if np.any(mask)
            else 0
        )
        pools[pool] = {
            "pairs": int(np.count_nonzero(mask)),
            "components": int(components),
            "HI-II-14_pairs": int(np.count_nonzero(mask & prepared["hi"])),
            "HuRI_pairs": int(np.count_nonzero(mask & prepared["huri"])),
        }
    total = len(prepared["nodes"])
    weights = (70, 15, 15)
    endpoint_deviations = [
        _quantize(abs(int(endpoint_counts[i]) * 100 - weights[i] * total), 100 * total, scale)
        for i in range(3)
    ]
    pair_floor = int(criteria["minimum_released_positive_pairs_each_opportunity_pool"])
    component_floor = int(criteria["minimum_participating_components_each_opportunity_pool"])
    source_floor = int(criteria["minimum_released_positive_pairs_per_source_each_opportunity_pool"])
    evidence = []
    for values in pools.values():
        evidence.extend(
            (
                _quantize(values["pairs"], pair_floor, scale),
                _quantize(values["components"], component_floor, scale),
                _quantize(values["HI-II-14_pairs"], source_floor, scale),
                _quantize(values["HuRI_pairs"], source_floor, scale),
            )
        )
    global_all = len(prepared["endpoint_a"])
    source_deviations = []
    for values in pools.values():
        for source, global_count in (
            ("HI-II-14", int(np.count_nonzero(prepared["hi"]))),
            ("HuRI", int(np.count_nonzero(prepared["huri"]))),
        ):
            source_deviations.append(
                _quantize(
                    abs(values[f"{source}_pairs"] * global_all - values["pairs"] * global_count),
                    max(1, values["pairs"] * global_all),
                    scale,
                )
            )
    heldout = []
    for axis in ("C2", "C3"):
        dev = pools[f"{axis}:development"]
        test = pools[f"{axis}:test"]
        for field in ("pairs", "HI-II-14_pairs", "HuRI_pairs"):
            heldout.append(
                _quantize(abs(dev[field] - test[field]), max(1, dev[field] + test[field]), scale)
            )
    total_degree = int(prepared["degrees"].sum())
    degree_deviations = []
    for code in range(3):
        mass = int(prepared["degrees"][node_partitions == code].sum())
        degree_deviations.append(
            _quantize(abs(mass * 100 - weights[code] * total_degree), 100 * total_degree, scale)
        )
    hub_deviations = []
    for indices in prepared["hubs"].values():
        for code in range(3):
            count = int(np.count_nonzero(node_partitions[indices] == code))
            hub_deviations.append(
                _quantize(abs(count * 100 - weights[code] * len(indices)), 100 * len(indices), scale)
            )
    endpoint_max = max(endpoint_deviations)
    evidence_min = min(evidence)
    source_max = max(source_deviations)
    heldout_max = max(heldout)
    degree_max = max(degree_deviations)
    hub_max = max(hub_deviations)
    failures = []
    if endpoint_max > _quantize(3, 100, scale):
        failures.append("endpoint_balance")
    if any(values["pairs"] < pair_floor for values in pools.values()):
        failures.append("positive_pair_floor")
    if any(values["components"] < component_floor for values in pools.values()):
        failures.append("component_floor")
    if any(
        values[f"{source}_pairs"] < source_floor
        for values in pools.values()
        for source in ("HI-II-14", "HuRI")
    ):
        failures.append("source_floor")
    if source_max > _quantize(10, 100, scale):
        failures.append("source_composition")
    if heldout_max > _quantize(35, 100, scale):
        failures.append("heldout_axis_balance")
    if degree_max > _quantize(10, 100, scale):
        failures.append("degree_mass_balance")
    if hub_max > _quantize(10, 100, scale):
        failures.append("hub_balance")
    score = (
        endpoint_max,
        -evidence_min,
        heldout_max,
        source_max,
        degree_max,
        hub_max,
        sum(abs(int(endpoint_counts[i]) * 100 - weights[i] * total) for i in range(3)),
        candidate_index,
    )
    return {
        "valid": not failures,
        "failures": failures,
        "score": score,
        "pools": pools,
        "masks": masks,
        "node_partitions": node_partitions,
        "endpoint_counts": [int(value) for value in endpoint_counts],
        "endpoint_max": endpoint_max,
        "evidence_min": evidence_min,
        "source_max": source_max,
        "heldout_max": heldout_max,
        "degree_max": degree_max,
        "hub_max": hub_max,
    }


def _search(
    prepared: Mapping[str, Any], definition: str, config: Mapping[str, Any]
) -> dict[str, Any]:
    valid = 0
    failures: Counter[str] = Counter()
    best_evaluation = None
    best_assignment = None
    count = int(config["allocation"]["candidate_count_per_definition"])
    for candidate_index in range(count):
        assignments, endpoint_counts = _allocate(prepared, definition, candidate_index, config)
        evaluation = _evaluate(
            prepared, assignments, endpoint_counts, candidate_index, config
        )
        failures.update(evaluation["failures"])
        if not evaluation["valid"]:
            continue
        valid += 1
        if best_evaluation is None or evaluation["score"] < best_evaluation["score"]:
            best_evaluation = evaluation
            best_assignment = assignments.copy()
    return {
        "candidate_count": count,
        "valid": valid,
        "failures": dict(sorted(failures.items())),
        "evaluation": best_evaluation,
        "assignment": best_assignment,
    }


def _rows_by(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> dict[tuple[Any, ...], Mapping[str, Any]]:
    return {tuple(row[field] for field in fields): row for row in rows}


def _same_value(observed: Any, expected: Any) -> bool:
    if isinstance(expected, float):
        return math.isclose(float(observed), expected, rel_tol=0.0, abs_tol=1e-12)
    return observed == expected


def _contains(row: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
    return all(key in row and _same_value(row[key], value) for key, value in expected.items())


def _validate_selected_outputs(
    *,
    checks: Checks,
    outputs: Mapping[str, list[dict[str, Any]]],
    nodes: Sequence[str],
    lengths: Mapping[str, int],
    pairs: Mapping[str, set[tuple[str, str]]],
    graphs: Mapping[str, Mapping[str, Any]],
    definition: str,
    search: Mapping[str, Any],
    primary: Mapping[str, Any],
    fallback: Mapping[str, Any] | None,
    prepared: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    assignments = search["assignment"]
    evaluation = search["evaluation"]
    assert assignments is not None and evaluation is not None
    memberships = graphs[definition]["memberships"]
    sizes = graphs[definition]["sizes"]
    representatives = prepared["representatives"]
    representative_index = {value: index for index, value in enumerate(representatives)}
    expected_component_id = {
        representative: _component_id(config["split_id"], definition, representative, sizes[representative])
        for representative in representatives
    }
    component_rows = _rows_by(outputs["component_partition_assignments"], ("component_representative_sha256",))
    endpoint_rows = _rows_by(outputs["endpoint_partition_assignments"], ("reference_sequence_sha256",))
    component_ok = len(component_rows) == len(sizes)
    for representative in representatives:
        partition = PARTITIONS[int(assignments[representative_index[representative]])]
        row = component_rows.get((representative,), {})
        component_ok &= _contains(
            row,
            {
                "leakage_definition": definition,
                "identity_threshold_percent": 30,
                "component_id": expected_component_id[representative],
                "component_size": sizes[representative],
                "partition": partition,
                "selected_candidate_index": int(evaluation["score"][-1]),
                "pair_rows_emitted": False,
                "model_output_used": False,
            },
        )
    endpoint_ok = len(endpoint_rows) == 17_000
    endpoint_partitions: dict[str, str] = {}
    for endpoint in nodes:
        representative = memberships[endpoint]
        partition = PARTITIONS[int(assignments[representative_index[representative]])]
        endpoint_partitions[endpoint] = partition
        row = endpoint_rows.get((endpoint,), {})
        endpoint_ok &= _contains(
            row,
            {
                "sequence_length": lengths[endpoint],
                "component_id": expected_component_id[representative],
                "component_size": sizes[representative],
                "partition": partition,
                "interaction_supervision_eligible": partition == "train",
                "exact_endpoint_absent_from_interaction_supervised_training": partition != "train",
                "pair_level_c1_c2_c3_label_assigned": False,
            },
        )
    checks.require(
        "assignments.all_endpoints_components_exact_selected_candidate",
        component_ok and endpoint_ok,
        observed={"components_ok": component_ok, "endpoints_ok": endpoint_ok},
        expected={"components_ok": True, "endpoints_ok": True},
    )

    source_masks = {
        "ALL": np.ones(len(prepared["endpoint_a"]), dtype=bool),
        "HI-II-14": prepared["hi"],
        "HuRI": prepared["huri"],
    }
    masks, node_partitions = _opportunity_masks(prepared, assignments)
    opportunity_rows = _rows_by(
        outputs["opportunity_summaries"],
        ("opportunity_axis", "evaluation_partition", "source_dataset"),
    )
    opportunity_ok = len(opportunity_rows) == 15
    for pool, base_mask in masks.items():
        axis, evaluation_partition = pool.split(":", 1)
        for source, source_mask in source_masks.items():
            mask = base_mask & source_mask
            endpoints = (
                np.unique(
                    np.concatenate((prepared["endpoint_a"][mask], prepared["endpoint_b"][mask]))
                )
                if np.any(mask)
                else np.array([], dtype=np.int64)
            )
            components = np.unique(prepared["node_components"][endpoints])
            row = opportunity_rows.get((axis, evaluation_partition, source), {})
            opportunity_ok &= _contains(
                row,
                {
                    "released_positive_pair_count": int(np.count_nonzero(mask)),
                    "participating_endpoint_count": int(endpoints.size),
                    "participating_component_count": int(components.size),
                    "exact_heldout_endpoints_absent_from_interaction_supervised_training": axis == "C3",
                    "component_disjoint_from_training_under_selected_rule": axis == "C3",
                    "pair_rows_emitted": False,
                    "pair_level_label_assigned": False,
                },
            )
    checks.require(
        "opportunities.c1_c2_c3_counts_sources_and_components_exact",
        opportunity_ok,
        observed=opportunity_ok,
        expected=True,
    )

    pair_part_a = node_partitions[prepared["endpoint_a"]]
    pair_part_b = node_partitions[prepared["endpoint_b"]]
    partition_rows = _rows_by(outputs["partition_summaries"], ("partition",))
    targets = config["allocation"]["target_endpoint_fractions"]
    partition_ok = len(partition_rows) == 3
    for code, partition in enumerate(PARTITIONS):
        endpoint_mask = node_partitions == code
        component_mask = assignments == code
        internal = (pair_part_a == code) & (pair_part_b == code)
        sizes_here = [sizes[representatives[index]] for index in np.flatnonzero(component_mask)]
        degree_sum = int(prepared["degrees"][endpoint_mask].sum())
        expected = {
            "target_endpoint_fraction": float(targets[partition]),
            "endpoint_count": int(np.count_nonzero(endpoint_mask)),
            "endpoint_fraction": np.count_nonzero(endpoint_mask) / len(nodes),
            "absolute_target_fraction_deviation": abs(
                np.count_nonzero(endpoint_mask) / len(nodes) - float(targets[partition])
            ),
            "component_count": int(np.count_nonzero(component_mask)),
            "singleton_component_count": sum(size == 1 for size in sizes_here),
            "largest_component_size": max(sizes_here),
            "positive_exposed_endpoint_count": int(np.count_nonzero(prepared["degrees"][endpoint_mask] > 0)),
            "internal_positive_pairs_all": int(np.count_nonzero(internal)),
            "internal_positive_pairs_hi_ii_14": int(np.count_nonzero(internal & prepared["hi"])),
            "internal_positive_pairs_huri": int(np.count_nonzero(internal & prepared["huri"])),
            "positive_degree_sum_all": degree_sum,
            "positive_degree_mass_fraction_all": degree_sum / int(prepared["degrees"].sum()),
        }
        partition_ok &= _contains(partition_rows.get((partition,), {}), expected)
    checks.require(
        "partitions.endpoint_component_source_and_degree_totals_exact",
        partition_ok,
        observed=partition_ok,
        expected=True,
    )

    degree_rows = _rows_by(outputs["partition_degree_summaries"], ("partition", "source_dataset"))
    degree_ok = len(degree_rows) == 9
    for source, pair_mask in source_masks.items():
        degree = np.bincount(
            np.concatenate((prepared["endpoint_a"][pair_mask], prepared["endpoint_b"][pair_mask])),
            minlength=len(nodes),
        ).astype(np.int64)
        ranked = np.array(
            sorted(range(len(nodes)), key=lambda index: (-int(degree[index]), prepared["nodes"][index])),
            dtype=np.int64,
        )
        hubs = {fraction: ranked[: math.ceil(fraction * len(nodes))] for fraction in (0.01, 0.05, 0.10)}
        for code, partition in enumerate(PARTITIONS):
            values = [int(value) for value in degree[node_partitions == code]]
            expected = {
                "endpoint_count": len(values),
                "positive_exposed_endpoint_count": sum(value > 0 for value in values),
                "positive_pair_count_global": int(np.count_nonzero(pair_mask)),
                "degree_sum": sum(values),
                "degree_mass_fraction": sum(values) / int(degree.sum()),
                "degree_q50": _nearest(values, 0.50),
                "degree_q90": _nearest(values, 0.90),
                "degree_q95": _nearest(values, 0.95),
                "degree_q99": _nearest(values, 0.99),
                "maximum_degree": max(values),
                "degree_histogram_json": _histogram(values),
                "endpoint_metric_rows_emitted": False,
            }
            for prefix, fraction in (("top_1_percent", 0.01), ("top_5_percent", 0.05), ("top_10_percent", 0.10)):
                count = int(np.count_nonzero(node_partitions[hubs[fraction]] == code))
                expected[f"{prefix}_global_hub_endpoint_count"] = count
                expected[f"{prefix}_global_hub_endpoint_fraction"] = count / len(hubs[fraction])
            degree_ok &= _contains(degree_rows.get((partition, source), {}), expected)
    checks.require(
        "degrees.source_partition_distributions_and_global_hubs_exact",
        degree_ok,
        observed=degree_ok,
        expected=True,
    )

    leakage_rows = _rows_by(outputs["leakage_validation_summaries"], ("leakage_definition",))
    leakage_ok = len(leakage_rows) == 2
    for graph_name, graph in graphs.items():
        cross_edges = sum(endpoint_partitions[a] != endpoint_partitions[b] for a, b in graph["edges"])
        partition_sets: dict[str, set[str]] = defaultdict(set)
        for endpoint, representative in graph["memberships"].items():
            partition_sets[representative].add(endpoint_partitions[endpoint])
        crossing_components = sum(len(value) > 1 for value in partition_sets.values())
        leakage_ok &= _contains(
            leakage_rows.get((graph_name,), {}),
            {
                "selected_as_hard_partition_rule": graph_name == definition,
                "fallback_definition": graph_name == "sensitive_fl80_union",
                "graph_edge_count": len(graph["edges"]),
                "graph_component_count": len(graph["sizes"]),
                "largest_graph_component_size": max(graph["sizes"].values()),
                "cross_partition_edge_count": cross_edges,
                "cross_partition_component_count": crossing_components,
                "partition_disjoint": cross_edges == 0 and crossing_components == 0,
                "exhaustive_homology_claim_supported": False,
            },
        )
    hard_row = leakage_rows[(definition,)]
    hard_zero = hard_row["cross_partition_edge_count"] == 0 and hard_row["cross_partition_component_count"] == 0
    sensitive_zero_if_primary = (
        definition != "local_domain_union"
        or leakage_rows[("sensitive_fl80_union",)]["cross_partition_edge_count"] == 0
    )
    checks.require(
        "leakage.both_graphs_exact_and_selected_hard_rule_disjoint",
        leakage_ok and hard_zero and sensitive_zero_if_primary,
        observed={"rows_exact": leakage_ok, "hard_zero": hard_zero, "sensitive_zero_if_primary": sensitive_zero_if_primary},
        expected={"rows_exact": True, "hard_zero": True, "sensitive_zero_if_primary": True},
    )

    selection = outputs["selection_summaries"][0]
    scale = int(config["allocation"]["score_quantization_scale"])
    score_names = (
        "maximum_endpoint_deviation_units",
        "negative_minimum_evidence_ratio_units",
        "maximum_heldout_imbalance_units",
        "maximum_source_deviation_units",
        "maximum_degree_deviation_units",
        "maximum_hub_deviation_units",
        "sum_endpoint_count_deviation_units",
        "candidate_index",
    )
    expected_score_json = json.dumps(
        dict(zip(score_names, map(int, evaluation["score"]))),
        sort_keys=True,
        separators=(",", ":"),
    )
    selection_ok = _contains(
        selection,
        {
            "selection_status": "primary_selected" if definition == "local_domain_union" else "fallback_selected",
            "candidate_count_per_definition": int(config["allocation"]["candidate_count_per_definition"]),
            "primary_candidates_evaluated": primary["candidate_count"],
            "primary_valid_candidate_count": primary["valid"],
            "primary_failure_counts_json": json.dumps(primary["failures"], sort_keys=True, separators=(",", ":")),
            "fallback_evaluated": fallback is not None,
            "fallback_candidates_evaluated": fallback["candidate_count"] if fallback else 0,
            "fallback_valid_candidate_count": fallback["valid"] if fallback else 0,
            "fallback_failure_counts_json": json.dumps(fallback["failures"], sort_keys=True, separators=(",", ":")) if fallback else "{}",
            "selected_leakage_definition": definition,
            "selected_candidate_index": int(evaluation["score"][-1]),
            "selected_score_json": expected_score_json,
            "frozen_objective_json": json.dumps(
                config["allocation"]["frozen_selection_objective"],
                sort_keys=True,
                separators=(",", ":"),
            ),
            "deterministic_seed": str(config["allocation"]["deterministic_seed"]),
            "target_endpoint_fractions_json": json.dumps(
                config["allocation"]["target_endpoint_fractions"],
                sort_keys=True,
                separators=(",", ":"),
            ),
            "selected_maximum_endpoint_fraction_deviation": evaluation["endpoint_max"] / scale,
            "selected_minimum_normalized_evidence_ratio": evaluation["evidence_min"] / scale,
            "selected_maximum_source_presence_fraction_deviation": evaluation["source_max"] / scale,
            "selected_maximum_heldout_axis_relative_imbalance": evaluation["heldout_max"] / scale,
            "selected_maximum_degree_mass_fraction_deviation": evaluation["degree_max"] / scale,
            "selected_maximum_hub_endpoint_fraction_deviation": evaluation["hub_max"] / scale,
            "future_model_results_inspected": False,
            "split_frozen": True,
        },
    )
    fallback_rule_ok = (primary["valid"] > 0 and fallback is None) or (primary["valid"] == 0 and fallback is not None)
    checks.require(
        "selection.full_search_objective_seed_ties_and_fallback_exact",
        selection_ok and fallback_rule_ok,
        observed={"selection_exact": selection_ok, "fallback_rule": fallback_rule_ok},
        expected={"selection_exact": True, "fallback_rule": True},
    )


def validate_split(
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
        expected={"sha256": config["runtime"]["container_sha256"], "architecture": config["runtime"]["architecture"]},
    )
    run_manifest_path = run_root / "RUN_MANIFEST.json"
    split_manifest_path = canonical_root / "SPLIT_MANIFEST.json"
    run_sha = _check_sidecar(checks, run_manifest_path, "inventory.run_manifest_sidecar")
    split_sha = _check_sidecar(checks, split_manifest_path, "inventory.split_manifest_sidecar")
    audit_sha = _check_sidecar(checks, audit_report_path, "inventory.audit_report_sidecar")
    run_manifest = load_json(run_manifest_path)
    split_manifest = load_json(split_manifest_path)
    audit_report = load_json(audit_report_path)
    _verify_run_inventory(checks, run_root, run_manifest)
    input_files, paths, verified_inputs = _verify_inputs(project_root, config)
    contract = load_contract(paths["split_schema"])
    outputs = _read_outputs(
        checks=checks,
        project_root=project_root,
        canonical_root=canonical_root,
        manifest=split_manifest,
        contract=contract,
    )
    production_clean = all(
        document.get("git", {}).get("tracked_worktree_clean") is True
        and document.get("git", {}).get("status") == ""
        for document in (run_manifest, split_manifest, audit_report)
    )
    production_commit = run_manifest.get("git", {}).get("commit")
    same_commit = bool(production_commit) and all(
        document.get("git", {}).get("commit") == production_commit
        for document in (split_manifest, audit_report)
    )
    checks.require(
        "provenance.production_clean_single_commit",
        production_clean and same_commit,
        observed={"clean": production_clean, "same_commit": same_commit},
        expected={"clean": True, "same_commit": True},
    )
    provenance_ok = (
        audit_report["outputs"]["run_manifest_sha256"] == run_sha
        and audit_report["outputs"]["split_manifest_sha256"] == split_sha
        and split_manifest["inputs"]["run_manifest_sha256"] == run_sha
        and split_manifest["inputs"]["documents"] == verified_inputs["documents"]
        and split_manifest["inputs"]["tables"] == verified_inputs["tables"]
        and run_manifest["config"]["sha256"] == sha256_file(config_path)
        and split_manifest["inputs"]["config_sha256"] == sha256_file(config_path)
        and audit_report["inputs"]["config_sha256"] == sha256_file(config_path)
    )
    checks.require(
        "provenance.config_parents_and_manifests_exact",
        provenance_ok,
        observed=provenance_ok,
        expected=True,
    )

    connection = duckdb.connect(":memory:")
    connection.execute(f"SET memory_limit='{config['runtime']['duckdb_memory_limit']}'")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    try:
        for name, files in input_files.items():
            connection.read_parquet([path.as_posix() for path in files]).create_view(name)
        nodes, lengths, pairs, pair_sources = _load_state(connection, config)
    finally:
        connection.close()
    checks.require(
        "parent.frozen_17000_endpoints_58049_positives_and_components",
        len(nodes) == 17000 and len(pairs["ALL"]) == 58049,
        observed={"endpoints": len(nodes), "positive_pairs": len(pairs["ALL"])},
        expected={"endpoints": 17000, "positive_pairs": 58049},
    )

    accepted = _edges(paths["parent_normalized_edges"])
    sensitive = accepted | _edges(paths["full_length_sensitivity_edges"])
    local = sensitive | _edges(paths["local_domain_sensitivity_edges"])
    graphs = {}
    for name, edges in (("sensitive_fl80_union", sensitive), ("local_domain_union", local)):
        memberships, sizes = _components(nodes, edges)
        graphs[name] = {"edges": edges, "memberships": memberships, "sizes": sizes}
    graph_counts = {
        name: (len(graph["edges"]), len(graph["sizes"]), max(graph["sizes"].values()))
        for name, graph in graphs.items()
    }
    checks.require(
        "leakage.independent_graph_reconstruction_matches_dec0020",
        graph_counts == {
            "sensitive_fl80_union": (63180, 11292, 362),
            "local_domain_union": (176264, 7782, 1624),
        }
        and sensitive.issubset(local),
        observed=graph_counts,
        expected={"sensitive_fl80_union": (63180, 11292, 362), "local_domain_union": (176264, 7782, 1624)},
    )

    primary_prepared = _prepare(
        nodes=nodes,
        memberships=graphs["local_domain_union"]["memberships"],
        sizes=graphs["local_domain_union"]["sizes"],
        positive_pairs=pairs["ALL"],
        pair_sources=pair_sources,
    )
    primary = _search(primary_prepared, "local_domain_union", config)
    fallback = None
    definition = "local_domain_union"
    selected = primary
    prepared = primary_prepared
    if primary["valid"] == 0:
        prepared = _prepare(
            nodes=nodes,
            memberships=graphs["sensitive_fl80_union"]["memberships"],
            sizes=graphs["sensitive_fl80_union"]["sizes"],
            positive_pairs=pairs["ALL"],
            pair_sources=pair_sources,
        )
        fallback = _search(prepared, "sensitive_fl80_union", config)
        definition = "sensitive_fl80_union"
        selected = fallback
    checks.require(
        "selection.independent_search_has_valid_selected_allocation",
        selected is not None and selected["valid"] > 0 and selected["assignment"] is not None,
        observed={"primary_valid": primary["valid"], "fallback_valid": fallback["valid"] if fallback else None},
        expected="at least one valid allocation under the authorized primary/fallback rule",
    )
    if selected is not None and selected["assignment"] is not None:
        _validate_selected_outputs(
            checks=checks,
            outputs=outputs,
            nodes=nodes,
            lengths=lengths,
            pairs=pairs,
            graphs=graphs,
            definition=definition,
            search=selected,
            primary=primary,
            fallback=fallback,
            prepared=prepared,
            config=config,
        )

    row_counts = {table: len(outputs[table]) for table in TABLES}
    aggregate_tables = {
        table: outputs[table]
        for table in TABLES
        if table not in {"component_partition_assignments", "endpoint_partition_assignments"}
    }
    metrics_ok = (
        split_manifest["row_counts"] == row_counts
        and audit_report["row_counts"] == row_counts
        and split_manifest["aggregate_metrics"] == aggregate_tables
        and audit_report["aggregate_metrics"] == aggregate_tables
    )
    checks.require(
        "metrics.manifest_report_and_canonical_tables_match",
        metrics_ok,
        observed=metrics_ok,
        expected=True,
    )
    claims = _rows_by(outputs["claim_assessments"], ("claim_name",))
    prohibited = {
        "unseen_biological_family",
        "plm_unseen_protein",
        "exhaustive_absence_of_homology",
        "universal_nonbinding",
        "prevalence",
        "calibrated_probability",
    }
    scope_false = all(
        split_manifest.get(name) is False
        for name in (
            "parent_audits_modified_or_recomputed",
            "candidate_pair_materialization_performed",
            "positive_pair_rows_emitted",
            "evidence_indicator_construction_performed",
            "negative_label_construction_performed",
            "pseudo_negative_sampling_performed",
            "pair_level_c1_c2_c3_assignment_performed",
            "external_panel_inputs_used",
            "structural_mapping_performed",
            "model_work_performed",
            "prevalence_estimation_performed",
            "calibration_performed",
        )
    )
    claims_ok = (
        claims[("exact_endpoint_component_disjoint_c3",)]["supported_by_split"] is True
        and claims[("exact_endpoint_component_disjoint_c3",)]["claim_status"]
        == "permitted_with_exact_operational_qualifier"
        and all(
            claims[(name,)]["supported_by_split"] is False
            and claims[(name,)]["claim_status"] == "prohibited"
            for name in prohibited
        )
    )
    no_forbidden_columns = not any(
        "pair_id" in row or "candidate_pair" in row or "negative_label" in row
        for rows in outputs.values()
        for row in rows
    )
    checks.require(
        "scope.no_pairs_negatives_external_structure_model_or_overclaim",
        scope_false and claims_ok and no_forbidden_columns,
        observed={"manifest_guards": scope_false, "claims": claims_ok, "columns": no_forbidden_columns},
        expected={"manifest_guards": True, "claims": True, "columns": True},
    )

    current_git = git_provenance(project_root)
    checks.require(
        "provenance.validator_started_from_clean_commit",
        current_git["tracked_worktree_clean"] is True and current_git["status"] == "",
        observed={"clean": current_git["tracked_worktree_clean"], "status": current_git["status"]},
        expected={"clean": True, "status": ""},
    )
    return {
        "schema_version": 1,
        "gate_id": "final_benchmark_component_split_v1_validation",
        "split_id": config["split_id"],
        "split_version": SPLIT_VERSION,
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
        "split_manifest": split_manifest_path.as_posix(),
        "split_manifest_sha256": split_sha,
        "audit_report": audit_report_path.as_posix(),
        "audit_report_sha256": audit_sha,
        "config": config_path.as_posix(),
        "config_sha256": sha256_file(config_path),
        "selected_leakage_definition": definition,
        "validated_table_row_counts": row_counts,
        "check_counts": checks.counts(),
        "checks": checks.records,
        "interpretation": (
            "Pass independently reconstructs both accepted 30% leakage graphs, repeats the "
            "complete deterministic candidate search and frozen objective, verifies every "
            "endpoint/component assignment and all aggregate C1/C2/C3, source, degree, hub, "
            "and leakage counts, and confirms that no pair rows, negatives, external panels, "
            "structures, or model outputs were used."
        ),
        "authorizations": {
            "split_technical_validation_passed": checks.passed,
            "endpoint_component_split_skeleton": True,
            "pair_level_c1_c2_c3_assignment": False,
            "candidate_pair_materialization": False,
            "negative_label_construction": False,
            "pseudo_negative_sampling": False,
            "external_panel_integration": False,
            "structural_mapping": False,
            "model_work": False,
            "return_to_governance_required": True,
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/final_benchmark_component_split_v1.yaml"),
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

    result = validate_split(
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
