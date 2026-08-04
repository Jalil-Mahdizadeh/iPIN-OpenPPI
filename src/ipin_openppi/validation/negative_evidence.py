"""Independent fail-closed validation for the conditional negative-evidence audit."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import stat
from typing import Any, Mapping

import duckdb
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import yaml

from ipin_openppi.ingestion.common import (
    git_provenance,
    load_asset_index,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import SchemaContract, load_contract, sha256_file
from ipin_openppi.validation.staging import Checks, _write_report


STAGING_MANIFEST = "STAGING_MANIFEST.json"
CANONICAL_MANIFEST = "AUDIT_MANIFEST.json"
RECORD_LEVEL_REPORT_KEYS = {
    "source_record_id",
    "parent_record_id",
    "mapping_record_id",
    "audit_record_id",
    "evidence_id",
    "intact_evidence_id",
    "overlap_id",
    "source_accession_a",
    "source_accession_b",
    "mapped_uniprot_accession_a",
    "mapped_uniprot_accession_b",
}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def _resolve_inside(
    project_root: Path,
    value: str | Path,
    boundary: Path,
    *,
    strict: bool = True,
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
    return resolved


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _parquet_glob(path: Path) -> str:
    return (path / "*.parquet").as_posix()


def _scalar(connection: duckdb.DuckDBPyConnection, sql: str) -> int:
    row = connection.execute(sql).fetchone()
    return 0 if row is None or row[0] is None else int(row[0])


def _column_counts(
    connection: duckdb.DuckDBPyConnection, view: str, column: str
) -> dict[str, int]:
    rows = connection.execute(
        f"SELECT {column}, count(*)::BIGINT FROM {view} GROUP BY {column} ORDER BY {column}"
    ).fetchall()
    return {str(key): int(count) for key, count in rows}


def contains_record_level_report_keys(value: Any) -> bool:
    """Return true when an aggregate report embeds prohibited record-level fields."""
    if isinstance(value, Mapping):
        if any(str(key) in RECORD_LEVEL_REPORT_KEYS for key in value):
            return True
        return any(contains_record_level_report_keys(child) for child in value.values())
    if isinstance(value, list):
        return any(contains_record_level_report_keys(child) for child in value)
    return False


def recompute_subset_metrics(
    rows_by_dataset: Mapping[str, list[tuple[str, str, str, str]]],
) -> dict[str, Any]:
    """Independently characterize raw and boundary-normalized stringent subsets."""
    result: dict[str, Any] = {"datasets": {}}
    for parent_name in ("manual", "pdb"):
        stringent_name = f"{parent_name}_stringent"
        parent_raw = Counter(rows_by_dataset[parent_name])
        stringent_raw = Counter(rows_by_dataset[stringent_name])
        normalize = lambda row: tuple(value.strip() for value in row)
        parent_normalized = Counter(
            normalize(row) for row in rows_by_dataset[parent_name]
        )
        stringent_normalized = Counter(
            normalize(row) for row in rows_by_dataset[stringent_name]
        )
        raw_excess = sum((stringent_raw - parent_raw).values())
        normalized_excess = sum((stringent_normalized - parent_normalized).values())
        result["datasets"][parent_name] = {
            "parent_rows": len(rows_by_dataset[parent_name]),
            "stringent_rows": len(rows_by_dataset[stringent_name]),
            "parent_unique_normalized_rows": len(parent_normalized),
            "stringent_unique_normalized_rows": len(stringent_normalized),
            "parent_duplicate_rows": len(rows_by_dataset[parent_name])
            - len(parent_normalized),
            "stringent_duplicate_rows": len(rows_by_dataset[stringent_name])
            - len(stringent_normalized),
            "stringent_normalized_multiset_subset": normalized_excess == 0,
            "normalization": "strip_boundary_whitespace_per_field_only",
            "stringent_raw_exact_multiset_subset": raw_excess == 0,
            "stringent_raw_exact_excess_rows": raw_excess,
        }
    result["physical_source_rows"] = sum(len(rows) for rows in rows_by_dataset.values())
    result["canonical_parent_records"] = sum(
        len(rows_by_dataset[name]) for name in ("manual", "pdb")
    )
    return result


def _read_raw_rows(path: Path, dataset: str) -> list[tuple[str, str, str, str]]:
    with path.open("rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if dataset.startswith("pdb"):
        expected = ["#ProteinA", "ProteinB", "PDB_Code", "evidence"]
        if not rows or rows[0] != expected:
            raise RuntimeError(f"Unexpected Negatome PDB header: {path}")
        rows = rows[1:]
    if any(len(row) != 4 or any(value == "" for value in row) for row in rows):
        raise RuntimeError(f"Malformed Negatome source row: {path}")
    return [tuple(str(value) for value in row) for row in rows]  # type: ignore[return-value]


def _validate_inventory(
    *,
    checks: Checks,
    project_root: Path,
    root: Path,
    manifest: Mapping[str, Any],
    manifest_name: str,
    contract: SchemaContract,
    expected_rows: Mapping[str, Any],
) -> tuple[dict[str, list[Path]], dict[str, int]]:
    manifest_path = root / manifest_name
    digest = sha256_file(manifest_path)
    sidecar = root / f"{manifest_name}.sha256"
    tokens = sidecar.read_text(encoding="utf-8").split()
    checks.require(
        f"inventory.{root.name}.manifest_sidecar",
        tokens == [digest, manifest_name],
        observed={
            "sha256_matches": bool(tokens and tokens[0] == digest),
            "tokens": len(tokens),
        },
        expected={"sha256_matches": True, "tokens": 2},
    )
    expected = {str(key): int(value) for key, value in expected_rows.items()}
    observed_tables = set(manifest.get("tables", {}))
    checks.require(
        f"inventory.{root.name}.table_set",
        observed_tables == set(expected),
        observed=sorted(observed_tables),
        expected=sorted(expected),
    )
    table_paths: dict[str, list[Path]] = {}
    declared_paths: set[Path] = set()
    errors = 0
    total_rows = 0
    total_bytes = 0
    for table in sorted(observed_tables & set(expected)):
        summary = manifest["tables"][table]
        files = list(summary.get("files", []))
        paths: list[Path] = []
        file_rows = 0
        for index, record in enumerate(files):
            candidate = Path(str(record.get("path")))
            if not candidate.is_absolute():
                candidate = project_root / candidate
            try:
                path = candidate.resolve(strict=True)
                path.relative_to(root)
                if (
                    path.parent != root / table
                    or path.name != f"part-{index:05d}.parquet"
                ):
                    raise ValueError("Parquet path or part name differs")
                info = path.stat(follow_symlinks=False)
                parquet_rows = int(pq.ParquetFile(path).metadata.num_rows)
                observed_file = (info.st_size, parquet_rows, sha256_file(path))
                expected_file = (
                    int(record["bytes"]),
                    int(record["rows"]),
                    str(record["sha256"]),
                )
                observed_schema = pq.read_schema(path)
                expected_schema = contract.arrow_schema(table)
                expected_metadata = dict(expected_schema.metadata or {})
                expected_metadata.update(
                    {
                        b"ipin.audit_version": str(manifest["audit_version"]).encode(),
                        b"ipin.audit_git_commit": str(
                            manifest["git"]["commit"]
                        ).encode(),
                        b"ipin.container_sif_sha256": str(
                            manifest["runtime"]["container_sif_sha256"]
                        ).encode(),
                        b"ipin.redistribution": (
                            b"internal_only_no_negatome_record_level_release"
                        ),
                    }
                )
                schema_ok = (
                    observed_schema.remove_metadata().equals(
                        expected_schema.remove_metadata()
                    )
                    and dict(observed_schema.metadata or {}) == expected_metadata
                )
                if (
                    path.is_symlink()
                    or not stat.S_ISREG(info.st_mode)
                    or info.st_mode & 0o222
                    or observed_file != expected_file
                    or not schema_ok
                    or path in declared_paths
                ):
                    errors += 1
                paths.append(path)
                declared_paths.add(path)
                file_rows += parquet_rows
                total_rows += parquet_rows
                total_bytes += info.st_size
            except (FileNotFoundError, ValueError, KeyError):
                errors += 1
        summary_ok = (
            summary.get("table") == table
            and int(summary.get("rows", -1)) == expected[table] == file_rows
            and int(summary.get("parts", -1)) == len(files)
            and summary.get("schema_name") == contract.name
            and int(summary.get("schema_version", -1)) == contract.version
            and summary.get("schema_sha256") == contract.sha256
        )
        if not summary_ok:
            errors += 1
        table_paths[table] = paths
    actual_paths = {path.resolve() for path in root.rglob("*.parquet")}
    if actual_paths != declared_paths:
        errors += 1
    allowed_files = {manifest_path.resolve(), sidecar.resolve(), *actual_paths}
    for path in (root, *sorted(root.rglob("*"))):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_mode & 0o222:
            errors += 1
        if stat.S_ISREG(info.st_mode) and path.resolve() not in allowed_files:
            errors += 1
    checks.require(
        f"inventory.{root.name}.hash_schema_immutability",
        errors == 0,
        observed={"error_count": errors, "parquet_files": len(actual_paths)},
        expected={"error_count": 0, "parquet_files": len(declared_paths)},
    )
    return table_paths, {
        "tables": len(table_paths),
        "parquet_files": len(actual_paths),
        "rows": total_rows,
        "bytes": total_bytes,
    }


def _validate_raw_fidelity(
    *,
    checks: Checks,
    project_root: Path,
    audit_config: Mapping[str, Any],
    staging_root: Path,
    staging_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    acquisition_path = project_root / str(
        audit_config["inputs"]["negative_acquisition_manifest"]
    )
    _, assets = load_asset_index(
        project_root, acquisition_path.relative_to(project_root)
    )
    raw_rows: dict[str, list[tuple[str, str, str, str]]] = {}
    asset_by_dataset: dict[str, Any] = {}
    for dataset, asset_id in audit_config["raw_assets"].items():
        asset = assets[str(asset_id)]
        asset_by_dataset[str(dataset)] = asset
        raw_rows[str(dataset)] = _read_raw_rows(asset.path, str(dataset))
    subset = recompute_subset_metrics(raw_rows)
    checks.require(
        "raw.subset_recomputation_matches_manifest",
        subset == staging_manifest.get("subset_validation"),
        observed=subset,
        expected=staging_manifest.get("subset_validation"),
    )

    rows = (
        ds.dataset(staging_root / "negatome_source_records", format="parquet")
        .to_table()
        .to_pylist()
    )
    indexed = {
        (str(row["source_dataset"]), int(row["source_record_ordinal"])): row
        for row in rows
    }
    mismatch_count = len(rows) - len(indexed)
    for dataset, physical_rows in raw_rows.items():
        asset = asset_by_dataset[dataset]
        family = (
            "manual_experimental_negative"
            if dataset.startswith("manual")
            else "structure_derived_noncontact"
        )
        for ordinal, raw in enumerate(physical_rows, start=1):
            row = indexed.get((dataset, ordinal))
            if row is None:
                mismatch_count += 1
                continue
            accession_a, accession_b, field_3, assay_text = raw
            publication_ids = []
            pdb_ids = []
            if dataset.startswith("manual"):
                publication_ids = [
                    f"pubmed:{field_3}" if field_3.isdigit() else f"pmc:{field_3}"
                ]
            else:
                pdb_ids = [value.strip().lower() for value in field_3.split(",")]
            expected_locator = (
                f"line:{ordinal + (1 if dataset.startswith('pdb') else 0)}"
            )
            try:
                source_fields = json.loads(str(row["source_fields_json"]))
            except (TypeError, ValueError):
                source_fields = {}
            comparisons = (
                row["source_accession_a"] == accession_a,
                row["source_accession_b"] == accession_b,
                row["assay_text"] == assay_text,
                list(row["publication_ids"]) == publication_ids,
                list(row["pdb_ids"]) == pdb_ids,
                row["evidence_family"] == family,
                bool(row["stringent_file"]) == dataset.endswith("_stringent"),
                row["raw_file_path"] == asset.relative_path,
                row["raw_file_sha256"] == asset.sha256,
                row["raw_locator"] == expected_locator,
                source_fields.get("field_3") == field_3,
            )
            mismatch_count += int(not all(comparisons))
    checks.require(
        "raw.every_physical_row_preserved_exactly",
        mismatch_count == 0,
        observed={"mismatch_count": mismatch_count, "rows": len(rows)},
        expected={"mismatch_count": 0, "rows": subset["physical_source_rows"]},
    )
    return subset


def _register_views(
    connection: duckdb.DuckDBPyConnection,
    *,
    project_root: Path,
    audit_config: Mapping[str, Any],
    staging_root: Path,
    canonical_root: Path,
) -> None:
    local = {
        "n_source": staging_root / "negatome_source_records",
        "n_map": canonical_root / "negatome_participant_mappings",
        "n_audit": canonical_root / "negatome_record_audit",
        "i_audit": canonical_root / "intact_negative_record_audit",
        "n_i_overlap": canonical_root / "negatome_intact_negative_overlaps",
    }
    upstream_names = {
        "u_sequences": "protein_sequences",
        "u_identifiers": "identifier_mappings",
        "u_huri_evidence": "huri_evidence",
        "u_huri_pairs": "huri_pair_views",
        "u_intact_evidence": "intact_evidence",
        "u_intact_participants": "intact_participants",
        "u_participant_map": "participant_sequence_mappings",
        "u_evidence_summary": "evidence_mapping_summaries",
    }
    for view, path in local.items():
        connection.execute(
            f"CREATE TEMP VIEW {view} AS SELECT * FROM read_parquet("
            f"{_sql_string(_parquet_glob(path))})"
        )
    for view, config_name in upstream_names.items():
        path = project_root / str(audit_config["inputs"]["paths"][config_name])
        connection.execute(
            f"CREATE TEMP VIEW {view} AS SELECT * FROM read_parquet("
            f"{_sql_string(_parquet_glob(path))})"
        )
    connection.execute(
        "CREATE TEMP VIEW u_evidence AS SELECT * FROM u_huri_evidence "
        "UNION ALL BY NAME SELECT * FROM u_intact_evidence"
    )


def _validate_contract_and_core_semantics(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    contract: SchemaContract,
) -> None:
    view_for_table = {
        "negatome_source_records": "n_source",
        "negatome_participant_mappings": "n_map",
        "negatome_record_audit": "n_audit",
        "intact_negative_record_audit": "i_audit",
        "negatome_intact_negative_overlaps": "n_i_overlap",
    }
    for table, view in view_for_table.items():
        spec = contract.table_spec(table)
        required = [str(value) for value in spec.get("required_non_null", [])]
        null_sql = " OR ".join(f'"{column}" IS NULL' for column in required) or "false"
        checks.require(
            f"schema.{table}.required_non_null",
            _scalar(connection, f"SELECT count(*) FROM {view} WHERE {null_sql}") == 0,
            observed=_scalar(
                connection, f"SELECT count(*) FROM {view} WHERE {null_sql}"
            ),
            expected=0,
        )
        for column, enum_name in spec.get("enum_columns", {}).items():
            allowed = ",".join(
                _sql_string(str(value))
                for value in contract.document["enums"][enum_name]
            )
            invalid = _scalar(
                connection,
                f'SELECT count(*) FROM {view} WHERE "{column}" IS NOT NULL '
                f'AND "{column}" NOT IN ({allowed})',
            )
            checks.require(
                f"schema.{table}.{column}.enum",
                invalid == 0,
                observed=invalid,
                expected=0,
            )

    universal = sum(
        _scalar(
            connection,
            f"SELECT count(*) FROM {view} WHERE universal_nonbinding_asserted",
        )
        for view in view_for_table.values()
    )
    labels = sum(
        _scalar(connection, f"SELECT count(*) FROM {view} WHERE label_authorized")
        for view in view_for_table.values()
    )
    checks.require(
        "semantics.no_universal_nonbinding_or_label_rows",
        universal == 0 and labels == 0,
        observed={"universal": universal, "labels": labels},
        expected={"universal": 0, "labels": 0},
    )
    duplicate_ids = {
        "source": _scalar(
            connection, "SELECT count(*)-count(DISTINCT source_record_id) FROM n_source"
        ),
        "mapping": _scalar(
            connection, "SELECT count(*)-count(DISTINCT mapping_record_id) FROM n_map"
        ),
        "negatome_audit": _scalar(
            connection, "SELECT count(*)-count(DISTINCT audit_record_id) FROM n_audit"
        ),
        "intact_audit": _scalar(
            connection, "SELECT count(*)-count(DISTINCT audit_record_id) FROM i_audit"
        ),
        "overlap": _scalar(
            connection, "SELECT count(*)-count(DISTINCT overlap_id) FROM n_i_overlap"
        ),
    }
    checks.require(
        "semantics.primary_ids_unique",
        not any(duplicate_ids.values()),
        observed=duplicate_ids,
        expected={key: 0 for key in duplicate_ids},
    )

    mapping_cardinality = _scalar(
        connection,
        """
        SELECT count(*) FROM (
          SELECT parent_record_id
          FROM n_map
          GROUP BY parent_record_id
          HAVING count(*) <> 2
             OR count_if(participant_ordinal = 1) <> 1
             OR count_if(participant_ordinal = 2) <> 1
        )
        """,
    )
    checks.require(
        "semantics.exactly_two_mappings_per_parent",
        mapping_cardinality == 0,
        observed=mapping_cardinality,
        expected=0,
    )
    connection.execute(
        """
        CREATE TEMP VIEW n_map_pair AS
        SELECT
          parent_record_id,
          count_if(reference_sequence_usable) AS usable_count,
          max(CASE WHEN participant_ordinal=1 THEN source_accession END) AS source_a,
          max(CASE WHEN participant_ordinal=2 THEN source_accession END) AS source_b,
          max(CASE WHEN participant_ordinal=1 THEN mapping_state END) AS state_a,
          max(CASE WHEN participant_ordinal=2 THEN mapping_state END) AS state_b,
          max(CASE WHEN participant_ordinal=1 THEN mapping_confidence END) AS confidence_a,
          max(CASE WHEN participant_ordinal=2 THEN mapping_confidence END) AS confidence_b,
          max(CASE WHEN participant_ordinal=1 THEN mapped_sequence_sha256 END) AS hash_a,
          max(CASE WHEN participant_ordinal=2 THEN mapped_sequence_sha256 END) AS hash_b
        FROM n_map GROUP BY parent_record_id
        """
    )
    pair_mismatch = _scalar(
        connection,
        """
        SELECT count(*)
        FROM n_audit AS a JOIN n_map_pair AS m USING(parent_record_id)
        WHERE a.source_accession_a <> m.source_a OR a.source_accession_b <> m.source_b
           OR a.mapping_state_a <> m.state_a OR a.mapping_state_b <> m.state_b
           OR a.mapping_confidence_a <> m.confidence_a
           OR a.mapping_confidence_b <> m.confidence_b
           OR a.mapped_sequence_sha256_a IS DISTINCT FROM m.hash_a
           OR a.mapped_sequence_sha256_b IS DISTINCT FROM m.hash_b
           OR a.reference_pair_usable <> (m.usable_count=2)
           OR a.pair_mapping_state <> CASE m.usable_count
                WHEN 2 THEN 'both_unique_human'
                WHEN 1 THEN 'one_unique_human'
                ELSE 'neither_unique_human' END
        """,
    )
    checks.require(
        "mapping.parent_audit_matches_participant_mappings",
        pair_mismatch == 0,
        observed=pair_mismatch,
        expected=0,
    )
    reference_mismatch = _scalar(
        connection,
        """
        SELECT count(*) FROM n_map AS m
        LEFT JOIN u_sequences AS s
          ON s.protein_sequence_id=m.mapped_sequence_id
         AND s.sequence_sha256=m.mapped_sequence_sha256
         AND s.uniprot_accession=m.mapped_uniprot_accession
        WHERE (m.reference_sequence_usable AND (
                 s.protein_sequence_id IS NULL OR m.mapping_candidate_count<>1
                 OR m.mapped_taxid<>9606 OR m.frozen_uniprot_release<>'2026_02'
                 OR NOT m.exact_unique_mapping
                 OR m.construct_confidence<>'D_reference_only_no_source_construct'))
           OR (NOT m.reference_sequence_usable AND (
                 m.mapped_sequence_id IS NOT NULL OR m.mapped_sequence_sha256 IS NOT NULL
                 OR m.mapped_uniprot_accession IS NOT NULL OR m.exact_unique_mapping))
           OR m.mapping_candidate_count<>len(m.candidate_sequence_ids)
        """,
    )
    checks.require(
        "mapping.frozen_reference_and_uncertainty_consistency",
        reference_mismatch == 0,
        observed=reference_mismatch,
        expected=0,
    )
    family_mismatch = _scalar(
        connection,
        """
        SELECT count(*) FROM n_audit
        WHERE construct_a_json IS NOT NULL OR construct_b_json IS NOT NULL
           OR orientation_a IS NOT NULL OR orientation_b IS NOT NULL
           OR source_taxid_a IS NOT NULL OR source_taxid_b IS NOT NULL
           OR source_species_name_a IS NOT NULL OR source_species_name_b IS NOT NULL
           OR experimental_conditions_json IS NOT NULL
           OR (evidence_family='manual_experimental_negative' AND
               (len(publication_ids)<>1 OR len(pdb_ids)<>0
                OR observation_state<>'source_asserted_conditional_negative'))
           OR (evidence_family='structure_derived_noncontact' AND
               (len(publication_ids)<>0 OR len(pdb_ids)=0
                OR observation_state<>'structure_derived_noncontact'))
        """,
    )
    checks.require(
        "provenance.families_separate_and_missing_fields_not_imputed",
        family_mismatch == 0,
        observed=family_mismatch,
        expected=0,
    )


def _build_independent_positive_index(
    connection: duckdb.DuckDBPyConnection,
    audit_config: Mapping[str, Any],
) -> dict[str, Any]:
    connection.execute(
        """
        CREATE TEMP TABLE v_positive_records AS
        WITH mapped AS (
          SELECT evidence_id, source_key,
                 min(mapped_sequence_sha256) AS hash_a,
                 max(mapped_sequence_sha256) AS hash_b,
                 count(*) AS participant_rows
          FROM u_participant_map
          WHERE reference_sequence_usable
          GROUP BY evidence_id, source_key
        )
        SELECT m.hash_a, m.hash_b, e.evidence_id, e.source_key, e.source_dataset,
               e.interaction_semantics, e.detection_method_ac, e.detection_method_name
        FROM mapped AS m
        JOIN u_evidence AS e USING(evidence_id, source_key)
        JOIN u_evidence_summary AS s USING(evidence_id, source_key)
        WHERE m.participant_rows=2 AND s.reference_pair_usable
          AND e.observation_state='positive' AND e.participant_count=2
          AND NOT e.original_nary AND NOT e.is_expanded_projection
        """
    )
    connection.execute(
        """
        CREATE TEMP VIEW v_positive_record_agg AS
        SELECT hash_a, hash_b,
               count(*)::BIGINT AS evidence_count,
               count_if(interaction_semantics='direct_binary')::BIGINT AS direct_count,
               count_if(source_key='intact_imex' AND
                        interaction_semantics<>'direct_binary')::BIGINT AS broader_count
        FROM v_positive_records GROUP BY hash_a, hash_b
        """
    )
    permitted = sorted(
        str(value)
        for value in audit_config["positive_conflict_policy"]["permitted_pair_views"]
    )
    allowed = ",".join(_sql_string(value) for value in permitted)
    connection.execute(
        """
        CREATE TEMP TABLE v_unique_gene_sequence AS
        WITH candidates AS (
          SELECT i.identifier_versionless AS gene_id, s.sequence_sha256
          FROM u_identifiers AS i JOIN u_sequences AS s
            ON s.uniprot_accession=i.uniprot_accession AND s.canonical
          WHERE i.database='Ensembl'
        )
        SELECT gene_id, min(sequence_sha256) AS sequence_sha256
        FROM candidates GROUP BY gene_id
        HAVING count(DISTINCT sequence_sha256)=1
        """
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE v_positive_pair_views AS
        SELECT least(a.sequence_sha256,b.sequence_sha256) AS hash_a,
               greatest(a.sequence_sha256,b.sequence_sha256) AS hash_b,
               p.source_dataset
        FROM u_huri_pairs AS p
        JOIN v_unique_gene_sequence AS a ON a.gene_id=p.member_a
        JOIN v_unique_gene_sequence AS b ON b.gene_id=p.member_b
        WHERE p.view_membership AND p.source_dataset IN ({allowed})
        """
    )
    connection.execute(
        """
        CREATE TEMP VIEW v_positive_pair_view_agg AS
        SELECT hash_a, hash_b, count(*)::BIGINT AS view_count
        FROM v_positive_pair_views GROUP BY hash_a, hash_b
        """
    )
    connection.execute(
        """
        CREATE TEMP VIEW v_audit_positive AS
        SELECT a.*,
               coalesce(r.direct_count,0)::BIGINT AS expected_direct,
               coalesce(r.broader_count,0)::BIGINT AS expected_broader,
               coalesce(v.view_count,0)::BIGINT AS expected_pair_view,
               (coalesce(r.direct_count,0)+coalesce(v.view_count,0)>0) AS expected_cf_d,
               (coalesce(r.broader_count,0)>0) AS expected_cf_b
        FROM n_audit AS a
        LEFT JOIN v_positive_record_agg AS r
          ON a.reference_pair_usable
         AND r.hash_a=least(a.mapped_sequence_sha256_a,a.mapped_sequence_sha256_b)
         AND r.hash_b=greatest(a.mapped_sequence_sha256_a,a.mapped_sequence_sha256_b)
        LEFT JOIN v_positive_pair_view_agg AS v
          ON a.reference_pair_usable
         AND v.hash_a=least(a.mapped_sequence_sha256_a,a.mapped_sequence_sha256_b)
         AND v.hash_b=greatest(a.mapped_sequence_sha256_a,a.mapped_sequence_sha256_b)
        """
    )
    mismatches = _scalar(
        connection,
        """
        SELECT count(*) FROM v_audit_positive
        WHERE qualifying_direct_positive_evidence_count<>expected_direct
           OR broader_intact_positive_evidence_count<>expected_broader
           OR permitted_positive_pair_view_count<>expected_pair_view
           OR positive_check_performed<>reference_pair_usable
           OR current_positive_conflict<>(expected_cf_d OR expected_cf_b)
           OR list_contains(positive_conflict_overlays,'CF')<>(expected_cf_d OR expected_cf_b)
           OR list_contains(positive_conflict_overlays,'CF-D')<>expected_cf_d
           OR list_contains(positive_conflict_overlays,'CF-B')<>expected_cf_b
           OR len(positive_conflict_overlays)<>
              cast(expected_cf_d OR expected_cf_b AS INTEGER)
              +cast(expected_cf_d AS INTEGER)+cast(expected_cf_b AS INTEGER)
           OR ((expected_cf_d OR expected_cf_b) AND
               (len(positive_source_keys)=0 OR len(positive_source_datasets)=0
                OR len(positive_interaction_semantics)=0
                OR len(positive_detection_methods)=0))
        """,
    )
    unique_record_pairs = _scalar(
        connection, "SELECT count(*) FROM v_positive_record_agg"
    )
    unique_view_pairs = _scalar(
        connection, "SELECT count(*) FROM v_positive_pair_view_agg"
    )
    combined_pairs = _scalar(
        connection,
        """
        SELECT count(*) FROM (
          SELECT hash_a,hash_b FROM v_positive_record_agg
          UNION SELECT hash_a,hash_b FROM v_positive_pair_view_agg
        )
        """,
    )
    return {
        "mismatch_count": mismatches,
        "metrics": {
            "mapped_positive_evidence_rows": _scalar(
                connection, "SELECT count(*) FROM v_positive_records"
            ),
            "mapped_positive_evidence_unique_pairs": unique_record_pairs,
            "mapped_permitted_pair_view_rows": _scalar(
                connection, "SELECT count(*) FROM v_positive_pair_views"
            ),
            "mapped_permitted_pair_view_unique_pairs": unique_view_pairs,
            "combined_positive_index_unique_pairs": combined_pairs,
            "permitted_pair_views": permitted,
        },
    }


def _validate_intact_and_overlap(
    checks: Checks, connection: duckdb.DuckDBPyConnection
) -> dict[str, int]:
    intact_set_mismatch = _scalar(
        connection,
        """
        SELECT count(*) FROM (
          (SELECT evidence_id FROM u_intact_evidence WHERE observation_state='negative'
           EXCEPT SELECT evidence_id FROM i_audit)
          UNION ALL
          (SELECT evidence_id FROM i_audit
           EXCEPT SELECT evidence_id FROM u_intact_evidence WHERE observation_state='negative')
        )
        """,
    )
    intact_metadata_mismatch = _scalar(
        connection,
        """
        SELECT count(*) FROM i_audit AS a JOIN u_intact_evidence AS e USING(evidence_id)
        WHERE e.observation_state<>'negative'
           OR a.source_record_id<>e.source_record_id
           OR a.publication_ids<>e.publication_ids
           OR a.participant_count<>e.participant_count
           OR a.original_nary<>e.original_nary
           OR a.interaction_semantics<>e.interaction_semantics
           OR a.detection_method_ac IS DISTINCT FROM e.detection_method_ac
           OR a.detection_method_name IS DISTINCT FROM e.detection_method_name
           OR a.host_taxid IS DISTINCT FROM e.host_taxid
           OR a.attempted_state<>e.attempted_state
           OR a.evaluability_state<>e.evaluability_state
           OR a.technical_state<>e.technical_state
           OR a.observation_state<>e.observation_state
           OR a.orientation_semantics<>e.orientation_semantics
           OR a.context_json<>e.context_json OR a.missingness_json<>e.missingness_json
        """,
    )
    checks.require(
        "intact.all_939_negative_records_and_provenance_exact",
        intact_set_mismatch == 0 and intact_metadata_mismatch == 0,
        observed={
            "set_mismatch": intact_set_mismatch,
            "metadata_mismatch": intact_metadata_mismatch,
        },
        expected={"set_mismatch": 0, "metadata_mismatch": 0},
    )
    connection.execute(
        """
        CREATE TEMP VIEW v_intact_negative_source_pairs AS
        SELECT p.evidence_id,
               max(CASE WHEN p.participant_ordinal=1 THEN p.primary_identifier END) AS ordered_a,
               max(CASE WHEN p.participant_ordinal=2 THEN p.primary_identifier END) AS ordered_b
        FROM u_intact_participants AS p
        JOIN u_intact_evidence AS e USING(evidence_id)
        WHERE e.observation_state='negative'
        GROUP BY p.evidence_id
        HAVING count(*)=2
           AND count_if(lower(coalesce(p.primary_identifier_db,''))
                        NOT IN ('uniprot','uniprotkb'))=0
           AND count_if(p.primary_identifier IS NULL)=0
        """
    )
    connection.execute(
        """
        CREATE TEMP VIEW v_expected_source_overlap AS
        SELECT n.parent_record_id, i.evidence_id,
               (n.source_accession_a=i.ordered_a AND n.source_accession_b=i.ordered_b)
                 AS exact_ordered,
               true AS exact_unordered
        FROM n_audit AS n JOIN v_intact_negative_source_pairs AS i
          ON least(n.source_accession_a,n.source_accession_b)=least(i.ordered_a,i.ordered_b)
         AND greatest(n.source_accession_a,n.source_accession_b)=greatest(i.ordered_a,i.ordered_b)
        """
    )
    connection.execute(
        """
        CREATE TEMP VIEW v_expected_sequence_overlap AS
        SELECT n.parent_record_id, i.evidence_id
        FROM n_audit AS n JOIN i_audit AS i
          ON n.mapped_unordered_sequence_pair_id=i.mapped_unordered_sequence_pair_id
        WHERE n.reference_pair_usable AND i.reference_pair_usable
        """
    )
    connection.execute(
        """
        CREATE TEMP VIEW v_expected_overlap AS
        SELECT parent_record_id,evidence_id FROM v_expected_source_overlap
        UNION SELECT parent_record_id,evidence_id FROM v_expected_sequence_overlap
        """
    )
    missing_or_excess = _scalar(
        connection,
        """
        SELECT count(*) FROM (
          (SELECT parent_record_id,evidence_id AS intact_evidence_id FROM v_expected_overlap
           EXCEPT SELECT parent_record_id,intact_evidence_id FROM n_i_overlap)
          UNION ALL
          (SELECT parent_record_id,intact_evidence_id FROM n_i_overlap
           EXCEPT SELECT parent_record_id,evidence_id FROM v_expected_overlap)
        )
        """,
    )
    expected_links = _scalar(connection, "SELECT count(*) FROM v_expected_overlap")
    stored_link_sums = _scalar(
        connection,
        "SELECT sum(intact_negative_overlap_count) FROM n_audit",
    ) + _scalar(connection, "SELECT sum(negatome_overlap_count) FROM i_audit")
    checks.require(
        "overlap.exact_source_and_frozen_pair_recomputation",
        missing_or_excess == 0
        and expected_links == _scalar(connection, "SELECT count(*) FROM n_i_overlap")
        and stored_link_sums == 2 * expected_links,
        observed={
            "expected_links": expected_links,
            "output_links": _scalar(connection, "SELECT count(*) FROM n_i_overlap"),
            "set_mismatch": missing_or_excess,
            "stored_bidirectional_link_sum": stored_link_sums,
        },
        expected={
            "expected_links": expected_links,
            "output_links": expected_links,
            "set_mismatch": 0,
            "stored_bidirectional_link_sum": 2 * expected_links,
        },
    )
    return {
        "cross_source_link_count": expected_links,
        "negatome_parent_records_with_overlap": _scalar(
            connection,
            "SELECT count(DISTINCT parent_record_id) FROM v_expected_overlap",
        ),
        "intact_negative_records_with_overlap": _scalar(
            connection, "SELECT count(DISTINCT evidence_id) FROM v_expected_overlap"
        ),
        "exact_ordered_source_links": _scalar(
            connection,
            "SELECT count(*) FROM v_expected_source_overlap WHERE exact_ordered",
        ),
        "exact_unordered_source_links": _scalar(
            connection, "SELECT count(*) FROM v_expected_source_overlap"
        ),
        "frozen_sequence_pair_links": _scalar(
            connection, "SELECT count(*) FROM v_expected_sequence_overlap"
        ),
    }


def _validate_tiers(checks: Checks, connection: duckdb.DuckDBPyConnection) -> None:
    mismatch = _scalar(
        connection,
        """
        SELECT count(*) FROM v_audit_positive
        WHERE reliability_tier<>CASE
            WHEN NOT reference_pair_usable THEN 'MX'
            WHEN evidence_family='manual_experimental_negative'
                 AND stringent_member AND NOT expected_cf_d THEN 'ME-1'
            WHEN evidence_family='manual_experimental_negative' THEN 'ME-2'
            WHEN evidence_family='structure_derived_noncontact' AND stringent_member THEN 'SN-1'
            ELSE 'SN-2' END
           OR permitted_role<>CASE
            WHEN expected_cf_d OR expected_cf_b
              THEN 'explicit_conflict_stratum_no_negative_label_or_training_use'
            WHEN reliability_tier='ME-1'
              THEN 'conditional_source_scoped_diagnostic_candidate_only'
            WHEN reliability_tier='ME-2'
              THEN 'conditional_descriptive_or_sensitivity_evidence_only'
            WHEN reliability_tier='SN-1'
              THEN 'structure_context_noncontact_diagnostic_only'
            WHEN reliability_tier='SN-2'
              THEN 'descriptive_structure_context_noncontact_only'
            ELSE 'outside_primary_human_sequence_scope_retain_for_audit' END
        """,
    )
    checks.require(
        "classification.tiers_and_permitted_roles_recomputed",
        mismatch == 0,
        observed=mismatch,
        expected=0,
    )


def _collect_metrics(
    connection: duckdb.DuckDBPyConnection,
    positive_metrics: Mapping[str, Any],
    overlap_metrics: Mapping[str, int],
) -> dict[str, Any]:
    source_rows = _column_counts(connection, "n_source", "source_dataset")
    families = _column_counts(connection, "n_audit", "evidence_family")
    mapped_family = {
        str(key): int(count)
        for key, count in connection.execute(
            "SELECT evidence_family,count(*) FROM n_audit WHERE reference_pair_usable "
            "GROUP BY evidence_family ORDER BY evidence_family"
        ).fetchall()
    }
    return {
        "source_rows": source_rows,
        "source_row_total": _scalar(connection, "SELECT count(*) FROM n_source"),
        "parent_record_total": _scalar(connection, "SELECT count(*) FROM n_audit"),
        "parent_records_by_family": families,
        "participant_mapping_rows": _scalar(connection, "SELECT count(*) FROM n_map"),
        "participant_mapping_states": _column_counts(
            connection, "n_map", "mapping_state"
        ),
        "participant_mapping_confidences": _column_counts(
            connection, "n_map", "mapping_confidence"
        ),
        "parent_pair_mapping_states": _column_counts(
            connection, "n_audit", "pair_mapping_state"
        ),
        "mapped_parent_records_by_family": mapped_family,
        "reliability_tiers": _column_counts(connection, "n_audit", "reliability_tier"),
        "positive_conflicts": {
            "any_current_positive": _scalar(
                connection,
                "SELECT count(*) FROM n_audit WHERE current_positive_conflict",
            ),
            "direct_CF_D": _scalar(
                connection,
                "SELECT count(*) FROM n_audit WHERE list_contains(positive_conflict_overlays,'CF-D')",
            ),
            "broader_CF_B": _scalar(
                connection,
                "SELECT count(*) FROM n_audit WHERE list_contains(positive_conflict_overlays,'CF-B')",
            ),
        },
        "positive_index": dict(positive_metrics),
        "intact_negative_records": _scalar(connection, "SELECT count(*) FROM i_audit"),
        "intact_negative_reference_pair_usable_records": _scalar(
            connection, "SELECT count(*) FROM i_audit WHERE reference_pair_usable"
        ),
        "overlap": dict(overlap_metrics),
        "universal_nonbinding_rows": 0,
        "label_authorized_rows": 0,
    }


def _collect_pnu(
    connection: duckdb.DuckDBPyConnection,
    expected: Mapping[str, Any],
    audit_config: Mapping[str, Any],
) -> dict[str, Any]:
    records = _scalar(
        connection,
        """SELECT count(*) FROM n_audit
        WHERE evidence_family='manual_experimental_negative'
          AND reliability_tier='ME-1' AND NOT current_positive_conflict""",
    )
    pairs = _scalar(
        connection,
        """SELECT count(DISTINCT mapped_unordered_sequence_pair_id) FROM n_audit
        WHERE evidence_family='manual_experimental_negative'
          AND reliability_tier='ME-1' AND NOT current_positive_conflict""",
    )
    publications = _scalar(
        connection,
        """SELECT count(DISTINCT publication) FROM n_audit,
        unnest(publication_ids) AS p(publication)
        WHERE evidence_family='manual_experimental_negative'
          AND reliability_tier='ME-1' AND NOT current_positive_conflict""",
    )
    thresholds = audit_config["pnu_feasibility_policy"]
    numerical = records >= int(thresholds["minimum_conditional_records_per_stratum"])
    numerical = numerical and publications >= int(
        thresholds["minimum_independent_publications_per_manual_stratum"]
    )
    result = dict(expected)
    result.update(
        {
            "bounded_manual_conditional_records": records,
            "bounded_manual_conditional_unique_sequence_pairs": pairs,
            "bounded_manual_conditional_publications": publications,
            "bounded_manual_conditional_stratum_numerically_adequate": numerical,
            "conditional_P_plus_N_plus_U_diagnostic_feasible": numerical,
            "intact_negative_records_total": _scalar(
                connection, "SELECT count(*) FROM i_audit"
            ),
            "intact_negative_reference_pair_usable_records": _scalar(
                connection, "SELECT count(*) FROM i_audit WHERE reference_pair_usable"
            ),
        }
    )
    return result


def validate_negative_evidence(
    *,
    project_root: Path,
    canonical_root: Path,
    staging_root: Path,
    audit_report_path: Path,
    expectation_path: Path,
    allow_smoke: bool,
) -> dict[str, Any]:
    require_apptainer()
    expectations = _load_yaml(expectation_path)
    audit_config_path = _resolve_inside(
        project_root, str(expectations["audit_config"]), project_root / "configs"
    )
    schema_path = _resolve_inside(
        project_root, str(expectations["audit_schema"]), project_root / "schemas"
    )
    if sha256_file(audit_config_path) != str(expectations["audit_config_sha256"]):
        raise RuntimeError("Audit configuration SHA-256 differs from validation policy")
    if sha256_file(schema_path) != str(expectations["audit_schema_sha256"]):
        raise RuntimeError("Audit schema SHA-256 differs from validation policy")
    audit_config = _load_yaml(audit_config_path)
    contract = load_contract(schema_path)
    canonical_root = _resolve_inside(
        project_root, canonical_root, project_root / "data/canonical"
    )
    staging_root = _resolve_inside(
        project_root, staging_root, project_root / "data/staging"
    )
    audit_report_path = _resolve_inside(
        project_root, audit_report_path, project_root / "artifacts/validation"
    )
    smoke = all(
        any(part.startswith("_smoke_") for part in path.parts)
        for path in (canonical_root, staging_root, audit_report_path)
    )
    if allow_smoke != smoke:
        raise RuntimeError("--allow-smoke must match consistently named _smoke_ inputs")

    checks = Checks()
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = (
        project_root / str(expectations["runtime"]["container"])
    ).resolve(strict=True)
    runtime_ok = (
        active_container == expected_container
        and sha256_file(active_container) == expectations["runtime"]["container_sha256"]
        and platform.machine() == expectations["runtime"]["architecture"]
    )
    checks.require(
        "runtime.pinned_apptainer_and_architecture",
        runtime_ok,
        observed={
            "container_matches": active_container == expected_container,
            "container_sha256": sha256_file(active_container),
            "architecture": platform.machine(),
        },
        expected={
            "container_matches": True,
            "container_sha256": expectations["runtime"]["container_sha256"],
            "architecture": expectations["runtime"]["architecture"],
        },
    )

    staging_manifest = _load_json(staging_root / STAGING_MANIFEST)
    canonical_manifest = _load_json(canonical_root / CANONICAL_MANIFEST)
    audit_report = _load_json(audit_report_path)
    _, staging_inventory = _validate_inventory(
        checks=checks,
        project_root=project_root,
        root=staging_root,
        manifest=staging_manifest,
        manifest_name=STAGING_MANIFEST,
        contract=contract,
        expected_rows=expectations["expected_table_rows"]["staging"],
    )
    _, canonical_inventory = _validate_inventory(
        checks=checks,
        project_root=project_root,
        root=canonical_root,
        manifest=canonical_manifest,
        manifest_name=CANONICAL_MANIFEST,
        contract=contract,
        expected_rows=expectations["expected_table_rows"]["canonical"],
    )
    required_manifest_values = (
        staging_manifest.get("status") == "complete",
        canonical_manifest.get("status") == "complete",
        staging_manifest.get("record_level_redistribution_authorized") is False,
        canonical_manifest.get("record_level_redistribution_authorized") is False,
        staging_manifest.get("universal_nonbinding_interpretation") is False,
        canonical_manifest.get("universal_nonbinding_interpretation") is False,
        staging_manifest.get("label_construction_performed") is False,
        canonical_manifest.get("label_construction_performed") is False,
        canonical_manifest.get("candidate_pair_materialization_performed") is False,
        canonical_manifest.get("split_construction_performed") is False,
        canonical_manifest.get("model_training_performed") is False,
    )
    checks.require(
        "manifest.scope_and_authorization_fail_closed",
        all(required_manifest_values),
        observed={"all_required_values": all(required_manifest_values)},
        expected={"all_required_values": True},
    )
    current_git = git_provenance(project_root)
    production_git_ok = allow_smoke or (
        canonical_manifest.get("git", {}).get("tracked_worktree_clean") is True
        and staging_manifest.get("git", {}).get("tracked_worktree_clean") is True
    )
    checks.require(
        "manifest.producer_git_commit_and_cleanliness",
        canonical_manifest.get("git", {}).get("commit") == current_git["commit"]
        and staging_manifest.get("git", {}).get("commit") == current_git["commit"]
        and production_git_ok,
        observed={
            "current_commit": current_git["commit"],
            "canonical_commit": canonical_manifest.get("git", {}).get("commit"),
            "staging_commit": staging_manifest.get("git", {}).get("commit"),
            "production_clean": production_git_ok,
        },
        expected={"commits_equal": True, "production_clean": True},
    )
    staging_manifest_sha = sha256_file(staging_root / STAGING_MANIFEST)
    canonical_manifest_sha = sha256_file(canonical_root / CANONICAL_MANIFEST)
    checks.require(
        "report.output_manifest_hashes",
        audit_report.get("outputs", {}).get("staging_manifest_sha256")
        == staging_manifest_sha
        and audit_report.get("outputs", {}).get("canonical_manifest_sha256")
        == canonical_manifest_sha,
        observed={
            "staging_matches": audit_report.get("outputs", {}).get(
                "staging_manifest_sha256"
            )
            == staging_manifest_sha,
            "canonical_matches": audit_report.get("outputs", {}).get(
                "canonical_manifest_sha256"
            )
            == canonical_manifest_sha,
        },
        expected={"staging_matches": True, "canonical_matches": True},
    )

    subset = _validate_raw_fidelity(
        checks=checks,
        project_root=project_root,
        audit_config=audit_config,
        staging_root=staging_root,
        staging_manifest=staging_manifest,
    )
    checks.require(
        "raw.subset_matches_frozen_expectations",
        subset == expectations["expected_subset_validation"],
        observed=subset,
        expected=expectations["expected_subset_validation"],
    )

    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            f"SET memory_limit={_sql_string(str(expectations['runtime']['duckdb_memory_limit']))}"
        )
        connection.execute(
            f"SET threads={int(expectations['runtime']['duckdb_threads'])}"
        )
        connection.execute("PRAGMA disable_progress_bar")
        _register_views(
            connection,
            project_root=project_root,
            audit_config=audit_config,
            staging_root=staging_root,
            canonical_root=canonical_root,
        )
        _validate_contract_and_core_semantics(checks, connection, contract)
        positive = _build_independent_positive_index(connection, audit_config)
        checks.require(
            "positive.current_evidence_recomputation_matches_every_mapped_pair",
            positive["mismatch_count"] == 0,
            observed=positive["mismatch_count"],
            expected=0,
        )
        overlap = _validate_intact_and_overlap(checks, connection)
        _validate_tiers(checks, connection)
        metrics = _collect_metrics(connection, positive["metrics"], overlap)
        pnu = _collect_pnu(
            connection, expectations["expected_pnu_feasibility"], audit_config
        )
    finally:
        connection.close()

    checks.require(
        "metrics.independent_recomputation_matches_frozen_expectations",
        metrics == expectations["expected_metrics"],
        observed=metrics,
        expected=expectations["expected_metrics"],
    )
    checks.require(
        "metrics.manifest_and_audit_report_match_recomputation",
        canonical_manifest.get("metrics") == metrics
        and audit_report.get("metrics") == metrics,
        observed={
            "manifest_matches": canonical_manifest.get("metrics") == metrics,
            "report_matches": audit_report.get("metrics") == metrics,
        },
        expected={"manifest_matches": True, "report_matches": True},
    )
    checks.require(
        "pnu.feasibility_recomputed_and_policy_preserved",
        pnu == expectations["expected_pnu_feasibility"]
        and canonical_manifest.get("pnu_feasibility") == pnu
        and audit_report.get("pnu_feasibility") == pnu,
        observed={
            "computed": pnu,
            "manifest_matches": canonical_manifest.get("pnu_feasibility") == pnu,
            "report_matches": audit_report.get("pnu_feasibility") == pnu,
        },
        expected=expectations["expected_pnu_feasibility"],
    )
    report_policy_ok = (
        audit_report.get("status") == "complete"
        and audit_report.get("license_and_redistribution", {}).get(
            "negatome_payload_license"
        )
        == "not_explicitly_stated"
        and audit_report.get("license_and_redistribution", {}).get(
            "raw_and_record_level_redistribution"
        )
        == "not_authorized"
        and audit_report.get("scientific_conclusion", {}).get(
            "manual_and_structure_noncontact_kept_separate"
        )
        is True
        and audit_report.get("scientific_conclusion", {}).get(
            "universal_nonbinding_interpretation"
        )
        is False
        and audit_report.get("authorizations", {}).get("negative_label_construction")
        is False
        and audit_report.get("authorizations", {}).get("model_training") is False
        and not contains_record_level_report_keys(audit_report)
    )
    checks.require(
        "report.non_extractive_license_and_scientific_scope",
        report_policy_ok,
        observed={"policy_ok": report_policy_ok},
        expected={"policy_ok": True},
    )

    return {
        "schema_version": 1,
        "gate_id": expectations["gate_id"],
        "audit_id": expectations["audit_id"],
        "audit_version": expectations["audit_version"],
        "status": "pass" if checks.passed else "fail",
        "scope": "qualification_smoke" if allow_smoke else "production_full",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_root": canonical_root.as_posix(),
        "canonical_manifest": (canonical_root / CANONICAL_MANIFEST).as_posix(),
        "canonical_manifest_sha256": canonical_manifest_sha,
        "staging_root": staging_root.as_posix(),
        "staging_manifest": (staging_root / STAGING_MANIFEST).as_posix(),
        "staging_manifest_sha256": staging_manifest_sha,
        "audit_report": audit_report_path.as_posix(),
        "audit_report_sha256": sha256_file(audit_report_path),
        "expectation_config": expectation_path.as_posix(),
        "expectation_config_sha256": sha256_file(expectation_path),
        "inventory": {"staging": staging_inventory, "canonical": canonical_inventory},
        "metrics": metrics,
        "pnu_feasibility": pnu,
        "check_counts": checks.counts(),
        "checks": checks.records,
        "interpretation": (
            "Pass validates immutable row fidelity, frozen-reference mapping invariants, "
            "current positive conflicts, all frozen IntAct negatives, exact overlap, and "
            "conditional PNU arithmetic. It does not create universal negative labels or "
            "authorize training."
        ),
        "authorizations": {
            "negative_evidence_audit_accepted": checks.passed,
            "record_level_redistribution": False,
            "negative_label_construction": False,
            "candidate_pair_materialization": False,
            "split_construction": False,
            "model_implementation": False,
            "model_training": False,
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Independently validate the conditional negative-evidence audit"
    )
    parser.add_argument("canonical_root", nargs="?", type=Path)
    parser.add_argument("--staging-root", type=Path)
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument(
        "--expectations",
        type=Path,
        default=Path("configs/negative_evidence_validation_v1.yaml"),
    )
    parser.add_argument("--allow-smoke", action="store_true")
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    expectation_path = args.expectations
    if not expectation_path.is_absolute():
        expectation_path = project_root / expectation_path
    expectation_path = expectation_path.resolve(strict=True)
    expectations = _load_yaml(expectation_path)

    def resolve_argument(value: Path | None, fallback: str) -> Path:
        path = value or Path(fallback)
        return path if path.is_absolute() else project_root / path

    canonical_root = resolve_argument(
        args.canonical_root, str(expectations["production"]["canonical_root"])
    )
    staging_root = resolve_argument(
        args.staging_root, str(expectations["production"]["staging_root"])
    )
    audit_report = resolve_argument(
        args.audit_report, str(expectations["production"]["audit_report"])
    )
    result = validate_negative_evidence(
        project_root=project_root,
        canonical_root=canonical_root,
        staging_root=staging_root,
        audit_report_path=audit_report,
        expectation_path=expectation_path,
        allow_smoke=args.allow_smoke,
    )
    if args.report:
        report_path = args.report
        if not report_path.is_absolute():
            report_path = project_root / report_path
        _write_report(report_path, result, project_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
