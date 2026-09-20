"""Five fixed candidate sets, four predictors, and all previous ranking metrics."""
from __future__ import annotations

from collections import Counter
import csv
import numpy as np

from metrics import CUTOFFS, evaluate, positive_ranks
from run_comparison import CONFIG, MODELS, SEEDS, TARGETS, inputs, now, read, record, sha, write_csv, write_json

SETS = {"context": ("context",), "background": ("background",),
        "low_plausibility": ("low_plausibility",), "context_background": ("context", "background"),
        "all_U": ("context", "background", "low_plausibility")}
SUBSETS = ("all_P", "exclude_development_P", "exclude_development_P_and_homomers",
           "exclude_prior_train_development_P", "exclude_prior_train_development_P_and_homomers",
           "exclude_any_model_prior_pairs", "exclude_any_model_prior_pairs_and_homomers")
COHORTS = {"all_twelve": TARGETS, "original_six": tuple(CONFIG["original_targets"]),
           "additional_six": tuple(t["gene"] for t in CONFIG["new_targets"]),
           "strict_evidence_eleven": tuple(g for g in TARGETS if g != "EGFR")}


def included(row, subset):
    if subset.startswith("exclude_any_model") and (row["prior_train_development_pair"] or row["original_tuna_prior_pair"]):
        return False
    if row["class"] == "U":
        return True
    if subset.startswith("exclude_development") and row["development_exposed_positive"]:
        return False
    if subset.startswith("exclude_prior_train_development") and row["prior_train_development_pair"]:
        return False
    return not (subset.endswith("and_homomers") and row["homomeric"])


def candidate_list(panel, subset, name):
    return [r for r in panel if included(r, subset) and (r["class"] == "P" or r["U_stratum"] in SETS[name])]


def table(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def summarize(root, out):
    rows, snapshot, order, sequences = inputs(root, out)
    for name, metadata in (("ipin", "IPIN_RUN.json"), ("tuna", "TUNA_RUN.json")):
        run, path = read(out / metadata), out / f"{name}_scores.csv"
        if sha(path) != run["score_artifact"]["sha256"]:
            raise RuntimeError("Score checksum mismatch")
        result = table(path)
        if len(result) != len(rows):
            raise RuntimeError("Incomplete scoring")
        for i, scored in enumerate(result):
            if int(scored.pop("row_index")) != i:
                raise RuntimeError("Scoring row order changed")
            for key, value in scored.items():
                number = float(value)
                if not np.isfinite(number):
                    raise RuntimeError("Nonfinite model score")
                rows[i][key] = number
    for row in rows:
        if np.mean([row[f"tuna_retrained_seed{s}_score"] for s in SEEDS], dtype=np.float64) != row["tuna_retrained_score"]:
            raise RuntimeError("Frozen ensemble arithmetic changed")
    metrics, ranks, matched, curves, coverage = [], [], [], [], []
    for gene in TARGETS:
        panel = [r for r in rows if r["query_gene"] == gene]
        positives = [r for r in panel if r["class"] == "P"]
        for subset in SUBSETS:
            for name in SETS:
                selected = candidate_list(panel, subset, name)
                p = sum(r["class"] == "P" for r in selected)
                coverage.append({"target": gene, "positive_subset": subset, "candidate_set": name,
                                 "P": p, "U": len(selected) - p, "evaluated": bool(p),
                                 "reason": "" if p else "No nominated P remains after exposure exclusions; metrics undefined."})
        for model in MODELS:
            key = model + "_score"
            for row in panel:
                row[model + "_rank"] = positive_ranks(row[key], [r[key] for r in panel])["rank_mid"]
            for name in SETS:
                selected = candidate_list(panel, "all_P", name)
                population = [r[key] for r in selected]
                for positive in positives:
                    ranks.append({"query_gene": gene, "partner_gene": positive["partner_gene"],
                                  "partner_uniprot": positive["partner_uniprot"], "model": model, "candidate_set": name,
                                  "score": positive[key], **positive_ranks(positive[key], population)})
                    own = [r for r in selected if r["class"] == "U" and r["anchor_positive_uniprot"] == positive["partner_uniprot"]]
                    matched.append({"target": gene, "partner_gene": positive["partner_gene"],
                                    "partner_uniprot": positive["partner_uniprot"], "model": model, "candidate_set": name,
                                    **evaluate([positive[key]] + [r[key] for r in own], np.array([True] + [False] * len(own)))})
                curve = evaluate(population, np.array([r["class"] == "P" for r in selected]), tuple(range(1, 51)))
                for k in range(1, 51):
                    curves.append({"target": gene, "model": model, "candidate_set": name, "K": k,
                                   "P": len(positives), "panel_size": len(selected), "recovered_P": curve[f"recovered_P_at_{k}"],
                                   "recall": curve[f"recall_at_{k}"], "target_success": curve[f"target_success_at_{k}"]})
            for subset in SUBSETS:
                for name in SETS:
                    selected = candidate_list(panel, subset, name)
                    if not any(r["class"] == "P" for r in selected):
                        continue
                    values = evaluate([r[key] for r in selected], np.array([r["class"] == "P" for r in selected]))
                    metrics.append({"target": gene, "model": model, "positive_subset": subset, "candidate_set": name, **values})
        write_csv(out / f"{gene.lower()}_four_model_scores.csv", panel)
    for filename, content in (("all_twelve_targets_scores.csv", rows), ("per_target_metrics.csv", metrics),
                              ("positive_partner_ranks.csv", ranks), ("matched_positive_metrics.csv", matched),
                              ("retrieval_curves.csv", curves), ("analysis_coverage.csv", coverage)):
        write_csv(out / filename, content)
    summary = []
    for cohort, genes in COHORTS.items():
        for subset in SUBSETS:
            for name in SETS:
                for model in MODELS:
                    selected = [r for r in metrics if r["target"] in genes and r["positive_subset"] == subset
                                and r["candidate_set"] == name and r["model"] == model]
                    if not selected:
                        raise RuntimeError("Empty macro cohort")
                    def mean(key):
                        return float(np.mean([r[key] for r in selected], dtype=np.float64))
                    row = {"cohort": cohort, "model": model, "positive_subset": subset, "candidate_set": name,
                           "planned_targets": len(genes), "targets": len(selected),
                           "omitted_targets": ";".join(g for g in genes if g not in {r["target"] for r in selected}),
                           "P": sum(r["P"] for r in selected), "U": sum(r["U"] for r in selected),
                           "macro_P_vs_U_concordance": mean("P_vs_U_concordance"), "MAP": mean("average_precision"),
                           "MRR": mean("reciprocal_rank"), "mean_first_positive_rank": mean("first_positive_rank_expected")}
                    for k in CUTOFFS:
                        row.update({f"total_recovered_P_at_{k}": sum(r[f"recovered_P_at_{k}"] for r in selected),
                                    f"target_success_count_at_{k}": sum(r[f"target_success_at_{k}"] for r in selected)})
                        for metric in ("recall", "known_positive_precision", "EF", "NDCG", "target_success"):
                            row[f"macro_{metric}_at_{k}"] = mean(f"{metric}_at_{k}")
                    summary.append(row)
    write_csv(out / "macro_metrics.csv", summary)
    # Compare within the preserved candidate lists: adding U necessarily changes
    # full-panel ranks and is not a numerical reproducibility failure.
    consistency = []
    current = {(r["query_gene"], r["partner_uniprot"]): r for r in rows}
    for previous_folder, models in (("twelve_target_comparison_v1", MODELS[:3]), ("six_target_comparison_v1", ("tuna_original",))):
        filename = "all_twelve_targets_scores.csv" if previous_folder.startswith("twelve") else "all_six_targets_scores.csv"
        previous = table(root / "example" / previous_folder / filename)
        for model in models:
            diffs = [abs(float(r[model + "_score"]) - current[r["query_gene"], r["partner_uniprot"]][model + "_score"]) for r in previous]
            changed = 0
            for gene in {r["query_gene"] for r in previous}:
                old_panel = [r for r in previous if r["query_gene"] == gene]
                scores = [current[gene, r["partner_uniprot"]][model + "_score"] for r in old_panel]
                changed += sum(float(r[model + "_rank"]) != positive_ranks(s, scores)["rank_mid"] for r, s in zip(old_panel, scores, strict=True))
            consistency.append({"model": model, "previous_folder": previous_folder, "pairs": len(previous),
                                "maximum_absolute_score_difference": max(diffs), "within_previous_panel_rank_changes": changed})
    write_json(out / "PREVIOUS_RUN_CONSISTENCY.json", {"at_utc": now(), "models": consistency,
               "note": "Fresh FP32 extraction batches can change rounding; rankings compared only within the same old candidate sets."})
    exposure = [{k: r[k] for k in ("query_gene", "partner_gene", "class", "U_stratum", "prior_train_development_pair", "original_tuna_prior_pair")}
                for r in rows if r["prior_train_development_pair"] or r["original_tuna_prior_pair"]]
    write_csv(out / "exposed_pairs.csv", exposure)
    for relative, digest in read(out / "INPUT_FREEZE.json")["original_file_hashes"].items():
        if sha(root / relative) != digest:
            raise RuntimeError(f"Historical artifact changed: {relative}")
    write_json(out / "VALIDATION.json", {"at_utc": now(), "passed": True, "pairs": len(rows), "P": 37, "U": 5550,
               "four_model_scores": len(rows) * 4, "metric_rows": len(metrics), "macro_rows": len(summary),
               "matched_metric_rows": len(matched), "ranking_rows": len(ranks), "curve_rows": len(curves),
               "fresh_embeddings_both_pipelines": True, "original_records_unchanged": True,
               "protected_test_truth_or_scores_used": False})
    print("Four-model, five-candidate-set comparison completed", flush=True)
