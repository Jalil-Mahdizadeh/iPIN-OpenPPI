#!/usr/bin/env python3
"""Read-only audit of panel pairs against documented original-TUnA train/validation.

This uses interaction records, not pre-existing embeddings or model scores.
The public input files do not independently establish a complete training history.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path

from run_comparison import now, read, record, sha, write_csv, write_json


def main():
    out = Path(__file__).resolve().parent
    root = out.parents[1]
    upstream = root / "benchmark/tuna/upstream/TUnA"
    previous = read(root / "benchmark/tuna/provenance/ORIGINAL_EXPOSURE_AUDIT.json")
    sources = []
    for item in previous["sources"]:
        path = upstream / item["path"].removeprefix("/upstream/")
        if sha(path) != item["sha256"]:
            raise RuntimeError("Documented original-TUnA input checksum mismatch")
        sources.append(record(path))
    fasta = upstream / "data/raw/bernett/human_swissprot_oneliner.fasta"
    sequences = {}
    accession = None
    for line in fasta.read_text().splitlines():
        if line.startswith(">"):
            accession = line[1:].split()[0]
            sequences[accession] = ""
        elif line.strip():
            sequences[accession] += line.strip()
    hashes = {a: hashlib.sha256(s.encode("ascii")).hexdigest() for a, s in sequences.items()}
    lookup = {}
    for role, name in (("training", "Intra1"), ("validation", "Intra0")):
        accession_pairs, sequence_pairs = collections.defaultdict(set), collections.defaultdict(set)
        path = upstream / "data/processed/bernett" / f"{name}_interaction_1500_or_less.tsv"
        with path.open(newline="") as handle:
            for a, b, label in csv.reader(handle, delimiter="\t"):
                if label not in ("0", "1") or a not in hashes or b not in hashes:
                    raise RuntimeError("Unexpected public training/validation record")
                accession_pairs[tuple(sorted((a, b)))].add(label)
                sequence_pairs[tuple(sorted((hashes[a], hashes[b])))].add(label)
        lookup[role] = (accession_pairs, sequence_pairs)
    results = []
    for row in read(out / "pairs.json"):
        acc_pair = tuple(sorted((row["query_uniprot"], row["partner_uniprot"])))
        seq_pair = tuple(sorted((row["query_sequence_sha256"], row["partner_sequence_sha256"])))
        result = {k: row[k] for k in ("query_gene", "partner_gene", "query_uniprot", "partner_uniprot", "class", "panel_row")}
        for role, (by_accession, by_sequence) in lookup.items():
            result[role + "_accession_labels"] = ";".join(sorted(by_accession.get(acc_pair, set())))
            result[role + "_exact_sequence_labels"] = ";".join(sorted(by_sequence.get(seq_pair, set())))
        results.append(result)
    write_csv(out / "original_tuna_pair_exposure.csv", results)
    summary = {}
    for panel_class in ("P", "U"):
        for role in lookup:
            for kind in ("accession", "exact_sequence"):
                key = f"{role}_{kind}_labels"
                found = [r for r in results if r["class"] == panel_class and r[key]]
                summary[f"panel_{panel_class}_{key}"] = {
                    "pairs": len(found),
                    "public_positive_labeled": sum("1" in r[key].split(";") for r in found),
                    "public_negative_labeled": sum("0" in r[key].split(";") for r in found),
                    "positive_pair_names": [r["query_gene"] + "--" + r["partner_gene"] for r in found] if panel_class == "P" else [],
                }
    report = {"at_utc": now(), "summary": summary, "verified_sources": sources,
              "all_pair_orientations_checked": True, "sequence_and_accession_pair_checks": True,
              "preexisting_embeddings_used": False,
              "caveat": "Documented public Bernett training/validation files only; not an authenticated complete checkpoint history, homology audit, or language-model exposure audit.",
              "script": record(Path(__file__))}
    write_json(out / "ORIGINAL_TUNA_PAIR_EXPOSURE.json", report)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
