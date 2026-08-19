#!/usr/bin/env python3
"""Independent validation of the complete frozen Stage 1 training registry."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import stat
from typing import Any, Sequence

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq
import torch
from torch.nn import functional as torch_functional


CONFIG_SHA256 = "3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5"
CONTAINER_SHA256 = "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"
REGISTRY_SHA256 = "11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318"
PRODUCTION_AUDIT_SHA256 = "fb15f7462f61597928be68e3f2963505a10318c2696f6575d0354b73a0cb7040"
PRODUCTION_EVIDENCE_COMMIT = "a46639245fc34d9b53063ec46370a6139a2bd021"
REGISTRY_PRODUCER_COMMIT = "90787bb6aae17dc5bf9eab89ca38e929bbd38558"
INDEPENDENT_PREPARATION_SHA256 = "a08a62513ef60feff5f3737dbab308c553f24a3f98b562edc8514ba5bd9d70f8"

VALIDATION_ROOT = Path("artifacts/validation/model_execution/stage1_model_execution_v1")
RUN_ROOT = Path("artifacts/runs/stage1_model_execution_v1")
CHECKPOINT_ROOT = Path("artifacts/checkpoints/stage1_model_execution_v1")
P_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "positive_pairs/part-00000.parquet"
)
U_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "unlabeled_pairs/part-00000.parquet"
)
P_SHA256 = "4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499"
U_SHA256 = "d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7"
SEEDS = (20260803, 20260817, 20260831)
PARAMETERS = {
    "lightweight_esm2_150m_linear": 1922,
    "esm2_650m_linear_ablation": 3842,
    "esm2_650m_nonlinear_no_gate_ablation": 426625,
    "esm2_650m_partner_gated_primary": 492417,
}
SOURCE_HASHES = {
    "src/ipin_openppi/stage1/baselines.py": "26786946de618b82ea4f7e4ad821f5ee6cbd8123bce978365f794cb0912552b7",
    "src/ipin_openppi/stage1/models.py": "653340c6aa7caa21672f855fec6b0562857984560b49b20a2e37a4c9579ede28",
    "src/ipin_openppi/stage1/objective.py": "34258f553dd6406d9a5ef0fd0320cd703f7ecb4ca0d3f2bb4e9cbc598942eaab",
    "src/ipin_openppi/stage1/training.py": "4000f8e5fab939e90f84d28a5343076d0d6b5b0e1e4f084669a259ac9bc6b0ee",
    "scripts/model/run_stage1_training_matrix_v1.py": "94166e30ff22a2f219eeff62563d1e2cf930e48db5d5313634a12183508490d7",
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
        raise RuntimeError(f"unsafe registry path: {relative}")
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


def _order(pair_ids: Sequence[str], seed: int, pass_index: int, state: str) -> np.ndarray:
    pair_bytes = np.asarray(pair_ids, dtype=f"S{max(map(len, pair_ids))}")
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


def _commutative(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    denominator = torch.linalg.vector_norm(a, dim=-1) * torch.linalg.vector_norm(b, dim=-1)
    if torch.any(denominator == 0):
        raise RuntimeError("zero vector in independent symmetry fixture")
    cosine = ((a * b).sum(dim=-1) / denominator).unsqueeze(-1)
    return torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)


def _independent_score(
    family: str, state: dict[str, torch.Tensor], a: torch.Tensor, b: torch.Tensor
) -> torch.Tensor:
    if family in ("lightweight_esm2_150m_linear", "esm2_650m_linear_ablation"):
        return torch_functional.linear(
            _commutative(a, b), state["output.weight"], state["output.bias"]
        ).squeeze(-1)
    projected_a = torch_functional.gelu(
        torch_functional.linear(a, state["projection.weight"], state["projection.bias"]),
        approximate="none",
    )
    projected_b = torch_functional.gelu(
        torch_functional.linear(b, state["projection.weight"], state["projection.bias"]),
        approximate="none",
    )
    if family == "esm2_650m_partner_gated_primary":
        conditioned_a = projected_a * torch.sigmoid(
            torch_functional.linear(projected_b, state["gate.weight"], state["gate.bias"])
        )
        conditioned_b = projected_b * torch.sigmoid(
            torch_functional.linear(projected_a, state["gate.weight"], state["gate.bias"])
        )
    else:
        conditioned_a, conditioned_b = projected_a, projected_b
    hidden = torch_functional.gelu(
        torch_functional.linear(
            _commutative(conditioned_a, conditioned_b),
            state["hidden.weight"],
            state["hidden.bias"],
        ),
        approximate="none",
    )
    return torch_functional.linear(hidden, state["output.weight"], state["output.bias"]).squeeze(-1)


def validate(project_root: Path, output: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    registry_path = _safe_regular(project_root, VALIDATION_ROOT / "TRAINING_ARTIFACT_REGISTRY.json")
    audit_path = _safe_regular(project_root, VALIDATION_ROOT / "TRAINING_PRODUCTION_AUDIT_REPORT.json")
    preparation_path = _safe_regular(project_root, VALIDATION_ROOT / "INDEPENDENT_TRAINING_PREPARATION_VALIDATION_REPORT.json")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    evidence_ok = _sha256(registry_path) == REGISTRY_SHA256 and _sha256(audit_path) == PRODUCTION_AUDIT_SHA256 and _sha256(preparation_path) == INDEPENDENT_PREPARATION_SHA256 and registry["generated_by_code_commit"] == REGISTRY_PRODUCER_COMMIT and audit["status"] == "pass" and audit["training_artifact_registry_sha256"] == REGISTRY_SHA256
    _check(checks, "production_registry_and_prior_independent_gate", evidence_ok, {"production_evidence_commit": PRODUCTION_EVIDENCE_COMMIT, "registry_sha256": _sha256(registry_path)})

    artifacts = {item["path"]: item for item in registry["artifacts"]}
    artifacts_ok = len(artifacts) == len(registry["artifacts"]) == 647
    role_counts: Counter[str] = Counter()
    for relative, item in artifacts.items():
        path = _safe_regular(project_root, Path(relative))
        artifacts_ok = artifacts_ok and path.stat().st_size == item["bytes"] and _sha256(path) == item["sha256"]
        role_counts.update(item["roles"])
    _check(checks, "independent_all_647_artifact_rehash", artifacts_ok, {"artifact_count": len(artifacts), "role_counts": dict(sorted(role_counts.items())), "unique_bytes": sum(item["bytes"] for item in artifacts.values())})

    source_ok = True
    for relative, expected in SOURCE_HASHES.items():
        source_ok = source_ok and _sha256(_safe_regular(project_root, Path(relative))) == expected
    model_source = (project_root / "src/ipin_openppi/stage1/models.py").read_text(encoding="utf-8")
    objective_source = (project_root / "src/ipin_openppi/stage1/objective.py").read_text(encoding="utf-8")
    baseline_source = (project_root / "src/ipin_openppi/stage1/baselines.py").read_text(encoding="utf-8")
    source_tokens = (
        "torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)",
        "conditioned_a = projected_a * torch.sigmoid(self.gate(projected_b))",
        "conditioned_b = projected_b * torch.sigmoid(self.gate(projected_a))",
        'F.gelu(self.projection(a), approximate="none")',
        "F.softplus(-(score_positive - score_unlabeled))",
        "((weights / mean_weight) * per_comparison.to(torch.float64)).mean()",
        'KMER_ALPHABET = "ACDEFGHIKLMNPQRSTVWYX"',
        "np.maximum(forward, reverse).max(initial=0.0)",
    )
    combined_source = model_source + objective_source + baseline_source
    source_ok = source_ok and all(token in combined_source for token in source_tokens)
    _check(checks, "independent_model_objective_and_baseline_source_binding", source_ok, SOURCE_HASHES)

    matrix_path = _safe_regular(project_root, RUN_ROOT / "MATRIX_MANIFEST.json")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    p_path = _safe_regular(project_root, P_PATH)
    u_path = _safe_regular(project_root, U_PATH)
    p = pq.read_table(p_path, columns=["pair_id", "endpoint_a_partition", "endpoint_b_partition", "state"])
    u = pq.read_table(u_path, columns=["pair_id", "endpoint_a_partition", "endpoint_b_partition", "state", "sampling_weight_numerator", "sampling_weight_denominator"])
    public_ok = _sha256(p_path) == P_SHA256 and _sha256(u_path) == U_SHA256 and p.num_rows == 16_799 and u.num_rows == 2_000_000 and pc.count_distinct(p["pair_id"]).as_py() == 16_799 and pc.count_distinct(u["pair_id"]).as_py() == 2_000_000 and pc.unique(p["state"]).to_pylist() == ["released_positive"] and pc.unique(u["state"]).to_pylist() == ["unlabeled"] and all(pc.unique(table[column]).to_pylist() == ["train"] for table in (p, u) for column in ("endpoint_a_partition", "endpoint_b_partition"))
    _check(checks, "independent_public_training_visibility", public_ok, {"P": p.num_rows, "U": u.num_rows})

    arrays_path = _safe_regular(project_root, Path(matrix["training_arrays_path"]))
    with np.load(arrays_path, allow_pickle=False) as arrays:
        prepared_num = arrays["unlabeled_weight_numerator"]
        prepared_den = arrays["unlabeled_weight_denominator"]
    source_num = u["sampling_weight_numerator"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
    source_den = u["sampling_weight_denominator"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
    weights = source_num.astype(np.float64) / source_den.astype(np.float64)
    weight_sum = float(np.sum(weights, dtype=np.float64))
    weights_ok = np.array_equal(prepared_num, source_num) and np.array_equal(prepared_den, source_den) and np.all(source_num > 0) and np.all(source_den > 0)
    _check(checks, "independent_exact_rational_objective_weights", weights_ok, {"mean_weight_float64": float(np.mean(weights, dtype=np.float64)), "weight_sum_float64": weight_sum})

    p_ids = p["pair_id"].to_pylist()
    u_ids = u["pair_id"].to_pylist()
    order_manifest_path = _safe_regular(project_root, Path(matrix["order_manifest_path"]))
    order_manifest = json.loads(order_manifest_path.read_text(encoding="utf-8"))
    orders_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    orders_ok = len(order_manifest["order_records"]) == 30
    for record in order_manifest["order_records"]:
        state, seed, pass_index = str(record["state"]), int(record["seed"]), int(record["pass_index"])
        pair_ids = p_ids if state == "P" else u_ids
        path = _safe_regular(project_root, Path(record["index_order_path"]))
        observed = np.load(path, mmap_mode="r", allow_pickle=False)
        expected = _order(pair_ids, seed, pass_index, state)
        orders_ok = orders_ok and observed.dtype == np.int64 and np.array_equal(observed, expected) and _sha256(path) == record["index_order_sha256"] and _ordered_digest(pair_ids, observed) == record["ordered_pair_id_sha256"]
        orders_by_key[(state, seed, pass_index)] = record
    counts = np.bincount((np.arange(2_000_000, dtype=np.int64) + 4) % 16_799, minlength=16_799)
    orders_ok = orders_ok and len(orders_by_key) == 30 and counts.min() == 119 and counts.max() == 120 and int(np.sum(counts == 120)) == 919
    _check(checks, "independent_all_orders_and_positive_coverage", orders_ok, {"ceiling_count": int(np.sum(counts == 120)), "order_count": len(orders_by_key)})

    summaries = {item["run_id"]: item for item in registry["run_summaries"]}
    run_ok = len(summaries) == 30
    checkpoint_ok = True
    selection_ok = True
    logs_ok = True
    selected_symmetry_ok = True
    selected_swap_maximum = 0.0
    total_comparisons = 0
    total_steps = 0
    selected_passes: Counter[int] = Counter()
    embedding_fixtures: dict[str, torch.Tensor] = {}
    checkpoint_count = 0

    for matrix_run in matrix["runs"]:
        run_id = str(matrix_run["run_id"])
        family = str(matrix_run["family"])
        recipe_id = str(matrix_run["recipe_id"])
        seed = int(matrix_run["seed"])
        summary = summaries[run_id]
        config_path = _safe_regular(project_root, Path(matrix_run["config_path"]))
        config = json.loads(config_path.read_text(encoding="utf-8"))
        result_path = _safe_regular(project_root, RUN_ROOT / "runs" / run_id / "RUN_RESULT.json")
        state_path = _safe_regular(project_root, RUN_ROOT / "runs" / run_id / "RUN_STATE.json")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        state = json.loads(state_path.read_text(encoding="utf-8"))
        monitors = result["complete_pass_monitors"]
        chosen = min(monitors, key=lambda item: (item["complete_pass_monitor"], item["pass_index"]))
        run_ok = run_ok and result["status"] == "complete" and result["run_id"] == run_id and result["family"] == family and result["recipe_id"] == recipe_id and result["seed"] == seed and result["resume_count"] == 0 and result["comparisons"] == 10_000_000 and result["steps"] == 2445 and result["parameter_count"] == PARAMETERS[family] and result["all_five_passes_attempted"] is True and result["performance_early_stopping_used"] is False and len(monitors) == 5 and state == {"resume_count": 0, "run_id": run_id, "status": "complete"} and summary["selected_checkpoint"] == result["selected_checkpoint"] and summary["run_config_sha256"] == matrix_run["config_sha256"] == _sha256(config_path)
        total_comparisons += int(result["comparisons"])
        total_steps += int(result["steps"])
        selected_passes[int(result["selected_pass"])] += 1
        for pass_index, monitor in enumerate(monitors, start=1):
            checkpoint_path = _safe_regular(project_root, CHECKPOINT_ROOT / run_id / f"pass_{pass_index:02d}.pt")
            sidecar_path = _safe_regular(project_root, CHECKPOINT_ROOT / run_id / f"pass_{pass_index:02d}.json")
            pass_path = _safe_regular(project_root, RUN_ROOT / "runs" / run_id / f"PASS_{pass_index:02d}.json")
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            pass_record = json.loads(pass_path.read_text(encoding="utf-8"))
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
            checkpoint_count += 1
            checkpoint_ok = checkpoint_ok and sidecar["sha256"] == _sha256(checkpoint_path) and sidecar["bytes"] == checkpoint_path.stat().st_size and sidecar["path"] == (CHECKPOINT_ROOT / run_id / f"pass_{pass_index:02d}.pt").as_posix() and pass_record == monitor and monitor["checkpoint"] == sidecar and monitor["pass_index"] == pass_index and monitor["comparisons"] == 2_000_000 and monitor["steps"] == 489 and monitor["global_step"] == pass_index * 489 and abs(float(monitor["weight_sum_float64"]) - weight_sum) <= 1e-6 and float(monitor["swap_max_absolute_difference"]) <= 1e-6 and checkpoint["pass_index"] == pass_index and checkpoint["global_step"] == pass_index * 489 and checkpoint["order_digests"] == monitor["order_digests"] == {"positive": orders_by_key[("P", seed, pass_index)]["ordered_pair_id_sha256"], "unlabeled": orders_by_key[("U", seed, pass_index)]["ordered_pair_id_sha256"]} and checkpoint["data_cursor"] == {"next_unlabeled_position": 0, "pass_complete": True} and checkpoint["scheduler_state"] == {"global_step": pass_index * 489, "name": "linear_warmup_then_cosine_decay", "total_steps": 2445} and set(checkpoint["rng_states"]) == {"numpy_pcg64dxsm", "python", "torch_cpu", "torch_cuda"} and len(checkpoint["rng_states"]["torch_cuda"]) == 1 and _all_finite(checkpoint["model_state"]) and _all_finite(checkpoint["optimizer_state"]) and sum(value.numel() for value in checkpoint["model_state"].values()) == PARAMETERS[family]
            if pass_index == result["selected_pass"]:
                candidate = "esm2_150m" if family == "lightweight_esm2_150m_linear" else "esm2_650m"
                if candidate not in embedding_fixtures:
                    matrix_embedding = np.load(_safe_regular(project_root, Path(config["embedding"]["standardized_matrix_path"])), mmap_mode="r", allow_pickle=False)
                    embedding_fixtures[candidate] = torch.from_numpy(np.array(matrix_embedding[:64], copy=True))
                fixture = embedding_fixtures[candidate]
                with torch.no_grad():
                    forward = _independent_score(family, checkpoint["model_state"], fixture[:32], fixture[32:64])
                    reverse = _independent_score(family, checkpoint["model_state"], fixture[32:64], fixture[:32])
                difference = float(torch.max(torch.abs(forward - reverse)))
                selected_swap_maximum = max(selected_swap_maximum, difference)
                selected_symmetry_ok = selected_symmetry_ok and torch.isfinite(forward).all() and difference <= 1e-6
        selection_ok = selection_ok and result["selected_pass"] == chosen["pass_index"] and result["selected_checkpoint"] == chosen["checkpoint"] and result["selection_rule"] == "minimum_complete_pass_monitor_earliest_exact_tie" and result["selected_checkpoint"]["sha256"] == _sha256(_safe_regular(project_root, Path(result["selected_checkpoint"]["path"])))
        log_path = _safe_regular(project_root, RUN_ROOT / "orchestrator_logs" / f"{run_id}.initial.json")
        log = json.loads(log_path.read_text(encoding="utf-8"))
        command = log["command"]
        logs_ok = logs_ok and log["returncode"] == 0 and float(log["elapsed_seconds_with_gpu_exposed"]) > 0 and "--nv" in command and "--cleanenv" in command and f"PYTHONHASHSEED={seed}" in command and "CUBLAS_WORKSPACE_CONFIG=:4096:8" in command and "HF_HUB_OFFLINE=1" in command and "TRANSFORMERS_OFFLINE=1" in command and "--resume-infrastructure" not in command and not (project_root / RUN_ROOT / "orchestrator_logs" / f"{run_id}.resume1.json").exists()

    _check(checks, "independent_30_run_completeness_and_budget", run_ok and total_comparisons == 300_000_000 and total_steps == 73_350, {"comparisons": total_comparisons, "run_count": len(summaries), "steps": total_steps})
    _check(checks, "independent_150_checkpoint_RNG_order_weight_and_finiteness", checkpoint_ok and checkpoint_count == 150, {"checkpoint_count": checkpoint_count, "weight_sum": weight_sum})
    _check(checks, "independent_training_only_checkpoint_selection", selection_ok, {"selected_pass_counts": dict(selected_passes)})
    _check(checks, "independent_selected_checkpoint_functional_symmetry", selected_symmetry_ok, {"selected_checkpoints": 30, "swap_max_absolute_difference": selected_swap_maximum})
    _check(checks, "independent_offline_single_GPU_logs_and_zero_resumes", logs_ok, {"initial_logs": 30, "resume_logs": 0})

    ensembles_ok = len(registry["ensembles"]) == 10
    ensemble_ids: set[str] = set()
    for ensemble in registry["ensembles"]:
        ensemble_ids.add(ensemble["candidate_id"])
        members = ensemble["members"]
        ensembles_ok = ensembles_ok and ensemble["ensemble_score"] == "arithmetic_mean_of_three_frozen_seed_scores" and [member["seed"] for member in members] == list(SEEDS) and len({member["run_id"] for member in members}) == 3 and all(member["selected_checkpoint"] == summaries[member["run_id"]]["selected_checkpoint"] for member in members)
    _check(checks, "independent_ten_three_seed_ensembles", ensembles_ok and len(ensemble_ids) == 10, {"ensemble_count": len(ensemble_ids)})

    accounting_path = _safe_regular(project_root, RUN_ROOT / "MATRIX_EXECUTION_ACCOUNTING.json")
    accounting = json.loads(accounting_path.read_text(encoding="utf-8"))
    budget_ok = accounting["matrix_run_count"] == 30 and accounting["status_counts"] == {"complete": 30} and float(accounting["total_gpu_hours_conservative"]) == float(registry["summary"]["conservative_total_gpu_hours"]) and float(accounting["total_gpu_hours_conservative"]) < 100 and int(accounting["final_governed_storage_bytes"]) < 100 * 2**30 and int(registry["summary"]["registered_bytes_unique"]) < 100 * 2**30 and registry["summary"]["total_comparisons"] == 300_000_000 and registry["summary"]["failed_runs"] == 0
    _check(checks, "independent_compute_storage_and_registry_totals", budget_ok, {**accounting, "registered_bytes_unique": registry["summary"]["registered_bytes_unique"]})

    registered_paths = "\n".join(sorted(artifacts))
    serialized = "\n".join((_safe_regular(project_root, Path(relative))).read_text(encoding="utf-8") for relative in artifacts if relative.endswith(".json") and ("/configs/" in relative or "/orchestrator_logs/" in relative))
    no_sensitive = all(fragment not in registered_paths and fragment not in serialized for fragment in FORBIDDEN)
    allowed_roots = ("artifacts/", "containers/", "data/canonical/", "scripts/model/", "src/ipin_openppi/stage1/")
    no_sensitive = no_sensitive and all(relative.startswith(allowed_roots) for relative in artifacts)
    no_temporaries = not any((project_root / root).exists() and any((project_root / root).rglob("*.tmp")) for root in (RUN_ROOT, CHECKPOINT_ROOT))
    _check(checks, "independent_absence_of_leakage_sensitive_paths_and_temporaries", no_sensitive and no_temporaries, {"registered_paths": len(artifacts), "temporary_files": False if no_temporaries else True})

    failures = [item for item in checks if item["status"] != "pass"]
    report = {
        "checks": checks,
        "independence": {"imports_production_stage1_modules": False, "model_framework_use": "checkpoint_deserialization_and_clean_room_functional_forward_only", "production_evidence_commit": PRODUCTION_EVIDENCE_COMMIT, "validation_method": "artifact_rehash_order_reconstruction_checkpoint_inspection_and_independent_forward"},
        "protocol_configuration_sha256": CONFIG_SHA256,
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "summary": {"fail": len(failures), "pass": len(checks) - len(failures), "warning": 0},
        "training_artifact_registry_sha256": REGISTRY_SHA256,
    }
    _write_json(output, report)
    if failures:
        raise RuntimeError(f"independent completed training validation failed: {failures}")
    return report


if __name__ == "__main__":
    root = Path.cwd().resolve(strict=True)
    validate(root, root / VALIDATION_ROOT / "INDEPENDENT_TRAINING_ARTIFACT_VALIDATION_REPORT.json")
