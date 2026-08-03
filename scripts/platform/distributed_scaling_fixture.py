#!/usr/bin/env python3
"""One-node DDP/NCCL throughput fixture for the Arrhenius container gate."""

from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel

SEED = 20260803


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--image-sha256", required=True)
    parser.add_argument("--dimension", type=int, default=4096)
    parser.add_argument("--layers", type=int, default=8)
    parser.add_argument("--local-batch-size", type=int, default=1024)
    parser.add_argument("--warmup-steps", type=int, default=10)
    parser.add_argument("--measured-steps", type=int, default=30)
    return parser.parse_args()


def require_within_root(path: Path, root: Path) -> Path:
    resolved_root = root.resolve(strict=True)
    resolved_path = path.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Output path is outside project root: {resolved_path}") from exc
    return resolved_path


def make_model(dimension: int, layers: int) -> nn.Module:
    modules: list[nn.Module] = []
    for _ in range(layers):
        modules.extend((nn.Linear(dimension, dimension, bias=False), nn.GELU()))
    return nn.Sequential(*modules)


def training_step(
    model: DistributedDataParallel,
    optimizer: torch.optim.Optimizer,
    features: torch.Tensor,
) -> float:
    optimizer.zero_grad(set_to_none=True)
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        output = model(features)
        loss = output.float().square().mean()
    loss.backward()
    optimizer.step()
    return float(loss.detach())


def execute(args: argparse.Namespace, output: Path) -> dict[str, Any] | None:
    if platform.machine() != "aarch64":
        raise RuntimeError(f"Expected aarch64, observed {platform.machine()}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")

    rank = int(os.environ["RANK"])
    local_rank = int(os.environ["LOCAL_RANK"])
    world_size = int(os.environ["WORLD_SIZE"])
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)
    dist.init_process_group(backend="nccl", init_method="env://")

    try:
        if torch.cuda.device_count() != world_size:
            raise RuntimeError(
                f"Visible CUDA devices ({torch.cuda.device_count()}) do not match world size ({world_size})"
            )
        if not torch.cuda.is_bf16_supported():
            raise RuntimeError("BF16 is not supported")

        collective = torch.tensor(float(rank + 1), device=device)
        dist.all_reduce(collective, op=dist.ReduceOp.SUM)
        expected_collective = world_size * (world_size + 1) / 2
        collective_ok = float(collective.cpu()) == expected_collective
        if not collective_ok:
            raise AssertionError(
                f"NCCL all-reduce mismatch: {float(collective.cpu())} != {expected_collective}"
            )

        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED + rank)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False

        model = make_model(args.dimension, args.layers).to(device)
        distributed_model = DistributedDataParallel(
            model,
            device_ids=[local_rank],
            output_device=local_rank,
            broadcast_buffers=False,
            gradient_as_bucket_view=True,
            static_graph=True,
        )
        optimizer = torch.optim.AdamW(
            distributed_model.parameters(),
            lr=1.0e-4,
            weight_decay=1.0e-2,
            fused=True,
        )
        generator = torch.Generator(device=device).manual_seed(SEED + 100 + rank)
        features = torch.randn(
            (args.local_batch_size, args.dimension),
            generator=generator,
            device=device,
        )

        last_loss = 0.0
        for _ in range(args.warmup_steps):
            last_loss = training_step(distributed_model, optimizer, features)
        torch.cuda.synchronize(device)
        dist.barrier()
        torch.cuda.reset_peak_memory_stats(device)

        started = time.perf_counter()
        for _ in range(args.measured_steps):
            last_loss = training_step(distributed_model, optimizer, features)
        torch.cuda.synchronize(device)
        dist.barrier()
        local_elapsed = time.perf_counter() - started

        elapsed_tensor = torch.tensor(local_elapsed, device=device)
        dist.all_reduce(elapsed_tensor, op=dist.ReduceOp.MAX)
        max_elapsed = float(elapsed_tensor.cpu())
        peak_tensor = torch.tensor(torch.cuda.max_memory_allocated(device), device=device, dtype=torch.int64)
        dist.all_reduce(peak_tensor, op=dist.ReduceOp.MAX)
        max_peak_memory = int(peak_tensor.cpu())
        throughput = world_size * args.local_batch_size * args.measured_steps / max_elapsed

        if rank != 0:
            return None

        properties = torch.cuda.get_device_properties(device)
        parameter_count = sum(parameter.numel() for parameter in model.parameters())
        return {
            "schema_version": 1,
            "status": "pass",
            "test": "one_node_ddp_nccl_scaling",
            "run_label": args.run_label,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "seed": SEED,
            "image_sha256": args.image_sha256,
            "platform": {
                "hostname": socket.gethostname(),
                "machine": platform.machine(),
                "python": platform.python_version(),
                "torch": torch.__version__,
                "torch_cuda": torch.version.cuda,
                "nccl": list(torch.cuda.nccl.version()),
                "gpu_name": properties.name,
                "gpu_compute_capability": [properties.major, properties.minor],
                "visible_gpu_count": torch.cuda.device_count(),
                "world_size": world_size,
                "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            },
            "fixture": {
                "dimension": args.dimension,
                "layers": args.layers,
                "parameter_count": parameter_count,
                "local_batch_size": args.local_batch_size,
                "global_batch_size": args.local_batch_size * world_size,
                "warmup_steps": args.warmup_steps,
                "measured_steps": args.measured_steps,
                "precision": "bf16_autocast",
                "optimizer": "fused_AdamW",
                "nccl_all_reduce": "pass",
                "last_loss": last_loss,
            },
            "performance": {
                "max_elapsed_seconds": max_elapsed,
                "aggregate_samples_per_second": throughput,
                "max_peak_gpu_memory_bytes": max_peak_memory,
            },
        }
    finally:
        dist.destroy_process_group()


def write_json_atomic(output: Path, payload: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)


def main() -> int:
    args = parse_args()
    output = require_within_root(args.output, args.project_root)
    rank = int(os.environ.get("RANK", "0"))
    try:
        payload = execute(args, output)
    except Exception as exc:
        if rank == 0:
            write_json_atomic(
                output,
                {
                    "schema_version": 1,
                    "status": "fail",
                    "run_label": args.run_label,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
        raise
    if rank == 0 and payload is not None:
        write_json_atomic(output, payload)
        print(json.dumps({"status": "pass", "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

