"""Map source accessions to the frozen human UniProt sequence reference."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pyarrow.dataset as ds

from ipin_openppi.ingestion.common import canonical_json, stable_id
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.ingestion.uniprot import parse_dat_metadata
from ipin_openppi.negative_evidence.negatome import split_accession


@dataclass(frozen=True)
class FrozenReferenceIndex:
    release: str
    taxid: int
    exact: dict[str, tuple[dict[str, Any], ...]]
    canonical: dict[str, tuple[dict[str, Any], ...]]
    secondary_to_primary: dict[str, tuple[str, ...]]
    dat_path: str
    dat_sha256: str

    @classmethod
    def load(
        cls,
        *,
        sequence_root: Path,
        dat_path: Path,
        release: str,
        taxid: int,
        project_root: Path,
    ) -> "FrozenReferenceIndex":
        columns = [
            "protein_sequence_id",
            "uniprot_accession",
            "isoform_id",
            "canonical",
            "sequence_view",
            "taxid",
            "sequence_version",
            "entry_version",
            "sequence_length",
            "sequence_sha256",
            "source_release",
            "raw_file_path",
            "raw_file_sha256",
        ]
        table = ds.dataset(sequence_root, format="parquet").to_table(columns=columns)
        exact: dict[str, list[dict[str, Any]]] = defaultdict(list)
        canonical: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in table.to_pylist():
            if row["source_release"] != release or int(row["taxid"]) != taxid:
                raise ValueError(
                    "Frozen sequence table release or taxon differs from policy"
                )
            if row["canonical"]:
                token = str(row["uniprot_accession"])
                canonical[token].append(row)
            elif row["isoform_id"]:
                token = str(row["isoform_id"])
            elif row["sequence_view"] == "additional_non_isoform":
                token = str(row["uniprot_accession"])
            else:
                raise ValueError(f"Unsupported frozen sequence representation: {row}")
            exact[token].append(row)

        dat_metadata, _ = parse_dat_metadata(dat_path)
        secondary: dict[str, set[str]] = defaultdict(set)
        for primary, metadata in dat_metadata.items():
            for accession in metadata["accessions"][1:]:
                secondary[str(accession)].add(primary)
        return cls(
            release=release,
            taxid=taxid,
            exact={key: tuple(value) for key, value in exact.items()},
            canonical={key: tuple(value) for key, value in canonical.items()},
            secondary_to_primary={
                key: tuple(sorted(value)) for key, value in secondary.items()
            },
            dat_path=dat_path.relative_to(project_root).as_posix(),
            dat_sha256=sha256_file(dat_path),
        )

    def _secondary_candidates(self, source_accession: str) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for primary in self.secondary_to_primary.get(source_accession, ()):
            candidates.extend(self.canonical.get(primary, ()))
        return candidates

    def map_accession(
        self,
        *,
        source_accession: str,
        parent_record_id: str,
        participant_ordinal: int,
        evidence_family: str,
    ) -> dict[str, Any]:
        base_accession, source_isoform = split_accession(source_accession)
        candidates = list(self.exact.get(source_accession, ()))
        mapping_state: str
        confidence: str
        basis: str
        if candidates:
            row = candidates[0] if len(candidates) == 1 else None
            if row is None:
                mapping_state = "ambiguous_frozen_accession"
                confidence = "D_unmapped_or_ambiguous"
                basis = "source_identifier_matches_multiple_frozen_sequence_records"
            elif row["canonical"]:
                mapping_state = "exact_primary_canonical"
                confidence = "A_exact_frozen_identifier"
                basis = "source_accession_exactly_matches_frozen_canonical_accession"
            elif row["isoform_id"]:
                mapping_state = "exact_isoform"
                confidence = "A_exact_frozen_identifier"
                basis = "source_isoform_exactly_matches_frozen_isoform_sequence"
            else:
                mapping_state = "exact_additional_non_isoform"
                confidence = "A_exact_frozen_identifier"
                basis = "source_accession_exactly_matches_frozen_additional_sequence"
        else:
            candidates = self._secondary_candidates(source_accession)
            if len(candidates) == 1:
                row = candidates[0]
                mapping_state = "secondary_accession_unique"
                confidence = "B_unique_frozen_secondary_accession"
                basis = "source_accession_is_unique_secondary_accession_in_frozen_DAT"
            elif len(candidates) > 1:
                row = None
                mapping_state = "ambiguous_frozen_accession"
                confidence = "D_unmapped_or_ambiguous"
                basis = (
                    "source_accession_maps_to_multiple_primary_entries_in_frozen_DAT"
                )
            elif source_isoform == f"{base_accession}-1":
                candidates = list(self.canonical.get(base_accession, ()))
                if len(candidates) == 1:
                    row = candidates[0]
                    mapping_state = "canonical_isoform1_alias"
                    confidence = "C_canonical_isoform1_alias"
                    basis = (
                        "explicit_isoform_1_resolved_by_frozen_canonical_alias_policy"
                    )
                elif candidates:
                    row = None
                    mapping_state = "ambiguous_frozen_accession"
                    confidence = "D_unmapped_or_ambiguous"
                    basis = "isoform_1_alias_has_multiple_frozen_canonical_candidates"
                else:
                    row = None
                    mapping_state = "not_in_frozen_human_reference"
                    confidence = "D_unmapped_or_ambiguous"
                    basis = "source_accession_absent_from_frozen_human_reference"
            else:
                row = None
                mapping_state = "not_in_frozen_human_reference"
                confidence = "D_unmapped_or_ambiguous"
                basis = "source_accession_absent_from_frozen_human_reference"

        usable = row is not None and len(candidates) == 1
        if source_isoform is None:
            isoform_state = "not_isoform_specific"
        elif mapping_state == "exact_isoform":
            isoform_state = "explicit_isoform_exact"
        elif mapping_state == "canonical_isoform1_alias":
            isoform_state = "explicit_isoform1_canonical_alias"
        else:
            isoform_state = "explicit_isoform_unresolved"

        sequence_ids = sorted(
            {str(value["protein_sequence_id"]) for value in candidates}
        )
        sequence_hashes = sorted(
            {str(value["sequence_sha256"]) for value in candidates}
        )
        accessions = sorted({str(value["uniprot_accession"]) for value in candidates})
        reference_paths = sorted(
            {str(value["raw_file_path"]) for value in candidates}
            | (
                {self.dat_path}
                if mapping_state == "secondary_accession_unique"
                else set()
            )
        )
        reference_hashes = sorted(
            {str(value["raw_file_sha256"]) for value in candidates}
            | (
                {self.dat_sha256}
                if mapping_state == "secondary_accession_unique"
                else set()
            )
        )
        return {
            "mapping_record_id": stable_id(
                "negatome-participant-map", parent_record_id, participant_ordinal
            ),
            "parent_record_id": parent_record_id,
            "evidence_family": evidence_family,
            "participant_ordinal": participant_ordinal,
            "source_accession": source_accession,
            "source_base_accession": base_accession,
            "source_isoform_id": source_isoform,
            "mapping_state": mapping_state,
            "mapping_confidence": confidence,
            "mapping_basis": basis,
            "mapping_candidate_count": len(sequence_ids),
            "candidate_sequence_ids": sequence_ids,
            "candidate_sequence_sha256s": sequence_hashes,
            "candidate_uniprot_accessions": accessions,
            "mapped_sequence_id": str(row["protein_sequence_id"]) if usable else None,
            "mapped_uniprot_accession": (
                str(row["uniprot_accession"]) if usable else None
            ),
            "mapped_isoform_id": (
                str(row["isoform_id"]) if usable and row["isoform_id"] else None
            ),
            "mapped_sequence_sha256": str(row["sequence_sha256"]) if usable else None,
            "mapped_sequence_length": int(row["sequence_length"]) if usable else None,
            "mapped_sequence_view": str(row["sequence_view"]) if usable else None,
            "mapped_sequence_version": (
                int(row["sequence_version"])
                if usable and row["sequence_version"] is not None
                else None
            ),
            "mapped_entry_version": (
                int(row["entry_version"])
                if usable and row["entry_version"] is not None
                else None
            ),
            "mapped_taxid": self.taxid if usable else None,
            "mapped_species_name": "Homo sapiens" if usable else None,
            "organism_state": (
                "exact_frozen_human_reference"
                if usable
                else "unknown_not_in_frozen_human_reference"
            ),
            "isoform_mapping_state": isoform_state,
            "reference_sequence_usable": usable,
            "exact_unique_mapping": usable,
            "construct_confidence": "D_reference_only_no_source_construct",
            "construct_sequence_sha256": None,
            "construct_start": None,
            "construct_end": None,
            "frozen_uniprot_release": self.release,
            "reference_raw_file_paths": reference_paths,
            "reference_raw_file_sha256s": reference_hashes,
            "universal_nonbinding_asserted": False,
            "label_authorized": False,
            "missingness_json": canonical_json(
                {
                    "source_sequence": "not_reported",
                    "assayed_construct_sequence": "not_reported",
                    "construct_boundaries": "not_reported",
                    "source_species": "not_reported",
                    **(
                        {"frozen_reference_mapping": "unresolved"} if not usable else {}
                    ),
                }
            ),
        }


def pair_mapping_state(mapping_rows: Iterable[dict[str, Any]]) -> str:
    usable = sum(bool(row["reference_sequence_usable"]) for row in mapping_rows)
    if usable == 2:
        return "both_unique_human"
    if usable == 1:
        return "one_unique_human"
    return "neither_unique_human"
