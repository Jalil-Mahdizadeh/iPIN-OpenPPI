from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from ipin_openppi.homology_source.data import project_sources, kmer_similarity
from ipin_openppi.homology_source.semantics import (
    alignment_values, alignment_scores, exhaustive_transfer_numpy, finite_ratio,
    fit_rows, panel_mask, purged_fit_mask, summary_interval,
)


def alignment(**changes):
    x = dict(a=0, b=1, mismatch=50, columns=100, qs=1, qe=100, qlen=200,
             ts=1, te=100, tlen=400, evalue=.0001, bits=30)
    x.update(changes)
    return [str(v) for v in x.values()]


def test_exact_alignment_identity_and_coverage():
    values = alignment_values(alignment(), [200, 400])
    a, b, loc, cov, purge = alignment_scores(values)
    assert (a, b, loc, purge) == (0, 1, .5, True)
    assert cov == pytest.approx(.5 * np.sqrt(.5 * .25))


def test_long_diverse_kmer_self_cosine_uses_accurate_accumulation():
    from itertools import product
    seq = ''.join(''.join(t) for t in product('ACDEFGHIKLMNPQRSTVWY', repeat=3))
    sim = kmer_similarity([seq, seq[::-1]])
    np.testing.assert_allclose(np.diag(sim), 1, rtol=0, atol=1e-7)
    np.testing.assert_array_equal(sim, sim.T)


def test_gaps_are_not_counted_as_matches():
    values = alignment_values(alignment(columns=120, mismatch=20), [200, 400])
    assert values[2] == 60  # 200 consumed residues - 120 columns - 20 mismatches
    assert alignment_scores(values)[2] == .5


@pytest.mark.parametrize('changes', [dict(a=2), dict(qlen=201), dict(qs=0), dict(qe=201),
                                    dict(mismatch=-1), dict(mismatch=101), dict(columns=80),
                                    dict(evalue=-1), dict(evalue='nan')])
def test_bad_alignment_rejected(changes):
    with pytest.raises(ValueError):
        alignment_values(alignment(**changes), [200, 400])


@pytest.mark.parametrize('changes', [dict(mismatch=81), dict(qe=39, te=39, columns=39, mismatch=0),
                                    dict(evalue=.00101)])
def test_alignment_below_criteria_zero(changes):
    assert alignment_scores(alignment_values(alignment(**changes), [200, 400]))[2:] == (0., 0., False)


def test_short_domain_is_scored_but_not_purge_link():
    values = alignment_values(alignment(qe=40, te=40, columns=40, mismatch=20), [200, 400])
    assert alignment_scores(values)[2] == .25
    assert not alignment_scores(values)[4]


def test_exact_twenty_percent_and_evalue_boundary_included():
    values = alignment_values(alignment(mismatch=80, evalue=.001), [200, 400])
    assert alignment_scores(values)[2] == .2
    assert alignment_scores(values)[4]


def test_reverse_alignment_scores_equal():
    forward = alignment_values(alignment(), [200, 400])
    reverse = alignment_values(alignment(a=1, b=0, qlen=400, tlen=200), [200, 400])
    assert alignment_scores(forward)[2:] == alignment_scores(reverse)[2:]


def test_purge_removes_whole_component_not_only_direct_neighbor():
    folds, comp = np.array([0, 1, 1, 2]), np.array([0, 1, 1, 2])
    fit = purged_fit_mask(folds, comp, 0, np.array([0]), np.array([1]))
    np.testing.assert_array_equal(fit, [False, False, False, True])


def test_purge_both_orientations_and_no_edges():
    folds, comp = np.arange(3), np.arange(3)
    a = purged_fit_mask(folds, comp, 0, np.array([1]), np.array([0]))
    b = purged_fit_mask(folds, comp, 0, np.array([], int), np.array([], int))
    np.testing.assert_array_equal(a, [False, False, True])
    np.testing.assert_array_equal(b, [False, True, True])


def fixture_data():
    return dict(p_a=np.array([0, 0, 1, 3]), p_b=np.array([1, 2, 2, 4]),
                u_a=np.array([0, 1]), u_b=np.array([3, 3]),
                u_num=np.array([7, 8]), u_den=np.array([2, 3]))


def test_source_hidden_positive_reinserted_in_U_with_unit_weight():
    data = fixture_data()
    plan = fit_rows(data, np.array([1, 2, 3, 2]), np.array([1, 1, 1, 1, 0], bool), 1)
    np.testing.assert_array_equal(plan['p_rows'], [0, 2])
    np.testing.assert_array_equal(plan['hidden_p_rows'], [1])
    np.testing.assert_array_equal(plan['u_a'], [0, 0, 1])
    np.testing.assert_array_equal(plan['u_b'], [2, 3, 3])
    np.testing.assert_array_equal(plan['u_num'], [1, 7, 8])
    np.testing.assert_array_equal(plan['u_den'], [1, 2, 3])
    assert 4 not in plan['u_b']


def test_union_has_no_reinserted_hidden_positives():
    plan = fit_rows(fixture_data(), np.array([1, 2, 3, 2]), np.ones(5, bool), 0)
    assert len(plan['p_rows']) == 4
    assert len(plan['hidden_p_rows']) == 0


@pytest.mark.parametrize('source', [[1, 0, 3, 2], [1, 4, 3, 2], [1, 2, 3]])
def test_unknown_source_fail_closed(source):
    with pytest.raises(ValueError):
        fit_rows(fixture_data(), np.array(source), np.ones(5, bool), 1)


def test_source_panels_exclude_shared_positive_not_turn_into_U():
    ev = {'a': np.arange(4), 'positive': np.array([1, 1, 1, 0], bool), 'parent_row': np.array([0, 1, 2, 20])}
    np.testing.assert_array_equal(panel_mask(ev, np.array([1, 2, 3]), 2), [False, True, False, True])


def test_exhaustive_transfer_reverse_and_full_edge_search():
    sim = np.eye(6)
    sim[0, 3], sim[1, 2] = .9, .8
    score = exhaustive_transfer_numpy(sim, np.array([0]), np.array([1]), np.array([4, 2]), np.array([5, 3]))
    np.testing.assert_array_equal(score, [.8])
    assert exhaustive_transfer_numpy(sim, np.array([1]), np.array([0]), np.array([4, 2]), np.array([5, 3])) == score


def test_heldout_positive_poison_not_used():
    sim = np.eye(6)
    score = exhaustive_transfer_numpy(sim, np.array([0]), np.array([1]), np.array([2]), np.array([3]))
    assert score[0] == 0
    assert exhaustive_transfer_numpy(sim, np.array([0]), np.array([1]), np.array([0, 2]), np.array([1, 3]))[0] == 1


def test_empty_fit_graph_is_not_zero_performance():
    with pytest.raises(ValueError):
        exhaustive_transfer_numpy(np.eye(2), np.array([0]), np.array([1]), np.array([], int), np.array([], int))


def test_gpu_exhaustive_transfer_matches_brute_force_when_cuda_available():
    import torch
    if not torch.cuda.is_available():
        pytest.skip('CUDA runtime exercised separately before execution freeze')
    from ipin_openppi.homology_source.pipeline import exhaustive_transfer_gpu
    rng = np.random.default_rng(47)
    sim = rng.random((20, 20), dtype=np.float32)
    a, b = np.array([0, 1, 2, 3]), np.array([4, 5, 6, 7])
    pa_, pb_ = np.array([8, 9, 10, 11, 12]), np.array([13, 14, 15, 16, 17])
    expected = exhaustive_transfer_numpy(sim, a, b, pa_, pb_)
    actual = exhaustive_transfer_gpu(sim, a, b, pa_, pb_, batch=3)
    np.testing.assert_array_equal(actual, expected)


def test_missing_mass_and_insufficient_bootstrap_are_explicit():
    assert np.isnan(finite_ratio(np.array([1.]), np.array([0.]))[0])
    out = summary_interval(np.r_[np.ones(94), np.full(6, np.nan)])
    assert out['ci95'] is None and out['valid_replicates'] == 94
    assert summary_interval(np.ones(100))['ci95'] == [1., 1.]


def test_source_projection_outputs_only_exact_public_positive_allowlist(tmp_path):
    import duckdb
    allowed = pa.table({'positive_index': [0, 1], 'a': [0, 1], 'b': [1, 2]})
    genes = pa.table({'gene': ['A', 'B', 'C', 'D'], 'endpoint': [0, 1, 2, 3]})
    src = pa.table({'gene_a': ['A', 'B', 'B', 'A', 'C', 'D'],
                    'gene_b': ['B', 'A', 'C', 'C', 'D', 'A'],
                    'source_dataset': ['HI-II-14', 'HuRI', 'HuRI', 'HuRI', 'HI-II-14', 'HuRI'],
                    'unique_gene_pair': [True] * 6, 'label_authorized': [False] * 6})
    path = tmp_path / 'evidence.parquet'
    pq.write_table(src, path)
    with duckdb.connect(':memory:') as conn:
        out = project_sources(conn, allowed, genes, [str(path)])
    assert out == [(0, 3), (1, 2)]  # A-C and C-D must not escape despite public endpoints.


def test_quartet_source_filter_retains_only_two_target_exclusive_P():
    ev = {'a': np.arange(6), 'positive': np.array([1, 1, 1, 1, 0, 0], bool), 'parent_row': np.arange(6)}
    keep = panel_mask(ev, np.array([1, 1, 2, 3]), 1)
    quartets = np.array([[0, 1, 4, 5], [0, 2, 4, 5], [0, 3, 4, 5]])
    np.testing.assert_array_equal(np.all(keep[quartets], axis=1), [True, False, False])
