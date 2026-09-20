#!/usr/bin/env python3
"""Render complete comparison tables and exportable scientific figures."""
from collections import Counter
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from run_comparison import MODELS, TARGETS, read, write_csv, write_json, now

HERE = Path(__file__).resolve().parent
LABELS = {"ipin_baseline": "Original iPIN", "ipin_optimized": "Optimized iPIN", "tuna_retrained": "TUnA-retrained", "tuna_original": "Original TUnA"}
SETS = ("context", "background", "low_plausibility", "context_background", "all_U")
SET_LABELS = {"context": "Context", "background": "Background", "low_plausibility": "Low plausibility", "context_background": "Context + background", "all_U": "All U"}
COLORS = ("#3366AA", "#D97823", "#238B67", "#99529B", "#333333")


def table(name):
    with (HERE / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def md_table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
                     + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def write(path, text):
    with path.open("x") as stream:
        stream.write(text.rstrip() + "\n")


def save(fig, stem):
    for extension in ("png", "pdf", "svg"):
        path = HERE / f"{stem}.{extension}"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def main():
    root = HERE.parents[1]
    validation = read(HERE / "INDEPENDENT_VALIDATION.json")
    assert validation["passed"]
    macro, metrics, curves = table("macro_metrics.csv"), table("per_target_metrics.csv"), table("retrieval_curves.csv")
    annotations, scores = table("low_plausibility_annotations.csv"), table("all_twelve_targets_scores.csv")
    main_rows = [r for r in macro if r["cohort"] == "all_twelve" and r["positive_subset"] == "all_P"]
    lookup = {(r["model"], r["candidate_set"]): r for r in main_rows}
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "svg.hashsalt": "ipin-v2-150U"})
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for axis, (key, title) in zip(axes.flat, (("macro_P_vs_U_concordance", "P-versus-U concordance"), ("MAP", "Mean average precision"),
                                           ("macro_recall_at_10", "Mean known-positive recall @10"), ("macro_NDCG_at_10", "Mean NDCG @10"))):
        x = np.arange(5)
        for i, model in enumerate(MODELS):
            axis.bar(x + (i - 1.5) * .19, [float(lookup[model, s][key]) for s in SETS], width=.18, label=LABELS[model], color=COLORS[i])
        axis.set_xticks(x, ["Context", "Background", "Low\nplausibility", "Context +\nbackground", "All U"])
        axis.set_title(title)
        axis.set_ylim(0, 1)
        axis.grid(axis="y", alpha=.2)
    axes[0, 0].legend(fontsize=9, loc="lower left")
    fig.suptitle("Twelve targets · 37 nominated positives · four unchanged predictors\nEqual-target averages; U is unlabeled; 139 weaker-tier EGFR candidates", fontsize=13)
    fig.tight_layout()
    save(fig, "candidate_set_metrics")
    fig, axes = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    for axis, model in zip(axes.flat, MODELS):
        values = np.array([[float(next(r["P_vs_U_concordance"] for r in metrics if r["model"] == model and r["target"] == g and r["candidate_set"] == s and r["positive_subset"] == "all_P")) for s in SETS] for g in TARGETS])
        image = axis.imshow(values, vmin=0, vmax=1, cmap="viridis", aspect="auto")
        axis.set_title(LABELS[model])
        axis.set_yticks(range(12), TARGETS)
        axis.set_xticks(range(5), ["Context", "Background", "Low U", "C + B", "All U"], rotation=25, ha="right")
        for (y, x), value in np.ndenumerate(values):
            axis.text(x, y, f"{value:.2f}", ha="center", va="center", color="white" if value < .65 else "black", fontsize=8)
    fig.suptitle("Target-specific P-versus-U concordance\nSame positives across five candidate sets; EGFR low-U includes the weaker tier")
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=.7, label="Concordance", pad=.02)
    save(fig, "per_target_concordance")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True, sharey=True)
    for axis, model in zip(axes.flat, MODELS):
        for s, color in zip(SETS, COLORS):
            values = [np.mean([float(r["recall"]) for r in curves if r["model"] == model and r["candidate_set"] == s and int(r["K"]) == k]) for k in range(1, 51)]
            axis.plot(range(1, 51), values, color=color, label=SET_LABELS[s], lw=1.8)
        axis.set_title(LABELS[model]); axis.set_ylim(0, 1); axis.grid(alpha=.2)
        axis.set_xlabel("Pairs screened per target"); axis.set_ylabel("Mean known-positive recall")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Known-positive retrieval curves across all five candidate sets")
    fig.tight_layout()
    save(fig, "retrieval_curves")
    tiers = Counter(r["evidence_tier"] for r in annotations)
    qualities = Counter(r["annotation_quality"] for r in annotations)
    reused = Counter(r["sequence_sha256"] for r in annotations)
    evidence_summary = []
    for gene in TARGETS:
        rr = [r for r in annotations if r["target"] == gene]
        evidence_summary.append({"target": gene, "new_U": len(rr), "tier_A": sum(r["evidence_tier"].startswith("A_") for r in rr),
                                 "tier_B": sum(r["evidence_tier"].startswith("B_") for r in rr),
                                 **{f"annotation_quality_{i}": sum(r["annotation_quality"] == str(i) for r in rr) for i in range(4)},
                                 "median_length_ratio": float(np.median([float(r["length_ratio"]) for r in rr])),
                                 "min_length_ratio": min(float(r["length_ratio"]) for r in rr), "max_length_ratio": max(float(r["length_ratio"]) for r in rr)})
    write_csv(HERE / "selection_summary.csv", evidence_summary)
    # Descriptive within-model score distributions; no common score threshold.
    distributions = []
    for gene in TARGETS:
        for model in MODELS:
            for group in ("P", "context", "background", "low_plausibility"):
                values = np.array([float(r[model + "_score"]) for r in scores if r["query_gene"] == gene and (r["class"] == "P" if group == "P" else r["U_stratum"] == group)])
                distributions.append({"target": gene, "model": model, "group": group, "n": len(values),
                                      "mean": float(values.mean()), "sd": float(values.std(ddof=1)),
                                      "q25": float(np.quantile(values, .25)), "median": float(np.median(values)), "q75": float(np.quantile(values, .75)),
                                      "min": float(values.min()), "max": float(values.max())})
    write_csv(HERE / "score_distributions.csv", distributions)
    comparison = []
    for model in MODELS:
        old, new, low = (lookup[model, s] for s in ("context_background", "all_U", "low_plausibility"))
        comparison.append({"model": model, "previous_100U_concordance": float(old["macro_P_vs_U_concordance"]),
                           "added_50U_concordance": float(low["macro_P_vs_U_concordance"]), "all_150U_concordance": float(new["macro_P_vs_U_concordance"]),
                           "concordance_change": float(new["macro_P_vs_U_concordance"]) - float(old["macro_P_vs_U_concordance"]),
                           "MAP_change": float(new["MAP"]) - float(old["MAP"]),
                           "recovered_P_at_10_change": float(new["total_recovered_P_at_10"]) - float(old["total_recovered_P_at_10"]),
                           "NDCG_at_10_change": float(new["macro_NDCG_at_10"]) - float(old["macro_NDCG_at_10"])})
    write_csv(HERE / "candidate_set_changes.csv", comparison)
    report = ["# Twelve targets, three U strata and four frozen predictors", "",
              "Completed descriptive application: **37 P + 5,550 U = 5,587 pairs**, scored by the three frozen iPIN models and original published TUnA. Each positive has 50 context, 50 background and 50 low-plausibility U. Original TUnA remains a comparator; the iPIN registry still contains three models.", "",
              "Across the twelve targets, all 3,737 original rows are preserved as prefixes of the extended panels. Selection used biological annotations and exclusion records before new scores. Every sequence was freshly retrieved and both embedding pipelines recomputed for 4,012 unique sequences. [Input freeze](INPUT_FREEZE.json), [selection protocol](SELECTION.md), [metric protocol](METRICS.md), and [independent validation](INDEPENDENT_VALIDATION.json) provide the audit trail.", "",
              "## Evidence and interpretation", "",
              f"Of 1,850 additions, **{tiers['A_compartment_separation']:,} are tier A** (annotated compartment separation) and **{tiers['B_secondary_location_overlap']:,} are tier B**, all for EGFR. Tier B is a weaker dominant-location prior with known nuclear/mitochondrial overlap, not spatial incompatibility. The user approved keeping 50 using explicit tiers. Neither tier is a verified negative.", "",
              f"The additions use {len(reused)} unique candidate sequences; {sum(v > 1 for v in reused.values())} recur across targets. Annotation quality counts: dual UniProt-experimental/HPA support {qualities['0']}; UniProt experimental only {qualities['1']}; HPA-supported plus reviewed UniProt {qualities['2']}; reviewed-only fallback {qualities['3']}. Every row has provenance in [low_plausibility_annotations.csv](low_plausibility_annotations.csv), with target-level counts in [selection_summary.csv](selection_summary.csv).", "",
              "## All five candidate sets", "",
              "Equal-target averages over all twelve targets and all 37 P. PU = P-versus-U concordance. MAP and MRR average target-level AP and reciprocal rank. Larger is better except first-positive rank. Original TUnA's sigmoid scores retain saturation ties.", ""]
    report.append(md_table(["Candidate set", "Model", "PU", "MAP", "MRR", "Mean first P rank"],
        [[SET_LABELS[s], LABELS[m], *[f"{float(lookup[m,s][key]):.4f}" for key in ("macro_P_vs_U_concordance", "MAP", "MRR", "mean_first_positive_rank")]] for s in SETS for m in MODELS]))
    report += ["", "![Candidate-set metrics](candidate_set_metrics.png)", "", "### Fixed screening budgets", "",
               "Recovered P is summed across targets, out of 37. Recall, known-positive precision, EF and NDCG are equal-target means. Success is expected successful targets out of 12, with exact fractional tie credit.", ""]
    for k in (5, 10, 20):
        report += [f"#### K = {k}", "", md_table(["Set", "Model", "Recovered P /37", "Recall", "Known-P precision", "EF", "NDCG", "Success /12"],
            [[SET_LABELS[s], LABELS[m], *[f"{float(lookup[m,s][key]):.4f}" for key in (f"total_recovered_P_at_{k}", f"macro_recall_at_{k}", f"macro_known_positive_precision_at_{k}", f"macro_EF_at_{k}", f"macro_NDCG_at_{k}", f"target_success_count_at_{k}")]] for s in SETS for m in MODELS]), ""]
    report += ["## What changes when the new U are added?", "", md_table(["Model", "PU: original 100 U", "PU: added 50 U", "PU: all 150 U", "Δ MAP", "Δ recovered P @10"],
        [[LABELS[r['model']], *[f"{r[k]:.4f}" for k in ("previous_100U_concordance", "added_50U_concordance", "all_150U_concordance", "MAP_change", "recovered_P_at_10_change")]] for r in comparison]), "",
        "Adding the new U raises macro concordance for every model, while MAP falls slightly and total top-10 recovery stays at 4, 7, 7 and 10 positives for original iPIN, optimized iPIN, TUnA-retrained and original TUnA, respectively. These changes use the same newly computed scores. Adding low-scoring U can raise concordance without improving discovery: `C150 = (2*C100 + Clow)/3`. Additional U can only preserve or worsen individual positive ranks; EF can rise because the known-positive prevalence falls. AP and top-K recovery measure different effects. This is a candidate-composition comparison, not a new model training result or evidence that any U is a noninteraction.", "",
        "![Per-target concordance](per_target_concordance.png)", "", "![Retrieval curves](retrieval_curves.png)", "",
        "## Exposure and evidence sensitivities", "",
        "All 1,850 additions are absent from checked iPIN TRAIN/development and documented original-TUnA training/validation pairs, by accession and exact sequence. Preserved data contain three iPIN-exposed positives (KEAP1–SQSTM1, BECN1–ATG14 and BECN1–UVRAG), six original-TUnA-exposed positives, and 22 original-TUnA-exposed U. See [exposed_pairs.csv](exposed_pairs.csv); exact original-TUnA roles/labels are retained per row in the panel manifests. Exposure audits are not complete training-history, homology or pretraining audits.", "",
        "The five previous P subsets and two common four-model exposure sensitivities appear for every candidate set in [per_target_metrics.csv](per_target_metrics.csv) and [macro_metrics.csv](macro_metrics.csv). In the common exposure sensitivity BCL2 has no P left and is explicitly omitted; [analysis_coverage.csv](analysis_coverage.csv) records undefined cells and macro rows name missing targets. Removed P are never relabeled U.", "",
        "The following sensitivity removes EGFR entirely so all included additions use tier A; the same eleven targets are used for every set and model.", ""]
    strict = {(r["model"], r["candidate_set"]): r for r in macro if r["cohort"] == "strict_evidence_eleven" and r["positive_subset"] == "all_P"}
    report.append(md_table(["Model", *[SET_LABELS[s] for s in SETS]], [[LABELS[m], *[f"{float(strict[m,s]['macro_P_vs_U_concordance']):.4f}" for s in SETS]] for m in MODELS]))
    clean = [r for r in macro if r["cohort"] == "all_twelve" and r["positive_subset"] == "exclude_any_model_prior_pairs_and_homomers"]
    report += ["", "The common exposure/homomer sensitivity below removes prior pairs for all four models, including exposed U. Denominators differ from the main result.", "",
               md_table(["Set", "Model", "Targets", "P", "U", "PU", "MAP"], [[SET_LABELS[r['candidate_set']], LABELS[r['model']], r['targets'], r['P'], r['U'], f"{float(r['macro_P_vs_U_concordance']):.4f}", f"{float(r['MAP']):.4f}"] for r in clean]), "",
               "## Files and validation", "",
               "- [All scores](all_twelve_targets_scores.csv): 22,348 model-level scores, plus seed scores and full-panel ranks.",
               "- [Per-target metrics](per_target_metrics.csv), [macro metrics](macro_metrics.csv), [matched-positive metrics](matched_positive_metrics.csv), [positive ranks](positive_partner_ranks.csv), and [curves](retrieval_curves.csv).",
               "- [Within-model score distributions](score_distributions.csv) and [candidate-set changes](candidate_set_changes.csv).",
               "- Figures also have PDF and SVG exports with the same filename stems.",
               "- [Previous-run consistency](PREVIOUS_RUN_CONSISTENCY.json) checks scores and ranks in the preserved old lists; fresh FP32 batch rounding is disclosed.",
               f"- Independent recomputation passed for {validation['metric_rows_recomputed']:,} target metric rows, {validation['matched_rows_recomputed']:,} matched rows, {validation['macro_rows_verified']:,} macro rows, {validation['rank_rows_verified']:,} positive-rank rows, and {validation['curve_rows_recomputed']:,} curve rows.",
               "- [Evidence reconciliation](EVIDENCE_VALIDATION.json) independently checked all 1,850 rows against the original UniProt and HPA tables.",
               "- Four native TUnA forward qualifications, pair-order symmetry, immutable parameters/GP buffers, and fresh embedding artifacts were checked. Frozen model registry verification passed before and after inference; the completed manifest records both results.", "",
               "These twelve selected targets are not independent random samples. Candidate reuse, exposure, localization uncertainty, and deliberately altered sampling limit generalization. No inferential superiority claim or interaction-probability estimate is made."]
    write(HERE / "REPORT.md", "\n".join(report))
    target_links = []
    for gene in TARGETS:
        rr = [r for r in metrics if r["target"] == gene and r["positive_subset"] == "all_P"]
        by_key = {(r["model"], r["candidate_set"]): r for r in rr}
        target = f"# {gene}: expanded four-model results\n\n" + (
            f"Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). "
            "The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. "
            "U remains unknown; EGFR includes an explicitly weaker evidence tier.\n\n")
        target += md_table(["Set", "Model", "PU", "AP", "RR", "Recovered P @10", "Recall @10", "NDCG @10"],
            [[SET_LABELS[s], LABELS[m], *[f"{float(by_key[m,s][key]):.4f}" for key in ("P_vs_U_concordance", "average_precision", "reciprocal_rank", "recovered_P_at_10", "recall_at_10", "NDCG_at_10")]] for s in SETS for m in MODELS])
        target += (f"\n\n[Expanded input](../twelve_target_comparison_v2/panels/{gene}/{gene.lower()}_ipin_panel.csv) · "
                   f"[Evidence manifest](../twelve_target_comparison_v2/panels/{gene}/panel_manifest.json) · "
                   f"[Four-model scores](../twelve_target_comparison_v2/{gene.lower()}_four_model_scores.csv) · "
                   "[All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)\n")
        write(root / "example" / gene / "RESULTS_v3.md", target)
        target_links.append([gene, 4 if gene == "ERN1" else 3, 600 if gene == "ERN1" else 450, f"[Results](../{gene}/RESULTS_v3.md)"])
    readme = "# Expanded twelve-target application\n\n" + (
        "**Current example comparison: 37 P + 5,550 U, four predictors, five candidate sets.** "
        "Start with the [report](REPORT.md), [selection rules](SELECTION.md), and [metric definitions](METRICS.md). "
        "Original TUnA is an external comparator; TUnA-retrained remains the third frozen iPIN model.\n\n")
    readme += md_table(["Target", "P", "U", "Details"], target_links)
    readme += "\n\n## Reproduction\n\n" + (
        "Run scientific Python inside the pinned data/model/TUnA Apptainer images listed in `RUN_MANIFEST.json`. "
        "GPU phases require one allocated GPU. Mount the project read-only at `/project`, with only this new output directory writable at the same path. "
        "All scientific outputs use exclusive creation; do not rerun phases over a completed run. "
        "Use a new version directory and retain exact source/implementation hashes.\n\n"
        "1. `fetch_sources.py` retrieves annotation sources.\n"
        "2. `build_panels.py --root /project --allow-secondary-overlap` selects new U without scores.\n"
        "3. `run_comparison.py prepare --root /project --output /project/example/twelve_target_comparison_v2` freezes panels, fresh sequences, metrics and scoring code.\n"
        "4. Run the same driver with phase `ipin` in the iPIN model SIF, then `tuna` in the TUnA SIF. Both recompute embeddings.\n"
        "5. Run `summarize`, `validate_results.py`, `render_report.py`, and `finish_run.py` in the TUnA SIF.\n\n"
        "Selection needs network access. GPU runs use `--nv`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `TOKENIZERS_PARALLELISM=false`, "
        "`CUBLAS_WORKSPACE_CONFIG=:4096:8`, and `PYTHONDONTWRITEBYTECODE=1`. Use `PYTHONPATH=/project/src` for pooled iPIN and `/opt/tuna/vendor` for TUnA. "
        "Fresh HDF5/NumPy embeddings, model weights and raw sources stay local and are not committed.\n\n"
        "Historical records: [twelve-target v1](../twelve_target_comparison_v1/REPORT.md), "
        "[six-target four-model run](../six_target_comparison_v1/REPORT.md), and "
        "[context/background score analysis](../u_context_background_analysis_v1/REPORT.md).\n")
    write(HERE / "README.md", readme)
    write_json(HERE / "REPORT_BUILD.json", {"at_utc": now(), "matplotlib": matplotlib.__version__, "report_generated_from_validated_scores": True,
               "candidate_sequences_in_new_U": len(reused), "new_candidate_sequences_reused_across_targets": sum(v > 1 for v in reused.values()),
               "annotation_quality_counts": dict(qualities), "evidence_tiers": dict(tiers)})
    print("Reports, twelve target pages and three figure sets generated", flush=True)


if __name__ == "__main__":
    main()
