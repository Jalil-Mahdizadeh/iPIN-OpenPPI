from __future__ import annotations

import pytest

from ipin_openppi.benchmark.systematic_screen_audit import (
    _validate_config,
    assess_universe_completeness,
    classify_binary_panel_result,
    classify_y2h_score,
)


def _config() -> dict:
    return {
        "schema_version": 1,
        "audit_version": "0.1.0",
        "authorization": {
            "source_metadata_audit": True,
            "benchmark_estimand_policy_design": True,
            "label_construction": False,
            "split_construction": False,
            "structural_mapping": False,
            "model_training": False,
        },
        "runtime": {"duckdb_memory_limit": "8GB"},
        "decision_policy": {
            "label_construction_authorized": False,
            "split_construction_authorized": False,
            "model_training_authorized": False,
        },
    }


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("1", "observed_positive"),
        ("0", "conditional_assay_negative"),
        ("NA", "technical_invalid"),
        ("AA", "technical_autoactivator"),
    ],
)
def test_y2h_scores_preserve_technical_states(token: str, expected: str) -> None:
    assert classify_y2h_score(token) == expected


def test_unknown_y2h_score_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unexpected Y2H"):
        classify_y2h_score("")


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("1.0", "observed_positive"),
        ("0.0", "conditional_assay_negative"),
        ("", "unresolved_missing_or_invalid"),
    ],
)
def test_binary_panel_blank_is_not_negative(token: str, expected: str) -> None:
    assert classify_binary_panel_result(token) == expected


def test_incomplete_universe_is_reported_without_imputation() -> None:
    result = assess_universe_completeness(
        {
            "pair_identity": "positive_only",
            "attempted_state": "unavailable",
            "technical_state": "unavailable",
        }
    )
    assert result["complete_attempted_evaluable_universe_reconstructed"] is False
    assert result["complete_pair_level_field_count"] == 0
    assert set(result["incomplete_fields"]) == {
        "pair_identity",
        "attempted_state",
        "technical_state",
    }


def test_complete_universe_requires_every_pair_level_field() -> None:
    result = assess_universe_completeness(
        {"pair_identity": "complete_pair_level", "outcome": "complete_pair_level"}
    )
    assert result["complete_attempted_evaluable_universe_reconstructed"] is True
    assert result["incomplete_fields"] == {}


@pytest.mark.parametrize(
    "field",
    [
        "label_construction",
        "split_construction",
        "structural_mapping",
        "model_training",
    ],
)
def test_config_rejects_prohibited_authorization(field: str) -> None:
    config = _config()
    config["authorization"][field] = True
    with pytest.raises(RuntimeError, match="prohibited"):
        _validate_config(config)


def test_config_rejects_label_authorization_in_decision() -> None:
    config = _config()
    config["decision_policy"]["label_construction_authorized"] = True
    with pytest.raises(RuntimeError, match="label_construction_authorized"):
        _validate_config(config)


def test_valid_guardrail_configuration_passes() -> None:
    _validate_config(_config())
