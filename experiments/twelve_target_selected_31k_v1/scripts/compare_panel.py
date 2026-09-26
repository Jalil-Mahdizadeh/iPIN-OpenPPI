"""Reproduce archived metrics and compare the fixed 31k ensemble on the same panel."""
from collections import defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analysis_outputs import SETS, SUBSETS, COHORTS, included
from run_comparison import TARGETS, MODELS as OLD_MODELS
from metrics import CUTOFFS, evaluate, positive_ranks
from panel_io import now, read, sha, table, verify_mounted, write_csv, write_json

OUT = Path("/output")
PANEL = Path("/panel")
NEW = "tuna_selected_31k"
MODELS = (*OLD_MODELS, NEW)
LABELS = dict(zip(MODELS, ("Original iPIN", "Optimized iPIN", "Previous retrained TUnA", "Original published TUnA", "Selected 31k TUnA")))
EXTRA_SUBSETS = ("exclude_all_five_prior_pairs", "exclude_all_five_prior_pairs_and_homomers")


def exposure_audit(rows):
    """Unordered exact-sequence and accession pair matches; no panel relabeling."""
    data = Path("/studydata")
    endpoints = read(data / "endpoints.json")
    meta = read(data / "sequences.json")
    assert endpoints == meta["sha256"]
    n = len(endpoints)
    index = {h: i for i, h in enumerate(endpoints)}
    accessions = defaultdict(list)
    for i, names in enumerate(meta["accessions"]):
        for name in names:
            accessions[name].append(i)

    def code(a, b):
        return min(a, b) * n + max(a, b)

    exact, accession = [], []
    for row in rows:
        a, b = (index.get(row[k + "_sequence_sha256"]) for k in ("query", "partner"))
        exact.append([] if a is None or b is None else [code(a, b)])
        accession.append([code(a, b) for a in accessions[row["query_uniprot"]] for b in accessions[row["partner_uniprot"]]])
    checks = [
        ("train_17k_P", "training_16799.npz", "p_a", "p_b", None),
        ("train_31k_P", "training_31188.npz", "p_a", "p_b", None),
        ("train_U_pool", "training_unlabeled.npz", "u_a", "u_b", None),
        ("selection_dev_legacy_P", "development/reconciled/C3.npz", "a", "b", True),
        ("selection_dev_legacy_U", "development/reconciled/C3.npz", "a", "b", False),
        ("selection_dev_added_P", "development/added/C3.npz", "a", "b", True),
        ("selection_dev_added_U", "development/added/C3.npz", "a", "b", False),
    ]
    audit = [{"row_index": i, **{k: row[k] for k in ("query_gene", "query_uniprot", "partner_gene", "partner_uniprot", "class")}}
             for i, row in enumerate(rows)]
    summary = {}
    for label, filename, akey, bkey, positive in checks:
        with np.load(data / filename, allow_pickle=False) as arrays:
            a, b = arrays[akey], arrays[bkey]
            if positive is not None:
                keep = arrays["positive"] == positive
                a, b = a[keep], b[keep]
            keys = np.unique(np.minimum(a, b) * n + np.maximum(a, b))
        for method, candidates in (("sequence", exact), ("accession", accession)):
            flat = np.array([key for group in candidates for key in group], dtype=np.int64)
            offsets = np.r_[0, np.cumsum([len(group) for group in candidates])]
            matches = np.isin(flat, keys, assume_unique=False)
            for i, row in enumerate(audit):
                row[label + "_" + method] = bool(matches[offsets[i]:offsets[i+1]].any())
        for row in audit:
            row[label] = row[label + "_sequence"] or row[label + "_accession"]
        summary[label] = {c: sum(row[label] and row["class"] == c for row in audit) for c in ("P", "U")}
    for row, flags in zip(rows, audit, strict=True):
        flags["newly_added_train_P"] = flags["train_31k_P"] and not flags["train_17k_P"]
        flags["selected_31k_prior_pair"] = any(flags[label] for label, *_ in checks if label != "train_17k_P")
        row["selected_31k_prior_pair"] = flags["selected_31k_prior_pair"]
        row["all_five_prior_pair"] = bool(row["prior_train_development_pair"] or row["original_tuna_prior_pair"] or flags["selected_31k_prior_pair"])
    for key in ("newly_added_train_P", "selected_31k_prior_pair"):
        summary[key] = {c: sum(row[key] and row["class"] == c for row in audit) for c in ("P", "U")}
    write_csv(OUT / "selected_31k_exposure.csv", audit)
    write_json(OUT / "EXPOSURE_AUDIT.json", {"at_utc": now(), "matching": "Unordered pairs; exact sequence identity OR shared annotated UniProt accession",
        "U_pool_overlap_is_potential_training_exposure": True,
        "selected_dev": "C3 reconciled legacy plus C3 added, used for the frozen checkpoint selection",
        "homology_overlap_assessed": False, "panel_labels_changed": False, "counts": summary})
    return summary


def candidate_list(panel, subset, name):
    def keep(row):
        if subset in EXTRA_SUBSETS:
            return not row["all_five_prior_pair"] and not (subset.endswith("and_homomers") and row["class"] == "P" and row["homomeric"])
        return included(row, subset)
    return [r for r in panel if keep(r) and (r["class"] == "P" or r["U_stratum"] in SETS[name])]


def verify_historical(filename, calculated, keys):
    historical = table(PANEL / filename)
    lookup = {tuple(str(r[k]) for k in keys): r for r in calculated}
    largest = 0.
    for old in historical:
        current = lookup[tuple(old[k] for k in keys)]
        for field, value in old.items():
            if isinstance(current[field], (int, float)):
                diff = abs(float(value) - current[field])
                largest = max(largest, diff)
                assert diff <= 2e-12, (filename, field, value, current[field])
            else:
                assert value == str(current[field]), (filename, field)
    return {"file": filename, "rows_reproduced": len(historical), "maximum_absolute_difference": largest, "passed": True}


def main():
    freeze = read("/freeze/INPUT_FREEZE.json")
    verify_mounted(freeze, {"panel", "studydata", "code"})
    assert sha(OUT / "selected_31k_scores.csv") == read(OUT / "SCORING_RUN.json")["score_sha256"]
    rows = read(PANEL / "pairs.json")
    archived = table(PANEL / "all_twelve_targets_scores.csv")
    fresh = table(OUT / "selected_31k_scores.csv")
    assert len(rows) == len(archived) == len(fresh) == 5587
    for i, (row, old, new) in enumerate(zip(rows, archived, fresh, strict=True)):
        for key, value in row.items():
            assert str(value) == old[key], (i, key)
        assert int(new["row_index"]) == i
        for key, value in old.items():
            if key.endswith("_score") or key.endswith("_rank"):
                row[key] = float(value)
        for key, value in new.items():
            if key.endswith("_score"):
                row[key] = float(value)
        seed_scores = [row[f"{NEW}_seed{s}_score"] for s in freeze["seeds"]]
        assert np.isfinite(seed_scores).all()
        assert np.mean(seed_scores, dtype=np.float64) == row[NEW + "_score"]
    for kind in ("ipin", "tuna"):
        prior = table(PANEL / f"{kind}_scores.csv")
        assert len(prior) == len(rows)
        for i, old in enumerate(prior):
            assert int(old["row_index"]) == i
            for key, value in old.items():
                if key.endswith("_score"):
                    assert float(value) == rows[i][key]
    exposure = exposure_audit(rows)
    metrics, ranks, coverage, curves = [], [], [], []
    for gene in TARGETS:
        panel = [r for r in rows if r["query_gene"] == gene]
        population = [r[NEW + "_score"] for r in panel]
        for row in panel:
            row[NEW + "_rank"] = positive_ranks(row[NEW + "_score"], population)["rank_mid"]
        for subset in (*SUBSETS, *EXTRA_SUBSETS):
            for name in SETS:
                selected = candidate_list(panel, subset, name)
                p = sum(r["class"] == "P" for r in selected)
                coverage.append({"target": gene, "positive_subset": subset, "candidate_set": name,
                                 "P": p, "U": len(selected) - p, "evaluated": bool(p)})
                if not p:
                    continue
                truth = np.array([r["class"] == "P" for r in selected], dtype=bool)
                for model in MODELS:
                    values = [r[model + "_score"] for r in selected]
                    result = evaluate(values, truth)
                    metrics.append({"target": gene, "model": model, "positive_subset": subset, "candidate_set": name, **result})
                    if subset == "all_P":
                        for row in selected:
                            if row["class"] == "P":
                                ranks.append({"query_gene": gene, "partner_gene": row["partner_gene"], "partner_uniprot": row["partner_uniprot"],
                                    "model": model, "candidate_set": name, "score": row[model + "_score"],
                                    **positive_ranks(row[model + "_score"], values)})
                        curve = evaluate(values, truth, tuple(range(1, 51)))
                        for k in range(1, 51):
                            curves.append({"target": gene, "model": model, "candidate_set": name, "K": k,
                                "P": p, "panel_size": len(selected), "recovered_P": curve[f"recovered_P_at_{k}"],
                                "recall": curve[f"recall_at_{k}"], "target_success": curve[f"target_success_at_{k}"]})
    macro = []
    for cohort, genes in COHORTS.items():
        for subset in (*SUBSETS, *EXTRA_SUBSETS):
            for name in SETS:
                for model in MODELS:
                    group = [r for r in metrics if r["target"] in genes and r["positive_subset"] == subset and r["candidate_set"] == name and r["model"] == model]
                    if not group:
                        continue
                    def mean(key):
                        return float(np.mean([r[key] for r in group], dtype=np.float64))
                    row = {"cohort": cohort, "model": model, "positive_subset": subset, "candidate_set": name,
                        "planned_targets": len(genes), "targets": len(group), "omitted_targets": ";".join(g for g in genes if g not in {r["target"] for r in group}),
                        "P": sum(r["P"] for r in group), "U": sum(r["U"] for r in group),
                        "macro_P_vs_U_concordance": mean("P_vs_U_concordance"), "MAP": mean("average_precision"),
                        "MRR": mean("reciprocal_rank"), "mean_first_positive_rank": mean("first_positive_rank_expected")}
                    for k in CUTOFFS:
                        row.update({f"total_recovered_P_at_{k}": sum(r[f"recovered_P_at_{k}"] for r in group),
                                    f"target_success_count_at_{k}": sum(r[f"target_success_at_{k}"] for r in group)})
                        for metric in ("recall", "known_positive_precision", "EF", "NDCG", "target_success"):
                            row[f"macro_{metric}_at_{k}"] = mean(f"{metric}_at_{k}")
                    macro.append(row)
    reproduced = [verify_historical("per_target_metrics.csv", metrics, ("target", "model", "positive_subset", "candidate_set")),
                  verify_historical("macro_metrics.csv", macro, ("cohort", "model", "positive_subset", "candidate_set")),
                  verify_historical("positive_partner_ranks.csv", ranks, ("query_gene", "partner_uniprot", "model", "candidate_set"))]
    comparisons = []
    for subset in (*SUBSETS, *EXTRA_SUBSETS):
        for name in SETS:
            for model in OLD_MODELS:
                for new in (r for r in metrics if r["model"] == NEW and r["positive_subset"] == subset and r["candidate_set"] == name):
                    old = next(r for r in metrics if r["target"] == new["target"] and r["model"] == model and r["positive_subset"] == subset and r["candidate_set"] == name)
                    record = {"target": new["target"], "positive_subset": subset, "candidate_set": name, "reference_model": model, "P": new["P"], "U": new["U"]}
                    for key in ("P_vs_U_concordance", "average_precision", "reciprocal_rank", "recovered_P_at_5", "recovered_P_at_10", "recovered_P_at_20"):
                        record.update({"reference_" + key: old[key], "selected_31k_" + key: new[key], "delta_" + key: new[key] - old[key]})
                    comparisons.append(record)
    for name, content in (("all_twelve_targets_scores.csv", rows), ("per_target_metrics.csv", metrics), ("macro_metrics.csv", macro),
                          ("positive_partner_ranks.csv", ranks), ("retrieval_curves.csv", curves), ("analysis_coverage.csv", coverage),
                          ("per_target_comparison.csv", comparisons)):
        write_csv(OUT / name, content)
    primary = [r for r in macro if r["cohort"] == "all_twelve" and r["positive_subset"] == "all_P"]
    write_csv(OUT / "primary_comparison.csv", primary)
    write_json(OUT / "VALIDATION.json", {"at_utc": now(), "passed": True, "historical_metric_reproduction": reproduced,
        "all_5587_panel_rows_and_metadata_preserved": True, "all_historical_scores_identical": True,
        "three_seed_mean_exact": True, "metric_code": "Unmodified example/twelve_target_comparison_v2/metrics.py",
        "historical_subsets": "Preserved original exposure flags; the two additional subsets conservatively remove newly audited 31k training/selection exposure for all five models"})
    plot(primary, metrics, curves)
    report(primary, macro, metrics, exposure)
    print("Comparison complete; historical metrics and positive ranks reproduced exactly within 2e-12", flush=True)
    print([(LABELS[r["model"]], round(r["macro_P_vs_U_concordance"], 6), r["total_recovered_P_at_10"]) for r in primary if r["candidate_set"] == "all_U"], flush=True)


def plot(primary, metrics, curves):
    colors = ("#8d99ae", "#457b9d", "#e9a23b", "#7662a8", "#00876c")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7), constrained_layout=True)
    for model, color in zip(MODELS, colors):
        series = []
        for k in range(1, 51):
            group = [r for r in curves if r["model"] == model and r["candidate_set"] == "all_U" and r["K"] == k]
            series.append(sum(r["recovered_P"] for r in group))
        axes[0].plot(range(1, 51), series, label=LABELS[model], color=color, linewidth=2)
    axes[0].set(xlabel="Candidates screened per target (K)", ylabel="Known positives retrieved (of 37)", title="Fixed 12-target panel: all U strata")
    axes[0].legend(fontsize=8)
    old = {r["target"]: r for r in metrics if r["model"] == "tuna_retrained" and r["positive_subset"] == "all_P" and r["candidate_set"] == "all_U"}
    new = {r["target"]: r for r in metrics if r["model"] == NEW and r["positive_subset"] == "all_P" and r["candidate_set"] == "all_U"}
    delta = np.array([new[g]["P_vs_U_concordance"] - old[g]["P_vs_U_concordance"] for g in TARGETS])
    axes[1].barh(TARGETS, delta, color=["#00876c" if v >= 0 else "#bb5566" for v in delta])
    axes[1].axvline(0, color="black", linewidth=.7)
    axes[1].invert_yaxis()
    axes[1].set(xlabel="31k minus previous retrained TUnA concordance", title="Change by target")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT / "comparison.png", dpi=180)
    fig.savefig(OUT / "comparison.pdf")
    plt.close(fig)


def report(primary, macro, metrics, exposure):
    def summary_row(model, candidate="all_U", subset="all_P"):
        return next(r for r in macro if r["model"] == model and r["cohort"] == "all_twelve" and r["candidate_set"] == candidate and r["positive_subset"] == subset)
    old, new = summary_row("tuna_retrained"), summary_row(NEW)
    selected = {r["target"]: r for r in metrics if r["model"] == NEW and r["candidate_set"] == "all_U" and r["positive_subset"] == "all_P"}
    previous = {r["target"]: r for r in metrics if r["model"] == "tuna_retrained" and r["candidate_set"] == "all_U" and r["positive_subset"] == "all_P"}
    wins = sum(selected[g]["P_vs_U_concordance"] > previous[g]["P_vs_U_concordance"] for g in TARGETS)
    lines = ["# Selected 31k TUnA: unchanged 12-target panel", "",
        f"Completed {now()}. The selected 31,188-positive, epoch-1 ensemble was scored on all 5,587 historical pairs (37 P, 5,550 U; 12 targets).",
        "",
        f"Against the previous frozen retrained TUnA, all-U macro P-versus-U concordance changed from {old['macro_P_vs_U_concordance']:.6f} to {new['macro_P_vs_U_concordance']:.6f} ({new['macro_P_vs_U_concordance']-old['macro_P_vs_U_concordance']:+.6f}); {wins}/12 targets improved. Known positives recovered at 10 candidates per target changed from {old['total_recovered_P_at_10']:g}/37 to {new['total_recovered_P_at_10']:g}/37.", "",
        "The source is `example/twelve_target_comparison_v2`, the latest established panel. Pairs, frozen sequence snapshot, P/U labels, U strata, and old predictions are unchanged. The context+background subset is reported separately to retain the older candidate population. U means unlabeled, not experimentally confirmed negative; these are retrieval results on nominated positives, not estimates of biological precision.", "",
        "## All three U strata", "", "| Model | Macro P/U concordance | MAP | MRR | P@5 /37 | P@10 /37 | P@20 /37 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for model in MODELS:
        r = summary_row(model)
        lines.append(f"| {LABELS[model]} | {r['macro_P_vs_U_concordance']:.6f} | {r['MAP']:.6f} | {r['MRR']:.6f} | {r['total_recovered_P_at_5']:g} | {r['total_recovered_P_at_10']:g} | {r['total_recovered_P_at_20']:g} |")
    lines += ["", "P@K here is the total number of nominated positives recovered across 12 separate top-K lists. Metrics use the original tie rules and equal target weighting.", "", "## Candidate-set comparison", "",
        "| U candidate set | Original iPIN | Optimized iPIN | Previous retrained TUnA | Original TUnA | Selected 31k | Delta vs previous retrained |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name in SETS:
        rs = [summary_row(m, name) for m in MODELS]
        lines.append("| " + name + " | " + " | ".join(f"{r['macro_P_vs_U_concordance']:.6f}" for r in rs) + f" | {rs[-1]['macro_P_vs_U_concordance']-rs[2]['macro_P_vs_U_concordance']:+.6f} |")
    lines += ["", "## Changes by target, all U", "", "| Target | Previous retrained P/U | Selected 31k P/U | Delta | Previous P@10 | Selected P@10 |", "|---|---:|---:|---:|---:|---:|"]
    for gene in TARGETS:
        a, b = previous[gene], selected[gene]
        lines.append(f"| {gene} | {a['P_vs_U_concordance']:.6f} | {b['P_vs_U_concordance']:.6f} | {b['P_vs_U_concordance']-a['P_vs_U_concordance']:+.6f} | {a['recovered_P_at_10']:g} | {b['recovered_P_at_10']:g} |")
    lines += ["", "## Prior exposure", "",
        "The main table preserves the complete historical panel. It is not an independent held-out benchmark. The new audit checks unordered exact-sequence pairs and annotated UniProt accession pairs against the 31k training P, training U pool, and the C3 development populations used for checkpoint selection. Training-U membership indicates potential sampling exposure. This audit does not measure homology exposure.", "",
        "| New-model overlap | Panel P | Panel U |", "|---|---:|---:|"]
    for key, count in exposure.items():
        lines.append(f"| {key} | {count['P']} | {count['U']} |")
    lines += ["", "A common sensitivity analysis removes the union of historical prior-pair flags and newly audited 31k exposure from every model's candidate lists. Target coverage can fall when no P remains; it is reported explicitly and should not be compared directly with the 12-target headline.", "",
        "| Common exposure-excluded subset, all U | Model | Targets | P | U | Macro P/U | MAP | P@10 |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for subset in EXTRA_SUBSETS:
        for model in MODELS:
            matches = [r for r in macro if r["cohort"] == "all_twelve" and r["positive_subset"] == subset and r["candidate_set"] == "all_U" and r["model"] == model]
            if matches:
                r = matches[0]
                lines.append(f"| {subset} | {LABELS[model]} | {r['targets']} | {r['P']} | {r['U']} | {r['macro_P_vs_U_concordance']:.6f} | {r['MAP']:.6f} | {r['total_recovered_P_at_10']:g} |")
    lines += ["", "## Reproducibility", "",
        "The three selected checkpoint seeds are 20260803, 20260817, and 20260831. All checkpoint hashes match `human_ppi_data_scaling_v1/runs/SELECTION.json` and `SCORER_FREEZE.json`. No training or checkpoint selection was performed here.", "",
        "Historical FP32, full-length ESM residue embeddings were verified and reused; 4,012 learned endpoint features were recomputed for each selected seed. Scores are mean-field-adjusted logits, averaged in float64 across seeds. The loaded GP `fitted` flag is set before `eval()` so the exact saved covariance is retained, as established in the completed study's scorer-replay review. No covariance refit was performed.", "",
        "Each seed passed native pair-forward agreement (13 panel fixtures, tolerance 1e-5), exact pair-order symmetry, and equality of all checkpoint parameters and buffers before/after inference. Every archived per-target metric, macro metric, and positive rank was reproduced within 2e-12 from the unchanged old scores. Historical files were mounted read-only. See the run-level `PRESERVATION.json` for final input-hash and tracked-status verification.", "",
        "Outputs: `all_twelve_targets_scores.csv` (all old and new scores); `primary_comparison.csv`; `per_target_comparison.csv`; `per_target_metrics.csv`; `macro_metrics.csv`; `positive_partner_ranks.csv`; `selected_31k_exposure.csv`; `retrieval_curves.csv`; `comparison.png` and `comparison.pdf`. The historical sensitivity subsets retain their original definitions; only the two explicitly named `exclude_all_five_prior_pairs` subsets incorporate this run's new exposure audit.", ""]
    (OUT / "REPORT.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
