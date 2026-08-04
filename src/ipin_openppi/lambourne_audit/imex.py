"""Loss-minimizing parsing of the dated IM-30553 preview exports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
import xml.etree.ElementTree as ET


MITAB27_COLUMNS = (
    "id_a",
    "id_b",
    "alt_id_a",
    "alt_id_b",
    "alias_a",
    "alias_b",
    "detection_method",
    "first_author",
    "publication_ids",
    "taxid_a",
    "taxid_b",
    "interaction_type",
    "source_database",
    "interaction_ids",
    "confidence",
    "expansion_method",
    "biological_role_a",
    "biological_role_b",
    "experimental_role_a",
    "experimental_role_b",
    "interactor_type_a",
    "interactor_type_b",
    "xref_a",
    "xref_b",
    "interaction_xrefs",
    "annotation_a",
    "annotation_b",
    "interaction_annotations",
    "host_taxid",
    "interaction_parameters",
    "creation_date",
    "update_date",
    "checksum_a",
    "checksum_b",
    "interaction_checksum",
    "negative",
    "feature_a",
    "feature_b",
    "stoichiometry_a",
    "stoichiometry_b",
    "participant_detection_method_a",
    "participant_detection_method_b",
)


def _tokens(value: str) -> Iterable[str]:
    if value in {"", "-"}:
        return ()
    return (token.strip() for token in value.split("|") if token.strip())


def first_uniprot_accession(*fields: str) -> str | None:
    for field in fields:
        for token in _tokens(field):
            if token.casefold().startswith("uniprotkb:"):
                value = token.split(":", 1)[1]
                value = value.split("(", 1)[0].strip()
                return value or None
    return None


def parse_mitab27(path: Path, *, raw_sha256: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    header_seen = False
    with path.open("rt", encoding="utf-8", errors="strict", newline="") as handle:
        for physical_line, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\r\n")
            if not line:
                continue
            if line.startswith("#"):
                header_seen = True
                continue
            values = line.split("\t")
            if len(values) != len(MITAB27_COLUMNS):
                raise RuntimeError(
                    f"IMEx MITAB 2.7 line {physical_line} has {len(values)} fields; "
                    f"expected {len(MITAB27_COLUMNS)}"
                )
            record = dict(zip(MITAB27_COLUMNS, values, strict=True))
            negative_token = record["negative"].strip().casefold()
            if negative_token in {"true", "yes", "1"}:
                negative: bool | None = True
            elif negative_token in {"false", "no", "0"}:
                negative = False
            elif negative_token in {"", "-"}:
                negative = None
            else:
                raise RuntimeError(
                    f"Unknown MITAB negative flag on line {physical_line}: "
                    f"{record['negative']!r}"
                )
            rows.append(
                {
                    "preview_row_ordinal": len(rows) + 1,
                    "physical_line": physical_line,
                    "source_accession_a": first_uniprot_accession(
                        record["id_a"], record["alt_id_a"]
                    ),
                    "source_accession_b": first_uniprot_accession(
                        record["id_b"], record["alt_id_b"]
                    ),
                    "id_a": record["id_a"],
                    "id_b": record["id_b"],
                    "alias_a": record["alias_a"],
                    "alias_b": record["alias_b"],
                    "publication_ids": record["publication_ids"],
                    "detection_method": record["detection_method"],
                    "interaction_type": record["interaction_type"],
                    "source_database": record["source_database"],
                    "interaction_ids": record["interaction_ids"],
                    "taxid_a": record["taxid_a"],
                    "taxid_b": record["taxid_b"],
                    "host_taxid": record["host_taxid"],
                    "biological_role_a": record["biological_role_a"],
                    "biological_role_b": record["biological_role_b"],
                    "experimental_role_a": record["experimental_role_a"],
                    "experimental_role_b": record["experimental_role_b"],
                    "feature_a": record["feature_a"],
                    "feature_b": record["feature_b"],
                    "participant_detection_method_a": record[
                        "participant_detection_method_a"
                    ],
                    "participant_detection_method_b": record[
                        "participant_detection_method_b"
                    ],
                    "negative_flag": negative,
                    "raw_line_sha256": hashlib.sha256(
                        raw_line.encode("utf-8")
                    ).hexdigest(),
                    "raw_file_sha256": raw_sha256,
                    "raw_fields_json": json.dumps(
                        record, sort_keys=True, separators=(",", ":")
                    ),
                }
            )
    if not header_seen:
        raise RuntimeError("IMEx MITAB 2.7 export lacks a header")
    return rows


def xml_preview_inventory(path: Path) -> dict[str, Any]:
    """Independently count local XML element names and interaction identifiers."""
    counts: dict[str, int] = {}
    interaction_ids: list[str] = []
    for _event, element in ET.iterparse(path, events=("end",)):
        name = element.tag.rsplit("}", 1)[-1]
        counts[name] = counts.get(name, 0) + 1
        if name == "interaction":
            identifier = element.attrib.get("id")
            if identifier is not None:
                interaction_ids.append(identifier)
        element.clear()
    return {
        "element_counts": dict(sorted(counts.items())),
        "interaction_elements": counts.get("interaction", 0),
        "unique_interaction_ids": len(set(interaction_ids)),
        "duplicate_interaction_ids": len(interaction_ids) - len(set(interaction_ids)),
    }
