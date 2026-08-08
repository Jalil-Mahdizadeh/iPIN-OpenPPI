"""Aggregate-only feasibility audit for the frozen pair-level PU-R protocol."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import (
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.validation.staging import _write_report

from . import PROTOCOL_VERSION
from .semantics import (
    DEGREE_BINS,
    PRIMARY_CELLS,
    Pair,
    c1_role,
    choose_two,
    degree_bin,
    degree_histogram,
    degree_pair_stratum,
    nearest_rank,
    pair_stratum_populations,
    sampling_design,
    unordered_pair,
)
from .support import (
    load_json,
    load_yaml,
    resolve_and_verify_documents,
    resolve_inside,
    validate_config,
    verify_manifest_table,
)


SOURCES = ("HI-II-14", "HuRI")
PARTITIONS = ("train", "development", "test")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _verify_explicit_summary(
    *,
    project_root: Path,
    summary: Mapping[str, Any],
    expected_root: Path,
    verify_hashes: bool,
) -> tuple[list[Path], dict[str, Any]]:
    root = expected_root.resolve(strict=True)
    files: list[Path] = []
    rows = 0
    total_bytes = 0
    for index, record in enumerate(summary["files"]):
        candidate = Path(str(record["path"]))
        if not candidate.is_absolute():
            candidate = project_root / candidate
        path = candidate.resolve(strict=True)
        path.relative_to(root)
        if path.parent != root or path.name != f"part-{index:05d}.parquet":
            raise RuntimeError(f"Unexpected manifest part: {path}")
        info = path.stat(follow_symlinks=False)
        if path.is_symlink() or not stat.S_ISREG(info.st_mode):
            raise RuntimeError(f"Manifest part is not a regular non-link file: {path}")
        observed_rows = int(pq.ParquetFile(path).metadata.num_rows)
        if (info.st_size, observed_rows) != (int(record["bytes"]), int(record["rows"])):
            raise RuntimeError(f"Manifest size/row mismatch for {path}")
        if verify_hashes and sha256_file(path) != str(record["sha256"]):
            raise RuntimeError(f"Manifest hash mismatch for {path}")
        files.append(path)
        rows += observed_rows
        total_bytes += info.st_size
    if rows != int(summary["rows"]) or len(files) != int(summary["parts"]):
        raise RuntimeError("Manifest aggregate mismatch")
    return files, {
        "table": str(summary["table"]),
        "rows": rows,
        "parts": len(files),
        "bytes": total_bytes,
        "schema_name": str(summary["schema_name"]),
        "schema_version": int(summary["schema_version"]),
        "schema_sha256": str(summary["schema_sha256"]),
        "sha256_verification": "complete" if verify_hashes else "smoke_skipped",
    }


def _verify_inputs(
    *,
    project_root: Path,
    config: Mapping[str, Any],
    verify_hashes: bool,
) -> tuple[dict[str, Any], dict[str, list[Path]], dict[str, Path]]:
    paths, documents = resolve_and_verify_documents(
        project_root=project_root, config=config, verify_hashes=verify_hashes
    )
    policy = load_yaml(paths["accepted_estimand_policy"])
    proposal = load_yaml(paths["incorporated_estimand_proposal"])
    screen_audit = load_json(paths["systematic_screen_audit_report"])
    screen_validation = load_json(paths["systematic_screen_validation_report"])
    acquisition = load_json(paths["acquisition_manifest"])
    parse_manifest = load_json(paths["parse_manifest"])
    reconciliation_manifest = load_json(paths["reconciliation_manifest"])
    eligibility_manifest = load_json(paths["eligibility_manifest"])
    split_manifest = load_json(paths["frozen_split_manifest"])
    parent_decision = paths["parent_acceptance_decision"].read_text(encoding="utf-8")
    gate = load_yaml(paths["active_gate"])

    if (
        policy.get("status") != "accepted_effective"
        or policy.get("primary_design", {}).get("task")
        != "reference_sequence_positive_unlabeled_ranking"
        or proposal.get("positive_and_unlabeled_sampling", {}).get("sampler", {}).get(
            "public_salt"
        )
        != "ipin-openppi-benchmark-v1"
    ):
        raise RuntimeError("Accepted PU-R policy is not present")
    if (
        screen_audit.get("status") != "complete"
        or screen_validation.get("status") != "pass"
        or acquisition.get("status") != "pass"
        or parse_manifest.get("status") != "complete"
        or reconciliation_manifest.get("status") != "complete"
        or eligibility_manifest.get("status") != "complete"
        or split_manifest.get("status") != "complete_frozen"
    ):
        raise RuntimeError("An immutable parent artifact is not complete and accepted")
    if "immutable benchmark" not in parent_decision or "pair-level" not in parent_decision:
        raise RuntimeError("DEC-0022 parent acceptance text is not the expected instrument")
    protocol_gate = (
        gate.get("gates", {})
        .get("evidence", {})
        .get("pair_level_pu_r_benchmark_protocol", {})
    )
    if (
        protocol_gate.get("status") != "authorized_not_executed"
        or protocol_gate.get("fail_closed") is not True
        or protocol_gate.get("protocol_definition_and_aggregate_validation_authorized")
        is not True
        or protocol_gate.get("pair_identity_persistence_authorized") is not False
        or protocol_gate.get("unlabeled_sample_realization_authorized") is not False
        or protocol_gate.get("model_work_authorized") is not False
    ):
        raise RuntimeError("Active governance gate does not authorize this exact protocol audit")

    inputs = config["inputs"]
    eligibility_root = resolve_inside(
        project_root,
        str(inputs["eligibility_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    reconciliation_root = resolve_inside(
        project_root,
        str(inputs["reconciliation_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    split_root = resolve_inside(
        project_root,
        str(inputs["frozen_split_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    staging_root = resolve_inside(
        project_root,
        str(inputs["staging_root"]),
        project_root / "data/staging",
        strict=True,
    )

    files: dict[str, list[Path]] = {}
    tables: dict[str, Any] = {}
    table_names = config["parent_tables"]
    for key in ("eligible_reference_sequences", "space_iii_gene_eligibility"):
        table = str(table_names[key])
        table_files, summary = verify_manifest_table(
            project_root=project_root,
            manifest=eligibility_manifest,
            table_name=table,
            expected_root=eligibility_root / table,
            verify_hashes=verify_hashes,
        )
        files[key] = table_files
        tables[key] = summary
    projection = str(table_names["huri_evidence_gene_pair_projections"])
    projection_files, summary = verify_manifest_table(
        project_root=project_root,
        manifest=reconciliation_manifest,
        table_name=projection,
        expected_root=reconciliation_root / projection,
        verify_hashes=verify_hashes,
    )
    files["huri_evidence_gene_pair_projections"] = projection_files
    tables["huri_evidence_gene_pair_projections"] = summary
    for key in ("endpoint_partition_assignments", "component_partition_assignments"):
        table = str(table_names[key])
        table_files, summary = verify_manifest_table(
            project_root=project_root,
            manifest=split_manifest,
            table_name=table,
            expected_root=split_root / table,
            verify_hashes=verify_hashes,
        )
        files[key] = table_files
        tables[key] = summary

    evidence_summary = parse_manifest["source_reports"]["huri"]["tables"][
        str(table_names["evidence_records"])
    ]
    evidence_files, summary = _verify_explicit_summary(
        project_root=project_root,
        summary=evidence_summary,
        expected_root=staging_root / "huri/evidence_records",
        verify_hashes=verify_hashes,
    )
    files["evidence_records"] = evidence_files
    tables["evidence_records"] = summary
    return {"documents": documents, "tables": tables}, files, paths


def _register_views(
    connection: duckdb.DuckDBPyConnection,
    table_files: Mapping[str, Sequence[Path]],
) -> None:
    for name, paths in table_files.items():
        connection.read_parquet([path.as_posix() for path in paths]).create_view(name)


def _load_endpoints(
    connection: duckdb.DuckDBPyConnection,
    config: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str], dict[str, int]]:
    expected = config["frozen_parent_expectations"]
    eligible = {
        str(row[0])
        for row in connection.execute(
            "SELECT reference_sequence_sha256 FROM eligible_reference_sequences"
        ).fetchall()
    }
    if len(eligible) != int(expected["eligible_reference_sequences"]):
        raise RuntimeError("Frozen eligible endpoint count changed")
    partition: dict[str, str] = {}
    component: dict[str, str] = {}
    component_size: dict[str, int] = {}
    rows = connection.execute(
        "SELECT reference_sequence_sha256, component_id, component_size, partition, "
        "interaction_supervision_eligible, "
        "exact_endpoint_absent_from_interaction_supervised_training, "
        "pair_level_c1_c2_c3_label_assigned "
        "FROM endpoint_partition_assignments ORDER BY reference_sequence_sha256"
    ).fetchall()
    for endpoint, component_id, size, name, supervision, absent, pair_label in rows:
        endpoint = str(endpoint)
        name = str(name)
        if endpoint in partition or endpoint not in eligible or name not in PARTITIONS:
            raise RuntimeError("Invalid frozen endpoint assignment")
        if bool(pair_label):
            raise RuntimeError("Frozen split unexpectedly contains a pair-level label")
        if bool(supervision) != (name == "train") or bool(absent) != (name != "train"):
            raise RuntimeError("Frozen endpoint supervision flags changed")
        partition[endpoint] = name
        component[endpoint] = str(component_id)
        component_size[str(component_id)] = int(size)
    if set(partition) != eligible:
        raise RuntimeError("Frozen endpoint assignment is incomplete")
    observed_partitions = Counter(partition.values())
    if dict(observed_partitions) != dict(expected["endpoint_counts"]):
        raise RuntimeError("Frozen endpoint partition counts changed")
    component_rows = connection.execute(
        "SELECT component_id, component_size, partition, pair_rows_emitted, model_output_used "
        "FROM component_partition_assignments"
    ).fetchall()
    component_partitions: dict[str, str] = {}
    for component_id, size, name, pair_rows, model_output in component_rows:
        component_id = str(component_id)
        if bool(pair_rows) or bool(model_output):
            raise RuntimeError("Frozen split contains pair rows or model output")
        if component_id in component_partitions:
            raise RuntimeError("Duplicate frozen component")
        component_partitions[component_id] = str(name)
        if component_size.get(component_id) != int(size):
            raise RuntimeError("Frozen component size mismatch")
    if len(component_partitions) != int(expected["hard_partition_components"]):
        raise RuntimeError("Frozen component count changed")
    if Counter(component_partitions.values()) != Counter(expected["component_counts"]):
        raise RuntimeError("Frozen component partition counts changed")
    if any(component_partitions[component[e]] != partition[e] for e in partition):
        raise RuntimeError("Endpoint and component partitions disagree")
    return partition, component, component_size


def _load_positive_pairs(
    connection: duckdb.DuckDBPyConnection,
    config: Mapping[str, Any],
) -> tuple[set[Pair], dict[Pair, frozenset[str]]]:
    expected = config["frozen_parent_expectations"]
    gene_map: dict[str, str | None] = {}
    for gene, sequence, usable in connection.execute(
        "SELECT ensembl_gene_id, selected_sequence_sha256, eligibility_usable "
        "FROM space_iii_gene_eligibility"
    ).fetchall():
        gene_map[str(gene)] = str(sequence) if bool(usable) and sequence is not None else None
    if sum(value is not None for value in gene_map.values()) != int(
        expected["eligible_space_iii_genes"]
    ):
        raise RuntimeError("Eligible gene mapping count changed")

    source_pairs = {source: set() for source in SOURCES}
    for source, unique, raw_a, raw_b, label_authorized in connection.execute(
        "SELECT source_dataset, unique_gene_pair, gene_a, gene_b, label_authorized "
        "FROM huri_evidence_gene_pair_projections"
    ).fetchall():
        source = str(source)
        if source not in source_pairs or bool(label_authorized):
            raise RuntimeError("Released-positive projection is outside the frozen scope")
        if not bool(unique) or raw_a is None or raw_b is None:
            continue
        endpoint_a = gene_map.get(str(raw_a))
        endpoint_b = gene_map.get(str(raw_b))
        if endpoint_a is None or endpoint_b is None or endpoint_a == endpoint_b:
            continue
        source_pairs[source].add(unordered_pair(endpoint_a, endpoint_b))
    if len(source_pairs["HI-II-14"]) != int(
        expected["distinct_released_positive_pairs_hi_ii_14"]
    ):
        raise RuntimeError("HI-II-14 positive-pair count changed")
    if len(source_pairs["HuRI"]) != int(expected["distinct_released_positive_pairs_huri"]):
        raise RuntimeError("HuRI positive-pair count changed")
    all_pairs = source_pairs["HI-II-14"] | source_pairs["HuRI"]
    if len(all_pairs) != int(expected["distinct_released_positive_pairs"]):
        raise RuntimeError("Released-positive union count changed")
    pair_sources = {
        pair: frozenset(source for source in SOURCES if pair in source_pairs[source])
        for pair in all_pairs
    }
    membership = Counter(
        "both"
        if len(sources) == 2
        else "hi_ii_14_only"
        if "HI-II-14" in sources
        else "huri_only"
        for sources in pair_sources.values()
    )
    if dict(membership) != dict(expected["source_membership"]):
        raise RuntimeError("Released-positive source membership changed")
    return all_pairs, pair_sources


def _primary_cell(
    pair: Pair,
    *,
    partition: Mapping[str, str],
    exposed: set[str],
    role: str | None,
) -> str | None:
    part_a, part_b = partition[pair[0]], partition[pair[1]]
    if part_a == part_b == "train":
        if role in {"development", "test"} and pair[0] in exposed and pair[1] in exposed:
            return f"C1_{role}"
        return None
    names = {part_a, part_b}
    for heldout in ("development", "test"):
        if names == {"train", heldout}:
            train_endpoint = pair[0] if part_a == "train" else pair[1]
            return f"C2_{heldout}" if train_endpoint in exposed else None
        if part_a == part_b == heldout:
            return f"C3_{heldout}"
    return None


def _cell_summary(
    pairs: Iterable[Pair],
    *,
    pair_sources: Mapping[Pair, frozenset[str]],
    component: Mapping[str, str],
) -> dict[str, Any]:
    values = set(pairs)
    endpoints = {endpoint for pair in values for endpoint in pair}
    components = {component[endpoint] for endpoint in endpoints}
    return {
        "pairs": len(values),
        "endpoints": len(endpoints),
        "components": len(components),
        "HI-II-14": sum("HI-II-14" in pair_sources[pair] for pair in values),
        "HuRI": sum("HuRI" in pair_sources[pair] for pair in values),
        "source_membership": dict(
            sorted(
                Counter(
                    "both"
                    if len(pair_sources[pair]) == 2
                    else "HI-II-14_only"
                    if "HI-II-14" in pair_sources[pair]
                    else "HuRI_only"
                    for pair in values
                ).items()
            )
        ),
    }


def _subtract_positive_strata(
    base: Mapping[str, int], positives: Iterable[Pair], degree: Mapping[str, int]
) -> dict[str, int]:
    positive_counts = Counter(
        degree_pair_stratum(degree.get(pair[0], 0), degree.get(pair[1], 0))
        for pair in positives
    )
    result = {
        stratum: int(population) - int(positive_counts[stratum])
        for stratum, population in base.items()
    }
    if any(value < 0 for value in result.values()):
        raise RuntimeError("Positive stratum exceeds candidate population")
    missing = set(positive_counts) - set(base)
    if missing:
        raise RuntimeError(f"Positive pairs occupy absent candidate strata: {sorted(missing)}")
    return {key: value for key, value in sorted(result.items()) if value > 0}


def _candidate_designs(
    *,
    partition: Mapping[str, str],
    positive_pairs: set[Pair],
    primary_sets: Mapping[str, set[Pair]],
    training_positive_pairs: set[Pair],
    training_degree: Mapping[str, int],
    exposed: set[str],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    sample_caps = config["unlabeled_sampling"]["sample_caps"]
    exposed_bin_counts = Counter(degree_bin(training_degree[endpoint]) for endpoint in exposed)
    c1_base = pair_stratum_populations(exposed_bin_counts)
    c1_visible_positives = {
        pair for pair in positive_pairs if pair[0] in exposed and pair[1] in exposed
    }
    c1_unlabeled = _subtract_positive_strata(c1_base, c1_visible_positives, training_degree)
    designs = {
        cell: sampling_design(c1_unlabeled, int(sample_caps[cell]))
        for cell in ("training", "C1_development", "C1_test")
    }
    for heldout in ("development", "test"):
        heldout_count = sum(name == heldout for name in partition.values())
        c2_base = {
            f"0|{label}": heldout_count * int(exposed_bin_counts[label])
            for label in DEGREE_BINS
            if int(exposed_bin_counts[label]) > 0
        }
        c2_cell = f"C2_{heldout}"
        c2_unlabeled = _subtract_positive_strata(
            c2_base, primary_sets[c2_cell], training_degree
        )
        designs[c2_cell] = sampling_design(c2_unlabeled, int(sample_caps[c2_cell]))
        c3_cell = f"C3_{heldout}"
        c3_base = {"0|0": choose_two(heldout_count)}
        c3_unlabeled = _subtract_positive_strata(
            c3_base, primary_sets[c3_cell], training_degree
        )
        designs[c3_cell] = sampling_design(c3_unlabeled, int(sample_caps[c3_cell]))

    target_positive_counts = {
        "training": len(training_positive_pairs),
        **{cell: len(primary_sets[cell]) for cell in PRIMARY_CELLS},
    }
    for cell, design in designs.items():
        design["target_positive_count"] = target_positive_counts[cell]
        design["positive_inclusion_probability"] = 1.0
        design["positive_sampling_weight"] = 1.0
        design["pair_rows_materialized"] = False
        design["sample_realized"] = False
    return dict(sorted(designs.items()))


def _evidence_completeness(connection: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    rows = connection.execute(
        "SELECT source_dataset, count(*) AS row_count, "
        "count_if(len(publication_ids) > 0) AS publication_nonnull, "
        "count(DISTINCT to_json(publication_ids)) AS distinct_publication_groups, "
        "count_if(len(experiment_ids) > 0) AS experiment_nonempty, "
        "count(assay_version) AS assay_version_nonnull, "
        "count(assay_batch) AS assay_batch_nonnull, "
        "count(source_created_date) AS source_created_nonnull, "
        "count(source_updated_date) AS source_updated_nonnull, "
        "list(DISTINCT assay_family ORDER BY assay_family) AS assay_families, "
        "list(DISTINCT to_json(publication_ids) ORDER BY to_json(publication_ids)) "
        "AS publication_groups, "
        "list(DISTINCT source_created_date ORDER BY source_created_date) "
        "AS source_created_values "
        "FROM evidence_records GROUP BY source_dataset ORDER BY source_dataset"
    ).fetchall()
    output: dict[str, Any] = {}
    for row in rows:
        output[str(row[0])] = {
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
    methods = connection.execute(
        "SELECT source_dataset, detection_method_ac, detection_method_name, count(*) "
        "FROM evidence_records GROUP BY ALL ORDER BY source_dataset, detection_method_ac"
    ).fetchall()
    for source, method_ac, method_name, count in methods:
        output[str(source)].setdefault("detection_methods", []).append(
            {
                "ac": str(method_ac),
                "name": str(method_name),
                "rows": int(count),
            }
        )
    return output


def _strict_source_analysis(
    *,
    positive_pairs: set[Pair],
    pair_sources: Mapping[Pair, frozenset[str]],
    partition: Mapping[str, str],
    component: Mapping[str, str],
    roles: Mapping[Pair, str],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    pair_floor = int(
        config["acceptance_criteria"]["minimum_released_positive_pairs_each_primary_cell"]
    )
    component_floor = int(
        config["acceptance_criteria"]["minimum_participating_components_each_primary_cell"]
    )
    output: dict[str, Any] = {}
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
            pair
            for pair in positive_pairs
            if pair_sources[pair] == frozenset({target})
        }
        cells: dict[str, Any] = {}
        for cell in PRIMARY_CELLS:
            selected = {
                pair
                for pair in target_only
                if _primary_cell(
                    pair,
                    partition=partition,
                    exposed=visible_exposed,
                    role=roles.get(pair),
                )
                == cell
            }
            summary = _cell_summary(
                selected, pair_sources=pair_sources, component=component
            )
            summary["disposition"] = (
                "headline_eligible"
                if summary["pairs"] >= pair_floor
                and summary["components"] >= component_floor
                else "descriptive_only_below_primary_floor"
            )
            cells[cell] = summary
        output[target] = {
            "visible_non_target_source": other,
            "visible_training_pairs": len(visible_training),
            "visible_training_endpoints": len(visible_exposed),
            "target_only_pairs_global": len(target_only),
            "cells": cells,
            "independent_study_claim_authorized": False,
        }
    return output


def _degree_analysis(
    *,
    partition: Mapping[str, str],
    training_degree: Mapping[str, int],
) -> dict[str, Any]:
    training_endpoints = sorted(
        endpoint for endpoint, name in partition.items() if name == "train"
    )
    values = [int(training_degree.get(endpoint, 0)) for endpoint in training_endpoints]
    ranked = sorted(training_endpoints, key=lambda endpoint: (-training_degree.get(endpoint, 0), endpoint))
    hubs: dict[str, Any] = {}
    for fraction in (0.01, 0.05, 0.10):
        count = max(1, __import__("math").ceil(fraction * len(training_endpoints)))
        selected = ranked[:count]
        hubs[str(fraction)] = {
            "endpoint_count": count,
            "positive_exposed_endpoint_count": sum(
                training_degree.get(endpoint, 0) > 0 for endpoint in selected
            ),
            "minimum_degree": min(training_degree.get(endpoint, 0) for endpoint in selected),
        }
    return {
        "population": "training_partition_endpoints",
        "endpoint_count": len(training_endpoints),
        "positive_exposed_endpoint_count": sum(value > 0 for value in values),
        "degree_sum": sum(values),
        "degree_q50": nearest_rank(values, 0.50),
        "degree_q90": nearest_rank(values, 0.90),
        "degree_q95": nearest_rank(values, 0.95),
        "degree_q99": nearest_rank(values, 0.99),
        "maximum_degree": max(values),
        "histogram": degree_histogram(values),
        "hubs": hubs,
        "heldout_or_withheld_positive_edges_used": False,
    }


def _analyze(
    *,
    connection: duckdb.DuckDBPyConnection,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    partition, component, component_sizes = _load_endpoints(connection, config)
    positive_pairs, pair_sources = _load_positive_pairs(connection, config)
    assignment = config["pair_assignment"]
    roles = {
        pair: c1_role(
            pair,
            salt=str(assignment["public_salt"]),
            seed=str(assignment["deterministic_seed"]),
        )
        for pair in positive_pairs
        if partition[pair[0]] == partition[pair[1]] == "train"
    }
    train_train_pairs = set(roles)
    training_positive_pairs = {
        pair for pair, role in roles.items() if role == "train"
    }
    training_degree = Counter(
        endpoint for pair in training_positive_pairs for endpoint in pair
    )
    exposed = set(training_degree)
    primary_sets = {
        cell: {
            pair
            for pair in positive_pairs
            if _primary_cell(
                pair,
                partition=partition,
                exposed=exposed,
                role=roles.get(pair),
            )
            == cell
        }
        for cell in PRIMARY_CELLS
    }
    all_primary_pairs = set().union(*primary_sets.values())
    if sum(map(len, primary_sets.values())) != len(all_primary_pairs):
        raise RuntimeError("A positive pair was assigned to multiple primary cells")
    if training_positive_pairs & all_primary_pairs:
        raise RuntimeError("A held-out positive pair entered interaction supervision")
    if any(
        partition[endpoint] != "train"
        for pair in training_positive_pairs
        for endpoint in pair
    ):
        raise RuntimeError("A heldout endpoint entered interaction supervision")

    quarantine = {
        "C1_development_failed_exposure": sum(
            role == "development"
            and not (pair[0] in exposed and pair[1] in exposed)
            for pair, role in roles.items()
        ),
        "C1_test_failed_exposure": sum(
            role == "test" and not (pair[0] in exposed and pair[1] in exposed)
            for pair, role in roles.items()
        ),
        "C2_development_failed_train_exposure": sum(
            {partition[pair[0]], partition[pair[1]]} == {"train", "development"}
            and (
                pair[0] if partition[pair[0]] == "train" else pair[1]
            )
            not in exposed
            for pair in positive_pairs
        ),
        "C2_test_failed_train_exposure": sum(
            {partition[pair[0]], partition[pair[1]]} == {"train", "test"}
            and (
                pair[0] if partition[pair[0]] == "train" else pair[1]
            )
            not in exposed
            for pair in positive_pairs
        ),
        "development_test_cross_partition": sum(
            {partition[pair[0]], partition[pair[1]]} == {"development", "test"}
            for pair in positive_pairs
        ),
    }

    primary = {
        cell: _cell_summary(
            primary_sets[cell], pair_sources=pair_sources, component=component
        )
        for cell in PRIMARY_CELLS
    }
    candidate_designs = _candidate_designs(
        partition=partition,
        positive_pairs=positive_pairs,
        primary_sets=primary_sets,
        training_positive_pairs=training_positive_pairs,
        training_degree=training_degree,
        exposed=exposed,
        config=config,
    )
    evidence = _evidence_completeness(connection)
    source_analysis = _strict_source_analysis(
        positive_pairs=positive_pairs,
        pair_sources=pair_sources,
        partition=partition,
        component=component,
        roles=roles,
        config=config,
    )

    criteria = config["acceptance_criteria"]
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Mapping[str, Any]) -> None:
        checks.append(
            {
                "check": name,
                "status": "pass" if passed else "fail",
                "detail": dict(detail),
            }
        )

    check(
        "parent_endpoint_and_component_counts",
        Counter(partition.values()) == Counter(config["frozen_parent_expectations"]["endpoint_counts"])
        and len(component_sizes)
        == int(config["frozen_parent_expectations"]["hard_partition_components"]),
        {"endpoints": len(partition), "components": len(component_sizes)},
    )
    check(
        "training_positive_and_exposure_floors",
        len(training_positive_pairs)
        >= int(criteria["minimum_interaction_supervision_training_positive_pairs"])
        and len(exposed)
        >= int(criteria["minimum_interaction_supervision_exposed_training_endpoints"]),
        {
            "training_positive_pairs": len(training_positive_pairs),
            "training_exposed_endpoints": len(exposed),
        },
    )
    expected_training = config["frozen_feasibility_expectations"]
    check(
        "frozen_training_and_c1_candidate_expectations",
        len(train_train_pairs)
        == int(expected_training["train_train_released_positive_pairs_before_hash"])
        and len(training_positive_pairs)
        == int(expected_training["interaction_supervision_training_positive_pairs"])
        and len(exposed)
        == int(expected_training["interaction_supervision_exposed_training_endpoints"])
        and int(candidate_designs["training"]["unlabeled_candidate_count"])
        == int(expected_training["c1_unlabeled_candidate_count"])
        and int(candidate_designs["training"]["unlabeled_candidate_count"])
        + int(expected_training["c1_visible_released_positive_pairs"])
        == int(expected_training["c1_candidate_endpoint_pair_count"]),
        {
            "train_train_pairs": len(train_train_pairs),
            "training_positive_pairs": len(training_positive_pairs),
            "training_exposed_endpoints": len(exposed),
            "c1_unlabeled_candidates": int(candidate_designs["training"]["unlabeled_candidate_count"]),
        },
    )
    pair_floor = int(criteria["minimum_released_positive_pairs_each_primary_cell"])
    component_floor = int(criteria["minimum_participating_components_each_primary_cell"])
    source_floor = int(criteria["minimum_source_presence_pairs_each_primary_cell"])
    for cell in PRIMARY_CELLS:
        summary = primary[cell]
        check(
            f"{cell}_primary_floors",
            summary["pairs"] >= pair_floor
            and summary["components"] >= component_floor
            and all(summary[source] >= source_floor for source in SOURCES),
            {
                "pairs": summary["pairs"],
                "components": summary["components"],
                "HI-II-14": summary["HI-II-14"],
                "HuRI": summary["HuRI"],
            },
        )
    check(
        "pair_role_disjointness",
        not bool(training_positive_pairs & all_primary_pairs)
        and sum(map(len, primary_sets.values())) == len(all_primary_pairs),
        {
            "training_evaluation_overlap": len(training_positive_pairs & all_primary_pairs),
            "distinct_evaluation_pairs": len(all_primary_pairs),
        },
    )
    sample_ok = all(
        all(int(row["sample_size"]) > 0 for row in design["strata"])
        for design in candidate_designs.values()
    )
    check(
        "sampling_probabilities_positive",
        sample_ok,
        {
            "cells": len(candidate_designs),
            "sample_realization_performed": False,
        },
    )
    expected_evidence = config["frozen_feasibility_expectations"][
        "evidence_field_completeness"
    ]
    evidence_counts = {
        source: {key: evidence[source][key] for key in expected_evidence[source]}
        for source in SOURCES
    }
    check(
        "evidence_field_completeness_matches_freeze",
        evidence_counts == expected_evidence,
        {"observed": evidence_counts},
    )
    check(
        "unsupported_holdouts_remain_inactive",
        all(evidence[source]["assay_version_nonnull"] == 0 for source in SOURCES)
        and all(evidence[source]["assay_batch_nonnull"] == 0 for source in SOURCES)
        and config["auxiliary_holdouts"]["study"]["status"]
        == "inactive_not_independently_identified"
        and config["auxiliary_holdouts"]["temporal"]["status"]
        == "inactive_not_supported_as_independent_pair_time_holdout",
        {
            "study": config["auxiliary_holdouts"]["study"]["status"],
            "assay": config["auxiliary_holdouts"]["assay_version_or_batch"]["status"],
            "temporal": config["auxiliary_holdouts"]["temporal"]["status"],
        },
    )

    expectation = config["frozen_feasibility_expectations"]
    observed_primary = {}
    for cell in PRIMARY_CELLS:
        observed_primary[cell] = {
            key: primary[cell][key]
            for key in expectation["primary_cells"][cell]
            if key in primary[cell]
        }
        design = candidate_designs[cell]
        if "candidate_pairs" in expectation["primary_cells"][cell]:
            observed_primary[cell]["candidate_pairs"] = (
                int(design["unlabeled_candidate_count"]) + int(primary[cell]["pairs"])
            )
            observed_primary[cell]["unlabeled_candidates"] = int(
                design["unlabeled_candidate_count"]
            )
    expected_primary = expectation["primary_cells"]
    check(
        "frozen_primary_feasibility_expectations",
        observed_primary == expected_primary,
        {"observed": observed_primary},
    )
    observed_source = {
        target: {
            "visible_training_pairs": source_analysis[target]["visible_training_pairs"],
            "visible_training_endpoints": source_analysis[target][
                "visible_training_endpoints"
            ],
            **{
                cell: {
                    "pairs": source_analysis[target]["cells"][cell]["pairs"],
                    "components": source_analysis[target]["cells"][cell]["components"],
                }
                for cell in PRIMARY_CELLS
            },
        }
        for target in SOURCES
    }
    check(
        "frozen_source_exclusive_expectations",
        observed_source == expectation["strict_source_exclusive_cells"],
        {"observed": observed_source},
    )
    check(
        "scope_prohibitions",
        all(
            config["authorization"][key] is False
            for key in (
                "persisted_positive_pair_rows",
                "persisted_unlabeled_pair_rows",
                "candidate_pair_materialization",
                "unlabeled_sample_realization",
                "negative_label_construction",
                "pseudo_negative_sampling",
                "frozen_endpoint_component_split_modification",
                "external_panel_input_use",
                "structural_mapping",
                "model_training",
                "model_evaluation",
            )
        ),
        {
            "pair_rows_emitted": False,
            "candidate_rows_emitted": False,
            "sample_realized": False,
            "model_work_performed": False,
        },
    )

    failures = [record for record in checks if record["status"] == "fail"]
    return {
        "parent": {
            "endpoints": len(partition),
            "components": len(component_sizes),
            "partition_endpoint_counts": dict(sorted(Counter(partition.values()).items())),
            "partition_component_counts": dict(
                sorted(
                    Counter(
                        {component[endpoint]: partition[endpoint] for endpoint in partition}.values()
                    ).items()
                )
            ),
            "released_positive_pairs": len(positive_pairs),
            "source_membership": dict(
                sorted(
                    Counter(
                        "both"
                        if len(sources) == 2
                        else "hi_ii_14_only"
                        if "HI-II-14" in sources
                        else "huri_only"
                        for sources in pair_sources.values()
                    ).items()
                )
            ),
        },
        "training": {
            "train_train_released_positive_pairs_before_hash": len(train_train_pairs),
            "interaction_supervision_training_positive_pairs": len(training_positive_pairs),
            "interaction_supervision_exposed_training_endpoints": len(exposed),
            "withheld_or_heldout_edges_in_training_degree": False,
        },
        "primary_cells": primary,
        "positive_quarantine": quarantine,
        "candidate_universes_and_sampling_design": candidate_designs,
        "degree_and_hub_stratification": _degree_analysis(
            partition=partition, training_degree=training_degree
        ),
        "evidence_field_completeness": evidence,
        "auxiliary_holdouts": {
            "source_exclusive": source_analysis,
            "study": {
                "status": "inactive_not_independently_identified",
                "independent_claim_authorized": False,
            },
            "assay_version_or_batch": {
                "status": "inactive_missing",
                "independent_claim_authorized": False,
            },
            "temporal": {
                "status": "inactive_not_supported_as_independent_pair_time_holdout",
                "independent_claim_authorized": False,
            },
        },
        "checks": checks,
        "check_counts": {
            "pass": sum(record["status"] == "pass" for record in checks),
            "fail": len(failures),
            "warning": 0,
        },
        "feasible": not failures,
    }


def audit_protocol(
    *,
    project_root: Path,
    config_path: Path,
    allow_dirty: bool = False,
    skip_input_hashes: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    config = load_yaml(config_path)
    validate_config(config)
    verify_hashes = not skip_input_hashes
    inputs, files, paths = _verify_inputs(
        project_root=project_root,
        config=config,
        verify_hashes=verify_hashes,
    )
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production protocol audit requires a clean Git worktree")
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    if active_container != expected_container:
        raise RuntimeError("Active Apptainer image differs from the frozen protocol image")
    if verify_hashes and sha256_file(active_container) != str(
        config["runtime"]["container_sha256"]
    ):
        raise RuntimeError("Active Apptainer image hash differs from the frozen protocol")

    connection = duckdb.connect()
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    connection.execute(
        f"SET memory_limit='{str(config['runtime']['duckdb_memory_limit'])}'"
    )
    _register_views(connection, files)
    started = _timestamp()
    analysis = _analyze(connection=connection, config=config)
    connection.close()
    status = "complete" if analysis["feasible"] else "failed"
    return {
        "schema_version": 1,
        "protocol_id": str(config["protocol_id"]),
        "protocol_version": PROTOCOL_VERSION,
        "status": status,
        "started_at_utc": started,
        "completed_at_utc": _timestamp(),
        "git": git,
        "runtime": {
            "container": expected_container.as_posix(),
            "container_sha256": str(config["runtime"]["container_sha256"]),
            "architecture": str(config["runtime"]["architecture"]),
            "duckdb": duckdb.__version__,
        },
        "inputs": {
            **inputs,
            "config": config_path.as_posix(),
            "config_sha256": sha256_file(config_path),
        },
        "analysis": analysis,
        "scope": {
            "pair_rows_emitted": False,
            "candidate_rows_emitted": False,
            "unlabeled_sample_realized": False,
            "negative_label_constructed": False,
            "pseudo_negative_constructed": False,
            "frozen_split_modified": False,
            "external_panel_input_used": False,
            "structural_mapping_performed": False,
            "model_work_performed": False,
            "prevalence_or_calibration_computed": False,
            "return_to_governance_required": True,
        },
        "disposition": {
            "protocol_internally_consistent_and_feasible": analysis["feasible"],
            "primary_c1_c2_c3_protocol": (
                "freeze_permitted" if analysis["feasible"] else "freeze_prohibited"
            ),
            "source_exclusive": "supported_with_cellwise_descriptive_demotion",
            "independent_study": "inactive_not_identified",
            "assay_version_or_batch": "inactive_missing",
            "independent_temporal": "inactive_not_supported",
            "c3_claim": (
                "exact_endpoints_interaction_supervision_unseen_and_component_disjoint_"
                "under_local_domain_union_30_only"
            ),
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/pair_level_pu_r_benchmark_protocol_v1.yaml"),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--skip-input-hashes", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    config_path = (
        args.config
        if args.config.is_absolute()
        else (project_root / args.config).resolve(strict=True)
    )
    config = load_yaml(config_path)
    report_path = args.report or Path(str(config["outputs"]["audit_report"]))
    if not report_path.is_absolute():
        report_path = project_root / report_path
    result = audit_protocol(
        project_root=project_root,
        config_path=config_path,
        allow_dirty=bool(args.allow_dirty),
        skip_input_hashes=bool(args.skip_input_hashes),
    )
    _write_report(report_path, result, project_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
