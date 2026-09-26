"""Experiment-local provenance and atomic, resumable inference outputs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np

SEEDS = (20260803, 20260817, 20260831)
CELLS = ("C1", "C2", "C3")
PRIMARY = ("selected_31k", "ipin_baseline", "ipin_optimized", "tuna_retrained_ensemble", "tuna_original",
           "dscript_original", "dscript_retrained", "plm_interact_original_650m_humanv11",
           "rapppid_original_released_mult", "rapppid_recovery_mean_logit", "sprint_native_train_positive_graph",
           "cross_attention_ensemble", "mean_pool_ensemble")


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def record(path, root=None):
    p = Path(path)
    return {"path": str(p.relative_to(root) if root else p), "bytes": p.stat().st_size, "sha256": sha(p)}


def verify(path, item):
    p = Path(path)
    assert sha(p) == item["sha256"], str(p)
    if "bytes" in item:
        assert p.stat().st_size == item["bytes"], str(p)


def write(path, value, exclusive=True):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x" if exclusive else "w") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def atomic(path, value):
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".next")
    write(tmp, value, exclusive=False)
    tmp.replace(p)


def arrays(path):
    with np.load(path, allow_pickle=False) as stream:
        return {k: stream[k].copy() for k in stream.files}


def save(path, **values):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("xb") as stream:
        np.savez(stream, **values)


def codes(a, b, n):
    return np.minimum(a, b) * n + np.maximum(a, b)


def configure_cuda():
    import torch
    torch.set_num_threads(8)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    assert torch.cuda.is_available() and torch.cuda.device_count() == 1
    return torch.device("cuda")


def checked_bundle(root="/bundle"):
    root = Path(root)
    config = read(root / "SCORER_FREEZE.json")
    for item in config["files"]:
        verify(root / item["path"], item)
    return config
