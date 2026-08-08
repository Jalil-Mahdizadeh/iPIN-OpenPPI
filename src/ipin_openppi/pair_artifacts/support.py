"""Fail-closed helpers for sealed pair-level PU-R benchmark artifacts."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
from typing import Any, Iterable, Mapping, Sequence

import pyarrow as pa
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import canonical_json
from ipin_openppi.ingestion.schema import SchemaContract, sha256_file
from ipin_openppi.sequence_component_audit.support import (
    load_json,
    load_yaml,
    make_read_only,
    require_hash,
    resolve_inside,
    write_json,
    write_manifest,
)


PACKAGE_ID = "pair_level_pu_r_benchmark_artifacts_v1"
PRIMARY_CELLS = (
    "C1_development",
    "C1_test",
    "C2_development",
    "C2_test",
    "C3_development",
    "C3_test",
)
SOURCES = ("HI-II-14", "HuRI")


def validate_config(config: Mapping[str, Any]) -> None:
    if (
        config.get("package_id") != PACKAGE_ID
        or int(config.get("configuration_revision", 0)) != 1
        or config.get("task")
        != "model_free_pair_level_pu_r_benchmark_artifact_construction"
        or config.get("status") != "authorized_not_executed"
    ):
        raise RuntimeError("Unexpected pair-artifact configuration identity")

    authorization = config["authorization"]
    required_true = (
        "immutable_parent_artifact_use",
        "training_positive_pair_persistence",
        "development_positive_pair_persistence",
        "protected_test_positive_pair_persistence",
        "deterministic_unlabeled_sample_realization",
        "source_exclusive_diagnostic_artifacts",
        "role_ledger_construction",
        "separate_development_candidate_and_truth_sealing",
        "independent_assignment_sample_hash_and_leakage_validation",
        "protected_evaluator_harness_and_fixture_tests",
        "return_to_governance_required",
    )
    required_false = (
        "full_candidate_pair_universe_materialization",
        "negative_label_construction",
        "pseudo_negative_sampling",
        "protocol_modification",
        "frozen_endpoint_component_split_modification",
        "development_release",
        "public_protected_test_candidate_identity",
        "public_protected_test_truth_identity",
        "public_protected_prediction_identity",
        "external_panel_input_use",
        "structural_mapping",
        "model_implementation",
        "model_embedding",
        "model_training",
        "model_tuning",
        "model_selection",
        "model_calibration",
        "model_evaluation",
        "prevalence_estimation",
        "parent_audit_reopening_recomputation_or_extension",
    )
    if (
        authorization.get("primary_design")
        != "reference_sequence_positive_unlabeled_ranking"
    ):
        raise RuntimeError("Primary PU-R design changed")
    if any(authorization.get(key) is not True for key in required_true):
        raise RuntimeError("Required pair-artifact authorization absent")
    if any(authorization.get(key) is not False for key in required_false):
        raise RuntimeError("Prohibited pair-artifact action not false")

    semantics = config["pair_semantics"]
    if (
        semantics.get("c1_role_public_salt")
        != "ipin-openppi-pair-level-pu-r-protocol-v1"
        or str(semantics.get("c1_role_deterministic_seed")) != "20260803"
        or semantics.get("c1_role_bucket_intervals")
        != {"train": [0, 7000], "development": [7000, 8500], "test": [8500, 10000]}
        or semantics.get("c3_component_rule") != "local_domain_union_30"
        or semantics.get("quarantine_reassignment") != "prohibited"
    ):
        raise RuntimeError("Frozen pair semantics changed")

    sampling = config["sampling"]
    expected_caps = {
        "training": 2_000_000,
        "C1_development": 1_000_000,
        "C1_test": 1_000_000,
        "C2_development": 1_000_000,
        "C2_test": 1_000_000,
        "C3_development": 1_000_000,
        "C3_test": 1_000_000,
    }
    if (
        sampling.get("method")
        != "deterministic_stratified_bottom_hash_without_replacement"
        or sampling.get("public_salt") != "ipin-openppi-benchmark-v1"
        or str(sampling.get("deterministic_seed")) != "20260803"
        or sampling.get("sample_caps") != expected_caps
        or sampling.get("cross_cell_unlabeled_pair_reuse_permitted") is not True
        or sampling.get("within_cell_duplicate_pair") != "prohibited"
        or sampling.get("state_field_value") != "unlabeled"
        or sampling.get("negative_interpretation") != "prohibited"
    ):
        raise RuntimeError("Frozen unlabeled-sampling semantics changed")

    boundaries = config["package_boundaries"]
    if (
        boundaries["encrypted_development"].get("release_authorized_now") is not False
        or boundaries["encrypted_protected_candidates"].get("truth_or_state_fields")
        != "prohibited"
        or boundaries["encrypted_protected_candidates"].get(
            "public_pair_or_candidate_identity"
        )
        != "prohibited"
        or boundaries["encrypted_protected_truth"].get(
            "key_must_differ_from_protected_candidates"
        )
        is not True
    ):
        raise RuntimeError("Artifact visibility boundary is unsafe")

    sealing = config["sealing"]
    if (
        sealing.get("archive_format") != "deterministic_ustar"
        or int(sealing.get("archive_mtime", -1)) != 0
        or sealing.get("envelope") != "openssl_cms_der"
        or sealing.get("content_cipher") != "aes-256-cbc"
        or sealing.get("development_candidate_truth_key_separation") is not True
        or sealing.get("private_keys_in_manifest_or_source_control") != "prohibited"
    ):
        raise RuntimeError("Sealing contract changed")

    evaluator = config["protected_evaluator"]
    if (
        evaluator.get("public_pair_keyed_prediction_submission") != "prohibited"
        or evaluator.get("scorer_input_projection")
        != ["candidate_token", "endpoint_a_sha256", "endpoint_b_sha256", "cell_id"]
        or evaluator.get("receipt_root")
        != "artifacts/validation/protected_evaluation_receipts"
        or evaluator.get("prediction_columns") != ["candidate_token", "score"]
        or evaluator.get("candidate_or_internal_prediction_identity_output")
        != "prohibited"
        or evaluator.get("prediction_sha256_before_truth_decryption") != "required"
        or evaluator.get("one_first_evaluation") is not True
        or evaluator.get("exact_full_universe_metrics_without_streaming_full_universe")
        != "prohibited"
    ):
        raise RuntimeError("Protected evaluator boundary changed")

    if any(value != "prohibited" for value in config["claims"].values()):
        raise RuntimeError("A prohibited claim was activated")


def verify_documents(
    *, project_root: Path, config: Mapping[str, Any], verify_hashes: bool
) -> tuple[dict[str, Path], dict[str, Any]]:
    keys = (
        "frozen_protocol_config",
        "protocol_acceptance_decision",
        "protocol_audit_report",
        "protocol_validation_report",
        "frozen_split_manifest",
        "authorization_decision",
        "active_gate",
        "active_status",
        "artifact_schema",
        "development_release_certificate",
        "protected_candidates_certificate",
        "protected_truth_certificate",
    )
    paths: dict[str, Path] = {}
    records: dict[str, Any] = {}
    for key in keys:
        path = resolve_inside(
            project_root, str(config["inputs"][key]), project_root, strict=True
        )
        paths[key] = path
        records[key] = (
            require_hash(path, str(config["inputs"][f"{key}_sha256"]))
            if verify_hashes
            else {
                "path": path.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": "smoke_skipped",
            }
        )
    gate = load_yaml(paths["active_gate"])
    subgate = (
        gate.get("gates", {})
        .get("evidence", {})
        .get("pair_level_pu_r_benchmark_artifacts", {})
    )
    if (
        int(gate.get("schema_version", 0)) != 24
        or subgate.get("status") != "authorized_not_executed"
        or subgate.get("package_id") != PACKAGE_ID
        or subgate.get("deterministic_unlabeled_sample_realization_authorized")
        is not True
        or subgate.get("full_candidate_pair_universe_materialization_authorized")
        is not False
        or subgate.get("model_work_authorized") is not False
    ):
        raise RuntimeError("Active gate does not authorize the exact construction")
    if load_json(paths["protocol_audit_report"]).get("status") != "complete":
        raise RuntimeError("Accepted protocol audit is not complete")
    if load_json(paths["protocol_validation_report"]).get("status") != "pass":
        raise RuntimeError("Accepted protocol validation is not pass")
    if load_json(paths["frozen_split_manifest"]).get("status") != "complete_frozen":
        raise RuntimeError("Frozen split manifest is not complete")
    return paths, records


def reject_symlink_components(path: Path, *, stop: Path) -> Path:
    """Return a lexical absolute path after rejecting links through the boundary."""

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
            raise RuntimeError("Symbolic-link path components are prohibited")
        if current == boundary:
            break
        current = current.parent
    return lexical


def private_key_paths(project_root: Path, config: Mapping[str, Any]) -> dict[str, Path]:
    mapping = {
        "development": "development_release_private_key",
        "protected_candidates": "protected_candidates_private_key",
        "protected_truth": "protected_truth_private_key",
    }
    output: dict[str, Path] = {}
    lexical_boundary = Path(os.path.abspath(os.fspath(project_root / ".private")))
    boundary = lexical_boundary.resolve(strict=True)
    for name, key in mapping.items():
        lexical = reject_symlink_components(
            project_root / str(config["inputs"][key]), stop=lexical_boundary
        )
        path = resolve_inside(project_root, lexical, boundary, strict=True)
        info = path.stat(follow_symlinks=False)
        if path.is_symlink() or not stat.S_ISREG(info.st_mode):
            raise RuntimeError(f"Private key is not a regular non-link file: {name}")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise RuntimeError(f"Private key has group/world permission: {name}")
        if stat.S_IMODE(path.parent.stat().st_mode) & 0o077:
            raise RuntimeError(
                f"Private key directory has group/world permission: {name}"
            )
        output[name] = path
    if len({path.resolve() for path in output.values()}) != 3:
        raise RuntimeError(
            "Development, candidate, and truth private keys are not distinct"
        )
    return output


def _run_bytes(args: Sequence[str]) -> bytes:
    completed = subprocess.run(
        list(args), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return completed.stdout


def certificate_fingerprint(path: Path) -> str:
    der = _run_bytes(("openssl", "x509", "-in", path.as_posix(), "-outform", "DER"))
    return hashlib.sha256(der).hexdigest()


def verify_key_pairs(
    *, paths: Mapping[str, Path], keys: Mapping[str, Path]
) -> dict[str, str]:
    certificates = {
        "development": paths["development_release_certificate"],
        "protected_candidates": paths["protected_candidates_certificate"],
        "protected_truth": paths["protected_truth_certificate"],
    }
    fingerprints: dict[str, str] = {}
    public_key_hashes: set[str] = set()
    for name, certificate in certificates.items():
        certificate_pem = _run_bytes(
            ("openssl", "x509", "-in", certificate.as_posix(), "-pubkey", "-noout")
        )
        certificate_der = subprocess.run(
            ("openssl", "pkey", "-pubin", "-outform", "DER"),
            input=certificate_pem,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        private_der = _run_bytes(
            (
                "openssl",
                "pkey",
                "-in",
                keys[name].as_posix(),
                "-pubout",
                "-outform",
                "DER",
            )
        )
        if private_der != certificate_der:
            raise RuntimeError(f"Private key does not match public certificate: {name}")
        public_key_hashes.add(hashlib.sha256(private_der).hexdigest())
        fingerprints[name] = certificate_fingerprint(certificate)
    if len(public_key_hashes) != 3:
        raise RuntimeError("Sealing keypairs are not cryptographically distinct")
    return fingerprints


def rational_design(population: int, sample: int) -> tuple[int, int, int, int]:
    probability = Fraction(int(sample), int(population))
    weight = 1 / probability
    return (
        probability.numerator,
        probability.denominator,
        weight.numerator,
        weight.denominator,
    )


def write_rows_part(
    *,
    root: Path,
    table_name: str,
    part_index: int,
    rows: Iterable[Mapping[str, Any]],
    contract: SchemaContract,
    compression: str,
) -> dict[str, Any]:
    directory = root / table_name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"part-{part_index:05d}.parquet"
    normalized = contract.normalize_and_validate_rows(table_name, rows)
    table = pa.Table.from_pylist(normalized, schema=contract.arrow_schema(table_name))
    pq.write_table(
        table,
        path,
        compression=compression,
        use_dictionary=True,
        write_statistics=True,
    )
    return file_record(path=path, root=root)


def file_record(*, path: Path, root: Path) -> dict[str, Any]:
    info = path.stat(follow_symlinks=False)
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"Artifact is not a regular non-link file: {path}")
    return {
        "path": path.relative_to(root).as_posix(),
        "rows": (
            int(pq.ParquetFile(path).metadata.num_rows)
            if path.suffix == ".parquet"
            else None
        ),
        "bytes": info.st_size,
        "sha256": sha256_file(path),
    }


def dataset_summary(
    *, root: Path, table_name: str, contract: SchemaContract
) -> dict[str, Any]:
    directory = root / table_name
    files = sorted(directory.glob("part-*.parquet"))
    if not files or any(
        path.name != f"part-{i:05d}.parquet" for i, path in enumerate(files)
    ):
        raise RuntimeError(f"Non-contiguous Parquet parts for {table_name}")
    records = [file_record(path=path, root=root) for path in files]
    return {
        "table": table_name,
        "rows": sum(int(record["rows"]) for record in records),
        "parts": len(records),
        "files": records,
        "schema_name": contract.name,
        "schema_version": contract.version,
        "schema_sha256": contract.sha256,
    }


def verify_arrow_schema(
    *, path: Path, contract: SchemaContract, table_name: str
) -> None:
    observed = pq.ParquetFile(path).schema_arrow
    expected = contract.arrow_schema(table_name)
    if observed.names != expected.names:
        raise RuntimeError(f"Parquet columns differ from contract: {path}")
    for left, right in zip(observed, expected):
        if left.type != right.type:
            raise RuntimeError(
                f"Parquet type differs for {table_name}.{left.name}: {left.type} != {right.type}"
            )


def deterministic_tar(source_root: Path, archive_path: Path) -> str:
    files = [path for path in source_root.rglob("*") if path.is_file()]
    directories = list(
        {
            parent
            for path in files
            for parent in path.parents
            if parent != source_root and parent.is_relative_to(source_root)
        },
    )
    if any(path.is_symlink() for path in (*directories, *files)):
        raise RuntimeError("A sealed package contains a symbolic link")
    entries = sorted(
        [("directory", path) for path in directories]
        + [("file", path) for path in files],
        key=lambda item: item[1].relative_to(source_root).as_posix(),
    )
    with tarfile.open(archive_path, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for kind, path in entries:
            relative = path.relative_to(source_root).as_posix()
            info = tarfile.TarInfo(relative)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            if kind == "directory":
                info.type = tarfile.DIRTYPE
                info.mode = 0o555
                archive.addfile(info)
                continue
            info.size = path.stat().st_size
            info.mode = 0o444
            with path.open("rb") as handle:
                archive.addfile(info, handle)
    return sha256_file(archive_path)


def cms_encrypt(*, archive: Path, certificate: Path, output: Path) -> str:
    subprocess.run(
        (
            "openssl",
            "cms",
            "-encrypt",
            "-binary",
            "-aes-256-cbc",
            "-outform",
            "DER",
            "-in",
            archive.as_posix(),
            "-out",
            output.as_posix(),
            certificate.as_posix(),
        ),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    return sha256_file(output)


def cms_decrypt(
    *, ciphertext: Path, certificate: Path, private_key: Path, output: Path
) -> str:
    subprocess.run(
        (
            "openssl",
            "cms",
            "-decrypt",
            "-binary",
            "-inform",
            "DER",
            "-in",
            ciphertext.as_posix(),
            "-recip",
            certificate.as_posix(),
            "-inkey",
            private_key.as_posix(),
            "-out",
            output.as_posix(),
        ),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    return sha256_file(output)


def extract_verified_tar(archive_path: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive_path, mode="r:") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if names != sorted(names):
            raise RuntimeError("Archive entries are not sorted")
        for member in members:
            candidate = Path(member.name)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise RuntimeError("Archive member escapes target")
            output = target / candidate
            output.resolve(strict=False).relative_to(target.resolve())
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise RuntimeError("Archive contains a non-file/non-directory entry")
            output.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError("Archive file has no payload")
            with output.open("wb") as handle:
                shutil.copyfileobj(source, handle)


def manifest_payload_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = [
    "PACKAGE_ID",
    "PRIMARY_CELLS",
    "SOURCES",
    "certificate_fingerprint",
    "cms_decrypt",
    "cms_encrypt",
    "dataset_summary",
    "deterministic_tar",
    "extract_verified_tar",
    "file_record",
    "load_json",
    "load_yaml",
    "make_read_only",
    "manifest_payload_hash",
    "private_key_paths",
    "rational_design",
    "reject_symlink_components",
    "resolve_inside",
    "validate_config",
    "verify_arrow_schema",
    "verify_documents",
    "verify_key_pairs",
    "write_json",
    "write_manifest",
    "write_rows_part",
]
