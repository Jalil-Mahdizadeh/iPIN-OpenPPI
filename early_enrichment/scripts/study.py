"""Explicit, gated phases. Usage: bash early_enrichment/run.sh <phase>."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import unittest

import numpy as np
import torch

from common import *
from training import QuerySampler, train_all


def qualify():
    import test_study
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_study))
    if not result.wasSuccessful():
        raise RuntimeError('Unit qualification failed')
    env = environment()
    x, ids, meta, train, dev = load_inputs()
    sampler = QuerySampler(train, len(ids))
    assert len(sampler.queries) == 4675
    assert sampler.counts.min() >= 40
    qpos, queries, pi, ui = sampler.draw(20260803, 1, 100000)
    assert (np.asarray(meta['partition'])[queries] == 'train').all()
    assert (np.asarray(meta['partition'])[sampler.p_partner[pi]] == 'train').all()
    assert (np.asarray(meta['partition'])[sampler.u_partner[ui]] == 'train').all()
    model = head.build(640, SPEC, 20260803).cuda()
    assert sum(p.numel() for p in model.parameters()) == protocol()['expected_parameters']
    cp = historical_members(4)[0]
    head.load_state(resolve(cp['checkpoint']), model)
    embedding = torch.from_numpy(x).cuda()
    count = 16384
    actual = score(model, embedding, dev['a'][:count], dev['b'][:count])
    expected = np.load(resolve(cp['predictions']), allow_pickle=False)[:count]
    error = float(np.max(np.abs(actual.astype(float) - expected.astype(float))))
    assert np.allclose(actual, expected, rtol=2e-6, atol=2e-5), error
    reverse = score(model, embedding, dev['b'][:count], dev['a'][:count])
    assert np.array_equal(reverse, actual)
    model = head.build(640, SPEC, 20260803).cuda().train()
    qp = torch.as_tensor(queries[:128], device='cuda')
    pp = torch.as_tensor(sampler.p_partner[pi[:128]], device='cuda')
    up = torch.as_tensor(sampler.u_partner[ui[:128]], device='cuda')
    loss = torch.nn.functional.softplus(model(embedding[qp], embedding[up]) -
                                       model(embedding[qp], embedding[pp])).mean()
    loss.backward()
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    # Prove the source and output mounts enforce the intended boundary without writing a probe.
    mounts = [line for line in open('/proc/self/mountinfo') if ' /source ' in line or ' /work ' in line]
    assert any(' /source ro,' in line for line in mounts), mounts
    assert any(' /work rw,' in line for line in mounts), mounts
    report = dict(at_utc=now(), tests=result.testsRun, environment=env,
                  historical_prediction_max_abs_error=error, exact_pair_symmetry=True,
                  finite_gradient=True, train_queries=len(sampler.queries),
                  train_candidates_min=int(sampler.counts.min()),
                  train_candidates_median=float(np.median(sampler.counts)),
                  train_candidates_max=int(sampler.counts.max()), mount_evidence=mounts,
                  test_labels_accessed=False, code=local_code())
    write_json('provenance/QUALIFICATION.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('code', 'mount_evidence')}), flush=True)


def prepare():
    q = read_json(OUT / 'provenance/QUALIFICATION.json')
    for rec in q['code']:
        resolve(rec)
    paths = set()
    def add(path, expected=None):
        if expected:
            check(path, expected)
        paths.add(Path(path))
    source_freeze = BUNDLE / 'SEARCH_FREEZE.json'
    add(source_freeze, 'c321841b6d79f4ca4256f14f9f7463a5bf3b5dc0085cfa554a1dc3ba4c906f67')
    for r in read_json(source_freeze)['files']:
        if r['path'].startswith('code/') or r['path'] in (
                'data/esm2_150m.npy', 'data/endpoints.json', 'data/training.npz', 'data/development_00.npz'):
            add(BUNDLE / r['path'], r['sha256'])
    for epoch in protocol()['checkpoint_audit_epochs']:
        for member in historical_members(epoch):
            add(resolve(member['checkpoint']))
            add(resolve(member['predictions']))
            add(OLD_RUNS / f"stage2__esm2_150m__residual_wide__seed{member['seed']}/epoch_{epoch:02d}.json")
    for rel in ('SELECTION.json',):
        add(OLD_RUNS / rel)
    add(TUNA / 'data/sequences.json')
    add(TUNA / 'data/DATA_MANIFEST.json')
    add(TUNA / 'runs/scorer_bundle/SELECTION.json')
    add(TUNA / 'runs/scorer_bundle/SCORER_FREEZE.json')
    for c in read_json(TUNA / 'runs/scorer_bundle/SELECTION.json')['candidates']:
        for m in c['members']:
            for key in ('checkpoint', 'development_predictions'):
                r = m[key]
                add(TUNA / 'runs' / r['path'].removeprefix('/output/'), r['sha256'])
    # Hash existing tables without parsing labels. They are read only after prediction freeze.
    for base, manifest in ((TUNA / 'private/session', 'SESSION.json'),
                           (TUNA / 'private/references', 'REFERENCES.json')):
        add(base / manifest)
        for r in read_json(base / manifest)['files']:
            add(base / r['path'], r['sha256'])
    add(COMBO / 'provenance/RESULTS_MANIFEST.json')
    for r in read_json(COMBO / 'provenance/RESULTS_MANIFEST.json')['artifacts']:
        add(COMBO / r['path'], r['sha256'])
    # Also preserve all small combo code/provenance/report files, plus current model freezes.
    for p in COMBO.rglob('*'):
        if p.is_file() and not any(s in p.parts for s in ('runtime', '__pycache__', 'graphify-out')):
            if p.stat().st_size < 2_000_000:
                add(p)
    for p in (SOURCE / 'models').rglob('*'):
        if p.is_file():
            add(p)
    add(IMAGE, read_json(source_freeze)['model_image_sha256'])
    source_records = [record(p) for p in sorted(paths)]
    freeze = dict(at_utc=now(), code=local_code(), source_records=source_records,
                  qualification=record(OUT / 'provenance/QUALIFICATION.json'),
                  test_tables_parsed=False, outputs_exclusive_create=True)
    freeze['freeze_identity'] = hashlib.sha256(json.dumps(freeze, sort_keys=True).encode()).hexdigest()
    receipt = write_json('provenance/INPUT_FREEZE.json', freeze)
    write_json('provenance/INPUT_FREEZE_SHA256.json', receipt)
    print(f"Frozen protocol/code and {len(source_records)} unchanged source artifacts", flush=True)


def checkpoint_audit():
    assert_frozen()
    _, _, _, _, dev = load_inputs()
    views, census = ranking.query_views(dev['a'], dev['b'], dev['positive'])
    rows, candidates = [], []
    for model in ('ipin_optimized', 'tuna_retrained'):
        for epoch in protocol()['checkpoint_audit_epochs']:
            if model == 'ipin_optimized':
                members = historical_members(epoch)
                recs = [m['predictions'] for m in members]
            else:
                c = next(c for c in read_json(TUNA / 'runs/scorer_bundle/SELECTION.json')['candidates']
                         if c['epoch'] == epoch)
                recs = [record(check(TUNA / 'runs' / m['development_predictions']['path'].removeprefix('/output/'),
                                     m['development_predictions']['sha256'])) for m in c['members']]
                members = None
            scores = ensemble(recs)
            _, mean = dev_metrics(scores, dev, views)
            pred = write_npy(f'private/audit/{model}_epoch_{epoch:02d}_development.npy', scores)
            c = dict(model=model, epoch=epoch, EF20=float(mean[1, 0]), predictions=pred, members=members)
            candidates.append(c)
            for ki, k in enumerate(BUDGETS):
                rows.append(dict(model=model, epoch=epoch, K=k, queries=len(views),
                                 **dict(zip(ranking.METRICS, mean[ki].tolist()))))
            print(f"Saved-checkpoint audit {model} epoch={epoch} dev EF20={c['EF20']:.6f}", flush=True)
    best = earliest_best([c for c in candidates if c['model'] == 'ipin_optimized'])
    write_csv('results/saved_checkpoint_audit.csv', rows)
    write_json('provenance/CHECKPOINT_AUDIT.json', dict(at_utc=now(), census=census,
               candidates=candidates, historical_selected=best, test_read=False))


def select():
    freeze = assert_frozen()
    train = read_json(OUT / 'provenance/TRAINING_COMPLETE.json')
    assert train['identical_epoch1_verified']
    _, _, _, _, dev = load_inputs()
    views, census = ranking.query_views(dev['a'], dev['b'], dev['positive'])
    audit = read_json(OUT / 'provenance/CHECKPOINT_AUDIT.json')
    historical = dict(audit['historical_selected'], variant='historical_ef_selected')
    chosen = [historical]
    curves = []
    for variant in protocol()['new_training_variants']:
        candidates = []
        for epoch in protocol()['evaluation_epochs']:
            members = [next(r for r in train['records'] if r['variant'] == variant and
                            r['seed'] == seed and r['epoch'] == epoch) for seed in protocol()['seeds']]
            scores = ensemble([m['predictions'] for m in members])
            _, mean = dev_metrics(scores, dev, views)
            pred = write_npy(f'private/development/{variant}_epoch_{epoch:02d}.npy', scores)
            c = dict(variant=variant, epoch=epoch, EF20=float(mean[1, 0]), predictions=pred,
                     members=[dict(seed=m['seed'], checkpoint=m['checkpoint'], predictions=m['predictions'])
                              for m in members])
            candidates.append(c)
            for ki, k in enumerate(BUDGETS):
                curves.append(dict(variant=variant, epoch=epoch, K=k, queries=len(views),
                                   **dict(zip(ranking.METRICS, mean[ki].tolist()))))
        chosen.append(earliest_best(candidates))
    best = max(c['EF20'] for c in chosen)
    winner = next(c for c in chosen if best - c['EF20'] <= protocol()['selection_tolerance'])
    selection = dict(at_utc=now(), primary_winner=winner['variant'], candidates=chosen,
                     criterion='C3-development macro EF@20 only', test_read=False, census=census,
                     input_freeze=record(OUT / 'provenance/INPUT_FREEZE.json'),
                     code=freeze['code'], development_curves=write_csv('results/development_curves.csv', curves),
                     training_complete=record(OUT / 'provenance/TRAINING_COMPLETE.json'),
                     checkpoint_audit=record(OUT / 'provenance/CHECKPOINT_AUDIT.json'))
    rec = write_json('provenance/SELECTION_FREEZE.json', selection)
    write_json('provenance/SELECTION_FREEZE_SHA256.json', rec)
    print(json.dumps(dict(primary=winner['variant'], selected=[dict(variant=c['variant'], epoch=c['epoch'],
                       EF20=c['EF20']) for c in chosen])), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase', choices=('qualify', 'prepare', 'checkpoint-audit', 'train', 'select',
                                     'score', 'evaluate', 'audit', 'report'))
    args = ap.parse_args()
    from evaluation import score_test, evaluate, audit_results, report
    actions = {'qualify': qualify, 'prepare': prepare, 'checkpoint-audit': checkpoint_audit,
               'train': train_all, 'select': select, 'score': score_test, 'evaluate': evaluate,
               'audit': audit_results, 'report': report}
    started = time.monotonic()
    actions[args.phase]()
    print(f'{args.phase} completed in {time.monotonic() - started:.2f} s', flush=True)


if __name__ == '__main__':
    main()
