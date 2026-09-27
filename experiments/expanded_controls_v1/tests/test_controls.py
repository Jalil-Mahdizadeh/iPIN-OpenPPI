import numpy as np
import pytest
import torch

from control_io import codes, check_pairs
from control_math import composition, graph, neighbor_max_numpy, neighbor_max_cuda, transfer_numpy, transfer_cuda
from diagnostic_math import anchor_bootstrap, quartet_estimates
from ipin_openppi.partner_specificity.semantics import (
    embedding_indices, build_queries, bootstrap_anchor_totals, quartet_bootstrap_totals, quartet_credit,
)
from ipin_openppi.homology_source.semantics import exhaustive_transfer_numpy, alignment_scores, alignment_values
from ipin_openppi.stage1.baselines import kmer3_csr
from control_metrics import cohort_bootstrap
from macro_metrics import macro_bootstrap


def test_identity_join_uses_manifest_rows_instead_of_input_order():
    manifest = [{"sequence_sha256": "B", "row_index": 2},
                {"sequence_sha256": "A", "row_index": 0},
                {"sequence_sha256": "C", "row_index": 1}]
    rows = embedding_indices(manifest, ["C", "B", "A"], 3)
    np.testing.assert_array_equal(rows, [1, 2, 0])
    with pytest.raises(ValueError):
        embedding_indices(manifest, ["C", "missing", "A"], 3)
    with pytest.raises(ValueError):
        embedding_indices(manifest + [manifest[0]], ["C", "B", "A"], 4)


def test_unordered_identity_and_duplicate_rejection():
    a, b = np.array([1, 3]), np.array([4, 2])
    np.testing.assert_array_equal(codes(a, b, 6), codes(b, a, 6))
    with pytest.raises(ValueError):
        check_pairs(np.array([1, 4]), np.array([4, 1]), 6)
    with pytest.raises(ValueError):
        codes(np.array([1]), np.array([1]), 6)


def test_graph_counts_train_edges_only_and_heldout_component_ties():
    adj, degree, mass = graph(6, np.array([0, 1, 0]), np.array([1, 2, 2]),
                              ["train_a", "train_a", "train_b", "heldout", "heldout", "other"])
    np.testing.assert_array_equal(degree, [2, 2, 2, 0, 0, 0])
    np.testing.assert_array_equal(mass, [4, 4, 2, 0, 0, 0])
    assert adj[0].multiply(adj[1]).sum() == 1
    with pytest.raises(ValueError):
        graph(6, np.array([0, 1]), np.array([1, 0]), np.arange(6))


def test_sequence_alphabet_and_cosines():
    aac = composition(["AAB", "AAX", "CCC"])
    np.testing.assert_allclose(aac[0], aac[1], rtol=0, atol=0)
    assert np.dot(aac[0], aac[2]) == 0
    km = kmer3_csr(["AAAB", "AAAX", "CCC", "A"])
    np.testing.assert_allclose(km[0].toarray(), km[1].toarray(), rtol=0, atol=0)
    assert float(km[0].multiply(km[2]).sum()) == 0
    assert km[3].nnz == 0


@pytest.mark.parametrize("seed", [7, 31, 99])
def test_full_edge_transfer_matches_both_orientations_and_negative_kernels(seed):
    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(9, 9))
    sim = (raw + raw.T) / 2
    pa, pb = np.array([0, 1, 2, 3]), np.array([1, 2, 3, 4])
    a, b = np.array([0, 5, 6, 7, 8]), np.array([8, 6, 7, 1, 2])
    neighbor = neighbor_max_numpy(sim, pa, pb)
    expected = exhaustive_transfer_numpy(sim, a, b, pa, pb)
    np.testing.assert_allclose(transfer_numpy(sim, neighbor, a, b), expected, rtol=0, atol=0)
    np.testing.assert_allclose(transfer_numpy(sim, neighbor, b, a), expected, rtol=0, atol=0)
    tensor = torch.as_tensor(sim, device="cuda")
    got = neighbor_max_cuda(tensor, pa, pb, batch=3)
    np.testing.assert_array_equal(got.cpu().numpy(), neighbor)
    np.testing.assert_allclose(transfer_cuda(tensor, got, a, b, batch=2), expected, rtol=0, atol=0)


def test_alignment_count_identity_and_filters():
    # 50+50-55-5 = 40 identical columns: identity 40/55.
    fields = ["0", "1", "5", "55", "1", "50", "100", "1", "50", "200", "1e-8", "80"]
    values = alignment_values(fields, [100, 200])
    a, b, local, coverage, purge = alignment_scores(values)
    assert (a, b) == (0, 1)
    assert local == pytest.approx(40/55 * 50/80)
    assert coverage == pytest.approx(40/55 * np.sqrt(.5*.25))
    assert not purge
    changed = list(values)
    changed[-1] = .01
    assert alignment_scores(changed)[2:4] == (0., 0.)


def test_constituent_cohort_draws_exactly_reproduce_established_macro():
    rng = np.random.default_rng(492)
    scores = rng.integers(0, 5, (43, 3)).astype(float)
    cohort = np.arange(43) % 2
    positive = np.arange(43) % 3 == 0
    weights = rng.integers(1, 7, 43).astype(float)/5
    ca = [f"c{x}" for x in rng.integers(0, 8, 43)]
    cb = [f"c{x}" for x in rng.integers(0, 8, 43)]
    cp, cd, cm = cohort_bootstrap(scores, positive, weights, cohort, ca, cb,
                                  "cohort_oracle", replicates=37, batch=3)
    point, draw, meta = macro_bootstrap(scores, positive, weights, cohort, ca, cb,
                                      "cohort_oracle", replicates=37, batch=3)
    np.testing.assert_array_equal(cp.mean(1), point)
    np.testing.assert_array_equal(cd.mean(1), draw)
    assert cm == meta


def test_anchor_gpu_matches_independent_cpu_ratios_with_ties_and_shared_components():
    rng = np.random.default_rng(333)
    a, b = np.triu_indices(9, 1)
    positive = np.arange(len(a)) % 3 == 0
    data = {"a": a, "b": b, "positive": positive,
            "weight": rng.integers(1, 9, len(a)).astype(float)/3}
    component = np.array([0, 0, 1, 1, 2, 3, 3, 4, 4])
    multipliers = rng.poisson(1, (37, 5))
    scores = rng.integers(-2, 4, (len(a), 3)).astype(float)
    points, got, support = anchor_bootstrap(scores, data, component, multipliers, batch=7)
    queries = build_queries(a, b, positive)
    for j in range(3):
        numerator, denominator = bootstrap_anchor_totals(scores[:, j], queries, data["weight"], component, multipliers)
        expected = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0)
        np.testing.assert_allclose(got[j], expected, rtol=0, atol=1e-12, equal_nan=True)
    assert support["anchors"] == len(queries)
    assert np.isfinite(points).all()


def test_quartets_preserve_additive_null_and_unique_component_multiplicity():
    a, b = np.array([0, 2, 0, 2, 0, 1]), np.array([1, 3, 3, 1, 2, 3])
    rows = np.array([[0, 1, 2, 3], [0, 1, 4, 5]])
    endpoints = np.array([[0, 1, 2, 3], [0, 1, 2, 3]])
    unary = np.array([.11, -2.2, 9.1, 1.5])
    additive = unary[a] + unary[b]
    scores = np.column_stack([additive, np.array([3., 2., 1., 0., 4., 8.])])
    component = np.array([0, 0, 1, 2])
    count = np.random.default_rng(97).poisson(1, (37, 3))
    points, draws, credit = quartet_estimates(scores, rows, endpoints, component, count)
    np.testing.assert_array_equal(credit[:, 0], .5)
    assert points[0] == .5
    for j in range(2):
        numerator, denominator = quartet_bootstrap_totals(credit[:, j], endpoints, component, count)
        expected = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0)
        np.testing.assert_allclose(draws[j], expected, atol=1e-12, rtol=0, equal_nan=True)
