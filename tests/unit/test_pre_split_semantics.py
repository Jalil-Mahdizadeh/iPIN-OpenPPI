from __future__ import annotations

import json

from ipin_openppi.pre_split_audit.semantics import (
    allocate_components,
    degree_summary,
    deterministic_components,
    numeric_distribution,
    opportunity_counts,
    source_membership_strata,
)


def test_components_are_transitive_and_edge_order_independent() -> None:
    nodes = ["d", "c", "b", "a", "singleton"]
    forward, sizes_forward = deterministic_components(
        nodes, [("c", "d"), ("a", "b"), ("b", "c")]
    )
    reverse, sizes_reverse = deterministic_components(
        reversed(nodes), [("b", "c"), ("a", "b"), ("d", "c")]
    )
    assert forward == reverse
    assert sizes_forward == sizes_reverse == {"a": 4, "singleton": 1}
    assert {forward[node] for node in "abcd"} == {"a"}


def test_degree_summary_includes_zero_degree_population_and_hubs() -> None:
    summary = degree_summary([0, 0, 1, 1, 2, 6])
    assert summary["population_entity_count"] == 6
    assert summary["positive_exposed_entity_count"] == 4
    assert summary["degree_sum"] == 10
    assert summary["degree_q50"] == 1
    assert summary["degree_q99"] == 6
    assert summary["maximum_degree"] == 6
    assert summary["top_1_percent_degree_share"] == 0.6
    assert json.loads(str(summary["degree_histogram_json"])) == {
        "0": 2,
        "1": 2,
        "10-19": 0,
        "100+": 0,
        "2": 1,
        "20-49": 0,
        "3-4": 0,
        "5-9": 1,
        "50-99": 0,
    }


def test_source_strata_are_mutually_exclusive_and_complete() -> None:
    hi = {("a", "b"), ("b", "c")}
    huri = {("b", "c"), ("c", "d")}
    strata = source_membership_strata(hi, huri)
    assert strata == {
        "HI-II-14_only": {("a", "b")},
        "HuRI_only": {("c", "d")},
        "both": {("b", "c")},
    }
    assert set().union(*strata.values()) == hi | huri


def test_ephemeral_allocation_is_deterministic_and_size_balanced() -> None:
    sizes = {f"c{index}": 1 for index in range(100)}
    fractions = {"train": 0.70, "development": 0.15, "test": 0.15}
    first, counts = allocate_components(
        sizes, seed="fixture", trial_index=3, target_fractions=fractions
    )
    second, repeated = allocate_components(
        dict(reversed(list(sizes.items()))),
        seed="fixture",
        trial_index=3,
        target_fractions=fractions,
    )
    assert first == second
    assert counts == repeated == {"train": 70, "development": 15, "test": 15}


def test_opportunity_counts_preserve_exclusive_c2_and_c3_semantics() -> None:
    pairs = {
        ("a", "b"),
        ("a", "c"),
        ("b", "c"),
        ("a", "d"),
        ("d", "e"),
    }
    memberships = {node: node for node in "abcde"}
    partitions = {
        "a": "train",
        "b": "train",
        "c": "train",
        "d": "test",
        "e": "test",
    }
    sources = {
        pair: frozenset({"HI-II-14", "HuRI"})
        if pair == ("d", "e")
        else frozenset({"HuRI"})
        for pair in pairs
    }
    observed = opportunity_counts(pairs, memberships, partitions, sources)
    assert observed == {
        "c1_pairs": 3,
        "c2_pairs": 1,
        "c3_pairs": 1,
        "c1_components": 3,
        "c2_components": 2,
        "c3_components": 2,
        "c3_hi_ii_14_pairs": 1,
        "c3_huri_pairs": 1,
    }


def test_numeric_distribution_is_nearest_rank_and_fail_closed_empty() -> None:
    assert numeric_distribution([]) == {
        "minimum": 0,
        "q05": 0,
        "q50": 0,
        "q95": 0,
        "maximum": 0,
    }
    assert numeric_distribution([1, 2, 3, 4, 5]) == {
        "minimum": 1,
        "q05": 1,
        "q50": 3,
        "q95": 5,
        "maximum": 5,
    }
