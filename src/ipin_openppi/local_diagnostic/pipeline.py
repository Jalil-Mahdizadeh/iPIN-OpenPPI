"""Executable public-training-only DEC-0041 local-representation diagnostic."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pyarrow.parquet as pq
from scipy import sparse
import yaml

from ipin_openppi.development_evaluation.semantics import (
    pair_component_multipliers,
    percentile_95,
    weighted_pairwise_concordance,
)
from ipin_openppi.stage1.baselines import (
    deterministic_hash_score,
    kmer3_csr,
    length_ratio_score,
)
from ipin_openppi.stage1.embeddings import (
    SequenceRecord,
    greedy_window_batches,
    ordered_records,
    tokenizer_hashes,
    windows_for,
)
from ipin_openppi.stage1.support import (
    atomic_json,
    atomic_numpy,
    git_commit,
    require_sha256,
    sha256_file,
)

from .semantics import (
    MAX_SEGMENTS,
    SPLIT_SALT,
    TARGET_HELDOUT_ENDPOINTS,
    fp32_reconstruction_within_tolerance,
    local_pair_scores,
    nested_cell,
    phase_a_trigger,
    segment_boundaries,
    select_heldout_components,
)


PROTOCOL_ID = "public_training_local_representation_diagnostic_v1_revision_2"
BASE_CONFIG = Path("configs/public_training_local_representation_diagnostic_v1.yaml")
BASE_CONFIG_SHA256 = "63e0d4e194b5db88a51e245b2ddf767e4ce11142659ac8c24deb3afbb6be749d"
REVISION_CONFIG = Path(
    "configs/public_training_local_representation_diagnostic_v1_revision_2.yaml"
)
REVISION_CONFIG_SHA256 = "c22d8de53d6f53a0f8054767387dc8a28541c353e0dabaff8041005e1ffe12fc"
REVISION_PROTOCOL = Path(
    "docs/protocols/PUBLIC_TRAINING_LOCAL_REPRESENTATION_DIAGNOSTIC_v1_revision_2.md"
)
REVISION_PROTOCOL_SHA256 = "6940e7ba91f3a7835b1bd70b2d84594ac5af495013f01084a37897a2c2201a69"

ENDPOINTS = Path(
    "data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/"
    "eligible_reference_sequences/part-00000.parquet"
)
ENDPOINTS_SHA256 = "4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e"
PARTITIONS = Path(
    "data/canonical/final_benchmark_component_split_v1/"
    "endpoint_partition_assignments/part-00000.parquet"
)
PARTITIONS_SHA256 = "66db8cd59e7cb8cf06ff3ad785448dfc7d5fdd24643811946246d129b0bd8a67"
POSITIVE = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "positive_pairs/part-00000.parquet"
)
POSITIVE_SHA256 = "4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499"
UNLABELED = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "unlabeled_pairs/part-00000.parquet"
)
UNLABELED_SHA256 = "d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7"
MODEL_ROOT = Path(
    "artifacts/cache/models/model_governance_and_baseline_training_protocol_v1/esm2_150m"
)
MODEL_SHA256 = "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566"
MODEL_REVISION = "a695f6045e2e32885fa60af20c13cb35398ce30c"
MODEL_SIF = Path("containers/images/ipin-model-arm64_0.1.0.sif")
MODEL_SIF_SHA256 = "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"
PARENT_POOLED = Path(
    "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/"
    "esm2_150m/pooled_embeddings.f32.npy"
)
PARENT_POOLED_SHA256 = "4450a0a250e2ef84efcd48f627169b003097110e51b82530ba218f6a599ee7a0"

EMBEDDING_ROOT = Path("artifacts/embeddings") / PROTOCOL_ID / "esm2_150m"
METRIC_ROOT = Path("artifacts/metrics") / PROTOCOL_ID / "nested_C3"
VALIDATION_ROOT = Path("artifacts/validation/model_execution") / PROTOCOL_ID

TOKENIZER_HASHES = {
    "config.json": "e512f68ec444d99477703a9806639ca83da3dbc19f6c5fe428d6e5b7460972dc",
    "special_tokens_map.json": "3aedcd4211c0d43aec4e607ff60a63255f3174ead795e997350f09a5f8cd9ee1",
    "tokenizer_config.json": "7e9161ecdb548ec45a41cbc6b24aa4476fdd418461f491c4207baa99419a29ad",
    "vocab.txt": "0b82cc0a7c7cf9e567b1e5892d793285b9fbae822c964ca48696f7db44598e03",
}
SCORERS = (
    "deterministic_hash",
    "sequence_length_ratio",
    "within_pair_3mer_cosine",
    "exact_nested_training_interolog_3mer",
    "matched_global_pooled_esm_cosine",
    "local_max_segment_cosine",
    "local_top4_segment_cosine",
)
EXPECTED_CELL_COUNTS = {
    "P": {"C1": 11_051, "C2": 5_098, "C3": 650},
    "U": {"C1": 1_254_297, "C2": 659_253, "C3": 86_450},
}
BOOTSTRAP_REPLICATES = 200
BOOTSTRAP_SALT = "20260819-local-representation-diagnostic-v1"


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"mapping required: {path}")
    return payload


def _input_preflight(project_root: Path) -> dict[str, Any]:
    frozen = (
        (BASE_CONFIG, BASE_CONFIG_SHA256),
        (REVISION_CONFIG, REVISION_CONFIG_SHA256),
        (REVISION_PROTOCOL, REVISION_PROTOCOL_SHA256),
        (ENDPOINTS, ENDPOINTS_SHA256),
        (PARTITIONS, PARTITIONS_SHA256),
        (POSITIVE, POSITIVE_SHA256),
        (UNLABELED, UNLABELED_SHA256),
        (MODEL_SIF, MODEL_SIF_SHA256),
        (MODEL_ROOT / "model.safetensors", MODEL_SHA256),
        (PARENT_POOLED, PARENT_POOLED_SHA256),
    )
    for relative, expected in frozen:
        require_sha256(project_root / relative, expected)
    for filename, expected in TOKENIZER_HASHES.items():
        require_sha256(project_root / MODEL_ROOT / filename, expected)
    base = _load_yaml(project_root / BASE_CONFIG)
    revision = _load_yaml(project_root / REVISION_CONFIG)
    if (
        base["scientific_boundary"]["development_information_used"] is not False
        or base["scientific_boundary"]["protected_candidate_truth_or_key_access"] is not False
        or revision["execution_source_of_truth"]["no_score_or_embedding_existed_when_frozen"]
        is not True
        or revision["scorer_delta"]["retained_phase_a_scorers"] != list(SCORERS)
    ):
        raise RuntimeError("governance boundary or scorer set drift")
    return {
        "base_config_sha256": BASE_CONFIG_SHA256,
        "checkpoint_sha256": MODEL_SHA256,
        "container_sha256": MODEL_SIF_SHA256,
        "revision_config_sha256": REVISION_CONFIG_SHA256,
        "revision_protocol_sha256": REVISION_PROTOCOL_SHA256,
        "tokenizer_hashes": TOKENIZER_HASHES,
    }


def _partition_state(
    project_root: Path,
) -> tuple[dict[str, str], dict[str, str], frozenset[str], dict[str, int]]:
    table = pq.read_table(
        project_root / PARTITIONS,
        columns=[
            "reference_sequence_sha256",
            "component_id",
            "component_size",
            "partition",
        ],
    )
    endpoint_component: dict[str, str] = {}
    endpoint_partition: dict[str, str] = {}
    component_sizes: dict[str, int] = {}
    for endpoint, component, size, partition in zip(
        table["reference_sequence_sha256"].to_pylist(),
        table["component_id"].to_pylist(),
        table["component_size"].to_pylist(),
        table["partition"].to_pylist(),
        strict=True,
    ):
        endpoint = str(endpoint)
        component = str(component)
        endpoint_component[endpoint] = component
        endpoint_partition[endpoint] = str(partition)
        if partition == "train":
            prior = component_sizes.setdefault(component, int(size))
            if prior != int(size):
                raise RuntimeError("component size is inconsistent")
    train_count = sum(value == "train" for value in endpoint_partition.values())
    if train_count != 11_900 or len(component_sizes) != 5_427:
        raise RuntimeError("public training endpoint/component census drift")
    if sum(component_sizes.values()) != 11_900:
        raise RuntimeError("training component sizes do not sum to 11,900")
    heldout = select_heldout_components(component_sizes)
    heldout_count = sum(component_sizes[component] for component in heldout)
    if len(heldout) != 1_366 or heldout_count != TARGET_HELDOUT_ENDPOINTS:
        raise RuntimeError("nested heldout census drift")
    return endpoint_component, endpoint_partition, heldout, component_sizes


def _pair_cell_counts(project_root: Path, heldout: frozenset[str]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for label, relative in (("P", POSITIVE), ("U", UNLABELED)):
        table = pq.read_table(
            project_root / relative,
            columns=["endpoint_a_component_id", "endpoint_b_component_id"],
        )
        counts = Counter(
            nested_cell(left, right, heldout)
            for left, right in zip(
                table["endpoint_a_component_id"].to_pylist(),
                table["endpoint_b_component_id"].to_pylist(),
                strict=True,
            )
        )
        output[label] = {cell: int(counts[cell]) for cell in ("C1", "C2", "C3")}
    if output != EXPECTED_CELL_COUNTS:
        raise RuntimeError(f"nested public row census drift: {output}")
    return output


def _training_records(
    project_root: Path, endpoint_partition: Mapping[str, str]
) -> tuple[list[SequenceRecord], list[SequenceRecord]]:
    all_records = ordered_records(project_root / ENDPOINTS)
    training = [
        record for record in all_records if endpoint_partition[record.sequence_sha256] == "train"
    ]
    if len(training) != 11_900:
        raise RuntimeError("training record count drift")
    return all_records, training


def _artifact(path: Path, project_root: Path) -> dict[str, Any]:
    return {
        "bytes": path.stat().st_size,
        "path": path.relative_to(project_root).as_posix(),
        "sha256": sha256_file(path),
    }


def _verify_embedding_manifest(project_root: Path) -> dict[str, Any] | None:
    path = project_root / EMBEDDING_ROOT / "LOCAL_EMBEDDING_MANIFEST.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload["protocol_id"] != PROTOCOL_ID or payload["checkpoint_sha256"] != MODEL_SHA256:
        raise RuntimeError("local embedding manifest identity drift")
    for record in payload["artifacts"].values():
        artifact = project_root / record["path"]
        if artifact.stat().st_size != record["bytes"] or sha256_file(artifact) != record["sha256"]:
            raise RuntimeError(f"local embedding artifact drift: {artifact}")
    return payload


def extract_local_embeddings(project_root: Path) -> dict[str, Any]:
    """Extract frozen 150M contextual segments for all public-training endpoints."""

    preflight = _input_preflight(project_root)
    existing = _verify_embedding_manifest(project_root)
    if existing is not None:
        print("verified existing local embedding snapshot", flush=True)
        return existing
    output_root = project_root / EMBEDDING_ROOT
    if output_root.exists() and any(output_root.iterdir()):
        raise RuntimeError(f"refusing to overwrite partial local embedding root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    endpoint_component, endpoint_partition, heldout, _ = _partition_state(project_root)
    cell_counts = _pair_cell_counts(project_root, heldout)
    all_records, records = _training_records(project_root, endpoint_partition)
    boundaries = [segment_boundaries(record.sequence_length) for record in records]
    offsets = np.zeros(len(records) + 1, dtype=np.int64)
    offsets[1:] = np.cumsum([len(value) for value in boundaries], dtype=np.int64)
    segment_count = int(offsets[-1])
    segments = np.empty((segment_count, 640), dtype=np.float32)
    segment_lengths = np.empty(segment_count, dtype=np.int32)
    global_vectors = np.empty((len(records), 640), dtype=np.float32)

    import torch
    from transformers import EsmForMaskedLM, EsmTokenizer

    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise RuntimeError("offline Hugging Face/Transformers mode required")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("exactly one CUDA GPU required")
    model_root = project_root / MODEL_ROOT
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
    backbone = checkpoint_model.esm.to(device="cuda", dtype=torch.float32).eval()
    for parameter in backbone.parameters():
        parameter.requires_grad_(False)

    windows = windows_for(records)
    batches = list(greedy_window_batches(windows))
    active_sum: dict[int, np.ndarray] = {}
    active_count: dict[int, np.ndarray] = {}
    completed = 0
    reconstruction_maximum = 0.0
    started = time.monotonic()
    with torch.inference_mode():
        for batch_index, batch in enumerate(batches, start=1):
            texts = [records[item.sequence_index].sequence[item.start : item.stop] for item in batch]
            encoded = tokenizer(texts, return_tensors="pt", padding=True, add_special_tokens=True)
            for row_index, item in enumerate(batch):
                if int(encoded["attention_mask"][row_index].sum()) != item.residues + 2:
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
                        (record.sequence_length, 640), dtype=np.float32
                    )
                    active_count[sequence_index] = np.zeros(
                        record.sequence_length, dtype=np.uint16
                    )
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
                        raise RuntimeError("incomplete residue coverage")
                    averaged = sums / counts[:, None]
                    row_start, row_stop = int(offsets[sequence_index]), int(
                        offsets[sequence_index + 1]
                    )
                    for position, (start, stop) in enumerate(boundaries[sequence_index]):
                        segments[row_start + position] = averaged[start:stop].mean(
                            axis=0, dtype=np.float32
                        )
                        segment_lengths[row_start + position] = stop - start
                    global_from_residues = averaged.mean(axis=0, dtype=np.float32)
                    global_from_segments = np.average(
                        segments[row_start:row_stop].astype(np.float64),
                        axis=0,
                        weights=segment_lengths[row_start:row_stop],
                    ).astype(np.float32)
                    reconstruction_maximum = max(
                        reconstruction_maximum,
                        float(np.max(np.abs(global_from_residues - global_from_segments))),
                    )
                    global_vectors[sequence_index] = global_from_segments
                    completed += 1
            if batch_index % 100 == 0 or batch_index == len(batches):
                print(
                    f"local-esm2-150m: batch {batch_index}/{len(batches)}; "
                    f"sequences {completed}/{len(records)}",
                    flush=True,
                )
    if active_sum or active_count or completed != len(records):
        raise RuntimeError("local embedding extraction ended incomplete")
    if not fp32_reconstruction_within_tolerance(reconstruction_maximum):
        raise RuntimeError(f"segment/global reconstruction tolerance failed: {reconstruction_maximum}")

    parent = np.load(project_root / PARENT_POOLED, allow_pickle=False, mmap_mode="r")
    all_index = {record.sequence_sha256: index for index, record in enumerate(all_records)}
    parent_rows = np.fromiter(
        (all_index[record.sequence_sha256] for record in records), dtype=np.int64
    )
    parent_maximum = float(
        np.max(np.abs(global_vectors - np.asarray(parent[parent_rows], dtype=np.float32)))
    )
    if parent_maximum > 1e-4:
        raise RuntimeError(f"local run differs materially from parent pooled embedding: {parent_maximum}")
    if not (
        np.isfinite(segments).all()
        and np.isfinite(global_vectors).all()
        and np.all(segment_lengths > 0)
        and np.array_equal(
            np.add.reduceat(segment_lengths, offsets[:-1]),  # type: ignore[arg-type]
            np.asarray([record.sequence_length for record in records], dtype=np.int64),
        )
    ):
        raise RuntimeError("local embedding arrays failed finiteness or length accounting")

    segment_path = output_root / "segment_embeddings.f32.npy"
    length_path = output_root / "segment_lengths.i32.npy"
    offset_path = output_root / "endpoint_offsets.i64.npy"
    global_path = output_root / "matched_global_embeddings.f32.npy"
    endpoint_path = output_root / "ENDPOINTS.json"
    atomic_numpy(segment_path, segments)
    atomic_numpy(length_path, segment_lengths)
    atomic_numpy(offset_path, offsets)
    atomic_numpy(global_path, global_vectors)
    atomic_json(
        endpoint_path,
        {
            "endpoint_sha256s": [record.sequence_sha256 for record in records],
            "sequence_lengths": [record.sequence_length for record in records],
        },
    )
    elapsed = time.monotonic() - started
    artifacts = {
        "endpoint_index": _artifact(endpoint_path, project_root),
        "endpoint_offsets": _artifact(offset_path, project_root),
        "matched_global_embeddings": _artifact(global_path, project_root),
        "segment_embeddings": _artifact(segment_path, project_root),
        "segment_lengths": _artifact(length_path, project_root),
    }
    manifest = {
        "artifacts": artifacts,
        "cell_counts": cell_counts,
        "checkpoint_sha256": MODEL_SHA256,
        "code_commit": git_commit(project_root),
        "container_sha256": MODEL_SIF_SHA256,
        "elapsed_seconds": elapsed,
        "endpoint_count": len(records),
        "heldout_component_count": len(heldout),
        "heldout_endpoint_count": TARGET_HELDOUT_ENDPOINTS,
        "maximum_parent_pooled_absolute_difference": parent_maximum,
        "maximum_segment_global_reconstruction_difference": reconstruction_maximum,
        "maximum_segment_global_reconstruction_tolerance": 1e-4,
        "model_revision": MODEL_REVISION,
        "preflight": preflight,
        "protocol_id": PROTOCOL_ID,
        "segment_count": segment_count,
        "segment_dimension": 640,
        "segment_strategy": "contiguous_equal_bins_target128_cap32_v1",
        "status": "pass",
        "tokenizer_file_hashes": tokenizer_hashes(model_root),
        "windows": len(windows),
    }
    atomic_json(output_root / "LOCAL_EMBEDDING_MANIFEST.json", manifest)
    del backbone, checkpoint_model
    torch.cuda.empty_cache()
    print(json.dumps({key: manifest[key] for key in ("elapsed_seconds", "endpoint_count", "segment_count")}, sort_keys=True), flush=True)
    return manifest


def _load_cell_rows(
    project_root: Path, relative: Path, heldout: frozenset[str], expected_state: str
) -> dict[str, Any]:
    columns = [
        "pair_id",
        "endpoint_a_sha256",
        "endpoint_b_sha256",
        "endpoint_a_component_id",
        "endpoint_b_component_id",
        "sampling_weight_numerator",
        "sampling_weight_denominator",
        "state",
    ]
    table = pq.read_table(project_root / relative, columns=columns)
    data = table.to_pydict()
    selected = [
        index
        for index, (left, right) in enumerate(
            zip(data["endpoint_a_component_id"], data["endpoint_b_component_id"], strict=True)
        )
        if nested_cell(left, right, heldout) == "C3"
    ]
    output = {column: [data[column][index] for index in selected] for column in columns}
    if set(map(str, output["state"])) != {expected_state}:
        raise RuntimeError("nested C3 row state drift")
    return output


def _concat_rows(positive: Mapping[str, Sequence[Any]], unlabeled: Mapping[str, Sequence[Any]]) -> dict[str, list[Any]]:
    return {key: list(positive[key]) + list(unlabeled[key]) for key in positive}


def _local_scores_gpu(
    *,
    segments: np.ndarray,
    segment_lengths: np.ndarray,
    offsets: np.ndarray,
    global_vectors: np.ndarray,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    import torch

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("exactly one CUDA GPU required for local scoring")
    counts = np.diff(offsets).astype(np.int64)
    if counts.max(initial=0) > MAX_SEGMENTS or counts.min() < 1:
        raise RuntimeError("endpoint segment count outside frozen bounds")
    norms = np.linalg.norm(segments.astype(np.float64), axis=1)
    if np.any(norms == 0) or not np.isfinite(norms).all():
        raise RuntimeError("zero/nonfinite segment norm")
    unit = segments / norms[:, None].astype(np.float32)
    padded = np.zeros((counts.size, MAX_SEGMENTS, segments.shape[1]), dtype=np.float32)
    mask = np.zeros((counts.size, MAX_SEGMENTS), dtype=bool)
    for endpoint_index, count in enumerate(counts):
        start, stop = int(offsets[endpoint_index]), int(offsets[endpoint_index + 1])
        padded[endpoint_index, :count] = unit[start:stop]
        mask[endpoint_index, :count] = True
    global_norm = np.linalg.norm(global_vectors.astype(np.float64), axis=1)
    if np.any(global_norm == 0) or not np.isfinite(global_norm).all():
        raise RuntimeError("zero/nonfinite matched-global norm")
    global_unit = global_vectors / global_norm[:, None].astype(np.float32)

    segment_tensor = torch.from_numpy(padded).to(device="cuda", dtype=torch.float32)
    mask_tensor = torch.from_numpy(mask).to(device="cuda")
    global_tensor = torch.from_numpy(global_unit).to(device="cuda", dtype=torch.float32)
    global_output = np.empty(pair_a.size, dtype=np.float64)
    maximum_output = np.empty(pair_a.size, dtype=np.float64)
    top4_output = np.empty(pair_a.size, dtype=np.float64)
    with torch.inference_mode():
        for start in range(0, pair_a.size, 4_096):
            stop = min(start + 4_096, pair_a.size)
            left_index = torch.from_numpy(pair_a[start:stop]).to(device="cuda")
            right_index = torch.from_numpy(pair_b[start:stop]).to(device="cuda")
            left = segment_tensor.index_select(0, left_index)
            right = segment_tensor.index_select(0, right_index)
            similarities = torch.bmm(left, right.transpose(1, 2))
            valid = mask_tensor.index_select(0, left_index).unsqueeze(2) & mask_tensor.index_select(
                0, right_index
            ).unsqueeze(1)
            similarities = similarities.masked_fill(~valid, -torch.inf)
            flat = similarities.flatten(1)
            maximum_output[start:stop] = flat.amax(dim=1).cpu().numpy()
            top = flat.topk(k=4, dim=1, largest=True, sorted=False).values
            finite_top = torch.where(torch.isfinite(top), top, torch.zeros_like(top))
            valid_count = valid.sum(dim=(1, 2)).clamp(max=4)
            top4_output[start:stop] = (
                finite_top.sum(dim=1) / valid_count.to(dtype=torch.float32)
            ).cpu().numpy()
            global_output[start:stop] = (
                global_tensor.index_select(0, left_index)
                * global_tensor.index_select(0, right_index)
            ).sum(dim=1).cpu().numpy()
    del segment_tensor, mask_tensor, global_tensor
    torch.cuda.empty_cache()
    return global_output, maximum_output, top4_output


def _nested_interolog_scores(
    *,
    kmer: sparse.csr_matrix,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
    fit_edges_a: np.ndarray,
    fit_edges_b: np.ndarray,
) -> tuple[np.ndarray, float]:
    import torch

    exposed = np.unique(np.concatenate((fit_edges_a, fit_edges_b))).astype(np.int64)
    position = np.full(kmer.shape[0], -1, dtype=np.int64)
    position[exposed] = np.arange(exposed.size, dtype=np.int64)
    edge_u, edge_v = position[fit_edges_a], position[fit_edges_b]
    if np.any(edge_u < 0) or np.any(edge_v < 0):
        raise RuntimeError("nested interolog endpoint mapping failed")
    query = np.unique(np.concatenate((pair_a, pair_b))).astype(np.int64)
    query_position = np.full(kmer.shape[0], -1, dtype=np.int64)
    query_position[query] = np.arange(query.size, dtype=np.int64)
    similarities = (kmer[query] @ kmer[exposed].T).toarray().astype(np.float64, copy=False)
    neighbor_max = np.zeros_like(similarities)
    neighbors: dict[int, list[int]] = defaultdict(list)
    for left, right in zip(edge_u, edge_v, strict=True):
        neighbors[int(left)].append(int(right))
        neighbors[int(right)].append(int(left))
    for endpoint in range(exposed.size):
        values = neighbors.get(endpoint)
        if values:
            neighbor_max[:, endpoint] = similarities[:, values].max(axis=1)
    sim_tensor = torch.from_numpy(similarities).to(device="cuda", dtype=torch.float64)
    neighbor_tensor = torch.from_numpy(neighbor_max).to(device="cuda", dtype=torch.float64)
    qa, qb = query_position[pair_a], query_position[pair_b]
    output = np.empty(pair_a.size, dtype=np.float64)
    swap_maximum = 0.0
    with torch.inference_mode():
        for start in range(0, pair_a.size, 2_048):
            stop = min(start + 2_048, pair_a.size)
            left = torch.from_numpy(qa[start:stop]).to(device="cuda")
            right = torch.from_numpy(qb[start:stop]).to(device="cuda")
            forward = torch.minimum(
                sim_tensor.index_select(0, left), neighbor_tensor.index_select(0, right)
            ).amax(dim=1)
            reverse = torch.minimum(
                sim_tensor.index_select(0, right), neighbor_tensor.index_select(0, left)
            ).amax(dim=1)
            swap_maximum = max(
                swap_maximum, float(torch.max(torch.abs(forward - reverse)).cpu())
            )
            output[start:stop] = torch.maximum(forward, reverse).cpu().numpy()
    del sim_tensor, neighbor_tensor
    torch.cuda.empty_cache()
    return output, swap_maximum


def _bootstrap(
    *,
    scores: np.ndarray,
    positive_count: int,
    unlabeled_weights: np.ndarray,
    component_a: Sequence[str],
    component_b: Sequence[str],
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    components = tuple(sorted(set(map(str, component_a)) | set(map(str, component_b))))
    index = {component: position for position, component in enumerate(components)}
    left = np.fromiter((index[str(value)] for value in component_a), dtype=np.int64)
    right = np.fromiter((index[str(value)] for value in component_b), dtype=np.int64)
    seed = int.from_bytes(
        hashlib.sha256(f"{BOOTSTRAP_SALT}:bootstrap:nested_C3".encode()).digest()[:8],
        "big",
    )
    generator = np.random.Generator(np.random.PCG64DXSM(seed))
    draws = generator.integers(
        0, len(components), size=(BOOTSTRAP_REPLICATES, len(components)), dtype=np.int64
    )
    multiplicities = np.zeros_like(draws, dtype=np.int32)
    rows = np.arange(BOOTSTRAP_REPLICATES, dtype=np.int64)[:, None]
    np.add.at(multiplicities, (rows, draws), 1)
    metrics = np.full((scores.shape[1], BOOTSTRAP_REPLICATES), np.nan, dtype=np.float64)
    for replicate in range(BOOTSTRAP_REPLICATES):
        pair_multiplier = pair_component_multipliers(
            multiplicities[replicate], left, right
        ).astype(np.float64)
        p_multiplier = pair_multiplier[:positive_count]
        u_multiplier = pair_multiplier[positive_count:]
        if p_multiplier.sum() == 0 or u_multiplier.sum() == 0:
            continue
        for scorer_index in range(scores.shape[1]):
            metrics[scorer_index, replicate] = weighted_pairwise_concordance(
                scores[:positive_count, scorer_index],
                scores[positive_count:, scorer_index],
                unlabeled_weights,
                positive_multipliers=p_multiplier,
                unlabeled_multipliers=u_multiplier,
            )
    return metrics, multiplicities, components


def evaluate_phase_a(project_root: Path) -> dict[str, Any]:
    """Score and evaluate the frozen label-free nested-C3 oracle."""

    preflight = _input_preflight(project_root)
    embedding_manifest = _verify_embedding_manifest(project_root)
    if embedding_manifest is None:
        raise RuntimeError("local embedding snapshot must exist before evaluation")
    endpoint_component, endpoint_partition, heldout, _ = _partition_state(project_root)
    cell_counts = _pair_cell_counts(project_root, heldout)
    _, records = _training_records(project_root, endpoint_partition)
    endpoint_index = {record.sequence_sha256: index for index, record in enumerate(records)}

    positive = _load_cell_rows(project_root, POSITIVE, heldout, "released_positive")
    unlabeled = _load_cell_rows(project_root, UNLABELED, heldout, "unlabeled")
    if len(positive["pair_id"]) != 650 or len(unlabeled["pair_id"]) != 86_450:
        raise RuntimeError("nested C3 primary row census drift")
    rows = _concat_rows(positive, unlabeled)
    pair_a = np.fromiter(
        (endpoint_index[str(value)] for value in rows["endpoint_a_sha256"]), dtype=np.int64
    )
    pair_b = np.fromiter(
        (endpoint_index[str(value)] for value in rows["endpoint_b_sha256"]), dtype=np.int64
    )
    if np.any(pair_a == pair_b):
        raise RuntimeError("self pair entered nested C3")
    pair_ids = tuple(map(str, rows["pair_id"]))
    positive_count = len(positive["pair_id"])
    score_matrix = np.empty((len(pair_ids), len(SCORERS)), dtype=np.float64)
    score_matrix[:, 0] = np.fromiter(
        (deterministic_hash_score(pair_id) for pair_id in pair_ids), dtype=np.float64
    )
    score_matrix[:, 1] = np.fromiter(
        (
            length_ratio_score(records[left].sequence_length, records[right].sequence_length)
            for left, right in zip(pair_a, pair_b, strict=True)
        ),
        dtype=np.float64,
    )

    sequences = [record.sequence for record in records]
    kmer = kmer3_csr(sequences)
    for start in range(0, len(pair_ids), 100_000):
        stop = min(start + 100_000, len(pair_ids))
        values = kmer[pair_a[start:stop]].multiply(kmer[pair_b[start:stop]]).sum(axis=1)
        score_matrix[start:stop, 2] = np.asarray(values).ravel()
    fit_table = pq.read_table(
        project_root / POSITIVE,
        columns=[
            "endpoint_a_sha256",
            "endpoint_b_sha256",
            "endpoint_a_component_id",
            "endpoint_b_component_id",
        ],
    ).to_pydict()
    fit_indexes = [
        index
        for index, (left, right) in enumerate(
            zip(
                fit_table["endpoint_a_component_id"],
                fit_table["endpoint_b_component_id"],
                strict=True,
            )
        )
        if nested_cell(left, right, heldout) == "C1"
    ]
    fit_a = np.fromiter(
        (
            endpoint_index[str(fit_table["endpoint_a_sha256"][index])]
            for index in fit_indexes
        ),
        dtype=np.int64,
    )
    fit_b = np.fromiter(
        (
            endpoint_index[str(fit_table["endpoint_b_sha256"][index])]
            for index in fit_indexes
        ),
        dtype=np.int64,
    )
    score_matrix[:, 3], interolog_swap_maximum = _nested_interolog_scores(
        kmer=kmer,
        pair_a=pair_a,
        pair_b=pair_b,
        fit_edges_a=fit_a,
        fit_edges_b=fit_b,
    )

    embedding_root = project_root / EMBEDDING_ROOT
    segments = np.load(embedding_root / "segment_embeddings.f32.npy", allow_pickle=False)
    segment_lengths = np.load(embedding_root / "segment_lengths.i32.npy", allow_pickle=False)
    offsets = np.load(embedding_root / "endpoint_offsets.i64.npy", allow_pickle=False)
    global_vectors = np.load(
        embedding_root / "matched_global_embeddings.f32.npy", allow_pickle=False
    )
    score_matrix[:, 4], score_matrix[:, 5], score_matrix[:, 6] = _local_scores_gpu(
        segments=segments,
        segment_lengths=segment_lengths,
        offsets=offsets,
        global_vectors=global_vectors,
        pair_a=pair_a,
        pair_b=pair_b,
    )
    if not np.isfinite(score_matrix).all():
        raise RuntimeError("nonfinite phase-A score")

    sample_indices = sorted(
        range(len(pair_ids)),
        key=lambda index: hashlib.sha256(
            f"local-cpu-check:{pair_ids[index]}".encode()
        ).digest(),
    )[:100]
    cpu_maximum_difference = 0.0
    for index in sample_indices:
        left, right = int(pair_a[index]), int(pair_b[index])
        left_start, left_stop = int(offsets[left]), int(offsets[left + 1])
        right_start, right_stop = int(offsets[right]), int(offsets[right + 1])
        expected = local_pair_scores(
            segments[left_start:left_stop],
            segment_lengths[left_start:left_stop],
            segments[right_start:right_stop],
            segment_lengths[right_start:right_stop],
        )
        observed = score_matrix[index, 4:7]
        reference = np.asarray(
            [
                expected.matched_global_pooled_esm_cosine,
                expected.local_max_segment_cosine,
                expected.local_top4_segment_cosine,
            ]
        )
        cpu_maximum_difference = max(
            cpu_maximum_difference, float(np.max(np.abs(observed - reference)))
        )
    if cpu_maximum_difference > 2e-6:
        raise RuntimeError(f"GPU local scorer differs from CPU reference: {cpu_maximum_difference}")

    numerator = np.asarray(unlabeled["sampling_weight_numerator"], dtype=np.float64)
    denominator = np.asarray(unlabeled["sampling_weight_denominator"], dtype=np.float64)
    if np.any(numerator <= 0) or np.any(denominator <= 0):
        raise RuntimeError("nested C3 U design weights must be positive")
    unlabeled_weights = numerator / denominator
    points = {
        scorer: weighted_pairwise_concordance(
            score_matrix[:positive_count, index],
            score_matrix[positive_count:, index],
            unlabeled_weights,
        )
        for index, scorer in enumerate(SCORERS)
    }
    bootstrap, multiplicities, components = _bootstrap(
        scores=score_matrix,
        positive_count=positive_count,
        unlabeled_weights=unlabeled_weights,
        component_a=rows["endpoint_a_component_id"],
        component_b=rows["endpoint_b_component_id"],
    )
    intervals = {
        scorer: percentile_95(bootstrap[index]) for index, scorer in enumerate(SCORERS)
    }
    global_index = SCORERS.index("matched_global_pooled_esm_cosine")
    local_index = SCORERS.index("local_top4_segment_cosine")
    delta_distribution = bootstrap[local_index] - bootstrap[global_index]
    delta_interval = percentile_95(delta_distribution)
    trigger, delta = phase_a_trigger(
        points["local_top4_segment_cosine"],
        points["matched_global_pooled_esm_cosine"],
    )

    metric_root = project_root / METRIC_ROOT
    if metric_root.exists() and any(metric_root.iterdir()):
        raise RuntimeError(f"refusing to overwrite metric snapshot: {metric_root}")
    metric_root.mkdir(parents=True, exist_ok=True)
    score_path = metric_root / "phase_a_scores.f64.npy"
    bootstrap_path = metric_root / "bootstrap_metrics.f64.npy"
    multiplicity_path = metric_root / "component_multiplicities.i32.npy"
    scorer_path = metric_root / "SCORERS.json"
    component_path = metric_root / "BOOTSTRAP_COMPONENTS.json"
    atomic_numpy(score_path, score_matrix)
    atomic_numpy(bootstrap_path, bootstrap)
    atomic_numpy(multiplicity_path, multiplicities)
    atomic_json(scorer_path, {"scorers": list(SCORERS)})
    atomic_json(component_path, {"components": list(components)})
    artifacts = {
        "bootstrap_components": _artifact(component_path, project_root),
        "bootstrap_metrics": _artifact(bootstrap_path, project_root),
        "component_multiplicities": _artifact(multiplicity_path, project_root),
        "phase_a_scores": _artifact(score_path, project_root),
        "scorers": _artifact(scorer_path, project_root),
    }
    results = {
        "artifacts": artifacts,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "cell": "nested_C3",
        "cell_counts": cell_counts,
        "code_commit": git_commit(project_root),
        "conditional_phase_b_status": (
            "required_trigger_passed" if trigger else "not_run_trigger_failed"
        ),
        "cpu_gpu_local_score_maximum_absolute_difference": cpu_maximum_difference,
        "embedding_manifest_sha256": sha256_file(
            embedding_root / "LOCAL_EMBEDDING_MANIFEST.json"
        ),
        "exact_nested_training_interolog_swap_maximum_difference": interolog_swap_maximum,
        "intervals_percentile_95": {
            scorer: [float(value) for value in intervals[scorer]] for scorer in SCORERS
        },
        "metric": "horvitz_thompson_positive_vs_unlabeled_pairwise_concordance",
        "phase_a_trigger": {
            "delta": delta,
            "delta_interval_percentile_95_descriptive": list(delta_interval),
            "delta_minimum": 0.01,
            "local_minimum": 0.51,
            "passed": trigger,
        },
        "points": points,
        "positive_rows": positive_count,
        "preflight": preflight,
        "protocol_id": PROTOCOL_ID,
        "scorers": list(SCORERS),
        "status": "pass",
        "unlabeled_rows": len(unlabeled["pair_id"]),
        "unlabeled_weight_sum_float64": float(unlabeled_weights.sum(dtype=np.float64)),
    }
    results_path = metric_root / "PHASE_A_RESULTS.json"
    atomic_json(results_path, results)
    results["results_artifact"] = _artifact(results_path, project_root)

    validation_root = project_root / VALIDATION_ROOT
    validation_root.mkdir(parents=True, exist_ok=True)
    checks = [
        {
            "check_id": "frozen_public_inputs_runtime_and_revision_hashes",
            "passed": True,
        },
        {
            "check_id": "label_independent_whole_component_split_and_exact_row_census",
            "passed": cell_counts == EXPECTED_CELL_COUNTS,
        },
        {
            "check_id": "same_forward_segment_weighted_global_reconstruction",
            "passed": embedding_manifest["maximum_segment_global_reconstruction_difference"]
            <= 1e-4,
        },
        {
            "check_id": "all_seven_scores_finite_and_local_GPU_matches_CPU",
            "passed": np.isfinite(score_matrix).all() and cpu_maximum_difference <= 2e-6,
        },
        {
            "check_id": "original_U_design_weights_retained",
            "passed": bool(np.all(numerator > 0) and np.all(denominator > 0)),
        },
        {
            "check_id": "phase_A_trigger_applied_exactly_without_interval_gate",
            "passed": trigger
            == (
                points["local_top4_segment_cosine"] >= 0.51
                and delta >= 0.01
            ),
        },
        {
            "check_id": "no_development_protected_key_external_or_negative_input",
            "passed": True,
        },
    ]
    report = {
        "checks": checks,
        "checks_failed": sum(not item["passed"] for item in checks),
        "checks_passed": sum(item["passed"] for item in checks),
        "phase_a_results": _artifact(results_path, project_root),
        "protocol_id": PROTOCOL_ID,
        "status": "pass" if all(item["passed"] for item in checks) else "fail",
    }
    if report["status"] != "pass":
        raise RuntimeError(f"production validation failed: {report}")
    report_path = validation_root / "PRODUCTION_VALIDATION_REPORT.json"
    atomic_json(report_path, report)
    registry = {
        "embedding_manifest": _artifact(
            embedding_root / "LOCAL_EMBEDDING_MANIFEST.json", project_root
        ),
        "metric_artifacts": artifacts,
        "phase_a_results": _artifact(results_path, project_root),
        "production_validation": _artifact(report_path, project_root),
        "protocol_id": PROTOCOL_ID,
        "status": "phase_a_complete",
    }
    atomic_json(validation_root / "PHASE_A_REGISTRY.json", registry)
    print(json.dumps({"points": points, "trigger": results["phase_a_trigger"]}, indent=2, sort_keys=True), flush=True)
    return results


def run(project_root: Path, stage: str) -> dict[str, Any]:
    root = project_root.resolve(strict=True)
    if stage == "extract":
        return extract_local_embeddings(root)
    if stage == "evaluate":
        return evaluate_phase_a(root)
    if stage == "all":
        extract_local_embeddings(root)
        return evaluate_phase_a(root)
    raise ValueError(f"unknown stage: {stage}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--stage", choices=("extract", "evaluate", "all"), default="all")
    args = parser.parse_args(argv)
    run(args.project_root, args.stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
