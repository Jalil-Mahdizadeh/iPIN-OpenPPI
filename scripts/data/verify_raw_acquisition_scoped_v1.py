#!/usr/bin/env python3
"""Verify one immutable acquisition within a manifest-backed shared raw tree."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ENTRYPOINT = Path(__file__).resolve()
ACTIVE_ENTRYPOINT = ENTRYPOINT.with_name("verify_raw_acquisition_v3.py")
SPEC = importlib.util.spec_from_file_location(
    "active_raw_acquisition_verifier", ACTIVE_ENTRYPOINT
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load active verifier: {ACTIVE_ENTRYPOINT}")
ACTIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ACTIVE)
IMPL = ACTIVE.IMPL
VerificationError = IMPL.VerificationError


STRICT_UNIPROT_METALINK = IMPL.verify_uniprot_metalink
PREVIOUS_ATOMIC_JSON = IMPL.atomic_json


def selected_source_uniprot_metalink(
    records: list[dict[str, Any]], repo_root: Path
) -> dict[str, Any]:
    """Apply the strict UniProt check only when UniProt belongs to this acquisition."""
    selected_sources = sorted({record["source_key"] for record in records})
    if "uniprot" in selected_sources:
        return STRICT_UNIPROT_METALINK(records, repo_root)
    return {
        "status": "not_applicable_source_not_selected",
        "selected_sources": selected_sources,
        "acquired_payloads_crosschecked": [],
        "reason": "this acquisition contains no UniProt release payload",
    }


def _manifest_declared_raw_paths(repo_root: Path) -> tuple[set[Path], list[str]]:
    manifest_root = repo_root / "data/source_manifests/acquisitions"
    if not manifest_root.is_dir() or manifest_root.is_symlink():
        raise VerificationError(f"invalid acquisition-manifest root: {manifest_root}")
    declared: set[Path] = set()
    used: list[str] = []
    for directory, directory_names, file_names in os.walk(manifest_root, followlinks=False):
        directory_path = Path(directory)
        linked_directories = [
            name for name in directory_names if (directory_path / name).is_symlink()
        ]
        if linked_directories:
            raise VerificationError(
                f"linked acquisition-manifest directories are prohibited: {linked_directories}"
            )
        if "ACQUISITION_MANIFEST.json" not in file_names:
            continue
        path = directory_path / "ACQUISITION_MANIFEST.json"
        if path.is_symlink() or not path.is_file():
            raise VerificationError(f"invalid acquisition manifest: {path}")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("status") != "pass" or manifest.get("errors"):
            continue
        records = manifest.get("records")
        if not isinstance(records, list):
            raise VerificationError(f"acquisition records are not a list: {path}")
        for record in records:
            for field in ("destination", "sidecar"):
                relative = record.get(field)
                if not isinstance(relative, str) or not relative.startswith("data/raw/"):
                    raise VerificationError(f"invalid {field} in {path}: {relative!r}")
                candidate = (repo_root / relative).resolve()
                try:
                    candidate.relative_to((repo_root / "data/raw").resolve())
                except ValueError as exc:
                    raise VerificationError(
                        f"manifest-declared raw path leaves data/raw: {relative}"
                    ) from exc
                declared.add(Path(relative))
        used.append(str(path.relative_to(repo_root)))
    return declared, sorted(used)


def manifest_backed_raw_tree_inventory(
    repo_root: Path, expected_paths: set[Path]
) -> dict[str, Any]:
    """Validate a shared raw tree without treating another acquisition as unexpected."""
    raw_root = (repo_root / "data/raw").resolve()
    if not raw_root.is_dir() or raw_root.is_symlink():
        raise VerificationError(f"invalid raw root: {raw_root}")
    observed: set[Path] = set()
    linked: list[str] = []
    partials: list[str] = []
    for directory, directory_names, file_names in os.walk(raw_root, followlinks=False):
        directory_path = Path(directory)
        for name in list(directory_names):
            path = directory_path / name
            if path.is_symlink():
                linked.append(str(path.relative_to(repo_root)))
        for name in file_names:
            path = directory_path / name
            relative = path.relative_to(repo_root)
            if path.is_symlink():
                linked.append(str(relative))
            observed.add(relative)
            if name.endswith(".partial") or ".partial." in name:
                partials.append(str(relative))

    declared, manifests = _manifest_declared_raw_paths(repo_root)
    allowed = declared | {Path("data/raw/README.md")}
    unmanifested = sorted(str(path) for path in observed - allowed)
    missing_selected = sorted(str(path) for path in expected_paths - observed)
    if linked or partials or unmanifested or missing_selected:
        raise VerificationError(
            "scoped raw tree mismatch: "
            f"links={linked}, partials={partials}, unmanifested={unmanifested}, "
            f"missing_selected={missing_selected}"
        )
    unrelated = observed - expected_paths - {Path("data/raw/README.md")}
    return {
        "scope": "selected_acquisition_with_manifest_backed_preexisting_files",
        "file_count": len(observed),
        "selected_payload_and_sidecar_count": len(expected_paths),
        "other_manifest_backed_file_count": len(unrelated),
        "acquisition_manifests_consulted": manifests,
        "unmanifested_files": [],
        "missing_selected_files": [],
        "symbolic_links": [],
        "partial_files": [],
        "status": "pass",
    }


def scoped_atomic_json(repo_root: Path, path: Path, value: dict[str, Any]) -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    value["scoped_verifier"] = {
        "git_commit": commit,
        "entrypoint": str(ENTRYPOINT.relative_to(repo_root)),
        "entrypoint_sha256": ACTIVE.sha256_file(ENTRYPOINT),
        "delegated_active_verifier": str(ACTIVE_ENTRYPOINT.relative_to(repo_root)),
        "semantics": (
            "verify the selected acquisition exactly; permit other raw files only when "
            "declared by a passed acquisition manifest"
        ),
    }
    PREVIOUS_ATOMIC_JSON(repo_root, path, value)


IMPL.verify_uniprot_metalink = selected_source_uniprot_metalink
IMPL.raw_tree_inventory = manifest_backed_raw_tree_inventory
IMPL.atomic_json = scoped_atomic_json


def main() -> int:
    return IMPL.main()


if __name__ == "__main__":
    raise SystemExit(main())
