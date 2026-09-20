"""Documented original-TUnA pair exposure; no benchmark test files are read."""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path


def load(root):
    upstream = root / "benchmark/tuna/upstream/TUnA"
    audit = json.loads((root / "benchmark/tuna/provenance/ORIGINAL_EXPOSURE_AUDIT.json").read_text())
    sources = []
    for item in audit["sources"]:
        path = upstream / item["path"].removeprefix("/upstream/")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            raise RuntimeError("Original TUnA training/validation source changed")
        sources.append({"path": str(path.relative_to(root)), "sha256": digest})
    sequences, accession = {}, None
    for line in (upstream / "data/raw/bernett/human_swissprot_oneliner.fasta").read_text().splitlines():
        if line.startswith(">"):
            accession = line[1:].split()[0]
            sequences[accession] = ""
        elif line.strip():
            sequences[accession] += line.strip()
    hashes = {a: hashlib.sha256(s.encode()).hexdigest() for a, s in sequences.items()}
    lookup = {}
    for role, name in (("training", "Intra1"), ("validation", "Intra0")):
        by_accession, by_sequence = defaultdict(set), defaultdict(set)
        with (upstream / "data/processed/bernett" / f"{name}_interaction_1500_or_less.tsv").open() as stream:
            for a, b, label in csv.reader(stream, delimiter="\t"):
                if label not in ("0", "1") or a not in hashes or b not in hashes:
                    raise RuntimeError("Unexpected original-TUnA source record")
                by_accession[tuple(sorted((a, b)))].add(label)
                by_sequence[tuple(sorted((hashes[a], hashes[b])))].add(label)
        lookup[role] = (by_accession, by_sequence)
    return lookup, sources


def check(lookup, query, partner):
    accessions = tuple(sorted((query["accession"], partner["accession"])))
    sequences = tuple(sorted((query["sequence_sha256"], partner["sequence_sha256"])))
    result = {}
    for role, (by_accession, by_sequence) in lookup.items():
        result[f"original_tuna_{role}_accession_labels"] = ";".join(sorted(by_accession.get(accessions, set())))
        result[f"original_tuna_{role}_exact_sequence_labels"] = ";".join(sorted(by_sequence.get(sequences, set())))
    return result
