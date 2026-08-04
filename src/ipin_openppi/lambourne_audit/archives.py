"""Safe, non-extracting inventory of the archived Lambourne code and inputs."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import stat
import tarfile
from typing import Callable
import zipfile


MAX_SELECTED_MEMBER_BYTES = 512 * 1024 * 1024


def _safe_member_name(name: str) -> str:
    token = name.replace("\\", "/")
    pure = PurePosixPath(token)
    if not token or pure.is_absolute() or ".." in pure.parts or "\x00" in token:
        raise RuntimeError(f"Unsafe archive member path: {name!r}")
    normalized = pure.as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized in {"", "."}:
        raise RuntimeError(f"Unsafe empty archive member path: {name!r}")
    return normalized


def scan_zip_archive(
    path: Path,
    *,
    asset_id: str,
    archive_sha256: str,
    select: Callable[[str], bool],
) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    inventory: list[dict[str, object]] = []
    selected: dict[str, bytes] = {}
    with zipfile.ZipFile(path) as archive:
        seen: set[str] = set()
        for ordinal, info in enumerate(archive.infolist(), start=1):
            name = _safe_member_name(info.filename)
            if name in seen:
                raise RuntimeError(f"Duplicate ZIP member path: {name}")
            seen.add(name)
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise RuntimeError(f"ZIP symbolic links are prohibited: {name}")
            kind = "directory" if info.is_dir() else "regular_file"
            chosen = kind == "regular_file" and bool(select(name))
            digest: str | None = None
            if chosen:
                if info.file_size > MAX_SELECTED_MEMBER_BYTES:
                    raise RuntimeError(f"Selected ZIP member exceeds limit: {name}")
                payload = archive.read(info)
                if len(payload) != info.file_size:
                    raise RuntimeError(f"Truncated ZIP member: {name}")
                digest = hashlib.sha256(payload).hexdigest()
                selected[name] = payload
            inventory.append(
                {
                    "archive_asset_id": asset_id,
                    "archive_format": "zip",
                    "member_ordinal": ordinal,
                    "member_path": name,
                    "member_type": kind,
                    "uncompressed_bytes": int(info.file_size),
                    "compressed_bytes": int(info.compress_size),
                    "selected_for_semantics": chosen,
                    "member_sha256": digest,
                    "archive_sha256": archive_sha256,
                    "safety_state": "safe_regular_or_directory_no_extraction",
                }
            )
    return inventory, selected


def scan_tar_gzip_archive(
    path: Path,
    *,
    asset_id: str,
    archive_sha256: str,
    select: Callable[[str], bool],
) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    """Stream the archive once; inventory headers and retain only bounded selected files."""
    inventory: list[dict[str, object]] = []
    selected: dict[str, bytes] = {}
    seen: set[str] = set()
    with tarfile.open(path, mode="r|gz") as archive:
        for ordinal, info in enumerate(archive, start=1):
            name = _safe_member_name(info.name)
            if name in seen:
                raise RuntimeError(f"Duplicate TAR member path: {name}")
            seen.add(name)
            if info.issym() or info.islnk():
                raise RuntimeError(f"TAR links are prohibited: {name}")
            if info.isdir():
                kind = "directory"
            elif info.isreg():
                kind = "regular_file"
            else:
                raise RuntimeError(f"Unsupported TAR member type: {name}")
            chosen = kind == "regular_file" and bool(select(name))
            digest: str | None = None
            if chosen:
                if info.size > MAX_SELECTED_MEMBER_BYTES:
                    raise RuntimeError(f"Selected TAR member exceeds limit: {name}")
                handle = archive.extractfile(info)
                if handle is None:
                    raise RuntimeError(f"Cannot read selected TAR member: {name}")
                payload = handle.read(MAX_SELECTED_MEMBER_BYTES + 1)
                if len(payload) != info.size:
                    raise RuntimeError(f"Truncated or oversized TAR member: {name}")
                digest = hashlib.sha256(payload).hexdigest()
                selected[name] = payload
            inventory.append(
                {
                    "archive_asset_id": asset_id,
                    "archive_format": "tar_gzip",
                    "member_ordinal": ordinal,
                    "member_path": name,
                    "member_type": kind,
                    "uncompressed_bytes": int(info.size),
                    "compressed_bytes": None,
                    "selected_for_semantics": chosen,
                    "member_sha256": digest,
                    "archive_sha256": archive_sha256,
                    "safety_state": "safe_regular_or_directory_no_extraction",
                }
            )
    return inventory, selected
