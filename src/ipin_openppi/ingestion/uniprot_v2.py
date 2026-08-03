"""Active UniProt parser with explicit additional-sequence semantics."""

from __future__ import annotations

from collections import Counter
import gzip
import hashlib
from pathlib import Path
import re
from typing import Any

from .common import ParquetBatchWriter, canonical_json, stable_id, strip_version
from .context import ParsingContext
from .uniprot import _parse_fasta_header, iter_fasta, parse_dat_metadata


_ISOFORM_OF_RE = re.compile(r"\bIsoform of ([A-Z0-9]+(?:-\d+)?)\b")


def _additional_relationship(parsed_header: dict[str, Any]) -> dict[str, Any]:
    description = str(parsed_header["description"])
    match = _ISOFORM_OF_RE.search(description)
    if match:
        parent_as_reported = match.group(1)
        return {
            "sequence_view": "additional_isoform",
            "parent_accession": parent_as_reported.split("-", 1)[0],
            "parent_accession_as_reported": parent_as_reported,
            "isoform_id": parsed_header["accession"],
            "relationship": "isoform_of",
        }
    return {
        "sequence_view": "additional_non_isoform",
        "parent_accession": parsed_header["accession"],
        "parent_accession_as_reported": None,
        "isoform_id": None,
        "relationship": "additional_proteome_sequence",
    }


def parse_uniprot(context: ParsingContext, output_root: Path) -> dict[str, Any]:
    cfg = context.config["sources"]["uniprot"]
    release = str(cfg["source_release"])
    canonical_asset = context.asset(str(cfg["canonical_fasta_asset_id"]))
    additional_asset = context.asset(str(cfg["additional_fasta_asset_id"]))
    dat_asset = context.asset(str(cfg["dat_asset_id"]))
    mapping_asset = context.asset(str(cfg["idmapping_asset_id"]))

    dat_metadata, dat_stats = parse_dat_metadata(dat_asset.path)
    sequence_writer = ParquetBatchWriter(
        output_root / "protein_sequences",
        context.evidence_contract,
        "protein_sequences",
        **context.writer_kwargs(),
    )
    sequence_counts = Counter()
    database_counts = Counter()
    parent_missing: list[str] = []
    seen_sequence_ids: set[str] = set()

    with sequence_writer:
        for ordinal, header, sequence in iter_fasta(canonical_asset.path):
            parsed = _parse_fasta_header(header)
            source_accession = parsed["accession"]
            dat = dat_metadata.get(source_accession)
            if dat is None:
                raise ValueError(
                    f"Canonical FASTA accession is absent from DAT: {source_accession}"
                )
            if dat["sequence"] != sequence:
                raise ValueError(
                    f"Canonical FASTA/DAT sequence mismatch: {source_accession}"
                )
            sequence_id = f"uniprot:{release}:{source_accession}"
            if sequence_id in seen_sequence_ids:
                raise ValueError(f"Duplicate UniProt sequence ID: {sequence_id}")
            seen_sequence_ids.add(sequence_id)
            sequence_writer.append(
                {
                    "protein_sequence_id": sequence_id,
                    "uniprot_accession": source_accession,
                    "isoform_id": None,
                    "entry_name": dat["entry_name"],
                    "reviewed": dat["reviewed"],
                    "canonical": True,
                    "sequence_view": "canonical",
                    "taxid": dat["taxid"] or parsed["taxid"],
                    "gene_names": dat["gene_names"],
                    "protein_names": dat["protein_names"]
                    or [parsed["protein_description"]],
                    "sequence_version": (
                        parsed["sequence_version"]
                        if parsed["sequence_version"] is not None
                        else dat["sequence_version"]
                    ),
                    "entry_version": dat["entry_version"],
                    "sequence_length": len(sequence),
                    "sequence": sequence,
                    "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
                    "source_release": release,
                    "raw_file_path": canonical_asset.relative_path,
                    "raw_file_sha256": canonical_asset.sha256,
                    "raw_locator": f"fasta_record:{ordinal}",
                    "source_fields_json": canonical_json(
                        {
                            "header": header,
                            "source_accession": source_accession,
                            "relationship": "canonical",
                            "dat_record_ordinal": dat["record_ordinal"],
                        }
                    ),
                    "missingness_json": canonical_json(
                        {
                            field: "not_reported"
                            for field, value in (
                                ("taxid", dat["taxid"] or parsed["taxid"]),
                                ("sequence_version", dat["sequence_version"]),
                                ("entry_version", dat["entry_version"]),
                            )
                            if value is None
                        }
                    ),
                }
            )
            sequence_counts["canonical"] += 1

        for ordinal, header, sequence in iter_fasta(additional_asset.path):
            parsed = _parse_fasta_header(header)
            source_accession = parsed["accession"]
            relationship = _additional_relationship(parsed)
            parent_accession = relationship["parent_accession"]
            if (
                relationship["relationship"] == "isoform_of"
                and parent_accession not in dat_metadata
            ):
                parent_missing.append(source_accession)
            sequence_id = f"uniprot:{release}:{source_accession}"
            if sequence_id in seen_sequence_ids:
                raise ValueError(f"Duplicate UniProt sequence ID: {sequence_id}")
            seen_sequence_ids.add(sequence_id)
            missingness = {"entry_version": "not_reported"}
            if parsed["taxid"] is None:
                missingness["taxid"] = "not_reported"
            if parsed["sequence_version"] is None:
                missingness["sequence_version"] = "not_reported"
            sequence_writer.append(
                {
                    "protein_sequence_id": sequence_id,
                    "uniprot_accession": parent_accession,
                    "isoform_id": relationship["isoform_id"],
                    "entry_name": parsed["entry_name"],
                    "reviewed": parsed["database"] == "sp",
                    "canonical": False,
                    "sequence_view": relationship["sequence_view"],
                    "taxid": parsed["taxid"],
                    "gene_names": parsed["gene_names"],
                    "protein_names": [parsed["protein_description"]],
                    "sequence_version": parsed["sequence_version"],
                    "entry_version": None,
                    "sequence_length": len(sequence),
                    "sequence": sequence,
                    "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
                    "source_release": release,
                    "raw_file_path": additional_asset.relative_path,
                    "raw_file_sha256": additional_asset.sha256,
                    "raw_locator": f"fasta_record:{ordinal}",
                    "source_fields_json": canonical_json(
                        {
                            "header": header,
                            "source_accession": source_accession,
                            "parent_accession": parent_accession,
                            "parent_accession_as_reported": relationship[
                                "parent_accession_as_reported"
                            ],
                            "relationship": relationship["relationship"],
                        }
                    ),
                    "missingness_json": canonical_json(missingness),
                }
            )
            sequence_counts[relationship["sequence_view"]] += 1

    mapping_writer = ParquetBatchWriter(
        output_root / "identifier_mappings",
        context.evidence_contract,
        "identifier_mappings",
        **context.writer_kwargs(),
    )
    with (
        mapping_writer,
        gzip.open(mapping_asset.path, "rt", encoding="utf-8", newline="") as handle,
    ):
        for line_number, line in enumerate(handle, start=1):
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) != 3 or not all(fields):
                raise ValueError(
                    f"Malformed UniProt idmapping row at line {line_number}: {fields!r}"
                )
            accession, database, identifier = fields
            mapping_writer.append(
                {
                    "mapping_id": stable_id(
                        "uniprot-map", mapping_asset.sha256, line_number
                    ),
                    "uniprot_accession": accession,
                    "database": database,
                    "identifier": identifier,
                    "identifier_versionless": strip_version(identifier),
                    "source_release": release,
                    "raw_file_path": mapping_asset.relative_path,
                    "raw_file_sha256": mapping_asset.sha256,
                    "raw_locator": f"line:{line_number}",
                }
            )
            database_counts[database] += 1

    return {
        "source": "uniprot",
        "release": release,
        "parser_revision": "v2_explicit_additional_sequence_semantics",
        "dat": dat_stats,
        "sequence_counts": dict(sorted(sequence_counts.items())),
        "canonical_fasta_dat_mismatch_count": 0,
        "additional_isoform_parent_missing_count": len(parent_missing),
        "additional_isoform_parent_missing_examples": parent_missing[:20],
        "identifier_mapping_database_counts": dict(sorted(database_counts.items())),
        "tables": {
            "protein_sequences": sequence_writer.summary(),
            "identifier_mappings": mapping_writer.summary(),
        },
    }
