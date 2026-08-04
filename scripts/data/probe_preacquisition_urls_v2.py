#!/usr/bin/env python3
"""HEAD-probe all active manifest assets without downloading payload bodies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from acquire_manifest_assets import build_https_opener


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a YAML mapping")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def head(repo_root: Path, url: str, timeout_seconds: float) -> dict[str, Any]:
    opener, tls_record = build_https_opener(repo_root, url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "iPIN-OpenPPI-source-audit/1.0 (+research provenance)",
            "Accept": "*/*",
        },
        method="HEAD",
    )
    with opener.open(request, timeout=timeout_seconds) as response:
        headers = response.headers
        return {
            "http_status": getattr(response, "status", None),
            "final_url": response.geturl(),
            "content_length": headers.get("Content-Length"),
            "content_type": headers.get("Content-Type"),
            "etag": headers.get("ETag"),
            "last_modified": headers.get("Last-Modified"),
            "accept_ranges": headers.get("Accept-Ranges"),
            "tls": tls_record,
        }


def comparison_checks(expected: dict[str, Any], observed: dict[str, Any]) -> list[dict[str, Any]]:
    status = observed.get("http_status")
    checks: list[dict[str, Any]] = [
        {
            "name": "reachable",
            "passed": isinstance(status, int) and 200 <= status < 400,
            "observed": status,
        }
    ]
    expected_length = expected.get("content_length_bytes")
    if expected_length is not None:
        actual_text = observed.get("content_length")
        actual_length = int(actual_text) if actual_text else None
        checks.append(
            {
                "name": "content_length",
                "passed": actual_length == int(expected_length),
                "expected": int(expected_length),
                "observed": actual_length,
            }
        )
    expected_etag = expected.get("etag")
    if expected_etag is not None:
        checks.append(
            {
                "name": "etag",
                "passed": observed.get("etag") == expected_etag,
                "expected": expected_etag,
                "observed": observed.get("etag"),
            }
        )
    expected_modified = expected.get("last_modified") or expected.get("last_modified_date")
    if expected_modified is not None:
        actual_modified = observed.get("last_modified")
        checks.append(
            {
                "name": "last_modified",
                "passed": isinstance(actual_modified, str) and expected_modified in actual_modified,
                "expected_contains": expected_modified,
                "observed": actual_modified,
            }
        )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout-seconds", default=45.0, type=float)
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="probe only the named source key; may be repeated",
    )
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    index_path = args.index.resolve()
    output_path = args.output.resolve()
    for path in (index_path, output_path):
        try:
            path.relative_to(repo_root)
        except ValueError as exc:
            raise SystemExit("index and output must remain beneath the repository root") from exc
    inside_apptainer = bool(os.environ.get("APPTAINER_CONTAINER") or os.environ.get("SINGULARITY_CONTAINER"))
    if not inside_apptainer:
        raise SystemExit("URL probing must run inside Apptainer")

    index = load_yaml(index_path)
    selected_sources = set(args.source)
    configured_sources = {
        str(entry.get("source_key"))
        for entry in index.get("manifests", [])
        if isinstance(entry, dict)
    }
    unknown_sources = sorted(selected_sources - configured_sources)
    if unknown_sources:
        raise SystemExit(f"unknown source key(s): {unknown_sources}")
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    for entry in index.get("manifests", []):
        source_key = entry["source_key"]
        if selected_sources and source_key not in selected_sources:
            continue
        manifest_path = (repo_root / entry["path"]).resolve()
        manifest = load_yaml(manifest_path)
        for asset in manifest.get("assets", []):
            required = bool(asset["required"])
            record: dict[str, Any] = {
                "source_key": source_key,
                "manifest": str(manifest_path.relative_to(repo_root)),
                "asset_id": asset["asset_id"],
                "url": asset["url"],
                "required": required,
            }
            try:
                observed = head(repo_root, asset["url"], args.timeout_seconds)
                checks = comparison_checks(asset.get("expected", {}), observed)
                record["observed"] = observed
                record["checks"] = checks
                failed = [check for check in checks if not check["passed"]]
                if failed:
                    message = f"{source_key}/{asset['asset_id']}: {len(failed)} probe check(s) failed"
                    (errors if required else warnings).append(message)
            except Exception as exc:
                record["exception"] = f"{type(exc).__name__}: {exc}"
                message = f"{source_key}/{asset['asset_id']}: URL probe failed: {exc}"
                (errors if required else warnings).append(message)
            records.append(record)

    report = {
        "schema_version": 1,
        "probe_id": "PREACQ-URL-PROBE-002",
        "probed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not errors else "fail",
        "scientific_payloads_downloaded": False,
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
        },
        "selected_sources": sorted(selected_sources or configured_sources),
        "asset_count": len(records),
        "records": records,
        "errors": errors,
        "warnings": warnings,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "assets": len(records), "errors": len(errors), "warnings": len(warnings)}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
