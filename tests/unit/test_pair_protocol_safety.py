from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ipin_openppi.pair_protocol.support import load_yaml, validate_config


CONFIG = Path("configs/pair_level_pu_r_benchmark_protocol_v1.yaml")


def test_protocol_config_freezes_scope_cutoffs_assignment_and_claims() -> None:
    config = load_yaml(CONFIG)
    validate_config(config)
    assert config["configuration_revision"] == 2
    assert config["information_cutoffs"]["partition"]["hard_rule"] == "local_domain_union_30"
    assert config["pair_assignment"]["C2"]["exclusive_of_C3"] is True
    assert config["unlabeled_sampling"]["realization_status"] == (
        "prohibited_in_this_work_package"
    )
    assert config["auxiliary_holdouts"]["assay_version_or_batch"]["status"] == (
        "inactive_missing"
    )
    assert config["claim_policy"]["prevalence_claim"] == "prohibited"
    assert config["later_simple_baselines"]["baselines"][
        "deterministic_hash_random"
    ]["public_salt"] == "ipin-openppi-pu-r-baseline-v1"
    assert config["auxiliary_holdouts"]["source_exclusive"]["canonical_cell_id"] == (
        "source_exclusive:{target_source}:{primary_cell}"
    )

    unsafe = deepcopy(config)
    unsafe["authorization"]["model_evaluation"] = True
    with pytest.raises(RuntimeError, match="prohibited protocol action"):
        validate_config(unsafe)

    unsafe = deepcopy(config)
    unsafe["auxiliary_holdouts"]["temporal"]["status"] = "active"
    with pytest.raises(RuntimeError, match="Unsupported metadata holdout"):
        validate_config(unsafe)

    unsafe = deepcopy(config)
    unsafe["pair_assignment"]["c1_positive_role"]["bucket_intervals"]["test"] = [
        8400,
        10000,
    ]
    with pytest.raises(RuntimeError, match="assignment semantics"):
        validate_config(unsafe)


def test_protocol_does_not_authorize_pair_or_sample_outputs() -> None:
    config = load_yaml(CONFIG)
    authorization = config["authorization"]
    for key in (
        "persisted_positive_pair_rows",
        "persisted_unlabeled_pair_rows",
        "pair_level_c1_c2_c3_output",
        "candidate_pair_materialization",
        "full_candidate_pair_universe_materialization",
        "unlabeled_sample_realization",
        "negative_label_construction",
        "pseudo_negative_sampling",
        "frozen_endpoint_component_split_modification",
        "external_panel_input_use",
        "structural_mapping",
        "model_training",
        "model_evaluation",
    ):
        assert authorization[key] is False
