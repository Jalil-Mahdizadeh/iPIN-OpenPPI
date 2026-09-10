from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest
import torch

from ipin_openppi.development_evaluation.embedding_identity import (
    align_embedding_matrix,
    embedding_row_indices,
)
from ipin_openppi.development_evaluation.scoring import optimized_checkpoint_scores
from ipin_openppi.stage1.models import build_model


def _manifest(hashes: list[str], dimension: int, stored_order: list[int]) -> dict:
    return {
        "candidate_id": "fixture",
        "vector_count": len(hashes),
        "vectors": [
            {
                "candidate_id": "fixture",
                "sequence_sha256": hashes[protein],
                "sequence_length": 100 + protein,
                "row_index": row,
                "vector_dimension": dimension,
            }
            for row, protein in enumerate(stored_order)
        ][::-1],  # The manifest's list order is not a matrix coordinate either.
    }


@pytest.mark.parametrize("family,dimension", [
    ("lightweight_esm2_150m_linear", 640),
    ("esm2_650m_linear_ablation", 1280),
    ("esm2_650m_nonlinear_no_gate_ablation", 1280),
    ("esm2_650m_partner_gated_primary", 1280),
])
def test_identity_join_preserves_training_scores_under_independent_row_permutations(
    family: str, dimension: int
) -> None:
    hashes = [f"{index:064x}" for index in range(11)]
    values = np.random.default_rng(3).normal(size=(11, dimension)).astype(np.float32)
    stored = [8, 3, 10, 0, 6, 2, 9, 1, 5, 7, 4]
    model = build_model(family, dropout=0.0, seed=20260803).eval()
    original_a = np.asarray([0, 2, 4, 6], dtype=np.int64)
    original_b = np.asarray([1, 3, 5, 10], dtype=np.int64)
    with torch.inference_mode():
        expected = model(torch.from_numpy(values[original_a]), torch.from_numpy(values[original_b])).numpy()
    for requested in (list(range(11)), [10, 1, 6, 0, 8, 2, 4, 9, 7, 5, 3]):
        manifest = _manifest(hashes, dimension, stored)
        aligned, _ = align_embedding_matrix(
            values[stored], manifest, [hashes[i] for i in requested],
            candidate_id="fixture", sequence_lengths=[100 + i for i in requested],
        )
        lookup = {protein: row for row, protein in enumerate(requested)}
        a = np.asarray([lookup[i] for i in original_a], dtype=np.int32)
        b = np.asarray([lookup[i] for i in original_b], dtype=np.int32)
        observed = optimized_checkpoint_scores(
            family=family, state=model.state_dict(), embeddings=torch.from_numpy(aligned),
            pair_a=a, pair_b=b,
        )
        np.testing.assert_allclose(observed, expected, rtol=0, atol=1e-6)
        incorrect = optimized_checkpoint_scores(
            family=family, state=model.state_dict(), embeddings=torch.from_numpy(values[stored]),
            pair_a=a, pair_b=b,
        )
        assert not np.allclose(incorrect, expected, rtol=0, atol=1e-3)


@pytest.mark.parametrize("defect", ["duplicate_sha", "duplicate_row", "missing", "unknown", "out_of_range", "bool_row", "wrong_length"])
def test_identity_join_rejects_non_bijections_and_wrong_sequence_lengths(defect: str) -> None:
    hashes = [f"{index:064x}" for index in range(4)]
    records = deepcopy(_manifest(hashes, 3, [2, 0, 3, 1])["vectors"])
    if defect == "duplicate_sha":
        records[1]["sequence_sha256"] = records[0]["sequence_sha256"]
    elif defect == "duplicate_row":
        records[1]["row_index"] = records[0]["row_index"]
    elif defect == "missing":
        records.pop()
    elif defect == "unknown":
        records[1]["sequence_sha256"] = "f" * 64
    elif defect == "out_of_range":
        records[1]["row_index"] = 4
    elif defect == "bool_row":
        records[1]["row_index"] = True
    else:
        records[1]["sequence_length"] += 1
    with pytest.raises(RuntimeError):
        embedding_row_indices(hashes, records, 4, sequence_lengths=[100, 101, 102, 103])


def test_identity_join_rejects_wrong_candidate_and_duplicate_requested_proteins() -> None:
    hashes = [f"{index:064x}" for index in range(4)]
    manifest = _manifest(hashes, 3, [2, 0, 3, 1])
    with pytest.raises(RuntimeError, match="candidate"):
        align_embedding_matrix(np.ones((4, 3), dtype=np.float32), manifest, hashes, candidate_id="different")
    with pytest.raises(RuntimeError, match="unique"):
        embedding_row_indices([hashes[0]] * 4, manifest["vectors"], 4)
