"""Streaming parsers for frozen PDBe/SIFTS mapping snapshots."""

from __future__ import annotations

import csv
import gzip
from pathlib import Path
from typing import Any, Callable

from .common import ParquetBatchWriter, stable_id
from .context import ParsingContext


def _optional_int(value: str) -> int | None:
    stripped = value.strip()
    if stripped in {"", "None", "null", "NULL", "-"}:
        return None
    return int(stripped)


def _mapping_row(
    fields: dict[str, str],
    *,
    record_id: str,
    asset_path: str,
    asset_sha256: str,
    line_number: int,
    snapshot: str,
    id_column: str,
) -> dict[str, Any]:
    return {
        id_column: record_id,
        "pdb_id": fields["PDB"].lower(),
        "chain_id": fields["CHAIN"],
        "uniprot_accession": fields["SP_PRIMARY"],
        "residue_begin": _optional_int(fields["RES_BEG"]),
        "residue_end": _optional_int(fields["RES_END"]),
        "pdb_begin": fields["PDB_BEG"] or None,
        "pdb_end": fields["PDB_END"] or None,
        "uniprot_begin": _optional_int(fields["SP_BEG"]),
        "uniprot_end": _optional_int(fields["SP_END"]),
        "source_snapshot": snapshot,
        "raw_file_path": asset_path,
        "raw_file_sha256": asset_sha256,
        "raw_locator": f"line:{line_number}",
    }


def _parse_gzip_tsv(
    context: ParsingContext,
    *,
    output_root: Path,
    asset_id: str,
    table_name: str,
    row_builder: Callable[[dict[str, str], int], dict[str, Any]],
) -> tuple[dict[str, Any], str, list[str]]:
    asset = context.asset(asset_id)
    writer = ParquetBatchWriter(
        output_root / table_name,
        context.evidence_contract,
        table_name,
        **context.writer_kwargs(),
    )
    with gzip.open(asset.path, "rt", encoding="utf-8-sig", newline="") as handle:
        comment = handle.readline().rstrip("\r\n")
        header_line = handle.readline().rstrip("\r\n")
        fieldnames = header_line.split("\t")
        reader = csv.DictReader(handle, fieldnames=fieldnames, delimiter="\t")
        with writer:
            for line_number, fields in enumerate(reader, start=3):
                if None in fields:
                    raise ValueError(
                        f"Malformed SIFTS row in {asset.relative_path} line {line_number}"
                    )
                writer.append(row_builder(fields, line_number))
    return writer.summary(), comment, fieldnames


def parse_sifts(context: ParsingContext, output_root: Path) -> dict[str, Any]:
    cfg = context.config["sources"]["pdb_sifts"]
    snapshot = str(cfg["source_release"])

    chain_asset = context.asset(str(cfg["chain_uniprot_asset_id"]))
    chain_summary, chain_comment, chain_columns = _parse_gzip_tsv(
        context,
        output_root=output_root,
        asset_id=chain_asset.asset_id,
        table_name="sifts_chain_uniprot",
        row_builder=lambda fields, line_number: _mapping_row(
            fields,
            record_id=stable_id("sifts-chain", chain_asset.sha256, line_number),
            asset_path=chain_asset.relative_path,
            asset_sha256=chain_asset.sha256,
            line_number=line_number,
            snapshot=snapshot,
            id_column="mapping_id",
        ),
    )

    taxonomy_asset = context.asset(str(cfg["chain_taxonomy_asset_id"]))

    def taxonomy_row(fields: dict[str, str], line_number: int) -> dict[str, Any]:
        return {
            "taxonomy_mapping_id": stable_id(
                "sifts-taxonomy", taxonomy_asset.sha256, line_number
            ),
            "pdb_id": fields["PDB"].lower(),
            "chain_id": fields["CHAIN"],
            "taxid": int(fields["TAX_ID"]),
            "scientific_name": fields["SCIENTIFIC_NAME"] or None,
            "source_snapshot": snapshot,
            "raw_file_path": taxonomy_asset.relative_path,
            "raw_file_sha256": taxonomy_asset.sha256,
            "raw_locator": f"line:{line_number}",
        }

    taxonomy_summary, taxonomy_comment, taxonomy_columns = _parse_gzip_tsv(
        context,
        output_root=output_root,
        asset_id=taxonomy_asset.asset_id,
        table_name="sifts_chain_taxonomy",
        row_builder=taxonomy_row,
    )

    observed_asset = context.asset(str(cfg["observed_segments_asset_id"]))
    observed_summary, observed_comment, observed_columns = _parse_gzip_tsv(
        context,
        output_root=output_root,
        asset_id=observed_asset.asset_id,
        table_name="sifts_observed_segments",
        row_builder=lambda fields, line_number: _mapping_row(
            fields,
            record_id=stable_id("sifts-observed", observed_asset.sha256, line_number),
            asset_path=observed_asset.relative_path,
            asset_sha256=observed_asset.sha256,
            line_number=line_number,
            snapshot=snapshot,
            id_column="observed_segment_id",
        ),
    )

    return {
        "source": "pdb_sifts",
        "release": snapshot,
        "source_headers": {
            "chain_uniprot": chain_comment,
            "chain_taxonomy": taxonomy_comment,
            "observed_segments": observed_comment,
        },
        "columns": {
            "chain_uniprot": chain_columns,
            "chain_taxonomy": taxonomy_columns,
            "observed_segments": observed_columns,
        },
        "declared_uniprot_release_in_sifts": _extract_release(chain_comment, "UniProt"),
        "tables": {
            "sifts_chain_uniprot": chain_summary,
            "sifts_chain_taxonomy": taxonomy_summary,
            "sifts_observed_segments": observed_summary,
        },
    }


def _extract_release(comment: str, label: str) -> str | None:
    marker = f"{label}:"
    if marker not in comment:
        return None
    return comment.split(marker, 1)[1].split("|", 1)[0].strip()
