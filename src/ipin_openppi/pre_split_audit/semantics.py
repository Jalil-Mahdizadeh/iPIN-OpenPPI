"""Pure deterministic semantics for the aggregate pre-split audit."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from typing import Iterable, Mapping, Sequence


Pair = tuple[str, str]


class DisjointSet:
    """Small deterministic union-find used only for in-memory stress graphs."""

    def __init__(self, nodes: Iterable[str]) -> None:
        ordered = sorted(set(nodes))
        self.parent = {node: node for node in ordered}
        self.rank = {node: 0 for node in ordered}

    def find(self, node: str) -> str:
        if node not in self.parent:
            raise KeyError(f"Unknown sequence endpoint: {node}")
        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[node] != node:
            parent = self.parent[node]
            self.parent[node] = root
            node = parent
        return root

    def union(self, endpoint_a: str, endpoint_b: str) -> None:
        root_a = self.find(endpoint_a)
        root_b = self.find(endpoint_b)
        if root_a == root_b:
            return
        rank_a = self.rank[root_a]
        rank_b = self.rank[root_b]
        if rank_a < rank_b or (rank_a == rank_b and root_b < root_a):
            root_a, root_b = root_b, root_a
            rank_a, rank_b = rank_b, rank_a
        self.parent[root_b] = root_a
        if rank_a == rank_b:
            self.rank[root_a] += 1


def deterministic_components(
    sequence_hashes: Iterable[str], edges: Iterable[Pair]
) -> tuple[dict[str, str], dict[str, int]]:
    """Return lexicographic component representatives and their sizes."""

    nodes = sorted(set(sequence_hashes))
    dsu = DisjointSet(nodes)
    for endpoint_a, endpoint_b in sorted(
        {tuple(sorted((str(a), str(b)))) for a, b in edges}
    ):
        if endpoint_a == endpoint_b:
            continue
        dsu.union(endpoint_a, endpoint_b)
    grouped: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        grouped[dsu.find(node)].append(node)
    memberships: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for members in grouped.values():
        representative = min(members)
        sizes[representative] = len(members)
        for member in members:
            memberships[member] = representative
    return memberships, sizes


def nearest_rank(values: Sequence[int], fraction: float) -> int:
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("fraction must be between zero and one")
    if not values:
        return 0
    ordered = sorted(map(int, values))
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def numeric_distribution(values: Sequence[int]) -> dict[str, int]:
    ordered = list(map(int, values))
    if not ordered:
        return {key: 0 for key in ("minimum", "q05", "q50", "q95", "maximum")}
    return {
        "minimum": min(ordered),
        "q05": nearest_rank(ordered, 0.05),
        "q50": nearest_rank(ordered, 0.50),
        "q95": nearest_rank(ordered, 0.95),
        "maximum": max(ordered),
    }


def degree_gini(values: Sequence[int]) -> float:
    ordered = sorted(map(int, values))
    if not ordered or sum(ordered) == 0:
        return 0.0
    weighted = sum(index * value for index, value in enumerate(ordered, start=1))
    count = len(ordered)
    return (2.0 * weighted) / (count * sum(ordered)) - (count + 1.0) / count


def top_fraction_share(values: Sequence[int], fraction: float) -> float:
    if not 0.0 < fraction <= 1.0:
        raise ValueError("fraction must be in (0, 1]")
    ordered = sorted(map(int, values), reverse=True)
    total = sum(ordered)
    if not ordered or total == 0:
        return 0.0
    count = max(1, math.ceil(fraction * len(ordered)))
    return sum(ordered[:count]) / total


def degree_histogram(values: Sequence[int]) -> str:
    counts = Counter(
        "0"
        if value == 0
        else "1"
        if value == 1
        else "2"
        if value == 2
        else "3-4"
        if value <= 4
        else "5-9"
        if value <= 9
        else "10-19"
        if value <= 19
        else "20-49"
        if value <= 49
        else "50-99"
        if value <= 99
        else "100+"
        for value in map(int, values)
    )
    labels = ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")
    return json.dumps({label: int(counts[label]) for label in labels}, sort_keys=True)


def degree_summary(values: Sequence[int]) -> dict[str, int | float | str]:
    observed = list(map(int, values))
    return {
        "population_entity_count": len(observed),
        "positive_exposed_entity_count": sum(value > 0 for value in observed),
        "degree_sum": sum(observed),
        "degree_q50": nearest_rank(observed, 0.50),
        "degree_q90": nearest_rank(observed, 0.90),
        "degree_q95": nearest_rank(observed, 0.95),
        "degree_q99": nearest_rank(observed, 0.99),
        "maximum_degree": max(observed, default=0),
        "top_1_percent_degree_share": top_fraction_share(observed, 0.01),
        "top_5_percent_degree_share": top_fraction_share(observed, 0.05),
        "top_10_percent_degree_share": top_fraction_share(observed, 0.10),
        "degree_gini": degree_gini(observed),
        "degree_histogram_json": degree_histogram(observed),
    }


def source_membership_strata(
    hi_pairs: set[Pair], huri_pairs: set[Pair]
) -> dict[str, set[Pair]]:
    return {
        "HI-II-14_only": set(hi_pairs) - set(huri_pairs),
        "HuRI_only": set(huri_pairs) - set(hi_pairs),
        "both": set(hi_pairs) & set(huri_pairs),
    }


def allocation_order(
    component_ids: Sequence[str], *, seed: str, trial_index: int
) -> list[str]:
    """Generate a deterministic family of hash-ordered cyclic permutations."""

    base = sorted(
        component_ids,
        key=lambda component: hashlib.sha256(
            f"{seed}:component:{component}".encode("utf-8")
        ).digest(),
    )
    if not base:
        return []
    digest = hashlib.sha256(f"{seed}:trial:{trial_index}".encode("utf-8")).digest()
    offset = int.from_bytes(digest[:8], "big") % len(base)
    stride = max(1, int.from_bytes(digest[8:16], "big") % len(base))
    while math.gcd(stride, len(base)) != 1:
        stride = (stride + 1) % len(base) or 1
    return [base[(offset + index * stride) % len(base)] for index in range(len(base))]


def allocate_components(
    component_sizes: Mapping[str, int],
    *,
    seed: str,
    trial_index: int,
    target_fractions: Mapping[str, float],
) -> tuple[dict[str, str], dict[str, int]]:
    """Create one ephemeral size-balanced allocation; callers must not persist it."""

    labels = tuple(target_fractions)
    if set(labels) != {"train", "development", "test"}:
        raise ValueError("Expected train/development/test target fractions")
    if abs(sum(float(target_fractions[label]) for label in labels) - 1.0) > 1e-12:
        raise ValueError("Target fractions must sum to one")
    total = sum(int(size) for size in component_sizes.values())
    targets = {label: total * float(target_fractions[label]) for label in labels}
    counts = {label: 0 for label in labels}
    assignments: dict[str, str] = {}
    for component in allocation_order(
        list(component_sizes), seed=seed, trial_index=trial_index
    ):
        relative_deficit = {
            label: (targets[label] - counts[label]) / max(targets[label], 1.0)
            for label in labels
        }
        chosen = min(
            labels,
            key=lambda label: (-relative_deficit[label], labels.index(label)),
        )
        assignments[component] = chosen
        counts[chosen] += int(component_sizes[component])
    return assignments, counts


def opportunity_counts(
    pairs: set[Pair],
    memberships: Mapping[str, str],
    component_partitions: Mapping[str, str],
    pair_sources: Mapping[Pair, frozenset[str]],
) -> dict[str, object]:
    """Evaluate one allocation without emitting pair identities or labels."""

    train_degree: Counter[str] = Counter()
    for endpoint_a, endpoint_b in pairs:
        if (
            component_partitions[memberships[endpoint_a]] == "train"
            and component_partitions[memberships[endpoint_b]] == "train"
        ):
            train_degree[endpoint_a] += 1
            train_degree[endpoint_b] += 1

    counts = Counter()
    components = {axis: set() for axis in ("c1", "c2", "c3")}
    c3_sources = Counter()
    for endpoint_a, endpoint_b in pairs:
        component_a = memberships[endpoint_a]
        component_b = memberships[endpoint_b]
        partition_a = component_partitions[component_a]
        partition_b = component_partitions[component_b]
        axis: str | None = None
        if (
            partition_a == partition_b == "train"
            and train_degree[endpoint_a] >= 2
            and train_degree[endpoint_b] >= 2
        ):
            axis = "c1"
        elif {partition_a, partition_b} == {"train", "test"}:
            train_endpoint = endpoint_a if partition_a == "train" else endpoint_b
            if train_degree[train_endpoint] >= 1:
                axis = "c2"
        elif partition_a == partition_b == "test":
            axis = "c3"
        if axis is None:
            continue
        counts[axis] += 1
        components[axis].update((component_a, component_b))
        if axis == "c3":
            for source in pair_sources[(endpoint_a, endpoint_b)]:
                c3_sources[source] += 1
    return {
        "c1_pairs": int(counts["c1"]),
        "c2_pairs": int(counts["c2"]),
        "c3_pairs": int(counts["c3"]),
        "c1_components": len(components["c1"]),
        "c2_components": len(components["c2"]),
        "c3_components": len(components["c3"]),
        "c3_hi_ii_14_pairs": int(c3_sources["HI-II-14"]),
        "c3_huri_pairs": int(c3_sources["HuRI"]),
    }
