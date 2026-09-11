"""Frozen external-source panels, checkpoint-only scoring and research triage."""

import argparse
import json
from pathlib import Path
import time

import numpy as np
import pyarrow.parquet as pq

from ipin_openppi.homology_source import data as hio
from ipin_openppi.homology_source.pipeline import exhaustive_transfer_gpu
from ipin_openppi.homology_source.semantics import finite_ratio, summary_interval
from ipin_openppi.partner_specificity import data as pio
from ipin_openppi.partner_specificity.pipeline import gpu_runtime
from ipin_openppi.partner_specificity.semantics import (
    anchor_points, bootstrap_anchor_totals, quartet_bootstrap_totals, quartet_credit,
)
from ipin_openppi.stage1.support import atomic_npz, atomic_numpy, sha256_file
from . import data as io
from .semantics import accession_lookup, classify, directed_queries, make_panel, project_source, select_directed_quartets


def prepare(root):
    cfg = io.verify_registration(root)
    io.verify_records(root, io.read_json(root / io.RESULT / 'ACQUISITION.json')['artifacts'])
    if (root / io.RUN).exists() or (root / io.RESULT / 'FEASIBILITY.json').exists():
        raise RuntimeError('existing preparation requires explicit operational review')
    data = hio.parent_data(root)
    meta = io.read_json(root / pio.GENERATED / 'endpoint_metadata.json')
    records = pq.read_table(root / pio.config(root)['inputs']['endpoints']['path'],
                           columns=['reference_sequence_sha256', 'uniprot_accessions']).to_pylist()
    accessions = accession_lookup(records, meta['endpoints'])
    edges = np.load(root / hio.RUN / 'purge_edges.npy', allow_pickle=False)
    crosslinks = []
    for fold in range(3):
        plan = io.load(root / hio.RUN / f'plan_purged20_{fold}.npz')
        fit = plan['fit_endpoints']
        crossing = ((data['fold'][edges[:, 0]] == fold) & fit[edges[:, 1]]) | (
            (data['fold'][edges[:, 1]] == fold) & fit[edges[:, 0]])
        if crossing.any() or np.any(fit & (data['fold'] == fold)):
            raise RuntimeError('frozen purge has heldout exposure')
        if not np.all(fit[data['p_a'][plan['p_rows']]] & fit[data['p_b'][plan['p_rows']]]):
            raise RuntimeError('transfer graph includes excluded endpoints')
        crosslinks.append(int(crossing.sum()))
    paths, cells = [], {}
    for cell in cfg['cells']:
        source_paths = {key: root / io.RAW / cfg['source']['files'][key + '_' + cell]
                        for key in ('network', 'directed', 'baits')}
        directed, baits, preys, counts = project_source(
            io.tsv(source_paths['network']), io.tsv(source_paths['directed']), io.tsv(source_paths['baits']), accessions)
        path = root / io.RUN / f'source_{cell}.npz'
        atomic_npz(path, directed=directed, baits=baits, preys=preys)
        paths.append(path)
        folds = []
        for fold in range(3):
            ev, attrition = make_panel(data, set(map(tuple, directed)), set(baits), set(preys), fold)
            qcfg = cfg['quartets']
            rows, ends, candidates = select_directed_quartets(ev['a'], ev['b'], ev['positive'],
                salt=f"{qcfg['salt']}:{cell}:{fold}", maximum=qcfg['maximum_per_fold'],
                edge_cap=qcfg['positive_edge_cap'], endpoint_cap=qcfg['endpoint_cap'])
            queries = directed_queries(ev['a'], ev['b'], ev['positive'])
            anchors = np.array([q.anchor for q in queries], dtype=np.int64)
            census = {'fold': fold, 'positive_directed_edges': int(ev['positive'].sum()),
                'unlabeled_directed_edges': int((~ev['positive']).sum()), 'anchors': len(anchors),
                'anchor_components': len(np.unique(data['component'][anchors])), 'quartets': len(rows),
                'quartet_components': len(np.unique(data['component'][ends])),
                'candidate_quartets': candidates, 'attrition': attrition}
            pcfg = cfg['panel']
            census['anchor_feasible'] = (census['positive_directed_edges'] >= pcfg['minimum_P_per_fold']
                and census['unlabeled_directed_edges'] >= pcfg['minimum_U_per_fold']
                and census['anchors'] >= pcfg['minimum_anchors_per_fold']
                and census['anchor_components'] >= pcfg['minimum_anchor_components_per_fold'])
            census['quartet_feasible'] = (len(rows) >= qcfg['minimum_per_fold']
                and census['quartet_components'] >= qcfg['minimum_components_per_fold'])
            path = root / io.RUN / f'panel_{cell}_{fold}.npz'
            atomic_npz(path, **ev, quartet_rows=rows, quartet_endpoints=ends)
            paths.append(path)
            folds.append(census)
            print({'cell': cell, **census}, flush=True)
        cells[cell] = {'source_census': counts, 'folds': folds,
                       'anchor_feasible': all(f['anchor_feasible'] for f in folds),
                       'quartet_feasible': all(f['quartet_feasible'] for f in folds)}
    out = {'created_utc': io.now(), 'cells': cells, 'qualifying_fit_eval_crosslinks': crosslinks,
           'artifacts': [io.artifact(root, p) for p in paths], 'external_scores_seen': False,
           'complete_pair_attempt_evaluability_log': False, 'new_fits': 0}
    io.write_json(root / io.RESULT / 'FEASIBILITY.json', out)
    return {'cells': cells}


def score(root):
    cfg = io.verify_freeze(root)
    if (root / io.RESULT / 'SCORING_COMPLETE.json').exists():
        raise RuntimeError('scores already complete')
    from ipin_openppi.partner_specificity.models import make_model
    torch = gpu_runtime(pio.config(root))
    data = hio.parent_data(root)
    raw = np.load(root / pio.GENERATED / 'raw_public_embeddings.npy', allow_pickle=False)
    feasibility = io.read_json(root / io.RESULT / 'FEASIBILITY.json')
    paths, count, started = [], 0, time.monotonic()
    for cell in cfg['cells']:
        if not feasibility['cells'][cell]['anchor_feasible']:
            continue
        for fold in range(3):
            path = root / io.RUN / f'scores_{cell}_{fold}.npz'
            if path.exists():
                raise RuntimeError('existing score table cannot be overwritten')
            ev = io.load(root / io.RUN / f'panel_{cell}_{fold}.npz')
            plan = io.load(root / hio.RUN / f'plan_purged20_{fold}.npz')
            norm = io.load(root / hio.RUN / f'normalization_purged20_{fold}.npz')
            x = torch.from_numpy(((raw.astype(np.float64) - norm['mean']) / norm['std']).astype(np.float32)).cuda()
            columns, values = [], []
            for name in cfg['models']:
                seed_values = []
                for seed in cfg['seeds']:
                    ckpt = torch.load(root / hio.RUN / f'purged20_f{fold}_{name}_s{seed}.pt', map_location='cpu', weights_only=True)
                    if ckpt['execution_freeze_sha256'] != cfg['parent_execution_freeze_sha256']:
                        raise RuntimeError('checkpoint provenance mismatch')
                    model = make_model(name, seed).cuda()
                    model.load_state_dict(ckpt['state_dict'])
                    model.eval()
                    output = np.empty(len(ev['a']), dtype=np.float64)
                    with torch.no_grad():
                        if name == 'endpoint_linear':
                            unary = model.unary(x).squeeze(-1).cpu().numpy().astype(np.float64)
                            output[:] = unary[ev['a']] + unary[ev['b']]
                        else:
                            for start in range(0, len(output), 4096):
                                a, b = [torch.from_numpy(ev[k][start:start + 4096]).cuda() for k in ('a', 'b')]
                                output[start:start + 4096] = model(x[a], x[b]).cpu().numpy()
                    seed_values.append(output)
                    values.append(output)
                    columns.append(f'{name}__{seed}')
                values.append(np.mean(seed_values, axis=0))
                columns.append(name)
            for name in ('kmer', 'plm', 'local', 'coverage'):
                sim = np.load(hio.similarity_path(root, name), mmap_mode='r', allow_pickle=False)
                output = exhaustive_transfer_gpu(sim, ev['a'], ev['b'],
                    data['p_a'][plan['p_rows']], data['p_b'][plan['p_rows']])
                values.append(output)
                columns.append('interolog_' + name)
                if name == 'kmer':
                    values.append(np.asarray(sim[ev['a'], ev['b']], dtype=np.float64))
                    columns.append('kmer3_cosine')
            unit = raw.astype(np.float64) / np.linalg.norm(raw.astype(np.float64), axis=1)[:, None]
            cosine = np.empty(len(ev['a']), dtype=np.float64)
            for start in range(0, len(cosine), 4096):
                a, b = ev['a'][start:start + 4096], ev['b'][start:start + 4096]
                cosine[start:start + 4096] = np.sum(unit[a] * unit[b], axis=1)
            values.append(cosine)
            columns.append('pooled_cosine')
            lengths_a, lengths_b = data['length'][ev['a']], data['length'][ev['b']]
            values.append(np.minimum(lengths_a, lengths_b) / np.maximum(lengths_a, lengths_b))
            columns.append('length_ratio')
            matrix = np.column_stack(values)
            if not np.isfinite(matrix).all():
                raise RuntimeError('nonfinite external scores')
            atomic_npz(path, scores=matrix, columns=np.array(columns))
            paths.append(path)
            count += matrix.size
            print({'scored': cell, 'fold': fold, 'rows': len(matrix), 'columns': len(columns)}, flush=True)
    out = {'created_utc': io.now(), 'artifacts': [io.artifact(root, p) for p in paths],
           'score_values': count, 'elapsed_seconds': time.monotonic() - started,
           'new_fits': 0, 'metrics_computed': False}
    io.write_json(root / io.RESULT / 'SCORING_COMPLETE.json', out)
    return {k: out[k] for k in ('score_values', 'elapsed_seconds', 'new_fits')}


def evaluate(root):
    cfg = io.verify_freeze(root)
    io.verify_records(root, io.read_json(root / io.RESULT / 'SCORING_COMPLETE.json')['artifacts'])
    if (root / io.RESULT / 'RESULTS.json').exists():
        raise RuntimeError('external readout already complete')
    data = hio.parent_data(root)
    draws = np.random.Generator(np.random.PCG64DXSM(cfg['bootstrap']['seed'])).poisson(
        1, size=(cfg['bootstrap']['replicates'], int(data['component'].max()) + 1)).astype(np.int16)
    path = root / io.RUN / 'component_multipliers.npy'
    atomic_numpy(path, draws)
    paths, cells = [path], {}
    feasibility = io.read_json(root / io.RESULT / 'FEASIBILITY.json')['cells']
    for cell in cfg['cells']:
        if not feasibility[cell]['anchor_feasible']:
            cells[cell] = {'anchor_status': 'infeasible', 'swap_status': 'inconclusive_insufficient_support',
                           'anchor_signal_survives': False, 'swap_signal_survives': False}
            continue
        points, credits, totals, qtotals, folds = {}, {}, {}, {}, []
        for fold in range(3):
            ev = io.load(root / io.RUN / f'panel_{cell}_{fold}.npz')
            scored = io.load(root / io.RUN / f'scores_{cell}_{fold}.npz')
            queries = directed_queries(ev['a'], ev['b'], ev['positive'])
            weight = ev['num'].astype(float) / ev['den']
            fold_points = {}
            for col, name in enumerate(scored['columns'].tolist()):
                values = scored['scores'][:, col]
                point = anchor_points(values, queries, weight)
                credit, delta = quartet_credit(values, ev['quartet_rows'], cfg['quartets']['tie_tolerance'])
                if name.startswith('endpoint_linear') and not np.all(credit == .5):
                    raise RuntimeError('additive null does not cancel on directed quartets')
                points.setdefault(name, []).append(point)
                credits.setdefault(name, []).append(credit)
                fold_points[name] = float(point.mean())
                if '__' not in name:
                    total = np.stack(bootstrap_anchor_totals(values, queries, weight, data['component'], draws))
                    qtotal = np.stack(quartet_bootstrap_totals(credit, ev['quartet_endpoints'], data['component'], draws))
                    totals[name] = totals.get(name, 0) + total
                    qtotals[name] = qtotals.get(name, 0) + qtotal
            folds.append({'fold': fold, 'anchors': len(queries), 'quartets': len(ev['quartet_rows']), 'macro': fold_points})
            print({'evaluated': cell, 'fold': fold}, flush=True)
        macro = {k: float(np.concatenate(v).mean()) for k, v in points.items()}
        qmacro = {k: float(np.concatenate(v).mean()) if sum(map(len, v)) else None for k, v in credits.items()}
        boot = {k: finite_ratio(*v) for k, v in totals.items()}
        qboot = {k: finite_ratio(*v) for k, v in qtotals.items()}
        deltas = {c: {'point': macro['pair_linear'] - macro[c], **summary_interval(boot['pair_linear'] - boot[c])}
                  for c in cfg['controls']}
        quartet = {'count': sum(f['quartets'] for f in folds), 'preference': qmacro,
                   'interval': summary_interval(qboot['pair_linear']),
                   'deltas': {c: {'point': qmacro['pair_linear'] - qmacro[c] if qmacro[c] is not None else None,
                                 **summary_interval(qboot['pair_linear'] - qboot[c])} for c in cfg['controls']}}
        decision = classify(True, feasibility[cell]['quartet_feasible'], macro, deltas, folds,
                            cfg['seeds'], quartet, cfg['controls'], cfg['decision']['minimum_anchor_margin'])
        cells[cell] = {'anchors': sum(f['anchors'] for f in folds), 'macro': macro, 'deltas': deltas,
                       'folds': folds, 'quartet': quartet, **decision}
        path = root / io.RUN / f'bootstrap_{cell}.npz'
        atomic_npz(path, **{f'anchor_{k}': v for k, v in totals.items()}, **{f'quartet_{k}': v for k, v in qtotals.items()})
        paths.append(path)
    passed = all(c['anchor_signal_survives'] and c['swap_signal_survives'] for c in cells.values())
    out = {'created_utc': io.now(), 'protocol_id': io.ID, 'cells': cells,
           'all_external_challenges_pass': passed, 'new_fits': 0, 'protected_access': False,
           'estimand': 'external_released_coassociation_P_versus_U_recovery_on_reused_public_endpoints',
           'artifacts': [io.artifact(root, p) for p in paths]}
    io.write_json(root / io.RESULT / 'RESULTS.json', out)
    return {'all_external_challenges_pass': passed, 'cells': {k: {n: v[n] for n in (
        'anchor_status', 'swap_status')} for k, v in cells.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['register', 'acquire', 'prepare', 'freeze', 'score', 'evaluate', 'validate', 'close'])
    phase = parser.parse_args().phase
    if phase in ('register', 'acquire', 'freeze'):
        function = getattr(io, phase)
    elif phase == 'validate':
        from .validation import validate
        function = validate
    elif phase == 'close':
        from .validation import close
        function = close
    else:
        function = globals()[phase]
    print(json.dumps(function(Path.cwd()), indent=2))
