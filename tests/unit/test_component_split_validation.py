from __future__ import annotations

import numpy as np

from ipin_openppi.component_split.semantics import allocate_candidate
from ipin_openppi.validation.component_split import _allocate, _components, _contains


def test_independent_components_are_transitive_and_order_stable() -> None:
    memberships, sizes = _components(
        ["d", "c", "b", "a", "singleton"],
        {("c", "d"), ("a", "b"), ("b", "c")},
    )
    assert sizes == {"a": 4, "singleton": 1}
    assert {memberships[node] for node in "abcd"} == {"a"}


def test_independent_allocator_reproduces_frozen_hash_and_tie_rules() -> None:
    sizes = {f"c{index:03d}": 1 for index in range(100)}
    prepared = {"representatives": tuple(sorted(sizes)), "sizes": sizes}
    config = {
        "allocation": {
            "public_hash_salt": "fixture",
            "deterministic_seed": "20260803",
        }
    }
    independent, counts = _allocate(prepared, "local_domain_union", 11, config)
    production, production_counts = allocate_candidate(
        component_representatives=tuple(sorted(sizes)),
        component_sizes=sizes,
        definition="local_domain_union",
        candidate_index=11,
        salt="fixture",
        seed="20260803",
    )
    assert np.array_equal(independent, production)
    assert counts.tolist() == production_counts.tolist() == [70, 15, 15]


def test_subset_comparison_is_float_tolerant_but_fail_closed() -> None:
    assert _contains({"count": 3, "fraction": 0.1 + 1e-15}, {"count": 3, "fraction": 0.1})
    assert not _contains({"count": 4, "fraction": 0.1}, {"count": 3, "fraction": 0.1})
