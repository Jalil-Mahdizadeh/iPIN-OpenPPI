from ipin_openppi.validation.negative_evidence import (
    contains_record_level_report_keys,
    recompute_subset_metrics,
)


def test_subset_metrics_distinguish_raw_whitespace_from_normalized_membership() -> None:
    rows = {
        "manual": [("P1", "P2", "1", "assay ")],
        "manual_stringent": [("P1", "P2", "1", "assay")],
        "pdb": [("P1", "P2", "1abc", "x-ray")],
        "pdb_stringent": [("P1", "P2", "1abc", "x-ray")],
    }
    metrics = recompute_subset_metrics(rows)
    manual = metrics["datasets"]["manual"]
    assert manual["stringent_normalized_multiset_subset"]
    assert not manual["stringent_raw_exact_multiset_subset"]
    assert manual["stringent_raw_exact_excess_rows"] == 1
    assert metrics["datasets"]["pdb"]["stringent_raw_exact_multiset_subset"]


def test_aggregate_report_record_key_guard_is_recursive() -> None:
    assert not contains_record_level_report_keys(
        {"metrics": {"intact_negative_records": 939}, "status": "complete"}
    )
    assert contains_record_level_report_keys(
        {"checks": [{"observed": {"parent_record_id": "private"}}]}
    )
