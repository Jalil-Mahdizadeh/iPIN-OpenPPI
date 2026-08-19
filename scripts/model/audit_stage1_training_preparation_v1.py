#!/usr/bin/env python3
"""Audit and register the frozen Stage 1 public training preparation."""

from pathlib import Path

from ipin_openppi.stage1.constants import VALIDATION_ROOT
from ipin_openppi.stage1.preparation_audit import audit_training_preparation


if __name__ == "__main__":
    root = Path.cwd().resolve(strict=True)
    audit_training_preparation(
        project_root=root,
        registry_path=root / VALIDATION_ROOT / "TRAINING_PREPARATION_REGISTRY.json",
        report_path=root / VALIDATION_ROOT / "TRAINING_PREPARATION_AUDIT_REPORT.json",
    )
