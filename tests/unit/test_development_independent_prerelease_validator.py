from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import numpy as np
import torch


SCRIPT = Path("scripts/model/validate_development_prerelease_independent_v1.py")


def _module():
    specification = importlib.util.spec_from_file_location("independent_development_prerelease", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_independent_development_validator_import_boundary() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any(name.startswith("ipin_openppi") for name in imports)
    assert "torch" in imports


def test_clean_room_ht_half_tie_and_component_multiplier() -> None:
    module = _module()
    assert module._ht([0.5, 1.0], [0.0, 0.5, 2.0], [1.0, 2.0, 1.0]) == 0.625
    counts = np.asarray([2, 3, 0])
    observed = module._pair_multiplier(counts, np.asarray([0, 0, 1]), np.asarray([0, 1, 1]))
    np.testing.assert_array_equal(observed, [2, 6, 3])


def test_clean_room_nonlinear_forward_is_swap_symmetric() -> None:
    module = _module()
    generator = torch.Generator().manual_seed(3)
    a = torch.randn((4, 5), generator=generator)
    b = torch.randn((4, 5), generator=generator)
    state = {
        "projection.weight": torch.randn((3, 5), generator=generator),
        "projection.bias": torch.randn(3, generator=generator),
        "gate.weight": torch.randn((3, 3), generator=generator),
        "gate.bias": torch.randn(3, generator=generator),
        "hidden.weight": torch.randn((2, 10), generator=generator),
        "hidden.bias": torch.randn(2, generator=generator),
        "output.weight": torch.randn((1, 2), generator=generator),
        "output.bias": torch.randn(1, generator=generator),
    }
    forward = module._independent_score("esm2_650m_partner_gated_primary", state, a, b)
    reverse = module._independent_score("esm2_650m_partner_gated_primary", state, b, a)
    assert torch.equal(forward, reverse)
