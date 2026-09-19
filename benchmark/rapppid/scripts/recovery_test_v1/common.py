"""Benchmark-local identities, weighted PU metric and reproducible CUDA setup."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import numpy as np

SEEDS = (20260803, 20260817, 20260831)
EVALUATION_EPOCHS = (4, 8, 12, 16, 20)
SIF_SHA = 'e853a89768c5351927f90fd0ccfb2ad899a15a6fc239a9014726af0c34442d48'
UPSTREAM_COMMIT = 'c3a28be56fb3bd96ccf8cc44ea9145cfcadeaf6c'
DATA_SHA = '43ae252277820ffe527dad1ed4839d5673cff279b6c8c943ff4b5350a9283ca6'
DEV_SHA = '8a1f61a429a2b79c9a41dd1e7f6d02ece58bf93adc9a8c9b07233f930a5422e5'
SEQUENCES_SHA = 'bc7a91661ea05cbfdcf3551b9a4d18c149ac077549ebbcf0be7e7ef5d94ace77'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix('.next.json')
    write(temporary, value)
    temporary.replace(path)


def record(path, root=None):
    path = Path(path)
    return {'path': str(path.relative_to(root) if root else path),
            'bytes': path.stat().st_size, 'sha256': sha(path)}


def verify(root, records):
    for item in records:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise RuntimeError('Unsafe manifest path')
        path = Path(root) / relative
        if path.is_symlink() or path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            raise RuntimeError(f'Frozen input changed: {relative}')


def arrays(path):
    with np.load(path, allow_pickle=False) as handle:
        return {name: handle[name].copy() for name in handle.files}


def concordance(scores, positive, weights):
    scores = np.asarray(scores, np.float64)
    positive = np.asarray(positive, bool)
    weights = np.asarray(weights, np.float64)
    if scores.shape != positive.shape or weights.shape != scores.shape:
        raise ValueError('Metric shape mismatch')
    if not np.isfinite(scores).all() or not positive.any() or positive.all():
        raise ValueError('Invalid PU classes or scores')
    u = scores[~positive]
    w = weights[~positive]
    if not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError('Invalid design weights')
    order = np.argsort(u, kind='stable')
    u = u[order]
    prefix = np.concatenate(([0.], np.cumsum(w[order], dtype=np.float64)))
    lo = np.searchsorted(u, scores[positive], side='left')
    hi = np.searchsorted(u, scores[positive], side='right')
    return float(np.mean((prefix[lo] + prefix[hi]) * .5) / prefix[-1])


def cuda(seed=20260803):
    import torch
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    if not torch.cuda.is_available():
        raise RuntimeError('An allocated CUDA GPU is required')
    torch.set_num_threads(8)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    return torch.device('cuda')

# Test panel definitions reused unchanged from the original benchmark.
CELLS = ('C1_test', 'C2_test', 'C3_test')
P_COUNTS = {'C1_test': 3187, 'C2_test': 13446, 'C3_test': 2379}
