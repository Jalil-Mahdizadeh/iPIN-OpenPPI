#!/usr/bin/env python3
"""Execute one exact frozen Stage 1 public-training run."""

from __future__ import annotations

import argparse
from pathlib import Path

from ipin_openppi.stage1.training import run_training


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--resume-infrastructure", action="store_true")
    args = parser.parse_args()
    run_training(
        project_root=Path.cwd().resolve(strict=True),
        run_id=args.run_id,
        resume_infrastructure=args.resume_infrastructure,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
