"""Pure, deterministic semantics for the sequence-component audit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from ipin_openppi.ingestion.common import stable_id


MAPPING_STATES = (
    "unique_reference_sequence",
    "sequence_equivalent_accessions",
    "ambiguous_multiple_sequences",
    "unmapped",
)


def classify_gene_mapping(
    accessions: Sequence[str], sequence_hashes: Sequence[str]
) -> tuple[str, bool, str]:
    """Classify a Space III gene without choosing among distinct sequences."""
    unique_accessions = sorted(set(accessions))
    unique_hashes = sorted(set(sequence_hashes))
    if not unique_hashes:
        if unique_accessions:
            raise ValueError("Accessions without frozen canonical sequence hashes")
        return "unmapped", False, "unmapped"
    if not unique_accessions:
        raise ValueError("Sequence hashes without mapped accessions")
    if len(unique_hashes) > 1:
        return (
            "ambiguous_multiple_sequences",
            False,
            "ambiguous_multiple_sequences",
        )
    if len(unique_accessions) > 1:
        return "sequence_equivalent_accessions", True, "none"
    return "unique_reference_sequence", True, "none"


def exact_unordered_pair_count(distinct_items: int) -> int:
    """Return n choose 2 without constructing any pair rows."""
    if isinstance(distinct_items, bool) or not isinstance(distinct_items, int):
        raise TypeError("distinct_items must be an integer")
    if distinct_items < 0:
        raise ValueError("distinct_items must be non-negative")
    return distinct_items * (distinct_items - 1) // 2


def exact_identity(nident: int, alignment_length: int) -> float:
    if alignment_length <= 0:
        raise ValueError("alignment_length must be positive")
    if nident < 0 or nident > alignment_length:
        raise ValueError("nident is outside the alignment length")
    return nident / alignment_length


def endpoint_coverage(start: int, end: int, sequence_length: int) -> float:
    if sequence_length <= 0:
        raise ValueError("sequence_length must be positive")
    if start <= 0 or end <= 0 or start > sequence_length or end > sequence_length:
        raise ValueError("alignment endpoint is outside the sequence")
    return (abs(end - start) + 1) / sequence_length


def normalize_edge(endpoint_a: str, endpoint_b: str) -> tuple[str, str]:
    if not endpoint_a or not endpoint_b:
        raise ValueError("Sequence-edge endpoints must be nonempty")
    return tuple(sorted((endpoint_a, endpoint_b)))  # type: ignore[return-value]


class DeterministicDisjointSet:
    """Union-find whose roots and emitted components do not depend on edge order."""

    def __init__(self, members: Iterable[str]) -> None:
        ordered = sorted(set(members))
        self.parent = {member: member for member in ordered}
        self.size = {member: 1 for member in ordered}

    def find(self, member: str) -> str:
        if member not in self.parent:
            raise KeyError(member)
        root = member
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[member] != member:
            parent = self.parent[member]
            self.parent[member] = root
            member = parent
        return root

    def union(self, endpoint_a: str, endpoint_b: str) -> None:
        root_a = self.find(endpoint_a)
        root_b = self.find(endpoint_b)
        if root_a == root_b:
            return
        keep, merge = sorted((root_a, root_b))
        self.parent[merge] = keep
        self.size[keep] += self.size.pop(merge)

    def components(self) -> list[tuple[str, ...]]:
        grouped: dict[str, list[str]] = {}
        for member in sorted(self.parent):
            grouped.setdefault(self.find(member), []).append(member)
        return sorted(tuple(values) for values in grouped.values())


@dataclass(frozen=True)
class ComponentMembership:
    component_id: str
    representative: str
    size: int
    member_rank: int


def sequence_component_id(
    identity_threshold_percent: int, members: Sequence[str]
) -> str:
    ordered = tuple(sorted(members))
    if not ordered:
        raise ValueError("A component must contain at least one sequence")
    return stable_id(f"seqcomp-{identity_threshold_percent}", *ordered)


def deterministic_component_memberships(
    *,
    sequence_hashes: Iterable[str],
    edges: Iterable[tuple[str, str]],
    identity_threshold_percent: int,
) -> dict[str, ComponentMembership]:
    nodes = sorted(set(sequence_hashes))
    disjoint = DeterministicDisjointSet(nodes)
    for endpoint_a, endpoint_b in edges:
        if endpoint_a == endpoint_b:
            continue
        disjoint.union(endpoint_a, endpoint_b)
    memberships: dict[str, ComponentMembership] = {}
    for members in disjoint.components():
        component_id = sequence_component_id(identity_threshold_percent, members)
        for rank, member in enumerate(members, start=1):
            memberships[member] = ComponentMembership(
                component_id=component_id,
                representative=members[0],
                size=len(members),
                member_rank=rank,
            )
    if set(memberships) != set(nodes):
        raise RuntimeError("Component assignment did not cover every sequence")
    return memberships


def classify_positive_projection(
    *,
    unique_gene_pair: bool,
    gene_a: str | None,
    gene_b: str | None,
    eligible_by_gene: Mapping[str, str],
    ambiguous_genes: set[str],
    unmapped_genes: set[str],
) -> tuple[str, tuple[str, str] | None]:
    """Apply the frozen exclusion precedence to a reconciled HuRI evidence row."""
    if not unique_gene_pair or not gene_a or not gene_b:
        return "unresolved_gene_projection", None
    if gene_a not in eligible_by_gene and gene_a not in ambiguous_genes | unmapped_genes:
        return "outside_space_iii", None
    if gene_b not in eligible_by_gene and gene_b not in ambiguous_genes | unmapped_genes:
        return "outside_space_iii", None
    if gene_a in unmapped_genes or gene_b in unmapped_genes:
        return "unmapped_endpoint", None
    if gene_a in ambiguous_genes or gene_b in ambiguous_genes:
        return "ambiguous_endpoint", None
    if gene_a not in eligible_by_gene or gene_b not in eligible_by_gene:
        raise RuntimeError("Space III gene is absent from every mapping state")
    pair = normalize_edge(eligible_by_gene[gene_a], eligible_by_gene[gene_b])
    if pair[0] == pair[1]:
        return "same_reference_sequence", None
    return "eligible_distinct_reference_sequence_pair", pair
