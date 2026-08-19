"""Production audit and hash registry for a completed development evaluation."""

from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import numpy as np
import pyarrow.parquet as pq
import yaml

from .evaluation import (
    _load_bootstrap,
    _read_cell,
    apply_selection_and_kill_rules,
    c1_novel_u_metrics,
    degree_and_hub_diagnostics,
    point_metrics,
    score_correlations,
)
from .release import sha256_file
from .scoring import DEVELOPMENT_CELLS, scorer_records
from .semantics import (
    DETERMINISTIC_SCORERS,
    PRIMARY_CELLS,
    component_draws,
    frozen_hub_sets,
    percentile_95,
)


PAIR_ID_PATTERN = re.compile(r"pair:[0-9a-f]{64}")


def _check(
    checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any
) -> None:
    checks.append(
        {"check_id": check_id, "status": "pass" if condition else "fail", "detail": detail}
    )


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite completed-evaluation evidence: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def contains_public_pair_identity(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return PAIR_ID_PATTERN.search(text) is not None or any(
        token in text
        for token in (
            '"endpoint_a_sha256"',
            '"endpoint_b_sha256"',
            '"candidate_token"',
        )
    )


def ensemble_columns_exact(
    scores: np.ndarray,
    scorer_index: Mapping[str, int],
    ensembles: Sequence[Mapping[str, Any]],
) -> bool:
    for ensemble in ensembles:
        candidate_id = str(ensemble["candidate_id"])
        member_columns = [
            scorer_index[str(member["run_id"])] for member in ensemble["members"]
        ]
        expected = np.mean(scores[:, member_columns], axis=1, dtype=np.float64)
        if not np.array_equal(expected, np.asarray(scores[:, scorer_index[candidate_id]])):
            return False
    return True


def _artifact_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def run_completed_audit(
    *,
    project_root: Path,
    config: Mapping[str, Any],
    production_source_commit: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    private_root = project_root / str(config["development_release"]["evaluation_root"])
    results_root = project_root / str(config["outputs"]["public_results_root"])
    scoring_manifest_path = private_root / "SCORING_RUN_MANIFEST.json"
    scoring_manifest = _load_json(scoring_manifest_path)
    result_manifest_path = results_root / "DEVELOPMENT_RESULTS_MANIFEST.json"
    result_manifest = _load_json(result_manifest_path)
    training_registry_path = project_root / str(config["frozen_inputs"]["training_registry"])
    training_registry = _load_json(training_registry_path)
    runs, ensembles, frozen_scorer_ids = scorer_records(training_registry)

    _check(
        checks,
        "complete_9_49_30_10_scoring_manifest_and_closed_boundaries",
        scoring_manifest.get("cell_count") == 9
        and scoring_manifest.get("scorer_count") == 49
        and scoring_manifest.get("selected_checkpoint_count") == 30
        and scoring_manifest.get("ensemble_count") == 10
        and scoring_manifest.get("training_or_checkpoint_change") is False
        and scoring_manifest.get("protected_candidates_accessed") is False
        and scoring_manifest.get("protected_truth_accessed") is False
        and [item["cell_id"] for item in scoring_manifest["cells"]]
        == list(DEVELOPMENT_CELLS)
        and len(runs) == 30
        and len(ensembles) == 10
        and len(frozen_scorer_ids) == 49,
        {
            "cells": scoring_manifest.get("cell_count"),
            "scorers": scoring_manifest.get("scorer_count"),
            "checkpoints": scoring_manifest.get("selected_checkpoint_count"),
            "ensembles": scoring_manifest.get("ensemble_count"),
        },
    )

    primary_payload = _load_json(results_root / "PRIMARY_METRICS.json")
    source_payload = _load_json(results_root / "SOURCE_EXCLUSIVE_METRICS.json")
    degree_payload = _load_json(results_root / "DEGREE_HUB_DIAGNOSTICS.json")
    correlation_payload = _load_json(results_root / "DIAGNOSTIC_CORRELATIONS.json")
    novel_payload = _load_json(results_root / "C1_NOVEL_U_SENSITIVITY.json")
    bootstrap_payload = _load_json(results_root / "BOOTSTRAP_REGISTRY.json")
    selection_payload = _load_json(results_root / "SELECTION_AND_KILL_TRACE.json")

    point_by_cell: dict[str, Any] = {}
    degree_by_cell: dict[str, Any] = {}
    bootstrap_by_cell: dict[str, tuple[list[str], np.ndarray]] = {}
    cell_registry: list[dict[str, Any]] = []
    c1_cache: tuple[Any, np.ndarray, list[str]] | None = None
    all_cell_files_ok = True
    all_scores_finite = True
    all_scorers_exact = True
    all_ensembles_exact = True
    all_point_metrics_exact = True
    total_rows = 0

    degree_by_training_endpoint: dict[str, int] = {}
    endpoint_partition_path = project_root / str(config["frozen_inputs"]["partitions"])
    partitions = pq.read_table(
        endpoint_partition_path,
        columns=["reference_sequence_sha256", "partition"],
    )
    training_positive = pq.read_table(
        project_root / str(config["frozen_inputs"]["training_positive"]),
        columns=["endpoint_a_sha256", "endpoint_b_sha256"],
    )
    degree_counts = Counter(
        map(
            str,
            training_positive["endpoint_a_sha256"].to_pylist()
            + training_positive["endpoint_b_sha256"].to_pylist(),
        )
    )
    for endpoint, partition in zip(
        partitions["reference_sequence_sha256"].to_pylist(),
        partitions["partition"].to_pylist(),
        strict=True,
    ):
        if str(partition) == "train":
            degree_by_training_endpoint[str(endpoint)] = int(degree_counts[str(endpoint)])
    hubs = frozen_hub_sets(degree_by_training_endpoint)

    run_cell_by_id = {str(item["cell_id"]): item for item in scoring_manifest["cells"]}
    for cell_id in DEVELOPMENT_CELLS:
        cell_root = private_root / "scores" / cell_id.replace(":", "__")
        disk_manifest_path = cell_root / "CELL_SCORE_MANIFEST.json"
        disk_manifest = _load_json(disk_manifest_path)
        rows, scores, scorer_ids, scorer_index = _read_cell(cell_root)
        all_cell_files_ok &= disk_manifest == run_cell_by_id[cell_id]
        all_scores_finite &= bool(np.isfinite(scores).all())
        all_scorers_exact &= scorer_ids == frozen_scorer_ids
        all_ensembles_exact &= ensemble_columns_exact(scores, scorer_index, ensembles)
        state_counts = Counter(map(str, rows["state"].to_pylist()))
        total_rows += rows.num_rows
        all_cell_files_ok &= (
            state_counts
            == Counter(
                {
                    "released_positive": int(disk_manifest["positive_rows"]),
                    "unlabeled": int(disk_manifest["unlabeled_rows"]),
                }
            )
            and rows.num_rows == int(disk_manifest["total_rows"])
        )
        observed_point = point_metrics(rows, scores, scorer_ids)
        point_by_cell[cell_id] = observed_point
        public_point = (
            primary_payload["cells"][cell_id]["metrics"]
            if cell_id in PRIMARY_CELLS
            else source_payload["cells"][cell_id]
        )
        all_point_metrics_exact &= observed_point == public_point
        if cell_id in PRIMARY_CELLS:
            observed_degree = degree_and_hub_diagnostics(
                rows=rows,
                scores=scores,
                scorer_ids=scorer_ids,
                hub_sets=hubs,
            )
            degree_by_cell[cell_id] = observed_degree
            all_point_metrics_exact &= observed_degree == degree_payload["cells"][cell_id]
            all_point_metrics_exact &= (
                score_correlations(scores, scorer_ids)
                == correlation_payload["cells"][cell_id]
            )
        if cell_id == "C1_development":
            c1_cache = (rows, scores, scorer_ids)
        cell_registry.append(
            {
                "cell_id": cell_id,
                "positive_rows": int(disk_manifest["positive_rows"]),
                "unlabeled_rows": int(disk_manifest["unlabeled_rows"]),
                "total_rows": int(disk_manifest["total_rows"]),
                "manifest": _artifact_record(disk_manifest_path, project_root),
                "rows": _artifact_record(
                    cell_root / str(disk_manifest["rows"]["path"]), project_root
                ),
                "scores": _artifact_record(
                    cell_root / str(disk_manifest["scores"]["path"]), project_root
                ),
                "scorers": _artifact_record(
                    cell_root / str(disk_manifest["scorers"]["path"]), project_root
                ),
            }
        )

    _check(
        checks,
        "all_cell_manifests_rows_states_hashes_shapes_and_finite_scores",
        all_cell_files_ok and all_scores_finite and total_rows == 9_044_323,
        {
            "cell_count": len(cell_registry),
            "total_rows": total_rows,
            "all_scores_finite": all_scores_finite,
        },
    )
    _check(
        checks,
        "exact_scorer_order_and_all_ten_ensemble_columns",
        all_scorers_exact and all_ensembles_exact,
        {
            "scorer_count": len(frozen_scorer_ids),
            "ensemble_count": len(ensembles),
            "all_rows_checked": True,
        },
    )
    _check(
        checks,
        "all_9_by_49_point_metrics_primary_strata_hubs_and_correlations_recomputed",
        all_point_metrics_exact,
        {
            "cell_count": len(point_by_cell),
            "scorer_count_each": 49,
            "primary_degree_hub_cells": len(degree_by_cell),
        },
    )

    bootstrap_registry: list[dict[str, Any]] = []
    bootstrap_ok = True
    for cell_id in PRIMARY_CELLS:
        cell_root = private_root / "scores" / cell_id
        rows, _, _, _ = _read_cell(cell_root)
        bootstrap_root = private_root / "bootstrap" / cell_id
        scorer_ids, distributions = _load_bootstrap(bootstrap_root)
        record = bootstrap_payload["cells"][cell_id]
        components = tuple(
            sorted(
                set(map(str, rows["endpoint_a_component_id"].to_pylist()))
                | set(map(str, rows["endpoint_b_component_id"].to_pylist()))
            )
        )
        drawn_components, regenerated_counts = component_draws(
            components, cell_id=cell_id, replicates=2_000
        )
        stored_counts = np.load(
            bootstrap_root / "component_multiplicities.i32.npy", allow_pickle=False
        )
        bootstrap_ok &= (
            drawn_components == components
            and np.array_equal(stored_counts, regenerated_counts)
            and scorer_ids == list(DETERMINISTIC_SCORERS)
            + [str(item["candidate_id"]) for item in ensembles]
            and distributions.shape == (19, 2_000)
            and all(
                int(np.isfinite(distributions[index]).sum())
                == int(record["finite_replicates_by_scorer"][scorer_id])
                for index, scorer_id in enumerate(scorer_ids)
            )
            and sha256_file(bootstrap_root / "component_multiplicities.i32.npy")
            == record["component_multiplicities_sha256"]
            and sha256_file(bootstrap_root / "bootstrap_metrics.f64.npy")
            == record["bootstrap_metrics_sha256"]
            and sha256_file(bootstrap_root / "BOOTSTRAP_SCORERS.json")
            == record["bootstrap_scorers_sha256"]
        )
        public_intervals = primary_payload["cells"][cell_id][
            "bootstrap_percentile_95_for_controls_and_ensembles"
        ]
        bootstrap_ok &= all(
            list(percentile_95(distributions[index])) == public_intervals[scorer_id]
            for index, scorer_id in enumerate(scorer_ids)
        )
        bootstrap_by_cell[cell_id] = (scorer_ids, distributions)
        bootstrap_registry.append(
            {
                "cell_id": cell_id,
                "participating_components": len(components),
                "component_multiplicities": _artifact_record(
                    bootstrap_root / "component_multiplicities.i32.npy", project_root
                ),
                "bootstrap_metrics": _artifact_record(
                    bootstrap_root / "bootstrap_metrics.f64.npy", project_root
                ),
                "bootstrap_scorers": _artifact_record(
                    bootstrap_root / "BOOTSTRAP_SCORERS.json", project_root
                ),
            }
        )
    _check(
        checks,
        "all_component_draws_bootstrap_hashes_finite_counts_and_intervals",
        bootstrap_ok,
        {"cells": list(PRIMARY_CELLS), "scorers": 19, "replicates": 2_000},
    )

    if c1_cache is None:
        raise RuntimeError("C1 cache absent after complete scoring audit")
    public_training_u = pq.read_table(
        project_root / str(config["frozen_inputs"]["training_unlabeled"]),
        columns=["pair_id"],
    )
    novel = c1_novel_u_metrics(
        rows=c1_cache[0],
        scores=c1_cache[1],
        scorer_ids=c1_cache[2],
        public_training_u_pair_ids=set(map(str, public_training_u["pair_id"].to_pylist())),
    )
    _check(
        checks,
        "C1_novel_U_census_weights_uniqueness_and_all_metrics_recomputed",
        novel == novel_payload["C1_development"],
        {
            "retained_U_rows": novel["retained_U_rows"],
            "removed_U_rows": novel["removed_U_rows"],
            "retained_pair_id_unique": novel["retained_pair_id_unique"],
        },
    )

    disposition = apply_selection_and_kill_rules(
        point_by_cell=point_by_cell,
        bootstrap_by_cell=bootstrap_by_cell,
        hub_by_cell=degree_by_cell,
        novel_u=novel,
        training_registry=training_registry,
    )
    public_disposition = {key: selection_payload[key] for key in disposition}
    _check(
        checks,
        "selection_complexity_seed_and_kill_trace_exact_recomputation",
        disposition == public_disposition
        and disposition["development_stage_disposition"]
        == "stop_complex_model_claim_and_stop_before_protected_evaluation"
        and disposition["kill_trace"]["stop_before_protected_evaluation"] is True,
        {
            "selected_candidate": disposition["selection_trace"]["selected_candidate_id"],
            "disposition": disposition["development_stage_disposition"],
            "stop_before_protected_evaluation": disposition["kill_trace"][
                "stop_before_protected_evaluation"
            ],
        },
    )

    result_files_ok = True
    result_records: list[dict[str, Any]] = []
    for record in result_manifest["files"]:
        path = results_root / str(record["path"])
        observed = _artifact_record(path, project_root)
        result_files_ok &= (
            observed["bytes"] == int(record["bytes"])
            and observed["sha256"] == str(record["sha256"])
            and not contains_public_pair_identity(path)
        )
        result_records.append(observed)
    common_public_ok = all(
        payload.get("pair_identity_public") is False
        and payload.get("protected_candidates_accessed") is False
        and payload.get("protected_truth_accessed") is False
        and payload.get("training_or_checkpoint_change") is False
        for payload in (
            primary_payload,
            source_payload,
            degree_payload,
            correlation_payload,
            novel_payload,
            bootstrap_payload,
            selection_payload,
            result_manifest,
        )
    )
    _check(
        checks,
        "public_result_hashes_no_pair_identity_and_closed_protected_boundary",
        result_files_ok
        and common_public_ok
        and sha256_file(scoring_manifest_path)
        == result_manifest["scoring_run_manifest_sha256"],
        {
            "registered_public_files": len(result_records),
            "pair_identity_public": False,
            "protected_access": False,
        },
    )

    log_records = []
    for name in (
        "SCORING_CONSOLE.log",
        "SCORING_RESUME_CONSOLE.log",
        "EVALUATION_CONSOLE.log",
    ):
        path = private_root.parent / name
        if path.is_file() and not path.is_symlink():
            log_records.append(_artifact_record(path, project_root))
    _check(
        checks,
        "private_execution_logs_and_reproducibility_flags_registered",
        len(log_records) == 3
        and result_manifest["training_or_checkpoint_change"] is False
        and result_manifest["protected_candidates_accessed"] is False
        and result_manifest["protected_truth_accessed"] is False,
        {"log_count": len(log_records)},
    )

    failures = [item for item in checks if item["status"] != "pass"]
    registry = {
        "schema_version": 1,
        "execution_id": str(config["execution_id"]),
        "status": "pass" if not failures else "fail",
        "production_audit_source_commit": production_source_commit,
        "execution_config_sha256": sha256_file(
            project_root / "configs/development_release_and_evaluation_execution_v1.yaml"
        ),
        "training_registry_sha256": sha256_file(training_registry_path),
        "scoring_run_manifest": _artifact_record(scoring_manifest_path, project_root),
        "development_results_manifest": _artifact_record(result_manifest_path, project_root),
        "cells": cell_registry,
        "bootstrap": bootstrap_registry,
        "public_results": result_records,
        "private_logs": log_records,
        "cell_count": 9,
        "scorer_count": 49,
        "selected_checkpoint_count": 30,
        "ensemble_count": 10,
        "development_stage_disposition": disposition["development_stage_disposition"],
        "stop_before_protected_evaluation": True,
        "training_or_checkpoint_change": False,
        "development_decryption_repeated": False,
        "protected_candidates_truth_or_private_key_accessed": False,
        "pair_identity_public": False,
    }
    report = {
        "schema_version": 1,
        "execution_id": str(config["execution_id"]),
        "status": "pass" if not failures else "fail",
        "production_audit_source_commit": production_source_commit,
        "check_counts": {
            "pass": len(checks) - len(failures),
            "fail": len(failures),
            "total": len(checks),
        },
        "checks": checks,
        "development_stage_disposition": disposition["development_stage_disposition"],
        "stop_before_protected_evaluation": True,
        "development_private_key_resolved_or_accessed": False,
        "protected_private_key_resolved_or_accessed": False,
        "protected_candidates_or_truth_accessed": False,
        "training_or_checkpoint_change": False,
        "pair_identity_public": False,
    }
    return registry, report


def write_completed_evidence(
    *,
    project_root: Path,
    config_path: Path,
    production_source_commit: str,
    registry_path: Path,
    report_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    registry, report = run_completed_audit(
        project_root=project_root,
        config=config,
        production_source_commit=production_source_commit,
    )
    _atomic_json(registry_path, registry)
    report = dict(report)
    report["registry_sha256"] = sha256_file(registry_path)
    _atomic_json(report_path, report)
    return registry, report
