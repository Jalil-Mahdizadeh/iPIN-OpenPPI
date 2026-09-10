from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest
import torch
from torch.nn import functional as F

from ipin_openppi.stage1.models import build_model


SCRIPT = Path("scripts/model/validate_development_completed_independent_v2.py")


def _module():
    spec = importlib.util.spec_from_file_location("independent_completed_v2", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _manifest(order: list[int], dimension: int) -> dict:
    return {
        "candidate_id": "fixture",
        "vector_count": len(order),
        "vectors": [
            {
                "row_index": row,
                "sequence_sha256": f"{protein:064x}",
                "sequence_length": 100 + protein,
                "candidate_id": "fixture",
                "vector_dimension": dimension,
            }
            for row, protein in enumerate(order)
        ][::-1],
    }


def test_validator_v2_has_no_production_imports_and_preserves_scientific_formulas() -> None:
    original = ast.parse(SCRIPT.with_name("validate_development_completed_independent_v1.py").read_text())
    corrected = ast.parse(SCRIPT.read_text())
    for node in ast.walk(corrected):
        if isinstance(node, ast.Import):
            assert all(not alias.name.startswith("ipin_openppi") for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("ipin_openppi")
    original_functions = {node.name: node for node in original.body if isinstance(node, ast.FunctionDef)}
    corrected_functions = {node.name: node for node in corrected.body if isinstance(node, ast.FunctionDef)}
    changed = {"_safe_regular", "_check", "_model_score_validation", "validate"}
    for name, node in original_functions.items():
        if name not in changed:
            assert ast.dump(node) == ast.dump(corrected_functions[name]), name


@pytest.mark.parametrize("family,dimension", [
    ("lightweight_esm2_150m_linear", 640),
    ("esm2_650m_linear_ablation", 1280),
    ("esm2_650m_nonlinear_no_gate_ablation", 1280),
    ("esm2_650m_partner_gated_primary", 1280),
])
def test_independent_storage_coordinate_translation_matches_training_forward(
    family: str, dimension: int,
) -> None:
    module = _module()
    values = np.random.default_rng(49).normal(size=(11, dimension)).astype(np.float32)
    stored_order = [8, 3, 10, 0, 6, 2, 9, 1, 5, 7, 4]
    stored = torch.from_numpy(values[stored_order])
    model = build_model(family, dropout=0.0, seed=20260803).eval()
    state = model.state_dict()
    projected = gate = None
    if "linear_ablation" not in family and "150m_linear" not in family:
        projected = F.gelu(F.linear(stored, state["projection.weight"], state["projection.bias"]))
        if family == "esm2_650m_partner_gated_primary":
            gate = torch.sigmoid(F.linear(projected, state["gate.weight"], state["gate.bias"]))
    original_a = [0, 2, 4, 6]
    original_b = [1, 3, 5, 10]
    with torch.inference_mode():
        expected = model(torch.from_numpy(values[original_a]), torch.from_numpy(values[original_b])).numpy()
    for endpoint_order in (list(range(11)), [10, 1, 6, 0, 8, 2, 4, 9, 7, 5, 3]):
        rows = module._storage_rows_from_manifest(
            [f"{protein:064x}" for protein in endpoint_order],
            [100 + protein for protein in endpoint_order],
            _manifest(stored_order, dimension), (11, dimension), "fixture",
        )
        lookup = {protein: row for row, protein in enumerate(endpoint_order)}
        a = np.asarray([lookup[protein] for protein in original_a])
        b = np.asarray([lookup[protein] for protein in original_b])
        observed = module._model_batch(
            family, state, stored, torch.from_numpy(rows[a]), torch.from_numpy(rows[b]), projected, gate,
        ).numpy()
        np.testing.assert_allclose(observed, expected, rtol=0, atol=1e-6)
        incorrect = module._model_batch(
            family, state, stored, torch.from_numpy(a), torch.from_numpy(b), projected, gate,
        ).numpy()
        assert not np.allclose(incorrect, expected, rtol=0, atol=1e-3)
        np.testing.assert_array_equal(stored.numpy(), values[stored_order])


@pytest.mark.parametrize("defect", [
    "duplicate_sha", "duplicate_row", "missing", "unknown", "out_of_range",
    "bool_row", "wrong_length", "wrong_dimension", "wrong_candidate", "duplicate_endpoint",
])
def test_independent_identity_map_fails_closed(defect: str) -> None:
    manifest = deepcopy(_manifest([2, 0, 3, 1], 3))
    hashes = [f"{index:064x}" for index in range(4)]
    records = manifest["vectors"]
    if defect == "duplicate_sha":
        records[1]["sequence_sha256"] = records[0]["sequence_sha256"]
        records[1]["sequence_length"] = records[0]["sequence_length"]
    elif defect == "duplicate_row":
        records[1]["row_index"] = records[0]["row_index"]
    elif defect == "missing":
        records.pop()
    elif defect == "unknown":
        records[1]["sequence_sha256"] = "f" * 64
    elif defect == "out_of_range":
        records[1]["row_index"] = 4
    elif defect == "bool_row":
        records[1]["row_index"] = True
    elif defect == "wrong_length":
        records[1]["sequence_length"] += 1
    elif defect == "wrong_dimension":
        records[1]["vector_dimension"] += 1
    elif defect == "wrong_candidate":
        records[1]["candidate_id"] = "wrong"
    else:
        hashes[1] = hashes[0]
    with pytest.raises(RuntimeError):
        _module()._storage_rows_from_manifest(hashes, [100, 101, 102, 103], manifest, (4, 3), "fixture")
