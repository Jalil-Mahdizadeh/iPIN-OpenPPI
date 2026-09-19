"""Candidate-only inference, frozen-list evaluation, independent audit, and reporting."""
from __future__ import annotations

import csv
import time
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import torch

from common import *


def selection():
    assert_frozen()
    receipt = read_json(OUT / 'provenance/SELECTION_FREEZE_SHA256.json')
    return read_json(resolve(receipt))


def candidate_table(cell):
    base = TUNA / 'private/session'
    rec = next(r for r in read_json(base / 'SESSION.json')['files'] if r['cell'] == cell)
    p = check(base / rec['path'], rec['sha256'])
    table = pq.read_table(p)
    assert set(table.column_names) == {'candidate_token', 'endpoint_a_sha256', 'endpoint_b_sha256', 'cell_id'}
    return table, record(p)


def column(table, name):
    return table[name].to_numpy(zero_copy_only=False)


def endpoint_indices(table, ids):
    assert np.array_equal(ids, np.sort(ids))
    result = []
    for name in ('endpoint_a_sha256', 'endpoint_b_sha256'):
        s = column(table, name).astype(ids.dtype)
        idx = np.searchsorted(ids, s)
        assert (idx < len(ids)).all() and np.array_equal(ids[idx], s)
        result.append(idx)
    return result


def align(source_tokens, target_tokens):
    if len(source_tokens) != len(target_tokens):
        raise ValueError('Candidate count mismatch')
    order = np.argsort(source_tokens)
    ordered = source_tokens[order]
    assert (ordered[1:] != ordered[:-1]).all(), 'Duplicate candidate token'
    ix = np.searchsorted(ordered, target_tokens)
    assert (ix < len(ix)).all() and np.array_equal(ordered[ix], target_tokens)
    assert len(np.unique(ix)) == len(ix)
    return order[ix]


def score_test():
    chosen = selection()
    environment()
    x, ids, meta, _, _ = load_inputs()
    x = torch.from_numpy(x).cuda()
    parts = np.asarray(meta['partition'])
    files = []
    started = time.monotonic()
    for cell in protocol()['test_cells']:
        table, candidate_rec = candidate_table(cell)
        a, b = endpoint_indices(table, ids)
        if cell == 'C3_test':
            assert ((parts[a] == 'test') & (parts[b] == 'test')).all()
        elif cell == 'C1_test':
            assert ((parts[a] == 'train') & (parts[b] == 'train')).all()
        else:
            assert (((parts[a] == 'train') & (parts[b] == 'test')) |
                    ((parts[b] == 'train') & (parts[a] == 'test'))).all()
        members = np.empty((len(a), len(VARIANTS), 3), dtype=np.float32)
        for vi, variant in enumerate(VARIANTS):
            c = next(c for c in chosen['candidates'] if c['variant'] == variant)
            for mi, m in enumerate(c['members']):
                model = head.build(640, SPEC, m['seed']).cuda()
                head.load_state(resolve(m['checkpoint']), model)
                members[:, vi, mi] = score(model, x, a, b)
                forward = score(model, x, a[:4096], b[:4096])
                reverse = score(model, x, b[:4096], a[:4096])
                assert np.array_equal(forward, reverse)
                del model
            print(f"Scored {cell}: {variant}, epoch {c['epoch']}, {len(a)} pairs", flush=True)
        means = members.astype(np.float64).mean(axis=2)
        files.append(dict(cell=cell, candidates=candidate_rec, models=list(VARIANTS),
                          member_scores=write_npy(f'private/test/{cell}_members.npy', members),
                          ensemble_scores=write_npy(f'private/test/{cell}_ensembles.npy', means),
                          symmetry_verified=True, pairs=len(a)))
    r = write_json('provenance/PREDICTION_FREEZE.json', dict(at_utc=now(), files=files,
                  selection=record(OUT / 'provenance/SELECTION_FREEZE.json'),
                  elapsed_seconds=time.monotonic() - started, test_labels_accessed=False))
    write_json('provenance/PREDICTION_FREEZE_SHA256.json', r)


def predictions_freeze():
    selection()
    rec = read_json(OUT / 'provenance/PREDICTION_FREEZE_SHA256.json')
    f = read_json(resolve(rec))
    resolve(f['selection'])
    return f


def old_combo_artifact(relative):
    m = read_json(COMBO / 'provenance/RESULTS_MANIFEST.json')
    r = next(r for r in m['artifacts'] if r['path'] == relative)
    return check(COMBO / relative, r['sha256'])


def table_with_scores(cell, new_rec, ids):
    # This function is only called AFTER the prediction-freeze gate.
    candidates = pq.read_table(resolve(new_rec['candidates']))
    tokens = column(candidates, 'candidate_token')
    a, b = endpoint_indices(candidates, ids)
    old = pq.read_table(old_combo_artifact(f'private/run_v1/{cell}_scores.parquet'))
    ix = align(column(old, 'candidate_token'), tokens)
    oa, ob = endpoint_indices(old, ids)
    assert np.array_equal(oa[ix], a) and np.array_equal(ob[ix], b)
    positive = column(old, 'known_positive')[ix].astype(bool)
    weights = column(old, 'sampling_weight')[ix].astype(float)
    refs = read_json(TUNA / 'private/references/REFERENCES.json')
    br = next(r for r in refs['files'] if r['cell'] == cell and r['model'] == 'ipin_baseline')
    base = pq.read_table(check(TUNA / 'private/references' / br['path'], br['sha256']))
    bi = align(column(base, 'candidate_token'), tokens)
    values = np.column_stack([column(base, 'score')[bi], column(old, 'ipin_optimized')[ix],
                              column(old, 'tuna_retrained')[ix], column(old, 'combo')[ix],
                              np.load(resolve(new_rec['ensemble_scores']), allow_pickle=False)])
    assert values.shape == (len(a), 7) and np.isfinite(values).all()
    return a, b, positive, weights, values


def evaluate():
    freeze = predictions_freeze()
    chosen = selection()
    _, ids, meta, _, _ = load_inputs()
    models = (*REFERENCES, *VARIANTS)
    components, parts = np.asarray(meta['component']), np.asarray(meta['partition'])
    rows, comparisons, concordance, coverage = [], [], [], []
    artifacts = []
    for cell_rec in freeze['files']:
        cell = cell_rec['cell']
        a, b, p, weight, scores = table_with_scores(cell, cell_rec, ids)
        views, census = ranking.query_views(a, b, p, protocol()['minimum_candidates'])
        queries = np.asarray([q for q, _ in views])
        counts = np.asarray([len(idx) for _, idx in views])
        positives = np.asarray([p[idx].sum() for _, idx in views])
        value = np.asarray([[ranking.rank_metrics(scores[idx, mi], p[idx], BUDGETS)
                             for mi in range(len(models))] for _, idx in views])
        artifacts.append(write_npy(f'private/evaluation/{cell}_all_scores.npy', scores))
        artifacts.append(write_npy(f'private/evaluation/{cell}_query_metrics.npy', value))
        qrows = []
        for qi, q in enumerate(queries):
            for mi, model in enumerate(models):
                for ki, k in enumerate(BUDGETS):
                    qrows.append(dict(dataset=cell, query_sha256=str(ids[q]), component=str(components[q]),
                                      partition=str(parts[q]), candidates=int(counts[qi]),
                                      positives=int(positives[qi]), model=model, K=k,
                                      **dict(zip(ranking.METRICS, value[qi, mi, ki].tolist()))))
        artifacts.append(write_csv(f'results/{cell}_per_query_metrics.csv', qrows))
        subsets = [('all', np.ones(len(queries), bool))]
        if cell == 'C2_test':
            subsets.extend((s, parts[queries] == s) for s in protocol()['C2_subgroups'])
        for subgroup, mask in subsets:
            v = value[mask]
            query_components = components[queries][mask]
            draws = ranking.cluster_draws(v, query_components, protocol()['bootstrap_replicates'],
                                          protocol()['bootstrap_seed'])
            means = v.mean(axis=0)
            intervals = np.quantile(draws, [.025, .975], axis=0)
            for mi, model in enumerate(models):
                for ki, k in enumerate(BUDGETS):
                    row = dict(dataset=cell, subgroup=subgroup, model=model, K=k,
                               primary_selected=(model == chosen['primary_winner']), queries=int(mask.sum()),
                               components=len(np.unique(query_components)))
                    for j, metric in enumerate(ranking.METRICS):
                        row.update({metric: float(means[mi, ki, j]),
                                    metric + '_low': float(intervals[0, mi, ki, j]),
                                    metric + '_high': float(intervals[1, mi, ki, j])})
                    row['total_oriented_query_hits'] = float(v[:, mi, ki, 1].sum())
                    row['micro_recall_oriented'] = float(v[:, mi, ki, 1].sum() / positives[mask].sum())
                    row['median_hits'] = float(np.median(v[:, mi, ki, 1]))
                    rows.append(row)
            for vi, variant in enumerate(VARIANTS, start=len(REFERENCES)):
                for ri, ref in enumerate(REFERENCES):
                    difference = draws[:, vi] - draws[:, ri]
                    ci = np.quantile(difference, [.025, .975], axis=0)
                    for ki, k in enumerate(BUDGETS):
                        row = dict(dataset=cell, subgroup=subgroup, variant=variant, reference=ref, K=k,
                                   primary_selected=(variant == chosen['primary_winner']), queries=int(mask.sum()))
                        for j, metric in enumerate(ranking.METRICS):
                            row.update({metric + '_delta': float(means[vi, ki, j] - means[ri, ki, j]),
                                        metric + '_delta_low': float(ci[0, ki, j]),
                                        metric + '_delta_high': float(ci[1, ki, j])})
                        comparisons.append(row)
        coverage.append(dict(dataset=cell, pairs=len(a), positives=int(p.sum()), unlabeled=int((~p).sum()),
                             query_components=len(np.unique(components[queries])), **census))
        for mi, model in enumerate(models):
            concordance.append(dict(dataset=cell, model=model,
                                    weighted_PU_concordance=ranking.concordance(scores[:, mi], p, weight)))
        print(f'Evaluated {cell}: {len(queries)} eligible queries, 7 models, K=10/20/30', flush=True)
    artifacts.extend([write_csv('results/all_panel_metrics.csv', rows),
                      write_csv('results/paired_comparisons.csv', comparisons),
                      write_csv('results/global_concordance.csv', concordance),
                      write_csv('results/panel_coverage.csv', coverage)])
    r = write_json('provenance/EVALUATION_COMPLETE.json', dict(at_utc=now(), artifacts=artifacts,
                  predictions=record(OUT / 'provenance/PREDICTION_FREEZE.json'), models=list(models),
                  metrics=list(ranking.METRICS), budgets=list(BUDGETS), test_used_for_selection=False))
    write_json('provenance/EVALUATION_COMPLETE_SHA256.json', r)


def independent_recovery(s, p):
    """Independent O(P*N) rank counting; no shared sort/rank implementation."""
    pos = s[p]
    greater = (s[:, None] > pos[None, :]).sum(axis=0)
    equal = (s[:, None] == pos[None, :]).sum(axis=0)
    hits = np.asarray([np.clip((k - greater) / equal, 0, 1).sum() for k in BUDGETS])
    return np.column_stack([len(s) * hits / (np.asarray(BUDGETS) * p.sum()),
                            hits, hits / p.sum(), hits / np.asarray(BUDGETS)])


def audit_results():
    frozen = assert_frozen()
    pred = predictions_freeze()
    chosen = selection()
    complete = read_json(resolve(read_json(OUT / 'provenance/EVALUATION_COMPLETE_SHA256.json')))
    for rec in complete['artifacts']:
        resolve(rec)
    _, ids, meta, _, dev = load_inputs()
    checked = 0
    max_error = 0.0
    reference_checks = 0
    for c in chosen['candidates']:
        for m in c['members']:
            resolve(m['checkpoint'])
        actual = ensemble([m['predictions'] for m in c['members']])
        expected = np.load(resolve(c['predictions']), allow_pickle=False)
        assert np.array_equal(actual, expected)
        _, mean = dev_metrics(actual, dev)
        assert abs(mean[1, 0] - c['EF20']) < 1e-12
    for cell_rec in pred['files']:
        cell = cell_rec['cell']
        member = np.load(resolve(cell_rec['member_scores']), allow_pickle=False)
        mean = np.load(resolve(cell_rec['ensemble_scores']), allow_pickle=False)
        assert np.array_equal(member.astype(np.float64).mean(axis=2), mean)
        a, b, p, w, scores = table_with_scores(cell, cell_rec, ids)
        views, _ = ranking.query_views(a, b, p)
        stored = np.load(OUT / f'private/evaluation/{cell}_query_metrics.npy', allow_pickle=False)
        for qi, (_, idx) in enumerate(views):
            for mi in range(scores.shape[1]):
                independent = independent_recovery(scores[idx, mi], p[idx])
                error = float(np.max(np.abs(independent - stored[qi, mi, :, :4])))
                assert error < 1e-11, (cell, qi, mi, error)
                max_error = max(max_error, error)
                checked += 12
        # The reused references must reproduce the completed combo report exactly.
        existing = list(csv.DictReader(open(old_combo_artifact(f'results/{cell}_metrics.csv'))))
        for model, mi in (('ipin_optimized', 1), ('tuna_retrained', 2), ('combo', 3)):
            for ki, k in enumerate(BUDGETS):
                r = next(r for r in existing if r['subgroup'] == 'all' and r['model'] == model and int(r['K']) == k)
                for j, metric in enumerate(ranking.METRICS):
                    assert abs(float(r[metric]) - stored[:, mi, ki, j].mean()) < 1e-11
                    reference_checks += 1
        print(f'Independent rank-counting audit passed: {cell}', flush=True)
    # Check all preserved inputs, existing results and checkpoint files again, byte for byte.
    for rec in frozen['source_records']:
        resolve(rec)
    report = dict(at_utc=now(), passed=True, independent_metric_checks=checked,
                  independent_max_abs_error=max_error, reproduced_reference_metrics=reference_checks,
                  unchanged_source_artifacts=len(frozen['source_records']), all_ensembles_verified=True,
                  selection_recomputed_from_development=True,
                  frozen_selections_not_changed_after_test=True,
                  evaluation=record(OUT / 'provenance/EVALUATION_COMPLETE.json'))
    write_json('provenance/AUDIT.json', report)
    print(json.dumps(report), flush=True)


def report():
    chosen = selection()
    audit = read_json(OUT / 'provenance/AUDIT.json')
    assert audit['passed']
    rows = list(csv.DictReader(open(OUT / 'results/all_panel_metrics.csv')))
    deltas = list(csv.DictReader(open(OUT / 'results/paired_comparisons.csv')))
    train = read_json(OUT / 'provenance/TRAINING_COMPLETE.json')
    models = (*REFERENCES, *VARIANTS)
    winner = chosen['primary_winner']
    def cell_row(cell, model, k):
        return next(r for r in rows if r['dataset'] == cell and r['subgroup'] == 'all' and
                    r['model'] == model and int(r['K']) == k)
    text = ['# Early-enrichment training: independent experiment', '',
            f'Completed {now()}. This study does not replace any existing model or result.', '',
            f'The C3-development-selected primary method is **{winner}**. '
            'This identity was frozen before new test predictions and never changed using test performance.', '',
            '## Development selection', '', '| Method | Epoch | C3-dev macro EF@20 |', '|---|---:|---:|']
    for c in chosen['candidates']:
        text.append(f"| {c['variant']} | {c['epoch']} | {c['EF20']:.4f} |")
    text += ['', 'Saved epoch-4/8 TUnA development results are in [saved_checkpoint_audit.csv](results/saved_checkpoint_audit.csv). '
             'That audit did not change the frozen TUnA comparator or initiate TUnA retraining.', '',
             '## Test comparison', '',
             'Recovery below means **mean known-positive hits per query** and **macro recall of the query’s known positives**. '
             'EF compares those hits with random ranking of that same query’s fixed P+U list. '
             'All methods use identical eligible queries and candidate lists. Budgets are never enlarged.', '']
    for cell in ('C1_test', 'C2_test', 'C3_test'):
        text += [f'### {cell}', '',
                 '| Model | EF@10 / 20 / 30 | Hits@10 / 20 / 30 | Recall % @10 / 20 / 30 |',
                 '|---|---:|---:|---:|']
        for model in models:
            entries = [cell_row(cell, model, k) for k in BUDGETS]
            ef = ' / '.join(f"{float(r['EF']):.2f}" for r in entries)
            hits = ' / '.join(f"{float(r['Hits']):.2f}" for r in entries)
            recall = ' / '.join(f"{100 * float(r['Recall']):.1f}" for r in entries)
            label = model + (' (dev-selected)' if model == winner else '')
            text.append(f'| {label} | {ef} | {hits} | {recall} |')
        selected = cell_row(cell, winner, 20)
        original = cell_row(cell, 'ipin_optimized', 20)
        difference = next(d for d in deltas if d['dataset'] == cell and d['subgroup'] == 'all' and
                          d['variant'] == winner and d['reference'] == 'ipin_optimized' and int(d['K']) == 20)
        delta = float(selected['EF']) - float(original['EF'])
        text += ['', f"At K=20, the prespecified winner changes EF by {delta:+.3f} "
                 f"({100*delta/float(original['EF']):+.1f}%) versus frozen optimized iPIN; "
                 f"paired 95% component-bootstrap interval: [{float(difference['EF_delta_low']):+.3f}, "
                 f"{float(difference['EF_delta_high']):+.3f}].", '']
    text += ['## Interpretation and limitations', '',
             'The three new-study rows are prespecified ablations, not three opportunities to choose a winner on test. '
             'The historical row tests checkpoint reselection without changing training. The query-balanced row changes '
             'global comparisons to same-query comparisons and targets the existing unweighted lists. The shortlist row '
             'adds bounded top-40 U emphasis after a common warmup epoch.', '',
             'Both new variants were initialized from scratch, using the original frozen 640-D ESM2-150M embeddings, '
             '498,053-parameter optimized-iPIN architecture, original AdamW settings, three seeds, and eight epochs. '
             'Embeddings were reused without changing sequence normalization. Each epoch sampled 2,000,000 same-query P/U '
             'comparisons, uniformly by query and partner, with an Nq/mean-Nq query scale. Original U design weights were '
             'not used: this objective is for the fixed unweighted lists. This is an EF-oriented surrogate, not a differentiable '
             'implementation of exact EF@20, and the top-40 emphasis is a fixed heuristic, not a tuned hyperparameter.', '',
             'U means unlabeled, not experimentally confirmed negative. High-scoring U may include real undiscovered '
             'interactors; emphasizing them can hurt biological discovery. Reported recovery is recovery of known P only. '
             'Results do not measure proteome-wide screening precision or validate novel interactions.', '',
             'Historical iPIN could only be selected between epochs 4 and 8; the new variants had eight checkpoint choices. '
             'Development results are selection-biased. Test has been inspected in earlier studies, so this is a bounded, '
             'prospectively specified experiment on an already-used test set, not a new untouched external validation.', '',
             'Intervals use 2,000 paired resamples of query sequence components with fixed candidate lists. They are '
             'conditional on this library, not adjusted for multiple comparisons, and do not fully model dependence from '
             'shared partner proteins. C2 train-side and test-side query breakdowns are retained in the CSV. Total oriented '
             'query hits may count the same physical pair from both endpoints; they are not unique interactions.', '',
             '## Files and integrity', '',
             '- [All panel metrics, confidence intervals, and C2 subgroups](results/all_panel_metrics.csv)',
             '- [Paired differences against all frozen references](results/paired_comparisons.csv)',
             '- [Development epoch curves](results/development_curves.csv)',
             '- [Panel coverage](results/panel_coverage.csv)',
             '- [Global weighted PU concordance (secondary)](results/global_concordance.csv)',
             '- [Frozen protocol](protocol.json) and [selection](provenance/SELECTION_FREEZE.json)',
             '- [Independent audit](provenance/AUDIT.json)', '',
             f"The training phase took {train['elapsed_seconds']/60:.2f} minutes on one GH200 GPU, including "
             '48 checkpoint saves and development scoring. All 48 new checkpoints are retained under `checkpoints/`; '
             'test member/ensemble scores are under `private/`. These are private, git-ignored artifacts. '
             'Per-query metric CSVs are under `results/`.', '',
             f"Audit: {audit['independent_metric_checks']:,} independent EF/hits/recall/rate checks, "
             f"{audit['reproduced_reference_metrics']} reproduced historical reference metrics, and "
             f"{audit['unchanged_source_artifacts']} existing source/checkpoint/result artifacts verified unchanged. "
             'The repository was mounted read-only during execution; only this new experiment folder was writable. '
             '`combo/` and all current models and results were left intact.', '']
    path = destination('REPORT.md')
    with path.open('x') as f:
        f.write('\n'.join(text))
    write_json('provenance/REPORT_MANIFEST.json', dict(at_utc=now(), report=record(path),
               audit=record(OUT / 'provenance/AUDIT.json')))
    print(f'Wrote {path}', flush=True)
