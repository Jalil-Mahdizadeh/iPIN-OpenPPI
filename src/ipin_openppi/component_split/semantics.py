"""Pure deterministic semantics for the frozen component split."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


Pair = tuple[str, str]
PARTITIONS = ("train", "development", "test")
PARTITION_CODES = {name: index for index, name in enumerate(PARTITIONS)}
POOL_KEYS = (
    "C1:training_pool",
    "C2:development",
    "C2:test",
    "C3:development",
    "C3:test",
)
SOURCES = ("ALL", "HI-II-14", "HuRI")


class DisjointSet:
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
    nodes = sorted(set(sequence_hashes))
    dsu = DisjointSet(nodes)
    for endpoint_a, endpoint_b in sorted(
        {tuple(sorted((str(a), str(b)))) for a, b in edges}
    ):
        if endpoint_a != endpoint_b:
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


def component_id(
    split_id: str, definition: str, threshold: int, representative: str, size: int
) -> str:
    payload = f"{split_id}:{definition}:{threshold}:{representative}:{size}"
    return "component:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def nearest_rank(values: Sequence[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(map(int, values))
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def degree_histogram(values: Sequence[int]) -> str:
    counts = Counter(
        "0" if value == 0 else "1" if value == 1 else "2" if value == 2
        else "3-4" if value <= 4 else "5-9" if value <= 9
        else "10-19" if value <= 19 else "20-49" if value <= 49
        else "50-99" if value <= 99 else "100+"
        for value in map(int, values)
    )
    labels = ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")
    return json.dumps({label: int(counts[label]) for label in labels}, sort_keys=True)


def quantized_ratio(numerator: int, denominator: int, scale: int) -> int:
    """Nearest integer, half up, for a nonnegative rational."""

    if numerator < 0 or denominator <= 0 or scale <= 0:
        raise ValueError("quantized_ratio requires nonnegative numerator and positive denominator/scale")
    return (2 * numerator * scale + denominator) // (2 * denominator)


def base_component_order(
    component_representatives: Sequence[str], *, salt: str, definition: str
) -> list[str]:
    return sorted(
        component_representatives,
        key=lambda component: (
            hashlib.sha256(
                f"{salt}:{definition}:component:{component}".encode("utf-8")
            ).digest(),
            component,
        ),
    )


def candidate_order_indices(
    component_count: int,
    *,
    salt: str,
    seed: str,
    definition: str,
    candidate_index: int,
) -> Iterable[int]:
    if component_count <= 0:
        return
    digest = hashlib.sha256(
        f"{salt}:{seed}:{definition}:candidate:{candidate_index}".encode("utf-8")
    ).digest()
    offset = int.from_bytes(digest[:8], "big") % component_count
    stride = int.from_bytes(digest[8:16], "big") % component_count or 1
    while math.gcd(stride, component_count) != 1:
        stride = (stride + 1) % component_count or 1
    for index in range(component_count):
        yield (offset + index * stride) % component_count


def allocate_candidate(
    *,
    component_representatives: Sequence[str],
    component_sizes: Mapping[str, int],
    definition: str,
    candidate_index: int,
    salt: str,
    seed: str,
    target_weights: Sequence[int] = (70, 15, 15),
) -> tuple[np.ndarray, np.ndarray]:
    """Allocate a candidate with exact rational largest-relative-deficit ties."""

    components = list(component_representatives)
    if len(target_weights) != 3 or sum(target_weights) != 100:
        raise ValueError("Expected integer 70/15/15 target weights")
    index_by_component = {component: index for index, component in enumerate(components)}
    base = base_component_order(components, salt=salt, definition=definition)
    base_indices = [index_by_component[component] for component in base]
    assignments = np.empty(len(components), dtype=np.int8)
    counts = np.zeros(3, dtype=np.int64)
    for base_position in candidate_order_indices(
        len(components),
        salt=salt,
        seed=seed,
        definition=definition,
        candidate_index=candidate_index,
    ):
        component_index = base_indices[base_position]
        chosen = 0
        for partition_index in (1, 2):
            if (
                int(counts[partition_index]) * int(target_weights[chosen])
                < int(counts[chosen]) * int(target_weights[partition_index])
            ):
                chosen = partition_index
        assignments[component_index] = chosen
        counts[chosen] += int(component_sizes[components[component_index]])
    return assignments, counts


@dataclass(frozen=True)
class PreparedAllocation:
    nodes: tuple[str, ...]
    component_representatives: tuple[str, ...]
    component_sizes: Mapping[str, int]
    node_components: np.ndarray
    pair_endpoint_a: np.ndarray
    pair_endpoint_b: np.ndarray
    pair_component_a: np.ndarray
    pair_component_b: np.ndarray
    hi_mask: np.ndarray
    huri_mask: np.ndarray
    all_degrees: np.ndarray
    global_hub_indices: Mapping[float, np.ndarray]


def prepare_allocation(
    *,
    nodes: Sequence[str],
    memberships: Mapping[str, str],
    component_sizes: Mapping[str, int],
    positive_pairs: set[Pair],
    pair_sources: Mapping[Pair, frozenset[str]],
    hub_fractions: Sequence[float],
) -> PreparedAllocation:
    ordered_nodes = tuple(sorted(nodes))
    components = tuple(sorted(component_sizes))
    component_index = {component: index for index, component in enumerate(components)}
    node_index = {node: index for index, node in enumerate(ordered_nodes)}
    node_components = np.array(
        [component_index[memberships[node]] for node in ordered_nodes], dtype=np.int64
    )
    ordered_pairs = sorted(positive_pairs)
    endpoint_a = np.array([node_index[pair[0]] for pair in ordered_pairs], dtype=np.int64)
    endpoint_b = np.array([node_index[pair[1]] for pair in ordered_pairs], dtype=np.int64)
    all_degrees = np.bincount(
        np.concatenate((endpoint_a, endpoint_b)), minlength=len(ordered_nodes)
    ).astype(np.int64)
    ranked = np.array(
        sorted(range(len(ordered_nodes)), key=lambda index: (-int(all_degrees[index]), ordered_nodes[index])),
        dtype=np.int64,
    )
    hubs = {
        float(fraction): ranked[: max(1, math.ceil(float(fraction) * len(ordered_nodes)))]
        for fraction in hub_fractions
    }
    return PreparedAllocation(
        nodes=ordered_nodes,
        component_representatives=components,
        component_sizes=dict(component_sizes),
        node_components=node_components,
        pair_endpoint_a=endpoint_a,
        pair_endpoint_b=endpoint_b,
        pair_component_a=node_components[endpoint_a],
        pair_component_b=node_components[endpoint_b],
        hi_mask=np.array(["HI-II-14" in pair_sources[pair] for pair in ordered_pairs], dtype=bool),
        huri_mask=np.array(["HuRI" in pair_sources[pair] for pair in ordered_pairs], dtype=bool),
        all_degrees=all_degrees,
        global_hub_indices=hubs,
    )


def opportunity_masks(
    prepared: PreparedAllocation, component_partitions: np.ndarray
) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    node_partitions = component_partitions[prepared.node_components]
    part_a = node_partitions[prepared.pair_endpoint_a]
    part_b = node_partitions[prepared.pair_endpoint_b]
    train_pairs = (part_a == 0) & (part_b == 0)
    train_degree = np.bincount(
        np.concatenate(
            (
                prepared.pair_endpoint_a[train_pairs],
                prepared.pair_endpoint_b[train_pairs],
            )
        ),
        minlength=len(prepared.nodes),
    )
    c1 = train_pairs & (train_degree[prepared.pair_endpoint_a] >= 2) & (
        train_degree[prepared.pair_endpoint_b] >= 2
    )
    masks: dict[str, np.ndarray] = {"C1:training_pool": c1}
    for partition_name in ("development", "test"):
        code = PARTITION_CODES[partition_name]
        a_train = (part_a == 0) & (part_b == code) & (
            train_degree[prepared.pair_endpoint_a] >= 1
        )
        b_train = (part_b == 0) & (part_a == code) & (
            train_degree[prepared.pair_endpoint_b] >= 1
        )
        masks[f"C2:{partition_name}"] = a_train | b_train
        masks[f"C3:{partition_name}"] = (part_a == code) & (part_b == code)
    return masks, node_partitions, train_degree


def _pool_counts(
    prepared: PreparedAllocation, masks: Mapping[str, np.ndarray]
) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    source_masks = {
        "ALL": np.ones(len(prepared.pair_endpoint_a), dtype=bool),
        "HI-II-14": prepared.hi_mask,
        "HuRI": prepared.huri_mask,
    }
    for pool, mask in masks.items():
        participating_components = int(
            np.unique(
                np.concatenate(
                    (
                        prepared.pair_component_a[mask],
                        prepared.pair_component_b[mask],
                    )
                )
            ).size
        ) if np.any(mask) else 0
        output[pool] = {
            "pairs": int(np.count_nonzero(mask)),
            "components": participating_components,
            **{
                f"{source}_pairs": int(np.count_nonzero(mask & source_mask))
                for source, source_mask in source_masks.items()
            },
        }
    return output


def evaluate_candidate(
    *,
    prepared: PreparedAllocation,
    component_partitions: np.ndarray,
    endpoint_counts: np.ndarray,
    config: Mapping[str, Any],
    candidate_index: int,
) -> dict[str, Any]:
    criteria = config["acceptance_criteria"]
    allocation = config["allocation"]
    scale = int(allocation["score_quantization_scale"])
    target_weights = (70, 15, 15)
    total_endpoints = len(prepared.nodes)
    masks, node_partitions, _ = opportunity_masks(prepared, component_partitions)
    pools = _pool_counts(prepared, masks)

    endpoint_deviations = [
        quantized_ratio(
            abs(int(endpoint_counts[index]) * 100 - target_weights[index] * total_endpoints),
            100 * total_endpoints,
            scale,
        )
        for index in range(3)
    ]
    endpoint_max = max(endpoint_deviations)
    endpoint_limit = quantized_ratio(3, 100, scale)

    pair_floor = int(criteria["minimum_released_positive_pairs_each_opportunity_pool"])
    component_floor = int(criteria["minimum_participating_components_each_opportunity_pool"])
    source_floor = int(criteria["minimum_released_positive_pairs_per_source_each_opportunity_pool"])
    evidence_ratios = []
    for values in pools.values():
        evidence_ratios.extend(
            [
                quantized_ratio(values["pairs"], pair_floor, scale),
                quantized_ratio(values["components"], component_floor, scale),
                quantized_ratio(values["HI-II-14_pairs"], source_floor, scale),
                quantized_ratio(values["HuRI_pairs"], source_floor, scale),
            ]
        )
    minimum_evidence_ratio = min(evidence_ratios)

    global_all = len(prepared.pair_endpoint_a)
    global_source_counts = {
        "HI-II-14": int(np.count_nonzero(prepared.hi_mask)),
        "HuRI": int(np.count_nonzero(prepared.huri_mask)),
    }
    source_deviations = []
    for values in pools.values():
        for source, global_count in global_source_counts.items():
            numerator = abs(values[f"{source}_pairs"] * global_all - values["pairs"] * global_count)
            source_deviations.append(
                quantized_ratio(numerator, max(1, values["pairs"] * global_all), scale)
            )
    maximum_source_deviation = max(source_deviations)

    heldout_imbalances = []
    for axis in ("C2", "C3"):
        development = pools[f"{axis}:development"]
        test = pools[f"{axis}:test"]
        for field in ("pairs", "HI-II-14_pairs", "HuRI_pairs"):
            heldout_imbalances.append(
                quantized_ratio(
                    abs(development[field] - test[field]),
                    max(1, development[field] + test[field]),
                    scale,
                )
            )
    maximum_heldout_imbalance = max(heldout_imbalances)

    total_degree = int(prepared.all_degrees.sum())
    degree_deviations = []
    degree_mass = []
    for index in range(3):
        value = int(prepared.all_degrees[node_partitions == index].sum())
        degree_mass.append(value)
        degree_deviations.append(
            quantized_ratio(abs(value * 100 - target_weights[index] * total_degree), 100 * total_degree, scale)
        )
    maximum_degree_deviation = max(degree_deviations)

    hub_deviations = []
    hub_counts: dict[str, list[int]] = {}
    for fraction, indices in prepared.global_hub_indices.items():
        counts = [int(np.count_nonzero(node_partitions[indices] == index)) for index in range(3)]
        hub_counts[str(fraction)] = counts
        for index, count in enumerate(counts):
            hub_deviations.append(
                quantized_ratio(abs(count * 100 - target_weights[index] * len(indices)), 100 * len(indices), scale)
            )
    maximum_hub_deviation = max(hub_deviations)

    failures: list[str] = []
    if endpoint_max > endpoint_limit:
        failures.append("endpoint_balance")
    if any(values["pairs"] < pair_floor for values in pools.values()):
        failures.append("positive_pair_floor")
    if any(values["components"] < component_floor for values in pools.values()):
        failures.append("component_floor")
    if any(
        values[f"{source}_pairs"] < source_floor
        for values in pools.values()
        for source in ("HI-II-14", "HuRI")
    ):
        failures.append("source_floor")
    if maximum_source_deviation > quantized_ratio(10, 100, scale):
        failures.append("source_composition")
    if maximum_heldout_imbalance > quantized_ratio(35, 100, scale):
        failures.append("heldout_axis_balance")
    if maximum_degree_deviation > quantized_ratio(10, 100, scale):
        failures.append("degree_mass_balance")
    if maximum_hub_deviation > quantized_ratio(10, 100, scale):
        failures.append("hub_balance")

    sum_endpoint_count_deviation_units = sum(
        abs(int(endpoint_counts[index]) * 100 - target_weights[index] * total_endpoints)
        for index in range(3)
    )
    score = (
        endpoint_max,
        -minimum_evidence_ratio,
        maximum_heldout_imbalance,
        maximum_source_deviation,
        maximum_degree_deviation,
        maximum_hub_deviation,
        sum_endpoint_count_deviation_units,
        int(candidate_index),
    )
    return {
        "candidate_index": int(candidate_index),
        "valid": not failures,
        "failures": failures,
        "score": score,
        "endpoint_counts": [int(value) for value in endpoint_counts],
        "endpoint_deviation_units": endpoint_deviations,
        "maximum_endpoint_deviation_units": endpoint_max,
        "minimum_evidence_ratio_units": minimum_evidence_ratio,
        "maximum_heldout_imbalance_units": maximum_heldout_imbalance,
        "maximum_source_deviation_units": maximum_source_deviation,
        "maximum_degree_deviation_units": maximum_degree_deviation,
        "maximum_hub_deviation_units": maximum_hub_deviation,
        "degree_mass": degree_mass,
        "hub_counts": hub_counts,
        "pools": pools,
    }


def search_allocations(
    *,
    prepared: PreparedAllocation,
    definition: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    allocation = config["allocation"]
    candidate_count = int(allocation["candidate_count_per_definition"])
    salt = str(allocation["public_hash_salt"])
    seed = str(allocation["deterministic_seed"])
    failures: Counter[str] = Counter()
    valid_count = 0
    selected_evaluation: dict[str, Any] | None = None
    selected_assignments: np.ndarray | None = None
    for candidate_index in range(candidate_count):
        assignments, counts = allocate_candidate(
            component_representatives=prepared.component_representatives,
            component_sizes=prepared.component_sizes,
            definition=definition,
            candidate_index=candidate_index,
            salt=salt,
            seed=seed,
        )
        evaluation = evaluate_candidate(
            prepared=prepared,
            component_partitions=assignments,
            endpoint_counts=counts,
            config=config,
            candidate_index=candidate_index,
        )
        failures.update(evaluation["failures"])
        if not evaluation["valid"]:
            continue
        valid_count += 1
        if selected_evaluation is None or evaluation["score"] < selected_evaluation["score"]:
            selected_evaluation = evaluation
            selected_assignments = assignments.copy()
    return {
        "definition": definition,
        "candidate_count": candidate_count,
        "valid_candidate_count": valid_count,
        "failure_counts": dict(sorted(failures.items())),
        "selected_evaluation": selected_evaluation,
        "selected_assignments": selected_assignments,
    }


__all__ = [
    "PARTITIONS",
    "PARTITION_CODES",
    "POOL_KEYS",
    "SOURCES",
    "PreparedAllocation",
    "allocate_candidate",
    "base_component_order",
    "candidate_order_indices",
    "component_id",
    "degree_histogram",
    "deterministic_components",
    "evaluate_candidate",
    "nearest_rank",
    "opportunity_masks",
    "prepare_allocation",
    "quantized_ratio",
    "search_allocations",
]
