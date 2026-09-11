"""A single frozen execution: features and matches, then explanatory readout."""

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from ipin_openppi.external_bioplex import data as bio
from ipin_openppi.external_bioplex.semantics import directed_queries
from ipin_openppi.homology_source import data as hio
from ipin_openppi.homology_source.semantics import finite_ratio, summary_interval
from ipin_openppi.partner_specificity import data as pio
from ipin_openppi.partner_specificity.semantics import (
    Query, anchor_points, bootstrap_anchor_totals, quartet_credit, quartet_bootstrap_totals,
)
from . import data as io
from .semantics import frequencies, shuffle_means, row_dot, build_matches, matched_metrics, diagnostic_flags


def score_map(root, cell, fold):
    old = io.load(root / bio.RUN / f'scores_{cell}_{fold}.npz')
    return dict(zip(old['columns'].tolist(), old['scores'].T, strict=True))


def match_census(ev, match, component, cfg):
    queries = directed_queries(ev['a'], ev['b'], ev['positive'])
    anchors = np.unique(ev['a'][match['p']])
    rankable_p = sum(len(q.positive) for q in queries)
    out = {'panel_P': int(ev['positive'].sum()), 'rankable_P': rankable_p,
           'parent_anchors': len(queries), 'retained_P': len(match['p']), 'anchors': len(anchors),
           'anchor_components': len(np.unique(component[anchors])),
           'comparisons': len(match['u']), 'distinct_U_rows': len(np.unique(match['u'])),
           'retained_P_fraction': len(match['p']) / rankable_p if rankable_p else None,
           'retained_anchor_fraction': len(anchors) / len(queries) if queries else None,
           'balance_quantiles_50_90_100': {}}
    for j, name in enumerate(('partner_length_ratio', 'partner_composition_TV', 'kmer3_difference', 'pooled_difference')):
        out['balance_quantiles_50_90_100'][name] = np.percentile(match['balance'][:, j], [50, 90, 100]).tolist() if len(match['u']) else None
    out['adequate_support'] = (out['retained_P'] >= cfg['minimum_positives_per_fold']
        and out['anchors'] >= cfg['minimum_anchors_per_fold']
        and out['anchor_components'] >= cfg['minimum_anchor_components_per_fold'])
    return out


def compute(root):
    cfg = io.verify_freeze(root)
    if (root / io.RUN).exists() or (root / io.RESULT / 'COMPUTATION_COMPLETE.json').exists():
        raise RuntimeError('existing diagnostic computation cannot be replaced')
    started = time.monotonic()
    meta = io.read_json(root / pio.GENERATED / 'endpoint_metadata.json')
    data = hio.parent_data(root)
    n = len(meta['endpoints'])
    if n != 11900 or len(set(meta['endpoints'])) != n or len(meta['sequences']) != n:
        raise RuntimeError('public endpoint identity census mismatch')
    for i, (sha, sequence) in enumerate(zip(meta['endpoints'], meta['sequences'], strict=True)):
        if hashlib.sha256(sequence.encode()).hexdigest() != sha or len(sequence) != data['length'][i]:
            raise RuntimeError('public sequence identity mismatch')
    freq = frequencies(meta['sequences'])
    first, second = np.empty((n, 21**3)), np.empty((n, 21**3))
    for i, (sha, sequence) in enumerate(zip(meta['endpoints'], meta['sequences'], strict=True)):
        first[i], second[i] = shuffle_means(sequence, sha, cfg['shuffle']['salt'], cfg['shuffle']['replicates_per_endpoint'])
        if (i + 1) % 1000 == 0:
            print({'shuffled_endpoints': i + 1}, flush=True)
    paths = []
    for filename, array in [('frequencies.npy', freq), ('shuffle_half_a.npy', first), ('shuffle_half_b.npy', second)]:
        path = root / io.RUN / filename
        io.save_numpy(path, array)
        paths.append(path)
    mean = (first + second) / 2  # crucially NOT normalized again
    aac = freq / np.linalg.norm(freq, axis=1)[:, None]
    census, values = {}, 0
    for cell in cfg['cells']:
        census[cell] = []
        for fold in cfg['folds']:
            ev = io.load(root / bio.RUN / f'panel_{cell}_{fold}.npz')
            old = score_map(root, cell, fold)
            shuffled = row_dot(mean, ev['a'], ev['b'])
            columns = cfg['new_scores']
            scores = np.column_stack((row_dot(aac, ev['a'], ev['b']), shuffled,
                old['kmer3_cosine'] - shuffled, row_dot(first, ev['a'], ev['b']), row_dot(second, ev['a'], ev['b'])))
            if not np.isfinite(scores).all():
                raise RuntimeError('nonfinite diagnostic scores')
            path = root / io.RUN / f'scores_{cell}_{fold}.npz'
            io.save_npz(path, scores=scores, columns=np.array(columns))
            paths.append(path)
            values += scores.size
            matched = build_matches(ev, freq, data['length'], old, cfg['matching'])
            fold_census = {'fold': fold, 'tiers': {}}
            for tier, arrays in matched.items():
                fold_census['tiers'][tier] = match_census(ev, arrays, data['component'], cfg['matching'])
                path = root / io.RUN / f'matches_{tier}_{cell}_{fold}.npz'
                io.save_npz(path, **arrays)
                paths.append(path)
            census[cell].append(fold_census)
            print({'computed': cell, 'fold': fold, 'matched_P': {k: v['retained_P'] for k, v in fold_census['tiers'].items()}}, flush=True)
    out = {'created_utc': io.now(), 'public_endpoints': n, 'permutations': n * 64,
           'new_score_values': values, 'metrics_computed': False, 'cells': census,
           'new_fits': 0, 'new_embeddings': 0, 'elapsed_seconds': time.monotonic() - started,
           'artifacts': [io.artifact(root, p) for p in paths]}
    io.write_json(root / io.RESULT / 'COMPUTATION_COMPLETE.json', out)
    return {k: out[k] for k in ('public_endpoints', 'permutations', 'new_score_values', 'elapsed_seconds')}


def point_record(point, bootstrap):
    return {'point': float(point) if point is not None and np.isfinite(point) else None, **summary_interval(bootstrap)}


def restricted_queries(ev, matched):
    retained = set(matched['p'].tolist())
    out = []
    for q in directed_queries(ev['a'], ev['b'], ev['positive']):
        mask = np.array([p in retained for p in q.positive])
        if mask.any():
            out.append(Query(q.anchor, q.positive[mask], q.positive_partner[mask], q.unlabeled, q.unlabeled_partner))
    return out


def evaluate(root):
    cfg = io.verify_freeze(root)
    prepared = io.read_json(root / io.RESULT / 'COMPUTATION_COMPLETE.json')
    io.verify_records(root, prepared['artifacts'])
    if (root / io.RESULT / 'RESULTS.json').exists():
        raise RuntimeError('diagnostic readout already complete')
    data = hio.parent_data(root)
    draws = np.load(root / cfg['bootstrap']['source'], allow_pickle=False)
    if draws.shape != (2000, int(data['component'].max()) + 1):
        raise RuntimeError('component draw census mismatch')
    old_results = io.read_json(root / bio.RESULT / 'RESULTS.json')
    cells, paths = {}, []
    for cell in cfg['cells']:
        old_boot = io.load(root / bio.RUN / f'bootstrap_{cell}.npz')
        boot = {f'{prefix}_{name}': old_boot[f'{prefix}_{name}'] for prefix in ('anchor', 'quartet')
                for name in cfg['scores'][:4]}
        points, credits, folds = {}, {}, []
        mpoints = {tier: [] for tier in cfg['matching']['tiers']}
        samepoints = {tier: [] for tier in cfg['matching']['tiers']}
        for fold in cfg['folds']:
            ev = io.load(root / bio.RUN / f'panel_{cell}_{fold}.npz')
            old = score_map(root, cell, fold)
            new = io.load(root / io.RUN / f'scores_{cell}_{fold}.npz')
            values = {**old, **dict(zip(new['columns'].tolist(), new['scores'].T, strict=True))}
            queries = directed_queries(ev['a'], ev['b'], ev['positive'])
            weight = ev['num'].astype(float) / ev['den']
            fc = {'fold': fold, 'anchor': {}, 'matched': {}}
            for name in cfg['scores'] + ['shuffle_half_a', 'shuffle_half_b']:
                point = anchor_points(values[name], queries, weight)
                credit, _ = quartet_credit(values[name], ev['quartet_rows'], 1e-6)
                points.setdefault(name, []).append(point)
                credits.setdefault(name, []).append(credit)
                fc['anchor'][name] = float(point.mean())
                if name in cfg['new_scores'][:3]:
                    ab = np.stack(bootstrap_anchor_totals(values[name], queries, weight, data['component'], draws))
                    qb = np.stack(quartet_bootstrap_totals(credit, ev['quartet_endpoints'], data['component'], draws))
                    boot['anchor_' + name] = boot.get('anchor_' + name, 0) + ab
                    boot['quartet_' + name] = boot.get('quartet_' + name, 0) + qb
            matrix = np.column_stack([values[k] for k in cfg['scores']])
            for tier in cfg['matching']['tiers']:
                match = io.load(root / io.RUN / f'matches_{tier}_{cell}_{fold}.npz')
                point, total, mass = matched_metrics(matrix, ev, match, data['component'], draws)
                mpoints[tier].append(point)
                rq = restricted_queries(ev, match)
                ref = np.column_stack([anchor_points(values[k], rq, weight) for k in cfg['scores']])
                samepoints[tier].append(ref)
                means = point.mean(axis=0) if len(point) else np.full(len(cfg['scores']), np.nan)
                same = ref.mean(axis=0) if len(ref) else np.full(len(cfg['scores']), np.nan)
                fc['matched'][tier] = {'macro': {k: float(v) if np.isfinite(v) else None for k, v in zip(cfg['scores'], means)},
                    'same_support_unmatched_macro': {k: float(v) if np.isfinite(v) else None for k, v in zip(cfg['scores'], same)}}
                for j, name in enumerate(cfg['scores']):
                    key = f'matched_{tier}_{name}'
                    boot[key] = boot.get(key, 0) + np.stack((total[:, j], mass))
                print({'evaluated': cell, 'fold': fold, 'matched_tier': tier}, flush=True)
            folds.append(fc)
        macro = {k: float(np.concatenate(v).mean()) for k, v in points.items()}
        qmacro = {k: float(np.concatenate(v).mean()) for k, v in credits.items()}
        for name in cfg['scores'][:4]:
            np.testing.assert_allclose(macro[name], old_results['cells'][cell]['macro'][name], atol=1e-12, rtol=0)
            np.testing.assert_allclose(qmacro[name], old_results['cells'][cell]['quartet']['preference'][name], atol=1e-12, rtol=0)
        ratios = {key: finite_ratio(*value) for key, value in boot.items()}
        ab = {k: ratios['anchor_' + k] for k in cfg['scores']}
        qb = {k: ratios['quartet_' + k] for k in cfg['scores']}
        deltas = [('kmer3_minus_shuffle', 'kmer3_cosine', 'shuffle_kmer3'),
                  ('pair_minus_aac', 'pair_linear', 'aac_cosine'), ('pair_minus_shuffle', 'pair_linear', 'shuffle_kmer3'),
                  ('shuffle_minus_aac', 'shuffle_kmer3', 'aac_cosine')]
        out = {'anchor': {k: point_record(macro[k], ab[k]) for k in cfg['scores']},
               'quartet': {k: point_record(qmacro[k], qb[k]) for k in cfg['scores']},
               'anchor_deltas': {key: point_record(macro[a] - macro[b], ab[a] - ab[b]) for key, a, b in deltas},
               'quartet_deltas': {key: point_record(qmacro[a] - qmacro[b], qb[a] - qb[b]) for key, a, b in deltas},
               'half_anchor_macro': {k: macro[k] for k in ('shuffle_half_a', 'shuffle_half_b')},
               'half_macro_difference': abs(macro['shuffle_half_a'] - macro['shuffle_half_b']),
               'folds': folds, 'matched': {}}
        for tier in cfg['matching']['tiers']:
            p = np.concatenate(mpoints[tier])
            ref = np.concatenate(samepoints[tier])
            mp = dict(zip(cfg['scores'], p.mean(axis=0) if len(p) else [None] * len(cfg['scores'])))
            mb = {k: ratios[f'matched_{tier}_{k}'] for k in cfg['scores']}
            support = [f['tiers'][tier] for f in prepared['cells'][cell]]
            out['matched'][tier] = {'adequate_support': all(f['adequate_support'] for f in support),
                'anchors': len(p), 'retained_P': sum(f['retained_P'] for f in support),
                'comparisons': sum(f['comparisons'] for f in support), 'support_by_fold': support,
                'scores': {k: point_record(mp[k], mb[k]) for k in cfg['scores']},
                'deltas': {k: point_record(mp['pair_linear'] - mp[k] if len(p) else None,
                    mb['pair_linear'] - mb[k]) for k in cfg['decision']['matched_controls']},
                'same_support_unmatched_macro': {k: float(v) if v is not None else None for k, v in zip(cfg['scores'],
                    ref.mean(axis=0) if len(ref) else [None] * len(cfg['scores']))}}
        path = root / io.RUN / f'bootstrap_{cell}.npz'
        io.save_npz(path, **boot)
        paths.append(path)
        cells[cell] = out
    out = {'created_utc': io.now(), 'protocol_id': io.ID, 'cells': cells, 'flags': diagnostic_flags(cells, cfg),
           'fresh_validation': False, 'new_fits': 0, 'new_embeddings': 0, 'protected_access': False,
           'estimand': 'conditional_released_coassociation_P_versus_U_diagnostic',
           'artifacts': [io.artifact(root, p) for p in paths]}
    io.write_json(root / io.RESULT / 'RESULTS.json', out)
    return out['flags']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['register', 'freeze', 'compute', 'evaluate', 'validate', 'close'])
    phase = parser.parse_args().phase
    if phase in ('register', 'freeze'):
        function = getattr(io, phase)
    elif phase in ('validate', 'close'):
        from . import validation
        function = getattr(validation, phase)
    else:
        function = globals()[phase]
    print(json.dumps(function(Path.cwd()), indent=2))
