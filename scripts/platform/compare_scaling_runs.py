#!/usr/bin/env python3
"""Evaluate one-node four-GPU scaling against the frozen container gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--single", required=True, type=Path)
    parser.add_argument("--four", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-efficiency", type=float, default=0.70)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    single = json.loads(args.single.read_text(encoding="utf-8"))
    four = json.loads(args.four.read_text(encoding="utf-8"))
    single_throughput = single.get("performance", {}).get("aggregate_samples_per_second", 0.0)
    four_throughput = four.get("performance", {}).get("aggregate_samples_per_second", 0.0)
    efficiency = four_throughput / (4.0 * single_throughput) if single_throughput > 0 else 0.0
    checks = {
        "both_runs_pass": single.get("status") == four.get("status") == "pass",
        "same_image": single.get("image_sha256") == four.get("image_sha256"),
        "single_world_size_is_one": single.get("platform", {}).get("world_size") == 1,
        "four_world_size_is_four": four.get("platform", {}).get("world_size") == 4,
        "single_nccl_all_reduce_pass": single.get("fixture", {}).get("nccl_all_reduce") == "pass",
        "four_nccl_all_reduce_pass": four.get("fixture", {}).get("nccl_all_reduce") == "pass",
        "scaling_efficiency_at_least_threshold": efficiency >= args.minimum_efficiency,
    }
    status = "pass" if all(checks.values()) else "fail"
    payload = {
        "schema_version": 1,
        "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "single_gpu_samples_per_second": single_throughput,
        "four_gpu_samples_per_second": four_throughput,
        "scaling_efficiency": efficiency,
        "minimum_efficiency": args.minimum_efficiency,
        "checks": checks,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "scaling_efficiency": efficiency}, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

