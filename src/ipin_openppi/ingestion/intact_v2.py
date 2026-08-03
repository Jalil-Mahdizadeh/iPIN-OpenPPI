"""Active IntAct parser with deterministic repair of malformed TSV line wraps.

The PSI-MI XML implementation remains in :mod:`intact`. The provider mutation
TSV contains five logical records split across multiple physical lines without
TSV quoting. Version 2 reconstructs a record only when exactly 15 fields are
present and both boundary accessions match the provider's EBI identifier form.
No values are invented and no malformed physical line is discarded.
"""

from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import re
from typing import Any, Iterator

from .common import ParquetBatchWriter, canonical_json, stable_id
from .context import ParsingContext
from .intact import _parse_obo, _parse_psi_xml_archive


EXPECTED_MUTATION_COLUMNS = [
    "Feature AC",
    "Feature short label",
    "Feature range(s)",
    "Original sequence",
    "Resulting sequence",
    "Feature type",
    "Feature annotation",
    "Affected protein AC",
    "Affected protein symbol",
    "Affected protein full name",
    "Affected protein organism",
    "Interaction participants",
    "PubMedID",
    "Figure legend",
    "Interaction AC",
]

_EBI_AC_RE = re.compile(r"EBI-\d+")


def iter_reconstructed_mutation_rows(
    path: Path,
) -> Iterator[tuple[int, int, dict[str, str]]]:
    """Yield logical TSV rows with their inclusive physical-line span."""

    with path.open("rt", encoding="utf-8", newline="") as handle:
        raw_header = handle.readline().rstrip("\r\n").split("\t")
        header = [value.lstrip("#") for value in raw_header]
        if header != EXPECTED_MUTATION_COLUMNS:
            raise ValueError(f"Unexpected IntAct mutation header: {header!r}")
        buffer = ""
        start_line = 0
        for line_number, physical_line in enumerate(handle, start=2):
            if not buffer:
                start_line = line_number
            buffer += physical_line.rstrip("\r\n")
            fields = buffer.split("\t")
            if len(fields) < len(header):
                continue
            if len(fields) > len(header):
                raise ValueError(
                    f"IntAct mutation record lines {start_line}-{line_number} "
                    f"contain {len(fields)} fields, expected {len(header)}"
                )
            if not _EBI_AC_RE.fullmatch(fields[0]):
                raise ValueError(
                    f"Reconstructed mutation record at lines {start_line}-{line_number} "
                    f"has invalid feature accession {fields[0]!r}"
                )
            if not _EBI_AC_RE.fullmatch(fields[-1]):
                raise ValueError(
                    f"Reconstructed mutation record at lines {start_line}-{line_number} "
                    f"has invalid interaction accession {fields[-1]!r}"
                )
            yield start_line, line_number, dict(zip(header, fields, strict=True))
            buffer = ""
        if buffer:
            raise ValueError(
                f"Truncated IntAct mutation record beginning at physical line {start_line}"
            )


def _parse_mutations_v2(
    context: ParsingContext, output_root: Path, cfg: dict[str, Any]
) -> dict[str, Any]:
    asset = context.asset(str(cfg["mutations_asset_id"]))
    writer = ParquetBatchWriter(
        output_root / "mutations",
        context.staging_contract,
        "intact_mutations",
        **context.writer_kwargs(),
    )
    span_counts: Counter[int] = Counter()
    blank_counts: Counter[str] = Counter()
    with writer:
        for logical_ordinal, (start_line, end_line, row) in enumerate(
            iter_reconstructed_mutation_rows(asset.path), start=1
        ):
            span_counts[end_line - start_line + 1] += 1
            for field, value in row.items():
                if value == "":
                    blank_counts[field] += 1
            participants = [
                token for token in row["Interaction participants"].split("|") if token
            ]
            writer.append(
                {
                    "mutation_record_id": stable_id(
                        "intact-mutation", asset.sha256, start_line, end_line
                    ),
                    "source_release": str(cfg["source_release"]),
                    "feature_ac": row["Feature AC"],
                    "feature_short_label": row["Feature short label"] or None,
                    "feature_ranges": row["Feature range(s)"] or None,
                    "original_sequence": row["Original sequence"] or None,
                    "resulting_sequence": row["Resulting sequence"] or None,
                    "feature_type": row["Feature type"] or None,
                    "feature_annotation": row["Feature annotation"] or None,
                    "affected_protein_ac": row["Affected protein AC"] or None,
                    "affected_protein_symbol": row["Affected protein symbol"] or None,
                    "affected_protein_name": row["Affected protein full name"] or None,
                    "affected_protein_organism": row["Affected protein organism"]
                    or None,
                    "interaction_participants": participants,
                    "publication_id": row["PubMedID"] or None,
                    "figure_legend": row["Figure legend"] or None,
                    "interaction_ac": row["Interaction AC"],
                    "raw_file_path": asset.relative_path,
                    "raw_file_sha256": asset.sha256,
                    "raw_locator": (
                        f"line:{start_line}"
                        if start_line == end_line
                        else f"lines:{start_line}-{end_line}"
                    ),
                    "fields_json": canonical_json(
                        {
                            **row,
                            "logical_ordinal": logical_ordinal,
                            "physical_line_start": start_line,
                            "physical_line_end": end_line,
                        }
                    ),
                }
            )
    return {
        "logical_records": writer.row_count,
        "physical_line_span_counts": {
            str(key): value for key, value in sorted(span_counts.items())
        },
        "reconstructed_multiline_records": sum(
            count for span, count in span_counts.items() if span > 1
        ),
        "blank_field_counts": dict(sorted(blank_counts.items())),
        "table": writer.summary(),
    }


def parse_intact(context: ParsingContext, output_root: Path) -> dict[str, Any]:
    cfg = dict(context.config["sources"]["intact_imex"])
    xml = _parse_psi_xml_archive(context, output_root, cfg)
    obo = _parse_obo(context, output_root, cfg)
    mutations = _parse_mutations_v2(context, output_root, cfg)
    return {
        "source": "intact_imex",
        "release": str(cfg["source_release"]),
        "parser_revision": "v2_multiline_mutation_reconstruction",
        "psi_xml": xml,
        "controlled_vocabulary": obo,
        "mutations": mutations,
    }
