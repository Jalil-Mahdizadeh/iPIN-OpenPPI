#!/usr/bin/env python3
"""Verify the public Git deposit without models, protected data or third-party packages."""

import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "artifacts/reports/repository_deposit_v1/PUBLICATION_MANIFEST.json"


def fingerprint(stream):
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
        size += len(block)
    return size, digest.hexdigest()


def repository_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Manifest path is outside repository: " + relative)
    return path


def verify_file(record):
    with repository_path(record["path"]).open("rb") as stream:
        size, digest = fingerprint(stream)
    if size != record["bytes"] or digest != record["sha256"]:
        raise ValueError("Fingerprint mismatch: " + record["path"])


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = [record["path"] for record in manifest["files"]]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate paths in publication manifest")
    for record in manifest["files"]:
        verify_file(record)

    registry_files = 0
    for record in manifest["preserved_registries"]:
        verify_file(record)
        registry = json.loads(repository_path(record["path"]).read_text(encoding="utf-8"))
        for artifact in registry[record["entries_key"]]:
            verify_file(artifact)
            registry_files += 1

    for record in manifest["compressed_public_tables"]:
        with gzip.open(repository_path(record["path"]), "rb") as stream:
            size, digest = fingerprint(stream)
        if size != record["uncompressed_bytes"] or digest != record["uncompressed_sha256"]:
            raise ValueError("Decompressed fingerprint mismatch: " + record["path"])

    print(json.dumps({
        "status": "pass",
        "public_files_verified": len(paths),
        "preserved_registry_artifacts_verified": registry_files,
        "lossless_tables_verified": len(manifest["compressed_public_tables"]),
        "protected_data_or_models_required": False,
    }, indent=2))


if __name__ == "__main__":
    main()
