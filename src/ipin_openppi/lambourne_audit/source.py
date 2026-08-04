"""Strict parsing and cross-source reconciliation for Lambourne source tables."""

from __future__ import annotations

from collections import defaultdict
from io import BytesIO
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from ipin_openppi.ingestion.common import canonical_json, stable_id
from ipin_openppi.lambourne_audit.semantics import (
    classify_paper_outcome,
    raw_readout_to_reported_outcome,
    unordered_text_pair,
)


ASSAY_ID = "lambourne-2026-human-y2h-v1"
GOVERNANCE_FALSE = {
    "outcome_training_label_authorized": False,
    "universal_nonbinding_asserted": False,
    "benchmark_integration_authorized": False,
}

AD_CONSTRUCT = {
    "vector": "pDEST-AD-CYH2",
    "experimental_role": "prey",
    "fusion_partner": "Gal4 activation domain residues 768-881",
    "fusion_location": "N-terminus",
    "promoter": "truncated ADH1 (-701 to +1)",
    "replication_origin": "CEN low-copy",
    "yeast_selection_marker": "TRP1",
    "linker": "GGSNQ",
    "strain": "Y8800 (MATa)",
    "pair_level_construct_sequence": "not_reported",
    "pair_level_construct_boundaries": "not_reported",
}
DB_CONSTRUCT = {
    "vector": "pDEST-DB",
    "experimental_role": "bait",
    "fusion_partner": "Gal4 DNA-binding domain residues 1-147",
    "fusion_location": "N-terminus",
    "promoter": "truncated ADH1 (-701 to +1)",
    "replication_origin": "CEN low-copy",
    "yeast_selection_marker": "LEU2",
    "linker": "SRSNQ",
    "strain": "Y8930 (MATalpha)",
    "pair_level_construct_sequence": "not_reported",
    "pair_level_construct_boundaries": "not_reported",
}
EXPERIMENTAL_CONDITIONS = {
    "assay": "Y2H-v1 pairwise mating",
    "diploid_selection": "SC-LW",
    "interaction_selection": "SC-LW-His with 1 mM 3-amino-1,2,4-triazole",
    "autoactivation_control": "DB/bait tested against AD-null",
    "negative_sequence_confirmation": "colonies sampled from SC-LW",
    "positive_sequence_confirmation": "colonies sampled from interaction-selective medium",
    "reported_confirmation_coverage": {
        "positive_samples": "90%",
        "SC_LW_samples": "83%",
    },
    "single_reported_orientation_per_selected_pair": True,
}


def _boolish(value: Any) -> bool | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in {0, 1}:
        return bool(value)
    token = str(value).strip().casefold()
    if token in {"true", "yes", "1"}:
        return True
    if token in {"false", "no", "0"}:
        return False
    raise ValueError(f"Unsupported boolean value: {value!r}")


def _orf(value: Any) -> str:
    if value is None or pd.isna(value):
        raise ValueError("Missing CCSB ORF identifier")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    token = str(value).strip()
    if token.endswith(".0") and token[:-2].isdigit():
        token = token[:-2]
    if not token:
        raise ValueError("Empty CCSB ORF identifier")
    return token


def _raw_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    token = str(value).strip()
    if token.endswith(".0") and token[:-2].isdigit():
        token = token[:-2]
    return token or None


def parse_selection_records(
    payload: bytes, *, member_path: str, member_sha256: str
) -> list[dict[str, Any]]:
    table = pd.read_csv(BytesIO(payload), sep="\t", dtype=object)
    expected = ["ad_orf_id", "db_orf_id", "source"]
    if list(table.columns) != expected:
        raise RuntimeError(f"Unexpected selection table columns: {list(table.columns)}")
    rows: list[dict[str, Any]] = []
    for index, source in table.iterrows():
        ordinal = int(index) + 1
        ad, db = _orf(source["ad_orf_id"]), _orf(source["db_orf_id"])
        category = str(source["source"]).strip()
        first, second = unordered_text_pair(ad, db)
        rows.append(
            {
                "selection_record_id": stable_id(
                    "lambourne-selection-row", member_sha256, ordinal
                ),
                "source_row_ordinal": ordinal,
                "ad_orf_id": ad,
                "db_orf_id": db,
                "source_dataset": category,
                "ordered_orf_pair_id": stable_id("ordered-orf-pair", ad, db),
                "unordered_orf_pair_id": stable_id(
                    "unordered-orf-pair", first, second
                ),
                "source_member_path": member_path,
                "source_member_sha256": member_sha256,
                "raw_locator": f"data-row:{ordinal}",
                "original_selection_candidate": category == "Zhang_et_al",
                **GOVERNANCE_FALSE,
            }
        )
    return rows


def parse_raw_assay_records(
    payload: bytes, *, member_path: str, member_sha256: str
) -> list[dict[str, Any]]:
    table = pd.read_csv(BytesIO(payload), sep="\t", dtype=object)
    expected = [
        "db_orf_id",
        "ad_orf_id",
        "category",
        "final_score",
        "seq_confirmation_final_3at",
        "seq_confirmation_final_lw",
    ]
    if list(table.columns) != expected:
        raise RuntimeError(f"Unexpected raw assay columns: {list(table.columns)}")
    rows: list[dict[str, Any]] = []
    for index, source in table.iterrows():
        ordinal = int(index) + 1
        ad, db = _orf(source["ad_orf_id"]), _orf(source["db_orf_id"])
        first, second = unordered_text_pair(ad, db)
        seq_3at = _boolish(source["seq_confirmation_final_3at"])
        seq_lw = _boolish(source["seq_confirmation_final_lw"])
        score = _raw_text(source["final_score"])
        rows.append(
            {
                "raw_assay_record_id": stable_id(
                    "lambourne-raw-assay-row", member_sha256, ordinal
                ),
                "source_row_ordinal": ordinal,
                "ad_orf_id": ad,
                "db_orf_id": db,
                "source_dataset": str(source["category"]).strip(),
                "ordered_orf_pair_id": stable_id("ordered-orf-pair", ad, db),
                "unordered_orf_pair_id": stable_id(
                    "unordered-orf-pair", first, second
                ),
                "final_score_raw": score,
                "sequence_confirmation_3at": seq_3at,
                "sequence_confirmation_lw": seq_lw,
                "derived_reported_outcome": raw_readout_to_reported_outcome(
                    score, seq_3at, seq_lw
                ),
                "source_member_path": member_path,
                "source_member_sha256": member_sha256,
                "raw_locator": f"data-row:{ordinal}",
                **GOVERNANCE_FALSE,
            }
        )
    return rows


def parse_paper_records(
    path: Path,
    *,
    raw_relative_path: str,
    raw_sha256: str,
    raw_assay_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    table = pd.read_excel(path, sheet_name="Supplementary_Data_22", dtype=object)
    expected = [
        "uniprot_ac_a",
        "uniprot_ac_b",
        "AD_CCSB_ORF_ID",
        "DB_CCSB_ORF_ID",
        "source_dataset",
        "source_dataset.1",
        "result",
        "in_biorxiv_version",
        "in_published_version",
    ]
    if list(table.columns) != expected:
        raise RuntimeError(f"Unexpected Supplementary Data 22 columns: {list(table.columns)}")
    raw_index: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for row in raw_assay_rows:
        key = (str(row["ad_orf_id"]), str(row["db_orf_id"]), str(row["source_dataset"]))
        if key in raw_index:
            raise RuntimeError(f"Duplicate raw assay orientation/category key: {key}")
        raw_index[key] = row
    rows: list[dict[str, Any]] = []
    matched_raw = 0
    for index, source in table.iterrows():
        ordinal = int(index) + 1
        ad, db = _orf(source["AD_CCSB_ORF_ID"]), _orf(source["DB_CCSB_ORF_ID"])
        category = str(source["source_dataset"]).strip()
        category_duplicate = str(source["source_dataset.1"]).strip()
        if category != category_duplicate:
            raise RuntimeError(f"Source dataset duplicate differs at row {ordinal}")
        accession_ad = str(source["uniprot_ac_a"]).strip()
        accession_db = str(source["uniprot_ac_b"]).strip()
        if not accession_ad or not accession_db:
            raise RuntimeError(f"Missing UniProt accession at row {ordinal}")
        outcome = classify_paper_outcome(source["result"])
        raw = raw_index.get((ad, db, category))
        if raw is not None:
            matched_raw += 1
            concordant: bool | None = (
                str(raw["derived_reported_outcome"]) == outcome.reported_outcome
            )
            seq_3at = raw["sequence_confirmation_3at"]
            seq_lw = raw["sequence_confirmation_lw"]
            if not concordant:
                raise RuntimeError(f"Raw/paper outcome crosswalk differs at row {ordinal}")
        else:
            concordant = None
            seq_3at = None
            seq_lw = None
        rows.append(
            {
                "paper_record_id": stable_id(
                    "lambourne-paper-data22", raw_sha256, ordinal
                ),
                "source_row_ordinal": ordinal,
                "uniprot_accession_ad": accession_ad,
                "uniprot_accession_db": accession_db,
                "ad_orf_id": ad,
                "db_orf_id": db,
                "source_dataset": category,
                "source_dataset_duplicate": category_duplicate,
                "reported_outcome": outcome.reported_outcome,
                "outcome_semantics": outcome.outcome_semantics,
                "attempted_state": outcome.attempted_state,
                "evaluability_state": outcome.evaluability_state,
                "technical_state": outcome.technical_state,
                "observation_state": outcome.observation_state,
                "in_biorxiv_version": _boolish(source["in_biorxiv_version"]),
                "in_published_version": _boolish(source["in_published_version"]),
                "sequence_confirmation_3at": seq_3at,
                "sequence_confirmation_lw": seq_lw,
                "raw_crosswalk_concordant": concordant,
                "ad_orientation_role": "prey_activation_domain",
                "db_orientation_role": "bait_dna_binding_domain",
                "assay_id": ASSAY_ID,
                "construct_ad_json": canonical_json(AD_CONSTRUCT),
                "construct_db_json": canonical_json(DB_CONSTRUCT),
                "experimental_conditions_json": canonical_json(
                    EXPERIMENTAL_CONDITIONS
                ),
                "raw_file_path": raw_relative_path,
                "raw_file_sha256": raw_sha256,
                "raw_locator": f"Supplementary_Data_22:data-row:{ordinal}",
                **outcome.governance_fields(),
            }
        )
    if matched_raw != len(raw_index):
        raise RuntimeError(
            f"Only {matched_raw} of {len(raw_index)} raw assay rows match paper records"
        )
    return rows


def parse_orf_accession_map(payload: bytes) -> dict[str, tuple[str, ...]]:
    table = pd.read_csv(BytesIO(payload), sep="\t", dtype=object)
    if list(table.columns) != ["uniprot_ac", "orf_id"]:
        raise RuntimeError(f"Unexpected ORF/accession columns: {list(table.columns)}")
    values: dict[str, set[str]] = defaultdict(set)
    for _, row in table.iterrows():
        values[_orf(row["orf_id"])].add(str(row["uniprot_ac"]).strip())
    return {key: tuple(sorted(value)) for key, value in values.items()}


def assay_metadata_row() -> dict[str, Any]:
    return {
        "assay_metadata_id": stable_id("assay-metadata", ASSAY_ID),
        "assay_id": ASSAY_ID,
        "assay_name": "human pairwise yeast two-hybrid version 1",
        "detection_method_mi_ac": "MI:0397",
        "detection_method_name": "two hybrid array",
        "organism_taxid": 9606,
        "organism_name": "Homo sapiens",
        "db_vector": "pDEST-DB",
        "ad_vector": "pDEST-AD-CYH2",
        "db_strain": "Y8930 (MATalpha)",
        "ad_strain": "Y8800 (MATa)",
        "db_orientation_role": "bait_dna_binding_domain",
        "ad_orientation_role": "prey_activation_domain",
        "construct_scope_json": canonical_json(
            {"AD": AD_CONSTRUCT, "DB": DB_CONSTRUCT}
        ),
        "autoactivation_control_json": canonical_json(
            {"test": "DB/bait against AD-null", "state": "pair-level result reported"}
        ),
        "selection_readout_json": canonical_json(
            {
                "positive": "growth on SC-LW-His plus 1 mM 3AT",
                "negative": "no interaction-selective growth after evaluable SC-LW growth",
                "technical_states_retained": [
                    "failed sequence confirmation",
                    "autoactivator",
                    "test failed",
                ],
            }
        ),
        "experimental_conditions_json": canonical_json(EXPERIMENTAL_CONDITIONS),
        "pair_selection_json": canonical_json(
            {
                "paper_claim": "4,100 model-selected human pairs",
                "final_analysis_filter": (
                    "intersection of the tested 2024 bioRxiv prediction list with the "
                    "2025 Science published Data S3 pair list"
                ),
                "outcome_dependent_filtering_detected": False,
                "public_source_reconciliation_required": True,
            }
        ),
        "provenance_json": canonical_json(
            {
                "article_doi": "10.1038/s41467-026-70942-x",
                "supplementary_methods_tables": [5, 6, 7, 8],
                "paper_pair_table": "Supplementary Data 22",
                "imex_study": "IM-30553",
                "imex_detection_method": "MI:0397 two hybrid array",
            }
        ),
        "construct_sequence_identifiability": (
            "reference accession and ORF clone identifiers are reported; exact assayed "
            "construct sequences and boundaries are not reported pair-by-pair"
        ),
        **GOVERNANCE_FALSE,
    }
