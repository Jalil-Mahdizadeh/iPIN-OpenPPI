from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys

import numpy as np
import torch


SCRIPT = Path("scripts/model/validate_development_completed_independent_v1.py")


def _module():
    specification = importlib.util.spec_from_file_location(
        "independent_completed_development", SCRIPT
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def test_independent_completed_development_import_boundary() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any(name.startswith("ipin_openppi") for name in imports)
    assert "torch" in imports
    assert "pyarrow.parquet" in imports


def test_independent_model_forward_is_swap_symmetric() -> None:
    module = _module()
    generator = torch.Generator().manual_seed(17)
    embeddings = torch.randn(12, 4, generator=generator)
    state = {
        "output.weight": torch.randn(1, 13, generator=generator),
        "output.bias": torch.randn(1, generator=generator),
    }
    a = torch.tensor([0, 1, 2, 3])
    b = torch.tensor([8, 7, 6, 5])
    forward = module._model_batch(
        "esm2_650m_linear_ablation", state, embeddings, a, b, None, None
    )
    reverse = module._model_batch(
        "esm2_650m_linear_ablation", state, embeddings, b, a, None, None
    )
    assert torch.equal(forward, reverse)


def test_independent_metric_ties_and_component_draws() -> None:
    module = _module()
    p = np.asarray([0.5, 0.7], dtype=np.float64)
    u = np.asarray([0.2, 0.5, 0.8], dtype=np.float64)
    weights = np.asarray([1.0, 2.0, 1.0], dtype=np.float64)
    assert module._concordance(p, u, weights) == 0.625
    components, first = module._draws(["b", "a", "c", "a"], "fixture")
    _, second = module._draws(["c", "b", "a"], "fixture")
    assert components == ("a", "b", "c")
    assert first.shape == (2_000, 3)
    assert np.array_equal(first, second)
    assert np.all(first.sum(axis=1) == 3)
