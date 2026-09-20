"""Post hoc audit of nominated pairs and their best local TRAIN sequence matches.

Motivation: after the fixed homology search, all three EGFR pairs had analogous
positive pairs in original TRAIN. Audit every nominated pair's best local TRAIN
matches, selected by alignment bits rather than PPI label or model score. Also
check these pairs in frozen iPIN TRAIN/development only. This does not establish
which training examples causally influenced either fitted predictor.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path

import numpy as np

from investigate import ROOT, OUT, PARENT, check_inputs, read, record, sha, table, write_csv, write_json
from original_exposure import load


def main():
    assert os.environ.get("APPTAINER_CONTAINER")
    check_inputs()
    lookup, _ = load(ROOT)
    matches = {(r["query_uniprot"]): r for r in table(OUT / "sequence_relative_matches.csv")
               if r["source"] == "training" and r["scope"] == "local"}
    candidates = []
    for r in table(PARENT / "all_twelve_targets_scores.csv"):
        if r["class"] != "P":
            continue
        for kind in ("nominated", "best_training_local_match"):
            a = r["query_uniprot"] if kind == "nominated" else matches[r["query_uniprot"]]["target"]
            b = r["partner_uniprot"] if kind == "nominated" else matches[r["partner_uniprot"]]["target"]
            result = dict(target=r["query_gene"], partner_gene=r["partner_gene"], pair_kind=kind, query_accession=a, partner_accession=b)
            for role, (by_acc, _) in lookup.items():
                result[f"original_{role}_labels"] = ";".join(sorted(by_acc.get(tuple(sorted((a, b))), set()))) if a and b else ""
            result.update({key: False for key in ("ipin_TRAIN_P", "ipin_TRAIN_U", "ipin_DEV_P", "ipin_DEV_U")})
            candidates.append(result)
    folder = ROOT / "benchmark/tuna/data"
    names = ("sequences.json", "training.npz", "development_00.npz", "development_01.npz", "development_02.npz")
    manifest = {Path(r["path"]).name: r["sha256"] for r in read(folder / "DATA_MANIFEST.json")["outputs"]}
    for name in names:
        assert sha(folder / name) == manifest[name]
    freeze = dict(at_utc=datetime.now(timezone.utc).isoformat(), exploratory_after_homology=True,
                  script=record(Path(__file__)), inputs=[record(folder / name) for name in names],
                  selection="Each endpoint's maximum-bits TRAIN local match; no PPI-label selection",
                  original_test_or_ipin_test_pairs_read=False)
    write_json("RELATIVE_PAIR_AUDIT_INPUTS.json", freeze)
    sequences = read(folder / "sequences.json")
    ids = defaultdict(set)
    for i, (h, accessions) in enumerate(zip(sequences["sha256"], sequences["accessions"], strict=True)):
        for key in [h, *accessions]:
            ids[key].add(i)
    reference, acc = {}, None
    for line in (ROOT / "benchmark/tuna/upstream/TUnA/data/raw/bernett/human_swissprot_oneliner.fasta").read_text().splitlines():
        if line.startswith(">"):
            acc = line[1:].split()[0]
            reference[acc] = ""
        elif line.strip():
            reference[acc] += line.strip()
    reference.update({a: r["sequence"] for a, r in read(PARENT / "uniprot_sequences.json")["records"].items()
                      if a not in reference})
    index_pairs = []
    for c in candidates:
        endpoints = []
        for key in ("query_accession", "partner_accession"):
            acc = c[key]
            seqhash = hashlib.sha256(reference[acc].encode()).hexdigest() if acc else ""
            endpoints.append(ids[acc] | ids[seqhash])
        index_pairs.append(endpoints)
    for name in names[1:]:
        with np.load(folder / name, allow_pickle=False) as data:
            if name == "training.npz":
                groups = [(key, data[p + "_a"], data[p + "_b"]) for key, p in (("ipin_TRAIN_P", "p"), ("ipin_TRAIN_U", "u"))]
            else:
                groups = [(key, data["a"][data["positive"] == value], data["b"][data["positive"] == value])
                          for key, value in (("ipin_DEV_P", True), ("ipin_DEV_U", False))]
            for key, left, right in groups:
                # Encode unordered index pairs for exact membership, avoiding
                # opening any test table or retaining unrelated pair identities.
                encoded = set((np.minimum(left, right).astype(np.int64) * len(sequences["sha256"]) + np.maximum(left, right)).tolist())
                for candidate, (a, b) in zip(candidates, index_pairs, strict=True):
                    candidate[key] |= any(min(x, y) * len(sequences["sha256"]) + max(x, y) in encoded for x in a for y in b)
    write_csv("nominated_and_relative_pair_exposure.csv", candidates)
    check_inputs()
    print("Nominated and best-local-relative pair audit completed", len(candidates), flush=True)


if __name__ == "__main__":
    main()
