"""Typed context shared by source parsers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .common import RawAsset
from .schema import SchemaContract


@dataclass(frozen=True)
class ParsingContext:
    project_root: Path
    config_path: Path
    config: Mapping[str, Any]
    assets: Mapping[str, RawAsset]
    evidence_contract: SchemaContract
    staging_contract: SchemaContract
    parser_git_commit: str
    parser_version: str
    container_sif_sha256: str

    @property
    def batch_rows(self) -> int:
        return int(self.config["runtime"]["batch_rows"])

    @property
    def compression(self) -> str:
        return str(self.config["runtime"]["parquet_compression"])

    @property
    def compression_level(self) -> int:
        return int(self.config["runtime"]["parquet_compression_level"])

    def asset(self, asset_id: str) -> RawAsset:
        try:
            return self.assets[asset_id]
        except KeyError as exc:
            raise RuntimeError(
                f"Configured acquisition asset is absent: {asset_id}"
            ) from exc

    def writer_kwargs(self) -> dict[str, Any]:
        return {
            "batch_rows": self.batch_rows,
            "compression": self.compression,
            "compression_level": self.compression_level,
            "extra_metadata": {
                "parser_version": self.parser_version,
                "parser_git_commit": self.parser_git_commit,
                "container_sif_sha256": self.container_sif_sha256,
            },
        }
