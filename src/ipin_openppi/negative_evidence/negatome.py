"""Lossless parsing and parent/stringent reconciliation for Negatome 2.0."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
import csv
from pathlib import Path
import re
from typing import Any, Iterable

from ipin_openppi.ingestion.common import canonical_json, stable_id


_MI_RE = re.compile(r"^(MI:\d{4})\s*(?:-|\s)\s*(.*)$")
_ISOFORM_RE = re.compile(r"^(.+)-(\d+)$")
_PDB_HEADER = ["#ProteinA", "ProteinB", "PDB_Code", "evidence"]


@dataclass(frozen=True)
class NegatomeRow:
    dataset: str
    evidence_family: str
    parent_dataset: str
    ordinal: int
    accession_a: str
    accession_b: str
    field_3: str
    assay_text: str
    publication_ids: tuple[str, ...]
    pdb_ids: tuple[str, ...]
    assay_mi_ac: str | None
    raw_file_path: str
    raw_file_sha256: str
    raw_locator: str
    source_record_id: str
    parent_record_id: str | None = None

    @property
    def raw_row_key(self) -> tuple[str, str, str, str]:
        return (
            self.accession_a,
            self.accession_b,
            self.field_3,
            self.assay_text,
        )

    @property
    def row_key(self) -> tuple[str, str, str, str]:
        """Return the provider row key after boundary-whitespace normalization."""
        return tuple(value.strip() for value in self.raw_row_key)

    @property
    def stringent_file(self) -> bool:
        return self.dataset.endswith("_stringent")


def split_accession(accession: str) -> tuple[str, str | None]:
    """Preserve the exact accession while separating an explicit numeric isoform."""
    match = _ISOFORM_RE.fullmatch(accession)
    if not match:
        return accession, None
    return match.group(1), accession


def parse_mi_accession(text: str) -> str | None:
    match = _MI_RE.match(text.strip())
    return match.group(1) if match else None


def _dataset_semantics(dataset: str) -> tuple[str, str, bool]:
    if dataset in {"manual", "manual_stringent"}:
        return "manual_experimental_negative", "manual", False
    if dataset in {"pdb", "pdb_stringent"}:
        return "structure_derived_noncontact", "pdb", True
    raise ValueError(f"Unsupported Negatome dataset: {dataset}")


def parse_negatome_file(
    *,
    path: Path,
    dataset: str,
    raw_file_path: str,
    raw_file_sha256: str,
) -> list[NegatomeRow]:
    """Parse one complete provider file without collapsing duplicate rows."""
    evidence_family, parent_dataset, has_header = _dataset_semantics(dataset)
    rows: list[NegatomeRow] = []
    with path.open("rt", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        if has_header:
            try:
                header = next(reader)
            except StopIteration as exc:
                raise ValueError(f"Empty Negatome PDB file: {path}") from exc
            if header != _PDB_HEADER:
                raise ValueError(f"Unexpected Negatome PDB header: {header!r}")
        for ordinal, fields in enumerate(reader, start=1):
            if len(fields) != 4 or any(field == "" for field in fields):
                raise ValueError(
                    f"{dataset} row {ordinal} must contain four nonempty fields"
                )
            accession_a, accession_b, field_3, assay_text = fields
            if evidence_family == "manual_experimental_negative":
                if field_3.isdigit():
                    publication_ids = (f"pubmed:{field_3}",)
                elif re.fullmatch(r"PMC\d+", field_3):
                    publication_ids = (f"pmc:{field_3}",)
                else:
                    raise ValueError(
                        f"Invalid PubMed identifier at {dataset}:{ordinal}"
                    )
                pdb_ids: tuple[str, ...] = ()
            else:
                publication_ids = ()
                pdb_ids = tuple(
                    value.strip().lower()
                    for value in field_3.split(",")
                    if value.strip()
                )
                if not pdb_ids:
                    raise ValueError(f"Missing PDB identifier at {dataset}:{ordinal}")
            line_number = ordinal + (1 if has_header else 0)
            rows.append(
                NegatomeRow(
                    dataset=dataset,
                    evidence_family=evidence_family,
                    parent_dataset=parent_dataset,
                    ordinal=ordinal,
                    accession_a=accession_a,
                    accession_b=accession_b,
                    field_3=field_3,
                    assay_text=assay_text,
                    publication_ids=publication_ids,
                    pdb_ids=pdb_ids,
                    assay_mi_ac=parse_mi_accession(assay_text),
                    raw_file_path=raw_file_path,
                    raw_file_sha256=raw_file_sha256,
                    raw_locator=f"line:{line_number}",
                    source_record_id=stable_id(
                        "negatome-source",
                        dataset,
                        ordinal,
                        accession_a,
                        accession_b,
                        field_3,
                        assay_text,
                    ),
                )
            )
    return rows


def reconcile_parent_and_stringent_rows(
    rows_by_dataset: dict[str, list[NegatomeRow]],
) -> tuple[list[NegatomeRow], list[NegatomeRow], dict[str, Any]]:
    """Prove exact multiset subset membership and link every physical source row."""
    required = {"manual", "manual_stringent", "pdb", "pdb_stringent"}
    if set(rows_by_dataset) != required:
        raise ValueError(
            f"Negatome dataset set differs: {sorted(rows_by_dataset)} != {sorted(required)}"
        )

    linked_by_dataset: dict[str, list[NegatomeRow]] = {}
    parent_rows: list[NegatomeRow] = []
    metrics: dict[str, Any] = {"datasets": {}}
    for parent_dataset in ("manual", "pdb"):
        stringent_dataset = f"{parent_dataset}_stringent"
        parents: list[NegatomeRow] = []
        parents_by_key: dict[tuple[str, str, str, str], list[NegatomeRow]] = (
            defaultdict(list)
        )
        for row in rows_by_dataset[parent_dataset]:
            parent_id = stable_id(
                "negatome-parent",
                parent_dataset,
                row.ordinal,
                *row.row_key,
            )
            linked = replace(row, parent_record_id=parent_id)
            parents.append(linked)
            parents_by_key[linked.row_key].append(linked)

        occurrence: Counter[tuple[str, str, str, str]] = Counter()
        stringents: list[NegatomeRow] = []
        for row in rows_by_dataset[stringent_dataset]:
            occurrence[row.row_key] += 1
            candidates = parents_by_key.get(row.row_key, [])
            index = occurrence[row.row_key] - 1
            if index >= len(candidates):
                raise ValueError(
                    f"{stringent_dataset} is not an exact multiset subset at row {row.ordinal}"
                )
            stringents.append(
                replace(row, parent_record_id=candidates[index].parent_record_id)
            )

        parent_counter = Counter(row.row_key for row in parents)
        stringent_counter = Counter(row.row_key for row in stringents)
        excess = {
            key: count - parent_counter[key]
            for key, count in stringent_counter.items()
            if count > parent_counter[key]
        }
        if excess:
            raise ValueError(f"Stringent multiset contains excess rows: {excess}")

        raw_parent_counter = Counter(row.raw_row_key for row in parents)
        raw_stringent_counter = Counter(row.raw_row_key for row in stringents)
        raw_excess_count = sum((raw_stringent_counter - raw_parent_counter).values())

        linked_by_dataset[parent_dataset] = parents
        linked_by_dataset[stringent_dataset] = stringents
        parent_rows.extend(parents)
        metrics["datasets"][parent_dataset] = {
            "parent_rows": len(parents),
            "stringent_rows": len(stringents),
            "parent_unique_normalized_rows": len(parent_counter),
            "stringent_unique_normalized_rows": len(stringent_counter),
            "parent_duplicate_rows": len(parents) - len(parent_counter),
            "stringent_duplicate_rows": len(stringents) - len(stringent_counter),
            "stringent_normalized_multiset_subset": True,
            "normalization": "strip_boundary_whitespace_per_field_only",
            "stringent_raw_exact_multiset_subset": raw_excess_count == 0,
            "stringent_raw_exact_excess_rows": raw_excess_count,
        }

    all_rows = [
        row
        for dataset in ("manual", "manual_stringent", "pdb", "pdb_stringent")
        for row in linked_by_dataset[dataset]
    ]
    metrics["physical_source_rows"] = len(all_rows)
    metrics["canonical_parent_records"] = len(parent_rows)
    return all_rows, parent_rows, metrics


def stringent_links(rows: Iterable[NegatomeRow]) -> dict[str, str]:
    links: dict[str, str] = {}
    for row in rows:
        if not row.stringent_file:
            continue
        if row.parent_record_id is None:
            raise ValueError("Stringent row has no parent link")
        if row.parent_record_id in links:
            raise ValueError(
                f"Parent record has multiple stringent links: {row.parent_record_id}"
            )
        links[row.parent_record_id] = row.source_record_id
    return links


def source_row_to_record(row: NegatomeRow) -> dict[str, Any]:
    if row.parent_record_id is None:
        raise ValueError("Negatome row has not been linked to a parent record")
    base_a, isoform_a = split_accession(row.accession_a)
    base_b, isoform_b = split_accession(row.accession_b)
    manual = row.evidence_family == "manual_experimental_negative"
    missing = [
        "construct_a",
        "construct_b",
        "orientation_a",
        "orientation_b",
        "source_species_a",
        "source_species_b",
        "experimental_conditions",
        "assay_batch",
        "repeat",
    ]
    if manual:
        missing.extend(["technical_evaluability", "technical_state"])
        attempted_state = "source_asserted_experiment_performed"
        evaluability_state = "not_reported"
        technical_state = "not_reported"
        observation_state = "source_asserted_conditional_negative"
    else:
        missing.append("publication")
        attempted_state = "not_applicable_structure_derived"
        evaluability_state = "not_applicable_structure_derived"
        technical_state = "not_applicable_structure_derived"
        observation_state = "structure_derived_noncontact"
    return {
        "source_record_id": row.source_record_id,
        "parent_record_id": row.parent_record_id,
        "source_dataset": row.dataset,
        "evidence_family": row.evidence_family,
        "parent_dataset": row.parent_dataset,
        "source_record_ordinal": row.ordinal,
        "source_accession_a": row.accession_a,
        "source_accession_b": row.accession_b,
        "source_base_accession_a": base_a,
        "source_base_accession_b": base_b,
        "source_isoform_id_a": isoform_a,
        "source_isoform_id_b": isoform_b,
        "publication_ids": list(row.publication_ids),
        "pdb_ids": list(row.pdb_ids),
        "assay_mi_ac": row.assay_mi_ac,
        "assay_text": row.assay_text,
        "construct_a_json": None,
        "construct_b_json": None,
        "orientation_a": None,
        "orientation_b": None,
        "orientation_state": "source_row_order_only_no_experimental_roles",
        "source_taxid_a": None,
        "source_taxid_b": None,
        "source_species_name_a": None,
        "source_species_name_b": None,
        "experimental_conditions_json": None,
        "attempted_state": attempted_state,
        "evaluability_state": evaluability_state,
        "technical_state": technical_state,
        "observation_state": observation_state,
        "stringent_file": row.stringent_file,
        "raw_file_path": row.raw_file_path,
        "raw_file_sha256": row.raw_file_sha256,
        "raw_locator": row.raw_locator,
        "license_id": "UNSPECIFIED-NO-REDISTRIBUTION",
        "redistribution_tier": "internal_only_no_record_level_redistribution",
        "universal_nonbinding_asserted": False,
        "label_authorized": False,
        "source_fields_json": canonical_json(
            {
                "field_3": row.field_3,
                "provider_dataset": row.dataset,
                "source_row_order_preserved": True,
            }
        ),
        "missingness_json": canonical_json(
            {field: "not_reported" for field in missing}
        ),
    }
