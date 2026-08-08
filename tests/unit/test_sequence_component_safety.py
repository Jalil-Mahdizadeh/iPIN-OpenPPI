from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tarfile

import pytest

from ipin_openppi.ingestion.schema import load_contract
from ipin_openppi.sequence_component_audit.support import (
    load_yaml,
    require_scoped_outputs,
    validate_config,
)
from ipin_openppi.sequence_component_audit.tooling import validate_tar_members
from ipin_openppi.validation.sequence_components import _independent_eligibility


CONFIG = Path("configs/benchmark_eligibility_and_sequence_component_audit_v1.yaml")
SCHEMA = Path(
    "schemas/canonical/benchmark_eligibility_and_sequence_component_audit_v1.yaml"
)


def test_frozen_config_preserves_pu_r_and_all_prohibitions() -> None:
    config = load_yaml(CONFIG)
    validate_config(config)
    assert config["authorization"]["primary_design"] == (
        "reference_sequence_positive_unlabeled_ranking"
    )
    assert config["sequence_components"]["emitted_thresholds_percent"] == [40, 30, 20]
    assert config["sequence_components"]["minimum_endpoint_coverage"] == 0.8
    assert config["expected_preflight"]["exact_unordered_candidate_count"] == 144_491_500
    assert not any(
        config["authorization"][name]
        for name in (
            "candidate_pair_materialization",
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
            "prevalence_estimation",
            "calibration",
            "external_panel_input_use",
        )
    )
    unsafe = deepcopy(config)
    unsafe["authorization"]["negative_label_construction"] = True
    with pytest.raises(RuntimeError, match="prohibited downstream"):
        validate_config(unsafe)


def test_schema_has_only_bounded_tables_and_false_guard_columns() -> None:
    contract = load_contract(SCHEMA)
    assert set(contract.document["tables"]) == {
        "space_iii_gene_eligibility",
        "eligible_reference_sequences",
        "sequence_component_assignments",
        "positive_mapping_aggregates",
        "positive_component_feasibility",
    }
    all_columns = {
        column["name"]
        for table in contract.document["tables"].values()
        for column in table["columns"]
    }
    assert "candidate_pair" not in all_columns
    assert "interaction_label" not in all_columns
    assert "split_id" not in all_columns
    assert "c3_assignment" not in all_columns


def test_dirty_and_hash_overrides_require_consistent_smoke_paths(tmp_path: Path) -> None:
    smoke_paths = (
        tmp_path / "_smoke_run",
        tmp_path / "_smoke_canonical",
        tmp_path / "_smoke_validation" / "report.json",
    )
    assert require_scoped_outputs(
        paths=smoke_paths, allow_dirty=True, skip_input_hashes=True
    )
    with pytest.raises(RuntimeError, match="allow-dirty"):
        require_scoped_outputs(
            paths=(tmp_path / "production", *smoke_paths[1:]),
            allow_dirty=True,
            skip_input_hashes=False,
        )
    with pytest.raises(RuntimeError, match="Skipping input hashes"):
        require_scoped_outputs(
            paths=(tmp_path / "production-a", tmp_path / "production-b"),
            allow_dirty=False,
            skip_input_hashes=True,
        )


def test_tool_archive_validation_rejects_links_and_traversal() -> None:
    safe = tarfile.TarInfo("mmseqs/bin/mmseqs")
    safe.size = 1
    validate_tar_members([safe])
    link = tarfile.TarInfo("mmseqs/bin/link")
    link.type = tarfile.SYMTYPE
    link.linkname = "/etc/passwd"
    with pytest.raises(RuntimeError, match="Unsafe"):
        validate_tar_members([link])
    traversal = tarfile.TarInfo("../escape")
    with pytest.raises(RuntimeError, match="Unsafe"):
        validate_tar_members([traversal])


def test_tool_archive_validation_rejects_duplicate_members() -> None:
    first = tarfile.TarInfo("mmseqs/LICENSE.md")
    second = tarfile.TarInfo("mmseqs/LICENSE.md")
    with pytest.raises(RuntimeError, match="Unsafe"):
        validate_tar_members([first, second])


def test_validator_embeds_escaped_literals_for_duckdb_ddl() -> None:
    class StopAfterFirstExecute(Exception):
        pass

    class CapturingConnection:
        def execute(self, sql: str, *parameters: object) -> None:
            assert not parameters
            assert "?" not in sql
            assert "identifiers.database = 'Gene''ID'" in sql
            assert "identifiers.source_release = 'release''v1'" in sql
            assert "seq.taxid = 9606" in sql
            assert "seq.source_release = 'release''v1'" in sql
            raise StopAfterFirstExecute

    with pytest.raises(StopAfterFirstExecute):
        _independent_eligibility(
            None,  # type: ignore[arg-type]
            CapturingConnection(),  # type: ignore[arg-type]
            {
                "eligibility_policy": {
                    "identifier_database": "Gene'ID",
                    "frozen_uniprot_release": "release'v1",
                    "frozen_human_taxid": 9606,
                }
            },
        )
