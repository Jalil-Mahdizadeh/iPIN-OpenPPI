from __future__ import annotations

from pathlib import Path

import pytest

from ipin_openppi.validation.staging import Checks
from ipin_openppi.validation.systematic_screen_audit import (
    _scope_for_reports,
    _validate_audit_guardrails,
)


def _config() -> dict:
    return {
        "audit_id": "systematic_screen_metadata_v1",
        "audit_version": "0.1.0",
        "task": "systematic_screen_and_negative_evidence_metadata_audit",
        "systematic_universe_requirements": {
            "pair_level_search_space_membership": "positive_only",
            "attempted_state_for_every_opportunity": "unavailable",
        },
        "decision_policy": {
            "complete_attempted_evaluable_universe_reconstructed": False,
            "issue_0003_disposition": "unresolved_resolution_path_3_recommended",
            "calibrated_primary_assay_probability_feasible": False,
            "primary_binary_negative_labels_feasible": False,
            "pu_compatibility_policy_design_feasible": True,
            "conditional_control_panel_analysis_feasible": True,
            "strict_construct_benchmark_feasible": False,
            "label_construction_authorized": False,
            "split_construction_authorized": False,
            "model_training_authorized": False,
        },
        "external_availability_review": {
            "attempted_pair_log_found": False,
            "authors_code_license_file_present": False,
        },
    }


def _audit(config: dict) -> dict:
    requirements = config["systematic_universe_requirements"]
    return {
        "schema_version": 1,
        "audit_id": config["audit_id"],
        "audit_version": "0.1.0",
        "task": config["task"],
        "status": "complete",
        "scope": "metadata_and_semantics_only_no_label_or_split_construction",
        "label_construction_performed": False,
        "split_construction_performed": False,
        "structural_mapping_performed": False,
        "model_training_performed": False,
        "authorizations": {
            "benchmark_estimand_policy_proposal": True,
            "label_construction": False,
            "split_construction": False,
            "structural_mapping": False,
            "model_training": False,
        },
        "systematic_universe_assessment": {
            "complete_attempted_evaluable_universe_reconstructed": False,
            "required_field_count": len(requirements),
            "complete_pair_level_field_count": 0,
            "incomplete_fields": dict(requirements),
        },
        "scientific_conclusion": {
            **config["decision_policy"],
            "explicit_panel_nondetections_are_universal_negatives": False,
            "unreported_space_iii_pairs_are_negatives": False,
            "table_15_never_detected_pairs_are_negatives": False,
            "intact_negative_records_define_primary_systematic_universe": False,
        },
        "warnings": [
            {"code": "HURI_ATTEMPTED_UNIVERSE_UNRESOLVED"},
            {"code": "STRICT_CONSTRUCT_COVERAGE_ZERO"},
            {"code": "AUTHOR_CODE_REPOSITORY_LICENSE_UNRESOLVED"},
        ],
        "external_public_availability_review": config["external_availability_review"],
    }


def _guardrail_failures(audit: dict, config: dict) -> list[dict]:
    checks = Checks()
    _validate_audit_guardrails(checks, audit, config)
    return [record for record in checks.records if record["status"] == "fail"]


def test_valid_audit_guardrails_pass() -> None:
    config = _config()
    assert _guardrail_failures(_audit(config), config) == []


@pytest.mark.parametrize(
    "field",
    [
        "label_construction",
        "split_construction",
        "structural_mapping",
        "model_training",
    ],
)
def test_validator_rejects_prohibited_authorization(field: str) -> None:
    config = _config()
    audit = _audit(config)
    audit["authorizations"][field] = True
    assert _guardrail_failures(audit, config)


def test_validator_rejects_unreported_pairs_promoted_to_negatives() -> None:
    config = _config()
    audit = _audit(config)
    audit["scientific_conclusion"]["unreported_space_iii_pairs_are_negatives"] = True
    assert _guardrail_failures(audit, config)


def test_validator_rejects_complete_universe_claim() -> None:
    config = _config()
    audit = _audit(config)
    audit["systematic_universe_assessment"][
        "complete_attempted_evaluable_universe_reconstructed"
    ] = True
    assert _guardrail_failures(audit, config)


def test_validator_requires_all_blocker_warnings() -> None:
    config = _config()
    audit = _audit(config)
    audit["warnings"].pop()
    assert _guardrail_failures(audit, config)


def test_report_scope_rules(tmp_path: Path) -> None:
    smoke_root = tmp_path / "_smoke_audit"
    production_root = tmp_path / "systematic_screen_metadata_v1"
    assert (
        _scope_for_reports(
            smoke_root / "AUDIT_REPORT.json",
            smoke_root / "VALIDATION_REPORT.json",
            allow_smoke=True,
        )
        == "qualification_smoke"
    )
    assert (
        _scope_for_reports(
            production_root / "AUDIT_REPORT.json",
            production_root / "VALIDATION_REPORT.json",
            allow_smoke=False,
        )
        == "production_full"
    )
    with pytest.raises(RuntimeError, match="requires --allow-smoke"):
        _scope_for_reports(
            smoke_root / "AUDIT_REPORT.json",
            smoke_root / "VALIDATION_REPORT.json",
            allow_smoke=False,
        )
    with pytest.raises(RuntimeError, match="restricted to _smoke_"):
        _scope_for_reports(
            production_root / "AUDIT_REPORT.json",
            production_root / "VALIDATION_REPORT.json",
            allow_smoke=True,
        )


def test_report_scope_must_share_run_directory(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="share one run directory"):
        _scope_for_reports(
            tmp_path / "_smoke_one" / "AUDIT_REPORT.json",
            tmp_path / "_smoke_two" / "VALIDATION_REPORT.json",
            allow_smoke=True,
        )
