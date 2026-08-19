#!/usr/bin/env python3
"""Standalone independent validator for the frozen DEC-0041 Phase A result.

This module deliberately imports no ipin_openppi production implementation.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pyarrow.parquet as pq
from scipy import sparse


PROTOCOL_ID = "public_training_local_representation_diagnostic_v1_revision_2"
SPLIT_SALT = "ipin-openppi-local-representation-diagnostic-v1"
BOOTSTRAP_SALT = "20260819-local-representation-diagnostic-v1"
BOOTSTRAP_REPLICATES = 200
SCORERS = (
    "deterministic_hash",
    "sequence_length_ratio",
    "within_pair_3mer_cosine",
    "exact_nested_training_interolog_3mer",
    "matched_global_pooled_esm_cosine",
    "local_max_segment_cosine",
    "local_top4_segment_cosine",
)
EXPECTED_COUNTS = {
    "P": {"C1": 11_051, "C2": 5_098, "C3": 650},
    "U": {"C1": 1_254_297, "C2": 659_253, "C3": 86_450},
}
ENDPOINTS = Path(
    "data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/"
    "eligible_reference_sequences/part-00000.parquet"
)
PARTITIONS = Path(
    "data/canonical/final_benchmark_component_split_v1/"
    "endpoint_partition_assignments/part-00000.parquet"
)
POSITIVE = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "positive_pairs/part-00000.parquet"
)
UNLABELED = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "unlabeled_pairs/part-00000.parquet"
)
EMBEDDING_ROOT = Path("artifacts/embeddings") / PROTOCOL_ID / "esm2_150m"
METRIC_ROOT = Path("artifacts/metrics") / PROTOCOL_ID / "nested_C3"
VALIDATION_ROOT = Path("artifacts/validation/model_execution") / PROTOCOL_ID
PARENT_POOLED = Path(
    "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/"
    "esm2_150m/pooled_embeddings.f32.npy"
)
FROZEN_HASHES = {
    ENDPOINTS: "4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e",
    PARTITIONS: "66db8cd59e7cb8cf06ff3ad785448dfc7d5fdd24643811946246d129b0bd8a67",
    POSITIVE: "4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499",
    UNLABELED: "d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7",
    Path("configs/public_training_local_representation_diagnostic_v1.yaml"):
        "63e0d4e194b5db88a51e245b2ddf767e4ce11142659ac8c24deb3afbb6be749d",
    Path("configs/public_training_local_representation_diagnostic_v1_revision_2.yaml"):
        "c22d8de53d6f53a0f8054767387dc8a28541c353e0dabaff8041005e1ffe12fc",
    Path("docs/protocols/PUBLIC_TRAINING_LOCAL_REPRESENTATION_DIAGNOSTIC_v1_revision_2.md"):
        "6940e7ba91f3a7835b1bd70b2d84594ac5af495013f01084a37897a2c2201a69",
    Path("containers/images/ipin-model-arm64_0.1.0.sif"):
        "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91",
    Path(
        "artifacts/cache/models/model_governance_and_baseline_training_protocol_v1/"
        "esm2_150m/model.safetensors"
    ): "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566",
    PARENT_POOLED: "4450a0a250e2ef84efcd48f627169b003097110e51b82530ba218f6a599ee7a0",
}
PROTECTED_HASHES = {
    Path(
        "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/"
        "protected_candidates.cms"
    ): "5ac1c30dbda85f6274f60febb2f4b01feda34c43bf87f4bbb690abe6c639ff63",
    Path(
        "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/"
        "protected_truth.cms"
    ): "69824547667861694aff88a0f6e43526d4f3aa27f930d4a4ff44c924d29aa1e9",
}
ALPHABET = "ACDEFGHIKLMNPQRSTVWYX"
KMER_INDEX = {
    a + b + c: (i * len(ALPHABET) + j) * len(ALPHABET) + k
    for i, a in enumerate(ALPHABET)
    for j, b in enumerate(ALPHABET)
    for k, c in enumerate(ALPHABET)
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_ok(project_root: Path, record: Mapping[str, Any]) -> bool:
    path = project_root / str(record["path"])
    return (
        path.is_file()
        and path.stat().st_size == int(record["bytes"])
        and sha256_file(path) == str(record["sha256"])
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists() or path.exists():
        raise RuntimeError(f"refusing to overwrite independent output: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def concordance(p: np.ndarray, u: np.ndarray, weights: np.ndarray, pm=None, um=None) -> float:
    positives = np.asarray(p, dtype=np.float64)
    scores = np.asarray(u, dtype=np.float64)
    design = np.asarray(weights, dtype=np.float64)
    p_multiplier = (
        np.ones(positives.size, dtype=np.float64)
        if pm is None
        else np.asarray(pm, dtype=np.float64)
    )
    u_multiplier = (
        np.ones(scores.size, dtype=np.float64)
        if um is None
        else np.asarray(um, dtype=np.float64)
    )
    weighted_u = design * u_multiplier
    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    cumulative = np.concatenate(
        ([0.0], np.cumsum(weighted_u[order], dtype=np.float64))
    )
    left = np.searchsorted(sorted_scores, positives, side="left")
    right = np.searchsorted(sorted_scores, positives, side="right")
    favorable = cumulative[left] + 0.5 * (cumulative[right] - cumulative[left])
    return float(np.dot(p_multiplier, favorable)) / (
        float(p_multiplier.sum()) * float(weighted_u.sum())
    )


def component_split(
    partition_data: Mapping[str, Sequence[Any]],
) -> tuple[dict[str, str], dict[str, str], frozenset[str]]:
    endpoint_component: dict[str, str] = {}
    endpoint_partition: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for endpoint, component, size, partition in zip(
        partition_data["reference_sequence_sha256"],
        partition_data["component_id"],
        partition_data["component_size"],
        partition_data["partition"],
        strict=True,
    ):
        endpoint_component[str(endpoint)] = str(component)
        endpoint_partition[str(endpoint)] = str(partition)
        if partition == "train":
            prior = sizes.setdefault(str(component), int(size))
            if prior != int(size):
                raise RuntimeError("independent component-size inconsistency")
    ordered = sorted(
        sizes,
        key=lambda component: (
            hashlib.sha256(f"{SPLIT_SALT}:{component}".encode()).hexdigest(),
            component,
        ),
    )
    heldout: set[str] = set()
    endpoint_count = 0
    for component in ordered:
        if endpoint_count >= 2_380:
            break
        heldout.add(component)
        endpoint_count += sizes[component]
    if len(sizes) != 5_427 or len(heldout) != 1_366 or endpoint_count != 2_380:
        raise RuntimeError("independent nested split census drift")
    return endpoint_component, endpoint_partition, frozenset(heldout)


def cell(left: str, right: str, heldout: frozenset[str]) -> str:
    a, b = str(left) in heldout, str(right) in heldout
    return "C3" if a and b else "C2" if a != b else "C1"


def select_rows(table: Mapping[str, Sequence[Any]], heldout: frozenset[str]) -> dict[str, list[Any]]:
    indexes = [
        index
        for index, (left, right) in enumerate(
            zip(
                table["endpoint_a_component_id"],
                table["endpoint_b_component_id"],
                strict=True,
            )
        )
        if cell(str(left), str(right), heldout) == "C3"
    ]
    return {key: [values[index] for index in indexes] for key, values in table.items()}


def kmer_matrix(sequences: Sequence[str]) -> sparse.csr_matrix:
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    for row, sequence in enumerate(sequences):
        mapped = "".join(residue if residue in ALPHABET else "X" for residue in sequence)
        counts = Counter(
            KMER_INDEX[mapped[index : index + 3]]
            for index in range(max(0, len(mapped) - 2))
        )
        norm = math.sqrt(sum(value * value for value in counts.values()))
        if norm:
            for column, value in sorted(counts.items()):
                rows.append(row)
                columns.append(column)
                values.append(value / norm)
    return sparse.csr_matrix(
        (np.asarray(values), (np.asarray(rows), np.asarray(columns))),
        shape=(len(sequences), len(ALPHABET) ** 3),
        dtype=np.float64,
    )


def local_scores_gpu(
    segments: np.ndarray,
    offsets: np.ndarray,
    globals_: np.ndarray,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    import torch

    counts = np.diff(offsets)
    norms = np.linalg.norm(segments.astype(np.float64), axis=1)
    unit = segments.astype(np.float64) / norms[:, None]
    padded = np.zeros((counts.size, 32, segments.shape[1]), dtype=np.float64)
    mask = np.zeros((counts.size, 32), dtype=bool)
    for endpoint, count in enumerate(counts):
        start, stop = int(offsets[endpoint]), int(offsets[endpoint + 1])
        padded[endpoint, :count] = unit[start:stop]
        mask[endpoint, :count] = True
    global_norm = np.linalg.norm(globals_.astype(np.float64), axis=1)
    global_unit = globals_.astype(np.float64) / global_norm[:, None]
    segment_tensor = torch.from_numpy(padded).cuda()
    mask_tensor = torch.from_numpy(mask).cuda()
    global_tensor = torch.from_numpy(global_unit).cuda()
    outputs = [np.empty(pair_a.size, dtype=np.float64) for _ in range(3)]
    with torch.inference_mode():
        for start in range(0, pair_a.size, 4_096):
            stop = min(start + 4_096, pair_a.size)
            a = torch.from_numpy(pair_a[start:stop]).cuda()
            b = torch.from_numpy(pair_b[start:stop]).cuda()
            similarity = torch.bmm(
                segment_tensor.index_select(0, a),
                segment_tensor.index_select(0, b).transpose(1, 2),
            )
            valid = mask_tensor.index_select(0, a).unsqueeze(2) & mask_tensor.index_select(
                0, b
            ).unsqueeze(1)
            flat = similarity.masked_fill(~valid, -torch.inf).flatten(1)
            outputs[1][start:stop] = flat.amax(dim=1).cpu().numpy()
            top = flat.topk(4, dim=1, largest=True, sorted=False).values
            top = torch.where(torch.isfinite(top), top, torch.zeros_like(top))
            outputs[2][start:stop] = (
                top.sum(dim=1) / valid.sum(dim=(1, 2)).clamp(max=4).to(torch.float64)
            ).cpu().numpy()
            outputs[0][start:stop] = (
                global_tensor.index_select(0, a) * global_tensor.index_select(0, b)
            ).sum(dim=1).cpu().numpy()
    del segment_tensor, mask_tensor, global_tensor
    torch.cuda.empty_cache()
    return outputs[0], outputs[1], outputs[2]


def interolog_gpu(
    kmer: sparse.csr_matrix,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
    edge_a: np.ndarray,
    edge_b: np.ndarray,
) -> np.ndarray:
    import torch

    exposed = np.unique(np.concatenate((edge_a, edge_b)))
    exposed_position = np.full(kmer.shape[0], -1, dtype=np.int64)
    exposed_position[exposed] = np.arange(exposed.size)
    u, v = exposed_position[edge_a], exposed_position[edge_b]
    query = np.unique(np.concatenate((pair_a, pair_b)))
    query_position = np.full(kmer.shape[0], -1, dtype=np.int64)
    query_position[query] = np.arange(query.size)
    similarity = (kmer[query] @ kmer[exposed].T).toarray().astype(np.float64)
    neighbor = np.zeros_like(similarity)
    adjacency: dict[int, list[int]] = defaultdict(list)
    for left, right in zip(u, v, strict=True):
        adjacency[int(left)].append(int(right))
        adjacency[int(right)].append(int(left))
    for endpoint in range(exposed.size):
        values = adjacency[endpoint]
        neighbor[:, endpoint] = similarity[:, values].max(axis=1)
    sim_tensor = torch.from_numpy(similarity).cuda()
    neighbor_tensor = torch.from_numpy(neighbor).cuda()
    qa, qb = query_position[pair_a], query_position[pair_b]
    output = np.empty(pair_a.size, dtype=np.float64)
    with torch.inference_mode():
        for start in range(0, pair_a.size, 2_048):
            stop = min(start + 2_048, pair_a.size)
            a = torch.from_numpy(qa[start:stop]).cuda()
            b = torch.from_numpy(qb[start:stop]).cuda()
            forward = torch.minimum(
                sim_tensor.index_select(0, a), neighbor_tensor.index_select(0, b)
            ).amax(dim=1)
            reverse = torch.minimum(
                sim_tensor.index_select(0, b), neighbor_tensor.index_select(0, a)
            ).amax(dim=1)
            output[start:stop] = torch.maximum(forward, reverse).cpu().numpy()
    del sim_tensor, neighbor_tensor
    torch.cuda.empty_cache()
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    root = args.project_root.resolve(strict=True)
    checks: list[dict[str, Any]] = []

    def check(check_id: str, passed: bool, detail: Any) -> None:
        checks.append({"check_id": check_id, "detail": detail, "passed": bool(passed)})

    frozen_ok = all(sha256_file(root / path) == digest for path, digest in FROZEN_HASHES.items())
    sealed_ok = all(
        sha256_file(root / path) == digest for path, digest in PROTECTED_HASHES.items()
    )
    check("frozen_public_inputs_runtime_model_and_protocol_hashes", frozen_ok, len(FROZEN_HASHES))
    check("protected_ciphertexts_unchanged_hash_only", sealed_ok, len(PROTECTED_HASHES))

    registry_path = root / VALIDATION_ROOT / "PHASE_A_REGISTRY.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    production = json.loads(
        (root / VALIDATION_ROOT / "PRODUCTION_VALIDATION_REPORT.json").read_text(
            encoding="utf-8"
        )
    )
    registry_records = [
        registry["embedding_manifest"],
        registry["phase_a_results"],
        registry["production_validation"],
        *registry["metric_artifacts"].values(),
    ]
    registry_ok = all(artifact_ok(root, record) for record in registry_records)
    check("production_registry_rehashes_all_registered_artifacts", registry_ok, len(registry_records))
    check(
        "production_validation_preexisted_and_passed",
        production["status"] == "pass" and production["checks_passed"] == 7,
        production,
    )

    embedding_manifest_path = root / EMBEDDING_ROOT / "LOCAL_EMBEDDING_MANIFEST.json"
    embedding_manifest = json.loads(embedding_manifest_path.read_text(encoding="utf-8"))
    embedding_ok = all(
        artifact_ok(root, record) for record in embedding_manifest["artifacts"].values()
    )
    check("embedding_manifest_rehashes_all_arrays", embedding_ok, len(embedding_manifest["artifacts"]))

    endpoint_table = pq.read_table(
        root / ENDPOINTS,
        columns=["reference_sequence_sha256", "sequence_length", "sequence"],
    ).to_pydict()
    all_records = sorted(
        zip(
            map(str, endpoint_table["reference_sequence_sha256"]),
            map(int, endpoint_table["sequence_length"]),
            map(str, endpoint_table["sequence"]),
            strict=True,
        ),
        key=lambda value: (value[1], value[0]),
    )
    partition_data = pq.read_table(
        root / PARTITIONS,
        columns=[
            "reference_sequence_sha256",
            "component_id",
            "component_size",
            "partition",
        ],
    ).to_pydict()
    endpoint_component, endpoint_partition, heldout = component_split(partition_data)
    records = [record for record in all_records if endpoint_partition[record[0]] == "train"]
    endpoint_index = {record[0]: index for index, record in enumerate(records)}
    endpoint_payload = json.loads((root / EMBEDDING_ROOT / "ENDPOINTS.json").read_text())
    endpoint_identity_ok = (
        endpoint_payload["endpoint_sha256s"] == [record[0] for record in records]
        and endpoint_payload["sequence_lengths"] == [record[1] for record in records]
    )
    check(
        "independent_nested_split_and_endpoint_order",
        len(heldout) == 1_366 and endpoint_identity_ok,
        {"heldout_components": len(heldout), "training_endpoints": len(records)},
    )

    segments = np.load(root / EMBEDDING_ROOT / "segment_embeddings.f32.npy", allow_pickle=False)
    lengths = np.load(root / EMBEDDING_ROOT / "segment_lengths.i32.npy", allow_pickle=False)
    offsets = np.load(root / EMBEDDING_ROOT / "endpoint_offsets.i64.npy", allow_pickle=False)
    globals_ = np.load(
        root / EMBEDDING_ROOT / "matched_global_embeddings.f32.npy", allow_pickle=False
    )
    reconstructed = np.empty_like(globals_)
    length_ok = True
    count_ok = True
    for endpoint, record in enumerate(records):
        start, stop = int(offsets[endpoint]), int(offsets[endpoint + 1])
        count = stop - start
        expected_count = min(32, max(1, math.ceil(record[1] / 128)))
        count_ok &= count == expected_count
        length_ok &= int(lengths[start:stop].sum(dtype=np.int64)) == record[1]
        reconstructed[endpoint] = np.average(
            segments[start:stop].astype(np.float64),
            axis=0,
            weights=lengths[start:stop],
        ).astype(np.float32)
    reconstruction_max = float(np.max(np.abs(reconstructed - globals_)))
    parent = np.load(root / PARENT_POOLED, allow_pickle=False, mmap_mode="r")
    all_index = {record[0]: index for index, record in enumerate(all_records)}
    parent_rows = np.fromiter((all_index[record[0]] for record in records), dtype=np.int64)
    parent_max = float(np.max(np.abs(globals_ - np.asarray(parent[parent_rows]))))
    array_ok = (
        segments.shape == (56_304, 640)
        and segments.dtype == np.float32
        and lengths.dtype == np.int32
        and offsets.dtype == np.int64
        and globals_.shape == (11_900, 640)
        and np.isfinite(segments).all()
        and np.isfinite(globals_).all()
        and length_ok
        and count_ok
        and reconstruction_max == 0.0
        and parent_max <= 1e-4
    )
    check(
        "independent_embedding_shapes_segments_lengths_and_global_reconstruction",
        array_ok,
        {
            "parent_maximum_absolute_difference": parent_max,
            "reconstruction_maximum_absolute_difference": reconstruction_max,
            "segments": int(segments.shape[0]),
        },
    )

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
    positive_all = pq.read_table(root / POSITIVE, columns=columns).to_pydict()
    unlabeled_all = pq.read_table(root / UNLABELED, columns=columns).to_pydict()
    observed_counts = {}
    for label, table in (("P", positive_all), ("U", unlabeled_all)):
        counts = Counter(
            cell(left, right, heldout)
            for left, right in zip(
                table["endpoint_a_component_id"],
                table["endpoint_b_component_id"],
                strict=True,
            )
        )
        observed_counts[label] = {name: counts[name] for name in ("C1", "C2", "C3")}
    p = select_rows(positive_all, heldout)
    u = select_rows(unlabeled_all, heldout)
    combined = {key: p[key] + u[key] for key in columns}
    row_ok = observed_counts == EXPECTED_COUNTS and len(p["pair_id"]) == 650 and len(u["pair_id"]) == 86_450
    check("independent_nested_cell_row_census", row_ok, observed_counts)

    pair_a = np.fromiter(
        (endpoint_index[str(value)] for value in combined["endpoint_a_sha256"]),
        dtype=np.int64,
    )
    pair_b = np.fromiter(
        (endpoint_index[str(value)] for value in combined["endpoint_b_sha256"]),
        dtype=np.int64,
    )
    recomputed = np.empty((pair_a.size, len(SCORERS)), dtype=np.float64)
    recomputed[:, 0] = np.fromiter(
        (
            int.from_bytes(
                hashlib.sha256(
                    f"ipin-openppi-pu-r-baseline-v1:20260803:baseline:{pair_id}".encode()
                ).digest(),
                "big",
            )
            / (2**256 - 1)
            for pair_id in combined["pair_id"]
        ),
        dtype=np.float64,
    )
    recomputed[:, 1] = np.fromiter(
        (
            -abs(math.log1p(records[left][1]) - math.log1p(records[right][1]))
            for left, right in zip(pair_a, pair_b, strict=True)
        ),
        dtype=np.float64,
    )
    kmer = kmer_matrix([record[2] for record in records])
    within = kmer[pair_a].multiply(kmer[pair_b]).sum(axis=1)
    recomputed[:, 2] = np.asarray(within).ravel()
    fit_indexes = [
        index
        for index, (left, right) in enumerate(
            zip(
                positive_all["endpoint_a_component_id"],
                positive_all["endpoint_b_component_id"],
                strict=True,
            )
        )
        if cell(str(left), str(right), heldout) == "C1"
    ]
    edge_a = np.fromiter(
        (
            endpoint_index[str(positive_all["endpoint_a_sha256"][index])]
            for index in fit_indexes
        ),
        dtype=np.int64,
    )
    edge_b = np.fromiter(
        (
            endpoint_index[str(positive_all["endpoint_b_sha256"][index])]
            for index in fit_indexes
        ),
        dtype=np.int64,
    )
    recomputed[:, 3] = interolog_gpu(kmer, pair_a, pair_b, edge_a, edge_b)
    recomputed[:, 4], recomputed[:, 5], recomputed[:, 6] = local_scores_gpu(
        segments, offsets, globals_, pair_a, pair_b
    )
    stored_scores = np.load(root / METRIC_ROOT / "phase_a_scores.f64.npy", allow_pickle=False)
    score_max = float(np.max(np.abs(recomputed - stored_scores)))
    score_ok = stored_scores.shape == (87_100, 7) and score_max <= 2e-12
    check("independently_recomputed_all_609700_scores", score_ok, score_max)

    weights = np.asarray(u["sampling_weight_numerator"], dtype=np.float64) / np.asarray(
        u["sampling_weight_denominator"], dtype=np.float64
    )
    points = {
        scorer: concordance(recomputed[:650, index], recomputed[650:, index], weights)
        for index, scorer in enumerate(SCORERS)
    }
    results = json.loads((root / METRIC_ROOT / "PHASE_A_RESULTS.json").read_text())
    point_max = max(abs(points[scorer] - float(results["points"][scorer])) for scorer in SCORERS)
    check("independent_HT_points_and_original_U_weights", point_max <= 2e-15, point_max)

    component_payload = json.loads(
        (root / METRIC_ROOT / "BOOTSTRAP_COMPONENTS.json").read_text()
    )
    components = tuple(component_payload["components"])
    component_index = {component: index for index, component in enumerate(components)}
    left_component = np.fromiter(
        (component_index[str(value)] for value in combined["endpoint_a_component_id"]),
        dtype=np.int64,
    )
    right_component = np.fromiter(
        (component_index[str(value)] for value in combined["endpoint_b_component_id"]),
        dtype=np.int64,
    )
    seed = int.from_bytes(
        hashlib.sha256(f"{BOOTSTRAP_SALT}:bootstrap:nested_C3".encode()).digest()[:8],
        "big",
    )
    generator = np.random.Generator(np.random.PCG64DXSM(seed))
    draws = generator.integers(
        0, len(components), size=(BOOTSTRAP_REPLICATES, len(components)), dtype=np.int64
    )
    expected_multiplicity = np.zeros_like(draws, dtype=np.int32)
    draw_rows = np.arange(BOOTSTRAP_REPLICATES)[:, None]
    np.add.at(expected_multiplicity, (draw_rows, draws), 1)
    stored_multiplicity = np.load(
        root / METRIC_ROOT / "component_multiplicities.i32.npy", allow_pickle=False
    )
    multiplicity_ok = np.array_equal(expected_multiplicity, stored_multiplicity)
    independently_bootstrapped = np.full((7, BOOTSTRAP_REPLICATES), np.nan, dtype=np.float64)
    for replicate in range(BOOTSTRAP_REPLICATES):
        counts = expected_multiplicity[replicate]
        pair_multiplier = np.where(
            left_component == right_component,
            counts[left_component],
            counts[left_component] * counts[right_component],
        ).astype(np.float64)
        for scorer_index in range(7):
            independently_bootstrapped[scorer_index, replicate] = concordance(
                recomputed[:650, scorer_index],
                recomputed[650:, scorer_index],
                weights,
                pair_multiplier[:650],
                pair_multiplier[650:],
            )
    stored_bootstrap = np.load(
        root / METRIC_ROOT / "bootstrap_metrics.f64.npy", allow_pickle=False
    )
    bootstrap_max = float(np.nanmax(np.abs(independently_bootstrapped - stored_bootstrap)))
    intervals = {
        scorer: np.percentile(independently_bootstrapped[index], (2.5, 97.5), method="linear")
        for index, scorer in enumerate(SCORERS)
    }
    interval_max = max(
        float(
            np.max(
                np.abs(
                    intervals[scorer]
                    - np.asarray(results["intervals_percentile_95"][scorer])
                )
            )
        )
        for scorer in SCORERS
    )
    bootstrap_ok = multiplicity_ok and bootstrap_max <= 2e-15 and interval_max <= 2e-15
    check(
        "independent_200_draw_paired_component_bootstrap_and_intervals",
        bootstrap_ok,
        {
            "bootstrap_maximum_absolute_difference": bootstrap_max,
            "interval_maximum_absolute_difference": interval_max,
            "multiplicities_exact": multiplicity_ok,
        },
    )

    delta = points["local_top4_segment_cosine"] - points["matched_global_pooled_esm_cosine"]
    trigger = points["local_top4_segment_cosine"] >= 0.51 and delta >= 0.01
    delta_distribution = (
        independently_bootstrapped[SCORERS.index("local_top4_segment_cosine")]
        - independently_bootstrapped[SCORERS.index("matched_global_pooled_esm_cosine")]
    )
    delta_interval = np.percentile(delta_distribution, (2.5, 97.5), method="linear")
    trigger_ok = (
        trigger is False
        and results["phase_a_trigger"]["passed"] is False
        and results["conditional_phase_b_status"] == "not_run_trigger_failed"
        and abs(delta - float(results["phase_a_trigger"]["delta"])) <= 2e-15
        and np.max(
            np.abs(
                delta_interval
                - np.asarray(
                    results["phase_a_trigger"][
                        "delta_interval_percentile_95_descriptive"
                    ]
                )
            )
        )
        <= 2e-15
    )
    check(
        "independent_trigger_and_conditional_phase_B_stop",
        trigger_ok,
        {"delta": delta, "delta_interval": delta_interval.tolist(), "trigger": trigger},
    )

    serialized_registry = json.dumps(registry, sort_keys=True)
    forbidden = (".private/", "development_release.cms", "protected_candidates.cms", "protected_truth.cms")
    information_flow_ok = not any(value in serialized_registry for value in forbidden)
    check(
        "public_only_registry_and_no_sensitive_information_flow",
        information_flow_ok,
        {"forbidden_fragments_found": []},
    )

    report = {
        "checks": checks,
        "checks_failed": sum(not item["passed"] for item in checks),
        "checks_passed": sum(item["passed"] for item in checks),
        "details": {
            "bootstrap_values_recomputed": int(independently_bootstrapped.size),
            "embedding_values_rehashed": int(segments.size + globals_.size),
            "phase_a_scores_recomputed": int(recomputed.size),
            "score_maximum_absolute_difference": score_max,
            "trigger": trigger,
        },
        "implementation_independence": {
            "imports_ipin_openppi_production_module": False,
            "implemented_after_production_evidence_commit": True,
            "production_evidence_commit": "220d0c4",
        },
        "protocol_id": PROTOCOL_ID,
        "status": "pass" if all(item["passed"] for item in checks) else "fail",
    }
    output = root / VALIDATION_ROOT / "INDEPENDENT_VALIDATION_REPORT.json"
    write_json(output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "pass":
        raise RuntimeError("independent local-diagnostic validation failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
