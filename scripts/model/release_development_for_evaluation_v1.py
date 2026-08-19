#!/usr/bin/env python3
"""Perform the single DEC-0032 development-only release after activation."""

from __future__ import annotations

import argparse
from pathlib import Path

from ipin_openppi.development_evaluation.release import release_development_once


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--execution-config",
        type=Path,
        default=Path("configs/development_release_and_evaluation_execution_v1.yaml"),
    )
    parser.add_argument("--activation-gate", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    result = release_development_once(
        project_root=root,
        execution_config_path=(root / args.execution_config).resolve(strict=True),
        activation_gate_path=(root / args.activation_gate).resolve(strict=True),
    )
    print(
        "development_release: PASS "
        f"tables={result['development_table_count']} rows={result['development_table_rows']}"
    )


if __name__ == "__main__":
    main()
