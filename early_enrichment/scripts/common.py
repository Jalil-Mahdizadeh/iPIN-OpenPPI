"""Read-only dependencies and exclusive-create outputs for the separate study."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

OUT = Path(__file__).resolve().parents[1]
SOURCE = Path('/source') if Path('/source').is_dir() else OUT.parent
BUNDLE = SOURCE / '.private/model_optimization_v1/bundle'
OLD_RUNS = SOURCE / '.private/model_optimization_v1/runs'
TUNA = SOURCE / 'benchmark/tuna'
COMBO = SOURCE / 'combo'
IMAGE = SOURCE / 'containers/images/ipin-model-arm64_0.1.0.sif'
SPEC = dict(family='residual_mlp', width=256, dropout=0.3)
BUDGETS = (10, 20, 30)
VARIANTS = ('historical_ef_selected', 'query_balanced', 'shortlist_weighted')
REFERENCES = ('ipin_baseline', 'ipin_optimized', 'tuna_retrained', 'combo_55_45')


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def check(path, expected):
    if sha(path) != expected:
        raise ValueError(f'Hash mismatch: {path}')
    return Path(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def destination(relative):
    p = (OUT / relative).resolve()
    if not p.is_relative_to(OUT) or p == OUT:
        raise ValueError('Output must be inside early_enrichment')
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_json(relative, value):
    p = destination(relative)
    with p.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')
    return record(p)


def write_csv(relative, rows):
    if not rows:
        raise ValueError('Empty CSV')
    p = destination(relative)
    with p.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return record(p)


def write_npy(relative, value):
    p = destination(relative)
    with p.open('xb') as f:
        np.save(f, value, allow_pickle=False)
    return record(p)


def record(path):
    p = Path(path).resolve()
    root, scope = (OUT, 'study') if p.is_relative_to(OUT) else (SOURCE, 'source')
    return dict(scope=scope, path=str(p.relative_to(root)), bytes=p.stat().st_size, sha256=sha(p))


def resolve(rec, verify=True):
    p = (OUT if rec['scope'] == 'study' else SOURCE) / rec['path']
    return check(p, rec['sha256']) if verify else p


def module(name, path, expected):
    check(path, expected)
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


head = module('frozen_ipin_head', BUNDLE / 'code/ipin_openppi/model_optimization/models.py',
              '90574feb103458cf56ae6ddf7b2800bb53b7a97314353d7cc620995496a0ca59')
ranking = module('frozen_fixed_list_metrics', COMBO / 'scripts/metrics.py',
                 '073e8d4b7816bc0ccc69c6b72bfff89cbad75f59fd93a02e62e4bd47587c5824')


def protocol():
    return read_json(OUT / 'protocol.json')


def local_code():
    return [record(p) for p in sorted((OUT / 'scripts').glob('*.py'))] + [
        record(OUT / 'protocol.json'), record(OUT / 'run.sh')]


def assert_frozen():
    freeze = read_json(resolve(read_json(OUT / 'provenance/INPUT_FREEZE_SHA256.json')))
    for rec in freeze['code']:
        resolve(rec)
    return freeze


def environment():
    torch.set_num_threads(8)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    if not torch.cuda.is_available():
        raise RuntimeError('This launcher requires the allocated GPU')
    return dict(torch=torch.__version__, numpy=np.__version__, cuda=torch.version.cuda,
                device=torch.cuda.get_device_name(0), deterministic=True, tf32=False)


def load_inputs():
    frozen = read_json(BUNDLE / 'SEARCH_FREEZE.json')
    for rel in ('data/esm2_150m.npy', 'data/endpoints.json', 'data/training.npz', 'data/development_00.npz'):
        r = next(r for r in frozen['files'] if r['path'] == rel)
        check(BUNDLE / rel, r['sha256'])
    x = np.load(BUNDLE / 'data/esm2_150m.npy', allow_pickle=False)
    ids = np.asarray(read_json(BUNDLE / 'data/endpoints.json'))
    meta = read_json(TUNA / 'data/sequences.json')
    check(TUNA / 'data/sequences.json', 'bc7a91661ea05cbfdcf3551b9a4d18c149ac077549ebbcf0be7e7ef5d94ace77')
    assert np.array_equal(ids, meta['sha256'])
    assert x.shape == (len(ids), 640) and np.isfinite(x).all()
    assert (np.linalg.norm(x, axis=1) > 0).all()
    with np.load(BUNDLE / 'data/training.npz', allow_pickle=False) as f:
        train = {k: f[k] for k in f.files}
    with np.load(BUNDLE / 'data/development_00.npz', allow_pickle=False) as f:
        dev = {k: f[k] for k in f.files if k != 'baseline'}
    part = np.asarray(meta['partition'])
    for k in ('p_a', 'p_b', 'u_a', 'u_b'):
        assert (part[train[k]] == 'train').all()
    assert (part[dev['a']] == 'development').all()
    assert (part[dev['b']] == 'development').all()
    for a, b in ((np.r_[train['p_a'], train['u_a']], np.r_[train['p_b'], train['u_b']]),
                 (dev['a'], dev['b'])):
        # Integer canonical keys catch reversed duplicates and conflicting labels.
        keys = np.minimum(a, b) * len(ids) + np.maximum(a, b)
        assert len(np.unique(keys)) == len(keys)
    return x, ids, meta, train, dev


@torch.inference_mode()
def score(model, x, a, b, batch=16384):
    model.eval()
    out = np.empty(len(a), dtype=np.float32)
    for lo in range(0, len(a), batch):
        hi = min(lo + batch, len(a))
        ia = torch.as_tensor(a[lo:hi], dtype=torch.long, device=x.device)
        ib = torch.as_tensor(b[lo:hi], dtype=torch.long, device=x.device)
        out[lo:hi] = model(x[ia], x[ib]).cpu().numpy()
    assert np.isfinite(out).all()
    return out


def ensemble(records):
    arrays = [np.load(resolve(r), allow_pickle=False) for r in records]
    assert len(arrays) == 3 and all(a.shape == arrays[0].shape for a in arrays)
    return np.stack(arrays).astype(np.float64).mean(axis=0)


def dev_metrics(scores, dev, views=None):
    if views is None:
        views, _ = ranking.query_views(dev['a'], dev['b'], dev['positive'])
    values = np.asarray([ranking.rank_metrics(scores[idx], dev['positive'][idx], BUDGETS)
                         for _, idx in views])
    return values, values.mean(axis=0)


def earliest_best(rows, key='EF20'):
    best = max(r[key] for r in rows)
    return min((r for r in rows if best - r[key] <= protocol()['selection_tolerance']),
               key=lambda r: r['epoch'])


def historical_members(epoch):
    members = []
    for seed in protocol()['seeds']:
        base = OLD_RUNS / f'stage2__esm2_150m__residual_wide__seed{seed}'
        metadata = read_json(base / f'epoch_{epoch:02d}.json')
        checkpoint = check(OLD_RUNS / metadata['checkpoint'], metadata['checkpoint_sha256'])
        predictions = check(OLD_RUNS / metadata['predictions'], metadata['prediction_sha256'])
        members.append(dict(seed=seed, checkpoint=record(checkpoint), predictions=record(predictions)))
    return members


def lr_at(step, total, peak):
    warmup = max(1, math.ceil(0.05 * total))
    if step < warmup:
        return peak * (step + 1) / warmup
    progress = (step - warmup) / max(1, total - warmup - 1)
    return peak * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, progress))))
