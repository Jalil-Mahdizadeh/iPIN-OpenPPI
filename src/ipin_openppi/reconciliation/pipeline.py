"""Produce the immutable primary identifier/construct reconciliation layer."""

from __future__ import annotations

import argparse
from collections.abc import Iterator
import json
import os
from pathlib import Path
import platform
import re
import stat
import tempfile
from typing import Any

import duckdb
import pyarrow
import yaml

from ipin_openppi.ingestion.common import (
    AtomicDatasetDirectory,
    git_provenance,
    project_root_from,
    require_apptainer,
    sha256_file,
    utc_now,
)
from ipin_openppi.ingestion.schema import load_contract

from . import RECONCILIATION_VERSION
from .policy import ReconciliationProvenance
from .sql import OUTPUT_QUERIES, build_work_tables, collect_metrics, setup_input_views
from .writer import ArrowQueryDatasetWriter


def _replace_prefix(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {key: _replace_prefix(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_prefix(item, old, new) for item in value]
    if isinstance(value, str) and value.startswith(old):
        return new + value[len(old) :]
    return value


def _make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError(f"Generated canonical dataset contains a link: {path}")
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    root.chmod(0o555)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _iter_manifest_files(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if {
            "table",
            "rows",
            "files",
            "schema_name",
            "schema_version",
            "schema_sha256",
        }.issubset(value):
            for record in value["files"]:
                yield record
            return
        for child in value.values():
            yield from _iter_manifest_files(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_manifest_files(child)


def _resolve_inside(project_root: Path, value: str | Path, boundary: Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(boundary.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(
            f"Path escapes required boundary {boundary}: {resolved}"
        ) from exc
    return resolved


def verify_staging_input(
    *,
    project_root: Path,
    config: dict[str, Any],
    skip_staging_sha256: bool,
) -> dict[str, Any]:
    """Reverify immutable staging inventory before canonical derivation."""

    staging_boundary = (project_root / "data/staging").resolve(strict=True)
    staging_root = _resolve_inside(
        project_root, config["inputs"]["staging_root"], staging_boundary
    )
    if staging_root.is_symlink() or not staging_root.is_dir():
        raise RuntimeError("Staging root must be a non-link directory")

    manifest_path = _resolve_inside(
        project_root, config["inputs"]["parse_manifest"], staging_root
    )
    manifest_sha = sha256_file(manifest_path)
    if manifest_sha != config["inputs"]["parse_manifest_sha256"]:
        raise RuntimeError("Parse-manifest SHA-256 differs from reconciliation config")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise RuntimeError("Input parse manifest is not complete")
    if manifest.get("label_construction_performed") is not False:
        raise RuntimeError("Input parse manifest indicates label construction")
    if manifest.get("model_training_performed") is not False:
        raise RuntimeError("Input parse manifest indicates model training")

    validation_boundary = (project_root / "artifacts/validation").resolve(strict=True)
    validation_path = _resolve_inside(
        project_root,
        config["inputs"]["staging_validation_report"],
        validation_boundary,
    )
    validation_sha = sha256_file(validation_path)
    if validation_sha != config["inputs"]["staging_validation_report_sha256"]:
        raise RuntimeError("Staging-validation SHA-256 differs from config")
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("status") != "pass":
        raise RuntimeError("Staging validation did not pass")
    authorization = validation.get("authorizations", {})
    if authorization.get("source_reconciliation") is not True:
        raise RuntimeError("Staging validation does not authorize reconciliation")
    if authorization.get("label_construction") is not False:
        raise RuntimeError("Staging validation unexpectedly authorizes labels")
    if validation.get("parse_manifest_sha256") != manifest_sha:
        raise RuntimeError("Staging validation references a different parse manifest")

    records = list(_iter_manifest_files(manifest.get("source_reports", {})))
    if not records:
        raise RuntimeError("Parse manifest contains no Parquet file records")
    expected_paths: set[Path] = set()
    total_bytes = 0
    total_rows = 0
    for record in records:
        path = _resolve_inside(project_root, str(record["path"]), staging_root)
        if path in expected_paths:
            raise RuntimeError(f"Duplicate staged Parquet path in manifest: {path}")
        expected_paths.add(path)
        info = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or path.is_symlink():
            raise RuntimeError(f"Staged Parquet is not a regular non-link file: {path}")
        if info.st_mode & 0o222:
            raise RuntimeError(f"Staged Parquet became writable: {path}")
        if info.st_size != int(record["bytes"]):
            raise RuntimeError(f"Staged Parquet size changed: {path}")
        if not skip_staging_sha256 and sha256_file(path) != str(record["sha256"]):
            raise RuntimeError(f"Staged Parquet SHA-256 changed: {path}")
        total_bytes += info.st_size
        total_rows += int(record["rows"])

    actual_paths = {path.resolve() for path in staging_root.rglob("*.parquet")}
    if actual_paths != expected_paths:
        raise RuntimeError("Staging Parquet inventory differs from parse manifest")
    for path in (staging_root, *staging_root.rglob("*")):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError(f"Staging tree contains a link: {path}")
        if info.st_mode & 0o222:
            raise RuntimeError(f"Staging tree contains a writable path: {path}")

    return {
        "staging_root": config["inputs"]["staging_root"],
        "parse_manifest": config["inputs"]["parse_manifest"],
        "parse_manifest_sha256": manifest_sha,
        "staging_validation_report": config["inputs"]["staging_validation_report"],
        "staging_validation_report_sha256": validation_sha,
        "parquet_files": len(expected_paths),
        "parquet_rows_across_tables": total_rows,
        "parquet_bytes": total_bytes,
        "sha256_verification": (
            "skipped_by_explicit_nonproduction_option"
            if skip_staging_sha256
            else "complete"
        ),
    }


def _validate_config(config: dict[str, Any]) -> None:
    if config["authorization"]["label_construction"]:
        raise RuntimeError("Reconciliation config may not authorize label construction")
    if config["authorization"]["model_training"]:
        raise RuntimeError("Reconciliation config may not authorize model training")
    if config["reconciliation_version"] != RECONCILIATION_VERSION:
        raise RuntimeError("Config and code reconciliation versions differ")
    mapping = config["mapping_policy"]
    if mapping["exact_construct_sequences_available"]:
        raise RuntimeError("Frozen inputs do not contain exact construct sequences")
    if mapping["explicit_construct_boundaries_available"]:
        raise RuntimeError("Frozen inputs do not contain explicit construct boundaries")
    if mapping["highest_assignable_construct_confidence"] != "C":
        raise RuntimeError("Current sources may assign at most construct confidence C")
    if not mapping["stop_after_first_resolving_candidate_route"]:
        raise RuntimeError(
            "Candidate precedence must stop at the first resolving route"
        )
    if mapping["unreported_pairs_are_negative"]:
        raise RuntimeError("Unreported pairs may not be treated as negatives")
    if mapping["provider_pair_views_are_labels"]:
        raise RuntimeError("Provider pair views may not be treated as labels")
    sifts = config["sifts_policy"]
    if sifts["releases_aligned"]:
        raise RuntimeError("SIFTS and frozen UniProt releases are not aligned")
    if sifts["authorize_structural_mapping"]:
        raise RuntimeError("Release-mismatched structural mapping is prohibited")
    if sifts["authorize_structure_derived_labels"]:
        raise RuntimeError("Structure-derived labels are prohibited")
    memory_limit = str(config["runtime"]["duckdb_memory_limit"])
    if not re.fullmatch(r"[1-9][0-9]*(?:MB|GB)", memory_limit):
        raise RuntimeError("DuckDB memory limit must be an explicit MB or GB value")


def _require_scoped_nonproduction_output(
    *, output_root: Path | None, allow_dirty: bool, skip_staging_sha256: bool
) -> None:
    if not (allow_dirty or skip_staging_sha256):
        return
    if output_root is None or not output_root.name.startswith("_smoke_"):
        raise RuntimeError(
            "Nonproduction overrides require an explicit _smoke_* canonical output"
        )


def reconcile_primary_sources(
    *,
    project_root: Path,
    config_path: Path,
    output_root: Path | None = None,
    allow_dirty: bool = False,
    skip_staging_sha256: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    absolute_config = (project_root / config_path).resolve(strict=True)
    config = yaml.safe_load(absolute_config.read_text(encoding="utf-8"))
    _validate_config(config)

    configured_output = (project_root / config["outputs"]["canonical_root"]).resolve()
    target = (output_root or configured_output).resolve()
    canonical_boundary = (project_root / "data/canonical").resolve(strict=True)
    try:
        target.relative_to(canonical_boundary)
    except ValueError as exc:
        raise RuntimeError(
            f"Canonical output escapes data/canonical: {target}"
        ) from exc
    _require_scoped_nonproduction_output(
        output_root=output_root,
        allow_dirty=allow_dirty,
        skip_staging_sha256=skip_staging_sha256,
    )

    git = git_provenance(project_root)
    if (
        config["runtime"]["require_clean_git_for_production"]
        and not git["tracked_worktree_clean"]
        and not allow_dirty
    ):
        raise RuntimeError(
            "Production reconciliation requires committed code and a clean worktree"
        )

    configured_container = (project_root / config["runtime"]["container"]).resolve(
        strict=True
    )
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    if active_container != configured_container:
        raise RuntimeError("Active Apptainer image differs from reconciliation config")
    observed_container_sha = sha256_file(configured_container)
    if observed_container_sha != config["runtime"]["container_sha256"]:
        raise RuntimeError("Active Apptainer SIF SHA-256 differs from config")
    if platform.machine() != config["runtime"]["architecture"]:
        raise RuntimeError("Reconciliation is running on the wrong architecture")

    print("INPUT_VERIFICATION_START", flush=True)
    input_verification = verify_staging_input(
        project_root=project_root,
        config=config,
        skip_staging_sha256=skip_staging_sha256,
    )
    print("INPUT_VERIFICATION_COMPLETE", flush=True)

    contract = load_contract(project_root / config["inputs"]["reconciliation_schema"])
    temporary_base = project_root / "artifacts/tmp"
    temporary_base.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()

    with tempfile.TemporaryDirectory(
        prefix="reconciliation-duckdb-", dir=temporary_base
    ) as duckdb_temporary:
        connection = duckdb.connect(":memory:")
        try:
            threads = int(config["runtime"]["duckdb_threads"])
            if threads < 1:
                raise RuntimeError("DuckDB thread count must be positive")
            connection.execute(f"SET threads={threads}")
            memory_limit = str(config["runtime"]["duckdb_memory_limit"])
            connection.execute(f"SET memory_limit='{memory_limit}'")
            escaped_temporary = duckdb_temporary.replace("'", "''")
            connection.execute(f"SET temp_directory='{escaped_temporary}'")
            connection.execute("PRAGMA disable_progress_bar")
            staging_root = (project_root / config["inputs"]["staging_root"]).resolve(
                strict=True
            )
            setup_input_views(connection, staging_root)
            provenance = ReconciliationProvenance(
                parse_manifest_sha256=config["inputs"]["parse_manifest_sha256"],
                version=config["reconciliation_version"],
                git_commit=git["commit"],
                container_sif_sha256=observed_container_sha,
                schema_version=contract.version,
                schema_sha256=contract.sha256,
                frozen_taxid=int(config["mapping_policy"]["frozen_taxid"]),
                protein_molecule_type_ac=str(
                    config["mapping_policy"]["protein_molecule_type_ac"]
                ),
                sifts_declared_uniprot_release=str(
                    config["sifts_policy"]["declared_uniprot_release"]
                ),
                frozen_uniprot_release=str(
                    config["sifts_policy"]["frozen_uniprot_release"]
                ),
            )
            print("WORK_RELATIONS_START", flush=True)
            build_work_tables(
                connection,
                provenance,
                config["mapping_policy"]["candidate_priority"],
                config["mapping_policy"]["ensembl_database_mapping"],
            )
            print("WORK_RELATIONS_COMPLETE", flush=True)
            metrics = collect_metrics(connection, config["provider_counts"])

            with AtomicDatasetDirectory(target) as temporary_output:
                table_summaries: dict[str, Any] = {}
                for table_name, query in OUTPUT_QUERIES.items():
                    print(f"TABLE_START {table_name}", flush=True)
                    table_summaries[table_name] = ArrowQueryDatasetWriter(
                        connection=connection,
                        query=query,
                        output_dir=temporary_output / table_name,
                        contract=contract,
                        table_name=table_name,
                        batch_rows=int(config["runtime"]["parquet_batch_rows"]),
                        compression=str(config["runtime"]["parquet_compression"]),
                        compression_level=int(
                            config["runtime"]["parquet_compression_level"]
                        ),
                    ).write()
                    print(f"TABLE_COMPLETE {table_name}", flush=True)

                completed_at = utc_now()
                report = {
                    "schema_version": 1,
                    "run_family": str(config["run_family"]),
                    "task": str(config["task"]),
                    "status": "complete",
                    "started_at_utc": started_at,
                    "completed_at_utc": completed_at,
                    "source_reconciliation_performed": True,
                    "label_construction_performed": False,
                    "model_training_performed": False,
                    "git": git,
                    "runtime": {
                        "apptainer_container": config["runtime"]["container"],
                        "container_sif_sha256": observed_container_sha,
                        "architecture": platform.machine(),
                        "python": platform.python_version(),
                        "pyarrow": pyarrow.__version__,
                        "duckdb": duckdb.__version__,
                        "reconciliation_version": RECONCILIATION_VERSION,
                    },
                    "inputs": {
                        "config": config_path.as_posix(),
                        "config_sha256": sha256_file(absolute_config),
                        "reconciliation_schema": config["inputs"][
                            "reconciliation_schema"
                        ],
                        "reconciliation_schema_sha256": contract.sha256,
                        **input_verification,
                    },
                    "policy": {
                        "mapping": config["mapping_policy"],
                        "sifts": config["sifts_policy"],
                        "provider_counts": config["provider_counts"],
                    },
                    "tables": table_summaries,
                    "metrics": metrics,
                    "authorizations": {
                        "source_reconciliation": True,
                        "label_construction": False,
                        "model_training": False,
                        "structural_mapping": False,
                    },
                }
                report = _replace_prefix(
                    report, temporary_output.as_posix(), target.as_posix()
                )
                manifest_path = temporary_output / "RECONCILIATION_MANIFEST.json"
                _write_json(manifest_path, report)
                manifest_sha = sha256_file(manifest_path)
                (temporary_output / "RECONCILIATION_MANIFEST.json.sha256").write_text(
                    f"{manifest_sha}  RECONCILIATION_MANIFEST.json\n",
                    encoding="utf-8",
                )
                _make_read_only(temporary_output)
        finally:
            connection.close()

    return {
        **report,
        "output_root": target.as_posix(),
        "reconciliation_manifest": (target / "RECONCILIATION_MANIFEST.json").as_posix(),
        "reconciliation_manifest_sha256": manifest_sha,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconcile source identifiers and construct confidence"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/reconciliation_primary_v1.yaml"),
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit dirty Git only for an explicitly named smoke output",
    )
    parser.add_argument(
        "--skip-staging-sha256",
        action="store_true",
        help="Skip staged-file hashes only for an explicitly named smoke output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    output = args.output_root
    if output is not None and not output.is_absolute():
        output = project_root / output
    report = reconcile_primary_sources(
        project_root=project_root,
        config_path=args.config,
        output_root=output,
        allow_dirty=args.allow_dirty,
        skip_staging_sha256=args.skip_staging_sha256,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
