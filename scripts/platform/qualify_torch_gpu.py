#!/usr/bin/env python3
"""Deterministic one-GPU BF16, training, and checkpoint/restart fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from torch import nn

SEED = 20260803


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--image-sha256", required=True)
    return parser.parse_args()


def require_within_root(path: Path, root: Path) -> Path:
    resolved_root = root.resolve(strict=True)
    resolved_path = path.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Output path is outside project root: {resolved_path}") from exc
    return resolved_path


def tensor_digest(named_tensors: list[tuple[str, torch.Tensor]]) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(named_tensors):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(value.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def assert_nested_equal(left: Any, right: Any, path: str = "root") -> None:
    if isinstance(left, torch.Tensor):
        if not isinstance(right, torch.Tensor) or not torch.equal(left.cpu(), right.cpu()):
            raise AssertionError(f"Checkpoint tensor mismatch at {path}")
        return
    if isinstance(left, dict):
        if not isinstance(right, dict) or left.keys() != right.keys():
            raise AssertionError(f"Checkpoint mapping mismatch at {path}")
        for key in left:
            assert_nested_equal(left[key], right[key], f"{path}.{key}")
        return
    if isinstance(left, (list, tuple)):
        if not isinstance(right, type(left)) or len(left) != len(right):
            raise AssertionError(f"Checkpoint sequence mismatch at {path}")
        for index, (left_item, right_item) in enumerate(zip(left, right, strict=True)):
            assert_nested_equal(left_item, right_item, f"{path}[{index}]")
        return
    if left != right:
        raise AssertionError(f"Checkpoint scalar mismatch at {path}: {left!r} != {right!r}")


def make_model() -> nn.Module:
    return nn.Sequential(
        nn.Linear(1024, 2048),
        nn.GELU(),
        nn.Linear(2048, 512),
        nn.GELU(),
        nn.Linear(512, 1),
    )


def train_step(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    features: torch.Tensor,
    targets: torch.Tensor,
) -> float:
    optimizer.zero_grad(set_to_none=True)
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        predictions = model(features)
        loss = torch.nn.functional.mse_loss(predictions.float(), targets)
    loss.backward()
    optimizer.step()
    scheduler.step()
    torch.cuda.synchronize()
    return float(loss.detach().cpu())


def execute_fixture(args: argparse.Namespace, output: Path) -> dict[str, Any]:
    if platform.machine() != "aarch64":
        raise RuntimeError(f"Expected aarch64, observed {platform.machine()}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available inside the Apptainer container")
    if torch.cuda.device_count() < 1:
        raise RuntimeError("No visible CUDA device")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("Visible GPU does not report BF16 support")

    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False

    device = torch.device("cuda:0")
    properties = torch.cuda.get_device_properties(device)
    torch.cuda.reset_peak_memory_stats(device)

    started = time.perf_counter()
    matrix_generator = torch.Generator(device=device).manual_seed(SEED + 1)
    left = torch.randn((1024, 1024), generator=matrix_generator, device=device, dtype=torch.bfloat16)
    product = left @ left.transpose(0, 1)
    torch.cuda.synchronize()
    matmul_digest = tensor_digest([("bf16_product", product)])
    matmul_mean = float(product.float().mean().cpu())

    data_generator = torch.Generator(device=device).manual_seed(SEED + 2)
    batches = [
        (
            torch.randn((256, 1024), generator=data_generator, device=device),
            torch.randn((256, 1), generator=data_generator, device=device),
        )
        for _ in range(3)
    ]

    model = make_model().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.0e-3, weight_decay=1.0e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=4)
    pre_checkpoint_losses = [
        train_step(model, optimizer, scheduler, *batches[0]),
        train_step(model, optimizer, scheduler, *batches[1]),
    ]

    checkpoint_path = output.with_suffix(".checkpoint.pt")
    checkpoint = {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict(),
        "data_position": 2,
        "seed": SEED,
        "torch_rng_state": torch.get_rng_state(),
        "cuda_rng_state_all": torch.cuda.get_rng_state_all(),
    }
    torch.save(checkpoint, checkpoint_path)

    uninterrupted_loss = train_step(model, optimizer, scheduler, *batches[2])
    uninterrupted_model = model.state_dict()
    uninterrupted_optimizer = optimizer.state_dict()
    uninterrupted_scheduler = scheduler.state_dict()

    resumed_model = make_model().to(device)
    resumed_optimizer = torch.optim.AdamW(resumed_model.parameters(), lr=1.0e-3, weight_decay=1.0e-2)
    resumed_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(resumed_optimizer, T_max=4)
    loaded = torch.load(checkpoint_path, map_location=device, weights_only=False)
    resumed_model.load_state_dict(loaded["model"])
    resumed_optimizer.load_state_dict(loaded["optimizer"])
    resumed_scheduler.load_state_dict(loaded["scheduler"])
    torch.set_rng_state(loaded["torch_rng_state"])
    torch.cuda.set_rng_state_all(loaded["cuda_rng_state_all"])
    resumed_loss = train_step(resumed_model, resumed_optimizer, resumed_scheduler, *batches[2])

    assert loaded["data_position"] == 2
    assert_nested_equal(uninterrupted_model, resumed_model.state_dict(), "model_after_resume")
    assert_nested_equal(uninterrupted_optimizer, resumed_optimizer.state_dict(), "optimizer_after_resume")
    assert_nested_equal(uninterrupted_scheduler, resumed_scheduler.state_dict(), "scheduler_after_resume")
    if uninterrupted_loss != resumed_loss:
        raise AssertionError(f"Resume loss differs: {uninterrupted_loss} != {resumed_loss}")

    state_digest = tensor_digest(list(resumed_model.state_dict().items()))
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    free_memory, total_memory = torch.cuda.mem_get_info(device)

    return {
        "schema_version": 1,
        "status": "pass",
        "test": "single_gpu_bf16_forward_backward_checkpoint_restart",
        "run_label": args.run_label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "image_sha256": args.image_sha256,
        "platform": {
            "hostname": socket.gethostname(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
            "gpu_name": properties.name,
            "gpu_compute_capability": [properties.major, properties.minor],
            "gpu_total_memory_bytes": properties.total_memory,
            "visible_gpu_count": torch.cuda.device_count(),
            "bf16_supported": torch.cuda.is_bf16_supported(),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        },
        "fixture": {
            "matmul_shape": [1024, 1024],
            "matmul_digest": matmul_digest,
            "matmul_mean": matmul_mean,
            "pre_checkpoint_losses": pre_checkpoint_losses,
            "uninterrupted_loss": uninterrupted_loss,
            "resumed_loss": resumed_loss,
            "checkpoint_restart_exact": True,
            "final_model_digest": state_digest,
        },
        "resources": {
            "elapsed_seconds": elapsed,
            "peak_gpu_memory_bytes": torch.cuda.max_memory_allocated(device),
            "free_gpu_memory_bytes_at_end": free_memory,
            "total_gpu_memory_bytes_at_end": total_memory,
        },
        "outputs": {"checkpoint": str(checkpoint_path)},
    }


def write_json_atomic(output: Path, payload: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)


def main() -> int:
    args = parse_args()
    output = require_within_root(args.output, args.project_root)
    try:
        payload = execute_fixture(args, output)
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "status": "fail",
            "run_label": args.run_label,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        write_json_atomic(output, payload)
        raise
    write_json_atomic(output, payload)
    print(json.dumps({"status": "pass", "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

