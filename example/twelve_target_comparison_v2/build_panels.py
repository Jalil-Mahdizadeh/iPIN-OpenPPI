#!/usr/bin/env python3
"""Extend the preserved panels without reading scores or protected test data."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment

from original_exposure import load as load_original, check as original_check
from selection import sources as load_sources, pair_evidence, STRICT_CLASSES
from run_comparison import TARGETS, INPUT_COLUMNS, now, read, sha, write_csv, write_json

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("previous_panel_builder", HERE.parent / "twelve_target_comparison_v1/build_panels.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
SALT = "ipin-twelve-target-low-plausibility-20260920-v2"


def exclusions(root, proteins, old, gene, intact, prior, original):
    acc = old["target"]["accession"]
    entry = read(HERE / "sources" / f"uniprot_{acc}.json")
    excluded = set(intact[0]) | {acc} | {r["partner_uniprot"] for r in old["rows"]}
    for key in ("excluded_accessions", "known_or_annotation_excluded_accessions", "reciprocal_annotation_excluded_accessions"):
        excluded.update(old.get(key, []))
    aliases = {gene, *[v["value"] for names in entry.get("genes", []) for v in names.get("synonyms", [])]}
    pattern = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(s) for s in aliases if len(s) >= 3) + r")(?![A-Za-z0-9])", re.I)
    subunit = " ".join(t["value"] for c in entry.get("comments", []) if c["commentType"] == "SUBUNIT" for t in c.get("texts", []))
    excluded.update(a for a, p in proteins.items() if pattern.search(p["subunit"]) or re.search(r"(?<![A-Za-z0-9])" + re.escape(p["gene"]) + r"(?![A-Za-z0-9])", subunit, re.I))
    for comment in entry.get("comments", []):
        if comment["commentType"] == "INTERACTION":
            for interaction in comment.get("interactions", []):
                for key in ("interactantOne", "interactantTwo"):
                    value = interaction.get(key, {}).get("uniProtKBAccession", "").split("-")[0]
                    if value:
                        excluded.add(value)
    hashes = {r["sequence_sha256"] for r in old["rows"]} | {old["target"]["sequence_sha256"]}
    for group in prior[gene].values():
        excluded.update(group["accessions"])
        hashes.update(group["sequence_sha256"])
    original_excluded = {a for a, p in proteins.items() if any(original_check(original, proteins[acc], p).values())}
    excluded.update(original_excluded)
    hashes.update(proteins[a]["sequence_sha256"] for a in excluded if a in proteins)
    return excluded, hashes, original_excluded


def choose(proteins, candidates, anchors, gene):
    """Global assignment avoids exhausting the scarce long-partner windows."""
    options = sorted(candidates)
    slots = [anchor for anchor in anchors for _ in range(50)]
    costs = np.full((len(slots), len(options)), 1e12, np.float64)
    for i, anchor in enumerate(slots):
        for j, acc in enumerate(options):
            protein, evidence = proteins[acc], candidates[acc]
            ratio = protein["length"] / anchor["length"]
            if not .5 <= ratio <= 2:
                continue
            secondary = evidence["evidence_tier"].startswith("B_")
            subrank = {"mitochondrial_matrix": 0, "mitochondrial": 1, "nuclear": 2}.get(evidence["localization_class"], 0) if secondary else 0
            tie = int(hashlib.sha256(f"{SALT}|{gene}|{anchor['partner_uniprot']}|{acc}".encode()).hexdigest()[:12], 16) / 16**12
            costs[i, j] = (int(secondary) * 1e9 + subrank * 1e6 + evidence["annotation_quality"] * 1000
                           + abs(math.log2(ratio)) + tie * 1e-6)
    left, right = linear_sum_assignment(costs)
    if len(left) != len(slots) or np.any(costs[left, right] >= 1e12):
        raise RuntimeError(f"Cannot fill all 50-per-positive quotas for {gene}; no silent relaxation")
    result = {a["partner_uniprot"]: [] for a in anchors}
    for i, j in zip(left, right, strict=True):
        result[slots[i]["partner_uniprot"]].append(options[j])
    return {anchor: sorted(chosen) for anchor, chosen in result.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--allow-secondary-overlap", action="store_true")
    parser.add_argument("--feasibility-only", action="store_true")
    args = parser.parse_args()
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Use the accepted data SIF")
    root, folder = args.root, HERE / "sources"
    proteins = load_sources(folder)
    old = {g: read(root / "example" / g / "panel_manifest.json") for g in TARGETS}
    targets = {g: proteins[m["target"]["accession"]] for g, m in old.items()}
    for gene, target in targets.items():
        if target["sequence_sha256"] != old[gene]["target"]["sequence_sha256"]:
            raise RuntimeError("Target sequence changed")
    prior, prior_sources, sequence_source = previous.prior_neighbors(root, targets)
    original, original_sources = load_original(root)
    def fetch(gene):
        result = previous.intact_partners(targets[gene]["accession"], folder)
        print(f"IntAct {gene}: {result[1]['records']} records, {len(result[0])} human partner identifiers", flush=True)
        return gene, result
    with ThreadPoolExecutor(max_workers=4) as executor:
        intact = dict(executor.map(fetch, TARGETS))
    summaries, annotation_rows, feasibility = [], [], []
    for gene in TARGETS:
        m = old[gene]
        excluded, excluded_hashes, original_excluded = exclusions(root, proteins, m, gene, intact[gene], prior, original)
        candidates, seen = {}, set()
        for acc, protein in sorted(proteins.items()):
            if acc in excluded or protein["sequence_sha256"] in excluded_hashes or protein["sequence_sha256"] in seen:
                continue
            evidence = pair_evidence(gene, protein, args.allow_secondary_overlap)
            if evidence:
                candidates[acc] = evidence
                seen.add(protein["sequence_sha256"])
        anchors = [r for r in m["rows"] if r["class"] == "P"]
        for anchor in anchors:
            counts = Counter(e["evidence_tier"] for acc, e in candidates.items() if .5 <= proteins[acc]["length"] / anchor["length"] <= 2)
            feasibility.append({"target": gene, "anchor": anchor["partner_gene"], "available_by_tier": dict(counts)})
        print(gene, feasibility[-len(anchors):], flush=True)
        selected = choose(proteins, candidates, anchors, gene)
        if args.feasibility_only:
            continue
        destination = HERE / "panels" / gene
        destination.mkdir(parents=True, exist_ok=False)
        annotations = []
        for r in m["rows"]:
            acc = r["partner_uniprot"]
            if proteins[acc]["sequence_sha256"] != r["sequence_sha256"]:
                raise RuntimeError("Existing partner identity changed")
            exposure = {k: acc in v["accessions"] or proteins[acc]["sequence_sha256"] in v["sequence_sha256"] for k, v in prior[gene].items()}
            annotations.append({**r, "prior_pair_exposure": exposure,
                                **original_check(original, targets[gene], proteins[acc])})
        for anchor in anchors:
            for acc in selected[anchor["partner_uniprot"]]:
                protein, evidence = proteins[acc], candidates[acc]
                exposure = original_check(original, targets[gene], protein)
                if any(exposure.values()):
                    raise RuntimeError("New U has documented original-TUnA exposure")
                annotations.append({"row": len(annotations) + 1, "class": "U", "partner_gene": protein["gene"],
                                    "partner_uniprot": acc, "length": protein["length"], "sequence_sha256": protein["sequence_sha256"],
                                    "stratum": "low_plausibility", "anchor_positive_uniprot": anchor["partner_uniprot"],
                                    "prior_pair_exposure": {k: False for k in prior[gene]}, **exposure, **evidence})
                hpa = protein["hpa"]
                annotation_rows.append({"target": gene, "query_uniprot": targets[gene]["accession"],
                    "anchor_gene": anchor["partner_gene"], "anchor_uniprot": anchor["partner_uniprot"],
                    "partner_gene": protein["gene"], "partner_uniprot": acc, "length": protein["length"],
                    "anchor_length": anchor["length"], "length_ratio": protein["length"] / anchor["length"],
                    **evidence, "uniprot_location": protein["location_raw"], "uniprot_signal_peptide": protein["signal_peptide"],
                    "HPA_Ensembl": hpa.get("Gene", ""), "HPA_gene": hpa.get("Gene name", ""),
                    "HPA_reliability": hpa.get("Reliability", ""),
                    "UniProt_URL": f"https://www.uniprot.org/uniprotkb/{acc}/entry",
                    "HPA_URL": f"https://www.proteinatlas.org/{hpa['Gene']}/subcellular" if hpa else "",
                    "sequence_sha256": protein["sequence_sha256"]})
        rows = [{"query_gene": gene, "query_uniprot": targets[gene]["accession"],
                 **{k: r[k] for k in ("partner_gene", "partner_uniprot", "class")}} for r in annotations]
        path = destination / f"{gene.lower()}_ipin_panel.csv"
        write_csv(path, rows, INPUT_COLUMNS)
        manifest = {"schema": "ipin_extended_target_panel_v2", "created_at_utc": now(), "target": m["target"],
            "P": len(anchors), "U": 150 * len(anchors), "csv": path.name, "csv_sha256": sha(path), "rows": annotations,
            "parent_manifest": {"path": str((root / 'example' / gene / 'panel_manifest.json').relative_to(root)),
                                "sha256": sha(root / "example" / gene / "panel_manifest.json")},
            "preserved_prefix_rows": len(m["rows"]), "excluded_accessions": sorted(excluded),
            "excluded_sequence_sha256": sorted(excluded_hashes), "intact_source": intact[gene][1],
            "original_tuna_excluded_accessions": sorted(original_excluded),
            "prior_neighbors": prior[gene], "strict_candidate_classes": sorted(STRICT_CLASSES[gene]),
            "allow_secondary_overlap": args.allow_secondary_overlap, "sampling_salt": SALT,
            "new_stratum": "low_plausibility", "length_ratio_limit": 2,
            "model_scores_read": False, "protected_test_truth_read": False,
            "selection_protocol_sha256": sha(HERE / "SELECTION.md")}
        write_json(destination / "panel_manifest.json", manifest)
        counts = Counter(r["evidence_tier"] for r in annotations if r.get("stratum") == "low_plausibility")
        summaries.append({"target": gene, "P": len(anchors), "U": 150 * len(anchors), "new_U_by_tier": dict(counts),
                          "csv_sha256": sha(path), "manifest_sha256": sha(destination / "panel_manifest.json")})
    if args.feasibility_only:
        print("All target quotas feasible without looking at scores", flush=True)
        return
    write_csv(HERE / "low_plausibility_annotations.csv", annotation_rows)
    source_records = [{"path": str(p.relative_to(root)), **read(p)} for p in sorted(folder.glob("*.metadata.json"))]
    write_json(HERE / "PANEL_BUILD.json", {"at_utc": now(), "passed": True, "targets": summaries,
        "feasibility": feasibility, "builder_sha256": sha(Path(__file__)), "selection_sha256": sha(HERE / "selection.py"),
        "configuration_sha256": sha(HERE / "panel_config.json"), "selection_protocol_sha256": sha(HERE / "SELECTION.md"),
        "training_development_sources": prior_sources, "frozen_sequence_source_sha256": sequence_source,
        "original_tuna_training_validation_sources": original_sources, "source_metadata": source_records,
        "model_scores_read": False, "protected_test_truth_read": False})


if __name__ == "__main__":
    main()
