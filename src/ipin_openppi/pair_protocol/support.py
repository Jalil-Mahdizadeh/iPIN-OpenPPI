"""Fail-closed guards for the pair-level PU-R protocol freeze."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ipin_openppi.sequence_component_audit.support import (
    load_json,
    load_yaml,
    require_hash,
    resolve_inside,
    verify_manifest_table,
)

from .semantics import DEGREE_BINS, PRIMARY_CELLS


def validate_config(config: Mapping[str, Any]) -> None:
    if (
        config.get("protocol_id") != "pair_level_pu_r_benchmark_protocol_v1"
        or int(config.get("configuration_revision", 0)) != 2
        or config.get("task")
        != "model_free_pair_level_positive_unlabeled_ranking_protocol_freeze"
        or config.get("status") != "authorized_not_executed"
    ):
        raise RuntimeError("Unexpected pair-level protocol identity or status")

    authorization = config["authorization"]
    required_true = (
        "immutable_parent_artifact_use",
        "protocol_definition_and_freeze",
        "transient_released_positive_pair_reconstruction",
        "aggregate_pair_rule_feasibility_analysis",
        "aggregate_candidate_count_algebra",
        "evidence_field_completeness_analysis",
        "independent_rule_and_count_validation",
        "return_to_governance_required",
    )
    required_false = (
        "persisted_positive_pair_rows",
        "persisted_unlabeled_pair_rows",
        "pair_level_c1_c2_c3_output",
        "candidate_pair_materialization",
        "full_candidate_pair_universe_materialization",
        "unlabeled_sample_realization",
        "evidence_indicator_construction",
        "interaction_label_construction",
        "negative_label_construction",
        "pseudo_negative_sampling",
        "frozen_endpoint_component_split_modification",
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
    if authorization.get("primary_design") != "reference_sequence_positive_unlabeled_ranking":
        raise RuntimeError("The accepted PU-R primary design is not preserved")
    if any(authorization.get(key) is not True for key in required_true):
        raise RuntimeError("A required protocol-freeze authorization is absent")
    if any(authorization.get(key) is not False for key in required_false):
        raise RuntimeError("A prohibited protocol action is not false")

    cutoff = config["information_cutoffs"]
    if (
        cutoff["evidence"].get("source_release") != "published_2020"
        or cutoff["evidence"].get("qualifying_sources") != ["HI-II-14", "HuRI"]
        or cutoff["sequence"].get("frozen_uniprot_release") != "2026_02"
        or cutoff["partition"].get("hard_rule") != "local_domain_union_30"
        or cutoff["partition"].get("split_modification") != "prohibited"
        or cutoff["external_features"].get("plm_unseen_claim_authorized") is not False
    ):
        raise RuntimeError("Information cutoffs or frozen parent rule changed")

    visibility = config["evidence_visibility"]
    if (
        visibility["training"].get("withheld_c1_pair_identity_visible") is not False
        or visibility["training"].get(
            "development_or_test_endpoint_visible_to_interaction_supervision"
        )
        is not False
        or visibility["development"].get("protected_test_positive_identity_visible")
        is not False
        or visibility["protected_test"].get("one_first_evaluation_rule") is not True
    ):
        raise RuntimeError("Training/development/test evidence visibility is unsafe")

    assignment = config["pair_assignment"]
    role = assignment["c1_positive_role"]
    if (
        assignment.get("public_salt")
        != "ipin-openppi-pair-level-pu-r-protocol-v1"
        or str(assignment.get("deterministic_seed")) != "20260803"
        or role.get("bucket_intervals")
        != {"train": [0, 7000], "development": [7000, 8500], "test": [8500, 10000]}
        or role.get("assignment_is_label_blind") is not True
        or role.get("role_hash_uses_source_study_assay_degree_or_model_result") is not False
        or assignment["C2"].get("exclusive_of_C3") is not True
        or assignment["C3"].get("component_disjoint_under") != "local_domain_union_30"
        or assignment.get("reassignment_after_quarantine") != "prohibited"
    ):
        raise RuntimeError("C1/C2/C3 assignment semantics changed")
    if config["pair_assignment"]["quarantine"] != [
        "development_test_cross_partition_pair",
        "train_train_positive_with_development_or_test_hash_role_failing_training_exposure_guard",
        "train_heldout_positive_whose_train_endpoint_is_not_training_exposed",
        "self_pair_or_same_frozen_sequence_hash",
        "ambiguous_or_unmapped_positive_projection",
        "any_pair_failing_source_or_cutoff_eligibility",
    ]:
        raise RuntimeError("Positive quarantine rules changed")

    grouping = config["pair_identity_and_grouping"]
    if (
        grouping.get("biological_pair_unit")
        != "unordered_exact_frozen_reference_sequence_pair"
        or grouping.get("pair_identity_persistence_in_this_work_package") is not False
        or len(grouping.get("group_co_location", [])) != 5
    ):
        raise RuntimeError("Pair identity or evidence-group co-location changed")

    sampling = config["unlabeled_sampling"]
    if (
        sampling.get("realization_status") != "prohibited_in_this_work_package"
        or sampling.get("method")
        != "deterministic_stratified_bottom_hash_without_replacement"
        or sampling.get("public_salt") != "ipin-openppi-benchmark-v1"
        or str(sampling.get("deterministic_seed")) != "20260803"
        or sampling.get("degree_bins") != list(DEGREE_BINS)
        or sampling.get("positive_inclusion_probability") != 1.0
        or sampling.get("positive_sampling_weight") != 1.0
        or sampling.get("scientific_negative_interpretation") != "prohibited"
    ):
        raise RuntimeError("Unlabeled sampling semantics changed")
    expected_caps = {
        "training": 2_000_000,
        "C1_development": 1_000_000,
        "C1_test": 1_000_000,
        "C2_development": 1_000_000,
        "C2_test": 1_000_000,
        "C3_development": 1_000_000,
        "C3_test": 1_000_000,
    }
    if sampling.get("sample_caps") != expected_caps:
        raise RuntimeError("Unlabeled sample caps changed")

    metrics = config["metrics"]
    if (
        metrics["primary"]["heldout_positive_recall_at_k"].get("k")
        != [10, 100, 1000]
        or metrics["primary"]["released_positive_enrichment_at_candidate_fraction"].get(
            "fractions"
        )
        != [0.0001, 0.001, 0.01]
        or "biological_precision" not in metrics.get("prohibited", [])
        or "prevalence" not in metrics.get("prohibited", [])
    ):
        raise RuntimeError("Primary metrics or prohibited interpretations changed")

    uncertainty = config["uncertainty"]
    if (
        uncertainty.get("primary_dependence_unit")
        != "frozen_local_domain_union_30_sequence_component"
        or uncertainty.get("method") != "two_endpoint_component_pigeonhole_bootstrap"
        or int(uncertainty.get("replicates", 0)) != 2000
        or str(uncertainty.get("deterministic_seed")) != "20260803"
        or uncertainty.get("interval") != "percentile_95"
    ):
        raise RuntimeError("Clustered uncertainty plan changed")

    holdouts = config["auxiliary_holdouts"]
    if (
        holdouts["source_exclusive"].get("status")
        != "supported_with_cellwise_minimum_size_demotion"
        or holdouts["source_exclusive"].get("canonical_cell_id")
        != "source_exclusive:{target_source}:{primary_cell}"
        or holdouts["source_exclusive"].get("sampling_cap")
        != "inherit_underlying_primary_cell_cap"
        or holdouts["study"].get("status") != "inactive_not_independently_identified"
        or holdouts["assay_version_or_batch"].get("status") != "inactive_missing"
        or holdouts["temporal"].get("status")
        != "inactive_not_supported_as_independent_pair_time_holdout"
    ):
        raise RuntimeError("Unsupported metadata holdout was activated")

    baselines = config["later_simple_baselines"]
    random_baseline = baselines["baselines"]["deterministic_hash_random"]
    component_baseline = baselines["baselines"]["component_degree_mass_product"]
    if (
        baselines.get("implementation_status") != "not_authorized"
        or random_baseline.get("public_salt") != "ipin-openppi-pu-r-baseline-v1"
        or str(random_baseline.get("deterministic_seed")) != "20260803"
        or random_baseline.get("hash_payload")
        != "{public_salt}:{deterministic_seed}:baseline:{pair_id}"
        or component_baseline.get("component_degree_mass")
        != "sum_of_training_positive_degree_over_all_endpoints_in_frozen_component"
    ):
        raise RuntimeError("Future simple baseline definitions are incomplete or changed")

    criteria = config["acceptance_criteria"]
    if (
        criteria.get("primary_cells") != list(PRIMARY_CELLS)
        or int(criteria.get("minimum_released_positive_pairs_each_primary_cell", 0)) != 500
        or int(criteria.get("minimum_participating_components_each_primary_cell", 0)) != 50
        or int(criteria.get("minimum_source_presence_pairs_each_primary_cell", 0)) != 50
        or criteria.get("required_source_presence") != ["HI-II-14", "HuRI"]
        or criteria.get("all_primary_criteria_are_hard_and_conjunctive") is not True
    ):
        raise RuntimeError("Protocol acceptance criteria changed")

    claims = config["claim_policy"]
    prohibited_claims = (
        "unsupported_study_assay_or_temporal_claim",
        "unseen_biological_family_claim",
        "family_generalization_claim",
        "plm_unseen_protein_claim",
        "exhaustive_nonhomology_claim",
        "universal_nonbinding_claim",
        "unlabeled_is_negative_claim",
        "prevalence_claim",
        "calibrated_probability_claim",
        "biological_precision_claim",
    )
    if any(claims.get(key) != "prohibited" for key in prohibited_claims):
        raise RuntimeError("Pair-level protocol claim ceiling changed")


def resolve_and_verify_documents(
    *, project_root: Path, config: Mapping[str, Any], verify_hashes: bool
) -> tuple[dict[str, Path], dict[str, Any]]:
    inputs = config["inputs"]
    document_keys = (
        "accepted_estimand_policy",
        "incorporated_estimand_proposal",
        "systematic_screen_audit_report",
        "systematic_screen_validation_report",
        "acquisition_manifest",
        "parse_manifest",
        "evidence_schema",
        "reconciliation_manifest",
        "eligibility_manifest",
        "frozen_split_config",
        "frozen_split_manifest",
        "parent_acceptance_decision",
        "authorization_decision",
        "active_gate",
        "active_status",
    )
    paths: dict[str, Path] = {}
    records: dict[str, Any] = {}
    for key in document_keys:
        path = resolve_inside(project_root, str(inputs[key]), project_root, strict=True)
        paths[key] = path
        records[key] = (
            require_hash(path, str(inputs[f"{key}_sha256"]))
            if verify_hashes
            else {"path": path.as_posix(), "bytes": path.stat().st_size, "sha256": "smoke_skipped"}
        )
    return paths, records


__all__ = [
    "load_json",
    "load_yaml",
    "resolve_and_verify_documents",
    "resolve_inside",
    "validate_config",
    "verify_manifest_table",
]
