from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

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


def test_orchestrator_launches_exact_offline_deterministic_environment() -> None:
    path = Path("scripts/model/run_stage1_training_matrix_v1.py")
    specification = importlib.util.spec_from_file_location("stage1_orchestrator", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    command = module.invocation_command(
        Path("/project"),
        {"run_id": "fixture", "seed": 20260803},
        resume=False,
    )
    assert "--nv" in command
    assert "--cleanenv" in command
    assert "PYTHONHASHSEED=20260803" in command
    assert "CUBLAS_WORKSPACE_CONFIG=:4096:8" in command
    assert "HF_HUB_OFFLINE=1" in command
    assert "TRANSFORMERS_OFFLINE=1" in command
    assert "TOKENIZERS_PARALLELISM=false" in command
    assert "--resume-infrastructure" not in command
    resumed = module.invocation_command(
        Path("/project"),
        {"run_id": "fixture", "seed": 20260803},
        resume=True,
    )
    assert resumed[-1] == "--resume-infrastructure"


def test_orchestrator_records_non_overwriting_attempt_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = Path("scripts/model/run_stage1_training_matrix_v1.py")
    specification = importlib.util.spec_from_file_location("stage1_orchestrator_log", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "ok", ""),
    )
    run = {"run_id": "fixture", "seed": 20260803}
    completed, elapsed = module.invoke(tmp_path, run, resume=False)
    assert completed.returncode == 0
    assert elapsed >= 0
    log = tmp_path / module.RUN_ROOT / "orchestrator_logs/fixture.initial.json"
    assert log.is_file()
    assert module.logged_training_gpu_seconds(tmp_path) >= 0
    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        module.invoke(tmp_path, run, resume=False)
