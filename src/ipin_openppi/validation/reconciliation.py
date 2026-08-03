"""Fail-closed validation gate for immutable primary reconciliation output."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import stat
from typing import Any, Mapping

import duckdb
import pyarrow.parquet as pq
import yaml

from ipin_openppi.ingestion.common import (
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import SchemaContract, load_contract, sha256_file
from ipin_openppi.validation.reconciliation_semantics import (
    collect_output_metrics,
    normalize_manifest_metrics,
    register_canonical_views,
    register_staging_views,
    validate_contract_rows,
    validate_evidence_summaries,
    validate_huri_reconciliation,
    validate_participant_mappings,
    validate_sifts_audit,
    validate_uniform_provenance_and_authorization,
)
from ipin_openppi.validation.staging import Checks, _write_report


MANIFEST_NAME = "RECONCILIATION_MANIFEST.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("rt", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("rt", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def _nested(document: Mapping[str, Any], dotted_path: str) -> Any:
    value: Any = document
    for component in dotted_path.split("."):
        if not isinstance(value, Mapping) or component not in value:
            return "__missing__"
        value = value[component]
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


def _require_validation_scope(root: Path, allow_smoke: bool) -> str:
    is_smoke = root.name.startswith("_smoke_")
    if is_smoke and not allow_smoke:
        raise RuntimeError("Validation of _smoke_* output requires --allow-smoke")
    if allow_smoke and not is_smoke:
        raise RuntimeError("--allow-smoke is restricted to a _smoke_* output root")
    return "qualification_smoke" if is_smoke else "production_full"


def _validate_manifest_and_runtime(
    *,
    checks: Checks,
    project_root: Path,
    root: Path,
    manifest: Mapping[str, Any],
    manifest_path: Path,
    expectations: Mapping[str, Any],
    scope: str,
) -> tuple[dict[str, Any], SchemaContract, Path]:
    manifest_sha = sha256_file(manifest_path)
    sidecar_path = root / f"{MANIFEST_NAME}.sha256"
    tokens = sidecar_path.read_text(encoding="utf-8").split()
    observed_sidecar = {
        "sha256": tokens[0] if tokens else None,
        "filename": tokens[1] if len(tokens) > 1 else None,
    }
    expected_sidecar = {"sha256": manifest_sha, "filename": MANIFEST_NAME}
    checks.require(
        "manifest.sha256_sidecar",
        observed_sidecar == expected_sidecar,
        observed=observed_sidecar,
        expected=expected_sidecar,
    )

    expected_top_level = {
        "schema_version": int(expectations["expected_manifest_schema_version"]),
        "run_family": str(expectations["expected_run_family"]),
        "task": str(expectations["expected_task"]),
        "status": "complete",
        "source_reconciliation_performed": True,
        "label_construction_performed": False,
        "model_training_performed": False,
    }
    for key, expected in expected_top_level.items():
        observed = manifest.get(key)
        checks.require(
            f"manifest.{key}",
            observed == expected,
            observed=observed,
            expected=expected,
        )

    expected_authorizations = {
        "source_reconciliation": True,
        "label_construction": False,
        "model_training": False,
        "structural_mapping": False,
    }
    observed_authorizations = manifest.get("authorizations")
    checks.require(
        "manifest.authorizations",
        observed_authorizations == expected_authorizations,
        observed=observed_authorizations,
        expected=expected_authorizations,
    )

    expected_container_sha = str(expectations["expected_container_sha256"])
    expected_version = str(expectations["expected_reconciliation_version"])
    expected_architecture = str(expectations["expected_architecture"])
    runtime = manifest.get("runtime", {})
    for key, expected in {
        "container_sif_sha256": expected_container_sha,
        "reconciliation_version": expected_version,
        "architecture": expected_architecture,
    }.items():
        observed = runtime.get(key)
        checks.require(
            f"runtime.manifest_{key}",
            observed == expected,
            observed=observed,
            expected=expected,
        )
    checks.require(
        "runtime.host_architecture",
        platform.machine() == expected_architecture,
        observed=platform.machine(),
        expected=expected_architecture,
    )
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    active_sha = sha256_file(active_container)
    checks.require(
        "runtime.active_container_sha256",
        active_sha == expected_container_sha,
        observed=active_sha,
        expected=expected_container_sha,
    )

    configured_run_path = _resolve_inside(
        project_root,
        str(expectations["run_config"]),
        project_root / "configs",
    )
    manifest_run_path = _resolve_inside(
        project_root,
        str(manifest["inputs"]["config"]),
        project_root / "configs",
    )
    checks.require(
        "manifest.run_config_path",
        manifest_run_path == configured_run_path,
        observed=manifest_run_path.as_posix(),
        expected=configured_run_path.as_posix(),
    )
    run_config = _load_yaml(manifest_run_path)
    run_config_sha = sha256_file(manifest_run_path)
    checks.require(
        "manifest.run_config_sha256",
        run_config_sha == manifest["inputs"].get("config_sha256"),
        observed=run_config_sha,
        expected=manifest["inputs"].get("config_sha256"),
    )
    checks.require(
        "runtime.configured_container_matches_active",
        (project_root / str(run_config["runtime"]["container"])).resolve(strict=True)
        == active_container,
        observed=active_container.as_posix(),
        expected=(project_root / str(run_config["runtime"]["container"]))
        .resolve(strict=True)
        .as_posix(),
    )
    checks.require(
        "runtime.run_config_container_sha256",
        run_config["runtime"].get("container_sha256") == expected_container_sha,
        observed=run_config["runtime"].get("container_sha256"),
        expected=expected_container_sha,
    )
    checks.require(
        "runtime.run_config_reconciliation_version",
        run_config.get("reconciliation_version") == expected_version,
        observed=run_config.get("reconciliation_version"),
        expected=expected_version,
    )

    expected_policy = {
        "mapping": run_config["mapping_policy"],
        "sifts": run_config["sifts_policy"],
        "provider_counts": run_config["provider_counts"],
    }
    checks.require(
        "manifest.policy_matches_run_config",
        manifest.get("policy") == expected_policy,
        observed=manifest.get("policy"),
        expected=expected_policy,
    )
    for dotted_path, expected in expectations["required_policy_values"].items():
        observed = _nested(manifest.get("policy", {}), str(dotted_path))
        checks.require(
            f"policy.{dotted_path}",
            observed == expected,
            observed=observed,
            expected=expected,
        )

    schema_path = _resolve_inside(
        project_root,
        str(run_config["inputs"]["reconciliation_schema"]),
        project_root / "schemas/canonical",
    )
    contract = load_contract(schema_path)
    checks.require(
        "schema.manifest_sha256",
        manifest["inputs"].get("reconciliation_schema_sha256") == contract.sha256,
        observed=manifest["inputs"].get("reconciliation_schema_sha256"),
        expected=contract.sha256,
    )
    checks.require(
        "schema.expected_sha256",
        contract.sha256 == str(expectations["expected_schema_sha256"]),
        observed=contract.sha256,
        expected=str(expectations["expected_schema_sha256"]),
    )

    staging_root = _resolve_inside(
        project_root,
        str(run_config["inputs"]["staging_root"]),
        project_root / "data/staging",
    )
    parse_manifest = _resolve_inside(
        project_root,
        str(run_config["inputs"]["parse_manifest"]),
        staging_root,
    )
    parse_sha = sha256_file(parse_manifest)
    expected_parse_sha = str(expectations["expected_parse_manifest_sha256"])
    checks.require(
        "input.parse_manifest_sha256",
        parse_sha == expected_parse_sha
        and manifest["inputs"].get("parse_manifest_sha256") == expected_parse_sha
        and run_config["inputs"].get("parse_manifest_sha256") == expected_parse_sha,
        observed={
            "actual": parse_sha,
            "manifest": manifest["inputs"].get("parse_manifest_sha256"),
            "run_config": run_config["inputs"].get("parse_manifest_sha256"),
        },
        expected=expected_parse_sha,
    )
    parse_document = _load_json(parse_manifest)
    checks.require(
        "input.parse_manifest_complete_without_labels",
        parse_document.get("status") == "complete"
        and parse_document.get("label_construction_performed") is False
        and parse_document.get("model_training_performed") is False,
        observed={
            "status": parse_document.get("status"),
            "label_construction_performed": parse_document.get(
                "label_construction_performed"
            ),
            "model_training_performed": parse_document.get("model_training_performed"),
        },
        expected={
            "status": "complete",
            "label_construction_performed": False,
            "model_training_performed": False,
        },
    )

    staging_validation = _resolve_inside(
        project_root,
        str(run_config["inputs"]["staging_validation_report"]),
        project_root / "artifacts/validation",
    )
    staging_validation_sha = sha256_file(staging_validation)
    expected_validation_sha = str(
        expectations["expected_staging_validation_report_sha256"]
    )
    checks.require(
        "input.staging_validation_report_sha256",
        staging_validation_sha == expected_validation_sha
        and manifest["inputs"].get("staging_validation_report_sha256")
        == expected_validation_sha
        and run_config["inputs"].get("staging_validation_report_sha256")
        == expected_validation_sha,
        observed={
            "actual": staging_validation_sha,
            "manifest": manifest["inputs"].get("staging_validation_report_sha256"),
            "run_config": run_config["inputs"].get("staging_validation_report_sha256"),
        },
        expected=expected_validation_sha,
    )
    staging_validation_document = _load_json(staging_validation)
    checks.require(
        "input.staging_validation_passed_for_same_parse_manifest",
        staging_validation_document.get("status") == "pass"
        and staging_validation_document.get("parse_manifest_sha256") == parse_sha
        and staging_validation_document.get("authorizations", {}).get(
            "source_reconciliation"
        )
        is True
        and staging_validation_document.get("authorizations", {}).get(
            "label_construction"
        )
        is False,
        observed={
            "status": staging_validation_document.get("status"),
            "parse_manifest_sha256": staging_validation_document.get(
                "parse_manifest_sha256"
            ),
            "authorizations": staging_validation_document.get("authorizations"),
        },
        expected={
            "status": "pass",
            "parse_manifest_sha256": parse_sha,
            "source_reconciliation": True,
            "label_construction": False,
        },
    )
    expected_sha_verification = (
        "skipped_by_explicit_nonproduction_option"
        if scope == "qualification_smoke"
        else "complete"
    )
    checks.require(
        "input.staging_parquet_sha256_verification",
        manifest["inputs"].get("sha256_verification") == expected_sha_verification,
        observed=manifest["inputs"].get("sha256_verification"),
        expected=expected_sha_verification,
    )

    if scope == "production_full":
        checks.require(
            "provenance.production_reconciliation_was_clean",
            manifest.get("git", {}).get("tracked_worktree_clean") is True,
            observed=manifest.get("git", {}).get("tracked_worktree_clean"),
            expected=True,
        )
        current_git = git_provenance(project_root)
        checks.require(
            "provenance.validator_checkout_matches_reconciliation_commit",
            current_git["commit"] == manifest.get("git", {}).get("commit"),
            observed=current_git["commit"],
            expected=manifest.get("git", {}).get("commit"),
        )

    return run_config, contract, staging_root


def _validate_inventory(
    *,
    checks: Checks,
    project_root: Path,
    root: Path,
    manifest: Mapping[str, Any],
    contract: SchemaContract,
    expectations: Mapping[str, Any],
) -> tuple[dict[str, list[Path]], dict[str, int]]:
    expected_rows = {
        str(table): int(rows)
        for table, rows in expectations["expected_table_rows"].items()
    }
    expected_tables = set(contract.document["tables"])
    observed_tables = set(manifest.get("tables", {}))
    checks.require(
        "manifest.exact_table_inventory",
        observed_tables == expected_tables == set(expected_rows),
        observed=sorted(observed_tables),
        expected=sorted(expected_tables),
    )

    table_paths: dict[str, list[Path]] = {}
    manifest_paths: set[Path] = set()
    file_mismatches: list[dict[str, Any]] = []
    schema_mismatches: list[dict[str, Any]] = []
    observed_rows: dict[str, int] = {}
    total_bytes = 0
    total_rows = 0

    for table in sorted(observed_tables & expected_tables):
        summary = manifest["tables"][table]
        records = summary.get("files", [])
        resolved_files: list[Path] = []
        expected_names = [f"part-{index:05d}.parquet" for index in range(len(records))]
        observed_names = [Path(str(record.get("path"))).name for record in records]
        if observed_names != expected_names:
            file_mismatches.append(
                {
                    "table": table,
                    "error": "nonsequential or unexpected Parquet part names",
                    "observed": observed_names,
                    "expected": expected_names,
                }
            )
        for record in records:
            candidate = Path(str(record["path"]))
            if not candidate.is_absolute():
                candidate = project_root / candidate
            try:
                path = candidate.resolve(strict=True)
                path.relative_to(root)
                if path.parent != root / table:
                    raise ValueError("file is not directly under its table directory")
            except (FileNotFoundError, ValueError) as exc:
                file_mismatches.append(
                    {"table": table, "path": str(record.get("path")), "error": str(exc)}
                )
                continue
            if path in manifest_paths:
                file_mismatches.append(
                    {"table": table, "path": path.as_posix(), "error": "duplicate path"}
                )
                continue
            info = path.stat(follow_symlinks=False)
            if path.is_symlink() or not stat.S_ISREG(info.st_mode):
                file_mismatches.append(
                    {
                        "table": table,
                        "path": path.as_posix(),
                        "error": "not a regular non-link file",
                    }
                )
                continue
            parquet_rows = int(pq.ParquetFile(path).metadata.num_rows)
            digest = sha256_file(path)
            observed_file = {
                "bytes": info.st_size,
                "rows": parquet_rows,
                "sha256": digest,
            }
            expected_file = {
                "bytes": int(record["bytes"]),
                "rows": int(record["rows"]),
                "sha256": str(record["sha256"]),
            }
            if observed_file != expected_file:
                file_mismatches.append(
                    {
                        "table": table,
                        "path": path.as_posix(),
                        "observed": observed_file,
                        "expected": expected_file,
                    }
                )
            observed_schema = pq.read_schema(path)
            expected_schema = contract.arrow_schema(table)
            observed_metadata = {
                key.decode(): value.decode()
                for key, value in (observed_schema.metadata or {}).items()
            }
            expected_metadata = {
                key.decode(): value.decode()
                for key, value in (expected_schema.metadata or {}).items()
            }
            if (
                not observed_schema.remove_metadata().equals(
                    expected_schema.remove_metadata()
                )
                or observed_metadata != expected_metadata
            ):
                schema_mismatches.append(
                    {
                        "table": table,
                        "path": path.as_posix(),
                        "arrow_schema_equal": observed_schema.remove_metadata().equals(
                            expected_schema.remove_metadata()
                        ),
                        "observed_metadata": observed_metadata,
                        "expected_metadata": expected_metadata,
                    }
                )
            resolved_files.append(path)
            manifest_paths.add(path)
            total_bytes += info.st_size
            total_rows += parquet_rows

        summary_file_rows = sum(int(record["rows"]) for record in records)
        summary_valid = (
            summary.get("table") == table
            and int(summary.get("rows", -1)) == expected_rows[table]
            and int(summary.get("rows", -1)) == summary_file_rows
            and int(summary.get("parts", -1)) == len(records)
            and summary.get("schema_name") == contract.name
            and int(summary.get("schema_version", -1)) == contract.version
            and summary.get("schema_sha256") == contract.sha256
        )
        checks.require(
            f"manifest.table_summary.{table}",
            summary_valid,
            observed={
                "table": summary.get("table"),
                "rows": summary.get("rows"),
                "file_rows": summary_file_rows,
                "parts": summary.get("parts"),
                "files": len(records),
                "schema_name": summary.get("schema_name"),
                "schema_version": summary.get("schema_version"),
                "schema_sha256": summary.get("schema_sha256"),
            },
            expected={
                "table": table,
                "rows": expected_rows[table],
                "file_rows": expected_rows[table],
                "parts_equal_files": True,
                "schema_name": contract.name,
                "schema_version": contract.version,
                "schema_sha256": contract.sha256,
            },
        )
        observed_rows[table] = int(summary.get("rows", -1))
        if resolved_files:
            table_paths[table] = resolved_files

    checks.require(
        "manifest.expected_table_rows",
        observed_rows == expected_rows,
        observed=observed_rows,
        expected=expected_rows,
    )
    actual_parquet_paths = {path.resolve() for path in root.rglob("*.parquet")}
    checks.require(
        "manifest.exact_parquet_file_inventory",
        actual_parquet_paths == manifest_paths,
        observed={
            "count": len(actual_parquet_paths),
            "unexpected": sorted(
                path.as_posix() for path in actual_parquet_paths - manifest_paths
            ),
            "missing": sorted(
                path.as_posix() for path in manifest_paths - actual_parquet_paths
            ),
        },
        expected={"count": len(manifest_paths), "unexpected": [], "missing": []},
    )
    checks.require(
        "manifest.parquet_hash_size_row_integrity",
        not file_mismatches,
        observed={
            "mismatch_count": len(file_mismatches),
            "examples": file_mismatches[:20],
        },
        expected={"mismatch_count": 0},
    )
    checks.require(
        "schema.parquet_contract_and_metadata",
        not schema_mismatches,
        observed={
            "mismatch_count": len(schema_mismatches),
            "examples": schema_mismatches[:20],
        },
        expected={"mismatch_count": 0},
    )

    allowed_regular_files = {
        (root / MANIFEST_NAME).resolve(),
        (root / f"{MANIFEST_NAME}.sha256").resolve(),
        *actual_parquet_paths,
    }
    filesystem_errors: list[dict[str, str]] = []
    for path in (root, *sorted(root.rglob("*"))):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            filesystem_errors.append(
                {"path": path.as_posix(), "error": "symbolic link"}
            )
        if info.st_mode & 0o222:
            filesystem_errors.append({"path": path.as_posix(), "error": "writable"})
        if stat.S_ISREG(info.st_mode) and path.resolve() not in allowed_regular_files:
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
    return table_paths, {
        "tables": len(observed_rows),
        "parquet_files": len(actual_parquet_paths),
        "parquet_rows_across_tables": total_rows,
        "parquet_bytes": total_bytes,
    }


def validate_reconciliation(
    *,
    project_root: Path,
    reconciliation_root: Path,
    expectation_path: Path,
    allow_smoke: bool,
) -> dict[str, Any]:
    require_apptainer()
    canonical_boundary = (project_root / "data/canonical").resolve(strict=True)
    root = reconciliation_root.resolve(strict=True)
    try:
        root.relative_to(canonical_boundary)
    except ValueError as exc:
        raise RuntimeError(f"Canonical root escapes data/canonical: {root}") from exc
    if reconciliation_root.is_symlink() or not root.is_dir():
        raise RuntimeError(
            f"Reconciliation root must be a non-link directory: {reconciliation_root}"
        )
    scope = _require_validation_scope(root, allow_smoke)
    expectations = _load_yaml(expectation_path)
    checks = Checks()
    manifest_path = root / MANIFEST_NAME
    manifest = _load_json(manifest_path)

    run_config, contract, staging_root = _validate_manifest_and_runtime(
        checks=checks,
        project_root=project_root,
        root=root,
        manifest=manifest,
        manifest_path=manifest_path,
        expectations=expectations,
        scope=scope,
    )
    table_paths, inventory_counts = _validate_inventory(
        checks=checks,
        project_root=project_root,
        root=root,
        manifest=manifest,
        contract=contract,
        expectations=expectations,
    )
    if set(table_paths) != set(contract.document["tables"]):
        checks.require(
            "semantic.all_tables_available",
            False,
            observed=sorted(table_paths),
            expected=sorted(contract.document["tables"]),
        )
        observed_metrics: dict[str, Any] = {}
    else:
        connection = duckdb.connect(":memory:")
        try:
            connection.execute(
                f"SET threads={int(expectations['validation_runtime']['duckdb_threads'])}"
            )
            memory_limit = str(
                expectations["validation_runtime"]["duckdb_memory_limit"]
            ).replace("'", "''")
            connection.execute(f"SET memory_limit='{memory_limit}'")
            connection.execute("PRAGMA disable_progress_bar")
            register_canonical_views(connection, table_paths)
            register_staging_views(connection, staging_root)
            validate_contract_rows(checks, connection, contract, table_paths)
            validate_uniform_provenance_and_authorization(
                checks, connection, contract, table_paths, manifest
            )
            mapping_policy = run_config["mapping_policy"]
            validate_participant_mappings(
                checks,
                connection,
                human_taxid=int(mapping_policy["frozen_taxid"]),
                protein_molecule_type_ac=str(
                    mapping_policy["protein_molecule_type_ac"]
                ),
            )
            validate_evidence_summaries(
                checks,
                connection,
                protein_molecule_type_ac=str(
                    mapping_policy["protein_molecule_type_ac"]
                ),
            )
            validate_huri_reconciliation(checks, connection)
            sifts_policy = run_config["sifts_policy"]
            validate_sifts_audit(
                checks,
                connection,
                human_taxid=int(mapping_policy["frozen_taxid"]),
                sifts_release=str(sifts_policy["declared_uniprot_release"]),
                frozen_release=str(sifts_policy["frozen_uniprot_release"]),
            )
            observed_metrics = collect_output_metrics(
                connection, run_config["provider_counts"]
            )
        finally:
            connection.close()

    expected_metrics = expectations["expected_metrics"]
    checks.require(
        "metrics.parquet_recomputation_matches_frozen_expectations",
        observed_metrics == expected_metrics,
        observed=observed_metrics,
        expected=expected_metrics,
    )
    normalized_manifest_metrics = normalize_manifest_metrics(manifest["metrics"])
    checks.require(
        "metrics.manifest_matches_parquet_recomputation",
        normalized_manifest_metrics == observed_metrics,
        observed=normalized_manifest_metrics,
        expected=observed_metrics,
    )

    construct_totals = observed_metrics.get("participant_totals", {})
    construct_ab = int(construct_totals.get("construct_a_or_b", 0))
    participant_total = int(construct_totals.get("participants", 0))
    construct_fraction = construct_ab / participant_total if participant_total else 0.0
    checks.warn(
        "blocker.evidence_gate.strict_construct_a_or_b_fraction",
        observed={
            "construct_a_or_b": construct_ab,
            "participants": participant_total,
            "fraction": construct_fraction,
            "blueprint_threshold": float(
                expectations["strict_construct_a_or_b_warning_threshold"]
            ),
        },
        detail=(
            "Frozen public records do not provide exact construct sequences and "
            "boundaries. Reference and canonical mappings are useful derived views, "
            "but none may be promoted to construct confidence A or B."
        ),
    )
    for blocker in expectations.get("known_blockers", []):
        checks.warn(
            f"blocker.{blocker['issue_id']}",
            observed=str(blocker["status"]),
            detail=str(blocker["reason"]),
        )

    manifest_sha = sha256_file(manifest_path)
    result = {
        "schema_version": 1,
        "gate_id": str(expectations["gate_id"]),
        "status": "pass" if checks.passed else "fail",
        "scope": scope,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reconciliation_root": root.as_posix(),
        "reconciliation_manifest": manifest_path.as_posix(),
        "reconciliation_manifest_sha256": manifest_sha,
        "expectation_config": expectation_path.as_posix(),
        "expectation_config_sha256": sha256_file(expectation_path),
        "counts": inventory_counts,
        "metrics": observed_metrics,
        "check_counts": checks.counts(),
        "checks": checks.records,
        "known_blockers": expectations.get("known_blockers", []),
        "interpretation": (
            "Pass certifies deterministic source reconciliation and honest uncertainty "
            "encoding. It does not satisfy the evidence gate's strict-construct, "
            "tested-universe, or release-aligned structural requirements."
        ),
        "authorizations": {
            "canonical_reconciliation_accepted": checks.passed,
            "benchmark_and_estimand_design": checks.passed,
            "strict_construct_benchmark": False,
            "label_construction": False,
            "structural_mapping": False,
            "model_training": False,
        },
    }
    return result


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate immutable primary reconciliation Parquet and semantics"
    )
    parser.add_argument("reconciliation_root", type=Path)
    parser.add_argument(
        "--expectations",
        type=Path,
        default=Path("configs/primary_reconciliation_validation_v1.yaml"),
    )
    parser.add_argument(
        "--allow-smoke",
        action="store_true",
        help="Validate only an explicitly named _smoke_* canonical output",
    )
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    root = args.reconciliation_root
    if not root.is_absolute():
        root = project_root / root
    expectation_path = args.expectations
    if not expectation_path.is_absolute():
        expectation_path = project_root / expectation_path
    expectation_path = expectation_path.resolve(strict=True)
    report = validate_reconciliation(
        project_root=project_root,
        reconciliation_root=root,
        expectation_path=expectation_path,
        allow_smoke=args.allow_smoke,
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
