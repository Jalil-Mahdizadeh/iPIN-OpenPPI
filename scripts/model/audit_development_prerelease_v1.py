#!/usr/bin/env python3
"""Write the production DEC-0032 pre-release audit report."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ipin_openppi.development_evaluation.audit import run_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/development_release_and_evaluation_execution_v1.yaml"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/validation/development_evaluation/"
            "development_release_and_evaluation_v1/PRE_RELEASE_PRODUCTION_AUDIT_REPORT.json"
        ),
    )
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise RuntimeError(f"refusing to overwrite audit evidence: {output}")
    report = run_audit(root, (root / args.config).resolve(strict=True))
    temporary = output.with_name(output.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output)
    print(
        f"development_prerelease_production_audit: {report['status'].upper()} "
        f"checks={report['check_counts']['total']}"
    )
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
