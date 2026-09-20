"""Utilities for the external fixed-model study; never opens human test pairs.

The module name deliberately avoids the pinned TUnA adapter's ``common``.
"""
from __future__ import annotations
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
CONFIG = json.loads((OUT / 'config.json').read_text())
LOCAL = OUT / 'local'
MODELS = ('ipin_baseline', 'ipin_optimized', 'tuna_retrained')

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()

def record(path):
    p = Path(path)
    return dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=sha(p))

def read(path):
    return json.loads(Path(path).read_text())

def write_json(path, obj):
    with Path(path).open('x') as f:
        json.dump(obj, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')

def write_csv(path, rows, columns=None):
    rows = list(rows)
    with Path(path).open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns or list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

def table(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))

def keyed(*parts):
    return hashlib.sha256((':'.join(map(str, (CONFIG['seed'], *parts)))).encode()).hexdigest()

def require_container():
    if not os.environ.get('APPTAINER_CONTAINER'):
        raise RuntimeError('Execute scientific work in a pinned Apptainer image')

def check_records(records):
    for r in records:
        p = ROOT / r['path']
        if sha(p) != r['sha256'] or p.stat().st_size != r['bytes']:
            raise RuntimeError(f'Frozen artifact changed: {p}')

def degree_bin(n):
    return 0 if n <= 2 else 1 if n <= 9 else 2 if n <= 29 else 3
