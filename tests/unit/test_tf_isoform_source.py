from pathlib import Path
import zipfile

import pytest

from ipin_openppi.tf_isoform_audit.source import (
    clone_id_from_accession,
    parse_fasta,
    unique_member,
)


def test_clone_accession_mapping_preserves_source_clone_identifier() -> None:
    assert clone_id_from_accession("FOXA1|2/7|anything") == "FOXA1-2"


def test_fasta_parser_is_exact_and_rejects_duplicate_identifiers() -> None:
    assert parse_fasta(b">a note\natg\nccc\n>b\nttt\n") == {
        "a": "ATGCCC",
        "b": "TTT",
    }
    with pytest.raises(RuntimeError, match="Invalid FASTA identifier"):
        parse_fasta(b">a\nATG\n>a\nCCC\n")


def test_selected_member_lookup_requires_unique_qualified_suffix() -> None:
    values = {"root/a/table.tsv": b"a", "root/b/table.tsv": b"b"}
    with pytest.raises(RuntimeError, match="found 2"):
        unique_member(values, "table.tsv")
    assert unique_member(values, "a/table.tsv") == ("root/a/table.tsv", b"a")
