"""Independent static validation of model-governance protocol v1.

The validator intentionally does not import the production protocol module and
contains no model, embedding, training, development, or protected-data code.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, Mapping, Sequence

import yaml

from ipin_openppi.ingestion.common import (
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.validation.staging import _write_report


EXPECTED_PROTOCOL = "model_governance_and_baseline_training_protocol_v1"
EXPECTED_DATA_SIF = "72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629"
EXPECTED_MODELS = {
    "esm2_150m": {
        "revision": "a695f6045e2e32885fa60af20c13cb35398ce30c",
        "sha256": "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566",
        "bytes": 595_257_706,
        "layers": 30,
        "hidden": 640,
        "role": "mandatory_lightweight_frozen_plm_pair_baseline",
    },
    "esm2_650m": {
        "revision": "08e4846e537177426273712802403f7ba8261b6c",
        "sha256": "a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0",
        "bytes": 2_609_506_392,
        "layers": 33,
        "hidden": 1280,
        "role": "primary_frozen_sequence_encoder_candidate",
    },
}


@dataclass
class IndependentChecks:
    records: list[dict[str, Any]] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: Mapping[str, Any]) -> None:
        self.records.append(
            {
                "check": name,
                "status": "pass" if passed else "fail",
                "detail": dict(detail),
            }
        )

    def counts(self) -> dict[str, int]:
        return {
            "pass": sum(item["status"] == "pass" for item in self.records),
            "warning": 0,
            "fail": sum(item["status"] == "fail" for item in self.records),
        }


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Independent validator expected a YAML object")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Independent validator expected a JSON object")
    return value


def _safe_project_file(root: Path, text: str) -> Path:
    raw = Path(text)
    if raw.is_absolute() or ".." in raw.parts:
        raise RuntimeError(f"Unsafe protocol path: {text}")
    candidate = root / raw
    current = root
    for part in raw.parts:
        current = current / part
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"Symlink prohibited in protocol input: {text}")
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(f"Protocol input escapes project: {text}") from exc
    if not resolved.is_file():
        raise RuntimeError(f"Protocol input is not a regular file: {text}")
    return resolved


def _verify_hash_record(root: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    path = _safe_project_file(root, str(record["path"]))
    observed = sha256_file(path)
    expected = str(record["sha256"])
    if observed != expected:
        raise RuntimeError(f"Independent input checksum mismatch: {record['path']}")
    return {"path": str(record["path"]), "bytes": path.stat().st_size, "sha256": observed}


def _verify_sidecar(report_path: Path) -> str:
    digest = sha256_file(report_path)
    sidecar = report_path.with_name(report_path.name + ".sha256")
    line = sidecar.read_text(encoding="utf-8").strip()
    fields = line.split()
    if len(fields) != 2 or fields[0] != digest or fields[1] != report_path.name:
        raise RuntimeError("Production audit sidecar mismatch")
    return digest


def independent_window_starts(
    length: int, *, window: int = 1022, stride: int = 894
) -> list[int]:
    """Reconstruct the frozen complete-coverage start rule independently."""

    if length <= 0 or window <= 0 or stride <= 0 or stride > window:
        raise ValueError("Invalid independent window arguments")
    if length <= window:
        return [0]
    starts = list(range(0, length - window + 1, stride))
    final = length - window
    if starts[-1] != final:
        starts.append(final)
    return starts


def independent_repetition_counts(unlabeled_rows: int, positive_rows: int) -> tuple[int, int, int]:
    """Return floor repeats, ceiling repeats, and positives receiving the ceiling."""

    if unlabeled_rows <= 0 or positive_rows <= 0:
        raise ValueError("Independent repetition counts require positive inputs")
    floor, remainder = divmod(unlabeled_rows, positive_rows)
    ceiling = floor + (1 if remainder else 0)
    return floor, ceiling, remainder


def independent_run_budget(config: Mapping[str, Any]) -> dict[str, int]:
    """Recompute the finite search and comparison ceilings from primitive rules."""

    optimization = config["optimization_and_search"]
    seeds = len(optimization["seeds"])
    linear_families = 2
    nonlinear_families = 2
    run_count = seeds * (
        linear_families * len(optimization["linear_recipes"])
        + nonlinear_families * len(optimization["nonlinear_recipes"])
    )
    passes = int(config["checkpointing_and_stopping"]["fixed_complete_U_passes"])
    u_rows = int(config["primary_training_objective"]["unlabeled_observations"]["rows"])
    return {"runs": run_count, "comparisons": run_count * passes * u_rows}


def independent_selection_key(
    metrics: Mapping[str, float], complexity_rank: int, candidate_id: str
) -> tuple[Decimal, Decimal, Decimal, int, str]:
    """Build the frozen development selection key without model code."""

    quantum = Decimal("0.001")

    def quantized(name: str) -> Decimal:
        value = Decimal(str(metrics[name])).quantize(quantum, rounding=ROUND_HALF_UP)
        if not Decimal("0") <= value <= Decimal("1"):
            raise ValueError("Selection metric is outside [0,1]")
        return -value

    return (
        quantized("C3_development"),
        quantized("C2_development"),
        quantized("C1_development"),
        int(complexity_rank),
        str(candidate_id),
    )


def _independent_input_verification(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    verified: dict[str, Any] = {}
    for key, record in config["immutable_inputs"].items():
        verified[key] = _verify_hash_record(root, record)
    authority = config["authority"]
    for key in ("authorization_decision", "active_gate", "active_status"):
        verified[key] = _verify_hash_record(
            root,
            {"path": authority[key], "sha256": authority[key + "_sha256"]},
        )
    objective = config["primary_training_objective"]
    for key in ("positive_observations", "unlabeled_observations", "sampling_strata"):
        path_text = str(objective[key]["path"])
        if not path_text.startswith(
            "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
        ):
            raise RuntimeError("Independent validator rejected a non-training table path")
        verified[key] = _verify_hash_record(root, objective[key])
    for key in ("binding_protocol", "scientific_report"):
        path = _safe_project_file(root, str(config["outputs"][key]))
        verified[key] = {
            "path": str(config["outputs"][key]),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return verified


def validate_protocol(
    *,
    project_root: Path,
    config_path: Path,
    audit_report_path: Path,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    config = _load_yaml(config_path)
    audit = _load_json(audit_report_path)
    audit_sha = _verify_sidecar(audit_report_path)
    verified_inputs = _independent_input_verification(project_root, config)

    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Independent model-protocol validation requires a clean Git worktree")

    container_path = _safe_project_file(
        project_root, str(config["validation_runtime"]["container"])
    )
    active_text = os.environ.get("APPTAINER_CONTAINER")
    if not active_text or Path(active_text).resolve(strict=True) != container_path:
        raise RuntimeError("Independent validation is running in the wrong container")
    if sha256_file(container_path) != EXPECTED_DATA_SIF:
        raise RuntimeError("Independent validation container checksum mismatch")

    checks = IndependentChecks()
    checks.add(
        "production_audit_identity_hash_and_scope",
        audit.get("protocol_id") == EXPECTED_PROTOCOL
        and audit.get("configuration_revision") == 1
        and audit.get("status") == "complete"
        and audit.get("check_counts") == {"pass": 24, "warning": 0, "fail": 0}
        and all(value is False for value in audit.get("scope", {}).values()),
        {"audit_sha256": audit_sha, "audit_counts": audit.get("check_counts")},
    )
    config_sha = sha256_file(config_path)
    checks.add(
        "configuration_identity_and_audit_binding",
        config.get("protocol_id") == EXPECTED_PROTOCOL
        and config.get("configuration_revision") == 1
        and config.get("status") == "authorized_not_executed"
        and audit.get("inputs", {}).get("configuration", {}).get("sha256") == config_sha,
        {"configuration_sha256": config_sha},
    )
    authority = config["authority"]
    prohibited_authority = (
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
    )
    checks.add(
        "independent_design_only_authority",
        authority.get("design_only") is True
        and authority.get("static_protocol_validation") is True
        and authority.get("return_to_governance_required") is True
        and all(authority.get(name) is False for name in prohibited_authority),
        {"prohibited_actions_false": sum(authority.get(name) is False for name in prohibited_authority)},
    )
    checks.add(
        "independent_parent_and_public_training_hashes",
        len(verified_inputs) == len(config["immutable_inputs"]) + 3 + 3 + 2,
        {"verified_records": len(verified_inputs)},
    )
    path_values = [str(item.get("path", "")) for item in config["immutable_inputs"].values()]
    path_values.extend(
        str(config["primary_training_objective"][key]["path"])
        for key in ("positive_observations", "unlabeled_observations", "sampling_strata")
    )
    path_values.extend(str(value) for value in config["outputs"].values())
    checks.add(
        "independent_sensitive_path_exclusion",
        not any(
            "/sealed/" in "/" + value
            or ".private" in value
            or "protected_candidates.cms" in value
            or "protected_truth.cms" in value
            or "development_release.cms" in value
            for value in path_values
        )
        and all(not Path(value).is_absolute() and ".." not in Path(value).parts for value in path_values)
        and all(
            config["primary_training_objective"][key]["path"].startswith(
                "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
            )
            for key in ("positive_observations", "unlabeled_observations", "sampling_strata")
        ),
        {"path_records_checked": len(path_values)},
    )

    candidates = config["plm_provenance"]["candidates"]
    model_ok = set(candidates) == set(EXPECTED_MODELS)
    for key, expected in EXPECTED_MODELS.items():
        actual = candidates.get(key, {})
        model_ok = model_ok and (
            actual.get("repository_revision") == expected["revision"]
            and actual.get("checkpoint_sha256") == expected["sha256"]
            and actual.get("checkpoint_bytes") == expected["bytes"]
            and actual.get("layers") == expected["layers"]
            and actual.get("hidden_size") == expected["hidden"]
            and actual.get("role") == expected["role"]
            and actual.get("checkpoint_file") == "model.safetensors"
            and actual.get("pickle_weights_permitted") is False
            and actual.get("trust_remote_code") is False
            and actual.get("license") == "MIT"
        )
    checks.add(
        "independent_exact_model_revisions_weights_and_roles",
        model_ok,
        {key: candidates.get(key, {}).get("repository_revision") for key in sorted(candidates)},
    )
    provenance = config["plm_provenance"]
    claim_limits = provenance["shared_claim_limits"]
    exposure_prohibitions = (
        "exact_benchmark_endpoint_unseen",
        "homolog_or_family_unseen",
        "plm_unseen_protein",
        "c3_implies_plm_unseen",
        "temporal_cleanliness_from_plm_corpus",
        "150m_vs_650m_difference_is_exposure_effect",
        "pretraining_exposure_caused_observed_gain_or_loss",
    )
    checks.add(
        "independent_pretraining_provenance_and_exposure_limits",
        provenance.get("documented_uniref_release") == "2021_04"
        and provenance.get("documented_pretraining_objective") == "masked_language_modeling"
        and provenance.get("exact_per_step_sequence_draw_log_available") is False
        and provenance.get("exact_endpoint_membership_audit_completed") is False
        and all(claim_limits.get(name) == "prohibited" for name in exposure_prohibitions),
        {"prohibited_exposure_claims": len(exposure_prohibitions)},
    )
    runtime = config["future_model_runtime"]
    custody = config["model_file_custody"]
    checks.add(
        "independent_unbuilt_runtime_and_offline_custody",
        runtime.get("status") == "recipe_frozen_image_not_built_or_authorized"
        and runtime.get("required_image_name") == "ipin-model-arm64_0.1.0.sif"
        and runtime.get("architecture") == "aarch64"
        and runtime.get("transformers") == "4.55.2"
        and runtime.get("huggingface_hub") == "0.34.4"
        and runtime.get("tokenizers") == "0.21.4"
        and runtime.get("safetensors") == "0.6.2"
        and custody.get("acquisition_status") == "not_authorized_not_present_by_this_protocol"
        and custody["future_acquisition_rules"].get("safetensors_only") is True
        and custody["future_acquisition_rules"].get("network_during_embedding_or_training")
        == "prohibited",
        {"runtime_status": runtime.get("status"), "acquisition": custody.get("acquisition_status")},
    )

    embedding = config["embedding_strategy"]
    window = embedding["windowing"]
    sample_lengths = [1, 1022, 1023, 1916, 2044, 5000]
    coverage_ok = True
    for length in sample_lengths:
        counts = [0] * length
        for start in independent_window_starts(
            length,
            window=int(window["maximum_residues"]),
            stride=int(window["stride_residues"]),
        ):
            for index in range(start, min(length, start + int(window["maximum_residues"]))):
                counts[index] += 1
        coverage_ok = coverage_ok and min(counts) >= 1
    checks.add(
        "independent_complete_long_sequence_embedding_rule",
        coverage_ok
        and int(window["overlap_residues"]) + int(window["stride_residues"])
        == int(window["maximum_residues"])
        and embedding.get("input_sequence")
        == "exact_uppercase_frozen_reference_sequence_no_truncation_or_replacement"
        and embedding.get("special_tokens_in_pool") is False
        and embedding.get("forward_dtype") == embedding.get("accumulation_dtype") == embedding.get("output_dtype") == "float32"
        and embedding["normalization_for_trainable_heads"].get("population")
        == "11900_training_partition_endpoint_embeddings_only"
        and embedding["normalization_for_trainable_heads"].get("heldout_endpoint_statistics_used")
        is False,
        {"coverage_lengths": sample_lengths},
    )
    baseline = config["mandatory_baselines"]
    zero = baseline["zero_parameter"]
    expected_zero = {
        "deterministic_hash_random",
        "endpoint_degree_sum",
        "preferential_attachment",
        "component_degree_mass_product",
        "training_graph_common_neighbors",
        "sequence_length_sum",
        "sequence_length_ratio",
        "within_pair_3mer_cosine",
        "training_interolog_3mer",
    }
    checks.add(
        "independent_mandatory_shortcut_and_sequence_baseline_ladder",
        set(zero) == expected_zero
        and zero["endpoint_degree_sum"]["score"] == "log1p(d_train_a) + log1p(d_train_b)"
        and zero["preferential_attachment"]["score"] == "log1p(d_train_a * d_train_b)"
        and zero["component_degree_mass_product"]["score"]
        == "log1p(D_component_a * D_component_b)"
        and zero["within_pair_3mer_cosine"]["feature_alphabet"]
        == "ACDEFGHIKLMNPQRSTVWYX"
        and zero["within_pair_3mer_cosine"]["k"] == 3
        and zero["training_interolog_3mer"]["approximate_nearest_neighbor_search"]
        == "prohibited"
        and baseline["trainable_frozen_plm"]["lightweight_esm2_150m_linear"]["head"]
        == "one_affine_scalar_no_hidden_layer"
        and set(baseline["strongest_simple_sequence_baseline_set"])
        == {
            "within_pair_3mer_cosine",
            "training_interolog_3mer",
            "lightweight_esm2_150m_linear",
            "esm2_650m_linear_ablation",
        },
        {"zero_parameter_baselines": len(zero)},
    )
    architectures = config["model_architectures"]
    primary = architectures["esm2_650m_partner_gated_primary"]
    expected_features = {
        "c_a_plus_c_b",
        "abs_c_a_minus_c_b",
        "c_a_hadamard_c_b",
        "cosine_c_a_c_b",
    }
    checks.add(
        "independent_swap_symmetry_partner_gate_and_ablations",
        architectures.get("implementation_status") == "frozen_not_implemented"
        and architectures.get("exact_swap_symmetry_required") is True
        and architectures.get("backbone_frozen_for_every_candidate") is True
        and architectures.get("parameter_ceiling_excluding_frozen_encoder") == 2_000_000
        and architectures.get("residue_level_features_or_outputs") == "prohibited"
        and architectures.get("interface_or_structure_features") == "prohibited"
        and architectures["esm2_650m_linear_ablation"]["purpose"]
        == "isolate_backbone_scale_without_nonlinear_or_partner_conditioning"
        and architectures["esm2_650m_nonlinear_no_gate_ablation"]["partner_gate"] == "absent"
        and primary["partner_gate"]["shared_gate_parameters"] is True
        and primary["partner_gate"]["formula_a"]
        == "c_a = projected_a * sigmoid(W_gate projected_b + b_gate)"
        and primary["partner_gate"]["formula_b"]
        == "c_b = projected_b * sigmoid(W_gate projected_a + b_gate)"
        and set(primary["commutative_pair_features"]) == expected_features,
        {"commutative_features": len(primary["commutative_pair_features"])},
    )

    objective = config["primary_training_objective"]
    p_rows = int(objective["positive_observations"]["rows"])
    u_rows = int(objective["unlabeled_observations"]["rows"])
    floor_rep, ceil_rep, high_count = independent_repetition_counts(u_rows, p_rows)
    checks.add(
        "independent_P_U_objective_and_complete_coverage_algebra",
        p_rows == 16_799
        and u_rows == 2_000_000
        and objective["positive_observations"]["use"] == "complete_census_every_training_pass"
        and objective["unlabeled_observations"]["use"]
        == "every_row_exactly_once_per_training_pass_as_a_comparison_observation"
        and objective["unlabeled_observations"]["scientific_negative_interpretation"]
        == "prohibited"
        and objective["unlabeled_observations"]["weight_clipping_or_reestimation"]
        == "prohibited"
        and objective.get("unlabeled_target_class_created") is False
        and objective.get("class_prior_required") is False
        and objective.get("probability_or_calibration_target") is False
        and objective.get("per_comparison_loss")
        == "softplus(-(score_positive - score_unlabeled))"
        and floor_rep == 119
        and ceil_rep == 120
        and high_count == 919,
        {"positive_repeat_floor": floor_rep, "ceiling": ceil_rep, "ceiling_count": high_count},
    )
    computed_budget = independent_run_budget(config)
    scheduler = config["optimization_and_search"]["scheduler"]
    checks.add(
        "independent_search_run_step_and_comparison_budget",
        computed_budget == {"runs": 30, "comparisons": 300_000_000}
        and scheduler["steps_per_pass"] == math.ceil(u_rows / 4096)
        and scheduler["total_steps"] == 5 * math.ceil(u_rows / 4096)
        and config["optimization_and_search"]["seed_runs"]["total"] == 30
        and config["optimization_and_search"]["total_pairwise_comparisons_ceiling"]
        == 300_000_000
        and config["optimization_and_search"]["adaptive_search_bayesian_optimization_or_optuna"]
        == "prohibited",
        computed_budget,
    )
    optimization = config["optimization_and_search"]
    stopping = config["checkpointing_and_stopping"]
    checks.add(
        "independent_reproducibility_checkpoint_and_fixed_stopping",
        optimization["seeds"] == [20260803, 20260817, 20260831]
        and optimization["seed_controls"]["numpy_generator"] == "PCG64DXSM_run_seed"
        and optimization["seed_controls"]["torch_deterministic_algorithms"] is True
        and optimization["seed_controls"]["allow_tf32"] is False
        and optimization["seed_controls"]["cublas_workspace_config"] == ":4096:8"
        and stopping["checkpoint_after_each_complete_U_pass"] is True
        and stopping["selected_training_checkpoint"]
        == "minimum_complete_pass_design_weighted_monitor_loss_earliest_pass_on_exact_tie"
        and stopping["performance_early_stopping"] == "prohibited"
        and stopping["fixed_complete_U_passes"] == 5
        and stopping["exact_swap_symmetry_absolute_tolerance"] == 0.000001,
        {"seeds": optimization["seeds"], "passes": stopping["fixed_complete_U_passes"]},
    )
    release = config["development_release_and_model_selection"]
    example_key_a = independent_selection_key(
        {"C3_development": 0.6125, "C2_development": 0.7, "C1_development": 0.8},
        3,
        "gated",
    )
    example_key_b = independent_selection_key(
        {"C3_development": 0.6124, "C2_development": 0.8, "C1_development": 0.9},
        0,
        "linear",
    )
    checks.add(
        "independent_training_registry_before_release_and_selection_order",
        release["development_status_now"] == "encrypted_unreleased"
        and release["training_stage_requires_separate_numbered_authorization"] is True
        and "complete_training_artifact_registry_sha256_frozen"
        in release["before_release_requirements"]
        and "independent_training_artifact_validation_passed"
        in release["before_release_requirements"]
        and "new_numbered_development_release_decision"
        in release["before_release_requirements"]
        and release["ensemble_score"] == "arithmetic_mean_of_the_three_run_seed_scores"
        and release["individual_seed_selection_on_development"] == "prohibited"
        and release["selection_metric_order"]["cells"]
        == ["C3_development", "C2_development", "C1_development"]
        and release["metric_pooling_across_C1_C2_C3"] == "prohibited"
        and release["post_selection_retraining"] == "prohibited"
        and example_key_a < example_key_b,
        {"selection_cells": release["selection_metric_order"]["cells"]},
    )
    evaluation = config["evaluation_and_reporting"]
    uncertainty = evaluation["uncertainty"]
    checks.add(
        "independent_metric_tie_reporting_and_bootstrap_hierarchy",
        evaluation["primary_metric"]["name"]
        == "horvitz_thompson_positive_vs_U_pairwise_concordance"
        and "0.5*I(s_p=s_u)" in evaluation["primary_metric"]["formula"]
        and evaluation["primary_metric"]["exact_score_ties"] == "half_credit"
        and evaluation["cell_reporting_order"] == ["C3", "C2", "C1"]
        and evaluation["partition_reporting_order"] == ["development", "protected_test"]
        and evaluation["cells_must_remain_separate"] is True
        and evaluation["no_pooled_headline_metric"] is True
        and uncertainty["method"] == "two_endpoint_component_pigeonhole_bootstrap"
        and uncertainty["dependence_unit"] == "frozen_local_domain_union_30_component"
        and uncertainty["replicates"] == 2000
        and uncertainty["seed"] == "20260803"
        and uncertainty["numpy_generator"] == "PCG64DXSM"
        and evaluation["conditional_full_ranking_metrics"]["status"]
        == "demoted_until_exact_streaming_full_candidate_scoring_is_separately_authorized",
        {"primary_metric": evaluation["primary_metric"]["name"]},
    )
    degree = config["degree_and_hub_stratification"]
    checks.add(
        "independent_training_only_degree_hub_strata",
        degree["degree_source"] == "16799_interaction_supervision_training_positives_only"
        and degree["degree_bins"]
        == ["0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+"]
        and degree["hubs"]["frozen_endpoint_counts"] == [119, 595, 1190]
        and degree["hubs"]["frozen_minimum_degrees"] == [41, 14, 7]
        and degree["heldout_endpoint_degree"] == 0
        and degree["quantitative_stratum_floor"]
        == {"positive_pairs": 100, "participating_components": 10}
        and degree["protected_or_development_positive_degree_feature"] == "prohibited",
        {"hub_counts": degree["hubs"]["frozen_endpoint_counts"]},
    )
    novel = config["c1_novel_U_sensitivity"]
    checks.add(
        "independent_C1_novel_U_view_semantics_and_weights",
        novel["status"] == "prespecified_view_only_not_executed"
        and novel["cells"] == ["C1_development", "C1_test"]
        and novel["positive_rows"] == "unchanged_complete_frozen_cell_positive_rows"
        and novel["U_inclusion_rule"]
        == "frozen_C1_U_row_pair_id_absent_from_frozen_public_training_U_pair_ids"
        and novel["new_rows_or_resampling"] == "prohibited"
        and novel["primary_cell_or_weight_modification"] == "prohibited"
        and novel["original_rational_design_weight"]
        == "retained_unchanged_per_retained_U_row"
        and "sum_over_retained_u(w_u)" in novel["conditional_metric"]
        and novel["interpretation"]
        == "design_weighted_Hajek_ratio_over_the_realized_novel_U_view_not_a_new_population_sample"
        and novel["model_selection_or_stopping_use"] == "prohibited",
        {"novel_U_cells": novel["cells"]},
    )
    complexity = config["complexity_justification"]
    kill = config["model_level_kill_criteria"]
    retention = " ".join(map(str, complexity["simple_partner_gate_retained_only_if"]))
    checks.add(
        "independent_complexity_thresholds_and_shortcut_kill_rules",
        "at least 0.02" in retention
        and "at least 0.01" in retention
        and "at least 0.005" in retention
        and complexity["fallback_order"]
        == [
            "remove_partner_gate_if_gate_specific_threshold_fails",
            "remove_nonlinear_head_if_no_gate_model_does_not_beat_linear_650m",
            "retain_lightweight_150m_linear_only_if_650m_scale_is_not_justified",
            "terminate_learned_model_line_if_no_learned_candidate_beats_deterministic_controls",
        ]
        and len(
            complexity[
                "proposal_of_residue_joint_encoder_sparse_routing_or_other_complex_model_requires"
            ]
        )
        == 6
        and len(kill) == 13
        and kill["degree_graph_or_length_control_matches_or_exceeds_learned_C1_and_no_qualifying_C2_or_C3_gain"]
        == "shortcut_explains_result_stop"
        and kill["training_interolog_or_frozen_PLM_linear_baseline_explains_C3_with_complex_delta_below_0.01_or_interval_including_zero"]
        == "reject_complex_model"
        and kill["development_release_precedes_complete_training_artifact_registry_hash"]
        == "invalidate_release_and_stop"
        and kill["new_candidate_training_or_retraining_after_development_release"]
        == "invalidate_selection_and_stop",
        {"kill_rules": len(kill)},
    )
    prohibited_claims = set(config["claim_policy"]["prohibited"])
    checks.add(
        "independent_claim_ceiling_and_no_executable_model_output",
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
        and config["outputs"]["pair_model_embedding_checkpoint_or_prediction_artifacts"]
        == "prohibited",
        {"prohibited_claims": len(prohibited_claims)},
    )

    counts = checks.counts()
    return {
        "schema_version": 1,
        "protocol_id": EXPECTED_PROTOCOL,
        "configuration_revision": 1,
        "status": "complete" if counts["fail"] == 0 else "failed",
        "started_at_utc": _timestamp(),
        "completed_at_utc": _timestamp(),
        "git": git,
        "runtime": {
            "container": config["validation_runtime"]["container"],
            "container_sha256": EXPECTED_DATA_SIF,
            "architecture": config["validation_runtime"]["architecture"],
        },
        "inputs": {
            **verified_inputs,
            "configuration": {
                "path": config_path.relative_to(project_root).as_posix(),
                "sha256": config_sha,
                "bytes": config_path.stat().st_size,
            },
            "production_audit": {
                "path": audit_report_path.relative_to(project_root).as_posix(),
                "sha256": audit_sha,
                "bytes": audit_report_path.stat().st_size,
            },
        },
        "checks": checks.records,
        "check_counts": counts,
        "scope": {
            "sealed_package_opened": False,
            "private_key_accessed": False,
            "development_or_protected_identity_accessed": False,
            "model_file_downloaded": False,
            "embedding_model_training_or_scoring_executed": False,
            "pair_sample_negative_or_pseudo_negative_created": False,
        },
        "disposition": {
            "consequential_rules_independently_validated": counts["fail"] == 0,
            "acceptance_permitted": counts["fail"] == 0,
            "model_implementation_or_training_authorized": False,
            "development_or_protected_access_authorized": False,
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/model_governance_and_baseline_training_protocol_v1.yaml"),
    )
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    config_path = args.config if args.config.is_absolute() else project_root / args.config
    config_path = config_path.resolve(strict=True)
    config = _load_yaml(config_path)
    audit_path = args.audit_report or Path(str(config["outputs"]["production_audit"]))
    report_path = args.report or Path(str(config["outputs"]["independent_validation"]))
    if not audit_path.is_absolute():
        audit_path = project_root / audit_path
    if not report_path.is_absolute():
        report_path = project_root / report_path
    result = validate_protocol(
        project_root=project_root,
        config_path=config_path,
        audit_report_path=audit_path.resolve(strict=True),
        allow_dirty=bool(args.allow_dirty),
    )
    _write_report(report_path, result, project_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
