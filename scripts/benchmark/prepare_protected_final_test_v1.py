"""Public-input-only preparation; never resolve or read evaluator keys."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import importlib.util
import io
from pathlib import Path
import shutil
import sys
import unittest

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from scipy import sparse
import torch

from ipin_openppi.development_evaluation.embedding_identity import align_embedding_matrix
from ipin_openppi.development_evaluation.scoring import (
    load_endpoint_universe, load_training_graph, build_kmer_matrix,
    build_interolog_matrices, optimized_checkpoint_scores,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protected_final_core_v1 as core


def prepare(project: Path):
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    test_path = project / "tests/unit/test_protected_final_test_v1.py"
    spec = importlib.util.spec_from_file_location("final_synthetic_tests", test_path)
    test_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_module)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_module))
    test_report = project / "artifacts/validation/protected_final_test_v1/PREACCESS_SYNTHETIC_TESTS.json"
    core.write_new(test_report, {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                   "pass": result.wasSuccessful(), "test_source_sha256": core.sha(test_path), "synthetic_only": True,
                   "same_author_not_independent_replication": True, "console": stream.getvalue()})
    if not result.wasSuccessful():
        raise RuntimeError("Synthetic qualification failed before preparation")
    torch.set_num_threads(8)
    root = project / "artifacts/runs/protected_final_test_v1/frozen_bundle"
    root.mkdir(parents=True, exist_ok=False)
    features, code = root / "features", root / "code"
    features.mkdir()
    code.mkdir()
    source_paths = ["scripts/benchmark/protected_final_guard_v1.py",
                    "scripts/benchmark/protected_final_core_v1.py",
                    "scripts/benchmark/prepare_protected_final_test_v1.py",
                    "scripts/benchmark/run_protected_final_test_v1.sh",
                    "tests/unit/test_protected_final_test_v1.py",
                    "governance/decisions/DEC-0051-authorize-one-final-protected-evaluation.md",
                    "docs/protocols/PROTECTED_FINAL_TEST_v1.md",
                    "artifacts/validation/protected_final_test_v1/PREACCESS_SYNTHETIC_TESTS.json"]
    for path in source_paths:
        shutil.copyfile(project / path, code / Path(path).name)
    registry = project / "artifacts/validation/model_execution/stage1_model_execution_v1"
    inputs = []

    def verify(path, expected):
        absolute = project / path
        if core.sha(absolute) != expected:
            raise RuntimeError("Upstream frozen input hash drift")
        inputs.append(core.record(absolute, project))
        return absolute

    tr_path = verify(str((registry / "TRAINING_ARTIFACT_REGISTRY.json").relative_to(project)), "11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318")
    er_path = verify(str((registry / "EMBEDDING_ARTIFACT_REGISTRY.json").relative_to(project)), "429e9b3c40827ea5a7513b3599a95d201cdc5eea1e0f99f8c384050cbfcbaed1")
    selection_path = project / "artifacts/results/development_evaluation/development_embedding_identity_correction_v2/SELECTION_AND_KILL_TRACE.json"
    selection = core.read(selection_path)
    if selection["selection_trace"]["selected_candidate_id"] != core.MODEL:
        raise RuntimeError("Development-selected model drift")
    inputs.append(core.record(selection_path, project))
    tr, er = core.read(tr_path), core.read(er_path)
    embedding = {}
    for rec in er["artifacts"]:
        if "/esm2_150m/" in rec["path"] or rec["path"].startswith("data/canonical/"):
            embedding[Path(rec["path"]).name] = verify(rec["path"], rec["sha256"])
    endpoints = verify("data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/eligible_reference_sequences/part-00000.parquet", "4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e")
    partitions = verify("data/canonical/final_benchmark_component_split_v1/endpoint_partition_assignments/part-00000.parquet", "66db8cd59e7cb8cf06ff3ad785448dfc7d5fdd24643811946246d129b0bd8a67")
    training = verify("data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/positive_pairs/part-00000.parquet", "4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499")
    package_path = verify("data/canonical/pair_level_pu_r_benchmark_artifacts_v1/PACKAGE_MANIFEST.json", "f0f850daf795481c8a1ae0ba64f6d050ae757f2738497ac0517003c6822015f5")
    package = core.read(package_path)
    universe = load_endpoint_universe(endpoints, partitions)
    graph = load_training_graph(training, universe)
    core.write_new(features / "endpoints.json", list(universe.sequence_sha256))
    core.write_new(features / "components.json", list(universe.components))
    em = core.read(embedding["EMBEDDING_MANIFEST.json"])
    z, identity = align_embedding_matrix(np.load(embedding["standardized_embeddings.f32.npy"], allow_pickle=False), em,
                                        universe.sequence_sha256, candidate_id="esm2_150m", sequence_lengths=universe.lengths)
    pooled, _ = align_embedding_matrix(np.load(embedding["pooled_embeddings.f32.npy"], allow_pickle=False), em,
                                      universe.sequence_sha256, candidate_id="esm2_150m", sequence_lengths=universe.lengths)
    pooled = pooled.astype(np.float64)
    pooled /= np.linalg.norm(pooled, axis=1, keepdims=True)
    alphabet = "ACDEFGHIKLMNPQRSTVWYX"
    aac_counts = [Counter(residue if residue in alphabet else "X" for residue in sequence) for sequence in universe.sequences]
    aac = np.array([[counts.get(letter, 0) for letter in alphabet] for counts in aac_counts], np.float64)
    if not np.array_equal(aac.sum(axis=1), universe.lengths):
        raise RuntimeError("Unexpected residue outside frozen amino-acid alphabet")
    aac /= np.linalg.norm(aac, axis=1, keepdims=True)
    for name, values in (("standardized", z), ("pooled_unit", pooled), ("aac_unit", aac),
                         ("degree", graph.degree), ("length", universe.lengths),
                         ("component_mass", np.array([graph.component_mass[c] for c in universe.components], np.int64))):
        np.save(features / f"{name}.npy", values, allow_pickle=False)
    sparse.save_npz(features / "adjacency.npz", graph.adjacency)
    kmer = build_kmer_matrix(universe)
    sparse.save_npz(features / "kmer.npz", kmer)
    sim, neighbor = build_interolog_matrices(kmer, graph)
    np.save(features / "similarities.npy", sim, allow_pickle=False)
    np.save(features / "neighbor.npy", neighbor, allow_pickle=False)
    ensemble = next(item for item in tr["ensembles"] if item["candidate_id"] == core.MODEL)
    if tuple(item["seed"] for item in ensemble["members"]) != core.SEEDS:
        raise RuntimeError("Frozen ensemble seed order drift")
    parameters, checkpoints = [], []
    p = pq.read_table(training, columns=["endpoint_a_sha256", "endpoint_b_sha256"]).slice(0, 128)
    a = np.array([universe.index_by_sha256[x] for x in p["endpoint_a_sha256"].to_pylist()])
    b = np.array([universe.index_by_sha256[x] for x in p["endpoint_b_sha256"].to_pylist()])
    reference = []
    for member in ensemble["members"]:
        rec = member["selected_checkpoint"]
        checkpoint_path = verify(rec["path"], rec["sha256"])
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if checkpoint["pass_index"] != 5 or checkpoint["global_step"] != 2445:
            raise RuntimeError("Frozen selected checkpoint cursor drift")
        state = checkpoint["model_state"]
        if set(state) != {"output.weight", "output.bias"}:
            raise RuntimeError("Unexpected head state")
        weight, bias = state["output.weight"].numpy(), state["output.bias"].numpy()
        parameters.append((weight, bias))
        np.savez(features / f"head_{member['seed']}.npz", weight=weight, bias=bias)
        reference.append(optimized_checkpoint_scores(family=ensemble["family"], state=state, embeddings=torch.from_numpy(z), pair_a=a, pair_b=b))
        checkpoints.append(member)
    actual = core.head_scores(z, parameters, a, b)
    error = float(np.max(np.abs(actual - np.column_stack(reference))))
    if error > 1e-6:
        raise RuntimeError("Frozen scorer CPU replay failed")
    fixture = p.add_column(0, "candidate_token", pa.array([f"public-fixture-{i}" for i in range(p.num_rows)]))
    fixture = fixture.append_column("cell_id", pa.array(["public_training_fixture"] * p.num_rows))
    pq.write_table(fixture, features / "public_training_fixture.parquet")
    np.save(features / "public_training_fixture_reference.npy", np.column_stack(reference), allow_pickle=False)
    sealed = {}
    for role in ("protected_candidates", "protected_truth"):
        rec = package["artifacts"]["sealed_packages"][role]
        verify(f"data/canonical/{core.PACKAGE}/sealed/{rec['ciphertext_path']}", rec["ciphertext_sha256"])
        cert_path = project / f"governance/keys/{core.PACKAGE}/{role}_certificate.pem"
        expected_cert = {"protected_candidates": "b53dc3fbedf1b17b99dc1eea6efe782305bf3d6e7a16b30e7cb8011e489611b1",
                         "protected_truth": "4504fdf748090e1122cfb914ccc7209c1afe0cf5c0aa53693aea4917d0801584"}[role]
        if core.sha(cert_path) != expected_cert:
            raise RuntimeError("Certificate drift")
        inputs.append(core.record(cert_path, project))
        sealed[role] = {**rec, "certificate_sha256": core.sha(cert_path)}
    # Freeze preparation dependencies as provenance; they are not mounted for scoring.
    dependencies = [core.record(path, project) for path in sorted((project / "src/ipin_openppi").rglob("*.py"))]
    prior_closures = []
    for study in ("within_anchor_partner_specificity_v1", "homology_source_challenge_v1", "external_bioplex_challenge_v1", "composition_order_challenge_v1", "direct_binary_feasibility_v1"):
        registry_path = project / f"artifacts/results/{study}/ARTIFACT_REGISTRY.json"
        registered = core.read(registry_path)["artifacts"]
        core.verify_records(project, registered)
        prior_closures.append({"study": study, "registry_sha256": core.sha(registry_path), "files_unchanged": len(registered)})
    files = [core.record(path, root) for path in sorted(root.rglob("*")) if path.is_file()]
    manifest = {"execution_id": "protected_final_test_v1", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                "model": core.MODEL, "scorers": list(core.SCORERS), "cells": list(core.CELLS), "checkpoints": checkpoints,
                "model_container_sha256": "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91",
                "files": files, "upstream_inputs": inputs, "preparation_source_closure": dependencies,
                "source_inputs": [core.record(project / x, project) for x in source_paths],
                "sealed_packages": sealed, "embedding_identity": identity, "CPU_replay_max_abs": error,
                "prior_closures": prior_closures, "protected_candidates_accessed": False,
                "protected_truth_accessed": False, "new_fit_or_encoder_inference": False}
    core.write_new(root / "SCORER_FREEZE.json", manifest)
    destination = project / "artifacts/validation/protected_final_test_v1/SCORER_FREEZE.json"
    core.write_new(destination, manifest)
    for path in root.rglob("*"):
        path.chmod(0o500 if path.is_dir() else 0o400)
    root.chmod(0o500)
    print(json.dumps({"public_feature_preparation_complete": True, "CPU_replay_max_abs": error,
                      "scorer_freeze_sha256": core.sha(destination), "protected_access": False}))


if __name__ == "__main__":
    prepare(Path(sys.argv[1]).resolve(strict=True))
