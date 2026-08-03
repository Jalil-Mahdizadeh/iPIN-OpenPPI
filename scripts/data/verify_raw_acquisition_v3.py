#!/usr/bin/env python3
"""Active raw verifier with explicit provider-count discrepancy semantics."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


ENTRYPOINT = Path(__file__).resolve()
HARDENED_ENTRYPOINT = ENTRYPOINT.with_name("verify_raw_acquisition_v2.py")
SPEC = importlib.util.spec_from_file_location("hardened_raw_verifier", HARDENED_ENTRYPOINT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load hardened verifier: {HARDENED_ENTRYPOINT}")
HARDENED = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARDENED)
IMPL = HARDENED.IMPL
VerificationError = IMPL.VerificationError


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discrepancy_aware_text_inventory(path: Path, asset_id: str) -> dict[str, Any]:
    prefix = b"[Term]" if asset_id == "intact_controlled_vocabulary" else None
    with path.open("rb") as handle:
        result = IMPL.line_inventory(handle, count_prefix=prefix)
    if asset_id in IMPL.EXPECTED_HURI_PAIR_LINES:
        advertised = IMPL.EXPECTED_HURI_PAIR_LINES[asset_id]
        observed = result["line_count"]
        result.update(
            {
                "portal_advertised_interaction_count": advertised,
                "downloaded_tsv_row_count": observed,
                "row_count_minus_advertised_count": observed - advertised,
                "advertised_count_matches_tsv_rows": observed == advertised,
                "interpretation": (
                    "advertised interaction count and gene-pair TSV rows are distinct source representations; "
                    "the discrepancy is retained and is not a raw-integrity failure"
                ),
            }
        )
    return {"inventory_method": "streamed_text_lines", **result}


PREVIOUS_ATOMIC_JSON = IMPL.atomic_json


def final_atomic_json(repo_root: Path, path: Path, value: dict[str, Any]) -> None:
    discrepancies: list[dict[str, Any]] = []
    for record in value.get("records", []):
        inventory = record.get("inventory", {})
        if inventory.get("advertised_count_matches_tsv_rows") is False:
            discrepancy = {
                "source_key": record["source_key"],
                "asset_id": record["asset_id"],
                "portal_advertised_interaction_count": inventory[
                    "portal_advertised_interaction_count"
                ],
                "downloaded_tsv_row_count": inventory["downloaded_tsv_row_count"],
                "difference": inventory["row_count_minus_advertised_count"],
                "classification": "source_representation_discrepancy_not_integrity_failure",
            }
            discrepancies.append(discrepancy)
            value.setdefault("warnings", []).append(
                f"{record['asset_id']}: portal advertises "
                f"{discrepancy['portal_advertised_interaction_count']} interactions but the immutable TSV has "
                f"{discrepancy['downloaded_tsv_row_count']} rows; preserve both counts"
            )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    value["source_count_discrepancies"] = discrepancies
    value["active_verifier"] = {
        "git_commit": commit,
        "entrypoint": str(ENTRYPOINT.relative_to(repo_root)),
        "entrypoint_sha256": sha256_file(ENTRYPOINT),
        "semantics": "provider-advertised counts are audited metadata, not assumed row-count invariants",
    }
    PREVIOUS_ATOMIC_JSON(repo_root, path, value)


IMPL.text_inventory = discrepancy_aware_text_inventory
IMPL.atomic_json = final_atomic_json


def main() -> int:
    return IMPL.main()


if __name__ == "__main__":
    raise SystemExit(main())
