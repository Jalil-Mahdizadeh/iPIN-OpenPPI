#!/usr/bin/env python3
"""Audit and register the two frozen Stage 1 embedding snapshots."""

from pathlib import Path

from ipin_openppi.stage1.constants import VALIDATION_ROOT
from ipin_openppi.stage1.embedding_audit import audit_embeddings


if __name__ == "__main__":
    root = Path.cwd().resolve(strict=True)
    validation_root = root / VALIDATION_ROOT
    audit_embeddings(
        project_root=root,
        registry_path=validation_root / "EMBEDDING_ARTIFACT_REGISTRY.json",
        report_path=validation_root / "EMBEDDING_PRODUCTION_AUDIT_REPORT.json",
    )
