from __future__ import annotations

import math

import numpy as np
import pytest
import torch

from ipin_openppi.stage1.baselines import (
    KMER_ALPHABET,
    build_training_graph,
    common_neighbors_score,
    component_mass_product_score,
    degree_sum_score,
    deterministic_hash_score,
    exact_interolog_score,
    kmer3_csr,
    length_ratio_score,
    length_sum_score,
    normalized_kmer3_vector,
    preferential_attachment_score,
    sparse_cosine,
)
from ipin_openppi.stage1.models import build_model, parameter_count


@pytest.mark.parametrize(
    "family,dropout,dimension",
    [
        ("lightweight_esm2_150m_linear", 0.0, 640),
        ("esm2_650m_linear_ablation", 0.0, 1280),
        ("esm2_650m_nonlinear_no_gate_ablation", 0.1, 1280),
        ("esm2_650m_partner_gated_primary", 0.1, 1280),
    ],
)
def test_all_frozen_heads_are_exactly_swap_symmetric(
    family: str, dropout: float, dimension: int
) -> None:
    model = build_model(family, dropout=dropout, seed=20260803).eval()
    generator = torch.Generator().manual_seed(7)
    a = torch.randn(5, dimension, generator=generator)
    b = torch.randn(5, dimension, generator=generator)
    with torch.no_grad():
        forward = model(a, b)
        reverse = model(b, a)
    assert torch.equal(forward, reverse)
    assert parameter_count(model) < 2_000_000


def test_initialization_is_reproducible_and_seed_specific() -> None:
    first = build_model("esm2_650m_partner_gated_primary", dropout=0.1, seed=20260803)
    second = build_model("esm2_650m_partner_gated_primary", dropout=0.1, seed=20260803)
    third = build_model("esm2_650m_partner_gated_primary", dropout=0.1, seed=20260817)
    assert all(torch.equal(a, b) for a, b in zip(first.parameters(), second.parameters(), strict=True))
    assert any(not torch.equal(a, b) for a, b in zip(first.parameters(), third.parameters(), strict=True))


def test_zero_parameter_control_formulas() -> None:
    assert 0.0 <= deterministic_hash_score("pair") <= 1.0
    assert degree_sum_score(2, 3) == pytest.approx(math.log1p(2) + math.log1p(3))
    assert preferential_attachment_score(2, 3) == pytest.approx(math.log1p(6))
    assert component_mass_product_score(4, 5) == pytest.approx(math.log1p(20))
    assert common_neighbors_score({"a", "b"}, {"b", "c"}) == pytest.approx(math.log1p(1))
    assert length_sum_score(10, 20) == pytest.approx(math.log1p(10) + math.log1p(20))
    assert length_ratio_score(10, 20) == pytest.approx(-abs(math.log1p(10) - math.log1p(20)))


def test_kmer_mapping_cosine_and_csr_are_exact() -> None:
    assert len(KMER_ALPHABET) == 21
    first = normalized_kmer3_vector("AAAU")
    second = normalized_kmer3_vector("AAAX")
    assert sparse_cosine(first, second) == pytest.approx(1.0)
    matrix = kmer3_csr(["AAAU", "AAAX", "CCC"])
    similarity = (matrix @ matrix.T).toarray()
    assert similarity[0, 1] == pytest.approx(1.0)
    assert similarity[0, 2] == pytest.approx(0.0)


def test_exact_interolog_checks_both_orientations() -> None:
    sim_a = np.asarray([0.9, 0.1, 0.3])
    sim_b = np.asarray([0.2, 0.8, 0.4])
    edge_u = np.asarray([0, 1], dtype=np.int64)
    edge_v = np.asarray([1, 2], dtype=np.int64)
    assert exact_interolog_score(sim_a, sim_b, edge_u, edge_v) == pytest.approx(0.8)


def test_training_graph_uses_only_supplied_positive_edges() -> None:
    degree, neighbors, mass = build_training_graph(
        [("a", "b"), ("a", "c")], {"a": "x", "b": "x", "c": "y"}
    )
    assert degree == {"a": 2, "b": 1, "c": 1}
    assert neighbors["a"] == {"b", "c"}
    assert mass == {"x": 3, "y": 1}
