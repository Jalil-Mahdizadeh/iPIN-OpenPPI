"""Independent counter/direct-comparison audit; same author, not peer review."""

from collections import Counter
import hashlib
from pathlib import Path

import numpy as np

from ipin_openppi.external_bioplex import data as bio
from ipin_openppi.external_bioplex.validation import reference_queries
from ipin_openppi.homology_source import data as hio
from ipin_openppi.homology_source.validation import check_interval, direct_metrics
from ipin_openppi.partner_specificity import data as pio
from . import data as io


def reference_shuffle(sequence, endpoint, salt, replicates):
    alphabet = 'ACDEFGHIKLMNPQRSTVWYX'
    mapped = [c if c in alphabet else 'X' for c in sequence]
    base = sorted(mapped, key=alphabet.index)
    sums = np.zeros((2, 9261))
    for r in range(replicates):
        digest = hashlib.sha256((':'.join([salt, endpoint, str(r)])).encode()).digest()
        rng = np.random.Generator(np.random.PCG64DXSM(int.from_bytes(digest[:16], byteorder='big')))
        shuffled = ''.join(base[j] for j in rng.permutation(len(base)))
        assert Counter(shuffled) == Counter(mapped)
        counts = Counter(shuffled[k:k + 3] for k in range(len(shuffled) - 2))
        norm = sum(v**2 for v in counts.values()) ** .5
        for word, count in counts.items():
            index = sum(alphabet.index(c) * 21 ** (2 - k) for k, c in enumerate(word))
            sums[int(r >= replicates // 2), index] += count / norm
    return sums * (2 / replicates)


def reference_matches(ev, counts, lengths, old, cfg):
    out = {tier: {'p': [], 'offsets': [0], 'u': [], 'balance': []} for tier in cfg['tiers']}
    for anchor, positives, partners, unlabeled, alternatives in reference_queries(ev):
        for p, partner in zip(positives, partners):
            # Compute TV from integer count cross-products, not saved frequencies.
            numerator = np.abs(counts[partner] * lengths[alternatives, None] - counts[alternatives] * lengths[partner]).sum(axis=1)
            tv = numerator / (2 * lengths[partner] * lengths[alternatives])
            ratio = np.exp(np.abs(np.log(lengths[partner]) - np.log(lengths[alternatives])))
            differences = [np.abs(old[name][p] - old[name][unlabeled]) for name in ('kmer3_cosine', 'pooled_cosine')]
            base = (tv <= .10 + 1e-12) & (ratio <= 1.25 + 1e-12)
            masks = [base, base & (differences[0] <= .01 + 1e-12) & (differences[1] <= .01 + 1e-12)]
            for tier, mask in zip(cfg['tiers'], masks):
                if np.count_nonzero(mask) < 5:
                    continue
                record = out[tier]
                record['p'].append(p)
                record['u'].extend(unlabeled[mask])
                record['offsets'].append(len(record['u']))
                record['balance'].extend(np.column_stack((ratio[mask], tv[mask], differences[0][mask], differences[1][mask])))
    for item in out.values():
        for key in ('p', 'u', 'offsets'):
            item[key] = np.array(item[key], dtype=np.int64)
        item['balance'] = np.array(item['balance'], dtype=np.float64).reshape(-1, 4)
    return out


def reference_matched(scores, ev, match, component, draws):
    """Include a unit-multiplier draw for the point, then explicit per-bait ratios."""
    multi = np.vstack((np.ones((1, draws.shape[1])), draws)).astype(float)
    numerator = np.zeros((len(multi), scores.shape[1]))
    denominator = np.zeros(len(multi))
    all_points = []
    for anchor in sorted(set(ev['a'][match['p']].tolist())):
        means, pweights = [], []
        for j, p in enumerate(match['p']):
            if ev['a'][p] != anchor:
                continue
            u = match['u'][match['offsets'][j]:match['offsets'][j + 1]]
            credit = np.sign(scores[p] - scores[u]) * .5 + .5
            uc = component[ev['b'][u]]
            w = ev['num'][u] / ev['den'][u]
            resampled = np.stack([w * np.array([1 if c == component[anchor] else row[c] for c in uc]) for row in multi])
            den = resampled.sum(axis=1)
            mean = np.divide(np.einsum('ru,uk->rk', resampled, credit), den[:, None],
                             out=np.zeros((len(multi), scores.shape[1])), where=den[:, None] > 0)
            pc = component[ev['b'][p]]
            pw = np.ones(len(multi)) if pc == component[anchor] else multi[:, pc].copy()
            pw[den == 0] = 0
            means.append(mean)
            pweights.append(pw)
        pw = np.stack(pweights)
        pmass = pw.sum(axis=0)
        av = np.divide(np.einsum('prk,pr->rk', np.stack(means), pw), pmass[:, None],
                       out=np.zeros((len(multi), scores.shape[1])), where=pmass[:, None] > 0)
        am = multi[:, component[anchor]] * (pmass > 0)
        numerator += am[:, None] * av
        denominator += am
        all_points.append(av[0])
    return np.array(all_points).reshape(-1, scores.shape[1]), numerator[1:], denominator[1:]


def validate(root):
    cfg = io.verify_freeze(root)
    if (root / io.VALID / 'REFERENCE_VALIDATION.json').exists():
        raise RuntimeError('reference evidence already recorded')
    for name in ('COMPUTATION_COMPLETE.json', 'RESULTS.json'):
        io.verify_records(root, io.read_json(root / io.RESULT / name)['artifacts'])
    meta = io.read_json(root / pio.GENERATED / 'endpoint_metadata.json')
    data = hio.parent_data(root)
    alphabet = 'ACDEFGHIKLMNPQRSTVWYX'
    counters = [Counter(c if c in alphabet else 'X' for c in s) for s in meta['sequences']]
    counts = np.array([[counter[a] for a in alphabet] for counter in counters])
    np.testing.assert_array_equal(counts.sum(axis=1), data['length'])
    freq = counts / data['length'][:, None]
    np.testing.assert_allclose(np.load(root / io.RUN / 'frequencies.npy', allow_pickle=False), freq, atol=1e-12, rtol=0)
    halves = [np.load(root / io.RUN / f'shuffle_half_{h}.npy', mmap_mode='r', allow_pickle=False) for h in ('a', 'b')]
    for half in halves:
        assert half.dtype == np.float64 and half.shape == (11900, 9261)
        assert np.isfinite(half).all() and (half >= 0).all()
        assert (np.linalg.norm(half, axis=1) <= 1 + 1e-12).all()
    sample = np.unique(np.linspace(0, len(freq) - 1, cfg['runtime']['reference_endpoint_count'], dtype=int))
    for i in sample:
        ref = reference_shuffle(meta['sequences'][i], meta['endpoints'][i], cfg['shuffle']['salt'], 64)
        for j in range(2):
            np.testing.assert_allclose(halves[j][i], ref[j], atol=1e-12, rtol=0)
    print({'reference_shuffle_endpoints': len(sample), 'permutations_checked': len(sample) * 64}, flush=True)
    results = io.read_json(root / io.RESULT / 'RESULTS.json')
    prepared = io.read_json(root / io.RESULT / 'COMPUTATION_COMPLETE.json')
    draws = np.load(root / cfg['bootstrap']['source'], allow_pickle=False)
    expected_draws = np.random.Generator(np.random.PCG64DXSM(20260917)).poisson(1, draws.shape).astype(np.int16)
    np.testing.assert_array_equal(draws, expected_draws)
    score_values, comparisons, maximum_error = 0, 0, 0.
    for cell in cfg['cells']:
        boot = io.load(root / io.RUN / f'bootstrap_{cell}.npz')
        outcome = results['cells'][cell]
        points, credits, at, qt = {}, {}, {}, {}
        matched_points = {tier: [] for tier in cfg['matching']['tiers']}
        support_points = {tier: [] for tier in cfg['matching']['tiers']}
        mt = {tier: 0 for tier in cfg['matching']['tiers']}
        for fold in cfg['folds']:
            ev = io.load(root / bio.RUN / f'panel_{cell}_{fold}.npz')
            old_table = io.load(root / bio.RUN / f'scores_{cell}_{fold}.npz')
            old = dict(zip(old_table['columns'].tolist(), old_table['scores'].T))
            scored = io.load(root / io.RUN / f'scores_{cell}_{fold}.npz')
            assert scored['columns'].tolist() == cfg['new_scores']
            for start in range(0, len(ev['a']), 256):
                stop = start + 256
                a, b = ev['a'][start:stop], ev['b'][start:stop]
                aa = (counts[a] * counts[b]).sum(axis=1) / (np.sqrt((counts[a]**2).sum(axis=1)) * np.sqrt((counts[b]**2).sum(axis=1)))
                left = (halves[0][a] + halves[1][a]) / 2
                right = (halves[0][b] + halves[1][b]) / 2
                shuffle = (left * right).sum(axis=1)
                ref = np.column_stack((aa, shuffle, old['kmer3_cosine'][start:stop] - shuffle,
                    (halves[0][a] * halves[0][b]).sum(axis=1), (halves[1][a] * halves[1][b]).sum(axis=1)))
                maximum_error = max(maximum_error, float(np.abs(ref - scored['scores'][start:stop]).max()))
                np.testing.assert_allclose(ref, scored['scores'][start:stop], atol=1e-12, rtol=0)
                score_values += ref.size
            values = {**old, **dict(zip(scored['columns'].tolist(), scored['scores'].T))}
            queries = reference_queries(ev)
            weight = ev['num'].astype(float) / ev['den']
            for name in cfg['scores'] + ['shuffle_half_a', 'shuffle_half_b']:
                point, total, mass = direct_metrics(values[name], queries, weight, data['component'], draws[:16])
                points.setdefault(name, []).append(point)
                np.testing.assert_allclose(point.mean(), outcome['folds'][fold]['anchor'][name], atol=1e-12, rtol=0)
                q = ev['quartet_rows']
                delta = (values[name][q[:, 0]] - values[name][q[:, 2]]) + (values[name][q[:, 1]] - values[name][q[:, 3]])
                credit = np.where(np.abs(delta) <= 1e-6, .5, np.where(delta > 0, 1., 0.))
                credits.setdefault(name, []).append(credit)
                if name not in cfg['scores']:
                    continue
                at[name] = at.get(name, 0) + np.stack((total, mass))
                qnum, qden = np.zeros(2000), np.zeros(2000)
                for value, endpoints in zip(credit, ev['quartet_endpoints']):
                    w = np.ones(2000)
                    for c in set(data['component'][endpoints].tolist()):
                        w *= draws[:, c]
                    qnum += value * w
                    qden += w
                qt[name] = qt.get(name, 0) + np.stack((qnum, qden))
            reference = reference_matches(ev, counts, data['length'], old, cfg['matching'])
            matrix = np.column_stack([values[k] for k in cfg['scores']])
            for tier, expected in reference.items():
                actual = io.load(root / io.RUN / f'matches_{tier}_{cell}_{fold}.npz')
                for key in ('p', 'offsets', 'u'):
                    np.testing.assert_array_equal(actual[key], expected[key])
                np.testing.assert_allclose(actual['balance'], expected['balance'], atol=1e-12, rtol=0)
                comparisons += len(expected['u'])
                census = prepared['cells'][cell][fold]['tiers'][tier]
                anchors = np.unique(ev['a'][expected['p']])
                assert census['retained_P'] == len(expected['p']) and census['anchors'] == len(anchors)
                assert census['anchor_components'] == len(np.unique(data['component'][anchors]))
                assert census['comparisons'] == len(expected['u'])
                assert census['distinct_U_rows'] == len(np.unique(expected['u']))
                adequate = len(expected['p']) >= 100 and len(anchors) >= 50 and len(np.unique(data['component'][anchors])) >= 30
                assert census['adequate_support'] == adequate
                for j, key in enumerate(('partner_length_ratio', 'partner_composition_TV', 'kmer3_difference', 'pooled_difference')):
                    if len(expected['u']):
                        np.testing.assert_allclose(census['balance_quantiles_50_90_100'][key], np.percentile(expected['balance'][:, j], [50, 90, 100]), atol=1e-12, rtol=0)
                point, total, mass = reference_matched(matrix, ev, expected, data['component'], draws[:16])
                matched_points[tier].append(point)
                mt[tier] = mt[tier] + np.stack((total.T, np.broadcast_to(mass, total.T.shape)))
                restricted = []
                for a, p, pp, u, up in queries:
                    mask = np.isin(p, expected['p'])
                    if mask.any():
                        restricted.append((a, p[mask], pp[mask], u, up))
                refpoints = np.column_stack([direct_metrics(values[k], restricted, weight, data['component'], None)[0] for k in cfg['scores']])
                support_points[tier].append(refpoints)
                for j, name in enumerate(cfg['scores']):
                    if len(point):
                        np.testing.assert_allclose(point[:, j].mean(), outcome['folds'][fold]['matched'][tier]['macro'][name], atol=1e-12, rtol=0)
                        np.testing.assert_allclose(refpoints[:, j].mean(), outcome['folds'][fold]['matched'][tier]['same_support_unmatched_macro'][name], atol=1e-12, rtol=0)
            print({'reference_validated': cell, 'fold': fold}, flush=True)
        macro = {k: np.concatenate(v).mean() for k, v in points.items()}
        qmacro = {k: np.concatenate(v).mean() for k, v in credits.items()}
        ab, qb = {}, {}
        for name in cfg['scores']:
            np.testing.assert_allclose(boot['anchor_' + name][:, :16], at[name], atol=1e-8, rtol=0)
            np.testing.assert_allclose(boot['quartet_' + name], qt[name], atol=1e-8, rtol=0)
            for prefix, mean, ratios in [('anchor', macro, ab), ('quartet', qmacro, qb)]:
                num, den = boot[prefix + '_' + name]
                ratios[name] = np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0)
                np.testing.assert_allclose(outcome[prefix][name]['point'], mean[name], atol=1e-12, rtol=0)
                check_interval(ratios[name], outcome[prefix][name])
        for key, a, b in [('kmer3_minus_shuffle', 'kmer3_cosine', 'shuffle_kmer3'), ('pair_minus_aac', 'pair_linear', 'aac_cosine'),
                          ('pair_minus_shuffle', 'pair_linear', 'shuffle_kmer3'), ('shuffle_minus_aac', 'shuffle_kmer3', 'aac_cosine')]:
            for prefix, mean, ratios in [('anchor', macro, ab), ('quartet', qmacro, qb)]:
                rec = outcome[prefix + '_deltas'][key]
                np.testing.assert_allclose(rec['point'], mean[a] - mean[b], atol=1e-12, rtol=0)
                check_interval(ratios[a] - ratios[b], rec)
        for name in ('shuffle_half_a', 'shuffle_half_b'):
            np.testing.assert_allclose(outcome['half_anchor_macro'][name], macro[name], atol=1e-12, rtol=0)
        np.testing.assert_allclose(outcome['half_macro_difference'], abs(macro['shuffle_half_a'] - macro['shuffle_half_b']), atol=1e-12, rtol=0)
        for tier in cfg['matching']['tiers']:
            m = outcome['matched'][tier]
            combined = np.concatenate(matched_points[tier])
            refcombined = np.concatenate(support_points[tier])
            assert m['anchors'] == len(combined)
            support = [f['tiers'][tier] for f in prepared['cells'][cell]]
            assert m['support_by_fold'] == support
            assert m['adequate_support'] == all(s['adequate_support'] for s in support)
            assert m['retained_P'] == sum(s['retained_P'] for s in support)
            assert m['comparisons'] == sum(s['comparisons'] for s in support)
            mb = {}
            for j, name in enumerate(cfg['scores']):
                saved = boot[f'matched_{tier}_{name}']
                np.testing.assert_allclose(saved[:, :16], mt[tier][:, j], atol=1e-8, rtol=0)
                mb[name] = np.divide(saved[0], saved[1], out=np.full(2000, np.nan), where=saved[1] > 0)
                check_interval(mb[name], m['scores'][name])
                if len(combined):
                    np.testing.assert_allclose(m['scores'][name]['point'], combined[:, j].mean(), atol=1e-12, rtol=0)
                    np.testing.assert_allclose(m['same_support_unmatched_macro'][name], refcombined[:, j].mean(), atol=1e-12, rtol=0)
                else:
                    assert m['scores'][name]['point'] is None and m['same_support_unmatched_macro'][name] is None
            for k, rec in m['deltas'].items():
                check_interval(mb['pair_linear'] - mb[k], rec)
                if len(combined):
                    np.testing.assert_allclose(rec['point'], m['scores']['pair_linear']['point'] - m['scores'][k]['point'], atol=1e-12, rtol=0)
    # Independent flag algebra, not the production classifier.
    values = list(results['cells'].values())
    stable = max(c['half_macro_difference'] for c in values) <= .01
    lower = lambda rec, x: rec['ci95'] is not None and rec['ci95'][0] > x
    flags = results['flags']
    assert flags['shuffle_half_stability'] == stable
    assert flags['order_free_recovery_supported'] == (stable and all(lower(c['anchor']['shuffle_kmer3'], .5) for c in values))
    assert flags['material_native_order_increment_supported'] == (stable and all(
        c['anchor_deltas']['kmer3_minus_shuffle']['point'] >= .02 and lower(c['anchor_deltas']['kmer3_minus_shuffle'], 0) for c in values))
    for tier in cfg['matching']['tiers']:
        passed = True
        for c in values:
            m = c['matched'][tier]
            passed = passed and m['adequate_support'] and lower(m['scores']['pair_linear'], .5) and all(
                rec['point'] >= .02 and lower(rec, 0) for rec in m['deltas'].values())
        assert flags['matched_incremental_ranking_supported'][tier] == passed
    closure_records = io.prior_closures(root)
    out = {'created_utc': io.now(), 'passed': True, 'same_author_numerical_audit_not_external_review': True,
           'all_public_AAC_vectors_checked': len(freq), 'shuffle_endpoints_reconstructed': len(sample),
           'shuffle_permutations_reconstructed': len(sample) * 64, 'all_new_score_values_checked': score_values,
           'maximum_score_absolute_error': maximum_error, 'all_matched_comparisons_checked': comparisons,
           'all_points_intervals_and_flags_checked': True, 'global_and_matched_bootstrap_draws_per_cell': 16,
           'quartet_bootstrap_draws_per_cell': 2000, 'prior_three_closures_unchanged': closure_records,
           'new_fits': 0, 'protected_access': False}
    io.write_json(root / io.VALID / 'REFERENCE_VALIDATION.json', out)
    return out


def close(root):
    io.verify_freeze(root)
    if (root / io.RESULT / 'ARTIFACT_REGISTRY.json').exists():
        raise RuntimeError('diagnostic closure already recorded')
    assert io.read_json(root / io.VALID / 'REFERENCE_VALIDATION.json')['passed'] is True
    for name in ('COMPUTATION_COMPLETE.json', 'RESULTS.json'):
        io.verify_records(root, io.read_json(root / io.RESULT / name)['artifacts'])
    prior = io.prior_closures(root)
    before = bio.passed_tests(root / io.VALID / 'unit_tests_pre_execution.xml')
    after = bio.passed_tests(root / io.VALID / 'unit_tests_post_execution.xml')
    assert before == after
    paths = [root / p for p in (io.CONFIG, 'docs/protocols/COMPOSITION_ORDER_CHALLENGE_v1.md',
        'governance/decisions/DEC-0049-authorize-composition-order-diagnostic.md',
        'docs/reports/m1/M1_Composition_Order_Challenge_v1.md', 'governance/PROJECT_STATUS_v49.md',
        'governance/gates/gate_status_v49.yaml', 'scripts/model/run_composition_order_challenge_v1.py',
        'tests/unit/test_composition_order.py')]
    paths += sorted((root / 'src/ipin_openppi/composition_order').glob('*.py'))
    paths += sorted((root / io.RESULT).glob('*.json'))
    paths += sorted(p for p in (root / io.VALID).iterdir() if p.is_file())
    io.write_json(root / io.RESULT / 'ARTIFACT_REGISTRY.json', {
        'created_utc': io.now(), 'protocol_id': io.ID, 'execution_complete': True,
        'numerical_validation_passed': True, 'CPU_tests_passed': len(after),
        'prior_three_closures_unchanged': prior, 'fresh_validation': False,
        'protected_access': False, 'new_fits': 0, 'new_embeddings': 0,
        'publication_authorized_by_user': True, 'large_arrays_and_pair_scores_remain_local': True,
        'artifacts': [io.artifact(root, p) for p in paths]})
    return {'closed': True, 'artifacts': len(paths), 'CPU_tests': len(after)}
