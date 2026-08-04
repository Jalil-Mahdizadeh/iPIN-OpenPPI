from ipin_openppi.negative_evidence.classification import (
    conflict_overlays,
    reliability_tier,
)
from ipin_openppi.negative_evidence.evidence import (
    unordered_accession_pair_id,
    unordered_pair,
    unordered_sequence_pair_id,
)


def test_unordered_pair_and_ids_are_orientation_invariant() -> None:
    assert unordered_pair("B", "A") == ("A", "B")
    assert unordered_sequence_pair_id("hash-b", "hash-a") == unordered_sequence_pair_id(
        "hash-a", "hash-b"
    )
    assert unordered_accession_pair_id("P2", "P1") == unordered_accession_pair_id(
        "P1", "P2"
    )


def test_manual_stringent_tier_is_downgraded_by_direct_conflict() -> None:
    assert (
        reliability_tier(
            evidence_family="manual_experimental_negative",
            stringent_member=True,
            reference_pair_usable=True,
            direct_positive_conflict=False,
        )
        == "ME-1"
    )
    assert (
        reliability_tier(
            evidence_family="manual_experimental_negative",
            stringent_member=True,
            reference_pair_usable=True,
            direct_positive_conflict=True,
        )
        == "ME-2"
    )
    assert conflict_overlays(direct_positive=True, broader_positive=True) == [
        "CF",
        "CF-D",
        "CF-B",
    ]
