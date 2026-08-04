"""Frozen evidence overlap and bounded UniRef contamination utilities."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import duckdb
import pyarrow.dataset as ds

from ipin_openppi.negative_evidence.evidence import unordered_pair
from ipin_openppi.negative_evidence.reference import FrozenReferenceIndex


FamilyMap = dict[str, frozenset[str]]


def _family_pair_signatures(
    left: Iterable[str], right: Iterable[str]
) -> set[tuple[str, str]]:
    return {unordered_pair(a, b) for a in left for b in right}


def load_sequence_family_maps(
    *,
    identifier_mapping_root: Path,
    reference: FrozenReferenceIndex,
) -> tuple[dict[str, dict[str, frozenset[str]]], dict[str, dict[str, frozenset[str]]]]:
    """Return accession and exact-sequence mappings for frozen UniRef100/90/50."""
    family_names = ("UniRef100", "UniRef90", "UniRef50")
    table = ds.dataset(identifier_mapping_root, format="parquet").to_table(
        columns=["uniprot_accession", "database", "identifier"],
        filter=ds.field("database").isin(family_names),
    )
    mutable_accession: dict[str, dict[str, set[str]]] = {
        name: defaultdict(set) for name in family_names
    }
    for row in table.to_pylist():
        mutable_accession[str(row["database"])][str(row["uniprot_accession"])].add(
            str(row["identifier"])
        )
    accession_maps = {
        name: {key: frozenset(value) for key, value in values.items()}
        for name, values in mutable_accession.items()
    }
    mutable_sequence: dict[str, dict[str, set[str]]] = {
        name: defaultdict(set) for name in family_names
    }
    seen_rows: set[tuple[str, str]] = set()
    for candidates in reference.exact.values():
        for row in candidates:
            key = (str(row["protein_sequence_id"]), str(row["uniprot_accession"]))
            if key in seen_rows:
                continue
            seen_rows.add(key)
            sequence_hash = str(row["sequence_sha256"])
            accession = str(row["uniprot_accession"])
            for name in family_names:
                mutable_sequence[name][sequence_hash].update(
                    accession_maps[name].get(accession, ())
                )
    sequence_maps = {
        name: {key: frozenset(value) for key, value in values.items()}
        for name, values in mutable_sequence.items()
    }
    return accession_maps, sequence_maps


@dataclass(frozen=True)
class ContaminationIndex:
    exact_pairs: frozenset[tuple[str, str]]
    exact_endpoints: frozenset[str]
    uniref90_pairs: frozenset[tuple[str, str]]
    uniref50_pairs: frozenset[tuple[str, str]]
    uniref90_endpoints: frozenset[str]
    uniref50_endpoints: frozenset[str]


def build_contamination_index(
    *,
    positive_index: Mapping[tuple[str, str], Mapping[str, Any]],
    sequence_family_maps: Mapping[str, FamilyMap],
) -> ContaminationIndex:
    exact_pairs = {
        unordered_pair(*pair)
        for pair, evidence in positive_index.items()
        if int(evidence["qualifying_direct_evidence_count"]) > 0
        or int(evidence["permitted_pair_view_count"]) > 0
    }
    exact_endpoints = {member for pair in exact_pairs for member in pair}

    def families(name: str) -> tuple[set[tuple[str, str]], set[str]]:
        mapping = sequence_family_maps[name]
        pairs: set[tuple[str, str]] = set()
        endpoints: set[str] = set()
        for left, right in exact_pairs:
            left_ids, right_ids = mapping.get(left, ()), mapping.get(right, ())
            endpoints.update(left_ids)
            endpoints.update(right_ids)
            pairs.update(_family_pair_signatures(left_ids, right_ids))
        return pairs, endpoints

    pairs90, endpoints90 = families("UniRef90")
    pairs50, endpoints50 = families("UniRef50")
    return ContaminationIndex(
        exact_pairs=frozenset(exact_pairs),
        exact_endpoints=frozenset(exact_endpoints),
        uniref90_pairs=frozenset(pairs90),
        uniref50_pairs=frozenset(pairs50),
        uniref90_endpoints=frozenset(endpoints90),
        uniref50_endpoints=frozenset(endpoints50),
    )


def contamination_flags(
    *,
    sequence_a: str | None,
    sequence_b: str | None,
    sequence_family_maps: Mapping[str, FamilyMap],
    index: ContaminationIndex,
) -> dict[str, bool]:
    if sequence_a is None or sequence_b is None:
        return {
            "exact_future_training_pair_overlap": False,
            "uniref90_pair_overlap": False,
            "uniref50_pair_overlap": False,
            "exact_endpoint_overlap": False,
            "uniref90_endpoint_overlap": False,
            "uniref50_endpoint_overlap": False,
        }
    pair = unordered_pair(sequence_a, sequence_b)
    family90_a = sequence_family_maps["UniRef90"].get(sequence_a, ())
    family90_b = sequence_family_maps["UniRef90"].get(sequence_b, ())
    family50_a = sequence_family_maps["UniRef50"].get(sequence_a, ())
    family50_b = sequence_family_maps["UniRef50"].get(sequence_b, ())
    return {
        "exact_future_training_pair_overlap": pair in index.exact_pairs,
        "uniref90_pair_overlap": bool(
            _family_pair_signatures(family90_a, family90_b) & index.uniref90_pairs
        ),
        "uniref50_pair_overlap": bool(
            _family_pair_signatures(family50_a, family50_b) & index.uniref50_pairs
        ),
        "exact_endpoint_overlap": (
            sequence_a in index.exact_endpoints or sequence_b in index.exact_endpoints
        ),
        "uniref90_endpoint_overlap": bool(
            set(family90_a) & index.uniref90_endpoints
            or set(family90_b) & index.uniref90_endpoints
        ),
        "uniref50_endpoint_overlap": bool(
            set(family50_a) & index.uniref50_endpoints
            or set(family50_b) & index.uniref50_endpoints
        ),
    }


def source_specific_positive_index(
    connection: duckdb.DuckDBPyConnection,
) -> dict[tuple[str, str], dict[str, int]]:
    """Aggregate the record-level positive view left by build_positive_pair_index."""
    rows = connection.execute(
        """
        SELECT
            sequence_sha256_a,
            sequence_sha256_b,
            count_if(source_key = 'huri')::BIGINT AS huri_records,
            count_if(source_key = 'intact_imex')::BIGINT AS intact_records,
            count_if(source_key = 'intact_imex'
                AND interaction_semantics = 'direct_binary')::BIGINT AS intact_direct
        FROM mapped_positive_evidence_pairs
        GROUP BY sequence_sha256_a, sequence_sha256_b
        """
    ).fetchall()
    return {
        unordered_pair(str(row[0]), str(row[1])): {
            "huri_record_positive_count": int(row[2]),
            "intact_positive_count": int(row[3]),
            "intact_direct_positive_count": int(row[4]),
        }
        for row in rows
    }


def load_negatome_pair_index(
    root: Path,
) -> dict[tuple[str, str], dict[str, list[str]]]:
    columns = [
        "parent_record_id",
        "evidence_family",
        "mapped_sequence_sha256_a",
        "mapped_sequence_sha256_b",
        "reference_pair_usable",
    ]
    table = ds.dataset(root, format="parquet").to_table(columns=columns)
    records: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"record_ids": set(), "evidence_families": set()}
    )
    for row in table.to_pylist():
        if not row["reference_pair_usable"]:
            continue
        pair = unordered_pair(
            str(row["mapped_sequence_sha256_a"]),
            str(row["mapped_sequence_sha256_b"]),
        )
        records[pair]["record_ids"].add(str(row["parent_record_id"]))
        records[pair]["evidence_families"].add(str(row["evidence_family"]))
    return {
        pair: {
            "record_ids": sorted(value["record_ids"]),
            "evidence_families": sorted(value["evidence_families"]),
        }
        for pair, value in records.items()
    }
