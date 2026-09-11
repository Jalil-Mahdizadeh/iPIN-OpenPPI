"""Separate pandas-based structural reference check and prior-closure audit.

Same-author numerical checking, not external review or assay validation.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path("/work")
    run = root / "artifacts/runs/direct_binary_feasibility_v1"
    source = run / "raw/organized_code_screen_processing"
    out = root / "artifacts/validation/direct_binary_feasibility_v1/REFERENCE_VALIDATION.json"
    result_path = root / "artifacts/results/direct_binary_feasibility_v1/SOURCE_STRUCTURE.json"
    result = json.loads(result_path.read_bytes())
    meta = pd.read_csv(source / "protein_metadata/leukocyte_proteins_final.csv", keep_default_na=False)
    names = meta.Symbol1 + meta.Symbol2.map(lambda x: "-" + x if x else "")
    for file, key in (("leuk_interactome_180928.csv", "primary_matrix"),
                      ("Leukocyte_2ndary_screen_data.csv", "secondary_matrix")):
        table = pd.read_csv(source / file, index_col=0)
        expected = result[key]
        assert list(table.shape) == [expected["rows"], expected["measurement_columns"]]
        assert int(table.size) == expected["cells_including_controls"]
        assert int(table.isna().sum().sum()) == expected["blank_cells_including_controls"]
        assert int(table.notna().sum().sum()) == expected["finite_cells_including_controls"]
        rect = table.loc[table.index.isin(names), table.columns.isin(names)]
        assert rect.size == expected["exact_alias_rectangle_cells_not_QC_filtered"]
        assert int(rect.notna().sum().sum()) == expected["exact_alias_rectangle_finite_cells_not_QC_filtered"]
    m = result["protein_metadata"]
    assert len(meta) == m["rows"]
    assert meta.Screen_ID.nunique() == m["unique_screen_ids"]
    assert names.nunique() == m["unique_source_symbol_aliases"]
    assert int(meta.Symbol2.ne("").sum()) == m["rows_with_second_chain"]
    assert int(meta.AA_seq1.ne("").sum()) == m["rows_with_nonblank_AA_seq1"]
    assert int(meta.AA_seq2.ne("").sum()) == m["rows_with_nonblank_AA_seq2"]
    terminal_stop = meta.AA_seq1.str.fullmatch("[ACDEFGHIKLMNPQRSTVWY]+\\*")
    canonical_or_stop = meta.AA_seq1.str.fullmatch("[ACDEFGHIKLMNPQRSTVWY]+\\*?")
    assert int(terminal_stop.sum()) == m["rows_with_first_chain_noncanonical_AA_characters"]
    assert int(canonical_or_stop.sum()) == m["rows_with_nonblank_AA_seq1"]
    for filename, table_result in result["QC_tables"].items():
        table = pd.read_csv(source / "protein_metadata" / filename)
        assert len(table) == table_result["rows"]
        for key, counts in table_result["numeric_fields"].items():
            values = pd.to_numeric(table[key], errors="raise")
            assert int(values.notna().sum()) == counts["finite"]
            assert int(values.isna().sum()) == counts["blank"]
            assert int(values.le(0).sum()) == counts["nonpositive_finite"]
    manifest = json.loads((run / "SOURCE_MANIFEST.json").read_bytes())
    for record in manifest["files"]:
        path = root / record["path"]
        assert sha(path) == record["sha256"]
        assert path.stat().st_size == record["bytes"]
    assert sum(r["bytes"] for r in manifest["files"]) == result["total_bytes"]
    prior_closures = []
    for name in ("within_anchor_partner_specificity_v1", "homology_source_challenge_v1",
                 "external_bioplex_challenge_v1", "composition_order_challenge_v1"):
        registry = root / f"artifacts/results/{name}/ARTIFACT_REGISTRY.json"
        prior = json.loads(registry.read_bytes())
        entries = prior["artifacts"]
        for entry in entries:
            path = root / entry["path"]
            assert path.resolve().is_relative_to(root), path
            assert sha(path) == entry["sha256"], path
            assert path.stat().st_size == entry["bytes"], path
        prior_closures.append({"path": str(registry.relative_to(root)), "sha256": sha(registry),
                               "registered_files_unchanged": len(entries)})
    verification = {
        "verified_utc": datetime.now(timezone.utc).isoformat(), "status": "pass",
        "validator_sha256": sha(Path(__file__)), "source_structure_sha256": sha(result_path),
        "independent_implementation": "pandas reference versus stdlib csv inventory",
        "same_author_not_external_review": True,
        "both_matrix_shapes_cells_missingness_alias_rectangles_checked": True,
        "protein_and_numeric_QC_counts_checked": True,
        "raw_files_SHA256_checked": len(manifest["files"]),
        "construct_sequence_clarification": {
            "first_chain_sequences_with_single_terminal_stop_marker": int(terminal_stop.sum()),
            "nonblank_first_chain_sequences_otherwise_canonical_AA": int(canonical_or_stop.sum()),
            "interpretation": "The 82 noncanonical-character rows are terminal stop markers, not 82 corrupt constructs. No sequence edits made; tags/maturation and complex identity still require assay-specific reconciliation.",
        },
        "prior_closures": prior_closures,
        "assay_P_N_semantics_or_matched_support_validated": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x") as stream:
        json.dump(verification, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
