from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/platform/validate_model_runtime_v0_1_0.py")
SPEC = importlib.util.spec_from_file_location("validate_model_runtime", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_validator_binds_exact_runtime_and_candidates() -> None:
    assert MODULE.SIF_SHA256 == "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"
    assert MODULE.SIF_BYTES == 10_656_620_544
    assert set(MODULE.CANDIDATES) == {"esm2_150m", "esm2_650m"}
    assert MODULE.CANDIDATES["esm2_150m"]["hidden_size"] == 640
    assert MODULE.CANDIDATES["esm2_650m"]["hidden_size"] == 1280


def test_validator_excludes_sensitive_paths_and_pickle_weights() -> None:
    assert "/sealed/" in MODULE.FORBIDDEN_PATH_FRAGMENTS
    assert "/.private/" in MODULE.FORBIDDEN_PATH_FRAGMENTS
    assert "model.safetensors" in MODULE.EXPECTED_FILES
    assert all(not filename.endswith((".bin", ".pt", ".pth")) for filename in MODULE.EXPECTED_FILES)
