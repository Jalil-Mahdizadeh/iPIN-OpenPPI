"""Deterministic mapping of exact TF clones and ORFeome partner constructs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import pyarrow.dataset as ds

from ipin_openppi.ingestion.common import canonical_json, stable_id
from ipin_openppi.tf_isoform_audit.semantics import GOVERNANCE_FALSE


def _sorted_strings(values: Iterable[Any]) -> list[str]:
    return sorted({str(value) for value in values if value not in {None, ""}})


@dataclass
class AuditReferenceMaps:
    release: str
    by_hash: dict[str, tuple[dict[str, Any], ...]]
    canonical_by_gene: dict[str, tuple[dict[str, Any], ...]]
    uniref90_by_accession: dict[str, frozenset[str]]
    huri_orf_candidates: dict[str, tuple[dict[str, Any], ...]]

    @classmethod
    def load(
        cls,
        *,
        sequence_root: Path,
        identifier_mapping_root: Path,
        participant_mapping_root: Path,
        release: str,
    ) -> "AuditReferenceMaps":
        sequence_columns = [
            "protein_sequence_id",
            "uniprot_accession",
            "isoform_id",
            "canonical",
            "reviewed",
            "sequence_view",
            "gene_names",
            "sequence_length",
            "sequence_sha256",
            "source_release",
            "raw_file_path",
            "raw_file_sha256",
        ]
        table = ds.dataset(sequence_root, format="parquet").to_table(
            columns=sequence_columns
        )
        by_hash_mutable: dict[str, list[dict[str, Any]]] = defaultdict(list)
        canonical_mutable: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in table.to_pylist():
            if str(row["source_release"]) != release:
                raise RuntimeError("Frozen protein table release differs from audit policy")
            by_hash_mutable[str(row["sequence_sha256"])].append(row)
            if row["canonical"]:
                for gene in row["gene_names"]:
                    canonical_mutable[str(gene)].append(row)

        family_table = ds.dataset(identifier_mapping_root, format="parquet").to_table(
            columns=["uniprot_accession", "database", "identifier"],
            filter=ds.field("database") == "UniRef90",
        )
        families: dict[str, set[str]] = defaultdict(set)
        for row in family_table.to_pylist():
            families[str(row["uniprot_accession"])].add(str(row["identifier"]))

        mapping_columns = [
            "source_key",
            "raw_orf_ids",
            "mapped_sequence_id",
            "mapped_uniprot_accession",
            "mapped_isoform_id",
            "mapped_sequence_sha256",
            "mapped_sequence_length",
            "mapped_sequence_view",
            "reference_sequence_usable",
            "staging_raw_file_path",
            "staging_raw_locator",
            "input_parse_manifest_sha256",
        ]
        mapping_table = ds.dataset(participant_mapping_root, format="parquet").to_table(
            columns=mapping_columns,
            filter=ds.field("source_key") == "huri",
        )
        orf_mutable: dict[str, dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)
        for row in mapping_table.to_pylist():
            if not row["reference_sequence_usable"] or not row["mapped_sequence_sha256"]:
                continue
            key = (
                str(row["mapped_sequence_sha256"]),
                str(row["mapped_sequence_id"]),
            )
            for orf_id in row["raw_orf_ids"]:
                orf_mutable[str(orf_id)][key] = row

        return cls(
            release=release,
            by_hash={
                key: tuple(sorted(rows, key=lambda row: str(row["protein_sequence_id"])))
                for key, rows in by_hash_mutable.items()
            },
            canonical_by_gene={
                key: tuple(sorted(rows, key=lambda row: str(row["protein_sequence_id"])))
                for key, rows in canonical_mutable.items()
            },
            uniref90_by_accession={
                key: frozenset(value) for key, value in families.items()
            },
            huri_orf_candidates={
                key: tuple(
                    value[index]
                    for index in sorted(value, key=lambda item: (item[0], item[1]))
                )
                for key, value in orf_mutable.items()
            },
        )

    def _family_ids(self, accessions: Iterable[str]) -> list[str]:
        return sorted(
            {
                family
                for accession in accessions
                for family in self.uniref90_by_accession.get(accession, ())
            }
        )

    def canonical_summary(self, gene_symbol: str) -> dict[str, Any]:
        rows = list(self.canonical_by_gene.get(gene_symbol, ()))
        hashes = _sorted_strings(row["sequence_sha256"] for row in rows)
        reviewed_hashes = _sorted_strings(
            row["sequence_sha256"] for row in rows if row["reviewed"]
        )
        if len(reviewed_hashes) == 1:
            state = "unique_reviewed_canonical_sequence"
        elif len(hashes) == 1:
            state = "unique_canonical_sequence"
        elif hashes:
            state = "ambiguous_multiple_canonical_sequences"
        else:
            state = "canonical_gene_not_in_frozen_reference"
        return {
            "canonical_mapping_state": state,
            "canonical_candidate_accessions": _sorted_strings(
                row["uniprot_accession"] for row in rows
            ),
            "canonical_candidate_sequence_hashes": hashes,
        }
    def clone_mapping(
        self,
        *,
        clone_id: str,
        gene_symbol: str,
        aa_sha256: str,
        aa_length: int,
        ad_orf_ids: Iterable[str],
        source_paths: Iterable[str],
        source_hashes: Iterable[str],
    ) -> dict[str, Any]:
        rows = list(self.by_hash.get(aa_sha256, ()))
        candidate_hashes = _sorted_strings(row["sequence_sha256"] for row in rows)
        exact = bool(rows)
        if exact:
            state = "exact_construct_sequence_in_frozen_reference"
        else:
            state = "exact_construct_sequence_not_in_frozen_reference"
        accessions = _sorted_strings(row["uniprot_accession"] for row in rows)
        canonical = self.canonical_summary(gene_symbol)
        return {
            "clone_mapping_id": stable_id("tfiso-clone-map", clone_id),
            "clone_id": clone_id,
            "gene_symbol": gene_symbol,
            "ad_orf_ids": _sorted_strings(ad_orf_ids),
            "construct_aa_sha256": aa_sha256,
            "construct_aa_length": int(aa_length),
            "construct_exact_frozen_match": exact,
            "construct_mapping_state": state,
            "frozen_candidate_sequence_ids": _sorted_strings(
                row["protein_sequence_id"] for row in rows
            ),
            "frozen_candidate_accessions": accessions,
            "frozen_candidate_isoform_ids": _sorted_strings(
                row["isoform_id"] for row in rows
            ),
            "frozen_candidate_sequence_hashes": candidate_hashes,
            **canonical,
            "uniref90_ids": self._family_ids(accessions),
            "frozen_uniprot_release": self.release,
            "mapping_provenance_json": canonical_json(
                {
                    "mapping_basis": "exact_reported_clone_amino_acid_sequence_sha256",
                    "source_paths": sorted(set(source_paths)),
                    "source_hashes": sorted(set(source_hashes)),
                }
            ),
            **GOVERNANCE_FALSE,
        }

    def partner_mapping(
        self,
        *,
        db_orf_id: str,
        db_gene_symbol: str,
        source_categories: Iterable[str],
        source_clone_hashes: Mapping[str, str],
        source_paths: Iterable[str],
        source_hashes: Iterable[str],
    ) -> dict[str, Any]:
        source_clone_ids = sorted(source_clone_hashes)
        source_hash_values = sorted(set(source_clone_hashes.values()))
        source_sequence_available = len(source_hash_values) == 1
        rows: list[dict[str, Any]] = []
        if source_sequence_available:
            construct_hash = source_hash_values[0]
            rows = list(self.by_hash.get(construct_hash, ()))
            if rows:
                state = "exact_tfiso_clone_sequence_in_frozen_reference"
                confidence = "A_exact_source_construct_sequence"
                basis = "db_orf_id_matches_a_unique_reported_tfiso_ad_construct"
            else:
                state = "exact_tfiso_clone_sequence_not_in_frozen_reference"
                confidence = "D_unmapped_from_frozen_reference"
                basis = "reported_db_construct_sequence_absent_from_frozen_reference"
        elif len(source_hash_values) > 1:
            state = "ambiguous_tfiso_construct_sequences"
            confidence = "D_ambiguous"
            basis = "db_orf_id_matches_multiple_reported_tfiso_construct_sequences"
        else:
            rows = list(self.huri_orf_candidates.get(db_orf_id, ()))
            hashes = _sorted_strings(row["mapped_sequence_sha256"] for row in rows)
            if len(hashes) == 1:
                state = "unique_huri_orfeome_reference_mapping"
                confidence = "B_unique_indirect_orfeome_mapping"
                basis = "same_orf_id_uniquely_maps_in_frozen_huri_reconciliation"
            elif hashes:
                state = "ambiguous_huri_orfeome_reference_mapping"
                confidence = "D_ambiguous"
                basis = "same_orf_id_maps_to_multiple_frozen_sequence_hashes"
            else:
                state = "orf_id_not_mapped_to_frozen_reference"
                confidence = "D_unmapped"
                basis = "no_source_sequence_and_no_unique_huri_orfeome_mapping"

        if source_sequence_available:
            candidate_hashes = _sorted_strings(row["sequence_sha256"] for row in rows)
            candidate_ids = _sorted_strings(row["protein_sequence_id"] for row in rows)
            candidate_accessions = _sorted_strings(row["uniprot_accession"] for row in rows)
            candidate_isoforms = _sorted_strings(row["isoform_id"] for row in rows)
        else:
            candidate_hashes = _sorted_strings(row["mapped_sequence_sha256"] for row in rows)
            candidate_ids = _sorted_strings(row["mapped_sequence_id"] for row in rows)
            candidate_accessions = _sorted_strings(row["mapped_uniprot_accession"] for row in rows)
            candidate_isoforms = _sorted_strings(row["mapped_isoform_id"] for row in rows)
        usable = len(candidate_hashes) == 1
        canonical = self.canonical_summary(db_gene_symbol)
        provenance = {
            "mapping_basis": basis,
            "source_paths": sorted(set(source_paths)),
            "source_hashes": sorted(set(source_hashes)),
            "huri_reconciliation_rows": sorted(
                {
                    f"{row.get('staging_raw_file_path')}#{row.get('staging_raw_locator')}"
                    for row in rows
                    if row.get("staging_raw_file_path")
                }
            ),
        }
        return {
            "partner_mapping_id": stable_id("tfiso-partner-map", db_orf_id),
            "db_orf_id": db_orf_id,
            "db_gene_symbol": db_gene_symbol,
            "source_categories": sorted(set(source_categories)),
            "source_construct_sequence_available": source_sequence_available,
            "source_clone_ids": source_clone_ids,
            "mapping_state": state,
            "mapping_confidence": confidence,
            "mapping_basis": basis,
            "candidate_sequence_ids": candidate_ids,
            "candidate_accessions": candidate_accessions,
            "candidate_isoform_ids": candidate_isoforms,
            "candidate_sequence_hashes": candidate_hashes,
            "mapped_sequence_sha256": candidate_hashes[0] if usable else None,
            "reference_sequence_usable": usable,
            **canonical,
            "uniref90_ids": self._family_ids(candidate_accessions),
            "frozen_uniprot_release": self.release,
            "mapping_provenance_json": canonical_json(provenance),
            **GOVERNANCE_FALSE,
        }
