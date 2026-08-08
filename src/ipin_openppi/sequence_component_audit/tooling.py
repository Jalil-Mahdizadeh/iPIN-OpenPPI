"""Checksum-pinned, fail-closed preparation of the MMseqs2 ARM64 release."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
from typing import Any, Iterable, Mapping
from urllib.request import Request, urlopen

import yaml

from ipin_openppi.ingestion.common import require_apptainer
from ipin_openppi.ingestion.schema import sha256_file


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def validate_tar_members(members: Iterable[tarfile.TarInfo]) -> None:
    """Reject links, special files, absolute names, and path traversal."""
    seen: set[str] = set()
    for member in members:
        name = member.name
        pure = PurePosixPath(name)
        if (
            not name
            or name in seen
            or pure.is_absolute()
            or ".." in pure.parts
            or "\\" in name
            or not (member.isdir() or member.isreg())
        ):
            raise RuntimeError(f"Unsafe or unsupported archive member: {name!r}")
        seen.add(name)


def _resolve_inside(path: Path, boundary: Path, *, strict: bool) -> Path:
    resolved = path.resolve(strict=strict)
    resolved.relative_to(boundary.resolve(strict=True))
    current = boundary.resolve(strict=True)
    if strict:
        for part in resolved.relative_to(current).parts:
            current = current / part
            if current.is_symlink():
                raise RuntimeError(f"Symbolic-link path component is prohibited: {current}")
    return resolved


def _verify_regular(path: Path, expected_bytes: int, expected_sha256: str) -> None:
    info = path.stat(follow_symlinks=False)
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"Tool asset is not a regular non-link file: {path}")
    if info.st_size != expected_bytes:
        raise RuntimeError(f"Tool asset size mismatch: {path}")
    observed = sha256_file(path)
    if observed != expected_sha256:
        raise RuntimeError(
            f"Tool asset SHA-256 mismatch for {path}: {observed} != {expected_sha256}"
        )


def verify_mmseqs_install(
    *, project_root: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    tool = config["mmseqs2"]
    cache_boundary = (project_root / "artifacts/cache").resolve(strict=True)
    archive = _resolve_inside(
        project_root / str(tool["archive_path"]), cache_boundary, strict=True
    )
    binary = _resolve_inside(
        project_root / str(tool["binary_path"]), cache_boundary, strict=True
    )
    license_path = _resolve_inside(
        project_root / str(tool["license_path"]), cache_boundary, strict=True
    )
    _verify_regular(archive, int(tool["archive_bytes"]), str(tool["archive_sha256"]))
    _verify_regular(binary, int(tool["binary_bytes"]), str(tool["binary_sha256"]))
    _verify_regular(license_path, license_path.stat().st_size, str(tool["license_sha256"]))
    if not os.access(binary, os.X_OK):
        raise RuntimeError(f"MMseqs2 binary is not executable: {binary}")
    completed = subprocess.run(
        [binary.as_posix(), "version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    observed_version = completed.stdout.strip()
    if observed_version != str(tool["version_stdout"]):
        raise RuntimeError(
            f"MMseqs2 version mismatch: {observed_version} != {tool['version_stdout']}"
        )
    return {
        "release": str(tool["release"]),
        "upstream_commit": str(tool["upstream_commit"]),
        "archive": archive.as_posix(),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        "binary": binary.as_posix(),
        "binary_bytes": binary.stat().st_size,
        "binary_sha256": sha256_file(binary),
        "license": license_path.as_posix(),
        "license_sha256": sha256_file(license_path),
        "version_stdout": observed_version,
    }


def _download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "iPIN-OpenPPI/1.0"})
    with urlopen(request, timeout=120) as response, destination.open("wb") as handle:
        while block := response.read(1024 * 1024):
            handle.write(block)


def prepare_mmseqs_install(
    *,
    project_root: Path,
    config_path: Path,
    archive_source: Path | None = None,
) -> dict[str, Any]:
    require_apptainer()
    config = _load_yaml(config_path)
    runtime = config["runtime"]
    if platform.machine() != str(runtime["architecture"]):
        raise RuntimeError("Tool preparation is running on the wrong architecture")
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    if sha256_file(active_container) != str(runtime["container_sha256"]):
        raise RuntimeError("Tool preparation is not running in the pinned SIF")

    tool = config["mmseqs2"]
    cache_boundary = project_root / "artifacts/cache"
    cache_boundary.mkdir(parents=True, exist_ok=True)
    target = project_root / "artifacts/cache/tools/mmseqs2" / str(tool["release"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        result = verify_mmseqs_install(project_root=project_root, config=config)
        result["state"] = "already_present_verified"
        return result

    temporary = Path(tempfile.mkdtemp(prefix=".mmseqs-install-", dir=target.parent))
    try:
        archive = temporary / "mmseqs-linux-arm64.tar.gz"
        if archive_source is None:
            _download(str(tool["archive_url"]), archive)
        else:
            source = archive_source.resolve(strict=True)
            if source.is_symlink() or not source.is_file():
                raise RuntimeError("Supplied archive is not a regular non-link file")
            shutil.copyfile(source, archive)
        _verify_regular(
            archive, int(tool["archive_bytes"]), str(tool["archive_sha256"])
        )
        with tarfile.open(archive, mode="r:gz") as handle:
            members = handle.getmembers()
            validate_tar_members(members)
            handle.extractall(temporary, members=members, filter="data")
        binary = temporary / "mmseqs/bin/mmseqs"
        license_path = temporary / "mmseqs/LICENSE.md"
        _verify_regular(
            binary, int(tool["binary_bytes"]), str(tool["binary_sha256"])
        )
        _verify_regular(
            license_path,
            license_path.stat().st_size,
            str(tool["license_sha256"]),
        )
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
        install_record = {
            "schema_version": 1,
            "source_url": str(tool["archive_url"]),
            "release": str(tool["release"]),
            "upstream_commit": str(tool["upstream_commit"]),
            "archive_sha256": str(tool["archive_sha256"]),
            "binary_sha256": str(tool["binary_sha256"]),
            "license_sha256": str(tool["license_sha256"]),
            "prepared_in_container_sha256": str(runtime["container_sha256"]),
        }
        (temporary / "INSTALL.json").write_text(
            json.dumps(install_record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.rename(target)
    except Exception:
        if temporary.exists() and temporary.is_dir() and not temporary.is_symlink():
            shutil.rmtree(temporary)
        raise

    result = verify_mmseqs_install(project_root=project_root, config=config)
    result["state"] = "installed_and_verified"
    return result
