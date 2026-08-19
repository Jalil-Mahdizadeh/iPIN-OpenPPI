"""Exact pooled frozen-ESM embedding extraction from DEC-0028."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Iterable, Iterator, Sequence

import numpy as np
import pyarrow.parquet as pq

from .constants import (
    CANDIDATES,
    EMBEDDING_ROOT,
    ENDPOINTS_PATH,
    ENDPOINTS_SHA256,
    MAX_RESIDUES,
    MAX_RESIDUE_TOKENS_PER_BATCH,
    MODEL_CACHE_ROOT,
    MODEL_SIF_SHA256,
    OVERLAP_RESIDUES,
    PARTITIONS_PATH,
    PARTITIONS_SHA256,
    PROTOCOL_CONFIGURATION_SHA256,
    PROTOCOL_ID,
    REPEAT_FRACTION,
    REPEAT_TOLERANCE,
    STRIDE_RESIDUES,
    TOTAL_ENDPOINTS,
    TRAIN_ENDPOINTS,
)
from .support import (
    atomic_json,
    atomic_numpy,
    atomic_npz,
    git_commit,
    require_sha256,
    sha256_bytes,
    sha256_file,
)


STRATEGY_ID = "final_hidden_state_residue_mean_fp32_window1022_overlap128_stride894_v1"


@dataclass(frozen=True)
class SequenceRecord:
    sequence_sha256: str
    sequence: str
    sequence_length: int


@dataclass(frozen=True)
class WindowRecord:
    sequence_index: int
    start: int
    stop: int
    final_for_sequence: bool

    @property
    def residues(self) -> int:
        return self.stop - self.start


def window_starts(length: int) -> tuple[int, ...]:
    if length <= 0:
        raise RuntimeError("empty sequence prohibited")
    if length <= MAX_RESIDUES:
        return (0,)
    starts = list(range(0, length - MAX_RESIDUES + 1, STRIDE_RESIDUES))
    final = length - MAX_RESIDUES
    if starts[-1] != final:
        starts.append(final)
    if starts != sorted(set(starts)):
        raise RuntimeError("window starts are not unique and ascending")
    coverage = np.zeros(length, dtype=np.uint16)
    for start in starts:
        coverage[start : start + MAX_RESIDUES] += 1
    if np.any(coverage == 0):
        raise RuntimeError("windowing failed complete residue coverage")
    return tuple(starts)


def ordered_records(endpoint_path: Path) -> list[SequenceRecord]:
    table = pq.read_table(
        endpoint_path,
        columns=["reference_sequence_sha256", "sequence_length", "sequence"],
    )
    records = [
        SequenceRecord(str(digest), str(sequence), int(length))
        for digest, length, sequence in zip(
            table["reference_sequence_sha256"].to_pylist(),
            table["sequence_length"].to_pylist(),
            table["sequence"].to_pylist(),
            strict=True,
        )
    ]
    if len(records) != TOTAL_ENDPOINTS or len({r.sequence_sha256 for r in records}) != TOTAL_ENDPOINTS:
        raise RuntimeError("endpoint population is not exactly 17,000 unique sequences")
    for record in records:
        if record.sequence_length != len(record.sequence) or record.sequence != record.sequence.upper():
            raise RuntimeError(f"sequence identity/length violation: {record.sequence_sha256}")
        if hashlib.sha256(record.sequence.encode("ascii")).hexdigest() != record.sequence_sha256:
            raise RuntimeError(f"sequence digest mismatch: {record.sequence_sha256}")
    return sorted(records, key=lambda record: (record.sequence_length, record.sequence_sha256))


def windows_for(records: Sequence[SequenceRecord]) -> list[WindowRecord]:
    windows: list[WindowRecord] = []
    for sequence_index, record in enumerate(records):
        starts = window_starts(record.sequence_length)
        for position, start in enumerate(starts):
            stop = min(start + MAX_RESIDUES, record.sequence_length)
            windows.append(
                WindowRecord(
                    sequence_index=sequence_index,
                    start=start,
                    stop=stop,
                    final_for_sequence=position == len(starts) - 1,
                )
            )
    return windows


def greedy_window_batches(windows: Sequence[WindowRecord]) -> Iterator[list[WindowRecord]]:
    batch: list[WindowRecord] = []
    residues = 0
    for window in windows:
        if window.residues > MAX_RESIDUE_TOKENS_PER_BATCH:
            if batch:
                yield batch
                batch = []
                residues = 0
            yield [window]
            continue
        if batch and residues + window.residues > MAX_RESIDUE_TOKENS_PER_BATCH:
            yield batch
            batch = []
            residues = 0
        batch.append(window)
        residues += window.residues
    if batch:
        yield batch


def tokenizer_hashes(model_root: Path) -> dict[str, str]:
    return {
        filename: sha256_file(model_root / filename)
        for filename in ("config.json", "special_tokens_map.json", "tokenizer_config.json", "vocab.txt")
    }


def cache_key(candidate_id: str, sequence_sha256: str) -> str:
    candidate = CANDIDATES[candidate_id]
    payload = "|".join(
        (
            candidate_id,
            candidate["revision"],
            candidate["checkpoint_sha256"],
            STRATEGY_ID,
            sequence_sha256,
        )
    )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def repeat_selection_key(candidate_id: str, sequence_sha256: str) -> bytes:
    return hashlib.sha256(f"{candidate_id}:{sequence_sha256}".encode("ascii")).digest()


def extract_matrix(
    *, candidate_id: str, records: Sequence[SequenceRecord], model_root: Path
) -> tuple[np.ndarray, dict[str, Any]]:
    import torch
    from transformers import EsmForMaskedLM, EsmTokenizer

    candidate = CANDIDATES[candidate_id]
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("exactly one CUDA GPU required")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise RuntimeError("offline Hugging Face/Transformers mode required")

    tokenizer = EsmTokenizer.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False
    )
    checkpoint_model, loading = EsmForMaskedLM.from_pretrained(
        model_root,
        local_files_only=True,
        output_loading_info=True,
        trust_remote_code=False,
        use_safetensors=True,
        torch_dtype=torch.float32,
    )
    if any(loading[key] for key in ("missing_keys", "unexpected_keys", "mismatched_keys")):
        raise RuntimeError(f"checkpoint key mismatch: {loading}")
    if checkpoint_model.esm.pooler is not None:
        raise RuntimeError("pooler must be absent")
    backbone = checkpoint_model.esm.to(device="cuda", dtype=torch.float32).eval()
    for parameter in backbone.parameters():
        parameter.requires_grad_(False)

    hidden_size = int(candidate["hidden_size"])
    output = np.empty((len(records), hidden_size), dtype=np.float32)
    active_sum: dict[int, np.ndarray] = {}
    active_count: dict[int, np.ndarray] = {}
    windows = windows_for(records)
    batches = list(greedy_window_batches(windows))
    started = time.monotonic()
    completed_sequences = 0
    with torch.inference_mode():
        for batch_index, batch in enumerate(batches, start=1):
            texts = [records[item.sequence_index].sequence[item.start : item.stop] for item in batch]
            encoded = tokenizer(texts, return_tensors="pt", padding=True, add_special_tokens=True)
            for row_index, item in enumerate(batch):
                nonpad = int(encoded["attention_mask"][row_index].sum())
                if nonpad != item.residues + 2:
                    raise RuntimeError("tokenizer residue/special-token count mismatch")
            encoded = {key: value.cuda(non_blocking=False) for key, value in encoded.items()}
            hidden = backbone(**encoded).last_hidden_state
            if hidden.dtype != torch.float32:
                raise RuntimeError("embedding forward dtype drift")
            for row_index, item in enumerate(batch):
                sequence_index = item.sequence_index
                record = records[sequence_index]
                if sequence_index not in active_sum:
                    active_sum[sequence_index] = np.zeros(
                        (record.sequence_length, hidden_size), dtype=np.float32
                    )
                    active_count[sequence_index] = np.zeros(record.sequence_length, dtype=np.uint16)
                residue_hidden = (
                    hidden[row_index, 1 : 1 + item.residues]
                    .detach()
                    .cpu()
                    .numpy()
                    .astype(np.float32, copy=False)
                )
                active_sum[sequence_index][item.start : item.stop] += residue_hidden
                active_count[sequence_index][item.start : item.stop] += 1
                if item.final_for_sequence:
                    counts = active_count.pop(sequence_index)
                    sums = active_sum.pop(sequence_index)
                    if np.any(counts == 0):
                        raise RuntimeError("incomplete residue coverage during pooling")
                    averaged = sums / counts[:, None]
                    vector = averaged.mean(axis=0, dtype=np.float32)
                    if vector.dtype != np.float32 or not np.isfinite(vector).all():
                        raise RuntimeError("nonfinite or non-FP32 pooled vector")
                    output[sequence_index] = vector
                    completed_sequences += 1
            if batch_index % 100 == 0 or batch_index == len(batches):
                print(
                    f"{candidate_id}: batch {batch_index}/{len(batches)}; "
                    f"sequences {completed_sequences}/{len(records)}",
                    flush=True,
                )
    if active_sum or active_count or completed_sequences != len(records):
        raise RuntimeError("embedding extraction ended with incomplete sequences")
    elapsed = time.monotonic() - started
    metadata = {
        "batches": len(batches),
        "elapsed_seconds": elapsed,
        "gpu_hours": elapsed / 3600.0,
        "residue_window_tokens": sum(item.residues for item in windows),
        "windows": len(windows),
    }
    del backbone, checkpoint_model
    torch.cuda.empty_cache()
    return output, metadata


def write_normalization(
    *, project_root: Path, records: Sequence[SequenceRecord], matrix: np.ndarray, output_root: Path
) -> dict[str, Any]:
    partition_path = project_root / PARTITIONS_PATH
    require_sha256(partition_path, PARTITIONS_SHA256)
    table = pq.read_table(partition_path, columns=["reference_sequence_sha256", "partition"])
    partition_by_sha = dict(
        zip(
            table["reference_sequence_sha256"].to_pylist(),
            table["partition"].to_pylist(),
            strict=True,
        )
    )
    training_indices = np.asarray(
        [index for index, record in enumerate(records) if partition_by_sha[record.sequence_sha256] == "train"],
        dtype=np.int64,
    )
    if training_indices.size != TRAIN_ENDPOINTS:
        raise RuntimeError("normalization population is not exactly 11,900 training endpoints")
    training = matrix[training_indices].astype(np.float64)
    mean = training.mean(axis=0, dtype=np.float64)
    raw_std = training.std(axis=0, dtype=np.float64, ddof=0)
    std = np.maximum(raw_std, 1e-6)
    standardized = ((matrix.astype(np.float64) - mean) / std).astype(np.float32)
    if not np.isfinite(standardized).all():
        raise RuntimeError("nonfinite standardized embeddings")
    normalizer_path = output_root / "training_normalization.npz"
    standardized_path = output_root / "standardized_embeddings.f32.npy"
    atomic_npz(
        normalizer_path,
        mean=mean,
        raw_standard_deviation=raw_std,
        standard_deviation=std,
        training_indices=training_indices,
    )
    atomic_numpy(standardized_path, standardized)
    return {
        "heldout_endpoint_statistics_used": False,
        "mean_dtype": str(mean.dtype),
        "normalizer_path": normalizer_path.relative_to(project_root).as_posix(),
        "normalizer_sha256": sha256_file(normalizer_path),
        "population": int(training_indices.size),
        "standard_deviation_floor": 1e-6,
        "standardized_matrix_path": standardized_path.relative_to(project_root).as_posix(),
        "standardized_matrix_sha256": sha256_file(standardized_path),
        "standardized_matrix_dtype": str(standardized.dtype),
    }


def extract_candidate(*, project_root: Path, candidate_id: str) -> dict[str, Any]:
    if candidate_id not in CANDIDATES:
        raise RuntimeError(f"candidate not frozen: {candidate_id}")
    endpoint_path = project_root / ENDPOINTS_PATH
    model_root = project_root / MODEL_CACHE_ROOT / candidate_id
    require_sha256(endpoint_path, ENDPOINTS_SHA256)
    require_sha256(model_root / "model.safetensors", CANDIDATES[candidate_id]["checkpoint_sha256"])
    output_root = project_root / EMBEDDING_ROOT / candidate_id
    if output_root.exists() and any(output_root.iterdir()):
        raise RuntimeError(f"refusing to overwrite embedding snapshot: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    records = ordered_records(endpoint_path)
    matrix, full_metadata = extract_matrix(
        candidate_id=candidate_id, records=records, model_root=model_root
    )
    matrix_path = output_root / "pooled_embeddings.f32.npy"
    atomic_numpy(matrix_path, matrix)

    repeat_count = math.ceil(len(records) * REPEAT_FRACTION)
    selected_indices = sorted(
        sorted(
            range(len(records)),
            key=lambda index: repeat_selection_key(candidate_id, records[index].sequence_sha256),
        )[:repeat_count],
        key=lambda index: (records[index].sequence_length, records[index].sequence_sha256),
    )
    repeat_records = [records[index] for index in selected_indices]
    repeated, repeat_metadata = extract_matrix(
        candidate_id=candidate_id, records=repeat_records, model_root=model_root
    )
    differences = np.max(np.abs(repeated - matrix[selected_indices]), axis=1)
    maximum_difference = float(differences.max(initial=0.0))
    if maximum_difference > REPEAT_TOLERANCE:
        raise RuntimeError(f"embedding repeat tolerance exceeded: {maximum_difference}")

    normalization = write_normalization(
        project_root=project_root,
        records=records,
        matrix=matrix,
        output_root=output_root,
    )
    tokens = tokenizer_hashes(model_root)
    producer_commit = git_commit(project_root)
    vector_records = []
    for row_index, record in enumerate(records):
        vector = np.ascontiguousarray(matrix[row_index], dtype=np.float32)
        vector_records.append(
            {
                "cache_key": cache_key(candidate_id, record.sequence_sha256),
                "candidate_id": candidate_id,
                "checkpoint_sha256": CANDIDATES[candidate_id]["checkpoint_sha256"],
                "code_commit": producer_commit,
                "container_sha256": MODEL_SIF_SHA256,
                "repository_revision": CANDIDATES[candidate_id]["revision"],
                "row_index": row_index,
                "sequence_length": record.sequence_length,
                "sequence_sha256": record.sequence_sha256,
                "strategy_id": STRATEGY_ID,
                "tokenizer_file_hashes": tokens,
                "vector_dimension": int(vector.size),
                "vector_dtype": str(vector.dtype),
                "vector_sha256": sha256_bytes(vector.tobytes(order="C")),
            }
        )
    repeat_report = {
        "candidate_id": candidate_id,
        "fraction": REPEAT_FRACTION,
        "maximum_absolute_difference": maximum_difference,
        "records": [
            {
                "maximum_absolute_difference": float(differences[position]),
                "sequence_sha256": repeat_records[position].sequence_sha256,
            }
            for position in range(len(repeat_records))
        ],
        "repeat_count": repeat_count,
        "selection": "bottom_SHA256(candidate_id:sequence_sha256)",
        "status": "pass",
        "tolerance": REPEAT_TOLERANCE,
    }
    repeat_path = output_root / "deterministic_repeat_report.json"
    atomic_json(repeat_path, repeat_report)
    manifest = {
        "candidate_id": candidate_id,
        "checkpoint_sha256": CANDIDATES[candidate_id]["checkpoint_sha256"],
        "code_commit": producer_commit,
        "container_sha256": MODEL_SIF_SHA256,
        "embedding_extractions": "one_complete_population_pass_plus_prespecified_one_percent_repeat",
        "full_extraction": full_metadata,
        "matrix_bytes": matrix_path.stat().st_size,
        "matrix_dtype": str(matrix.dtype),
        "matrix_path": matrix_path.relative_to(project_root).as_posix(),
        "matrix_sha256": sha256_file(matrix_path),
        "normalization": normalization,
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "protocol_id": PROTOCOL_ID,
        "repeat_extraction": repeat_metadata,
        "repeat_report_path": repeat_path.relative_to(project_root).as_posix(),
        "repeat_report_sha256": sha256_file(repeat_path),
        "repository_revision": CANDIDATES[candidate_id]["revision"],
        "schema_version": 1,
        "strategy_id": STRATEGY_ID,
        "tokenizer_file_hashes": tokens,
        "vector_count": len(vector_records),
        "vectors": vector_records,
    }
    manifest_path = output_root / "EMBEDDING_MANIFEST.json"
    atomic_json(manifest_path, manifest)
    print(manifest_path.relative_to(project_root))
    return manifest
