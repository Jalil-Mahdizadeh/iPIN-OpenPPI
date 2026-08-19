"""Production audit and registry for the frozen Stage 1 training preparation."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from .constants import (
    BATCH_COMPARISONS,
    CHECKPOINT_ROOT,
    EMBEDDING_ROOT,
    FAMILIES,
    MODEL_SIF_SHA256,
    PASSES,
    POSITIVE_PATH,
    POSITIVE_ROWS,
    POSITIVE_SHA256,
    PROTOCOL_CONFIGURATION_SHA256,
    RUN_ROOT,
    SEEDS,
    STEPS_PER_PASS,
    STRATA_PATH,
    STRATA_SHA256,
    TOTAL_STEPS,
    UNLABELED_PATH,
    UNLABELED_ROWS,
    UNLABELED_SHA256,
)
from .embeddings import ordered_records
from .constants import ENDPOINTS_PATH, ENDPOINTS_SHA256
from .objective import deterministic_order, ordered_pair_id_digest
from .preparation import CODE_PATHS
from .support import (
    assert_no_sensitive_path,
    atomic_json,
    git_commit,
    require_sha256,
    resolve_regular_inside,
    sha256_file,
)


def _check(checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any) -> None:
    checks.append(
        {"check_id": check_id, "detail": detail, "status": "pass" if condition else "fail"}
    )


def expected_run_ids() -> list[str]:
    return [
        f"{family}__{recipe_id}__seed{seed}"
        for family, specification in FAMILIES.items()
        for recipe_id in specification["recipes"]
        for seed in SEEDS
    ]


def _artifact(project_root: Path, relative: Path) -> dict[str, Any]:
    path = resolve_regular_inside(project_root, relative)
    return {
        "bytes": path.stat().st_size,
        "path": relative.as_posix(),
        "sha256": sha256_file(path),
    }


def audit_training_preparation(
    *, project_root: Path, registry_path: Path, report_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for relative, expected in (
        (ENDPOINTS_PATH, ENDPOINTS_SHA256),
        (POSITIVE_PATH, POSITIVE_SHA256),
        (UNLABELED_PATH, UNLABELED_SHA256),
        (STRATA_PATH, STRATA_SHA256),
    ):
        require_sha256(project_root / relative, expected)

    matrix_relative = RUN_ROOT / "MATRIX_MANIFEST.json"
    matrix_path = resolve_regular_inside(project_root, matrix_relative)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    expected_ids = expected_run_ids()
    matrix_ids = [str(run["run_id"]) for run in matrix["runs"]]
    matrix_ok = (
        matrix["run_count"] == 30
        and matrix_ids == expected_ids
        and len(set(matrix_ids)) == 30
        and matrix["comparison_ceiling"] == 300_000_000
        and matrix["adaptive_search"] is False
        and matrix["multi_gpu_or_multi_node"] is False
        and matrix["container_sha256"] == MODEL_SIF_SHA256
        and matrix["protocol_configuration_sha256"] == PROTOCOL_CONFIGURATION_SHA256
        and Counter(run["family"] for run in matrix["runs"])
        == Counter(
            {
                "lightweight_esm2_150m_linear": 6,
                "esm2_650m_linear_ablation": 6,
                "esm2_650m_nonlinear_no_gate_ablation": 9,
                "esm2_650m_partner_gated_primary": 9,
            }
        )
    )
    _check(
        checks,
        "exact_nonadaptive_30_run_matrix",
        matrix_ok,
        {"code_commit": matrix["code_commit"], "run_count": matrix["run_count"]},
    )

    records = ordered_records(project_root / ENDPOINTS_PATH)
    index_by_sha = {record.sequence_sha256: index for index, record in enumerate(records)}
    positive = pq.read_table(
        project_root / POSITIVE_PATH,
        columns=[
            "pair_id",
            "endpoint_a_sha256",
            "endpoint_b_sha256",
            "endpoint_a_partition",
            "endpoint_b_partition",
            "state",
            "sampling_weight_numerator",
            "sampling_weight_denominator",
        ],
    )
    unlabeled = pq.read_table(
        project_root / UNLABELED_PATH,
        columns=[
            "pair_id",
            "endpoint_a_sha256",
            "endpoint_b_sha256",
            "endpoint_a_partition",
            "endpoint_b_partition",
            "state",
            "stratum_id",
            "sampling_weight_numerator",
            "sampling_weight_denominator",
        ],
    )
    strata = pq.read_table(
        project_root / STRATA_PATH,
        columns=["stratum_id", "sampling_weight_numerator", "sampling_weight_denominator"],
    )
    public_ok = (
        positive.num_rows == POSITIVE_ROWS
        and unlabeled.num_rows == UNLABELED_ROWS
        and strata.num_rows == 36
        and set(positive["state"].to_pylist()) == {"released_positive"}
        and set(unlabeled["state"].to_pylist()) == {"unlabeled"}
        and all(
            set(table[column].to_pylist()) == {"train"}
            for table in (positive, unlabeled)
            for column in ("endpoint_a_partition", "endpoint_b_partition")
        )
    )
    _check(
        checks,
        "public_training_only_P_U_strata_boundary",
        public_ok,
        {"P": positive.num_rows, "U": unlabeled.num_rows, "strata": strata.num_rows},
    )

    arrays_relative = Path(matrix["training_arrays_path"])
    arrays_path = resolve_regular_inside(project_root, arrays_relative)
    require_sha256(arrays_path, matrix["training_arrays_sha256"])
    with np.load(arrays_path, allow_pickle=False) as arrays:
        observed_arrays = {name: arrays[name] for name in arrays.files}

    def mapped(column: Any) -> np.ndarray:
        return np.fromiter(
            (index_by_sha[value] for value in column.to_pylist()),
            dtype=np.int32,
            count=len(column),
        )

    expected_arrays = {
        "positive_endpoint_a": mapped(positive["endpoint_a_sha256"]),
        "positive_endpoint_b": mapped(positive["endpoint_b_sha256"]),
        "unlabeled_endpoint_a": mapped(unlabeled["endpoint_a_sha256"]),
        "unlabeled_endpoint_b": mapped(unlabeled["endpoint_b_sha256"]),
        "unlabeled_weight_numerator": np.asarray(
            unlabeled["sampling_weight_numerator"].to_numpy(), dtype=np.int64
        ),
        "unlabeled_weight_denominator": np.asarray(
            unlabeled["sampling_weight_denominator"].to_numpy(), dtype=np.int64
        ),
    }
    arrays_ok = set(observed_arrays) == set(expected_arrays) and all(
        np.array_equal(observed_arrays[name], expected)
        for name, expected in expected_arrays.items()
    )
    _check(
        checks,
        "prepared_endpoint_and_rational_weight_arrays_exact",
        arrays_ok,
        {name: list(value.shape) for name, value in observed_arrays.items()},
    )

    positive_ids = positive["pair_id"].to_pylist()
    unlabeled_ids = unlabeled["pair_id"].to_pylist()
    order_manifest_relative = Path(matrix["order_manifest_path"])
    order_manifest_path = resolve_regular_inside(project_root, order_manifest_relative)
    require_sha256(order_manifest_path, matrix["order_manifest_sha256"])
    order_manifest = json.loads(order_manifest_path.read_text(encoding="utf-8"))
    order_records = order_manifest["order_records"]
    order_ok = len(order_records) == 30
    order_artifacts: list[dict[str, Any]] = []
    order_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    for record in order_records:
        state = str(record["state"])
        seed = int(record["seed"])
        pass_index = int(record["pass_index"])
        pair_ids = positive_ids if state == "P" else unlabeled_ids
        path_relative = Path(record["index_order_path"])
        path = resolve_regular_inside(project_root, path_relative)
        observed = np.load(path, mmap_mode="r", allow_pickle=False)
        expected = deterministic_order(
            pair_ids, seed=seed, pass_index=pass_index, state=state
        )
        order_ok = order_ok and (
            observed.dtype == np.int64
            and np.array_equal(observed, expected)
            and sha256_file(path) == record["index_order_sha256"]
            and ordered_pair_id_digest(pair_ids, observed)
            == record["ordered_pair_id_sha256"]
            and record["rows"] == len(pair_ids)
        )
        order_by_key[(state, seed, pass_index)] = record
        order_artifacts.append(_artifact(project_root, path_relative))
    expected_order_keys = {
        (state, seed, pass_index)
        for seed in SEEDS
        for pass_index in range(1, PASSES + 1)
        for state in ("P", "U")
    }
    _check(
        checks,
        "all_30_full_SHA_orders_independently_reconstructed",
        order_ok and set(order_by_key) == expected_order_keys,
        {"order_records": len(order_records), "unique_keys": len(order_by_key)},
    )

    code_hashes = {
        path.as_posix(): sha256_file(project_root / path) for path in CODE_PATHS
    }
    config_artifacts: list[dict[str, Any]] = []
    configs_ok = True
    for run_record in matrix["runs"]:
        config_relative = Path(run_record["config_path"])
        config_path = resolve_regular_inside(project_root, config_relative)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        family = str(run_record["family"])
        recipe_id = str(run_record["recipe_id"])
        seed = int(run_record["seed"])
        expected_recipe = FAMILIES[family]["recipes"][recipe_id]
        configs_ok = configs_ok and (
            sha256_file(config_path) == run_record["config_sha256"]
            and config["run_id"] == run_record["run_id"]
            and config["family"] == family
            and config["seed"] == seed
            and config["recipe"] == {"recipe_id": recipe_id, **expected_recipe}
            and config["code_commit"] == matrix["code_commit"]
            and config["code_hashes"] == code_hashes
            and config["container_sha256"] == MODEL_SIF_SHA256
            and config["protocol_configuration_sha256"]
            == PROTOCOL_CONFIGURATION_SHA256
            and config["batch_comparisons"] == BATCH_COMPARISONS
            and config["fixed_complete_U_passes"] == PASSES
            and config["scheduler"]
            == {
                "final_learning_rate_fraction": 0.1,
                "name": "linear_warmup_then_cosine_decay",
                "steps_per_pass": STEPS_PER_PASS,
                "total_steps": TOTAL_STEPS,
                "warmup_steps": 123,
            }
            and config["objective"]
            == "design_weighted_positive_vs_unlabeled_pairwise_logistic_ranking"
            and config["performance_early_stopping"] is False
            and config["infrastructure_resume_limit"] == 1
            and config["numerical_failure_retry"] is False
            and config["orders"]
            == [
                order_by_key[(state, seed, pass_index)]
                for pass_index in range(1, PASSES + 1)
                for state in ("P", "U")
            ]
            and config["training_arrays_sha256"] == matrix["training_arrays_sha256"]
        )
        embedding = config["embedding"]
        embedding_manifest = resolve_regular_inside(
            project_root, Path(embedding["manifest_path"])
        )
        standardized = resolve_regular_inside(
            project_root, Path(embedding["standardized_matrix_path"])
        )
        configs_ok = configs_ok and (
            sha256_file(embedding_manifest) == embedding["manifest_sha256"]
            and sha256_file(standardized) == embedding["standardized_matrix_sha256"]
        )
        config_artifacts.append(_artifact(project_root, config_relative))
    _check(
        checks,
        "all_30_run_configs_exact_and_hash_bound",
        configs_ok and len(config_artifacts) == 30,
        {"configs": len(config_artifacts), "code_hashes": code_hashes},
    )

    expected_config_files = {f"{run_id}.json" for run_id in expected_ids}
    config_root = project_root / RUN_ROOT / "configs"
    observed_config_files = {path.name for path in config_root.iterdir() if path.is_file()}
    order_root = project_root / RUN_ROOT / "prepared/orders"
    expected_order_files = {
        f"{state}_seed{seed}_pass{pass_index}.i64.npy"
        for seed in SEEDS
        for pass_index in range(1, PASSES + 1)
        for state in ("P", "U")
    }
    observed_order_files = {path.name for path in order_root.iterdir() if path.is_file()}
    run_products = project_root / RUN_ROOT / "runs"
    checkpoint_products = project_root / CHECKPOINT_ROOT
    no_execution = (
        (not run_products.exists() or not any(run_products.iterdir()))
        and (not checkpoint_products.exists() or not any(checkpoint_products.iterdir()))
        and not (project_root / RUN_ROOT / "orchestrator_logs").exists()
        and not (project_root / RUN_ROOT / "MATRIX_EXECUTION_ACCOUNTING.json").exists()
    )
    _check(
        checks,
        "pretraining_file_census_and_no_execution",
        observed_config_files == expected_config_files
        and observed_order_files == expected_order_files
        and no_execution,
        {
            "configs": len(observed_config_files),
            "orders": len(observed_order_files),
            "training_started": not no_execution,
        },
    )

    preparation_artifacts = [
        _artifact(project_root, matrix_relative),
        _artifact(project_root, arrays_relative),
        _artifact(project_root, order_manifest_relative),
        *order_artifacts,
        *config_artifacts,
    ]
    paths = [item["path"] for item in preparation_artifacts]
    no_sensitive = len(paths) == len(set(paths))
    try:
        for path in paths:
            assert_no_sensitive_path(Path(path))
    except RuntimeError:
        no_sensitive = False
    serialized_configs = matrix_path.read_text(encoding="utf-8") + "\n".join(
        (project_root / item["path"]).read_text(encoding="utf-8")
        for item in config_artifacts
    )
    no_sensitive = no_sensitive and all(
        fragment not in serialized_configs
        for fragment in (
            "development_release.cms",
            "protected_candidates.cms",
            "protected_truth.cms",
            "/.private/",
            "/sealed/",
        )
    )
    _check(
        checks,
        "public_only_preparation_registry_boundary",
        no_sensitive,
        {"registered_preparation_artifacts": len(preparation_artifacts)},
    )

    failures = [item for item in checks if item["status"] != "pass"]
    registry = {
        "artifacts": sorted(preparation_artifacts, key=lambda item: item["path"]),
        "code_hashes": code_hashes,
        "embedding_inputs": {
            candidate: {
                "manifest_sha256": sha256_file(
                    project_root / EMBEDDING_ROOT / candidate / "EMBEDDING_MANIFEST.json"
                )
            }
            for candidate in ("esm2_150m", "esm2_650m")
        },
        "generated_by_code_commit": git_commit(project_root),
        "matrix_producer_commit": matrix["code_commit"],
        "orchestrator_sha256": sha256_file(
            project_root / "scripts/model/run_stage1_training_matrix_v1.py"
        ),
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "schema_version": 1,
        "summary": {
            "artifact_count": len(preparation_artifacts),
            "bytes": sum(item["bytes"] for item in preparation_artifacts),
            "config_count": len(config_artifacts),
            "order_count": len(order_artifacts),
            "run_count": len(matrix["runs"]),
        },
    }
    atomic_json(registry_path, registry)
    report = {
        "checks": checks,
        "code_commit": git_commit(project_root),
        "preparation_registry_path": registry_path.relative_to(project_root).as_posix(),
        "preparation_registry_sha256": sha256_file(registry_path),
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "summary": {
            "fail": len(failures),
            "pass": len(checks) - len(failures),
            "warning": 0,
        },
    }
    atomic_json(report_path, report)
    if failures:
        raise RuntimeError(f"training preparation audit failed: {failures}")
    return registry, report
