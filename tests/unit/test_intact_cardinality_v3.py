from __future__ import annotations

from ipin_openppi.ingestion.intact_v3 import _correct_participant_cardinality
from ipin_openppi.ingestion.pipeline_v4 import PARSER_VERSION


def _row(participant_count: int, original_nary: bool, flags: list[str]) -> dict:
    return {
        "participant_count": participant_count,
        "original_nary": original_nary,
        "quality_flags": flags,
    }


def test_unary_record_is_preserved_but_not_marked_nary() -> None:
    corrected = _correct_participant_cardinality(
        _row(1, True, ["original_nary_preserved", "not_binary_two_protein_record"])
    )
    assert corrected["original_nary"] is False
    assert "original_nary_preserved" not in corrected["quality_flags"]
    assert "original_unary_preserved" in corrected["quality_flags"]


def test_binary_and_nary_cardinality_are_exact() -> None:
    binary = _correct_participant_cardinality(
        _row(2, False, ["binary_two_protein_record"])
    )
    nary = _correct_participant_cardinality(_row(3, True, ["original_nary_preserved"]))
    assert binary["original_nary"] is False
    assert "original_unary_preserved" not in binary["quality_flags"]
    assert nary["original_nary"] is True
    assert nary["quality_flags"] == ["original_nary_preserved"]
    assert PARSER_VERSION == "1.2.0"
