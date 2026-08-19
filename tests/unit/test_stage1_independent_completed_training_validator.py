from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import torch


SCRIPT = Path("scripts/model/validate_stage1_completed_training_independent_v1.py")


def _module():
    specification = importlib.util.spec_from_file_location("independent_completed_training", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_independent_completed_training_import_boundary() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any(name.startswith("ipin_openppi") for name in imports)
    assert "torch" in imports


def test_clean_room_linear_forward_is_swap_symmetric() -> None:
    module = _module()
    generator = torch.Generator().manual_seed(5)
    a = torch.randn(4, 3, generator=generator)
    b = torch.randn(4, 3, generator=generator)
    state = {
        "output.weight": torch.randn(1, 10, generator=generator),
        "output.bias": torch.randn(1, generator=generator),
    }
    forward = module._independent_score("esm2_650m_linear_ablation", state, a, b)
    reverse = module._independent_score("esm2_650m_linear_ablation", state, b, a)
    assert torch.equal(forward, reverse)
