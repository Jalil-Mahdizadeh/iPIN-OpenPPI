"""Independent validation of the frozen pair-level PU-R protocol audit."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import stat
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import git_provenance, project_root_from, require_apptainer
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.pair_protocol.support import (
    load_json,
    load_yaml,
    require_hash,
    resolve_inside,
    validate_config,
    verify_manifest_table,
)
from ipin_openppi.validation.staging import _write_report


SOURCES = ("HI-II-14", "HuRI")
CELLS = (
    "C1_development",
    "C1_test",
    "C2_development",
    "C2_test",
    "C3_development",
    "C3_test",
)
BINS = ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")


@dataclass
class Checks:
    records: list[dict[str, Any]] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: Mapping[str, Any]) -> None:
        self.records.append(
            {
                "check": name,
                "status": "pass" if passed else "fail",
                "detail": dict(detail),
            }
        )

    @property
    def passed(self) -> bool:
        return all(record["status"] == "pass" for record in self.records)

    def counts(self) -> dict[str, int]:
        return {
            "pass": sum(record["status"] == "pass" for record in self.records),
            "warning": 0,
            "fail": sum(record["status"] == "fail" for record in self.records),
        }


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _independent_pair(endpoint_a: str, endpoint_b: str) -> tuple[str, str]:
    a, b = str(endpoint_a), str(endpoint_b)
    if not a or not b or a == b:
        raise ValueError("Independent pair requires distinct endpoints")
    return (a, b) if a < b else (b, a)


def _independent_pair_id(pair: tuple[str, str]) -> str:
    a, b = _independent_pair(*pair)
    return "pair:" + hashlib.sha256((a + "|" + b).encode("utf-8")).hexdigest()


def _independent_role(
    pair: tuple[str, str], *, salt: str, seed: str
) -> str:
    payload = (
        salt + ":" + seed + ":primary:C1:" + _independent_pair_id(pair)
    ).encode("utf-8")
    bucket = int.from_bytes(hashlib.sha256(payload).digest()[0:8], byteorder="big")
    bucket %= 10_000
    if 0 <= bucket <= 6_999:
        return "train"
    if 7_000 <= bucket <= 8_499:
        return "development"
    return "test"


def _independent_bin(value: int) -> str:
    degree = int(value)
    if degree == 0:
        return "0"
    if degree == 1:
        return "1"
    if degree == 2:
        return "2"
    if degree <= 4:
        return "3-4"
    if degree <= 9:
        return "5-9"
    if degree <= 19:
        return "10-19"
    if degree <= 49:
        return "20-49"
    if degree <= 99:
        return "50-99"
    return "100+"


def _stratum(degree_a: int, degree_b: int) -> str:
    left, right = _independent_bin(degree_a), _independent_bin(degree_b)
    if BINS.index(left) > BINS.index(right):
        left, right = right, left
    return left + "|" + right


def _choose_two(count: int) -> int:
    return int(count) * (int(count) - 1) // 2


def _base_pair_strata(bin_counts: Mapping[str, int]) -> dict[str, int]:
    result: dict[str, int] = {}
    for i, left in enumerate(BINS):
        for right in BINS[i:]:
            n_left = int(bin_counts.get(left, 0))
            n_right = int(bin_counts.get(right, 0))
            value = _choose_two(n_left) if left == right else n_left * n_right
            if value:
                result[left + "|" + right] = value
    return result


def _subtract(
    base: Mapping[str, int],
    positives: Iterable[tuple[str, str]],
    degree: Mapping[str, int],
) -> dict[str, int]:
    positive = Counter(
        _stratum(degree.get(pair[0], 0), degree.get(pair[1], 0))
        for pair in positives
    )
    if set(positive) - set(base):
        raise RuntimeError("Independent positive stratum is outside candidate base")
    output = {
        key: int(value) - int(positive[key])
        for key, value in base.items()
    }
    if any(value < 0 for value in output.values()):
        raise RuntimeError("Independent positive count exceeds candidate stratum")
    return {key: value for key, value in sorted(output.items()) if value}


def _independent_apportion(
    populations: Mapping[str, int], cap: int
) -> dict[str, int]:
    populations = {key: int(value) for key, value in populations.items() if int(value) > 0}
    total = sum(populations.values())
    target = min(total, int(cap))
    if target < len(populations):
        raise RuntimeError("Independent sample cap leaves a nonempty stratum unsampled")
    if target == total:
        return dict(sorted(populations.items()))
    allocated = {key: 1 for key in populations}
    remaining = target - len(populations)
    capacity = {key: populations[key] - 1 for key in populations}
    denominator = sum(capacity.values())
    remainders: dict[str, int] = {}
    if remaining:
        for key in populations:
            numerator = remaining * capacity[key]
            quotient, remainder = divmod(numerator, denominator)
            allocated[key] += quotient
            remainders[key] = remainder
        for key in sorted(populations, key=lambda item: (-remainders[item], item))[
            : target - sum(allocated.values())
        ]:
            allocated[key] += 1
    return dict(sorted(allocated.items()))


def _independent_sampling(
    populations: Mapping[str, int], cap: int, positive_count: int
) -> dict[str, Any]:
    allocated = _independent_apportion(populations, cap)
    rows = []
    for key in sorted(allocated):
        population = int(populations[key])
        sample = int(allocated[key])
        probability = Fraction(sample, population)
        weight = 1 / probability
        rows.append(
            {
                "stratum_id": key,
                "unlabeled_population": population,
                "sample_size": sample,
                "inclusion_probability_numerator": probability.numerator,
                "inclusion_probability_denominator": probability.denominator,
                "sampling_weight_numerator": weight.numerator,
                "sampling_weight_denominator": weight.denominator,
            }
        )
    return {
        "unlabeled_candidate_count": sum(populations.values()),
        "sample_cap": int(cap),
        "sample_size": sum(allocated.values()),
        "nonempty_strata": len(rows),
        "strata": rows,
        "target_positive_count": int(positive_count),
        "positive_inclusion_probability": 1.0,
        "positive_sampling_weight": 1.0,
        "pair_rows_materialized": False,
        "sample_realized": False,
    }


def _verify_sidecar(path: Path) -> str:
    digest = sha256_file(path)
    sidecar = path.with_name(path.name + ".sha256")
    if sidecar.is_symlink() or not sidecar.is_file():
        raise RuntimeError(f"Missing report sidecar: {sidecar}")
    fields = sidecar.read_text(encoding="utf-8").strip().split()
    if fields != [digest, path.name]:
        raise RuntimeError(f"Report sidecar mismatch: {sidecar}")
    return digest


def _verify_huri_evidence(
    *,
    project_root: Path,
    parse_manifest: Mapping[str, Any],
    root: Path,
) -> tuple[list[Path], dict[str, Any]]:
    summary = parse_manifest["source_reports"]["huri"]["tables"]["evidence_records"]
    expected_root = root.resolve(strict=True)
    paths: list[Path] = []
    rows = 0
    total_bytes = 0
    for index, record in enumerate(summary["files"]):
        candidate = Path(str(record["path"]))
        if not candidate.is_absolute():
            candidate = project_root / candidate
        path = candidate.resolve(strict=True)
        if path.parent != expected_root or path.name != f"part-{index:05d}.parquet":
            raise RuntimeError("Independent evidence part path check failed")
        info = path.stat(follow_symlinks=False)
        if path.is_symlink() or not stat.S_ISREG(info.st_mode):
            raise RuntimeError("Independent evidence part regular-file check failed")
        observed_rows = int(pq.ParquetFile(path).metadata.num_rows)
        if (
            info.st_size != int(record["bytes"])
            or observed_rows != int(record["rows"])
            or sha256_file(path) != str(record["sha256"])
        ):
            raise RuntimeError("Independent evidence part integrity check failed")
        paths.append(path)
        rows += observed_rows
        total_bytes += info.st_size
    if rows != int(summary["rows"]):
        raise RuntimeError("Independent evidence row total check failed")
    return paths, {
        "table": "evidence_records",
        "rows": rows,
        "parts": len(paths),
        "bytes": total_bytes,
    }


def _load_verified_inputs(
    *,
    project_root: Path,
    config: Mapping[str, Any],
) -> tuple[dict[str, list[Path]], dict[str, Any]]:
    inputs = config["inputs"]
    document_keys = (
        "accepted_estimand_policy",
        "incorporated_estimand_proposal",
        "systematic_screen_audit_report",
        "systematic_screen_validation_report",
        "acquisition_manifest",
        "parse_manifest",
        "evidence_schema",
        "reconciliation_manifest",
        "eligibility_manifest",
        "frozen_split_config",
        "frozen_split_manifest",
        "parent_acceptance_decision",
        "authorization_decision",
        "active_gate",
        "active_status",
    )
    documents = {}
    paths = {}
    for key in document_keys:
        path = resolve_inside(project_root, inputs[key], project_root, strict=True)
        paths[key] = path
        documents[key] = require_hash(path, inputs[key + "_sha256"])

    eligibility_manifest = load_json(paths["eligibility_manifest"])
    reconciliation_manifest = load_json(paths["reconciliation_manifest"])
    split_manifest = load_json(paths["frozen_split_manifest"])
    parse_manifest = load_json(paths["parse_manifest"])
    roots = {
        "eligibility": resolve_inside(
            project_root, inputs["eligibility_root"], project_root / "data/canonical", strict=True
        ),
        "reconciliation": resolve_inside(
            project_root, inputs["reconciliation_root"], project_root / "data/canonical", strict=True
        ),
        "split": resolve_inside(
            project_root, inputs["frozen_split_root"], project_root / "data/canonical", strict=True
        ),
        "staging": resolve_inside(
            project_root, inputs["staging_root"], project_root / "data/staging", strict=True
        ),
    }
    files: dict[str, list[Path]] = {}
    table_records: dict[str, Any] = {}
    for name in ("eligible_reference_sequences", "space_iii_gene_eligibility"):
        files[name], table_records[name] = verify_manifest_table(
            project_root=project_root,
            manifest=eligibility_manifest,
            table_name=name,
            expected_root=roots["eligibility"] / name,
            verify_hashes=True,
        )
    name = "huri_evidence_gene_pair_projections"
    files[name], table_records[name] = verify_manifest_table(
        project_root=project_root,
        manifest=reconciliation_manifest,
        table_name=name,
        expected_root=roots["reconciliation"] / name,
        verify_hashes=True,
    )
    for name in ("endpoint_partition_assignments", "component_partition_assignments"):
        files[name], table_records[name] = verify_manifest_table(
            project_root=project_root,
            manifest=split_manifest,
            table_name=name,
            expected_root=roots["split"] / name,
            verify_hashes=True,
        )
    files["evidence_records"], table_records["evidence_records"] = _verify_huri_evidence(
        project_root=project_root,
        parse_manifest=parse_manifest,
        root=roots["staging"] / "huri/evidence_records",
    )
    return files, {"documents": documents, "tables": table_records}


def _register(
    connection: duckdb.DuckDBPyConnection,
    files: Mapping[str, Sequence[Path]],
) -> None:
    for name, paths in files.items():
        connection.read_parquet([path.as_posix() for path in paths]).create_view(name)


def _independent_state(
    connection: duckdb.DuckDBPyConnection,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    endpoint_rows = connection.execute(
        "SELECT reference_sequence_sha256, component_id, partition, "
        "interaction_supervision_eligible, "
        "exact_endpoint_absent_from_interaction_supervised_training, "
        "pair_level_c1_c2_c3_label_assigned "
        "FROM endpoint_partition_assignments ORDER BY reference_sequence_sha256"
    ).fetchall()
    partition = {str(row[0]): str(row[2]) for row in endpoint_rows}
    component = {str(row[0]): str(row[1]) for row in endpoint_rows}
    endpoint_flags_ok = all(
        bool(row[3]) == (str(row[2]) == "train")
        and bool(row[4]) == (str(row[2]) != "train")
        and not bool(row[5])
        for row in endpoint_rows
    )
    component_rows = connection.execute(
        "SELECT component_id, partition, pair_rows_emitted, model_output_used "
        "FROM component_partition_assignments ORDER BY component_id"
    ).fetchall()
    component_partition = {str(row[0]): str(row[1]) for row in component_rows}
    component_flags_ok = all(not bool(row[2]) and not bool(row[3]) for row in component_rows)

    mapped_rows = connection.execute(
        "WITH gene_map AS ("
        " SELECT ensembl_gene_id, selected_sequence_sha256 "
        " FROM space_iii_gene_eligibility "
        " WHERE eligibility_usable AND selected_sequence_sha256 IS NOT NULL"
        ") "
        "SELECT DISTINCT p.source_dataset, "
        "least(a.selected_sequence_sha256, b.selected_sequence_sha256) endpoint_a, "
        "greatest(a.selected_sequence_sha256, b.selected_sequence_sha256) endpoint_b "
        "FROM huri_evidence_gene_pair_projections p "
        "JOIN gene_map a ON a.ensembl_gene_id = p.gene_a "
        "JOIN gene_map b ON b.ensembl_gene_id = p.gene_b "
        "WHERE p.unique_gene_pair AND NOT p.label_authorized "
        "AND a.selected_sequence_sha256 <> b.selected_sequence_sha256 "
        "ORDER BY 1,2,3"
    ).fetchall()
    sources_by_pair: dict[tuple[str, str], set[str]] = {}
    for source, endpoint_a, endpoint_b in mapped_rows:
        pair = _independent_pair(str(endpoint_a), str(endpoint_b))
        sources_by_pair.setdefault(pair, set()).add(str(source))
    positive_pairs = set(sources_by_pair)
    pair_sources = {
        pair: frozenset(sources) for pair, sources in sources_by_pair.items()
    }

    assignment = config["pair_assignment"]
    roles = {
        pair: _independent_role(
            pair,
            salt=str(assignment["public_salt"]),
            seed=str(assignment["deterministic_seed"]),
        )
        for pair in positive_pairs
        if partition[pair[0]] == partition[pair[1]] == "train"
    }
    training_positive = {pair for pair, role in roles.items() if role == "train"}
    degree = Counter(endpoint for pair in training_positive for endpoint in pair)
    exposed = set(degree)

    def cell_for(
        pair: tuple[str, str],
        exposure: set[str],
    ) -> str | None:
        left, right = partition[pair[0]], partition[pair[1]]
        role = roles.get(pair)
        if left == right == "train":
            if role in ("development", "test") and pair[0] in exposure and pair[1] in exposure:
                return "C1_" + str(role)
            return None
        for heldout in ("development", "test"):
            if {left, right} == {"train", heldout}:
                train_endpoint = pair[0] if left == "train" else pair[1]
                return "C2_" + heldout if train_endpoint in exposure else None
            if left == right == heldout:
                return "C3_" + heldout
        return None

    primary_sets = {
        cell: {pair for pair in positive_pairs if cell_for(pair, exposed) == cell}
        for cell in CELLS
    }

    def summary(pairs: Iterable[tuple[str, str]]) -> dict[str, Any]:
        pairs = set(pairs)
        endpoints = {endpoint for pair in pairs for endpoint in pair}
        return {
            "pairs": len(pairs),
            "endpoints": len(endpoints),
            "components": len({component[endpoint] for endpoint in endpoints}),
            "HI-II-14": sum("HI-II-14" in pair_sources[pair] for pair in pairs),
            "HuRI": sum("HuRI" in pair_sources[pair] for pair in pairs),
            "source_membership": dict(
                sorted(
                    Counter(
                        "both"
                        if len(pair_sources[pair]) == 2
                        else "HI-II-14_only"
                        if "HI-II-14" in pair_sources[pair]
                        else "HuRI_only"
                        for pair in pairs
                    ).items()
                )
            ),
        }

    primary = {cell: summary(primary_sets[cell]) for cell in CELLS}
    quarantine = {
        "C1_development_failed_exposure": sum(
            role == "development" and not (pair[0] in exposed and pair[1] in exposed)
            for pair, role in roles.items()
        ),
        "C1_test_failed_exposure": sum(
            role == "test" and not (pair[0] in exposed and pair[1] in exposed)
            for pair, role in roles.items()
        ),
        "C2_development_failed_train_exposure": sum(
            {partition[pair[0]], partition[pair[1]]} == {"train", "development"}
            and (pair[0] if partition[pair[0]] == "train" else pair[1]) not in exposed
            for pair in positive_pairs
        ),
        "C2_test_failed_train_exposure": sum(
            {partition[pair[0]], partition[pair[1]]} == {"train", "test"}
            and (pair[0] if partition[pair[0]] == "train" else pair[1]) not in exposed
            for pair in positive_pairs
        ),
        "development_test_cross_partition": sum(
            {partition[pair[0]], partition[pair[1]]} == {"development", "test"}
            for pair in positive_pairs
        ),
    }

    exposed_bins = Counter(_independent_bin(degree[endpoint]) for endpoint in exposed)
    c1_base = _base_pair_strata(exposed_bins)
    c1_positive = {
        pair for pair in positive_pairs if pair[0] in exposed and pair[1] in exposed
    }
    c1_unlabeled = _subtract(c1_base, c1_positive, degree)
    caps = config["unlabeled_sampling"]["sample_caps"]
    designs = {
        cell: _independent_sampling(
            c1_unlabeled,
            int(caps[cell]),
            len(training_positive) if cell == "training" else len(primary_sets[cell]),
        )
        for cell in ("training", "C1_development", "C1_test")
    }
    for heldout in ("development", "test"):
        heldout_count = sum(value == heldout for value in partition.values())
        c2_base = {
            "0|" + label: heldout_count * int(exposed_bins[label])
            for label in BINS
            if int(exposed_bins[label])
        }
        c2 = "C2_" + heldout
        designs[c2] = _independent_sampling(
            _subtract(c2_base, primary_sets[c2], degree),
            int(caps[c2]),
            len(primary_sets[c2]),
        )
        c3 = "C3_" + heldout
        designs[c3] = _independent_sampling(
            _subtract({"0|0": _choose_two(heldout_count)}, primary_sets[c3], degree),
            int(caps[c3]),
            len(primary_sets[c3]),
        )
    designs = dict(sorted(designs.items()))

    evidence_rows = connection.execute(
        "SELECT source_dataset, count(*), "
        "count_if(len(publication_ids)>0), "
        "count(DISTINCT to_json(publication_ids)), "
        "count_if(len(experiment_ids)>0), count(assay_version), count(assay_batch), "
        "count(source_created_date), count(source_updated_date), "
        "list(DISTINCT assay_family ORDER BY assay_family), "
        "list(DISTINCT to_json(publication_ids) ORDER BY to_json(publication_ids)), "
        "list(DISTINCT source_created_date ORDER BY source_created_date) "
        "FROM evidence_records GROUP BY source_dataset ORDER BY source_dataset"
    ).fetchall()
    evidence: dict[str, Any] = {}
    for row in evidence_rows:
        evidence[str(row[0])] = {
            "rows": int(row[1]),
            "publication_nonnull": int(row[2]),
            "distinct_publication_groups": int(row[3]),
            "experiment_nonempty": int(row[4]),
            "assay_version_nonnull": int(row[5]),
            "assay_batch_nonnull": int(row[6]),
            "source_created_nonnull": int(row[7]),
            "source_updated_nonnull": int(row[8]),
            "assay_families": list(row[9]),
            "publication_groups": [str(value) for value in row[10]],
            "source_created_values": list(row[11]),
        }
    for source, ac, name, count in connection.execute(
        "SELECT source_dataset,detection_method_ac,detection_method_name,count(*) "
        "FROM evidence_records GROUP BY ALL ORDER BY source_dataset,detection_method_ac"
    ).fetchall():
        evidence[str(source)].setdefault("detection_methods", []).append(
            {"ac": str(ac), "name": str(name), "rows": int(count)}
        )

    source_output: dict[str, Any] = {}
    pair_floor = int(
        config["acceptance_criteria"]["minimum_released_positive_pairs_each_primary_cell"]
    )
    component_floor = int(
        config["acceptance_criteria"]["minimum_participating_components_each_primary_cell"]
    )
    for target, other in (("HI-II-14", "HuRI"), ("HuRI", "HI-II-14")):
        visible_training = {
            pair
            for pair in positive_pairs
            if partition[pair[0]] == partition[pair[1]] == "train"
            and roles.get(pair) == "train"
            and other in pair_sources[pair]
        }
        visible_degree = Counter(endpoint for pair in visible_training for endpoint in pair)
        visible_exposed = set(visible_degree)
        target_only = {
            pair for pair in positive_pairs if pair_sources[pair] == frozenset({target})
        }
        cells = {}
        for cell in CELLS:
            pairs = {pair for pair in target_only if cell_for(pair, visible_exposed) == cell}
            values = summary(pairs)
            values["disposition"] = (
                "headline_eligible"
                if values["pairs"] >= pair_floor
                and values["components"] >= component_floor
                else "descriptive_only_below_primary_floor"
            )
            cells[cell] = values
        source_output[target] = {
            "visible_non_target_source": other,
            "visible_training_pairs": len(visible_training),
            "visible_training_endpoints": len(visible_exposed),
            "target_only_pairs_global": len(target_only),
            "cells": cells,
            "independent_study_claim_authorized": False,
        }

    training_endpoints = sorted(
        endpoint for endpoint, value in partition.items() if value == "train"
    )
    degree_values = [degree.get(endpoint, 0) for endpoint in training_endpoints]
    ranked = sorted(training_endpoints, key=lambda endpoint: (-degree.get(endpoint, 0), endpoint))
    hubs = {}
    for fraction in (0.01, 0.05, 0.10):
        count = max(1, math.ceil(fraction * len(training_endpoints)))
        selected = ranked[:count]
        hubs[str(fraction)] = {
            "endpoint_count": count,
            "positive_exposed_endpoint_count": sum(degree.get(endpoint, 0) > 0 for endpoint in selected),
            "minimum_degree": min(degree.get(endpoint, 0) for endpoint in selected),
        }

    def nearest(values: list[int], fraction: float) -> int:
        ordered = sorted(values)
        return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]

    degree_output = {
        "population": "training_partition_endpoints",
        "endpoint_count": len(training_endpoints),
        "positive_exposed_endpoint_count": sum(value > 0 for value in degree_values),
        "degree_sum": sum(degree_values),
        "degree_q50": nearest(degree_values, 0.50),
        "degree_q90": nearest(degree_values, 0.90),
        "degree_q95": nearest(degree_values, 0.95),
        "degree_q99": nearest(degree_values, 0.99),
        "maximum_degree": max(degree_values),
        "histogram": {
            label: sum(_independent_bin(value) == label for value in degree_values)
            for label in BINS
        },
        "hubs": hubs,
        "heldout_or_withheld_positive_edges_used": False,
    }

    return {
        "endpoint_flags_ok": endpoint_flags_ok,
        "component_flags_ok": component_flags_ok,
        "partition": partition,
        "component": component,
        "component_partition": component_partition,
        "positive_pairs": positive_pairs,
        "pair_sources": pair_sources,
        "roles": roles,
        "training_positive": training_positive,
        "degree": degree,
        "exposed": exposed,
        "primary_sets": primary_sets,
        "primary": primary,
        "quarantine": quarantine,
        "designs": designs,
        "evidence": evidence,
        "source": source_output,
        "degree_output": degree_output,
    }


def validate_protocol(
    *,
    project_root: Path,
    config_path: Path,
    audit_report_path: Path,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    config = load_yaml(config_path)
    validate_config(config)
    audit = load_json(audit_report_path)
    audit_sha = _verify_sidecar(audit_report_path)
    files, verified_inputs = _load_verified_inputs(
        project_root=project_root, config=config
    )
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Independent protocol validation requires a clean Git worktree")

    connection = duckdb.connect()
    _register(connection, files)
    state = _independent_state(connection, config)
    connection.close()

    checks = Checks()
    expected = config["frozen_parent_expectations"]
    checks.add(
        "audit_identity_status_and_hash",
        audit.get("protocol_id") == config["protocol_id"]
        and audit.get("status") == "complete"
        and audit.get("analysis", {}).get("feasible") is True,
        {"audit_sha256": audit_sha, "audit_status": audit.get("status")},
    )
    checks.add(
        "independent_endpoint_component_integrity",
        len(state["partition"]) == int(expected["eligible_reference_sequences"])
        and len(state["component_partition"]) == int(expected["hard_partition_components"])
        and state["endpoint_flags_ok"]
        and state["component_flags_ok"],
        {
            "endpoints": len(state["partition"]),
            "components": len(state["component_partition"]),
        },
    )
    checks.add(
        "independent_partition_counts",
        dict(Counter(state["partition"].values())) == dict(expected["endpoint_counts"])
        and dict(Counter(state["component_partition"].values()))
        == dict(expected["component_counts"]),
        {
            "endpoints": dict(sorted(Counter(state["partition"].values()).items())),
            "components": dict(
                sorted(Counter(state["component_partition"].values()).items())
            ),
        },
    )
    checks.add(
        "independent_positive_union_and_sources",
        len(state["positive_pairs"]) == int(expected["distinct_released_positive_pairs"])
        and sum("HI-II-14" in value for value in state["pair_sources"].values())
        == int(expected["distinct_released_positive_pairs_hi_ii_14"])
        and sum("HuRI" in value for value in state["pair_sources"].values())
        == int(expected["distinct_released_positive_pairs_huri"]),
        {"pairs": len(state["positive_pairs"])},
    )
    checks.add(
        "independent_c1_hash_and_training_exposure",
        len(state["roles"])
        == int(
            config["frozen_feasibility_expectations"][
                "train_train_released_positive_pairs_before_hash"
            ]
        )
        and len(state["training_positive"])
        == int(
            config["frozen_feasibility_expectations"][
                "interaction_supervision_training_positive_pairs"
            ]
        )
        and len(state["exposed"])
        == int(
            config["frozen_feasibility_expectations"][
                "interaction_supervision_exposed_training_endpoints"
            ]
        ),
        {
            "train_train_pairs": len(state["roles"]),
            "training_positive_pairs": len(state["training_positive"]),
            "exposed_endpoints": len(state["exposed"]),
        },
    )
    evaluation_union = set().union(*state["primary_sets"].values())
    checks.add(
        "independent_pair_role_disjointness",
        not bool(evaluation_union & state["training_positive"])
        and sum(map(len, state["primary_sets"].values())) == len(evaluation_union),
        {
            "training_evaluation_overlap": len(
                evaluation_union & state["training_positive"]
            ),
            "evaluation_pairs": len(evaluation_union),
        },
    )
    checks.add(
        "independent_primary_cell_counts",
        all(
            {
                key: state["primary"][cell][key]
                for key in config["frozen_feasibility_expectations"]["primary_cells"][
                    cell
                ]
                if key in state["primary"][cell]
            }
            == {
                key: value
                for key, value in config["frozen_feasibility_expectations"][
                    "primary_cells"
                ][cell].items()
                if key in state["primary"][cell]
            }
            for cell in CELLS
        ),
        {
            cell: {
                key: state["primary"][cell][key]
                for key in ("pairs", "components", "HI-II-14", "HuRI")
            }
            for cell in CELLS
        },
    )
    checks.add(
        "audit_primary_cells_match_independent",
        audit["analysis"]["primary_cells"] == state["primary"],
        {"cells": len(CELLS)},
    )
    checks.add(
        "audit_quarantine_matches_independent",
        audit["analysis"]["positive_quarantine"] == state["quarantine"],
        state["quarantine"],
    )
    checks.add(
        "independent_candidate_algebra_and_sampling",
        audit["analysis"]["candidate_universes_and_sampling_design"]
        == state["designs"]
        and all(
            all(row["sample_size"] > 0 for row in design["strata"])
            for design in state["designs"].values()
        ),
        {
            cell: {
                "unlabeled": design["unlabeled_candidate_count"],
                "sample": design["sample_size"],
            }
            for cell, design in state["designs"].items()
        },
    )
    checks.add(
        "independent_evidence_field_completeness",
        audit["analysis"]["evidence_field_completeness"] == state["evidence"],
        {
            source: {
                key: state["evidence"][source][key]
                for key in (
                    "rows",
                    "distinct_publication_groups",
                    "assay_version_nonnull",
                    "assay_batch_nonnull",
                )
            }
            for source in SOURCES
        },
    )
    checks.add(
        "unsupported_study_assay_temporal_axes_inactive",
        all(state["evidence"][source]["assay_version_nonnull"] == 0 for source in SOURCES)
        and all(state["evidence"][source]["assay_batch_nonnull"] == 0 for source in SOURCES)
        and audit["analysis"]["auxiliary_holdouts"]["study"]["status"]
        == "inactive_not_independently_identified"
        and audit["analysis"]["auxiliary_holdouts"]["temporal"]["status"]
        == "inactive_not_supported_as_independent_pair_time_holdout",
        {
            "study": audit["analysis"]["auxiliary_holdouts"]["study"]["status"],
            "assay": audit["analysis"]["auxiliary_holdouts"][
                "assay_version_or_batch"
            ]["status"],
            "temporal": audit["analysis"]["auxiliary_holdouts"]["temporal"][
                "status"
            ],
        },
    )
    checks.add(
        "independent_strict_source_holdouts",
        audit["analysis"]["auxiliary_holdouts"]["source_exclusive"] == state["source"],
        {
            source: {
                cell: state["source"][source]["cells"][cell]["pairs"]
                for cell in CELLS
            }
            for source in SOURCES
        },
    )
    checks.add(
        "independent_degree_hub_stratification",
        audit["analysis"]["degree_and_hub_stratification"]
        == state["degree_output"],
        {
            "degree_sum": state["degree_output"]["degree_sum"],
            "maximum_degree": state["degree_output"]["maximum_degree"],
        },
    )
    checks.add(
        "protected_test_visibility_and_one_shot_rule",
        config["evidence_visibility"]["protected_test"]["read_only_evaluator_only"]
        is True
        and config["evidence_visibility"]["protected_test"][
            "model_or_tuner_positive_identity_visible"
        ]
        is False
        and config["evidence_visibility"]["protected_test"][
            "one_first_evaluation_rule"
        ]
        is True,
        {"protected_test": "sealed_one_shot"},
    )
    checks.add(
        "metric_uncertainty_baseline_and_source_cell_freeze",
        config["metrics"]["primary"]["heldout_positive_recall_at_k"]["k"]
        == [10, 100, 1000]
        and config["uncertainty"]["replicates"] == 2000
        and config["uncertainty"]["method"]
        == "two_endpoint_component_pigeonhole_bootstrap"
        and config["later_simple_baselines"]["baselines"][
            "deterministic_hash_random"
        ]["public_salt"]
        == "ipin-openppi-pu-r-baseline-v1"
        and config["auxiliary_holdouts"]["source_exclusive"]["canonical_cell_id"]
        == "source_exclusive:{target_source}:{primary_cell}",
        {
            "recall_k": [10, 100, 1000],
            "bootstrap_replicates": 2000,
            "baseline_salt": "ipin-openppi-pu-r-baseline-v1",
        },
    )
    checks.add(
        "scope_and_claim_prohibitions",
        all(value is False for key, value in audit["scope"].items() if key != "return_to_governance_required")
        and audit["scope"]["return_to_governance_required"] is True
        and config["claim_policy"]["unlabeled_is_negative_claim"] == "prohibited"
        and config["claim_policy"]["prevalence_claim"] == "prohibited"
        and config["claim_policy"]["calibrated_probability_claim"] == "prohibited"
        and config["claim_policy"]["unseen_biological_family_claim"] == "prohibited",
        audit["scope"],
    )
    checks.add(
        "production_audit_internal_checks",
        audit["analysis"]["check_counts"].get("fail") == 0
        and audit["analysis"]["check_counts"].get("warning") == 0,
        audit["analysis"]["check_counts"],
    )

    status = "pass" if checks.passed else "fail"
    return {
        "schema_version": 1,
        "protocol_id": str(config["protocol_id"]),
        "status": status,
        "completed_at_utc": _timestamp(),
        "validator_git": git,
        "production_git": audit.get("git"),
        "config": config_path.as_posix(),
        "config_sha256": sha256_file(config_path),
        "audit_report": audit_report_path.as_posix(),
        "audit_report_sha256": audit_sha,
        "verified_inputs": verified_inputs,
        "check_counts": checks.counts(),
        "checks": checks.records,
        "interpretation": (
            "The validator independently reconstructs the frozen positive union with SQL, "
            "reimplements the pair hash, C1/C2/C3 exposure rules, source-exclusive holdouts, "
            "candidate algebra, Hamilton sampling probabilities, degree/hub summaries, and "
            "metadata completeness. It emits no pair rows or sample."
        ),
        "authorizations": {
            "protocol_technical_validation_passed": checks.passed,
            "pair_or_candidate_rows": False,
            "unlabeled_sample_realized": False,
            "negative_or_pseudo_negative_constructed": False,
            "frozen_split_modified": False,
            "external_panel_used": False,
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
        default=Path("configs/pair_level_pu_r_benchmark_protocol_v1.yaml"),
    )
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())

    def absolute(path: Path | None) -> Path | None:
        if path is None or path.is_absolute():
            return path
        return (project_root / path).resolve(strict=False)

    config_path = absolute(args.config) or args.config
    config = load_yaml(config_path)
    audit_path = absolute(args.audit_report) or project_root / str(
        config["outputs"]["audit_report"]
    )
    report_path = absolute(args.report) or project_root / str(
        config["outputs"]["validation_report"]
    )
    result = validate_protocol(
        project_root=project_root,
        config_path=config_path,
        audit_report_path=audit_path,
        allow_dirty=bool(args.allow_dirty),
    )
    _write_report(report_path, result, project_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
