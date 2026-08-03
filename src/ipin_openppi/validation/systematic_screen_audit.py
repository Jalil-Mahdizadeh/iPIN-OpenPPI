"""Independent integrity gate for the systematic-screen metadata audit."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import stat
from typing import Any, Mapping

import duckdb
import pyarrow.parquet as pq
import yaml

from ipin_openppi.benchmark import SYSTEMATIC_SCREEN_AUDIT_VERSION
from ipin_openppi.ingestion.common import (
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.validation.staging import Checks, _write_report


_SAFE_JSON_FIELD = re.compile(r"[A-Za-z0-9_]+")
_REQUIRED_WARNING_CODES = {
    "HURI_ATTEMPTED_UNIVERSE_UNRESOLVED",
    "STRICT_CONSTRUCT_COVERAGE_ZERO",
    "AUTHOR_CODE_REPOSITORY_LICENSE_UNRESOLVED",
}
_DOCUMENT_BOUNDARIES = {
    "acquisition_manifest": "data",
    "parse_manifest": "data/staging",
    "staging_validation_report": "artifacts/validation",
    "reconciliation_manifest": "data/canonical",
    "reconciliation_validation_report": "artifacts/validation",
    "source_policy": "configs",
    "evidence_schema": "schemas",
    "staging_schema": "schemas",
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


def _nested(document: Mapping[str, Any], dotted_path: str) -> Any:
    value: Any = document
    for component in dotted_path.split("."):
        if not isinstance(value, Mapping) or component not in value:
            raise KeyError(dotted_path)
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


def _json_field(name: str) -> str:
    if not _SAFE_JSON_FIELD.fullmatch(name):
        raise ValueError(f"Unsafe JSON field name: {name!r}")
    return f"json_extract_string(fields_json, '$.{name}')"


def _records(
    connection: duckdb.DuckDBPyConnection,
    sql: str,
    parameters: list[Any] | None = None,
) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, parameters or [])
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _scope_for_reports(
    audit_path: Path,
    validation_path: Path,
    *,
    allow_smoke: bool,
) -> str:
    audit_is_smoke = any(part.startswith("_smoke_") for part in audit_path.parts)
    validation_is_smoke = any(
        part.startswith("_smoke_") for part in validation_path.parts
    )
    if audit_path.parent != validation_path.parent:
        raise RuntimeError("Audit and validation reports must share one run directory")
    if audit_is_smoke != validation_is_smoke:
        raise RuntimeError("Audit and validation report scopes differ")
    if audit_is_smoke and not allow_smoke:
        raise RuntimeError("Validation of _smoke_* audit requires --allow-smoke")
    if allow_smoke and not audit_is_smoke:
        raise RuntimeError("--allow-smoke is restricted to _smoke_* reports")
    return "qualification_smoke" if audit_is_smoke else "production_full"


def _read_sidecar(path: Path) -> dict[str, Any]:
    sidecar = path.with_name(path.name + ".sha256")
    tokens = sidecar.read_text(encoding="utf-8").split()
    return {
        "path": sidecar.as_posix(),
        "sha256": tokens[0] if tokens else None,
        "filename": tokens[1] if len(tokens) > 1 else None,
    }


def _validate_audit_guardrails(
    checks: Checks,
    audit: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    expected_top_level = {
        "schema_version": 1,
        "audit_id": str(config["audit_id"]),
        "audit_version": SYSTEMATIC_SCREEN_AUDIT_VERSION,
        "task": str(config["task"]),
        "status": "complete",
        "scope": "metadata_and_semantics_only_no_label_or_split_construction",
        "label_construction_performed": False,
        "split_construction_performed": False,
        "structural_mapping_performed": False,
        "model_training_performed": False,
    }
    for key, expected in expected_top_level.items():
        observed = audit.get(key)
        checks.require(
            f"audit.{key}",
            observed == expected,
            observed=observed,
            expected=expected,
        )

    expected_authorizations = {
        "benchmark_estimand_policy_proposal": True,
        "label_construction": False,
        "split_construction": False,
        "structural_mapping": False,
        "model_training": False,
    }
    observed_authorizations = audit.get("authorizations")
    checks.require(
        "audit.authorizations",
        observed_authorizations == expected_authorizations,
        observed=observed_authorizations,
        expected=expected_authorizations,
    )

    requirements = {
        str(key): str(value)
        for key, value in config["systematic_universe_requirements"].items()
    }
    incomplete = {
        key: value
        for key, value in requirements.items()
        if value != "complete_pair_level"
    }
    expected_universe = {
        "complete_attempted_evaluable_universe_reconstructed": not incomplete,
        "required_field_count": len(requirements),
        "complete_pair_level_field_count": len(requirements) - len(incomplete),
        "incomplete_fields": incomplete,
    }
    observed_universe = audit.get("systematic_universe_assessment")
    checks.require(
        "semantics.systematic_universe_assessment",
        observed_universe == expected_universe
        and expected_universe["complete_attempted_evaluable_universe_reconstructed"]
        is False,
        observed=observed_universe,
        expected=expected_universe,
    )

    conclusion = audit.get("scientific_conclusion", {})
    decision = config["decision_policy"]
    decision_matches = isinstance(conclusion, Mapping) and all(
        conclusion.get(key) == expected for key, expected in decision.items()
    )
    negative_guardrails = {
        "explicit_panel_nondetections_are_universal_negatives": False,
        "unreported_space_iii_pairs_are_negatives": False,
        "table_15_never_detected_pairs_are_negatives": False,
        "intact_negative_records_define_primary_systematic_universe": False,
    }
    guardrails_match = isinstance(conclusion, Mapping) and all(
        conclusion.get(key) == expected for key, expected in negative_guardrails.items()
    )
    checks.require(
        "semantics.scientific_conclusion_guardrails",
        decision_matches and guardrails_match,
        observed=conclusion,
        expected={**dict(decision), **negative_guardrails},
    )

    warnings = audit.get("warnings", [])
    observed_codes = {
        str(record.get("code")) for record in warnings if isinstance(record, Mapping)
    }
    checks.require(
        "semantics.required_warning_codes",
        observed_codes == _REQUIRED_WARNING_CODES,
        observed=sorted(observed_codes),
        expected=sorted(_REQUIRED_WARNING_CODES),
    )
    external_review = audit.get("external_public_availability_review")
    checks.require(
        "semantics.external_public_availability_review",
        external_review == config["external_availability_review"],
        observed=external_review,
        expected=config["external_availability_review"],
    )


def _validate_runtime_and_provenance(
    *,
    checks: Checks,
    project_root: Path,
    audit: Mapping[str, Any],
    audit_path: Path,
    config: Mapping[str, Any],
    config_path: Path,
    scope: str,
) -> dict[str, Any]:
    sidecar = _read_sidecar(audit_path)
    audit_sha = sha256_file(audit_path)
    checks.require(
        "audit.sha256_sidecar",
        sidecar["sha256"] == audit_sha and sidecar["filename"] == audit_path.name,
        observed=sidecar,
        expected={"sha256": audit_sha, "filename": audit_path.name},
    )
    immutable = True
    for candidate in (audit_path, audit_path.with_name(audit_path.name + ".sha256")):
        info = candidate.stat(follow_symlinks=False)
        immutable = (
            immutable
            and not candidate.is_symlink()
            and stat.S_ISREG(info.st_mode)
            and not bool(info.st_mode & 0o222)
        )
    checks.require(
        "audit.immutable_regular_files",
        immutable,
        observed=immutable,
        expected=True,
    )

    expected_container = _resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
    )
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    active_sha = sha256_file(active_container)
    expected_sha = str(config["runtime"]["container_sha256"])
    expected_architecture = str(config["runtime"]["architecture"])
    runtime = audit.get("runtime", {})
    checks.require(
        "runtime.active_container",
        active_container == expected_container and active_sha == expected_sha,
        observed={
            "path": active_container.as_posix(),
            "sha256": active_sha,
        },
        expected={
            "path": expected_container.as_posix(),
            "sha256": expected_sha,
        },
    )
    checks.require(
        "runtime.architecture",
        platform.machine() == expected_architecture
        and runtime.get("architecture") == expected_architecture,
        observed={
            "host": platform.machine(),
            "audit": runtime.get("architecture"),
        },
        expected=expected_architecture,
    )
    checks.require(
        "runtime.audit_container_sha256",
        runtime.get("container_sif_sha256") == expected_sha,
        observed=runtime.get("container_sif_sha256"),
        expected=expected_sha,
    )

    config_sha = sha256_file(config_path)
    audit_inputs = audit.get("inputs", {})
    checks.require(
        "input.audit_config",
        audit_inputs.get("config") == config_path.relative_to(project_root).as_posix()
        and audit_inputs.get("config_sha256") == config_sha,
        observed={
            "path": audit_inputs.get("config"),
            "sha256": audit_inputs.get("config_sha256"),
        },
        expected={
            "path": config_path.relative_to(project_root).as_posix(),
            "sha256": config_sha,
        },
    )

    current_git = git_provenance(project_root)
    audit_git = audit.get("git", {})
    clean_requirement = (
        scope == "qualification_smoke"
        or audit_git.get("tracked_worktree_clean") is True
    )
    checks.require(
        "git.audit_commit_and_production_cleanliness",
        audit_git.get("commit") == current_git["commit"] and clean_requirement,
        observed={
            "audit": audit_git,
            "current_commit": current_git["commit"],
            "scope": scope,
        },
        expected={
            "same_commit": True,
            "production_audit_started_clean": True,
        },
    )
    return {
        "audit_report_sha256": audit_sha,
        "active_container_sha256": active_sha,
        "git": current_git,
    }


def _validate_documents_and_staged_files(
    *,
    checks: Checks,
    project_root: Path,
    audit: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, list[Path]]:
    audit_inputs = audit["inputs"]
    reported_documents = audit_inputs["documents"]
    for name, boundary_value in _DOCUMENT_BOUNDARIES.items():
        hash_key = f"{name}_sha256"
        configured_path = _resolve_inside(
            project_root,
            str(config["inputs"][name]),
            project_root / boundary_value,
        )
        info = configured_path.stat(follow_symlinks=False)
        observed = {
            "path": configured_path.as_posix(),
            "bytes": info.st_size,
            "sha256": sha256_file(configured_path),
        }
        expected = {
            "path": configured_path.as_posix(),
            "bytes": info.st_size,
            "sha256": str(config["inputs"][hash_key]),
        }
        checks.require(
            f"input.document.{name}",
            not configured_path.is_symlink()
            and stat.S_ISREG(info.st_mode)
            and observed == expected
            and reported_documents.get(name) == expected,
            observed={
                "actual": observed,
                "audit": reported_documents.get(name),
            },
            expected=expected,
        )

    expected_raw_ids = {str(value) for value in config["inputs"]["raw_asset_ids"]}
    reported_raw = audit_inputs["raw_assets"]
    checks.require(
        "input.raw_asset_inventory",
        set(reported_raw) == expected_raw_ids,
        observed=sorted(reported_raw),
        expected=sorted(expected_raw_ids),
    )
    for asset_id in sorted(expected_raw_ids & set(reported_raw)):
        record = reported_raw[asset_id]
        path = _resolve_inside(
            project_root,
            str(record["path"]),
            project_root / "data/raw",
        )
        info = path.stat(follow_symlinks=False)
        observed = {
            "asset_id": asset_id,
            "path": path.relative_to(project_root).as_posix(),
            "bytes": info.st_size,
            "sha256": sha256_file(path),
            "read_only": not bool(info.st_mode & 0o222),
        }
        checks.require(
            f"input.raw_asset.{asset_id}",
            not path.is_symlink() and stat.S_ISREG(info.st_mode) and observed == record,
            observed=observed,
            expected=record,
        )

    parse_path = _resolve_inside(
        project_root,
        str(config["inputs"]["parse_manifest"]),
        project_root / "data/staging",
    )
    parse_manifest = _load_json(parse_path)
    datasets: dict[str, list[Path]] = {}
    for key, dotted_path in config["inputs"]["dataset_summaries"].items():
        summary = _nested(parse_manifest, str(dotted_path))
        paths: list[Path] = []
        observed_files: list[dict[str, Any]] = []
        total_rows = 0
        for record in summary["files"]:
            path = _resolve_inside(
                project_root,
                str(record["path"]),
                project_root / "data/staging",
            )
            info = path.stat(follow_symlinks=False)
            rows = int(pq.ParquetFile(path).metadata.num_rows)
            observed = {
                "path": path.as_posix(),
                "bytes": info.st_size,
                "rows": rows,
                "sha256": sha256_file(path),
            }
            checks.require(
                f"input.staged_file.{key}.{path.name}",
                not path.is_symlink()
                and stat.S_ISREG(info.st_mode)
                and not bool(info.st_mode & 0o222)
                and observed
                == {
                    "path": str(record["path"]),
                    "bytes": int(record["bytes"]),
                    "rows": int(record["rows"]),
                    "sha256": str(record["sha256"]),
                },
                observed=observed,
                expected=record,
            )
            paths.append(path)
            observed_files.append(observed)
            total_rows += rows
        observed_summary = {
            "table": str(summary["table"]),
            "rows": total_rows,
            "parts": len(observed_files),
            "files": observed_files,
        }
        checks.require(
            f"input.staged_summary.{key}",
            total_rows == int(summary["rows"])
            and observed_summary == audit_inputs["staged_datasets"].get(key),
            observed=observed_summary,
            expected=audit_inputs["staged_datasets"].get(key),
        )
        datasets[str(key)] = paths
    return datasets


def _register_views(
    connection: duckdb.DuckDBPyConnection,
    datasets: Mapping[str, list[Path]],
) -> None:
    for key, paths in datasets.items():
        connection.read_parquet([path.as_posix() for path in paths]).create_view(
            f"v_{key}"
        )


def _value_counts(
    connection: duckdb.DuckDBPyConnection,
    *,
    dataset: str,
    field: str,
) -> dict[str, int]:
    expression = _json_field(field)
    records = _records(
        connection,
        f"SELECT {expression} AS source_value, count(*) AS n "
        "FROM v_huri_supplement WHERE source_dataset=? GROUP BY 1 ORDER BY 1",
        [dataset],
    )
    return {
        (
            "<blank>"
            if record["source_value"] in {None, ""}
            else str(record["source_value"])
        ): int(record["n"])
        for record in records
    }


def _recompute_metrics(
    connection: duckdb.DuckDBPyConnection,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    space = connection.execute(
        "SELECT count(*), count(DISTINCT ensembl_gene_id), "
        "sum(CASE WHEN in_space_3 IS TRUE THEN 1 ELSE 0 END), "
        "sum(CASE WHEN in_space_3 IS FALSE THEN 1 ELSE 0 END), "
        "sum(CASE WHEN in_space_3 IS NULL THEN 1 ELSE 0 END) FROM v_huri_space"
    ).fetchone()
    pair_view_rows = {
        str(dataset): int(rows)
        for dataset, rows in connection.execute(
            "SELECT source_dataset, count(*) FROM v_huri_pair_views GROUP BY 1"
        ).fetchall()
    }
    pair_view_label_rows = int(
        connection.execute(
            "SELECT sum(CASE WHEN label_authorized THEN 1 ELSE 0 END) "
            "FROM v_huri_pair_views"
        ).fetchone()[0]
    )
    evidence = connection.execute(
        "SELECT count(*), "
        "sum(CASE WHEN observation_state='positive' THEN 1 ELSE 0 END), "
        "sum(CASE WHEN observation_state='negative' THEN 1 ELSE 0 END) "
        "FROM v_huri_evidence"
    ).fetchone()
    evidence_states = _records(
        connection,
        "SELECT source_dataset, observation_state, search_space_state, "
        "selection_state, attempted_state, evaluability_state, technical_state, "
        "state_basis, count(*) AS n FROM v_huri_evidence GROUP BY ALL "
        "ORDER BY source_dataset, observation_state",
    )
    supplement_rows = {
        str(dataset): int(rows)
        for dataset, rows in connection.execute(
            "SELECT source_dataset, count(*) FROM v_huri_supplement "
            "GROUP BY 1 ORDER BY 1"
        ).fetchall()
    }

    panel_outcomes: dict[str, dict[str, int]] = {}
    panel_strata: dict[str, dict[str, dict[str, int]]] = {}
    for panel_name, panel in config["supplementary_panels"].items():
        outcome_field = panel.get("outcome_field")
        if outcome_field:
            panel_outcomes[str(panel_name)] = _value_counts(
                connection,
                dataset=str(panel["dataset"]),
                field=str(outcome_field),
            )
        strata = {
            str(field): _value_counts(
                connection,
                dataset=str(panel["dataset"]),
                field=str(field),
            )
            for field in panel.get("strata_fields", [])
        }
        if strata:
            panel_strata[str(panel_name)] = strata

    ad = _json_field("ad_orf_id")
    db = _json_field("db_orf_id")
    assay = _json_field("assay_version")
    source = _json_field("source")
    orientation = connection.execute(
        f"WITH pair_assays AS (SELECT {source} AS source_value, "
        f"{assay} AS assay_value, least({ad},{db}) AS pair_a, "
        f"greatest({ad},{db}) AS pair_b, count(*) AS n, "
        f"count(DISTINCT {ad} || '|' || {db}) AS orientations "
        "FROM v_huri_supplement "
        "WHERE source_dataset='huri_supplement_table_5' "
        "GROUP BY 1,2,3,4) SELECT count(*), "
        "sum(CASE WHEN n=2 AND orientations=2 THEN 1 ELSE 0 END) "
        "FROM pair_assays"
    ).fetchone()

    table_seven = connection.execute(
        f"SELECT count(*), "
        f"sum(array_length(string_split({_json_field('screens')}, ','))) "
        "FROM v_huri_supplement "
        "WHERE source_dataset='huri_supplement_table_7'"
    ).fetchone()
    table_eight = connection.execute(
        f"SELECT count(try_cast(nullif({_json_field('final_score')}, '') AS DOUBLE)) "
        "FROM v_huri_supplement "
        "WHERE source_dataset='huri_supplement_table_8'"
    ).fetchone()
    screen_terms = "+".join(
        f"cast({_json_field(f'in_screen_{index}')} AS INTEGER)"
        for index in range(1, 10)
    )
    assay_terms = "+".join(
        f"cast({_json_field(f'in_assay_v{index}')} AS INTEGER)" for index in range(1, 4)
    )
    table_nine = connection.execute(
        f"SELECT count(*), min({screen_terms}), max({screen_terms}), "
        f"sum({screen_terms}), sum({assay_terms}) FROM v_huri_supplement "
        "WHERE source_dataset='huri_supplement_table_9'"
    ).fetchone()
    table_nine_distribution = _records(
        connection,
        f"SELECT ({screen_terms}) AS detected_screens, "
        f"({assay_terms}) AS detected_assay_versions, count(*) AS positive_pairs "
        "FROM v_huri_supplement "
        "WHERE source_dataset='huri_supplement_table_9' GROUP BY ALL ORDER BY 1,2",
    )

    fusion = connection.execute(
        "SELECT count(*), "
        "sum(CASE WHEN NOT found_v1 AND NOT found_v2 AND NOT found_v3 THEN 1 ELSE 0 END), "
        "sum(CASE WHEN label_authorized THEN 1 ELSE 0 END) FROM v_huri_fusion"
    ).fetchone()
    intact_negative_states = _records(
        connection,
        "SELECT observation_state, search_space_state, selection_state, attempted_state, "
        "evaluability_state, technical_state, state_basis, count(*) AS n "
        "FROM v_intact_evidence WHERE observation_state='negative' GROUP BY ALL "
        "ORDER BY n DESC",
    )
    intact_negative = int(
        connection.execute(
            "SELECT count(*) FROM v_intact_evidence "
            "WHERE observation_state='negative'"
        ).fetchone()[0]
    )
    return {
        "huri_space": {
            "rows": int(space[0]),
            "unique_genes": int(space[1]),
            "in_space_iii_true": int(space[2]),
            "in_space_iii_false": int(space[3]),
            "in_space_iii_unknown": int(space[4]),
        },
        "huri_pair_view_rows": pair_view_rows,
        "huri_pair_view_label_authorized_rows": pair_view_label_rows,
        "huri_evidence": {
            "rows": int(evidence[0]),
            "positive": int(evidence[1]),
            "negative": int(evidence[2]),
            "state_combinations": evidence_states,
        },
        "supplement_table_rows": supplement_rows,
        "panel_outcome_counts": panel_outcomes,
        "panel_stratum_counts": panel_strata,
        "table_5_orientation": {
            "pair_assays": int(orientation[0]),
            "complete_two_orientation_pair_assays": int(orientation[1]),
        },
        "table_7": {
            "positive_pairs": int(table_seven[0]),
            "detection_mentions": int(table_seven[1]),
        },
        "table_8_numeric_scores": int(table_eight[0]),
        "table_9": {
            "positive_pairs": int(table_nine[0]),
            "minimum_detected_screens": int(table_nine[1]),
            "maximum_detected_screens": int(table_nine[2]),
            "screen_detection_mentions": int(table_nine[3]),
            "assay_version_detection_mentions": int(table_nine[4]),
            "detection_multiplicity": table_nine_distribution,
        },
        "table_15": {
            "rows": int(fusion[0]),
            "never_detected_any_version": int(fusion[1]),
            "label_authorized_rows": int(fusion[2]),
        },
        "intact_explicit_negatives": {
            "rows": intact_negative,
            "state_combinations": intact_negative_states,
        },
    }


def _validate_recomputed_metrics(
    checks: Checks,
    *,
    metrics: Mapping[str, Any],
    audit: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    expected = config["expected"]
    frozen_observed = {
        "huri_space_rows": metrics["huri_space"]["rows"],
        "huri_space_iii_true": metrics["huri_space"]["in_space_iii_true"],
        "huri_space_iii_false": metrics["huri_space"]["in_space_iii_false"],
        "huri_evidence_rows": metrics["huri_evidence"]["rows"],
        "huri_evidence_positive": metrics["huri_evidence"]["positive"],
        "huri_evidence_negative": metrics["huri_evidence"]["negative"],
        "table_5_complete_two_orientation_pair_assays": metrics["table_5_orientation"][
            "complete_two_orientation_pair_assays"
        ],
        "table_7_detection_mentions": metrics["table_7"]["detection_mentions"],
        "table_8_numeric_scores": metrics["table_8_numeric_scores"],
        "table_9_screen_detection_mentions": metrics["table_9"][
            "screen_detection_mentions"
        ],
        "table_9_assay_version_detection_mentions": metrics["table_9"][
            "assay_version_detection_mentions"
        ],
        "table_15_rows": metrics["table_15"]["rows"],
        "table_15_never_detected_any_version": metrics["table_15"][
            "never_detected_any_version"
        ],
        "table_15_label_authorized": metrics["table_15"]["label_authorized_rows"],
        "intact_explicit_negative_rows": metrics["intact_explicit_negatives"]["rows"],
    }
    frozen_expected = {key: int(expected[key]) for key in frozen_observed}
    checks.require(
        "metrics.parquet_recomputation_matches_frozen_expectations",
        frozen_observed == frozen_expected
        and metrics["huri_pair_view_rows"]
        == {
            str(key): int(value)
            for key, value in expected["huri_pair_view_rows"].items()
        }
        and metrics["huri_pair_view_label_authorized_rows"] == 0,
        observed={
            "scalars": frozen_observed,
            "pair_views": metrics["huri_pair_view_rows"],
            "pair_view_label_authorized_rows": metrics[
                "huri_pair_view_label_authorized_rows"
            ],
        },
        expected={
            "scalars": frozen_expected,
            "pair_views": expected["huri_pair_view_rows"],
            "pair_view_label_authorized_rows": 0,
        },
    )
    checks.require(
        "metrics.panel_outcomes_match_frozen_expectations",
        metrics["panel_outcome_counts"]
        == {
            str(panel): {str(key): int(value) for key, value in counts.items()}
            for panel, counts in expected["panel_outcome_counts"].items()
        },
        observed=metrics["panel_outcome_counts"],
        expected=expected["panel_outcome_counts"],
    )
    expected_supplement = {
        str(key): int(value) for key, value in expected["supplement_table_rows"].items()
    }
    observed_expected_supplement = {
        key: metrics["supplement_table_rows"].get(key) for key in expected_supplement
    }
    checks.require(
        "metrics.supplement_rows_match_frozen_expectations",
        observed_expected_supplement == expected_supplement,
        observed=observed_expected_supplement,
        expected=expected_supplement,
    )

    reported = audit["metrics"]
    reported_pair_rows = {
        str(record["source_dataset"]): int(record["rows"])
        for record in reported["huri_pair_views"]
    }
    reported_panel_outcomes = {
        str(panel): dict(reported["outcome_panels"][str(panel)]["outcome_counts"])
        for panel in metrics["panel_outcome_counts"]
    }
    reported_panel_strata = {
        str(panel): dict(reported["outcome_panels"][str(panel)]["stratum_counts"])
        for panel in metrics["panel_stratum_counts"]
    }
    checks.require(
        "metrics.audit_core_matches_independent_recomputation",
        reported["huri_space_membership"]["rows"] == metrics["huri_space"]["rows"]
        and reported["huri_space_membership"]["unique_genes"]
        == metrics["huri_space"]["unique_genes"]
        and reported["huri_space_membership"]["in_space_iii_true"]
        == metrics["huri_space"]["in_space_iii_true"]
        and reported["huri_space_membership"]["in_space_iii_false"]
        == metrics["huri_space"]["in_space_iii_false"]
        and reported["huri_space_membership"]["in_space_iii_unknown"]
        == metrics["huri_space"]["in_space_iii_unknown"]
        and reported_pair_rows == metrics["huri_pair_view_rows"]
        and reported["huri_evidence"] == metrics["huri_evidence"]
        and reported["supplement_table_rows"] == metrics["supplement_table_rows"]
        and reported_panel_outcomes == metrics["panel_outcome_counts"]
        and reported_panel_strata == metrics["panel_stratum_counts"],
        observed={
            "pair_views": reported_pair_rows,
            "panel_outcomes": reported_panel_outcomes,
            "panel_strata": reported_panel_strata,
        },
        expected={
            "pair_views": metrics["huri_pair_view_rows"],
            "panel_outcomes": metrics["panel_outcome_counts"],
            "panel_strata": metrics["panel_stratum_counts"],
        },
    )

    positive_metadata = reported["positive_screen_metadata"]
    reported_positive = {
        "table_7": {
            "positive_pairs": positive_metadata["table_7_test_space_positive_pairs"],
            "detection_mentions": positive_metadata["table_7_detection_mentions"],
        },
        "table_9": {
            "positive_pairs": positive_metadata["table_9_huri_positive_pairs"],
            "minimum_detected_screens": positive_metadata[
                "table_9_min_detected_screens"
            ],
            "maximum_detected_screens": positive_metadata[
                "table_9_max_detected_screens"
            ],
            "screen_detection_mentions": positive_metadata[
                "table_9_screen_detection_mentions"
            ],
            "assay_version_detection_mentions": positive_metadata[
                "table_9_assay_version_detection_mentions"
            ],
            "detection_multiplicity": positive_metadata[
                "table_9_detection_multiplicity"
            ],
        },
    }
    checks.require(
        "metrics.audit_positive_detection_metadata_matches_recomputation",
        reported_positive["table_7"] == metrics["table_7"]
        and reported_positive["table_9"] == metrics["table_9"]
        and positive_metadata["negative_or_failed_opportunities_enumerated"] is False,
        observed={
            **reported_positive,
            "negative_or_failed_opportunities_enumerated": positive_metadata[
                "negative_or_failed_opportunities_enumerated"
            ],
        },
        expected={
            "table_7": metrics["table_7"],
            "table_9": metrics["table_9"],
            "negative_or_failed_opportunities_enumerated": False,
        },
    )
    checks.require(
        "metrics.audit_control_and_negative_panels_match_recomputation",
        reported["table_5_orientation_coverage"] == metrics["table_5_orientation"]
        and reported["table_15_detection_flags"]["rows"] == metrics["table_15"]["rows"]
        and reported["table_15_detection_flags"]["never_detected_any_version"]
        == metrics["table_15"]["never_detected_any_version"]
        and reported["table_15_detection_flags"]["label_authorized_rows"]
        == metrics["table_15"]["label_authorized_rows"]
        and reported["intact_explicit_negatives"]["rows"]
        == metrics["intact_explicit_negatives"]["rows"]
        and reported["intact_explicit_negatives"]["state_combinations"]
        == metrics["intact_explicit_negatives"]["state_combinations"]
        and reported["outcome_panels"]["table_8"]["numeric_score_summary"]["numeric"]
        == metrics["table_8_numeric_scores"],
        observed={
            "table_5": reported["table_5_orientation_coverage"],
            "table_15": reported["table_15_detection_flags"],
            "intact": reported["intact_explicit_negatives"],
            "table_8_numeric": reported["outcome_panels"]["table_8"][
                "numeric_score_summary"
            ]["numeric"],
        },
        expected={
            "table_5": metrics["table_5_orientation"],
            "table_15": metrics["table_15"],
            "intact": metrics["intact_explicit_negatives"],
            "table_8_numeric": metrics["table_8_numeric_scores"],
        },
    )

    conclusion = audit["scientific_conclusion"]
    expected_difference = int(metrics["table_9"]["positive_pairs"]) - int(
        metrics["huri_pair_view_rows"]["HuRI"]
    )
    conclusion_counts = {
        "main_huri_mitab_negative_records": metrics["huri_evidence"]["negative"],
        "main_huri_pair_view_rows": metrics["huri_pair_view_rows"]["HuRI"],
        "supplement_table_9_positive_rows": metrics["table_9"]["positive_pairs"],
        "provider_to_supplement_positive_row_difference": expected_difference,
    }
    checks.require(
        "metrics.scientific_conclusion_counts",
        all(conclusion.get(key) == value for key, value in conclusion_counts.items()),
        observed={key: conclusion.get(key) for key in conclusion_counts},
        expected=conclusion_counts,
    )


def validate_systematic_screen_audit(
    *,
    project_root: Path,
    config_path: Path,
    audit_path: Path,
    validation_path: Path,
    allow_smoke: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    config_path = _resolve_inside(
        project_root,
        config_path,
        project_root / "configs",
    )
    config = _load_yaml(config_path)
    audit_path = _resolve_inside(
        project_root,
        audit_path,
        project_root / "artifacts/validation",
    )
    validation_path = _resolve_inside(
        project_root,
        validation_path,
        project_root / "artifacts/validation",
        strict=False,
    )
    scope = _scope_for_reports(
        audit_path,
        validation_path,
        allow_smoke=allow_smoke,
    )
    if scope == "production_full":
        configured_audit = _resolve_inside(
            project_root,
            str(config["outputs"]["audit_report"]),
            project_root / "artifacts/validation",
        )
        configured_validation = _resolve_inside(
            project_root,
            str(config["outputs"]["validation_report"]),
            project_root / "artifacts/validation",
            strict=False,
        )
        if audit_path != configured_audit or validation_path != configured_validation:
            raise RuntimeError(
                "Production report paths differ from audit configuration"
            )

    checks = Checks()
    audit = _load_json(audit_path)
    _validate_audit_guardrails(checks, audit, config)
    provenance = _validate_runtime_and_provenance(
        checks=checks,
        project_root=project_root,
        audit=audit,
        audit_path=audit_path,
        config=config,
        config_path=config_path,
        scope=scope,
    )
    datasets = _validate_documents_and_staged_files(
        checks=checks,
        project_root=project_root,
        audit=audit,
        config=config,
    )

    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            f"SET memory_limit='{config['runtime']['duckdb_memory_limit']}'"
        )
        connection.execute("PRAGMA disable_progress_bar")
        _register_views(connection, datasets)
        metrics = _recompute_metrics(connection, config)
    finally:
        connection.close()
    _validate_recomputed_metrics(
        checks,
        metrics=metrics,
        audit=audit,
        config=config,
    )

    source_inventory = audit["source_inventory"]
    checks.require(
        "source_inventory.frozen_document_structure",
        source_inventory["supplementary_archive"]["scientific_table_count"]
        == int(config["expected"]["archive_scientific_tables"])
        and source_inventory["supplementary_methods_pdf"]["pages"]
        == int(config["expected"]["methods_pdf_pages"])
        and source_inventory["supplementary_table_guide_pdf"]["pages"]
        == int(config["expected"]["table_guide_pdf_pages"]),
        observed={
            "archive_scientific_tables": source_inventory["supplementary_archive"][
                "scientific_table_count"
            ],
            "methods_pdf_pages": source_inventory["supplementary_methods_pdf"]["pages"],
            "table_guide_pdf_pages": source_inventory["supplementary_table_guide_pdf"][
                "pages"
            ],
        },
        expected={
            "archive_scientific_tables": int(
                config["expected"]["archive_scientific_tables"]
            ),
            "methods_pdf_pages": int(config["expected"]["methods_pdf_pages"]),
            "table_guide_pdf_pages": int(config["expected"]["table_guide_pdf_pages"]),
        },
    )

    checks.warn(
        "blocker.ISSUE-0003",
        observed="attempted_evaluable_pair_universe_unresolved",
        detail=(
            "Integrity validation passed for the public metadata audit, but the "
            "complete HuRI selected/attempted/evaluable opportunity log remains absent."
        ),
    )
    checks.warn(
        "blocker.ISSUE-0005",
        observed="strict_construct_a_or_b_coverage_zero",
        detail=(
            "The strict construct benchmark remains unavailable; reference-sequence "
            "mappings may not be promoted to construct confidence A or B."
        ),
    )
    checks.warn(
        "blocker.external_author_repository_license",
        observed="no_license_file",
        detail=(
            "The reviewed author repository is metadata evidence only and was not "
            "ingested as a project data source."
        ),
    )

    result = {
        "schema_version": 1,
        "gate_id": "systematic_screen_metadata_audit_integrity_v1",
        "status": "pass" if checks.passed else "fail",
        "scope": scope,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_report": audit_path.as_posix(),
        "audit_report_sha256": provenance["audit_report_sha256"],
        "config": config_path.as_posix(),
        "config_sha256": sha256_file(config_path),
        "runtime": {
            "container_sif_sha256": provenance["active_container_sha256"],
            "architecture": platform.machine(),
            "duckdb_version": duckdb.__version__,
        },
        "git": provenance["git"],
        "independently_recomputed_metrics": metrics,
        "check_counts": checks.counts(),
        "checks": checks.records,
        "interpretation": (
            "Pass certifies integrity, reproducibility, and conservative semantics of "
            "the metadata audit. It does not establish a complete tested universe, "
            "authorize binary negatives, satisfy strict construct coverage, or "
            "authorize label, split, structure, or model construction."
        ),
        "authorizations": {
            "systematic_screen_metadata_audit_accepted": checks.passed,
            "benchmark_estimand_policy_proposal": checks.passed,
            "label_construction": False,
            "split_construction": False,
            "structural_mapping": False,
            "model_training": False,
        },
    }
    return result


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Independently validate the systematic-screen metadata audit"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/systematic_screen_metadata_audit_v1.yaml"),
    )
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-smoke", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    config_path = args.config
    if not config_path.is_absolute():
        config_path = project_root / config_path
    config_path = config_path.resolve(strict=True)
    config = _load_yaml(config_path)

    audit_path = args.audit_report or Path(config["outputs"]["audit_report"])
    validation_path = args.report or Path(config["outputs"]["validation_report"])
    if not audit_path.is_absolute():
        audit_path = project_root / audit_path
    if not validation_path.is_absolute():
        validation_path = project_root / validation_path

    report = validate_systematic_screen_audit(
        project_root=project_root,
        config_path=config_path,
        audit_path=audit_path,
        validation_path=validation_path,
        allow_smoke=args.allow_smoke,
    )
    _write_report(validation_path, report, project_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
