"""Independent fail-closed validation of the Lambourne Y2H-v1 audit."""

from __future__ import annotations

import argparse
from collections import Counter
from io import BytesIO
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping
import zipfile

import duckdb
import pandas as pd
import pyarrow.parquet as pq
import yaml

from ipin_openppi.ingestion.common import (
    load_asset_index,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.validation.staging import Checks, _write_report


RECORD_LEVEL_REPORT_KEYS = {
    "panel_pair_id",
    "paper_record_id",
    "mapping_record_id",
    "selection_record_id",
    "preview_record_id",
    "source_accession",
    "uniprot_accession_ad",
    "uniprot_accession_db",
    "intact_negative_evidence_ids",
    "negatome_parent_record_ids",
}


def contains_record_level_report_keys(value: Any) -> bool:
    if isinstance(value, Mapping):
        if any(str(key) in RECORD_LEVEL_REPORT_KEYS for key in value):
            return True
        return any(contains_record_level_report_keys(child) for child in value.values())
    if isinstance(value, list):
        return any(contains_record_level_report_keys(child) for child in value)
    return False


def independent_raw_outcome(score: Any, seq_3at: Any, seq_lw: Any) -> str:
    def tri(value: Any) -> int | None:
        if value is None or pd.isna(value):
            return None
        return int(float(value))

    if score is None or pd.isna(score):
        return "Test failed"
    token = str(score).strip()
    if token.endswith(".0") and token[:-2] in {"0", "1"}:
        token = token[:-2]
    if token == "AA":
        return "Autoactivator"
    if token == "0":
        return "Negative" if tri(seq_lw) == 1 else "Failed sequence confirmation"
    if token == "1":
        return "Positive" if tri(seq_3at) == 1 else "Failed sequence confirmation"
    raise RuntimeError(f"Unexpected independent raw score: {score!r}")


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
    project_root: Path, value: str | Path, boundary: Path, *, strict: bool = True
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


def _validate_dataset(
    *,
    checks: Checks,
    project_root: Path,
    root: Path,
    manifest_name: str,
    expected_tables: set[str],
    contract: Any,
) -> tuple[dict[str, Path], dict[str, Any]]:
    manifest_path = root / manifest_name
    sidecar = root / f"{manifest_name}.sha256"
    manifest = _load_json(manifest_path)
    digest = sha256_file(manifest_path)
    checks.require(
        f"inventory.{root.name}.manifest_sidecar",
        sidecar.read_text(encoding="utf-8").split() == [digest, manifest_name],
        observed={"sha256": digest},
        expected={"sidecar_matches": True},
    )
    observed_tables = set(manifest.get("tables", {}))
    checks.require(
        f"inventory.{root.name}.table_set",
        observed_tables == expected_tables,
        observed=sorted(observed_tables),
        expected=sorted(expected_tables),
    )
    table_roots: dict[str, Path] = {}
    errors = 0
    total_rows = 0
    declared_files: set[Path] = set()
    for table_name in sorted(expected_tables & observed_tables):
        summary = manifest["tables"][table_name]
        table_root = root / table_name
        table_roots[table_name] = table_root
        files = list(summary.get("files", []))
        row_count = 0
        for index, record in enumerate(files):
            path = Path(str(record["path"]))
            if not path.is_absolute():
                path = project_root / path
            try:
                path = path.resolve(strict=True)
                path.relative_to(table_root)
                info = path.stat(follow_symlinks=False)
                rows = int(pq.ParquetFile(path).metadata.num_rows)
                base_schema = pq.read_schema(path).remove_metadata()
                expected_schema = contract.arrow_schema(table_name).remove_metadata()
                metadata = pq.read_schema(path).metadata or {}
                valid = (
                    path.parent == table_root
                    and path.name == f"part-{index:05d}.parquet"
                    and not path.is_symlink()
                    and stat.S_ISREG(info.st_mode)
                    and not info.st_mode & 0o222
                    and info.st_size == int(record["bytes"])
                    and rows == int(record["rows"])
                    and sha256_file(path) == str(record["sha256"])
                    and base_schema.equals(expected_schema)
                    and metadata.get(b"ipin.audit_version") == b"1.0.0"
                    and metadata.get(b"ipin.redistribution")
                    == b"internal_governance_bounded_audit_only"
                )
                if not valid or path in declared_files:
                    errors += 1
                declared_files.add(path)
                row_count += rows
                total_rows += rows
            except (FileNotFoundError, ValueError, KeyError):
                errors += 1
        if (
            row_count != int(summary.get("rows", -1))
            or summary.get("schema_sha256") != contract.sha256
            or summary.get("table") != table_name
        ):
            errors += 1
    actual_parquet = {path.resolve() for path in root.rglob("*.parquet")}
    if actual_parquet != declared_files:
        errors += 1
    allowed = {manifest_path.resolve(), sidecar.resolve(), *actual_parquet}
    for path in (root, *root.rglob("*")):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or mode & 0o222:
            errors += 1
        if stat.S_ISREG(mode) and path.resolve() not in allowed:
            errors += 1
    checks.require(
        f"inventory.{root.name}.hash_schema_immutability",
        errors == 0,
        observed={"errors": errors, "parquet_files": len(actual_parquet)},
        expected={"errors": 0},
    )
    return table_roots, {"tables": len(table_roots), "rows": total_rows}


def _independent_source_metrics(
    *, project_root: Path, config: Mapping[str, Any], acquisition_path: Path
) -> dict[str, Any]:
    _, assets = load_asset_index(project_root, acquisition_path.relative_to(project_root))
    raw_assets = config["raw_assets"]
    code = assets[str(raw_assets["archived_code"])]
    with zipfile.ZipFile(code.path) as archive:
        def one(suffix: str) -> bytes:
            names = [name for name in archive.namelist() if name.endswith(suffix)]
            if len(names) != 1:
                raise RuntimeError(f"Independent ZIP lookup failed: {suffix}")
            return archive.read(names[0])

        selection = pd.read_csv(
            BytesIO(one("predicting_human_interactome_pairs_to_test_2024-12-13.tsv")),
            sep="\t",
            dtype=str,
        )
        raw = pd.read_csv(
            BytesIO(one("Y2H_v1_pairwise_test_AlphaFoldRoseTTAFold_human.tsv")),
            sep="\t",
            dtype=object,
        )
    paper_asset = assets[str(raw_assets["supplementary_data_22"])]
    paper = pd.read_excel(paper_asset.path, sheet_name="Supplementary_Data_22")
    raw["independent_outcome"] = [
        independent_raw_outcome(row.final_score, row.seq_confirmation_final_3at, row.seq_confirmation_final_lw)
        for row in raw.itertuples(index=False)
    ]
    merged = paper.merge(
        raw,
        how="left",
        left_on=["AD_CCSB_ORF_ID", "DB_CCSB_ORF_ID", "source_dataset"],
        right_on=["ad_orf_id", "db_orf_id", "category"],
        validate="one_to_one",
    )
    raw_matched = merged["independent_outcome"].notna()
    crosswalk_disagreements = int(
        (merged.loc[raw_matched, "result"] != merged.loc[raw_matched, "independent_outcome"]).sum()
    )
    zhang_selection = selection.loc[selection["source"] == "Zhang_et_al"].copy()
    zhang_selection["pair"] = [
        "_".join(sorted((str(a), str(b))))
        for a, b in zip(zhang_selection["ad_orf_id"], zhang_selection["db_orf_id"], strict=True)
    ]
    final = paper.loc[
        (paper["source_dataset"] == "Zhang_et_al")
        & (paper["in_published_version"] == True)  # noqa: E712
    ]
    outcomes = final["result"].value_counts().to_dict()
    return {
        "selection_rows": len(selection),
        "zhang_selection_physical_rows": len(zhang_selection),
        "zhang_selection_unique_pairs": int(zhang_selection["pair"].nunique()),
        "raw_assay_rows": len(raw),
        "paper_rows": len(paper),
        "paper_zhang_rows": int((paper["source_dataset"] == "Zhang_et_al").sum()),
        "raw_paper_crosswalk_disagreements": crosswalk_disagreements,
        "final_pairs": len(final),
        "final_outcomes": {str(key): int(value) for key, value in outcomes.items()},
    }


def _glob(path: Path) -> str:
    return (path / "*.parquet").as_posix()


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _register_views(
    connection: duckdb.DuckDBPyConnection,
    *,
    canonical: Mapping[str, Path],
    dataset_paths: Mapping[str, Path],
) -> None:
    for name, path in canonical.items():
        connection.execute(
            f"CREATE TEMP VIEW {name} AS SELECT * FROM read_parquet("
            f"{_sql_string(_glob(path))})"
        )
    for name, path in dataset_paths.items():
        connection.execute(
            f"CREATE TEMP VIEW upstream_{name} AS SELECT * FROM read_parquet("
            f"{_sql_string(_glob(path))})"
        )


def _independent_evidence_checks(
    *,
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    permitted_pair_views: list[str],
) -> dict[str, Any]:
    connection.execute(
        """
        CREATE TEMP VIEW upstream_combined_evidence AS
        SELECT * FROM upstream_huri_evidence
        UNION ALL BY NAME
        SELECT * FROM upstream_intact_evidence
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_positive_records AS
        WITH mapped AS (
            SELECT
                evidence_id,
                source_key,
                min(mapped_sequence_sha256) AS sequence_a,
                max(mapped_sequence_sha256) AS sequence_b,
                count(*) AS participant_rows
            FROM upstream_participant_sequence_mappings
            WHERE reference_sequence_usable
            GROUP BY evidence_id, source_key
        )
        SELECT
            mapped.sequence_a,
            mapped.sequence_b,
            evidence.source_key,
            evidence.interaction_semantics
        FROM mapped
        JOIN upstream_combined_evidence evidence
          ON evidence.evidence_id = mapped.evidence_id
         AND evidence.source_key = mapped.source_key
        JOIN upstream_evidence_mapping_summaries summary
          ON summary.evidence_id = mapped.evidence_id
         AND summary.source_key = mapped.source_key
        WHERE mapped.participant_rows = 2
          AND summary.reference_pair_usable
          AND evidence.observation_state = 'positive'
          AND evidence.participant_count = 2
          AND NOT evidence.original_nary
          AND NOT evidence.is_expanded_projection
        """
    )
    allowed = ",".join(_sql_string(value) for value in permitted_pair_views)
    connection.execute(
        f"""
        CREATE TEMP TABLE independent_pair_views AS
        WITH candidate_map AS (
            SELECT
                mapping.identifier_versionless AS gene_id,
                sequence.sequence_sha256
            FROM upstream_identifier_mappings mapping
            JOIN upstream_protein_sequences sequence
              ON sequence.uniprot_accession = mapping.uniprot_accession
             AND sequence.canonical
            WHERE mapping.database = 'Ensembl'
        ), unique_map AS (
            SELECT gene_id, min(sequence_sha256) AS sequence_sha256
            FROM candidate_map
            GROUP BY gene_id
            HAVING count(DISTINCT sequence_sha256) = 1
        )
        SELECT
            least(a.sequence_sha256, b.sequence_sha256) AS sequence_a,
            greatest(a.sequence_sha256, b.sequence_sha256) AS sequence_b,
            count(*)::BIGINT AS pair_view_count
        FROM upstream_huri_pair_views pair
        JOIN unique_map a ON a.gene_id = pair.member_a
        JOIN unique_map b ON b.gene_id = pair.member_b
        WHERE pair.source_dataset IN ({allowed})
          AND pair.view_membership
        GROUP BY sequence_a, sequence_b
        """
    )
    mismatches = int(
        connection.execute(
            """
            WITH record_counts AS (
                SELECT sequence_a, sequence_b,
                    count_if(source_key = 'huri')::BIGINT AS huri_count,
                    count_if(source_key = 'intact_imex')::BIGINT AS intact_count,
                    count_if(interaction_semantics = 'direct_binary')::BIGINT AS direct_count,
                    count_if(source_key = 'intact_imex'
                        AND interaction_semantics <> 'direct_binary')::BIGINT AS broader_count
                FROM independent_positive_records GROUP BY sequence_a, sequence_b
            ), panel AS (
                SELECT *,
                    least(mapped_sequence_sha256_ad, mapped_sequence_sha256_db) AS sequence_a,
                    greatest(mapped_sequence_sha256_ad, mapped_sequence_sha256_db) AS sequence_b
                FROM panel_pair_audit
            )
            SELECT count(*)
            FROM panel
            LEFT JOIN record_counts USING (sequence_a, sequence_b)
            LEFT JOIN independent_pair_views USING (sequence_a, sequence_b)
            WHERE huri_record_positive_count <> coalesce(huri_count, 0)
               OR intact_positive_count <> coalesce(intact_count, 0)
               OR qualifying_direct_positive_count <> coalesce(direct_count, 0)
               OR broader_intact_positive_count <> coalesce(broader_count, 0)
               OR huri_pair_view_count <> coalesce(pair_view_count, 0)
               OR exact_future_training_pair_overlap <>
                    (coalesce(direct_count, 0) > 0 OR coalesce(pair_view_count, 0) > 0)
            """
        ).fetchone()[0]
    )
    checks.require(
        "evidence.record_and_pair_view_recomputation",
        mismatches == 0,
        observed={"mismatched_panel_rows": mismatches},
        expected={"mismatched_panel_rows": 0},
    )
    negative_mismatches = int(
        connection.execute(
            """
            WITH intact_counts AS (
                SELECT mapped_unordered_sequence_pair_id, count(*)::BIGINT AS n
                FROM upstream_intact_negative_record_audit
                WHERE reference_pair_usable
                GROUP BY mapped_unordered_sequence_pair_id
            ), negatome_counts AS (
                SELECT mapped_unordered_sequence_pair_id, count(*)::BIGINT AS n
                FROM upstream_negatome_record_audit
                WHERE reference_pair_usable
                GROUP BY mapped_unordered_sequence_pair_id
            )
            SELECT count(*)
            FROM panel_pair_audit panel
            LEFT JOIN intact_counts intact USING (mapped_unordered_sequence_pair_id)
            LEFT JOIN negatome_counts negatome USING (mapped_unordered_sequence_pair_id)
            WHERE panel.intact_negative_overlap_count <> coalesce(intact.n, 0)
               OR panel.negatome_overlap_count <> coalesce(negatome.n, 0)
            """
        ).fetchone()[0]
    )
    checks.require(
        "evidence.negative_pair_recomputation",
        negative_mismatches == 0,
        observed={"mismatched_panel_rows": negative_mismatches},
        expected={"mismatched_panel_rows": 0},
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_training_pairs AS
        SELECT DISTINCT sequence_a, sequence_b
        FROM independent_positive_records
        WHERE interaction_semantics = 'direct_binary'
        UNION
        SELECT sequence_a, sequence_b FROM independent_pair_views
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_sequence_families AS
        SELECT DISTINCT
            sequence.sequence_sha256,
            mapping.database,
            mapping.identifier AS family_id
        FROM upstream_protein_sequences sequence
        JOIN upstream_identifier_mappings mapping
          ON mapping.uniprot_accession = sequence.uniprot_accession
        WHERE mapping.database IN ('UniRef90', 'UniRef50')
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_training_family_pairs AS
        SELECT DISTINCT
            a.database,
            least(a.family_id, b.family_id) AS family_a,
            greatest(a.family_id, b.family_id) AS family_b
        FROM independent_training_pairs pair
        JOIN independent_sequence_families a
          ON a.sequence_sha256 = pair.sequence_a
        JOIN independent_sequence_families b
          ON b.sequence_sha256 = pair.sequence_b
         AND b.database = a.database
        """
    )
    family_pair_mismatches = int(
        connection.execute(
            """
            WITH panel_families AS (
                SELECT
                    panel.panel_pair_id,
                    a.database,
                    least(a.family_id, b.family_id) AS family_a,
                    greatest(a.family_id, b.family_id) AS family_b
                FROM panel_pair_audit panel
                JOIN independent_sequence_families a
                  ON a.sequence_sha256 = panel.mapped_sequence_sha256_ad
                JOIN independent_sequence_families b
                  ON b.sequence_sha256 = panel.mapped_sequence_sha256_db
                 AND b.database = a.database
            ), expected AS (
                SELECT
                    panel.panel_pair_id,
                    coalesce(bool_or(training.family_a IS NOT NULL)
                        FILTER (WHERE family.database = 'UniRef90'), false)
                        AS overlap90,
                    coalesce(bool_or(training.family_a IS NOT NULL)
                        FILTER (WHERE family.database = 'UniRef50'), false)
                        AS overlap50
                FROM panel_pair_audit panel
                LEFT JOIN panel_families family USING (panel_pair_id)
                LEFT JOIN independent_training_family_pairs training
                  ON training.database = family.database
                 AND training.family_a = family.family_a
                 AND training.family_b = family.family_b
                GROUP BY panel.panel_pair_id
            )
            SELECT count(*)
            FROM panel_pair_audit panel
            JOIN expected USING (panel_pair_id)
            WHERE panel.uniref90_pair_overlap <> expected.overlap90
               OR panel.uniref50_pair_overlap <> expected.overlap50
            """
        ).fetchone()[0]
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_training_family_endpoints AS
        SELECT DISTINCT database, family_id
        FROM independent_training_pairs pair
        JOIN independent_sequence_families family
          ON family.sequence_sha256 = pair.sequence_a
        UNION
        SELECT DISTINCT database, family_id
        FROM independent_training_pairs pair
        JOIN independent_sequence_families family
          ON family.sequence_sha256 = pair.sequence_b
        """
    )
    endpoint_mismatches = int(
        connection.execute(
            """
            WITH training_endpoints AS (
                SELECT sequence_a AS sequence_sha256 FROM independent_training_pairs
                UNION SELECT sequence_b FROM independent_training_pairs
            ), panel_family_endpoints AS (
                SELECT panel.panel_pair_id, family.database, family.family_id
                FROM panel_pair_audit panel
                JOIN independent_sequence_families family
                  ON family.sequence_sha256 = panel.mapped_sequence_sha256_ad
                UNION
                SELECT panel.panel_pair_id, family.database, family.family_id
                FROM panel_pair_audit panel
                JOIN independent_sequence_families family
                  ON family.sequence_sha256 = panel.mapped_sequence_sha256_db
            ), family_expected AS (
                SELECT
                    panel.panel_pair_id,
                    coalesce(bool_or(training.family_id IS NOT NULL)
                        FILTER (WHERE family.database = 'UniRef90'), false)
                        AS overlap90,
                    coalesce(bool_or(training.family_id IS NOT NULL)
                        FILTER (WHERE family.database = 'UniRef50'), false)
                        AS overlap50
                FROM panel_pair_audit panel
                LEFT JOIN panel_family_endpoints family USING (panel_pair_id)
                LEFT JOIN independent_training_family_endpoints training
                  ON training.database = family.database
                 AND training.family_id = family.family_id
                GROUP BY panel.panel_pair_id
            )
            SELECT count(*)
            FROM panel_pair_audit panel
            JOIN family_expected expected USING (panel_pair_id)
            WHERE panel.exact_endpoint_overlap <>
                (coalesce(panel.mapped_sequence_sha256_ad IN (
                    SELECT sequence_sha256 FROM training_endpoints
                 ), false) OR coalesce(panel.mapped_sequence_sha256_db IN (
                    SELECT sequence_sha256 FROM training_endpoints
                 ), false))
               OR panel.uniref90_endpoint_overlap <> expected.overlap90
               OR panel.uniref50_endpoint_overlap <> expected.overlap50
            """
        ).fetchone()[0]
    )
    checks.require(
        "contamination.family_pair_and_endpoint_recomputation",
        family_pair_mismatches == 0 and endpoint_mismatches == 0,
        observed={
            "family_pair_mismatches": family_pair_mismatches,
            "endpoint_mismatches": endpoint_mismatches,
        },
        expected={"family_pair_mismatches": 0, "endpoint_mismatches": 0},
    )
    return {
        "positive_record_rows": int(
            connection.execute("SELECT count(*) FROM independent_positive_records").fetchone()[0]
        ),
        "permitted_pair_view_pairs": int(
            connection.execute("SELECT count(*) FROM independent_pair_views").fetchone()[0]
        ),
        "positive_mismatches": mismatches,
        "negative_mismatches": negative_mismatches,
        "family_pair_mismatches": family_pair_mismatches,
        "endpoint_mismatches": endpoint_mismatches,
    }


def run_validation(*, project_root: Path, config_path: Path, report_path: Path | None = None) -> dict[str, Any]:
    require_apptainer()
    config_path = _resolve_inside(
        project_root, config_path, project_root / "configs", strict=True
    )
    config = _load_yaml(config_path)
    checks = Checks()
    schema_spec = config["inputs"]["documents"]["audit_schema"]
    schema_path = _resolve_inside(
        project_root,
        str(schema_spec["path"]),
        project_root / str(schema_spec["boundary"]),
        strict=True,
    )
    checks.require(
        "inputs.schema_hash",
        sha256_file(schema_path) == str(schema_spec["sha256"]),
        observed={"sha256": sha256_file(schema_path)},
        expected={"sha256": str(schema_spec["sha256"])},
    )
    contract = load_contract(schema_path)
    staging_root = _resolve_inside(
        project_root,
        str(config["outputs"]["staging_root"]),
        project_root / "data/staging",
        strict=True,
    )
    canonical_root = _resolve_inside(
        project_root,
        str(config["outputs"]["canonical_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    staging, staging_inventory = _validate_dataset(
        checks=checks,
        project_root=project_root,
        root=staging_root,
        manifest_name="STAGING_MANIFEST.json",
        expected_tables={
            "archive_members",
            "selection_records",
            "raw_assay_records",
            "paper_records",
            "imex_preview_records",
        },
        contract=contract,
    )
    canonical, canonical_inventory = _validate_dataset(
        checks=checks,
        project_root=project_root,
        root=canonical_root,
        manifest_name="AUDIT_MANIFEST.json",
        expected_tables={
            "selected_universe_reconciliation",
            "participant_mappings",
            "panel_pair_audit",
            "imex_pair_reconciliation",
            "assay_metadata",
        },
        contract=contract,
    )
    audit_report_path = _resolve_inside(
        project_root,
        str(config["outputs"]["audit_report"]),
        project_root / "artifacts/validation",
        strict=True,
    )
    audit_report = _load_json(audit_report_path)
    audit_digest = sha256_file(audit_report_path)
    audit_sidecar = audit_report_path.with_name(audit_report_path.name + ".sha256")
    checks.require(
        "audit_report.aggregate_only_and_checksummed",
        audit_sidecar.read_text(encoding="utf-8").split()
        == [audit_digest, audit_report_path.name]
        and not contains_record_level_report_keys(audit_report),
        observed={
            "sidecar_matches": audit_sidecar.read_text(encoding="utf-8").split()
            == [audit_digest, audit_report_path.name],
            "contains_record_level_keys": contains_record_level_report_keys(audit_report),
        },
        expected={"sidecar_matches": True, "contains_record_level_keys": False},
    )
    acquisition_spec = config["inputs"]["documents"]["acquisition_manifest"]
    acquisition_path = _resolve_inside(
        project_root,
        str(acquisition_spec["path"]),
        project_root / str(acquisition_spec["boundary"]),
        strict=True,
    )
    source_metrics = _independent_source_metrics(
        project_root=project_root, config=config, acquisition_path=acquisition_path
    )
    expected_source = {
        "selection_rows": 4600,
        "zhang_selection_physical_rows": 4133,
        "zhang_selection_unique_pairs": 4130,
        "raw_assay_rows": 4499,
        "paper_rows": 4775,
        "paper_zhang_rows": 4046,
        "raw_paper_crosswalk_disagreements": 0,
        "final_pairs": 3222,
        "final_outcomes": {
            "Positive": 376,
            "Negative": 2300,
            "Failed sequence confirmation": 478,
            "Autoactivator": 41,
            "Test failed": 27,
        },
    }
    checks.require(
        "source.independent_counts_and_crosswalk",
        source_metrics == expected_source,
        observed=source_metrics,
        expected=expected_source,
    )

    dataset_paths: dict[str, Path] = {}
    for name, relative in config["inputs"]["dataset_paths"].items():
        boundary = "data/staging" if str(relative).startswith("data/staging/") else "data/canonical"
        dataset_paths[str(name)] = _resolve_inside(
            project_root, str(relative), project_root / boundary, strict=True
        )
    connection = duckdb.connect()
    connection.execute(f"SET memory_limit='{config['runtime']['duckdb_memory_limit']}'")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    try:
        _register_views(
            connection,
            canonical={**staging, **canonical},
            dataset_paths=dataset_paths,
        )
        row_counts = {
            name: int(connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0])
            for name in canonical
        }
        expected_rows = {
            "selected_universe_reconciliation": 4130,
            "participant_mappings": 8092,
            "panel_pair_audit": 4046,
            "imex_pair_reconciliation": int(
                connection.execute("SELECT count(*) FROM imex_preview_records").fetchone()[0]
            ),
            "assay_metadata": 1,
        }
        checks.require(
            "canonical.row_counts",
            row_counts == expected_rows,
            observed=row_counts,
            expected=expected_rows,
        )
        governance_errors = 0
        for name in (*staging.keys(), *canonical.keys()):
            columns = {
                row[1]
                for row in connection.execute(f"PRAGMA table_info('{name}')").fetchall()
            }
            guard_columns = {
                "outcome_training_label_authorized",
                "universal_nonbinding_asserted",
                "benchmark_integration_authorized",
            } & columns
            for column in guard_columns:
                governance_errors += int(
                    connection.execute(
                        f"SELECT count(*) FROM {name} WHERE {column}"
                    ).fetchone()[0]
                )
        technical_negative_errors = int(
            connection.execute(
                """
                SELECT count(*) FROM panel_pair_audit
                WHERE evaluability_state = 'not_evaluable'
                  AND observation_state = 'negative'
                """
            ).fetchone()[0]
        )
        checks.require(
            "governance.row_level_guards",
            governance_errors == 0 and technical_negative_errors == 0,
            observed={
                "true_guard_values": governance_errors,
                "technical_rows_marked_negative": technical_negative_errors,
            },
            expected={"true_guard_values": 0, "technical_rows_marked_negative": 0},
        )
        final_counts = {
            str(outcome): int(count)
            for outcome, count in connection.execute(
                """
                SELECT reported_outcome, count(*) FROM panel_pair_audit
                WHERE in_final_analysis GROUP BY reported_outcome
                """
            ).fetchall()
        }
        checks.require(
            "canonical.final_outcomes",
            final_counts == expected_source["final_outcomes"],
            observed=final_counts,
            expected=expected_source["final_outcomes"],
        )
        evidence_metrics = _independent_evidence_checks(
            checks=checks,
            connection=connection,
            permitted_pair_views=list(config["evidence_policy"]["permitted_pair_views"]),
        )
    finally:
        connection.close()

    counts = checks.counts()
    status = "pass" if checks.passed else "fail"
    report = {
        "schema_version": 1,
        "validator": "independent_lambourne_y2h_v1",
        "status": status,
        "checks": checks.records,
        "check_counts": counts,
        "inventory": {
            "staging": staging_inventory,
            "canonical": canonical_inventory,
        },
        "independent_source_metrics": source_metrics,
        "independent_evidence_metrics": evidence_metrics,
        "governance": {
            "outcomes_as_training_labels": False,
            "merge_with_negatome": False,
            "benchmark_split_construction": False,
            "model_training": False,
            "universal_nonbinding_interpretation": False,
            "return_to_governance_required": True,
        },
    }
    target = report_path or project_root / str(config["outputs"]["validation_report"])
    target = _resolve_inside(
        project_root, target, project_root / "artifacts/validation", strict=False
    )
    _write_report(target, report, project_root)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Independently validate the Lambourne Y2H audit")
    parser.add_argument(
        "--config", type=Path, default=Path("configs/lambourne_y2h_audit_v1.yaml")
    )
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_validation(
        project_root=project_root_from(Path.cwd()),
        config_path=args.config,
        report_path=args.report,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1
