from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path("scripts/model/acquire_frozen_esm2_models_v1.py")
SPEC = importlib.util.spec_from_file_location("acquire_frozen_esm2", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_exact_candidates_revisions_and_safetensors_only() -> None:
    assert set(MODULE.CANDIDATES) == {"esm2_150m", "esm2_650m"}
    assert MODULE.CANDIDATES["esm2_150m"]["revision"] == "a695f6045e2e32885fa60af20c13cb35398ce30c"
    assert MODULE.CANDIDATES["esm2_650m"]["revision"] == "08e4846e537177426273712802403f7ba8261b6c"
    assert "model.safetensors" in MODULE.REQUIRED_FILES
    assert all(not name.endswith((".bin", ".pt", ".pth")) for name in MODULE.REQUIRED_FILES)


def test_custody_path_must_remain_within_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    MODULE.assert_within_project(project / "cache", project)
    with pytest.raises(RuntimeError, match="escapes project root"):
        MODULE.assert_within_project(tmp_path / "outside", project)


def test_custody_rejects_symlink(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = project / "link"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="symlink prohibited"):
        MODULE.assert_link_free(link / "model.safetensors", project)


def test_all_required_model_files_are_co_revision_metadata_or_safetensors() -> None:
    assert set(MODULE.REQUIRED_FILES) == {
        "README.md",
        "config.json",
        "model.safetensors",
        "special_tokens_map.json",
        "tokenizer_config.json",
        "vocab.txt",
    }
