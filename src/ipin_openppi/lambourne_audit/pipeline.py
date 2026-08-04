"""Execute the governance-bounded Lambourne human Y2H-v1 semantics audit."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import platform
from typing import Any, Iterable, Mapping

import duckdb
import pandas as pd
import pyarrow
import pyarrow.dataset as ds
import yaml

from ipin_openppi.ingestion.common import (
    AtomicDatasetDirectory,
    ParquetBatchWriter,
    canonical_json,
    git_provenance,
    load_asset_index,
    project_root_from,
    require_apptainer,
    stable_id,
    verify_asset,
)
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.lambourne_audit import LAMBOURNE_AUDIT_VERSION
from ipin_openppi.lambourne_audit.archives import (
    scan_tar_gzip_archive,
    scan_zip_archive,
)
from ipin_openppi.lambourne_audit.imex import parse_mitab27, xml_preview_inventory
from ipin_openppi.lambourne_audit.overlap import (
    build_contamination_index,
    contamination_flags,
    load_negatome_pair_index,
    load_sequence_family_maps,
    source_specific_positive_index,
)
from ipin_openppi.lambourne_audit.semantics import (
    benchmark_claim_identifiability,
    summarize_final_analysis,
    unordered_text_pair,
)
from ipin_openppi.lambourne_audit.source import (
    AD_CONSTRUCT,
    ASSAY_ID,
    DB_CONSTRUCT,
    EXPERIMENTAL_CONDITIONS,
    GOVERNANCE_FALSE,
    assay_metadata_row,
    parse_orf_accession_map,
    parse_paper_records,
    parse_raw_assay_records,
    parse_selection_records,
)
from ipin_openppi.negative_evidence.evidence import (
    build_positive_pair_index,
    index_intact_negatives,
    load_intact_negative_records,
    register_evidence_views,
    unordered_pair,
    unordered_sequence_pair_id,
)
from ipin_openppi.negative_evidence.reference import FrozenReferenceIndex
from ipin_openppi.validation.staging import _write_report


STAGING_TABLES = (
    "archive_members",
    "selection_records",
    "raw_assay_records",
    "paper_records",
    "imex_preview_records",
)
CANONICAL_TABLES = (
    "selected_universe_reconciliation",
    "participant_mappings",
    "panel_pair_audit",
    "imex_pair_reconciliation",
    "assay_metadata",
)

CODE_SELECTED_SUFFIXES = (
    "data/internal/Y2H_v1_pairwise_test_AlphaFoldRoseTTAFold_human.tsv",
    "data/internal/predicting_human_interactome_pairs_to_test_2024-12-13.tsv",
    "data/internal/uniprot_ac_to_orf_id_used_for_Zhang_et_al_experiment.tsv",
    "notebooks/Y2H_AlphaFoldRoseTTAFold_human.ipynb",
    "notebooks/datasets.py",
    "LICENSE",
    "README.md",
)
INPUT_SELECTED_BASENAMES = {
    "Y2H_v1_pairwise_test_AlphaFoldRoseTTAFold_human_filtered.tsv",
    "Zhang-et-al_2024_with-strategies.tsv",
    "science.adt1630_data_s1_to_s8.xlsx",
    "Zhang-et-al_biorxiv-2024_pairs.txt",
    "predicting_human_interactome_pairs_to_test_2024-12-13.tsv",
    "Y2H_v1_pairwise_test_AlphaFoldRoseTTAFold_human.tsv",
    "uniprot_ac_to_orf_id_used_for_Zhang_et_al_experiment.tsv",
    "ppiDB_pairs.txt",
    "string_pairs.txt",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected YAML mapping: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def _resolve_inside(
    project_root: Path, value: str | Path, boundary: Path, *, strict: bool
) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve(strict=strict)
    try:
        resolved.relative_to(boundary.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(f"Path escapes boundary {boundary}: {resolved}") from exc
    return resolved


def _verified_document(
    project_root: Path,
    inputs: Mapping[str, Any],
    name: str,
    hash_name: str,
    boundary: str,
) -> tuple[Path, dict[str, Any]]:
    path = _resolve_inside(
        project_root,
        str(inputs[name]),
        project_root / boundary,
        strict=True,
    )
    observed = sha256_file(path)
    expected = str(inputs[hash_name])
    if observed != expected:
        raise RuntimeError(f"Input document SHA-256 mismatch: {name}")
    return path, {
        "path": path.relative_to(project_root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": observed,
    }


def _validate_config(config: Mapping[str, Any]) -> None:
    if int(config.get("schema_version", -1)) != 1:
        raise RuntimeError("Unsupported Lambourne audit configuration schema")
    if config.get("audit_version") != LAMBOURNE_AUDIT_VERSION:
        raise RuntimeError("Lambourne audit configuration/code version mismatch")
    authorization = config.get("authorization", {})
    for key in (
        "provenance_preserving_parsing",
        "frozen_reference_mapping",
        "evidence_overlap_audit",
        "aggregate_benchmark_feasibility_assessment",
    ):
        if authorization.get(key) is not True:
            raise RuntimeError(f"Required action is not authorized: {key}")
    for key in (
        "outcomes_as_training_labels",
        "merge_with_negatome",
        "benchmark_split_construction",
        "benchmark_integration",
        "model_training",
        "universal_nonbinding_interpretation",
    ):
        if authorization.get(key) is not False:
            raise RuntimeError(f"Prohibited action must remain false: {key}")
    if config["governance"]["return_before_benchmark_integration"] is not True:
        raise RuntimeError("Return-to-governance guard is absent")


def _selected_payload(
    values: Mapping[str, bytes], suffix: str
) -> tuple[str, bytes, str]:
    matches = [(name, payload) for name, payload in values.items() if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one selected archive member ending {suffix!r}, found {len(matches)}")
    name, payload = matches[0]
    import hashlib

    return name, payload, hashlib.sha256(payload).hexdigest()


def _bool_value(value: Any) -> bool:
    return bool(value is True or value == 1 or str(value).strip().casefold() == "true")


def _write_table(
    *,
    root: Path,
    table_name: str,
    rows: Iterable[Mapping[str, Any]],
    contract: Any,
    config: Mapping[str, Any],
    metadata: Mapping[str, str],
) -> dict[str, Any]:
    writer = ParquetBatchWriter(
        root / table_name,
        contract,
        table_name,
        batch_rows=int(config["runtime"]["parquet_batch_rows"]),
        compression=str(config["runtime"]["parquet_compression"]),
        compression_level=int(config["runtime"]["parquet_compression_level"]),
        extra_metadata=metadata,
    )
    with writer:
        writer.extend(rows)
    return writer.summary()


def _replace_prefix(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {key: _replace_prefix(child, old, new) for key, child in value.items()}
    if isinstance(value, list):
        return [_replace_prefix(child, old, new) for child in value]
    if isinstance(value, str) and value.startswith(old):
        return new + value[len(old) :]
    return value


def _write_manifest(path: Path, value: Mapping[str, Any]) -> str:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256_file(path)
    path.with_name(path.name + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="utf-8"
    )
    return digest


def _make_read_only(root: Path) -> None:
    import stat

    for path in sorted(root.rglob("*"), reverse=True):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"Generated dataset contains a link: {path}")
        path.chmod(0o444 if path.is_file() else 0o555)
    root.chmod(0o555)


def _archive_inventory_rows(
    rows: list[dict[str, object]], *, asset: Any, license_id: str
) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "source_archive_path": asset.relative_path,
            "license_id": license_id,
            "redistribution_tier": "internal_immutable_audit_only",
        }
        for row in rows
    ]


def _workbook_inventory(path: Path) -> dict[str, Any]:
    workbook = pd.ExcelFile(path)
    sheets: dict[str, Any] = {}
    for name in workbook.sheet_names:
        table = pd.read_excel(path, sheet_name=name)
        sheets[str(name)] = {
            "rows": int(table.shape[0]),
            "columns": [str(column) for column in table.columns],
        }
    return {"sheet_count": len(sheets), "sheets": sheets}


def _science_published_pairs(payload: bytes) -> set[tuple[str, str]]:
    table = pd.read_excel(BytesIO(payload), sheet_name="Data S3", skiprows=15)
    required = {"Protein1", "Protein2"}
    if not required.issubset(table.columns):
        raise RuntimeError("Science Data S3 lacks Protein1/Protein2")
    table = table.dropna(subset=["Protein1", "Protein2"])
    return {
        unordered_text_pair(row["Protein1"], row["Protein2"])
        for _, row in table.iterrows()
    }


def _family_ids_for_candidates(
    candidates: Iterable[str], accession_maps: Mapping[str, Mapping[str, Iterable[str]]]
) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for family in ("UniRef100", "UniRef90", "UniRef50"):
        output[family] = sorted(
            {
                identifier
                for accession in candidates
                for identifier in accession_maps[family].get(accession, ())
            }
        )
    return output


def _reconcile_selected_universe(
    *,
    selection_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    orf_accessions: Mapping[str, tuple[str, ...]],
    paper_claim: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selection = [row for row in selection_rows if row["source_dataset"] == "Zhang_et_al"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selection:
        groups[str(row["unordered_orf_pair_id"])].append(row)
    raw_counts = Counter(
        str(row["unordered_orf_pair_id"])
        for row in raw_rows
        if row["source_dataset"] == "Zhang_et_al"
    )
    paper_counts: Counter[str] = Counter()
    final_counts: Counter[str] = Counter()
    for row in paper_rows:
        if row["source_dataset"] != "Zhang_et_al":
            continue
        first, second = unordered_text_pair(row["ad_orf_id"], row["db_orf_id"])
        pair_id = stable_id("unordered-orf-pair", first, second)
        paper_counts[pair_id] += 1
        final_counts[pair_id] += bool(row["in_published_version"])
    unique_count = len(groups)
    rows: list[dict[str, Any]] = []
    for pair_id in sorted(groups):
        source_rows = groups[pair_id]
        all_orfs = {
            str(row["ad_orf_id"]) for row in source_rows
        } | {str(row["db_orf_id"]) for row in source_rows}
        if len(all_orfs) != 2:
            raise RuntimeError(f"Unexpected selected pair cardinality: {pair_id}")
        first, second = sorted(all_orfs)
        raw_count = int(raw_counts[pair_id])
        paper_count = int(paper_counts[pair_id])
        final_count = int(final_counts[pair_id])
        if final_count:
            state = "public_candidate_tested_and_in_final_analysis"
        elif paper_count:
            state = "public_candidate_tested_excluded_by_published_prediction_intersection"
        elif raw_count:
            state = "public_candidate_raw_assay_only"
        else:
            state = "public_candidate_no_reported_assay_record"
        rows.append(
            {
                "selection_pair_record_id": stable_id(
                    "lambourne-selected-universe-pair", pair_id
                ),
                "unordered_orf_pair_id": pair_id,
                "source_dataset": "Zhang_et_al",
                "selected_ad_orf_ids": sorted(
                    {str(row["ad_orf_id"]) for row in source_rows}
                ),
                "selected_db_orf_ids": sorted(
                    {str(row["db_orf_id"]) for row in source_rows}
                ),
                "selection_physical_row_count": len(source_rows),
                "raw_assay_record_count": raw_count,
                "paper_record_count": paper_count,
                "final_analysis_record_count": final_count,
                "accession_candidates_a": list(orf_accessions.get(first, ())),
                "accession_candidates_b": list(orf_accessions.get(second, ())),
                "reconstruction_state": state,
                "paper_original_selected_pair_claim": paper_claim,
                "public_selection_unique_pair_count": unique_count,
                "discrepancy_to_paper_claim": unique_count - paper_claim,
                **GOVERNANCE_FALSE,
            }
        )
    metrics = {
        "paper_claimed_selected_pairs": paper_claim,
        "public_selection_physical_rows": len(selection),
        "public_selection_unique_unordered_orf_pairs": unique_count,
        "duplicate_physical_rows": len(selection) - unique_count,
        "discrepancy_unique_pairs_minus_paper_claim": unique_count - paper_claim,
        "tested_pairs_in_paper_table": len(paper_counts),
        "final_analysis_pairs": sum(final_counts.values()),
        "reconstruction_conclusion": (
            "public_archived_selection_file_does_not_reconstruct_an_exact_4100_pair_"
            "universe" if unique_count != paper_claim else "exactly_reconstructed"
        ),
    }
    return rows, metrics


def _participant_mapping_row(
    *,
    reference: FrozenReferenceIndex,
    panel_pair_id: str,
    participant_ordinal: int,
    orientation_role: str,
    source_accession: str,
    source_orf_id: str,
    construct: Mapping[str, Any],
    accession_maps: Mapping[str, Mapping[str, Iterable[str]]],
) -> dict[str, Any]:
    mapped = reference.map_accession(
        source_accession=source_accession,
        parent_record_id=panel_pair_id,
        participant_ordinal=participant_ordinal,
        evidence_family="assay_specific_y2h_observation",
    )
    candidates = [str(value) for value in mapped["candidate_uniprot_accessions"]]
    families = _family_ids_for_candidates(candidates, accession_maps)
    return {
        "mapping_record_id": stable_id(
            "lambourne-participant-map", panel_pair_id, participant_ordinal
        ),
        "panel_pair_id": panel_pair_id,
        "participant_ordinal": participant_ordinal,
        "orientation_role": orientation_role,
        "source_accession": source_accession,
        "source_orf_id": source_orf_id,
        "mapping_state": mapped["mapping_state"],
        "mapping_confidence": mapped["mapping_confidence"],
        "mapping_basis": mapped["mapping_basis"],
        "mapping_candidate_count": int(mapped["mapping_candidate_count"]),
        "candidate_sequence_ids": list(mapped["candidate_sequence_ids"]),
        "candidate_sequence_sha256s": list(mapped["candidate_sequence_sha256s"]),
        "candidate_uniprot_accessions": candidates,
        "mapped_sequence_id": mapped["mapped_sequence_id"],
        "mapped_uniprot_accession": mapped["mapped_uniprot_accession"],
        "mapped_isoform_id": mapped["mapped_isoform_id"],
        "mapped_sequence_sha256": mapped["mapped_sequence_sha256"],
        "mapped_sequence_length": mapped["mapped_sequence_length"],
        "mapped_sequence_view": mapped["mapped_sequence_view"],
        "reference_sequence_usable": bool(mapped["reference_sequence_usable"]),
        "exact_unique_mapping": bool(mapped["exact_unique_mapping"]),
        "uniref100_ids": families["UniRef100"],
        "uniref90_ids": families["UniRef90"],
        "uniref50_ids": families["UniRef50"],
        "construct_json": canonical_json(construct),
        "frozen_uniprot_release": reference.release,
        **GOVERNANCE_FALSE,
    }


def _build_panel_rows(
    *,
    paper_rows: list[dict[str, Any]],
    reference: FrozenReferenceIndex,
    accession_maps: Mapping[str, Mapping[str, Iterable[str]]],
    sequence_family_maps: Mapping[str, Mapping[str, Iterable[str]]],
    positive_index: Mapping[tuple[str, str], Mapping[str, Any]],
    positive_source_index: Mapping[tuple[str, str], Mapping[str, int]],
    contamination_index: Any,
    intact_negative_index: Mapping[tuple[str, str], list[Any]],
    negatome_index: Mapping[tuple[str, str], Mapping[str, list[str]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    panel: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    empty_positive = {
        "positive_evidence_count": 0,
        "qualifying_direct_evidence_count": 0,
        "broader_intact_evidence_count": 0,
        "permitted_pair_view_count": 0,
        "source_datasets": [],
        "detection_methods": [],
    }
    empty_source = {
        "huri_record_positive_count": 0,
        "intact_positive_count": 0,
        "intact_direct_positive_count": 0,
    }
    for source in paper_rows:
        if source["source_dataset"] != "Zhang_et_al":
            continue
        panel_pair_id = stable_id("lambourne-panel-pair", source["paper_record_id"])
        ad = _participant_mapping_row(
            reference=reference,
            panel_pair_id=panel_pair_id,
            participant_ordinal=1,
            orientation_role="prey_activation_domain",
            source_accession=str(source["uniprot_accession_ad"]),
            source_orf_id=str(source["ad_orf_id"]),
            construct=AD_CONSTRUCT,
            accession_maps=accession_maps,
        )
        db = _participant_mapping_row(
            reference=reference,
            panel_pair_id=panel_pair_id,
            participant_ordinal=2,
            orientation_role="bait_dna_binding_domain",
            source_accession=str(source["uniprot_accession_db"]),
            source_orf_id=str(source["db_orf_id"]),
            construct=DB_CONSTRUCT,
            accession_maps=accession_maps,
        )
        mappings.extend((ad, db))
        usable_count = sum(
            bool(row["reference_sequence_usable"]) for row in (ad, db)
        )
        pair_state = (
            "both_unique_human"
            if usable_count == 2
            else "one_unique_human"
            if usable_count == 1
            else "neither_unique_human"
        )
        sequence_pair: tuple[str, str] | None = None
        if usable_count == 2:
            sequence_pair = unordered_pair(
                str(ad["mapped_sequence_sha256"]),
                str(db["mapped_sequence_sha256"]),
            )
        positive = positive_index.get(sequence_pair, empty_positive)
        source_positive = positive_source_index.get(sequence_pair, empty_source)
        intact_negative = intact_negative_index.get(sequence_pair, [])
        negatome = negatome_index.get(
            sequence_pair, {"record_ids": [], "evidence_families": []}
        )
        contamination = contamination_flags(
            sequence_a=(sequence_pair[0] if sequence_pair else None),
            sequence_b=(sequence_pair[1] if sequence_pair else None),
            sequence_family_maps=sequence_family_maps,
            index=contamination_index,
        )
        in_final = bool(source["in_published_version"])
        if not in_final:
            eligibility = "not_in_final_analysis"
        elif sequence_pair is None:
            eligibility = "ineligible_unresolved_frozen_reference_mapping"
        elif source["evaluability_state"] != "evaluable":
            eligibility = "ineligible_technically_unevaluable"
        elif contamination["exact_future_training_pair_overlap"]:
            eligibility = "contaminated_exact_future_training_pair"
        else:
            eligibility = "audit_only_pair_disjoint_assay_specific_candidate"
        direct_count = int(positive["qualifying_direct_evidence_count"])
        pair_view_count = int(positive["permitted_pair_view_count"])
        intact_ids = sorted(record.evidence_id for record in intact_negative)
        panel.append(
            {
                "panel_pair_id": panel_pair_id,
                "paper_record_id": source["paper_record_id"],
                "source_dataset": source["source_dataset"],
                "source_row_ordinal": int(source["source_row_ordinal"]),
                "ad_orf_id": source["ad_orf_id"],
                "db_orf_id": source["db_orf_id"],
                "uniprot_accession_ad": source["uniprot_accession_ad"],
                "uniprot_accession_db": source["uniprot_accession_db"],
                "in_biorxiv_version": source["in_biorxiv_version"],
                "in_final_analysis": in_final,
                "reported_outcome": source["reported_outcome"],
                "outcome_semantics": source["outcome_semantics"],
                "attempted_state": source["attempted_state"],
                "evaluability_state": source["evaluability_state"],
                "technical_state": source["technical_state"],
                "observation_state": source["observation_state"],
                "sequence_confirmation_3at": source["sequence_confirmation_3at"],
                "sequence_confirmation_lw": source["sequence_confirmation_lw"],
                "pair_mapping_state": pair_state,
                "mapped_uniprot_accession_ad": ad["mapped_uniprot_accession"],
                "mapped_uniprot_accession_db": db["mapped_uniprot_accession"],
                "mapped_isoform_id_ad": ad["mapped_isoform_id"],
                "mapped_isoform_id_db": db["mapped_isoform_id"],
                "mapped_sequence_sha256_ad": ad["mapped_sequence_sha256"],
                "mapped_sequence_sha256_db": db["mapped_sequence_sha256"],
                "mapped_unordered_sequence_pair_id": (
                    unordered_sequence_pair_id(*sequence_pair) if sequence_pair else None
                ),
                "reference_pair_usable": sequence_pair is not None,
                "current_positive_check_performed": sequence_pair is not None,
                "huri_record_positive_count": int(
                    source_positive["huri_record_positive_count"]
                ),
                "huri_pair_view_count": pair_view_count,
                "intact_positive_count": int(source_positive["intact_positive_count"]),
                "qualifying_direct_positive_count": direct_count,
                "broader_intact_positive_count": int(
                    positive["broader_intact_evidence_count"]
                ),
                "current_permitted_positive_overlap": direct_count > 0
                or pair_view_count > 0,
                "positive_source_datasets": list(positive["source_datasets"]),
                "positive_detection_methods": list(positive["detection_methods"]),
                "intact_negative_overlap_count": len(intact_ids),
                "intact_negative_evidence_ids": intact_ids,
                "negatome_overlap_count": len(negatome["record_ids"]),
                "negatome_parent_record_ids": list(negatome["record_ids"]),
                "negatome_evidence_families": list(negatome["evidence_families"]),
                **contamination,
                "protected_benchmark_eligibility_state": eligibility,
                "assay_id": ASSAY_ID,
                "construct_ad_json": canonical_json(AD_CONSTRUCT),
                "construct_db_json": canonical_json(DB_CONSTRUCT),
                "experimental_conditions_json": canonical_json(
                    EXPERIMENTAL_CONDITIONS
                ),
                "frozen_uniprot_release": reference.release,
                **GOVERNANCE_FALSE,
            }
        )
    return panel, mappings


def _prepare_imex_rows(asset: Any) -> list[dict[str, Any]]:
    parsed = parse_mitab27(asset.path, raw_sha256=asset.sha256)
    rows: list[dict[str, Any]] = []
    for source in parsed:
        preview_record_id = stable_id(
            "im30553-preview-row", asset.sha256, source["preview_row_ordinal"]
        )
        rows.append(
            {
                **source,
                "preview_record_id": preview_record_id,
                "raw_file_path": asset.relative_path,
                "imex_study_id": "IM-30553",
                "provider_snapshot_state": (
                    "curated_not_integrated_preview_snapshot_2026-08-04"
                ),
                **GOVERNANCE_FALSE,
            }
        )
    return rows


def _reconcile_imex(
    imex_rows: Iterable[Mapping[str, Any]], panel_rows: Iterable[Mapping[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_accession: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in panel_rows:
        key = unordered_text_pair(
            row["uniprot_accession_ad"], row["uniprot_accession_db"]
        )
        by_accession[key].append(row)
    output: list[dict[str, Any]] = []
    states: Counter[str] = Counter()
    negative_flags: Counter[str] = Counter()
    matched_outcomes: Counter[str] = Counter()
    matched_pair_ids: set[str] = set()
    matched_final_pair_ids: set[str] = set()
    matched_outcome_pair_ids: dict[str, set[str]] = defaultdict(set)
    methods: Counter[str] = Counter()
    taxon_contexts: Counter[str] = Counter()
    for source in imex_rows:
        left, right = source["source_accession_a"], source["source_accession_b"]
        matched_rows: list[Mapping[str, Any]] = []
        candidates: list[str] = []
        bases: list[str] = []
        if left and right:
            matched_rows = by_accession.get(unordered_text_pair(left, right), [])
            candidates = sorted(str(row["panel_pair_id"]) for row in matched_rows)
            if candidates:
                bases.append("exact_unordered_reported_uniprot_accession_pair")
        if len(candidates) == 1:
            state = "exact_unique_panel_pair_match"
        elif candidates:
            state = "multiple_panel_pair_candidates"
        elif left and right:
            state = "reported_uniprot_pair_not_in_zhang_tested_panel"
        else:
            state = "preview_pair_lacks_two_uniprot_accessions"
        flag = source["negative_flag"]
        negative_flags["missing" if flag is None else str(bool(flag)).lower()] += 1
        methods[str(source["detection_method"])] += 1
        taxon_contexts[
            "|".join(
                (
                    str(source["taxid_a"]),
                    str(source["taxid_b"]),
                    str(source["host_taxid"]),
                )
            )
        ] += 1
        outcomes = sorted({str(row["reported_outcome"]) for row in matched_rows})
        for outcome in outcomes:
            matched_outcomes[outcome] += 1
        for row in matched_rows:
            pair_id = str(row["panel_pair_id"])
            matched_pair_ids.add(pair_id)
            matched_outcome_pair_ids[str(row["reported_outcome"])].add(pair_id)
            if bool(row["in_final_analysis"]):
                matched_final_pair_ids.add(pair_id)
        states[state] += 1
        output.append(
            {
                "reconciliation_record_id": stable_id(
                    "im30553-panel-reconciliation", source["preview_record_id"]
                ),
                "preview_record_id": source["preview_record_id"],
                "match_state": state,
                "match_bases": bases,
                "candidate_panel_pair_ids": candidates,
                "matched_panel_reported_outcomes": outcomes,
                "matched_panel_final_analysis_count": sum(
                    bool(row["in_final_analysis"]) for row in matched_rows
                ),
                "imex_outcome_semantics": (
                    "interaction_record_without_explicit_negative_flag"
                ),
                "supports_attempted_negative_or_na_semantics": False,
                "imex_study_id": "IM-30553",
                "provider_snapshot_state": (
                    "curated_not_integrated_preview_snapshot_2026-08-04"
                ),
                "preview_negative_flag_is_assay_bounded": True,
                **GOVERNANCE_FALSE,
            }
        )
    return output, {
        "preview_rows": len(output),
        "match_states": dict(sorted(states.items())),
        "negative_flags": dict(sorted(negative_flags.items())),
        "matched_panel_outcomes_by_preview_record": dict(sorted(matched_outcomes.items())),
        "matched_distinct_panel_pairs": len(matched_pair_ids),
        "matched_distinct_final_analysis_pairs": len(matched_final_pair_ids),
        "matched_distinct_panel_pairs_by_outcome": {
            outcome: len(pair_ids)
            for outcome, pair_ids in sorted(matched_outcome_pair_ids.items())
        },
        "detection_methods": dict(sorted(methods.items())),
        "taxon_context_count": len(taxon_contexts),
        "attempted_negative_or_na_semantics_available": False,
        "interpretation": (
            "IMEx preview contains interaction records from multiple assays/species and "
            "does not encode the attempted negative or technical states of Data 22"
        ),
        "provider_state": "curated_not_integrated_preview_snapshot_2026-08-04",
        "treated_as_intact_release_252": False,
    }


def _outcome_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    values = list(rows)
    outcomes = Counter(str(row["reported_outcome"]) for row in values)
    return {
        "pairs": len(values),
        "positive": outcomes["Positive"],
        "negative": outcomes["Negative"],
        "technically_unevaluable_or_na": sum(
            outcomes[name]
            for name in (
                "Failed sequence confirmation",
                "Autoactivator",
                "Test failed",
            )
        ),
        "evaluable": outcomes["Positive"] + outcomes["Negative"],
        "reported_outcomes": dict(sorted(outcomes.items())),
    }


def _aggregate_panel_metrics(
    *,
    panel_rows: list[dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    positive_metrics: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    final = [row for row in panel_rows if row["in_final_analysis"]]
    final_counts = _outcome_counts(final)
    mapping_states = Counter(str(row["mapping_state"]) for row in mapping_rows)
    mapping_confidence = Counter(str(row["mapping_confidence"]) for row in mapping_rows)
    pair_states = Counter(str(row["pair_mapping_state"]) for row in final)

    def overlap_counts(predicate: Any) -> dict[str, Any]:
        return _outcome_counts(row for row in final if predicate(row))

    exact_pair_disjoint = [
        row
        for row in final
        if row["reference_pair_usable"]
        and not row["exact_future_training_pair_overlap"]
    ]
    uniref90_pair_disjoint = [
        row
        for row in final
        if row["reference_pair_usable"] and not row["uniref90_pair_overlap"]
    ]
    uniref50_pair_disjoint = [
        row
        for row in final
        if row["reference_pair_usable"] and not row["uniref50_pair_overlap"]
    ]
    exact_endpoint_disjoint = [
        row
        for row in final
        if row["reference_pair_usable"] and not row["exact_endpoint_overlap"]
    ]
    uniref90_endpoint_disjoint = [
        row
        for row in final
        if row["reference_pair_usable"] and not row["uniref90_endpoint_overlap"]
    ]
    uniref50_endpoint_disjoint = [
        row
        for row in final
        if row["reference_pair_usable"] and not row["uniref50_endpoint_overlap"]
    ]
    pair_disjoint_counts = _outcome_counts(exact_pair_disjoint)
    minimum_positive = int(
        config["benchmark_feasibility"]["minimum_positive_assay_observations"]
    )
    minimum_negative = int(
        config["benchmark_feasibility"]["minimum_negative_assay_observations"]
    )
    pair_diagnostic_size_ok = (
        pair_disjoint_counts["positive"] >= minimum_positive
        and pair_disjoint_counts["negative"] >= minimum_negative
    )
    endpoint_disjoint_counts = _outcome_counts(uniref90_endpoint_disjoint)
    endpoint_disjoint_size_ok = (
        endpoint_disjoint_counts["positive"] >= minimum_positive
        and endpoint_disjoint_counts["negative"] >= minimum_negative
    )
    if pair_diagnostic_size_ok:
        decision = (
            "conditionally_feasible_only_as_protected_exact_pair_disjoint_assay_specific_"
            "assay_transfer_diagnostic_pending_governance"
        )
    else:
        decision = "not_statistically_feasible_after_exact_pair_decontamination"
    feasibility = {
        "decision": decision,
        "benchmark_constructed": False,
        "split_constructed": False,
        "integration_authorized": False,
        "exact_pair_disjoint_assay_specific_diagnostic": {
            **pair_disjoint_counts,
            "minimum_positive_required": minimum_positive,
            "minimum_negative_required": minimum_negative,
            "size_threshold_met": pair_diagnostic_size_ok,
            "remaining_participant_overlap_is_expected": True,
        },
        "uniref90_endpoint_disjoint_generalization": {
            **endpoint_disjoint_counts,
            "minimum_positive_required": minimum_positive,
            "minimum_negative_required": minimum_negative,
            "size_threshold_met": endpoint_disjoint_size_ok,
        },
        "sequence_family_generalization_supported": endpoint_disjoint_size_ok,
        "limitations": [
            "single Y2H-v1 orientation and condition per selected pair",
            "model-selected rather than proteome-wide probability sample",
            "technical missingness is not equivalent to a negative observation",
            "substantial participant-level overlap with current permitted evidence",
            "exact 4,100-pair original universe is not reconstructed by public files",
        ],
    }
    metrics = {
        "tested_zhang_pairs": len(panel_rows),
        "final_analysis": final_counts,
        "mapping": {
            "participant_rows": len(mapping_rows),
            "mapping_states": dict(sorted(mapping_states.items())),
            "mapping_confidence": dict(sorted(mapping_confidence.items())),
            "final_pair_states": dict(sorted(pair_states.items())),
        },
        "current_evidence_overlap": {
            "huri_record_positive": overlap_counts(
                lambda row: row["huri_record_positive_count"] > 0
            ),
            "huri_permitted_pair_view": overlap_counts(
                lambda row: row["huri_pair_view_count"] > 0
            ),
            "intact_positive": overlap_counts(
                lambda row: row["intact_positive_count"] > 0
            ),
            "qualifying_direct_or_permitted_pair_view": overlap_counts(
                lambda row: row["current_permitted_positive_overlap"]
            ),
            "intact_negative_939": overlap_counts(
                lambda row: row["intact_negative_overlap_count"] > 0
            ),
            "negatome": overlap_counts(lambda row: row["negatome_overlap_count"] > 0),
            "positive_index_metrics": dict(positive_metrics),
        },
        "contamination": {
            "exact_pair_overlap": overlap_counts(
                lambda row: row["exact_future_training_pair_overlap"]
            ),
            "uniref90_pair_overlap": overlap_counts(
                lambda row: row["uniref90_pair_overlap"]
            ),
            "uniref50_pair_overlap": overlap_counts(
                lambda row: row["uniref50_pair_overlap"]
            ),
            "exact_pair_disjoint": _outcome_counts(exact_pair_disjoint),
            "uniref90_pair_disjoint": _outcome_counts(uniref90_pair_disjoint),
            "uniref50_pair_disjoint": _outcome_counts(uniref50_pair_disjoint),
            "exact_endpoint_disjoint": _outcome_counts(exact_endpoint_disjoint),
            "uniref90_endpoint_disjoint": _outcome_counts(uniref90_endpoint_disjoint),
            "uniref50_endpoint_disjoint": _outcome_counts(uniref50_endpoint_disjoint),
        },
    }
    return metrics, feasibility


def run_audit(
    *,
    project_root: Path,
    config_path: Path,
    staging_root: Path | None = None,
    canonical_root: Path | None = None,
    report_path: Path | None = None,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    started_at = datetime.now(timezone.utc).isoformat()
    config_path = _resolve_inside(
        project_root, config_path, project_root / "configs", strict=True
    )
    config = _load_yaml(config_path)
    _validate_config(config)
    staging_target = _resolve_inside(
        project_root,
        staging_root or str(config["outputs"]["staging_root"]),
        project_root / "data/staging",
        strict=False,
    )
    canonical_target = _resolve_inside(
        project_root,
        canonical_root or str(config["outputs"]["canonical_root"]),
        project_root / "data/canonical",
        strict=False,
    )
    report_target = _resolve_inside(
        project_root,
        report_path or str(config["outputs"]["audit_report"]),
        project_root / "artifacts/validation",
        strict=False,
    )
    smoke = all("_smoke_" in path.parts for path in (staging_target, canonical_target, report_target))
    if allow_dirty != smoke:
        raise RuntimeError("--allow-dirty is restricted to consistently named _smoke_ outputs")
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production Lambourne audit requires a clean Git worktree")

    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = _resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    if active_container != expected_container:
        raise RuntimeError("Active Apptainer image differs from configuration")
    container_sha = sha256_file(active_container)
    if container_sha != str(config["runtime"]["container_sha256"]):
        raise RuntimeError("Active Apptainer image SHA-256 differs from configuration")
    if platform.machine() != str(config["runtime"]["architecture"]):
        raise RuntimeError("Lambourne audit is running on the wrong architecture")

    paths: dict[str, Path] = {}
    verified_documents: dict[str, Any] = {}
    for name, specification in config["inputs"]["documents"].items():
        path = _resolve_inside(
            project_root,
            str(specification["path"]),
            project_root / str(specification["boundary"]),
            strict=True,
        )
        digest = sha256_file(path)
        if digest != str(specification["sha256"]):
            raise RuntimeError(f"Document SHA-256 mismatch: {name}")
        paths[str(name)] = path
        verified_documents[str(name)] = {
            "path": path.relative_to(project_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": digest,
        }
    acquisition = _load_json(paths["acquisition_manifest"])
    raw_verification = _load_json(paths["raw_verification_report"])
    primary_parse = _load_json(paths["primary_parse_manifest"])
    primary_validation = _load_json(paths["primary_staging_validation"])
    reconciliation = _load_json(paths["primary_reconciliation_manifest"])
    reconciliation_validation = _load_json(paths["primary_reconciliation_validation"])
    negative_manifest = _load_json(paths["negative_audit_manifest"])
    negative_validation = _load_json(paths["negative_audit_validation"])
    if acquisition.get("status") != "pass" or acquisition.get("errors"):
        raise RuntimeError("Lambourne acquisition is not a passed manifest")
    if raw_verification.get("status") != "pass":
        raise RuntimeError("Lambourne raw verification did not pass")
    if primary_parse.get("status") != "complete" or primary_validation.get("status") != "pass":
        raise RuntimeError("Primary staging inputs are not validated")
    if reconciliation.get("status") != "complete" or reconciliation_validation.get("status") != "pass":
        raise RuntimeError("Primary reconciliation inputs are not validated")
    if negative_manifest.get("status") != "complete" or negative_validation.get("status") != "pass":
        raise RuntimeError("Negative-evidence audit inputs are not validated")
    for upstream in (primary_parse, reconciliation, negative_manifest):
        if upstream.get("label_construction_performed") is not False:
            raise RuntimeError("An upstream input indicates label construction")
        if upstream.get("model_training_performed") is not False:
            raise RuntimeError("An upstream input indicates model training")

    for name, relative in config["inputs"]["dataset_paths"].items():
        boundary = "data/staging" if str(relative).startswith("data/staging/") else "data/canonical"
        paths[str(name)] = _resolve_inside(
            project_root, str(relative), project_root / boundary, strict=True
        )

    _, assets = load_asset_index(
        project_root, paths["acquisition_manifest"].relative_to(project_root)
    )
    required_assets = config["raw_assets"]
    raw_verified: dict[str, Any] = {}
    for logical_name, asset_id in required_assets.items():
        asset = assets[str(asset_id)]
        raw_verified[str(logical_name)] = verify_asset(asset)

    code_asset = assets[str(required_assets["archived_code"])]
    input_asset = assets[str(required_assets["archived_input"])]
    code_inventory, code_selected = scan_zip_archive(
        code_asset.path,
        asset_id=code_asset.asset_id,
        archive_sha256=code_asset.sha256,
        select=lambda name: any(name.endswith(suffix) for suffix in CODE_SELECTED_SUFFIXES),
    )
    input_inventory, input_selected = scan_tar_gzip_archive(
        input_asset.path,
        asset_id=input_asset.asset_id,
        archive_sha256=input_asset.sha256,
        select=lambda name: Path(name).name in INPUT_SELECTED_BASENAMES,
    )
    archive_rows = _archive_inventory_rows(
        code_inventory, asset=code_asset, license_id="MIT"
    ) + _archive_inventory_rows(
        input_inventory, asset=input_asset, license_id="MIT"
    )

    selection_name, selection_payload, selection_sha = _selected_payload(
        code_selected,
        "data/internal/predicting_human_interactome_pairs_to_test_2024-12-13.tsv",
    )
    raw_name, raw_payload, raw_sha = _selected_payload(
        code_selected,
        "data/internal/Y2H_v1_pairwise_test_AlphaFoldRoseTTAFold_human.tsv",
    )
    map_name, map_payload, _map_sha = _selected_payload(
        code_selected,
        "data/internal/uniprot_ac_to_orf_id_used_for_Zhang_et_al_experiment.tsv",
    )
    selection_rows = parse_selection_records(
        selection_payload, member_path=selection_name, member_sha256=selection_sha
    )
    raw_rows = parse_raw_assay_records(
        raw_payload, member_path=raw_name, member_sha256=raw_sha
    )
    orf_accessions = parse_orf_accession_map(map_payload)
    paper_asset = assets[str(required_assets["supplementary_data_22"])]
    paper_rows = parse_paper_records(
        paper_asset.path,
        raw_relative_path=paper_asset.relative_path,
        raw_sha256=paper_asset.sha256,
        raw_assay_rows=raw_rows,
    )
    expected = config["expected"]
    observed_counts = {
        "selection_rows": len(selection_rows),
        "raw_assay_rows": len(raw_rows),
        "paper_rows": len(paper_rows),
        "paper_zhang_rows": sum(row["source_dataset"] == "Zhang_et_al" for row in paper_rows),
    }
    for name, observed in observed_counts.items():
        if observed != int(expected[name]):
            raise RuntimeError(f"Source row count differs for {name}: {observed}")
    final_summary = summarize_final_analysis(paper_rows)
    for name in (
        "selected_pairs",
        "positive_assay_observations",
        "negative_assay_observations",
        "technically_unevaluable_or_na",
        "evaluable",
    ):
        if int(final_summary[name]) != int(expected["final_analysis"][name]):
            raise RuntimeError(f"Final-analysis count differs for {name}")

    science_name, science_payload, science_sha = _selected_payload(
        input_selected, "science.adt1630_data_s1_to_s8.xlsx"
    )
    science_pairs = _science_published_pairs(science_payload)
    final_filter_disagreements = sum(
        bool(row["in_published_version"])
        != (unordered_text_pair(row["uniprot_accession_ad"], row["uniprot_accession_db"]) in science_pairs)
        for row in paper_rows
        if row["source_dataset"] == "Zhang_et_al"
    )
    if final_filter_disagreements:
        raise RuntimeError("Paper final flags differ from frozen Science Data S3 membership")
    archive_crosschecks: dict[str, Any] = {
        "science_data_s3_member": science_name,
        "science_data_s3_member_sha256": science_sha,
        "final_filter_disagreements": final_filter_disagreements,
    }
    for suffix, code_payload in (
        ("predicting_human_interactome_pairs_to_test_2024-12-13.tsv", selection_payload),
        ("Y2H_v1_pairwise_test_AlphaFoldRoseTTAFold_human.tsv", raw_payload),
        ("uniprot_ac_to_orf_id_used_for_Zhang_et_al_experiment.tsv", map_payload),
    ):
        matches = [(name, value) for name, value in input_selected.items() if name.endswith(suffix)]
        archive_crosschecks[f"input_copy_{suffix}"] = {
            "copies_found": len(matches),
            "byte_identical_to_code_archive": bool(matches and matches[0][1] == code_payload),
        }
        if matches and matches[0][1] != code_payload:
            raise RuntimeError(f"Code/input archive source copies differ: {suffix}")

    universe_rows, universe_metrics = _reconcile_selected_universe(
        selection_rows=selection_rows,
        raw_rows=raw_rows,
        paper_rows=paper_rows,
        orf_accessions=orf_accessions,
        paper_claim=int(expected["paper_original_selected_pair_claim"]),
    )
    if universe_metrics["public_selection_unique_unordered_orf_pairs"] != int(
        expected["public_selection_unique_zhang_pairs"]
    ):
        raise RuntimeError("Public selected-universe unique pair count differs")

    imex_asset = assets[str(required_assets["imex_mitab27"])]
    imex_rows = _prepare_imex_rows(imex_asset)
    xml_asset = assets[str(required_assets["imex_xml300"])]
    xml_inventory = xml_preview_inventory(xml_asset.path)

    reference = FrozenReferenceIndex.load(
        sequence_root=paths["protein_sequences"],
        dat_path=paths["frozen_uniprot_dat"],
        release=str(config["inputs"]["frozen_uniprot_release"]),
        taxid=int(config["inputs"]["frozen_taxid"]),
        project_root=project_root,
    )
    accession_maps, sequence_family_maps = load_sequence_family_maps(
        identifier_mapping_root=paths["identifier_mappings"], reference=reference
    )
    connection = duckdb.connect()
    connection.execute(f"SET memory_limit='{config['runtime']['duckdb_memory_limit']}'")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    try:
        register_evidence_views(connection, paths)
        positive_index, positive_metrics = build_positive_pair_index(
            connection,
            permitted_pair_views=config["evidence_policy"]["permitted_pair_views"],
        )
        positive_source_index = source_specific_positive_index(connection)
        intact_negative_records = load_intact_negative_records(connection)
    finally:
        connection.close()
    if len(intact_negative_records) != int(expected["intact_negative_records"]):
        raise RuntimeError("Frozen IntAct negative record count differs")
    _, intact_negative_index = index_intact_negatives(intact_negative_records)
    negatome_index = load_negatome_pair_index(paths["negatome_record_audit"])
    contamination_index = build_contamination_index(
        positive_index=positive_index, sequence_family_maps=sequence_family_maps
    )
    panel_rows, mapping_rows = _build_panel_rows(
        paper_rows=paper_rows,
        reference=reference,
        accession_maps=accession_maps,
        sequence_family_maps=sequence_family_maps,
        positive_index=positive_index,
        positive_source_index=positive_source_index,
        contamination_index=contamination_index,
        intact_negative_index=intact_negative_index,
        negatome_index=negatome_index,
    )
    imex_reconciliation, imex_metrics = _reconcile_imex(imex_rows, panel_rows)
    panel_metrics, feasibility = _aggregate_panel_metrics(
        panel_rows=panel_rows,
        mapping_rows=mapping_rows,
        positive_metrics=positive_metrics,
        config=config,
    )

    source_data_asset = assets[str(required_assets["article_source_data"])]
    source_data_inventory = _workbook_inventory(source_data_asset.path)
    contract = load_contract(paths["audit_schema"])
    metadata = {
        "audit_version": LAMBOURNE_AUDIT_VERSION,
        "audit_git_commit": str(git["commit"]),
        "container_sif_sha256": container_sha,
        "redistribution": "internal_governance_bounded_audit_only",
    }
    staging_table_rows = {
        "archive_members": archive_rows,
        "selection_records": selection_rows,
        "raw_assay_records": raw_rows,
        "paper_records": paper_rows,
        "imex_preview_records": imex_rows,
    }
    canonical_table_rows = {
        "selected_universe_reconciliation": universe_rows,
        "participant_mappings": mapping_rows,
        "panel_pair_audit": panel_rows,
        "imex_pair_reconciliation": imex_reconciliation,
        "assay_metadata": [assay_metadata_row()],
    }
    with AtomicDatasetDirectory(staging_target) as temporary_staging:
        staging_summaries = {
            name: _write_table(
                root=temporary_staging,
                table_name=name,
                rows=staging_table_rows[name],
                contract=contract,
                config=config,
                metadata=metadata,
            )
            for name in STAGING_TABLES
        }
        staging_summaries = _replace_prefix(
            staging_summaries, temporary_staging.as_posix(), staging_target.as_posix()
        )
        staging_manifest = {
            "schema_version": 1,
            "audit_id": config["audit_id"],
            "audit_version": LAMBOURNE_AUDIT_VERSION,
            "status": "complete",
            "scope": "internal_provenance_preserving_no_training_labels",
            "runtime": {
                "container_sif_sha256": container_sha,
                "architecture": platform.machine(),
                "python": platform.python_version(),
                "pyarrow": pyarrow.__version__,
            },
            "git": git,
            "verified_documents": verified_documents,
            "raw_assets": raw_verified,
            "tables": staging_summaries,
            "outcomes_as_training_labels": False,
            "merge_with_negatome": False,
            "benchmark_split_construction": False,
            "benchmark_integration": False,
            "universal_nonbinding_interpretation": False,
            "label_construction_performed": False,
            "model_training_performed": False,
        }
        staging_manifest_path = temporary_staging / "STAGING_MANIFEST.json"
        staging_manifest_sha = _write_manifest(staging_manifest_path, staging_manifest)
        _make_read_only(temporary_staging)

        with AtomicDatasetDirectory(canonical_target) as temporary_canonical:
            canonical_summaries = {
                name: _write_table(
                    root=temporary_canonical,
                    table_name=name,
                    rows=canonical_table_rows[name],
                    contract=contract,
                    config=config,
                    metadata=metadata,
                )
                for name in CANONICAL_TABLES
            }
            canonical_summaries = _replace_prefix(
                canonical_summaries,
                temporary_canonical.as_posix(),
                canonical_target.as_posix(),
            )
            canonical_manifest = {
                "schema_version": 1,
                "audit_id": config["audit_id"],
                "audit_version": LAMBOURNE_AUDIT_VERSION,
                "status": "complete",
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "pair_level_semantics_and_contamination_audit_only",
                "runtime": {
                    "container_sif_sha256": container_sha,
                    "architecture": platform.machine(),
                    "python": platform.python_version(),
                    "pyarrow": pyarrow.__version__,
                    "duckdb": duckdb.__version__,
                },
                "git": git,
                "inputs": {
                    "config": config_path.relative_to(project_root).as_posix(),
                    "config_sha256": sha256_file(config_path),
                    "staging_manifest": (
                        staging_target / "STAGING_MANIFEST.json"
                    ).relative_to(project_root).as_posix(),
                    "staging_manifest_sha256": staging_manifest_sha,
                },
                "tables": canonical_summaries,
                "governance": {
                    "outcomes_as_training_labels": False,
                    "merge_with_negatome": False,
                    "benchmark_split_construction": False,
                    "benchmark_integration": False,
                    "universal_nonbinding_interpretation": False,
                    "return_to_governance_required": True,
                },
                "label_construction_performed": False,
                "model_training_performed": False,
            }
            canonical_manifest_path = temporary_canonical / "AUDIT_MANIFEST.json"
            canonical_manifest_sha = _write_manifest(
                canonical_manifest_path, canonical_manifest
            )
            _make_read_only(temporary_canonical)

    report = {
        "schema_version": 1,
        "audit_id": config["audit_id"],
        "audit_version": LAMBOURNE_AUDIT_VERSION,
        "status": "complete_pending_independent_validation_and_governance",
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "runtime": {
            "container_sif_sha256": container_sha,
            "architecture": platform.machine(),
            "python": platform.python_version(),
        },
        "source_inventory": {
            "verified_assets": len(raw_verified),
            "code_archive_members": len(code_inventory),
            "input_archive_members": len(input_inventory),
            "selected_archive_members": sum(
                bool(row["selected_for_semantics"]) for row in archive_rows
            ),
            "archive_crosschecks": archive_crosschecks,
            "article_source_data_workbook": source_data_inventory,
            "imex_xml_preview": xml_inventory,
        },
        "selected_universe": universe_metrics,
        "final_analysis": final_summary,
        "panel_audit": panel_metrics,
        "imex_preview": imex_metrics,
        "benchmark_feasibility": feasibility,
        "claim_identifiability": benchmark_claim_identifiability(),
        "artifacts": {
            "staging_manifest_sha256": staging_manifest_sha,
            "canonical_manifest_sha256": canonical_manifest_sha,
        },
        "governance": {
            "outcomes_used_as_training_labels": False,
            "merged_with_negatome": False,
            "benchmark_splits_constructed": False,
            "models_trained": False,
            "universal_nonbinding_claimed": False,
            "benchmark_integration_authorized": False,
            "return_to_governance_required": True,
        },
    }
    _write_report(report_target, report, project_root)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the governance-bounded Lambourne Y2H-v1 semantics audit"
    )
    parser.add_argument(
        "--config", type=Path, default=Path("configs/lambourne_y2h_audit_v1.yaml")
    )
    parser.add_argument("--staging-root", type=Path)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    report = run_audit(
        project_root=project_root,
        config_path=args.config,
        staging_root=args.staging_root,
        canonical_root=args.canonical_root,
        report_path=args.report,
        allow_dirty=args.allow_dirty,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
