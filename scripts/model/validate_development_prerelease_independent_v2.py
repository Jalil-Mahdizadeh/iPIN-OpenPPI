#!/usr/bin/env python3
"""Revision-2 clean-room qualification after the ISSUE-0009 correction.

The complete frozen clean-room reconstruction from revision 1 is re-executed
from a hash-pinned source file with revision-2 production hashes.  This wrapper
imports no production package and adds an independent AST plus Arrow fixture
for the sole authorized nullable-schema concatenation change.
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

import pyarrow as pa


EXECUTION_ID = "development_release_and_evaluation_execution_v1"
BASE_VALIDATOR = Path("scripts/model/validate_development_prerelease_independent_v1.py")
BASE_VALIDATOR_SHA256 = "f9c5e7e9ba3ee6cd5fd9aecb1265317a559fbfc8a5e62922cef74a8c380aeea1"
PRODUCTION_AUDIT = Path(
    "artifacts/validation/development_evaluation/development_release_and_evaluation_v1/"
    "revision_2/PRE_RELEASE_PRODUCTION_AUDIT_REPORT.json"
)
PRODUCTION_AUDIT_SHA256 = "963b3a9d0e567bc0dd4d1850bd9d8a9382579f46ce9f4643297923f5ccb4962e"
PRODUCTION_CODE_COMMIT = "90ed5007d1deed7f50bab0f2901bf5780a1ab034"
PRODUCTION_EVIDENCE_COMMIT = "818cadb9e0981a9b13ac6cb70ed8a4e8e24053ca"
CORRECTED_SCORING_SHA256 = "5ccd061814a3d20bb39b54048ef11cf86bc350f832bd373b2d7aca1892feef30"
OUTPUT = Path(
    "artifacts/validation/development_evaluation/development_release_and_evaluation_v1/"
    "revision_2/PRE_RELEASE_INDEPENDENT_VALIDATION_REPORT.json"
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
        raise RuntimeError("revision-1 clean-room validator hash drift")
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
        "independent_development_prerelease_revision_1_frozen", base_path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load frozen clean-room base validator")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module, base_path


def _independent_nullability_check(scoring_path: Path, audit: Mapping[str, Any]) -> dict[str, Any]:
    scoring_text = scoring_path.read_text(encoding="utf-8")
    tree = ast.parse(scoring_text)
    concat_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "concat_tables"
    ]
    exact_ast = len(concat_calls) == 1
    if exact_ast:
        keywords = {keyword.arg: keyword.value for keyword in concat_calls[0].keywords}
        promote = keywords.get("promote_options")
        exact_ast = (
            len(concat_calls[0].args) == 1
            and isinstance(concat_calls[0].args[0], ast.Name)
            and concat_calls[0].args[0].id == "tables"
            and set(keywords) == {"promote_options"}
            and isinstance(promote, ast.Constant)
            and promote.value == "permissive"
        )

    nonnullable = pa.schema(
        [pa.field("pair_id", pa.string(), nullable=False), pa.field("weight", pa.int64(), nullable=False)]
    )
    nullable = pa.schema(
        [pa.field("pair_id", pa.string(), nullable=True), pa.field("weight", pa.int64(), nullable=True)]
    )
    positive = pa.Table.from_arrays(
        [pa.array(["p2", "p1"]), pa.array([1, 1], type=pa.int64())], schema=nonnullable
    )
    unlabeled = pa.Table.from_arrays(
        [pa.array(["u2", "u1"]), pa.array([7, 3], type=pa.int64())], schema=nullable
    )
    combined = pa.concat_tables([positive, unlabeled], promote_options="permissive")
    fixture_ok = (
        combined.num_rows == 4
        and combined.column_names == ["pair_id", "weight"]
        and combined.schema.types == [pa.string(), pa.int64()]
        and combined.to_pydict() == {"pair_id": ["p2", "p1", "u2", "u1"], "weight": [1, 1, 7, 3]}
        and all(field.nullable for field in combined.schema)
    )
    audit_by_id = {item["check_id"]: item for item in audit["checks"]}
    production_check = audit_by_id.get(
        "issue_0009_nullability_only_concat_preserves_rows_values_and_type", {}
    )
    return {
        "status": "pass"
        if exact_ast and fixture_ok and production_check.get("status") == "pass"
        else "fail",
        "detail": {
            "corrected_scoring_sha256": _sha256(scoring_path),
            "concat_call_count": len(concat_calls),
            "exact_authorized_AST": exact_ast,
            "fixture_rows": combined.num_rows,
            "fixture_values_and_order_preserved": fixture_ok,
            "logical_types": [str(value) for value in combined.schema.types],
            "production_preservation_check_status": production_check.get("status"),
        },
    }


def validate(project_root: Path, output: Path) -> dict[str, Any]:
    root = project_root.resolve(strict=True)
    base, base_path = _load_hash_pinned_base(root)
    base.PRODUCTION_AUDIT = PRODUCTION_AUDIT
    base.PRODUCTION_AUDIT_SHA256 = PRODUCTION_AUDIT_SHA256
    base.PRODUCTION_CODE_COMMIT = PRODUCTION_CODE_COMMIT
    base.PRODUCTION_EVIDENCE_COMMIT = PRODUCTION_EVIDENCE_COMMIT
    base.SOURCE_HASHES = dict(base.SOURCE_HASHES)
    base.SOURCE_HASHES["src/ipin_openppi/development_evaluation/scoring.py"] = CORRECTED_SCORING_SHA256

    with tempfile.TemporaryDirectory(prefix="ipin_dev_prerelease_v2_") as temporary:
        base_report = base.validate(root, Path(temporary) / "base_report.json")

    audit_path = root / PRODUCTION_AUDIT
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    correction = _independent_nullability_check(
        root / "src/ipin_openppi/development_evaluation/scoring.py", audit
    )
    correction["check_id"] = "independent_issue_0009_exact_nullability_only_correction"
    base_report["checks"].append(correction)
    failures = [item for item in base_report["checks"] if item["status"] != "pass"]
    base_report["schema_version"] = 2
    base_report["status"] = "pass" if not failures else "fail"
    base_report["summary"] = {
        "pass": len(base_report["checks"]) - len(failures),
        "fail": len(failures),
        "warning": 0,
    }
    base_report["independence"] = {
        "imports_production_development_modules": False,
        "imports_production_metric_or_selection": False,
        "method": "hash_pinned_clean_room_v1_reexecution_plus_independent_issue_0009_AST_and_Arrow_fixture",
        "base_validator": str(BASE_VALIDATOR),
        "base_validator_sha256": _sha256(base_path),
        "production_code_commit": PRODUCTION_CODE_COMMIT,
        "production_evidence_commit": PRODUCTION_EVIDENCE_COMMIT,
    }
    _write_json(output, base_report)
    if failures:
        raise RuntimeError(f"revision-2 independent qualification failed: {failures}")
    return base_report


if __name__ == "__main__":
    project = Path.cwd().resolve(strict=True)
    result = validate(project, project / OUTPUT)
    print(
        "development_prerelease_independent_validation_v2: "
        f"{result['status'].upper()} checks={result['summary']['pass']}"
    )
