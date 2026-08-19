from __future__ import annotations

import hashlib

import numpy as np
import pytest

from ipin_openppi.local_diagnostic.semantics import (
    local_pair_scores,
    nested_cell,
    phase_a_trigger,
    segment_boundaries,
    select_heldout_components,
)


def test_segment_boundaries_are_exact_exhaustive_and_bounded() -> None:
    assert segment_boundaries(1) == ((0, 1),)
    assert segment_boundaries(256) == ((0, 128), (128, 256))
    long = segment_boundaries(10_000)
    assert len(long) == 32
    assert long[0][0] == 0 and long[-1][1] == 10_000
    assert all(left[1] == right[0] for left, right in zip(long, long[1:]))


def test_component_holdout_is_hash_ordered_and_cells_are_symmetric() -> None:
    sizes = {"a": 2, "b": 3, "c": 1}
    salt = "fixture"
    expected_first = min(
        sizes, key=lambda value: (hashlib.sha256(f"{salt}:{value}".encode()).hexdigest(), value)
    )
    observed = select_heldout_components(sizes, salt=salt, target_endpoints=1)
    assert observed == frozenset({expected_first})
    other = next(value for value in sizes if value not in observed)
    assert nested_cell(expected_first, expected_first, observed) == "C3"
    assert nested_cell(expected_first, other, observed) == "C2"
    assert nested_cell(other, expected_first, observed) == "C2"
    assert nested_cell(other, other, observed) == "C1"


def test_local_scores_match_hand_calculation_and_swap_symmetry() -> None:
    a = np.asarray([[1.0, 0.0], [0.0, 1.0]])
    b = np.asarray([[1.0, 0.0], [0.0, -1.0]])
    first = local_pair_scores(a, [1, 3], b, [2, 2])
    second = local_pair_scores(b, [2, 2], a, [1, 3])
    assert first.local_max_segment_cosine == pytest.approx(1.0)
    assert first.local_top4_segment_cosine == pytest.approx(0.0)
    assert first.matched_global_pooled_esm_cosine == pytest.approx(-1.0 / np.sqrt(5.0))
    assert first == second


def test_segment_weighted_global_reconstructs_residue_mean() -> None:
    residues = np.arange(21, dtype=np.float64).reshape(7, 3)
    bounds = segment_boundaries(7, target_residues=3)
    segments = np.stack([residues[start:stop].mean(axis=0) for start, stop in bounds])
    lengths = np.asarray([stop - start for start, stop in bounds])
    assert np.allclose(np.average(segments, axis=0, weights=lengths), residues.mean(axis=0))


def test_phase_a_trigger_is_permissive_point_rule() -> None:
    passed, delta = phase_a_trigger(0.52, 0.50)
    assert passed is True and delta == pytest.approx(0.02)
    assert phase_a_trigger(0.509, 0.40)[0] is False
    assert phase_a_trigger(0.60, 0.595)[0] is False
