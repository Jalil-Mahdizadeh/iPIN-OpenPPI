"""Synthetic tests of three-model custody; no model weights or pair data used."""
import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("freeze_v2_fixture", ROOT / "scripts/model/freeze_pair_models_v2.py")
freeze = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freeze)


def fixture():
    previous = {"models": {freeze.v1.BASELINE: {"original": "affine"}, freeze.v1.BEST: {"original": "residual"}}}
    inventory = []
    members = []
    for seed in freeze.SEEDS:
        member = {"seed": seed}
        for key, folder, suffix in (("state", "weights", "pt"), ("endpoint_features", "features", "npy")):
            item = {"path": f"{folder}/tuna_retrained_seed{seed}.{suffix}", "bytes": seed,
                    "sha256": (str(seed) * 8)[:64]}
            inventory.append(item)
            member[key] = dict(item)
        members.append(member)
    models = copy.deepcopy(previous["models"])
    models[freeze.THIRD] = {
        "status": "frozen", "selected_epoch": 4, "seeds": list(freeze.SEEDS), "members": members,
        "aggregation": freeze.AGGREGATION, "member_weights": [1, 1, 1], "weight_divisor": 3,
        "sigmoid_applied": False, "gp_covariance_refitted": False, "training_normalizer_used": False,
    }
    registry = {
        "roles": dict(freeze.ROLES), "model_order": [freeze.v1.BASELINE, freeze.v1.BEST, freeze.THIRD],
        "models": models,
        "model_bundles": {freeze.v1.BASELINE: freeze.v1.BUNDLE, freeze.v1.BEST: freeze.v1.BUNDLE, freeze.THIRD: freeze.BUNDLE},
        "aliases": {"tuna-retrained": freeze.THIRD, "ipin_tuna_retrained": freeze.THIRD},
        "claims": {"conclusive_primary_C3_superiority": False},
        "new_training_or_benchmark_scoring": False, "test_truth_or_pairs_accessed_for_release": False,
        "weights_publicly_redistributed": False,
    }
    return previous, registry, inventory


def test_three_models_retain_exact_existing_definitions():
    previous, registry, inventory = fixture()
    freeze.validate_registry(registry, previous)
    freeze.validate_member_records(registry["models"][freeze.THIRD], inventory)
    registry["models"][freeze.v1.BASELINE]["original"] = "replacement"
    with pytest.raises(RuntimeError, match="Existing frozen model"):
        freeze.validate_registry(registry, previous)


@pytest.mark.parametrize("field,value", [
    ("selected_epoch", 8), ("seeds", list(reversed(freeze.SEEDS))),
    ("member_weights", [1, 0, 1]), ("weight_divisor", 2),
    ("aggregation", "mean_probabilities"), ("sigmoid_applied", True),
    ("gp_covariance_refitted", True), ("training_normalizer_used", True),
])
def test_prediction_definition_drift_is_rejected(field, value):
    previous, registry, _ = fixture()
    registry["models"][freeze.THIRD][field] = value
    with pytest.raises(RuntimeError):
        freeze.validate_registry(registry, previous)


def test_missing_or_reordered_members_are_rejected():
    previous, registry, _ = fixture()
    registry["models"][freeze.THIRD]["members"].reverse()
    with pytest.raises(RuntimeError, match="seed membership"):
        freeze.validate_registry(registry, previous)
    registry["models"][freeze.THIRD]["members"].pop()
    with pytest.raises(RuntimeError, match="seed membership"):
        freeze.validate_registry(registry, previous)


@pytest.mark.parametrize("key", ["state", "endpoint_features"])
def test_a_different_seed_state_or_feature_file_is_rejected(key):
    _, registry, inventory = fixture()
    model = registry["models"][freeze.THIRD]
    model["members"][0][key] = dict(model["members"][1][key])
    with pytest.raises(RuntimeError, match="original scorer freeze"):
        freeze.validate_member_records(model, inventory)


def test_declared_superiority_is_not_part_of_this_freeze():
    previous, registry, _ = fixture()
    registry["claims"]["conclusive_primary_C3_superiority"] = True
    with pytest.raises(RuntimeError, match="claim drift"):
        freeze.validate_registry(registry, previous)


def test_existing_release_is_never_overwritten(tmp_path, monkeypatch):
    bundle = tmp_path / freeze.BUNDLE
    bundle.mkdir(parents=True)
    sentinel = bundle / "sentinel"
    sentinel.write_bytes(b"immutable")
    def forbidden(*args):
        pytest.fail("Creation inspected source inputs before rejecting an existing release")
    monkeypatch.setattr(freeze, "inputs", forbidden)
    with pytest.raises(FileExistsError):
        freeze.create(tmp_path)
    assert sentinel.read_bytes() == b"immutable"


def test_pin_rejects_content_drift_and_symlinks(tmp_path):
    source = tmp_path / "state"
    source.write_bytes(b"original tensors and GP covariance")
    digest = freeze.v1.sha(source)
    freeze.pinned(tmp_path, "state", digest)
    (tmp_path / "alias").symlink_to(source)
    with pytest.raises(RuntimeError, match="Symlink"):
        freeze.pinned(tmp_path, "alias", digest)
    source.write_bytes(b"changed GP covariance")
    with pytest.raises(RuntimeError):
        freeze.pinned(tmp_path, "state", digest)
