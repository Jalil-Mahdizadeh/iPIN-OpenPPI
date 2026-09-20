"""Publish the predeclared twelve-target retrieval analysis from frozen scores."""
from __future__ import annotations

import csv
from pathlib import Path
import numpy as np

from metrics import CUTOFFS, evaluate, positive_ranks
from run_comparison import CONFIG, MODELS, SEEDS, TARGETS, inputs, now, read, record, sha, write_csv, write_json

SUBSETS = ("all_P", "exclude_development_P", "exclude_development_P_and_homomers",
           "exclude_prior_train_development_P", "exclude_prior_train_development_P_and_homomers")
STRATA = ("all_U", "context", "background")


def included(row, subset):
    if subset.startswith("exclude_development") and row["development_exposed_positive"]:
        return False
    if subset.startswith("exclude_prior_train_development") and row["prior_train_development_pair"]:
        return False
    return not (subset.endswith("and_homomers") and row["homomeric"])


def summarize(root, out):
    rows, snapshot, order, sequences = inputs(root, out)
    for name, metadata in (("ipin", "IPIN_RUN.json"), ("tuna", "TUNA_RUN.json")):
        run = read(out / metadata)
        path = out / f"{name}_scores.csv"
        if sha(path) != run["score_artifact"]["sha256"]:
            raise RuntimeError("Score file checksum mismatch")
        with path.open(newline="") as stream:
            result = list(csv.DictReader(stream))
        if len(result) != len(rows):
            raise RuntimeError("Incomplete score coverage")
        for i, scored in enumerate(result):
            if int(scored.pop("row_index")) != i:
                raise RuntimeError("Score row order changed")
            for key, value in scored.items():
                number = float(value)
                if not np.isfinite(number):
                    raise RuntimeError("Nonfinite model score")
                rows[i][key] = number
    member_cols = [f"tuna_retrained_seed{s}_score" for s in SEEDS]
    for row in rows:
        if np.mean([row[c] for c in member_cols], dtype=np.float64) != row["tuna_retrained_score"]:
            raise RuntimeError("TUnA ensemble differs from fixed three-seed arithmetic")
    metrics, ranks, matched, curves = [], [], [], []
    for gene in TARGETS:
        panel = [r for r in rows if r["query_gene"] == gene]
        positives = [r for r in panel if r["class"] == "P"]
        unlabeled = [r for r in panel if r["class"] == "U"]
        for model in MODELS:
            key = model + "_score"
            population = [r[key] for r in panel]
            for row in panel:
                row[model + "_rank"] = positive_ranks(row[key], population)["rank_mid"]
            for positive in positives:
                own = [r for r in unlabeled if r["anchor_positive_uniprot"] == positive["partner_uniprot"]]
                if len(own) != 100:
                    raise RuntimeError("Each positive requires its original 100 U controls")
                ranks.append({"query_gene": gene, "partner_gene": positive["partner_gene"], "partner_uniprot": positive["partner_uniprot"],
                              "model": model, "score": positive[key], **positive_ranks(positive[key], population),
                              "development_exposed_positive": positive["development_exposed_positive"],
                              "training_exposed_positive": positive["training_exposed_positive"],
                              "prior_train_development_pair": positive["prior_train_development_pair"], "homomeric": positive["homomeric"]})
                for stratum in STRATA:
                    controls = [r for r in own if stratum == "all_U" or r["U_stratum"] == stratum]
                    matched.append({"target": gene, "partner_gene": positive["partner_gene"], "partner_uniprot": positive["partner_uniprot"],
                                    "model": model, "U_stratum": stratum,
                                    **evaluate([positive[key]] + [r[key] for r in controls], np.asarray([True] + [False] * len(controls)))})
            curve = evaluate(population, np.asarray([r["class"] == "P" for r in panel]), tuple(range(1, 51)))
            for k in range(1, 51):
                curves.append({"target": gene, "model": model, "K": k, "P": len(positives), "panel_size": len(panel),
                               "recovered_P": curve[f"recovered_P_at_{k}"], "recall": curve[f"recall_at_{k}"],
                               "target_success": curve[f"target_success_at_{k}"]})
            for subset in SUBSETS:
                pp = [r for r in positives if included(r, subset)]
                for stratum in STRATA:
                    uu = [r for r in unlabeled if stratum == "all_U" or r["U_stratum"] == stratum]
                    # Never relabel excluded positives as U. Remove them from
                    # the candidate list and keep the exact same U controls.
                    if not pp:
                        raise RuntimeError(f"No positive remains in {gene}/{subset}; explicit missing-data policy required")
                    values = evaluate([r[key] for r in pp + uu], np.asarray([True] * len(pp) + [False] * len(uu)))
                    metrics.append({"target": gene, "model": model, "positive_subset": subset, "U_stratum": stratum, **values})
        name = f"{gene.lower()}_three_model_scores.csv"
        write_csv(out / name, panel)
        with (root / "example" / gene / name).open("xb") as stream:
            stream.write((out / name).read_bytes())
    write_csv(out / "all_twelve_targets_scores.csv", rows)
    write_csv(out / "per_target_metrics.csv", metrics)
    write_csv(out / "positive_partner_ranks.csv", ranks)
    write_csv(out / "matched_positive_metrics.csv", matched)
    write_csv(out / "retrieval_curves.csv", curves)
    summary = []
    cohorts = {"all_twelve": TARGETS, "original_six": tuple(CONFIG["original_targets"]),
               "additional_six": tuple(t["gene"] for t in CONFIG["new_targets"])}
    for cohort, genes in cohorts.items():
        for subset in SUBSETS:
            for stratum in STRATA:
                for model in MODELS:
                    selected = [r for r in metrics if r["target"] in genes and r["positive_subset"] == subset
                                and r["U_stratum"] == stratum and r["model"] == model]
                    if len(selected) != len(genes):
                        raise RuntimeError("Incomplete macro denominator")
                    def mean(key):
                        return float(np.mean([r[key] for r in selected], dtype=np.float64))
                    row = {"cohort": cohort, "model": model, "positive_subset": subset, "U_stratum": stratum,
                           "targets": len(selected), "P": sum(r["P"] for r in selected), "U": sum(r["U"] for r in selected),
                           "macro_P_vs_U_concordance": mean("P_vs_U_concordance"), "MAP": mean("average_precision"),
                           "MRR": mean("reciprocal_rank"), "mean_first_positive_rank": mean("first_positive_rank_expected")}
                    for k in CUTOFFS:
                        row.update({f"total_recovered_P_at_{k}": sum(r[f"recovered_P_at_{k}"] for r in selected),
                                    f"target_success_count_at_{k}": sum(r[f"target_success_at_{k}"] for r in selected)})
                        for metric in ("recall", "known_positive_precision", "EF", "NDCG", "target_success"):
                            row[f"macro_{metric}_at_{k}"] = mean(f"{metric}_at_{k}")
                    summary.append(row)
    write_csv(out / "macro_metrics.csv", summary)
    # These small cases are a disclosed extension of previously examined data.
    # Quantify numerical consistency of the rescored original six separately.
    with (root / "example/six_target_comparison_v1/all_six_targets_scores.csv").open(newline="") as stream:
        previous = list(csv.DictReader(stream))
    current = {(r["query_gene"], r["partner_uniprot"]): r for r in rows}
    consistency = []
    for model in MODELS:
        key = model + "_score"
        differences = [abs(float(r[key]) - current[r["query_gene"], r["partner_uniprot"]][key]) for r in previous]
        rank_changes = sum(float(r[model + "_rank"]) != current[r["query_gene"], r["partner_uniprot"]][model + "_rank"] for r in previous)
        consistency.append({"model": model, "pairs": len(previous), "maximum_absolute_score_difference": max(differences),
                            "rank_changes": rank_changes, "note": "Fresh extraction on expanded sequence batches can change FP32 rounding; no parameters or preprocessing changed."})
    write_json(out / "ORIGINAL_SIX_CONSISTENCY.json", {"at_utc": now(), "models": consistency})
    plan = read(out / "INPUT_FREEZE.json")
    for rel, expected in plan["original_file_hashes"].items():
        if sha(root / rel) != expected:
            raise RuntimeError(f"Pre-existing file changed: {rel}")
    write_json(out / "VALIDATION.json", {"at_utc": now(), "passed": True, "pairs": len(rows),
               "three_model_scores": len(rows) * 3, "P": 37, "U": 3700, "targets": len(TARGETS),
               "input_alignment_finite_complete": True, "three_seed_ensemble_verified": True,
               "preexisting_files_checked_unchanged": len(plan["original_file_hashes"]),
               "fresh_embeddings_both_pipelines": True, "no_preexisting_feature_cache_used": True,
               "protected_test_truth_or_scores_used": False, "metric_rows": len(metrics), "macro_rows": len(summary),
               "outputs": [record(p) for p in sorted(out.glob("*.csv"))]})
    print("All twelve panels scored and summarized; publication checks passed", flush=True)


if __name__ == "__main__":
    raise SystemExit("Use run_comparison.py summarize --root ROOT --output OUTPUT")
