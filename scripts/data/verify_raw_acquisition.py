#!/usr/bin/env python3
"""Independently verify immutable raw payloads and issue format-level inventories."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO


BLOCK_BYTES = 8 * 1024 * 1024
EXPECTED_HURI_PAIR_LINES = {
    "huri_pairs": 52569,
    "test_space_screen_pairs": 1159,
    "literature_benchmark_pairs": 13441,
    "hi_ii_14_pairs": 13993,
}


class VerificationError(RuntimeError):
    """Raised when an independently checked acquisition invariant fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(BLOCK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(BLOCK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root is not an object: {path}")
    return value


def ensure_regular_unlinked(path: Path, description: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise VerificationError(f"{description} must be a regular unlinked file: {path}")


def ensure_repo_path(repo_root: Path, relative: str, prefix: str | None = None) -> Path:
    candidate = (repo_root / relative).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise VerificationError(f"path leaves repository: {relative}") from exc
    if prefix is not None and not relative.startswith(prefix):
        raise VerificationError(f"path is outside required prefix {prefix}: {relative}")
    ensure_regular_unlinked(candidate, relative)
    return candidate


def atomic_json(repo_root: Path, path: Path, value: dict[str, Any]) -> None:
    try:
        path.resolve().relative_to(repo_root)
    except ValueError as exc:
        raise VerificationError(f"output leaves repository: {path}") from exc
    if path.exists() or path.is_symlink():
        raise VerificationError(f"refusing to overwrite verification output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise VerificationError(f"output parent is linked: {path.parent}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary.exists() and not temporary.is_symlink() and temporary.parent == path.parent:
            temporary.unlink()
        raise


def line_inventory(handle: BinaryIO, count_prefix: bytes | None = None) -> dict[str, Any]:
    lines = 0
    blank_lines = 0
    minimum_fields: int | None = None
    maximum_fields = 0
    prefix_count = 0
    for line in handle:
        lines += 1
        stripped = line.rstrip(b"\r\n")
        if not stripped:
            blank_lines += 1
        fields = stripped.count(b"\t") + 1 if stripped else 0
        minimum_fields = fields if minimum_fields is None else min(minimum_fields, fields)
        maximum_fields = max(maximum_fields, fields)
        if count_prefix is not None and line.startswith(count_prefix):
            prefix_count += 1
    result: dict[str, Any] = {
        "line_count": lines,
        "blank_line_count": blank_lines,
        "minimum_tabular_field_count": minimum_fields,
        "maximum_tabular_field_count": maximum_fields,
    }
    if count_prefix is not None:
        result["prefix"] = count_prefix.decode("ascii")
        result["prefix_count"] = prefix_count
    return result


def gzip_inventory(path: Path, asset_id: str) -> dict[str, Any]:
    prefix = b">" if asset_id in {"canonical_fasta", "additional_isoform_fasta"} else None
    with gzip.open(path, "rb") as handle:
        result = line_inventory(handle, count_prefix=prefix)
    if asset_id == "canonical_dat":
        entries = 0
        with gzip.open(path, "rb") as handle:
            for line in handle:
                if line.rstrip(b"\r\n") == b"//":
                    entries += 1
        result["uniprot_entry_count"] = entries
    return {"inventory_method": "streamed_gzip_lines", **result}


def text_inventory(path: Path, asset_id: str) -> dict[str, Any]:
    prefix = b"[Term]" if asset_id == "intact_controlled_vocabulary" else None
    with path.open("rb") as handle:
        result = line_inventory(handle, count_prefix=prefix)
    if asset_id in EXPECTED_HURI_PAIR_LINES:
        expected = EXPECTED_HURI_PAIR_LINES[asset_id]
        observed = result["line_count"]
        if observed != expected:
            raise VerificationError(
                f"HuRI portal pair count mismatch for {asset_id}: expected {expected}, observed {observed}"
            )
        result["published_pair_count_expected"] = expected
        result["published_pair_count_passed"] = True
    return {"inventory_method": "streamed_text_lines", **result}


def zip_inventory(path: Path) -> dict[str, Any]:
    unsafe: list[str] = []
    links: list[str] = []
    encrypted: list[str] = []
    total_compressed = 0
    total_uncompressed = 0
    maximum_ratio = 0.0
    suffix_counts: dict[str, int] = {}
    with zipfile.ZipFile(path, "r") as archive:
        members = archive.infolist()
        for member in members:
            normalized = member.filename.replace("\\", "/")
            pure = PurePosixPath(normalized)
            if pure.is_absolute() or ".." in pure.parts or normalized.startswith("/"):
                unsafe.append(member.filename)
            if stat.S_ISLNK(member.external_attr >> 16):
                links.append(member.filename)
            if member.flag_bits & 0x1:
                encrypted.append(member.filename)
            total_compressed += member.compress_size
            total_uncompressed += member.file_size
            if member.compress_size:
                maximum_ratio = max(maximum_ratio, member.file_size / member.compress_size)
            suffix = PurePosixPath(normalized).suffix.lower() or "<none>"
            suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
    if unsafe or links or encrypted:
        raise VerificationError(
            f"unsafe ZIP content: paths={len(unsafe)}, links={len(links)}, encrypted={len(encrypted)}"
        )
    if len(members) > 1_000_000 or total_uncompressed > 100 * 1024**3:
        raise VerificationError("ZIP exceeds member-count or uncompressed-size safety bound")
    if maximum_ratio > 1000 and total_uncompressed > 100 * 1024**2:
        raise VerificationError("ZIP exceeds compression-ratio safety bound")
    return {
        "inventory_method": "zip_central_directory_no_extraction",
        "member_count": len(members),
        "total_compressed_bytes": total_compressed,
        "total_uncompressed_bytes": total_uncompressed,
        "maximum_member_compression_ratio": maximum_ratio,
        "member_suffix_counts": dict(sorted(suffix_counts.items())),
        "unsafe_path_count": 0,
        "symlink_member_count": 0,
        "encrypted_member_count": 0,
        "extracted": False,
    }


def payload_inventory(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    detected = record["format_inspection"]["detected_container_format"]
    if detected == "gzip":
        return gzip_inventory(path, record["asset_id"])
    if detected == "zip":
        return zip_inventory(path)
    if detected in {"text", "xml"}:
        return text_inventory(path, record["asset_id"])
    if detected == "pdf":
        with path.open("rb") as handle:
            if not handle.read(8).startswith(b"%PDF-"):
                raise VerificationError(f"PDF signature mismatch: {path}")
        return {"inventory_method": "pdf_signature", "signature_passed": True}
    raise VerificationError(f"unsupported detected payload format: {detected}")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def verify_uniprot_metalink(
    records: list[dict[str, Any]], repo_root: Path
) -> dict[str, Any]:
    uniprot = {record["asset_id"]: record for record in records if record["source_key"] == "uniprot"}
    metalink_record = uniprot.get("release_metalink")
    if metalink_record is None:
        raise VerificationError("UniProt release metalink record is missing")
    metalink_path = ensure_repo_path(
        repo_root, metalink_record["destination"], prefix="data/raw/uniprot/"
    )
    root = ET.parse(metalink_path).getroot()
    version = next(
        (element.text for element in root.iter() if local_name(element.tag) == "version"),
        None,
    )
    if version != "2026_02":
        raise VerificationError(f"UniProt metalink release mismatch: {version!r}")
    license_name = next(
        (
            element.text
            for parent in root.iter()
            if local_name(parent.tag) == "license"
            for element in parent
            if local_name(element.tag) == "name"
        ),
        None,
    )
    if not isinstance(license_name, str) or "CC BY 4.0" not in license_name:
        raise VerificationError(f"UniProt metalink license mismatch: {license_name!r}")
    files: dict[str, dict[str, Any]] = {}
    for file_element in root.iter():
        if local_name(file_element.tag) != "file":
            continue
        name = file_element.attrib.get("name")
        size: int | None = None
        md5: str | None = None
        for descendant in file_element.iter():
            if local_name(descendant.tag) == "size" and descendant.text:
                size = int(descendant.text)
            if (
                local_name(descendant.tag) == "hash"
                and descendant.attrib.get("type", "").lower() == "md5"
            ):
                md5 = descendant.text
        if name:
            files[name] = {"size": size, "md5": md5}
    checked: list[dict[str, Any]] = []
    for asset_id, record in uniprot.items():
        if asset_id == "release_metalink":
            continue
        filename = Path(record["destination"]).name
        entry = files.get(filename)
        if entry is None:
            raise VerificationError(f"UniProt metalink lacks acquired file: {filename}")
        expected_md5 = record["provider_checksum"]["observed"]
        if entry["size"] != record["bytes"] or entry["md5"] != expected_md5:
            raise VerificationError(f"UniProt metalink payload metadata mismatch: {filename}")
        checked.append(
            {
                "asset_id": asset_id,
                "filename": filename,
                "bytes": entry["size"],
                "md5": entry["md5"],
                "passed": True,
            }
        )
    return {
        "release": version,
        "license_name": license_name,
        "metalink_file_count": len(files),
        "acquired_payloads_crosschecked": checked,
        "status": "pass",
    }


def verify_code_record(acquisition: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    code = acquisition["code"]
    commit = code["git"]["commit"]
    script = code["script"]
    completed = subprocess.run(
        ["git", "show", f"{commit}:{script}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    committed_script_sha256 = hashlib.sha256(completed.stdout).hexdigest()
    if committed_script_sha256 != code["script_sha256"]:
        raise VerificationError("acquisition script hash does not match its recorded Git commit")
    lock_path = ensure_repo_path(repo_root, code["qualification_lock"])
    if sha256_file(lock_path) != code["qualification_lock_sha256"]:
        raise VerificationError("qualification lock hash mismatch")
    return {
        "acquisition_commit": commit,
        "script": script,
        "committed_script_sha256": committed_script_sha256,
        "qualification_lock_sha256": code["qualification_lock_sha256"],
        "status": "pass",
    }


def raw_tree_inventory(repo_root: Path, expected_paths: set[Path]) -> dict[str, Any]:
    raw_root = (repo_root / "data/raw").resolve()
    observed: set[Path] = set()
    linked: list[str] = []
    partials: list[str] = []
    for directory, directory_names, file_names in os.walk(raw_root, followlinks=False):
        directory_path = Path(directory)
        for name in list(directory_names):
            path = directory_path / name
            if path.is_symlink():
                linked.append(str(path.relative_to(repo_root)))
        for name in file_names:
            path = directory_path / name
            relative = path.relative_to(repo_root)
            if path.is_symlink():
                linked.append(str(relative))
            observed.add(relative)
            if name.endswith(".partial") or ".partial." in name:
                partials.append(str(relative))
    allowed = expected_paths | {Path("data/raw/README.md")}
    unexpected = sorted(str(path) for path in observed - allowed)
    missing = sorted(str(path) for path in expected_paths - observed)
    if linked or partials or unexpected or missing:
        raise VerificationError(
            "raw tree mismatch: "
            f"links={linked}, partials={partials}, unexpected={unexpected}, missing={missing}"
        )
    return {
        "file_count": len(observed),
        "expected_payload_and_sidecar_count": len(expected_paths),
        "unexpected_files": [],
        "missing_files": [],
        "symbolic_links": [],
        "partial_files": [],
        "status": "pass",
    }


def run(args: argparse.Namespace) -> int:
    repo_root = Path.cwd().resolve()
    container = os.environ.get("APPTAINER_CONTAINER") or os.environ.get("SINGULARITY_CONTAINER")
    if not container:
        raise VerificationError("raw verification must run inside Apptainer")
    acquisition_path = ensure_repo_path(
        repo_root, args.acquisition_manifest, prefix="data/source_manifests/acquisitions/"
    )
    output_path = (repo_root / args.output).resolve()
    try:
        output_path.relative_to(repo_root)
    except ValueError as exc:
        raise VerificationError("output path leaves repository") from exc
    acquisition = load_json(acquisition_path)
    if acquisition.get("status") != "pass" or acquisition.get("errors"):
        raise VerificationError("acquisition manifest is not a clean pass")
    records = acquisition.get("records")
    if not isinstance(records, list) or len(records) != acquisition.get("asset_count"):
        raise VerificationError("acquisition record count mismatch")

    verified_records: list[dict[str, Any]] = []
    expected_raw_paths: set[Path] = set()
    total_bytes = 0
    for record in records:
        destination = ensure_repo_path(repo_root, record["destination"], prefix="data/raw/")
        sidecar = ensure_repo_path(repo_root, record["sidecar"], prefix="data/raw/")
        expected_raw_paths.update(
            {Path(record["destination"]), Path(record["sidecar"])}
        )
        if destination.stat().st_mode & 0o222 or sidecar.stat().st_mode & 0o222:
            raise VerificationError(f"raw payload or sidecar is writable: {destination}")
        sidecar_record = load_json(sidecar)
        for key in (
            "source_key",
            "asset_id",
            "url",
            "destination",
            "bytes",
            "sha256",
            "source_manifest_sha256",
        ):
            if sidecar_record.get(key) != record.get(key):
                raise VerificationError(f"sidecar mismatch for {record['asset_id']}: {key}")
        observed_size = destination.stat().st_size
        observed_sha256 = sha256_file(destination)
        if observed_size != record["bytes"] or observed_sha256 != record["sha256"]:
            raise VerificationError(f"payload size or SHA-256 mismatch: {destination}")
        provider = record.get("provider_checksum", {})
        provider_recheck: dict[str, Any] | None = None
        if provider.get("algorithm") == "md5":
            observed_md5 = md5_file(destination)
            if observed_md5 != provider.get("expected"):
                raise VerificationError(f"provider MD5 recheck failed: {destination}")
            provider_recheck = {"algorithm": "md5", "observed": observed_md5, "passed": True}
        inventory = payload_inventory(destination, record)
        total_bytes += observed_size
        verified_records.append(
            {
                "source_key": record["source_key"],
                "asset_id": record["asset_id"],
                "destination": record["destination"],
                "bytes": observed_size,
                "sha256": observed_sha256,
                "read_only": True,
                "sidecar_passed": True,
                "provider_checksum_recheck": provider_recheck,
                "inventory": inventory,
                "status": "pass",
            }
        )
    if total_bytes != acquisition.get("total_payload_bytes"):
        raise VerificationError("acquisition total byte count mismatch")

    report = {
        "schema_version": 1,
        "verification_id": args.verification_id,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "runtime": {
            "inside_apptainer": True,
            "apptainer_container": container,
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        },
        "acquisition_manifest": {
            "path": str(acquisition_path.relative_to(repo_root)),
            "sha256": sha256_file(acquisition_path),
            "run_id": acquisition["run_id"],
        },
        "code_provenance": verify_code_record(acquisition, repo_root),
        "asset_count": len(verified_records),
        "required_asset_count": acquisition["required_asset_count"],
        "total_payload_bytes": total_bytes,
        "records": verified_records,
        "uniprot_metalink": verify_uniprot_metalink(records, repo_root),
        "raw_tree": raw_tree_inventory(repo_root, expected_raw_paths),
        "label_construction_performed": False,
        "model_training_performed": False,
        "errors": [],
        "warnings": [],
    }
    atomic_json(repo_root, output_path, report)
    print(
        json.dumps(
            {
                "status": "pass",
                "assets": len(verified_records),
                "bytes": total_bytes,
                "output": str(output_path.relative_to(repo_root)),
            }
        ),
        flush=True,
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquisition-manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--verification-id", required=True)
    return parser.parse_args()


def main() -> int:
    try:
        return run(parse_args())
    except (VerificationError, OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
        print(
            json.dumps({"status": "fail", "error": f"{type(exc).__name__}: {exc}"}),
            file=sys.stderr,
            flush=True,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
