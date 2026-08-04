#!/usr/bin/env python3
"""Validate pre-acquisition source manifests without downloading scientific data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DEFAULT_EXPECTED_SOURCE_KEYS = {"huri", "uniprot", "intact_imex", "pdb_sifts"}
SUPPORTED_SOURCE_KEYS = DEFAULT_EXPECTED_SOURCE_KEYS | {
    "negatome",
    "lambourne_human_y2h",
    "tf_isoform_y2h_2025",
}
ALLOWED_LICENSES = {
    "CC-BY-4.0",
    "CC0-1.0",
    "MIXED-CC-BY-4.0-MIT",
    "MIXED-CC-BY-4.0-ALL-RIGHTS-RESERVED",
    "UNSPECIFIED-NO-REDISTRIBUTION",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a YAML mapping")
    return value


def nested_get(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "passed": passed, "detail": detail})


def validate_manifest(
    repo_root: Path,
    source_key: str,
    path: Path,
) -> tuple[list[dict[str, Any]], list[str], list[str], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    data = load_yaml(path)

    def require(name: str, passed: bool, detail: str) -> None:
        add_check(checks, name, passed, detail)
        if not passed:
            errors.append(f"{source_key}: {detail}")

    require("schema_version", data.get("schema_version") == 1, "schema_version must equal 1")
    require("source_key", data.get("source_key") == source_key, "source_key must match index")
    require("stage", data.get("stage") == "preacquisition", "stage must be preacquisition")
    require(
        "approved_for_download",
        data.get("approved_for_download") is True,
        "approved_for_download must be true",
    )
    require("source_mapping", isinstance(data.get("source"), dict), "source metadata is required")

    license_data = data.get("license")
    require("license_mapping", isinstance(license_data, dict), "license metadata is required")
    if isinstance(license_data, dict):
        identifier = license_data.get("identifier")
        require(
            "license_identifier",
            identifier in ALLOWED_LICENSES,
            f"license identifier must be one of {sorted(ALLOWED_LICENSES)}",
        )
        terms_url = license_data.get("terms_url") or license_data.get("pdb_terms_url")
        require(
            "license_terms_https",
            isinstance(terms_url, str) and terms_url.startswith("https://"),
            "an HTTPS license/terms URL is required",
        )

    assets = data.get("assets")
    require("asset_list", isinstance(assets, list) and len(assets) > 0, "at least one asset is required")
    asset_ids: set[str] = set()
    destinations: set[str] = set()
    required_assets = 0
    checksum_assets = 0
    if isinstance(assets, list):
        for position, asset in enumerate(assets):
            prefix = f"asset[{position}]"
            if not isinstance(asset, dict):
                errors.append(f"{source_key}: {prefix} must be a mapping")
                continue
            asset_id = asset.get("asset_id")
            url = asset.get("url")
            destination = asset.get("destination")
            required = asset.get("required")
            expected = asset.get("expected")
            if not isinstance(asset_id, str) or not asset_id:
                errors.append(f"{source_key}: {prefix} requires asset_id")
            elif asset_id in asset_ids:
                errors.append(f"{source_key}: duplicate asset_id {asset_id}")
            else:
                asset_ids.add(asset_id)
            if not isinstance(url, str) or not url.startswith("https://"):
                errors.append(f"{source_key}: {prefix} URL must use HTTPS")
            if not isinstance(destination, str) or not destination.startswith("data/raw/"):
                errors.append(f"{source_key}: {prefix} destination must be beneath data/raw/")
            elif destination in destinations:
                errors.append(f"{source_key}: duplicate destination {destination}")
            else:
                destinations.add(destination)
            if not isinstance(required, bool):
                errors.append(f"{source_key}: {prefix} required must be boolean")
            elif required:
                required_assets += 1
            if not isinstance(expected, dict):
                errors.append(f"{source_key}: {prefix} expected metadata must be a mapping")
            elif isinstance(expected.get("provider_checksum"), dict):
                checksum_assets += 1

    verification = data.get("verification")
    require("verification_mapping", isinstance(verification, dict), "verification metadata is required")
    require(
        "local_sha256",
        nested_get(data, "verification", "calculate_sha256") is True,
        "local SHA-256 calculation must be required",
    )
    require(
        "record_validation",
        nested_get(data, "verification", "record_count_and_schema_report") == "required",
        "record-count and schema validation must be required",
    )
    require(
        "approved_actions",
        isinstance(data.get("approved_actions"), list) and bool(data.get("approved_actions")),
        "approved_actions must be non-empty",
    )
    require(
        "prohibited_actions",
        isinstance(data.get("prohibited_actions"), list) and bool(data.get("prohibited_actions")),
        "prohibited_actions must be non-empty",
    )

    special_expectations: dict[str, list[tuple[tuple[str, ...], Any]]] = {
        "huri": [
            (("guards", "unreported_pairs_are_negative"), False),
            (("guards", "space_iii_cross_product_is_complete_attempted_universe"), False),
            (("guards", "technical_failures_are_negative"), False),
        ],
        "uniprot": [
            (("guards", "canonical_and_additional_sequences_kept_separate"), True),
            (("guards", "isoforms_silently_collapsed_to_gene"), False),
            (("guards", "current_release_url_accepted_only_with_metalink_verification"), True),
        ],
        "intact_imex": [
            (("guards", "nary_expansions_are_direct"), False),
            (("guards", "preserve_original_nary_records"), True),
            (("guards", "unreported_pairs_are_negative"), False),
        ],
        "pdb_sifts": [
            (("guards", "computed_models_allowed"), False),
            (("guards", "experimental_entries_only"), True),
            (("guards", "interface_must_be_recalculated_from_frozen_coordinates"), True),
        ],
        "negatome": [
            (("guards", "unreported_pairs_are_negative"), False),
            (("guards", "universal_nonbinding_interpretation"), False),
            (("guards", "preserve_manual_and_pdb_families_separately"), True),
            (("guards", "raw_redistribution_allowed"), False),
        ],
        "lambourne_human_y2h": [
            (("guards", "original_4100_selected_pair_universe_required"), True),
            (("guards", "final_3222_analysis_subset_required"), True),
            (("guards", "technical_or_na_outcome_is_negative"), False),
            (("guards", "outcomes_as_training_labels"), False),
            (("guards", "merge_with_negatome"), False),
            (("guards", "benchmark_split_construction"), False),
            (("guards", "universal_nonbinding_interpretation"), False),
        ],
        "tf_isoform_y2h_2025": [
            (("guards", "blank_or_unresolved_outcome_is_negative"), False),
            (("guards", "technical_failure_is_negative"), False),
            (("guards", "outcomes_as_training_labels"), False),
            (("guards", "merge_with_negatome"), False),
            (("guards", "benchmark_construction"), False),
            (("guards", "universal_nonbinding_interpretation"), False),
            (("guards", "preserve_ad_to_db_orientation"), True),
            (("guards", "keep_y2h_and_n2h_separate"), True),
        ],
    }
    for key_path, expected_value in special_expectations[source_key]:
        observed = nested_get(data, *key_path)
        require(
            "guard_" + "_".join(key_path),
            observed is expected_value,
            f"{'.'.join(key_path)} must be {expected_value!r}",
        )

    if source_key == "uniprot":
        require(
            "provider_checksums",
            checksum_assets >= 4,
            "the UniProt release assets must include provider checksums",
        )
    elif checksum_assets == 0:
        warnings.append(f"{source_key}: provider checksum catalogue unavailable; local SHA-256 is authoritative")

    summary = {
        "source_key": source_key,
        "path": str(path.relative_to(repo_root)),
        "sha256": sha256_file(path),
        "asset_count": len(assets) if isinstance(assets, list) else 0,
        "required_asset_count": required_assets,
        "provider_checksum_asset_count": checksum_assets,
        "check_count": len(checks),
        "passed_check_count": sum(1 for check in checks if check["passed"]),
    }
    return checks, errors, warnings, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    index_path = args.index.resolve()
    output_path = args.output.resolve()
    try:
        index_path.relative_to(repo_root)
        output_path.relative_to(repo_root)
    except ValueError as exc:
        raise SystemExit("index and output must remain beneath the repository root") from exc

    inside_apptainer = bool(os.environ.get("APPTAINER_CONTAINER") or os.environ.get("SINGULARITY_CONTAINER"))
    index = load_yaml(index_path)
    errors: list[str] = []
    warnings: list[str] = []
    index_checks: list[dict[str, Any]] = []
    configured_keys = nested_get(index, "validation", "expected_source_keys")
    expected_source_keys = (
        set(configured_keys) if isinstance(configured_keys, list) else DEFAULT_EXPECTED_SOURCE_KEYS
    )

    def index_check(name: str, passed: bool, detail: str) -> None:
        add_check(index_checks, name, passed, detail)
        if not passed:
            errors.append(f"index: {detail}")

    index_check("inside_apptainer", inside_apptainer, "validation must run inside Apptainer")
    index_check("schema_version", index.get("schema_version") == 1, "schema_version must equal 1")
    index_check("stage", index.get("stage") == "preacquisition", "stage must be preacquisition")
    index_check(
        "label_construction_boundary",
        nested_get(index, "authorization", "label_construction_permitted") is False,
        "label construction must remain prohibited",
    )

    manifest_entries = index.get("manifests")
    index_check(
        "manifest_entries",
        isinstance(manifest_entries, list) and bool(manifest_entries),
        "manifest list must be non-empty",
    )
    seen_keys: set[str] = set()
    source_results: list[dict[str, Any]] = []
    if isinstance(manifest_entries, list):
        for entry in manifest_entries:
            if not isinstance(entry, dict):
                errors.append("index: each manifest entry must be a mapping")
                continue
            source_key = entry.get("source_key")
            rel_path = entry.get("path")
            if not isinstance(source_key, str) or source_key not in expected_source_keys:
                errors.append(f"index: invalid source_key {source_key!r}")
                continue
            if source_key in seen_keys:
                errors.append(f"index: duplicate source_key {source_key}")
                continue
            seen_keys.add(source_key)
            if not isinstance(rel_path, str):
                errors.append(f"index: {source_key} path must be a string")
                continue
            path = (repo_root / rel_path).resolve()
            try:
                path.relative_to(repo_root)
            except ValueError:
                errors.append(f"index: {source_key} path leaves repository root")
                continue
            if not path.is_file():
                errors.append(f"index: missing manifest {rel_path}")
                continue
            checks, source_errors, source_warnings, source_summary = validate_manifest(
                repo_root, source_key, path
            )
            errors.extend(source_errors)
            warnings.extend(source_warnings)
            source_summary["checks"] = checks
            source_results.append(source_summary)

    index_check(
        "complete_source_set",
        seen_keys == expected_source_keys and expected_source_keys <= SUPPORTED_SOURCE_KEYS,
        f"source keys must equal supported configured set {sorted(expected_source_keys)}",
    )

    policy_path = (repo_root / str(index.get("policy", ""))).resolve()
    policy_ok = policy_path.is_file()
    index_check("policy_exists", policy_ok, "referenced source policy must exist")
    policy_sha256 = sha256_file(policy_path) if policy_ok else None

    report = {
        "schema_version": 1,
        "validation_id": "PREACQ-VALIDATION-002",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not errors else "fail",
        "runtime": {
            "inside_apptainer": inside_apptainer,
            "apptainer_container": os.environ.get("APPTAINER_CONTAINER")
            or os.environ.get("SINGULARITY_CONTAINER"),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "index": {
            "path": str(index_path.relative_to(repo_root)),
            "sha256": sha256_file(index_path),
            "checks": index_checks,
        },
        "policy": {
            "path": str(policy_path.relative_to(repo_root)) if policy_ok else str(policy_path),
            "sha256": policy_sha256,
        },
        "sources": sorted(source_results, key=lambda value: value["source_key"]),
        "errors": errors,
        "warnings": warnings,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": len(errors), "warnings": len(warnings)}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
