from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from ipin_openppi.validation.pre_split_feasibility import (
    _components,
    _parse_search_independently,
    _scope_guards,
)
from ipin_openppi.validation.staging import Checks


def test_independent_components_preserve_transitive_single_linkage() -> None:
    memberships, sizes = _components(
        ["d", "c", "b", "a", "singleton"],
        {("c", "d"), ("a", "b"), ("b", "c")},
    )
    assert sizes == {"a": 4, "singleton": 1}
    assert {memberships[node] for node in "abcd"} == {"a"}


def test_raw_alignment_reparse_reconstructs_exact_normalized_edge(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "alignments.tsv"
    normalized = tmp_path / "edges.parquet"
    raw.write_text(
        "a\tb\t10\t100\t1\t100\t100\t1\t100\t100\t1e-10\t50\n"
        "b\ta\t5\t100\t1\t100\t100\t1\t100\t100\t1e-20\t60\n"
        "a\ta\t0\t100\t1\t100\t100\t1\t100\t100\t0\t100\n"
        "b\tb\t0\t100\t1\t100\t100\t1\t100\t100\t0\t100\n",
        encoding="utf-8",
    )
    row = {
        "sequence_a_sha256": "a",
        "sequence_b_sha256": "b",
        "maximum_identity": 0.95,
        "maximum_minimum_endpoint_coverage": 1.0,
        "maximum_minimum_aligned_span": 100,
        "minimum_evalue": 1e-20,
        "maximum_bits": 60.0,
        "supporting_alignment_records": 2,
    }
    pq.write_table(pa.Table.from_pylist([row]), normalized)

    parsed, metrics = _parse_search_independently(
        raw_path=raw,
        normalized_path=normalized,
        lengths={"a": 100, "b": 100},
        minimum_identity=0.20,
        minimum_coverage=0.80,
        minimum_span=0,
        maximum_evalue=1e100,
    )
    assert parsed[("a", "b")]["maximum_identity"] == 0.95
    assert parsed[("a", "b")]["supporting_alignment_records"] == 2
    assert metrics["raw_alignment_records"] == 4
    assert metrics["self_match_query_sequences"] == 2

    tampered = dict(row)
    tampered["maximum_identity"] = 0.90
    pq.write_table(pa.Table.from_pylist([tampered]), normalized)
    with pytest.raises(RuntimeError, match="Normalized value differs"):
        _parse_search_independently(
            raw_path=raw,
            normalized_path=normalized,
            lengths={"a": 100, "b": 100},
            minimum_identity=0.20,
            minimum_coverage=0.80,
            minimum_span=0,
            maximum_evalue=1e100,
        )


def test_scope_guard_fails_closed_on_downstream_or_family_claims() -> None:
    outputs = {
        "claim_assessments": [
            {
                "claim_name": "unseen_biological_family",
                "supported_by_audit": False,
                "claim_status": "prohibited",
                "model_performance_claimed": False,
                "experimental_validation_claimed": False,
            },
            {
                "claim_name": "exhaustive_absence_of_homology",
                "supported_by_audit": False,
                "claim_status": "prohibited",
                "model_performance_claimed": False,
                "experimental_validation_claimed": False,
            },
        ]
    }
    false_fields = (
        "parent_audit_modified",
        "candidate_pair_materialization_performed",
        "candidate_sampling_performed",
        "positive_pair_rows_emitted",
        "endpoint_or_component_metric_rows_emitted",
        "evidence_indicator_construction_performed",
        "interaction_label_construction_performed",
        "negative_label_construction_performed",
        "pseudo_negative_sampling_performed",
        "selected_allocation_emitted",
        "c1_c2_c3_assignment_performed",
        "split_construction_performed",
        "structural_mapping_performed",
        "model_work_performed",
        "prevalence_estimation_performed",
        "calibration_performed",
        "external_panel_inputs_used",
    )
    manifest = {field: False for field in false_fields}
    report = {"scientific_interpretation": {"unseen_family_claim_supported": False}}

    passing = Checks()
    _scope_guards(passing, outputs, manifest, report)
    assert passing.passed

    manifest["split_construction_performed"] = True
    failing = Checks()
    _scope_guards(failing, outputs, manifest, report)
    assert not failing.passed
