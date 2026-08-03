#!/usr/bin/env python3
"""Hardened entry point for independent raw-acquisition verification."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


ENTRYPOINT = Path(__file__).resolve()
IMPLEMENTATION = ENTRYPOINT.with_name("verify_raw_acquisition.py")
SPEC = importlib.util.spec_from_file_location("raw_verification_implementation", IMPLEMENTATION)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load verification implementation: {IMPLEMENTATION}")
IMPL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPL)


VerificationError = IMPL.VerificationError


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_repo_path(repo_root: Path, relative: str, prefix: str | None = None) -> Path:
    unresolved = repo_root / relative
    try:
        relative_parts = unresolved.relative_to(repo_root).parts
    except ValueError as exc:
        raise VerificationError(f"path leaves repository: {relative}") from exc
    current = repo_root
    for part in relative_parts:
        current = current / part
        if current.is_symlink():
            raise VerificationError(f"symbolic-link path component is prohibited: {current}")
    candidate = unresolved.resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise VerificationError(f"path leaves repository: {relative}") from exc
    if prefix is not None and not relative.startswith(prefix):
        raise VerificationError(f"path is outside required prefix {prefix}: {relative}")
    IMPL.ensure_regular_unlinked(candidate, relative)
    return candidate


def verifier_git_identity(repo_root: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if status:
        raise VerificationError(f"tracked worktree must be clean for verification: {status}")
    return {"commit": commit, "tracked_worktree_clean": True}


ORIGINAL_ATOMIC_JSON = IMPL.atomic_json


def provenance_atomic_json(repo_root: Path, path: Path, value: dict[str, Any]) -> None:
    value["verifier_code"] = {
        "git": verifier_git_identity(repo_root),
        "entrypoint": str(ENTRYPOINT.relative_to(repo_root)),
        "entrypoint_sha256": sha256_file(ENTRYPOINT),
        "implementation": str(IMPLEMENTATION.relative_to(repo_root)),
        "implementation_sha256": sha256_file(IMPLEMENTATION),
    }
    ORIGINAL_ATOMIC_JSON(repo_root, path, value)


IMPL.ensure_repo_path = ensure_repo_path
IMPL.atomic_json = provenance_atomic_json


def main() -> int:
    return IMPL.main()


if __name__ == "__main__":
    raise SystemExit(main())
