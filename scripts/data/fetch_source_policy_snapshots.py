#!/usr/bin/env python3
"""Freeze official source-policy pages and record byte-level provenance."""

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


POLICY_PAGES = (
    (
        "huri_download_and_terms",
        "https://interactome-atlas.org/download",
        "huri_download_and_terms.html",
    ),
    (
        "uniprot_license",
        "https://www.uniprot.org/help/license",
        "uniprot_license.html",
    ),
    (
        "intact_about_and_license",
        "https://www.ebi.ac.uk/intact/about",
        "intact_about_and_license.html",
    ),
    (
        "rcsb_pdb_usage_policy",
        "https://www1.rcsb.org/pages/usage-policy",
        "rcsb_pdb_usage_policy.html",
    ),
    (
        "pdbe_public_data_access_statement",
        "https://www.ebi.ac.uk/pdbe/about/public-data-access-statement",
        "pdbe_public_data_access_statement.html",
    ),
    (
        "embl_ebi_terms_of_use",
        "https://www.ebi.ac.uk/about/terms-of-use",
        "embl_ebi_terms_of_use.html",
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    output_dir = args.output_dir.resolve()
    try:
        output_dir.relative_to(repo_root)
    except ValueError as exc:
        raise SystemExit("output directory must remain beneath the repository root") from exc

    inside_apptainer = bool(os.environ.get("APPTAINER_CONTAINER") or os.environ.get("SINGULARITY_CONTAINER"))
    if not inside_apptainer:
        raise SystemExit("policy snapshots must be fetched inside Apptainer")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty snapshot directory: {output_dir}")

    retrieved_at = datetime.now(timezone.utc).isoformat()
    payloads: list[tuple[str, bytes]] = []
    records: list[dict[str, object]] = []
    opener = urllib.request.build_opener()
    for policy_id, url, filename in POLICY_PAGES:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "iPIN-OpenPPI-source-audit/1.0 (+research provenance)",
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
            },
            method="GET",
        )
        with opener.open(request, timeout=args.timeout_seconds) as response:
            content = response.read()
            status = getattr(response, "status", None)
            final_url = response.geturl()
            headers = response.headers
        digest = hashlib.sha256(content).hexdigest()
        payloads.append((filename, content))
        records.append(
            {
                "policy_id": policy_id,
                "requested_url": url,
                "final_url": final_url,
                "http_status": status,
                "filename": filename,
                "bytes": len(content),
                "sha256": digest,
                "content_type": headers.get("Content-Type"),
                "etag": headers.get("ETag"),
                "last_modified": headers.get("Last-Modified"),
                "retrieved_at_utc": retrieved_at,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=False)
    for filename, content in payloads:
        (output_dir / filename).write_bytes(content)
    manifest = {
        "schema_version": 1,
        "snapshot_id": "SOURCE-POLICY-SNAPSHOT-2026-08-03",
        "retrieved_at_utc": retrieved_at,
        "purpose": "internal provenance snapshot before scientific-source acquisition",
        "runtime": {
            "inside_apptainer": inside_apptainer,
            "apptainer_container": os.environ.get("APPTAINER_CONTAINER")
            or os.environ.get("SINGULARITY_CONTAINER"),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "records": records,
    }
    manifest_path = output_dir / "SNAPSHOT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "pages": len(records), "manifest": str(manifest_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
