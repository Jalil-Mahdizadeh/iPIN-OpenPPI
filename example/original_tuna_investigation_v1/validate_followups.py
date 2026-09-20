"""Check follow-up provenance, alignment summaries, and key training-source claims."""
from __future__ import annotations

import csv
import os
from pathlib import Path
import numpy as np

from investigate import ROOT, OUT, PARENT, check_inputs, read, record, sha, table, write_json


def main():
    assert os.environ.get("APPTAINER_CONTAINER")
    check_inputs()
    freeze = read(OUT / "HOMOLOGY_INPUT_FREEZE.json")
    for item in [freeze[k] for k in ("primary_freeze", "protocol", "script", "binary")] + freeze["local_inputs"]:
        assert sha(ROOT / item["path"]) == item["sha256"]
    matchfile = OUT / "homology_local/matches.tsv"
    assert sha(matchfile) == read(OUT / "HOMOLOGY_RUN.json")["matches"]["sha256"]
    fields = "query,target,fident,alnlen,qstart,qend,qlen,tstart,tend,tlen,evalue,bits,qcov,tcov".split(",")
    with matchfile.open() as stream:
        matches = list(csv.DictReader(stream, fieldnames=fields, delimiter="\t"))
    coverage_discrepancies = 0
    for r in matches:
        qcov = (int(r["qend"]) - int(r["qstart"]) + 1) / int(r["qlen"])
        tcov = (int(r["tend"]) - int(r["tstart"]) + 1) / int(r["tlen"])
        assert abs(qcov - float(r["qcov"])) <= .00051 and abs(tcov - float(r["tcov"])) <= .00051
        coverage_discrepancies += ((qcov >= .8 and tcov >= .8) != (float(r["qcov"]) >= .8 and float(r["tcov"]) >= .8))
    assert coverage_discrepancies == 0
    upstream = ROOT / "benchmark/tuna/upstream/TUnA/data/processed/bernett"
    sources = {}
    for role, stem in (("training", "Intra1"), ("validation", "Intra0")):
        source_rows = list(csv.reader((upstream / f"{stem}_interaction_1500_or_less.tsv").open(), delimiter="\t"))
        endpoints = {a for r in source_rows for a in r[:2]}
        sources[role] = (source_rows, endpoints)
    alignment_rows = table(OUT / "sequence_relative_matches.csv")
    for row in alignment_rows:
        hits = [r for r in matches if r["query"] == row["query_uniprot"] and r["target"] in sources[row["source"]][1]]
        if row["scope"] != "local":
            hits = [r for r in hits if float(r["qcov"]) >= .8 and float(r["tcov"]) >= .8]
        assert int(row["reported_matches"]) == len(hits)
        if hits:
            assert float(row["bits"]) == max(float(r["bits"]) for r in hits)
            assert any(all(row[k] == r[k] for k in fields if k != "query") for r in hits)
        else:
            assert row["target"] == ""
    pair_rows = table(OUT / "nominated_and_relative_pair_exposure.csv")
    for row in pair_rows:
        for role, (source_rows, _) in sources.items():
            labels = {c for a, b, c in source_rows if {a, b} == {row["query_accession"], row["partner_accession"]}}
            assert row[f"original_{role}_labels"] == ";".join(sorted(labels))
    audited_inputs = read(OUT / "RELATIVE_PAIR_AUDIT_INPUTS.json")
    for item in [audited_inputs["script"], *audited_inputs["inputs"]]:
        assert sha(ROOT / item["path"]) == item["sha256"]
    folder = ROOT / "benchmark/tuna/data"
    sequences = read(folder / "sequences.json")
    egfr_relatives = [r for r in pair_rows if r["target"] == "EGFR" and r["pair_kind"] == "best_training_local_match"]
    assert len(egfr_relatives) == 3 and all(r["original_training_labels"] == "1" for r in egfr_relatives)
    # Direct array masks independently confirm the central absence claim.
    for name in ("training.npz", "development_00.npz", "development_01.npz", "development_02.npz"):
        with np.load(folder / name, allow_pickle=False) as data:
            arrays = [(data["p_a"], data["p_b"]), (data["u_a"], data["u_b"])] if name == "training.npz" else [(data["a"], data["b"])]
            for row in egfr_relatives:
                a = [i for i, accs in enumerate(sequences["accessions"]) if row["query_accession"] in accs]
                b = [i for i, accs in enumerate(sequences["accessions"]) if row["partner_accession"] in accs]
                for left, right in arrays:
                    assert not ((np.isin(left, a) & np.isin(right, b)) | (np.isin(left, b) & np.isin(right, a))).any()
    ctx = {r["accession"]: r for r in table(OUT / "ipin_training_endpoint_context.csv")}
    with np.load(folder / "training.npz", allow_pickle=False) as data:
        for acc in ("P00533", "P21860", "P29353", "Q6S5L8"):
            ids = {i for i, accs in enumerate(sequences["accessions"]) if acc in accs}
            assert ids
            assert not any(np.isin(data[key], list(ids)).any() for key in ("p_a", "p_b", "u_a", "u_b"))
            assert int(ctx[acc]["TRAIN_P_rows"]) == int(ctx[acc]["TRAIN_U_rows"]) == 0
    write_json("FOLLOWUP_VALIDATION.json", dict(passed=True, alignment_summary_rows=len(alignment_rows),
        local_alignment_rows=len(matches), coverage_threshold_rounding_discrepancies=coverage_discrepancies,
        original_source_pair_label_checks=len(pair_rows) * 2, EGFR_analogous_training_positive_pairs_verified=3,
        EGFR_analogous_pairs_absent_from_ipin_TRAIN_and_development=True,
        EGFR_ERBB3_SHC1_SHC4_absent_from_actual_retraining_TRAIN_rows=True,
        script=record(Path(__file__)), frozen_inputs_unchanged=True, protected_test_records_read=False))
    print("Follow-up validation passed", flush=True)


if __name__ == "__main__":
    main()
