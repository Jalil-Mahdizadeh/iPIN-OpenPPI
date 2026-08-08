from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ipin_openppi.component_split.support import load_yaml, validate_config
from ipin_openppi.ingestion.schema import load_contract


CONFIG = Path("configs/final_benchmark_component_split_v1.yaml")
SCHEMA = Path("schemas/canonical/final_benchmark_component_split_v1.yaml")


def test_config_freezes_primary_fallback_objective_and_scope() -> None:
    config = load_yaml(CONFIG)
    validate_config(config)
    assert config["leakage_partition_policy"]["primary_hard_rule"]["id"] == "local_domain_union"
    assert config["leakage_partition_policy"]["fallback_hard_rule"]["id"] == "sensitive_fl80_union"
    assert config["allocation"]["candidate_count_per_definition"] == 4096
    assert config["allocation"]["deterministic_seed"] == "20260803"
    assert config["authorization"]["model_evaluation"] is False
    assert config["authorization"]["negative_label_construction"] is False

    unsafe = deepcopy(config)
    unsafe["leakage_partition_policy"]["evaluate_fallback_when_primary_valid"] = True
    with pytest.raises(RuntimeError, match="Leakage or fallback"):
        validate_config(unsafe)

    unsafe = deepcopy(config)
    unsafe["authorization"]["model_evaluation"] = True
    with pytest.raises(RuntimeError, match="prohibited downstream"):
        validate_config(unsafe)


def test_schema_contains_only_split_skeleton_and_aggregate_opportunities() -> None:
    contract = load_contract(SCHEMA)
    assert set(contract.document["tables"]) == {
        "component_partition_assignments",
        "endpoint_partition_assignments",
        "partition_summaries",
        "partition_degree_summaries",
        "opportunity_summaries",
        "leakage_validation_summaries",
        "selection_summaries",
        "claim_assessments",
    }
    all_columns = {
        column["name"]
        for table in contract.document["tables"].values()
        for column in table["columns"]
    }
    assert "pair_id" not in all_columns
    assert "candidate_pair_id" not in all_columns
    assert "negative_label" not in all_columns
    assert {"reference_sequence_sha256", "component_id", "partition"}.issubset(all_columns)
    assert {"pair_rows_emitted", "pair_level_label_assigned"}.issubset(all_columns)
