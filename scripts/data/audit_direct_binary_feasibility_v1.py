"""Bounded source acquisition/schema inventory; no outcome labels or model scores.

Run only inside the pinned ARM64 data image. Upstream R is stored as text,
never imported or executed. Raw payloads remain in the ignored run namespace.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def csv_inventory(data: bytes) -> dict:
    """Inventory missingness without replacing missing values by assay zeros."""
    try:
        decoded = data.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        # The source metadata contain a Windows-1252 plus/minus symbol.
        # Strict fallback, recorded explicitly; never replace undecodable bytes.
        decoded = data.decode("cp1252")
        encoding = "cp1252"
    rows = list(csv.reader(io.StringIO(decoded)))
    if not rows:
        raise ValueError("Empty CSV")
    header, body = rows[0], rows[1:]
    if len(header) != len(set(header)):
        raise ValueError("Duplicate CSV column names")
    if any(len(row) != len(header) for row in body):
        raise ValueError("Ragged CSV")
    columns = {}
    for index, name in enumerate(header):
        values = [row[index] for row in body]
        blank = sum(not value.strip() for value in values)
        nonfinite = 0
        finite = 0
        for value in values:
            try:
                number = float(value)
            except ValueError:
                continue
            finite += int(math.isfinite(number))
            nonfinite += int(not math.isfinite(number))
        columns[name] = {
            "unique_text_values": len(set(values)),
            "blank": blank,
            "finite_numeric": finite,
            "nonfinite_numeric_tokens": nonfinite,
            "NA_tokens": sum(value.strip().lower() in {"na", "n/a", "null"} for value in values),
        }
    return {"rows": len(body), "encoding": encoding, "columns": columns}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/work"))
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--resume", action="store_true",
                        help="Resume incomplete acquisition, verifying existing blobs")
    args = parser.parse_args()
    if args.resume and not args.acquire:
        parser.error("--resume requires --acquire")
    root = args.root.resolve()
    config_path = root / "configs/direct_binary_feasibility_v1.json"
    config_data = config_path.read_bytes()
    config = json.loads(config_data)
    protocol = root / config["protocol"]
    if digest(protocol.read_bytes()) != config["protocol_sha256"]:
        raise ValueError("Protocol hash changed")
    entries = config["files"]
    if len(entries) > config["max_files"] or len({x[0] for x in entries}) != len(entries):
        raise ValueError("Invalid file count / duplicate path")
    if sum(x[1] for x in entries) > config["max_total_bytes"]:
        raise ValueError("Byte budget exceeded")
    run = root / "artifacts/runs/direct_binary_feasibility_v1"
    registration = run / "REGISTRATION.json"
    manifest = run / "SOURCE_MANIFEST.json"
    if args.acquire and not args.resume:
        write_new(registration, json_bytes({
            "registered_utc": datetime.now(timezone.utc).isoformat(),
            "protocol_sha256": config["protocol_sha256"],
            "config_sha256": digest(config_data),
            "acquisition_script_sha256": digest(Path(__file__).read_bytes()),
            "source_selection_informed_by_prior_metadata": True,
            "external_preregistration": False,
        }))
    else:
        prior = json.loads(registration.read_bytes())
        if prior["config_sha256"] != digest(config_data):
            raise ValueError("Config changed since registration")
        if args.resume:
            if manifest.exists():
                raise ValueError("Acquisition already complete")
            write_new(run / "ACQUISITION_RECOVERY.json", json_bytes({
                "utc": datetime.now(timezone.utc).isoformat(),
                "script_sha256": digest(Path(__file__).read_bytes()),
                "reason": "Strict UTF-8 parser stopped on source Windows-1252 metadata; add recorded strict fallback and verified resume, preserving all source bytes and registration.",
            }))
    records = []
    for relative, size, expected_blob in entries:
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("Unsafe source path")
        path = run / "raw" / relative
        url = f"https://raw.githubusercontent.com/{config['source_repository']}/{config['source_commit']}/{relative}"
        use_existing = not args.acquire or (args.resume and path.exists())
        if not use_existing:
            with urlopen(url, timeout=30) as response:
                data = response.read(size + 1)
        else:
            data = path.read_bytes()
        if len(data) != size or git_blob(data) != expected_blob:
            raise ValueError(f"Size/blob mismatch: {relative}")
        if not use_existing:
            write_new(path, data)
        record = {"path": str(path.relative_to(root)), "url": url,
                  "bytes": len(data), "git_blob_sha1": git_blob(data), "sha256": digest(data)}
        if args.acquire:
            record["snapshot_utc"] = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
            record["timestamp_basis"] = "local_snapshot_file_mtime"
        if relative.endswith(".csv"):
            record["csv_inventory"] = csv_inventory(data)
        records.append(record)
    result = {"source_commit": config["source_commit"], "files": records,
              "total_bytes": sum(record["bytes"] for record in records),
              "completed_with_script_sha256": digest(Path(__file__).read_bytes()),
              "labels_created": False, "model_scores_computed": False}
    if args.acquire:
        write_new(manifest, json_bytes(result))
    else:
        prior = json.loads(manifest.read_bytes())
        stripped = [dict(record) for record in prior["files"]]
        for record in stripped:
            record.pop("snapshot_utc")
            record.pop("timestamp_basis")
        if stripped != records:
            raise ValueError("Source manifest inventory mismatch")
    print(json.dumps({"files_verified": len(records), "total_bytes": result["total_bytes"],
                      "csv_schemas": {Path(r["path"]).name: {
                          "rows": r["csv_inventory"]["rows"],
                          "column_count": len(r["csv_inventory"]["columns"]),
                          "columns": list(r["csv_inventory"]["columns"]) if len(r["csv_inventory"]["columns"]) < 60 else "matrix axes omitted"
                      } for r in records if "csv_inventory" in r}}, indent=2))


if __name__ == "__main__":
    main()
