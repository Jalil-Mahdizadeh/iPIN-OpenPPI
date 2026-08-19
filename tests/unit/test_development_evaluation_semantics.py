from __future__ import annotations

from decimal import Decimal
import hashlib

import numpy as np
import pytest

from ipin_openppi.development_evaluation.semantics import (
    bootstrap_cell_seed,
    bootstrap_concordance_reference,
    component_draws,
    degree_bin,
    degree_pair_stratum,
    exact_interolog_from_neighbor_max,
    exact_interolog_reference,
    neighbor_max_similarity,
    pair_component_multipliers,
    percentile_95,
    quantize_selection_metric,
    sampled_weighted_average_precision,
    seed_metric_range,
    selection_key,
    weighted_pairwise_concordance,
)


def test_ht_concordance_retains_weights_and_half_ties() -> None:
    observed = weighted_pairwise_concordance(
        [0.5, 1.0], [0.0, 0.5, 2.0], [1.0, 2.0, 1.0]
    )
    # p=.5: (1 + .5*2)/4; p=1: (1+2)/4
    assert observed == pytest.approx((0.5 + 0.75) / 2)
    bootstrapped = weighted_pairwise_concordance(
        [0.5, 1.0],
        [0.0, 0.5, 2.0],
        [1.0, 2.0, 1.0],
        positive_multipliers=[2.0, 1.0],
        unlabeled_multipliers=[1.0, 3.0, 0.0],
    )
    # U mass=7; favorable masses are 1+3 and 1+6.
    assert bootstrapped == pytest.approx((2 * 4 + 7) / (3 * 7))


def test_bootstrap_seed_and_draws_are_exact_pcg64dxsm() -> None:
    expected_seed = int.from_bytes(
        hashlib.sha256(b"20260803:bootstrap:C3_development").digest()[:8], "big"
    )
    assert bootstrap_cell_seed("C3_development") == expected_seed
    components, counts = component_draws(
        ["z", "a", "m", "a"], cell_id="C3_development", replicates=4
    )
    generator = np.random.Generator(np.random.PCG64DXSM(expected_seed))
    raw = generator.integers(0, 3, size=(4, 3), dtype=np.int64)
    expected = np.stack([np.bincount(row, minlength=3) for row in raw])
    assert components == ("a", "m", "z")
    np.testing.assert_array_equal(counts, expected)
    np.testing.assert_array_equal(counts.sum(axis=1), np.full(4, 3))


def test_pigeonhole_pair_multiplier_handles_same_component_once() -> None:
    observed = pair_component_multipliers(
        [2, 3, 0], [0, 0, 1, 2], [0, 1, 2, 1]
    )
    np.testing.assert_array_equal(observed, [2, 6, 0, 0])


def test_reference_bootstrap_is_paired_and_can_emit_empty_replicates() -> None:
    one = bootstrap_concordance_reference(
        cell_id="fixture",
        positive_scores=[0.8, 0.4],
        unlabeled_scores=[0.2, 0.6],
        unlabeled_weights=[2.0, 1.0],
        positive_component_a=["a", "b"],
        positive_component_b=["b", "b"],
        unlabeled_component_a=["a", "b"],
        unlabeled_component_b=["a", "b"],
        replicates=20,
    )
    two = bootstrap_concordance_reference(
        cell_id="fixture",
        positive_scores=[0.8, 0.4],
        unlabeled_scores=[0.2, 0.6],
        unlabeled_weights=[2.0, 1.0],
        positive_component_a=["a", "b"],
        positive_component_b=["b", "b"],
        unlabeled_component_a=["a", "b"],
        unlabeled_component_b=["a", "b"],
        replicates=20,
    )
    np.testing.assert_equal(one, two)
    assert np.isfinite(one).sum() > 0
    low, high = percentile_95(one)
    assert 0 <= low <= high <= 1


def test_selection_quantization_and_tie_breaks() -> None:
    assert quantize_selection_metric(0.6125) == Decimal("0.613")
    assert quantize_selection_metric(0.6124) == Decimal("0.612")
    linear = selection_key(
        candidate_id="z",
        family="lightweight_esm2_150m_linear",
        metrics={"C3_development": 0.7, "C2_development": 0.6, "C1_development": 0.5},
    )
    gated = selection_key(
        candidate_id="a",
        family="esm2_650m_partner_gated_primary",
        metrics={"C3_development": 0.7, "C2_development": 0.6, "C1_development": 0.5},
    )
    assert linear < gated
    assert seed_metric_range({20260803: 0.5, 20260817: 0.51, 20260831: 0.49}) == pytest.approx(0.02)


@pytest.mark.parametrize(
    ("degree", "expected"),
    [(0, "0"), (2, "2"), (3, "3-4"), (9, "5-9"), (99, "50-99"), (100, "100+")],
)
def test_degree_bins(degree: int, expected: str) -> None:
    assert degree_bin(degree) == expected
    assert degree_pair_stratum(100, 0) == "0|100+"


def test_neighbor_max_interolog_identity_matches_edge_enumeration() -> None:
    similarities = np.asarray(
        [
            [1.0, 0.2, 0.3, 0.4],
            [0.1, 1.0, 0.8, 0.2],
            [0.6, 0.1, 1.0, 0.9],
        ],
        dtype=np.float64,
    )
    edge_u = np.asarray([0, 1, 2])
    edge_v = np.asarray([1, 2, 3])
    neighbor = neighbor_max_similarity(similarities, edge_u, edge_v)
    observed = exact_interolog_from_neighbor_max(similarities, neighbor, [0, 1], [1, 2])
    expected = np.asarray(
        [
            exact_interolog_reference(similarities[0], similarities[1], edge_u, edge_v),
            exact_interolog_reference(similarities[1], similarities[2], edge_u, edge_v),
        ]
    )
    np.testing.assert_allclose(observed, expected, rtol=0, atol=0)


def test_diagnostic_average_precision_groups_exact_ties() -> None:
    assert sampled_weighted_average_precision([1.0], [0.0], [3.0]) == 1.0
    # All scores tie: one positive over total design mass 1+3.
    assert sampled_weighted_average_precision([0.0], [0.0], [3.0]) == pytest.approx(0.25)
