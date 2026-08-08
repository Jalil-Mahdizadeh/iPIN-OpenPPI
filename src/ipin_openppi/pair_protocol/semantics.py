"""Pure deterministic semantics for the pair-level PU-R protocol."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
import math
from typing import Mapping


Pair = tuple[str, str]
DEGREE_BINS = (
    "0",
    "1",
    "2",
    "3-4",
    "5-9",
    "10-19",
    "20-49",
    "50-99",
    "100+",
)
PRIMARY_CELLS = (
    "C1_development",
    "C1_test",
    "C2_development",
    "C2_test",
    "C3_development",
    "C3_test",
)


def unordered_pair(endpoint_a: str, endpoint_b: str) -> Pair:
    """Return the canonical pair and reject self/same-sequence pairs."""

    a, b = str(endpoint_a), str(endpoint_b)
    if not a or not b or a == b:
        raise ValueError("A protocol pair requires two distinct nonempty endpoints")
    return (a, b) if a < b else (b, a)


def pair_id(pair: Pair) -> str:
    """Stable full-digest identifier for one unordered frozen sequence pair."""

    a, b = unordered_pair(*pair)
    return "pair:" + hashlib.sha256(f"{a}|{b}".encode("utf-8")).hexdigest()


def c1_role(
    pair: Pair,
    *,
    salt: str,
    seed: str,
) -> str:
    """Assign a train/train pair to the frozen label-blind 70/15/15 role."""

    payload = f"{salt}:{seed}:primary:C1:{pair_id(pair)}"
    bucket = int.from_bytes(
        hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big"
    ) % 10_000
    if bucket < 7_000:
        return "train"
    if bucket < 8_500:
        return "development"
    return "test"


def degree_bin(degree: int) -> str:
    value = int(degree)
    if value < 0:
        raise ValueError("Degree cannot be negative")
    if value == 0:
        return "0"
    if value == 1:
        return "1"
    if value == 2:
        return "2"
    if value <= 4:
        return "3-4"
    if value <= 9:
        return "5-9"
    if value <= 19:
        return "10-19"
    if value <= 49:
        return "20-49"
    if value <= 99:
        return "50-99"
    return "100+"


def degree_pair_stratum(degree_a: int, degree_b: int) -> str:
    bins = sorted(
        (degree_bin(degree_a), degree_bin(degree_b)),
        key=DEGREE_BINS.index,
    )
    return f"{bins[0]}|{bins[1]}"


def choose_two(size: int) -> int:
    n = int(size)
    if n < 0:
        raise ValueError("Population size cannot be negative")
    return n * (n - 1) // 2


def pair_stratum_populations(endpoint_degree_counts: Mapping[str, int]) -> dict[str, int]:
    """Algebraic unordered-pair counts by fixed endpoint-degree bin pair."""

    unknown = set(endpoint_degree_counts) - set(DEGREE_BINS)
    if unknown:
        raise ValueError(f"Unknown degree bins: {sorted(unknown)}")
    populations: dict[str, int] = {}
    for left_index, left in enumerate(DEGREE_BINS):
        left_count = int(endpoint_degree_counts.get(left, 0))
        for right in DEGREE_BINS[left_index:]:
            right_count = int(endpoint_degree_counts.get(right, 0))
            value = (
                choose_two(left_count)
                if left == right
                else left_count * right_count
            )
            if value:
                populations[f"{left}|{right}"] = value
    return populations


def hamilton_sample_allocation(
    populations: Mapping[str, int], cap: int
) -> dict[str, int]:
    """Allocate a capped sample with one seat then exact Hamilton apportionment."""

    normalized = {str(k): int(v) for k, v in populations.items() if int(v) > 0}
    if any(int(v) < 0 for v in populations.values()):
        raise ValueError("Stratum populations cannot be negative")
    total = sum(normalized.values())
    sample_size = min(int(cap), total)
    if cap < 0:
        raise ValueError("Sample cap cannot be negative")
    if sample_size == 0:
        return {key: 0 for key in sorted(normalized)}
    if sample_size < len(normalized):
        raise ValueError("Sample cap cannot give every nonempty stratum positive inclusion")
    if sample_size == total:
        return dict(sorted(normalized.items()))

    allocations = {key: 1 for key in normalized}
    remaining = sample_size - len(normalized)
    capacities = {key: normalized[key] - 1 for key in normalized}
    capacity_total = sum(capacities.values())
    if remaining == 0:
        return dict(sorted(allocations.items()))

    quotas = {
        key: Fraction(remaining * capacities[key], capacity_total)
        for key in normalized
    }
    for key, quota in quotas.items():
        allocations[key] += quota.numerator // quota.denominator
    seats_left = sample_size - sum(allocations.values())
    order = sorted(
        normalized,
        key=lambda key: (
            -(quotas[key] - math.floor(quotas[key])),
            key,
        ),
    )
    for key in order[:seats_left]:
        allocations[key] += 1
    if sum(allocations.values()) != sample_size:
        raise RuntimeError("Hamilton allocation did not conserve the sample size")
    if any(allocations[key] <= 0 or allocations[key] > normalized[key] for key in normalized):
        raise RuntimeError("Hamilton allocation violates a stratum population")
    return dict(sorted(allocations.items()))


def sampling_design(
    populations: Mapping[str, int], cap: int
) -> dict[str, object]:
    allocations = hamilton_sample_allocation(populations, cap)
    rows: list[dict[str, object]] = []
    for stratum in sorted(allocations):
        population = int(populations[stratum])
        sample = int(allocations[stratum])
        probability = Fraction(sample, population)
        weight = 1 / probability
        rows.append(
            {
                "stratum_id": stratum,
                "unlabeled_population": population,
                "sample_size": sample,
                "inclusion_probability_numerator": probability.numerator,
                "inclusion_probability_denominator": probability.denominator,
                "sampling_weight_numerator": weight.numerator,
                "sampling_weight_denominator": weight.denominator,
            }
        )
    return {
        "unlabeled_candidate_count": sum(int(value) for value in populations.values()),
        "sample_cap": int(cap),
        "sample_size": sum(allocations.values()),
        "nonempty_strata": len(rows),
        "strata": rows,
    }


def nearest_rank(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(map(int, values))
    return ordered[max(0, math.ceil(float(fraction) * len(ordered)) - 1)]


def degree_histogram(values: list[int]) -> dict[str, int]:
    counts = Counter(degree_bin(value) for value in values)
    return {label: int(counts[label]) for label in DEGREE_BINS}


__all__ = [
    "DEGREE_BINS",
    "PRIMARY_CELLS",
    "Pair",
    "c1_role",
    "choose_two",
    "degree_bin",
    "degree_histogram",
    "degree_pair_stratum",
    "hamilton_sample_allocation",
    "nearest_rank",
    "pair_id",
    "pair_stratum_populations",
    "sampling_design",
    "unordered_pair",
]
