"""Frozen reconciliation provenance and safe SQL literal helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReconciliationProvenance:
    parse_manifest_sha256: str
    version: str
    git_commit: str
    container_sif_sha256: str
    schema_version: int
    schema_sha256: str
    frozen_taxid: int
    protein_molecule_type_ac: str
    sifts_declared_uniprot_release: str
    frozen_uniprot_release: str


def sql_string(value: str | Path) -> str:
    text = str(value)
    if "\x00" in text:
        raise ValueError("SQL string contains NUL")
    return "'" + text.replace("'", "''") + "'"


def parquet_glob(root: Path, source: str, table: str) -> str:
    return (root / source / table / "*.parquet").as_posix()
