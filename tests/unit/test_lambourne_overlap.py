from ipin_openppi.lambourne_audit.overlap import (
    build_contamination_index,
    contamination_flags,
)


def test_pair_and_endpoint_contamination_are_distinct() -> None:
    positives = {
        ("s1", "s2"): {
            "qualifying_direct_evidence_count": 1,
            "permitted_pair_view_count": 0,
        }
    }
    families = {
        "UniRef90": {"s1": frozenset({"a"}), "s2": frozenset({"b"}), "s3": frozenset({"c"})},
        "UniRef50": {"s1": frozenset({"x"}), "s2": frozenset({"y"}), "s3": frozenset({"z"})},
    }
    index = build_contamination_index(
        positive_index=positives, sequence_family_maps=families
    )
    same = contamination_flags(
        sequence_a="s2", sequence_b="s1", sequence_family_maps=families, index=index
    )
    assert same["exact_future_training_pair_overlap"]
    assert same["uniref90_pair_overlap"]
    seen_endpoint = contamination_flags(
        sequence_a="s1", sequence_b="s3", sequence_family_maps=families, index=index
    )
    assert not seen_endpoint["exact_future_training_pair_overlap"]
    assert seen_endpoint["exact_endpoint_overlap"]
