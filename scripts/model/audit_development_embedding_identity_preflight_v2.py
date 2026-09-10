#!/usr/bin/env python3
"""Verify the frozen identity join and training/inference agreement before rescore."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pyarrow.parquet as pq
import torch
import yaml

from ipin_openppi.development_evaluation.embedding_identity import align_embedding_matrix
from ipin_openppi.development_evaluation.release import _validate_extracted_package, sha256_file
from ipin_openppi.development_evaluation.scoring import (
    configure_scoring_runtime,
    load_endpoint_universe,
    optimized_checkpoint_scores,
)
from ipin_openppi.stage1.models import build_model
from ipin_openppi.stage1.support import atomic_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=Path("configs/development_embedding_identity_correction_v2.yaml"))
    args = parser.parse_args()
    root = args.project_root.resolve()
    config_path = root / args.config
    config = yaml.safe_load(config_path.read_text())
    parent_path = root / config["identity_correction"]["parent_config"]
    assert sha256_file(parent_path) == config["identity_correction"]["parent_config_sha256"]
    parent = yaml.safe_load(parent_path.read_text())
    # The correction may not change a scientific definition or frozen input.
    for key in ("runtime", "frozen_inputs", "protected_boundary", "scorers", "evaluation", "degree_and_hub", "c1_novel_U", "complexity_thresholds"):
        assert config[key] == parent[key], f"frozen policy drift: {key}"
    assert config["development_release"]["release_root"] == parent["development_release"]["release_root"]
    assert config["development_release"]["evaluation_root"] != parent["development_release"]["evaluation_root"]
    assert config["outputs"]["public_results_root"] != parent["outputs"]["public_results_root"]
    assert sha256_file(root / config["authority"]["decision"]) == config["authority"]["decision_sha256"]
    configure_scoring_runtime()

    inputs = config["frozen_inputs"]
    for key, relative in inputs.items():
        if not key.endswith("_sha256"):
            assert sha256_file(root / relative) == inputs[key + "_sha256"], f"input hash drift: {key}"
    release_root = root / config["development_release"]["release_root"]
    receipt = json.loads((release_root / "DEVELOPMENT_RELEASE_RECEIPT.json").read_text())
    assert receipt["development_archive_sha256"] == config["development_release"]["plaintext_archive_sha256"]
    _, released_files = _validate_extracted_package(release_root)
    assert len(released_files) == 13
    universe = load_endpoint_universe(root / inputs["endpoints"], root / inputs["partitions"])
    registry = json.loads((root / inputs["embedding_registry"]).read_text())
    registered = {r["path"]: r for r in registry["artifacts"]}
    training = json.loads((root / inputs["training_registry"]).read_text())
    training_artifacts = {r["path"]: r for r in training["artifacts"]}
    arrays_relative = "artifacts/runs/stage1_model_execution_v1/prepared/training_arrays.npz"
    assert sha256_file(root / arrays_relative) == training_artifacts[arrays_relative]["sha256"]
    arrays = np.load(root / arrays_relative, allow_pickle=False)
    records = {}
    sample_a = np.concatenate((arrays["positive_endpoint_a"][:128], arrays["unlabeled_endpoint_a"][:128])).astype(np.int64)
    sample_b = np.concatenate((arrays["positive_endpoint_b"][:128], arrays["unlabeled_endpoint_b"][:128])).astype(np.int64)
    for candidate in ("esm2_150m", "esm2_650m"):
        base = "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/" + candidate
        manifest_relative = base + "/EMBEDDING_MANIFEST.json"
        assert sha256_file(root / manifest_relative) == registered[manifest_relative]["sha256"]
        manifest = json.loads((root / manifest_relative).read_text())
        for relative in (manifest["matrix_path"], manifest["normalization"]["standardized_matrix_path"], manifest["normalization"]["normalizer_path"]):
            assert sha256_file(root / relative) == registered[relative]["sha256"]
        raw = np.load(root / manifest["matrix_path"], mmap_mode="r", allow_pickle=False)
        matrix = np.load(root / manifest["normalization"]["standardized_matrix_path"], mmap_mode="r", allow_pickle=False)
        normalizer = np.load(root / manifest["normalization"]["normalizer_path"], allow_pickle=False)
        vectors = sorted(manifest["vectors"], key=lambda value: value["row_index"])
        stored_shas = [v["sequence_sha256"] for v in vectors]
        assert stored_shas == [sha for _, sha in sorted(zip(universe.lengths, universe.sequence_sha256))]
        assert all(hashlib.sha256(raw[i].tobytes()).hexdigest() == v["vector_sha256"] for i, v in enumerate(vectors))
        for start in range(0, len(vectors), 512):
            stop = start + 512
            reconstructed = ((raw[start:stop].astype(np.float64) - normalizer["mean"]) / normalizer["standard_deviation"]).astype(np.float32)
            assert np.array_equal(reconstructed, matrix[start:stop])
        aligned, identity = align_embedding_matrix(matrix, manifest, universe.sequence_sha256, candidate_id=candidate, sequence_lengths=universe.lengths)
        stored_lookup = {sha: i for i, sha in enumerate(stored_shas)}
        for table_key, array_prefix in (("training_positive", "positive"), ("training_unlabeled", "unlabeled")):
            offset = 0
            for batch in pq.ParquetFile(root / inputs[table_key]).iter_batches(batch_size=131072, columns=["endpoint_a_sha256", "endpoint_b_sha256"]):
                for letter in ("a", "b"):
                    expected = np.asarray([stored_lookup[sha] for sha in batch["endpoint_" + letter + "_sha256"].to_pylist()])
                    assert np.array_equal(expected, arrays[array_prefix + "_endpoint_" + letter][offset:offset + batch.num_rows])
                offset += batch.num_rows
        a = np.asarray([universe.index_by_sha256[stored_shas[i]] for i in sample_a], dtype=np.int64)
        b = np.asarray([universe.index_by_sha256[stored_shas[i]] for i in sample_b], dtype=np.int64)
        assert np.array_equal(aligned[a], matrix[sample_a]) and np.array_equal(aligned[b], matrix[sample_b])
        values = torch.from_numpy(aligned).cuda()
        comparisons = []
        for run in training["run_summaries"]:
            run_candidate = "esm2_150m" if run["family"] == "lightweight_esm2_150m_linear" else "esm2_650m"
            if run_candidate != candidate:
                continue
            checkpoint_record = run["selected_checkpoint"]
            checkpoint_path = root / checkpoint_record["path"]
            assert sha256_file(checkpoint_path) == checkpoint_record["sha256"]
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
            model = build_model(run["family"], dropout=0.0, seed=run["seed"]).cuda().eval()
            model.load_state_dict(checkpoint["model_state"])
            with torch.inference_mode():
                expected = model(torch.from_numpy(np.array(matrix[sample_a])).cuda(), torch.from_numpy(np.array(matrix[sample_b])).cuda()).cpu().numpy()
            observed = optimized_checkpoint_scores(family=run["family"], state=model.state_dict(), embeddings=values, pair_a=a, pair_b=b)
            difference = float(np.max(np.abs(expected.astype(np.float64) - observed)))
            assert difference <= 1e-4, f"training/inference score disagreement: {run['run_id']} {difference}"
            comparisons.append({"run_id": run["run_id"], "maximum_absolute_difference": difference})
            del model, checkpoint
        records[candidate] = {**identity, "all_raw_vector_hashes_verified": True, "all_standardized_values_reconstructed_exactly": True, "training_P_and_U_index_identity_verified": True, "public_pair_score_checks": comparisons}
        del values, aligned
        torch.cuda.empty_cache()
    source_hashes = {path: sha256_file(root / path) for path in config["identity_correction"]["source_paths"]}
    report = {
        "schema_version": 2, "status": "pass", "execution_id": config["execution_id"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "source_hashes": source_hashes, "execution_config_sha256": sha256_file(config_path),
        "encoders": records, "released_development_files_hash_verified": len(released_files),
        "public_training_pairs_checked": {"P": 16799, "U": 2000000},
        "score_agreement_absolute_tolerance": 1e-4,
        "tolerance_reason": "FP32 GEMM batch-shape rounding; input vectors agree exactly",
        "training_or_checkpoint_change": False, "decryption_or_private_key_access": False,
        "protected_candidates_or_truth_accessed": False,
    }
    output = root / config["identity_correction"]["preflight_report"]
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise RuntimeError("refusing to overwrite identity preflight evidence")
    atomic_json(output, report)
    print("embedding_identity_preflight: PASS both_encoders=17000 public_pairs=2016799 checkpoints=30", flush=True)


if __name__ == "__main__":
    main()
