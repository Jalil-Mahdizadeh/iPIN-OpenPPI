"""Exploratory frozen-score audit; see PROTOCOL.md for estimands and limits."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PARENT = ROOT / "example/twelve_target_comparison_v2"
sys.path.insert(0, str(PARENT))
from metrics import evaluate
from analysis_outputs import SETS

MODELS = ("ipin_baseline", "ipin_optimized", "tuna_retrained", "tuna_original")
METRICS = ("P_vs_U_concordance", "average_precision")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def table(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def write_csv(name, rows):
    with (OUT / name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def record(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "bytes": path.stat().st_size}


def parent_check():
    manifest = read(PARENT / "RUN_MANIFEST.json")
    for item in manifest["scientific_outputs"]:
        assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
    return len(manifest["scientific_outputs"])


def prepare():
    paths = [OUT / "PROTOCOL.md", OUT / "investigate.py", OUT / "gpu_diagnostics.py",
             PARENT / "RUN_MANIFEST.json", PARENT / "sequence_order.json",
             ROOT / "benchmark/tuna/scripts/adapter.py",
             ROOT / "artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json",
             ROOT / "benchmark/tuna/weights/bernett_original.pt",
             ROOT / "benchmark/tuna/runs/scorer_bundle/weights/tuna_original.pt"]
    for seed in (20260803, 20260817, 20260831):
        paths.append(ROOT / f".private/frozen_pair_models_v2/bundle/weights/tuna_retrained_seed{seed}.pt")
    paths.extend(sorted(PARENT.glob("*_fresh_endpoint_features.npy")))
    paths.append(PARENT / "tuna_fresh_residues.h5")
    sys.path.insert(0, str(PARENT))
    import original_exposure
    _, sources = original_exposure.load(ROOT)
    paths.extend(ROOT / item["path"] for item in sources)
    assert not (OUT / "INPUT_FREEZE.json").exists(), "Input freeze already exists"
    write_json("INPUT_FREEZE.json", {
        "at_utc": datetime.now(timezone.utc).isoformat(), "exploratory": True,
        "parent_scientific_artifacts_verified": parent_check(),
        "inputs": [record(p) for p in paths],
        "cached_parent_features_reused_for_diagnostics": True,
        "model_training_or_selection": False, "protected_test_records_read": False})


def check_inputs():
    for item in read(OUT / "INPUT_FREEZE.json")["inputs"]:
        assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
    parent_check()


def selected(rows, gene, candidate_set):
    return np.array([i for i, r in enumerate(rows) if r["query_gene"] == gene and
                     (r["class"] == "P" or r["U_stratum"] in SETS[candidate_set])])


def effect_analysis():
    metrics = table(PARENT / "per_target_metrics.csv")
    genes = list(dict.fromkeys(r["target"] for r in metrics))
    idx = {(r["target"], r["model"], r["candidate_set"]): r for r in metrics if r["positive_subset"] == "all_P"}
    output, leaveout, uncertainty = [], [], []
    rng = np.random.default_rng(20260920)
    draws = rng.integers(0, len(genes), size=(100000, len(genes)))
    for name in SETS:
        for comparator in MODELS[:-1]:
            for metric in METRICS:
                a = np.array([float(idx[g, "tuna_original", name][metric]) for g in genes])
                b = np.array([float(idx[g, comparator, name][metric]) for g in genes])
                delta = a - b
                for g, x, y, d in zip(genes, a, b, delta, strict=True):
                    output.append(dict(target=g, candidate_set=name, comparator=comparator, metric=metric,
                                       original=x, comparator_value=y, difference=d,
                                       contribution_to_macro_difference=d / len(genes)))
                boot = delta[draws].mean(1)
                uncertainty.append(dict(candidate_set=name, comparator=comparator, metric=metric,
                                        original_mean=a.mean(), comparator_mean=b.mean(), difference=delta.mean(),
                                        target_bootstrap_2_5_percentile=np.quantile(boot, .025),
                                        target_bootstrap_97_5_percentile=np.quantile(boot, .975),
                                        original_wins=int((delta > 0).sum()), ties=int((delta == 0).sum()),
                                        comparator_wins=int((delta < 0).sum()), targets=len(genes), draws=100000))
                for j, gene in enumerate(genes):
                    keep = np.arange(len(genes)) != j
                    leaveout.append(dict(omitted_target=gene, candidate_set=name, comparator=comparator,
                                         metric=metric, original_mean=a[keep].mean(), comparator_mean=b[keep].mean(),
                                         difference=delta[keep].mean(), targets=int(keep.sum())))
    write_csv("target_contributions.csv", output)
    write_csv("leave_one_target_out.csv", leaveout)
    write_csv("paired_target_bootstrap.csv", uncertainty)


def endpoint_exposure(rows):
    upstream = ROOT / "benchmark/tuna/upstream/TUnA"
    sequences, acc = {}, None
    for line in (upstream / "data/raw/bernett/human_swissprot_oneliner.fasta").read_text().splitlines():
        if line.startswith(">"):
            acc = line[1:].split()[0]
            sequences[acc] = ""
        elif line.strip():
            sequences[acc] += line.strip()
    hashes = {a: hashlib.sha256(s.encode()).hexdigest() for a, s in sequences.items()}
    by_acc, by_seq = {}, {}
    source_counts = []
    for role, stem in (("training", "Intra1"), ("validation", "Intra0")):
        da, ds = defaultdict(set), defaultdict(set)
        counts = {"0": 0, "1": 0}
        path = upstream / f"data/processed/bernett/{stem}_interaction_1500_or_less.tsv"
        with path.open() as stream:
            for a, b, label in csv.reader(stream, delimiter="\t"):
                counts[label] += 1
                da[a, label].add(b)
                da[b, label].add(a)
                ds[hashes[a], label].add(hashes[b])
                ds[hashes[b], label].add(hashes[a])
        by_acc[role], by_seq[role] = da, ds
        source_counts.append(dict(role=role, positive_rows=counts["1"], sampled_negative_rows=counts["0"],
                                  unique_accessions=len({a for a, _ in da}), unique_sequences=len({s for s, _ in ds})))
    enriched = []
    for row in rows:
        d = {k: row[k] for k in ("query_gene", "partner_gene", "query_uniprot", "partner_uniprot", "class", "U_stratum",
                                 "original_tuna_prior_pair", "prior_train_development_pair")}
        for endpoint in ("query", "partner"):
            acc, h = row[endpoint + "_uniprot"], row[endpoint + "_sequence_sha256"]
            for role in by_acc:
                for basis, value, lookup in (("accession", acc, by_acc[role]), ("exact_sequence", h, by_seq[role])):
                    for label, name in (("1", "positive"), ("0", "sampled_negative")):
                        d[f"{endpoint}_{role}_{basis}_{name}_degree"] = len(lookup.get((value, label), ()))
        p = d["partner_training_exact_sequence_positive_degree"]
        n = d["partner_training_exact_sequence_sampled_negative_degree"]
        d.update(partner_training_seen=int(p + n > 0), partner_positive_degree=p,
                 partner_positive_degree_fraction=(p + 1) / (p + n + 2))
        enriched.append(d)
    write_csv("pair_endpoint_exposure.csv", enriched)
    write_csv("original_public_source_counts.csv", source_counts)
    summary, baselines, correlations = [], [], []
    genes = list(dict.fromkeys(r["query_gene"] for r in rows))
    for gene in genes:
        for group in ("P", "context", "background", "low_plausibility"):
            ids = [i for i, r in enumerate(rows) if r["query_gene"] == gene and
                   (r["class"] == "P" if group == "P" else r["U_stratum"] == group)]
            for endpoint in ("query", "partner"):
                for role in by_seq:
                    pos = np.array([enriched[i][f"{endpoint}_{role}_exact_sequence_positive_degree"] for i in ids])
                    neg = np.array([enriched[i][f"{endpoint}_{role}_exact_sequence_sampled_negative_degree"] for i in ids])
                    summary.append(dict(target=gene, group=group, endpoint=endpoint, source=role, pairs=len(ids),
                                        seen=int(((pos + neg) > 0).sum()), seen_fraction=float(((pos + neg) > 0).mean()),
                                        mean_positive_degree=float(pos.mean()), median_positive_degree=float(np.median(pos))))
        for name in SETS:
            ids = selected(rows, gene, name)
            positive = np.array([rows[i]["class"] == "P" for i in ids])
            for key in ("partner_training_seen", "partner_positive_degree", "partner_positive_degree_fraction"):
                result = evaluate([enriched[i][key] for i in ids], positive)
                baselines.append(dict(target=gene, candidate_set=name, diagnostic=key, **result))
            uids = [i for i in ids if rows[i]["class"] == "U"]
            degrees = [enriched[i]["partner_positive_degree"] for i in uids]
            for model in ("tuna_original", "tuna_retrained"):
                rho = float(spearmanr(degrees, [float(rows[i][model + "_score"]) for i in uids]).statistic) if len(set(degrees)) > 1 else None
                correlations.append(dict(target=gene, candidate_set=name, model=model, U=len(uids),
                                         spearman_score_training_positive_degree=rho))
    write_csv("endpoint_exposure_summary.csv", summary)
    write_csv("partner_only_baselines.csv", baselines)
    write_csv("score_degree_correlations.csv", correlations)


def swap_analysis(rows):
    data = np.load(OUT / "query_swap_scores.npz", allow_pickle=False)
    genes = data["query_genes"].tolist()
    labels = np.array([r["class"] == "P" for r in rows])
    metrics, summary, propensity_rows = [], [], []
    for model in ("tuna_original", "tuna_retrained"):
        matrix = data[model]
        assert matrix.shape == (len(genes), len(rows)) and np.isfinite(matrix).all()
        for j, gene in enumerate(genes):
            for name in SETS:
                ids = selected(rows, gene, name)
                actual = np.array([float(rows[i][model + "_score"]) for i in ids])
                assert np.max(np.abs(matrix[j, ids] - actual)) < 1e-5
                ref_rank = rankdata(actual)
                wrong = []
                percentile_sum = np.zeros(len(ids), np.float64)
                for k, replacement in enumerate(genes):
                    scores = matrix[k, ids]
                    ev = evaluate(scores, labels[ids])
                    rho = float(spearmanr(actual, scores).statistic)
                    metrics.append(dict(target=gene, replacement_query=replacement, model=model,
                                        candidate_set=name, actual_query=k == j, rank_spearman_to_actual=rho, **ev))
                    if k != j:
                        wrong.append((ev, rho))
                        percentile_sum += (rankdata(scores) - .5) / len(scores)
                    else:
                        assert np.array_equal(ref_rank, rankdata(scores)), (model, gene, name)
                propensity = percentile_sum / (len(genes) - 1)
                pe = evaluate(propensity, labels[ids])
                for i, val in zip(ids, propensity, strict=True):
                    propensity_rows.append(dict(target=gene, partner_uniprot=rows[i]["partner_uniprot"],
                                                model=model, candidate_set=name, **{"class": rows[i]["class"]},
                                                replacement_query_mean_rank_percentile=float(val)))
                original = evaluate(actual, labels[ids])
                summary.append(dict(target=gene, model=model, candidate_set=name,
                                    actual_P_vs_U=original["P_vs_U_concordance"], actual_AP=original["average_precision"],
                                    mean_replacement_P_vs_U=float(np.mean([e["P_vs_U_concordance"] for e, _ in wrong])),
                                    mean_replacement_AP=float(np.mean([e["average_precision"] for e, _ in wrong])),
                                    mean_replacement_rank_spearman=float(np.mean([r for _, r in wrong])),
                                    query_specific_P_vs_U_lift=original["P_vs_U_concordance"] - float(np.mean([e["P_vs_U_concordance"] for e, _ in wrong])),
                                    query_specific_AP_lift=original["average_precision"] - float(np.mean([e["average_precision"] for e, _ in wrong])),
                                    replacement_consensus_P_vs_U=pe["P_vs_U_concordance"], replacement_consensus_AP=pe["average_precision"],
                                    replacement_consensus_recovered_P_at_10=pe["recovered_P_at_10"]))
    write_csv("query_swap_metrics.csv", metrics)
    write_csv("query_swap_summary.csv", summary)
    write_csv("replacement_partner_propensity.csv", propensity_rows)
    native = table(OUT / "original_score_components.csv")
    component_metrics = []
    for gene in genes:
        for name in SETS:
            ids = selected(rows, gene, name)
            for key in ("raw_logit", "adjusted_logit", "probability"):
                scores = np.array([float(native[i][key]) for i in ids])
                component_metrics.append(dict(target=gene, candidate_set=name, component=key,
                                              **evaluate(scores, labels[ids])))
    write_csv("score_component_metrics.csv", component_metrics)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "analyze", "swaps"))
    args = parser.parse_args()
    assert os.environ.get("APPTAINER_CONTAINER"), "Use the accepted SIF"
    if args.phase == "prepare":
        prepare()
    else:
        check_inputs()
        rows = table(PARENT / "all_twelve_targets_scores.csv")
        if args.phase == "analyze":
            effect_analysis()
            endpoint_exposure(rows)
        else:
            swap_analysis(rows)
        parent_check()
    print(args.phase + " completed", flush=True)


if __name__ == "__main__":
    main()
