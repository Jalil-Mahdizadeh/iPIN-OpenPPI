#!/usr/bin/env python3
"""Acquire the two DEC-0028 ESM-2 snapshots into link-free local custody."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


PROTOCOL_ID = "model_governance_and_baseline_training_protocol_v1"
REQUIRED_FILES = (
    "README.md",
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer_config.json",
    "vocab.txt",
)
CANDIDATES: dict[str, dict[str, Any]] = {
    "esm2_150m": {
        "repository": "facebook/esm2_t30_150M_UR50D",
        "revision": "a695f6045e2e32885fa60af20c13cb35398ce30c",
        "checkpoint_sha256": "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566",
        "checkpoint_bytes": 595_257_706,
    },
    "esm2_650m": {
        "repository": "facebook/esm2_t33_650M_UR50D",
        "revision": "08e4846e537177426273712802403f7ba8261b6c",
        "checkpoint_sha256": "a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0",
        "checkpoint_bytes": 2_609_506_392,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def assert_within_project(path: Path, project_root: Path) -> None:
    resolved_root = project_root.resolve(strict=True)
    resolved = path.resolve(strict=False)
    if os.path.commonpath((str(resolved_root), str(resolved))) != str(resolved_root):
        raise RuntimeError(f"path escapes project root: {path}")


def assert_link_free(path: Path, stop: Path) -> None:
    stop = stop.resolve(strict=True)
    current = path
    while current != stop:
        if current.exists() and current.is_symlink():
            raise RuntimeError(f"symlink prohibited in model custody: {current}")
        if current.parent == current:
            raise RuntimeError(f"custody path does not descend from project: {path}")
        current = current.parent


def download(url: str, destination: Path) -> tuple[int, str]:
    partial = destination.with_name(destination.name + ".part")
    if partial.exists():
        raise RuntimeError(f"stale partial download must be reviewed: {partial}")
    request = urllib.request.Request(url, headers={"User-Agent": "iPIN-OpenPPI/1.0"})
    digest = hashlib.sha256()
    size = 0
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("xb") as out:
            while block := response.read(8 * 1024 * 1024):
                out.write(block)
                digest.update(block)
                size += len(block)
                if size // (256 * 1024 * 1024) != (size - len(block)) // (256 * 1024 * 1024):
                    print(f"  {destination.name}: {size / 2**30:.2f} GiB", flush=True)
            out.flush()
            os.fsync(out.fileno())
        os.replace(partial, destination)
    except BaseException:
        if partial.exists():
            partial.unlink()
        raise
    print(f"  acquired {destination.name}: {size} bytes in {time.monotonic() - started:.1f}s", flush=True)
    return size, digest.hexdigest()


def git_commit(project_root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=project_root, text=True
    ).strip()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".tmp")
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with partial.open("x", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(partial, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=Path("artifacts/cache/models") / PROTOCOL_ID,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/validation/model_execution/stage1_model_execution_v1/MODEL_CUSTODY_MANIFEST.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve(strict=True)
    cache_root = args.cache_root if args.cache_root.is_absolute() else project_root / args.cache_root
    manifest_path = args.manifest if args.manifest.is_absolute() else project_root / args.manifest
    assert_within_project(cache_root, project_root)
    assert_within_project(manifest_path, project_root)
    assert_link_free(cache_root, project_root)
    cache_root.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for candidate_id, spec in CANDIDATES.items():
        candidate_root = cache_root / candidate_id
        assert_link_free(candidate_root, project_root)
        candidate_root.mkdir(parents=False, exist_ok=True)
        print(f"Acquiring {candidate_id} at {spec['revision']}", flush=True)
        files: list[dict[str, Any]] = []
        for filename in REQUIRED_FILES:
            destination = candidate_root / filename
            assert_link_free(destination, project_root)
            if destination.exists():
                if destination.is_symlink() or not destination.is_file():
                    raise RuntimeError(f"custody object is not a regular file: {destination}")
                size = destination.stat().st_size
                digest = sha256_file(destination)
                disposition = "verified_existing"
            else:
                url = (
                    f"https://huggingface.co/{spec['repository']}/resolve/"
                    f"{spec['revision']}/{filename}?download=true"
                )
                size, digest = download(url, destination)
                disposition = "downloaded"
            if filename == "model.safetensors":
                if size != spec["checkpoint_bytes"] or digest != spec["checkpoint_sha256"]:
                    raise RuntimeError(f"frozen checkpoint mismatch for {candidate_id}")
            files.append(
                {
                    "bytes": size,
                    "filename": filename,
                    "path": str(destination.relative_to(project_root)),
                    "sha256": digest,
                    "source_url": (
                        f"https://huggingface.co/{spec['repository']}/resolve/"
                        f"{spec['revision']}/{filename}"
                    ),
                    "status": disposition,
                }
            )
        unexpected = sorted(p.name for p in candidate_root.iterdir() if p.name not in REQUIRED_FILES)
        if unexpected:
            raise RuntimeError(f"unexpected custody files for {candidate_id}: {unexpected}")
        records.append(
            {
                "candidate_id": candidate_id,
                "files": files,
                "repository": spec["repository"],
                "repository_revision": spec["revision"],
                "trust_remote_code": False,
            }
        )

    payload = {
        "acquisition_network_boundary": "network_used_only_for_this_exact_revision_acquisition",
        "candidates": records,
        "code_commit": git_commit(project_root),
        "pickle_weights_present": False,
        "protocol_configuration_sha256": "3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5",
        "protocol_id": PROTOCOL_ID,
        "required_files": list(REQUIRED_FILES),
        "schema_version": 1,
        "symlinks_present": False,
    }
    atomic_json(manifest_path, payload)
    print(manifest_path.relative_to(project_root))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
