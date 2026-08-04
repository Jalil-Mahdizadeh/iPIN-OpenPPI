"""Strict parsers for the bounded TF-isoform archive members."""

from __future__ import annotations

from io import BytesIO, StringIO
import csv
from typing import Any

import pandas as pd

from ipin_openppi.tf_isoform_audit.semantics import text


PUBLIC_CLONE_SUFFIX = "supp/SuppTable_CloneList.txt"
PUBLIC_Y2H_SUFFIX = "supp/SuppTable_PairwiseY2HResults.txt"
PUBLIC_N2H_SUFFIX = "supp/SuppTable_N2HResults.txt"
LOADER_SUFFIX = "src/data_loading/clones_and_assays_data.py"
SUPPLEMENT_CHECK_SUFFIX = "src/test_supplementary_tables.ipynb"
README_SUFFIX = "README.md"

RAW_Y2H_PATH = "data/internal/Y2H-data_2022-03-08.tsv"
SCREEN_SELECTION_PATH = "data/internal/tf_isoform_y2h_screen.tsv"
INTERNAL_CLONES_PATH = "data/internal/isoform_clones.tsv"
RAW_N2H_PATH = "data/internal/N2H_results.tsv"
CLONE_NT_FASTA_PATH = "data/internal/j2_6k_unique_isoacc_and_nt_seqs.fa"


EXPECTED_COLUMNS = {
    PUBLIC_CLONE_SUFFIX: [
        "clone_id", "gene_symbol", "isoform_status", "gencode_transcript_names",
        "ensembl_transcript_ids", "cds_seq", "aa_seq", "tf_family",
    ],
    PUBLIC_Y2H_SUFFIX: [
        "ad_clone_id", "ad_gene_symbol", "ad_orf_id", "db_gene_symbol",
        "db_orf_id", "Y2H_result", "db_gene_category", "db_gene_cofactor_type",
    ],
    PUBLIC_N2H_SUFFIX: [
        "clone_id", "gene_symbol_tf", "gene_symbol_partner", "test_orf_ida",
        "test_orf_idb", "source", "score_pair", "score_empty-N1",
        "score_empty-N2", "log2 NLR",
    ],
    RAW_Y2H_PATH: [
        "large_plate_name", "retest_pla", "retest_pos", "ad_gene_symbol",
        "ad_clone_name", "ad_orf_id", "db_gene_symbol", "db_orf_id", "category",
        "3AT", "LW", "empty_AD_3AT", "empty_AD_LW", "Y2H_result",
        "seq_confirmation_3AT", "seq_confirmation_LW",
    ],
    SCREEN_SELECTION_PATH: [
        "ad_orf_id", "db_orf_id", "in_orfeome_screen", "in_focussed_screen",
    ],
    INTERNAL_CLONES_PATH: ["gene", "clone_acc", "dup_idx"],
    RAW_N2H_PATH: [
        "test_orf_ida", "test_orf_idb", "test_pla", "test_pos_pair", "score_pair",
        "pair", "source", "test_pos_empty-N1", "score_empty-N1",
        "test_pos_empty-N2", "score_empty-N2", "clone_acc", "gene_symbol_tf",
        "gene_symbol_partner",
    ],
}


def read_tsv(payload: bytes, source_name: str) -> pd.DataFrame:
    frame = pd.read_csv(
        BytesIO(payload), sep="\t", dtype=str, keep_default_na=False
    )
    expected = EXPECTED_COLUMNS[source_name]
    if list(frame.columns) != expected:
        raise RuntimeError(
            f"Unexpected columns for {source_name}: {list(frame.columns)!r}"
        )
    return frame


def parse_fasta(payload: bytes) -> dict[str, str]:
    records: dict[str, str] = {}
    current: str | None = None
    parts: list[str] = []
    for physical_line, raw_line in enumerate(
        StringIO(payload.decode("utf-8")), start=1
    ):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current is not None:
                records[current] = "".join(parts).upper()
            current = line[1:].split()[0]
            if not current or current in records:
                raise RuntimeError(f"Invalid FASTA identifier at line {physical_line}")
            parts = []
        else:
            if current is None:
                raise RuntimeError("FASTA sequence encountered before a header")
            parts.append(line)
    if current is not None:
        records[current] = "".join(parts).upper()
    if not records:
        raise RuntimeError("No FASTA records parsed")
    return records


def clone_id_from_accession(clone_accession: str) -> str:
    fields = clone_accession.split("|")
    if len(fields) < 2 or "/" not in fields[1]:
        raise ValueError(f"Unexpected clone accession: {clone_accession!r}")
    return fields[0] + "-" + fields[1].split("/", 1)[0]


def unique_member(
    values: dict[str, bytes], suffix: str
) -> tuple[str, bytes]:
    matches = [(name, payload) for name, payload in values.items() if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one selected member ending {suffix!r}; found {len(matches)}"
        )
    return matches[0]


def raw_row_key(row: Any) -> tuple[str, str, str, str, str]:
    return (
        text(row.ad_clone_name), text(row.ad_gene_symbol), text(row.ad_orf_id),
        text(row.db_gene_symbol), text(row.db_orf_id),
    )

def public_row_key(row: Any) -> tuple[str, str, str, str, str]:
    return (
        text(row.ad_clone_id), text(row.ad_gene_symbol), text(row.ad_orf_id),
        text(row.db_gene_symbol), text(row.db_orf_id),
    )
