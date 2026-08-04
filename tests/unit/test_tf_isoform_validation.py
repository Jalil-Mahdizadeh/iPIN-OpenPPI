import pytest

from ipin_openppi.validation.tf_isoform import (
    contains_record_keys,
    independent_y2h_outcome,
)


def test_independent_validator_recomputes_all_source_states() -> None:
    base = {
        "Y2H_result": "",
        "LW": "4",
        "empty_AD_LW": "4",
        "3AT": "3",
        "empty_AD_3AT": "0",
        "seq_confirmation_3AT": "True",
        "seq_confirmation_LW": "True",
    }
    assert independent_y2h_outcome({**base, "Y2H_result": "False"}) == (
        "explicit_negative_y2h_observation",
        "evaluable",
        "negative",
    )
    assert independent_y2h_outcome({**base, "seq_confirmation_LW": "False"}) == (
        "sequence_confirmation_failure",
        "technically_unevaluable",
        "not_applicable",
    )
    assert independent_y2h_outcome({**base, "LW": "NA"}) == (
        "mating_or_spotting_failure",
        "technically_unevaluable",
        "not_applicable",
    )


def test_independent_validator_rejects_unexpected_public_call() -> None:
    with pytest.raises(RuntimeError, match="Unexpected Y2H result"):
        independent_y2h_outcome({"Y2H_result": "Negative"})


def test_aggregate_report_guard_rejects_record_level_identifiers() -> None:
    assert not contains_record_keys({"outcomes": {"positive": 2563}})
    assert contains_record_keys({"preview": [{"pair_record_id": "private"}]})
