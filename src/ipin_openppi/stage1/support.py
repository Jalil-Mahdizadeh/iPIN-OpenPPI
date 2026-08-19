"""Fail-closed filesystem, hashing, and public-input helpers for Stage 1."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

from .constants import FORBIDDEN_PATH_FRAGMENTS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_no_sensitive_path(path: Path) -> None:
    text = "/" + path.as_posix().lstrip("/")
    if any(fragment in text for fragment in FORBIDDEN_PATH_FRAGMENTS):
        raise RuntimeError(f"sensitive path prohibited in Stage 1: {path}")


def resolve_regular_inside(project_root: Path, relative: Path) -> Path:
    if relative.is_absolute():
        raise RuntimeError(f"expected project-relative path: {relative}")
    assert_no_sensitive_path(relative)
    root = project_root.resolve(strict=True)
    lexical = Path(os.path.abspath(os.fspath(root / relative)))
    lexical.relative_to(root)
    current = lexical
    while True:
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"symlink prohibited: {current}")
        if current == root:
            break
        current = current.parent
    if not lexical.is_file():
        raise RuntimeError(f"regular file required: {relative}")
    return lexical


def require_sha256(path: Path, expected: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise RuntimeError(f"SHA-256 mismatch for {path}: {observed} != {expected}")


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"stale temporary output requires review: {temporary}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_numpy(path: Path, array: Any) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"stale temporary output requires review: {temporary}")
    with temporary.open("xb") as handle:
        np.save(handle, array, allow_pickle=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_npz(path: Path, **arrays: Any) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"stale temporary output requires review: {temporary}")
    with temporary.open("xb") as handle:
        np.savez(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def git_commit(project_root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=project_root, text=True
    ).strip()


def require_clean_worktree(project_root: Path, *, allow_prefixes: tuple[str, ...] = ()) -> None:
    output = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=project_root, text=True
    )
    unexpected = []
    for line in output.splitlines():
        path = line[3:]
        if not any(path.startswith(prefix) for prefix in allow_prefixes):
            unexpected.append(line)
    if unexpected:
        raise RuntimeError(f"unexpected dirty worktree entries: {unexpected}")
