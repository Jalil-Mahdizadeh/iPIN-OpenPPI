from ipin_openppi.validation.lambourne import (
    contains_record_level_report_keys,
    independent_raw_outcome,
)


def test_independent_validator_preserves_technical_states() -> None:
    assert independent_raw_outcome(0, None, 0) == "Failed sequence confirmation"
    assert independent_raw_outcome(0, None, 1) == "Negative"
    assert independent_raw_outcome(None, None, None) == "Test failed"


def test_aggregate_report_record_key_guard_is_recursive() -> None:
    assert not contains_record_level_report_keys(
        {"final_analysis": {"positive": 376, "negative": 2300}}
    )
    assert contains_record_level_report_keys(
        {"metrics": [{"panel_pair_id": "private"}]}
    )
