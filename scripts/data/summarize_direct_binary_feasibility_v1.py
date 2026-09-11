"""Exploratory structural checks on the allowlisted SAVEXIS snapshot only.

Never interpret a numeric cell, curated reference or missing cell as a new P/N
label. This source triage does not reproduce the source's scientific pipeline.
"""
from __future__ import annotations

import csv
import io
import json
import math
from collections import Counter
from pathlib import Path

from audit_direct_binary_feasibility_v1 import digest, git_blob, json_bytes, write_new


def read_csv(path: Path) -> list[list[str]]:
    data = path.read_bytes()
    try:
        decoded = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = data.decode("cp1252")
    return list(csv.reader(io.StringIO(decoded)))


def records(path: Path) -> list[dict]:
    rows = read_csv(path)
    assert all(len(row) == len(rows[0]) for row in rows[1:])
    return [dict(zip(rows[0], row, strict=True)) for row in rows[1:]]


def finite(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def matrix_summary(rows: list[list[str]], aliases: set[str]) -> dict:
    baits = [row[0] for row in rows[1:]]
    preys = rows[0][1:]
    assert len(set(preys)) == len(preys)
    assert all(len(row) == len(preys) + 1 for row in rows[1:])
    values = [value for row in rows[1:] for value in row[1:]]
    allowed_rows = [row for row in rows[1:] if row[0] in aliases]
    allowed_cols = [i + 1 for i, prey in enumerate(preys) if prey in aliases]
    return {
        "rows": len(baits), "measurement_columns": len(preys),
        "cells_including_controls": len(values),
        "finite_cells_including_controls": sum(map(finite, values)),
        "blank_cells_including_controls": sum(not value.strip() for value in values),
        "other_nonfinite_cells": sum(bool(v.strip()) and not finite(v) for v in values),
        "duplicate_bait_axis_occurrences": len(baits) - len(set(baits)),
        "unique_baits_exactly_in_metadata_aliases": len(set(baits) & aliases),
        "unique_preys_exactly_in_metadata_aliases": len(set(preys) & aliases),
        "bait_axis_occurrences_not_in_metadata_aliases": sum(b not in aliases for b in baits),
        "prey_axis_occurrences_not_in_metadata_aliases": sum(p not in aliases for p in preys),
        "exact_alias_rectangle_cells_not_QC_filtered": len(allowed_rows) * len(allowed_cols),
        "exact_alias_rectangle_finite_cells_not_QC_filtered": sum(
            finite(row[col]) for row in allowed_rows for col in allowed_cols),
        "not_a_negative_label_count": True,
    }


def main() -> None:
    root = Path("/work")
    run = root / "artifacts/runs/direct_binary_feasibility_v1"
    manifest = json.loads((run / "SOURCE_MANIFEST.json").read_bytes())
    for record in manifest["files"]:
        data = (root / record["path"]).read_bytes()
        assert len(data) == record["bytes"]
        assert digest(data) == record["sha256"]
        assert git_blob(data) == record["git_blob_sha1"]
    source = run / "raw/organized_code_screen_processing"
    metadata = records(source / "protein_metadata/leukocyte_proteins_final.csv")
    alias_counts = Counter(r["Symbol1"] + ("-" + r["Symbol2"] if r["Symbol2"] else "") for r in metadata)
    aliases = set(alias_counts)
    summary = {
        "scope": "structural_feasibility_only_no_labels_no_scores",
        "source_commit": manifest["source_commit"],
        "files": len(manifest["files"]), "total_bytes": manifest["total_bytes"],
        "source_manifest_sha256": digest((run / "SOURCE_MANIFEST.json").read_bytes()),
        "summary_script_sha256": digest(Path(__file__).read_bytes()),
        "protein_metadata": {
            "rows": len(metadata), "unique_screen_ids": len({r["Screen_ID"] for r in metadata}),
            "unique_source_symbol_aliases": len(aliases),
            "aliases_with_multiple_metadata_rows": sum(n > 1 for n in alias_counts.values()),
            "rows_with_second_chain": sum(bool(r["Symbol2"]) for r in metadata),
            "rows_with_nonblank_AA_seq1": sum(bool(r["AA_seq1"]) for r in metadata),
            "rows_with_nonblank_AA_seq2": sum(bool(r["AA_seq2"]) for r in metadata),
            "rows_with_first_chain_noncanonical_AA_characters": sum(
                bool(r["AA_seq1"]) and bool(set(r["AA_seq1"]) - set("ACDEFGHIKLMNPQRSTVWY"))
                for r in metadata),
            "rows_with_blank_first_chain_plasmid_ID": sum(not r["Plasmid_ID_BLH1"] for r in metadata),
            "exact_assayed_construct_validation": "not_completed",
        },
        "primary_matrix": matrix_summary(read_csv(source / "leuk_interactome_180928.csv"), aliases),
        "secondary_matrix": matrix_summary(read_csv(source / "Leukocyte_2ndary_screen_data.csv"), aliases),
        "QC_tables": {},
        "gates": {
            "public_direct_assay_source": "candidate_pass",
            "raw_measurement_opportunity": "available_with_axis_reconciliation_needed",
            "evaluable_P_N_definition": "unresolved_source_processing_and_missingness",
            "exact_construct_and_QC_mapping": "partial_not_qualified",
            "matched_P_N_support": "not_assessed_upstream_semantics_not_qualified",
            "actual_training_homology_interolog_exposure": "not_assessed",
            "untouched_precision_adequate_confirmation": "not_established",
            "resume_current_model_track": "no_go",
            "separate_SAVEXIS_data_reconstruction_pilot": "conditional_candidate_not_started",
        },
        "new_fits": 0, "new_embeddings": 0, "model_scores": 0, "P_N_labels_created": 0,
    }
    for filename in ("bradford_measurements.csv", "leukocyte_screen_plates.csv", "followup_plasmids_FINAL.csv"):
        table = records(source / "protein_metadata" / filename)
        summary["QC_tables"][filename] = {
            "rows": len(table),
            "numeric_fields": {key: {
                "finite": sum(finite(row[key]) for row in table),
                "blank": sum(not row[key].strip() for row in table),
                "nonpositive_finite": sum(finite(row[key]) and float(row[key]) <= 0 for row in table),
            } for key in ("conc_ngul", "final_ngul", "band_intensity") if key in table[0]},
        }
    out = root / "artifacts/results/direct_binary_feasibility_v1/SOURCE_STRUCTURE.json"
    write_new(out, json_bytes(summary))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
