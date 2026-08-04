import pytest

from ipin_openppi.lambourne_audit.semantics import (
    benchmark_claim_identifiability,
    classify_paper_outcome,
    raw_readout_to_reported_outcome,
    summarize_final_analysis,
)


@pytest.mark.parametrize(
    ("score", "seq_3at", "seq_lw", "expected"),
    [
        (0, None, 1, "Negative"),
        (0, None, 0, "Failed sequence confirmation"),
        (1, 1, 0, "Positive"),
        (1, 0, 1, "Failed sequence confirmation"),
        ("AA", None, None, "Autoactivator"),
        (None, None, None, "Test failed"),
    ],
)
def test_raw_readout_crosswalk_preserves_technical_states(
    score, seq_3at, seq_lw, expected
) -> None:
    assert raw_readout_to_reported_outcome(score, seq_3at, seq_lw) == expected


def test_negative_is_assay_bounded_and_never_authorized_as_label() -> None:
    record = classify_paper_outcome("Negative")
    assert record.observation_state == "negative"
    assert record.outcome_semantics == "negative_assay_observation"
    assert record.governance_fields() == {
        "outcome_training_label_authorized": False,
        "universal_nonbinding_asserted": False,
        "benchmark_integration_authorized": False,
    }


def test_technical_state_is_not_negative() -> None:
    record = classify_paper_outcome("Failed sequence confirmation")
    assert record.evaluability_state == "not_evaluable"
    assert record.observation_state == "not_applicable_technically_unevaluable"


def test_final_summary_keeps_positive_negative_and_na_separate() -> None:
    rows = [
        {
            "source_dataset": "Zhang_et_al",
            "in_published_version": True,
            "reported_outcome": value,
        }
        for value in [
            "Positive",
            "Negative",
            "Failed sequence confirmation",
            "Autoactivator",
            "Test failed",
        ]
    ]
    summary = summarize_final_analysis(rows)
    assert summary["selected_pairs"] == 5
    assert summary["positive_assay_observations"] == 1
    assert summary["negative_assay_observations"] == 1
    assert summary["technically_unevaluable_or_na"] == 3
    assert summary["evaluable"] == 2


def test_claim_boundary_rejects_universal_and_biological_probability_claims() -> None:
    claims = benchmark_claim_identifiability()
    assert "assay_observation_rate" in claims["identifiable"]
    assert "universal_nonbinding" in claims["not_identifiable"]
    assert "biological_interaction_probability" in claims["not_identifiable"]
