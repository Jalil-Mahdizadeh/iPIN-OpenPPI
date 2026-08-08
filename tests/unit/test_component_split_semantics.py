from __future__ import annotations

import numpy as np

from ipin_openppi.component_split.semantics import (
    allocate_candidate,
    deterministic_components,
    opportunity_masks,
    prepare_allocation,
    quantized_ratio,
)


def test_components_and_candidate_allocation_are_deterministic() -> None:
    nodes = ["d", "c", "b", "a", "singleton"]
    memberships, sizes = deterministic_components(
        nodes, [("a", "b"), ("c", "d"), ("b", "c")]
    )
    assert sizes == {"a": 4, "singleton": 1}
    assert {memberships[node] for node in "abcd"} == {"a"}

    singleton_sizes = {f"c{index:03d}": 1 for index in range(100)}
    components = sorted(singleton_sizes)
    first, counts = allocate_candidate(
        component_representatives=components,
        component_sizes=singleton_sizes,
        definition="local_domain_union",
        candidate_index=17,
        salt="fixture",
        seed="20260803",
    )
    second, repeated = allocate_candidate(
        component_representatives=components,
        component_sizes=dict(reversed(list(singleton_sizes.items()))),
        definition="local_domain_union",
        candidate_index=17,
        salt="fixture",
        seed="20260803",
    )
    assert np.array_equal(first, second)
    assert counts.tolist() == repeated.tolist() == [70, 15, 15]


def test_quantization_is_nonnegative_nearest_half_up() -> None:
    assert quantized_ratio(1, 3, 1_000) == 333
    assert quantized_ratio(1, 2, 1) == 1
    assert quantized_ratio(1, 4, 2) == 1


def test_opportunity_masks_preserve_c1_exclusive_c2_and_strict_c3() -> None:
    nodes = list("abcdefg")
    pairs = {
        ("a", "b"),
        ("a", "c"),
        ("b", "c"),
        ("a", "d"),
        ("d", "e"),
        ("a", "f"),
        ("f", "g"),
    }
    pair_sources = {pair: frozenset({"HuRI"}) for pair in pairs}
    prepared = prepare_allocation(
        nodes=nodes,
        memberships={node: node for node in nodes},
        component_sizes={node: 1 for node in nodes},
        positive_pairs=pairs,
        pair_sources=pair_sources,
        hub_fractions=[0.01, 0.05, 0.10],
    )
    component_index = {
        component: index for index, component in enumerate(prepared.component_representatives)
    }
    assignments = np.empty(len(nodes), dtype=np.int8)
    for endpoint in "abc":
        assignments[component_index[endpoint]] = 0
    for endpoint in "de":
        assignments[component_index[endpoint]] = 1
    for endpoint in "fg":
        assignments[component_index[endpoint]] = 2
    masks, node_partitions, _ = opportunity_masks(prepared, assignments)
    assert int(np.count_nonzero(masks["C1:training_pool"])) == 3
    assert int(np.count_nonzero(masks["C2:development"])) == 1
    assert int(np.count_nonzero(masks["C2:test"])) == 1
    assert int(np.count_nonzero(masks["C3:development"])) == 1
    assert int(np.count_nonzero(masks["C3:test"])) == 1
    assert [int(np.count_nonzero(node_partitions == code)) for code in range(3)] == [3, 2, 2]
