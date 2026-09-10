"""Join frozen embedding rows to endpoint identities, never positional guesses."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

import numpy as np


def embedding_row_indices(
    sequence_hashes: Sequence[str],
    vector_records: Sequence[Mapping[str, Any]],
    matrix_rows: int,
    *,
    sequence_lengths: Sequence[int] | None = None,
) -> np.ndarray:
    """Return matrix rows in the requested endpoint order, validating a bijection."""
    requested = tuple(sequence_hashes)
    if len(requested) != matrix_rows or len(set(requested)) != matrix_rows:
        raise RuntimeError("endpoint identities must be unique and cover the embedding matrix")
    if len(vector_records) != matrix_rows:
        raise RuntimeError("embedding manifest must describe every matrix row")
    row_by_sha: dict[str, int] = {}
    length_by_sha: dict[str, int] = {}
    seen_rows: set[int] = set()
    for record in vector_records:
        sha = record["sequence_sha256"]
        row = record["row_index"]
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise RuntimeError("invalid embedding sequence SHA-256")
        if type(row) is not int or not 0 <= row < matrix_rows:
            raise RuntimeError("embedding row index must be an in-range integer")
        if sha in row_by_sha or row in seen_rows:
            raise RuntimeError("duplicate embedding sequence identity or row index")
        row_by_sha[sha] = row
        length_by_sha[sha] = int(record["sequence_length"])
        seen_rows.add(row)
    if set(requested) != set(row_by_sha):
        raise RuntimeError("embedding manifest sequence identities differ from endpoint universe")
    if sequence_lengths is not None:
        if len(sequence_lengths) != len(requested) or any(
            int(length) != length_by_sha[sha]
            for sha, length in zip(requested, sequence_lengths, strict=True)
        ):
            raise RuntimeError("embedding manifest sequence lengths differ from endpoint identities")
    return np.asarray([row_by_sha[sha] for sha in requested], dtype=np.int64)


def align_embedding_matrix(
    matrix: np.ndarray,
    manifest: Mapping[str, Any],
    sequence_hashes: Sequence[str],
    *,
    candidate_id: str,
    sequence_lengths: Sequence[int] | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Align an integrity-verified matrix using its integrity-verified manifest."""
    if matrix.ndim != 2 or matrix.dtype != np.float32 or not np.isfinite(matrix).all():
        raise RuntimeError("embedding matrix must be a finite FP32 matrix")
    if manifest["candidate_id"] != candidate_id or manifest["vector_count"] != matrix.shape[0]:
        raise RuntimeError("embedding candidate or manifest census mismatch")
    if any(
        record["candidate_id"] != candidate_id
        or record["vector_dimension"] != matrix.shape[1]
        for record in manifest["vectors"]
    ):
        raise RuntimeError("embedding vector candidate or dimension mismatch")
    rows = embedding_row_indices(
        sequence_hashes, manifest["vectors"], matrix.shape[0], sequence_lengths=sequence_lengths
    )
    aligned = np.ascontiguousarray(matrix[rows], dtype=np.float32)
    identity = {
        "strategy": "join_sequence_sha256_to_frozen_manifest_row_index_v2",
        "endpoint_count": int(rows.size),
        "reordered_row_count": int(np.count_nonzero(rows != np.arange(rows.size))),
        "embedding_row_permutation_sha256": hashlib.sha256(rows.astype("<i8").tobytes()).hexdigest(),
        "endpoint_order_sha256": hashlib.sha256("\n".join(sequence_hashes).encode("ascii")).hexdigest(),
        "aligned_matrix_sha256": hashlib.sha256(aligned.tobytes()).hexdigest(),
    }
    return aligned, identity
