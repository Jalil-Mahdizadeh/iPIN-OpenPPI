"""Streaming UniProt flat-file, FASTA, and identifier-mapping parser."""

from __future__ import annotations

from collections import Counter
import gzip
import hashlib
from pathlib import Path
import re
from typing import Any, Iterator

from .common import ParquetBatchWriter, canonical_json, stable_id, strip_version
from .context import ParsingContext


_ID_RE = re.compile(r"^ID\s+(\S+)\s+(Reviewed|Unreviewed);\s+(\d+) AA\.")
_SEQUENCE_VERSION_RE = re.compile(r"sequence version (\d+)", re.IGNORECASE)
_ENTRY_VERSION_RE = re.compile(r"entry version (\d+)", re.IGNORECASE)
_TAXID_RE = re.compile(r"NCBI_TaxID=(\d+)")
_EVIDENCE_RE = re.compile(r"\s*\{[^{}]*\}")


def _clean_annotation(text: str) -> str:
    return _EVIDENCE_RE.sub("", text).strip().rstrip(";")


def parse_dat_metadata(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    in_sequence = False
    sequence_parts: list[str] = []
    record_ordinal = 0

    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, start=1):
            code = line[:2]
            content = line[5:].rstrip("\r\n") if len(line) >= 5 else ""
            if code == "ID":
                match = _ID_RE.match(line.rstrip("\r\n"))
                if not match:
                    raise ValueError(
                        f"Malformed UniProt ID line {line_number}: {line!r}"
                    )
                record_ordinal += 1
                current = {
                    "entry_name": match.group(1),
                    "reviewed": match.group(2) == "Reviewed",
                    "declared_length": int(match.group(3)),
                    "accessions": [],
                    "sequence_version": None,
                    "entry_version": None,
                    "taxid": None,
                    "gene_names": [],
                    "protein_names": [],
                    "record_ordinal": record_ordinal,
                    "start_line": line_number,
                }
                sequence_parts = []
                in_sequence = False
            elif current is None:
                continue
            elif code == "AC":
                current["accessions"].extend(
                    token.strip() for token in content.split(";") if token.strip()
                )
            elif code == "DT":
                if match := _SEQUENCE_VERSION_RE.search(content):
                    current["sequence_version"] = int(match.group(1))
                if match := _ENTRY_VERSION_RE.search(content):
                    current["entry_version"] = int(match.group(1))
            elif code == "DE" and "Full=" in content:
                value = content.split("Full=", 1)[1].split(";", 1)[0]
                cleaned = _clean_annotation(value)
                if cleaned and cleaned not in current["protein_names"]:
                    current["protein_names"].append(cleaned)
            elif code == "GN":
                for key in ("Name=", "Synonyms=", "OrderedLocusNames=", "ORFNames="):
                    if key not in content:
                        continue
                    value = content.split(key, 1)[1].split(";", 1)[0]
                    for name in _clean_annotation(value).split(","):
                        name = name.strip()
                        if name and name not in current["gene_names"]:
                            current["gene_names"].append(name)
            elif code == "OX":
                if match := _TAXID_RE.search(content):
                    current["taxid"] = int(match.group(1))
            elif code == "SQ":
                in_sequence = True
            elif line.startswith("//"):
                in_sequence = False
                if not current["accessions"]:
                    raise ValueError(
                        f"UniProt record ending at line {line_number} lacks accession"
                    )
                sequence = "".join(sequence_parts)
                if len(sequence) != current["declared_length"]:
                    raise ValueError(
                        f"UniProt DAT length mismatch for {current['accessions'][0]}: "
                        f"{len(sequence)} != {current['declared_length']}"
                    )
                current["sequence"] = sequence
                current["end_line"] = line_number
                primary = current["accessions"][0]
                if primary in metadata:
                    raise ValueError(
                        f"Duplicate UniProt DAT primary accession: {primary}"
                    )
                metadata[primary] = current
                current = None
                sequence_parts = []
            elif in_sequence:
                sequence_parts.append("".join(line.split()))

    if current is not None:
        raise ValueError("Truncated UniProt DAT record at end of file")
    return metadata, {"entries": record_ordinal}


def iter_fasta(path: Path) -> Iterator[tuple[int, str, str]]:
    header: str | None = None
    sequence_parts: list[str] = []
    ordinal = 0
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    ordinal += 1
                    yield ordinal, header, "".join(sequence_parts)
                header = line[1:]
                sequence_parts = []
            else:
                if header is None:
                    raise ValueError(
                        f"FASTA sequence before header at line {line_number}"
                    )
                sequence_parts.append(line)
    if header is not None:
        ordinal += 1
        yield ordinal, header, "".join(sequence_parts)


def _parse_fasta_header(header: str) -> dict[str, Any]:
    tokens = header.split("|", 2)
    if len(tokens) != 3:
        raise ValueError(f"Unexpected UniProt FASTA header: {header}")
    database, accession, remainder = tokens
    entry_name, _, description = remainder.partition(" ")
    taxid = None
    gene_names: list[str] = []
    sequence_version = None
    if match := re.search(r"\bOX=(\d+)", description):
        taxid = int(match.group(1))
    if match := re.search(r"\bGN=([^=]+?)(?=\s[A-Z]{2}=|$)", description):
        gene_names = [match.group(1).strip()]
    if match := re.search(r"\bSV=(\d+)", description):
        sequence_version = int(match.group(1))
    protein_description = re.split(r"\sOS=", description, maxsplit=1)[0].strip()
    return {
        "database": database,
        "accession": accession,
        "entry_name": entry_name,
        "description": description,
        "protein_description": protein_description,
        "taxid": taxid,
        "gene_names": gene_names,
        "sequence_version": sequence_version,
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
    fasta_dat_mismatches: list[str] = []
    additional_base_missing: list[str] = []

    with sequence_writer:
        for sequence_view, asset, canonical in (
            ("canonical", canonical_asset, True),
            ("additional_isoform", additional_asset, False),
        ):
            for ordinal, header, sequence in iter_fasta(asset.path):
                parsed = _parse_fasta_header(header)
                fasta_accession = parsed["accession"]
                base_accession = fasta_accession.split("-", 1)[0]
                dat = dat_metadata.get(base_accession)
                if canonical and dat is None:
                    fasta_dat_mismatches.append(f"missing_dat:{fasta_accession}")
                elif canonical and dat["sequence"] != sequence:
                    fasta_dat_mismatches.append(f"sequence_mismatch:{fasta_accession}")
                elif not canonical and dat is None:
                    additional_base_missing.append(fasta_accession)

                entry_name = dat["entry_name"] if dat else parsed["entry_name"]
                reviewed = dat["reviewed"] if dat else parsed["database"] == "sp"
                taxid = dat["taxid"] if dat and dat["taxid"] else parsed["taxid"]
                gene_names = dat["gene_names"] if dat else parsed["gene_names"]
                protein_names = (
                    dat["protein_names"]
                    if dat and dat["protein_names"]
                    else [parsed["protein_description"]]
                )
                sequence_version = (
                    parsed["sequence_version"]
                    if parsed["sequence_version"] is not None
                    else (dat["sequence_version"] if dat else None)
                )
                entry_version = dat["entry_version"] if dat else None
                sequence_sha256 = hashlib.sha256(sequence.encode()).hexdigest()
                missingness = {}
                for field, value in (
                    ("taxid", taxid),
                    ("sequence_version", sequence_version),
                    ("entry_version", entry_version),
                ):
                    if value is None:
                        missingness[field] = "not_reported"
                sequence_writer.append(
                    {
                        "protein_sequence_id": f"uniprot:{release}:{fasta_accession}",
                        "uniprot_accession": base_accession,
                        "isoform_id": None if canonical else fasta_accession,
                        "entry_name": entry_name,
                        "reviewed": reviewed,
                        "canonical": canonical,
                        "sequence_view": sequence_view,
                        "taxid": taxid,
                        "gene_names": gene_names,
                        "protein_names": protein_names,
                        "sequence_version": sequence_version,
                        "entry_version": entry_version,
                        "sequence_length": len(sequence),
                        "sequence": sequence,
                        "sequence_sha256": sequence_sha256,
                        "source_release": release,
                        "raw_file_path": asset.relative_path,
                        "raw_file_sha256": asset.sha256,
                        "raw_locator": f"fasta_record:{ordinal}",
                        "source_fields_json": canonical_json(
                            {"header": header, "database": parsed["database"]}
                        ),
                        "missingness_json": canonical_json(missingness),
                    }
                )
                sequence_counts[sequence_view] += 1

    if fasta_dat_mismatches:
        raise ValueError(
            "Canonical FASTA/DAT reconciliation failed: "
            + ", ".join(fasta_dat_mismatches[:20])
        )

    mapping_writer = ParquetBatchWriter(
        output_root / "identifier_mappings",
        context.evidence_contract,
        "identifier_mappings",
        **context.writer_kwargs(),
    )
    database_counts = Counter()
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
        "dat": dat_stats,
        "sequence_counts": dict(sorted(sequence_counts.items())),
        "canonical_fasta_dat_mismatch_count": 0,
        "additional_isoform_base_accession_missing_count": len(additional_base_missing),
        "additional_isoform_base_accession_missing_examples": additional_base_missing[
            :20
        ],
        "identifier_mapping_database_counts": dict(sorted(database_counts.items())),
        "tables": {
            "protein_sequences": sequence_writer.summary(),
            "identifier_mappings": mapping_writer.summary(),
        },
    }
