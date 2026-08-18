"""Fail-closed static audit for model-governance protocol v1.

This module deliberately contains no model, embedding, training, development,
or protected-package implementation.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

import yaml

from ipin_openppi.ingestion.common import (
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.sequence_component_audit.support import resolve_inside
from ipin_openppi.validation.staging import _write_report


PROTOCOL_ID = "model_governance_and_baseline_training_protocol_v1"
DATA_SIF_SHA256 = "72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629"
MODEL_REVISIONS = {
    "esm2_150m": (
        "a695f6045e2e32885fa60af20c13cb35398ce30c",
        "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566",
        595_257_706,
        30,
        640,
    ),
    "esm2_650m": (
        "08e4846e537177426273712802403f7ba8261b6c",
        "a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0",
        2_609_506_392,
        33,
        1280,
    ),
}
DEGREE_BINS = ["0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+"]
SEEDS = [20260803, 20260817, 20260831]


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected YAML mapping: {path}")
    return data


def _check(name: str, passed: bool, detail: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "check": name,
        "status": "pass" if passed else "fail",
        "detail": dict(detail),
    }


def _all_false(mapping: Mapping[str, Any], names: tuple[str, ...]) -> bool:
    return all(mapping.get(name) is False for name in names)


def _all_prohibited(values: Mapping[str, Any], names: tuple[str, ...]) -> bool:
    return all(values.get(name) == "prohibited" for name in names)


def protocol_checks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    authority = config.get("authority", {})
    frozen = config.get("frozen_benchmark", {})
    boundary = config.get("protected_boundary", {})
    provenance = config.get("plm_provenance", {})
    candidates = provenance.get("candidates", {})
    runtime = config.get("future_model_runtime", {})
    validation_runtime = config.get("validation_runtime", {})
    custody = config.get("model_file_custody", {})
    embedding = config.get("embedding_strategy", {})
    baselines = config.get("mandatory_baselines", {})
    architectures = config.get("model_architectures", {})
    objective = config.get("primary_training_objective", {})
    optimization = config.get("optimization_and_search", {})
    checkpoints = config.get("checkpointing_and_stopping", {})
    budget = config.get("compute_budget", {})
    release = config.get("development_release_and_model_selection", {})
    evaluation = config.get("evaluation_and_reporting", {})
    stratification = config.get("degree_and_hub_stratification", {})
    novel_u = config.get("c1_novel_U_sensitivity", {})
    complexity = config.get("complexity_justification", {})
    kills = config.get("model_level_kill_criteria", {})
    claims = config.get("claim_policy", {})
    outputs = config.get("outputs", {})

    checks: list[dict[str, Any]] = []
    checks.append(
        _check(
            "identity_and_design_only_authority",
            config.get("protocol_id") == PROTOCOL_ID
            and config.get("configuration_revision") == 1
            and config.get("task") == "model_governance_and_baseline_training_protocol_design_only"
            and config.get("status") == "authorized_not_executed"
            and authority.get("design_only") is True
            and authority.get("public_metadata_review") is True
            and authority.get("static_protocol_validation") is True
            and authority.get("return_to_governance_required") is True
            and _all_false(
                authority,
                (
                    "model_weight_or_tokenizer_download",
                    "model_cache_population",
                    "model_runtime_container_build",
                    "embedding_extraction",
                    "baseline_or_model_implementation",
                    "model_training_or_checkpointing",
                    "development_release_or_access",
                    "protected_candidate_or_truth_access",
                    "external_panel_integration",
                    "structural_residue_or_interface_work",
                ),
            ),
            {"status": config.get("status"), "design_only": authority.get("design_only")},
        )
    )
    checks.append(
        _check(
            "frozen_benchmark_identity_and_counts",
            frozen.get("primary_design") == "reference_sequence_positive_unlabeled_ranking"
            and frozen.get("eligible_reference_sequences") == 17_000
            and frozen.get("hard_partition_rule") == "local_domain_union_30"
            and frozen.get("hard_rule_components") == 7_782
            and frozen.get("endpoint_counts")
            == {"training": 11_900, "development": 2_550, "protected_test": 2_550}
            and frozen.get("public_training_positive_pairs") == 16_799
            and frozen.get("public_training_unlabeled_rows") == 2_000_000
            and frozen.get("pair_state_vocabulary") == ["released_positive", "unlabeled"]
            and frozen.get("unlabeled_is_negative") is False
            and frozen.get("negative_or_pseudo_negative_creation") == "prohibited"
            and frozen.get("parent_semantics_modification") == "prohibited",
            {
                "endpoints": frozen.get("eligible_reference_sequences"),
                "training_P": frozen.get("public_training_positive_pairs"),
                "training_U": frozen.get("public_training_unlabeled_rows"),
            },
        )
    )
    checks.append(
        _check(
            "development_and_protected_boundary_closed",
            boundary.get("development_package") == "encrypted_unreleased"
            and boundary.get("protected_candidates") == "encrypted_invisible_to_model_development"
            and boundary.get("protected_truth") == "encrypted_invisible_to_model_development"
            and boundary.get("private_key_access") == "prohibited"
            and boundary.get("package_decryption_in_this_work_package") == "prohibited"
            and boundary.get("candidate_identity_reconstruction_or_probing") == "prohibited"
            and boundary.get("public_pair_keyed_predictions") == "prohibited"
            and boundary.get("development_release_prerequisite")
            == "separately_numbered_decision_after_training_artifact_registry_sha256_freeze"
            and boundary.get("protected_test_use") == "evaluator_only_once_after_model_selection",
            {"development": boundary.get("development_package")},
        )
    )

    candidate_ok = set(candidates) == set(MODEL_REVISIONS)
    candidate_detail: dict[str, Any] = {}
    for candidate_id, expected in MODEL_REVISIONS.items():
        record = candidates.get(candidate_id, {})
        revision, digest, size, layer, hidden = expected
        passed = (
            record.get("repository_revision") == revision
            and record.get("checkpoint_file") == "model.safetensors"
            and record.get("checkpoint_sha256") == digest
            and record.get("checkpoint_bytes") == size
            and record.get("pickle_weights_permitted") is False
            and record.get("trust_remote_code") is False
            and record.get("license") == "MIT"
            and record.get("layers") == layer
            and record.get("hidden_size") == hidden
            and record.get("maximum_residues_per_window") == 1022
            and record.get("final_representation_layer") == layer
        )
        candidate_ok = candidate_ok and passed
        candidate_detail[candidate_id] = {
            "revision": record.get("repository_revision"),
            "sha256": record.get("checkpoint_sha256"),
        }
    checks.append(_check("exact_two_plm_candidates", candidate_ok, candidate_detail))

    limits = provenance.get("shared_claim_limits", {})
    checks.append(
        _check(
            "plm_provenance_and_exposure_claim_ceiling",
            provenance.get("candidate_count") == 2
            and provenance.get("documented_pretraining_objective") == "masked_language_modeling"
            and provenance.get("documented_uniref_release") == "2021_04"
            and provenance.get("exact_per_step_sequence_draw_log_available") is False
            and provenance.get("exact_endpoint_membership_audit_completed") is False
            and provenance.get("exposure_disposition")
            == "exact_or_homologous_exposure_of_any_benchmark_endpoint_is_unknown_and_possible"
            and _all_prohibited(
                limits,
                (
                    "exact_benchmark_endpoint_unseen",
                    "homolog_or_family_unseen",
                    "plm_unseen_protein",
                    "c3_implies_plm_unseen",
                    "temporal_cleanliness_from_plm_corpus",
                    "150m_vs_650m_difference_is_exposure_effect",
                    "pretraining_exposure_caused_observed_gain_or_loss",
                ),
            ),
            {"uniref_release": provenance.get("documented_uniref_release")},
        )
    )
    checks.append(
        _check(
            "future_runtime_recipe_frozen_but_not_built",
            runtime.get("status") == "recipe_frozen_image_not_built_or_authorized"
            and runtime.get("required_image_name") == "ipin-model-arm64_0.1.0.sif"
            and runtime.get("qualified_parent_image_sha256")
            == "9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5"
            and runtime.get("architecture") == "aarch64"
            and runtime.get("python") == "3.12.3"
            and runtime.get("pytorch") == "2.8.0a0+34c6371d24.nv25.08"
            and runtime.get("transformers") == "4.55.2"
            and runtime.get("huggingface_hub") == "0.34.4"
            and runtime.get("tokenizers") == "0.21.4"
            and runtime.get("safetensors") == "0.6.2"
            and len(runtime.get("future_image_requirements", [])) == 8
            and validation_runtime.get("container")
            == "containers/images/ipin-data-arm64_0.1.2.sif"
            and validation_runtime.get("container_sha256") == DATA_SIF_SHA256
            and validation_runtime.get("model_import_embedding_or_training") == "prohibited",
            {"model_image_status": runtime.get("status")},
        )
    )
    checks.append(
        _check(
            "future_model_file_custody_is_offline_and_hash_pinned",
            custody.get("acquisition_status") == "not_authorized_not_present_by_this_protocol"
            and custody.get("cache_must_resolve_inside_project") is True
            and custody.get("required_files", []).count("model.safetensors") == 1
            and custody.get("future_acquisition_rules", {}).get("symlinks_or_external_cache_links")
            == "prohibited"
            and custody.get("future_acquisition_rules", {}).get("safetensors_only") is True
            and custody.get("future_acquisition_rules", {}).get("per_file_bytes_and_sha256_manifest_required")
            is True
            and custody.get("future_acquisition_rules", {}).get("local_files_only_after_acquisition")
            is True
            and custody.get("future_acquisition_rules", {}).get("network_during_embedding_or_training")
            == "prohibited",
            {"acquisition_status": custody.get("acquisition_status")},
        )
    )
    window = embedding.get("windowing", {})
    normalization = embedding.get("normalization_for_trainable_heads", {})
    checks.append(
        _check(
            "pooled_embedding_strategy_is_frozen_complete_and_label_blind",
            embedding.get("status") == "frozen_not_executed"
            and embedding.get("endpoint_population") == "all_17000_frozen_reference_sequences_label_blind"
            and embedding.get("backbone_parameters_trainable") is False
            and embedding.get("model_mode") == "eval"
            and embedding.get("autograd") == "disabled"
            and embedding.get("representation") == "final_hidden_state_residue_mean"
            and embedding.get("special_tokens_in_pool") is False
            and embedding.get("input_sequence")
            == "exact_uppercase_frozen_reference_sequence_no_truncation_or_replacement"
            and embedding.get("forward_dtype") == "float32"
            and embedding.get("output_dtype") == "float32"
            and window.get("maximum_residues") == 1022
            and window.get("overlap_residues") == 128
            and window.get("stride_residues") == 894
            and normalization.get("population") == "11900_training_partition_endpoint_embeddings_only"
            and normalization.get("heldout_endpoint_statistics_used") is False
            and embedding.get("all_17000_embeddings_complete_unique_finite_before_training") is True
            and embedding.get("duplicate_extraction_check_fraction") == 0.01
            and embedding.get("duplicate_max_absolute_difference") == 0.000001,
            {"window": 1022, "overlap": 128, "stride": 894},
        )
    )

    zero = baselines.get("zero_parameter", {})
    checks.append(
        _check(
            "frozen_hash_graph_and_degree_baselines_preserved",
            zero.get("deterministic_hash_random", {}).get("public_salt")
            == "ipin-openppi-pu-r-baseline-v1"
            and zero.get("deterministic_hash_random", {}).get("deterministic_seed") == "20260803"
            and zero.get("endpoint_degree_sum", {}).get("score")
            == "log1p(d_train_a) + log1p(d_train_b)"
            and zero.get("preferential_attachment", {}).get("score")
            == "log1p(d_train_a * d_train_b)"
            and zero.get("component_degree_mass_product", {}).get("score")
            == "log1p(D_component_a * D_component_b)"
            and zero.get("training_graph_common_neighbors", {}).get("neighbor_graph")
            == "16799_training_positive_pairs_only"
            and baselines.get("common_feature_boundary", {}).get("heldout_endpoint_training_degree") == 0
            and baselines.get("common_feature_boundary", {}).get("heldout_or_full_graph_degree")
            == "prohibited",
            {"zero_parameter_count": len(zero)},
        )
    )
    checks.append(
        _check(
            "deterministic_length_sequence_and_interolog_controls",
            zero.get("sequence_length_sum", {}).get("score")
            == "log1p(length_a) + log1p(length_b)"
            and zero.get("sequence_length_ratio", {}).get("score")
            == "-abs(log1p(length_a) - log1p(length_b))"
            and zero.get("within_pair_3mer_cosine", {}).get("feature_alphabet")
            == "ACDEFGHIKLMNPQRSTVWYX"
            and zero.get("within_pair_3mer_cosine", {}).get("k") == 3
            and zero.get("training_interolog_3mer", {}).get("training_reference_pairs")
            == "16799_training_positive_pairs_only"
            and zero.get("training_interolog_3mer", {}).get("approximate_nearest_neighbor_search")
            == "prohibited"
            and baselines.get("trainable_frozen_plm", {})
            .get("lightweight_esm2_150m_linear", {})
            .get("head")
            == "one_affine_scalar_no_hidden_layer"
            and len(baselines.get("strongest_simple_sequence_baseline_set", [])) == 4,
            {"alphabet": zero.get("within_pair_3mer_cosine", {}).get("feature_alphabet")},
        )
    )
    primary_arch = architectures.get("esm2_650m_partner_gated_primary", {})
    checks.append(
        _check(
            "simple_symmetric_partner_architecture_and_minimal_ablations",
            architectures.get("implementation_status") == "frozen_not_implemented"
            and architectures.get("exact_swap_symmetry_required") is True
            and architectures.get("backbone_frozen_for_every_candidate") is True
            and architectures.get("residue_level_features_or_outputs") == "prohibited"
            and architectures.get("interface_or_structure_features") == "prohibited"
            and architectures.get("full_finetuning_lora_or_adapters") == "prohibited"
            and architectures.get("parameter_ceiling_excluding_frozen_encoder") == 2_000_000
            and architectures.get("esm2_650m_linear_ablation", {}).get("head")
            == "one_affine_scalar_no_hidden_layer"
            and architectures.get("esm2_650m_nonlinear_no_gate_ablation", {}).get("partner_gate")
            == "absent"
            and primary_arch.get("purpose") == "primary_simple_partner_conditioned_pooled_pair_model"
            and primary_arch.get("shared_projection", {}).get("output_dimension") == 256
            and primary_arch.get("partner_gate", {}).get("shared_gate_parameters") is True
            and primary_arch.get("head", {}).get("hidden_dimension") == 128
            and len(primary_arch.get("commutative_pair_features", [])) == 4,
            {"trainable_parameter_ceiling": architectures.get("parameter_ceiling_excluding_frozen_encoder")},
        )
    )
    p_obs = objective.get("positive_observations", {})
    u_obs = objective.get("unlabeled_observations", {})
    strata = objective.get("sampling_strata", {})
    checks.append(
        _check(
            "exact_public_training_P_U_and_strata_use",
            p_obs.get("rows") == 16_799
            and p_obs.get("use") == "complete_census_every_training_pass"
            and p_obs.get("design_weight") == "1/1"
            and u_obs.get("rows") == 2_000_000
            and u_obs.get("use")
            == "every_row_exactly_once_per_training_pass_as_a_comparison_observation"
            and u_obs.get("replacement") is False
            and u_obs.get("scientific_negative_interpretation") == "prohibited"
            and u_obs.get("weight") == "exact_frozen_rational_design_weight_N_h_over_m_h"
            and u_obs.get("weight_clipping_or_reestimation") == "prohibited"
            and strata.get("rows") == 36,
            {"P": p_obs.get("rows"), "U": u_obs.get("rows"), "strata": strata.get("rows")},
        )
    )
    checks.append(
        _check(
            "class_prior_free_design_weighted_pairwise_objective",
            objective.get("name") == "design_weighted_positive_vs_unlabeled_pairwise_logistic_ranking"
            and objective.get("unlabeled_target_class_created") is False
            and objective.get("class_prior_required") is False
            and objective.get("probability_or_calibration_target") is False
            and objective.get("per_comparison_loss")
            == "softplus(-(score_positive - score_unlabeled))"
            and objective.get("normalized_training_loss")
            == "mean((w_u / mean_weight_over_all_2000000_U_rows) * per_comparison_loss)"
            and len(objective.get("prohibited_alternatives_in_first_stage", [])) == 6,
            {"objective": objective.get("name")},
        )
    )
    order = objective.get("order", {})
    checks.append(
        _check(
            "deterministic_complete_P_U_comparison_order",
            order.get("salt") == "ipin-openppi-model-training-v1"
            and order.get("positive_key") == "sha256:{salt}:{seed}:{pass_index}:P:{pair_id}"
            and order.get("unlabeled_key") == "sha256:{salt}:{seed}:{pass_index}:U:{pair_id}"
            and order.get("sort") == "full_unsigned_digest_ascending_then_pair_id_ascending"
            and order.get("positive_for_unlabeled_position_i")
            == "positive_order[(i + pass_index - 1) mod 16799]",
            {"salt": order.get("salt")},
        )
    )
    runs = optimization.get("seed_runs", {})
    checks.append(
        _check(
            "bounded_optimizer_seed_and_search_budget",
            optimization.get("seeds") == SEEDS
            and optimization.get("batch", {}).get("pairwise_comparisons") == 4096
            and optimization.get("optimizer", {}).get("name") == "AdamW"
            and optimization.get("optimizer", {}).get("gradient_global_norm_clip") == 1.0
            and optimization.get("scheduler", {}).get("total_training_passes") == 5
            and optimization.get("scheduler", {}).get("steps_per_pass")
            == math.ceil(2_000_000 / 4096)
            and optimization.get("scheduler", {}).get("total_steps") == 2445
            and len(optimization.get("linear_recipes", [])) == 2
            and len(optimization.get("nonlinear_recipes", [])) == 3
            and runs.get("total") == 30
            and optimization.get("total_pairwise_comparisons_ceiling") == 300_000_000
            and optimization.get("adaptive_search_bayesian_optimization_or_optuna") == "prohibited",
            {"seeds": optimization.get("seeds"), "runs": runs.get("total")},
        )
    )
    checks.append(
        _check(
            "fixed_pass_checkpoint_restart_and_failure_rules",
            checkpoints.get("checkpoint_after_each_complete_U_pass") is True
            and len(checkpoints.get("checkpoint_fields", [])) == 8
            and checkpoints.get("atomic_write_then_sha256") is True
            and checkpoints.get("exact_resume_required") is True
            and checkpoints.get("selected_training_checkpoint")
            == "minimum_complete_pass_design_weighted_monitor_loss_earliest_pass_on_exact_tie"
            and checkpoints.get("performance_early_stopping") == "prohibited"
            and checkpoints.get("fixed_complete_U_passes") == 5
            and len(checkpoints.get("numerical_failure_conditions", [])) == 5
            and checkpoints.get("exact_swap_symmetry_absolute_tolerance") == 0.000001,
            {"passes": checkpoints.get("fixed_complete_U_passes")},
        )
    )
    checks.append(
        _check(
            "single_gpu_compute_and_storage_ceiling",
            budget.get("hardware") == "one_NVIDIA_GH200_120GB"
            and budget.get("four_gpu_or_multi_node_training") == "prohibited_in_first_stage"
            and budget.get("maximum_total_gpu_hours") == 100
            and budget.get("maximum_project_storage_gib") == 100,
            {"gpu_hours": budget.get("maximum_total_gpu_hours")},
        )
    )
    selection = release.get("selection_metric_order", {})
    checks.append(
        _check(
            "training_hash_before_release_and_nonadaptive_model_selection",
            release.get("development_status_now") == "encrypted_unreleased"
            and release.get("training_stage_requires_separate_numbered_authorization") is True
            and "complete_training_artifact_registry_sha256_frozen"
            in release.get("before_release_requirements", [])
            and "new_numbered_development_release_decision"
            in release.get("before_release_requirements", [])
            and release.get("ensemble_score") == "arithmetic_mean_of_the_three_run_seed_scores"
            and release.get("individual_seed_selection_on_development") == "prohibited"
            and release.get("eligibility", {}).get("all_three_seed_runs_required") is True
            and release.get("eligibility", {}).get("maximum_seed_metric_range_each_primary_cell") == 0.02
            and selection.get("cells") == ["C3_development", "C2_development", "C1_development"]
            and selection.get("quantization") == "decimal_0.001_ROUND_HALF_UP_for_selection_only"
            and release.get("metric_pooling_across_C1_C2_C3") == "prohibited"
            and release.get("post_selection_retraining") == "prohibited",
            {"development": release.get("development_status_now")},
        )
    )
    uncertainty = evaluation.get("uncertainty", {})
    checks.append(
        _check(
            "frozen_metric_reporting_and_uncertainty_hierarchy",
            evaluation.get("primary_metric", {}).get("name")
            == "horvitz_thompson_positive_vs_U_pairwise_concordance"
            and evaluation.get("primary_metric", {}).get("exact_score_ties") == "half_credit"
            and evaluation.get("cell_reporting_order") == ["C3", "C2", "C1"]
            and evaluation.get("partition_reporting_order") == ["development", "protected_test"]
            and evaluation.get("cells_must_remain_separate") is True
            and evaluation.get("no_pooled_headline_metric") is True
            and uncertainty.get("method") == "two_endpoint_component_pigeonhole_bootstrap"
            and uncertainty.get("replicates") == 2000
            and uncertainty.get("seed") == "20260803"
            and uncertainty.get("numpy_generator") == "PCG64DXSM"
            and evaluation.get("conditional_full_ranking_metrics", {}).get("status")
            == "demoted_until_exact_streaming_full_candidate_scoring_is_separately_authorized",
            {"reporting_order": evaluation.get("cell_reporting_order")},
        )
    )
    checks.append(
        _check(
            "training_only_degree_and_hub_stratification",
            stratification.get("degree_source") == "16799_interaction_supervision_training_positives_only"
            and stratification.get("degree_bins") == DEGREE_BINS
            and stratification.get("heldout_endpoint_degree") == 0
            and stratification.get("hubs", {}).get("nested_top_fractions") == [0.01, 0.05, 0.10]
            and stratification.get("hubs", {}).get("frozen_endpoint_counts") == [119, 595, 1190]
            and stratification.get("hubs", {}).get("frozen_minimum_degrees") == [41, 14, 7]
            and stratification.get("quantitative_stratum_floor")
            == {"positive_pairs": 100, "participating_components": 10}
            and stratification.get("protected_or_development_positive_degree_feature") == "prohibited",
            {"degree_bins": stratification.get("degree_bins")},
        )
    )
    checks.append(
        _check(
            "prespecified_view_only_C1_novel_U_sensitivity",
            novel_u.get("status") == "prespecified_view_only_not_executed"
            and novel_u.get("cells") == ["C1_development", "C1_test"]
            and novel_u.get("positive_rows") == "unchanged_complete_frozen_cell_positive_rows"
            and novel_u.get("U_inclusion_rule")
            == "frozen_C1_U_row_pair_id_absent_from_frozen_public_training_U_pair_ids"
            and novel_u.get("new_rows_or_resampling") == "prohibited"
            and novel_u.get("primary_cell_or_weight_modification") == "prohibited"
            and novel_u.get("original_rational_design_weight")
            == "retained_unchanged_per_retained_U_row"
            and novel_u.get("interpretation")
            == "design_weighted_Hajek_ratio_over_the_realized_novel_U_view_not_a_new_population_sample"
            and novel_u.get("model_selection_or_stopping_use") == "prohibited",
            {"cells": novel_u.get("cells")},
        )
    )
    retained = complexity.get("simple_partner_gate_retained_only_if", [])
    proposal = complexity.get(
        "proposal_of_residue_joint_encoder_sparse_routing_or_other_complex_model_requires", []
    )
    checks.append(
        _check(
            "prespecified_complexity_gate_and_simple_fallback",
            len(retained) == 7
            and any("at least 0.02" in str(value) for value in retained)
            and any("at least 0.01" in str(value) for value in retained)
            and any("at least 0.005" in str(value) for value in retained)
            and len(complexity.get("fallback_order", [])) == 4
            and len(proposal) == 6
            and "new_numbered_governance_decision" in proposal,
            {"retention_rules": len(retained), "future_complexity_prerequisites": len(proposal)},
        )
    )
    checks.append(
        _check(
            "model_level_kill_criteria_cover_shortcuts_and_release_leakage",
            len(kills) == 13
            and kills.get("any_integrity_custody_or_protected_boundary_violation")
            == "invalidate_stage_and_stop"
            and kills.get("any_use_of_U_as_scientific_negative_or_probability_target")
            == "invalidate_stage_and_stop"
            and kills.get(
                "no_learned_candidate_C3_gain_at_least_0.02_over_strongest_mandatory_baseline_with_interval_excluding_zero"
            )
            == "stop_before_protected_test"
            and kills.get("degree_graph_or_length_control_matches_or_exceeds_learned_C1_and_no_qualifying_C2_or_C3_gain")
            == "shortcut_explains_result_stop"
            and kills.get("training_interolog_or_frozen_PLM_linear_baseline_explains_C3_with_complex_delta_below_0.01_or_interval_including_zero")
            == "reject_complex_model"
            and kills.get("development_release_precedes_complete_training_artifact_registry_hash")
            == "invalidate_release_and_stop"
            and kills.get("new_candidate_training_or_retraining_after_development_release")
            == "invalidate_selection_and_stop",
            {"kill_rules": len(kills)},
        )
    )
    prohibited_claims = set(claims.get("prohibited", []))
    output_strings = [str(value) for value in outputs.values()]
    safe_output_paths = all(
        not Path(value).is_absolute()
        and ".." not in Path(value).parts
        and ".private" not in value
        and "/sealed/" not in "/" + value
        and "development_release.cms" not in value
        and "protected_candidates.cms" not in value
        and "protected_truth.cms" not in value
        for value in output_strings
    )
    checks.append(
        _check(
            "claim_ceiling_and_no_model_outputs",
            {
                "unlabeled_is_negative_nonbinding_or_failed_assay",
                "biological_or_natural_prevalence",
                "biological_precision_specificity_or_false_positive_rate",
                "calibrated_assay_or_binding_probability",
                "C3_is_unseen_gene_isoform_homolog_domain_family_or_nonhomology",
                "PLM_unseen_endpoint_or_family",
                "pretraining_exposure_cleanliness_or_causal_exposure_effect",
                "sampled_U_is_full_candidate_universe",
                "external_panel_structure_residue_or_interface_claim",
            }
            <= prohibited_claims
            and outputs.get("pair_model_embedding_checkpoint_or_prediction_artifacts") == "prohibited"
            and safe_output_paths,
            {"prohibited_claims": len(prohibited_claims)},
        )
    )
    return checks


def validate_config(config: Mapping[str, Any]) -> None:
    failures = [record for record in protocol_checks(config) if record["status"] == "fail"]
    if failures:
        names = ", ".join(record["check"] for record in failures)
        raise RuntimeError(f"Model-governance protocol validation failed: {names}")


def _verify_record(project_root: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    path = resolve_inside(project_root, str(record["path"]), project_root, strict=True)
    digest = sha256_file(path)
    expected = str(record["sha256"])
    if digest != expected:
        raise RuntimeError(f"Immutable input hash mismatch: {path}")
    return {"path": path.relative_to(project_root).as_posix(), "bytes": path.stat().st_size, "sha256": digest}


def _verify_inputs(project_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    verified: dict[str, Any] = {}
    for name, record in config["immutable_inputs"].items():
        verified[name] = _verify_record(project_root, record)
    for name in ("authorization_decision", "active_gate", "active_status"):
        record = {
            "path": config["authority"][name],
            "sha256": config["authority"][f"{name}_sha256"],
        }
        verified[name] = _verify_record(project_root, record)
    objective = config["primary_training_objective"]
    for name in ("positive_observations", "unlabeled_observations", "sampling_strata"):
        record = objective[name]
        path_text = str(record["path"])
        if "/training/" not in "/" + path_text or "/sealed/" in "/" + path_text:
            raise RuntimeError(f"Non-public training path in objective: {path_text}")
        verified[name] = _verify_record(project_root, record)
    for name in ("binding_protocol", "scientific_report"):
        path = resolve_inside(project_root, str(config["outputs"][name]), project_root, strict=True)
        verified[name] = {
            "path": path.relative_to(project_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return verified


def audit_protocol(
    *, project_root: Path, config_path: Path, allow_dirty: bool = False
) -> dict[str, Any]:
    require_apptainer()
    config = load_yaml(config_path)
    checks = protocol_checks(config)
    validate_config(config)
    verified_inputs = _verify_inputs(project_root, config)
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production model-governance audit requires a clean Git worktree")

    expected_container = resolve_inside(
        project_root,
        str(config["validation_runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    active_container_text = os.environ.get("APPTAINER_CONTAINER")
    if not active_container_text:
        raise RuntimeError("APPTAINER_CONTAINER is missing")
    active_container = Path(active_container_text).resolve(strict=True)
    if active_container != expected_container:
        raise RuntimeError("Static audit is running in the wrong container")
    if sha256_file(active_container) != DATA_SIF_SHA256:
        raise RuntimeError("Static-audit container hash mismatch")

    counts = {
        "pass": sum(record["status"] == "pass" for record in checks),
        "warning": 0,
        "fail": sum(record["status"] == "fail" for record in checks),
    }
    now = _timestamp()
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "configuration_revision": 1,
        "status": "complete" if counts["fail"] == 0 else "failed",
        "started_at_utc": now,
        "completed_at_utc": _timestamp(),
        "git": git,
        "runtime": {
            "container": expected_container.relative_to(project_root).as_posix(),
            "container_sha256": DATA_SIF_SHA256,
            "architecture": config["validation_runtime"]["architecture"],
        },
        "inputs": {
            **verified_inputs,
            "configuration": {
                "path": config_path.relative_to(project_root).as_posix(),
                "bytes": config_path.stat().st_size,
                "sha256": sha256_file(config_path),
            },
        },
        "checks": checks,
        "check_counts": counts,
        "scope": {
            "model_files_downloaded": False,
            "model_cache_populated": False,
            "model_container_built": False,
            "embedding_or_feature_cache_created": False,
            "baseline_or_model_implemented": False,
            "training_or_checkpointing_performed": False,
            "development_released_or_accessed": False,
            "protected_candidate_or_truth_accessed": False,
            "pair_or_sample_rows_created": False,
            "negative_or_pseudo_negative_created": False,
            "external_panel_or_structure_used": False,
        },
        "disposition": {
            "protocol_internally_consistent": counts["fail"] == 0,
            "independent_validation_required": True,
            "acceptance_decision_required_before_any_model_stage": True,
            "model_implementation_or_training_authorized": False,
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/model_governance_and_baseline_training_protocol_v1.yaml"),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    config_path = args.config if args.config.is_absolute() else project_root / args.config
    config_path = config_path.resolve(strict=True)
    config = load_yaml(config_path)
    report_path = args.report or Path(str(config["outputs"]["production_audit"]))
    if not report_path.is_absolute():
        report_path = project_root / report_path
    result = audit_protocol(
        project_root=project_root,
        config_path=config_path,
        allow_dirty=bool(args.allow_dirty),
    )
    _write_report(report_path, result, project_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
