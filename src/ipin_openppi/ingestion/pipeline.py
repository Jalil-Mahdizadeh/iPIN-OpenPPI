"""Orchestrate immutable, source-specific primary-source parsing."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
from typing import Any, Callable

import pyarrow
import yaml

from . import PARSER_VERSION
from .common import (
    AtomicDatasetDirectory,
    canonical_json,
    git_provenance,
    load_asset_index,
    project_root_from,
    require_apptainer,
    sha256_file,
    utc_now,
    verify_asset,
)
from .context import ParsingContext
from .huri import parse_huri
from .intact import parse_intact
from .schema import load_contract
from .sifts import parse_sifts
from .uniprot import parse_uniprot


SOURCE_PARSERS: dict[str, Callable[[ParsingContext, Path], dict[str, Any]]] = {
    "uniprot": parse_uniprot,
    "huri": parse_huri,
    "pdb_sifts": parse_sifts,
    "intact_imex": parse_intact,
}


def _selected_asset_ids(config: dict[str, Any], sources: list[str]) -> list[str]:
    ids: list[str] = []
    for source in sources:
        source_cfg = config["sources"][source]
        for key, value in source_cfg.items():
            if key.endswith("_asset_id"):
                ids.append(str(value))
            elif key.endswith("_asset_ids"):
                ids.extend(str(item) for item in value)
    return sorted(set(ids))


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
            raise RuntimeError(
                f"Generated dataset unexpectedly contains a link: {path}"
            )
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    root.chmod(0o555)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_primary_sources(
    *,
    project_root: Path,
    config_path: Path,
    sources: list[str],
    output_root: Path | None = None,
    allow_dirty: bool = False,
    skip_raw_sha256: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    absolute_config = (project_root / config_path).resolve(strict=True)
    with absolute_config.open("rt", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if config["authorization"]["label_construction"]:
        raise RuntimeError("Parsing config may not authorize label construction")
    if config["authorization"]["model_training"]:
        raise RuntimeError("Parsing config may not authorize model training")
    unknown_sources = sorted(set(sources) - set(SOURCE_PARSERS))
    if unknown_sources:
        raise ValueError(f"Unknown parser sources: {unknown_sources}")

    manifest_path = Path(config["inputs"]["acquisition_manifest"])
    observed_manifest_sha = sha256_file(project_root / manifest_path)
    if observed_manifest_sha != config["inputs"]["acquisition_manifest_sha256"]:
        raise RuntimeError("Acquisition manifest SHA-256 differs from parsing config")
    acquisition_manifest, assets = load_asset_index(project_root, manifest_path)
    evidence_contract = load_contract(
        project_root / config["inputs"]["evidence_schema"]
    )
    staging_contract = load_contract(project_root / config["inputs"]["staging_schema"])

    git = git_provenance(project_root)
    require_clean = bool(config["runtime"]["require_clean_git_for_production"])
    if require_clean and not git["tracked_worktree_clean"] and not allow_dirty:
        raise RuntimeError(
            "Production parsing requires a clean Git worktree; commit parser/schema changes first"
        )
    configured_container = (project_root / config["runtime"]["container"]).resolve(
        strict=True
    )
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    if active_container != configured_container:
        raise RuntimeError(
            f"Active Apptainer image {active_container} != configured {configured_container}"
        )
    observed_container_sha = sha256_file(configured_container)
    if observed_container_sha != config["runtime"]["container_sha256"]:
        raise RuntimeError("Active Apptainer SIF SHA-256 differs from parsing config")
    if platform.machine() != "aarch64":
        raise RuntimeError(
            f"Primary parsing requires aarch64, observed {platform.machine()}"
        )

    selected_asset_ids = _selected_asset_ids(config, sources)
    raw_verification = []
    for asset_id in selected_asset_ids:
        asset = assets.get(asset_id)
        if asset is None:
            raise RuntimeError(
                f"Configured asset absent from acquisition manifest: {asset_id}"
            )
        if skip_raw_sha256:
            raw_verification.append(
                {
                    "asset_id": asset_id,
                    "path": asset.relative_path,
                    "sha256": asset.sha256,
                    "verification": "skipped_by_explicit_nonproduction_option",
                }
            )
        else:
            raw_verification.append(verify_asset(asset))

    context = ParsingContext(
        project_root=project_root,
        config_path=config_path,
        config=config,
        assets=assets,
        evidence_contract=evidence_contract,
        staging_contract=staging_contract,
        parser_git_commit=git["commit"],
        parser_version=str(config["runtime"]["parser_version"]),
        container_sif_sha256=observed_container_sha,
    )
    if context.parser_version != PARSER_VERSION:
        raise RuntimeError(
            f"Config parser version {context.parser_version} != code {PARSER_VERSION}"
        )

    configured_output = project_root / config["outputs"]["staging_root"]
    target = (output_root or configured_output).resolve()
    try:
        target.relative_to((project_root / "data/staging").resolve())
    except ValueError as exc:
        raise RuntimeError(f"Staging output escapes data/staging: {target}") from exc

    started_at = utc_now()
    with AtomicDatasetDirectory(target) as temporary:
        source_reports: dict[str, Any] = {}
        for source in sources:
            print(f"SOURCE_START {source}", flush=True)
            source_root = temporary / source
            source_root.mkdir(parents=False, exist_ok=False)
            source_reports[source] = SOURCE_PARSERS[source](context, source_root)
            print(f"SOURCE_COMPLETE {source}", flush=True)
        completed_at = utc_now()
        report = {
            "schema_version": 1,
            "run_family": str(config["run_family"]),
            "task": str(config["task"]),
            "status": "complete",
            "started_at_utc": started_at,
            "completed_at_utc": completed_at,
            "sources": sources,
            "label_construction_performed": False,
            "model_training_performed": False,
            "git": git,
            "runtime": {
                "apptainer_container": config["runtime"]["container"],
                "container_sif_sha256": observed_container_sha,
                "architecture": platform.machine(),
                "python": platform.python_version(),
                "pyarrow": pyarrow.__version__,
                "parser_version": context.parser_version,
            },
            "inputs": {
                "config": config_path.as_posix(),
                "config_sha256": sha256_file(absolute_config),
                "acquisition_manifest": manifest_path.as_posix(),
                "acquisition_manifest_sha256": observed_manifest_sha,
                "acquisition_run_id": acquisition_manifest.get("run_id"),
                "evidence_schema": evidence_contract.path.as_posix(),
                "evidence_schema_sha256": evidence_contract.sha256,
                "staging_schema": staging_contract.path.as_posix(),
                "staging_schema_sha256": staging_contract.sha256,
                "raw_verification": raw_verification,
            },
            "source_reports": source_reports,
        }
        report = _replace_prefix(report, temporary.as_posix(), target.as_posix())
        manifest_output = temporary / "PARSE_MANIFEST.json"
        _write_json(manifest_output, report)
        manifest_sha = sha256_file(manifest_output)
        (temporary / "PARSE_MANIFEST.json.sha256").write_text(
            f"{manifest_sha}  PARSE_MANIFEST.json\n", encoding="utf-8"
        )
        _make_read_only(temporary)
    return {
        **report,
        "output_root": target.as_posix(),
        "parse_manifest": (target / "PARSE_MANIFEST.json").as_posix(),
        "parse_manifest_sha256": manifest_sha,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse frozen primary evidence sources into staging Parquet"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/parsing_primary_sources_v1.yaml"),
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=list(SOURCE_PARSERS),
        default=list(SOURCE_PARSERS),
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit dirty Git only for bounded tests; never use for production",
    )
    parser.add_argument(
        "--skip-raw-sha256",
        action="store_true",
        help="Skip expensive raw hashing only for bounded tests",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    output = args.output_root
    if output is not None and not output.is_absolute():
        output = project_root / output
    report = parse_primary_sources(
        project_root=project_root,
        config_path=args.config,
        sources=args.sources,
        output_root=output,
        allow_dirty=args.allow_dirty,
        skip_raw_sha256=args.skip_raw_sha256,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
