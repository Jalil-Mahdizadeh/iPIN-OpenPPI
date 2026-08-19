"""Production audit and immutable registry for completed Stage 1 training."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .constants import (
    CHECKPOINT_ROOT,
    COMPONENTS_PATH,
    COMPONENTS_SHA256,
    EMBEDDING_ROOT,
    ENDPOINTS_PATH,
    ENDPOINTS_SHA256,
    FAMILIES,
    MODEL_CACHE_ROOT,
    MODEL_SIF_SHA256,
    PARTITIONS_PATH,
    PARTITIONS_SHA256,
    POSITIVE_PATH,
    POSITIVE_SHA256,
    PROTOCOL_CONFIGURATION_SHA256,
    RUN_ROOT,
    SEEDS,
    STRATA_PATH,
    STRATA_SHA256,
    UNLABELED_PATH,
    UNLABELED_SHA256,
)
from .objective import learning_rate_multiplier
from .support import (
    assert_no_sensitive_path,
    atomic_json,
    git_commit,
    resolve_regular_inside,
    sha256_file,
)


VALIDATION_ROOT = Path("artifacts/validation/model_execution/stage1_model_execution_v1")
PREPARATION_REGISTRY_SHA256 = "8d15f244f390d7069a4ecd7453622a425a465dcf1ec9d32087e4d557fbb84f4e"
INDEPENDENT_PREPARATION_SHA256 = "a08a62513ef60feff5f3737dbab308c553f24a3f98b562edc8514ba5bd9d70f8"
EXPECTED_PARAMETERS = {
    "lightweight_esm2_150m_linear": 1922,
    "esm2_650m_linear_ablation": 3842,
    "esm2_650m_nonlinear_no_gate_ablation": 426625,
    "esm2_650m_partner_gated_primary": 492417,
}


def _check(checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any) -> None:
    checks.append(
        {"check_id": check_id, "detail": detail, "status": "pass" if condition else "fail"}
    )


def _all_finite(value: Any) -> bool:
    if torch.is_tensor(value):
        return bool(torch.isfinite(value).all())
    if isinstance(value, np.ndarray):
        return bool(np.isfinite(value).all()) if value.dtype.kind in "fci" else True
    if isinstance(value, dict):
        return all(_all_finite(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return all(_all_finite(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def expected_candidate_count() -> int:
    return sum(len(specification["recipes"]) for specification in FAMILIES.values())


def _register(
    *,
    project_root: Path,
    records: dict[str, dict[str, Any]],
    relative: Path,
    role: str,
) -> dict[str, Any]:
    path = resolve_regular_inside(project_root, relative)
    key = relative.as_posix()
    digest = sha256_file(path)
    if key in records:
        existing = records[key]
        if existing["bytes"] != path.stat().st_size or existing["sha256"] != digest:
            raise RuntimeError(f"artifact identity drift across registry roles: {relative}")
        existing["roles"] = sorted(set(existing["roles"] + [role]))
        return existing
    record = {
        "bytes": path.stat().st_size,
        "path": key,
        "roles": [role],
        "sha256": digest,
    }
    records[key] = record
    return record


def _expected_run_ids() -> list[str]:
    return [
        f"{family}__{recipe_id}__seed{seed}"
        for family, specification in FAMILIES.items()
        for recipe_id in specification["recipes"]
        for seed in SEEDS
    ]


def audit_completed_training(
    *, project_root: Path, registry_path: Path, report_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    preparation_registry_path = project_root / VALIDATION_ROOT / "TRAINING_PREPARATION_REGISTRY.json"
    independent_preparation_path = (
        project_root
        / VALIDATION_ROOT
        / "INDEPENDENT_TRAINING_PREPARATION_VALIDATION_REPORT.json"
    )
    prerequisite_ok = (
        sha256_file(preparation_registry_path) == PREPARATION_REGISTRY_SHA256
        and sha256_file(independent_preparation_path) == INDEPENDENT_PREPARATION_SHA256
        and json.loads(independent_preparation_path.read_text(encoding="utf-8"))["status"]
        == "pass"
    )
    _check(
        checks,
        "accepted_preparation_and_independent_gate",
        prerequisite_ok,
        {
            "independent_preparation_sha256": sha256_file(independent_preparation_path),
            "preparation_registry_sha256": sha256_file(preparation_registry_path),
        },
    )

    matrix_path = project_root / RUN_ROOT / "MATRIX_MANIFEST.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    run_ids = [str(run["run_id"]) for run in matrix["runs"]]
    matrix_ok = (
        run_ids == _expected_run_ids()
        and len(set(run_ids)) == 30
        and matrix["run_count"] == 30
        and matrix["comparison_ceiling"] == 300_000_000
        and matrix["container_sha256"] == MODEL_SIF_SHA256
        and matrix["protocol_configuration_sha256"] == PROTOCOL_CONFIGURATION_SHA256
    )
    _check(checks, "exact_frozen_matrix_identity", matrix_ok, {"run_count": len(run_ids)})

    arrays = np.load(project_root / matrix["training_arrays_path"], allow_pickle=False)
    u_weights = arrays["unlabeled_weight_numerator"].astype(np.float64) / arrays[
        "unlabeled_weight_denominator"
    ].astype(np.float64)
    expected_weight_sum = float(np.sum(u_weights, dtype=np.float64))
    expected_artifacts: dict[str, dict[str, Any]] = {}
    preparation_registry = json.loads(preparation_registry_path.read_text(encoding="utf-8"))
    for item in preparation_registry["artifacts"]:
        record = _register(
            project_root=project_root,
            records=expected_artifacts,
            relative=Path(item["path"]),
            role="training_preparation",
        )
        if record["sha256"] != item["sha256"] or record["bytes"] != item["bytes"]:
            raise RuntimeError(f"preparation registry artifact drift: {item['path']}")

    embedding_registry_path = project_root / VALIDATION_ROOT / "EMBEDDING_ARTIFACT_REGISTRY.json"
    embedding_registry = json.loads(embedding_registry_path.read_text(encoding="utf-8"))
    for item in embedding_registry["artifacts"]:
        record = _register(
            project_root=project_root,
            records=expected_artifacts,
            relative=Path(item["path"]),
            role="embedding_dependency",
        )
        if record["sha256"] != item["sha256"] or record["bytes"] != item["bytes"]:
            raise RuntimeError(f"embedding registry artifact drift: {item['path']}")

    for relative in (
        POSITIVE_PATH,
        UNLABELED_PATH,
        STRATA_PATH,
        ENDPOINTS_PATH,
        PARTITIONS_PATH,
        COMPONENTS_PATH,
    ):
        _register(
            project_root=project_root,
            records=expected_artifacts,
            relative=relative,
            role="frozen_public_input",
        )
    expected_input_hashes = {
        POSITIVE_PATH.as_posix(): POSITIVE_SHA256,
        UNLABELED_PATH.as_posix(): UNLABELED_SHA256,
        STRATA_PATH.as_posix(): STRATA_SHA256,
        ENDPOINTS_PATH.as_posix(): ENDPOINTS_SHA256,
        PARTITIONS_PATH.as_posix(): PARTITIONS_SHA256,
        COMPONENTS_PATH.as_posix(): COMPONENTS_SHA256,
    }
    input_ok = all(
        expected_artifacts[path]["sha256"] == expected
        for path, expected in expected_input_hashes.items()
    )
    _check(checks, "frozen_public_input_and_embedding_rehash", input_ok, expected_input_hashes)

    code_paths = (
        Path("src/ipin_openppi/stage1/constants.py"),
        Path("src/ipin_openppi/stage1/support.py"),
        Path("src/ipin_openppi/stage1/baselines.py"),
        Path("src/ipin_openppi/stage1/embeddings.py"),
        Path("src/ipin_openppi/stage1/models.py"),
        Path("src/ipin_openppi/stage1/objective.py"),
        Path("src/ipin_openppi/stage1/preparation.py"),
        Path("src/ipin_openppi/stage1/training.py"),
        Path("scripts/model/train_stage1_models_v1.py"),
        Path("scripts/model/run_stage1_training_matrix_v1.py"),
    )
    for relative in code_paths:
        _register(
            project_root=project_root,
            records=expected_artifacts,
            relative=relative,
            role="executable_code",
        )
    sif_record = _register(
        project_root=project_root,
        records=expected_artifacts,
        relative=Path("containers/images/ipin-model-arm64_0.1.0.sif"),
        role="model_runtime",
    )
    _check(
        checks,
        "container_and_executable_code_bound",
        sif_record["sha256"] == MODEL_SIF_SHA256,
        {"container_bytes": sif_record["bytes"], "container_sha256": sif_record["sha256"]},
    )

    custody_path = project_root / VALIDATION_ROOT / "MODEL_CUSTODY_MANIFEST.json"
    custody = json.loads(custody_path.read_text(encoding="utf-8"))
    for candidate in custody["candidates"]:
        for item in candidate["files"]:
            record = _register(
                project_root=project_root,
                records=expected_artifacts,
                relative=Path(item["path"]),
                role="model_custody",
            )
            if record["sha256"] != item["sha256"] or record["bytes"] != item["bytes"]:
                raise RuntimeError(f"model custody drift: {item['path']}")

    run_summaries: list[dict[str, Any]] = []
    results_by_candidate: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    runs_ok = True
    checkpoints_ok = True
    selection_ok = True
    logs_ok = True
    artifact_census_ok = True
    total_comparisons = 0
    total_steps = 0
    reported_training_gpu_hours = 0.0

    for matrix_run in matrix["runs"]:
        run_id = str(matrix_run["run_id"])
        family = str(matrix_run["family"])
        recipe_id = str(matrix_run["recipe_id"])
        seed = int(matrix_run["seed"])
        config_path = resolve_regular_inside(project_root, Path(matrix_run["config_path"]))
        config = json.loads(config_path.read_text(encoding="utf-8"))
        run_relative = RUN_ROOT / "runs" / run_id
        checkpoint_relative = CHECKPOINT_ROOT / run_id
        result_relative = run_relative / "RUN_RESULT.json"
        state_relative = run_relative / "RUN_STATE.json"
        result_path = resolve_regular_inside(project_root, result_relative)
        state_path = resolve_regular_inside(project_root, state_relative)
        result = json.loads(result_path.read_text(encoding="utf-8"))
        state = json.loads(state_path.read_text(encoding="utf-8"))
        expected_run_files = {
            "RUN_RESULT.json",
            "RUN_STATE.json",
            *(f"PASS_{pass_index:02d}.json" for pass_index in range(1, 6)),
        }
        observed_run_files = {
            path.name for path in (project_root / run_relative).iterdir() if path.is_file()
        }
        expected_checkpoint_files = {
            *(f"pass_{pass_index:02d}.pt" for pass_index in range(1, 6)),
            *(f"pass_{pass_index:02d}.json" for pass_index in range(1, 6)),
        }
        observed_checkpoint_files = {
            path.name
            for path in (project_root / checkpoint_relative).iterdir()
            if path.is_file()
        }
        artifact_census_ok = artifact_census_ok and (
            observed_run_files == expected_run_files
            and observed_checkpoint_files == expected_checkpoint_files
        )
        _register(
            project_root=project_root,
            records=expected_artifacts,
            relative=result_relative,
            role="run_result",
        )
        _register(
            project_root=project_root,
            records=expected_artifacts,
            relative=state_relative,
            role="run_state",
        )

        monitors = result["complete_pass_monitors"]
        selected = min(
            monitors,
            key=lambda item: (item["complete_pass_monitor"], item["pass_index"]),
        )
        result_ok = (
            result["status"] == "complete"
            and result["run_id"] == run_id
            and result["family"] == family
            and result["recipe_id"] == recipe_id
            and result["seed"] == seed
            and result["resume_count"] == 0
            and result["all_five_passes_attempted"] is True
            and result["performance_early_stopping_used"] is False
            and result["comparisons"] == 10_000_000
            and result["steps"] == 2445
            and result["parameter_count"] == EXPECTED_PARAMETERS[family]
            and result["run_config_sha256"] == matrix_run["config_sha256"]
            and sha256_file(config_path) == matrix_run["config_sha256"]
            and state == {"resume_count": 0, "run_id": run_id, "status": "complete"}
            and len(monitors) == 5
        )
        runs_ok = runs_ok and result_ok
        total_comparisons += int(result["comparisons"])
        total_steps += int(result["steps"])
        reported_training_gpu_hours += float(result["gpu_hours_this_attempt"])

        for pass_index, monitor in enumerate(monitors, start=1):
            pass_relative = run_relative / f"PASS_{pass_index:02d}.json"
            pass_path = resolve_regular_inside(project_root, pass_relative)
            pass_record = json.loads(pass_path.read_text(encoding="utf-8"))
            _register(
                project_root=project_root,
                records=expected_artifacts,
                relative=pass_relative,
                role="complete_pass_metric",
            )
            sidecar_relative = checkpoint_relative / f"pass_{pass_index:02d}.json"
            checkpoint_file_relative = checkpoint_relative / f"pass_{pass_index:02d}.pt"
            sidecar_path = resolve_regular_inside(project_root, sidecar_relative)
            checkpoint_path = resolve_regular_inside(project_root, checkpoint_file_relative)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            checkpoint_sha = sha256_file(checkpoint_path)
            checkpoint_record = _register(
                project_root=project_root,
                records=expected_artifacts,
                relative=checkpoint_file_relative,
                role="selected_checkpoint" if pass_index == result["selected_pass"] else "complete_pass_checkpoint",
            )
            _register(
                project_root=project_root,
                records=expected_artifacts,
                relative=sidecar_relative,
                role="checkpoint_sidecar",
            )
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
            binding = checkpoint[
                "config_protocol_code_container_embedding_and_input_hashes"
            ]
            expected_lr = float(config["recipe"]["learning_rate"]) * learning_rate_multiplier(
                pass_index * 489
            )
            pass_ok = (
                pass_record == monitor
                and monitor["pass_index"] == pass_index
                and monitor["comparisons"] == 2_000_000
                and monitor["steps"] == 489
                and monitor["global_step"] == pass_index * 489
                and math.isfinite(float(monitor["complete_pass_monitor"]))
                and abs(float(monitor["weight_sum_float64"]) - expected_weight_sum) <= 1e-6
                and float(monitor["swap_max_absolute_difference"]) <= 1e-6
                and math.isclose(
                    float(monitor["final_learning_rate"]), expected_lr, rel_tol=0.0, abs_tol=1e-15
                )
                and sidecar
                == {
                    "bytes": checkpoint_path.stat().st_size,
                    "pass_index": pass_index,
                    "path": checkpoint_file_relative.as_posix(),
                    "sha256": checkpoint_sha,
                }
                and monitor["checkpoint"] == sidecar
                and checkpoint_record["sha256"] == checkpoint_sha
                and checkpoint["pass_index"] == pass_index
                and checkpoint["global_step"] == pass_index * 489
                and checkpoint["data_cursor"]
                == {"next_unlabeled_position": 0, "pass_complete": True}
                and checkpoint["order_digests"] == monitor["order_digests"]
                and checkpoint["scheduler_state"]
                == {
                    "global_step": pass_index * 489,
                    "name": "linear_warmup_then_cosine_decay",
                    "total_steps": 2445,
                }
                and binding
                == {
                    "code_hashes": config["code_hashes"],
                    "container_sha256": config["container_sha256"],
                    "embedding_manifest_sha256": config["embedding"]["manifest_sha256"],
                    "run_config_sha256": matrix_run["config_sha256"],
                    "training_arrays_sha256": config["training_arrays_sha256"],
                }
                and set(checkpoint["rng_states"])
                == {"numpy_pcg64dxsm", "python", "torch_cpu", "torch_cuda"}
                and len(checkpoint["rng_states"]["torch_cuda"]) == 1
                and _all_finite(checkpoint["model_state"])
                and _all_finite(checkpoint["optimizer_state"])
                and sum(value.numel() for value in checkpoint["model_state"].values())
                == EXPECTED_PARAMETERS[family]
            )
            checkpoints_ok = checkpoints_ok and pass_ok

        selection_ok = selection_ok and (
            result["selected_pass"] == selected["pass_index"]
            and result["selected_checkpoint"] == selected["checkpoint"]
            and result["selection_rule"]
            == "minimum_complete_pass_monitor_earliest_exact_tie"
            and result["selected_checkpoint"]["sha256"]
            == sha256_file(project_root / result["selected_checkpoint"]["path"])
        )

        log_relative = RUN_ROOT / "orchestrator_logs" / f"{run_id}.initial.json"
        log_path = resolve_regular_inside(project_root, log_relative)
        log = json.loads(log_path.read_text(encoding="utf-8"))
        _register(
            project_root=project_root,
            records=expected_artifacts,
            relative=log_relative,
            role="orchestrator_log",
        )
        command = log["command"]
        logs_ok = logs_ok and (
            log["returncode"] == 0
            and float(log["elapsed_seconds_with_gpu_exposed"]) > 0
            and "--nv" in command
            and "--cleanenv" in command
            and f"PYTHONHASHSEED={seed}" in command
            and "CUBLAS_WORKSPACE_CONFIG=:4096:8" in command
            and "HF_HUB_OFFLINE=1" in command
            and "TRANSFORMERS_OFFLINE=1" in command
            and "--resume-infrastructure" not in command
            and not (project_root / RUN_ROOT / "orchestrator_logs" / f"{run_id}.resume1.json").exists()
        )

        summary = {
            "family": family,
            "gpu_hours_reported": float(result["gpu_hours_this_attempt"]),
            "parameter_count": int(result["parameter_count"]),
            "recipe_id": recipe_id,
            "run_config_path": matrix_run["config_path"],
            "run_config_sha256": matrix_run["config_sha256"],
            "run_id": run_id,
            "seed": seed,
            "selected_checkpoint": result["selected_checkpoint"],
            "selected_monitor": float(selected["complete_pass_monitor"]),
            "selected_pass": int(selected["pass_index"]),
            "status": result["status"],
        }
        run_summaries.append(summary)
        results_by_candidate[(family, recipe_id)].append(summary)

    _check(
        checks,
        "all_30_runs_complete_exact_budget",
        runs_ok and total_comparisons == 300_000_000 and total_steps == 73_350,
        {
            "comparisons": total_comparisons,
            "run_count": len(run_summaries),
            "status_counts": dict(Counter(item["status"] for item in run_summaries)),
            "steps": total_steps,
        },
    )
    _check(
        checks,
        "all_150_checkpoints_metrics_RNG_and_symmetry",
        checkpoints_ok,
        {"checkpoint_count": 150, "expected_weight_sum": expected_weight_sum},
    )
    _check(
        checks,
        "training_only_checkpoint_selection",
        selection_ok,
        {"selected_pass_counts": dict(Counter(item["selected_pass"] for item in run_summaries))},
    )
    _check(
        checks,
        "offline_single_GPU_logs_and_zero_resumes",
        logs_ok,
        {"initial_logs": 30, "resume_logs": 0},
    )

    ensembles: list[dict[str, Any]] = []
    ensembles_ok = len(results_by_candidate) == expected_candidate_count()
    for (family, recipe_id), members in sorted(results_by_candidate.items()):
        members = sorted(members, key=lambda item: item["seed"])
        ensembles_ok = ensembles_ok and [item["seed"] for item in members] == list(SEEDS)
        ensembles.append(
            {
                "candidate_id": f"{family}__{recipe_id}",
                "ensemble_score": "arithmetic_mean_of_three_frozen_seed_scores",
                "family": family,
                "members": [
                    {
                        "run_id": item["run_id"],
                        "seed": item["seed"],
                        "selected_checkpoint": item["selected_checkpoint"],
                    }
                    for item in members
                ],
                "recipe_id": recipe_id,
            }
        )
    _check(
        checks,
        "ten_three_seed_ensemble_definitions_frozen",
        ensembles_ok and len(ensembles) == 10,
        {"ensemble_count": len(ensembles), "members_each": [len(item["members"]) for item in ensembles]},
    )

    accounting_relative = RUN_ROOT / "MATRIX_EXECUTION_ACCOUNTING.json"
    accounting_path = resolve_regular_inside(project_root, accounting_relative)
    accounting = json.loads(accounting_path.read_text(encoding="utf-8"))
    _register(
        project_root=project_root,
        records=expected_artifacts,
        relative=accounting_relative,
        role="compute_and_storage_accounting",
    )
    budget_ok = (
        accounting["matrix_run_count"] == 30
        and accounting["status_counts"] == {"complete": 30}
        and float(accounting["total_gpu_hours_conservative"]) < 100
        and int(accounting["final_governed_storage_bytes"]) < 100 * 2**30
        and reported_training_gpu_hours < 100
    )
    _check(
        checks,
        "GPU_comparison_and_storage_budget",
        budget_ok,
        {
            **accounting,
            "reported_training_gpu_hours": reported_training_gpu_hours,
        },
    )

    temporary_files = [
        path.relative_to(project_root).as_posix()
        for root in (project_root / RUN_ROOT, project_root / CHECKPOINT_ROOT)
        if root.exists()
        for path in root.rglob("*.tmp")
    ]
    _check(
        checks,
        "exact_training_artifact_census_and_no_temporaries",
        artifact_census_ok and not temporary_files,
        {
            "registered_unique_artifacts": len(expected_artifacts),
            "temporary_files": temporary_files,
        },
    )

    registered_paths = sorted(expected_artifacts)
    sensitive_ok = True
    try:
        for path in registered_paths:
            assert_no_sensitive_path(Path(path))
    except RuntimeError:
        sensitive_ok = False
    serialized_logs_configs = "\n".join(
        (project_root / path).read_text(encoding="utf-8")
        for path in registered_paths
        if path.endswith(".json") and (
            "/configs/" in path or "/orchestrator_logs/" in path
        )
    )
    sensitive_ok = sensitive_ok and all(
        fragment not in serialized_logs_configs
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
        "absence_of_development_protected_or_sensitive_inputs",
        sensitive_ok,
        {"paths_scanned": len(registered_paths)},
    )

    failures = [item for item in checks if item["status"] != "pass"]
    registry = {
        "artifacts": [expected_artifacts[path] for path in registered_paths],
        "container_sha256": MODEL_SIF_SHA256,
        "ensembles": ensembles,
        "generated_by_code_commit": git_commit(project_root),
        "matrix_sha256": sha256_file(matrix_path),
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "run_summaries": run_summaries,
        "schema_version": 1,
        "summary": {
            "artifact_count": len(expected_artifacts),
            "complete_runs": sum(item["status"] == "complete" for item in run_summaries),
            "conservative_total_gpu_hours": accounting["total_gpu_hours_conservative"],
            "ensemble_count": len(ensembles),
            "failed_runs": sum(item["status"] != "complete" for item in run_summaries),
            "registered_bytes_unique": sum(item["bytes"] for item in expected_artifacts.values()),
            "selected_checkpoint_count": len(run_summaries),
            "total_checkpoints": 150,
            "total_comparisons": total_comparisons,
        },
    }
    atomic_json(registry_path, registry)
    report = {
        "checks": checks,
        "code_commit": git_commit(project_root),
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "summary": {
            "fail": len(failures),
            "pass": len(checks) - len(failures),
            "warning": 0,
        },
        "training_artifact_registry_path": registry_path.relative_to(project_root).as_posix(),
        "training_artifact_registry_sha256": sha256_file(registry_path),
    }
    atomic_json(report_path, report)
    if failures:
        raise RuntimeError(f"completed training audit failed: {failures}")
    return registry, report
