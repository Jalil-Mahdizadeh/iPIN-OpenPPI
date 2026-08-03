#!/usr/bin/env python3
"""Compare repeated platform fixtures and emit a gate result."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True, type=Path)
    parser.add_argument("--right", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tolerance", type=float, default=1.0e-6)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    left = json.loads(args.left.read_text(encoding="utf-8"))
    right = json.loads(args.right.read_text(encoding="utf-8"))
    checks = {
        "both_runs_pass": left.get("status") == right.get("status") == "pass",
        "same_image": left.get("image_sha256") == right.get("image_sha256"),
        "same_machine_architecture": left.get("platform", {}).get("machine") == right.get("platform", {}).get("machine") == "aarch64",
        "bf16_supported": bool(left.get("platform", {}).get("bf16_supported")) and bool(right.get("platform", {}).get("bf16_supported")),
        "checkpoint_restart_exact": bool(left.get("fixture", {}).get("checkpoint_restart_exact")) and bool(right.get("fixture", {}).get("checkpoint_restart_exact")),
        "same_matmul_digest": left.get("fixture", {}).get("matmul_digest") == right.get("fixture", {}).get("matmul_digest"),
        "same_model_digest": left.get("fixture", {}).get("final_model_digest") == right.get("fixture", {}).get("final_model_digest"),
        "matmul_mean_within_tolerance": abs(left.get("fixture", {}).get("matmul_mean", float("inf")) - right.get("fixture", {}).get("matmul_mean", float("-inf"))) <= args.tolerance,
        "resume_loss_within_tolerance": abs(left.get("fixture", {}).get("resumed_loss", float("inf")) - right.get("fixture", {}).get("resumed_loss", float("-inf"))) <= args.tolerance,
    }
    status = "pass" if all(checks.values()) else "fail"
    payload = {
        "schema_version": 1,
        "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tolerance": args.tolerance,
        "left": str(args.left),
        "right": str(args.right),
        "checks": checks,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "output": str(args.output)}, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

