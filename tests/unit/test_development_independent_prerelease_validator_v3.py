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
    # Isolate the degree semantics against the current source. The historical
    # production validator retains its original immutable hash; drift rejection
    # is exercised separately below.
    scoring = Path("src/ipin_openppi/development_evaluation/scoring.py")
    module.CORRECTED_SCORING_SHA256 = module._sha256(scoring)
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


def test_revision_3_validator_rejects_source_hash_drift() -> None:
    module = _module()
    module.CORRECTED_SCORING_SHA256 = "0" * 64
    audit = {"checks": [{
        "check_id": "issue_0010_source_design_degree_guard_and_pooled_scorer_features",
        "status": "pass",
    }]}
    observed = module._independent_degree_check(
        Path("src/ipin_openppi/development_evaluation/scoring.py"), audit
    )
    assert observed["status"] == "fail"
    assert observed["detail"]["required_source_invariants_present"] is True
