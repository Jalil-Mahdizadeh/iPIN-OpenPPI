from __future__ import annotations

from ipin_openppi.validation.staging import (
    Checks,
    _iter_summaries,
    _nested,
    _sum_key,
    _view_name,
)


def test_table_summary_discovery_stops_at_summary_node() -> None:
    document = {
        "source": {
            "tables": {
                "records": {
                    "table": "evidence_records",
                    "rows": 2,
                    "parts": 1,
                    "files": [{"path": "part-00000.parquet"}],
                    "schema_name": "warehouse",
                    "schema_version": 1,
                    "schema_sha256": "a" * 64,
                }
            }
        }
    }
    summaries = list(_iter_summaries(document))
    assert len(summaries) == 1
    assert summaries[0].report_path == "source.tables.records"
    assert summaries[0].table == "evidence_records"
    assert summaries[0].rows == 2


def test_nested_and_recursive_diagnostic_sum() -> None:
    document = {
        "source_reports": {"huri": {"tables": {"1": {"errors": 2}}}},
        "other": [{"errors": 3}, {"errors": None}],
    }
    assert _nested(document, "source_reports.huri.tables.1.errors") == 2
    assert _sum_key(document, "errors") == 5


def test_checks_fail_closed_but_warnings_do_not_fail_gate() -> None:
    checks = Checks()
    checks.require("pass", True, observed=0, expected=0)
    checks.warn("known_issue", observed="open", detail="downstream blocked")
    assert checks.passed
    assert checks.counts() == {"pass": 1, "warning": 1, "fail": 0}
    checks.require("fail", False, observed=1, expected=0)
    assert not checks.passed
    assert checks.counts()["fail"] == 1


def test_duckdb_view_names_are_identifier_safe() -> None:
    assert _view_name("huri-fusion/interference") == "v_huri_fusion_interference"
