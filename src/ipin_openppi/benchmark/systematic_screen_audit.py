"""Audit whether public systematic-screen evidence supports benchmark labels.

This module is deliberately label-free.  It inventories immutable source metadata,
classifies source-reported outcome panels by their original scope, and tests whether
the complete selected/attempted/evaluable HuRI opportunity universe is reconstructable.
"""

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
import zipfile

import duckdb
import pyarrow.parquet as pq
from pypdf import PdfReader
import yaml

from ipin_openppi.benchmark import SYSTEMATIC_SCREEN_AUDIT_VERSION
from ipin_openppi.ingestion.common import (
    git_provenance,
    load_asset_index,
    project_root_from,
    require_apptainer,
    verify_asset,
)
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.validation.staging import _write_report


_SAFE_JSON_FIELD = re.compile(r"[A-Za-z0-9_]+")
_MEMBER_RE = re.compile(r"Supplementary Table (\d+)\.(txt|xls|xlsx)$", re.I)
_PDF_TERMS = (
    "attempt",
    "evaluable",
    "screen",
    "test space",
    "negative",
    "autoactiv",
    "technical",
    "retest",
    "selected",
    "candidate",
    "orientation",
    "assay version",
    "pairwise",
)


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


def _nested(document: Mapping[str, Any], dotted_path: str) -> Any:
    value: Any = document
    for component in dotted_path.split("."):
        if not isinstance(value, Mapping) or component not in value:
            raise KeyError(dotted_path)
        value = value[component]
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
        raise RuntimeError(
            f"Path escapes required boundary {boundary}: {resolved}"
        ) from exc
    return resolved


def _validate_config(config: Mapping[str, Any]) -> None:
    if int(config.get("schema_version", -1)) != 1:
        raise RuntimeError("Unsupported systematic-screen audit configuration schema")
    if config.get("audit_version") != SYSTEMATIC_SCREEN_AUDIT_VERSION:
        raise RuntimeError("Audit configuration and code versions differ")
    authorization = config.get("authorization", {})
    if authorization.get("source_metadata_audit") is not True:
        raise RuntimeError("Source metadata audit is not authorized")
    if authorization.get("benchmark_estimand_policy_design") is not True:
        raise RuntimeError("Benchmark/estimand policy design is not authorized")
    prohibited = (
        "label_construction",
        "split_construction",
        "structural_mapping",
        "model_training",
    )
    enabled = [key for key in prohibited if authorization.get(key) is not False]
    if enabled:
        raise RuntimeError(f"Audit configuration enables prohibited actions: {enabled}")
    decision = config.get("decision_policy", {})
    for key in (
        "label_construction_authorized",
        "split_construction_authorized",
        "model_training_authorized",
    ):
        if decision.get(key) is not False:
            raise RuntimeError(f"Decision policy must keep {key}=false")
    memory_limit = str(config["runtime"]["duckdb_memory_limit"])
    if not re.fullmatch(r"[1-9][0-9]*(?:MB|GB)", memory_limit):
        raise RuntimeError("DuckDB memory limit must be an explicit MB or GB value")


def classify_y2h_score(value: str) -> str:
    """Return the conservative state for source Y2H score tokens."""

    mapping = {
        "1": "observed_positive",
        "0": "conditional_assay_negative",
        "NA": "technical_invalid",
        "AA": "technical_autoactivator",
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"Unexpected Y2H score token: {value!r}") from exc


def classify_binary_panel_result(value: str) -> str:
    """Return the conservative state for orthogonal binary-result tokens."""

    mapping = {
        "1.0": "observed_positive",
        "0.0": "conditional_assay_negative",
        "": "unresolved_missing_or_invalid",
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"Unexpected binary panel result token: {value!r}") from exc


def assess_universe_completeness(
    requirements: Mapping[str, str],
) -> dict[str, Any]:
    """Assess whether every required opportunity field is complete pair-level data."""

    complete_token = "complete_pair_level"
    incomplete = {
        key: value for key, value in requirements.items() if value != complete_token
    }
    return {
        "complete_attempted_evaluable_universe_reconstructed": not incomplete,
        "required_field_count": len(requirements),
        "complete_pair_level_field_count": len(requirements) - len(incomplete),
        "incomplete_fields": incomplete,
    }


def _require_hash(path: Path, expected: str) -> dict[str, Any]:
    observed = sha256_file(path)
    if observed != expected:
        raise RuntimeError(f"SHA-256 mismatch for {path}: {observed} != {expected}")
    return {
        "path": path.as_posix(),
        "bytes": path.stat(follow_symlinks=False).st_size,
        "sha256": observed,
    }


def _input_documents(
    project_root: Path, config: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Path]]:
    inputs = config["inputs"]
    path_specs = {
        "acquisition_manifest": ("acquisition_manifest_sha256", project_root / "data"),
        "parse_manifest": ("parse_manifest_sha256", project_root / "data/staging"),
        "staging_validation_report": (
            "staging_validation_report_sha256",
            project_root / "artifacts/validation",
        ),
        "reconciliation_manifest": (
            "reconciliation_manifest_sha256",
            project_root / "data/canonical",
        ),
        "reconciliation_validation_report": (
            "reconciliation_validation_report_sha256",
            project_root / "artifacts/validation",
        ),
        "source_policy": ("source_policy_sha256", project_root / "configs"),
        "evidence_schema": ("evidence_schema_sha256", project_root / "schemas"),
        "staging_schema": ("staging_schema_sha256", project_root / "schemas"),
    }
    verified: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    for name, (hash_key, boundary) in path_specs.items():
        path = _resolve_inside(project_root, str(inputs[name]), boundary)
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Input must be a regular non-link file: {path}")
        verified[name] = _require_hash(path, str(inputs[hash_key]))
        paths[name] = path

    parse_manifest = _load_json(paths["parse_manifest"])
    if parse_manifest.get("status") != "complete":
        raise RuntimeError("Parse manifest is not complete")
    if parse_manifest.get("label_construction_performed") is not False:
        raise RuntimeError("Parse manifest indicates label construction")
    if parse_manifest.get("model_training_performed") is not False:
        raise RuntimeError("Parse manifest indicates model training")

    staging_validation = _load_json(paths["staging_validation_report"])
    if staging_validation.get("status") != "pass":
        raise RuntimeError("Staging validation did not pass")
    if (
        staging_validation.get("authorizations", {}).get("label_construction")
        is not False
    ):
        raise RuntimeError("Staging validation unexpectedly authorizes labels")

    reconciliation = _load_json(paths["reconciliation_manifest"])
    if reconciliation.get("status") != "complete":
        raise RuntimeError("Reconciliation manifest is not complete")
    for key in ("label_construction_performed", "model_training_performed"):
        if reconciliation.get(key) is not False:
            raise RuntimeError(f"Reconciliation manifest indicates {key}")
    reconciliation_validation = _load_json(paths["reconciliation_validation_report"])
    if reconciliation_validation.get("status") != "pass":
        raise RuntimeError("Reconciliation validation did not pass")

    return parse_manifest, verified, paths


def _verify_dataset_summaries(
    *,
    project_root: Path,
    parse_manifest: Mapping[str, Any],
    summary_paths: Mapping[str, str],
) -> dict[str, dict[str, Any]]:
    boundary = (project_root / "data/staging").resolve(strict=True)
    results: dict[str, dict[str, Any]] = {}
    for key, dotted_path in summary_paths.items():
        summary = _nested(parse_manifest, str(dotted_path))
        if not isinstance(summary, Mapping):
            raise RuntimeError(f"Dataset summary is not a mapping: {dotted_path}")
        records = summary.get("files", [])
        if not records:
            raise RuntimeError(f"Dataset summary contains no files: {dotted_path}")
        files: list[dict[str, Any]] = []
        observed_rows = 0
        for record in records:
            path = _resolve_inside(project_root, str(record["path"]), boundary)
            info = path.stat(follow_symlinks=False)
            if path.is_symlink() or not stat.S_ISREG(info.st_mode):
                raise RuntimeError(
                    f"Staged input is not a regular non-link file: {path}"
                )
            if info.st_mode & 0o222:
                raise RuntimeError(f"Staged input became writable: {path}")
            rows = int(pq.ParquetFile(path).metadata.num_rows)
            digest = sha256_file(path)
            observed = {
                "path": path.as_posix(),
                "bytes": info.st_size,
                "rows": rows,
                "sha256": digest,
            }
            expected = {
                "path": str(record["path"]),
                "bytes": int(record["bytes"]),
                "rows": int(record["rows"]),
                "sha256": str(record["sha256"]),
            }
            if observed != expected:
                raise RuntimeError(
                    f"Staged file differs from parse manifest: {observed} != {expected}"
                )
            files.append(observed)
            observed_rows += rows
        if observed_rows != int(summary["rows"]):
            raise RuntimeError(f"Dataset row total differs from summary: {dotted_path}")
        results[str(key)] = {
            "table": str(summary["table"]),
            "rows": observed_rows,
            "parts": len(files),
            "files": files,
        }
    return results


def _verify_raw_assets(
    *, project_root: Path, acquisition_manifest: Path, asset_ids: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, Path]]:
    _, assets = load_asset_index(
        project_root, acquisition_manifest.relative_to(project_root)
    )
    verified: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    for asset_id in asset_ids:
        if asset_id not in assets:
            raise RuntimeError(
                f"Raw asset is absent from acquisition manifest: {asset_id}"
            )
        asset = assets[asset_id]
        verified[asset_id] = verify_asset(asset)
        paths[asset_id] = asset.path
    return verified, paths


def _pdf_keyword_inventory(path: Path) -> dict[str, Any]:
    reader = PdfReader(str(path))
    keyword_pages: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").casefold()
        hits = {term: text.count(term) for term in _PDF_TERMS if term in text}
        if hits:
            keyword_pages.append({"page": page_number, "hits": hits})
    return {"pages": len(reader.pages), "keyword_pages": keyword_pages}


def _archive_inventory(path: Path) -> dict[str, Any]:
    table_members: dict[int, dict[str, Any]] = {}
    ignored_members = 0
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir() or info.filename.startswith("__MACOSX/"):
                ignored_members += 1
                continue
            match = _MEMBER_RE.search(info.filename)
            if not match:
                raise RuntimeError(
                    f"Unexpected scientific archive member: {info.filename}"
                )
            table_number = int(match.group(1))
            if table_number in table_members:
                raise RuntimeError(f"Duplicate supplementary table: {table_number}")
            table_members[table_number] = {
                "member": info.filename,
                "format": match.group(2).casefold(),
                "bytes": info.file_size,
            }
    expected = set(range(1, 30))
    if set(table_members) != expected:
        raise RuntimeError(
            f"Supplementary table inventory mismatch: {sorted(table_members)}"
        )
    return {
        "scientific_table_count": len(table_members),
        "tables": {str(key): value for key, value in sorted(table_members.items())},
        "ignored_archive_metadata_members": ignored_members,
    }


def _register_views(
    connection: duckdb.DuckDBPyConnection,
    datasets: Mapping[str, Mapping[str, Any]],
) -> None:
    for key, summary in datasets.items():
        paths = [str(record["path"]) for record in summary["files"]]
        connection.read_parquet(paths).create_view(f"v_{key}")


def _records(
    connection: duckdb.DuckDBPyConnection, sql: str, parameters: list[Any] | None = None
) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, parameters or [])
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _json_field(name: str) -> str:
    if not _SAFE_JSON_FIELD.fullmatch(name):
        raise ValueError(f"Unsafe JSON field name: {name!r}")
    return f"json_extract_string(fields_json, '$.{name}')"


def _panel_metrics(
    connection: duckdb.DuckDBPyConnection,
    panel_config: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for panel_name, panel in panel_config.items():
        dataset = str(panel["dataset"])
        rows = int(
            connection.execute(
                "SELECT count(*) FROM v_huri_supplement WHERE source_dataset=?",
                [dataset],
            ).fetchone()[0]
        )
        result: dict[str, Any] = {
            "dataset": dataset,
            "rows": rows,
            "assay": panel["assay"],
            "scope": panel["scope"],
            "unit": panel["unit"],
            "admissible_use": panel["admissible_use"],
            "label_authorized": False,
        }
        outcome_field = panel.get("outcome_field")
        if outcome_field:
            expression = _json_field(str(outcome_field))
            counts = _records(
                connection,
                f"SELECT {expression} AS source_value, count(*) AS n "
                "FROM v_huri_supplement WHERE source_dataset=? "
                "GROUP BY 1 ORDER BY 1",
                [dataset],
            )
            normalized = {
                (
                    "<blank>"
                    if record["source_value"] in {None, ""}
                    else str(record["source_value"])
                ): int(record["n"])
                for record in counts
            }
            expected_tokens = set(panel.get("outcome_semantics", {}))
            if set(normalized) != expected_tokens:
                raise RuntimeError(
                    f"Unexpected outcome tokens for {panel_name}: {normalized}"
                )
            result["outcome_counts"] = normalized
            result["outcome_semantics"] = dict(panel["outcome_semantics"])
        score_field = panel.get("score_field")
        if score_field:
            expression = _json_field(str(score_field))
            numeric = connection.execute(
                f"SELECT count(try_cast(nullif({expression}, '') AS DOUBLE)), "
                f"count(*) - count(try_cast(nullif({expression}, '') AS DOUBLE)), "
                f"min(try_cast(nullif({expression}, '') AS DOUBLE)), "
                f"max(try_cast(nullif({expression}, '') AS DOUBLE)) "
                "FROM v_huri_supplement WHERE source_dataset=?",
                [dataset],
            ).fetchone()
            result["numeric_score_summary"] = {
                "numeric": int(numeric[0]),
                "missing_or_nonnumeric": int(numeric[1]),
                "minimum": float(numeric[2]) if numeric[2] is not None else None,
                "maximum": float(numeric[3]) if numeric[3] is not None else None,
                "source_binary_result_field_present": False,
            }
        strata: dict[str, dict[str, int]] = {}
        for field in panel.get("strata_fields", []):
            expression = _json_field(str(field))
            counts = _records(
                connection,
                f"SELECT {expression} AS source_value, count(*) AS n "
                "FROM v_huri_supplement WHERE source_dataset=? "
                "GROUP BY 1 ORDER BY 1",
                [dataset],
            )
            strata[str(field)] = {
                (
                    "<blank>"
                    if record["source_value"] in {None, ""}
                    else str(record["source_value"])
                ): int(record["n"])
                for record in counts
            }
        if strata:
            result["stratum_counts"] = strata
        output[str(panel_name)] = result
    return output


def _collect_metrics(
    connection: duckdb.DuckDBPyConnection,
    panels: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    space = connection.execute(
        "SELECT count(*), count(DISTINCT ensembl_gene_id), "
        "sum(CASE WHEN in_space_3 IS TRUE THEN 1 ELSE 0 END), "
        "sum(CASE WHEN in_space_3 IS FALSE THEN 1 ELSE 0 END), "
        "sum(CASE WHEN in_space_3 IS NULL THEN 1 ELSE 0 END) FROM v_huri_space"
    ).fetchone()
    pair_views = _records(
        connection,
        "SELECT source_dataset, count(*) AS rows, "
        "count(DISTINCT unordered_pair_id) AS unique_unordered_pairs, "
        "sum(CASE WHEN self_pair THEN 1 ELSE 0 END) AS self_pairs, "
        "sum(CASE WHEN label_authorized THEN 1 ELSE 0 END) AS label_authorized_rows "
        "FROM v_huri_pair_views GROUP BY 1 ORDER BY 1",
    )
    evidence_states = _records(
        connection,
        "SELECT source_dataset, observation_state, search_space_state, "
        "selection_state, attempted_state, evaluability_state, technical_state, "
        "state_basis, count(*) AS n FROM v_huri_evidence GROUP BY ALL "
        "ORDER BY source_dataset, observation_state",
    )
    evidence_totals = connection.execute(
        "SELECT count(*), "
        "sum(CASE WHEN observation_state='positive' THEN 1 ELSE 0 END), "
        "sum(CASE WHEN observation_state='negative' THEN 1 ELSE 0 END) "
        "FROM v_huri_evidence"
    ).fetchone()
    supplement_rows = {
        str(dataset): int(rows)
        for dataset, rows in connection.execute(
            "SELECT source_dataset, count(*) FROM v_huri_supplement "
            "GROUP BY 1 ORDER BY 1"
        ).fetchall()
    }
    panel_metrics = _panel_metrics(connection, panels)

    table_seven = connection.execute(
        f"SELECT count(*), "
        f"sum(array_length(string_split({_json_field('screens')}, ','))) "
        "FROM v_huri_supplement "
        "WHERE source_dataset='huri_supplement_table_7'"
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

    ad = _json_field("ad_orf_id")
    db = _json_field("db_orf_id")
    assay = _json_field("assay_version")
    source = _json_field("source")
    orientation = connection.execute(
        f"WITH pair_assays AS (SELECT {source} AS source_value, {assay} AS assay_value, "
        f"least({ad},{db}) AS pair_a, greatest({ad},{db}) AS pair_b, count(*) AS n, "
        f"count(DISTINCT {ad} || '|' || {db}) AS orientations "
        "FROM v_huri_supplement WHERE source_dataset='huri_supplement_table_5' "
        "GROUP BY 1,2,3,4) SELECT count(*), "
        "sum(CASE WHEN n=2 AND orientations=2 THEN 1 ELSE 0 END) FROM pair_assays"
    ).fetchone()
    table_five_orientation = {
        "pair_assays": int(orientation[0]),
        "complete_two_orientation_pair_assays": int(orientation[1]),
    }

    fusion_patterns = _records(
        connection,
        "SELECT found_v1, found_v2, found_v3, count(*) AS n FROM v_huri_fusion "
        "GROUP BY ALL ORDER BY found_v1, found_v2, found_v3",
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
    intact_negative_count = int(
        connection.execute(
            "SELECT count(*) FROM v_intact_evidence WHERE observation_state='negative'"
        ).fetchone()[0]
    )

    return {
        "huri_space_membership": {
            "rows": int(space[0]),
            "unique_genes": int(space[1]),
            "in_space_iii_true": int(space[2]),
            "in_space_iii_false": int(space[3]),
            "in_space_iii_unknown": int(space[4]),
            "unit": "gene_membership_not_pair_opportunity",
        },
        "huri_pair_views": pair_views,
        "huri_evidence": {
            "rows": int(evidence_totals[0]),
            "positive": int(evidence_totals[1]),
            "negative": int(evidence_totals[2]),
            "state_combinations": evidence_states,
        },
        "supplement_table_rows": supplement_rows,
        "outcome_panels": panel_metrics,
        "positive_screen_metadata": {
            "table_7_test_space_positive_pairs": int(table_seven[0]),
            "table_7_detection_mentions": int(table_seven[1]),
            "table_9_huri_positive_pairs": int(table_nine[0]),
            "table_9_min_detected_screens": int(table_nine[1]),
            "table_9_max_detected_screens": int(table_nine[2]),
            "table_9_screen_detection_mentions": int(table_nine[3]),
            "table_9_assay_version_detection_mentions": int(table_nine[4]),
            "table_9_detection_multiplicity": table_nine_distribution,
            "negative_or_failed_opportunities_enumerated": False,
        },
        "table_5_orientation_coverage": table_five_orientation,
        "table_15_detection_flags": {
            "rows": int(fusion[0]),
            "never_detected_any_version": int(fusion[1]),
            "label_authorized_rows": int(fusion[2]),
            "patterns": fusion_patterns,
        },
        "intact_explicit_negatives": {
            "rows": intact_negative_count,
            "state_combinations": intact_negative_states,
            "systematic_primary_universe": False,
        },
    }


def _assert_expected(metrics: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    expected = config["expected"]
    space = metrics["huri_space_membership"]
    comparisons = {
        "huri_space_rows": space["rows"],
        "huri_space_iii_true": space["in_space_iii_true"],
        "huri_space_iii_false": space["in_space_iii_false"],
        "huri_evidence_rows": metrics["huri_evidence"]["rows"],
        "huri_evidence_positive": metrics["huri_evidence"]["positive"],
        "huri_evidence_negative": metrics["huri_evidence"]["negative"],
        "table_5_complete_two_orientation_pair_assays": metrics[
            "table_5_orientation_coverage"
        ]["complete_two_orientation_pair_assays"],
        "table_7_detection_mentions": metrics["positive_screen_metadata"][
            "table_7_detection_mentions"
        ],
        "table_8_numeric_scores": metrics["outcome_panels"]["table_8"][
            "numeric_score_summary"
        ]["numeric"],
        "table_9_screen_detection_mentions": metrics["positive_screen_metadata"][
            "table_9_screen_detection_mentions"
        ],
        "table_9_assay_version_detection_mentions": metrics["positive_screen_metadata"][
            "table_9_assay_version_detection_mentions"
        ],
        "table_15_never_detected_any_version": metrics["table_15_detection_flags"][
            "never_detected_any_version"
        ],
        "table_15_label_authorized": metrics["table_15_detection_flags"][
            "label_authorized_rows"
        ],
        "intact_explicit_negative_rows": metrics["intact_explicit_negatives"]["rows"],
    }
    for key, observed in comparisons.items():
        if observed != int(expected[key]):
            raise RuntimeError(f"Expected metric changed: {key}={observed}")
    observed_pair_rows = {
        str(record["source_dataset"]): int(record["rows"])
        for record in metrics["huri_pair_views"]
    }
    if observed_pair_rows != {
        str(key): int(value) for key, value in expected["huri_pair_view_rows"].items()
    }:
        raise RuntimeError(f"HuRI pair-view counts changed: {observed_pair_rows}")
    for dataset, expected_rows in expected["supplement_table_rows"].items():
        observed = metrics["supplement_table_rows"].get(str(dataset))
        if observed != int(expected_rows):
            raise RuntimeError(f"Supplement table count changed: {dataset}={observed}")
    for panel, expected_counts in expected["panel_outcome_counts"].items():
        observed = metrics["outcome_panels"][str(panel)]["outcome_counts"]
        normalized_expected = {
            str(key): int(value) for key, value in expected_counts.items()
        }
        if observed != normalized_expected:
            raise RuntimeError(f"Panel outcome counts changed: {panel}={observed}")


def audit_systematic_screen_metadata(
    *,
    project_root: Path,
    config_path: Path,
    report_path: Path,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    config_path = _resolve_inside(project_root, config_path, project_root / "configs")
    config = _load_yaml(config_path)
    _validate_config(config)

    report_path = report_path.resolve()
    validation_boundary = (project_root / "artifacts/validation").resolve()
    try:
        report_path.parent.relative_to(validation_boundary)
    except ValueError as exc:
        raise RuntimeError("Audit report must be under artifacts/validation") from exc
    is_smoke = any(part.startswith("_smoke_") for part in report_path.parts)
    if allow_dirty != is_smoke:
        raise RuntimeError("--allow-dirty is restricted to an _smoke_* report path")

    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production audit requires a clean Git worktree")

    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = _resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
    )
    if active_container != expected_container:
        raise RuntimeError("Active Apptainer image differs from audit configuration")
    active_sha = sha256_file(active_container)
    if active_sha != str(config["runtime"]["container_sha256"]):
        raise RuntimeError("Active Apptainer image SHA-256 differs from configuration")
    if platform.machine() != str(config["runtime"]["architecture"]):
        raise RuntimeError("Audit is running on the wrong architecture")

    parse_manifest, verified_documents, document_paths = _input_documents(
        project_root, config
    )
    datasets = _verify_dataset_summaries(
        project_root=project_root,
        parse_manifest=parse_manifest,
        summary_paths=config["inputs"]["dataset_summaries"],
    )
    raw_assets, raw_paths = _verify_raw_assets(
        project_root=project_root,
        acquisition_manifest=document_paths["acquisition_manifest"],
        asset_ids=[str(value) for value in config["inputs"]["raw_asset_ids"]],
    )

    archive = _archive_inventory(raw_paths["huri_supplementary_tables"])
    methods_pdf = _pdf_keyword_inventory(raw_paths["huri_supplementary_methods"])
    guide_pdf = _pdf_keyword_inventory(raw_paths["huri_supplementary_table_guide"])
    expected = config["expected"]
    if archive["scientific_table_count"] != int(expected["archive_scientific_tables"]):
        raise RuntimeError("HuRI supplementary archive table count changed")
    if methods_pdf["pages"] != int(expected["methods_pdf_pages"]):
        raise RuntimeError("HuRI supplementary-method PDF page count changed")
    if guide_pdf["pages"] != int(expected["table_guide_pdf_pages"]):
        raise RuntimeError("HuRI table-guide PDF page count changed")

    connection = duckdb.connect()
    connection.execute(f"SET memory_limit='{config['runtime']['duckdb_memory_limit']}'")
    try:
        _register_views(connection, datasets)
        metrics = _collect_metrics(connection, config["supplementary_panels"])
    finally:
        connection.close()
    _assert_expected(metrics, config)

    completeness = assess_universe_completeness(
        config["systematic_universe_requirements"]
    )
    if completeness["complete_attempted_evaluable_universe_reconstructed"]:
        raise RuntimeError("Configuration unexpectedly declares a complete universe")

    provider_pair_count = next(
        int(record["rows"])
        for record in metrics["huri_pair_views"]
        if record["source_dataset"] == "HuRI"
    )
    supplement_positive_count = int(
        metrics["supplement_table_rows"]["huri_supplement_table_9"]
    )
    report = {
        "schema_version": 1,
        "audit_id": config["audit_id"],
        "audit_version": SYSTEMATIC_SCREEN_AUDIT_VERSION,
        "task": config["task"],
        "status": "complete",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "metadata_and_semantics_only_no_label_or_split_construction",
        "label_construction_performed": False,
        "split_construction_performed": False,
        "structural_mapping_performed": False,
        "model_training_performed": False,
        "runtime": {
            "container": str(config["runtime"]["container"]),
            "container_sif_sha256": active_sha,
            "architecture": platform.machine(),
            "duckdb_version": duckdb.__version__,
        },
        "git": git,
        "inputs": {
            "config": config_path.relative_to(project_root).as_posix(),
            "config_sha256": sha256_file(config_path),
            "documents": verified_documents,
            "raw_assets": raw_assets,
            "staged_datasets": datasets,
        },
        "source_inventory": {
            "supplementary_archive": archive,
            "supplementary_methods_pdf": methods_pdf,
            "supplementary_table_guide_pdf": guide_pdf,
        },
        "metrics": metrics,
        "systematic_universe_assessment": completeness,
        "external_public_availability_review": dict(
            config["external_availability_review"]
        ),
        "scientific_conclusion": {
            **dict(config["decision_policy"]),
            "main_huri_mitab_negative_records": metrics["huri_evidence"]["negative"],
            "main_huri_pair_view_rows": provider_pair_count,
            "supplement_table_9_positive_rows": supplement_positive_count,
            "provider_to_supplement_positive_row_difference": supplement_positive_count
            - provider_pair_count,
            "explicit_panel_nondetections_are_universal_negatives": False,
            "unreported_space_iii_pairs_are_negatives": False,
            "table_15_never_detected_pairs_are_negatives": False,
            "intact_negative_records_define_primary_systematic_universe": False,
        },
        "authorizations": {
            "benchmark_estimand_policy_proposal": True,
            "label_construction": False,
            "split_construction": False,
            "structural_mapping": False,
            "model_training": False,
        },
        "warnings": [
            {
                "code": "HURI_ATTEMPTED_UNIVERSE_UNRESOLVED",
                "issue": "governance/issues/ISSUE-0003-huri-attempted-pair-universe.md",
                "effect": "calibrated_primary_binary_benchmark_is_not_identifiable",
            },
            {
                "code": "STRICT_CONSTRUCT_COVERAGE_ZERO",
                "issue": "governance/issues/ISSUE-0005-sifts-uniprot-release-alignment.md",
                "effect": "strict_construct_benchmark_remains_infeasible",
            },
            {
                "code": "AUTHOR_CODE_REPOSITORY_LICENSE_UNRESOLVED",
                "effect": "reviewed_metadata_not_ingested_as_a_project_data_source",
            },
        ],
    }
    return report


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit systematic-screen and negative-evidence metadata"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/systematic_screen_metadata_audit_v1.yaml"),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    config_path = args.config
    if not config_path.is_absolute():
        config_path = project_root / config_path
    config = _load_yaml(config_path.resolve(strict=True))
    report_path = args.report or Path(config["outputs"]["audit_report"])
    if not report_path.is_absolute():
        report_path = project_root / report_path
    report = audit_systematic_screen_metadata(
        project_root=project_root,
        config_path=config_path,
        report_path=report_path,
        allow_dirty=args.allow_dirty,
    )
    _write_report(report_path, report, project_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
