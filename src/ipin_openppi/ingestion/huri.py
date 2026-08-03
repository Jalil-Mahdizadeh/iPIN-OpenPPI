"""HuRI/CCSB pair-view, MITAB, and supplementary-table parsers."""

from __future__ import annotations

from collections import Counter
import csv
import io
import json
from pathlib import Path
import re
from typing import Any
import zipfile

from .common import (
    ParquetBatchWriter,
    canonical_json,
    stable_id,
    strip_version,
)
from .context import ParsingContext


MITAB_27_COLUMNS = [
    "id_a",
    "id_b",
    "alt_id_a",
    "alt_id_b",
    "alias_a",
    "alias_b",
    "detection_method",
    "publication_first_author",
    "publication_identifiers",
    "taxid_a",
    "taxid_b",
    "interaction_type",
    "source_database",
    "interaction_identifiers",
    "confidence",
    "complex_expansion",
    "biological_role_a",
    "biological_role_b",
    "experimental_role_a",
    "experimental_role_b",
    "molecule_type_a",
    "molecule_type_b",
    "xref_a",
    "xref_b",
    "interaction_xrefs",
    "annotation_a",
    "annotation_b",
    "interaction_annotations",
    "host_organism",
    "interaction_parameters",
    "creation_date",
    "update_date",
    "checksum_a",
    "checksum_b",
    "interaction_checksum",
    "negative",
    "features_a",
    "features_b",
    "stoichiometry_a",
    "stoichiometry_b",
    "participant_identification_method_a",
    "participant_identification_method_b",
]

_TERM_RE = re.compile(r"(?:(?:psi-mi):)?(MI:\d+)\((.*)\)$", re.IGNORECASE)
_TAXID_RE = re.compile(r"taxid:(-?\d+)(?:\((.*)\))?", re.IGNORECASE)
_TABLE_NUMBER_RE = re.compile(r"Supplementary Table (\d+)\.txt$")


def _split_pipe(value: str) -> list[str]:
    if not value or value == "-":
        return []
    return [
        token.strip() for token in value.split("|") if token.strip() and token != "-"
    ]


def _parse_term(value: str) -> tuple[str | None, str | None]:
    if not value or value == "-":
        return None, None
    if match := _TERM_RE.search(value.strip()):
        return match.group(1).upper(), match.group(2).strip()
    return None, value.strip()


def _parse_taxid(value: str) -> tuple[int | None, str | None]:
    if not value or value == "-":
        return None, None
    if match := _TAXID_RE.search(value.strip()):
        return int(match.group(1)), (match.group(2) or None)
    return None, value.strip()


def _parse_identifier(value: str) -> tuple[str | None, str | None]:
    if not value or value == "-" or ":" not in value:
        return None, None
    database, identifier = value.split(":", 1)
    identifier = re.sub(r"\([^()]*(?:\([^()]*\)[^()]*)*\)$", "", identifier).strip()
    return database.strip(), identifier


def _identifiers(value: str) -> list[tuple[str, str]]:
    parsed = [_parse_identifier(token) for token in _split_pipe(value)]
    return [(db, identifier) for db, identifier in parsed if db and identifier]


def _identifiers_for_database(value: str, database: str) -> list[str]:
    target = database.casefold()
    return [
        identifier for db, identifier in _identifiers(value) if db.casefold() == target
    ]


def _ensembl_by_kind(value: str, prefix: str) -> list[str]:
    return [
        identifier
        for database, identifier in _identifiers(value)
        if database.casefold() == "ensembl" and identifier.startswith(prefix)
    ]


def _raw_bool(value: str) -> bool | None:
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    if normalized in {"", "-", "na", "n/a", "null"}:
        return None
    raise ValueError(f"Cannot parse source boolean: {value!r}")


def _raw_float(value: str) -> float | None:
    if not value or value == "-":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _pair_token(alt_ids: str, primary_id: str) -> str:
    genes = sorted(
        {strip_version(value) for value in _ensembl_by_kind(alt_ids, "ENSG")}
    )
    if len(genes) == 1:
        return f"ensembl_gene:{genes[0]}"
    database, identifier = _parse_identifier(primary_id)
    if database and identifier:
        return f"{database.casefold()}:{identifier}"
    return primary_id


def _feature_parts(value: str) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for ordinal, raw in enumerate(_split_pipe(value), start=1):
        label, separator, remainder = raw.partition(":")
        range_token = remainder.split(" ", 1)[0] if separator else ""
        start: int | None = None
        end: int | None = None
        if "-" in range_token:
            start_text, end_text = range_token.split("-", 1)
            if start_text.isdigit():
                start = int(start_text)
            if end_text.isdigit():
                end = int(end_text)
        parsed.append(
            {
                "ordinal": ordinal,
                "raw": raw,
                "label": label.strip() or None,
                "start": start,
                "end": end,
                "range_token": range_token or None,
            }
        )
    return parsed


def _interaction_semantics(
    participant_count: int,
    detection_name: str | None,
    interaction_ac: str | None,
    expansion: str,
) -> tuple[str, list[str]]:
    flags: list[str] = []
    detection = (detection_name or "").casefold()
    if participant_count == 2 and "two hybrid" in detection and expansion in {"", "-"}:
        if interaction_ac == "MI:0915":
            flags.append("source_term_physical_association_classified_binary_y2h")
        return "direct_binary", flags
    if interaction_ac == "MI:0407":
        return "direct_binary", flags
    if interaction_ac == "MI:0915":
        return "physical_association", flags
    if interaction_ac == "MI:0914":
        return "association", flags
    return "unknown", flags


def _participant_row(
    *,
    side: str,
    row: dict[str, str],
    evidence_id: str,
    asset_path: str,
    raw_locator: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    suffix = side.casefold()
    ordinal = 1 if suffix == "a" else 2
    primary_db, primary_identifier = _parse_identifier(row[f"id_{suffix}"])
    alternate = _split_pipe(row[f"alt_id_{suffix}"])
    aliases = _split_pipe(row[f"alias_{suffix}"])
    uniprot = [
        identifier
        for db, identifier in _identifiers(row[f"id_{suffix}"])
        if db.casefold() in {"uniprotkb", "uniprot"}
    ]
    genes = _ensembl_by_kind(row[f"alt_id_{suffix}"], "ENSG")
    transcripts = _ensembl_by_kind(row[f"alt_id_{suffix}"], "ENST")
    proteins = _ensembl_by_kind(row[f"alt_id_{suffix}"], "ENSP")
    orfs = [identifier for _, identifier in _identifiers(row[f"alias_{suffix}"])]
    taxid, organism_name = _parse_taxid(row[f"taxid_{suffix}"])
    molecule_ac, molecule_name = _parse_term(row[f"molecule_type_{suffix}"])
    bio_ac, bio_name = _parse_term(row[f"biological_role_{suffix}"])
    exp_ac, exp_name = _parse_term(row[f"experimental_role_{suffix}"])
    identification_ac, identification_name = _parse_term(
        row[f"participant_identification_method_{suffix}"]
    )
    features = _feature_parts(row[f"features_{suffix}"])
    tags = [
        feature["label"]
        for feature in features
        if feature["label"] and "tag" in feature["label"].casefold()
    ]
    fusions = [
        feature["label"]
        for feature in features
        if feature["label"] and "domain" in feature["label"].casefold()
    ]
    participant_id = f"{evidence_id}:p{ordinal}"
    confidence = "C" if uniprot or transcripts or proteins else "D"
    missingness: dict[str, str] = {
        "mapped_uniprot_accession": "not_parsed",
        "mapped_sequence_sha256": "not_parsed",
        "construct_sequence_sha256": "not_reported",
        "construct_start": "not_reported",
        "construct_end": "not_reported",
        "expressed_in_taxid": "not_reported",
        "expressed_in_name": "not_reported",
    }
    participant = {
        "participant_id": participant_id,
        "evidence_id": evidence_id,
        "participant_ordinal": ordinal,
        "source_participant_id": orfs[0] if len(orfs) == 1 else None,
        "source_interactor_id": None,
        "primary_identifier_db": primary_db,
        "primary_identifier": primary_identifier,
        "alternate_identifiers": alternate,
        "aliases": aliases,
        "taxid": taxid,
        "organism_name": organism_name,
        "molecule_type_ac": molecule_ac,
        "molecule_type_name": molecule_name,
        "biological_role_ac": bio_ac,
        "biological_role_name": bio_name,
        "experimental_role_ac": exp_ac,
        "experimental_role_name": exp_name,
        "orientation_role": exp_name,
        "expressed_in_taxid": None,
        "expressed_in_name": None,
        "raw_uniprot_accessions": uniprot,
        "raw_ensembl_gene_ids": genes,
        "raw_ensembl_transcript_ids": transcripts,
        "raw_ensembl_protein_ids": proteins,
        "raw_orf_ids": orfs,
        "mapped_uniprot_accession": None,
        "mapped_isoform_id": None,
        "mapped_sequence_sha256": None,
        "mapping_state": "not_attempted",
        "mapping_basis": "source_native_parse_only",
        "construct_sequence_sha256": None,
        "construct_start": None,
        "construct_end": None,
        "construct_mutations": [],
        "construct_tags": tags,
        "construct_fusion_partners": fusions,
        "signal_propeptide_handling": None,
        "construct_confidence": confidence,
        "construct_confidence_basis": (
            "identifier_level_mapping_without_exact_construct_sequence_or_boundaries"
            if confidence == "C"
            else "source_identifier_ambiguous_or_absent"
        ),
        "participant_identification_method_ac": identification_ac,
        "participant_identification_method_name": identification_name,
        "stoichiometry": _raw_float(row[f"stoichiometry_{suffix}"]),
        "raw_file_path": asset_path,
        "raw_locator": raw_locator,
        "source_fields_json": canonical_json(
            {
                "annotation": row[f"annotation_{suffix}"],
                "checksum": row[f"checksum_{suffix}"],
                "xref": row[f"xref_{suffix}"],
            }
        ),
        "missingness_json": canonical_json(missingness),
    }
    feature_rows: list[dict[str, Any]] = []
    for feature in features:
        feature_rows.append(
            {
                "feature_id": stable_id(
                    "huri-feature", participant_id, feature["ordinal"], feature["raw"]
                ),
                "participant_id": participant_id,
                "evidence_id": evidence_id,
                "source_feature_id": None,
                "feature_short_label": feature["label"],
                "feature_type_ac": None,
                "feature_type_name": feature["label"],
                "feature_role_ac": None,
                "feature_role_name": None,
                "range_ordinal": feature["ordinal"],
                "start_position": feature["start"],
                "end_position": feature["end"],
                "start_status_ac": None,
                "start_status_name": (
                    "specified" if feature["start"] is not None else "undetermined"
                ),
                "end_status_ac": None,
                "end_status_name": (
                    "specified" if feature["end"] is not None else "undetermined"
                ),
                "original_sequence": None,
                "resulting_sequence": None,
                "linked_feature_id": None,
                "raw_file_path": asset_path,
                "raw_locator": raw_locator,
                "source_fields_json": canonical_json({"raw_feature": feature["raw"]}),
                "missingness_json": canonical_json(
                    {
                        "feature_type_ac": "not_reported",
                        "original_sequence": "not_reported",
                        "resulting_sequence": "not_reported",
                    }
                ),
            }
        )
    return participant, feature_rows


def _parse_pair_views(
    context: ParsingContext, output_root: Path, cfg: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    writer = ParquetBatchWriter(
        output_root / "source_pair_views",
        context.evidence_contract,
        "source_pair_views",
        **context.writer_kwargs(),
    )
    asset_stats: dict[str, Any] = {}
    with writer:
        for asset_id in cfg["pair_asset_ids"]:
            asset = context.asset(str(asset_id))
            dataset = Path(asset.relative_path).stem
            pair_counts: Counter[str] = Counter()
            row_count = 0
            self_pairs = 0
            with asset.path.open("rt", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle, delimiter="\t")
                for line_number, fields in enumerate(reader, start=1):
                    if len(fields) != 2 or not all(fields):
                        raise ValueError(
                            f"Malformed HuRI pair row in {asset.relative_path} "
                            f"line {line_number}: {fields!r}"
                        )
                    member_a, member_b = (strip_version(value) for value in fields)
                    unordered = stable_id("ensembl-pair", *sorted((member_a, member_b)))
                    duplicate_ordinal = pair_counts[unordered]
                    pair_counts[unordered] += 1
                    self_pair = member_a == member_b
                    self_pairs += int(self_pair)
                    row_count += 1
                    writer.append(
                        {
                            "pair_view_id": stable_id(
                                "huri-pair-view", asset.sha256, line_number
                            ),
                            "source_key": "huri",
                            "source_dataset": dataset,
                            "source_release": str(cfg["source_release"]),
                            "source_record_ordinal": line_number,
                            "member_a": member_a,
                            "member_b": member_b,
                            "unordered_pair_id": unordered,
                            "view_membership": True,
                            "provider_claim": "reported_interaction_pair",
                            "label_authorized": False,
                            "self_pair": self_pair,
                            "duplicate_ordinal": duplicate_ordinal,
                            "raw_file_path": asset.relative_path,
                            "raw_file_sha256": asset.sha256,
                            "raw_locator": f"line:{line_number}",
                            "source_fields_json": canonical_json(
                                {"raw_member_a": fields[0], "raw_member_b": fields[1]}
                            ),
                        }
                    )
            asset_stats[asset_id] = {
                "rows": row_count,
                "unique_unordered_pairs": len(pair_counts),
                "duplicate_rows": row_count - len(pair_counts),
                "self_pairs": self_pairs,
            }
    return writer.summary(), asset_stats


def _parse_mitab(
    context: ParsingContext, output_root: Path, cfg: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    evidence_writer = ParquetBatchWriter(
        output_root / "evidence_records",
        context.evidence_contract,
        "evidence_records",
        **context.writer_kwargs(),
    )
    participant_writer = ParquetBatchWriter(
        output_root / "participants",
        context.evidence_contract,
        "participants",
        **context.writer_kwargs(),
    )
    feature_writer = ParquetBatchWriter(
        output_root / "participant_features",
        context.evidence_contract,
        "participant_features",
        **context.writer_kwargs(),
    )
    asset_stats: dict[str, Any] = {}
    with evidence_writer, participant_writer, feature_writer:
        for asset_id in cfg["psi_asset_ids"]:
            asset = context.asset(str(asset_id))
            dataset = Path(asset.relative_path).stem
            detection_counts = Counter()
            interaction_type_counts = Counter()
            evidence_count = 0
            negative_count = 0
            expanded_count = 0
            with asset.path.open("rt", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
                for line_number, fields in enumerate(reader, start=1):
                    if len(fields) != len(MITAB_27_COLUMNS):
                        raise ValueError(
                            f"Expected 42 MITAB columns in {asset.relative_path} "
                            f"line {line_number}, observed {len(fields)}"
                        )
                    row = dict(zip(MITAB_27_COLUMNS, fields, strict=True))
                    evidence_id = stable_id("huri-evidence", asset.sha256, line_number)
                    raw_locator = f"line:{line_number}"
                    participant_a, features_a = _participant_row(
                        side="a",
                        row=row,
                        evidence_id=evidence_id,
                        asset_path=asset.relative_path,
                        raw_locator=raw_locator,
                    )
                    participant_b, features_b = _participant_row(
                        side="b",
                        row=row,
                        evidence_id=evidence_id,
                        asset_path=asset.relative_path,
                        raw_locator=raw_locator,
                    )
                    participant_writer.append(participant_a)
                    participant_writer.append(participant_b)
                    feature_writer.extend(features_a)
                    feature_writer.extend(features_b)

                    detection_ac, detection_name = _parse_term(row["detection_method"])
                    interaction_ac, interaction_name = _parse_term(
                        row["interaction_type"]
                    )
                    semantics, quality_flags = _interaction_semantics(
                        2,
                        detection_name,
                        interaction_ac,
                        row["complex_expansion"],
                    )
                    negative_flag = _raw_bool(row["negative"])
                    observation_state = (
                        "negative" if negative_flag is True else "positive"
                    )
                    if observation_state == "positive":
                        selection_state = "selected"
                        attempted_state = "attempted"
                        evaluability_state = "evaluable"
                        technical_state = "passed"
                        state_basis = "logically_implied_by_source_positive"
                    else:
                        selection_state = "selected"
                        attempted_state = "attempted"
                        evaluability_state = "unknown"
                        technical_state = "unknown"
                        state_basis = "source_asserted"
                    expansion_ac, expansion_name = _parse_term(row["complex_expansion"])
                    is_expanded = row["complex_expansion"] not in {"", "-"}
                    token_a = _pair_token(row["alt_id_a"], row["id_a"])
                    token_b = _pair_token(row["alt_id_b"], row["id_b"])
                    ordered_pair_id = stable_id("ordered-pair", token_a, token_b)
                    unordered_pair_id = stable_id(
                        "unordered-pair", *sorted((token_a, token_b))
                    )
                    interaction_ids = _split_pipe(row["interaction_identifiers"])
                    source_record_id = (
                        interaction_ids[0]
                        if interaction_ids
                        else f"{asset.asset_id}:line:{line_number}"
                    )
                    publications = _split_pipe(row["publication_identifiers"])
                    source_db_ids = _split_pipe(row["source_database"])
                    source_db_ids.extend(interaction_ids)
                    host_taxid, host_name = _parse_taxid(row["host_organism"])
                    (
                        participant_identification_ac_a,
                        participant_identification_name_a,
                    ) = _parse_term(row["participant_identification_method_a"])
                    (
                        participant_identification_ac_b,
                        participant_identification_name_b,
                    ) = _parse_term(row["participant_identification_method_b"])
                    participant_identification_acs = {
                        value
                        for value in (
                            participant_identification_ac_a,
                            participant_identification_ac_b,
                        )
                        if value
                    }
                    participant_identification_names = {
                        value
                        for value in (
                            participant_identification_name_a,
                            participant_identification_name_b,
                        )
                        if value
                    }
                    missingness = {
                        "search_space_state": "unresolved",
                        "assay_version": "not_reported",
                        "assay_batch": "not_reported",
                    }
                    if negative_flag is None:
                        missingness["negative_flag"] = "not_reported"
                    evidence_writer.append(
                        {
                            "evidence_id": evidence_id,
                            "source_key": "huri",
                            "source_dataset": dataset,
                            "source_release": str(cfg["source_release"]),
                            "source_record_id": source_record_id,
                            "source_record_ordinal": line_number,
                            "source_member": None,
                            "record_kind": "mitab_interaction_evidence",
                            "unordered_pair_id": unordered_pair_id,
                            "ordered_pair_id": ordered_pair_id,
                            "experiment_ids": [],
                            "publication_ids": publications,
                            "imex_ids": [
                                value
                                for value in interaction_ids
                                if "imex" in value.casefold()
                            ],
                            "source_database_ids": source_db_ids,
                            "participant_count": 2,
                            "original_nary": is_expanded,
                            "is_expanded_projection": is_expanded,
                            "expansion_method_ac": expansion_ac,
                            "expansion_method_name": expansion_name,
                            "negative_flag": negative_flag,
                            "interaction_type_ac": interaction_ac,
                            "interaction_type_name": interaction_name,
                            "interaction_semantics": semantics,
                            "detection_method_ac": detection_ac,
                            "detection_method_name": detection_name,
                            "participant_identification_method_ac": (
                                next(iter(participant_identification_acs))
                                if len(participant_identification_acs) == 1
                                else None
                            ),
                            "participant_identification_method_name": (
                                next(iter(participant_identification_names))
                                if len(participant_identification_names) == 1
                                else None
                            ),
                            "assay_family": (
                                "Y2H"
                                if detection_name
                                and "two hybrid" in detection_name.casefold()
                                else None
                            ),
                            "assay_version": None,
                            "assay_batch": None,
                            "host_taxid": host_taxid,
                            "host_name": host_name,
                            "orientation_semantics": "ordered_bait_prey",
                            "search_space_state": "unknown",
                            "selection_state": selection_state,
                            "attempted_state": attempted_state,
                            "evaluability_state": evaluability_state,
                            "technical_state": technical_state,
                            "observation_state": observation_state,
                            "state_basis": state_basis,
                            "failure_reasons": [],
                            "context_json": canonical_json(
                                {
                                    "participant_a_annotation": row["annotation_a"],
                                    "participant_b_annotation": row["annotation_b"],
                                    "interaction_annotations": row[
                                        "interaction_annotations"
                                    ],
                                }
                            ),
                            "assay_parameters_json": canonical_json(
                                {"raw": row["interaction_parameters"]}
                            ),
                            "confidence_values": _split_pipe(row["confidence"]),
                            "repeat_group_id": None,
                            "quality_flags": quality_flags,
                            "source_created_date": (
                                row["creation_date"]
                                if row["creation_date"] != "-"
                                else None
                            ),
                            "source_updated_date": (
                                row["update_date"]
                                if row["update_date"] != "-"
                                else None
                            ),
                            "raw_file_path": asset.relative_path,
                            "raw_file_sha256": asset.sha256,
                            "raw_locator": raw_locator,
                            "source_acquired_at_utc": asset.acquired_at_utc,
                            "parser_name": "ipin_openppi.ingestion.huri",
                            "parser_version": context.parser_version,
                            "parser_git_commit": context.parser_git_commit,
                            "container_sif_sha256": context.container_sif_sha256,
                            "schema_version": context.evidence_contract.version,
                            "schema_sha256": context.evidence_contract.sha256,
                            "license_id": str(cfg["public_license_id"]),
                            "attribution": str(cfg["public_attribution"]),
                            "redistribution_tier": str(
                                cfg["public_redistribution_tier"]
                            ),
                            "source_fields_json": canonical_json(row),
                            "missingness_json": canonical_json(missingness),
                        }
                    )
                    evidence_count += 1
                    negative_count += int(observation_state == "negative")
                    expanded_count += int(is_expanded)
                    detection_counts[f"{detection_ac}|{detection_name}"] += 1
                    interaction_type_counts[f"{interaction_ac}|{interaction_name}"] += 1
            asset_stats[asset_id] = {
                "evidence_records": evidence_count,
                "participants": evidence_count * 2,
                "negative_records": negative_count,
                "expanded_records": expanded_count,
                "detection_methods": dict(sorted(detection_counts.items())),
                "interaction_types": dict(sorted(interaction_type_counts.items())),
            }
    return (
        evidence_writer.summary(),
        participant_writer.summary(),
        feature_writer.summary(),
        asset_stats,
    )


def _parse_supplementary_tables(
    context: ParsingContext, output_root: Path, cfg: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    asset = context.asset(str(cfg["supplementary_asset_id"]))
    generic_writer = ParquetBatchWriter(
        output_root / "supplementary_raw_tabular_records",
        context.staging_contract,
        "raw_tabular_records",
        **context.writer_kwargs(),
    )
    orf_writer = ParquetBatchWriter(
        output_root / "huri_orf_mappings",
        context.evidence_contract,
        "huri_orf_mappings",
        **context.writer_kwargs(),
    )
    space_writer = ParquetBatchWriter(
        output_root / "huri_space_membership",
        context.evidence_contract,
        "huri_space_membership",
        **context.writer_kwargs(),
    )
    table_stats: dict[str, Any] = {}
    unparsed_members: list[dict[str, Any]] = []
    archive_inventory: list[dict[str, Any]] = []
    with (
        zipfile.ZipFile(asset.path) as archive,
        generic_writer,
        orf_writer,
        space_writer,
    ):
        for info in archive.infolist():
            archive_inventory.append(
                {
                    "member": info.filename,
                    "bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "is_directory": info.is_dir(),
                }
            )
            if info.is_dir() or info.filename.startswith("__MACOSX/"):
                continue
            match = _TABLE_NUMBER_RE.search(info.filename)
            if not match:
                unparsed_members.append(
                    {"member": info.filename, "reason": "unsupported_member_format"}
                )
                continue
            table_number = int(match.group(1))
            dataset = f"huri_supplement_table_{table_number}"
            with archive.open(info) as binary:
                text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text, delimiter="\t")
                if reader.fieldnames is None:
                    raise ValueError(f"Supplement table lacks header: {info.filename}")
                row_count = 0
                field_value_counts: dict[str, Counter[str]] = {
                    name: Counter() for name in reader.fieldnames
                }
                for row_ordinal, row in enumerate(reader, start=1):
                    if None in row:
                        raise ValueError(
                            f"Malformed supplementary row in {info.filename} "
                            f"record {row_ordinal}"
                        )
                    fields = {str(key): value for key, value in row.items()}
                    generic_writer.append(
                        {
                            "staging_record_id": stable_id(
                                "huri-supp-row",
                                asset.sha256,
                                info.filename,
                                row_ordinal,
                            ),
                            "source_key": "huri",
                            "source_dataset": dataset,
                            "source_release": str(cfg["source_release"]),
                            "source_member": info.filename,
                            "source_record_ordinal": row_ordinal,
                            "raw_file_path": asset.relative_path,
                            "raw_file_sha256": asset.sha256,
                            "raw_locator": f"zip:{info.filename}#data_row:{row_ordinal}",
                            "fields_json": canonical_json(fields),
                            "redistribution_tier": str(
                                cfg["supplement_redistribution_tier"]
                            ),
                        }
                    )
                    if table_number == 1:
                        space_writer.append(
                            {
                                "space_record_id": stable_id(
                                    "huri-space", asset.sha256, row_ordinal
                                ),
                                "ensembl_gene_id": strip_version(
                                    fields["Ensembl_gene_id"]
                                ),
                                "in_space_3": _raw_bool(fields["in_space_3"]),
                                "in_gtex": _raw_bool(fields["in_GTEx"]),
                                "in_hpa": _raw_bool(fields["in_HPA"]),
                                "in_fantom": _raw_bool(fields["in_FANTOM"]),
                                "raw_file_path": asset.relative_path,
                                "raw_locator": f"zip:{info.filename}#data_row:{row_ordinal}",
                                "redistribution_tier": str(
                                    cfg["supplement_redistribution_tier"]
                                ),
                            }
                        )
                    elif table_number == 2:
                        missingness = {
                            key: "not_reported"
                            for key in (
                                "ensembl_transcript_id",
                                "ensembl_protein_id",
                                "ensembl_gene_id",
                                "gene_symbol",
                            )
                            if not fields.get(
                                {
                                    "ensembl_transcript_id": "ensembl_transcript_id",
                                    "ensembl_protein_id": "ensembl_protein_id",
                                    "ensembl_gene_id": "ensembl_gene_id",
                                    "gene_symbol": "symbol",
                                }[key]
                            )
                        }
                        orf_writer.append(
                            {
                                "orf_mapping_id": stable_id(
                                    "huri-orf-map", asset.sha256, row_ordinal
                                ),
                                "orf_id": fields["orf_id"],
                                "ensembl_transcript_id": fields["ensembl_transcript_id"]
                                or None,
                                "ensembl_protein_id": fields["ensembl_protein_id"]
                                or None,
                                "ensembl_gene_id": fields["ensembl_gene_id"] or None,
                                "gene_symbol": fields["symbol"] or None,
                                "raw_file_path": asset.relative_path,
                                "raw_locator": f"zip:{info.filename}#data_row:{row_ordinal}",
                                "redistribution_tier": str(
                                    cfg["supplement_redistribution_tier"]
                                ),
                                "missingness_json": canonical_json(missingness),
                            }
                        )
                    row_count += 1
                    for field, value in fields.items():
                        if table_number in {1, 9, 11, 16}:
                            field_value_counts[field][value] += 1
                table_stats[str(table_number)] = {
                    "member": info.filename,
                    "rows": row_count,
                    "columns": reader.fieldnames,
                    "selected_value_counts": {
                        field: dict(counter.most_common(30))
                        for field, counter in field_value_counts.items()
                        if len(counter) <= 30
                    },
                }
        for info in archive.infolist():
            if (
                not info.is_dir()
                and not info.filename.startswith("__MACOSX/")
                and not info.filename.endswith(".txt")
            ):
                unparsed_members.append(
                    {
                        "member": info.filename,
                        "reason": "binary_spreadsheet_not_parsed_v1",
                    }
                )
    return (
        generic_writer.summary(),
        orf_writer.summary(),
        space_writer.summary(),
        {
            "tables": table_stats,
            "archive_inventory": archive_inventory,
            "unparsed_members": unparsed_members,
        },
    )


def parse_huri(context: ParsingContext, output_root: Path) -> dict[str, Any]:
    cfg = dict(context.config["sources"]["huri"])
    pair_summary, pair_stats = _parse_pair_views(context, output_root, cfg)
    evidence_summary, participant_summary, feature_summary, mitab_stats = _parse_mitab(
        context, output_root, cfg
    )
    supplement_summary, orf_summary, space_summary, supplement_stats = (
        _parse_supplementary_tables(context, output_root, cfg)
    )
    return {
        "source": "huri",
        "release": str(cfg["source_release"]),
        "pair_assets": pair_stats,
        "mitab_assets": mitab_stats,
        "supplement": supplement_stats,
        "tables": {
            "source_pair_views": pair_summary,
            "evidence_records": evidence_summary,
            "participants": participant_summary,
            "participant_features": feature_summary,
            "supplementary_raw_tabular_records": supplement_summary,
            "huri_orf_mappings": orf_summary,
            "huri_space_membership": space_summary,
        },
    }
