from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from ipin_openppi.benchmark.estimand_policy_validation import (
    _validate_policy_semantics,
)
from ipin_openppi.validation.staging import Checks


_POLICY_PATH = Path("configs/benchmark_estimand_policy_proposal_v1.yaml")


def _policy() -> dict:
    value = yaml.safe_load(_POLICY_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _failures(policy: dict) -> list[dict]:
    checks = Checks()
    _validate_policy_semantics(checks, policy)
    return [record for record in checks.records if record["status"] == "fail"]


def test_frozen_proposal_semantics_pass() -> None:
    assert _failures(_policy()) == []


def test_effective_policy_is_rejected_before_expert_approval() -> None:
    policy = _policy()
    policy["effective"] = True
    assert _failures(policy)


def test_accepted_status_is_rejected_before_expert_approval() -> None:
    policy = _policy()
    policy["status"] = "accepted"
    assert _failures(policy)


def test_label_authority_is_rejected() -> None:
    policy = _policy()
    policy["authority"]["label_construction"] = True
    assert _failures(policy)


def test_split_authority_is_rejected() -> None:
    policy = _policy()
    policy["authority"]["split_construction"] = True
    assert _failures(policy)


def test_unreported_pair_cannot_become_negative() -> None:
    policy = _policy()
    policy["evidence_state_policy"]["unreported_space_iii_pair"][
        "negative_role"
    ] = "allowed"
    assert _failures(policy)


def test_probability_interpretation_is_rejected() -> None:
    policy = _policy()
    policy["estimands"]["primary"]["probability_interpretation"] = "allowed"
    assert _failures(policy)


def test_calibration_metric_cannot_become_primary() -> None:
    policy = _policy()
    policy["metrics"]["primary"].append("Brier_skill")
    assert _failures(policy)


def test_split_construction_must_remain_not_started() -> None:
    policy = _policy()
    policy["sequence_and_split_design"]["construction_status"] = "complete"
    assert _failures(policy)


def test_tested_universe_threshold_cannot_be_weakened() -> None:
    policy = _policy()
    policy["future_tested_universe_gate"]["minimum_auditable_coverage"] = 0.50
    assert _failures(policy)


def test_construct_threshold_cannot_be_weakened() -> None:
    policy = _policy()
    policy["future_strict_construct_and_structure_gate"][
        "minimum_construct_confidence_A_or_B_fraction"
    ] = 0.20
    assert _failures(policy)


def test_scientific_count_change_is_detected() -> None:
    policy = deepcopy(_policy())
    policy["evidence_basis"]["critical_observations"]["huri_negative_evidence_rows"] = 1
    assert _failures(policy)
