"""Paths, immutable I/O and qualified execution for the corrected PU study."""
import csv
import gzip
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PARENT = ROOT / 'benchmark/reference_organism_transfer_v1'
LOCAL = OUT / 'local'
CONFIG = json.loads((OUT / 'config.json').read_text())
MODELS = ('ipin_baseline', 'ipin_optimized', 'tuna_retrained')
NAMES = dict(zip(MODELS, ('Baseline iPIN', 'Optimized iPIN', 'TUnA retrained')))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def record(path):
    p = Path(path)
    return {'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)}


def verify(item):
    p = ROOT / item['path']
    require(sha(p) == item['sha256'], 'Checksum changed: ' + item['path'])
    require('bytes' not in item or p.stat().st_size == item['bytes'], 'Size changed: ' + item['path'])
    return p


def check_records(items):
    for item in items:
        verify(item)


def read(path):
    return json.loads(Path(path).read_text())


def table(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


def write_json(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def write_csv(path, rows):
    require(bool(rows), 'Empty table: ' + str(path))
    with Path(path).open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_gzip(path, value):
    with Path(path).open('xb') as f:
        with gzip.GzipFile(filename='', mode='wb', fileobj=f, mtime=0) as g:
            g.write((json.dumps(value, sort_keys=True) + '\n').encode())


def load_gzip(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)


def require_container():
    require(bool(os.environ.get('APPTAINER_CONTAINER')), 'Use a pinned accepted Apptainer image')


def keyed(*parts):
    return hashlib.sha256('|'.join(map(str, (CONFIG['seed'],) + parts)).encode()).hexdigest()


def degree_bin(n):
    return 0 if n < 3 else 1 if n < 10 else 2 if n < 30 else 3


def qualified_module(name):
    folder = ROOT / 'benchmark/nonhuman_transfer_v1'
    spec = importlib.util.spec_from_file_location('qualified_reference_pu_' + name, folder / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT, module.LOCAL, module.ROOT = OUT, LOCAL, ROOT
    module.CONFIG = {**CONFIG, 'species': [{'id': 'human_s288c_reference'}]}
    return module


def metric_module():
    p = ROOT / 'example/twelve_target_comparison_v1/metrics.py'
    spec = importlib.util.spec_from_file_location('reference_pu_rank_metrics', p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
