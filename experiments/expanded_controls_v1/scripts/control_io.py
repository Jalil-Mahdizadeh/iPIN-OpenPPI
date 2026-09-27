"""Experiment-local identities, immutable outputs and phase manifests."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path("/experiment")
OUT = Path("/output")
CELLS = ("C1", "C2", "C3")
COHORTS = ("legacy", "added")
FOLDS = ("development", "test")
FIXED = (
    "deterministic_hash", "training_degree_sum", "preferential_attachment",
    "component_degree_mass_product", "training_common_neighbors",
    "sequence_length_sum", "sequence_length_ratio", "within_pair_3mer_cosine",
    "exact_training_interolog_3mer", "pooled_150m_cosine", "aac_cosine",
)
ADDITIONAL = (
    "interolog_pooled_150m", "interolog_alignment_local", "interolog_alignment_coverage",
    "endpoint_linear", "endpoint_mlp64",
)
MODELS = ("selected_31k",) + FIXED + ADDITIONAL
KERNELS = {
    "kmer": "exact_training_interolog_3mer",
    "pooled": "interolog_pooled_150m",
    "local": "interolog_alignment_local",
    "coverage": "interolog_alignment_coverage",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def record(path, root=None):
    p = Path(path)
    return {"path": str(p.relative_to(root) if root else p),
            "bytes": p.stat().st_size, "sha256": sha(p)}


def verify(path, expected):
    p = Path(path)
    if p.stat().st_size != expected["bytes"] or sha(p) != expected["sha256"]:
        raise RuntimeError(f"frozen artifact changed: {p}")


def write(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x") as f:
        json.dump(obj, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")


def arrays(path):
    with np.load(path, allow_pickle=False) as data:
        return {k: data[k] for k in data.files}


def save(path, **values):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"refusing overwrite: {p}")
    temp = p.with_name(p.name + f".{os.getpid()}.tmp")
    with temp.open("xb") as f:
        np.savez(f, **values)
    temp.replace(p)


def save_array(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("xb") as f:
        np.save(f, value, allow_pickle=False)


def codes(a, b, n):
    a, b = np.asarray(a, dtype=np.int64), np.asarray(b, dtype=np.int64)
    if a.shape != b.shape or a.ndim != 1 or np.any(a == b):
        raise ValueError("invalid pair shapes or self-pairs")
    if np.any(a < 0) or np.any(b < 0) or np.any(a >= n) or np.any(b >= n):
        raise ValueError("endpoint outside frozen universe")
    return np.minimum(a, b) * n + np.maximum(a, b)


def check_pairs(a, b, n):
    keys = codes(a, b, n)
    if len(np.unique(keys)) != len(keys):
        raise ValueError("duplicate unordered candidate identity")
    return keys


def protocol():
    cfg = read(ROOT / "PROTOCOL.json")
    if tuple(cfg["fixed_controls"]) != FIXED or tuple(cfg["additional_controls"]) != ADDITIONAL:
        raise RuntimeError("control catalogue drift")
    return cfg


def phase_guard():
    freeze = read(ROOT / "IMPLEMENTATION_FREEZE.json")
    if sha(ROOT / "PROTOCOL.json") != freeze["protocol_sha256"]:
        raise RuntimeError("protocol changed after freeze")
    if sha(ROOT / "INPUT_FREEZE.json") != freeze["input_freeze_sha256"]:
        raise RuntimeError("input freeze changed")
    for item in freeze["code"]:
        verify(ROOT / item["path"], item)
    for item in freeze["libraries"]:
        verify(Path("/library") / item["path"], item)
    for item in freeze["native"]:
        verify(Path("/native") / item["path"], item)
    if Path("/upstream").exists():
        for item in freeze["upstream"]:
            verify(Path("/upstream") / item["path"], item)
    for item in freeze["preprocessing"]:
        verify(Path("/features") / Path(item["path"]).name, item)
    return freeze


def cuda():
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("one CUDA device required")
    torch.set_num_threads(8)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("deterministic CUBLAS workspace required")
    return torch.device("cuda")


def panel_names():
    for fold in FOLDS:
        for cell in CELLS:
            for cohort in COHORTS:
                yield fold, cell, cohort, f"{fold}_{cohort}_{cell}"


def manifest_files(manifest, base):
    for item in read(manifest)["files"]:
        verify(Path(base) / item["path"], item)


def summary(point, draws):
    finite = np.isfinite(draws)
    return {
        "point": float(point) if np.isfinite(point) else None,
        "ci95": np.quantile(draws[finite], [.025, .975]).tolist() if finite.mean() >= .95 else None,
        "finite_replicates": int(finite.sum()),
    }
