"""Experiment-local immutable I/O; production inputs are mounted read-only."""
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import os

HERE = Path(__file__).resolve().parents[1]
ROOT = Path('/project') if os.environ.get('APPTAINER_CONTAINER') else HERE.parents[1]
OUT = Path('/work') if os.environ.get('APPTAINER_CONTAINER') else HERE
STUDIES = ('nonhuman_transfer_v1', 'reference_organism_pu_transfer_v1')
NEW = 'ipin_tuna_31k'
OLD = ('ipin_baseline', 'ipin_optimized', 'tuna_retrained')
MODELS = (*OLD, NEW)
LABELS = dict(zip(MODELS, ('Original iPIN', 'Optimized iPIN', 'Previous TUnA (17k)', 'iPIN-TUnA-31k')))
BUNDLE = ROOT / '.private/frozen_pair_models_v3/bundle'
DATA = ROOT / 'experiments/human_ppi_data_scaling_v1/data'
REGISTRY = ROOT / 'artifacts/models/frozen_pair_models_v3/MODEL_REGISTRY.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text())


def table(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def record(path):
    path = Path(path)
    relative = str(path.relative_to(OUT)) if path.is_relative_to(OUT) else str(path.relative_to(ROOT))
    return {'path': relative, 'scope': 'experiment' if path.is_relative_to(OUT) else 'repository',
            'bytes': path.stat().st_size, 'sha256': sha(path)}


def resolve(item):
    return (OUT if item.get('scope') == 'experiment' else ROOT) / item['path']


def verify(item):
    path = resolve(item)
    require(path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], 'Changed input: ' + str(path))


def write_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def metrics_module():
    path = ROOT / 'example/twelve_target_comparison_v1/metrics.py'
    spec = importlib.util.spec_from_file_location('historical_transfer_metrics', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_small_inputs(freeze):
    for item in freeze['inputs']:
        if item['bytes'] < (1 << 30):
            verify(item)

