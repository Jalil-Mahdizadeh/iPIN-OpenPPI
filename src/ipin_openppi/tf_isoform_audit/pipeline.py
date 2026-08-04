"""Execute the governance-bounded 2025 TF-isoform Y2H/N2H audit."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import stat
from typing import Any, Iterable, Mapping

import duckdb
import pandas as pd
import pyarrow
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
from ipin_openppi.lambourne_audit.archives import (
    scan_tar_gzip_archive,
    scan_zip_archive,
)
from ipin_openppi.lambourne_audit.overlap import (
    build_contamination_index,
    contamination_flags,
    load_sequence_family_maps,
    source_specific_positive_index,
)
from ipin_openppi.negative_evidence.evidence import (
    build_positive_pair_index,
    register_evidence_views,
    unordered_pair,
    unordered_sequence_pair_id,
)
from ipin_openppi.negative_evidence.reference import FrozenReferenceIndex
from ipin_openppi.tf_isoform_audit import TF_ISOFORM_AUDIT_VERSION
from ipin_openppi.tf_isoform_audit.mapping import AuditReferenceMaps
from ipin_openppi.tf_isoform_audit.semantics import (
    GOVERNANCE_FALSE,
    classify_y2h_outcome,
    optional_bool,
    percentile,
    reconstruct_analytical_filter,
    sequence_sha256,
    split_multi_identifier,
    text,
    translate_cds,
)
from ipin_openppi.tf_isoform_audit.source import (
    CLONE_NT_FASTA_PATH,
    INTERNAL_CLONES_PATH,
    LOADER_SUFFIX,
    PUBLIC_CLONE_SUFFIX,
    PUBLIC_N2H_SUFFIX,
    PUBLIC_Y2H_SUFFIX,
    RAW_N2H_PATH,
    RAW_Y2H_PATH,
    README_SUFFIX,
    SCREEN_SELECTION_PATH,
    SUPPLEMENT_CHECK_SUFFIX,
    clone_id_from_accession,
    parse_fasta,
    public_row_key,
    raw_row_key,
    read_tsv,
    unique_member,
)
from ipin_openppi.validation.staging import _write_report


STAGING_TABLES = (
    "archive_members",
    "clone_records",
    "screen_selection_records",
    "raw_y2h_records",
    "raw_n2h_records",
)
CANONICAL_TABLES = (
    "clone_sequence_mappings",
    "partner_construct_mappings",
    "y2h_pair_audit",
    "n2h_observation_audit",
    "matched_contrast_groups",
    "analytical_filter_steps",
)
CODE_SELECTED_SUFFIXES = (
    PUBLIC_CLONE_SUFFIX,
    PUBLIC_Y2H_SUFFIX,
    PUBLIC_N2H_SUFFIX,
    LOADER_SUFFIX,
    SUPPLEMENT_CHECK_SUFFIX,
    README_SUFFIX,
)
INPUT_SELECTED_PATHS = {
    RAW_Y2H_PATH,
    SCREEN_SELECTION_PATH,
    INTERNAL_CLONES_PATH,
    RAW_N2H_PATH,
    CLONE_NT_FASTA_PATH,
}

ASSAY_METADATA = {
    "assay": "pairwise yeast two-hybrid",
    "assay_family": "Y2H",
    "host": "Saccharomyces cerevisiae",
    "ad_orientation": "TF isoform fused to Gal4 activation domain in Y8800",
    "db_orientation": "hORFeome v9.1 partner fused to Gal4 DNA-binding domain in Y8930",
    "pair_media": "SC-Leu-Trp-His plus 1 mM 3AT",
    "mating_control_media": "SC-Leu-Trp",
    "autoactivation_control": "same DB-ORF mated to AD-null",
    "score_range": "0,1,2,3,4,NA",
    "positive_rule": "pair 3AT score >=2 and greater than autoactivation-control score",
    "negative_rule": "source-reported False after valid growth and sequence acceptance",
    "technical_acceptance": "valid growth score and ORF identities confirmed by sequencing",
    "expression_measurement": "not reported; no expression-failure state is inferred",
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


def _validate_config(config: Mapping[str, Any]) -> None:
    if int(config.get("schema_version", -1)) != 1:
        raise RuntimeError("Unsupported TF-isoform audit configuration schema")
    if str(config.get("audit_version")) != TF_ISOFORM_AUDIT_VERSION:
        raise RuntimeError("TF-isoform audit configuration/code version mismatch")
    authorization = config.get("authorization", {})
    for key in (
        "provenance_preserving_parsing",
        "frozen_reference_mapping",
        "positive_evidence_overlap_audit",
        "aggregate_diagnostic_feasibility_assessment",
    ):
        if authorization.get(key) is not True:
            raise RuntimeError(f"Required audit action is not authorized: {key}")
    for key in (
        "outcomes_as_training_labels",
        "training_data_integration",
        "merge_with_negatome",
        "model_training",
        "model_tuning",
        "model_calibration",
        "thresholding",
        "benchmark_construction",
        "benchmark_integration",
        "primary_pur_design_change",
        "universal_nonbinding_interpretation",
    ):
        if authorization.get(key) is not False:
            raise RuntimeError(f"Prohibited action must remain false: {key}")
    if config["governance"]["return_before_benchmark_integration"] is not True:
        raise RuntimeError("Return-to-governance guard is absent")


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
    for path in sorted(root.rglob("*"), reverse=True):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"Generated dataset contains a link: {path}")
        path.chmod(0o444 if path.is_file() else 0o555)
    root.chmod(0o555)


def _bool_token(value: Any) -> bool:
    parsed = optional_bool(value)
    if parsed is None:
        raise ValueError(f"Required boolean is absent: {value!r}")
    return parsed


def _member(values: dict[str, bytes], suffix: str) -> tuple[str, bytes, str]:
    name, payload = unique_member(values, suffix)
    return name, payload, sha256(payload).hexdigest()


def _inventory_rows(
    values: list[dict[str, object]], *, asset: Any
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in values:
        row = dict(source)
        row["selected_for_audit"] = bool(row.pop("selected_for_semantics"))
        row["source_archive_path"] = asset.relative_path
        row["license_id"] = "CC-BY-4.0"
        row["redistribution_tier"] = "internal_governance_bounded_audit_only"
        rows.append(row)
    return rows


def _verified_inputs(
    project_root: Path, config: Mapping[str, Any]
) -> tuple[dict[str, Path], dict[str, Any]]:
    paths: dict[str, Path] = {}
    documents: dict[str, Any] = {}
    for name, specification in config["inputs"]["documents"].items():
        path = _resolve_inside(
            project_root,
            str(specification["path"]),
            project_root / str(specification["boundary"]),
            strict=True,
        )
        digest = sha256_file(path)
        if digest != str(specification["sha256"]):
            raise RuntimeError(f"Input document SHA-256 mismatch: {name}")
        paths[str(name)] = path
        documents[str(name)] = {
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
    if acquisition.get("status") != "pass" or acquisition.get("errors"):
        raise RuntimeError("TF-isoform acquisition manifest is not passed")
    if raw_verification.get("status") != "pass":
        raise RuntimeError("Independent raw verification did not pass")
    if primary_parse.get("status") != "complete" or primary_validation.get("status") != "pass":
        raise RuntimeError("Primary staging inputs are not validated")
    if reconciliation.get("status") != "complete" or reconciliation_validation.get("status") != "pass":
        raise RuntimeError("Primary reconciliation inputs are not validated")
    for upstream in (acquisition, raw_verification, primary_parse, reconciliation):
        if upstream.get("label_construction_performed") not in {False, None}:
            raise RuntimeError("An upstream input indicates label construction")
        if upstream.get("model_training_performed") not in {False, None}:
            raise RuntimeError("An upstream input indicates model training")
    for name, relative in config["inputs"]["dataset_paths"].items():
        boundary = "data/staging" if str(relative).startswith("data/staging/") else "data/canonical"
        paths[str(name)] = _resolve_inside(
            project_root, str(relative), project_root / boundary, strict=True
        )
    return paths, documents


def _source_reconstruction(
    *,
    project_root: Path,
    config: Mapping[str, Any],
    paths: Mapping[str, Path],
) -> dict[str, Any]:
    _, assets = load_asset_index(
        project_root, paths["acquisition_manifest"].relative_to(project_root)
    )
    verified_assets: dict[str, Any] = {}
    for logical_name, asset_id in config["raw_assets"].items():
        verified_assets[str(logical_name)] = verify_asset(assets[str(asset_id)])
    verified_licenses: dict[str, str] = {}
    for logical_name in ("code_metadata", "input_metadata"):
        metadata_asset = assets[str(config["raw_assets"][logical_name])]
        metadata = _load_json(metadata_asset.path)
        license_id = text(metadata.get("metadata", {}).get("license", {}).get("id"))
        if license_id.casefold() != "cc-by-4.0":
            raise RuntimeError(f"Zenodo license is not the governed CC-BY-4.0: {logical_name}")
        verified_licenses[logical_name] = license_id

    code_asset = assets[str(config["raw_assets"]["archived_code"])]
    input_asset = assets[str(config["raw_assets"]["archived_input"])]
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
        select=lambda name: name in INPUT_SELECTED_PATHS,
    )
    archive_rows = _inventory_rows(code_inventory, asset=code_asset) + _inventory_rows(
        input_inventory, asset=input_asset
    )

    clone_name, clone_payload, clone_sha = _member(code_selected, PUBLIC_CLONE_SUFFIX)
    public_y2h_name, public_y2h_payload, public_y2h_sha = _member(
        code_selected, PUBLIC_Y2H_SUFFIX
    )
    public_n2h_name, public_n2h_payload, public_n2h_sha = _member(
        code_selected, PUBLIC_N2H_SUFFIX
    )
    loader_name, _loader_payload, loader_sha = _member(code_selected, LOADER_SUFFIX)
    raw_y2h_name, raw_y2h_payload, raw_y2h_sha = _member(
        input_selected, RAW_Y2H_PATH
    )
    selection_name, selection_payload, selection_sha = _member(
        input_selected, SCREEN_SELECTION_PATH
    )
    internal_clone_name, internal_clone_payload, internal_clone_sha = _member(
        input_selected, INTERNAL_CLONES_PATH
    )
    raw_n2h_name, raw_n2h_payload, raw_n2h_sha = _member(
        input_selected, RAW_N2H_PATH
    )
    fasta_name, fasta_payload, fasta_sha = _member(
        input_selected, CLONE_NT_FASTA_PATH
    )

    clones = read_tsv(clone_payload, PUBLIC_CLONE_SUFFIX)
    public_y2h = read_tsv(public_y2h_payload, PUBLIC_Y2H_SUFFIX)
    public_n2h = read_tsv(public_n2h_payload, PUBLIC_N2H_SUFFIX)
    raw_y2h = read_tsv(raw_y2h_payload, RAW_Y2H_PATH)
    selection = read_tsv(selection_payload, SCREEN_SELECTION_PATH)
    internal_clones = read_tsv(internal_clone_payload, INTERNAL_CLONES_PATH)
    raw_n2h = read_tsv(raw_n2h_payload, RAW_N2H_PATH)
    nt_fasta = parse_fasta(fasta_payload)

    expected = config["expected"]
    observed_sizes = {
        "clone_rows": len(clones),
        "screen_selection_rows": len(selection),
        "raw_y2h_rows": len(raw_y2h),
        "public_y2h_rows": len(public_y2h),
        "raw_n2h_rows": len(raw_n2h),
        "public_n2h_rows": len(public_n2h),
    }
    for key, value in observed_sizes.items():
        if value != int(expected[key]):
            raise RuntimeError(f"Source row count differs for {key}: {value}")

    internal_clones = internal_clones.copy()
    internal_clones["clone_id"] = internal_clones["clone_acc"].map(
        clone_id_from_accession
    )
    if internal_clones["clone_id"].duplicated().any():
        raise RuntimeError("Internal clone identifiers are not unique")
    internal_by_id = internal_clones.set_index("clone_id").to_dict("index")
    clone_rows: list[dict[str, Any]] = []
    clone_hash_by_id: dict[str, str] = {}
    for ordinal, row in enumerate(clones.itertuples(index=False), start=1):
        clone_id = text(row.clone_id)
        if clone_id not in internal_by_id:
            raise RuntimeError(f"Public clone lacks internal accession: {clone_id}")
        internal = internal_by_id[clone_id]
        clone_accession = text(internal["clone_acc"])
        cds = text(row.cds_seq).upper()
        aa = text(row.aa_seq).upper()
        if nt_fasta.get(clone_accession) != cds:
            raise RuntimeError(f"Clone CDS differs from raw FASTA: {clone_id}")
        try:
            translation_concordant = translate_cds(cds) == aa
        except ValueError:
            translation_concordant = False
        aa_hash = sequence_sha256(aa)
        clone_hash_by_id[clone_id] = aa_hash
        clone_rows.append(
            {
                "clone_record_id": stable_id("tfiso-clone", clone_id),
                "source_row_ordinal": ordinal,
                "clone_id": clone_id,
                "clone_accession": clone_accession,
                "gene_symbol": text(row.gene_symbol),
                "isoform_status": text(row.isoform_status),
                "gencode_transcript_ids": split_multi_identifier(row.gencode_transcript_names),
                "ensembl_transcript_ids": split_multi_identifier(row.ensembl_transcript_ids),
                "cds_sequence": cds,
                "aa_sequence": aa,
                "cds_sha256": sequence_sha256(cds),
                "aa_sha256": aa_hash,
                "cds_length": len(cds),
                "aa_length": len(aa),
                "cds_translates_to_reported_aa": translation_concordant,
                "raw_fasta_cds_concordant": True,
                "tf_family": text(row.tf_family),
                "source_member_path": clone_name,
                "source_member_sha256": clone_sha,
                "raw_locator": f"row:{ordinal + 1}",
                "license_id": "CC-BY-4.0",
                "redistribution_tier": "internal_governance_bounded_audit_only",
                **GOVERNANCE_FALSE,
            }
        )

    selection_rows: list[dict[str, Any]] = []
    selection_index: dict[tuple[str, str], dict[str, bool]] = {}
    for ordinal, row in enumerate(selection.itertuples(index=False), start=1):
        ad_orf, db_orf = text(row.ad_orf_id), text(row.db_orf_id)
        key = (ad_orf, db_orf)
        if key in selection_index:
            raise RuntimeError(f"Duplicate screen-selection pair: {key}")
        flags = {
            "in_orfeome_screen": _bool_token(row.in_orfeome_screen),
            "in_focussed_screen": _bool_token(row.in_focussed_screen),
        }
        if not any(flags.values()):
            raise RuntimeError("Screen selection row has neither source screen")
        selection_index[key] = flags
        selection_rows.append(
            {
                "selection_record_id": stable_id("tfiso-screen-selection", ad_orf, db_orf),
                "source_row_ordinal": ordinal,
                "ad_orf_id": ad_orf,
                "db_orf_id": db_orf,
                "ordered_orf_pair_id": stable_id("ordered-orf-pair", ad_orf, db_orf),
                **flags,
                "source_member_path": selection_name,
                "source_member_sha256": selection_sha,
                "raw_locator": f"row:{ordinal + 1}",
                **GOVERNANCE_FALSE,
            }
        )

    public_keys: dict[tuple[str, str, str, str, str], int] = {}
    for ordinal, row in enumerate(public_y2h.itertuples(index=False), start=1):
        key = public_row_key(row)
        if key in public_keys:
            raise RuntimeError(f"Duplicate public Y2H row: {key}")
        public_keys[key] = ordinal
    raw_keys: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    raw_y2h_rows: list[dict[str, Any]] = []
    for ordinal, source in enumerate(raw_y2h.to_dict("records"), start=1):
        key = (
            text(source["ad_clone_name"]), text(source["ad_gene_symbol"]),
            text(source["ad_orf_id"]), text(source["db_gene_symbol"]),
            text(source["db_orf_id"]),
        )
        if key in raw_keys:
            raise RuntimeError(f"Duplicate raw Y2H row: {key}")
        raw_keys[key] = {**source, "source_row_ordinal": ordinal}
        public_ordinal = public_keys.get(key)
        raw_y2h_rows.append(
            {
                "raw_y2h_record_id": stable_id("tfiso-raw-y2h", raw_y2h_sha, ordinal),
                "source_row_ordinal": ordinal,
                "large_plate_name": text(source["large_plate_name"]),
                "retest_plate": text(source["retest_pla"]),
                "retest_position": text(source["retest_pos"]),
                "ad_gene_symbol": text(source["ad_gene_symbol"]),
                "ad_clone_id": text(source["ad_clone_name"]),
                "ad_orf_id": text(source["ad_orf_id"]),
                "db_gene_symbol": text(source["db_gene_symbol"]),
                "db_orf_id": text(source["db_orf_id"]),
                "source_category": text(source["category"]),
                "score_3at_raw": text(source["3AT"]),
                "score_lw_raw": text(source["LW"]),
                "empty_ad_3at_raw": text(source["empty_AD_3AT"]),
                "empty_ad_lw_raw": text(source["empty_AD_LW"]),
                "reported_result_raw": text(source["Y2H_result"]),
                "sequence_confirmation_3at_raw": text(source["seq_confirmation_3AT"]),
                "sequence_confirmation_lw_raw": text(source["seq_confirmation_LW"]),
                "in_public_pairwise_table": public_ordinal is not None,
                "public_source_row_ordinal": public_ordinal,
                "source_member_path": raw_y2h_name,
                "source_member_sha256": raw_y2h_sha,
                "raw_locator": f"row:{ordinal + 1}",
                **GOVERNANCE_FALSE,
            }
        )
    if set(public_keys) - set(raw_keys):
        raise RuntimeError("One or more public Y2H rows lack an exact raw crosswalk")

    raw_n2h_public_key: dict[tuple[str, ...], int] = {}
    raw_n2h_rows: list[dict[str, Any]] = []
    internal_accession_to_clone = {
        text(row.clone_acc): text(row.clone_id)
        for row in internal_clones.itertuples(index=False)
    }
    for ordinal, source in enumerate(raw_n2h.to_dict("records"), start=1):
        clone_id = internal_accession_to_clone.get(text(source["clone_acc"]), "")
        complete = all(
            text(source[name])
            for name in ("score_pair", "score_empty-N1", "score_empty-N2")
        )
        in_public = complete and text(source["source"]) != "vignettes"
        key = (
            text(source["test_orf_ida"]), text(source["test_orf_idb"]),
            text(source["source"]), text(source["score_pair"]),
            text(source["score_empty-N1"]), text(source["score_empty-N2"]),
            text(source["gene_symbol_tf"]), text(source["gene_symbol_partner"]),
        )
        if in_public:
            if key in raw_n2h_public_key:
                raise RuntimeError(f"Duplicate public-eligible raw N2H key: {key}")
            raw_n2h_public_key[key] = ordinal
        raw_n2h_rows.append(
            {
                "raw_n2h_record_id": stable_id("tfiso-raw-n2h", raw_n2h_sha, ordinal),
                "source_row_ordinal": ordinal,
                "test_orf_ida": text(source["test_orf_ida"]),
                "test_orf_idb": text(source["test_orf_idb"]),
                "test_plate": text(source["test_pla"]),
                "test_position_pair": text(source["test_pos_pair"]),
                "score_pair_raw": text(source["score_pair"]),
                "pair_token": text(source["pair"]),
                "source_stratum": text(source["source"]),
                "test_position_empty_n1": text(source["test_pos_empty-N1"]),
                "score_empty_n1_raw": text(source["score_empty-N1"]),
                "test_position_empty_n2": text(source["test_pos_empty-N2"]),
                "score_empty_n2_raw": text(source["score_empty-N2"]),
                "clone_accession": text(source["clone_acc"]),
                "gene_symbol_tf": text(source["gene_symbol_tf"]),
                "gene_symbol_partner": text(source["gene_symbol_partner"]),
                "in_public_n2h_table": in_public,
                "public_source_row_ordinal": None,
                "source_member_path": raw_n2h_name,
                "source_member_sha256": raw_n2h_sha,
                "raw_locator": f"row:{ordinal + 1}",
                **GOVERNANCE_FALSE,
            }
        )
    public_n2h_keys: dict[tuple[str, ...], int] = {}
    for ordinal, source in enumerate(public_n2h.to_dict("records"), start=1):
        key = (
            text(source["test_orf_ida"]), text(source["test_orf_idb"]),
            text(source["source"]), text(source["score_pair"]),
            text(source["score_empty-N1"]), text(source["score_empty-N2"]),
            text(source["gene_symbol_tf"]), text(source["gene_symbol_partner"]),
        )
        if key in public_n2h_keys or key not in raw_n2h_public_key:
            raise RuntimeError(f"Public N2H crosswalk is not unique: {key}")
        public_n2h_keys[key] = ordinal
    if set(public_n2h_keys) != set(raw_n2h_public_key):
        raise RuntimeError("Raw complete non-vignette N2H set differs from public table")
    public_ordinal_by_raw = {
        raw_n2h_public_key[key]: ordinal for key, ordinal in public_n2h_keys.items()
    }
    for row in raw_n2h_rows:
        if row["source_row_ordinal"] in public_ordinal_by_raw:
            row["public_source_row_ordinal"] = public_ordinal_by_raw[row["source_row_ordinal"]]

    return {
        "assets": assets,
        "verified_assets": verified_assets,
        "verified_licenses": verified_licenses,
        "archive_rows": archive_rows,
        "clone_frame": clones,
        "clone_rows": clone_rows,
        "clone_hash_by_id": clone_hash_by_id,
        "public_y2h": public_y2h,
        "public_n2h": public_n2h,
        "raw_y2h_frame": raw_y2h,
        "raw_y2h_rows": raw_y2h_rows,
        "raw_y2h_index": raw_keys,
        "selection_frame": selection,
        "selection_rows": selection_rows,
        "selection_index": selection_index,
        "raw_n2h_frame": raw_n2h,
        "raw_n2h_rows": raw_n2h_rows,
        "raw_n2h_public_key": raw_n2h_public_key,
        "member_metadata": {
            "public_clones": (clone_name, clone_sha),
            "public_y2h": (public_y2h_name, public_y2h_sha),
            "public_n2h": (public_n2h_name, public_n2h_sha),
            "loader": (loader_name, loader_sha),
            "raw_y2h": (raw_y2h_name, raw_y2h_sha),
            "selection": (selection_name, selection_sha),
            "internal_clones": (internal_clone_name, internal_clone_sha),
            "raw_n2h": (raw_n2h_name, raw_n2h_sha),
            "clone_fasta": (fasta_name, fasta_sha),
        },
        "observed_sizes": observed_sizes,
    }


def _build_mapping_rows(
    *,
    source: Mapping[str, Any],
    reference_maps: AuditReferenceMaps,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    public_y2h: pd.DataFrame = source["public_y2h"]
    clone_rows: list[dict[str, Any]] = source["clone_rows"]
    member = source["member_metadata"]
    ad_orfs_by_clone = {
        clone_id: sorted(set(group["ad_orf_id"].map(text)))
        for clone_id, group in public_y2h.groupby("ad_clone_id")
    }
    clone_mappings: list[dict[str, Any]] = []
    for clone in clone_rows:
        clone_mappings.append(
            reference_maps.clone_mapping(
                clone_id=str(clone["clone_id"]),
                gene_symbol=str(clone["gene_symbol"]),
                aa_sha256=str(clone["aa_sha256"]),
                aa_length=int(clone["aa_length"]),
                ad_orf_ids=ad_orfs_by_clone.get(str(clone["clone_id"]), ()),
                source_paths=[
                    str(member["public_clones"][0]),
                    str(member["raw_y2h"][0]),
                ],
                source_hashes=[
                    str(member["public_clones"][1]),
                    str(member["raw_y2h"][1]),
                ],
            )
        )
    clone_map = {str(row["clone_id"]): row for row in clone_mappings}
    source_clone_ids_by_orf: dict[str, set[str]] = defaultdict(set)
    for clone_id, orf_ids in ad_orfs_by_clone.items():
        for orf_id in orf_ids:
            source_clone_ids_by_orf[orf_id].add(clone_id)

    partner_mappings: list[dict[str, Any]] = []
    for (db_orf_id, db_gene_symbol), group in public_y2h.groupby(
        ["db_orf_id", "db_gene_symbol"], sort=True
    ):
        source_clone_hashes = {
            clone_id: str(clone_map[clone_id]["construct_aa_sha256"])
            for clone_id in sorted(source_clone_ids_by_orf.get(str(db_orf_id), ()))
            if clone_id in clone_map
        }
        source_categories = set()
        for record in group.to_dict("records"):
            key = (
                text(record["ad_clone_id"]), text(record["ad_gene_symbol"]),
                text(record["ad_orf_id"]), text(record["db_gene_symbol"]),
                text(record["db_orf_id"]),
            )
            source_categories.add(text(source["raw_y2h_index"][key]["category"]))
        partner_mappings.append(
            reference_maps.partner_mapping(
                db_orf_id=text(db_orf_id),
                db_gene_symbol=text(db_gene_symbol),
                source_categories=source_categories,
                source_clone_hashes=source_clone_hashes,
                source_paths=[
                    str(member["public_y2h"][0]),
                    "data/canonical/primary_reconciliation_v1/participant_sequence_mappings",
                ],
                source_hashes=[str(member["public_y2h"][1])],
            )
        )
    if len({row["db_orf_id"] for row in partner_mappings}) != len(partner_mappings):
        raise RuntimeError("A DB ORF identifier maps to multiple gene symbols")
    return clone_mappings, partner_mappings


def _semantic_frame(source: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    raw_index = source["raw_y2h_index"]
    selection_index = source["selection_index"]
    public_y2h: pd.DataFrame = source["public_y2h"]
    ad_gene_by_orf: dict[str, set[str]] = defaultdict(set)
    for raw in raw_index.values():
        ad_gene_by_orf[text(raw["ad_orf_id"])].add(text(raw["ad_gene_symbol"]))
    selected_gene_partners: set[tuple[str, str]] = set()
    for ad_orf, db_orf in selection_index:
        for gene in ad_gene_by_orf.get(ad_orf, ()):
            selected_gene_partners.add((gene, db_orf))

    for ordinal, public in enumerate(public_y2h.to_dict("records"), start=1):
        key = (
            text(public["ad_clone_id"]), text(public["ad_gene_symbol"]),
            text(public["ad_orf_id"]), text(public["db_gene_symbol"]),
            text(public["db_orf_id"]),
        )
        raw = raw_index[key]
        if text(public["Y2H_result"]) != text(raw["Y2H_result"]):
            raise RuntimeError(f"Public/raw Y2H outcome disagreement: {key}")
        semantic_input = {**raw, "Y2H_result": public["Y2H_result"]}
        semantics = classify_y2h_outcome(semantic_input)
        selection = selection_index.get((key[2], key[4]))
        rows.append(
            {
                "source_row_ordinal": ordinal,
                "ad_clone_id": key[0],
                "ad_gene_symbol": key[1],
                "ad_orf_id": key[2],
                "db_gene_symbol": key[3],
                "db_orf_id": key[4],
                "db_gene_category": text(public["db_gene_category"]),
                "db_gene_cofactor_type": text(public["db_gene_cofactor_type"]),
                "source_category": text(raw["category"]),
                "public_reported_result": text(public["Y2H_result"]),
                "outcome_class": semantics.outcome_class,
                "evaluability_state": semantics.evaluability_state,
                "observation_state": semantics.observation_state,
                "technical_state": semantics.technical_state,
                "state_basis": semantics.state_basis,
                "score_3at_raw": text(raw["3AT"]),
                "score_lw_raw": text(raw["LW"]),
                "empty_ad_3at_raw": text(raw["empty_AD_3AT"]),
                "empty_ad_lw_raw": text(raw["empty_AD_LW"]),
                "sequence_confirmation_3at_raw": text(raw["seq_confirmation_3AT"]),
                "sequence_confirmation_lw_raw": text(raw["seq_confirmation_LW"]),
                "public_raw_crosswalk_concordant": True,
                "in_orfeome_screen": selection["in_orfeome_screen"] if selection else None,
                "in_focussed_screen": selection["in_focussed_screen"] if selection else None,
                "exact_screen_pair_selected": selection is not None,
                "gene_partner_screen_selected": (key[1], key[4]) in selected_gene_partners,
                "raw_source_row_ordinal": int(raw["source_row_ordinal"]),
            }
        )
    frame = pd.DataFrame(rows)
    membership, steps = reconstruct_analytical_filter(frame)
    frame["in_post_selection_attempt_universe"] = membership
    frame["in_reported_3509_evaluable_analysis"] = membership & frame[
        "evaluability_state"
    ].eq("evaluable")
    frame["analysis_exclusion_reason"] = "excluded_by_archived_analytical_filter"
    frame.loc[membership & frame["evaluability_state"].ne("evaluable"), "analysis_exclusion_reason"] = (
        "post_selection_technical_unevaluable"
    )
    frame.loc[frame["in_reported_3509_evaluable_analysis"], "analysis_exclusion_reason"] = (
        "included_in_reported_3509_evaluable_analysis"
    )
    frame.attrs["filter_steps"] = steps
    return frame


def _build_pair_rows(
    *,
    source: Mapping[str, Any],
    clone_mappings: list[dict[str, Any]],
    partner_mappings: list[dict[str, Any]],
    positive_index: Mapping[tuple[str, str], Mapping[str, Any]],
    positive_source_index: Mapping[tuple[str, str], Mapping[str, int]],
    sequence_family_maps: Mapping[str, Mapping[str, Iterable[str]]],
    contamination_index: Any,
    frozen_release: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    frame = _semantic_frame(source)
    clone_map = {str(row["clone_id"]): row for row in clone_mappings}
    partner_map = {str(row["db_orf_id"]): row for row in partner_mappings}
    member = source["member_metadata"]
    empty_positive = {
        "positive_evidence_count": 0,
        "qualifying_direct_evidence_count": 0,
        "permitted_pair_view_count": 0,
    }
    empty_source = {"huri_record_positive_count": 0}
    rows: list[dict[str, Any]] = []
    for semantic in frame.to_dict("records"):
        clone = clone_map[str(semantic["ad_clone_id"])]
        partner = partner_map[str(semantic["db_orf_id"])]
        ad_hash = (
            str(clone["construct_aa_sha256"])
            if clone["construct_exact_frozen_match"]
            else None
        )
        db_hash = (
            str(partner["mapped_sequence_sha256"])
            if partner["reference_sequence_usable"]
            else None
        )
        pair: tuple[str, str] | None = None
        if ad_hash and db_hash:
            pair = unordered_pair(ad_hash, db_hash)
        positive = positive_index.get(pair, empty_positive)
        positive_source = positive_source_index.get(pair, empty_source)
        flags = contamination_flags(
            sequence_a=pair[0] if pair else None,
            sequence_b=pair[1] if pair else None,
            sequence_family_maps=sequence_family_maps,
            index=contamination_index,
        )
        direct_count = int(positive["qualifying_direct_evidence_count"])
        pair_view_count = int(positive["permitted_pair_view_count"])
        pair_record_id = stable_id(
            "tfiso-public-y2h",
            member["public_y2h"][1],
            semantic["source_row_ordinal"],
        )
        group_id = stable_id(
            "tfiso-matched-group",
            semantic["ad_gene_symbol"],
            semantic["db_orf_id"],
        )
        rows.append(
            {
                "pair_record_id": pair_record_id,
                "source_row_ordinal": int(semantic["source_row_ordinal"]),
                "ad_clone_id": semantic["ad_clone_id"],
                "ad_gene_symbol": semantic["ad_gene_symbol"],
                "ad_orf_id": semantic["ad_orf_id"],
                "db_gene_symbol": semantic["db_gene_symbol"],
                "db_orf_id": semantic["db_orf_id"],
                "db_gene_category": semantic["db_gene_category"],
                "db_gene_cofactor_type": semantic["db_gene_cofactor_type"],
                "source_category": semantic["source_category"],
                "ad_orientation_role": "prey_activation_domain_tf_isoform",
                "db_orientation_role": "bait_dna_binding_domain_partner",
                "public_reported_result": semantic["public_reported_result"],
                "outcome_class": semantic["outcome_class"],
                "evaluability_state": semantic["evaluability_state"],
                "observation_state": semantic["observation_state"],
                "technical_state": semantic["technical_state"],
                "state_basis": semantic["state_basis"],
                "score_3at_raw": semantic["score_3at_raw"],
                "score_lw_raw": semantic["score_lw_raw"],
                "empty_ad_3at_raw": semantic["empty_ad_3at_raw"],
                "empty_ad_lw_raw": semantic["empty_ad_lw_raw"],
                "sequence_confirmation_3at_raw": semantic["sequence_confirmation_3at_raw"],
                "sequence_confirmation_lw_raw": semantic["sequence_confirmation_lw_raw"],
                "public_raw_crosswalk_concordant": True,
                "in_orfeome_screen": semantic["in_orfeome_screen"],
                "in_focussed_screen": semantic["in_focussed_screen"],
                "exact_screen_pair_selected": bool(semantic["exact_screen_pair_selected"]),
                "gene_partner_screen_selected": bool(semantic["gene_partner_screen_selected"]),
                "in_post_selection_attempt_universe": bool(semantic["in_post_selection_attempt_universe"]),
                "in_reported_3509_evaluable_analysis": bool(semantic["in_reported_3509_evaluable_analysis"]),
                "analysis_exclusion_reason": semantic["analysis_exclusion_reason"],
                "ad_construct_sequence_sha256": clone["construct_aa_sha256"],
                "ad_mapping_state": clone["construct_mapping_state"],
                "ad_mapped_sequence_sha256": ad_hash,
                "db_mapping_state": partner["mapping_state"],
                "db_mapped_sequence_sha256": db_hash,
                "pair_mapping_state": "both_frozen_sequence_usable" if pair else "incomplete_frozen_sequence_mapping",
                "mapped_unordered_sequence_pair_id": unordered_sequence_pair_id(*pair) if pair else None,
                "reference_pair_usable": pair is not None,
                "ad_uniref90_ids": list(clone["uniref90_ids"]),
                "db_uniref90_ids": list(partner["uniref90_ids"]),
                "huri_positive_record_count": int(positive_source["huri_record_positive_count"]),
                "permitted_positive_record_count": direct_count,
                "permitted_pair_view_count": pair_view_count,
                "current_permitted_positive_overlap": direct_count > 0 or pair_view_count > 0,
                "exact_future_training_pair_overlap": bool(flags["exact_future_training_pair_overlap"]),
                "uniref90_pair_overlap": bool(flags["uniref90_pair_overlap"]),
                "exact_endpoint_overlap": bool(flags["exact_endpoint_overlap"]),
                "uniref90_endpoint_overlap": bool(flags["uniref90_endpoint_overlap"]),
                "matched_group_id": group_id,
                "assay_metadata_json": canonical_json(ASSAY_METADATA),
                "source_member_path": member["public_y2h"][0],
                "source_member_sha256": member["public_y2h"][1],
                "raw_member_path": member["raw_y2h"][0],
                "raw_member_sha256": member["raw_y2h"][1],
                "raw_locator": f"row:{int(semantic['raw_source_row_ordinal']) + 1}",
                "frozen_uniprot_release": frozen_release,
                **GOVERNANCE_FALSE,
            }
        )
    loader_path, loader_sha = member["loader"]
    filter_steps = [
        {
            **step,
            "filter_step": int(step["filter_step"]),
            "archived_code_member_path": loader_path,
            "archived_code_member_sha256": loader_sha,
            **GOVERNANCE_FALSE,
        }
        for step in frame.attrs["filter_steps"]
    ]
    return rows, filter_steps


def _build_group_rows(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pair_rows:
        groups[str(row["matched_group_id"])].append(row)
    output: list[dict[str, Any]] = []
    for group_id in sorted(groups):
        rows = groups[group_id]
        clones = {str(row["ad_clone_id"]) for row in rows}
        if len(clones) < 2:
            continue
        evaluable = [row for row in rows if row["evaluability_state"] == "evaluable"]
        positive_count = sum(row["observation_state"] == "positive" for row in evaluable)
        negative_count = sum(row["observation_state"] == "negative" for row in evaluable)
        has_two = len(evaluable) >= 2 and len({row["ad_clone_id"] for row in evaluable}) >= 2
        contrast = has_two and positive_count > 0 and negative_count > 0
        mapped = has_two and all(row["reference_pair_usable"] for row in evaluable)
        exact_pair_protected = mapped and not any(
            row["exact_future_training_pair_overlap"] for row in evaluable
        )
        family_pair_protected = exact_pair_protected and not any(
            row["uniref90_pair_overlap"] for row in evaluable
        )
        exact_endpoint_protected = mapped and not any(
            row["exact_endpoint_overlap"] for row in evaluable
        )
        family_endpoint_protected = exact_endpoint_protected and not any(
            row["uniref90_endpoint_overlap"] for row in evaluable
        )
        if not contrast:
            state = "not_positive_negative_contrast"
        elif not mapped:
            state = "contrast_mapping_incomplete"
        elif not exact_pair_protected:
            state = "contrast_exact_pair_exposed"
        elif not family_pair_protected:
            state = "contrast_uniref90_pair_exposed"
        elif not family_endpoint_protected:
            state = "pair_protected_but_endpoint_family_exposed"
        else:
            state = "strict_uniref90_endpoint_protected_contrast"
        first = rows[0]
        output.append(
            {
                "matched_group_id": group_id,
                "ad_gene_symbol": first["ad_gene_symbol"],
                "db_gene_symbol": first["db_gene_symbol"],
                "db_orf_id": first["db_orf_id"],
                "public_row_count": len(rows),
                "distinct_clone_count": len(clones),
                "evaluable_row_count": len(evaluable),
                "positive_count": positive_count,
                "explicit_negative_count": negative_count,
                "technical_count": len(rows) - len(evaluable),
                "has_two_evaluable_isoforms": has_two,
                "has_positive_negative_contrast": contrast,
                "in_post_selection_attempt_universe": any(row["in_post_selection_attempt_universe"] for row in rows),
                "in_reported_analysis": any(row["in_reported_3509_evaluable_analysis"] for row in rows),
                "all_evaluable_pairs_reference_usable": mapped,
                "exact_pair_protected": exact_pair_protected,
                "uniref90_pair_protected": family_pair_protected,
                "exact_endpoint_protected": exact_endpoint_protected,
                "uniref90_endpoint_protected": family_endpoint_protected,
                "protection_state": state,
                **GOVERNANCE_FALSE,
            }
        )
    return output


def _build_n2h_rows(
    *, source: Mapping[str, Any], pair_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    pair_by_orfs = {
        (str(row["ad_orf_id"]), str(row["db_orf_id"])): row for row in pair_rows
    }
    public_n2h: pd.DataFrame = source["public_n2h"]
    raw_public = source["raw_n2h_public_key"]
    member = source["member_metadata"]
    rows: list[dict[str, Any]] = []
    for ordinal, record in enumerate(public_n2h.to_dict("records"), start=1):
        key = (
            text(record["test_orf_ida"]), text(record["test_orf_idb"]),
            text(record["source"]), text(record["score_pair"]),
            text(record["score_empty-N1"]), text(record["score_empty-N2"]),
            text(record["gene_symbol_tf"]), text(record["gene_symbol_partner"]),
        )
        raw_ordinal = raw_public[key]
        y2h = pair_by_orfs.get((key[1], key[0]))
        if y2h:
            crosswalk_state = "ordered_orf_pair_found_in_public_y2h"
            y2h_state = str(y2h["observation_state"])
            y2h_id = str(y2h["pair_record_id"])
        else:
            crosswalk_state = "ordered_orf_pair_not_in_public_y2h"
            y2h_state = "not_available"
            y2h_id = None
        score_pair = float(record["score_pair"])
        empty_n1 = float(record["score_empty-N1"])
        empty_n2 = float(record["score_empty-N2"])
        calculated = math.log2(score_pair / max(empty_n1, empty_n2))
        reported = float(record["log2 NLR"])
        if not math.isclose(calculated, reported, rel_tol=1e-12, abs_tol=1e-12):
            raise RuntimeError(f"N2H log2 NLR calculation differs at row {ordinal}")
        rows.append(
            {
                "n2h_record_id": stable_id("tfiso-public-n2h", member["public_n2h"][1], ordinal),
                "source_row_ordinal": ordinal,
                "clone_id": text(record["clone_id"]),
                "gene_symbol_tf": text(record["gene_symbol_tf"]),
                "gene_symbol_partner": text(record["gene_symbol_partner"]),
                "test_orf_ida": key[0],
                "test_orf_idb": key[1],
                "n2h_orientation_a": "partner_fused_to_NanoLuc_fragment_N1_or_N2_as_source_reported",
                "n2h_orientation_b": "TF_isoform_fused_to_complementary_NanoLuc_fragment",
                "source_stratum": key[2],
                "score_pair": score_pair,
                "score_empty_n1": empty_n1,
                "score_empty_n2": empty_n2,
                "log2_nlr": reported,
                "raw_public_crosswalk_concordant": True,
                "y2h_pair_record_id": y2h_id,
                "y2h_pair_crosswalk_state": crosswalk_state,
                "y2h_observation_state": y2h_state,
                "n2h_binary_label_assigned": False,
                "source_member_path": member["public_n2h"][0],
                "source_member_sha256": member["public_n2h"][1],
                "raw_member_path": member["raw_n2h"][0],
                "raw_member_sha256": member["raw_n2h"][1],
                "raw_locator": f"row:{raw_ordinal + 1}",
                **GOVERNANCE_FALSE,
            }
        )
    return rows


def _numeric_summary(values: list[float]) -> dict[str, Any]:
    series = pd.Series(values, dtype=float)
    return {
        "count": int(series.size),
        "mean": float(series.mean()) if not series.empty else None,
        "standard_deviation": float(series.std(ddof=1)) if series.size > 1 else None,
        "minimum": float(series.min()) if not series.empty else None,
        "q1": percentile(values, 0.25),
        "median": percentile(values, 0.5),
        "q3": percentile(values, 0.75),
        "maximum": float(series.max()) if not series.empty else None,
    }


def _aggregate_findings(
    *,
    source: Mapping[str, Any],
    clone_mappings: list[dict[str, Any]],
    partner_mappings: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    n2h_rows: list[dict[str, Any]],
    group_rows: list[dict[str, Any]],
    filter_steps: list[dict[str, Any]],
    positive_metrics: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    expected = config["expected"]
    outcomes = Counter(str(row["outcome_class"]) for row in pair_rows)
    for outcome, expected_count in expected["public_y2h_outcomes"].items():
        if int(outcomes[outcome]) != int(expected_count):
            raise RuntimeError(
                f"Public Y2H outcome count differs for {outcome}: {outcomes[outcome]}"
            )
    blank_count = sum(not row["public_reported_result"] for row in pair_rows)
    if blank_count != int(expected["public_blank_rows"]):
        raise RuntimeError("Public blank Y2H count differs")
    attempted = [row for row in pair_rows if row["in_post_selection_attempt_universe"]]
    analysis = [row for row in pair_rows if row["in_reported_3509_evaluable_analysis"]]
    analysis_positive = sum(row["observation_state"] == "positive" for row in analysis)
    analysis_negative = sum(row["observation_state"] == "negative" for row in analysis)
    analysis_technical = sum(row["evaluability_state"] != "evaluable" for row in attempted)
    analytic_checks = {
        "analytical_attempt_rows": len(attempted),
        "analytical_evaluable_rows": len(analysis),
        "analytical_positive_rows": analysis_positive,
        "analytical_negative_rows": analysis_negative,
        "analytical_technical_rows": analysis_technical,
    }
    for key, value in analytic_checks.items():
        if value != int(expected[key]):
            raise RuntimeError(f"Analytical reconstruction differs for {key}: {value}")
    gene_partner_count = len(
        {
            (row["ad_gene_symbol"], row["db_gene_symbol"])
            for row in analysis
            if row["observation_state"] == "positive"
        }
    )
    if gene_partner_count != int(expected["analytical_positive_gene_partner_groups"]):
        raise RuntimeError("Analytical positive gene-partner count differs")

    exact_selected = sum(row["exact_screen_pair_selected"] for row in pair_rows)
    gene_partner_selected = sum(row["gene_partner_screen_selected"] for row in pair_rows)
    selection_counts = Counter(
        (
            bool(row["in_orfeome_screen"]),
            bool(row["in_focussed_screen"]),
        )
        for row in source["selection_rows"]
    )

    mapped_pairs = [row for row in pair_rows if row["reference_pair_usable"]]
    evaluable_pairs = [row for row in pair_rows if row["evaluability_state"] == "evaluable"]
    analysis_mapped = [row for row in analysis if row["reference_pair_usable"]]

    def overlap_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "rows": len(rows),
            "reference_pair_usable": sum(row["reference_pair_usable"] for row in rows),
            "huri_positive_overlap": sum(row["huri_positive_record_count"] > 0 for row in rows),
            "permitted_positive_overlap": sum(row["current_permitted_positive_overlap"] for row in rows),
            "exact_future_training_pair_overlap": sum(row["exact_future_training_pair_overlap"] for row in rows),
            "uniref90_pair_overlap": sum(row["uniref90_pair_overlap"] for row in rows),
            "exact_endpoint_overlap": sum(row["exact_endpoint_overlap"] for row in rows),
            "uniref90_endpoint_overlap": sum(row["uniref90_endpoint_overlap"] for row in rows),
        }

    contrast = [row for row in group_rows if row["has_positive_negative_contrast"]]
    analysis_contrast = [
        row for row in contrast if row["in_reported_analysis"]
    ]
    group_metrics = {
        "matched_groups_with_two_or_more_public_isoforms": len(group_rows),
        "groups_with_two_or_more_evaluable_isoforms": sum(
            row["has_two_evaluable_isoforms"] for row in group_rows
        ),
        "positive_negative_evaluable_contrast_groups": len(contrast),
        "reported_analysis_positive_negative_contrast_groups": len(analysis_contrast),
        "reported_analysis_contrast_groups_all_pairs_reference_usable": sum(
            row["all_evaluable_pairs_reference_usable"] for row in analysis_contrast
        ),
        "reported_analysis_contrast_groups_exact_pair_protected": sum(
            row["exact_pair_protected"] for row in analysis_contrast
        ),
        "reported_analysis_contrast_groups_uniref90_pair_protected": sum(
            row["uniref90_pair_protected"] for row in analysis_contrast
        ),
        "reported_analysis_contrast_groups_exact_endpoint_protected": sum(
            row["exact_endpoint_protected"] for row in analysis_contrast
        ),
        "reported_analysis_contrast_groups_uniref90_endpoint_protected": sum(
            row["uniref90_endpoint_protected"] for row in analysis_contrast
        ),
        "contrast_groups_all_pairs_reference_usable": sum(
            row["all_evaluable_pairs_reference_usable"] for row in contrast
        ),
        "contrast_groups_exact_pair_protected": sum(
            row["exact_pair_protected"] for row in contrast
        ),
        "contrast_groups_uniref90_pair_protected": sum(
            row["uniref90_pair_protected"] for row in contrast
        ),
        "contrast_groups_exact_endpoint_protected": sum(
            row["exact_endpoint_protected"] for row in contrast
        ),
        "contrast_groups_uniref90_endpoint_protected": sum(
            row["uniref90_endpoint_protected"] for row in contrast
        ),
        "protection_states": dict(sorted(Counter(row["protection_state"] for row in contrast).items())),
    }

    n2h_sources = Counter(str(row["source_stratum"]) for row in n2h_rows)
    if n2h_sources["isoform positives"] != int(expected["isoform_positive_n2h_rows"]):
        raise RuntimeError("N2H isoform-positive stratum count differs")
    if n2h_sources["isoform negatives"] != int(expected["isoform_negative_n2h_rows"]):
        raise RuntimeError("N2H isoform-negative stratum count differs")
    isoform_n2h = [
        row for row in n2h_rows if row["source_stratum"] in {"isoform positives", "isoform negatives"}
    ]
    source_state_counts = Counter(
        (str(row["source_stratum"]), str(row["y2h_observation_state"]))
        for row in isoform_n2h
    )
    if source_state_counts[("isoform positives", "positive")] != 131:
        raise RuntimeError("N2H positive source stratum is not concordant with Y2H")
    if source_state_counts[("isoform negatives", "negative")] != 131:
        raise RuntimeError("N2H negative source stratum is not concordant with Y2H")
    positive_n2h = [
        float(row["log2_nlr"]) for row in isoform_n2h if row["y2h_observation_state"] == "positive"
    ]
    negative_n2h = [
        float(row["log2_nlr"]) for row in isoform_n2h if row["y2h_observation_state"] == "negative"
    ]
    rank_frame = pd.DataFrame(
        {
            "y2h_positive": [
                1 if row["y2h_observation_state"] == "positive" else 0
                for row in isoform_n2h
            ],
            "log2_nlr": [float(row["log2_nlr"]) for row in isoform_n2h],
        }
    )
    spearman = float(
        rank_frame["y2h_positive"].rank().corr(rank_frame["log2_nlr"].rank())
    )

    blank_technical = {
        key: int(outcomes[key])
        for key in (
            "sequence_confirmation_failure",
            "mating_or_spotting_failure",
            "assay_measurement_failure",
            "autoactivation",
            "unknown_unresolved",
        )
    }
    blank_technical["expression_failure"] = 0
    blank_technical["expression_failure_identifiability"] = (
        "not_identifiable_no_expression_measurement_reported"
    )

    return {
        "source_universes": {
            **source["observed_sizes"],
            "public_y2h_exact_raw_crosswalk_rows": len(pair_rows),
            "public_n2h_exact_raw_crosswalk_rows": len(n2h_rows),
            "raw_y2h_rows_excluded_from_public_table": len(source["raw_y2h_rows"]) - len(pair_rows),
            "raw_n2h_complete_non_vignette_rule_reconstructs_public": True,
            "clone_cds_translation_concordant": sum(
                row["cds_translates_to_reported_aa"] for row in source["clone_rows"]
            ),
            "clone_cds_translation_discordant_or_non_codon_length": sum(
                not row["cds_translates_to_reported_aa"] for row in source["clone_rows"]
            ),
        },
        "y2h_semantics": {
            "outcome_counts": {
                key: int(outcomes[key])
                for key in sorted(expected["public_y2h_outcomes"])
            },
            "blank_rows": blank_count,
            "blank_rows_resolved_from_archived_raw_fields": blank_count - outcomes["unknown_unresolved"],
            "blank_rows_not_converted_to_negative": blank_count,
            "technical_blank_breakdown": blank_technical,
            "universal_nonbinding_claims": 0,
        },
        "selection_and_filtering": {
            "screen_selection_rows": len(source["selection_rows"]),
            "screen_flag_combinations": {
                f"orfeome_{str(key[0]).lower()}__focussed_{str(key[1]).lower()}": value
                for key, value in sorted(selection_counts.items())
            },
            "public_rows_exactly_present_in_screen_hits": exact_selected,
            "public_rows_with_gene_partner_selected_by_any_isoform_screen": gene_partner_selected,
            "filter_steps": [
                {key: value for key, value in row.items() if key not in GOVERNANCE_FALSE}
                for row in filter_steps
            ],
            **analytic_checks,
            "analytical_positive_gene_partner_groups": gene_partner_count,
            "prevalence_representative": False,
            "reason_not_prevalence_representative": [
                "candidates originate from positive first-pass screens plus HuRI and Lit-BM positives",
                "all isoforms are expanded against the union of partners found for the TF gene",
                "TF-gene/partner groups without any positive are removed",
                "retained clones are required by the archived default to have at least one positive",
                "multiple evaluable isoforms are required per retained TF-gene/partner group",
            ],
        },
        "mapping": {
            "clone_constructs": len(clone_mappings),
            "clone_constructs_exactly_matching_frozen_sequence": sum(
                row["construct_exact_frozen_match"] for row in clone_mappings
            ),
            "clone_constructs_absent_from_frozen_sequence": sum(
                not row["construct_exact_frozen_match"] for row in clone_mappings
            ),
            "partner_construct_identifiers": len(partner_mappings),
            "partner_source_sequences_available": sum(
                row["source_construct_sequence_available"] for row in partner_mappings
            ),
            "partner_reference_sequence_usable": sum(
                row["reference_sequence_usable"] for row in partner_mappings
            ),
            "partner_mapping_states": dict(
                sorted(Counter(row["mapping_state"] for row in partner_mappings).items())
            ),
            "public_pairs_reference_usable": len(mapped_pairs),
            "evaluable_pairs_reference_usable": sum(row["reference_pair_usable"] for row in evaluable_pairs),
            "reported_analysis_pairs_reference_usable": len(analysis_mapped),
            "db_exact_construct_sequence_limit": (
                "most DB plasmid sequences are not in the study archive; unique hORFeome mapping is an indirect frozen-reference mapping, not an exact construct claim"
            ),
        },
        "contamination": {
            "evidence_index": dict(positive_metrics),
            "all_public_rows": overlap_counts(pair_rows),
            "all_evaluable_rows": overlap_counts(evaluable_pairs),
            "reported_3509_analysis_rows": overlap_counts(analysis),
            "matched_isoform_contrasts": group_metrics,
            "future_training_exposure_definition": (
                "current validated permitted positive-evidence snapshot only; no model or training dataset was built"
            ),
        },
        "n2h": {
            "public_continuous_observations": len(n2h_rows),
            "source_strata": dict(sorted(n2h_sources.items())),
            "y2h_ordered_pair_crosswalk_rows": sum(row["y2h_pair_record_id"] is not None for row in n2h_rows),
            "isoform_validation_strata_rows": len(isoform_n2h),
            "source_stratum_y2h_state_counts": {
                f"{key[0]}__{key[1]}": value for key, value in sorted(source_state_counts.items())
            },
            "continuous_log2_nlr_by_y2h_observation": {
                "positive": _numeric_summary(positive_n2h),
                "negative": _numeric_summary(negative_n2h),
            },
            "spearman_y2h_positive_indicator_vs_continuous_log2_nlr": spearman,
            "n2h_binary_labels_assigned": 0,
            "threshold_applied": False,
            "interpretation": (
                "continuous cross-assay observations overlap substantially; N2H was not thresholded and does not relabel Y2H"
            ),
        },
        "licensing": {
            "code_and_input_archives": "CC-BY-4.0 with attribution",
            "machine_verified_zenodo_license_ids": source["verified_licenses"],
            "paper_pdf": "Elsevier copyright; internal methods audit only; no redistribution",
            "generated_artifact_tier": config["licensing"]["generated_artifact_tier"],
            "license_indeterminate": False,
            "public_release_action": (
                "retain source attribution and exclude the article PDF; project-wide release still requires governance review"
            ),
        },
        "identifiability": {
            "identifiable": [
                "conditional Y2H outcome frequencies within the selected and technically evaluable panel",
                "within-panel matched isoform contrasts for a fixed DB partner and fixed AD-to-DB orientation",
                "continuous N2H score distributions for the published selected validation strata",
                "overlap with the frozen permitted evidence snapshot where both construct references map uniquely",
            ],
            "not_identifiable": [
                "population PPI prevalence or a calibrated probability over arbitrary human protein pairs",
                "orientation-invariant interaction probability",
                "universal nonbinding from a negative Y2H observation",
                "endogenous cell-type-specific binding or physiological interaction",
                "a binary N2H interaction call without a separately governed threshold",
                "exact DB construct-sequence effects where the DB plasmid sequence is absent",
                "family-generalizing performance where UniRef90 endpoints overlap future training evidence",
            ],
        },
        "disposition": {
            "decision": "external-only diagnostic candidate",
            "benchmark_protocol_suitable_now": False,
            "rationale": [
                "raw technical states and clone sequences are sufficiently reconstructable for assay-specific diagnostics",
                "the panel is deliberately positive-enriched and cannot estimate prevalence",
                "selection explicitly incorporates HuRI and Lit-BM positives, creating structural evidence exposure",
                "DB construct sequences are unavailable for most partners and are mapped indirectly through frozen hORFeome identifiers",
                "strict family/endpoint protection must be evaluated separately before any future benchmark protocol",
                "N2H remains continuous and weakly concordant without an authorized threshold",
            ],
            "required_governance_action_before_any_later_benchmark": (
                "new protocol and expert-group approval; current audit authorizes no split, threshold, integration, or model use"
            ),
        },
    }


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
        raise RuntimeError("Production TF-isoform audit requires a clean Git worktree")

    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = _resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    if not os.path.samefile(active_container, expected_container):
        raise RuntimeError("Active Apptainer image differs from configuration")
    container_sha = sha256_file(active_container)
    if container_sha != str(config["runtime"]["container_sha256"]):
        raise RuntimeError("Active Apptainer image SHA-256 differs from configuration")
    if platform.machine() != str(config["runtime"]["architecture"]):
        raise RuntimeError("TF-isoform audit is running on the wrong architecture")

    paths, verified_documents = _verified_inputs(project_root, config)
    source = _source_reconstruction(project_root=project_root, config=config, paths=paths)
    reference_maps = AuditReferenceMaps.load(
        sequence_root=paths["protein_sequences"],
        identifier_mapping_root=paths["identifier_mappings"],
        participant_mapping_root=paths["participant_sequence_mappings"],
        release=str(config["inputs"]["frozen_uniprot_release"]),
    )
    clone_mappings, partner_mappings = _build_mapping_rows(
        source=source, reference_maps=reference_maps
    )
    frozen_reference = FrozenReferenceIndex.load(
        sequence_root=paths["protein_sequences"],
        dat_path=paths["frozen_uniprot_dat"],
        release=str(config["inputs"]["frozen_uniprot_release"]),
        taxid=int(config["inputs"]["frozen_taxid"]),
        project_root=project_root,
    )
    _accession_maps, sequence_family_maps = load_sequence_family_maps(
        identifier_mapping_root=paths["identifier_mappings"], reference=frozen_reference
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
    finally:
        connection.close()
    contamination_index = build_contamination_index(
        positive_index=positive_index, sequence_family_maps=sequence_family_maps
    )
    pair_rows, filter_steps = _build_pair_rows(
        source=source,
        clone_mappings=clone_mappings,
        partner_mappings=partner_mappings,
        positive_index=positive_index,
        positive_source_index=positive_source_index,
        sequence_family_maps=sequence_family_maps,
        contamination_index=contamination_index,
        frozen_release=frozen_reference.release,
    )
    group_rows = _build_group_rows(pair_rows)
    n2h_rows = _build_n2h_rows(source=source, pair_rows=pair_rows)
    findings = _aggregate_findings(
        source=source,
        clone_mappings=clone_mappings,
        partner_mappings=partner_mappings,
        pair_rows=pair_rows,
        n2h_rows=n2h_rows,
        group_rows=group_rows,
        filter_steps=filter_steps,
        positive_metrics=positive_metrics,
        config=config,
    )

    contract = load_contract(paths["audit_schema"])
    metadata = {
        "audit_version": TF_ISOFORM_AUDIT_VERSION,
        "audit_git_commit": str(git["commit"]),
        "container_sif_sha256": container_sha,
        "redistribution": str(config["licensing"]["generated_artifact_tier"]),
    }
    staging_table_rows = {
        "archive_members": source["archive_rows"],
        "clone_records": source["clone_rows"],
        "screen_selection_records": source["selection_rows"],
        "raw_y2h_records": source["raw_y2h_rows"],
        "raw_n2h_records": source["raw_n2h_rows"],
    }
    canonical_table_rows = {
        "clone_sequence_mappings": clone_mappings,
        "partner_construct_mappings": partner_mappings,
        "y2h_pair_audit": pair_rows,
        "n2h_observation_audit": n2h_rows,
        "matched_contrast_groups": group_rows,
        "analytical_filter_steps": filter_steps,
    }
    with AtomicDatasetDirectory(staging_target) as temporary:
        staging_summaries = {
            name: _write_table(
                root=temporary,
                table_name=name,
                rows=staging_table_rows[name],
                contract=contract,
                config=config,
                metadata=metadata,
            )
            for name in STAGING_TABLES
        }
        staging_summaries = _replace_prefix(
            staging_summaries, temporary.as_posix(), staging_target.as_posix()
        )
        staging_manifest = {
            "schema_version": 1,
            "audit_id": config["audit_id"],
            "audit_version": TF_ISOFORM_AUDIT_VERSION,
            "status": "complete",
            "scope": "bounded_source_semantics_no_training_labels",
            "started_at_utc": started_at,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "runtime": {
                "container_sif_sha256": container_sha,
                "architecture": platform.machine(),
                "python": platform.python_version(),
                "pyarrow": pyarrow.__version__,
            },
            "git": git,
            "verified_documents": verified_documents,
            "verified_raw_assets": source["verified_assets"],
            "tables": staging_summaries,
            "label_construction_performed": False,
            "training_data_integration_performed": False,
            "model_training_performed": False,
            "benchmark_construction_performed": False,
            "merge_with_negatome_performed": False,
            "universal_nonbinding_interpretation_performed": False,
        }
        staging_manifest_sha = _write_manifest(
            temporary / "STAGING_MANIFEST.json", staging_manifest
        )
        _make_read_only(temporary)

    with AtomicDatasetDirectory(canonical_target) as temporary:
        canonical_summaries = {
            name: _write_table(
                root=temporary,
                table_name=name,
                rows=canonical_table_rows[name],
                contract=contract,
                config=config,
                metadata=metadata,
            )
            for name in CANONICAL_TABLES
        }
        canonical_summaries = _replace_prefix(
            canonical_summaries, temporary.as_posix(), canonical_target.as_posix()
        )
        canonical_manifest = {
            "schema_version": 1,
            "audit_id": config["audit_id"],
            "audit_version": TF_ISOFORM_AUDIT_VERSION,
            "status": "complete",
            "scope": "assay_semantics_mapping_contamination_audit_only",
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "runtime": staging_manifest["runtime"],
            "git": git,
            "input_staging_manifest": staging_target.joinpath("STAGING_MANIFEST.json").relative_to(project_root).as_posix(),
            "input_staging_manifest_sha256": staging_manifest_sha,
            "tables": canonical_summaries,
            "disposition": findings["disposition"]["decision"],
            "label_construction_performed": False,
            "training_data_integration_performed": False,
            "model_training_performed": False,
            "benchmark_construction_performed": False,
            "merge_with_negatome_performed": False,
            "universal_nonbinding_interpretation_performed": False,
        }
        canonical_manifest_sha = _write_manifest(
            temporary / "AUDIT_MANIFEST.json", canonical_manifest
        )
        _make_read_only(temporary)

    report = {
        "schema_version": 1,
        "audit_id": config["audit_id"],
        "audit_version": TF_ISOFORM_AUDIT_VERSION,
        "status": "pass",
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "bounded_2025_human_tf_isoform_y2h_n2h_audit",
        "findings": findings,
        "artifacts": {
            "staging_manifest": staging_target.joinpath("STAGING_MANIFEST.json").relative_to(project_root).as_posix(),
            "staging_manifest_sha256": staging_manifest_sha,
            "canonical_manifest": canonical_target.joinpath("AUDIT_MANIFEST.json").relative_to(project_root).as_posix(),
            "canonical_manifest_sha256": canonical_manifest_sha,
        },
        "governance": {
            "training_labels_created": False,
            "training_data_integrated": False,
            "negatome_merged": False,
            "model_training_or_tuning_performed": False,
            "threshold_applied": False,
            "benchmark_constructed": False,
            "primary_pur_design_changed": False,
            "universal_nonbinding_asserted": False,
            "return_to_governance_required": True,
        },
    }
    _write_report(report_target, report, project_root)
    return report


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/tf_isoform_y2h_audit_v1.yaml")
    )
    parser.add_argument("--staging-root", type=Path)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    report = run_audit(
        project_root=project_root,
        config_path=args.config,
        staging_root=args.staging_root,
        canonical_root=args.canonical_root,
        report_path=args.report,
        allow_dirty=args.allow_dirty,
    )
    print(json.dumps({"status": report["status"], "disposition": report["findings"]["disposition"]["decision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
