"""Synthetic promotion/custody tests; no learned weights or biological pairs."""
import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("freeze_v3_fixture", ROOT / "scripts/model/freeze_pair_models_v3.py")
freeze = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freeze)


def fixture():
    names = [freeze.v1.BASELINE, freeze.v1.BEST, freeze.v2.THIRD]
    previous = {"model_order": names, "models": {n: {"historical": n} for n in names},
                "model_bundles": {n: f"old/{i}" for i, n in enumerate(names)},
                "aliases": {"tuna-retrained": freeze.v2.THIRD, "ipin_tuna_retrained": freeze.v2.THIRD}}
    source, selected, members = [], [], []
    for seed in freeze.SEEDS:
        member = {"seed": seed}
        original = {"seed": seed, "name": f"scaled_31188_seed{seed}"}
        for key, source_key, folder, suffix in (("state", "weights", "weights", "pt"),
                                               ("endpoint_features", "features", "features", "npy")):
            item = {"path": f"frozen/scaled_31188_seed{seed}.{suffix}", "sha256": f"{seed:064x}", "bytes": 100}
            original[source_key] = item
            member[key] = {**item, "path": f"{folder}/ipin_tuna_31k_seed{seed}.{suffix}"}
        checkpoint = {**original["weights"], "path": f"training/budget_31188/seed_{seed}/epoch_01.pt"}
        selected.append({"seed": seed, "checkpoint": checkpoint})
        member["training_checkpoint"] = {**checkpoint, "path": f"{freeze.STUDY}/runs/{checkpoint['path']}"}
        members.append(member)
        source.append(original)
    model = {"display_name": "iPIN-TUnA-31k", "status": "frozen", "training_positive_pairs": 31188,
             "selected_epoch": 1, "seeds": list(freeze.SEEDS), "members": members,
             "member_weights": [1, 1, 1], "weight_divisor": 3, "aggregation": freeze.v2.AGGREGATION,
             "sigmoid_applied": False, "gp_covariance_refitted": False, "gp_fitted_before_eval": True,
             "update_precision": False, "training_normalizer_used": False,
             "benchmark_result_id": "selected_31k", "endpoint_feature_shape": [17583, 64]}
    registry = {"release_id": freeze.RELEASE, "primary_model": freeze.PRIMARY, "default_model": freeze.PRIMARY,
                "roles": dict(freeze.ROLES), "model_order": names + [freeze.PRIMARY],
                "models": {**copy.deepcopy(previous["models"]), freeze.PRIMARY: model},
                "model_bundles": {**previous["model_bundles"], freeze.PRIMARY: freeze.BUNDLE},
                "aliases": {**previous["aliases"], **freeze.ALIASES},
                "claims": {"best_observed_test2_macro_C1_C2_C3": True, "pointwise_C3_intervals_above_zero": True,
                           "previously_examined_test": True, "PLM_interact_higher_on_added_C3": True,
                           "independent_replication": False, "multiplicity_adjusted_intervals": False,
                           "universal_superiority": False, "calibrated_binding_probability": False,
                           "direct_binding_or_partner_specific_generalization_established": False,
                           "TUnA_architecture_is_original_iPIN_work": False},
                "new_training_or_benchmark_scoring": False, "test_truth_or_pairs_accessed_for_release": False,
                "weights_publicly_redistributed": False}
    return previous, registry, {"members": source}, {"selected": {"members": selected}}


def test_primary_is_new_fourth_model_with_unchanged_historical_entries():
    previous, registry, source, selection = fixture()
    freeze.validate_registry(registry, previous)
    freeze.validate_members(registry["models"][freeze.PRIMARY], source, selection)
    registry["models"][freeze.v2.THIRD]["historical"] = "rewritten as 31k"
    with pytest.raises(RuntimeError, match="Historical frozen model changed"):
        freeze.validate_registry(registry, previous)


@pytest.mark.parametrize("field", ["primary_model", "default_model"])
def test_stale_primary_or_default_is_rejected(field):
    previous, registry, _, _ = fixture()
    registry[field] = freeze.v2.THIRD
    with pytest.raises(RuntimeError, match="identity/role"):
        freeze.validate_registry(registry, previous)


def test_historical_alias_cannot_be_redirected_to_new_model():
    previous, registry, _, _ = fixture()
    registry["aliases"]["tuna-retrained"] = freeze.PRIMARY
    with pytest.raises(RuntimeError, match="identity/role"):
        freeze.validate_registry(registry, previous)


@pytest.mark.parametrize("field,value", [
    ("selected_epoch", 4), ("training_positive_pairs", 16799),
    ("member_weights", [1, 0, 1]), ("weight_divisor", 2),
    ("aggregation", "mean_probabilities"), ("sigmoid_applied", True),
    ("gp_covariance_refitted", True), ("gp_fitted_before_eval", False),
    ("update_precision", True), ("endpoint_feature_shape", [17000, 64]),
])
def test_prediction_identity_changes_are_rejected(field, value):
    previous, registry, _, _ = fixture()
    registry["models"][freeze.PRIMARY][field] = value
    with pytest.raises(RuntimeError, match="prediction definition"):
        freeze.validate_registry(registry, previous)


def test_seed_dropping_and_reordering_are_rejected():
    previous, registry, _, _ = fixture()
    members = registry["models"][freeze.PRIMARY]["members"]
    members.reverse()
    with pytest.raises(RuntimeError, match="seed membership"):
        freeze.validate_registry(registry, previous)
    members.pop()
    with pytest.raises(RuntimeError, match="seed membership"):
        freeze.validate_registry(registry, previous)


@pytest.mark.parametrize("key", ["state", "endpoint_features", "training_checkpoint"])
def test_cross_seed_artifact_substitution_is_rejected(key):
    _, registry, source, selection = fixture()
    model = registry["models"][freeze.PRIMARY]
    model["members"][0][key] = dict(model["members"][1][key])
    with pytest.raises(RuntimeError):
        freeze.validate_members(model, source, selection)


@pytest.mark.parametrize("field,value", [
    ("independent_replication", True), ("multiplicity_adjusted_intervals", True),
    ("universal_superiority", True), ("PLM_interact_higher_on_added_C3", False),
    ("calibrated_binding_probability", True), ("TUnA_architecture_is_original_iPIN_work", True),
])
def test_overstated_promotion_claims_are_rejected(field, value):
    previous, registry, _, _ = fixture()
    registry["claims"][field] = value
    with pytest.raises(RuntimeError, match="claim drift"):
        freeze.validate_registry(registry, previous)


@pytest.mark.parametrize("namespace", [freeze.PUBLIC, freeze.BUNDLE])
def test_creation_never_overwrites_a_release(tmp_path, monkeypatch, namespace):
    directory = tmp_path / namespace
    directory.mkdir(parents=True)
    sentinel = directory / "sentinel"
    sentinel.write_bytes(b"preserve")
    monkeypatch.setattr(freeze, "inputs", lambda *args: pytest.fail("Existing release must be rejected before input reads"))
    with pytest.raises(FileExistsError):
        freeze.create(tmp_path)
    assert sentinel.read_bytes() == b"preserve"
