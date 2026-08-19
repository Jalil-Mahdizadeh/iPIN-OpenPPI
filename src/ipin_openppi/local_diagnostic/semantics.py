"""Pure frozen semantics for the DEC-0041 representation-bottleneck test."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Mapping, Sequence

import numpy as np


SPLIT_SALT = "ipin-openppi-local-representation-diagnostic-v1"
TARGET_HELDOUT_ENDPOINTS = 2_380
TARGET_RESIDUES_PER_SEGMENT = 128
MAX_SEGMENTS = 32


def segment_boundaries(
    sequence_length: int,
    *,
    target_residues: int = TARGET_RESIDUES_PER_SEGMENT,
    maximum_segments: int = MAX_SEGMENTS,
) -> tuple[tuple[int, int], ...]:
    """Return exhaustive contiguous approximately equal bins."""

    length = int(sequence_length)
    if length <= 0 or target_residues <= 0 or maximum_segments <= 0:
        raise ValueError("positive sequence length and segment limits required")
    count = min(maximum_segments, max(1, math.ceil(length / target_residues)))
    boundaries = tuple(
        ((index * length) // count, ((index + 1) * length) // count)
        for index in range(count)
    )
    if (
        boundaries[0][0] != 0
        or boundaries[-1][1] != length
        or any(start >= stop for start, stop in boundaries)
        or any(left[1] != right[0] for left, right in zip(boundaries, boundaries[1:]))
    ):
        raise RuntimeError("segment boundaries are not a contiguous exhaustive partition")
    return boundaries


def select_heldout_components(
    component_sizes: Mapping[str, int],
    *,
    salt: str = SPLIT_SALT,
    target_endpoints: int = TARGET_HELDOUT_ENDPOINTS,
) -> frozenset[str]:
    """Select whole components by the frozen label-independent bottom-hash rule."""

    if not component_sizes or not salt or target_endpoints <= 0:
        raise ValueError("component sizes, salt, and target must be nonempty")
    normalized = {str(component): int(size) for component, size in component_sizes.items()}
    if any(not component or size <= 0 for component, size in normalized.items()):
        raise ValueError("component IDs and sizes must be positive")
    if target_endpoints > sum(normalized.values()):
        raise ValueError("heldout target exceeds endpoint population")
    ordered = sorted(
        normalized,
        key=lambda component: (
            hashlib.sha256(f"{salt}:{component}".encode("utf-8")).hexdigest(),
            component,
        ),
    )
    heldout: set[str] = set()
    endpoint_count = 0
    for component in ordered:
        if endpoint_count >= target_endpoints:
            break
        heldout.add(component)
        endpoint_count += normalized[component]
    if endpoint_count < target_endpoints:
        raise RuntimeError("component selection failed to reach target")
    return frozenset(heldout)


def nested_cell(component_a: str, component_b: str, heldout: frozenset[str]) -> str:
    left = str(component_a) in heldout
    right = str(component_b) in heldout
    if left and right:
        return "C3"
    if left != right:
        return "C2"
    return "C1"


def _finite_matrix(name: str, values: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or not array.size or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite nonempty matrix")
    norms = np.linalg.norm(array, axis=1)
    if np.any(norms == 0):
        raise ValueError(f"{name} contains a zero-norm segment")
    return array


@dataclass(frozen=True)
class LocalPairScores:
    matched_global_pooled_esm_cosine: float
    local_max_segment_cosine: float
    local_top4_segment_cosine: float


def local_pair_scores(
    segments_a: Sequence[Sequence[float]] | np.ndarray,
    lengths_a: Sequence[int] | np.ndarray,
    segments_b: Sequence[Sequence[float]] | np.ndarray,
    lengths_b: Sequence[int] | np.ndarray,
) -> LocalPairScores:
    """Calculate the three exact matched global/local cosine summaries."""

    left = _finite_matrix("segments_a", segments_a)
    right = _finite_matrix("segments_b", segments_b)
    if left.shape[1] != right.shape[1]:
        raise ValueError("partner segment dimensions differ")
    left_lengths = np.asarray(lengths_a, dtype=np.int64)
    right_lengths = np.asarray(lengths_b, dtype=np.int64)
    if (
        left_lengths.shape != (left.shape[0],)
        or right_lengths.shape != (right.shape[0],)
        or np.any(left_lengths <= 0)
        or np.any(right_lengths <= 0)
    ):
        raise ValueError("positive segment lengths must align with segment matrices")

    left_unit = left / np.linalg.norm(left, axis=1, keepdims=True)
    right_unit = right / np.linalg.norm(right, axis=1, keepdims=True)
    similarities = left_unit @ right_unit.T
    flat = similarities.ravel()
    top_count = min(4, flat.size)
    top = np.partition(flat, flat.size - top_count)[-top_count:]

    left_global = np.average(left, axis=0, weights=left_lengths)
    right_global = np.average(right, axis=0, weights=right_lengths)
    global_denominator = np.linalg.norm(left_global) * np.linalg.norm(right_global)
    if global_denominator == 0:
        raise ValueError("matched global mean has zero norm")
    global_cosine = float(np.dot(left_global, right_global) / global_denominator)
    return LocalPairScores(
        matched_global_pooled_esm_cosine=global_cosine,
        local_max_segment_cosine=float(flat.max()),
        local_top4_segment_cosine=float(top.mean()),
    )


def phase_a_trigger(
    local_concordance: float,
    matched_global_concordance: float,
    *,
    local_minimum: float = 0.51,
    delta_minimum: float = 0.01,
) -> tuple[bool, float]:
    local = float(local_concordance)
    global_value = float(matched_global_concordance)
    if not (math.isfinite(local) and math.isfinite(global_value)):
        raise ValueError("trigger inputs must be finite")
    delta = local - global_value
    return local >= local_minimum and delta >= delta_minimum, delta
