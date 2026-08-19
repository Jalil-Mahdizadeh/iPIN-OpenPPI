#!/usr/bin/env python3
"""Write the production completed-development registry and audit report."""

from __future__ import annotations

import argparse
from pathlib import Path

from ipin_openppi.development_evaluation.completed_audit import write_completed_evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/development_release_and_evaluation_execution_v1.yaml"),
    )
    parser.add_argument("--production-source-commit", required=True)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path(
            "artifacts/validation/development_evaluation/"
            "development_release_and_evaluation_v1/DEVELOPMENT_EVALUATION_REGISTRY.json"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "artifacts/validation/development_evaluation/"
            "development_release_and_evaluation_v1/COMPLETED_EVALUATION_PRODUCTION_AUDIT_REPORT.json"
        ),
    )
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    registry, report = write_completed_evidence(
        project_root=root,
        config_path=(root / args.config).resolve(strict=True),
        production_source_commit=str(args.production_source_commit),
        registry_path=root / args.registry,
        report_path=root / args.report,
    )
    print(
        "development_completed_production_audit: "
        f"{report['status'].upper()} checks={report['check_counts']['total']} "
        f"cells={registry['cell_count']} scorers={registry['scorer_count']}"
    )
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
