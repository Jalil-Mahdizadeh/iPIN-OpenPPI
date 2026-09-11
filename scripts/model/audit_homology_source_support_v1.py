#!/usr/bin/env python3
"""Supporting arithmetic audit; no new fits, candidate panels or decision rules.

Written after execution freeze. Edge counts are label-free descriptive context;
readout mode verifies the already specified strata, support and decision logic.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from ipin_openppi.homology_source import data as io
from ipin_openppi.homology_source.validation import direct_queries, direct_metrics, load
from ipin_openppi.partner_specificity import data as parent
from ipin_openppi.stage1.support import sha256_file


def edges(root):
    data = io.parent_data(root)
    sets = {k: set() for k in (20, 30, 40)}
    with (root / io.RUN / 'mmseqs/alignments.tsv').open() as handle:
        for line in handle:
            f = line.split()
            a, b, mismatch, columns, qs, qe, qlen, ts, te, tlen = map(int, f[:10])
            qspan, tspan = qe - qs + 1, te - ts + 1
            if a == b or min(qspan, tspan) < 80 or 5 * qspan < qlen or 5 * tspan < tlen or float(f[10]) > .001:
                continue
            identical = qspan + tspan - columns - mismatch
            for k in sets:
                if 100 * identical >= k * columns:
                    sets[k].add(tuple(sorted((a, b))))
    counts = {}
    for k, pairs in sets.items():
        aa = np.array([p[0] for p in pairs], dtype=int)
        bb = np.array([p[1] for p in pairs], dtype=int)
        per_fold, after_purge = [], []
        for fold in range(3):
            held = data['fold'] == fold
            fit = load(root / io.RUN / f'plan_purged20_{fold}.npz')['fit_endpoints']
            per_fold.append(int(np.sum(held[aa] ^ held[bb])))
            after_purge.append(int(np.sum((held[aa] & fit[bb]) | (held[bb] & fit[aa]))))
        assert after_purge == [0, 0, 0]
        counts[str(k)] = {'undirected_edges': len(pairs),
                         'cross_original_components': int(np.sum(data['component'][aa] != data['component'][bb])),
                         'cross_original_folds': int(np.sum(data['fold'][aa] != data['fold'][bb])),
                         'cross_fit_evaluation_per_fold': per_fold,
                         'cross_fit_evaluation_after_purge': after_purge}
    out = {'created_utc': io.now(), 'timing': 'supplementary_label_free_context_after_execution_freeze',
           'all_use_minimum_span_80_and_both_coverage_20pct_and_evalue_1e_3': True,
           'counts': counts, 'scientific_gate_or_fitting_changes': False,
           'script_sha256': sha256_file(Path(__file__))}
    io.write_json(root / io.VALID / 'HOMOLOGY_EDGE_AUDIT.json', out)
    return out


def readout(root):
    cfg = io.config(root)
    data = io.parent_data(root)
    result = io.read_json(root / io.RESULT / 'RESULTS.json')
    source = np.load(root / io.RUN / 'public_positive_source_bits.npy', allow_pickle=False)
    feasible = io.read_json(root / io.RESULT / 'FEASIBILITY.json')
    local = np.load(root / io.RUN / 'similarity_local.npy', mmap_mode='r', allow_pickle=False)
    rows = []
    for fold in range(3):
        ev = load(root / parent.GENERATED / f'evaluation_fold_{fold}.npz')
        plan = load(root / io.RUN / f'plan_union_{fold}.npz')
        scored = load(root / io.RUN / f'scores_union_{fold}.npz')
        names = scored['columns'].tolist()
        w = ev['num'].astype(np.float64) / ev['den']
        endpoint = ~np.any(local[:, data['fold'] != fold] > 0, axis=1)
        nohit = endpoint[ev['a']] & endpoint[ev['b']]
        np.testing.assert_array_equal(nohit, plan['no_hit_pair'])
        for stratum in ['source_1', 'source_2', 'source_3', 'no_detected_hit']:
            keep = nohit.copy() if stratum == 'no_detected_hit' else np.ones(len(ev['a']), bool)
            if stratum != 'no_detected_hit':
                keep[ev['positive']] = source[ev['parent_row'][ev['positive']]] == int(stratum[-1])
            queries = direct_queries(ev['a'][keep], ev['b'][keep], ev['positive'][keep])
            points = {n: direct_metrics(scored['scores'][keep, names.index(n)], queries, w[keep], data['component'])[0]
                      for n in cfg['models'] + cfg['controls']}
            rows.append({'fold': fold, 'stratum': stratum, 'anchors': len(queries),
                         'components': len(set(data['component'][q[0]] for q in queries)),
                         'P': int((keep & ev['positive']).sum()), 'U': int((keep & ~ev['positive']).sum()),
                         'points': points})
    for stratum, actual in result['arms']['union']['stratum_summary'].items():
        select = [r for r in rows if r['stratum'] == stratum]
        for key in ('anchors', 'components', 'P', 'U'):
            assert sum(r[key] for r in select) == actual[key]
        assert actual['supported'] == (actual['anchors'] >= 50 and actual['components'] >= 20)
        if actual['supported']:
            for name in actual['macro']:
                np.testing.assert_allclose(np.concatenate([r['points'][name] for r in select]).mean(), actual['macro'][name], atol=1e-10, rtol=0)
        else:
            assert actual['macro'] == {}
    for arm, r in result['arms'].items():
        expected_checks = {
            'margin_over_strongest': r['macro']['pair_linear'] - max(r['macro'][c] for c in ['endpoint_linear'] + cfg['controls']) >= .02,
            'all_control_paired_lower_positive': all(d['ci95'] is not None and d['ci95'][0] > 0 for d in r['deltas'].values()),
            'each_fold_beats_linear_unary': all(f['macro']['pair_linear'] > f['macro']['endpoint_linear'] for f in r['folds']),
            'each_seed_beats_linear_unary': all(r['macro'][f'pair_linear__{s}'] > r['macro'][f'endpoint_linear__{s}'] for s in parent.config(root)['training']['seeds'])}
        assert r['checks'] == expected_checks
        assert r['anchor_signal_survives'] == all(expected_checks.values())
        q = r['quartet']
        expected_q = {'feasible': arm in feasible['quartet_feasible_arms'],
                      'pair_lower_above_half': q['pair_interval']['ci95'] is not None and q['pair_interval']['ci95'][0] > .5,
                      'all_transfer_paired_lower_positive': all(d['ci95'] is not None and d['ci95'][0] > 0 for d in q['deltas'].values())}
        assert q['checks'] == expected_q and q['signal_survives'] == all(expected_q.values())
    overall = len(result['arms']) == 4 and all(r['anchor_signal_survives'] and r['quartet']['signal_survives'] for r in result['arms'].values())
    assert result['all_challenges_survived'] == overall
    out = {'created_utc': io.now(), 'passed': True, 'all_descriptive_strata_and_no_hit_masks_checked': True,
           'all_frozen_decision_rules_checked': True, 'no_new_estimand_or_model_selection': True,
           'timing': 'supporting_arithmetic_only_written_after_execution_freeze',
           'script_sha256': sha256_file(Path(__file__))}
    io.write_json(root / io.VALID / 'SUPPORTING_READOUT_AUDIT.json', out)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['edges', 'readout'])
    args = parser.parse_args()
    print(json.dumps(globals()[args.action](Path.cwd()), indent=2))
