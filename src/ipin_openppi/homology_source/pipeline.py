"""Execute fixed-budget refits, exhaustive controls and paired challenge readouts."""

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

from ipin_openppi.partner_specificity import data as parent
from ipin_openppi.partner_specificity.pipeline import gpu_runtime
from ipin_openppi.partner_specificity.semantics import (
    anchor_points, bootstrap_anchor_totals, build_queries, normalize,
    quartet_bootstrap_totals, quartet_credit,
)
from ipin_openppi.stage1.support import atomic_numpy, atomic_npz, sha256_file
from . import data as io
from .semantics import finite_ratio, panel_mask, summary_interval


def arrays(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def digest(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def train(root):
    cfg = io.verify_freeze(root)
    if (root / io.RESULT / 'TRAINING_COMPLETE.json').exists():
        raise RuntimeError('training already complete')
    pcfg = parent.config(root)
    torch = gpu_runtime(pcfg)
    from ipin_openppi.partner_specificity.models import make_model
    data = io.parent_data(root)
    raw = np.load(root / parent.GENERATED / 'raw_public_embeddings.npy', allow_pickle=False)
    recipe = pcfg['training']
    arms = io.read_json(root / io.RESULT / 'FEASIBILITY.json')['feasible_arms']
    records, runs, start_all = [], [], time.monotonic()
    for arm in (a for a in arms if a != 'union'):
        for fold in range(3):
            plan = arrays(root / io.RUN / f'plan_{arm}_{fold}.npz')
            norm_path = root / io.RUN / f'normalization_{arm}_{fold}.npz'
            if norm_path.exists():
                raise RuntimeError('existing fit artifacts require operational review')
            normalized, mean, std = normalize(raw, plan['fit_endpoints'])
            atomic_npz(norm_path, mean=mean, std=std, fit_endpoints=np.flatnonzero(plan['fit_endpoints']))
            records.append(io.artifact(root, norm_path))
            x = torch.from_numpy(normalized).cuda()
            p_a = torch.from_numpy(data['p_a'][plan['p_rows']]).cuda()
            p_b = torch.from_numpy(data['p_b'][plan['p_rows']]).cuda()
            u_a, u_b = (torch.from_numpy(plan['u_' + side]).cuda() for side in ('a', 'b'))
            weight = plan['u_num'].astype(np.float64) / plan['u_den']
            mean_weight = float(weight.mean())
            w = torch.from_numpy(weight).cuda()
            n_p, n_u, batch = len(p_a), len(u_a), recipe['comparisons_per_batch']
            steps = math.ceil(n_u / batch) * recipe['complete_passes']
            warmup = max(1, math.ceil(steps * recipe['warmup_fraction']))
            for name in cfg['models']:
                for seed in recipe['seeds']:
                    run_id = f'{arm}_f{fold}_{name}_s{seed}'
                    path = root / io.RUN / f'{run_id}.pt'
                    if path.exists():
                        raise RuntimeError('refusing checkpoint overwrite')
                    model = make_model(name, seed).cuda()
                    opt = torch.optim.AdamW(model.parameters(), lr=recipe['learning_rate'],
                        betas=tuple(recipe['betas']), eps=recipe['epsilon'],
                        weight_decay=recipe['weight_decay'], foreach=False, fused=False)
                    step, logs, started = 0, [], time.monotonic()
                    for pass_index in range(1, recipe['complete_passes'] + 1):
                        rng = np.random.Generator(np.random.PCG64DXSM(seed + pass_index))
                        po, uo = rng.permutation(n_p), rng.permutation(n_u)
                        cycle = po[(np.arange(n_u) + pass_index - 1) % n_p]
                        numerator = torch.zeros((), device='cuda', dtype=torch.float64)
                        denominator = torch.zeros_like(numerator)
                        for start in range(0, n_u, batch):
                            if time.monotonic() - start_all > cfg['runtime']['gpu_hours_ceiling'] * 3600:
                                raise RuntimeError('GPU budget exceeded')
                            ip = torch.from_numpy(cycle[start:start + batch]).cuda()
                            iu = torch.from_numpy(uo[start:start + batch]).cuda()
                            opt.zero_grad(set_to_none=True)
                            per = torch.nn.functional.softplus(-(model(x[p_a[ip]], x[p_b[ip]]) - model(x[u_a[iu]], x[u_b[iu]])))
                            loss = ((w[iu] / mean_weight) * per.double()).mean()
                            if not torch.isfinite(loss):
                                raise FloatingPointError('nonfinite training loss')
                            loss.backward()
                            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), recipe['gradient_clip_norm'])
                            if not torch.isfinite(norm):
                                raise FloatingPointError('nonfinite gradient')
                            step += 1
                            if step <= warmup:
                                fraction = step / warmup
                            else:
                                floor = recipe['final_learning_rate_fraction']
                                fraction = floor + (1 - floor) * .5 * (1 + math.cos(math.pi * (step - warmup) / (steps - warmup)))
                            for group in opt.param_groups:
                                group['lr'] = recipe['learning_rate'] * fraction
                            opt.step()
                            numerator += (w[iu] * per.detach().double()).sum()
                            denominator += w[iu].sum()
                        logs.append({'pass': pass_index, 'steps': step, 'U_comparisons': n_u,
                                     'training_loss': float((numerator / denominator).cpu()),
                                     'order_hashes': {'p': digest(po), 'u': digest(uo)}})
                    if step != steps or not all(torch.isfinite(v).all() for v in model.parameters()):
                        raise RuntimeError('incomplete or nonfinite model')
                    checkpoint = {'state_dict': {k: v.detach().cpu() for k, v in model.state_dict().items()},
                                  'arm': arm, 'fold': fold, 'model': name, 'seed': seed,
                                  'execution_freeze_sha256': sha256_file(root / io.RESULT / 'EXECUTION_FREEZE.json')}
                    with path.open('xb') as handle:
                        torch.save(checkpoint, handle)
                    rec = {'arm': arm, 'fold': fold, 'model': name, 'seed': seed,
                           'fit_P': n_p, 'fit_U': n_u, 'monitors': logs,
                           'elapsed_seconds': time.monotonic() - started, 'checkpoint': io.artifact(root, path)}
                    io.write_json(path.with_suffix('.json'), rec)
                    runs.append(rec)
                    records.extend((rec['checkpoint'], io.artifact(root, path.with_suffix('.json'))))
                    print(json.dumps({k: rec[k] for k in ('arm', 'fold', 'model', 'seed', 'elapsed_seconds')}), flush=True)
    out = {'created_utc': io.now(), 'runs': runs, 'artifacts': records,
           'elapsed_seconds': time.monotonic() - start_all, 'new_holdout_scoring_performed': False,
           'expected_fits': 18 * len([a for a in arms if a != 'union'])}
    if len(runs) != out['expected_fits']:
        raise RuntimeError('missing fixed fits')
    io.write_json(root / io.RESULT / 'TRAINING_COMPLETE.json', out)
    return {'fits': len(runs), 'elapsed_seconds': out['elapsed_seconds']}


def exhaustive_transfer_gpu(similarity, a, b, p_a, p_b, batch=512):
    import torch
    if not len(p_a):
        raise ValueError('empty fitting P graph')
    sim = torch.from_numpy(np.array(similarity, dtype=np.float32)).cuda()
    pa, pb = torch.from_numpy(p_a).cuda(), torch.from_numpy(p_b).cuda()
    out = np.empty(len(a), dtype=np.float32)
    with torch.no_grad():
        for start in range(0, len(a), batch):
            aa, bb = (torch.from_numpy(v[start:start + batch]).cuda() for v in (a, b))
            forward = torch.minimum(sim[aa[:, None], pa], sim[bb[:, None], pb])
            reverse = torch.minimum(sim[aa[:, None], pb], sim[bb[:, None], pa])
            out[start:start + batch] = torch.maximum(forward, reverse).amax(dim=1).cpu().numpy()
    return out.astype(np.float64)


def score(root):
    cfg = io.verify_freeze(root)
    trained = io.read_json(root / io.RESULT / 'TRAINING_COMPLETE.json')
    io.verify_records(root, trained['artifacts'])
    if len(trained['runs']) != trained['expected_fits']:
        raise RuntimeError('all fits must finish before scoring')
    if (root / io.RESULT / 'SCORING_COMPLETE.json').exists():
        raise RuntimeError('scoring already complete')
    pcfg = parent.config(root)
    torch = gpu_runtime(pcfg)
    from ipin_openppi.partner_specificity.models import make_model
    data = io.parent_data(root)
    raw = np.load(root / parent.GENERATED / 'raw_public_embeddings.npy', allow_pickle=False)
    feasible = io.read_json(root / io.RESULT / 'FEASIBILITY.json')['feasible_arms']
    records, count, started = [], 0, time.monotonic()
    for arm in feasible:
        for fold in range(3):
            path = root / io.RUN / f'scores_{arm}_{fold}.npz'
            if path.exists():
                raise RuntimeError('existing score artifact requires operational review')
            ev = arrays(root / parent.GENERATED / f'evaluation_fold_{fold}.npz')
            plan = arrays(root / io.RUN / f'plan_{arm}_{fold}.npz')
            parent_scores = arrays(root / parent.GENERATED / f'scores_fold_{fold}.npz')
            original_columns = parent_scores['columns'].tolist()
            names, columns = [], []
            normalized, _, _ = normalize(raw, plan['fit_endpoints'])
            x = torch.from_numpy(normalized).cuda()
            for name in cfg['models']:
                seeds = []
                for seed in pcfg['training']['seeds']:
                    if arm == 'union':
                        values = parent_scores['scores'][:, original_columns.index(f'{name}__{seed}')]
                    else:
                        ckpt = torch.load(root / io.RUN / f'{arm}_f{fold}_{name}_s{seed}.pt', map_location='cpu', weights_only=True)
                        if ckpt['execution_freeze_sha256'] != sha256_file(root / io.RESULT / 'EXECUTION_FREEZE.json'):
                            raise RuntimeError('checkpoint freeze mismatch')
                        model = make_model(name, seed).cuda()
                        model.load_state_dict(ckpt['state_dict'])
                        model.eval()
                        values = np.empty(len(ev['a']), dtype=np.float64)
                        with torch.no_grad():
                            if name == 'endpoint_linear':
                                unary = model.unary(x).squeeze(-1).cpu().numpy().astype(np.float64)
                                values[:] = unary[ev['a']] + unary[ev['b']]
                            else:
                                for start in range(0, len(values), 4096):
                                    a, b = (torch.from_numpy(ev[side][start:start + 4096]).cuda() for side in ('a', 'b'))
                                    values[start:start + 4096] = model(x[a], x[b]).cpu().numpy().astype(np.float64)
                    names.append(f'{name}__{seed}')
                    columns.append(values)
                    seeds.append(values)
                names.append(name)
                columns.append(np.mean(seeds, axis=0))
            for name in cfg['controls']:
                sim = np.load(io.similarity_path(root, name.removeprefix('interolog_')), mmap_mode='r', allow_pickle=False)
                values = exhaustive_transfer_gpu(sim, ev['a'], ev['b'], data['p_a'][plan['p_rows']], data['p_b'][plan['p_rows']])
                columns.append(values)
                names.append(name)
                print(f'scored {arm}/{fold}: {name}', flush=True)
            for name in ('length_ratio', 'kmer3_cosine', 'pooled_cosine'):
                names.append(name)
                columns.append(parent_scores['scores'][:, original_columns.index(name)])
            matrix = np.column_stack(columns)
            if not np.isfinite(matrix).all():
                raise RuntimeError('nonfinite scores')
            atomic_npz(path, columns=np.array(names), scores=matrix)
            records.append(io.artifact(root, path))
            count += matrix.size
    out = {'created_utc': io.now(), 'artifacts': records, 'score_values': count,
           'elapsed_seconds': time.monotonic() - started, 'metrics_computed': False}
    io.write_json(root / io.RESULT / 'SCORING_COMPLETE.json', out)
    return {'score_values': count, 'elapsed_seconds': out['elapsed_seconds']}


def _subpanel(ev, mask):
    return build_queries(ev['a'][mask], ev['b'][mask], ev['positive'][mask])


def evaluate(root):
    cfg = io.verify_freeze(root)
    if (root / io.RESULT / 'RESULTS.json').exists():
        raise RuntimeError('readout already exists')
    io.verify_records(root, io.read_json(root / io.RESULT / 'SCORING_COMPLETE.json')['artifacts'])
    feasibility = io.read_json(root / io.RESULT / 'FEASIBILITY.json')
    data, source = io.parent_data(root), np.load(root / io.RUN / 'public_positive_source_bits.npy', allow_pickle=False)
    component = data['component']
    draws = np.random.Generator(np.random.PCG64DXSM(cfg['bootstrap']['seed'])).poisson(
        1, size=(cfg['bootstrap']['replicates'], int(component.max()) + 1)).astype(np.int16)
    draw_path = root / io.RUN / 'component_multipliers.npy'
    atomic_numpy(draw_path, draws)
    records = [io.artifact(root, draw_path)]
    results = {}
    for arm in feasibility['feasible_arms']:
        all_points, all_credits, totals, quartet_totals, folds, extra = {}, {}, {}, {}, [], []
        for fold in range(3):
            print(f'evaluate {arm}/{fold}', flush=True)
            ev = arrays(root / parent.GENERATED / f'evaluation_fold_{fold}.npz')
            plan = arrays(root / io.RUN / f'plan_{arm}_{fold}.npz')
            scores = arrays(root / io.RUN / f'scores_{arm}_{fold}.npz')
            names = scores['columns'].tolist()
            keep = plan['evaluation_mask']
            queries = _subpanel(ev, keep)
            w = ev['num'].astype(np.float64) / ev['den']
            anchors = np.array([q.anchor for q in queries], dtype=np.int64)
            qrows, qends = ev['quartet_rows'][plan['quartet_mask']], ev['quartet_endpoints'][plan['quartet_mask']]
            points, credits = {}, {}
            for i, name in enumerate(names):
                values = scores['scores'][:, i]
                pts = anchor_points(values[keep], queries, w[keep])
                points[name] = pts
                credit, _ = quartet_credit(values, qrows)
                credits[name] = credit
                all_points.setdefault(name, []).append(pts)
                all_credits.setdefault(name, []).append(credit)
                if name in cfg['models'] + cfg['controls']:
                    total, mass = bootstrap_anchor_totals(values[keep], queries, w[keep], component, draws)
                    totals.setdefault(name, []).append((total, mass))
                    qt, qm = quartet_bootstrap_totals(credit, qends, component, draws)
                    quartet_totals.setdefault(name, []).append((qt, qm))
            metric_path = root / io.RUN / f'points_{arm}_{fold}.npz'
            atomic_npz(metric_path, anchors=anchors, **points)
            records.append(io.artifact(root, metric_path))
            folds.append({'fold': fold, 'anchors': len(queries), 'quartets': len(qrows),
                          'macro': {n: float(v.mean()) for n, v in points.items()},
                          'quartet': {n: float(v.mean()) if len(v) else None for n, v in credits.items()}})
            if arm == 'union':
                for stratum, mask in [(f'source_{k}', panel_mask(ev, source, k)) for k in (1, 2, 3)] + [('no_detected_hit', plan['no_hit_pair'])]:
                    query = _subpanel(ev, mask)
                    comps = np.unique(component[[q.anchor for q in query]]) if query else []
                    pts = {n: anchor_points(scores['scores'][mask, names.index(n)], query, w[mask])
                           for n in cfg['models'] + cfg['controls']} if query else {}
                    extra.append({'fold': fold, 'stratum': stratum, 'anchors': len(query), 'components': len(comps),
                                  'P': int((ev['positive'] & mask).sum()), 'U': int((~ev['positive'] & mask).sum()),
                                  'macro': {n: float(v.mean()) for n, v in pts.items()}})
        macro = {n: float(np.concatenate(v).mean()) for n, v in all_points.items()}
        qmacro = {n: float(np.concatenate(v).mean()) if sum(map(len, v)) else None for n, v in all_credits.items()}
        def combine(items):
            return finite_ratio(sum(t for t, _ in items), sum(m for _, m in items))
        boot = {n: combine(v) for n, v in totals.items()}
        qboot = {n: combine(v) for n, v in quartet_totals.items()}
        comparators = ['endpoint_linear'] + cfg['controls']
        deltas = {n: {'point': macro['pair_linear'] - macro[n],
                      **summary_interval(boot['pair_linear'] - boot[n])} for n in comparators}
        strongest = max(comparators, key=lambda n: macro[n])
        envelope = boot['pair_linear'] - np.maximum.reduce([boot[n] for n in comparators])
        qdeltas = {n: {'point': qmacro['pair_linear'] - qmacro[n] if qmacro[n] is not None else None,
                       **summary_interval(qboot['pair_linear'] - qboot[n])} for n in cfg['controls']}
        seed_delta = {str(s): macro[f'pair_linear__{s}'] - macro[f'endpoint_linear__{s}']
                      for s in parent.config(root)['training']['seeds']}
        checks = {'margin_over_strongest': deltas[strongest]['point'] >= cfg['decision']['minimum_margin'],
                  'all_control_paired_lower_positive': all(d['ci95'] is not None and d['ci95'][0] > 0 for d in deltas.values()),
                  'each_fold_beats_linear_unary': all(f['macro']['pair_linear'] > f['macro']['endpoint_linear'] for f in folds),
                  'each_seed_beats_linear_unary': all(v > 0 for v in seed_delta.values())}
        qinterval = summary_interval(qboot['pair_linear'])
        qchecks = {'feasible': arm in feasibility['quartet_feasible_arms'],
                   'pair_lower_above_half': qinterval['ci95'] is not None and qinterval['ci95'][0] > .5,
                   'all_transfer_paired_lower_positive': all(d['ci95'] is not None and d['ci95'][0] > 0 for d in qdeltas.values())}
        bootstrap_path = root / io.RUN / f'bootstrap_{arm}.npz'
        atomic_npz(bootstrap_path, **{f'anchor_{k}': v for k, v in boot.items()},
                   **{f'quartet_{k}': v for k, v in qboot.items()})
        records.append(io.artifact(root, bootstrap_path))
        stratum_summary = {}
        for stratum in sorted({e['stratum'] for e in extra}):
            rows = [e for e in extra if e['stratum'] == stratum]
            na, nc = sum(e['anchors'] for e in rows), sum(e['components'] for e in rows)
            supported = na >= 50 and nc >= 20
            stratum_summary[stratum] = {'anchors': na, 'components': nc,
                'P': sum(e['P'] for e in rows), 'U': sum(e['U'] for e in rows), 'supported': supported,
                'macro': {n: sum(e['anchors'] * e['macro'].get(n, 0) for e in rows) / na
                          for n in cfg['models'] + cfg['controls']} if supported else {}}
            if not supported:
                for e in rows:
                    e['macro'] = {}
        results[arm] = {'macro': macro, 'model_intervals': {n: summary_interval(v) for n, v in boot.items()},
                        'deltas': deltas, 'strongest_control': strongest,
                        'margin_over_strongest': deltas[strongest]['point'],
                        'descriptive_minimum_margin_interval': summary_interval(envelope),
                        'folds': folds, 'seed_delta_vs_linear': seed_delta, 'checks': checks,
                        'anchor_signal_survives': all(checks.values()),
                        'quartet': {'points': qmacro, 'pair_interval': qinterval, 'deltas': qdeltas,
                                    'checks': qchecks, 'signal_survives': all(qchecks.values())},
                        'descriptive_strata': extra, 'stratum_summary': stratum_summary}
        print(json.dumps({'arm': arm, 'margin': results[arm]['margin_over_strongest'], 'checks': checks}), flush=True)
    overall = len(results) == 4 and all(v['anchor_signal_survives'] and v['quartet']['signal_survives'] for v in results.values())
    out = {'created_utc': io.now(), 'arms': results, 'all_challenges_survived': overall,
           'disposition': 'survives_tested_internal_challenges_not_external_confirmation' if overall else 'mixed_or_explained_internal_signal_inspect_each_challenge',
           'source_claim': 'internal_source_exclusive_recovery_not_independent_assay_or_laboratory_validation',
           'joint_source_and_purge_tested': False, 'protected_access': False, 'artifacts': records}
    io.write_json(root / io.RESULT / 'RESULTS.json', out)
    return {'disposition': out['disposition'], 'arms': {a: v['anchor_signal_survives'] for a, v in results.items()}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('register', 'annotate', 'search', 'prepare', 'correct_precision', 'freeze', 'train', 'score', 'evaluate', 'validate'))
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.project_root.resolve(strict=True)
    if args.action in ('register', 'annotate', 'search', 'prepare', 'correct_precision', 'freeze'):
        result = getattr(io, args.action)(root)
    elif args.action == 'validate':
        from .validation import validate
        result = validate(root)
    else:
        result = globals()[args.action](root)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0
