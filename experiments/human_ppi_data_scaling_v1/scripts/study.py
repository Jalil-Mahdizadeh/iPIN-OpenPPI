"""I/O and deterministic identities shared by this isolated human PPI study."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import numpy as np

SEEDS = [20260803, 20260817, 20260831]

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')

def record(path, root=None):
    p = Path(path)
    return {'path': str(p.relative_to(root) if root else p), 'sha256': sha(p), 'bytes': p.stat().st_size}

def arrays(path):
    with np.load(path, allow_pickle=False) as f:
        return {k: f[k].copy() for k in f.files}

def save(path, **values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        np.savez(f, **values)

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def pair_id(a, b):
    return 'pair:' + digest('|'.join(sorted((a, b))))

def c1_role(a, b):
    payload = 'ipin-openppi-pair-level-pu-r-protocol-v1:20260803:primary:C1:' + pair_id(a, b)
    bucket = int.from_bytes(hashlib.sha256(payload.encode()).digest()[:8], 'big') % 10000
    return 'train' if bucket < 7000 else 'development' if bucket < 8500 else 'test'

def codes(a, b, n):
    a, b = np.asarray(a, dtype=np.int64), np.asarray(b, dtype=np.int64)
    return np.minimum(a, b) * n + np.maximum(a, b)

def check(condition, message):
    if not condition:
        raise RuntimeError(message)
