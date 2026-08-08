from __future__ import annotations

import pytest

from ipin_openppi.sequence_component_audit.semantics import (
    classify_gene_mapping,
    classify_positive_projection,
    deterministic_component_memberships,
    endpoint_coverage,
    exact_identity,
    exact_unordered_pair_count,
)


def test_gene_mapping_is_hash_based_and_fail_closed() -> None:
    assert classify_gene_mapping([], []) == ("unmapped", False, "unmapped")
    assert classify_gene_mapping(["P1"], ["a"]) == (
        "unique_reference_sequence",
        True,
        "none",
    )
    assert classify_gene_mapping(["P1", "P2"], ["a", "a"]) == (
        "sequence_equivalent_accessions",
        True,
        "none",
    )
    assert classify_gene_mapping(["P1", "P2"], ["a", "b"]) == (
        "ambiguous_multiple_sequences",
        False,
        "ambiguous_multiple_sequences",
    )
    with pytest.raises(ValueError, match="Accessions without"):
        classify_gene_mapping(["P1"], [])


def test_candidate_count_is_exact_algebra_without_rows() -> None:
    assert exact_unordered_pair_count(0) == 0
    assert exact_unordered_pair_count(1) == 0
    assert exact_unordered_pair_count(17_000) == 144_491_500
    with pytest.raises(ValueError):
        exact_unordered_pair_count(-1)
    with pytest.raises(TypeError):
        exact_unordered_pair_count(True)


def test_alignment_identity_and_coverage_use_exact_integer_coordinates() -> None:
    assert exact_identity(30, 100) == 0.3
    assert endpoint_coverage(1, 80, 100) == 0.8
    assert endpoint_coverage(80, 1, 100) == 0.8
    with pytest.raises(ValueError):
        exact_identity(101, 100)
    with pytest.raises(ValueError):
        endpoint_coverage(0, 80, 100)


def test_connected_components_are_transitive_and_edge_order_independent() -> None:
    nodes = ["d", "c", "b", "a", "singleton"]
    edges = [("c", "d"), ("a", "b"), ("b", "c")]
    forward = deterministic_component_memberships(
        sequence_hashes=nodes,
        edges=edges,
        identity_threshold_percent=30,
    )
    reverse = deterministic_component_memberships(
        sequence_hashes=reversed(nodes),
        edges=reversed(edges),
        identity_threshold_percent=30,
    )
    assert forward == reverse
    assert {forward[value].component_id for value in "abcd"} == {
        forward["a"].component_id
    }
    assert forward["a"].representative == "a"
    assert forward["d"].size == 4
    assert forward["singleton"].size == 1


def test_positive_projection_exclusion_precedence_and_no_pair_for_exclusions() -> None:
    eligible = {"g1": "h1", "g2": "h2", "g3": "h1"}
    ambiguous = {"ga"}
    unmapped = {"gu"}
    assert classify_positive_projection(
        unique_gene_pair=False,
        gene_a=None,
        gene_b=None,
        eligible_by_gene=eligible,
        ambiguous_genes=ambiguous,
        unmapped_genes=unmapped,
    ) == ("unresolved_gene_projection", None)
    assert classify_positive_projection(
        unique_gene_pair=True,
        gene_a="outside",
        gene_b="gu",
        eligible_by_gene=eligible,
        ambiguous_genes=ambiguous,
        unmapped_genes=unmapped,
    ) == ("outside_space_iii", None)
    assert classify_positive_projection(
        unique_gene_pair=True,
        gene_a="gu",
        gene_b="g1",
        eligible_by_gene=eligible,
        ambiguous_genes=ambiguous,
        unmapped_genes=unmapped,
    ) == ("unmapped_endpoint", None)
    assert classify_positive_projection(
        unique_gene_pair=True,
        gene_a="ga",
        gene_b="g1",
        eligible_by_gene=eligible,
        ambiguous_genes=ambiguous,
        unmapped_genes=unmapped,
    ) == ("ambiguous_endpoint", None)
    assert classify_positive_projection(
        unique_gene_pair=True,
        gene_a="g1",
        gene_b="g3",
        eligible_by_gene=eligible,
        ambiguous_genes=ambiguous,
        unmapped_genes=unmapped,
    ) == ("same_reference_sequence", None)
    assert classify_positive_projection(
        unique_gene_pair=True,
        gene_a="g2",
        gene_b="g1",
        eligible_by_gene=eligible,
        ambiguous_genes=ambiguous,
        unmapped_genes=unmapped,
    ) == ("eligible_distinct_reference_sequence_pair", ("h1", "h2"))
