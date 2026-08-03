from __future__ import annotations

from pathlib import Path

import pytest

from ipin_openppi.ingestion.intact_v2 import (
    EXPECTED_MUTATION_COLUMNS,
    iter_reconstructed_mutation_rows,
)


def _header() -> str:
    values = list(EXPECTED_MUTATION_COLUMNS)
    values[0] = "#" + values[0]
    return "\t".join(values) + "\n"


def test_reconstructs_unquoted_multiline_mutation_record(tmp_path: Path) -> None:
    path = tmp_path / "mutations.tsv"
    first = [
        "EBI-1",
        "P1:p.Gln1[4]",
        "1-4",
        "QQQQ",
        "QQ",
        "mutation(MI:0118)",
        "wrapped annotation",
        "uniprotkb:P1",
        "GENE",
        "Protein",
        "9606 - Homo sapiens",
        "uniprotkb:P1(protein)",
        "123",
        "1A",
        "EBI-2",
    ]
    second = list(first)
    second[0] = "EBI-3"
    second[-1] = "EBI-4"
    logical_first = "\t".join(first)
    split_at = logical_first.index("wrapped") + 4
    path.write_text(
        _header()
        + logical_first[:split_at]
        + "\n"
        + logical_first[split_at:]
        + "\n"
        + "\t".join(second)
        + "\n",
        encoding="utf-8",
    )
    rows = list(iter_reconstructed_mutation_rows(path))
    assert [(start, end) for start, end, _ in rows] == [(2, 3), (4, 4)]
    assert rows[0][2]["Feature AC"] == "EBI-1"
    assert rows[0][2]["Interaction AC"] == "EBI-2"
    assert rows[0][2]["Feature annotation"] == "wrapped annotation"


def test_reconstruction_refuses_invalid_boundary_accessions(tmp_path: Path) -> None:
    path = tmp_path / "mutations.tsv"
    values = [""] * len(EXPECTED_MUTATION_COLUMNS)
    values[0] = "not-an-ebi-ac"
    values[-1] = "EBI-2"
    path.write_text(_header() + "\t".join(values) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid feature accession"):
        list(iter_reconstructed_mutation_rows(path))
