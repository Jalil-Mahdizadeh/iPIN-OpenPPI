"""Execute the immutable Negatome/IntAct conditional negative-evidence audit."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import stat
from typing import Any, Iterable, Mapping

import duckdb
import pyarrow
import pyarrow.parquet as pq
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
from ipin_openppi.negative_evidence import NEGATIVE_EVIDENCE_AUDIT_VERSION
from ipin_openppi.negative_evidence.classification import (
    conflict_overlays,
    effective_tier,
    permitted_role,
    reliability_tier,
)
from ipin_openppi.negative_evidence.evidence import (
    IntactNegativeRecord,
    build_positive_pair_index,
    index_intact_negatives,
    load_intact_negative_records,
    register_evidence_views,
    unordered_accession_pair_id,
    unordered_pair,
    unordered_sequence_pair_id,
)
from ipin_openppi.negative_evidence.negatome import (
    NegatomeRow,
    parse_negatome_file,
    reconcile_parent_and_stringent_rows,
    source_row_to_record,
    stringent_links,
)
from ipin_openppi.negative_evidence.reference import (
    FrozenReferenceIndex,
    pair_mapping_state,
)
from ipin_openppi.validation.staging import _write_report


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _resolve_inside(
    project_root: Path,
    value: str | Path,
    boundary: Path,
    *,
    strict: bool,
) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve(strict=strict)
    try:
        resolved.relative_to(boundary.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(
            f"Path escapes required boundary {boundary}: {resolved}"
        ) from exc
    if strict:
        current = project_root.resolve()
        for component in resolved.relative_to(project_root.resolve()).parts:
            current = current / component
            if current.is_symlink():
                raise RuntimeError(
                    f"Symbolic-link path component is prohibited: {current}"
                )
    return resolved


def _require_hash(path: Path, expected: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"Input is not a regular non-link file: {path}")
    observed = sha256_file(path)
    if observed != expected:
        raise RuntimeError(f"SHA-256 mismatch for {path}: {observed} != {expected}")
    return {
        "path": path.as_posix(),
        "bytes": path.stat(follow_symlinks=False).st_size,
        "sha256": observed,
    }


def _validate_config(config: Mapping[str, Any]) -> None:
    if int(config.get("schema_version", -1)) != 1:
        raise RuntimeError("Unsupported negative-evidence audit configuration schema")
    if config.get("audit_version") != NEGATIVE_EVIDENCE_AUDIT_VERSION:
        raise RuntimeError("Negative-evidence configuration and code versions differ")
    authorization = config.get("authorization", {})
    for key in (
        "provenance_preserving_parsing",
        "frozen_reference_mapping",
        "positive_and_negative_reconciliation",
        "reliability_tier_assignment",
        "aggregate_feasibility_reporting",
    ):
        if authorization.get(key) is not True:
            raise RuntimeError(f"Required audit action is not authorized: {key}")
    for key in (
        "record_level_redistribution",
        "universal_negative_label",
        "candidate_pair_materialization",
        "evidence_indicator_construction",
        "label_construction",
        "split_construction",
        "model_implementation",
        "model_training",
    ):
        if authorization.get(key) is not False:
            raise RuntimeError(f"Prohibited audit action must remain false: {key}")
    if config["reliability_policy"]["universal_nonbinding_class"] != "prohibited":
        raise RuntimeError("Universal nonbinding class must remain prohibited")


def _iter_table_summaries(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if {"table", "rows", "files"}.issubset(value):
            yield value
            return
        for child in value.values():
            yield from _iter_table_summaries(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_table_summaries(child)


def _verify_dataset_directory(
    *,
    root: Path,
    manifest: Mapping[str, Any],
    skip_hashes: bool,
) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"Dataset root is not a non-link directory: {root}")
    summaries = []
    for summary in _iter_table_summaries(manifest):
        records = summary.get("files", [])
        if records and all(
            Path(str(record["path"])).resolve().parent == root for record in records
        ):
            summaries.append(summary)
    if len(summaries) != 1:
        raise RuntimeError(
            f"Expected one manifest summary for {root}, found {len(summaries)}"
        )
    summary = summaries[0]
    expected_records = {
        Path(str(record["path"])).resolve(): record for record in summary["files"]
    }
    actual = set(root.glob("*.parquet"))
    if actual != set(expected_records):
        raise RuntimeError(f"Parquet inventory differs from manifest for {root}")
    rows = 0
    bytes_total = 0
    file_hashes: list[str] = []
    for path in sorted(actual):
        info = path.stat(follow_symlinks=False)
        if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_mode & 0o222:
            raise RuntimeError(
                f"Dataset file must be regular, unlinked, and read-only: {path}"
            )
        record = expected_records[path]
        observed_rows = int(pq.ParquetFile(path).metadata.num_rows)
        if observed_rows != int(record["rows"]) or info.st_size != int(record["bytes"]):
            raise RuntimeError(
                f"Parquet size or row count differs from manifest: {path}"
            )
        if not skip_hashes:
            digest = sha256_file(path)
            if digest != str(record["sha256"]):
                raise RuntimeError(f"Parquet SHA-256 differs from manifest: {path}")
            file_hashes.append(digest)
        rows += observed_rows
        bytes_total += info.st_size
    if rows != int(summary["rows"]):
        raise RuntimeError(f"Dataset total rows differ from manifest for {root}")
    return {
        "table": str(summary["table"]),
        "rows": rows,
        "parts": len(actual),
        "bytes": bytes_total,
        "file_hashes_reverified": not skip_hashes,
        "combined_file_sha256": (
            stable_id("dataset-files", *file_hashes) if file_hashes else None
        ),
    }


def _replace_prefix(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {key: _replace_prefix(child, old, new) for key, child in value.items()}
    if isinstance(value, list):
        return [_replace_prefix(child, old, new) for child in value]
    if isinstance(value, str) and value.startswith(old):
        return new + value[len(old) :]
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_manifest(path: Path, value: Mapping[str, Any]) -> str:
    _write_json(path, value)
    digest = sha256_file(path)
    path.with_name(path.name + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="utf-8"
    )
    return digest


def _make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError(f"Generated audit dataset contains a link: {path}")
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    root.chmod(0o555)


def _verify_inputs(
    *,
    project_root: Path,
    config: Mapping[str, Any],
    skip_dataset_hashes: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Path]]:
    inputs = config["inputs"]
    documents = {
        "negative_acquisition_manifest": (
            "negative_acquisition_manifest_sha256",
            "data",
        ),
        "negative_raw_verification_report": (
            "negative_raw_verification_report_sha256",
            "artifacts/validation",
        ),
        "primary_parse_manifest": ("primary_parse_manifest_sha256", "data/staging"),
        "primary_staging_validation_report": (
            "primary_staging_validation_report_sha256",
            "artifacts/validation",
        ),
        "primary_reconciliation_manifest": (
            "primary_reconciliation_manifest_sha256",
            "data/canonical",
        ),
        "primary_reconciliation_validation_report": (
            "primary_reconciliation_validation_report_sha256",
            "artifacts/validation",
        ),
        "source_policy": ("source_policy_sha256", "configs"),
        "benchmark_estimand_policy": ("benchmark_estimand_policy_sha256", "configs"),
        "audit_schema": ("audit_schema_sha256", "schemas"),
        "source_survey": ("source_survey_sha256", "governance"),
        "frozen_uniprot_dat": ("frozen_uniprot_dat_sha256", "data/raw"),
    }
    verified_documents: dict[str, Any] = {}
    paths: dict[str, Path] = {}
    for name, (hash_key, boundary) in documents.items():
        path = _resolve_inside(
            project_root,
            str(inputs[name]),
            project_root / boundary,
            strict=True,
        )
        verified_documents[name] = _require_hash(path, str(inputs[hash_key]))
        paths[name] = path

    acquisition = _load_json(paths["negative_acquisition_manifest"])
    raw_verification = _load_json(paths["negative_raw_verification_report"])
    parse_manifest = _load_json(paths["primary_parse_manifest"])
    staging_validation = _load_json(paths["primary_staging_validation_report"])
    reconciliation_manifest = _load_json(paths["primary_reconciliation_manifest"])
    reconciliation_validation = _load_json(
        paths["primary_reconciliation_validation_report"]
    )
    survey = _load_yaml(paths["source_survey"])
    if acquisition.get("status") != "pass" or acquisition.get("errors"):
        raise RuntimeError("Negative-evidence acquisition did not pass")
    if raw_verification.get("status") != "pass" or raw_verification.get("warnings"):
        raise RuntimeError("Negative raw verification is not a warning-free pass")
    if parse_manifest.get("status") != "complete":
        raise RuntimeError("Primary parse manifest is not complete")
    if staging_validation.get("status") != "pass":
        raise RuntimeError("Primary staging validation did not pass")
    if reconciliation_manifest.get("status") != "complete":
        raise RuntimeError("Primary reconciliation manifest is not complete")
    if reconciliation_validation.get("status") != "pass":
        raise RuntimeError("Primary reconciliation validation did not pass")
    for document in (parse_manifest, reconciliation_manifest):
        if document.get("label_construction_performed") is not False:
            raise RuntimeError("Upstream document indicates label construction")
        if document.get("model_training_performed") is not False:
            raise RuntimeError("Upstream document indicates model training")
    conclusion = survey.get("survey_conclusion", {})
    if conclusion.get("universal_nonbinding_source_found") is not False:
        raise RuntimeError("Survey must not assert a universal nonbinding source")

    dataset_paths: dict[str, Path] = {}
    dataset_verification: dict[str, Any] = {}
    parse_names = {
        "protein_sequences",
        "identifier_mappings",
        "huri_evidence",
        "huri_pair_views",
        "intact_evidence",
        "intact_participants",
    }
    for name, relative in inputs["paths"].items():
        boundary = "data/staging" if name in parse_names else "data/canonical"
        root = _resolve_inside(
            project_root, str(relative), project_root / boundary, strict=True
        )
        dataset_paths[str(name)] = root
        manifest = parse_manifest if name in parse_names else reconciliation_manifest
        dataset_verification[str(name)] = _verify_dataset_directory(
            root=root,
            manifest=manifest,
            skip_hashes=skip_dataset_hashes,
        )
    return (
        verified_documents,
        dataset_verification,
        survey,
        {**paths, **dataset_paths},
    )


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


def _map_parent_records(
    reference: FrozenReferenceIndex, parent_rows: Iterable[NegatomeRow]
) -> tuple[list[dict[str, Any]], dict[str, tuple[dict[str, Any], dict[str, Any]]]]:
    output: list[dict[str, Any]] = []
    by_parent: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for row in parent_rows:
        if row.parent_record_id is None:
            raise RuntimeError("Parent record lacks canonical parent ID")
        mapped_a = reference.map_accession(
            source_accession=row.accession_a,
            parent_record_id=row.parent_record_id,
            participant_ordinal=1,
            evidence_family=row.evidence_family,
        )
        mapped_b = reference.map_accession(
            source_accession=row.accession_b,
            parent_record_id=row.parent_record_id,
            participant_ordinal=2,
            evidence_family=row.evidence_family,
        )
        output.extend((mapped_a, mapped_b))
        by_parent[row.parent_record_id] = (mapped_a, mapped_b)
    return output, by_parent


def _overlap_rows_for_parent(
    *,
    row: NegatomeRow,
    mappings: tuple[dict[str, Any], dict[str, Any]],
    by_source: Mapping[tuple[str, str], list[IntactNegativeRecord]],
    by_sequence: Mapping[tuple[str, str], list[IntactNegativeRecord]],
) -> list[dict[str, Any]]:
    source_ordered = (row.accession_a, row.accession_b)
    source_unordered = unordered_pair(*source_ordered)
    source_matches = by_source.get(source_unordered, [])
    sequence_pair: tuple[str, str] | None = None
    if all(mapping["reference_sequence_usable"] for mapping in mappings):
        sequence_pair = unordered_pair(
            str(mappings[0]["mapped_sequence_sha256"]),
            str(mappings[1]["mapped_sequence_sha256"]),
        )
    sequence_matches = by_sequence.get(sequence_pair, []) if sequence_pair else []
    matches = {
        record.evidence_id: record for record in [*source_matches, *sequence_matches]
    }
    links: list[dict[str, Any]] = []
    for evidence_id in sorted(matches):
        record = matches[evidence_id]
        exact_ordered = record.ordered_source_pair == source_ordered
        exact_unordered = record.unordered_source_pair == source_unordered
        frozen = (
            sequence_pair is not None
            and record.unordered_sequence_pair == sequence_pair
        )
        bases = []
        if exact_ordered:
            bases.append("exact_ordered_source_accession_pair")
        if exact_unordered:
            bases.append("exact_unordered_source_accession_pair")
        if frozen:
            bases.append("unordered_frozen_sequence_sha256_pair")
        links.append(
            {
                "overlap_id": stable_id(
                    "negatome-intact-negative-overlap",
                    row.parent_record_id,
                    evidence_id,
                ),
                "parent_record_id": row.parent_record_id,
                "evidence_family": row.evidence_family,
                "intact_evidence_id": evidence_id,
                "match_bases": bases,
                "exact_ordered_source_pair": exact_ordered,
                "exact_unordered_source_pair": exact_unordered,
                "frozen_sequence_pair": frozen,
                "universal_nonbinding_asserted": False,
                "label_authorized": False,
            }
        )
    return links


def _record_audit_rows(
    *,
    parent_rows: list[NegatomeRow],
    source_records: Mapping[str, dict[str, Any]],
    mappings_by_parent: Mapping[str, tuple[dict[str, Any], dict[str, Any]]],
    stringent_by_parent: Mapping[str, str],
    positive_index: Mapping[tuple[str, str], dict[str, Any]],
    negative_by_source: Mapping[tuple[str, str], list[IntactNegativeRecord]],
    negative_by_sequence: Mapping[tuple[str, str], list[IntactNegativeRecord]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    audits: list[dict[str, Any]] = []
    all_links: list[dict[str, Any]] = []
    empty_positive = {
        "positive_evidence_count": 0,
        "qualifying_direct_evidence_count": 0,
        "broader_intact_evidence_count": 0,
        "permitted_pair_view_count": 0,
        "source_keys": [],
        "source_datasets": [],
        "interaction_semantics": [],
        "detection_methods": [],
    }
    for row in parent_rows:
        assert row.parent_record_id is not None
        source = source_records[row.parent_record_id]
        mappings = mappings_by_parent[row.parent_record_id]
        pair_state = pair_mapping_state(mappings)
        usable = pair_state == "both_unique_human"
        sequence_pair = None
        if usable:
            sequence_pair = unordered_pair(
                str(mappings[0]["mapped_sequence_sha256"]),
                str(mappings[1]["mapped_sequence_sha256"]),
            )
        positive = positive_index.get(sequence_pair, empty_positive)
        direct_count = int(positive["qualifying_direct_evidence_count"]) + int(
            positive["permitted_pair_view_count"]
        )
        broader_count = int(positive["broader_intact_evidence_count"])
        overlays = conflict_overlays(
            direct_positive=direct_count > 0,
            broader_positive=broader_count > 0,
        )
        stringent = row.parent_record_id in stringent_by_parent
        tier = reliability_tier(
            evidence_family=row.evidence_family,
            stringent_member=stringent,
            reference_pair_usable=usable,
            direct_positive_conflict=direct_count > 0,
        )
        links = _overlap_rows_for_parent(
            row=row,
            mappings=mappings,
            by_source=negative_by_source,
            by_sequence=negative_by_sequence,
        )
        all_links.extend(links)
        intact_ids = sorted({str(link["intact_evidence_id"]) for link in links})
        missing = [
            "construct_a",
            "construct_b",
            "orientation_a",
            "orientation_b",
            "source_species_a",
            "source_species_b",
            "experimental_conditions",
            "assay_batch",
            "repeat",
        ]
        if row.evidence_family == "manual_experimental_negative":
            missing.extend(["technical_evaluability", "technical_state"])
        else:
            missing.append("publication")
        audits.append(
            {
                "audit_record_id": stable_id("negatome-audit", row.parent_record_id),
                "parent_record_id": row.parent_record_id,
                "evidence_family": row.evidence_family,
                "parent_dataset": row.parent_dataset,
                "parent_record_ordinal": row.ordinal,
                "source_accession_a": row.accession_a,
                "source_accession_b": row.accession_b,
                "source_isoform_id_a": mappings[0]["source_isoform_id"],
                "source_isoform_id_b": mappings[1]["source_isoform_id"],
                "publication_ids": list(row.publication_ids),
                "pdb_ids": list(row.pdb_ids),
                "assay_mi_ac": row.assay_mi_ac,
                "assay_text": row.assay_text,
                "stringent_member": stringent,
                "stringent_source_record_id": stringent_by_parent.get(
                    row.parent_record_id
                ),
                "pair_mapping_state": pair_state,
                "mapping_state_a": mappings[0]["mapping_state"],
                "mapping_state_b": mappings[1]["mapping_state"],
                "mapping_confidence_a": mappings[0]["mapping_confidence"],
                "mapping_confidence_b": mappings[1]["mapping_confidence"],
                "mapped_uniprot_accession_a": mappings[0]["mapped_uniprot_accession"],
                "mapped_uniprot_accession_b": mappings[1]["mapped_uniprot_accession"],
                "mapped_isoform_id_a": mappings[0]["mapped_isoform_id"],
                "mapped_isoform_id_b": mappings[1]["mapped_isoform_id"],
                "mapped_sequence_sha256_a": mappings[0]["mapped_sequence_sha256"],
                "mapped_sequence_sha256_b": mappings[1]["mapped_sequence_sha256"],
                "mapped_unordered_sequence_pair_id": (
                    unordered_sequence_pair_id(*sequence_pair)
                    if sequence_pair
                    else None
                ),
                "source_unordered_accession_pair_id": unordered_accession_pair_id(
                    row.accession_a, row.accession_b
                ),
                "reference_pair_usable": usable,
                "positive_check_performed": usable,
                "qualifying_direct_positive_evidence_count": int(
                    positive["qualifying_direct_evidence_count"]
                ),
                "broader_intact_positive_evidence_count": broader_count,
                "permitted_positive_pair_view_count": int(
                    positive["permitted_pair_view_count"]
                ),
                "current_positive_conflict": bool(overlays),
                "positive_conflict_overlays": overlays,
                "positive_source_keys": list(positive["source_keys"]),
                "positive_source_datasets": list(positive["source_datasets"]),
                "positive_interaction_semantics": list(
                    positive["interaction_semantics"]
                ),
                "positive_detection_methods": list(positive["detection_methods"]),
                "intact_negative_check_performed": True,
                "intact_exact_ordered_source_pair_count": sum(
                    bool(link["exact_ordered_source_pair"]) for link in links
                ),
                "intact_exact_unordered_source_pair_count": sum(
                    bool(link["exact_unordered_source_pair"]) for link in links
                ),
                "intact_frozen_sequence_pair_count": sum(
                    bool(link["frozen_sequence_pair"]) for link in links
                ),
                "intact_negative_overlap_count": len(intact_ids),
                "intact_negative_evidence_ids": intact_ids,
                "reliability_tier": tier,
                "effective_tier": effective_tier(tier, overlays),
                "permitted_role": permitted_role(tier, overlays),
                "construct_a_json": None,
                "construct_b_json": None,
                "orientation_a": None,
                "orientation_b": None,
                "source_taxid_a": None,
                "source_taxid_b": None,
                "source_species_name_a": None,
                "source_species_name_b": None,
                "experimental_conditions_json": None,
                "attempted_state": source["attempted_state"],
                "evaluability_state": source["evaluability_state"],
                "technical_state": source["technical_state"],
                "observation_state": source["observation_state"],
                "missing_provenance_fields": sorted(missing),
                "universal_nonbinding_asserted": False,
                "label_authorized": False,
            }
        )
    return audits, all_links


def _intact_audit_rows(
    records: Iterable[IntactNegativeRecord], links: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    links_by_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    family_by_parent = {
        str(link["parent_record_id"]): str(link["evidence_family"]) for link in links
    }
    for link in links:
        links_by_evidence[str(link["intact_evidence_id"])].append(link)
    output: list[dict[str, Any]] = []
    for record in records:
        participants = list(record.participants)
        pair = participants if len(participants) == 2 else [None, None]
        current_links = links_by_evidence.get(record.evidence_id, [])
        parent_ids = sorted({str(link["parent_record_id"]) for link in current_links})

        def value(index: int, field: str) -> Any:
            participant = pair[index]
            return participant.get(field) if participant else None

        output.append(
            {
                "audit_record_id": stable_id(
                    "intact-negative-audit", record.evidence_id
                ),
                "evidence_id": record.evidence_id,
                "source_record_id": str(record.evidence["source_record_id"]),
                "publication_ids": list(record.evidence["publication_ids"]),
                "participant_count": int(record.evidence["participant_count"]),
                "original_nary": bool(record.evidence["original_nary"]),
                "interaction_semantics": str(record.evidence["interaction_semantics"]),
                "detection_method_ac": record.evidence["detection_method_ac"],
                "detection_method_name": record.evidence["detection_method_name"],
                "host_taxid": record.evidence["host_taxid"],
                "host_name": record.evidence["host_name"],
                "attempted_state": str(record.evidence["attempted_state"]),
                "evaluability_state": str(record.evidence["evaluability_state"]),
                "technical_state": str(record.evidence["technical_state"]),
                "observation_state": str(record.evidence["observation_state"]),
                "orientation_semantics": str(record.evidence["orientation_semantics"]),
                "source_accession_a": value(0, "primary_identifier"),
                "source_accession_b": value(1, "primary_identifier"),
                "participant_taxid_a": value(0, "taxid"),
                "participant_taxid_b": value(1, "taxid"),
                "orientation_a": value(0, "orientation_role"),
                "orientation_b": value(1, "orientation_role"),
                "mapped_uniprot_accession_a": value(0, "mapped_uniprot_accession"),
                "mapped_uniprot_accession_b": value(1, "mapped_uniprot_accession"),
                "mapped_isoform_id_a": value(0, "mapped_isoform_id"),
                "mapped_isoform_id_b": value(1, "mapped_isoform_id"),
                "mapped_sequence_sha256_a": value(0, "mapped_sequence_sha256"),
                "mapped_sequence_sha256_b": value(1, "mapped_sequence_sha256"),
                "mapped_unordered_sequence_pair_id": (
                    unordered_sequence_pair_id(*record.unordered_sequence_pair)
                    if record.unordered_sequence_pair
                    else None
                ),
                "reference_pair_usable": record.unordered_sequence_pair is not None,
                "negatome_exact_ordered_source_pair_count": sum(
                    bool(link["exact_ordered_source_pair"]) for link in current_links
                ),
                "negatome_exact_unordered_source_pair_count": sum(
                    bool(link["exact_unordered_source_pair"]) for link in current_links
                ),
                "negatome_frozen_sequence_pair_count": sum(
                    bool(link["frozen_sequence_pair"]) for link in current_links
                ),
                "negatome_overlap_count": len(parent_ids),
                "negatome_parent_record_ids": parent_ids,
                "negatome_evidence_families": sorted(
                    {family_by_parent[parent_id] for parent_id in parent_ids}
                ),
                "universal_nonbinding_asserted": False,
                "label_authorized": False,
                "context_json": str(record.evidence["context_json"]),
                "missingness_json": str(record.evidence["missingness_json"]),
            }
        )
    return output


def _aggregate_metrics(
    *,
    source_rows: list[dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    intact_rows: list[dict[str, Any]],
    overlap_rows: list[dict[str, Any]],
    positive_metrics: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_dataset = Counter(str(row["source_dataset"]) for row in source_rows)
    mapping_states = Counter(str(row["mapping_state"]) for row in mapping_rows)
    mapping_confidences = Counter(
        str(row["mapping_confidence"]) for row in mapping_rows
    )
    pair_states = Counter(str(row["pair_mapping_state"]) for row in audit_rows)
    tiers = Counter(str(row["reliability_tier"]) for row in audit_rows)
    family_counts = Counter(str(row["evidence_family"]) for row in audit_rows)
    mapped_family = Counter(
        str(row["evidence_family"])
        for row in audit_rows
        if row["reference_pair_usable"]
    )
    conflict_counts = {
        "any_current_positive": sum(
            bool(row["current_positive_conflict"]) for row in audit_rows
        ),
        "direct_CF_D": sum(
            "CF-D" in row["positive_conflict_overlays"] for row in audit_rows
        ),
        "broader_CF_B": sum(
            "CF-B" in row["positive_conflict_overlays"] for row in audit_rows
        ),
    }
    overlap_parent_ids = {str(row["parent_record_id"]) for row in overlap_rows}
    overlap_intact_ids = {str(row["intact_evidence_id"]) for row in overlap_rows}
    overlap_basis = {
        "exact_ordered_source_links": sum(
            bool(row["exact_ordered_source_pair"]) for row in overlap_rows
        ),
        "exact_unordered_source_links": sum(
            bool(row["exact_unordered_source_pair"]) for row in overlap_rows
        ),
        "frozen_sequence_pair_links": sum(
            bool(row["frozen_sequence_pair"]) for row in overlap_rows
        ),
    }
    manual_candidate = [
        row
        for row in audit_rows
        if row["evidence_family"] == "manual_experimental_negative"
        and row["reliability_tier"] == "ME-1"
        and not row["current_positive_conflict"]
    ]
    manual_publications = {
        publication
        for row in manual_candidate
        for publication in row["publication_ids"]
    }
    manual_sequence_pairs = {
        str(row["mapped_unordered_sequence_pair_id"])
        for row in manual_candidate
        if row["mapped_unordered_sequence_pair_id"]
    }
    threshold = config["pnu_feasibility_policy"]
    numerical_manual_pass = len(manual_candidate) >= int(
        threshold["minimum_conditional_records_per_stratum"]
    ) and len(manual_publications) >= int(
        threshold["minimum_independent_publications_per_manual_stratum"]
    )
    intact_usable = [row for row in intact_rows if row["reference_pair_usable"]]
    pnu = {
        "positive_negative_unlabeled_design_evaluated": True,
        "primary_population_calibrated_PNU_statistically_feasible": False,
        "primary_population_calibrated_PNU_scientifically_identified": False,
        "bounded_manual_conditional_stratum_numerically_adequate": numerical_manual_pass,
        "bounded_manual_conditional_records": len(manual_candidate),
        "bounded_manual_conditional_unique_sequence_pairs": len(manual_sequence_pairs),
        "bounded_manual_conditional_publications": len(manual_publications),
        "intact_negative_records_total": len(intact_rows),
        "intact_negative_reference_pair_usable_records": len(intact_usable),
        "conditional_P_plus_N_plus_U_diagnostic_feasible": numerical_manual_pass,
        "conditional_P_plus_N_plus_U_training_role_authorized": False,
        "structure_noncontacts_join_manual_negative_class": False,
        "recommended_primary_design": "retain_reference_sequence_positive_unlabeled_ranking_PU_R",
        "recommended_optional_role": (
            "protected_source_assay_stratified_conditional_diagnostic_only"
            if numerical_manual_pass
            else "descriptive_only_below_minimum_size"
        ),
        "blocking_identifiability_conditions": [
            "no_complete_human_pair_level_selected_attempted_evaluable_population",
            "Negatome_manual_construct_orientation_conditions_and_technical_evaluability_missing",
            "IntAct_negatives_are_heterogeneous_curated_records_without_sampling_denominator",
            "negative_source_selection_and_assay_sensitivity_are_unknown",
            "biological_class_prior_is_not_identified",
        ],
        "universal_nonbinding_interpretation": False,
    }
    metrics = {
        "source_rows": dict(sorted(by_dataset.items())),
        "source_row_total": len(source_rows),
        "parent_record_total": len(audit_rows),
        "parent_records_by_family": dict(sorted(family_counts.items())),
        "participant_mapping_rows": len(mapping_rows),
        "participant_mapping_states": dict(sorted(mapping_states.items())),
        "participant_mapping_confidences": dict(sorted(mapping_confidences.items())),
        "parent_pair_mapping_states": dict(sorted(pair_states.items())),
        "mapped_parent_records_by_family": dict(sorted(mapped_family.items())),
        "reliability_tiers": dict(sorted(tiers.items())),
        "positive_conflicts": conflict_counts,
        "positive_index": dict(positive_metrics),
        "intact_negative_records": len(intact_rows),
        "intact_negative_reference_pair_usable_records": len(intact_usable),
        "overlap": {
            "cross_source_link_count": len(overlap_rows),
            "negatome_parent_records_with_overlap": len(overlap_parent_ids),
            "intact_negative_records_with_overlap": len(overlap_intact_ids),
            **overlap_basis,
        },
        "universal_nonbinding_rows": 0,
        "label_authorized_rows": 0,
    }
    return metrics, pnu


def run_negative_evidence_audit(
    *,
    project_root: Path,
    config_path: Path,
    staging_root: Path | None = None,
    canonical_root: Path | None = None,
    report_path: Path | None = None,
    allow_dirty: bool = False,
    skip_dataset_hashes: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    started_at = datetime.now(timezone.utc).isoformat()
    config_path = _resolve_inside(
        project_root, config_path, project_root / "configs", strict=True
    )
    config = _load_yaml(config_path)
    _validate_config(config)
    staging_target = staging_root or project_root / str(
        config["outputs"]["staging_root"]
    )
    canonical_target = canonical_root or project_root / str(
        config["outputs"]["canonical_root"]
    )
    report_target = report_path or project_root / str(config["outputs"]["audit_report"])
    staging_target = _resolve_inside(
        project_root, staging_target, project_root / "data/staging", strict=False
    )
    canonical_target = _resolve_inside(
        project_root, canonical_target, project_root / "data/canonical", strict=False
    )
    report_target = _resolve_inside(
        project_root,
        report_target,
        project_root / "artifacts/validation",
        strict=False,
    )
    smoke = all(
        any(part.startswith("_smoke_") for part in path.parts)
        for path in (staging_target, canonical_target, report_target)
    )
    if allow_dirty != smoke:
        raise RuntimeError(
            "--allow-dirty is restricted to consistently named _smoke_ outputs"
        )
    if skip_dataset_hashes and not smoke:
        raise RuntimeError("Skipping dataset hashes is restricted to _smoke_ outputs")
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError(
            "Production negative-evidence audit requires a clean Git worktree"
        )

    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = _resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    if active_container != expected_container:
        raise RuntimeError("Active Apptainer image differs from audit configuration")
    container_sha = sha256_file(active_container)
    if container_sha != str(config["runtime"]["container_sha256"]):
        raise RuntimeError(
            "Active Apptainer image SHA-256 differs from audit configuration"
        )
    if platform.machine() != str(config["runtime"]["architecture"]):
        raise RuntimeError(
            "Negative-evidence audit is running on the wrong architecture"
        )

    verified_documents, verified_datasets, survey, paths = _verify_inputs(
        project_root=project_root,
        config=config,
        skip_dataset_hashes=skip_dataset_hashes,
    )
    acquisition, assets = load_asset_index(
        project_root,
        paths["negative_acquisition_manifest"].relative_to(project_root),
    )
    raw_verified: dict[str, Any] = {}
    rows_by_dataset: dict[str, list[NegatomeRow]] = {}
    for dataset, asset_id in config["raw_assets"].items():
        asset = assets[str(asset_id)]
        raw_verified[str(dataset)] = verify_asset(asset)
        rows_by_dataset[str(dataset)] = parse_negatome_file(
            path=asset.path,
            dataset=str(dataset),
            raw_file_path=asset.relative_path,
            raw_file_sha256=asset.sha256,
        )
        expected_count = int(config["expected"]["source_rows"][dataset])
        if len(rows_by_dataset[str(dataset)]) != expected_count:
            raise RuntimeError(f"Negatome row count differs for {dataset}")
    all_source_rows, parent_rows, subset_metrics = reconcile_parent_and_stringent_rows(
        rows_by_dataset
    )
    source_records = [source_row_to_record(row) for row in all_source_rows]
    parent_source_records = {
        str(record["parent_record_id"]): record
        for record in source_records
        if not record["stringent_file"]
    }
    expected_parent = int(config["expected"]["parent_records"]["total"])
    if (
        len(parent_rows) != expected_parent
        or len(parent_source_records) != expected_parent
    ):
        raise RuntimeError("Negatome canonical parent record count differs")

    reference = FrozenReferenceIndex.load(
        sequence_root=paths["protein_sequences"],
        dat_path=paths["frozen_uniprot_dat"],
        release=str(config["inputs"]["frozen_uniprot_release"]),
        taxid=int(config["inputs"]["frozen_taxid"]),
        project_root=project_root,
    )
    mapping_rows, mappings_by_parent = _map_parent_records(reference, parent_rows)
    if len(mapping_rows) != int(config["expected"]["participant_mapping_rows"]):
        raise RuntimeError("Negatome participant mapping count differs")

    connection = duckdb.connect()
    connection.execute(f"SET memory_limit='{config['runtime']['duckdb_memory_limit']}'")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    try:
        register_evidence_views(connection, paths)
        positive_index, positive_metrics = build_positive_pair_index(
            connection,
            permitted_pair_views=config["positive_conflict_policy"][
                "permitted_pair_views"
            ],
        )
        intact_records = load_intact_negative_records(connection)
    finally:
        connection.close()
    if len(intact_records) != int(config["expected"]["intact_negative_records"]):
        raise RuntimeError("Frozen IntAct negative record count differs")
    negative_by_source, negative_by_sequence = index_intact_negatives(intact_records)
    links_by_parent = stringent_links(all_source_rows)
    audit_rows, overlap_rows = _record_audit_rows(
        parent_rows=parent_rows,
        source_records=parent_source_records,
        mappings_by_parent=mappings_by_parent,
        stringent_by_parent=links_by_parent,
        positive_index=positive_index,
        negative_by_source=negative_by_source,
        negative_by_sequence=negative_by_sequence,
    )
    intact_audit_rows = _intact_audit_rows(intact_records, overlap_rows)
    metrics, pnu = _aggregate_metrics(
        source_rows=source_records,
        mapping_rows=mapping_rows,
        audit_rows=audit_rows,
        intact_rows=intact_audit_rows,
        overlap_rows=overlap_rows,
        positive_metrics=positive_metrics,
        config=config,
    )
    contract = load_contract(paths["audit_schema"])
    metadata = {
        "audit_version": NEGATIVE_EVIDENCE_AUDIT_VERSION,
        "audit_git_commit": str(git["commit"]),
        "container_sif_sha256": container_sha,
        "redistribution": "internal_only_no_negatome_record_level_release",
    }

    with AtomicDatasetDirectory(staging_target) as temporary_staging:
        staging_summary = _write_table(
            root=temporary_staging,
            table_name="negatome_source_records",
            rows=source_records,
            contract=contract,
            config=config,
            metadata=metadata,
        )
        staging_summary = _replace_prefix(
            staging_summary, temporary_staging.as_posix(), staging_target.as_posix()
        )
        staging_manifest = {
            "schema_version": 1,
            "audit_id": config["audit_id"],
            "audit_version": NEGATIVE_EVIDENCE_AUDIT_VERSION,
            "status": "complete",
            "scope": "internal_only_provenance_preserving_source_rows",
            "runtime": {
                "container_sif_sha256": container_sha,
                "architecture": platform.machine(),
                "python": platform.python_version(),
                "pyarrow": pyarrow.__version__,
            },
            "git": git,
            "raw_assets": raw_verified,
            "subset_validation": subset_metrics,
            "tables": {"negatome_source_records": staging_summary},
            "record_level_redistribution_authorized": False,
            "universal_nonbinding_interpretation": False,
            "label_construction_performed": False,
            "model_training_performed": False,
        }
        staging_manifest_path = temporary_staging / "STAGING_MANIFEST.json"
        staging_manifest_sha = _write_manifest(staging_manifest_path, staging_manifest)
        _make_read_only(temporary_staging)

        with AtomicDatasetDirectory(canonical_target) as temporary_canonical:
            table_rows = {
                "negatome_participant_mappings": mapping_rows,
                "negatome_record_audit": audit_rows,
                "intact_negative_record_audit": intact_audit_rows,
                "negatome_intact_negative_overlaps": overlap_rows,
            }
            canonical_summaries = {
                table_name: _write_table(
                    root=temporary_canonical,
                    table_name=table_name,
                    rows=rows,
                    contract=contract,
                    config=config,
                    metadata=metadata,
                )
                for table_name, rows in table_rows.items()
            }
            canonical_summaries = _replace_prefix(
                canonical_summaries,
                temporary_canonical.as_posix(),
                canonical_target.as_posix(),
            )
            canonical_manifest = {
                "schema_version": 1,
                "audit_id": config["audit_id"],
                "audit_version": NEGATIVE_EVIDENCE_AUDIT_VERSION,
                "status": "complete",
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "conditional_negative_evidence_audit_no_labels",
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
                    ).as_posix(),
                    "staging_manifest_sha256": staging_manifest_sha,
                    "documents": verified_documents,
                    "datasets": verified_datasets,
                },
                "tables": canonical_summaries,
                "metrics": metrics,
                "pnu_feasibility": pnu,
                "policy": {
                    "mapping": config["mapping_policy"],
                    "positive_conflicts": config["positive_conflict_policy"],
                    "negative_overlap": config["negative_overlap_policy"],
                    "reliability": config["reliability_policy"],
                },
                "record_level_redistribution_authorized": False,
                "universal_nonbinding_interpretation": False,
                "label_construction_performed": False,
                "candidate_pair_materialization_performed": False,
                "split_construction_performed": False,
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
        "audit_version": NEGATIVE_EVIDENCE_AUDIT_VERSION,
        "task": config["task"],
        "status": "complete",
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "aggregate_non_extractive_negative_evidence_discovery_audit",
        "runtime": {
            "container": str(config["runtime"]["container"]),
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
            "documents": verified_documents,
            "datasets": verified_datasets,
            "raw_assets": raw_verified,
            "acquisition_run_id": acquisition["run_id"],
        },
        "outputs": {
            "staging_manifest": (staging_target / "STAGING_MANIFEST.json").as_posix(),
            "staging_manifest_sha256": staging_manifest_sha,
            "canonical_manifest": (canonical_target / "AUDIT_MANIFEST.json").as_posix(),
            "canonical_manifest_sha256": canonical_manifest_sha,
            "record_level_outputs_internal_only": True,
        },
        "license_and_redistribution": {
            "negatome_payload_license": "not_explicitly_stated",
            "internal_research_audit": "approved",
            "raw_and_record_level_redistribution": "not_authorized",
            "aggregate_non_extractive_reporting": "approved",
            "intact_data_license": "CC-BY-4.0",
            "determination_is_legal_advice": False,
        },
        "subset_validation": subset_metrics,
        "metrics": metrics,
        "pnu_feasibility": pnu,
        "additional_public_source_survey": {
            "survey_id": survey["survey_id"],
            "source_count": len(survey["sources"]),
            "conclusion": survey["survey_conclusion"],
        },
        "scientific_conclusion": {
            "manual_and_structure_noncontact_kept_separate": True,
            "all_939_intact_negative_records_enumerated": True,
            "every_usable_negatome_pair_checked_against_current_positive_index": True,
            "historical_stringency_treated_as_current_conflict_clearance": False,
            "universal_nonbinding_source_found": False,
            "universal_nonbinding_interpretation": False,
            "primary_design_should_change_from_PU_R": False,
        },
        "authorizations": {
            "negative_evidence_audit_complete": True,
            "record_level_redistribution": False,
            "negative_label_construction": False,
            "candidate_pair_materialization": False,
            "evidence_indicator_construction": False,
            "split_construction": False,
            "model_implementation": False,
            "model_training": False,
        },
        "warnings": [
            {
                "code": "NEGATOME_LICENSE_UNRESOLVED",
                "effect": "raw_and_record_level_outputs_remain_internal_only",
            },
            {
                "code": "NEGATOME_PROVENANCE_INCOMPLETE",
                "effect": "construct_orientation_species_conditions_and_evaluability_are_not_imputed",
            },
            {
                "code": "NO_COMPLETE_HUMAN_TESTED_UNIVERSE",
                "effect": "population_calibrated_PNU_is_not_identified",
            },
        ],
    }
    _write_report(report_target, report, project_root)
    return report


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit conditional negative PPI evidence"
    )
    parser.add_argument(
        "--config", type=Path, default=Path("configs/negative_evidence_audit_v1.yaml")
    )
    parser.add_argument("--staging-root", type=Path)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--skip-dataset-hashes", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())

    def absolute(path: Path | None) -> Path | None:
        if path is None or path.is_absolute():
            return path
        return project_root / path

    report = run_negative_evidence_audit(
        project_root=project_root,
        config_path=absolute(args.config) or args.config,
        staging_root=absolute(args.staging_root),
        canonical_root=absolute(args.canonical_root),
        report_path=absolute(args.report),
        allow_dirty=args.allow_dirty,
        skip_dataset_hashes=args.skip_dataset_hashes,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
