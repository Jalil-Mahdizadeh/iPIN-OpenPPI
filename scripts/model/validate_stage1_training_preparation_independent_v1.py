#!/usr/bin/env python3
"""Clean-room validation of frozen Stage 1 orders, arrays, configs, and launch."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import stat
from typing import Any, Sequence

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq


CONFIG_SHA256 = "3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5"
CONTAINER_SHA256 = "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"
PREPARATION_REGISTRY_SHA256 = "8d15f244f390d7069a4ecd7453622a425a465dcf1ec9d32087e4d557fbb84f4e"
PREPARATION_AUDIT_SHA256 = "849f09fdf3f32f6572ffdc097de21fa8a56da29a2494b949386df7871f37631f"
PREPARATION_EVIDENCE_COMMIT = "8d026f6b18c4770bd820654ca95f5dfaf7465f33"
MATRIX_PRODUCER_COMMIT = "8555d7217df40fe0f4629fb77797bc190f250521"
ORCHESTRATOR_SHA256 = "94166e30ff22a2f219eeff62563d1e2cf930e48db5d5313634a12183508490d7"

VALIDATION_ROOT = Path("artifacts/validation/model_execution/stage1_model_execution_v1")
RUN_ROOT = Path("artifacts/runs/stage1_model_execution_v1")
CHECKPOINT_ROOT = Path("artifacts/checkpoints/stage1_model_execution_v1")
ENDPOINT_PATH = Path(
    "data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/"
    "eligible_reference_sequences/part-00000.parquet"
)
P_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "positive_pairs/part-00000.parquet"
)
U_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "unlabeled_pairs/part-00000.parquet"
)
STRATA_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "sampling_strata/part-00000.parquet"
)
INPUT_HASHES = {
    ENDPOINT_PATH: "4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e",
    P_PATH: "4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499",
    U_PATH: "d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7",
    STRATA_PATH: "b8e4247ce934d837477513b322af008413ac8d61fa95ccedd16fe2712c1d6427",
}
SEEDS = (20260803, 20260817, 20260831)
FAMILIES = {
    "lightweight_esm2_150m_linear": {
        "candidate": "esm2_150m",
        "recipes": {
            "linear_lr3e-4": {"learning_rate": 0.0003, "weight_decay": 0.0001, "dropout": 0.0},
            "linear_lr1e-3": {"learning_rate": 0.001, "weight_decay": 0.0001, "dropout": 0.0},
        },
    },
    "esm2_650m_linear_ablation": {
        "candidate": "esm2_650m",
        "recipes": {
            "linear_lr3e-4": {"learning_rate": 0.0003, "weight_decay": 0.0001, "dropout": 0.0},
            "linear_lr1e-3": {"learning_rate": 0.001, "weight_decay": 0.0001, "dropout": 0.0},
        },
    },
    "esm2_650m_nonlinear_no_gate_ablation": {
        "candidate": "esm2_650m",
        "recipes": {
            "nonlinear_conservative": {"learning_rate": 0.0003, "weight_decay": 0.0001, "dropout": 0.1},
            "nonlinear_default": {"learning_rate": 0.001, "weight_decay": 0.0001, "dropout": 0.1},
            "nonlinear_no_dropout": {"learning_rate": 0.001, "weight_decay": 0.00001, "dropout": 0.0},
        },
    },
    "esm2_650m_partner_gated_primary": {
        "candidate": "esm2_650m",
        "recipes": {
            "nonlinear_conservative": {"learning_rate": 0.0003, "weight_decay": 0.0001, "dropout": 0.1},
            "nonlinear_default": {"learning_rate": 0.001, "weight_decay": 0.0001, "dropout": 0.1},
            "nonlinear_no_dropout": {"learning_rate": 0.001, "weight_decay": 0.00001, "dropout": 0.0},
        },
    },
}
FORBIDDEN = (
    "/sealed/",
    "/.private/",
    "development_release.cms",
    "protected_candidates.cms",
    "protected_truth.cms",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_regular(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or any(fragment in "/" + relative.as_posix() for fragment in FORBIDDEN):
        raise RuntimeError(f"unsafe path: {relative}")
    root = root.resolve(strict=True)
    target = (root / relative).absolute()
    target.relative_to(root)
    current = target
    while True:
        if stat.S_ISLNK(current.lstat().st_mode):
            raise RuntimeError(f"symlink prohibited: {current}")
        if current == root:
            break
        current = current.parent
    if not target.is_file():
        raise RuntimeError(f"regular file required: {relative}")
    return target


def _check(checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any) -> None:
    checks.append(
        {"check_id": check_id, "detail": detail, "status": "pass" if condition else "fail"}
    )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite validation evidence: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
    temporary.replace(path)


def _expected_runs() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": specification["candidate"],
            "family": family,
            "recipe_id": recipe_id,
            "run_id": f"{family}__{recipe_id}__seed{seed}",
            "seed": seed,
        }
        for family, specification in FAMILIES.items()
        for recipe_id in specification["recipes"]
        for seed in SEEDS
    ]


def _order(pair_ids: Sequence[str], seed: int, pass_index: int, state: str) -> np.ndarray:
    maximum = max(map(len, pair_ids))
    pair_bytes = np.asarray(pair_ids, dtype=f"S{maximum}")
    keys = np.empty(len(pair_ids), dtype="S32")
    for index, pair_id in enumerate(pair_ids):
        payload = f"sha256:ipin-openppi-model-training-v1:{seed}:{pass_index}:{state}:{pair_id}"
        keys[index] = hashlib.sha256(payload.encode("utf-8")).digest()
    return np.lexsort((pair_bytes, keys)).astype(np.int64, copy=False)


def _ordered_digest(pair_ids: Sequence[str], order: np.ndarray) -> str:
    digest = hashlib.sha256()
    for index in order:
        value = pair_ids[int(index)].encode("utf-8")
        digest.update(len(value).to_bytes(4, "big"))
        digest.update(value)
    return digest.hexdigest()


def validate(project_root: Path, output: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    config_path = _safe_regular(project_root, Path("configs/model_governance_and_baseline_training_protocol_v1.yaml"))
    input_ok = _sha256(config_path) == CONFIG_SHA256
    for relative, expected in INPUT_HASHES.items():
        input_ok = input_ok and _sha256(_safe_regular(project_root, relative)) == expected
    _check(checks, "binding_config_and_public_input_rehash", input_ok, {path.as_posix(): digest for path, digest in INPUT_HASHES.items()})

    registry_path = _safe_regular(project_root, VALIDATION_ROOT / "TRAINING_PREPARATION_REGISTRY.json")
    audit_path = _safe_regular(project_root, VALIDATION_ROOT / "TRAINING_PREPARATION_AUDIT_REPORT.json")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    evidence_ok = _sha256(registry_path) == PREPARATION_REGISTRY_SHA256 and _sha256(audit_path) == PREPARATION_AUDIT_SHA256 and registry["matrix_producer_commit"] == MATRIX_PRODUCER_COMMIT and audit["status"] == "pass" and audit["preparation_registry_sha256"] == PREPARATION_REGISTRY_SHA256
    _check(checks, "production_preparation_evidence_boundary", evidence_ok, {"evidence_commit": PREPARATION_EVIDENCE_COMMIT, "registry_sha256": _sha256(registry_path)})

    artifacts_ok = len(registry["artifacts"]) == 63
    artifact_paths: set[str] = set()
    for item in registry["artifacts"]:
        path = _safe_regular(project_root, Path(item["path"]))
        artifacts_ok = artifacts_ok and path.stat().st_size == item["bytes"] and _sha256(path) == item["sha256"]
        artifact_paths.add(item["path"])
    _check(checks, "all_63_preparation_artifacts_rehashed", artifacts_ok and len(artifact_paths) == 63, {"artifact_count": len(artifact_paths), "bytes": sum(item["bytes"] for item in registry["artifacts"])})

    matrix_path = _safe_regular(project_root, RUN_ROOT / "MATRIX_MANIFEST.json")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    expected_runs = _expected_runs()
    matrix_projection = [{key: run[key] for key in ("candidate_id", "family", "recipe_id", "run_id", "seed")} for run in matrix["runs"]]
    matrix_ok = matrix_projection == expected_runs and matrix["run_count"] == 30 and matrix["code_commit"] == MATRIX_PRODUCER_COMMIT and matrix["comparison_ceiling"] == 300_000_000 and matrix["adaptive_search"] is False and matrix["multi_gpu_or_multi_node"] is False and matrix["container_sha256"] == CONTAINER_SHA256 and matrix["maximum_gpu_hours"] == 100 and matrix["maximum_project_storage_gib"] == 100
    _check(checks, "independent_exact_30_run_matrix", matrix_ok, {"family_counts": dict(Counter(run["family"] for run in matrix["runs"])), "run_count": matrix["run_count"]})

    endpoint_table = pq.read_table(project_root / ENDPOINT_PATH, columns=["reference_sequence_sha256", "sequence_length"])
    endpoint_records = sorted(zip(endpoint_table["reference_sequence_sha256"].to_pylist(), endpoint_table["sequence_length"].to_pylist(), strict=True), key=lambda item: (int(item[1]), str(item[0])))
    endpoint_index = {str(digest): index for index, (digest, _) in enumerate(endpoint_records)}
    p = pq.read_table(project_root / P_PATH, columns=["pair_id", "endpoint_a_sha256", "endpoint_b_sha256", "endpoint_a_partition", "endpoint_b_partition", "state", "sampling_weight_numerator", "sampling_weight_denominator"])
    u = pq.read_table(project_root / U_PATH, columns=["pair_id", "endpoint_a_sha256", "endpoint_b_sha256", "endpoint_a_partition", "endpoint_b_partition", "state", "sampling_weight_numerator", "sampling_weight_denominator"])
    p_ids = p["pair_id"].to_pylist()
    u_ids = u["pair_id"].to_pylist()
    public_ok = len(endpoint_index) == 17_000 and p.num_rows == 16_799 and u.num_rows == 2_000_000 and pc.count_distinct(p["pair_id"]).as_py() == 16_799 and pc.count_distinct(u["pair_id"]).as_py() == 2_000_000 and pc.unique(p["state"]).to_pylist() == ["released_positive"] and pc.unique(u["state"]).to_pylist() == ["unlabeled"] and all(pc.unique(table[column]).to_pylist() == ["train"] for table in (p, u) for column in ("endpoint_a_partition", "endpoint_b_partition"))
    _check(checks, "independent_public_P_U_endpoint_boundary", public_ok, {"P": p.num_rows, "U": u.num_rows, "endpoints": len(endpoint_index)})

    arrays_path = _safe_regular(project_root, Path(matrix["training_arrays_path"]))
    with np.load(arrays_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    def mapped(column: Any) -> np.ndarray:
        return np.fromiter((endpoint_index[value] for value in column.to_pylist()), dtype=np.int32, count=len(column))
    expected_arrays = {
        "positive_endpoint_a": mapped(p["endpoint_a_sha256"]),
        "positive_endpoint_b": mapped(p["endpoint_b_sha256"]),
        "unlabeled_endpoint_a": mapped(u["endpoint_a_sha256"]),
        "unlabeled_endpoint_b": mapped(u["endpoint_b_sha256"]),
        "unlabeled_weight_numerator": u["sampling_weight_numerator"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False),
        "unlabeled_weight_denominator": u["sampling_weight_denominator"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False),
    }
    arrays_ok = set(arrays) == set(expected_arrays) and all(np.array_equal(arrays[name], value) for name, value in expected_arrays.items()) and _sha256(arrays_path) == matrix["training_arrays_sha256"]
    _check(checks, "independent_training_array_reconstruction", arrays_ok, {name: list(value.shape) for name, value in arrays.items()})

    order_manifest_path = _safe_regular(project_root, Path(matrix["order_manifest_path"]))
    order_manifest = json.loads(order_manifest_path.read_text(encoding="utf-8"))
    order_records = order_manifest["order_records"]
    records_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    orders_ok = len(order_records) == 30 and _sha256(order_manifest_path) == matrix["order_manifest_sha256"]
    for record in order_records:
        state, seed, pass_index = str(record["state"]), int(record["seed"]), int(record["pass_index"])
        pair_ids = p_ids if state == "P" else u_ids
        path = _safe_regular(project_root, Path(record["index_order_path"]))
        observed = np.load(path, mmap_mode="r", allow_pickle=False)
        expected = _order(pair_ids, seed, pass_index, state)
        orders_ok = orders_ok and observed.dtype == np.int64 and np.array_equal(observed, expected) and _sha256(path) == record["index_order_sha256"] and _ordered_digest(pair_ids, observed) == record["ordered_pair_id_sha256"] and record["rows"] == len(pair_ids)
        records_by_key[(state, seed, pass_index)] = record
    _check(checks, "independent_all_30_order_reconstruction", orders_ok and len(records_by_key) == 30, {"order_count": len(records_by_key)})

    configs_ok = True
    for expected_run, matrix_run in zip(expected_runs, matrix["runs"], strict=True):
        config_path = _safe_regular(project_root, Path(matrix_run["config_path"]))
        config = json.loads(config_path.read_text(encoding="utf-8"))
        family, recipe_id, seed = expected_run["family"], expected_run["recipe_id"], expected_run["seed"]
        recipe = FAMILIES[family]["recipes"][recipe_id]
        configs_ok = configs_ok and _sha256(config_path) == matrix_run["config_sha256"] and config["run_id"] == expected_run["run_id"] and config["family"] == family and config["seed"] == seed and config["recipe"] == {"recipe_id": recipe_id, **recipe} and config["code_commit"] == MATRIX_PRODUCER_COMMIT and config["container_sha256"] == CONTAINER_SHA256 and config["protocol_configuration_sha256"] == CONFIG_SHA256 and config["batch_comparisons"] == 4096 and config["fixed_complete_U_passes"] == 5 and config["objective"] == "design_weighted_positive_vs_unlabeled_pairwise_logistic_ranking" and config["optimizer"] == {"beta1": 0.9, "beta2": 0.999, "epsilon": 1e-8, "gradient_global_norm_clip": 1.0, "name": "AdamW"} and config["scheduler"] == {"final_learning_rate_fraction": 0.1, "name": "linear_warmup_then_cosine_decay", "steps_per_pass": 489, "total_steps": 2445, "warmup_steps": 123} and config["seed_controls"] == {"allow_tf32": False, "cublas_workspace_config": ":4096:8", "cudnn_benchmark": False, "cudnn_deterministic": True, "numpy_generator": "PCG64DXSM", "pythonhashseed": seed, "torch_deterministic_algorithms": True} and config["orders"] == [records_by_key[(state, seed, pass_index)] for pass_index in range(1, 6) for state in ("P", "U")] and config["training_arrays_sha256"] == matrix["training_arrays_sha256"] and config["performance_early_stopping"] is False and config["infrastructure_resume_limit"] == 1 and config["numerical_failure_retry"] is False
        configs_ok = configs_ok and all(_sha256(_safe_regular(project_root, Path(path))) == digest for path, digest in config["code_hashes"].items()) and _sha256(_safe_regular(project_root, Path(config["embedding"]["manifest_path"]))) == config["embedding"]["manifest_sha256"] and _sha256(_safe_regular(project_root, Path(config["embedding"]["standardized_matrix_path"]))) == config["embedding"]["standardized_matrix_sha256"]
    _check(checks, "independent_all_30_config_contracts", configs_ok, {"config_count": len(matrix["runs"])})

    orchestrator_path = _safe_regular(project_root, Path("scripts/model/run_stage1_training_matrix_v1.py"))
    orchestrator_source = orchestrator_path.read_text(encoding="utf-8")
    required_launch_tokens = ("--nv", "--cleanenv", "CUBLAS_WORKSPACE_CONFIG=:4096:8", "HF_HUB_OFFLINE=1", "TRANSFORMERS_OFFLINE=1", "PYTHONHASHSEED=", "100 * 2**30", "100 GPU-hour ceiling exceeded", "refusing to overwrite orchestrator attempt log")
    launch_ok = _sha256(orchestrator_path) == ORCHESTRATOR_SHA256 == registry["orchestrator_sha256"] and all(token in orchestrator_source for token in required_launch_tokens) and "sbatch" not in orchestrator_source and "srun" not in orchestrator_source
    _check(checks, "independent_single_GPU_offline_launch_and_budget_contract", launch_ok, {"orchestrator_sha256": _sha256(orchestrator_path)})

    run_products = project_root / RUN_ROOT / "runs"
    checkpoint_products = project_root / CHECKPOINT_ROOT
    no_execution = (not run_products.exists() or not any(run_products.iterdir())) and (not checkpoint_products.exists() or not any(checkpoint_products.iterdir())) and not (project_root / RUN_ROOT / "orchestrator_logs").exists() and not (project_root / RUN_ROOT / "MATRIX_EXECUTION_ACCOUNTING.json").exists()
    serialized = matrix_path.read_text(encoding="utf-8") + "\n".join((_safe_regular(project_root, Path(run["config_path"]))).read_text(encoding="utf-8") for run in matrix["runs"])
    no_sensitive = all(fragment not in serialized and all(fragment not in path for path in artifact_paths) for fragment in FORBIDDEN)
    _check(checks, "independent_no_training_and_no_sensitive_input", no_execution and no_sensitive, {"registered_artifacts": len(artifact_paths), "training_started": not no_execution})

    failures = [item for item in checks if item["status"] != "pass"]
    report = {
        "checks": checks,
        "independence": {"imports_production_stage1_modules": False, "imports_torch_or_model_framework": False, "method": "clean_room_order_array_config_and_launch_reconstruction", "production_evidence_commit": PREPARATION_EVIDENCE_COMMIT},
        "protocol_configuration_sha256": CONFIG_SHA256,
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "summary": {"fail": len(failures), "pass": len(checks) - len(failures), "warning": 0},
    }
    _write_json(output, report)
    if failures:
        raise RuntimeError(f"independent preparation validation failed: {failures}")
    return report


if __name__ == "__main__":
    root = Path.cwd().resolve(strict=True)
    validate(root, root / VALIDATION_ROOT / "INDEPENDENT_TRAINING_PREPARATION_VALIDATION_REPORT.json")
