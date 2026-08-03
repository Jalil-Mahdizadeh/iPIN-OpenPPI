"""Fail-closed consistency gate for the proposed benchmark/estimand policy."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import stat
from typing import Any, Mapping

import yaml

from ipin_openppi.ingestion.common import (
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.validation.staging import Checks, _write_report


_REQUIRED_FALSE_AUTHORITIES = (
    "candidate_universe_construction",
    "evidence_indicator_construction",
    "label_construction",
    "split_construction",
    "structural_mapping",
    "model_implementation",
    "model_training",
)
_PRIMARY_METRICS = {
    "positive_unlabeled_pairwise_concordance",
    "held_out_positive_recall_at_10",
    "held_out_positive_recall_at_100",
    "held_out_positive_recall_at_1000",
    "released_positive_enrichment_at_fixed_candidate_fraction",
    "positive_rank_percentile",
}
_DEFERRED_CALIBRATION_METRICS = {
    "assay_endpoint_AUPRC_at_natural_prevalence",
    "Brier_skill",
    "calibration_slope",
    "calibration_intercept",
    "adaptive_calibration_error",
    "recall_at_fixed_biological_precision",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _resolve_inside(
    project_root: Path,
    value: str | Path,
    boundary: Path,
    *,
    strict: bool = True,
) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve(strict=strict)
    try:
        resolved.relative_to(boundary.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(
            f"Path escapes required boundary {boundary}: {resolved}"
        ) from exc
    return resolved


def _nested(document: Mapping[str, Any], dotted_path: str) -> Any:
    value: Any = document
    for component in dotted_path.split("."):
        if not isinstance(value, Mapping) or component not in value:
            return "__missing__"
        value = value[component]
    return value


def _validate_policy_semantics(checks: Checks, policy: Mapping[str, Any]) -> None:
    expected_top = {
        "schema_version": 1,
        "policy_id": "benchmark_estimand_policy_proposal_v1",
        "version": "0.1.0",
        "status": "proposed_for_expert_group_review",
        "effective": False,
        "supersedes": None,
    }
    for key, expected in expected_top.items():
        observed = policy.get(key)
        checks.require(
            f"policy.{key}",
            observed == expected,
            observed=observed,
            expected=expected,
        )

    authority = policy.get("authority", {})
    checks.require(
        "authority.design_and_validation_only",
        authority.get("policy_design") is True
        and authority.get("proposal_validation") is True,
        observed=authority,
        expected={"policy_design": True, "proposal_validation": True},
    )
    observed_false = {key: authority.get(key) for key in _REQUIRED_FALSE_AUTHORITIES}
    checks.require(
        "authority.construction_and_training_prohibited",
        all(value is False for value in observed_false.values()),
        observed=observed_false,
        expected={key: False for key in _REQUIRED_FALSE_AUTHORITIES},
    )
    checks.require(
        "authority.activation_requires_expert_acceptance",
        authority.get("activation_condition")
        == "expert_group_acceptance_of_blueprint_amendment_and_new_gate_record",
        observed=authority.get("activation_condition"),
        expected=("expert_group_acceptance_of_blueprint_amendment_and_new_gate_record"),
    )

    conclusion = _nested(policy, "evidence_basis.conclusion")
    expected_conclusion = {
        "complete_selected_attempted_evaluable_huri_universe_reconstructed": False,
        "original_calibrated_assay_probability_primary_endpoint_feasible": False,
        "binary_negative_benchmark_feasible": False,
        "reference_sequence_pu_ranking_design_feasible": True,
        "conditional_control_diagnostics_feasible": True,
        "strict_construct_benchmark_feasible": False,
        "structure_derived_benchmark_feasible": False,
    }
    checks.require(
        "evidence.conclusion",
        conclusion == expected_conclusion,
        observed=conclusion,
        expected=expected_conclusion,
    )
    observations = _nested(policy, "evidence_basis.critical_observations")
    checks.require(
        "evidence.frozen_counts",
        observations.get("huri_evidence_rows") == 220934
        and observations.get("huri_positive_evidence_rows") == 220934
        and observations.get("huri_negative_evidence_rows") == 0
        and observations.get("space_iii_genes") == 17408
        and observations.get("space_iii_gene_pair_upper_universe_excluding_self")
        == 17408 * 17407 // 2
        and observations.get("strict_construct_a_or_b_rows") == 0,
        observed=observations,
        expected={
            "huri_evidence_rows": 220934,
            "huri_positive_evidence_rows": 220934,
            "huri_negative_evidence_rows": 0,
            "space_iii_genes": 17408,
            "space_iii_gene_pair_upper_universe_excluding_self": 151510528,
            "strict_construct_a_or_b_rows": 0,
        },
    )

    scope = policy.get("scientific_scope", {})
    checks.require(
        "scope.reference_sequence_heteromeric_candidate_universe",
        scope.get("primary_pair_type") == "heteromeric"
        and scope.get("biological_unit") == "unordered_reference_sequence_pair"
        and scope.get("candidate_universe_semantics")
        == "candidate_and_unlabeled_not_attempted_not_evaluable_not_negative"
        and scope.get("laboratory_validation_available") is False,
        observed=scope,
        expected={
            "primary_pair_type": "heteromeric",
            "biological_unit": "unordered_reference_sequence_pair",
            "candidate_universe_semantics": (
                "candidate_and_unlabeled_not_attempted_not_evaluable_not_negative"
            ),
            "laboratory_validation_available": False,
        },
    )

    variables = policy.get("variables", {})
    checks.require(
        "variables.unlabeled_and_selection_semantics",
        _nested(variables, "R_AB.prohibited_interpretation") == "unlabeled_is_negative"
        and _nested(variables, "Y_AB.observed") is False
        and _nested(variables, "Y_AB.identifiability")
        == "not_identified_from_current_public_release"
        and _nested(
            variables,
            "selection_propensity.scar_or_constant_propensity_assumption_authorized",
        )
        is False,
        observed=variables,
        expected="unlabeled_not_negative_and_no_SCAR_or_probability_identification",
    )

    primary = _nested(policy, "estimands.primary")
    checks.require(
        "estimand.primary_is_ranking_not_probability",
        primary.get("id") == "frozen_released_positive_recovery_ranking"
        and primary.get("model_output")
        == "symmetric_sequence_compatibility_prioritization_score"
        and primary.get("probability_interpretation") == "prohibited"
        and primary.get("biological_binding_probability_interpretation") == "prohibited"
        and primary.get("assay_probability_interpretation") == "prohibited"
        and primary.get("selection_causal_interpretation") == "prohibited",
        observed=primary,
        expected="released_positive_recovery_ranking_with_no_probability_claim",
    )
    checks.require(
        "estimand.future_probability_tiers_inactive",
        _nested(policy, "estimands.future_tested_universe.active") is False
        and _nested(policy, "estimands.latent_compatibility_probability.active")
        is False,
        observed={
            "future_tested_universe": _nested(
                policy, "estimands.future_tested_universe.active"
            ),
            "latent_compatibility_probability": _nested(
                policy, "estimands.latent_compatibility_probability.active"
            ),
        },
        expected=False,
    )

    evidence_states = policy.get("evidence_state_policy", {})
    negative_roles = {
        key: value.get("negative_role")
        for key, value in evidence_states.items()
        if isinstance(value, Mapping) and "negative_role" in value
    }
    checks.require(
        "evidence_states.no_absent_or_technical_negative",
        negative_roles
        and all(value == "prohibited" for value in negative_roles.values())
        and _nested(
            evidence_states,
            "source_explicit_negative.universal_negative_role",
        )
        == "prohibited"
        and _nested(
            evidence_states,
            "random_reference_control.population_negative_role",
        )
        == "prohibited",
        observed={
            "negative_roles": negative_roles,
            "source_explicit_universal": _nested(
                evidence_states,
                "source_explicit_negative.universal_negative_role",
            ),
            "random_control_population": _nested(
                evidence_states,
                "random_reference_control.population_negative_role",
            ),
        },
        expected="all_prohibited",
    )

    tiers = policy.get("benchmark_tiers", {})
    checks.require(
        "tiers.only_reference_PU_and_controls_feasible",
        _nested(tiers, "PU_R.role") == "proposed_primary"
        and _nested(tiers, "PU_R.feasible_now") is True
        and _nested(tiers, "PU_R.calibration_claims") is False
        and _nested(tiers, "CP_D.feasible_now") is True
        and _nested(tiers, "CP_D.universal_negative_role") == "prohibited"
        and _nested(tiers, "TU_C.feasible_now") is False
        and _nested(tiers, "SC_S.feasible_now") is False,
        observed=tiers,
        expected="PU_R_and_CP_D_only_with_no_calibration_or_universal_negatives",
    )

    sampling = policy.get("positive_and_unlabeled_sampling", {})
    checks.require(
        "sampling.not_started_and_not_negative",
        sampling.get("construction_status") == "not_started"
        and _nested(sampling, "pseudo_negative_semantics.scientific_negative_label")
        is False
        and _nested(sampling, "class_prior.identified") is False
        and _nested(sampling, "class_prior.point_estimate_claim_authorized") is False
        and _nested(sampling, "sampler.method")
        == "deterministic_uniform_hash_sampling_without_replacement_within_split_and_stratum"
        and _nested(sampling, "sampler.record_inclusion_probability") is True
        and _nested(sampling, "sampler.record_sampling_weight") is True,
        observed=sampling,
        expected="not_started_deterministic_weighted_PU_sampling",
    )

    split = policy.get("sequence_and_split_design", {})
    checks.require(
        "splits.not_started_and_cluster_first",
        split.get("construction_status") == "not_started"
        and _nested(split, "sequence_identity_graph.component_rule")
        == "deterministic_connected_components"
        and _nested(split, "sequence_identity_graph.thresholds.primary") == 0.30
        and _nested(split, "sequence_identity_graph.thresholds.sensitivity")
        == [0.40, 0.20]
        and _nested(split, "partitioning.split_unit") == "entire_sequence_component"
        and _nested(split, "partitioning.model_output_or_performance_inputs_allowed")
        is False
        and _nested(split, "novelty_categories.C2_exclusive") is True,
        observed=split,
        expected="not_started_30_percent_component_first_exclusive_C2",
    )

    metrics = policy.get("metrics", {})
    checks.require(
        "metrics.primary_are_ranking_and_retrieval",
        set(metrics.get("primary", [])) == _PRIMARY_METRICS,
        observed=metrics.get("primary"),
        expected=sorted(_PRIMARY_METRICS),
    )
    checks.require(
        "metrics.calibration_deferred_and_claims_prohibited",
        set(metrics.get("deferred_until_TU_C", [])) == _DEFERRED_CALIBRATION_METRICS
        and {
            "biological_precision",
            "calibrated_binding_probability",
            "calibrated_assay_probability",
            "proteome_wide_precision",
        }.issubset(set(metrics.get("prohibited_headline_interpretations", []))),
        observed={
            "deferred": metrics.get("deferred_until_TU_C"),
            "prohibited": metrics.get("prohibited_headline_interpretations"),
        },
        expected={
            "deferred": sorted(_DEFERRED_CALIBRATION_METRICS),
            "prohibited_contains": [
                "biological_precision",
                "calibrated_binding_probability",
                "calibrated_assay_probability",
                "proteome_wide_precision",
            ],
        },
    )

    checks.require(
        "uncertainty.clustered_and_seeded",
        _nested(policy, "uncertainty.dependence_unit_primary") == "sequence_component"
        and _nested(policy, "uncertainty.clustered_bootstrap_replicates") == 2000
        and _nested(policy, "uncertainty.clustered_bootstrap_seed") == 20260803
        and _nested(policy, "uncertainty.independent_trials_claim_authorized") is False,
        observed=policy.get("uncertainty"),
        expected="2000_component_clustered_replicates_seed_20260803",
    )
    checks.require(
        "minimum_sizes.preserve_blueprint_thresholds",
        _nested(
            policy, "minimum_size_rules.headline_axis.held_out_released_positive_pairs"
        )
        == 500
        and _nested(
            policy,
            "minimum_size_rules.headline_axis.independent_sequence_components",
        )
        == 50
        and _nested(policy, "minimum_size_rules.below_threshold_action")
        == "demote_to_descriptive_and_do_not_pool_axes_to_hide_failure",
        observed=policy.get("minimum_size_rules"),
        expected={"positive_pairs": 500, "components": 50},
    )

    checks.require(
        "future_gates.not_weakened",
        _nested(policy, "future_tested_universe_gate.minimum_auditable_coverage")
        == 0.90
        and _nested(policy, "future_tested_universe_gate.negative_labels_before_gate")
        == "prohibited"
        and _nested(
            policy,
            "future_tested_universe_gate.calibrated_assay_endpoint_before_gate",
        )
        == "prohibited"
        and _nested(
            policy,
            "future_strict_construct_and_structure_gate.minimum_construct_confidence_A_or_B_fraction",
        )
        == 0.80
        and _nested(
            policy,
            "future_strict_construct_and_structure_gate.unresolved_structure_derived_labels",
        )
        == 0
        and _nested(
            policy,
            "future_strict_construct_and_structure_gate.strict_construct_or_structural_labels_before_gate",
        )
        == "prohibited",
        observed={
            "tested": policy.get("future_tested_universe_gate"),
            "strict": policy.get("future_strict_construct_and_structure_gate"),
        },
        expected={"tested_coverage": 0.90, "construct_fraction": 0.80},
    )

    claims = policy.get("claim_ceiling", {})
    checks.require(
        "claims.computational_only",
        {
            "experimentally_validated_novel_interactions",
            "universal_context_free_binding_probability",
            "calibrated_assay_probability_without_TU_C_gate",
            "undocumented_pair_is_negative",
            "complete_or_validated_human_interactome",
        }.issubset(set(claims.get("prohibited", [])))
        and "computationally prioritized hypotheses"
        in str(claims.get("required_hypothesis_warning", "")),
        observed=claims,
        expected="computational_hypotheses_only_with_probability_and_negative_claims_prohibited",
    )

    first_action = policy.get("post_approval_first_action", {})
    checks.require(
        "next_action.label_free_and_returns_to_gate",
        first_action.get("id")
        == "benchmark_eligibility_and_sequence_component_audit_v1"
        and "before any evidence indicator, pseudo-negative sample, split, or model"
        in str(first_action.get("description", ""))
        and first_action.get("construction_sequence", [])[-1]
        == "return_for_gate_confirmation_before_evidence_indicators_or_splits",
        observed=first_action,
        expected="eligibility_and_components_only_then_gate",
    )


def _validate_evidence_and_governance(
    *,
    checks: Checks,
    project_root: Path,
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    basis = policy["evidence_basis"]
    evidence_records: dict[str, Any] = {}
    for name, path_key, sha_key in (
        ("audit", "audit_report", "audit_report_sha256"),
        (
            "audit_validation",
            "audit_validation_report",
            "audit_validation_report_sha256",
        ),
    ):
        path = _resolve_inside(
            project_root,
            str(basis[path_key]),
            project_root / "artifacts/validation",
        )
        info = path.stat(follow_symlinks=False)
        digest = sha256_file(path)
        checks.require(
            f"evidence.{name}.immutable_hash",
            not path.is_symlink()
            and stat.S_ISREG(info.st_mode)
            and not bool(info.st_mode & 0o222)
            and digest == str(basis[sha_key]),
            observed={
                "path": path.as_posix(),
                "sha256": digest,
                "read_only": not bool(info.st_mode & 0o222),
            },
            expected={
                "sha256": str(basis[sha_key]),
                "read_only": True,
            },
        )
        evidence_records[name] = {
            "path": path.as_posix(),
            "sha256": digest,
            "document": _load_json(path),
        }

    audit = evidence_records["audit"]["document"]
    validation = evidence_records["audit_validation"]["document"]
    checks.require(
        "evidence.audit_semantics_and_authorizations",
        audit.get("status") == "complete"
        and audit.get("git", {}).get("commit")
        == str(basis["audit_implementation_commit"])
        and audit.get("git", {}).get("tracked_worktree_clean") is True
        and audit.get("scientific_conclusion", {}).get(
            "complete_attempted_evaluable_universe_reconstructed"
        )
        is False
        and audit.get("scientific_conclusion", {}).get(
            "primary_binary_negative_labels_feasible"
        )
        is False
        and audit.get("authorizations", {}).get("label_construction") is False
        and audit.get("authorizations", {}).get("split_construction") is False
        and audit.get("authorizations", {}).get("structural_mapping") is False
        and audit.get("authorizations", {}).get("model_training") is False,
        observed={
            "status": audit.get("status"),
            "git": audit.get("git"),
            "scientific_conclusion": audit.get("scientific_conclusion"),
            "authorizations": audit.get("authorizations"),
        },
        expected="complete_clean_audit_with_incomplete_universe_and_no_construction_authority",
    )
    checks.require(
        "evidence.independent_validation_pass",
        validation.get("status") == "pass"
        and validation.get("check_counts") == {"pass": 71, "warning": 3, "fail": 0}
        and validation.get("authorizations", {}).get(
            "benchmark_estimand_policy_proposal"
        )
        is True
        and validation.get("authorizations", {}).get("label_construction") is False
        and validation.get("authorizations", {}).get("split_construction") is False
        and validation.get("authorizations", {}).get("structural_mapping") is False
        and validation.get("authorizations", {}).get("model_training") is False,
        observed={
            "status": validation.get("status"),
            "check_counts": validation.get("check_counts"),
            "authorizations": validation.get("authorizations"),
        },
        expected={
            "status": "pass",
            "check_counts": {"pass": 71, "warning": 3, "fail": 0},
            "construction_authorized": False,
        },
    )

    references = {
        "parent_blueprint": "docs/blueprints/iPIN_OpenPPI_Final_Computational_Blueprint_and_Workflow_v3.md",
        "blueprint_amendment": str(policy["blueprint_amendment"]),
        "human_report": "docs/reports/m0/M0_Systematic_Screen_Metadata_Audit_and_Benchmark_Estimand_Proposal_v1.md",
        "decision": str(policy["decision_record"]),
        "review_gate": str(policy["outputs"]["review_gate"]),
        "issue_0003": "governance/issues/ISSUE-0003-huri-attempted-pair-universe.md",
        "issue_0005": "governance/issues/ISSUE-0005-sifts-uniprot-release-alignment.md",
    }
    reference_records: dict[str, Any] = {}
    for name, value in references.items():
        path = _resolve_inside(project_root, value, project_root)
        info = path.stat(follow_symlinks=False)
        checks.require(
            f"governance.reference.{name}",
            not path.is_symlink() and stat.S_ISREG(info.st_mode),
            observed=path.as_posix(),
            expected="regular_nonlink_file",
        )
        reference_records[name] = {
            "path": path.as_posix(),
            "sha256": sha256_file(path),
        }

    amendment_text = Path(reference_records["blueprint_amendment"]["path"]).read_text(
        encoding="utf-8"
    )
    report_text = Path(reference_records["human_report"]["path"]).read_text(
        encoding="utf-8"
    )
    decision_text = Path(reference_records["decision"]["path"]).read_text(
        encoding="utf-8"
    )
    checks.require(
        "governance.documents_state_proposal_not_approval",
        "Status:** Proposed for expert-group approval; not effective" in amendment_text
        and "The proposal is not yet effective." in report_text
        and "Status:** Proposed for expert-group approval; not accepted"
        in decision_text,
        observed={
            "amendment_proposed": "not effective" in amendment_text,
            "report_proposed": "not yet effective" in report_text,
            "decision_proposed": "not accepted" in decision_text,
        },
        expected=True,
    )
    checks.require(
        "governance.documents_preserve_core_claim_limits",
        "Unlabeled; never negative by absence" in amendment_text
        and "unlabeled, not negative" in report_text
        and "The score must not be called a probability." in amendment_text
        and "No split has been constructed." in report_text
        and "model training remain prohibited" in report_text,
        observed="reviewed_document_phrases",
        expected="unlabeled_not_negative_no_probability_no_split_no_training",
    )

    gate = _load_yaml(Path(reference_records["review_gate"]["path"]))
    checks.require(
        "governance.review_gate_v9",
        gate.get("schema_version") == 9
        and gate.get("supersedes") == "governance/gates/gate_status_v8.yaml"
        and _nested(gate, "gates.benchmark.status")
        == "policy_proposed_awaiting_expert_approval"
        and _nested(gate, "gates.benchmark.proposal_effective") is False
        and _nested(gate, "gates.benchmark.candidate_universe_construction_authorized")
        is False
        and _nested(gate, "gates.benchmark.evidence_indicator_construction_authorized")
        is False
        and _nested(gate, "gates.benchmark.label_construction_authorized") is False
        and _nested(gate, "gates.benchmark.split_construction_authorized") is False
        and _nested(gate, "gates.benchmark.structural_mapping_authorized") is False
        and _nested(gate, "gates.benchmark.model_implementation_authorized") is False
        and _nested(gate, "gates.benchmark.model_training_authorized") is False,
        observed=gate.get("gates", {}).get("benchmark"),
        expected="proposal_awaiting_approval_with_all_construction_false",
    )

    for issue_name in ("issue_0003", "issue_0005"):
        issue_text = Path(reference_records[issue_name]["path"]).read_text(
            encoding="utf-8"
        )
        checks.require(
            f"governance.{issue_name}_remains_open",
            "**Status:** Open;" in issue_text,
            observed=(
                issue_text.splitlines()[2] if len(issue_text.splitlines()) > 2 else ""
            ),
            expected="Status Open",
        )
    return {
        "evidence": {
            key: {"path": value["path"], "sha256": value["sha256"]}
            for key, value in evidence_records.items()
        },
        "references": reference_records,
    }


def validate_estimand_policy_proposal(
    *,
    project_root: Path,
    policy_path: Path,
    report_path: Path,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    policy_path = _resolve_inside(
        project_root,
        policy_path,
        project_root / "configs",
    )
    policy = _load_yaml(policy_path)
    report_path = _resolve_inside(
        project_root,
        report_path,
        project_root / "artifacts/validation",
        strict=False,
    )
    is_smoke = any(part.startswith("_smoke_") for part in report_path.parts)
    if allow_dirty != is_smoke:
        raise RuntimeError("--allow-dirty is restricted to an _smoke_* report path")
    configured_report = _resolve_inside(
        project_root,
        str(policy["outputs"]["validation_report"]),
        project_root / "artifacts/validation",
        strict=False,
    )
    if not allow_dirty and report_path != configured_report:
        raise RuntimeError("Production validation path differs from policy")

    expected_container = _resolve_inside(
        project_root,
        str(policy["execution"]["container"]),
        project_root / "containers/images",
    )
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    active_sha = sha256_file(active_container)
    expected_sha = str(policy["execution"]["container_sha256"])
    expected_arch = str(policy["execution"]["architecture"])
    if active_container != expected_container:
        raise RuntimeError("Active Apptainer image differs from policy")
    if active_sha != expected_sha:
        raise RuntimeError("Active Apptainer SHA-256 differs from policy")
    if platform.machine() != expected_arch:
        raise RuntimeError("Policy validation is running on the wrong architecture")

    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production policy validation requires a clean Git worktree")

    checks = Checks()
    _validate_policy_semantics(checks, policy)
    inventory = _validate_evidence_and_governance(
        checks=checks,
        project_root=project_root,
        policy=policy,
    )
    checks.warn(
        "blocker.expert_group_approval",
        observed="not_yet_approved",
        detail=(
            "Consistency validation can certify the proposal package, but only the "
            "expert group can activate the target amendment."
        ),
    )
    checks.warn(
        "blocker.ISSUE-0003",
        observed="open_until_expert_approved_estimand_narrowing",
        detail="The complete HuRI tested universe remains unavailable.",
    )
    checks.warn(
        "blocker.ISSUE-0005",
        observed="open_strict_construct_and_structural_tiers_inactive",
        detail="Strict construct A/B coverage is zero and release alignment is unresolved.",
    )

    result = {
        "schema_version": 1,
        "gate_id": "benchmark_estimand_policy_proposal_consistency_v1",
        "status": "pass" if checks.passed else "fail",
        "scope": "proposal_consistency_only_no_benchmark_construction",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": policy_path.as_posix(),
        "policy_sha256": sha256_file(policy_path),
        "runtime": {
            "container": expected_container.as_posix(),
            "container_sif_sha256": active_sha,
            "architecture": platform.machine(),
        },
        "git": git,
        "inventory": inventory,
        "check_counts": checks.counts(),
        "checks": checks.records,
        "interpretation": (
            "Pass means the proposal is internally consistent with the validated "
            "audit, open blockers, frozen thresholds, and construction prohibitions. "
            "It does not approve the amendment or authorize candidate, indicator, "
            "label, split, structure, model, or training construction."
        ),
        "authorizations": {
            "proposal_ready_for_expert_review": checks.passed,
            "amendment_effective": False,
            "candidate_universe_construction": False,
            "evidence_indicator_construction": False,
            "label_construction": False,
            "split_construction": False,
            "structural_mapping": False,
            "model_implementation": False,
            "model_training": False,
        },
    }
    return result


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the proposed benchmark/estimand policy package"
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("configs/benchmark_estimand_policy_proposal_v1.yaml"),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    policy_path = args.policy
    if not policy_path.is_absolute():
        policy_path = project_root / policy_path
    policy_path = policy_path.resolve(strict=True)
    policy = _load_yaml(policy_path)
    report_path = args.report or Path(policy["outputs"]["validation_report"])
    if not report_path.is_absolute():
        report_path = project_root / report_path

    report = validate_estimand_policy_proposal(
        project_root=project_root,
        policy_path=policy_path,
        report_path=report_path,
        allow_dirty=args.allow_dirty,
    )
    _write_report(report_path, report, project_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
