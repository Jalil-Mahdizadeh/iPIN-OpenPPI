"""Exact deterministic public-training-only Stage 1 runner."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import random
import time
from typing import Any, Iterable

import numpy as np
import torch

from .constants import (
    BATCH_COMPARISONS,
    MODEL_SIF_SHA256,
    PASSES,
    POSITIVE_ROWS,
    RUN_ROOT,
    SEEDS,
    STEPS_PER_PASS,
    SWAP_TOLERANCE,
    TOTAL_STEPS,
    UNLABELED_ROWS,
)
from .models import build_model, parameter_count, score_indexed_pairs
from .objective import (
    learning_rate_multiplier,
    positive_positions_for_batch,
    positive_repetition_counts,
    rational_weights,
    weighted_pairwise_logistic_loss,
)
from .support import atomic_json, sha256_file


def configure_reproducibility(seed: int) -> np.random.Generator:
    if seed not in SEEDS:
        raise RuntimeError("run seed not frozen")
    if os.environ.get("PYTHONHASHSEED") != str(seed):
        raise RuntimeError("PYTHONHASHSEED must equal the run seed before interpreter start")
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("CUBLAS_WORKSPACE_CONFIG drift")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise RuntimeError("offline runtime required")
    random.seed(seed)
    numpy_generator = np.random.Generator(np.random.PCG64DXSM(seed))
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("exactly one CUDA GPU required")
    return numpy_generator


def _all_finite(value: Any) -> bool:
    if torch.is_tensor(value):
        return bool(torch.isfinite(value).all())
    if isinstance(value, dict):
        return all(_all_finite(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return all(_all_finite(item) for item in value)
    return True


def atomic_torch_checkpoint(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"stale checkpoint temporary requires review: {temporary}")
    torch.save(payload, temporary)
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return sha256_file(path)


def set_step_learning_rate(optimizer: torch.optim.Optimizer, initial_lr: float, step: int) -> float:
    value = initial_lr * learning_rate_multiplier(step)
    for group in optimizer.param_groups:
        group["lr"] = value
    return value


def _order_record(config: dict[str, Any], state: str, pass_index: int) -> dict[str, Any]:
    matches = [
        record
        for record in config["orders"]
        if record["state"] == state and record["pass_index"] == pass_index
    ]
    if len(matches) != 1:
        raise RuntimeError("missing or duplicate order record")
    return matches[0]


def _validate_code_and_inputs(project_root: Path, config: dict[str, Any], config_path: Path) -> None:
    if config["container_sha256"] != MODEL_SIF_SHA256:
        raise RuntimeError("run config container drift")
    for relative, expected in config["code_hashes"].items():
        if sha256_file(project_root / relative) != expected:
            raise RuntimeError(f"model code hash drift: {relative}")
    for key in ("training_arrays",):
        if sha256_file(project_root / config[f"{key}_path"]) != config[f"{key}_sha256"]:
            raise RuntimeError(f"{key} hash drift")
    embedding = config["embedding"]
    if sha256_file(project_root / embedding["manifest_path"]) != embedding["manifest_sha256"]:
        raise RuntimeError("embedding manifest hash drift")
    if sha256_file(project_root / embedding["standardized_matrix_path"]) != embedding["standardized_matrix_sha256"]:
        raise RuntimeError("standardized embedding hash drift")
    for record in config["orders"]:
        if sha256_file(project_root / record["index_order_path"]) != record["index_order_sha256"]:
            raise RuntimeError("order cache hash drift")


def _restore_checkpoint(
    checkpoint: dict[str, Any],
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    numpy_generator: np.random.Generator,
) -> tuple[int, int, list[dict[str, Any]]]:
    model.load_state_dict(checkpoint["model_state"])
    optimizer.load_state_dict(checkpoint["optimizer_state"])
    random.setstate(checkpoint["rng_states"]["python"])
    numpy_generator.bit_generator.state = checkpoint["rng_states"]["numpy_pcg64dxsm"]
    torch.set_rng_state(checkpoint["rng_states"]["torch_cpu"].cpu())
    torch.cuda.set_rng_state_all([state.cpu() for state in checkpoint["rng_states"]["torch_cuda"]])
    return (
        int(checkpoint["pass_index"]),
        int(checkpoint["global_step"]),
        list(checkpoint["complete_pass_monitors"]),
    )


def run_training(
    *, project_root: Path, run_id: str, resume_infrastructure: bool = False
) -> dict[str, Any]:
    config_path = project_root / RUN_ROOT / "configs" / f"{run_id}.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["run_id"] != run_id:
        raise RuntimeError("run config identity mismatch")
    seed = int(config["seed"])
    numpy_generator = configure_reproducibility(seed)
    _validate_code_and_inputs(project_root, config, config_path)
    run_root = project_root / config["run_output_root"]
    checkpoint_root = project_root / config["checkpoint_root"]
    run_root.mkdir(parents=True, exist_ok=True)
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    result_path = run_root / "RUN_RESULT.json"
    state_path = run_root / "RUN_STATE.json"
    if result_path.exists():
        raise RuntimeError(f"run already closed: {run_id}")

    state = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.exists()
        else {"resume_count": 0, "run_id": run_id, "status": "new"}
    )
    if resume_infrastructure:
        if int(state["resume_count"]) >= 1:
            raise RuntimeError("infrastructure resume limit exhausted")
        state["resume_count"] = int(state["resume_count"]) + 1
    elif state["status"] != "new":
        raise RuntimeError("existing run state requires explicit infrastructure resume")
    state["status"] = "running"
    atomic_json(state_path, state)

    arrays = np.load(project_root / config["training_arrays_path"], allow_pickle=False)
    p_a = arrays["positive_endpoint_a"]
    p_b = arrays["positive_endpoint_b"]
    u_a = arrays["unlabeled_endpoint_a"]
    u_b = arrays["unlabeled_endpoint_b"]
    u_num = arrays["unlabeled_weight_numerator"]
    u_den = arrays["unlabeled_weight_denominator"]
    if len(p_a) != POSITIVE_ROWS or len(u_a) != UNLABELED_ROWS:
        raise RuntimeError("prepared array row-count drift")
    weights_numpy = rational_weights(u_num, u_den)
    mean_weight = float(weights_numpy.mean(dtype=np.float64))

    embedding_path = project_root / config["embedding"]["standardized_matrix_path"]
    embedding_numpy = np.load(embedding_path, mmap_mode="r", allow_pickle=False)
    if embedding_numpy.dtype != np.float32 or embedding_numpy.shape[0] != 17_000:
        raise RuntimeError("standardized embedding identity drift")
    embeddings = torch.from_numpy(np.array(embedding_numpy, copy=True)).to(device="cuda")
    if embeddings.dtype != torch.float32 or not torch.isfinite(embeddings).all():
        raise RuntimeError("invalid standardized embeddings")

    model = build_model(
        config["family"], dropout=float(config["recipe"]["dropout"]), seed=seed
    ).cuda()
    initial_lr = float(config["recipe"]["learning_rate"])
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=initial_lr,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=float(config["recipe"]["weight_decay"]),
        foreach=False,
        fused=False,
    )
    completed_pass = 0
    global_step = 0
    monitors: list[dict[str, Any]] = []
    existing = sorted(checkpoint_root.glob("pass_*.pt"))
    if resume_infrastructure:
        if not existing:
            raise RuntimeError("no verified complete-pass checkpoint available for resume")
        latest = existing[-1]
        sidecar = latest.with_suffix(".json")
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        if sha256_file(latest) != metadata["sha256"]:
            raise RuntimeError("resume checkpoint hash mismatch")
        checkpoint = torch.load(latest, map_location="cuda", weights_only=False)
        completed_pass, global_step, monitors = _restore_checkpoint(
            checkpoint, model, optimizer, numpy_generator
        )
        for monitor in monitors:
            monitor_sidecar = checkpoint_root / f"pass_{int(monitor['pass_index']):02d}.json"
            monitor["checkpoint"] = json.loads(monitor_sidecar.read_text(encoding="utf-8"))

    started = time.monotonic()
    total_comparisons = completed_pass * UNLABELED_ROWS
    try:
        for pass_index in range(completed_pass + 1, PASSES + 1):
            p_record = _order_record(config, "P", pass_index)
            u_record = _order_record(config, "U", pass_index)
            p_order = np.load(project_root / p_record["index_order_path"], mmap_mode="r")
            u_order = np.load(project_root / u_record["index_order_path"], mmap_mode="r")
            if p_order.shape != (POSITIVE_ROWS,) or u_order.shape != (UNLABELED_ROWS,):
                raise RuntimeError("order shape drift")
            positive_repetition_counts(pass_index)
            model.train()
            monitor_numerator = torch.zeros((), dtype=torch.float64, device="cuda")
            monitor_denominator = torch.zeros((), dtype=torch.float64, device="cuda")
            pass_steps = 0
            pass_comparisons = 0
            final_lr = None
            for start in range(0, UNLABELED_ROWS, BATCH_COMPARISONS):
                stop = min(start + BATCH_COMPARISONS, UNLABELED_ROWS)
                unlabeled_rows = np.asarray(u_order[start:stop], dtype=np.int64)
                positive_positions = positive_positions_for_batch(start, stop, pass_index=pass_index)
                positive_rows = np.asarray(p_order[positive_positions], dtype=np.int64)

                def cuda_index(values: np.ndarray) -> torch.Tensor:
                    return torch.from_numpy(np.asarray(values, dtype=np.int64)).to("cuda")

                p_a_index = cuda_index(p_a[positive_rows])
                p_b_index = cuda_index(p_b[positive_rows])
                u_a_index = cuda_index(u_a[unlabeled_rows])
                u_b_index = cuda_index(u_b[unlabeled_rows])
                batch_weights = torch.from_numpy(weights_numpy[unlabeled_rows]).to(
                    device="cuda", dtype=torch.float64
                )
                optimizer.zero_grad(set_to_none=True)
                score_positive = score_indexed_pairs(model, embeddings, p_a_index, p_b_index)
                score_unlabeled = score_indexed_pairs(model, embeddings, u_a_index, u_b_index)
                if not torch.isfinite(score_positive).all() or not torch.isfinite(score_unlabeled).all():
                    raise FloatingPointError("nonfinite model score")
                loss, per_comparison = weighted_pairwise_logistic_loss(
                    score_positive, score_unlabeled, batch_weights, mean_weight
                )
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite training loss")
                monitor_numerator += torch.sum(batch_weights * per_comparison.detach().to(torch.float64))
                monitor_denominator += torch.sum(batch_weights)
                loss.backward()
                if any(
                    parameter.grad is not None and not torch.isfinite(parameter.grad).all()
                    for parameter in model.parameters()
                ):
                    raise FloatingPointError("nonfinite gradient")
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                if not torch.isfinite(norm):
                    raise FloatingPointError("nonfinite global gradient norm")
                global_step += 1
                final_lr = set_step_learning_rate(optimizer, initial_lr, global_step)
                optimizer.step()
                if not _all_finite(model.state_dict()) or not _all_finite(optimizer.state_dict()):
                    raise FloatingPointError("nonfinite parameter or optimizer state")
                batch_size = stop - start
                pass_comparisons += batch_size
                total_comparisons += batch_size
                pass_steps += 1
            if pass_steps != STEPS_PER_PASS or pass_comparisons != UNLABELED_ROWS:
                raise RuntimeError("missing or duplicate U comparison in complete pass")
            if global_step != pass_index * STEPS_PER_PASS:
                raise RuntimeError("global-step/pass algebra drift")
            monitor = float((monitor_numerator / monitor_denominator).cpu())
            if not math.isfinite(monitor):
                raise FloatingPointError("nonfinite complete-pass monitor")
            model.eval()
            fixture_rows = np.arange(min(128, POSITIVE_ROWS), dtype=np.int64)
            fixture_a = cuda_index(p_a[fixture_rows])
            fixture_b = cuda_index(p_b[fixture_rows])
            with torch.no_grad():
                forward = score_indexed_pairs(model, embeddings, fixture_a, fixture_b)
                reverse = score_indexed_pairs(model, embeddings, fixture_b, fixture_a)
            swap_difference = float(torch.max(torch.abs(forward - reverse)).cpu())
            if swap_difference > SWAP_TOLERANCE:
                raise RuntimeError("exact swap-symmetry tolerance failure")
            pass_record = {
                "complete_pass_monitor": monitor,
                "comparisons": pass_comparisons,
                "final_learning_rate": final_lr,
                "global_step": global_step,
                "order_digests": {
                    "positive": p_record["ordered_pair_id_sha256"],
                    "unlabeled": u_record["ordered_pair_id_sha256"],
                },
                "pass_index": pass_index,
                "steps": pass_steps,
                "swap_max_absolute_difference": swap_difference,
                "weight_sum_float64": float(monitor_denominator.cpu()),
            }
            monitors.append(pass_record)
            checkpoint_payload = {
                "complete_pass_monitors": monitors,
                "config_protocol_code_container_embedding_and_input_hashes": {
                    "code_hashes": config["code_hashes"],
                    "container_sha256": config["container_sha256"],
                    "embedding_manifest_sha256": config["embedding"]["manifest_sha256"],
                    "run_config_sha256": sha256_file(config_path),
                    "training_arrays_sha256": config["training_arrays_sha256"],
                },
                "data_cursor": {"next_unlabeled_position": 0, "pass_complete": True},
                "global_step": global_step,
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "order_digests": pass_record["order_digests"],
                "pass_index": pass_index,
                "rng_states": {
                    "numpy_pcg64dxsm": numpy_generator.bit_generator.state,
                    "python": random.getstate(),
                    "torch_cpu": torch.get_rng_state(),
                    "torch_cuda": torch.cuda.get_rng_state_all(),
                },
                "scheduler_state": {
                    "global_step": global_step,
                    "name": "linear_warmup_then_cosine_decay",
                    "total_steps": TOTAL_STEPS,
                },
            }
            checkpoint_path = checkpoint_root / f"pass_{pass_index:02d}.pt"
            checkpoint_sha = atomic_torch_checkpoint(checkpoint_path, checkpoint_payload)
            checkpoint_metadata = {
                "bytes": checkpoint_path.stat().st_size,
                "pass_index": pass_index,
                "path": checkpoint_path.relative_to(project_root).as_posix(),
                "sha256": checkpoint_sha,
            }
            atomic_json(checkpoint_path.with_suffix(".json"), checkpoint_metadata)
            pass_record["checkpoint"] = checkpoint_metadata
            atomic_json(run_root / f"PASS_{pass_index:02d}.json", pass_record)

        if global_step != TOTAL_STEPS or total_comparisons != PASSES * UNLABELED_ROWS:
            raise RuntimeError("run did not complete exact fixed training budget")
        selected = min(monitors, key=lambda record: (record["complete_pass_monitor"], record["pass_index"]))
        elapsed = time.monotonic() - started
        result = {
            "all_five_passes_attempted": True,
            "comparisons": total_comparisons,
            "complete_pass_monitors": monitors,
            "elapsed_seconds_this_attempt": elapsed,
            "family": config["family"],
            "gpu_hours_this_attempt": elapsed / 3600.0,
            "parameter_count": parameter_count(model),
            "performance_early_stopping_used": False,
            "recipe_id": config["recipe"]["recipe_id"],
            "resume_count": state["resume_count"],
            "run_config_path": config_path.relative_to(project_root).as_posix(),
            "run_config_sha256": sha256_file(config_path),
            "run_id": run_id,
            "seed": seed,
            "selected_checkpoint": selected["checkpoint"],
            "selected_pass": selected["pass_index"],
            "selection_rule": "minimum_complete_pass_monitor_earliest_exact_tie",
            "status": "complete",
            "steps": global_step,
        }
        atomic_json(result_path, result)
        state["status"] = "complete"
        atomic_json(state_path, state)
        return result
    except (FloatingPointError, RuntimeError) as exc:
        result = {
            "error": str(exc),
            "family": config["family"],
            "recipe_id": config["recipe"]["recipe_id"],
            "replacement_recipe_or_seed": False,
            "run_id": run_id,
            "seed": seed,
            "status": "failed_numerical_or_integrity",
        }
        atomic_json(result_path, result)
        state["status"] = result["status"]
        atomic_json(state_path, state)
        raise
