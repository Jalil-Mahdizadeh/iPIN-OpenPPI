from __future__ import annotations

from pathlib import Path

from ipin_openppi.negative_evidence.negatome import (
    parse_negatome_file,
    reconcile_parent_and_stringent_rows,
    split_accession,
)
from ipin_openppi.negative_evidence.reference import FrozenReferenceIndex


def test_split_accession_preserves_only_numeric_isoform_suffix() -> None:
    assert split_accession("P12345-2") == ("P12345", "P12345-2")
    assert split_accession("P12345") == ("P12345", None)
    assert split_accession("ABC-X") == ("ABC-X", None)


def test_stringent_rows_are_linked_as_a_normalized_multiset_subset(
    tmp_path: Path,
) -> None:
    files = {
        "manual": "P1\tP2\t1\tMI:0019 - coip \nP1\tP2\t1\tMI:0019 - coip \n",
        "manual_stringent": "P1\tP2\t1\tMI:0019 - coip\n",
        "pdb": "#ProteinA\tProteinB\tPDB_Code\tevidence\nP1\tP2\t1abc\tMI:0114  x-ray\n",
        "pdb_stringent": "#ProteinA\tProteinB\tPDB_Code\tevidence\nP1\tP2\t1abc\tMI:0114  x-ray\n",
    }
    parsed = {}
    for dataset, text in files.items():
        path = tmp_path / f"{dataset}.txt"
        path.write_text(text, encoding="utf-8")
        parsed[dataset] = parse_negatome_file(
            path=path,
            dataset=dataset,
            raw_file_path=f"data/raw/{dataset}.txt",
            raw_file_sha256="0" * 64,
        )
    all_rows, parents, metrics = reconcile_parent_and_stringent_rows(parsed)
    assert len(all_rows) == 5
    assert len(parents) == 3
    assert metrics["datasets"]["manual"]["parent_duplicate_rows"] == 1
    assert metrics["datasets"]["manual"]["stringent_normalized_multiset_subset"]
    assert not metrics["datasets"]["manual"]["stringent_raw_exact_multiset_subset"]
    assert metrics["datasets"]["manual"]["stringent_raw_exact_excess_rows"] == 1
    stringent = [row for row in all_rows if row.dataset == "manual_stringent"]
    assert stringent[0].parent_record_id == parents[0].parent_record_id


def test_manual_pmc_identifier_is_preserved(tmp_path: Path) -> None:
    path = tmp_path / "manual.txt"
    path.write_text(
        "P1\tP2\tPMC1717011\tMI:0045 - experimental interaction detection\n",
        encoding="utf-8",
    )
    rows = parse_negatome_file(
        path=path,
        dataset="manual",
        raw_file_path="data/raw/manual.txt",
        raw_file_sha256="0" * 64,
    )
    assert rows[0].publication_ids == ("pmc:PMC1717011",)


def _sequence(accession: str, *, isoform: str | None = None) -> dict[str, object]:
    token = isoform or accession
    return {
        "protein_sequence_id": f"uniprot:2026_02:{token}",
        "uniprot_accession": accession,
        "isoform_id": isoform,
        "canonical": isoform is None,
        "sequence_view": "canonical" if isoform is None else "additional_isoform",
        "taxid": 9606,
        "sequence_version": 1,
        "entry_version": 2,
        "sequence_length": 4,
        "sequence_sha256": token.lower().ljust(64, "0")[:64],
        "source_release": "2026_02",
        "raw_file_path": "data/raw/reference.fasta.gz",
        "raw_file_sha256": "a" * 64,
    }


def test_mapping_routes_preserve_isoform_and_secondary_confidence() -> None:
    canonical = _sequence("P12345")
    isoform = _sequence("P12345", isoform="P12345-2")
    index = FrozenReferenceIndex(
        release="2026_02",
        taxid=9606,
        exact={"P12345": (canonical,), "P12345-2": (isoform,)},
        canonical={"P12345": (canonical,)},
        secondary_to_primary={"QOLD01": ("P12345",)},
        dat_path="data/raw/reference.dat.gz",
        dat_sha256="b" * 64,
    )
    exact = index.map_accession(
        source_accession="P12345-2",
        parent_record_id="parent:1",
        participant_ordinal=1,
        evidence_family="manual_experimental_negative",
    )
    secondary = index.map_accession(
        source_accession="QOLD01",
        parent_record_id="parent:1",
        participant_ordinal=2,
        evidence_family="manual_experimental_negative",
    )
    alias = index.map_accession(
        source_accession="P12345-1",
        parent_record_id="parent:2",
        participant_ordinal=1,
        evidence_family="manual_experimental_negative",
    )
    assert exact["mapping_state"] == "exact_isoform"
    assert exact["mapped_isoform_id"] == "P12345-2"
    assert secondary["mapping_state"] == "secondary_accession_unique"
    assert secondary["mapping_confidence"] == "B_unique_frozen_secondary_accession"
    assert alias["mapping_state"] == "canonical_isoform1_alias"
    assert alias["source_isoform_id"] == "P12345-1"
