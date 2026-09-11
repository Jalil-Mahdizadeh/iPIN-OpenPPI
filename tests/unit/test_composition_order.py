"""DEC-0049 semantic, boundary and independent-reference regressions."""

from copy import deepcopy
from itertools import permutations
from pathlib import Path

import numpy as np
import pytest
import yaml

from ipin_openppi.composition_order import data as io
from ipin_openppi.composition_order.semantics import (
    encode, frequencies, unit_triplets, shuffle_means, row_dot, build_matches,
    matched_metrics, diagnostic_flags,
)
from ipin_openppi.composition_order.pipeline import match_census, restricted_queries
from ipin_openppi.composition_order.validation import reference_shuffle, reference_matched
from ipin_openppi.external_bioplex.semantics import directed_queries
from ipin_openppi.partner_specificity.semantics import anchor_points, bootstrap_anchor_totals
from ipin_openppi.stage1.baselines import kmer3_csr

ROOT = Path(__file__).resolve().parents[2]
CFG = yaml.safe_load((ROOT / io.CONFIG).read_text())


def panel():
    return dict(a=np.array([0] * 5 + [6] * 4), b=np.array([1, 2, 3, 4, 5, 7, 8, 9, 10]),
        positive=np.array([1, 1, 0, 0, 0, 1, 0, 0, 0], dtype=bool),
        num=np.array([1, 1, 1, 7, 3, 1, 2, 9, 2]), den=np.array([1, 1, 2, 3, 5, 1, 1, 4, 3]))


def complete_matches():
    return dict(p=np.array([0, 1, 5]), offsets=np.array([0, 3, 6, 9]), u=np.array([2, 3, 4, 2, 3, 4, 6, 7, 8]))


def test_aac_order_free_unknown_mapping():
    seq = ['AACCDUU', 'UUDCCAA', 'XXXXXX']
    f = frequencies(seq)
    np.testing.assert_array_equal(f[0], f[1])
    assert f[0, 20] == 2 / 7 and f[2, 20] == 1
    np.testing.assert_allclose(f.sum(axis=1), 1)
    with pytest.raises(ValueError):
        encode('')


@pytest.mark.parametrize('sequence', ['A', 'AC', 'AAA', 'ACDEFG', 'UUAXCCU', 'AACACCCAAA'])
def test_numeric_triplets_match_parent_string_counter(sequence):
    np.testing.assert_allclose(unit_triplets(encode(sequence)), kmer3_csr([sequence]).toarray()[0], atol=1e-15, rtol=0)


def test_exact_permutation_mean_dot_not_renormalized():
    a = np.stack([unit_triplets(encode(''.join(p))) for p in sorted(set(permutations('AAACC')))])
    b = np.stack([unit_triplets(encode(''.join(p))) for p in sorted(set(permutations('AACCC')))])
    mean_dot = a.mean(axis=0) @ b.mean(axis=0)
    np.testing.assert_allclose(mean_dot, np.mean(a @ b.T), atol=1e-15, rtol=0)
    incorrectly_normalized = mean_dot / (np.linalg.norm(a.mean(axis=0)) * np.linalg.norm(b.mean(axis=0)))
    assert incorrectly_normalized - mean_dot > .1


def test_iid_tensor_cosine_has_identical_aac_ranking():
    freq = frequencies(['AAAAACCD', 'AACCCCDE', 'ACDEFFGG'])
    tensor = np.stack([np.einsum('i,j,k->ijk', f, f, f).reshape(-1) for f in freq])
    f = freq / np.linalg.norm(freq, axis=1)[:, None]
    t = tensor / np.linalg.norm(tensor, axis=1)[:, None]
    np.testing.assert_allclose(t @ t.T, (f @ f.T)**3, atol=1e-14, rtol=0)


@pytest.mark.parametrize('sequence', ['AC', 'AAAAAA', 'AACCDDXXXU', 'ACDEFGHIKLMNPQ'])
def test_seeded_shuffle_agrees_with_independent_string_reference(sequence):
    actual = shuffle_means(sequence, 'public-identity', 'fixed-salt', 8)
    expected = reference_shuffle(sequence, 'public-identity', 'fixed-salt', 8)
    np.testing.assert_allclose(actual, expected, atol=1e-15, rtol=0)
    np.testing.assert_array_equal(actual, shuffle_means(sequence[::-1], 'public-identity', 'fixed-salt', 8))
    assert np.all(np.linalg.norm(actual, axis=1) <= 1 + 1e-15)


@pytest.mark.parametrize('count', [0, 1, 3, 7])
def test_shuffle_rejects_incomplete_halves(count):
    with pytest.raises(ValueError):
        shuffle_means('AACCDD', 'identity', 'salt', count)


def test_full_shuffle_includes_cross_half_products():
    rng = np.random.default_rng(13)
    a, b = rng.random((2, 5, 17))
    x, y = np.array([0, 1, 3]), np.array([4, 2, 0])
    full = row_dot((a + b) / 2, x, y, batch=1)
    expected = np.array([sum((a[i] @ a[j], a[i] @ b[j], b[i] @ a[j], b[i] @ b[j])) / 4 for i, j in zip(x, y)])
    np.testing.assert_allclose(full, expected, atol=1e-14, rtol=0)
    assert not np.allclose(full, (row_dot(a, x, y) + row_dot(b, x, y)) / 2)


def test_match_calipers_direction_and_no_learned_score_selection():
    cfg = deepcopy(CFG['matching'])
    cfg['minimum_U_per_positive'] = 1
    ev = dict(a=np.array([0, 0, 0, 0, 0, 6]), b=np.array([1, 2, 3, 4, 5, 1]),
              positive=np.array([1, 0, 0, 0, 0, 0], dtype=bool))
    freq = np.zeros((7, 21))
    freq[:, 0] = 1
    freq[3, :2] = [.9, .1]  # inclusive TV boundary
    freq[4, :2] = [.8999, .1001]
    lengths = np.array([100, 100, 125, 100, 100, 126, 100])
    old = {'kmer3_cosine': np.array([.2, .21, .22, .2, .2, .2]),
           'pooled_cosine': np.array([.5, .51, .5, .5, .5, .5])}
    matches = build_matches(ev, freq, lengths, old, cfg)
    np.testing.assert_array_equal(matches['composition_length']['u'], [1, 2])
    np.testing.assert_array_equal(matches['also_direct_similarity']['u'], [1])
    old['pair_linear'] = np.array([100, -100, 100, -100, 100, -100])
    repeated = build_matches(ev, freq, lengths, old, cfg)
    for tier in matches:
        for key in matches[tier]:
            np.testing.assert_array_equal(matches[tier][key], repeated[tier][key])
    cfg['minimum_U_per_positive'] = 3
    empty = build_matches(ev, freq, lengths, old, cfg)
    assert all(len(m['p']) == len(m['u']) == 0 for m in empty.values())


def test_strict_matching_requires_both_similarities():
    cfg = deepcopy(CFG['matching'])
    cfg['minimum_U_per_positive'] = 1
    ev = dict(a=np.zeros(3, dtype=int), b=np.array([1, 2, 3]), positive=np.array([1, 0, 0], bool))
    f = frequencies(['AAA'] * 4)
    old = {'kmer3_cosine': np.array([.2, .205, .22]), 'pooled_cosine': np.array([.5, .52, .5])}
    result = build_matches(ev, f, np.full(4, 100), old, cfg)
    assert len(result['composition_length']['p']) == 1
    assert len(result['also_direct_similarity']['p']) == 0


def test_matched_weight_ties_components_and_empty_draws_against_reference():
    ev, match = panel(), complete_matches()
    score = np.array([[.5, 1], [.4, 0], [.5, 1], [.1, 1], [.8, -1], [.2, .5], [.1, .5], [.3, 0], [.2, 1]])
    component = np.array([0, 0, 1, 1, 0, 2, 3, 1, 2, 3, 0])
    draws = np.array([[1, 1, 1, 1], [0, 1, 2, 1], [2, 0, 1, 0], [1, 2, 0, 3], [0, 0, 0, 0]])
    actual = matched_metrics(score, ev, match, component, draws)
    expected = reference_matched(score, ev, match, component, draws)
    for a, e in zip(actual, expected):
        np.testing.assert_allclose(a, e, atol=1e-14, rtol=0)
    assert actual[2][-1] == 0 and np.all(actual[1][-1] == 0)
    q = directed_queries(ev['a'], ev['b'], ev['positive'])
    weight = ev['num'] / ev['den']
    for j in range(score.shape[1]):
        np.testing.assert_allclose(actual[0][:, j], anchor_points(score[:, j], q, weight), atol=1e-14, rtol=0)
        num, den = bootstrap_anchor_totals(score[:, j], q, weight, component, draws)
        np.testing.assert_allclose(actual[1][:, j], num, atol=1e-14, rtol=0)
        np.testing.assert_allclose(actual[2], den, atol=1e-14, rtol=0)


def test_each_positive_has_its_own_u_denominator():
    ev, match = panel(), complete_matches()
    match.update(u=np.array([2, 3, 3, 4, 6, 7, 8]), offsets=np.array([0, 2, 4, 7]))
    scores = np.arange(9, dtype=float)[:, None]
    scores[:2, 0] = [2.5, 4.5]
    points, _, _ = matched_metrics(scores, ev, match, np.arange(11), np.ones((1, 11)))
    first_p = .5 / (.5 + 7 / 3)
    np.testing.assert_allclose(points[0, 0], (first_p + 1) / 2, atol=1e-15, rtol=0)


@pytest.mark.parametrize('fault', ['nan', 'zero_weight', 'bait', 'positive', 'offsets'])
def test_matched_invalid_inputs_fail(fault):
    ev, match = panel(), complete_matches()
    scores = np.ones((9, 2))
    if fault == 'nan':
        scores[0, 0] = np.nan
    elif fault == 'zero_weight':
        ev['num'][2] = 0
    elif fault == 'bait':
        ev['a'][2] = 6
    elif fault == 'positive':
        ev['positive'][2] = True
    else:
        match['offsets'][-1] = 8
    with pytest.raises(ValueError):
        matched_metrics(scores, ev, match, np.arange(11), np.ones((1, 11)))


def test_empty_matching_is_inconclusive_not_zero_effect():
    ev = panel()
    match = {'p': np.array([], int), 'u': np.array([], int), 'offsets': np.array([0]), 'balance': np.empty((0, 4))}
    points, total, mass = matched_metrics(np.ones((9, 2)), ev, match, np.arange(11), np.ones((5, 11)))
    assert points.shape == (0, 2) and not total.any() and not mass.any()
    census = match_census(ev, match, np.arange(11), CFG['matching'])
    assert not census['adequate_support'] and census['retained_P'] == 0
    assert restricted_queries(ev, match) == []


def flag_fixture():
    cell = {'half_macro_difference': .001, 'anchor': {'shuffle_kmer3': {'ci95': [.55, .65]}},
            'anchor_deltas': {'kmer3_minus_shuffle': {'point': .03, 'ci95': [.01, .05]}}, 'matched': {}}
    for tier in CFG['matching']['tiers']:
        cell['matched'][tier] = {'adequate_support': True, 'scores': {'pair_linear': {'ci95': [.6, .7]}},
            'deltas': {c: {'point': .03, 'ci95': [.01, .05]} for c in CFG['decision']['matched_controls']}}
    return {c: deepcopy(cell) for c in CFG['cells']}


def test_flags_require_both_cells_and_all_controls():
    cells = flag_fixture()
    flags = diagnostic_flags(cells, CFG)
    assert flags['order_free_recovery_supported'] and flags['material_native_order_increment_supported']
    assert all(flags['matched_incremental_ranking_supported'].values())
    cells['HCT116']['matched']['also_direct_similarity']['deltas']['pooled_cosine']['ci95'][0] = 0
    assert not diagnostic_flags(cells, CFG)['matched_incremental_ranking_supported']['also_direct_similarity']
    cells['293T']['anchor_deltas']['kmer3_minus_shuffle']['point'] = .0199
    assert not diagnostic_flags(cells, CFG)['material_native_order_increment_supported']


def test_mc_instability_and_missing_support_fail_closed():
    cells = flag_fixture()
    cells['293T']['half_macro_difference'] = .01001
    cells['HCT116']['matched']['composition_length'] = {'adequate_support': False}
    flags = diagnostic_flags(cells, CFG)
    assert not flags['order_free_recovery_supported'] and not flags['material_native_order_increment_supported']
    assert not flags['matched_incremental_ranking_supported']['composition_length']


@pytest.mark.parametrize('key', ['protected_access', 'development_access', 'new_source_acquisition', 'fresh_validation'])
def test_scope_flags_cannot_be_broadened(tmp_path, key):
    cfg = deepcopy(CFG)
    cfg[key] = True
    path = tmp_path / io.CONFIG
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(RuntimeError, match='boundary'):
        io.config(tmp_path)


def test_runtime_requires_container(monkeypatch):
    monkeypatch.delenv('APPTAINER_CONTAINER', raising=False)
    with pytest.raises(RuntimeError, match='Apptainer'):
        io.runtime()


def test_array_outputs_refuse_overwrite(tmp_path):
    p = tmp_path / 'array.npy'
    io.save_numpy(p, np.array([1]))
    with pytest.raises(RuntimeError):
        io.save_numpy(p, np.array([2]))
    np.testing.assert_array_equal(np.load(p), [1])
    z = tmp_path / 'table.npz'
    io.save_npz(z, value=np.array([1]))
    with pytest.raises(RuntimeError):
        io.save_npz(z, value=np.array([2]))
