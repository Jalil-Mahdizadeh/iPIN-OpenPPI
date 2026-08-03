"""Shared ingestion primitives with deterministic IDs and atomic Parquet output."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from typing import Any, Iterable, Mapping
import uuid

import pyarrow as pa
import pyarrow.parquet as pq

from .schema import SchemaContract, sha256_file


EMPTY_JSON = "{}"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_id(prefix: str, *parts: Any, length: int = 32) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = str(part).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"{prefix}:{digest.hexdigest()[:length]}"


def strip_version(identifier: str) -> str:
    return re.sub(r"\.\d+$", "", identifier)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_apptainer() -> None:
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Scientific parsing must run inside Apptainer")


def project_root_from(path: Path) -> Path:
    resolved = path.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "data").is_dir():
            return candidate
    raise RuntimeError(f"Could not locate project root from {path}")


def git_provenance(project_root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=project_root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return completed.stdout.strip()

    status = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD"),
        "status": status,
        "tracked_worktree_clean": not bool(status),
    }


@dataclass(frozen=True)
class RawAsset:
    asset_id: str
    source_key: str
    path: Path
    relative_path: str
    sha256: str
    bytes: int
    acquired_at_utc: str
    source_manifest: str


def load_asset_index(
    project_root: Path, manifest_path: Path
) -> tuple[dict[str, Any], dict[str, RawAsset]]:
    absolute_manifest = (project_root / manifest_path).resolve(strict=True)
    with absolute_manifest.open("rt", encoding="utf-8") as handle:
        manifest = json.load(handle)
    assets: dict[str, RawAsset] = {}
    for record in manifest["records"]:
        relative = str(record["destination"])
        path = (project_root / relative).resolve(strict=True)
        try:
            path.relative_to((project_root / "data/raw").resolve())
        except ValueError as exc:
            raise RuntimeError(f"Raw asset escapes data/raw: {relative}") from exc
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Raw asset is not a regular non-link file: {relative}")
        assets[str(record["asset_id"])] = RawAsset(
            asset_id=str(record["asset_id"]),
            source_key=str(record["source_key"]),
            path=path,
            relative_path=relative,
            sha256=str(record["sha256"]),
            bytes=int(record["bytes"]),
            acquired_at_utc=str(record["acquired_at_utc"]),
            source_manifest=str(record["source_manifest"]),
        )
    if len(assets) != len(manifest["records"]):
        raise RuntimeError("Acquisition manifest contains duplicate asset_id values")
    return manifest, assets


def verify_asset(asset: RawAsset) -> dict[str, Any]:
    info = asset.path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"Raw asset changed type: {asset.relative_path}")
    if info.st_size != asset.bytes:
        raise RuntimeError(
            f"Raw asset size mismatch for {asset.relative_path}: "
            f"{info.st_size} != {asset.bytes}"
        )
    observed_sha256 = sha256_file(asset.path)
    if observed_sha256 != asset.sha256:
        raise RuntimeError(
            f"Raw asset SHA-256 mismatch for {asset.relative_path}: "
            f"{observed_sha256} != {asset.sha256}"
        )
    if info.st_mode & 0o222:
        raise RuntimeError(f"Raw asset became writable: {asset.relative_path}")
    return {
        "asset_id": asset.asset_id,
        "path": asset.relative_path,
        "bytes": info.st_size,
        "sha256": observed_sha256,
        "read_only": True,
    }


class ParquetBatchWriter(AbstractContextManager["ParquetBatchWriter"]):
    """Write validated, fixed-schema Parquet parts and retain exact statistics."""

    def __init__(
        self,
        output_dir: Path,
        contract: SchemaContract,
        table_name: str,
        *,
        batch_rows: int,
        compression: str,
        compression_level: int | None,
        extra_metadata: Mapping[str, str] | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.contract = contract
        self.table_name = table_name
        self.batch_rows = batch_rows
        self.compression = compression
        self.compression_level = compression_level
        self.rows: list[Mapping[str, Any]] = []
        self.row_count = 0
        self.part_count = 0
        self.files: list[dict[str, Any]] = []
        schema = contract.arrow_schema(table_name)
        metadata = dict(schema.metadata or {})
        for key, value in (extra_metadata or {}).items():
            metadata[f"ipin.{key}".encode()] = str(value).encode()
        self.schema = schema.with_metadata(metadata)

    def __enter__(self) -> "ParquetBatchWriter":
        self.output_dir.mkdir(parents=True, exist_ok=False)
        return self

    def append(self, row: Mapping[str, Any]) -> None:
        self.rows.append(row)
        if len(self.rows) >= self.batch_rows:
            self.flush()

    def extend(self, rows: Iterable[Mapping[str, Any]]) -> None:
        for row in rows:
            self.append(row)

    def flush(self) -> None:
        if not self.rows:
            return
        normalized = self.contract.normalize_and_validate_rows(
            self.table_name, self.rows
        )
        table = pa.Table.from_pylist(normalized, schema=self.schema)
        filename = f"part-{self.part_count:05d}.parquet"
        path = self.output_dir / filename
        pq.write_table(
            table,
            path,
            compression=self.compression,
            compression_level=self.compression_level,
            use_dictionary=True,
            write_statistics=True,
            row_group_size=self.batch_rows,
        )
        file_rows = table.num_rows
        self.files.append(
            {
                "path": path.as_posix(),
                "rows": file_rows,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
        self.row_count += file_rows
        self.part_count += 1
        self.rows.clear()

    def close(self) -> None:
        self.flush()
        if self.part_count == 0:
            empty = pa.Table.from_pylist([], schema=self.schema)
            path = self.output_dir / "part-00000.parquet"
            pq.write_table(
                empty,
                path,
                compression=self.compression,
                compression_level=self.compression_level,
            )
            self.files.append(
                {
                    "path": path.as_posix(),
                    "rows": 0,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
            self.part_count = 1

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is None:
            self.close()
        return False

    def summary(self) -> dict[str, Any]:
        return {
            "table": self.table_name,
            "rows": self.row_count,
            "parts": self.part_count,
            "files": self.files,
            "schema_name": self.contract.name,
            "schema_version": self.contract.version,
            "schema_sha256": self.contract.sha256,
        }


class AtomicDatasetDirectory(AbstractContextManager[Path]):
    """Create a dataset in a sibling temporary directory, then rename atomically."""

    def __init__(self, target: Path) -> None:
        self.target = target
        self.temporary = target.parent / f".{target.name}.incomplete-{uuid.uuid4().hex}"

    def __enter__(self) -> Path:
        if self.target.exists() or self.target.is_symlink():
            raise FileExistsError(f"Output target already exists: {self.target}")
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.temporary.mkdir(parents=False, exist_ok=False)
        return self.temporary

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is None:
            self.temporary.rename(self.target)
        elif self.temporary.is_dir() and not self.temporary.is_symlink():
            shutil.rmtree(self.temporary)
        return False
