"""Freeze a published assay-comparison mapping for the reference-only study."""
import csv
import gzip
import json
import math
import os
import warnings
import zipfile
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path

import openpyxl

from prepare import OUT, ROOT, record, require, verify, write_csv, write_gzip, write_json


def read_table(name):
    with (OUT / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def identifier(value):
    if isinstance(value, (int, float)):
        require(float(value).is_integer(), "Noninteger gene identifier")
        return str(int(value))
    return str(value).strip()


def main():
    require(bool(os.environ.get("APPTAINER_CONTAINER")), "Use the accepted data image")
    names = ["panels.csv", "selected_sequences.json.gz", "assay_comparison.csv",
             "comparison_mapping_audit.csv", "PANEL_SELECTION.json", "COMPARISON_VALIDATION.json"]
    require(not any((OUT / n).exists() for n in names), "Refusing to replace comparison outputs")
    preparation = json.loads((OUT / "SOURCE_PREPARATION.json").read_text())
    for item in preparation["outputs"]:
        verify(item)
    sources = json.loads((OUT / "COMPARISON_SOURCES.json").read_text())
    for item in sources["sources"]:
        verify(item)
    with gzip.open(OUT / "published_evidence.json.gz", "rt") as handle:
        evidence = json.load(handle)
    with gzip.open(OUT / "published_sequences.json.gz", "rt") as handle:
        sequences = json.load(handle)
    require({p["taxid"] for p in sequences.values()} == {9606, 559292}, "Unexpected sequence taxon")
    by_evidence = defaultdict(set)
    for row in evidence:
        by_evidence[row["interaction_id"]].add(row["pair_id"])
    archive = ROOT / next(r["path"] for r in sources["sources"] if r["path"].endswith(".zip"))
    with zipfile.ZipFile(archive) as zipped:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Unknown extension is not supported.*")
            ev2 = list(openpyxl.load_workbook(BytesIO(zipped.read("MSB-12-865-s004.xlsx")),
                                            read_only=True, data_only=True).active.values)
            ev7 = list(openpyxl.load_workbook(BytesIO(zipped.read("MSB-12-865-s009.xlsx")),
                                            read_only=True, data_only=True).active.values)
    require(ev2[1][0] == "Yeast DB-X" and ev2[1][2] == "Human AD-Y", "Table EV2 schema changed")
    require(ev7[1][0] == "Yeast protein" and ev7[1][1] == "Human protein" and
            str(ev7[1][4]).strip() == "Final score" and ev7[1][5] == "Call", "Table EV7 schema changed")
    mapping = defaultdict(set)
    evidence_ids = defaultdict(set)
    for row in ev2[2:]:
        if not row[0] or not row[2]:
            continue
        key = (identifier(row[0]), identifier(row[2]))
        for accession in str(row[4] or "").split(","):
            accession = accession.strip()
            evidence_ids[key].add(accession)
            mapping[key].update(by_evidence.get(accession, set()))
    published = read_table("published_pairs.csv")
    by_pair = {r["pair_id"]: (i, r) for i, r in enumerate(published)}
    audit, comparison, selected_pair_ids = [], [], set()
    for number, row in enumerate(ev7[2:], 3):
        if not row[0] or not row[1]:
            continue
        key = (identifier(row[0]), identifier(row[1]))
        call = str(row[5]).strip().lower()
        score = float(row[4])
        require(call in {"yes", "no"} and math.isfinite(score), f"Invalid assay outcome at row {number}")
        hits = mapping[key]
        reason = "included" if len(hits) == 1 else "ambiguous_sequence_pair" if hits else "no_verified_sequence_pair_mapping"
        audit.append({"ev7_row": number, "yeast_gene": key[0], "human_entrez_gene": key[1],
                      "published_call": call, "published_assay_score": score,
                      "candidate_sequence_pairs": len(hits), "decision": reason,
                      "ev2_intact_identifiers": ";".join(sorted(evidence_ids[key])),
                      "candidate_pair_ids": ";".join(sorted(hits))})
        if reason != "included":
            continue
        pair_id = next(iter(hits))
        require(pair_id not in selected_pair_ids, "Repeated assay sequence pair requires explicit handling")
        selected_pair_ids.add(pair_id)
        index, pair = by_pair[pair_id]
        comparison.append({"row_index": index, "pair_id": pair_id, "ev7_row": number,
                           "yeast_gene": key[0], "human_entrez_gene": key[1],
                           "confirmed": call == "yes", "published_call": call,
                           "published_assay_score": score,
                           "query_sequence_sha256": pair["reference_sequence_sha256"],
                           "partner_sequence_sha256": pair["human_sequence_sha256"]})
    require({r["confirmed"] for r in comparison} == {True, False}, "Both assay outcomes are required")
    selected = {}
    panels = []
    for i, pair in enumerate(published):
        require(pair["reference_taxid"] == "559292" and pair["human_taxid"] == "9606", "Unexpected pair taxon")
        left, right = pair["reference_sequence_sha256"], pair["human_sequence_sha256"]
        for taxid, digest in ((559292, left), (9606, right)):
            protein = sequences[f"{taxid}:{digest}"]
            if digest in selected:
                require(selected[digest] == protein["sequence"], "Conflicting sequence digest")
            selected[digest] = protein["sequence"]
        panels.append({"row_index": i, "pair_id": pair["pair_id"], "species": "human_yeast_reference",
                       "query_taxid": 559292, "partner_taxid": 9606, "label": "P",
                       "query_sequence_sha256": left, "partner_sequence_sha256": right,
                       "has_published_assay_outcome": pair["pair_id"] in selected_pair_ids})
    write_csv(OUT / "panels.csv", panels)
    write_csv(OUT / "assay_comparison.csv", comparison)
    write_csv(OUT / "comparison_mapping_audit.csv", audit)
    write_gzip(OUT / "selected_sequences.json.gz", selected)
    summary = {"published_assay_rows": len(audit), "published_calls": dict(Counter(r["published_call"] for r in audit)),
               "included_assay_rows": len(comparison), "included_calls": dict(Counter(r["published_call"] for r in comparison)),
               "exclusion_reasons": dict(Counter(r["decision"] for r in audit if r["decision"] != "included")),
               "excluded_calls": dict(Counter(r["published_call"] for r in audit if r["decision"] != "included")),
               "comparison_endpoint": "Published orthogonal-assay confirmation among previously reported interactions",
               "unconfirmed_interpreted_as_biological_negative": False}
    write_json(OUT / "PANEL_SELECTION.json", {
        "pairs": len(panels), "unique_sequences": len(selected), "comparison": summary,
        "published_pairs_only": True, "model_scores_read": False,
        "inputs": [record(OUT / p) for p in ("COMPARISON_SOURCES.json", "SOURCE_PREPARATION.json", "EVALUATION_PROTOCOL.md")],
        "script": record(Path(__file__)),
        "outputs": [record(OUT / p) for p in names[:4]],
    })
    # A separate direct worksheet parse checks stored numeric/call/row alignment.
    for item in comparison:
        raw = ev7[item["ev7_row"] - 1]
        require(item["published_assay_score"] == float(raw[4]) and item["published_call"] == str(raw[5]).strip().lower(),
                "Exported assay outcome differs from the worksheet")
        pair = panels[item["row_index"]]
        require(pair["pair_id"] == item["pair_id"] and pair["query_sequence_sha256"] == item["query_sequence_sha256"] and
                pair["partner_sequence_sha256"] == item["partner_sequence_sha256"], "Assay pair alignment mismatch")
    write_json(OUT / "COMPARISON_VALIDATION.json", {"status": "passed", "summary": summary,
        "selection": record(OUT / "PANEL_SELECTION.json"), "same_mapping_rule_for_both_outcomes": True,
        "all_scoring_pairs_present_in_verified_published_input": True,
        "all_selected_endpoints_have_exact_reference_or_human_taxonomy": True,
        "model_scores_read": False})
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
