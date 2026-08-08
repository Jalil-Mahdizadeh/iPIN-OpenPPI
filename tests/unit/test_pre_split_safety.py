from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ipin_openppi.ingestion.schema import load_contract
from ipin_openppi.pre_split_audit.support import load_yaml, validate_config


CONFIG = Path("configs/pre_split_feasibility_and_leakage_stress_test_v1.yaml")
SCHEMA = Path("schemas/canonical/pre_split_feasibility_and_leakage_stress_test_v1.yaml")


def test_config_preserves_pu_r_parent_and_all_prohibitions() -> None:
    config = load_yaml(CONFIG)
    validate_config(config)
    assert config["authorization"]["primary_design"] == (
        "reference_sequence_positive_unlabeled_ranking"
    )
    assert config["frozen_parent_expectations"]["eligible_reference_sequences"] == 17_000
    assert config["leakage_graphs"]["identity_thresholds_percent"] == [40, 30, 20]
    assert config["allocation_feasibility"]["target_fractions"] == {
        "train": 0.70,
        "development": 0.15,
        "test": 0.15,
    }

    unsafe = deepcopy(config)
    unsafe["authorization"]["split_construction"] = True
    with pytest.raises(RuntimeError, match="prohibited downstream"):
        validate_config(unsafe)

    unsafe = deepcopy(config)
    unsafe["leakage_graphs"]["exhaustive_homology_claim_authorized"] = True
    with pytest.raises(RuntimeError, match="Leakage definitions"):
        validate_config(unsafe)


def test_schema_is_aggregate_only_and_has_explicit_false_guards() -> None:
    contract = load_contract(SCHEMA)
    assert set(contract.document["tables"]) == {
        "network_degree_summaries",
        "source_composition_summaries",
        "similarity_sensitivity_summaries",
        "leakage_graph_summaries",
        "allocation_feasibility_summaries",
        "claim_assessments",
    }
    all_columns = {
        column["name"]
        for table in contract.document["tables"].values()
        for column in table["columns"]
    }
    assert "reference_sequence_sha256" not in all_columns
    assert "component_id" not in all_columns
    assert "pair_id" not in all_columns
    assert "partition" not in all_columns
    assert {
        "pair_rows_emitted",
        "split_assignment_constructed",
        "selected_trial_emitted",
        "c1_c2_c3_labels_constructed",
        "split_constructed",
    }.issubset(all_columns)
