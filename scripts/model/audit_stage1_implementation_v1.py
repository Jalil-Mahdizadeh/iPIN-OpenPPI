#!/usr/bin/env python3
"""Run the production Stage 1 implementation audit."""

from pathlib import Path

from ipin_openppi.stage1.audit import audit_stage1_implementation
from ipin_openppi.stage1.constants import VALIDATION_ROOT


if __name__ == "__main__":
    root = Path.cwd().resolve(strict=True)
    audit_stage1_implementation(
        root, root / VALIDATION_ROOT / "STAGE1_IMPLEMENTATION_AUDIT_REPORT.json"
    )
