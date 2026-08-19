from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/model/validate_development_prerelease_independent_v3.py")


def _module():
    specification = importlib.util.spec_from_file_location(
        "independent_development_prerelease_v3", SCRIPT
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_revision_3_validator_imports_no_production_package() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any(name.startswith("ipin_openppi") for name in imports)


def test_revision_3_clean_room_degree_semantics_fixture() -> None:
    module = _module()
    audit = {
        "checks": [
            {
                "check_id": "issue_0010_source_design_degree_guard_and_pooled_scorer_features",
                "status": "pass",
            }
        ]
    }
    observed = module._independent_degree_check(
        Path("src/ipin_openppi/development_evaluation/scoring.py"), audit
    )
    assert observed["status"] == "pass"
    assert observed["detail"]["source_visible_design_fixture_valid"] is True
    assert observed["detail"]["primary_pooled_mismatch_fixture_detected"] is True
    assert observed["detail"]["source_bad_stratum_fixture_rejected"] is True
