"""Post hoc TRAIN/validation sequence-relative audit, never reading original test."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess

from investigate import ROOT, OUT, PARENT, check_inputs, read, record, sha, table, write_csv, write_json


def main():
    assert os.environ.get("APPTAINER_CONTAINER")
    check_inputs()
    binary = ROOT / "artifacts/cache/tools/mmseqs2/18-8cc5c/mmseqs/bin/mmseqs"
    assert sha(binary) == "d5f6d96578e3dbcd1d8772bb575b112e9dd1dbf077d150914962a2356ae0d75d"
    version = subprocess.check_output([str(binary), "version"], text=True).strip()
    local = OUT / "homology_local"
    local.mkdir(exist_ok=True)
    rows = table(PARENT / "all_twelve_targets_scores.csv")
    snapshot = read(PARENT / "uniprot_sequences.json")["records"]
    queries = {}
    for row in rows:
        queries[row["query_uniprot"]] = row["query_gene"]
        if row["class"] == "P":
            queries[row["partner_uniprot"]] = row["partner_gene"]
    upstream = ROOT / "benchmark/tuna/upstream/TUnA"
    reference, acc = {}, None
    for line in (upstream / "data/raw/bernett/human_swissprot_oneliner.fasta").read_text().splitlines():
        if line.startswith(">"):
            acc = line[1:].split()[0]
            reference[acc] = ""
        elif line.strip():
            reference[acc] += line.strip()
    role_ids, role_pairs = {}, {}
    for role, stem in (("training", "Intra1"), ("validation", "Intra0")):
        pairs = list(csv.reader((upstream / f"data/processed/bernett/{stem}_interaction_1500_or_less.tsv").open(), delimiter="\t"))
        role_ids[role] = {a for pair in pairs for a in pair[:2]}
        role_pairs[role] = {label: {tuple(sorted((a, b))) for a, b, value in pairs if value == label} for label in ("0", "1")}
    reference_ids = set().union(*role_ids.values())
    query_path, reference_path = local / "query.fasta", local / "reference.fasta"
    query_path.write_text("".join(f">{a}\n{snapshot[a]['sequence']}\n" for a in sorted(queries)))
    reference_path.write_text("".join(f">{a}\n{reference[a]}\n" for a in sorted(reference_ids)))
    fields = "query,target,fident,alnlen,qstart,qend,qlen,tstart,tend,tlen,evalue,bits,qcov,tcov"
    command = [str(binary), "easy-search", str(query_path), str(reference_path), str(local / "matches.tsv"), str(local / "tmp"),
               "--threads", "8", "-s", "7.5", "-e", "0.001", "--max-seqs", str(len(reference_ids)),
               "--max-accept", str(len(reference_ids)), "--max-rejected", str(len(reference_ids)),
               "--alignment-mode", "3", "--format-output", fields]
    assert not (OUT / "HOMOLOGY_INPUT_FREEZE.json").exists()
    write_json("HOMOLOGY_INPUT_FREEZE.json", dict(at_utc=datetime.now(timezone.utc).isoformat(),
               exploratory_followup=True, primary_freeze=record(OUT / "INPUT_FREEZE.json"),
               protocol=record(OUT / "HOMOLOGY_FOLLOWUP.md"), script=record(Path(__file__)), binary=record(binary),
               version=version, query_sequences=len(queries), reference_sequences=len(reference_ids),
               local_inputs=[record(query_path), record(reference_path)], command=command))
    with (local / "mmseqs.log").open("w") as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    with (local / "matches.tsv").open() as stream:
        matches = list(csv.DictReader(stream, fieldnames=fields.split(","), delimiter="\t"))
    output, relatives = [], {}
    for acc, gene in queries.items():
        for role, allowed in role_ids.items():
            hits = [r for r in matches if r["query"] == acc and r["target"] in allowed]
            broad = [r for r in hits if float(r["qcov"]) >= .8 and float(r["tcov"]) >= .8]
            relatives[acc, role] = {r["target"] for r in broad if float(r["fident"]) >= .3}
            for scope, selected in (("local", hits), ("both_coverage_80pct", broad)):
                best = max(selected, key=lambda r: (float(r["bits"]), float(r["fident"]), r["target"])) if selected else None
                row = dict(query_gene=gene, query_uniprot=acc, source=role, scope=scope, reported_matches=len(selected),
                           hits_30pct_identity_both_80pct_coverage=len(relatives[acc, role]),
                           hits_40pct_identity_both_80pct_coverage=sum(float(r["fident"]) >= .4 for r in broad))
                row.update({key: best[key] if best else "" for key in fields.split(",") if key != "query"})
                output.append(row)
    write_csv("sequence_relative_matches.csv", output)
    pair_output = []
    for row in rows:
        if row["class"] != "P":
            continue
        for role, reference_pairs in role_pairs.items():
            a, b = relatives[row["query_uniprot"], role], relatives[row["partner_uniprot"], role]
            generated = {tuple(sorted((x, y))) for x in a for y in b}
            p, n = sorted(generated & reference_pairs["1"]), sorted(generated & reference_pairs["0"])
            pair_output.append(dict(target=row["query_gene"], partner_gene=row["partner_gene"], source=role,
                                    query_hits=len(a), partner_hits=len(b), positive_relative_pairs=len(p),
                                    sampled_negative_relative_pairs=len(n),
                                    positive_pairs=";".join("|".join(v) for v in p), sampled_negative_pairs=";".join("|".join(v) for v in n)))
    write_csv("sequence_relative_pair_exposure.csv", pair_output)
    write_json("HOMOLOGY_RUN.json", dict(mmseqs_version=version, reported_local_matches=len(matches),
               reference_accessions=len(reference_ids), query_accessions=len(queries),
               matches=record(local / "matches.tsv"), freeze=record(OUT / "HOMOLOGY_INPUT_FREEZE.json"),
               passed=True, protected_test_records_read=False))
    check_inputs()
    print(f"Homology follow-up completed: {len(queries)} queries, {len(reference_ids)} TRAIN/validation references", flush=True)


if __name__ == "__main__":
    main()
