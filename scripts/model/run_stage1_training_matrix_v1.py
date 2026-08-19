#!/usr/bin/env python3
"""Single-GPU orchestrator for the exact 30-run frozen Stage 1 matrix."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from ipin_openppi.stage1.constants import (
    CHECKPOINT_ROOT,
    MODEL_SIF_SHA256,
    RUN_ROOT,
)
from ipin_openppi.stage1.support import atomic_json, sha256_file


def governed_storage_bytes(project_root: Path) -> int:
    roots = (
        project_root / "artifacts/cache/models/model_governance_and_baseline_training_protocol_v1",
        project_root / "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1",
        project_root / RUN_ROOT,
        project_root / CHECKPOINT_ROOT,
        project_root / "containers/images/ipin-model-arm64_0.1.0.sif",
    )
    total = 0
    for root in roots:
        if root.is_file():
            total += root.stat().st_size
        elif root.is_dir():
            total += sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    return total


def invoke(project_root: Path, run: dict[str, object], *, resume: bool) -> subprocess.CompletedProcess[str]:
    seed = int(run["seed"])
    run_id = str(run["run_id"])
    command = [
        "apptainer",
        "exec",
        "--nv",
        "--cleanenv",
        "--containall",
        "--bind",
        f"{project_root}:{project_root}",
        "--pwd",
        str(project_root),
        "--env",
        f"PYTHONHASHSEED={seed}",
        str(project_root / "containers/images/ipin-model-arm64_0.1.0.sif"),
        "env",
        "PYTHONPATH=src",
        "python",
        "scripts/model/train_stage1_models_v1.py",
        "--run-id",
        run_id,
    ]
    if resume:
        command.append("--resume-infrastructure")
    completed = subprocess.run(command, capture_output=True, text=True)
    log_root = project_root / RUN_ROOT / "orchestrator_logs"
    log_root.mkdir(parents=True, exist_ok=True)
    attempt = "resume1" if resume else "initial"
    atomic_json(
        log_root / f"{run_id}.{attempt}.json",
        {
            "command": command,
            "returncode": completed.returncode,
            "stderr": completed.stderr,
            "stdout": completed.stdout,
        },
    )
    return completed


def main() -> int:
    project_root = Path.cwd().resolve(strict=True)
    sif = project_root / "containers/images/ipin-model-arm64_0.1.0.sif"
    if sha256_file(sif) != MODEL_SIF_SHA256:
        raise RuntimeError("model SIF hash drift")
    matrix = json.loads((project_root / RUN_ROOT / "MATRIX_MANIFEST.json").read_text())
    if matrix["run_count"] != 30 or len(matrix["runs"]) != 30:
        raise RuntimeError("matrix is not exactly 30 runs")
    started = time.monotonic()
    for position, run in enumerate(matrix["runs"], start=1):
        run_id = str(run["run_id"])
        result_path = project_root / RUN_ROOT / "runs" / run_id / "RUN_RESULT.json"
        if result_path.exists():
            result = json.loads(result_path.read_text())
            if result["status"] in ("complete", "failed_numerical_or_integrity", "failed_infrastructure"):
                print(f"[{position}/30] closed {run_id}: {result['status']}", flush=True)
                continue
        storage = governed_storage_bytes(project_root)
        if storage > 100 * 2**30:
            raise RuntimeError("100 GiB governed storage ceiling exceeded")
        print(f"[{position}/30] starting {run_id}", flush=True)
        completed = invoke(project_root, run, resume=False)
        if completed.returncode != 0:
            if result_path.exists():
                result = json.loads(result_path.read_text())
                if result["status"] == "failed_numerical_or_integrity":
                    print(f"[{position}/30] fail-closed numerical/integrity {run_id}", flush=True)
                    continue
            checkpoints = sorted((project_root / CHECKPOINT_ROOT / run_id).glob("pass_*.pt"))
            if checkpoints:
                print(f"[{position}/30] exact infrastructure resume {run_id}", flush=True)
                resumed = invoke(project_root, run, resume=True)
                if resumed.returncode == 0:
                    continue
            atomic_json(
                result_path,
                {
                    "replacement_recipe_or_seed": False,
                    "run_id": run_id,
                    "status": "failed_infrastructure",
                },
            )
            print(f"[{position}/30] fail-closed infrastructure {run_id}", flush=True)
            continue
        result = json.loads(result_path.read_text())
        print(
            f"[{position}/30] complete {run_id}; selected pass {result['selected_pass']}; "
            f"{result['gpu_hours_this_attempt']:.4f} GPU h",
            flush=True,
        )
        elapsed_hours = (time.monotonic() - started) / 3600.0
        if elapsed_hours > 100:
            raise RuntimeError("100 GPU-hour ceiling exceeded")
    print("matrix execution closed all 30 run IDs", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
