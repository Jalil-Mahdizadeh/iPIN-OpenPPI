"""Construct the frozen model-free benchmark component-partition skeleton."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
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
from ipin_openppi.component_split.semantics import (
    PARTITIONS,
    POOL_KEYS,
    SOURCES,
    component_id,
    degree_histogram,
    deterministic_components,
    nearest_rank,
    opportunity_masks,
    prepare_allocation,
    search_allocations,
)
from ipin_openppi.component_split.support import (
    artifact_inventory,
    load_json,
    load_yaml,
    make_read_only,
    replace_prefix,
    require_hash,
    require_output_paths,
    resolve_inside,
    validate_config,
    verify_manifest_table,
    write_json,
    write_manifest,
)
from ipin_openppi.ingestion.common import (
    AtomicDatasetDirectory,
    ParquetBatchWriter,
    canonical_json,
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.validation.staging import _write_report


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


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_table(
    *,
    root: Path,
    table_name: str,
    rows: Iterable[Mapping[str, Any]],
    contract: Any,
    config: Mapping[str, Any],
    metadata: Mapping[str, str],
) -> dict[str, Any]:
    with ParquetBatchWriter(
        root / table_name,
        contract,
        table_name,
        batch_rows=int(config["runtime"]["parquet_batch_rows"]),
        compression=str(config["runtime"]["parquet_compression"]),
        compression_level=int(config["runtime"]["parquet_compression_level"]),
        extra_metadata=metadata,
    ) as writer:
        writer.extend(rows)
    return writer.summary()


def _verify_inputs(
    *, project_root: Path, config: Mapping[str, Any], verify_hashes: bool
) -> tuple[dict[str, Any], dict[str, list[Path]], dict[str, Path]]:
    inputs = config["inputs"]
    document_keys = (
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
    for key in document_keys:
        path = resolve_inside(project_root, str(inputs[key]), project_root, strict=True)
        paths[key] = path
        if verify_hashes:
            documents[key] = require_hash(path, str(inputs[f"{key}_sha256"]))
        else:
            documents[key] = {
                "path": path.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": "smoke_skipped",
            }

    parent_manifest = load_json(paths["parent_canonical_manifest"])
    pre_split_manifest = load_json(paths["pre_split_canonical_manifest"])
    pre_split_run = load_json(paths["pre_split_run_manifest"])
    pre_split_report = load_json(paths["pre_split_audit_report"])
    pre_split_validation = load_json(paths["pre_split_validation_report"])
    gate = load_yaml(paths["active_gate"])
    policy = load_yaml(paths["benchmark_estimand_policy"])
    if (
        parent_manifest.get("status") != "complete"
        or pre_split_manifest.get("status") != "complete"
        or pre_split_run.get("status") != "complete"
        or pre_split_report.get("status") != "complete"
        or pre_split_validation.get("status") != "pass"
    ):
        raise RuntimeError("An accepted parent artifact is not complete and passing")
    forbidden_parent_true = (
        "candidate_pair_materialization_performed",
        "negative_label_construction_performed",
        "pseudo_negative_sampling_performed",
        "structural_mapping_performed",
        "model_work_performed",
        "external_panel_inputs_used",
    )
    if any(pre_split_manifest.get(name) is not False for name in forbidden_parent_true):
        raise RuntimeError("The accepted pre-split parent no longer preserves its scope")
    split_gate = gate.get("gates", {}).get("evidence", {}).get(
        "final_benchmark_component_split", {}
    )
    if (
        split_gate.get("status") != "authorized_not_executed"
        or split_gate.get("fail_closed") is not True
        or split_gate.get("primary_hard_partition_rule") != "local_domain_union_30"
        or split_gate.get("fallback_hard_partition_rule") != "sensitive_fl80_union_30"
        or split_gate.get("split_skeleton_freeze_authorized") is not True
        or split_gate.get("model_work_authorized") is not False
    ):
        raise RuntimeError("Active governance gate does not authorize this exact split")
    if (
        policy.get("status") != "accepted_effective"
        or policy.get("primary_design", {}).get("task")
        != "reference_sequence_positive_unlabeled_ranking"
    ):
        raise RuntimeError("Accepted PU-R policy is absent")

    parent_root = resolve_inside(
        project_root,
        str(inputs["parent_canonical_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    reconciliation_manifest = load_json(paths["primary_reconciliation_manifest"])
    reconciliation_root = resolve_inside(
        project_root,
        str(inputs["primary_reconciliation_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    files: dict[str, list[Path]] = {}
    tables: dict[str, Any] = {}
    for key in (
        "eligible_reference_sequences",
        "space_iii_gene_eligibility",
        "sequence_component_assignments",
    ):
        table = str(config["parent_tables"][key])
        table_files, summary = verify_manifest_table(
            project_root=project_root,
            manifest=parent_manifest,
            table_name=table,
            expected_root=parent_root / table,
            verify_hashes=verify_hashes,
        )
        files[key] = table_files
        tables[key] = summary
    projection = str(config["parent_tables"]["huri_evidence_gene_pair_projections"])
    projection_files, summary = verify_manifest_table(
        project_root=project_root,
        manifest=reconciliation_manifest,
        table_name=projection,
        expected_root=reconciliation_root / projection,
        verify_hashes=verify_hashes,
    )
    files["huri_evidence_gene_pair_projections"] = projection_files
    tables["huri_evidence_gene_pair_projections"] = summary
    return {"documents": documents, "tables": tables}, files, paths


def _register_views(
    connection: duckdb.DuckDBPyConnection,
    table_files: Mapping[str, Sequence[Path]],
) -> None:
    for view, paths in table_files.items():
        connection.read_parquet([path.as_posix() for path in paths]).create_view(view)


def _load_parent_state(
    connection: duckdb.DuckDBPyConnection, config: Mapping[str, Any]
) -> tuple[list[str], dict[str, int]]:
    expected = config["frozen_parent_expectations"]
    rows = connection.execute(
        "SELECT reference_sequence_sha256, sequence_length "
        "FROM eligible_reference_sequences ORDER BY reference_sequence_sha256"
    ).fetchall()
    nodes = [str(row[0]) for row in rows]
    lengths = {str(row[0]): int(row[1]) for row in rows}
    if len(nodes) != int(expected["eligible_reference_sequences"]) or len(set(nodes)) != len(nodes):
        raise RuntimeError("Frozen eligible endpoint inventory differs from DEC-0018")

    memberships: dict[int, dict[str, str]] = defaultdict(dict)
    sizes: dict[int, dict[str, int]] = defaultdict(dict)
    for threshold, endpoint, component, size in connection.execute(
        "SELECT identity_threshold_percent, reference_sequence_sha256, component_id, component_size "
        "FROM sequence_component_assignments ORDER BY identity_threshold_percent, reference_sequence_sha256"
    ).fetchall():
        threshold = int(threshold)
        endpoint = str(endpoint)
        component = str(component)
        if endpoint in memberships[threshold]:
            raise RuntimeError("Duplicate accepted component assignment")
        memberships[threshold][endpoint] = component
        if component in sizes[threshold] and sizes[threshold][component] != int(size):
            raise RuntimeError("Accepted component size is inconsistent")
        sizes[threshold][component] = int(size)
    for threshold, expected_count in expected["accepted_component_counts"].items():
        threshold = int(threshold)
        if set(memberships[threshold]) != set(nodes):
            raise RuntimeError(f"Accepted {threshold}% membership is incomplete")
        if len(sizes[threshold]) != int(expected_count):
            raise RuntimeError(f"Accepted {threshold}% component count differs")
        if dict(Counter(memberships[threshold].values())) != sizes[threshold]:
            raise RuntimeError(f"Accepted {threshold}% component sizes differ")
    return nodes, lengths


def _load_positive_pairs(
    connection: duckdb.DuckDBPyConnection, config: Mapping[str, Any]
) -> tuple[dict[str, set[tuple[str, str]]], dict[tuple[str, str], frozenset[str]]]:
    mapping: dict[str, str | None] = {}
    for gene, selected, usable in connection.execute(
        "SELECT ensembl_gene_id, selected_sequence_sha256, eligibility_usable "
        "FROM space_iii_gene_eligibility"
    ).fetchall():
        mapping[str(gene)] = str(selected) if bool(usable) and selected is not None else None
    expected = config["frozen_parent_expectations"]
    if sum(value is not None for value in mapping.values()) != int(expected["eligible_space_iii_genes"]):
        raise RuntimeError("Frozen eligible gene mapping differs from DEC-0018")

    pairs = {"HI-II-14": set(), "HuRI": set()}
    for source, unique, raw_a, raw_b, label_authorized in connection.execute(
        "SELECT source_dataset, unique_gene_pair, gene_a, gene_b, label_authorized "
        "FROM huri_evidence_gene_pair_projections"
    ).fetchall():
        source = str(source)
        if source not in pairs or bool(label_authorized):
            raise RuntimeError("Released-positive projection is outside the accepted scope")
        if not bool(unique) or raw_a is None or raw_b is None:
            continue
        sequence_a = mapping.get(str(raw_a))
        sequence_b = mapping.get(str(raw_b))
        if sequence_a is None or sequence_b is None or sequence_a == sequence_b:
            continue
        pairs[source].add(tuple(sorted((sequence_a, sequence_b))))
    pairs["ALL"] = pairs["HI-II-14"] | pairs["HuRI"]
    for source, key in (
        ("ALL", "distinct_positive_pairs_all"),
        ("HI-II-14", "distinct_positive_pairs_hi_ii_14"),
        ("HuRI", "distinct_positive_pairs_huri"),
    ):
        if len(pairs[source]) != int(expected[key]):
            raise RuntimeError(f"Frozen {source} released-positive count differs")
    endpoints = {endpoint for pair in pairs["ALL"] for endpoint in pair}
    if len(endpoints) != int(expected["positive_endpoint_sequences_all"]):
        raise RuntimeError("Frozen positive-exposed endpoint count differs")
    pair_sources = {
        pair: frozenset(source for source in ("HI-II-14", "HuRI") if pair in pairs[source])
        for pair in pairs["ALL"]
    }
    return pairs, pair_sources


def _edge_set(path: Path, threshold: float) -> set[tuple[str, str]]:
    rows = pq.read_table(
        path, columns=["sequence_a_sha256", "sequence_b_sha256", "maximum_identity"]
    ).to_pylist()
    return {
        tuple(sorted((str(row["sequence_a_sha256"]), str(row["sequence_b_sha256"]))))
        for row in rows
        if float(row["maximum_identity"]) + 1e-12 >= threshold
        and str(row["sequence_a_sha256"]) != str(row["sequence_b_sha256"])
    }


def _load_graphs(
    *, nodes: Sequence[str], paths: Mapping[str, Path], config: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    expected = config["frozen_parent_expectations"]
    accepted = _edge_set(paths["parent_normalized_edges"], 0.30)
    if len(accepted) != int(expected["accepted_normalized_edge_counts"][30]):
        raise RuntimeError("Accepted 30% edge count differs")
    full = _edge_set(paths["full_length_sensitivity_edges"], 0.30)
    local = _edge_set(paths["local_domain_sensitivity_edges"], 0.30)
    sensitive_union = accepted | full
    local_union = sensitive_union | local
    graphs: dict[str, dict[str, Any]] = {}
    for definition, edges in (
        ("sensitive_fl80_union", sensitive_union),
        ("local_domain_union", local_union),
    ):
        memberships, sizes = deterministic_components(nodes, edges)
        expected_graph = expected[definition + "_30"]
        if (
            len(edges) != int(expected_graph["edge_count"])
            or len(sizes) != int(expected_graph["component_count"])
            or max(sizes.values()) != int(expected_graph["largest_component_size"])
        ):
            raise RuntimeError(f"Accepted {definition} graph differs from DEC-0020")
        graphs[definition] = {
            "edges": edges,
            "memberships": memberships,
            "sizes": sizes,
        }
    if not sensitive_union.issubset(local_union):
        raise RuntimeError("Local/domain union removed a full-length edge")
    return graphs


def _source_pair_masks(prepared: Any) -> dict[str, np.ndarray]:
    return {
        "ALL": np.ones(len(prepared.pair_endpoint_a), dtype=bool),
        "HI-II-14": prepared.hi_mask,
        "HuRI": prepared.huri_mask,
    }


def _selected_tables(
    *,
    nodes: Sequence[str],
    lengths: Mapping[str, int],
    pairs_by_source: Mapping[str, set[tuple[str, str]]],
    graphs: Mapping[str, Mapping[str, Any]],
    selected_definition: str,
    selected_search: Mapping[str, Any],
    primary_search: Mapping[str, Any],
    fallback_search: Mapping[str, Any] | None,
    prepared: Any,
    config: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    split_id = str(config["split_id"])
    scale = int(config["allocation"]["score_quantization_scale"])
    assignments = selected_search["selected_assignments"]
    evaluation = selected_search["selected_evaluation"]
    if assignments is None or evaluation is None:
        raise RuntimeError("No valid selected allocation")
    memberships = graphs[selected_definition]["memberships"]
    sizes = graphs[selected_definition]["sizes"]
    representatives = list(prepared.component_representatives)
    component_ids = {
        representative: component_id(
            split_id, selected_definition, 30, representative, int(sizes[representative])
        )
        for representative in representatives
    }
    component_index = {component: index for index, component in enumerate(representatives)}
    selected_index = int(evaluation["candidate_index"])
    component_rows = [
        {
            "split_id": split_id,
            "leakage_definition": selected_definition,
            "identity_threshold_percent": 30,
            "component_id": component_ids[representative],
            "component_representative_sha256": representative,
            "component_size": int(sizes[representative]),
            "partition": PARTITIONS[int(assignments[component_index[representative]])],
            "selected_candidate_index": selected_index,
            "pair_rows_emitted": False,
            "model_output_used": False,
        }
        for representative in representatives
    ]
    endpoint_rows = []
    for endpoint in sorted(nodes):
        representative = memberships[endpoint]
        partition = PARTITIONS[int(assignments[component_index[representative]])]
        endpoint_rows.append(
            {
                "split_id": split_id,
                "reference_sequence_sha256": endpoint,
                "sequence_length": int(lengths[endpoint]),
                "component_id": component_ids[representative],
                "component_size": int(sizes[representative]),
                "partition": partition,
                "interaction_supervision_eligible": partition == "train",
                "exact_endpoint_absent_from_interaction_supervised_training": partition != "train",
                "pair_level_c1_c2_c3_label_assigned": False,
            }
        )

    masks, node_partitions, _ = opportunity_masks(prepared, assignments)
    pair_part_a = node_partitions[prepared.pair_endpoint_a]
    pair_part_b = node_partitions[prepared.pair_endpoint_b]
    source_masks = _source_pair_masks(prepared)
    targets = config["allocation"]["target_endpoint_fractions"]
    total_degree = int(prepared.all_degrees.sum())
    partition_rows = []
    for code, partition in enumerate(PARTITIONS):
        endpoint_mask = node_partitions == code
        component_mask = assignments == code
        internal = (pair_part_a == code) & (pair_part_b == code)
        component_sizes_here = [
            int(sizes[representatives[index]])
            for index in np.flatnonzero(component_mask)
        ]
        partition_rows.append(
            {
                "split_id": split_id,
                "partition": partition,
                "target_endpoint_fraction": float(targets[partition]),
                "endpoint_count": int(np.count_nonzero(endpoint_mask)),
                "endpoint_fraction": float(np.count_nonzero(endpoint_mask) / len(nodes)),
                "absolute_target_fraction_deviation": abs(
                    np.count_nonzero(endpoint_mask) / len(nodes) - float(targets[partition])
                ),
                "component_count": int(np.count_nonzero(component_mask)),
                "singleton_component_count": sum(value == 1 for value in component_sizes_here),
                "largest_component_size": max(component_sizes_here, default=0),
                "positive_exposed_endpoint_count": int(
                    np.count_nonzero(prepared.all_degrees[endpoint_mask] > 0)
                ),
                "internal_positive_pairs_all": int(np.count_nonzero(internal)),
                "internal_positive_pairs_hi_ii_14": int(np.count_nonzero(internal & prepared.hi_mask)),
                "internal_positive_pairs_huri": int(np.count_nonzero(internal & prepared.huri_mask)),
                "positive_degree_sum_all": int(prepared.all_degrees[endpoint_mask].sum()),
                "positive_degree_mass_fraction_all": float(
                    prepared.all_degrees[endpoint_mask].sum() / total_degree
                ),
            }
        )

    degree_rows = []
    for source in SOURCES:
        source_mask = source_masks[source]
        degrees = np.bincount(
            np.concatenate(
                (
                    prepared.pair_endpoint_a[source_mask],
                    prepared.pair_endpoint_b[source_mask],
                )
            ),
            minlength=len(nodes),
        ).astype(np.int64)
        ranked = np.array(
            sorted(range(len(nodes)), key=lambda index: (-int(degrees[index]), prepared.nodes[index])),
            dtype=np.int64,
        )
        total = int(degrees.sum())
        hubs = {
            fraction: ranked[: max(1, math.ceil(fraction * len(nodes)))]
            for fraction in (0.01, 0.05, 0.10)
        }
        for code, partition in enumerate(PARTITIONS):
            endpoint_mask = node_partitions == code
            values = [int(value) for value in degrees[endpoint_mask]]
            hub_counts = {
                fraction: int(np.count_nonzero(node_partitions[indices] == code))
                for fraction, indices in hubs.items()
            }
            degree_rows.append(
                {
                    "split_id": split_id,
                    "partition": partition,
                    "source_dataset": source,
                    "endpoint_count": len(values),
                    "positive_exposed_endpoint_count": sum(value > 0 for value in values),
                    "positive_pair_count_global": int(np.count_nonzero(source_mask)),
                    "degree_sum": sum(values),
                    "degree_mass_fraction": float(sum(values) / total),
                    "degree_q50": nearest_rank(values, 0.50),
                    "degree_q90": nearest_rank(values, 0.90),
                    "degree_q95": nearest_rank(values, 0.95),
                    "degree_q99": nearest_rank(values, 0.99),
                    "maximum_degree": max(values, default=0),
                    "top_1_percent_global_hub_endpoint_count": hub_counts[0.01],
                    "top_1_percent_global_hub_endpoint_fraction": hub_counts[0.01] / len(hubs[0.01]),
                    "top_5_percent_global_hub_endpoint_count": hub_counts[0.05],
                    "top_5_percent_global_hub_endpoint_fraction": hub_counts[0.05] / len(hubs[0.05]),
                    "top_10_percent_global_hub_endpoint_count": hub_counts[0.10],
                    "top_10_percent_global_hub_endpoint_fraction": hub_counts[0.10] / len(hubs[0.10]),
                    "degree_histogram_json": degree_histogram(values),
                    "endpoint_metric_rows_emitted": False,
                }
            )

    opportunity_rows = []
    for pool in POOL_KEYS:
        axis, evaluation_partition = pool.split(":", 1)
        base_mask = masks[pool]
        for source in SOURCES:
            mask = base_mask & source_masks[source]
            endpoint_indices = np.unique(
                np.concatenate(
                    (
                        prepared.pair_endpoint_a[mask],
                        prepared.pair_endpoint_b[mask],
                    )
                )
            ) if np.any(mask) else np.array([], dtype=np.int64)
            component_indices = np.unique(prepared.node_components[endpoint_indices])
            opportunity_rows.append(
                {
                    "split_id": split_id,
                    "opportunity_axis": axis,
                    "evaluation_partition": evaluation_partition,
                    "source_dataset": source,
                    "released_positive_pair_count": int(np.count_nonzero(mask)),
                    "participating_endpoint_count": int(endpoint_indices.size),
                    "participating_component_count": int(component_indices.size),
                    "exact_heldout_endpoints_absent_from_interaction_supervised_training": axis == "C3",
                    "component_disjoint_from_training_under_selected_rule": axis == "C3",
                    "pair_rows_emitted": False,
                    "pair_level_label_assigned": False,
                }
            )

    endpoint_partition = {
        endpoint: PARTITIONS[int(node_partitions[index])]
        for index, endpoint in enumerate(prepared.nodes)
    }
    leakage_rows = []
    for definition in ("local_domain_union", "sensitive_fl80_union"):
        graph = graphs[definition]
        cross_edges = sum(
            endpoint_partition[a] != endpoint_partition[b] for a, b in graph["edges"]
        )
        component_partitions: dict[str, set[str]] = defaultdict(set)
        for endpoint, representative in graph["memberships"].items():
            component_partitions[representative].add(endpoint_partition[endpoint])
        crossing_components = sum(len(value) > 1 for value in component_partitions.values())
        leakage_rows.append(
            {
                "split_id": split_id,
                "leakage_definition": definition,
                "identity_threshold_percent": 30,
                "selected_as_hard_partition_rule": definition == selected_definition,
                "fallback_definition": definition == "sensitive_fl80_union",
                "graph_edge_count": len(graph["edges"]),
                "graph_component_count": len(graph["sizes"]),
                "largest_graph_component_size": max(graph["sizes"].values()),
                "cross_partition_edge_count": cross_edges,
                "cross_partition_component_count": crossing_components,
                "partition_disjoint": cross_edges == 0 and crossing_components == 0,
                "exhaustive_homology_claim_supported": False,
            }
        )
    if selected_definition == "local_domain_union" and any(
        row["cross_partition_edge_count"] != 0
        or row["cross_partition_component_count"] != 0
        for row in leakage_rows
    ):
        raise RuntimeError("Primary allocation is not disjoint under both frozen graphs")
    if selected_definition == "sensitive_fl80_union" and next(
        row for row in leakage_rows if row["leakage_definition"] == selected_definition
    )["cross_partition_edge_count"] != 0:
        raise RuntimeError("Fallback allocation crosses its hard graph")

    primary_failure = dict(primary_search["failure_counts"])
    fallback_failure = dict(fallback_search["failure_counts"]) if fallback_search else {}
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
    selection_row = {
        "split_id": split_id,
        "selection_status": "primary_selected" if selected_definition == "local_domain_union" else "fallback_selected",
        "primary_leakage_definition": "local_domain_union",
        "fallback_leakage_definition": "sensitive_fl80_union",
        "candidate_count_per_definition": int(config["allocation"]["candidate_count_per_definition"]),
        "primary_candidates_evaluated": int(primary_search["candidate_count"]),
        "primary_valid_candidate_count": int(primary_search["valid_candidate_count"]),
        "primary_failure_counts_json": canonical_json(primary_failure),
        "fallback_evaluated": fallback_search is not None,
        "fallback_trigger_reason": (
            "not_evaluated_primary_has_valid_candidates"
            if fallback_search is None
            else "zero_primary_candidates_passed_all_frozen_criteria"
        ),
        "fallback_candidates_evaluated": int(fallback_search["candidate_count"]) if fallback_search else 0,
        "fallback_valid_candidate_count": int(fallback_search["valid_candidate_count"]) if fallback_search else 0,
        "fallback_failure_counts_json": canonical_json(fallback_failure),
        "selected_leakage_definition": selected_definition,
        "selected_candidate_index": selected_index,
        "selected_score_json": canonical_json(dict(zip(score_names, map(int, evaluation["score"])))),
        "frozen_objective_json": canonical_json(config["allocation"]["frozen_selection_objective"]),
        "deterministic_seed": str(config["allocation"]["deterministic_seed"]),
        "tie_breaking_json": canonical_json(
            {
                "component_order": config["allocation"]["candidate_component_order"],
                "partition_order": config["allocation"]["partition_iteration_and_tie_order"],
                "relative_deficit": config["allocation"]["relative_deficit_tie_break"],
                "final": "minimum_candidate_index",
            }
        ),
        "target_endpoint_fractions_json": canonical_json(config["allocation"]["target_endpoint_fractions"]),
        "maximum_absolute_endpoint_fraction_deviation": float(config["acceptance_criteria"]["maximum_absolute_endpoint_fraction_deviation"]),
        "selected_maximum_endpoint_fraction_deviation": evaluation["maximum_endpoint_deviation_units"] / scale,
        "selected_minimum_normalized_evidence_ratio": evaluation["minimum_evidence_ratio_units"] / scale,
        "selected_maximum_source_presence_fraction_deviation": evaluation["maximum_source_deviation_units"] / scale,
        "selected_maximum_heldout_axis_relative_imbalance": evaluation["maximum_heldout_imbalance_units"] / scale,
        "selected_maximum_degree_mass_fraction_deviation": evaluation["maximum_degree_deviation_units"] / scale,
        "selected_maximum_hub_endpoint_fraction_deviation": evaluation["maximum_hub_deviation_units"] / scale,
        "future_model_results_inspected": False,
        "split_frozen": True,
    }

    operational_wording = (
        "Both exact frozen reference-sequence endpoints were absent from interaction-supervised "
        f"training and component-disjoint from training under {selected_definition}_v1 at 30% identity."
    )
    prohibited_claims = {
        "unseen_biological_family": "unseen family, novel family, or biological-family generalization",
        "plm_unseen_protein": "the pretrained language model had not encountered either protein",
        "exhaustive_absence_of_homology": "proven nonhomology or exhaustively homology-free",
        "universal_nonbinding": "unreported or panel pairs are universal nonbinders",
        "prevalence": "interaction prevalence in the eligible candidate universe",
        "calibrated_probability": "calibrated interaction probability",
    }
    claim_rows = [
        {
            "split_id": split_id,
            "claim_name": "exact_endpoint_component_disjoint_c3",
            "claim_status": "permitted_with_exact_operational_qualifier",
            "supported_by_split": True,
            "permitted_wording": operational_wording,
            "prohibited_wording": "unseen family, unseen homolog/domain, or PLM-unseen protein",
            "rationale": "Held-out endpoints are excluded from interaction supervision and their hard-rule components do not cross training.",
            "model_performance_claimed": False,
            "prevalence_claimed": False,
            "calibration_claimed": False,
        }
    ]
    for name, wording in prohibited_claims.items():
        claim_rows.append(
            {
                "split_id": split_id,
                "claim_name": name,
                "claim_status": "prohibited",
                "supported_by_split": False,
                "permitted_wording": operational_wording if name in {"unseen_biological_family", "plm_unseen_protein", "exhaustive_absence_of_homology"} else "none",
                "prohibited_wording": wording,
                "rationale": "The component skeleton, released-positive evidence, and heuristic similarity graphs do not identify this estimand or exposure state.",
                "model_performance_claimed": False,
                "prevalence_claimed": False,
                "calibration_claimed": False,
            }
        )

    return {
        "component_partition_assignments": sorted(component_rows, key=lambda row: row["component_id"]),
        "endpoint_partition_assignments": endpoint_rows,
        "partition_summaries": partition_rows,
        "partition_degree_summaries": sorted(degree_rows, key=lambda row: (row["partition"], row["source_dataset"])),
        "opportunity_summaries": sorted(opportunity_rows, key=lambda row: (row["opportunity_axis"], row["evaluation_partition"], row["source_dataset"])),
        "leakage_validation_summaries": sorted(leakage_rows, key=lambda row: row["leakage_definition"]),
        "selection_summaries": [selection_row],
        "claim_assessments": sorted(claim_rows, key=lambda row: row["claim_name"]),
    }


def run_split(
    *,
    project_root: Path,
    config_path: Path,
    run_root: Path | None = None,
    canonical_root: Path | None = None,
    report_path: Path | None = None,
    allow_dirty: bool = False,
    skip_input_hashes: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    started_at = _timestamp()
    config_path = resolve_inside(project_root, config_path, project_root / "configs", strict=True)
    config = load_yaml(config_path)
    validate_config(config)
    run_target = resolve_inside(
        project_root,
        run_root or str(config["outputs"]["run_root"]),
        project_root / "artifacts/runs",
        strict=False,
    )
    canonical_target = resolve_inside(
        project_root,
        canonical_root or str(config["outputs"]["canonical_root"]),
        project_root / "data/canonical",
        strict=False,
    )
    report_target = resolve_inside(
        project_root,
        report_path or str(config["outputs"]["audit_report"]),
        project_root / "artifacts/validation",
        strict=False,
    )
    smoke = require_output_paths(
        run_root=run_target,
        canonical_root=canonical_target,
        report_path=report_target,
        allow_dirty=allow_dirty,
        skip_input_hashes=skip_input_hashes,
    )
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production component split requires a clean Git worktree")
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    if active_container != expected_container:
        raise RuntimeError("Active Apptainer image differs from the split configuration")
    container_sha = sha256_file(active_container)
    if container_sha != str(config["runtime"]["container_sha256"]):
        raise RuntimeError("Active container hash differs from the split configuration")
    if platform.machine() != str(config["runtime"]["architecture"]):
        raise RuntimeError("Component split is running on the wrong architecture")

    verified_inputs, table_files, paths = _verify_inputs(
        project_root=project_root, config=config, verify_hashes=not skip_input_hashes
    )
    connection = duckdb.connect(":memory:")
    connection.execute(f"SET memory_limit='{str(config['runtime']['duckdb_memory_limit'])}'")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    connection.execute("PRAGMA disable_progress_bar")
    try:
        _register_views(connection, table_files)
        nodes, lengths = _load_parent_state(connection, config)
        pairs_by_source, pair_sources = _load_positive_pairs(connection, config)
    finally:
        connection.close()
    graphs = _load_graphs(nodes=nodes, paths=paths, config=config)

    primary_definition = str(config["leakage_partition_policy"]["primary_hard_rule"]["id"])
    primary_graph = graphs[primary_definition]
    primary_prepared = prepare_allocation(
        nodes=nodes,
        memberships=primary_graph["memberships"],
        component_sizes=primary_graph["sizes"],
        positive_pairs=pairs_by_source["ALL"],
        pair_sources=pair_sources,
        hub_fractions=config["acceptance_criteria"]["global_hub_fractions"],
    )
    primary_search = search_allocations(
        prepared=primary_prepared, definition=primary_definition, config=config
    )
    fallback_search = None
    selected_definition = primary_definition
    selected_search = primary_search
    selected_prepared = primary_prepared
    if int(primary_search["valid_candidate_count"]) == 0:
        fallback_definition = str(config["leakage_partition_policy"]["fallback_hard_rule"]["id"])
        fallback_graph = graphs[fallback_definition]
        fallback_prepared = prepare_allocation(
            nodes=nodes,
            memberships=fallback_graph["memberships"],
            component_sizes=fallback_graph["sizes"],
            positive_pairs=pairs_by_source["ALL"],
            pair_sources=pair_sources,
            hub_fractions=config["acceptance_criteria"]["global_hub_fractions"],
        )
        fallback_search = search_allocations(
            prepared=fallback_prepared, definition=fallback_definition, config=config
        )
        if int(fallback_search["valid_candidate_count"]) == 0:
            raise RuntimeError(
                "No primary or fallback allocation satisfies every frozen acceptance criterion"
            )
        selected_definition = fallback_definition
        selected_search = fallback_search
        selected_prepared = fallback_prepared

    table_rows = _selected_tables(
        nodes=nodes,
        lengths=lengths,
        pairs_by_source=pairs_by_source,
        graphs=graphs,
        selected_definition=selected_definition,
        selected_search=selected_search,
        primary_search=primary_search,
        fallback_search=fallback_search,
        prepared=selected_prepared,
        config=config,
    )
    aggregate_metrics = {
        table: table_rows[table]
        for table in TABLES
        if table not in {"component_partition_assignments", "endpoint_partition_assignments"}
    }
    row_counts = {table: len(rows) for table, rows in table_rows.items()}
    runtime = {
        "container_sif_sha256": container_sha,
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "duckdb": duckdb.__version__,
        "pyarrow": pyarrow.__version__,
        "numpy": np.__version__,
    }

    with AtomicDatasetDirectory(run_target) as temporary_run:
        selection_execution = {
            "schema_version": 1,
            "split_id": config["split_id"],
            "primary_definition": primary_definition,
            "primary_candidates_evaluated": primary_search["candidate_count"],
            "primary_valid_candidate_count": primary_search["valid_candidate_count"],
            "primary_failure_counts": primary_search["failure_counts"],
            "fallback_evaluated": fallback_search is not None,
            "fallback_candidates_evaluated": fallback_search["candidate_count"] if fallback_search else 0,
            "fallback_valid_candidate_count": fallback_search["valid_candidate_count"] if fallback_search else 0,
            "fallback_failure_counts": fallback_search["failure_counts"] if fallback_search else {},
            "selected_definition": selected_definition,
            "selected_candidate_index": selected_search["selected_evaluation"]["candidate_index"],
            "selected_score": list(map(int, selected_search["selected_evaluation"]["score"])),
            "future_model_results_inspected": False,
            "candidate_pair_rows_emitted": False,
            "positive_pair_rows_emitted": False,
            "pair_level_c1_c2_c3_rows_emitted": False,
        }
        write_json(temporary_run / "SELECTION_EXECUTION.json", selection_execution)
        run_files = artifact_inventory(temporary_run, run_target)
        run_manifest = {
            "schema_version": 1,
            "split_id": config["split_id"],
            "split_version": SPLIT_VERSION,
            "status": "complete",
            "scope": "model_free_component_and_endpoint_partition_skeleton",
            "started_at_utc": started_at,
            "completed_at_utc": _timestamp(),
            "git": git,
            "runtime": runtime,
            "config": {
                "path": config_path.relative_to(project_root).as_posix(),
                "sha256": sha256_file(config_path),
            },
            "files": run_files,
            "selection_execution": selection_execution,
            "candidate_pair_materialization_performed": False,
            "positive_pair_rows_emitted": False,
            "negative_label_construction_performed": False,
            "pseudo_negative_sampling_performed": False,
            "pair_level_c1_c2_c3_assignment_performed": False,
            "endpoint_component_split_constructed": True,
            "external_panel_inputs_used": False,
            "structural_mapping_performed": False,
            "model_work_performed": False,
        }
        run_manifest_sha = write_manifest(temporary_run / "RUN_MANIFEST.json", run_manifest)
        make_read_only(temporary_run)

    contract = load_contract(paths["split_schema"])
    metadata = {
        "split_version": SPLIT_VERSION,
        "split_git_commit": str(git["commit"]),
        "container_sif_sha256": container_sha,
        "primary_design": "reference_sequence_positive_unlabeled_ranking",
        "selected_leakage_definition": selected_definition,
        "model_output_used": "false",
    }
    with AtomicDatasetDirectory(canonical_target) as temporary_canonical:
        summaries = {
            table: _write_table(
                root=temporary_canonical,
                table_name=table,
                rows=table_rows[table],
                contract=contract,
                config=config,
                metadata=metadata,
            )
            for table in TABLES
        }
        summaries = replace_prefix(
            summaries, temporary_canonical.as_posix(), canonical_target.as_posix()
        )
        split_manifest = {
            "schema_version": 1,
            "split_id": config["split_id"],
            "split_version": SPLIT_VERSION,
            "status": "complete_frozen",
            "scope": "endpoint_component_partition_skeleton_and_aggregate_positive_opportunities",
            "completed_at_utc": _timestamp(),
            "git": git,
            "runtime": runtime,
            "inputs": {
                "config": config_path.relative_to(project_root).as_posix(),
                "config_sha256": sha256_file(config_path),
                **verified_inputs,
                "run_manifest": (run_target / "RUN_MANIFEST.json").as_posix(),
                "run_manifest_sha256": run_manifest_sha,
            },
            "tables": summaries,
            "row_counts": row_counts,
            "aggregate_metrics": aggregate_metrics,
            "primary_design": "reference_sequence_positive_unlabeled_ranking",
            "selected_leakage_definition": selected_definition,
            "identity_threshold_percent": 30,
            "split_frozen": True,
            "parent_audits_modified_or_recomputed": False,
            "candidate_pair_materialization_performed": False,
            "positive_pair_rows_emitted": False,
            "evidence_indicator_construction_performed": False,
            "negative_label_construction_performed": False,
            "pseudo_negative_sampling_performed": False,
            "pair_level_c1_c2_c3_assignment_performed": False,
            "endpoint_component_split_constructed": True,
            "external_panel_inputs_used": False,
            "structural_mapping_performed": False,
            "model_work_performed": False,
            "prevalence_estimation_performed": False,
            "calibration_performed": False,
            "return_to_governance_required": True,
        }
        split_manifest_sha = write_manifest(
            temporary_canonical / "SPLIT_MANIFEST.json", split_manifest
        )
        make_read_only(temporary_canonical)

    report = {
        "schema_version": 1,
        "split_id": config["split_id"],
        "split_version": SPLIT_VERSION,
        "task": config["task"],
        "status": "complete_frozen",
        "scope": "qualification_smoke" if smoke else "production_full",
        "started_at_utc": started_at,
        "completed_at_utc": _timestamp(),
        "git": git,
        "runtime": runtime,
        "inputs": {
            "config": config_path.relative_to(project_root).as_posix(),
            "config_sha256": sha256_file(config_path),
            **verified_inputs,
        },
        "outputs": {
            "run_manifest": (run_target / "RUN_MANIFEST.json").as_posix(),
            "run_manifest_sha256": run_manifest_sha,
            "split_manifest": (canonical_target / "SPLIT_MANIFEST.json").as_posix(),
            "split_manifest_sha256": split_manifest_sha,
            "candidate_pair_rows": "not_materialized",
            "positive_pair_rows": "not_emitted",
            "pair_level_c1_c2_c3_rows": "not_emitted",
            "endpoint_partition_rows": row_counts["endpoint_partition_assignments"],
            "component_partition_rows": row_counts["component_partition_assignments"],
        },
        "row_counts": row_counts,
        "aggregate_metrics": aggregate_metrics,
        "scientific_interpretation": {
            "primary_design_preserved": "reference_sequence_positive_unlabeled_ranking",
            "selected_leakage_definition": selected_definition,
            "fallback_evaluated": fallback_search is not None,
            "exact_endpoint_component_disjoint_c3_only": True,
            "unseen_biological_family_claim_supported": False,
            "plm_unseen_protein_claim_supported": False,
            "exhaustive_nonhomology_claim_supported": False,
            "unreported_eligible_pairs_remain_unlabeled": True,
            "external_panel_outcomes_used": False,
            "prevalence_identified": False,
            "calibration_performed": False,
            "model_results_inspected": False,
            "model_performance_evaluated": False,
        },
        "authorizations": {
            "endpoint_component_split_skeleton": True,
            "candidate_pair_materialization": False,
            "positive_pair_row_output": False,
            "negative_label_construction": False,
            "pseudo_negative_sampling": False,
            "pair_level_c1_c2_c3_assignment": False,
            "external_panel_integration": False,
            "structural_mapping": False,
            "model_work": False,
            "return_to_governance_required": True,
        },
    }
    _write_report(report_target, report, project_root)
    return report


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
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--skip-input-hashes", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path(__file__))
    report = run_split(
        project_root=project_root,
        config_path=args.config,
        run_root=args.run_root,
        canonical_root=args.canonical_root,
        report_path=args.audit_report,
        allow_dirty=args.allow_dirty,
        skip_input_hashes=args.skip_input_hashes,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
