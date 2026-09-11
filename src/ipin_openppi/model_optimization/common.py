"""Immutable artifact helpers and the prospective recipe census."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

BASELINE = "lightweight_esm2_150m_linear__linear_lr3e-4"
SEEDS = (20260803, 20260817, 20260831)
STUDIES = (
    "within_anchor_partner_specificity_v1", "homology_source_challenge_v1",
    "external_bioplex_challenge_v1", "composition_order_challenge_v1",
    "direct_binary_feasibility_v1", "protected_final_test_v1",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def write_new(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def record(path: Path, root: Path) -> dict:
    return {"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha(path)}


def verify(root: Path, records) -> None:
    for item in records:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("Unsafe artifact path")
        path = root / relative
        if path.is_symlink() or path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise RuntimeError(f"Artifact drift: {relative}")


def recipes(config: dict) -> list[dict]:
    result = []
    for encoder in config["encoders"]:
        for spec in config["recipes_per_encoder"]:
            result.append({**spec, "encoder": encoder, "id": f"{encoder}__{spec['name']}"})
    if len(result) != 24 or len({x["id"] for x in result}) != 24:
        raise RuntimeError("Prospective recipe census drift")
    return result


def historical_integrity(root: Path) -> dict:
    studies = []
    for name in STUDIES:
        path = root / "artifacts/results" / name / "ARTIFACT_REGISTRY.json"
        registry = read(path)
        verify(root, registry["artifacts"])
        studies.append({"study": name, "registry_sha256": sha(path), "files": len(registry["artifacts"])})
    custody = root / ".private/pair_level_pu_r_benchmark_artifacts_v1"
    expected = {
        "protected_evaluation_ledger.json": "e23a6a8980d3e9d148a40be8e9b3d1316ff1c2c6ed8f7f03ab2bd899b777914f",
        "protected_evaluation_completion.json": "6f38d22ada537dad55a22687223a0294dc66be79fda4f031326cd937e9d17678",
    }
    for name, digest in expected.items():
        if sha(custody / name) != digest:
            raise RuntimeError("Original spent custody record drift")
    return {"studies": studies, "registered_files": sum(x["files"] for x in studies),
            "original_custody_sha256": expected, "unchanged": True}
