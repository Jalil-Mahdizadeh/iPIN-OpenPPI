"""Prepare an allowlisted train/dev-only bundle and freeze it before fitting."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil

import numpy as np
import pyarrow.parquet as pq
import torch

from ipin_openppi.development_evaluation.embedding_identity import align_embedding_matrix
from ipin_openppi.development_evaluation.scoring import load_cell_rows, load_endpoint_universe
from ipin_openppi.stage1 import constants as c
from .common import BASELINE, SEEDS, historical_integrity, read, record, recipes, sha, verify, write_new


def prepare(project: Path) -> None:
    os.umask(0o077)
    output = project / ".private/model_optimization_v1"
    output.mkdir(mode=0o700, exist_ok=False)
    bundle = output / "bundle"
    data = bundle / "data"
    data.mkdir(parents=True)
    validation = project / "artifacts/validation/model_optimization_v1"
    historical = historical_integrity(project)
    if historical["registered_files"] != 148:
        raise RuntimeError("Original closure census drift")
    inputs = []

    def checked(relative, digest=None):
        path = project / relative
        if digest is not None and sha(path) != digest:
            raise RuntimeError(f"Scientific input checksum mismatch: {relative}")
        inputs.append(record(path, project))
        return path

    for name in ("ENDPOINTS", "PARTITIONS", "COMPONENTS", "POSITIVE", "UNLABELED", "STRATA"):
        checked(getattr(c, name + "_PATH"), getattr(c, name + "_SHA256"))
    image = checked("containers/images/ipin-model-arm64_0.1.0.sif", c.MODEL_SIF_SHA256)
    universe = load_endpoint_universe(project / c.ENDPOINTS_PATH, project / c.PARTITIONS_PATH)
    write_new(data / "endpoints.json", list(universe.sequence_sha256))
    train = {}
    for state, prefix, relative in (("released_positive", "p", c.POSITIVE_PATH), ("unlabeled", "u", c.UNLABELED_PATH)):
        rows = pq.read_table(project / relative)
        if set(rows["state"].to_pylist()) != {state}:
            raise RuntimeError("Invalid training state")
        for side in ("a", "b"):
            indices = np.array([universe.index_by_sha256[x] for x in rows[f"endpoint_{side}_sha256"].to_pylist()], dtype=np.int64)
            if any(universe.partitions[i] != "train" for i in np.unique(indices)):
                raise RuntimeError("Non-training endpoint in optimization training rows")
            train[f"{prefix}_{side}"] = indices
        if np.any(train[f"{prefix}_a"] == train[f"{prefix}_b"]):
            raise RuntimeError("Self-pair")
        weights = rows["sampling_weight_numerator"].to_numpy().astype(np.float64) / rows["sampling_weight_denominator"].to_numpy()
        if not np.isfinite(weights).all() or np.any(weights <= 0):
            raise RuntimeError("Invalid training weights")
        if prefix == "p" and not np.all(weights == 1):
            raise RuntimeError("Non-census positive weight")
        if prefix == "u":
            train["u_weight"] = weights
    if (train["p_a"].size, train["u_a"].size) != (16799, 2000000):
        raise RuntimeError("Training census drift")
    np.savez(data / "training.npz", **train)

    expected_embeddings = {
        "esm2_150m": ("bc4ea08691cdd55f393fc6ebb6264c338c70846b82e5a9001c3ac2a57a34d27f", "deacaf3c087ca8da7ea5bd5fafe5760dfa53978bb58a145b4733e4d3ca949110"),
        "esm2_650m": ("878bd90d60dcfcf546479c94255e673ebd18f10756179cfcafac680028a53902", "d54d9d943088a9b0c301242b1c717c668c6561721496ea071cd5c512e5e3475c"),
    }
    identities = {}
    for encoder, (manifest_hash, matrix_hash) in expected_embeddings.items():
        root = c.EMBEDDING_ROOT / encoder
        manifest = read(checked(root / "EMBEDDING_MANIFEST.json", manifest_hash))
        matrix = np.load(checked(root / "standardized_embeddings.f32.npy", matrix_hash), allow_pickle=False)
        aligned, identity = align_embedding_matrix(matrix, manifest, universe.sequence_sha256,
                                                   candidate_id=encoder, sequence_lengths=universe.lengths)
        if np.any(np.linalg.norm(aligned, axis=1) <= 0):
            raise RuntimeError("Zero endpoint vector")
        np.save(data / f"{encoder}.npy", aligned, allow_pickle=False)
        identities[encoder] = identity

    registry_path = checked(c.VALIDATION_ROOT / "TRAINING_ARTIFACT_REGISTRY.json", "11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318")
    registered = {x["path"]: x for x in read(registry_path)["artifacts"]}
    for seed in SEEDS:
        relative = c.CHECKPOINT_ROOT / f"{BASELINE}__seed{seed}/pass_05.pt"
        item = registered[str(relative)]
        verify(project, [item])
        checkpoint = checked(relative, item["sha256"])
        # Trusted original pickle is hash-checked before load, then converted
        # to data-only NPZ for every downstream model/scorer process.
        state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model_state"]
        np.savez(data / f"baseline_{seed}.npz", **{k: v.numpy() for k, v in state.items()})

    # This is the already released development package, never test custody.
    release = project / ".private/development_release_and_evaluation_v1/release"
    release_manifest = read(checked(release.relative_to(project) / "DEVELOPMENT_PACKAGE_MANIFEST.json"))
    for table in ("positive_pairs", "unlabeled_pairs"):
        verify(release, release_manifest["tables"][table]["files"])
        inputs.extend(record(release / x["path"], project) for x in release_manifest["tables"][table]["files"])
    cache = project / ".private/development_embedding_identity_correction_v2/evaluation/scores"
    cells = [f"C{n}_development" for n in (3, 2, 1)]
    cells += [f"source_exclusive:{source}:C{n}_development" for n in (3, 2, 1) for source in ("HI-II-14", "HuRI")]
    cell_records = []
    for i, cell in enumerate(cells):
        cell_cache = cache / cell.replace(":", "__")
        cm = read(checked((cell_cache / "CELL_SCORE_MANIFEST.json").relative_to(project)))
        verify(cell_cache, [cm[k] for k in ("rows", "scores", "scorers")])
        inputs.extend(record(cell_cache / cm[k]["path"], project) for k in ("rows", "scores", "scorers"))
        rows = load_cell_rows(release, cell)
        cached_rows = pq.read_table(cell_cache / cm["rows"]["path"])
        if not rows.select(cached_rows.column_names).equals(cached_rows):
            raise RuntimeError("Development cache/released row identity mismatch")
        p = np.array(rows["state"].to_pylist()) == "released_positive"
        a = np.array([universe.index_by_sha256[x] for x in rows["endpoint_a_sha256"].to_pylist()], dtype=np.int64)
        b = np.array([universe.index_by_sha256[x] for x in rows["endpoint_b_sha256"].to_pylist()], dtype=np.int64)
        if any(universe.partitions[j] == "test" for j in np.unique(np.concatenate((a, b)))):
            raise RuntimeError("Test endpoint entered development pairs")
        comp_a = rows["endpoint_a_component_id"].to_pylist()
        comp_b = rows["endpoint_b_component_id"].to_pylist()
        components = sorted(set(comp_a + comp_b))
        comp_index = {x: j for j, x in enumerate(components)}
        columns = {x["scorer_id"]: x["column"] for x in read(cell_cache / "SCORERS.json")["scorers"]}
        scores = np.load(cell_cache / "scores.f64.npy", mmap_mode="r", allow_pickle=False)
        baseline = scores[:, [columns[f"{BASELINE}__seed{seed}"] for seed in SEEDS]].copy()
        if not np.array_equal(baseline.mean(axis=1), scores[:, columns[BASELINE]]):
            raise RuntimeError("Original ensemble is not the exact raw-score seed mean")
        weights = rows["sampling_weight_numerator"].to_numpy().astype(np.float64) / rows["sampling_weight_denominator"].to_numpy()
        np.savez(data / f"development_{i:02d}.npz", a=a, b=b, positive=p, weight=weights,
                 component_a=np.array([comp_index[x] for x in comp_a], dtype=np.int64),
                 component_b=np.array([comp_index[x] for x in comp_b], dtype=np.int64),
                 components=np.array(components), baseline=baseline)
        cell_records.append({"cell_id": cell, "file": f"development_{i:02d}.npz", "positive_rows": int(p.sum()), "unlabeled_rows": int((~p).sum())})
        print(f"prepared {cell}: P={p.sum()} U={(~p).sum()}", flush=True)

    code = bundle / "code"
    shutil.copytree(project / "src/ipin_openppi", code / "ipin_openppi", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for relative in ("configs/model_optimization_v1.json", "docs/protocols/MODEL_OPTIMIZATION_v1.md",
                     "governance/decisions/DEC-0052-development-only-optimization-and-conditional-followup.md",
                     "docs/protocols/MODEL_OPTIMIZATION_v1_PREFIT_TECHNICAL_ERRATUM.md",
                     "tests/test_model_optimization_v1.py", "scripts/model/run_model_optimization_v1.sh"):
        source = project / relative
        destination = bundle / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    config = read(bundle / "configs/model_optimization_v1.json")
    frozen = {
        "study_id": config["study_id"], "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "prior_prefit_gpu_seconds_charged": 2,
        "formal_training_started": False, "protected_pairs_or_truth_accessed": False,
        "configuration": config, "recipes": recipes(config), "cells": cell_records,
        "embedding_identity": identities, "input_records": inputs,
        "historical_integrity": historical, "model_image_sha256": sha(image),
        "files": [record(p, bundle) for p in sorted(bundle.rglob("*")) if p.is_file()],
    }
    write_new(bundle / "SEARCH_FREEZE.json", frozen)
    write_new(validation / "SEARCH_FREEZE.json", frozen)
    print(f"Frozen 24 recipes and {len(frozen['files'])} bundle files; no test access", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    prepare(parser.parse_args().project.resolve())
