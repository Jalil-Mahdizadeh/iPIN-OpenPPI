"""Fail-closed configuration and output guards for component splitting."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ipin_openppi.sequence_component_audit.support import (
    artifact_inventory,
    load_json,
    load_yaml,
    make_read_only,
    replace_prefix,
    require_hash,
    require_scoped_outputs,
    resolve_inside,
    verify_manifest_table,
    write_json,
    write_manifest,
)


_OBJECTIVE = [
    "minimize_maximum_absolute_endpoint_fraction_deviation",
    "maximize_minimum_normalized_evidence_ratio_over_all_frozen_pair_component_and_source_floors",
    "minimize_maximum_development_test_relative_opportunity_imbalance_over_c2_c3_and_all_sources",
    "minimize_maximum_source_presence_fraction_deviation_from_global_released_positive_union",
    "minimize_maximum_positive_degree_mass_fraction_deviation_from_endpoint_targets",
    "minimize_maximum_global_hub_endpoint_fraction_deviation_from_endpoint_targets",
    "minimize_sum_absolute_endpoint_count_deviation_from_targets",
    "minimize_candidate_index",
]


def validate_config(config: Mapping[str, Any]) -> None:
    """Reject any configuration that broadens or mutates the frozen package."""

    if config.get("split_id") != "final_benchmark_component_split_v1":
        raise RuntimeError("Unexpected final component split_id")
    authorization = config["authorization"]
    if authorization.get("primary_design") != "reference_sequence_positive_unlabeled_ranking":
        raise RuntimeError("Primary PU-R design is not frozen")
    required_true = (
        "immutable_parent_artifact_use",
        "transient_released_positive_opportunity_analysis",
        "endpoint_partition_assignment",
        "component_partition_assignment",
        "split_skeleton_construction_and_freeze",
        "aggregate_c1_c2_c3_opportunity_summaries",
        "independent_assignment_and_count_validation",
        "return_to_governance_required",
    )
    required_false = (
        "candidate_pair_materialization",
        "candidate_sampling",
        "positive_pair_row_output",
        "evidence_indicator_construction",
        "interaction_label_construction",
        "negative_label_construction",
        "pseudo_negative_sampling",
        "pair_level_c1_c2_c3_assignment",
        "full_candidate_pair_universe_materialization",
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
    if any(authorization.get(name) is not True for name in required_true):
        raise RuntimeError("A required split-skeleton authorization is absent")
    if any(authorization.get(name) is not False for name in required_false):
        raise RuntimeError("A prohibited downstream authorization is not false")

    leakage = config["leakage_partition_policy"]
    if (
        int(leakage.get("identity_threshold_percent", 0)) != 30
        or leakage.get("primary_hard_rule", {}).get("id") != "local_domain_union"
        or leakage.get("fallback_hard_rule", {}).get("id") != "sensitive_fl80_union"
        or leakage.get("fallback_trigger")
        != "zero_primary_candidates_pass_every_frozen_acceptance_criterion"
        or leakage.get("evaluate_fallback_when_primary_valid") is not False
        or leakage.get("verify_selected_split_against")
        != ["local_domain_union", "sensitive_fl80_union"]
        or leakage.get("exhaustive_homology_claim_authorized") is not False
        or leakage.get("unseen_biological_family_claim_authorized") is not False
        or leakage.get("plm_unseen_protein_claim_authorized") is not False
    ):
        raise RuntimeError("Leakage or fallback policy differs from DEC-0021")

    allocation = config["allocation"]
    if (
        int(allocation.get("candidate_count_per_definition", 0)) != 4096
        or str(allocation.get("deterministic_seed")) != "20260803"
        or allocation.get("target_endpoint_fractions")
        != {"train": 0.70, "development": 0.15, "test": 0.15}
        or allocation.get("partition_iteration_and_tie_order")
        != ["train", "development", "test"]
        or allocation.get("frozen_selection_objective") != _OBJECTIVE
        or allocation.get("allocation_uses_model_results") is not False
        or allocation.get("future_model_results_inspected") is not False
        or int(allocation.get("score_quantization_scale", 0)) != 1_000_000_000
    ):
        raise RuntimeError("Allocation search or objective is not the frozen design")

    opportunity = config["opportunity_definitions"]
    pools = [
        (str(row["axis"]), str(row["evaluation_partition"]))
        for row in opportunity.get("evaluation_pools", [])
    ]
    if (
        opportunity.get("c2_exclusive") is not True
        or opportunity.get("pair_level_label_output_authorized") is not False
        or opportunity.get("interaction_supervised_training_endpoint_partitions")
        != ["train"]
        or pools
        != [
            ("C1", "training_pool"),
            ("C2", "development"),
            ("C2", "test"),
            ("C3", "development"),
            ("C3", "test"),
        ]
    ):
        raise RuntimeError("C1/C2/C3 opportunity semantics differ from DEC-0021")

    criteria = config["acceptance_criteria"]
    if (
        float(criteria.get("maximum_absolute_endpoint_fraction_deviation", -1)) != 0.03
        or int(criteria.get("minimum_released_positive_pairs_each_opportunity_pool", 0)) != 500
        or int(criteria.get("minimum_participating_components_each_opportunity_pool", 0)) != 50
        or int(criteria.get("minimum_released_positive_pairs_per_source_each_opportunity_pool", 0)) != 50
        or criteria.get("required_sources") != ["HI-II-14", "HuRI"]
        or float(criteria.get("maximum_absolute_source_presence_fraction_deviation", -1)) != 0.10
        or float(criteria.get("maximum_development_test_relative_opportunity_imbalance", -1)) != 0.35
        or float(criteria.get("maximum_absolute_positive_degree_mass_fraction_deviation", -1)) != 0.10
        or criteria.get("global_hub_fractions") != [0.01, 0.05, 0.10]
        or float(criteria.get("maximum_absolute_global_hub_endpoint_fraction_deviation", -1)) != 0.10
        or int(criteria.get("selected_hard_rule_cross_partition_edge_count", -1)) != 0
        or int(criteria.get("primary_selection_requires_sensitive_fl80_union_cross_partition_edge_count", -1)) != 0
        or criteria.get("all_criteria_are_hard_and_conjunctive") is not True
    ):
        raise RuntimeError("Acceptance criteria differ from the preregistration")

    claims = config["claim_policy"]
    prohibited = (
        "unseen_biological_family_claim",
        "family_generalization_claim",
        "exhaustive_nonhomology_claim",
        "plm_unseen_protein_claim",
        "universal_nonbinding_claim",
        "prevalence_claim",
        "calibrated_probability_claim",
    )
    if (
        claims.get("unseen_protein_term_requires_exact_operational_definition") is not True
        or any(claims.get(name) != "prohibited" for name in prohibited)
    ):
        raise RuntimeError("Claim ceiling is not fail-closed")


def require_output_paths(
    *,
    run_root: Path,
    canonical_root: Path,
    report_path: Path,
    allow_dirty: bool,
    skip_input_hashes: bool,
) -> bool:
    return require_scoped_outputs(
        paths=(run_root, canonical_root, report_path),
        allow_dirty=allow_dirty,
        skip_input_hashes=skip_input_hashes,
    )


__all__ = [
    "artifact_inventory",
    "load_json",
    "load_yaml",
    "make_read_only",
    "replace_prefix",
    "require_hash",
    "require_output_paths",
    "resolve_inside",
    "validate_config",
    "verify_manifest_table",
    "write_json",
    "write_manifest",
]
