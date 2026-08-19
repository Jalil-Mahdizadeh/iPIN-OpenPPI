"""Mandatory deterministic shortcut and exact sequence/interolog controls."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import math
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy import sparse

from .constants import HASH_BASELINE_SALT, HASH_BASELINE_SEED


KMER_ALPHABET = "ACDEFGHIKLMNPQRSTVWYX"
KMER_INDEX = {
    a + b + c: (i * len(KMER_ALPHABET) + j) * len(KMER_ALPHABET) + k
    for i, a in enumerate(KMER_ALPHABET)
    for j, b in enumerate(KMER_ALPHABET)
    for k, c in enumerate(KMER_ALPHABET)
}


def deterministic_hash_score(pair_id: str) -> float:
    payload = f"{HASH_BASELINE_SALT}:{HASH_BASELINE_SEED}:baseline:{pair_id}"
    integer = int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest(), "big")
    return integer / (2**256 - 1)


def degree_sum_score(degree_a: int, degree_b: int) -> float:
    return math.log1p(degree_a) + math.log1p(degree_b)


def preferential_attachment_score(degree_a: int, degree_b: int) -> float:
    return math.log1p(degree_a * degree_b)


def component_mass_product_score(mass_a: int, mass_b: int) -> float:
    return math.log1p(mass_a * mass_b)


def common_neighbors_score(neighbors_a: set[str], neighbors_b: set[str]) -> float:
    return math.log1p(len(neighbors_a.intersection(neighbors_b)))


def length_sum_score(length_a: int, length_b: int) -> float:
    return math.log1p(length_a) + math.log1p(length_b)


def length_ratio_score(length_a: int, length_b: int) -> float:
    return -abs(math.log1p(length_a) - math.log1p(length_b))


def map_kmer_residue(residue: str) -> str:
    return residue if residue in KMER_ALPHABET else "X"


def kmer3_counts(sequence: str) -> Counter[int]:
    mapped = "".join(map_kmer_residue(residue) for residue in sequence)
    return Counter(KMER_INDEX[mapped[index : index + 3]] for index in range(max(0, len(mapped) - 2)))


def normalized_kmer3_vector(sequence: str) -> dict[int, float]:
    counts = kmer3_counts(sequence)
    norm = math.sqrt(sum(value * value for value in counts.values()))
    if norm == 0:
        return {}
    return {index: value / norm for index, value in counts.items()}


def sparse_cosine(a: Mapping[int, float], b: Mapping[int, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(value * b.get(index, 0.0) for index, value in a.items())


def kmer3_csr(sequences: Sequence[str]) -> sparse.csr_matrix:
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    for row, sequence in enumerate(sequences):
        normalized = normalized_kmer3_vector(sequence)
        for column, value in sorted(normalized.items()):
            rows.append(row)
            columns.append(column)
            values.append(value)
    return sparse.csr_matrix(
        (np.asarray(values), (np.asarray(rows), np.asarray(columns))),
        shape=(len(sequences), len(KMER_ALPHABET) ** 3),
        dtype=np.float64,
    )


def exact_interolog_score(
    similarity_a: np.ndarray,
    similarity_b: np.ndarray,
    positive_endpoint_u: np.ndarray,
    positive_endpoint_v: np.ndarray,
) -> float:
    forward = np.minimum(similarity_a[positive_endpoint_u], similarity_b[positive_endpoint_v])
    reverse = np.minimum(similarity_a[positive_endpoint_v], similarity_b[positive_endpoint_u])
    return float(np.maximum(forward, reverse).max(initial=0.0))


def build_training_graph(
    positive_pairs: Iterable[tuple[str, str]], component_by_endpoint: Mapping[str, str]
) -> tuple[dict[str, int], dict[str, set[str]], dict[str, int]]:
    degree: Counter[str] = Counter()
    neighbors: dict[str, set[str]] = defaultdict(set)
    for endpoint_a, endpoint_b in positive_pairs:
        if endpoint_a == endpoint_b:
            raise RuntimeError("self-pair prohibited")
        degree[endpoint_a] += 1
        degree[endpoint_b] += 1
        neighbors[endpoint_a].add(endpoint_b)
        neighbors[endpoint_b].add(endpoint_a)
    component_mass: Counter[str] = Counter()
    for endpoint, value in degree.items():
        component_mass[component_by_endpoint[endpoint]] += value
    return dict(degree), dict(neighbors), dict(component_mass)
