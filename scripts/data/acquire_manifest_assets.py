#!/usr/bin/env python3
"""Atomically acquire only assets authorized by a pre-acquisition manifest set."""

from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import os
import platform
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

import yaml


ALLOWED_HOSTS = frozenset(
    {
        "interactome-atlas.org",
        "media.springernature.com",
        "zenodo.org",
        "ftp.uniprot.org",
        "ftp.ebi.ac.uk",
        "www.ebi.ac.uk",
        "mips.helmholtz-muenchen.de",
    }
)
BLOCK_BYTES = 8 * 1024 * 1024
PROGRESS_BYTES = 256 * 1024 * 1024
MINIMUM_FREE_BYTES = 5 * 1024 * 1024 * 1024
ADDITIONAL_CA_CERTIFICATES = {
    "mips.helmholtz-muenchen.de": {
        "path": "governance/provenance/tls/HARICA-GEANT-TLS-R1.pem",
        "pem_sha256": "cdc78c3185ce918c8e87f9b2559197d641288e564c5a8b789cd796abdea298d4",
        "der_fingerprint_sha256": (
            "5b678dc44095a52895b63b31f27227f4b36c3e347491bf2bfa691837a5fb8c79"
        ),
        "source_url": "https://repo.harica.gr/certs/HARICA-GEANT-TLS-R1.der",
    }
}


class AcquisitionError(RuntimeError):
    """Raised when provenance, integrity, or path controls fail."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise AcquisitionError(f"YAML root is not a mapping: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(BLOCK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def provider_hasher(algorithm: str | None) -> Any | None:
    if algorithm is None:
        return None
    normalized = algorithm.lower()
    if normalized == "md5":
        return hashlib.md5(usedforsecurity=False)
    try:
        return hashlib.new(normalized)
    except ValueError as exc:
        raise AcquisitionError(f"unsupported provider-checksum algorithm: {algorithm}") from exc


def ensure_inside_apptainer() -> str:
    container = os.environ.get("APPTAINER_CONTAINER") or os.environ.get("SINGULARITY_CONTAINER")
    if not container:
        raise AcquisitionError("scientific acquisition must run inside Apptainer")
    return container


def relative_file(repo_root: Path, relative: str) -> Path:
    candidate = (repo_root / relative).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise AcquisitionError(f"path leaves repository root: {relative}") from exc
    if not candidate.is_file() or candidate.is_symlink():
        raise AcquisitionError(f"required regular file is missing or linked: {relative}")
    return candidate


def ensure_safe_directory(path: Path, repo_root: Path) -> None:
    try:
        relative = path.relative_to(repo_root)
    except ValueError as exc:
        raise AcquisitionError(f"directory leaves repository root: {path}") from exc
    current = repo_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AcquisitionError(f"symbolic-link directory is prohibited: {current}")
        if current.exists():
            if not current.is_dir():
                raise AcquisitionError(f"directory component is not a directory: {current}")
        else:
            current.mkdir()


def resolve_destination(repo_root: Path, raw_root: Path, relative: str) -> Path:
    if not relative.startswith("data/raw/"):
        raise AcquisitionError(f"destination is outside the raw zone: {relative}")
    unresolved = repo_root / relative
    normalized = Path(os.path.abspath(unresolved))
    try:
        normalized.relative_to(raw_root)
    except ValueError as exc:
        raise AcquisitionError(f"destination escapes the raw zone: {relative}") from exc
    ensure_safe_directory(normalized.parent, repo_root)
    if normalized.is_symlink():
        raise AcquisitionError(f"destination is a symbolic link: {relative}")
    return normalized


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise AcquisitionError(f"only HTTPS source URLs are allowed: {url}")
    if parsed.hostname.lower() not in ALLOWED_HOSTS:
        raise AcquisitionError(f"source host is not whitelisted: {parsed.hostname}")
    if parsed.username or parsed.password:
        raise AcquisitionError("credentials in source URLs are prohibited")


def build_https_opener(
    repo_root: Path, url: str
) -> tuple[urllib.request.OpenerDirector, dict[str, Any]]:
    hostname = (urllib.parse.urlparse(url).hostname or "").lower()
    context = ssl.create_default_context()
    tls_record: dict[str, Any] = {
        "hostname_verification": True,
        "certificate_verification": True,
        "insecure_mode": False,
        "additional_ca_certificate": None,
    }
    certificate = ADDITIONAL_CA_CERTIFICATES.get(hostname)
    if certificate is not None:
        certificate_path = relative_file(repo_root, str(certificate["path"]))
        observed_sha256 = sha256_file(certificate_path)
        if observed_sha256 != certificate["pem_sha256"]:
            raise AcquisitionError(
                f"additional CA certificate hash mismatch for {hostname}: {observed_sha256}"
            )
        context.load_verify_locations(cafile=str(certificate_path))
        tls_record.update(
            {
                "additional_ca_certificate": str(certificate_path.relative_to(repo_root)),
                "additional_ca_pem_sha256": observed_sha256,
                "additional_ca_der_fingerprint_sha256": certificate[
                    "der_fingerprint_sha256"
                ],
                "additional_ca_source_url": certificate["source_url"],
            }
        )
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    return opener, tls_record


def git_identity(repo_root: Path) -> dict[str, Any]:
    def run(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    try:
        commit = run("rev-parse", "HEAD")
        status = run("status", "--porcelain", "--untracked-files=no")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AcquisitionError("Git identity is required for acquisition provenance") from exc
    return {"commit": commit, "tracked_worktree_clean": status == "", "status": status}


def response_metadata(response: Any) -> dict[str, Any]:
    headers = response.headers
    return {
        "http_status": getattr(response, "status", None),
        "final_url": response.geturl(),
        "content_length": headers.get("Content-Length"),
        "content_type": headers.get("Content-Type"),
        "etag": headers.get("ETag"),
        "last_modified": headers.get("Last-Modified"),
        "content_disposition": headers.get("Content-Disposition"),
        "accept_ranges": headers.get("Accept-Ranges"),
    }


def verify_response_metadata(expected: dict[str, Any], observed: dict[str, Any]) -> None:
    status = observed.get("http_status")
    if not isinstance(status, int) or not 200 <= status < 300:
        raise AcquisitionError(f"unexpected HTTP status: {status}")
    validate_url(str(observed.get("final_url")))
    expected_length = expected.get("content_length_bytes")
    observed_length_text = observed.get("content_length")
    if expected_length is not None:
        if observed_length_text is None or int(observed_length_text) != int(expected_length):
            raise AcquisitionError(
                f"Content-Length mismatch: expected {expected_length}, observed {observed_length_text}"
            )
    expected_etag = expected.get("etag")
    if expected_etag is not None and observed.get("etag") != expected_etag:
        raise AcquisitionError(
            f"ETag mismatch: expected {expected_etag!r}, observed {observed.get('etag')!r}"
        )
    expected_modified = expected.get("last_modified") or expected.get("last_modified_date")
    observed_modified = observed.get("last_modified")
    # Last-Modified is optional HTTP metadata. Some providers expose it on the
    # pre-acquisition HEAD response but omit it from the content GET. Absence is
    # recorded in provenance and is not a contradiction; an explicit different
    # value remains a hard failure. Byte counts and checksums are still enforced.
    if (
        expected_modified is not None
        and observed_modified is not None
        and (not isinstance(observed_modified, str) or expected_modified not in observed_modified)
    ):
        raise AcquisitionError(
            f"Last-Modified mismatch: expected {expected_modified!r}, observed {observed_modified!r}"
        )


def detect_format(path: Path) -> str:
    with path.open("rb") as handle:
        prefix = handle.read(16)
    if prefix.startswith(b"\x1f\x8b"):
        return "gzip"
    if prefix.startswith(b"PK\x03\x04") or prefix.startswith(b"PK\x05\x06"):
        return "zip"
    if prefix.startswith(b"%PDF-"):
        return "pdf"
    if prefix.lstrip().startswith(b"<?xml"):
        return "xml"
    try:
        prefix.decode("utf-8")
    except UnicodeDecodeError:
        return "binary_unknown"
    return "text"


def expected_container_format(declared: str) -> str | None:
    if declared == "pdf":
        return "pdf"
    if declared.endswith("_gzip"):
        return "gzip"
    if declared.startswith("zip_") or declared.endswith("_zip"):
        return "zip"
    return None


def inspect_zip(path: Path) -> dict[str, Any]:
    unsafe_names: list[str] = []
    linked_names: list[str] = []
    encrypted_names: list[str] = []
    total_compressed = 0
    total_uncompressed = 0
    maximum_ratio = 0.0
    with zipfile.ZipFile(path, "r") as archive:
        members = archive.infolist()
        for member in members:
            normalized_name = member.filename.replace("\\", "/")
            pure = PurePosixPath(normalized_name)
            if pure.is_absolute() or ".." in pure.parts or normalized_name.startswith("/"):
                unsafe_names.append(member.filename)
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                linked_names.append(member.filename)
            if member.flag_bits & 0x1:
                encrypted_names.append(member.filename)
            total_compressed += member.compress_size
            total_uncompressed += member.file_size
            if member.compress_size:
                maximum_ratio = max(maximum_ratio, member.file_size / member.compress_size)
    if unsafe_names or linked_names or encrypted_names:
        raise AcquisitionError(
            "unsafe ZIP members detected: "
            f"paths={len(unsafe_names)}, links={len(linked_names)}, encrypted={len(encrypted_names)}"
        )
    if len(members) > 1_000_000:
        raise AcquisitionError(f"ZIP member count exceeds safety bound: {len(members)}")
    if total_uncompressed > 100 * 1024 * 1024 * 1024:
        raise AcquisitionError(f"ZIP uncompressed size exceeds 100 GiB: {total_uncompressed}")
    if maximum_ratio > 1000 and total_uncompressed > 100 * 1024 * 1024:
        raise AcquisitionError(f"ZIP compression ratio exceeds safety bound: {maximum_ratio:.1f}")
    return {
        "member_count": len(members),
        "total_compressed_bytes": total_compressed,
        "total_uncompressed_bytes": total_uncompressed,
        "maximum_member_compression_ratio": maximum_ratio,
        "unsafe_path_count": 0,
        "symlink_member_count": 0,
        "encrypted_member_count": 0,
        "extracted": False,
    }


def inspect_payload(path: Path, declared_format: str) -> dict[str, Any]:
    detected = detect_format(path)
    required_container = expected_container_format(declared_format)
    if required_container is not None and detected != required_container:
        raise AcquisitionError(
            f"format mismatch for {path.name}: declared {declared_format}, detected {detected}"
        )
    inspection: dict[str, Any] = {
        "declared_format": declared_format,
        "detected_container_format": detected,
    }
    if detected == "zip":
        inspection["archive"] = inspect_zip(path)
    elif detected == "gzip":
        with gzip.open(path, "rb") as handle:
            prefix = handle.read(65536)
        inspection["gzip_prefix_decompressed_bytes"] = len(prefix)
    return inspection


def atomic_json(path: Path, value: dict[str, Any], read_only: bool = False) -> None:
    if path.exists() or path.is_symlink():
        raise AcquisitionError(f"refusing to overwrite JSON output: {path}")
    ensure_safe_directory(path.parent, Path.cwd().resolve())
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
        if read_only:
            path.chmod(0o444)
    except Exception:
        if temporary.exists() and not temporary.is_symlink() and temporary.parent == path.parent:
            temporary.unlink()
        raise


def existing_record(
    destination: Path,
    sidecar: Path,
    asset: dict[str, Any],
    source_manifest_sha256: str,
) -> dict[str, Any] | None:
    destination_present = destination.exists() or destination.is_symlink()
    sidecar_present = sidecar.exists() or sidecar.is_symlink()
    if not destination_present and not sidecar_present:
        return None
    if destination.is_symlink() or sidecar.is_symlink():
        raise AcquisitionError(f"linked existing raw path is prohibited: {destination}")
    if not destination.is_file() or not sidecar.is_file():
        raise AcquisitionError(f"raw payload and provenance sidecar must both exist: {destination}")
    record = json.loads(sidecar.read_text(encoding="utf-8"))
    if record.get("url") != asset["url"]:
        raise AcquisitionError(f"existing sidecar URL mismatch: {destination}")
    if record.get("source_manifest_sha256") != source_manifest_sha256:
        raise AcquisitionError(f"existing sidecar manifest hash mismatch: {destination}")
    observed_size = destination.stat().st_size
    if observed_size != record.get("bytes"):
        raise AcquisitionError(f"existing payload size mismatch: {destination}")
    observed_sha256 = sha256_file(destination)
    if observed_sha256 != record.get("sha256"):
        raise AcquisitionError(f"existing payload SHA-256 mismatch: {destination}")
    expected_length = asset.get("expected", {}).get("content_length_bytes")
    if expected_length is not None and observed_size != int(expected_length):
        raise AcquisitionError(f"existing payload differs from expected length: {destination}")
    return {
        **record,
        "run_disposition": "reused_existing_verified",
        "verified_at_utc": utc_now(),
    }


def stream_download(
    response: Any,
    handle: BinaryIO,
    provider_algorithm: str | None,
    label: str,
) -> tuple[int, str, str | None]:
    sha256 = hashlib.sha256()
    provider = provider_hasher(provider_algorithm)
    total = 0
    next_progress = PROGRESS_BYTES
    while True:
        block = response.read(BLOCK_BYTES)
        if not block:
            break
        handle.write(block)
        sha256.update(block)
        if provider is not None:
            provider.update(block)
        total += len(block)
        if total >= next_progress:
            print(json.dumps({"event": "progress", "asset": label, "bytes": total}), flush=True)
            next_progress += PROGRESS_BYTES
    return total, sha256.hexdigest(), provider.hexdigest() if provider is not None else None


def acquire_asset(
    repo_root: Path,
    raw_root: Path,
    source_key: str,
    asset: dict[str, Any],
    source_manifest_path: Path,
    source_manifest_sha256: str,
    timeout_seconds: float,
    retries: int,
) -> dict[str, Any]:
    url = str(asset["url"])
    validate_url(url)
    destination = resolve_destination(repo_root, raw_root, str(asset["destination"]))
    sidecar = destination.with_name(destination.name + ".acquisition.json")
    reused = existing_record(destination, sidecar, asset, source_manifest_sha256)
    if reused is not None:
        print(json.dumps({"event": "reuse", "asset": asset["asset_id"]}), flush=True)
        return reused

    opener, tls_record = build_https_opener(repo_root, url)
    provider_checksum = asset.get("expected", {}).get("provider_checksum")
    provider_algorithm = provider_checksum.get("algorithm") if isinstance(provider_checksum, dict) else None
    provider_expected = provider_checksum.get("value") if isinstance(provider_checksum, dict) else None
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".partial", dir=destination.parent
        )
        temporary = Path(temporary_name)
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "iPIN-OpenPPI-acquisition/1.0 (+research provenance)",
                    "Accept": "*/*",
                    "Accept-Encoding": "identity",
                },
                method="GET",
            )
            acquired_at = utc_now()
            with opener.open(request, timeout=timeout_seconds) as response:
                observed = response_metadata(response)
                verify_response_metadata(asset.get("expected", {}), observed)
                with os.fdopen(descriptor, "wb") as handle:
                    descriptor = -1
                    total, sha256, provider_observed = stream_download(
                        response, handle, provider_algorithm, f"{source_key}/{asset['asset_id']}"
                    )
                    handle.flush()
                    os.fsync(handle.fileno())
            expected_length = asset.get("expected", {}).get("content_length_bytes")
            if expected_length is not None and total != int(expected_length):
                raise AcquisitionError(
                    f"downloaded byte count mismatch: expected {expected_length}, observed {total}"
                )
            response_length = observed.get("content_length")
            if response_length is not None and total != int(response_length):
                raise AcquisitionError(
                    f"response byte count mismatch: header {response_length}, observed {total}"
                )
            if provider_expected is not None and provider_observed != str(provider_expected).lower():
                raise AcquisitionError(
                    f"provider checksum mismatch: expected {provider_expected}, observed {provider_observed}"
                )
            inspection = inspect_payload(temporary, str(asset["format"]))
            record = {
                "schema_version": 1,
                "source_key": source_key,
                "asset_id": asset["asset_id"],
                "required": bool(asset["required"]),
                "url": url,
                "destination": str(destination.relative_to(repo_root)),
                "sidecar": str(sidecar.relative_to(repo_root)),
                "source_manifest": str(source_manifest_path.relative_to(repo_root)),
                "source_manifest_sha256": source_manifest_sha256,
                "acquired_at_utc": acquired_at,
                "bytes": total,
                "sha256": sha256,
                "provider_checksum": {
                    "algorithm": provider_algorithm,
                    "expected": provider_expected,
                    "observed": provider_observed,
                    "passed": provider_expected is None or provider_observed == str(provider_expected).lower(),
                },
                "tls": tls_record,
                "response": observed,
                "format_inspection": inspection,
                "run_disposition": "downloaded_new",
                "raw_immutable": True,
            }
            if destination.exists() or destination.is_symlink():
                raise AcquisitionError(f"destination appeared during download: {destination}")
            os.replace(temporary, destination)
            destination.chmod(0o444)
            atomic_json(sidecar, record, read_only=True)
            print(
                json.dumps(
                    {
                        "event": "acquired",
                        "asset": f"{source_key}/{asset['asset_id']}",
                        "bytes": total,
                        "sha256": sha256,
                    }
                ),
                flush=True,
            )
            return record
        except Exception as exc:
            last_error = exc
            if descriptor >= 0:
                os.close(descriptor)
            if temporary.exists() and not temporary.is_symlink() and temporary.parent == destination.parent:
                temporary.unlink()
            if attempt < retries:
                delay = min(2**attempt, 10)
                print(
                    json.dumps(
                        {
                            "event": "retry",
                            "asset": f"{source_key}/{asset['asset_id']}",
                            "attempt": attempt,
                            "delay_seconds": delay,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    ),
                    flush=True,
                )
                time.sleep(delay)
    raise AcquisitionError(
        f"failed after {retries} attempts: {source_key}/{asset['asset_id']}: {last_error}"
    )


def selected_manifest_entries(index: dict[str, Any], selected: set[str]) -> list[dict[str, str]]:
    entries = index.get("manifests")
    if not isinstance(entries, list):
        raise AcquisitionError("index manifests must be a list")
    available = {entry.get("source_key") for entry in entries if isinstance(entry, dict)}
    unknown = selected - available
    if unknown:
        raise AcquisitionError(f"unknown selected sources: {sorted(unknown)}")
    return [entry for entry in entries if not selected or entry.get("source_key") in selected]


def build_plan(
    repo_root: Path, index: dict[str, Any], entries: list[dict[str, str]]
) -> tuple[list[dict[str, Any]], int]:
    plan: list[dict[str, Any]] = []
    expected_bytes = 0
    seen_destinations: set[str] = set()
    for entry in entries:
        source_key = str(entry["source_key"])
        manifest_path = relative_file(repo_root, str(entry["path"]))
        manifest = load_yaml(manifest_path)
        if manifest.get("source_key") != source_key or manifest.get("approved_for_download") is not True:
            raise AcquisitionError(f"source manifest is not acquisition-approved: {manifest_path}")
        manifest_sha256 = sha256_file(manifest_path)
        for asset in manifest.get("assets", []):
            destination = str(asset["destination"])
            if destination in seen_destinations:
                raise AcquisitionError(f"duplicate destination in active set: {destination}")
            seen_destinations.add(destination)
            validate_url(str(asset["url"]))
            size = asset.get("expected", {}).get("content_length_bytes")
            if size is not None:
                expected_bytes += int(size)
            plan.append(
                {
                    "source_key": source_key,
                    "source_manifest_path": manifest_path,
                    "source_manifest_sha256": manifest_sha256,
                    "asset": asset,
                }
            )
    return plan, expected_bytes


def run(args: argparse.Namespace) -> int:
    repo_root = Path.cwd().resolve()
    if not (repo_root / "governance/START_MANIFEST_v1.yaml").is_file():
        raise AcquisitionError("run from the validated project root")
    container = ensure_inside_apptainer()
    index_path = relative_file(repo_root, str(args.index))
    index = load_yaml(index_path)
    authorization = index.get("authorization", {})
    if authorization.get("scientific_downloads_permitted") is not True:
        raise AcquisitionError("active index does not authorize scientific downloads")
    if authorization.get("required_runtime") != "apptainer":
        raise AcquisitionError("active index runtime authorization is not Apptainer")
    if authorization.get("label_construction_permitted") is not False:
        raise AcquisitionError("active index must prohibit label construction")
    if authorization.get("model_training_permitted") is not False:
        raise AcquisitionError("active index must prohibit model training")

    git = git_identity(repo_root)
    if not git["tracked_worktree_clean"]:
        raise AcquisitionError(f"tracked Git worktree must be clean: {git['status']}")
    selected = set(args.source or [])
    entries = selected_manifest_entries(index, selected)
    plan, expected_bytes = build_plan(repo_root, index, entries)
    raw_root = (repo_root / "data/raw").resolve()
    ensure_safe_directory(raw_root, repo_root)
    free_bytes = shutil.disk_usage(repo_root).free
    if not args.dry_run and free_bytes < max(MINIMUM_FREE_BYTES, expected_bytes * 2):
        raise AcquisitionError(
            f"insufficient free space: free={free_bytes}, known payload bytes={expected_bytes}"
        )

    run_id = args.run_id
    if not run_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in run_id):
        raise AcquisitionError("run-id must be non-empty and contain only letters, digits, '-' or '_'")
    artifact_dir = repo_root / "artifacts/runs/data_acquisition" / run_id
    ensure_safe_directory(artifact_dir, repo_root)
    report_path = artifact_dir / "download_report.json"
    if report_path.exists() or report_path.is_symlink():
        raise AcquisitionError(f"run report already exists: {report_path}")

    qualification_lock = relative_file(
        repo_root, "containers/locks/ipin-qual-arm64_0.1.0.qualification.lock"
    )
    script_path = Path(__file__).resolve()
    base_report: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "started_at_utc": utc_now(),
        "dry_run": bool(args.dry_run),
        "scientific_payloads_downloaded": False,
        "label_construction_performed": False,
        "model_training_performed": False,
        "runtime": {
            "inside_apptainer": True,
            "apptainer_container": container,
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        },
        "code": {
            "git": git,
            "script": str(script_path.relative_to(repo_root)),
            "script_sha256": sha256_file(script_path),
            "qualification_lock": str(qualification_lock.relative_to(repo_root)),
            "qualification_lock_sha256": sha256_file(qualification_lock),
        },
        "index": {
            "path": str(index_path.relative_to(repo_root)),
            "sha256": sha256_file(index_path),
            "manifest_set_id": index.get("manifest_set_id"),
        },
        "selected_sources": [str(entry["source_key"]) for entry in entries],
        "asset_count": len(plan),
        "required_asset_count": sum(1 for item in plan if item["asset"]["required"]),
        "known_expected_bytes": expected_bytes,
        "free_bytes_at_start": free_bytes,
        "records": [],
        "errors": [],
        "warnings": [],
    }
    if args.dry_run:
        base_report.update(
            {
                "status": "dry_run_pass",
                "completed_at_utc": utc_now(),
                "planned_assets": [
                    {
                        "source_key": item["source_key"],
                        "asset_id": item["asset"]["asset_id"],
                        "url": item["asset"]["url"],
                        "destination": item["asset"]["destination"],
                        "required": item["asset"]["required"],
                    }
                    for item in plan
                ],
            }
        )
        atomic_json(report_path, base_report)
        print(json.dumps({"status": "dry_run_pass", "assets": len(plan)}), flush=True)
        return 0

    lock_path = repo_root / "artifacts/tmp/raw_acquisition.lock"
    ensure_safe_directory(lock_path.parent, repo_root)
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AcquisitionError("another raw-acquisition process holds the project lock") from exc
        for item in plan:
            asset = item["asset"]
            try:
                record = acquire_asset(
                    repo_root=repo_root,
                    raw_root=raw_root,
                    source_key=item["source_key"],
                    asset=asset,
                    source_manifest_path=item["source_manifest_path"],
                    source_manifest_sha256=item["source_manifest_sha256"],
                    timeout_seconds=args.timeout_seconds,
                    retries=args.retries,
                )
                base_report["records"].append(record)
            except Exception as exc:
                message = f"{item['source_key']}/{asset['asset_id']}: {type(exc).__name__}: {exc}"
                if asset["required"]:
                    base_report["errors"].append(message)
                    break
                base_report["warnings"].append(message)
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    if lock_path.exists() and not lock_path.is_symlink() and lock_path.stat().st_size == 0:
        lock_path.unlink()

    base_report["completed_at_utc"] = utc_now()
    base_report["scientific_payloads_downloaded"] = any(
        record.get("run_disposition") == "downloaded_new" for record in base_report["records"]
    )
    base_report["downloaded_new_count"] = sum(
        record.get("run_disposition") == "downloaded_new" for record in base_report["records"]
    )
    base_report["reused_existing_count"] = sum(
        record.get("run_disposition") == "reused_existing_verified"
        for record in base_report["records"]
    )
    base_report["total_payload_bytes"] = sum(record["bytes"] for record in base_report["records"])
    base_report["status"] = "pass" if not base_report["errors"] else "fail"
    atomic_json(report_path, base_report)
    if base_report["errors"]:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "records": len(base_report["records"]),
                    "errors": len(base_report["errors"]),
                    "report": str(report_path.relative_to(repo_root)),
                }
            ),
            flush=True,
        )
        return 1

    acquisition_path = (
        repo_root
        / "data/source_manifests/acquisitions"
        / run_id
        / "ACQUISITION_MANIFEST.json"
    )
    base_report["acquisition_manifest"] = str(acquisition_path.relative_to(repo_root))
    atomic_json(acquisition_path, base_report)
    print(
        json.dumps(
            {
                "status": "pass",
                "records": len(base_report["records"]),
                "bytes": base_report["total_payload_bytes"],
                "manifest": str(acquisition_path.relative_to(repo_root)),
            }
        ),
        flush=True,
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source", action="append")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if args.retries < 1 or args.retries > 5:
        parser.error("--retries must be between 1 and 5")
    return args


def main() -> int:
    try:
        return run(parse_args())
    except AcquisitionError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
