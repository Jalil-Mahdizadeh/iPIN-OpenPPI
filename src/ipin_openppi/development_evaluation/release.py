"""One-time development-only release path authorised by DEC-0032.

This module deliberately does not import or call ``private_key_paths``.  It
resolves exactly one configured key only after a separately committed gate says
both pre-release validators passed.  No protected-key path is enumerated.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Any, Mapping

import yaml

from ipin_openppi.pair_artifacts.support import cms_decrypt, extract_verified_tar


EXECUTION_ID = "development_release_and_evaluation_execution_v1"
PACKAGE_ID = "pair_level_pu_r_benchmark_artifacts_v1"
AUTHORIZATION_DECISION = "DEC-0032"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"mapping required: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"mapping required: {path}")
    return value


def _reject_links(path: Path, *, stop: Path) -> Path:
    lexical = Path(os.path.abspath(os.fspath(path)))
    boundary = Path(os.path.abspath(os.fspath(stop)))
    lexical.relative_to(boundary)
    current = lexical
    while True:
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            mode = None
        if mode is not None and stat.S_ISLNK(mode):
            raise RuntimeError(f"symbolic-link component prohibited: {current}")
        if current == boundary:
            return lexical
        current = current.parent


def _public_regular(project_root: Path, relative: str, expected_sha256: str) -> Path:
    candidate = _reject_links(project_root / relative, stop=project_root)
    info = candidate.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"regular public artifact required: {relative}")
    if sha256_file(candidate) != expected_sha256:
        raise RuntimeError(f"public artifact hash drift: {relative}")
    return candidate


def _require_private_boundary(project_root: Path) -> Path:
    lexical = _reject_links(project_root / ".private", stop=project_root)
    boundary = lexical.resolve(strict=True)
    mode = boundary.stat(follow_symlinks=False).st_mode
    if not stat.S_ISDIR(mode) or stat.S_IMODE(mode) & 0o077:
        raise RuntimeError(".private must be a mode-0700 non-link directory")
    return boundary


def resolve_development_key_only(project_root: Path, configured_relative: str) -> Path:
    """Resolve and inspect exactly the development release key.

    Callers must invoke :func:`validate_release_activation` first.  The
    function accepts only the exact path frozen in the execution projection.
    """

    expected = ".private/pair_level_pu_r_benchmark_artifacts_v1/development_release_private.pem"
    if configured_relative != expected:
        raise RuntimeError("development key path differs from DEC-0032")
    boundary = _require_private_boundary(project_root)
    lexical = _reject_links(project_root / configured_relative, stop=project_root / ".private")
    resolved = lexical.resolve(strict=True)
    resolved.relative_to(boundary)
    info = lexical.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
        raise RuntimeError("development key must be a mode-0600-or-stricter regular file")
    if stat.S_IMODE(resolved.parent.stat(follow_symlinks=False).st_mode) & 0o077:
        raise RuntimeError("development key directory must deny group/world access")
    return resolved


def _private_target(project_root: Path, relative: str) -> Path:
    boundary = _require_private_boundary(project_root)
    lexical = _reject_links(project_root / relative, stop=project_root / ".private")
    lexical.resolve(strict=False).relative_to(boundary)
    if lexical.exists():
        raise RuntimeError(f"one-time release target already exists: {relative}")
    parent = lexical.parent
    parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    current = parent.resolve(strict=True)
    while True:
        info = current.stat(follow_symlinks=False)
        if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
            raise RuntimeError("private release ancestors must be mode 0700")
        if current == boundary:
            break
        current = current.parent
    return lexical


def validate_release_activation(
    *, project_root: Path, execution_config_path: Path, activation_gate_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = _load_yaml(execution_config_path)
    gate = _load_yaml(activation_gate_path)
    if config.get("execution_id") != EXECUTION_ID:
        raise RuntimeError("development execution config identity drift")
    authority = config.get("authority", {})
    if not str(authority.get("decision", "")).endswith(
        "DEC-0032-authorize-development-release-and-evaluation.md"
    ):
        raise RuntimeError("DEC-0032 is not the configured authority")
    _public_regular(project_root, str(authority["decision"]), str(authority["decision_sha256"]))
    _public_regular(
        project_root,
        str(config["frozen_inputs"]["training_registry"]),
        str(config["frozen_inputs"]["training_registry_sha256"]),
    )
    if gate.get("development_evaluation", {}).get("authorization_decision") != AUTHORIZATION_DECISION:
        raise RuntimeError("activation gate is not subordinate to DEC-0032")
    qualification = gate.get("development_evaluation", {}).get("pre_release_qualification", {})
    if qualification.get("production_audit") != "pass" or qualification.get("independent_validation") != "pass":
        raise RuntimeError("both pre-release qualifications must pass")
    if gate.get("development_evaluation", {}).get("development_decryption_authorized_now") is not True:
        raise RuntimeError("development decryption is not active")
    if gate.get("protected_test", {}).get("candidate_access_authorized") is not False or gate.get(
        "protected_test", {}
    ).get("truth_access_authorized") is not False:
        raise RuntimeError("activation gate opened a protected boundary")
    for key, report_key, hash_key in (
        ("production_report", "production_audit_report", "production_audit_sha256"),
        ("independent_report", "independent_validation_report", "independent_validation_sha256"),
    ):
        record = qualification.get(key, {})
        path = _public_regular(project_root, str(record[report_key]), str(record[hash_key]))
        report = _load_json(path)
        if report.get("status") != "pass" or report.get("execution_id") != EXECUTION_ID:
            raise RuntimeError("pre-release evidence is not a passing report")
    return config, gate


def _validate_extracted_package(package_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_path = package_root / "DEVELOPMENT_PACKAGE_MANIFEST.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError("development manifest missing after extraction")
    manifest = _load_json(manifest_path)
    if (
        manifest.get("package_id") != PACKAGE_ID
        or manifest.get("package_role") != "encrypted_development_release"
        or manifest.get("status") != "complete_frozen"
        or manifest.get("negative_or_pseudo_negative_state_present") is not False
        or manifest.get("source_assay_publication_fields_in_model_development_tables") is not False
    ):
        raise RuntimeError("released development manifest semantics drift")
    records: list[dict[str, Any]] = []
    for table_name, table_record in sorted(manifest.get("tables", {}).items()):
        for item in table_record.get("files", []):
            relative = Path(str(item["path"]))
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError("development manifest file escapes release root")
            path = package_root / relative
            info = path.stat(follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise RuntimeError("development table is not a regular file")
            observed = sha256_file(path)
            if observed != str(item["sha256"]) or info.st_size != int(item["bytes"]):
                raise RuntimeError("released development table hash/size drift")
            records.append(
                {
                    "table": table_name,
                    "relative_path": relative.as_posix(),
                    "rows": int(item["rows"]),
                    "bytes": int(item["bytes"]),
                    "sha256": observed,
                }
            )
    if not records:
        raise RuntimeError("development package contains no registered tables")
    return manifest, records


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite release evidence: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def release_development_once(
    *, project_root: Path, execution_config_path: Path, activation_gate_path: Path
) -> dict[str, Any]:
    config, gate = validate_release_activation(
        project_root=project_root,
        execution_config_path=execution_config_path,
        activation_gate_path=activation_gate_path,
    )
    release = config["development_release"]
    ciphertext = _public_regular(
        project_root, str(release["ciphertext"]), str(release["ciphertext_sha256"])
    )
    certificate = _public_regular(
        project_root, str(release["certificate"]), str(release["certificate_sha256"])
    )
    target = _private_target(project_root, str(release["release_root"]))
    # This is intentionally the first operation in this call that can inspect a
    # private key. Activation and every immutable public hash were checked first.
    development_key = resolve_development_key_only(project_root, str(release["private_key"]))

    private_parent = target.parent
    temporary_root = Path(tempfile.mkdtemp(prefix="development_release_", dir=private_parent))
    os.chmod(temporary_root, 0o700)
    try:
        archive = temporary_root / "development.tar"
        observed_archive_sha = cms_decrypt(
            ciphertext=ciphertext,
            certificate=certificate,
            private_key=development_key,
            output=archive,
        )
        os.chmod(archive, 0o600)
        if observed_archive_sha != str(release["plaintext_archive_sha256"]):
            raise RuntimeError("decrypted development archive hash drift")
        package_root = temporary_root / "package"
        extract_verified_tar(archive, package_root)
        manifest, table_records = _validate_extracted_package(package_root)
        archive.unlink()
        package_root.replace(target)
        receipt = {
            "schema_version": 1,
            "execution_id": EXECUTION_ID,
            "package_id": PACKAGE_ID,
            "released_at_utc": datetime.now(timezone.utc).isoformat(),
            "authorization_decision": AUTHORIZATION_DECISION,
            "activation_gate": activation_gate_path.relative_to(project_root).as_posix(),
            "activation_gate_sha256": sha256_file(activation_gate_path),
            "training_registry_sha256": config["frozen_inputs"]["training_registry_sha256"],
            "development_ciphertext_sha256": release["ciphertext_sha256"],
            "development_archive_sha256": observed_archive_sha,
            "development_manifest_sha256": sha256_file(target / "DEVELOPMENT_PACKAGE_MANIFEST.json"),
            "development_table_count": len(table_records),
            "development_table_rows": sum(item["rows"] for item in table_records),
            "development_table_bytes": sum(item["bytes"] for item in table_records),
            "private_key_hash_recorded": False,
            "protected_private_key_resolved_or_accessed": False,
            "protected_candidates_accessed": False,
            "protected_truth_accessed": False,
            "model_training_or_checkpoint_change": False,
            "model_evaluation_performed": False,
            "manifest_cells": manifest["cells"],
        }
        _atomic_json(target / "DEVELOPMENT_RELEASE_RECEIPT.json", receipt)
        return receipt
    except Exception:
        if target.exists():
            raise RuntimeError(
                "release failed after target publication; preserve private target for governance review"
            )
        raise
    finally:
        # After a successful atomic package move this only removes the now-empty
        # random private staging directory. Failures preserve no published target.
        if temporary_root.exists() and not any(temporary_root.iterdir()):
            temporary_root.rmdir()
