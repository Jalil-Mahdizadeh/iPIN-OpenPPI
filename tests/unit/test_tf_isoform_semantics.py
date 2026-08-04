import pandas as pd
import pytest

from ipin_openppi.tf_isoform_audit.semantics import (
    classify_y2h_outcome,
    reconstruct_analytical_filter,
    translate_cds,
)


@pytest.mark.parametrize(
    ("updates", "outcome", "evaluability", "observation"),
    [
        ({"Y2H_result": "True"}, "positive_y2h_observation", "evaluable", "positive"),
        ({"Y2H_result": "False"}, "explicit_negative_y2h_observation", "evaluable", "negative"),
        ({"LW": "1", "empty_AD_LW": "4"}, "mating_or_spotting_failure", "technically_unevaluable", "not_applicable"),
        ({"LW": "4", "empty_AD_LW": "4", "empty_AD_3AT": "4"}, "autoactivation", "technically_unevaluable", "not_applicable"),
        ({"LW": "4", "empty_AD_LW": "4", "empty_AD_3AT": "0", "3AT": "NA"}, "assay_measurement_failure", "technically_unevaluable", "not_applicable"),
        ({"LW": "4", "empty_AD_LW": "4", "empty_AD_3AT": "0", "3AT": "3", "seq_confirmation_3AT": "False"}, "sequence_confirmation_failure", "technically_unevaluable", "not_applicable"),
        ({"LW": "4", "empty_AD_LW": "4", "empty_AD_3AT": "0", "3AT": "3", "seq_confirmation_3AT": "True", "seq_confirmation_LW": "True"}, "unknown_unresolved", "technically_unevaluable", "not_applicable"),
    ],
)
def test_y2h_semantics_preserve_negative_and_technical_states(
    updates, outcome: str, evaluability: str, observation: str
) -> None:
    row = {
        "Y2H_result": "",
        "LW": "",
        "empty_AD_LW": "",
        "empty_AD_3AT": "",
        "3AT": "",
        "seq_confirmation_3AT": "",
        "seq_confirmation_LW": "",
        **updates,
    }
    result = classify_y2h_outcome(row)
    assert result.outcome_class == outcome
    assert result.evaluability_state == evaluability
    assert result.observation_state == observation


def test_archived_filter_retains_attempts_but_not_technical_rows_in_analysis() -> None:
    frame = pd.DataFrame(
        [
            {"ad_clone_id": "c1", "ad_gene_symbol": "TF", "db_gene_symbol": "P", "source_category": "tf_isoform_ppis", "observation_state": "positive"},
            {"ad_clone_id": "c2", "ad_gene_symbol": "TF", "db_gene_symbol": "P", "source_category": "tf_isoform_ppis", "observation_state": "negative"},
            {"ad_clone_id": "c2", "ad_gene_symbol": "TF", "db_gene_symbol": "Q", "source_category": "tf_isoform_ppis", "observation_state": "positive"},
            {"ad_clone_id": "c1", "ad_gene_symbol": "TF", "db_gene_symbol": "P", "source_category": "tf_isoform_ppis", "observation_state": "not_applicable"},
            {"ad_clone_id": "control", "ad_gene_symbol": "CTRL", "db_gene_symbol": "X", "source_category": "reference_controls", "observation_state": "positive"},
        ]
    )
    membership, steps = reconstruct_analytical_filter(frame)
    assert membership.tolist() == [True, True, False, True, False]
    assert [step["output_rows"] for step in steps] == [4, 4, 4, 4, 4, 3]
    assert int((membership & frame.observation_state.isin({"positive", "negative"})).sum()) == 2


def test_translation_accepts_terminal_stop_and_fails_closed_on_frame_error() -> None:
    assert translate_cds("ATGAAATAA") == "MK"
    with pytest.raises(ValueError, match="not divisible"):
        translate_cds("ATGA")
