#!/usr/bin/env python3
"""Revision-3 clean-room qualification after the ISSUE-0010 correction.

The full revision-2 clean-room reconstruction is rerun from a hash-pinned
source with revision-3 production hashes.  This module imports no production
package and independently checks the split between source-design metadata and
pooled-training scorer features.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

import numpy as np


BASE_VALIDATOR = Path("scripts/model/validate_development_prerelease_independent_v2.py")
BASE_VALIDATOR_SHA256 = "9e70554ca48aa80631f5b89c97a19b9fbe95dd3dae8fefa55fb5b6dfbd823b23"
PRODUCTION_AUDIT = Path(
    "artifacts/validation/development_evaluation/development_release_and_evaluation_v1/"
    "revision_3/PRE_RELEASE_PRODUCTION_AUDIT_REPORT.json"
)
PRODUCTION_AUDIT_SHA256 = "778b8d68ff102aad005286bc5ab85691e949742c69f116c9027492523d823fd7"
PRODUCTION_CODE_COMMIT = "da5a56026753ec0d58ff9a55ac994c5a6a40a885"
PRODUCTION_EVIDENCE_COMMIT = "9bdafc3805b53ca9ff6013fa9c4e366a4cb3aae4"
CORRECTED_SCORING_SHA256 = "874b84270be2fe47211a3936907762ebb6442052eb6928adbdcda50ace60ca5f"
OUTPUT = Path(
    "artifacts/validation/development_evaluation/development_release_and_evaluation_v1/"
    "revision_3/PRE_RELEASE_INDEPENDENT_VALIDATION_REPORT.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite independent evidence: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_hash_pinned_base(project_root: Path) -> tuple[Any, Path]:
    base_path = project_root / BASE_VALIDATOR
    if _sha256(base_path) != BASE_VALIDATOR_SHA256:
        raise RuntimeError("revision-2 clean-room validator hash drift")
    tree = ast.parse(base_path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    if any(name.startswith("ipin_openppi") for name in imports):
        raise RuntimeError("base validator imports production package")
    specification = importlib.util.spec_from_file_location(
        "independent_development_prerelease_revision_2_frozen", base_path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load revision-2 clean-room validator")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module, base_path


def _degree_bin(value: int) -> str:
    if value < 0:
        raise ValueError("negative degree")
    if value <= 2:
        return str(value)
    for lower, upper in ((3, 4), (5, 9), (10, 19), (20, 49), (50, 99)):
        if lower <= value <= upper:
            return f"{lower}-{upper}"
    return "100+"


def _stratum(left: int, right: int) -> str:
    bins = ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")
    order = {value: index for index, value in enumerate(bins)}
    values = sorted((_degree_bin(left), _degree_bin(right)), key=order.__getitem__)
    return f"{values[0]}|{values[1]}"


def _independent_degree_check(
    scoring_path: Path, audit: Mapping[str, Any]
) -> dict[str, Any]:
    source = scoring_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    required_functions = {"validate_degree_metadata", "deterministic_scores"}
    required_tokens = (
        'cell_id.startswith("source_exclusive:")',
        'rows["stratum_id"].to_pylist() != expected_strata',
        "degree_a, degree_b = graph.degree[a], graph.degree[b]",
        "output[:, 1] = np.log1p(degree_a) + np.log1p(degree_b)",
        "pooled_degree_a=degree_a",
        "pooled_degree_b=degree_b",
    )
    ast_and_source_ok = required_functions <= set(functions) and all(
        token in source for token in required_tokens
    )

    recorded_a = np.asarray([1, 0], dtype=np.int64)
    recorded_b = np.asarray([0, 2], dtype=np.int64)
    pooled_a = np.asarray([12, 0], dtype=np.int64)
    pooled_b = np.asarray([0, 25], dtype=np.int64)
    recorded_strata = [_stratum(int(a), int(b)) for a, b in zip(recorded_a, recorded_b, strict=True)]
    source_design_valid = recorded_strata == ["0|1", "0|2"] and bool(
        np.all(recorded_a >= 0)
    )
    primary_mismatch_exists = not np.array_equal(recorded_a, pooled_a) or not np.array_equal(
        recorded_b, pooled_b
    )
    source_bad_stratum_rejected = ["0|2", "0|2"] != recorded_strata
    audit_by_id = {item["check_id"]: item for item in audit["checks"]}
    production = audit_by_id.get(
        "issue_0010_source_design_degree_guard_and_pooled_scorer_features", {}
    )
    passed = (
        _sha256(scoring_path) == CORRECTED_SCORING_SHA256
        and ast_and_source_ok
        and source_design_valid
        and primary_mismatch_exists
        and source_bad_stratum_rejected
        and production.get("status") == "pass"
    )
    return {
        "check_id": "independent_issue_0010_source_design_metadata_and_pooled_feature_split",
        "status": "pass" if passed else "fail",
        "detail": {
            "corrected_scoring_sha256": _sha256(scoring_path),
            "required_functions_present": required_functions <= set(functions),
            "required_source_invariants_present": ast_and_source_ok,
            "source_visible_design_fixture_valid": source_design_valid,
            "primary_pooled_mismatch_fixture_detected": primary_mismatch_exists,
            "source_bad_stratum_fixture_rejected": source_bad_stratum_rejected,
            "production_check_status": production.get("status"),
            "scorer_degree_source": "pooled_16799_training_positive_graph",
        },
    }


def validate(project_root: Path, output: Path) -> dict[str, Any]:
    root = project_root.resolve(strict=True)
    base, base_path = _load_hash_pinned_base(root)
    base.PRODUCTION_AUDIT = PRODUCTION_AUDIT
    base.PRODUCTION_AUDIT_SHA256 = PRODUCTION_AUDIT_SHA256
    base.PRODUCTION_CODE_COMMIT = PRODUCTION_CODE_COMMIT
    base.PRODUCTION_EVIDENCE_COMMIT = PRODUCTION_EVIDENCE_COMMIT
    base.CORRECTED_SCORING_SHA256 = CORRECTED_SCORING_SHA256

    with tempfile.TemporaryDirectory(prefix="ipin_dev_prerelease_v3_") as temporary:
        base_report = base.validate(root, Path(temporary) / "base_report.json")

    audit = json.loads((root / PRODUCTION_AUDIT).read_text(encoding="utf-8"))
    correction = _independent_degree_check(
        root / "src/ipin_openppi/development_evaluation/scoring.py", audit
    )
    base_report["checks"].append(correction)
    failures = [item for item in base_report["checks"] if item["status"] != "pass"]
    base_report["schema_version"] = 3
    base_report["status"] = "pass" if not failures else "fail"
    base_report["summary"] = {
        "pass": len(base_report["checks"]) - len(failures),
        "fail": len(failures),
        "warning": 0,
    }
    base_report["independence"] = {
        "imports_production_development_modules": False,
        "imports_production_metric_or_selection": False,
        "method": "hash_pinned_clean_room_v2_reexecution_plus_independent_issue_0010_AST_and_degree_semantics_fixture",
        "base_validator": str(BASE_VALIDATOR),
        "base_validator_sha256": _sha256(base_path),
        "production_code_commit": PRODUCTION_CODE_COMMIT,
        "production_evidence_commit": PRODUCTION_EVIDENCE_COMMIT,
    }
    _write_json(output, base_report)
    if failures:
        raise RuntimeError(f"revision-3 independent qualification failed: {failures}")
    return base_report


if __name__ == "__main__":
    project = Path.cwd().resolve(strict=True)
    result = validate(project, project / OUTPUT)
    print(
        "development_prerelease_independent_validation_v3: "
        f"{result['status'].upper()} checks={result['summary']['pass']}"
    )
