from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/model/validate_stage1_training_preparation_independent_v1.py")


def _module():
    specification = importlib.util.spec_from_file_location("independent_preparation", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_independent_preparation_validator_import_boundary() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert "torch" not in imports
    assert not any(name.startswith("ipin_openppi") for name in imports)


def test_independent_preparation_matrix_and_order_fixture() -> None:
    module = _module()
    runs = module._expected_runs()
    assert len(runs) == len({run["run_id"] for run in runs}) == 30
    assert runs[0] == {
        "candidate_id": "esm2_150m",
        "family": "lightweight_esm2_150m_linear",
        "recipe_id": "linear_lr3e-4",
        "run_id": "lightweight_esm2_150m_linear__linear_lr3e-4__seed20260803",
        "seed": 20260803,
    }
    pair_ids = ["pair-c", "pair-a", "pair-b"]
    assert module._order(pair_ids, 20260803, 1, "U").tolist() == [0, 2, 1]
