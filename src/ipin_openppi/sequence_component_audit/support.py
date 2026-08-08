"""Safety, provenance, and immutable-output helpers for the bounded audit."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import stat
from typing import Any, Iterable, Mapping

import pyarrow.parquet as pq
import yaml

from ipin_openppi.ingestion.schema import sha256_file


SUMMARY_KEYS = {
    "table",
    "rows",
    "parts",
    "files",
    "schema_name",
    "schema_version",
    "schema_sha256",
}


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def resolve_inside(
    project_root: Path,
    value: str | Path,
    boundary: Path,
    *,
    strict: bool,
) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve(strict=strict)
    root = project_root.resolve(strict=True)
    bounded = boundary.resolve(strict=True)
    resolved.relative_to(bounded)
    if strict:
        current = root
        for part in resolved.relative_to(root).parts:
            current = current / part
            if current.is_symlink():
                raise RuntimeError(f"Symbolic-link path component is prohibited: {current}")
    return resolved


def require_hash(path: Path, expected_sha256: str) -> dict[str, Any]:
    info = path.stat(follow_symlinks=False)
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"Input is not a regular non-link file: {path}")
    observed = sha256_file(path)
    if observed != expected_sha256:
        raise RuntimeError(
            f"Input SHA-256 mismatch for {path}: {observed} != {expected_sha256}"
        )
    return {"path": path.as_posix(), "bytes": info.st_size, "sha256": observed}


def iter_table_summaries(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if SUMMARY_KEYS.issubset(value):
            yield value
            return
        for child in value.values():
            yield from iter_table_summaries(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_table_summaries(child)


def find_table_summary(manifest: Mapping[str, Any], table_name: str) -> Mapping[str, Any]:
    matches = [
        summary
        for summary in iter_table_summaries(manifest)
        if str(summary["table"]) == table_name
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one manifest summary for {table_name}, observed {len(matches)}"
        )
    return matches[0]


def verify_manifest_table(
    *,
    project_root: Path,
    manifest: Mapping[str, Any],
    table_name: str,
    expected_root: Path,
    verify_hashes: bool,
) -> tuple[list[Path], dict[str, Any]]:
    summary = find_table_summary(manifest, table_name)
    root = expected_root.resolve(strict=True)
    files: list[Path] = []
    rows = 0
    total_bytes = 0
    for index, record in enumerate(summary["files"]):
        candidate = Path(str(record["path"]))
        if not candidate.is_absolute():
            candidate = project_root / candidate
        path = candidate.resolve(strict=True)
        path.relative_to(root)
        if path.parent != root or path.name != f"part-{index:05d}.parquet":
            raise RuntimeError(f"Unexpected manifest part path for {table_name}: {path}")
        info = path.stat(follow_symlinks=False)
        if path.is_symlink() or not stat.S_ISREG(info.st_mode):
            raise RuntimeError(f"Manifest part is not a regular non-link file: {path}")
        parquet_rows = int(pq.ParquetFile(path).metadata.num_rows)
        expected = (int(record["bytes"]), int(record["rows"]))
        observed = (info.st_size, parquet_rows)
        if observed != expected:
            raise RuntimeError(f"Manifest size/row mismatch for {path}")
        if verify_hashes and sha256_file(path) != str(record["sha256"]):
            raise RuntimeError(f"Manifest SHA-256 mismatch for {path}")
        files.append(path)
        rows += parquet_rows
        total_bytes += info.st_size
    if rows != int(summary["rows"]) or len(files) != int(summary["parts"]):
        raise RuntimeError(f"Manifest aggregate mismatch for {table_name}")
    return files, {
        "table": table_name,
        "rows": rows,
        "parts": len(files),
        "bytes": total_bytes,
        "schema_name": str(summary["schema_name"]),
        "schema_version": int(summary["schema_version"]),
        "schema_sha256": str(summary["schema_sha256"]),
        "sha256_verification": "complete" if verify_hashes else "smoke_skipped",
    }


def replace_prefix(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {key: replace_prefix(child, old, new) for key, child in value.items()}
    if isinstance(value, list):
        return [replace_prefix(child, old, new) for child in value]
    if isinstance(value, str) and value.startswith(old):
        return new + value[len(old) :]
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_manifest(path: Path, value: Mapping[str, Any]) -> str:
    write_json(path, value)
    digest = sha256_file(path)
    path.with_name(path.name + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="utf-8"
    )
    return digest


def make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError(f"Generated audit output contains a link: {path}")
        if stat.S_ISREG(info.st_mode):
            path.chmod(0o444)
        elif stat.S_ISDIR(info.st_mode):
            path.chmod(0o555)
        else:
            raise RuntimeError(f"Generated audit output has unsupported type: {path}")
    root.chmod(0o555)


def artifact_inventory(root: Path, final_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        if path.is_symlink():
            raise RuntimeError(f"Generated artifact is a link: {path}")
        relative = path.relative_to(root)
        records.append(
            {
                "path": (final_root / relative).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return records


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("audit_id") != "benchmark_eligibility_and_sequence_component_audit_v1":
        raise RuntimeError("Unexpected audit_id")
    authorization = config["authorization"]
    if authorization.get("primary_design") != "reference_sequence_positive_unlabeled_ranking":
        raise RuntimeError("Primary PU-R design is not frozen")
    required_true = (
        "eligibility_audit",
        "aggregate_positive_mapping_audit",
        "sequence_component_construction",
        "return_to_governance_required",
    )
    required_false = (
        "candidate_pair_materialization",
        "evidence_indicator_construction",
        "interaction_label_construction",
        "negative_label_construction",
        "pseudo_negative_sampling",
        "c1_c2_c3_assignment",
        "split_construction",
        "structural_mapping",
        "model_implementation",
        "model_training",
        "model_selection",
        "prevalence_estimation",
        "calibration",
        "external_panel_input_use",
    )
    if any(authorization.get(key) is not True for key in required_true):
        raise RuntimeError("Required audit authorization is absent")
    if any(authorization.get(key) is not False for key in required_false):
        raise RuntimeError("A prohibited downstream authorization is not false")
    components = config["sequence_components"]
    if (
        components.get("primary_identity_threshold_percent") != 30
        or components.get("exact_integer_identity_and_endpoint_coverage_postfilter")
        is not True
        or components.get("below_exact_criteria_behavior")
        != "exclude_and_count_fail_closed"
        or components.get("emitted_thresholds_percent") != [40, 30, 20]
        or float(components.get("minimum_endpoint_coverage")) != 0.8
        or float(components.get("search_minimum_identity")) != 0.2
        or components.get("split_assignment_authorized") is not False
        or components.get("c1_c2_c3_assignment_authorized") is not False
    ):
        raise RuntimeError("Sequence-component policy differs from the accepted scope")
    eligibility = config["eligibility_policy"]
    if (
        eligibility.get("imputation_authorized") is not False
        or eligibility.get("candidate_pair_rows_authorized") is not False
        or eligibility.get("candidate_endpoint_unit")
        != "distinct_frozen_reference_sequence_sha256"
    ):
        raise RuntimeError("Eligibility policy is not fail-closed")
    positive = config["positive_mapping_policy"]
    if (
        positive.get("pair_level_output_authorized") is not False
        or positive.get("evidence_indicator_construction_authorized") is not False
        or positive.get("source_datasets") != ["HI-II-14", "HuRI"]
    ):
        raise RuntimeError("Positive mapping scope differs from accepted primary evidence")
    tool = config["mmseqs2"]
    if (
        int(tool["search_parameters"][tool["search_parameters"].index("--max-seqs") + 1])
        < int(config["expected_preflight"]["eligible_reference_sequences"])
        or tool["alignment_output_fields"][:4]
        != ["query", "target", "mismatch", "alnlen"]
    ):
        raise RuntimeError("MMseqs2 search/output parameters can truncate identity")


def require_scoped_outputs(
    *, paths: Iterable[Path], allow_dirty: bool, skip_input_hashes: bool
) -> bool:
    paths = tuple(paths)
    smoke = all(any(part.startswith("_smoke_") for part in path.parts) for path in paths)
    if allow_dirty != smoke:
        raise RuntimeError("--allow-dirty is restricted to consistently named _smoke_ outputs")
    if skip_input_hashes and not smoke:
        raise RuntimeError("Skipping input hashes is restricted to _smoke_ outputs")
    return smoke


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
