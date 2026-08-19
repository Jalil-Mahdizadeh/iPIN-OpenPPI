#!/usr/bin/env python3
"""Score all nine released-development cells with the exact 49 scorers."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

import yaml

from ipin_openppi.development_evaluation.release import sha256_file
from ipin_openppi.development_evaluation.scoring import (
    DEVELOPMENT_CELLS,
    build_interolog_matrices,
    build_kmer_matrix,
    configure_scoring_runtime,
    load_endpoint_universe,
    load_training_graph,
    score_cell,
)


def _load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"mapping required: {path}")
    return value


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _verified(root: Path, relative: str, expected: str) -> Path:
    path = root / relative
    if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
        raise RuntimeError(f"frozen input hash drift: {relative}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--execution-config",
        type=Path,
        default=Path("configs/development_release_and_evaluation_execution_v1.yaml"),
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    config_path = (root / args.execution_config).resolve(strict=True)
    config = _load(config_path)
    configure_scoring_runtime()
    inputs = config["frozen_inputs"]
    endpoint_path = _verified(root, inputs["endpoints"], inputs["endpoints_sha256"])
    partition_path = _verified(root, inputs["partitions"], inputs["partitions_sha256"])
    positive_path = _verified(
        root, inputs["training_positive"], inputs["training_positive_sha256"]
    )
    training_registry_path = _verified(
        root, inputs["training_registry"], inputs["training_registry_sha256"]
    )
    embedding_registry_path = _verified(
        root, inputs["embedding_registry"], inputs["embedding_registry_sha256"]
    )
    release_root = root / config["development_release"]["release_root"]
    receipt_path = release_root / "DEVELOPMENT_RELEASE_RECEIPT.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise RuntimeError("development release receipt is absent")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("development_archive_sha256")
        != config["development_release"]["plaintext_archive_sha256"]
        or receipt.get("protected_candidates_accessed") is not False
        or receipt.get("protected_truth_accessed") is not False
        or receipt.get("model_evaluation_performed") is not False
    ):
        raise RuntimeError("development release receipt is unsafe")
    training_registry = json.loads(training_registry_path.read_text(encoding="utf-8"))
    embedding_registry = json.loads(embedding_registry_path.read_text(encoding="utf-8"))
    artifact_by_path = {item["path"]: item for item in embedding_registry["artifacts"]}
    embedding_paths = {}
    for candidate_id in ("esm2_150m", "esm2_650m"):
        relative = (
            "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/"
            f"{candidate_id}/standardized_embeddings.f32.npy"
        )
        record = artifact_by_path[relative]
        path = _verified(root, relative, record["sha256"])
        if path.stat().st_size != int(record["bytes"]):
            raise RuntimeError("registered embedding byte count drift")
        embedding_paths[candidate_id] = path

    output_root = root / config["development_release"]["evaluation_root"]
    if output_root.exists() and not args.resume:
        raise RuntimeError("private evaluation root exists; use only exact --resume after review")
    output_root.mkdir(parents=True, mode=0o700, exist_ok=args.resume)
    started_wall = datetime.now(timezone.utc)
    started = time.monotonic()
    universe = load_endpoint_universe(endpoint_path, partition_path)
    graph = load_training_graph(positive_path, universe)
    kmer = build_kmer_matrix(universe)
    similarities, neighbor_max = build_interolog_matrices(kmer, graph)
    manifests = []
    for cell_id in DEVELOPMENT_CELLS:
        cell_root = output_root / "scores" / cell_id.replace(":", "__")
        if cell_root.exists():
            if not args.resume or not (cell_root / "CELL_SCORE_MANIFEST.json").is_file():
                raise RuntimeError(f"incomplete or unauthorized existing cell output: {cell_id}")
            manifest = json.loads((cell_root / "CELL_SCORE_MANIFEST.json").read_text(encoding="utf-8"))
            if manifest.get("cell_id") != cell_id:
                raise RuntimeError("resume cell identity drift")
            manifests.append(manifest)
            continue
        cell_root.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        print(f"scoring {cell_id}", flush=True)
        manifests.append(
            score_cell(
                project_root=root,
                package_root=release_root,
                output_root=cell_root,
                cell_id=cell_id,
                universe=universe,
                graph=graph,
                kmer=kmer,
                similarities=similarities,
                neighbor_max=neighbor_max,
                training_registry=training_registry,
                embedding_paths=embedding_paths,
            )
        )
    elapsed = time.monotonic() - started
    run_manifest = {
        "schema_version": 1,
        "execution_id": config["execution_id"],
        "started_at_utc": started_wall.isoformat(),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed,
        "conservative_gpu_hours": elapsed / 3600.0,
        "container_sha256": config["runtime"]["container_sha256"],
        "execution_config_sha256": sha256_file(config_path),
        "training_registry_sha256": inputs["training_registry_sha256"],
        "development_release_receipt_sha256": sha256_file(receipt_path),
        "cells": manifests,
        "cell_count": len(manifests),
        "scorer_count": 49,
        "selected_checkpoint_count": 30,
        "ensemble_count": 10,
        "training_or_checkpoint_change": False,
        "protected_candidates_accessed": False,
        "protected_truth_accessed": False,
    }
    _atomic_json(output_root / "SCORING_RUN_MANIFEST.json", run_manifest)
    print(f"development_scoring: PASS cells={len(manifests)} elapsed_seconds={elapsed:.3f}")


if __name__ == "__main__":
    main()
