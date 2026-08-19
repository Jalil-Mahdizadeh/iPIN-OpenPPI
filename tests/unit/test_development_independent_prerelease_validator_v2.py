from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/model/validate_development_prerelease_independent_v2.py")


def _module():
    specification = importlib.util.spec_from_file_location(
        "independent_development_prerelease_v2", SCRIPT
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_revision_2_validator_imports_no_production_package() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any(name.startswith("ipin_openppi") for name in imports)


def test_revision_2_clean_room_nullability_fixture_and_exact_ast() -> None:
    module = _module()
    audit = {
        "checks": [
            {
                "check_id": "issue_0009_nullability_only_concat_preserves_rows_values_and_type",
                "status": "pass",
            }
        ]
    }
    observed = module._independent_nullability_check(
        Path("src/ipin_openppi/development_evaluation/scoring.py"), audit
    )
    assert observed["status"] == "pass"
    assert observed["detail"]["exact_authorized_AST"] is True
    assert observed["detail"]["fixture_values_and_order_preserved"] is True
