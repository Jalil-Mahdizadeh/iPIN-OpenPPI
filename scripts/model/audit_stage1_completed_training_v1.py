#!/usr/bin/env python3
"""Audit completed Stage 1 runs and freeze the complete training registry."""

from pathlib import Path

from ipin_openppi.stage1.constants import VALIDATION_ROOT
from ipin_openppi.stage1.training_audit import audit_completed_training


if __name__ == "__main__":
    root = Path.cwd().resolve(strict=True)
    audit_completed_training(
        project_root=root,
        registry_path=root / VALIDATION_ROOT / "TRAINING_ARTIFACT_REGISTRY.json",
        report_path=root / VALIDATION_ROOT / "TRAINING_PRODUCTION_AUDIT_REPORT.json",
    )
