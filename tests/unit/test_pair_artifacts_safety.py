from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ipin_openppi.ingestion.schema import load_contract
from ipin_openppi.pair_artifacts.support import load_yaml, validate_config


CONFIG = Path("configs/pair_level_pu_r_benchmark_artifacts_v1.yaml")
SCHEMA = Path("schemas/canonical/pair_level_pu_r_benchmark_artifacts_v1.yaml")


def test_artifact_config_freezes_scope_sampling_and_sealing() -> None:
    config = load_yaml(CONFIG)
    validate_config(config)
    assert config["authorization"]["deterministic_unlabeled_sample_realization"] is True
    assert (
        config["authorization"]["full_candidate_pair_universe_materialization"] is False
    )
    assert config["authorization"]["model_evaluation"] is False
    assert config["sampling"]["public_salt"] == "ipin-openppi-benchmark-v1"
    assert config["sampling"]["deterministic_seed"] == "20260803"
    assert config["sampling"]["cross_cell_unlabeled_pair_reuse_permitted"] is True
    assert config["sealing"]["development_candidate_truth_key_separation"] is True
    assert config["protected_evaluator"][
        "prediction_sha256_before_truth_decryption"
    ] == ("required")
    assert config["protected_evaluator"]["scorer_input_projection"] == [
        "candidate_token",
        "endpoint_a_sha256",
        "endpoint_b_sha256",
        "cell_id",
    ]
    assert config["protected_evaluator"]["receipt_root"] == (
        "artifacts/validation/protected_evaluation_receipts"
    )

    unsafe = deepcopy(config)
    unsafe["authorization"]["public_protected_test_candidate_identity"] = True
    with pytest.raises(RuntimeError, match="Prohibited pair-artifact"):
        validate_config(unsafe)

    unsafe = deepcopy(config)
    unsafe["authorization"]["model_evaluation"] = True
    with pytest.raises(RuntimeError, match="Prohibited pair-artifact"):
        validate_config(unsafe)

    unsafe = deepcopy(config)
    unsafe["sampling"]["cross_cell_unlabeled_pair_reuse_permitted"] = False
    with pytest.raises(RuntimeError, match="sampling semantics"):
        validate_config(unsafe)

    unsafe = deepcopy(config)
    unsafe["protected_evaluator"]["scorer_input_projection"].append("stratum_id")
    with pytest.raises(RuntimeError, match="evaluator boundary"):
        validate_config(unsafe)


def test_schema_has_only_positive_unlabeled_and_role_free_scorer_input() -> None:
    contract = load_contract(SCHEMA)
    assert set(contract.document["enums"]["pair_state"]) == {
        "released_positive",
        "unlabeled",
    }
    assert "negative" not in contract.document["enums"]["pair_state"]
    assert "pseudo_negative" not in contract.document["enums"]["pair_state"]
    candidate_columns = {
        column["name"]
        for column in contract.document["tables"]["protected_candidates"]["columns"]
    }
    assert "pair_id" not in candidate_columns
    assert "state" not in candidate_columns
    assert "sampling_weight_numerator" not in candidate_columns
    assert {"candidate_token", "endpoint_a_sha256", "endpoint_b_sha256"}.issubset(
        candidate_columns
    )
