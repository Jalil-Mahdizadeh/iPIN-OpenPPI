from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/model/validate_stage1_pretraining_independent_v1.py")


def _load_module():
    specification = importlib.util.spec_from_file_location("independent_pretraining", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_independent_validator_import_boundary() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert "torch" not in imports
    assert not any(name.startswith("ipin_openppi") for name in imports)


def test_independent_window_order_and_parameter_algebra() -> None:
    module = _load_module()
    assert module._window_starts(1022) == (0,)
    assert module._window_starts(1023) == (0, 1)
    assert module._window_starts(2000) == (0, 894, 978)
    assert module._order_key(20260803, 1, "U", "pair-a").hex() == (
        "eb149944373db6115f1a7b47aeee3da5578350a734a1ab9521a1eb68a5dce1b1"
    )
    assert module._parameter_counts() == {
        "lightweight_esm2_150m_linear": 1922,
        "esm2_650m_linear_ablation": 3842,
        "esm2_650m_nonlinear_no_gate_ablation": 426625,
        "esm2_650m_partner_gated_primary": 492417,
    }
