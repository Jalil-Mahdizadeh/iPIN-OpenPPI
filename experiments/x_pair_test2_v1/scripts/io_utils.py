"""Experiment-local, atomic provenance helpers."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODELS = ('multitask_xfair', 'interaction_xfair')
CELLS = ('C1', 'C2', 'C3')
COHORTS = ('legacy', 'added')

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20), b''):
            h.update(block)
    return h.hexdigest()

def record(path, root=ROOT):
    path=Path(path)
    return {'path':str(path.relative_to(root)), 'bytes':path.stat().st_size, 'sha256':sha(path)}

def verify(path, expected):
    path=Path(path)
    assert path.stat().st_size == expected['bytes'], str(path)
    assert sha(path) == expected['sha256'], str(path)

def atomic(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    temp.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
    temp.replace(path)

def arrays(path):
    with np.load(path,allow_pickle=False) as source:
        return {k:source[k].copy() for k in source.files}

def save(path, **values):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:
        np.savez(stream,**values)

def cuda():
    import torch
    torch.set_num_threads(8)
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    assert torch.cuda.is_available() and torch.cuda.device_count()==1
    return torch.device('cuda')
