from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
import torch

from ipin_openppi.stage1.constants import FAMILIES, SEEDS
from ipin_openppi.stage1.objective import learning_rate_multiplier
from ipin_openppi.stage1.training import atomic_torch_checkpoint, set_step_learning_rate


def test_matrix_algebra_is_exactly_thirty_runs() -> None:
    count = sum(len(spec["recipes"]) * len(SEEDS) for spec in FAMILIES.values())
    assert count == 30
    assert len(FAMILIES["lightweight_esm2_150m_linear"]["recipes"]) == 2
    assert len(FAMILIES["esm2_650m_linear_ablation"]["recipes"]) == 2
    assert len(FAMILIES["esm2_650m_nonlinear_no_gate_ablation"]["recipes"]) == 3
    assert len(FAMILIES["esm2_650m_partner_gated_primary"]["recipes"]) == 3


def test_step_learning_rate_uses_one_based_exact_schedule() -> None:
    parameter = torch.nn.Parameter(torch.ones(1))
    optimizer = torch.optim.AdamW([parameter], lr=1e-3)
    assert set_step_learning_rate(optimizer, 1e-3, 1) == pytest.approx(1e-3 / 123)
    assert optimizer.param_groups[0]["lr"] == pytest.approx(1e-3 / 123)
    assert set_step_learning_rate(optimizer, 1e-3, 123) == pytest.approx(1e-3)
    assert set_step_learning_rate(optimizer, 1e-3, 2445) == pytest.approx(1e-4)


def test_atomic_checkpoint_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "pass_01.pt"
    digest = atomic_torch_checkpoint(path, {"tensor": torch.arange(4), "pass_index": 1})
    assert len(digest) == 64
    loaded = torch.load(path, weights_only=False)
    assert loaded["pass_index"] == 1
    assert torch.equal(loaded["tensor"], torch.arange(4))


def test_all_run_code_dependencies_are_hash_bound() -> None:
    from ipin_openppi.stage1.preparation import CODE_PATHS

    names = {path.name for path in CODE_PATHS}
    assert {"constants.py", "models.py", "objective.py", "support.py", "training.py"} <= names
