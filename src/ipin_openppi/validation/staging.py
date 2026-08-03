"""Independent validation gate for immutable primary-source staging datasets."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
from typing import Any, Iterable, Mapping
import uuid

import duckdb
import pyarrow.parquet as pq
import yaml

from ipin_openppi.ingestion.common import (
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import SchemaContract, load_contract, sha256_file


_SUMMARY_KEYS = {
    "table",
    "rows",
    "parts",
    "files",
    "schema_name",
    "schema_version",
    "schema_sha256",
}
_SAFE_NAME = re.compile(r"[^a-zA-Z0-9_]")


@dataclass(frozen=True)
class DatasetSummary:
    report_path: str
    table: str
    rows: int
    parts: int
    files: tuple[Mapping[str, Any], ...]
    schema_name: str
    schema_version: int
    schema_sha256: str


class Checks:
    """Collect all failures so one expensive scan yields a complete diagnosis."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def require(
        self,
        check_id: str,
        passed: bool,
        *,
        observed: Any = None,
        expected: Any = None,
        detail: str | None = None,
    ) -> None:
        record = {
            "check_id": check_id,
            "status": "pass" if passed else "fail",
            "observed": observed,
            "expected": expected,
        }
        if detail:
            record["detail"] = detail
        self.records.append(record)

    def warn(self, check_id: str, *, observed: Any, detail: str) -> None:
        self.records.append(
            {
                "check_id": check_id,
                "status": "warning",
                "observed": observed,
                "detail": detail,
            }
        )

    @property
    def passed(self) -> bool:
        return not any(record["status"] == "fail" for record in self.records)

    def counts(self) -> dict[str, int]:
        return {
            status: sum(record["status"] == status for record in self.records)
            for status in ("pass", "warning", "fail")
        }


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("rt", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("rt", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _iter_summaries(node: Any, path: tuple[str, ...] = ()) -> Iterable[DatasetSummary]:
    if isinstance(node, dict):
        if _SUMMARY_KEYS.issubset(node):
            yield DatasetSummary(
                report_path=".".join(path),
                table=str(node["table"]),
                rows=int(node["rows"]),
                parts=int(node["parts"]),
                files=tuple(node["files"]),
                schema_name=str(node["schema_name"]),
                schema_version=int(node["schema_version"]),
                schema_sha256=str(node["schema_sha256"]),
            )
            return
        for key, value in node.items():
            yield from _iter_summaries(value, (*path, str(key)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_summaries(value, (*path, str(index)))


def _nested(document: Mapping[str, Any], dotted_path: str) -> Any:
    value: Any = document
    for component in dotted_path.split("."):
        if not isinstance(value, Mapping) or component not in value:
            raise KeyError(dotted_path)
        value = value[component]
    return value


def _sum_key(node: Any, key: str) -> int:
    if isinstance(node, dict):
        own = int(node.get(key, 0)) if node.get(key) is not None else 0
        return own + sum(_sum_key(value, key) for value in node.values())
    if isinstance(node, list):
        return sum(_sum_key(value, key) for value in node)
    return 0


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _view_name(table: str) -> str:
    return "v_" + _SAFE_NAME.sub("_", table)


def _query_scalar(connection: duckdb.DuckDBPyConnection, sql: str) -> int:
    value = connection.execute(sql).fetchone()
    if value is None or value[0] is None:
        return 0
    return int(value[0])


def _validate_contract_rows(
    *,
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    contracts: Mapping[str, SchemaContract],
    table_paths: Mapping[str, list[Path]],
) -> None:
    table_contracts: dict[str, SchemaContract] = {}
    for contract in contracts.values():
        for table in contract.document["tables"]:
            if table in table_contracts:
                raise ValueError(f"Table appears in two contracts: {table}")
            table_contracts[str(table)] = contract

    for table, paths in sorted(table_paths.items()):
        contract = table_contracts[table]
        view = _view_name(table)
        connection.read_parquet([path.as_posix() for path in paths]).create_view(view)
        spec = contract.table_spec(table)

        null_counts: dict[str, int] = {}
        for column in spec.get("required_non_null", []):
            quoted = _quote_identifier(str(column))
            count = _query_scalar(
                connection, f"SELECT count(*) FROM {view} WHERE {quoted} IS NULL"
            )
            if count:
                null_counts[str(column)] = count
        checks.require(
            f"contract.{table}.required_non_null",
            not null_counts,
            observed=null_counts,
            expected={},
        )

        invalid_enums: dict[str, int] = {}
        for column, enum_name in spec.get("enum_columns", {}).items():
            allowed = list(contract.document["enums"][enum_name])
            placeholders = ",".join("?" for _ in allowed)
            quoted = _quote_identifier(str(column))
            count = int(
                connection.execute(
                    f"SELECT count(*) FROM {view} "
                    f"WHERE {quoted} IS NOT NULL AND {quoted} NOT IN ({placeholders})",
                    allowed,
                ).fetchone()[0]
            )
            if count:
                invalid_enums[str(column)] = count
        checks.require(
            f"contract.{table}.enum_values",
            not invalid_enums,
            observed=invalid_enums,
            expected={},
        )

        primary_key = [str(value) for value in spec.get("primary_key", [])]
        if primary_key:
            columns = ", ".join(_quote_identifier(value) for value in primary_key)
            duplicates = _query_scalar(
                connection,
                f"SELECT coalesce(sum(n - 1), 0) FROM "
                f"(SELECT {columns}, count(*) AS n FROM {view} "
                f"GROUP BY {columns} HAVING count(*) > 1)",
            )
            checks.require(
                f"contract.{table}.primary_key_unique",
                duplicates == 0,
                observed=duplicates,
                expected=0,
            )

    for table, paths in sorted(table_paths.items()):
        del paths
        contract = table_contracts[table]
        for foreign_key in contract.table_spec(table).get("foreign_keys", []):
            columns = [str(value) for value in foreign_key["columns"]]
            referenced_table, referenced_column = str(foreign_key["references"]).split(
                ".", 1
            )
            if referenced_table not in table_paths:
                checks.require(
                    f"contract.{table}.foreign_key.{referenced_table}",
                    False,
                    observed="referenced table absent",
                    expected="referenced table present",
                )
                continue
            if len(columns) != 1:
                raise ValueError("Validator currently supports one-column foreign keys")
            column = _quote_identifier(columns[0])
            reference = _quote_identifier(referenced_column)
            orphans = _query_scalar(
                connection,
                f"SELECT count(*) FROM {_view_name(table)} child "
                f"LEFT JOIN {_view_name(referenced_table)} parent "
                f"ON child.{column} = parent.{reference} "
                f"WHERE child.{column} IS NOT NULL AND parent.{reference} IS NULL",
            )
            checks.require(
                f"contract.{table}.foreign_key.{referenced_table}",
                orphans == 0,
                observed=orphans,
                expected=0,
            )


def _validate_semantics(
    *,
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    table_paths: Mapping[str, list[Path]],
    manifest: Mapping[str, Any],
    expectations: Mapping[str, Any],
) -> None:
    available = set(table_paths)
    if {"evidence_records", "participants"}.issubset(available):
        evidence = _view_name("evidence_records")
        participants = _view_name("participants")
        queries = {
            "evidence.positive_participant_count": (
                f"SELECT count(*) FROM {evidence} WHERE participant_count < 1",
                0,
            ),
            "evidence.exact_original_nary": (
                f"SELECT count(*) FROM {evidence} "
                "WHERE original_nary IS DISTINCT FROM (participant_count > 2)",
                0,
            ),
            "evidence.pair_ids_only_for_binary": (
                f"SELECT count(*) FROM {evidence} WHERE "
                "((participant_count = 2) AND "
                "(unordered_pair_id IS NULL OR ordered_pair_id IS NULL)) OR "
                "((participant_count <> 2) AND "
                "(unordered_pair_id IS NOT NULL OR ordered_pair_id IS NOT NULL))",
                0,
            ),
            "evidence.direct_binary_cardinality": (
                f"SELECT count(*) FROM {evidence} "
                "WHERE interaction_semantics = 'direct_binary' "
                "AND participant_count <> 2",
                0,
            ),
            "evidence.expanded_not_direct_binary": (
                f"SELECT count(*) FROM {evidence} "
                "WHERE is_expanded_projection "
                "AND interaction_semantics = 'direct_binary'",
                0,
            ),
            "evidence.technical_failure_not_negative": (
                f"SELECT count(*) FROM {evidence} "
                "WHERE technical_state = 'failed' AND observation_state = 'negative'",
                0,
            ),
            "evidence.negative_flag_state_consistency": (
                f"SELECT count(*) FROM {evidence} WHERE "
                "(negative_flag IS TRUE AND observation_state <> 'negative') OR "
                "(observation_state = 'negative' AND negative_flag IS NOT TRUE)",
                0,
            ),
            "evidence.participant_count_matches_rows": (
                f"SELECT count(*) FROM {evidence} e LEFT JOIN "
                f"(SELECT evidence_id, count(*) AS n FROM {participants} "
                "GROUP BY evidence_id) p USING (evidence_id) "
                "WHERE e.participant_count <> coalesce(p.n, 0)",
                0,
            ),
            "evidence.unary_quality_flag": (
                f"SELECT count(*) FROM {evidence} WHERE participant_count = 1 "
                "AND NOT list_contains(quality_flags, 'original_unary_preserved')",
                0,
            ),
            "evidence.unary_not_nary_flagged": (
                f"SELECT count(*) FROM {evidence} WHERE participant_count = 1 "
                "AND list_contains(quality_flags, 'original_nary_preserved')",
                0,
            ),
            "evidence.nary_quality_flag": (
                f"SELECT count(*) FROM {evidence} WHERE participant_count > 2 "
                "AND NOT list_contains(quality_flags, 'original_nary_preserved')",
                0,
            ),
        }
        for check_id, (sql, expected) in queries.items():
            observed = _query_scalar(connection, sql)
            checks.require(
                check_id, observed == expected, observed=observed, expected=expected
            )

    if "participant_features" in available:
        features = _view_name("participant_features")
        participants = _view_name("participants")
        evidence = _view_name("evidence_records")
        mismatches = _query_scalar(
            connection,
            f"SELECT count(*) FROM {features} f "
            f"JOIN {participants} p USING (participant_id) "
            f"LEFT JOIN {evidence} e ON f.evidence_id = e.evidence_id "
            "WHERE f.evidence_id <> p.evidence_id OR e.evidence_id IS NULL",
        )
        checks.require(
            "evidence.feature_evidence_links",
            mismatches == 0,
            observed=mismatches,
            expected=0,
        )

    for table in (
        "source_pair_views",
        "huri_structural_contact_annotations",
        "huri_fusion_interference",
    ):
        if table in available:
            authorized = _query_scalar(
                connection,
                f"SELECT count(*) FROM {_view_name(table)} WHERE label_authorized",
            )
            checks.require(
                f"authorization.{table}.labels_prohibited",
                authorized == 0,
                observed=authorized,
                expected=0,
            )

    if "protein_sequences" in available:
        sequences = _view_name("protein_sequences")
        bad_length = _query_scalar(
            connection,
            f"SELECT count(*) FROM {sequences} WHERE length(sequence) <> sequence_length",
        )
        bad_sha = _query_scalar(
            connection,
            f"SELECT count(*) FROM {sequences} WHERE sha256(sequence) <> sequence_sha256",
        )
        bad_view = _query_scalar(
            connection,
            f"SELECT count(*) FROM {sequences} WHERE "
            "canonical IS DISTINCT FROM (sequence_view = 'canonical') OR "
            "sequence_view NOT IN "
            "('canonical', 'additional_isoform', 'additional_non_isoform')",
        )
        checks.require(
            "uniprot.sequence_lengths", bad_length == 0, observed=bad_length, expected=0
        )
        checks.require(
            "uniprot.sequence_sha256", bad_sha == 0, observed=bad_sha, expected=0
        )
        checks.require(
            "uniprot.sequence_view_semantics",
            bad_view == 0,
            observed=bad_view,
            expected=0,
        )

    diagnostics = expectations.get("expected_diagnostics", {})
    source_reports = manifest.get("source_reports", {})
    if "huri" in source_reports:
        source_error_cells = _sum_key(
            source_reports["huri"].get("supplement", {}).get("tables", {}),
            "source_error_cells",
        )
        expected = int(diagnostics["huri_workbook_source_error_cells"])
        checks.require(
            "huri.workbook_source_error_cells_preserved",
            source_error_cells == expected,
            observed=source_error_cells,
            expected=expected,
        )

    if "sifts_chain_uniprot" in available:
        chain = _view_name("sifts_chain_uniprot")
        descending = _query_scalar(
            connection,
            f"SELECT count(*) FROM {chain} "
            "WHERE uniprot_begin IS NOT NULL AND uniprot_end IS NOT NULL "
            "AND uniprot_begin > uniprot_end",
        )
        expected = int(diagnostics["sifts_chain_uniprot_descending_intervals"])
        checks.require(
            "sifts.chain_uniprot_descending_intervals_preserved",
            descending == expected,
            observed=descending,
            expected=expected,
        )
    if "sifts_observed_segments" in available:
        observed_segments = _view_name("sifts_observed_segments")
        descending = _query_scalar(
            connection,
            f"SELECT count(*) FROM {observed_segments} "
            "WHERE uniprot_begin IS NOT NULL AND uniprot_end IS NOT NULL "
            "AND uniprot_begin > uniprot_end",
        )
        expected = int(diagnostics["sifts_observed_segment_descending_intervals"])
        checks.require(
            "sifts.observed_segment_descending_intervals",
            descending == expected,
            observed=descending,
            expected=expected,
        )
    if {
        "sifts_chain_uniprot",
        "sifts_chain_taxonomy",
        "protein_sequences",
    }.issubset(available):
        chain = _view_name("sifts_chain_uniprot")
        taxonomy = _view_name("sifts_chain_taxonomy")
        sequences = _view_name("protein_sequences")
        row = connection.execute(
            f"WITH human_accessions AS ("
            f"SELECT DISTINCT u.uniprot_accession FROM {chain} u "
            f"JOIN {taxonomy} t USING (pdb_id, chain_id) WHERE t.taxid = 9606), "
            f"primary_accessions AS ("
            f"SELECT DISTINCT uniprot_accession FROM {sequences}), "
            f"additional_sequence_ids AS ("
            f"SELECT DISTINCT isoform_id AS uniprot_accession FROM {sequences} "
            f"WHERE isoform_id IS NOT NULL) "
            f"SELECT count(*), count(p.uniprot_accession), "
            f"count(a.uniprot_accession), "
            f"count(*) FILTER (WHERE p.uniprot_accession IS NOT NULL "
            f"OR a.uniprot_accession IS NOT NULL) "
            f"FROM human_accessions h "
            f"LEFT JOIN primary_accessions p USING (uniprot_accession) "
            f"LEFT JOIN additional_sequence_ids a USING (uniprot_accession)"
        ).fetchone()
        human_accessions = int(row[0])
        primary_matches = int(row[1])
        additional_matches = int(row[2])
        overlapping_accessions = int(row[3])
        expected_human = int(diagnostics["sifts_human_chain_distinct_accessions"])
        expected_primary = int(
            diagnostics["sifts_human_chain_accessions_matching_primary_accessions"]
        )
        expected_additional = int(
            diagnostics["sifts_human_chain_accessions_matching_additional_sequence_ids"]
        )
        expected_overlap = int(
            diagnostics["sifts_human_chain_accessions_in_frozen_uniprot"]
        )
        checks.require(
            "sifts.human_chain_distinct_accessions",
            human_accessions == expected_human,
            observed=human_accessions,
            expected=expected_human,
        )
        checks.require(
            "sifts.human_chain_accessions_matching_primary_accessions",
            primary_matches == expected_primary,
            observed=primary_matches,
            expected=expected_primary,
        )
        checks.require(
            "sifts.human_chain_accessions_matching_additional_sequence_ids",
            additional_matches == expected_additional,
            observed=additional_matches,
            expected=expected_additional,
        )
        checks.require(
            "sifts.human_chain_accessions_in_frozen_uniprot",
            overlapping_accessions == expected_overlap,
            observed=overlapping_accessions,
            expected=expected_overlap,
        )

    if {"pdb_sifts", "uniprot"}.issubset(source_reports):
        checks.warn(
            "blocker.ISSUE-0005.sifts_uniprot_release_alignment",
            observed={
                "sifts_declared_uniprot_release": source_reports["pdb_sifts"].get(
                    "declared_uniprot_release_in_sifts"
                ),
                "frozen_uniprot_release": source_reports["uniprot"].get("release"),
            },
            detail=(
                "Parsing may proceed, but exact structure reconciliation and all "
                "structure-derived labels remain blocked."
            ),
        )


def validate_staging(
    *,
    project_root: Path,
    staging_root: Path,
    expectation_path: Path,
    allow_source_subset: bool,
) -> dict[str, Any]:
    require_apptainer()
    checks = Checks()
    root = staging_root.resolve(strict=True)
    staging_boundary = (project_root / "data/staging").resolve(strict=True)
    try:
        root.relative_to(staging_boundary)
    except ValueError as exc:
        raise RuntimeError(f"Staging root escapes data/staging: {root}") from exc
    if staging_root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"Staging root must be a non-link directory: {staging_root}")
    if allow_source_subset and not root.name.startswith("_smoke_"):
        raise RuntimeError("--allow-source-subset is restricted to _smoke_* roots")

    manifest_path = root / "PARSE_MANIFEST.json"
    sidecar_path = root / "PARSE_MANIFEST.json.sha256"
    manifest = _load_json(manifest_path)
    expectations = _load_yaml(expectation_path)
    manifest_sha = sha256_file(manifest_path)
    sidecar_tokens = sidecar_path.read_text(encoding="utf-8").split()
    sidecar_sha = sidecar_tokens[0] if sidecar_tokens else None
    sidecar_name = sidecar_tokens[1] if len(sidecar_tokens) > 1 else None
    checks.require(
        "manifest.sha256_sidecar",
        sidecar_sha == manifest_sha and sidecar_name == "PARSE_MANIFEST.json",
        observed={"sha256": sidecar_sha, "filename": sidecar_name},
        expected={"sha256": manifest_sha, "filename": "PARSE_MANIFEST.json"},
    )
    checks.require(
        "manifest.status_complete",
        manifest.get("status") == "complete",
        observed=manifest.get("status"),
        expected="complete",
    )
    checks.require(
        "authorization.no_label_construction",
        manifest.get("label_construction_performed") is False,
        observed=manifest.get("label_construction_performed"),
        expected=False,
    )
    checks.require(
        "authorization.no_model_training",
        manifest.get("model_training_performed") is False,
        observed=manifest.get("model_training_performed"),
        expected=False,
    )

    expected_sources = [str(value) for value in expectations["expected_sources"]]
    observed_sources = [str(value) for value in manifest.get("sources", [])]
    if allow_source_subset:
        expected_ordered_subset = [
            source for source in expected_sources if source in observed_sources
        ]
        valid_sources = (
            observed_sources == expected_ordered_subset
            and bool(observed_sources)
            and set(observed_sources).issubset(expected_sources)
        )
    else:
        valid_sources = observed_sources == expected_sources
    checks.require(
        "manifest.source_scope",
        valid_sources,
        observed=observed_sources,
        expected=(
            expected_sources if not allow_source_subset else "ordered nonempty subset"
        ),
    )

    runtime = manifest.get("runtime", {})
    expected_parser = str(expectations["expected_parser_version"])
    expected_container_sha = str(expectations["expected_container_sha256"])
    checks.require(
        "runtime.parser_version",
        runtime.get("parser_version") == expected_parser,
        observed=runtime.get("parser_version"),
        expected=expected_parser,
    )
    checks.require(
        "runtime.architecture",
        runtime.get("architecture") == "aarch64",
        observed=runtime.get("architecture"),
        expected="aarch64",
    )
    checks.require(
        "runtime.manifest_container_sha256",
        runtime.get("container_sif_sha256") == expected_container_sha,
        observed=runtime.get("container_sif_sha256"),
        expected=expected_container_sha,
    )
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    active_sha = sha256_file(active_container)
    checks.require(
        "runtime.active_container_sha256",
        active_sha == expected_container_sha,
        observed=active_sha,
        expected=expected_container_sha,
    )

    parse_config_path = project_root / str(manifest["inputs"]["config"])
    parse_config = _load_yaml(parse_config_path)
    observed_parse_config_sha = sha256_file(parse_config_path)
    checks.require(
        "manifest.parse_config_sha256",
        observed_parse_config_sha == manifest["inputs"]["config_sha256"],
        observed=observed_parse_config_sha,
        expected=manifest["inputs"]["config_sha256"],
    )
    checks.require(
        "authorization.parse_config_labels_false",
        parse_config["authorization"].get("label_construction") is False,
        observed=parse_config["authorization"].get("label_construction"),
        expected=False,
    )
    checks.require(
        "authorization.parse_config_training_false",
        parse_config["authorization"].get("model_training") is False,
        observed=parse_config["authorization"].get("model_training"),
        expected=False,
    )
    if not allow_source_subset:
        checks.require(
            "provenance.production_parse_was_clean",
            manifest.get("git", {}).get("tracked_worktree_clean") is True,
            observed=manifest.get("git", {}).get("tracked_worktree_clean"),
            expected=True,
        )
        current_git = git_provenance(project_root)
        checks.require(
            "provenance.validator_checkout_matches_parse_commit",
            current_git["commit"] == manifest.get("git", {}).get("commit"),
            observed=current_git["commit"],
            expected=manifest.get("git", {}).get("commit"),
        )

    expected_releases = expectations["expected_source_releases"]
    for source in observed_sources:
        observed_release = manifest["source_reports"][source].get("release")
        expected_release = str(expected_releases[source])
        checks.require(
            f"source.{source}.release",
            observed_release == expected_release,
            observed=observed_release,
            expected=expected_release,
        )

    for dotted_path, expected in expectations["expected_report_values"].items():
        components = str(dotted_path).split(".")
        if len(components) > 1 and components[0] == "source_reports":
            if components[1] not in observed_sources:
                continue
        try:
            observed = _nested(manifest, str(dotted_path))
        except KeyError:
            observed = "__missing__"
        checks.require(
            f"report.{dotted_path}",
            observed == expected,
            observed=observed,
            expected=expected,
        )

    evidence_contract = load_contract(
        project_root / str(manifest["inputs"]["evidence_schema"])
    )
    staging_contract = load_contract(
        project_root / str(manifest["inputs"]["staging_schema"])
    )
    contracts = {
        evidence_contract.name: evidence_contract,
        staging_contract.name: staging_contract,
    }
    checks.require(
        "schema.evidence_manifest_sha256",
        evidence_contract.sha256 == manifest["inputs"]["evidence_schema_sha256"],
        observed=evidence_contract.sha256,
        expected=manifest["inputs"]["evidence_schema_sha256"],
    )
    checks.require(
        "schema.staging_manifest_sha256",
        staging_contract.sha256 == manifest["inputs"]["staging_schema_sha256"],
        observed=staging_contract.sha256,
        expected=manifest["inputs"]["staging_schema_sha256"],
    )

    summaries = list(_iter_summaries(manifest.get("source_reports", {})))
    checks.require(
        "manifest.table_summaries_present",
        bool(summaries),
        observed=len(summaries),
        expected=">0",
    )
    expected_rows = {
        str(key): int(value)
        for key, value in expectations["expected_table_rows"].items()
        if str(key).split("/", 1)[0] in observed_sources
    }
    observed_rows: dict[str, int] = {}
    manifest_file_paths: set[Path] = set()
    table_paths: dict[str, list[Path]] = {}
    file_mismatches: list[dict[str, Any]] = []
    schema_mismatches: list[dict[str, Any]] = []
    total_manifest_bytes = 0
    total_manifest_rows = 0

    for summary in summaries:
        contract = contracts.get(summary.schema_name)
        if contract is None or summary.table not in contract.document["tables"]:
            schema_mismatches.append(
                {"report_path": summary.report_path, "error": "unknown contract/table"}
            )
            continue
        expected_schema = contract.arrow_schema(summary.table).remove_metadata()
        resolved_files: list[Path] = []
        for file_record in summary.files:
            candidate = Path(str(file_record["path"]))
            if not candidate.is_absolute():
                candidate = project_root / candidate
            try:
                candidate = candidate.resolve(strict=True)
                candidate.relative_to(root)
            except (FileNotFoundError, ValueError) as exc:
                file_mismatches.append(
                    {
                        "report_path": summary.report_path,
                        "path": str(file_record.get("path")),
                        "error": str(exc),
                    }
                )
                continue
            if candidate.is_symlink() or not candidate.is_file():
                file_mismatches.append(
                    {
                        "path": candidate.as_posix(),
                        "error": "not a regular non-link file",
                    }
                )
                continue
            resolved_files.append(candidate)
            manifest_file_paths.add(candidate)
            info = candidate.stat(follow_symlinks=False)
            observed_file_rows = int(pq.ParquetFile(candidate).metadata.num_rows)
            observed_file_sha = sha256_file(candidate)
            expected_bytes = int(file_record["bytes"])
            expected_file_rows = int(file_record["rows"])
            expected_file_sha = str(file_record["sha256"])
            total_manifest_bytes += info.st_size
            total_manifest_rows += observed_file_rows
            if (
                info.st_size != expected_bytes
                or observed_file_rows != expected_file_rows
                or observed_file_sha != expected_file_sha
            ):
                file_mismatches.append(
                    {
                        "path": candidate.as_posix(),
                        "observed": {
                            "bytes": info.st_size,
                            "rows": observed_file_rows,
                            "sha256": observed_file_sha,
                        },
                        "expected": {
                            "bytes": expected_bytes,
                            "rows": expected_file_rows,
                            "sha256": expected_file_sha,
                        },
                    }
                )
            observed_schema = pq.read_schema(candidate)
            metadata = {
                key.decode(): value.decode()
                for key, value in (observed_schema.metadata or {}).items()
            }
            expected_metadata = {
                "ipin.schema_name": contract.name,
                "ipin.schema_version": str(contract.version),
                "ipin.schema_sha256": contract.sha256,
                "ipin.table_name": summary.table,
                "ipin.parser_version": expected_parser,
                "ipin.container_sif_sha256": expected_container_sha,
                "ipin.parser_git_commit": str(manifest.get("git", {}).get("commit")),
            }
            metadata_errors = {
                key: {"observed": metadata.get(key), "expected": value}
                for key, value in expected_metadata.items()
                if metadata.get(key) != value
            }
            if (
                not observed_schema.remove_metadata().equals(expected_schema)
                or metadata_errors
            ):
                schema_mismatches.append(
                    {
                        "path": candidate.as_posix(),
                        "arrow_schema_equal": observed_schema.remove_metadata().equals(
                            expected_schema
                        ),
                        "metadata_errors": metadata_errors,
                    }
                )

        if resolved_files:
            parent_set = {path.parent for path in resolved_files}
            if len(parent_set) != 1:
                file_mismatches.append(
                    {
                        "report_path": summary.report_path,
                        "error": "files span directories",
                    }
                )
                continue
            dataset_key = next(iter(parent_set)).relative_to(root).as_posix()
            observed_rows[dataset_key] = summary.rows
            table_paths.setdefault(summary.table, []).extend(resolved_files)
            summary_file_rows = sum(int(record["rows"]) for record in summary.files)
            checks.require(
                f"manifest.dataset_summary.{dataset_key}",
                summary.parts == len(summary.files)
                and summary.rows == summary_file_rows
                and summary.schema_name == contract.name
                and summary.schema_version == contract.version
                and summary.schema_sha256 == contract.sha256,
                observed={
                    "parts": summary.parts,
                    "files": len(summary.files),
                    "rows": summary.rows,
                    "file_rows": summary_file_rows,
                    "schema_name": summary.schema_name,
                    "schema_version": summary.schema_version,
                    "schema_sha256": summary.schema_sha256,
                },
                expected={
                    "parts_equal_files": True,
                    "rows_equal_file_rows": True,
                    "schema_name": contract.name,
                    "schema_version": contract.version,
                    "schema_sha256": contract.sha256,
                },
            )

    checks.require(
        "manifest.expected_dataset_rows",
        observed_rows == expected_rows,
        observed=observed_rows,
        expected=expected_rows,
    )
    actual_parquet_paths = {path.resolve() for path in root.rglob("*.parquet")}
    checks.require(
        "manifest.exact_parquet_file_inventory",
        actual_parquet_paths == manifest_file_paths,
        observed={
            "count": len(actual_parquet_paths),
            "unexpected": sorted(
                path.as_posix() for path in actual_parquet_paths - manifest_file_paths
            ),
            "missing": sorted(
                path.as_posix() for path in manifest_file_paths - actual_parquet_paths
            ),
        },
        expected={"count": len(manifest_file_paths), "unexpected": [], "missing": []},
    )
    checks.require(
        "manifest.parquet_file_hash_size_row_integrity",
        not file_mismatches,
        observed={
            "mismatch_count": len(file_mismatches),
            "examples": file_mismatches[:20],
        },
        expected={"mismatch_count": 0},
    )
    checks.require(
        "schema.parquet_contract_and_provenance_metadata",
        not schema_mismatches,
        observed={
            "mismatch_count": len(schema_mismatches),
            "examples": schema_mismatches[:20],
        },
        expected={"mismatch_count": 0},
    )

    filesystem_errors = []
    allowed_non_parquet = {manifest_path.resolve(), sidecar_path.resolve()}
    for path in (root, *sorted(root.rglob("*"))):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            filesystem_errors.append(
                {"path": path.as_posix(), "error": "symbolic link"}
            )
        if info.st_mode & 0o222:
            filesystem_errors.append({"path": path.as_posix(), "error": "writable"})
        if stat.S_ISREG(info.st_mode):
            resolved = path.resolve()
            if (
                resolved not in actual_parquet_paths
                and resolved not in allowed_non_parquet
            ):
                filesystem_errors.append(
                    {"path": path.as_posix(), "error": "unexpected regular file"}
                )
    checks.require(
        "filesystem.immutable_link_free_exact_inventory",
        not filesystem_errors,
        observed={
            "error_count": len(filesystem_errors),
            "examples": filesystem_errors[:20],
        },
        expected={"error_count": 0},
    )

    raw_pairs = {
        (str(record["path"]), str(record["sha256"]))
        for record in manifest["inputs"]["raw_verification"]
    }
    unexpected_raw_pairs: dict[str, list[list[str]]] = {}
    connection = duckdb.connect(":memory:")
    try:
        connection.execute("SET threads=4")
        _validate_contract_rows(
            checks=checks,
            connection=connection,
            contracts=contracts,
            table_paths=table_paths,
        )
        for table in sorted(table_paths):
            schema_names = {
                tuple(pq.read_schema(path).names) for path in table_paths[table]
            }
            if len(schema_names) != 1:
                continue
            columns = next(iter(schema_names))
            if "raw_file_path" not in columns or "raw_file_sha256" not in columns:
                continue
            rows = connection.execute(
                f"SELECT DISTINCT raw_file_path, raw_file_sha256 "
                f"FROM {_view_name(table)}"
            ).fetchall()
            invalid = sorted(
                [str(path), str(digest)]
                for path, digest in rows
                if (str(path), str(digest)) not in raw_pairs
            )
            if invalid:
                unexpected_raw_pairs[table] = invalid[:20]
        checks.require(
            "provenance.row_raw_assets_in_manifest",
            not unexpected_raw_pairs,
            observed=unexpected_raw_pairs,
            expected={},
        )
        _validate_semantics(
            checks=checks,
            connection=connection,
            table_paths=table_paths,
            manifest=manifest,
            expectations=expectations,
        )
    finally:
        connection.close()

    blockers = expectations.get("known_blockers", [])
    result = {
        "schema_version": 1,
        "gate_id": str(expectations["gate_id"]),
        "status": "pass" if checks.passed else "fail",
        "scope": (
            "qualification_source_subset" if allow_source_subset else "production_full"
        ),
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "staging_root": root.as_posix(),
        "parse_manifest": manifest_path.as_posix(),
        "parse_manifest_sha256": manifest_sha,
        "expectation_config": expectation_path.as_posix(),
        "expectation_config_sha256": sha256_file(expectation_path),
        "sources": observed_sources,
        "counts": {
            "datasets": len(observed_rows),
            "parquet_files": len(actual_parquet_paths),
            "parquet_rows_across_tables": total_manifest_rows,
            "parquet_bytes": total_manifest_bytes,
        },
        "check_counts": checks.counts(),
        "checks": checks.records,
        "known_blockers": blockers,
        "authorizations": {
            "source_reconciliation": checks.passed,
            "label_construction": False,
            "model_training": False,
        },
    }
    return result


def _write_report(path: Path, report: Mapping[str, Any], project_root: Path) -> None:
    resolved_parent = path.parent.resolve()
    artifact_boundary = (project_root / "artifacts/validation").resolve()
    try:
        resolved_parent.relative_to(artifact_boundary)
    except ValueError as exc:
        raise RuntimeError(
            f"Validation report must be under artifacts/validation: {path}"
        ) from exc
    sidecar = path.with_name(path.name + ".sha256")
    existing = [
        candidate
        for candidate in (path, sidecar)
        if candidate.exists() or candidate.is_symlink()
    ]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite validation output: "
            + ", ".join(candidate.as_posix() for candidate in existing)
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    nonce = uuid.uuid4().hex
    temporary = path.parent / f".{path.name}.incomplete-{nonce}"
    temporary_sidecar = path.parent / f".{sidecar.name}.incomplete-{nonce}"
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    digest = sha256_file(temporary)
    temporary_sidecar.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    temporary.chmod(0o444)
    temporary_sidecar.chmod(0o444)
    temporary.rename(path)
    temporary_sidecar.rename(sidecar)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate immutable primary-source staging Parquet and provenance"
    )
    parser.add_argument("staging_root", type=Path)
    parser.add_argument(
        "--expectations",
        type=Path,
        default=Path("configs/primary_staging_validation_v1.yaml"),
    )
    parser.add_argument(
        "--allow-source-subset",
        action="store_true",
        help="Qualify a nonempty source subset only when the root is named _smoke_*",
    )
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    staging_root = args.staging_root
    if not staging_root.is_absolute():
        staging_root = project_root / staging_root
    expectation_path = args.expectations
    if not expectation_path.is_absolute():
        expectation_path = project_root / expectation_path
    expectation_path = expectation_path.resolve(strict=True)
    report = validate_staging(
        project_root=project_root,
        staging_root=staging_root,
        expectation_path=expectation_path,
        allow_source_subset=args.allow_source_subset,
    )
    if args.report:
        report_path = args.report
        if not report_path.is_absolute():
            report_path = project_root / report_path
        _write_report(report_path, report, project_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
