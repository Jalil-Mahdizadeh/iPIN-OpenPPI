from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ipin_openppi.model_governance.protocol import (
    load_yaml,
    protocol_checks,
    validate_config,
)


CONFIG = Path("configs/model_governance_and_baseline_training_protocol_v1.yaml")


def _validated_config() -> dict:
    config = load_yaml(CONFIG)
    validate_config(config)
    return config


def test_protocol_has_exactly_24_passing_fail_closed_checks() -> None:
    config = _validated_config()
    checks = protocol_checks(config)

    assert len(checks) == 24
    assert {record["status"] for record in checks} == {"pass"}
    assert len({record["check"] for record in checks}) == 24


def test_protocol_is_design_only_and_declares_no_model_output() -> None:
    config = _validated_config()
    authority = config["authority"]

    assert authority["design_only"] is True
    assert authority["return_to_governance_required"] is True
    for key in (
        "model_weight_or_tokenizer_download",
        "model_cache_population",
        "model_runtime_container_build",
        "embedding_extraction",
        "baseline_or_model_implementation",
        "model_training_or_checkpointing",
        "development_release_or_access",
        "protected_candidate_or_truth_access",
        "external_panel_integration",
        "structural_residue_or_interface_work",
    ):
        assert authority[key] is False

    assert config["outputs"]["pair_model_embedding_checkpoint_or_prediction_artifacts"] == (
        "prohibited"
    )


@pytest.mark.parametrize(
    ("mutation", "expected_check"),
    [
        (
            lambda value: value["authority"].__setitem__("model_training_or_checkpointing", True),
            "identity_and_design_only_authority",
        ),
        (
            lambda value: value["plm_provenance"]["candidates"]["esm2_150m"].__setitem__(
                "checkpoint_sha256", "0" * 64
            ),
            "exact_two_plm_candidates",
        ),
        (
            lambda value: value["embedding_strategy"].__setitem__(
                "input_sequence", "truncate_to_first_window"
            ),
            "pooled_embedding_strategy_is_frozen_complete_and_label_blind",
        ),
        (
            lambda value: value["primary_training_objective"]["unlabeled_observations"].__setitem__(
                "scientific_negative_interpretation", "negative"
            ),
            "exact_public_training_P_U_and_strata_use",
        ),
        (
            lambda value: value["development_release_and_model_selection"][
                "selection_metric_order"
            ].__setitem__(
                "cells", ["C1_development", "C2_development", "C3_development"]
            ),
            "training_hash_before_release_and_nonadaptive_model_selection",
        ),
        (
            lambda value: value["model_level_kill_criteria"].pop(
                "new_candidate_training_or_retraining_after_development_release"
            ),
            "model_level_kill_criteria_cover_shortcuts_and_release_leakage",
        ),
        (
            lambda value: value["outputs"].__setitem__(
                "scientific_report", "../sealed/protected_truth.cms"
            ),
            "claim_ceiling_and_no_model_outputs",
        ),
    ],
)
def test_consequential_rule_mutations_fail_closed(mutation, expected_check: str) -> None:
    unsafe = deepcopy(_validated_config())
    mutation(unsafe)

    failures = {
        record["check"] for record in protocol_checks(unsafe) if record["status"] == "fail"
    }
    assert expected_check in failures
    with pytest.raises(RuntimeError, match=expected_check):
        validate_config(unsafe)
