from pathlib import Path
import zipfile

import pytest

from ipin_openppi.validation.lambourne import (
    _read_unique_zip_member,
    contains_record_level_report_keys,
    independent_orf_id,
    independent_raw_outcome,
)


def test_independent_validator_preserves_technical_states() -> None:
    assert independent_raw_outcome(0, None, 0) == "Failed sequence confirmation"
    assert independent_raw_outcome(0, None, 1) == "Negative"
    assert independent_raw_outcome(None, None, None) == "Test failed"


@pytest.mark.parametrize(("value", "expected"), [(123, "123"), (123.0, "123"), ("123.0", "123")])
def test_independent_orf_identifier_normalization(value, expected: str) -> None:
    assert independent_orf_id(value) == expected


def test_aggregate_report_record_key_guard_is_recursive() -> None:
    assert not contains_record_level_report_keys(
        {"final_analysis": {"positive": 376, "negative": 2300}}
    )
    assert contains_record_level_report_keys(
        {"metrics": [{"panel_pair_id": "private"}]}
    )


def test_independent_zip_lookup_requires_a_unique_qualified_suffix(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("root/data/internal/table.tsv", "internal")
        archive.writestr("root/supplementary_tables/table.tsv", "supplement")
    with zipfile.ZipFile(path) as archive:
        with pytest.raises(RuntimeError, match="found 2"):
            _read_unique_zip_member(archive, "table.tsv")
        assert (
            _read_unique_zip_member(archive, "data/internal/table.tsv")
            == b"internal"
        )
