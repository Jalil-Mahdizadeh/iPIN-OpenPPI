"""Fail-closed configuration and output guards for the pre-split audit."""

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


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("audit_id") != "pre_split_feasibility_and_leakage_stress_test_v1":
        raise RuntimeError("Unexpected pre-split audit_id")
    authorization = config["authorization"]
    required_true = (
        "immutable_parent_artifact_use",
        "aggregate_positive_network_analysis",
        "ephemeral_component_allocation_trials",
        "full_length_similarity_sensitivity_challenge",
        "local_domain_similarity_stress_test",
        "aggregate_output_only",
        "return_to_governance_required",
    )
    required_false = (
        "candidate_pair_materialization",
        "candidate_sampling",
        "evidence_indicator_construction",
        "interaction_label_construction",
        "negative_label_construction",
        "pseudo_negative_sampling",
        "c1_c2_c3_assignment",
        "split_construction",
        "structural_mapping",
        "model_implementation",
        "model_training",
        "model_selection",
        "model_evaluation",
        "prevalence_estimation",
        "calibration",
        "external_panel_input_use",
        "parent_audit_reopening_or_modification",
    )
    if authorization.get("primary_design") != "reference_sequence_positive_unlabeled_ranking":
        raise RuntimeError("Primary PU-R design is not frozen")
    if any(authorization.get(name) is not True for name in required_true):
        raise RuntimeError("A required bounded audit authorization is absent")
    if any(authorization.get(name) is not False for name in required_false):
        raise RuntimeError("A prohibited downstream authorization is not false")

    leakage = config["leakage_graphs"]
    if (
        leakage.get("identity_thresholds_percent") != [40, 30, 20]
        or leakage.get("primary_identity_threshold_percent") != 30
        or float(leakage["accepted_full_length_definition"]["minimum_endpoint_coverage"]) != 0.8
        or float(leakage["local_domain_union_definition"]["minimum_endpoint_coverage"]) != 0.2
        or int(leakage["local_domain_union_definition"]["minimum_aligned_endpoint_span"]) != 80
        or leakage.get("exhaustive_homology_claim_authorized") is not False
        or leakage.get("universal_family_definition_authorized") is not False
    ):
        raise RuntimeError("Leakage definitions differ from the governed scope")

    allocation = config["allocation_feasibility"]
    if (
        allocation.get("target_fractions")
        != {"train": 0.70, "development": 0.15, "test": 0.15}
        or int(allocation.get("trial_count", 0)) < 100
        or allocation.get("selected_trial_output_authorized") is not False
        or allocation.get("component_assignment_output_authorized") is not False
        or allocation.get("pair_assignment_output_authorized") is not False
    ):
        raise RuntimeError("Allocation feasibility policy is not aggregate-only")

    if config["positive_network"].get("pair_level_output_authorized") is not False:
        raise RuntimeError("Positive pair-level output is prohibited")
    if config["positive_network"].get("endpoint_level_output_authorized") is not False:
        raise RuntimeError("Endpoint-level output is prohibited")
    if config["positive_network"].get("component_level_output_authorized") is not False:
        raise RuntimeError("Component-level output is prohibited")


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
