#!/usr/bin/env python3
"""Render documentation and standalone figures from independently verified CSVs."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

MODELS = ("ipin_baseline", "ipin_optimized", "tuna_retrained")
LABELS = ("Original iPIN", "Optimized iPIN", "TUnA-retrained")
COLORS = ("#2463a6", "#de791c", "#23846d")


def read(path):
    return json.loads(path.read_text())


def table(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def markdown(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |",
                      *["| " + " | ".join(map(str, row)) + " |" for row in rows]])


def f(value):
    return str(Decimal(str(round(float(value), 12))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root, args.output
    validation = read(out / "INDEPENDENT_VALIDATION.json")
    assert validation["passed"]
    freeze, config = read(out / "INPUT_FREEZE.json"), read(out / "panel_config.json")
    targets = config["original_targets"] + [t["gene"] for t in config["new_targets"]]
    metrics, macro, ranks = (table(out / name) for name in ("per_target_metrics.csv", "macro_metrics.csv", "positive_partner_ranks.csv"))
    main_rows = [r for r in metrics if r["positive_subset"] == "all_P" and r["U_stratum"] == "all_U"]
    summary = [r for r in macro if r["cohort"] == "all_twelve" and r["positive_subset"] == "all_P" and r["U_stratum"] == "all_U"]
    mapping = {(r["target"], r["model"]): r for r in main_rows}
    curves = table(out / "retrieval_curves.csv")
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 10), gridspec_kw={"height_ratios": [1.5, 1.]}, constrained_layout=True)
    for ax, metric, title in ((axes[0, 0], "P_vs_U_concordance", "P-versus-U concordance"), (axes[0, 1], "average_precision", "Known-positive average precision")):
        values = np.asarray([[float(mapping[gene, model][metric]) for model in MODELS] for gene in targets])
        im = ax.imshow(values, vmin=0, vmax=1, cmap="Blues", aspect="auto")
        ax.set_xticks(range(3), LABELS, fontsize=9)
        ax.set_yticks(range(12), [gene + (" *" if gene in ("KEAP1", "BECN1") else "") for gene in targets])
        ax.set_title(title, loc="left", fontweight="bold")
        ax.axhline(5.5, color="#de791c", linewidth=1.8)
        for i in range(12):
            for j in range(3):
                ax.text(j, i, f(values[i, j]), ha="center", va="center", color="white" if values[i, j] > .6 else "#111111", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=.035, pad=.025)
    for ax, field, title in ((axes[1, 0], "recall", "Mean known-positive recall"), (axes[1, 1], "target_success", "Fraction of targets with at least one recovered P")):
        for model, label, color in zip(MODELS, LABELS, COLORS, strict=True):
            values = [np.mean([float(r[field]) for r in curves if r["model"] == model and int(r["K"]) == k]) for k in range(1, 51)]
            ax.step(range(1, 51), values, where="post", label=label, color=color, linewidth=2)
        for k in (5, 10, 20):
            ax.axvline(k, color="#aaaaaa", linewidth=.7, linestyle=":")
        ax.set(title=title, xlabel="Candidates screened per target (K)", ylabel="Equal-target mean", ylim=(0, 1.02), xlim=(1, 50))
        ax.grid(axis="y", alpha=.2)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Twelve human target panels · three frozen iPIN models", fontsize=15, fontweight="bold")
    fig.supxlabel("37 nominated positives + 3,700 unlabeled pairs. * Known TRAIN/development exposure; see sensitivity results.\nOrange divider separates the original six targets from the six additions. U is not a verified negative.", fontsize=9)
    for extension in ("pdf", "svg", "png"):
        fig.savefig(out / f"retrieval_summary.{extension}", dpi=180)
    plt.close(fig)
    main_table = markdown(["Model", "PU concordance", "MAP", "MRR", "Recall@5", "Recall@10", "Recall@20", "NDCG@10", "NDCG@20", "EF@20", "Targets with P@20"],
        [[LABELS[MODELS.index(r["model"])], *[f(r[key]) for key in ("macro_P_vs_U_concordance", "MAP", "MRR", "macro_recall_at_5", "macro_recall_at_10", "macro_recall_at_20", "macro_NDCG_at_10", "macro_NDCG_at_20", "macro_EF_at_20")], f"{float(r['target_success_count_at_20']):g}/12"] for r in summary])
    target_table = markdown(["Target", "P / U", *LABELS], [[f"[{gene}](../{gene}/RESULTS_v2.md)", "4 / 400" if gene == "ERN1" else "3 / 300", *[f(mapping[gene, model]["P_vs_U_concordance"]) for model in MODELS]] for gene in targets])
    sensitivity = [r for r in macro if r["cohort"] == "all_twelve" and r["U_stratum"] == "all_U" and r["positive_subset"] in ("all_P", "exclude_prior_train_development_P", "exclude_prior_train_development_P_and_homomers")]
    sensitivity_table = markdown(["Positive subset", "Model", "P", "PU concordance", "MAP", "Recall@20"], [[r["positive_subset"], LABELS[MODELS.index(r["model"])], r["P"], f(r["macro_P_vs_U_concordance"]), f(r["MAP"]), f(r["macro_recall_at_20"])] for r in sensitivity])
    cohort_rows = [r for r in macro if r["cohort"] != "all_twelve" and r["positive_subset"] == "all_P" and r["U_stratum"] == "all_U"]
    cohort_table = markdown(["Cohort", "Model", "PU concordance", "MAP", "Recall@20"], [[r["cohort"], LABELS[MODELS.index(r["model"])], f(r["macro_P_vs_U_concordance"]), f(r["MAP"]), f(r["macro_recall_at_20"])] for r in cohort_rows])
    observed = read(out / "ORIGINAL_SIX_CONSISTENCY.json")["models"]
    max_error = max(r["maximum_absolute_score_difference"] for r in observed)
    rank_changes = sum(r["rank_changes"] for r in observed)
    report = f"""# Twelve-target comparison of the three frozen iPIN models

The example application now contains **12 human targets, 37 nominated positives,
and 3,700 unlabeled pairs**. All 3,737 pairs were scored by original iPIN,
optimized pooled iPIN, and TUnA-retrained, using the unchanged
[three-model catalogue](../../docs/models/FROZEN_PAIR_MODELS_v2.md).
These are descriptive biological retrieval cases; no model was selected or tuned.

The additional targets are KRAS, CDK2, HIF1A, CTNNB1, TNFRSF1A, and BECN1.
Their evidence, canonical identities, selection rules, source checksums, and
exposure records are retained in each target folder. All original six inputs and
their [historical four-predictor comparison](../six_target_comparison_v1/REPORT.md)
are preserved. Original released TUnA is a historical comparator, not one of the
three frozen iPIN models scored in this extension.

## Equal-target results

Higher is better for the metrics below. Every target has equal weight. MAP is
mean average precision; MRR concerns the first known partner; recall concerns
the nominated positives. All cutoff metrics are available at K=5,10,20, including
known-positive precision and successful-target counts. Definitions and tie rules
are in [METRICS.md](METRICS.md); complete results are in [macro_metrics.csv](macro_metrics.csv).

{main_table}

TUnA-retrained has the highest mean PU concordance and MAP in the main panel.
Optimized iPIN recovers the most nominated positives within the top 20:
**13/37**, compared with **9/37** for original iPIN and **9/37** for TUnA-retrained.
Model ordering therefore depends on the retrieval objective. The exposure
sensitivities below are part of the interpretation of these main-panel values.

![Twelve-target retrieval summary](retrieval_summary.png)

Standalone exports: [PDF](retrieval_summary.pdf) and [SVG](retrieval_summary.svg).

## Individual targets: P-versus-U concordance

{target_table}

Each linked target report also gives AP, first-positive rank, reciprocal rank,
recovered counts, recall, NDCG, enrichment, and target success. Full stratum and
sensitivity metrics are in [per_target_metrics.csv](per_target_metrics.csv).
[Positive ranks](positive_partner_ranks.csv), [matched positive-control metrics](matched_positive_metrics.csv),
and [screening-budget curves](retrieval_curves.csv) retain the underlying detail.

## Exposure and sensitivity

The exact-pair audit identified **BECN1-ATG14 and BECN1-UVRAG in TRAIN-P**, and
the existing **KEAP1-SQSTM1 pair in DEV-P**. All U candidates are absent from the
checked TRAIN/development P and U arrays by accession and exact sequence.
Exposure results were recorded before scoring; nominated partners were not
replaced using model performance. The main result also retains the original
ERN1 homodimer. Sensitivity removes exposed positives, and then the homodimer,
from the ranked candidate lists while retaining the same U controls.

{sensitivity_table}

The original and additional cohorts are also shown separately:

{cohort_table}

Only 3-4 positives are nominated per target. These are not exhaustive interaction
catalogues or a random sample of human biology. The three RAF partners are
homologous; targets also share some proteins. Metrics do not establish statistical
superiority, homology-independent generalization, or absence from sequence
pretraining. Existing IRE1 cases and the original six panels have been examined
before. Binding conditions, phosphorylation, hydroxylation, nucleotide state,
proteolysis, and experimental fragments are not encoded by a canonical sequence.

U is unknown, not an experimentally verified noninteractor. AP, NDCG, and
known-positive precision describe this reference panel rather than true
interaction precision. EF rescales recall; ordinary P/U ROC-AUC equals the
reported concordance. No accuracy, F1, MCC, calibration, or common score-threshold
claim is made. Context and background U groups are reported separately, and
historical benchmark sampling weights are not reused.

## Execution and validation

All **{freeze['unique_sequences']:,} unique human sequences** were fetched from
UniProt and matched to panel hashes. Both frozen preprocessing pipelines were
recomputed from scratch across all twelve targets. No existing embedding or
endpoint feature cache was used. The frozen TRAIN normalization, model weights,
GP covariance, selected epoch 4, seed order, and equal FP64 ensemble means were
preserved. No training, checkpoint reselection, GP refitting, or protected-test
access took place.

The [independent validation](INDEPENDENT_VALIDATION.json) checks all 11,211
ensemble scores, 540 target/subset/stratum metric rows, 333 matched-positive metric
rows, 135 macro rows, 1,800 curve rows, and 111 positive-rank rows. AP, NDCG, and
P/U AUROC were independently recomputed with scikit-learn; exposure and matching
constraints were rechecked. [Unit-test evidence](UNIT_TESTS.xml) and
[metric tie tests](METRIC_TESTS.xml) are retained.

The [original-six consistency check](ORIGINAL_SIX_CONSISTENCY.json) found a
maximum fresh-score difference of {max_error:.3g} and {rank_changes} changed rank
entries across the three models. Fresh FP32 batch composition can affect rounding;
the original results are retained exactly.

Reproduction instructions and the artifact map are in [README.md](README.md).
"""
    (out / "REPORT.md").write_text(report)
    for gene in targets:
        folder = root / "example" / gene
        manifest = read(folder / "panel_manifest.json")
        positive_rows = [r for r in ranks if r["query_gene"] == gene]
        target_metrics = [mapping[gene, model] for model in MODELS]
        overview = markdown(["Metric", *LABELS], [[label, *[f(r[key]) for r in target_metrics]] for label, key in (
            ("P/U concordance", "P_vs_U_concordance"), ("Average precision", "average_precision"),
            ("Expected first-positive rank (lower is better)", "first_positive_rank_expected"), ("Reciprocal rank", "reciprocal_rank"),
            *[(f"{label}@{k}", f"{key}_at_{k}") for k in (5, 10, 20) for label, key in (("Recovered P", "recovered_P"), ("Recall", "recall"), ("Known-positive precision", "known_positive_precision"), ("EF", "EF"), ("NDCG", "NDCG"), ("Target success", "target_success"))])])
        partners = [r for r in manifest["rows"] if r["class"] == "P"]
        rank_table = markdown(["Known partner", "Exposure / pair type", *LABELS], [[p["partner_gene"], ", ".join([key for key, value in p.get("prior_pair_exposure", {}).items() if value] + (["homomer"] if p.get("homomeric") else [])) or "No checked TRAIN/dev pair overlap", *[f(next(r["rank_mid"] for r in positive_rows if r["partner_uniprot"] == p["partner_uniprot"] and r["model"] == model)) for model in MODELS]] for p in partners])
        (folder / "RESULTS_v2.md").write_text(f"# {gene}: three frozen iPIN models\n\nPart of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).\nMain panel: {manifest['P']} P and {manifest['U']} U; U is unknown. Scores and ranks\nare in [{gene.lower()}_three_model_scores.csv]({gene.lower()}_three_model_scores.csv).\n\n{overview}\n\n## Positive-partner ranks\n\n{rank_table}\n\nRanks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)\nand [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for\ncontext/background results and exposure/homomer sensitivities. The target-level\nresult is descriptive, with only {manifest['P']} nominated positives.\n")
        if gene not in config["original_targets"]:
            evidence = markdown(["Partner", "Accession", "Evidence and context"], [[p["partner_gene"], p["partner_uniprot"], f"[{p['evidence']['note']}]({p['evidence']['url']})"] for p in partners])
            block_table = markdown(["Anchor", "U group", "Rows", "Compartment", "TRANSMEM"], [[b["anchor_gene"], b["stratum"], f"{b['first_data_row']}-{b['last_data_row']}", b["compartment"] or "Unrestricted", b["transmembrane"] if b["transmembrane"] is not None else "Unrestricted"] for b in manifest["U_blocks"]])
            exposed = [p["partner_gene"] + ": " + ", ".join(k for k, v in p["prior_pair_exposure"].items() if v) for p in partners if any(p["prior_pair_exposure"].values())]
            (folder / "README.md").write_text(f"# {gene} biological partner panel\n\nHuman {gene} ({manifest['target']['accession']}), selected for {manifest['process'].lower()}.\nThe [input CSV]({gene.lower()}_ipin_panel.csv) contains **3 P + 300 U = 303 pairs**.\nCurrent inference and all retrieval metrics: [RESULTS_v2.md](RESULTS_v2.md).\n\n## Nominated positives\n\n{evidence}\n\nThese are supported nominated partners, not an exhaustive catalogue. Canonical\nsequences do not encode biological state, modifications, cleavage, or experimental\nfragment boundaries. Evidence may concern particular domains or conditions.\n\n## Unlabeled controls\n\nEach positive anchors 50 compartment/TRANSMEM-matched and 50 background U\nproteins, all within 0.5-2 times its length. All quotas were met without widening.\nU means unlabeled, not verified noninteraction. The source pool contains reviewed\nhuman UniProt proteins with protein-level evidence, primary gene names, and\nsupported canonical sequences of at least 30 residues. Controls are deduplicated\nby sequence and sampled without replacement within this target.\n\n{block_table}\n\nRows are one-based data rows, excluding the CSV header. Broad compartment matching\nuses UniProt location text; the declared positive context can also be supported\nby UniProt GO cellular-component annotation. Absence of TRANSMEM does not prove\nsolubility. Context groups are allocated first, most constrained first. Selection\nuses SHA-256 ordering with salt `{config['sampling_salt']}` and no model scores.\n\nExclusions include the query, all nominated partners, IntAct human-human partner\nidentifiers, target/reciprocal UniProt subunit annotations, TRAIN/development P\nand U neighbors, and identical excluded sequences. The [manifest](panel_manifest.json)\nretains source URLs and hashes, exact row identities, matching groups, and exposure\nrecords. Public raw responses are retained locally in the comparison's ignored\n`sources/` directory.\n\n## Exposure\n\n{'; '.join(exposed) if exposed else 'No nominated P exact pair was found in the checked TRAIN/development P/U arrays.'}\n\nThe checks use accessions and exact sequences. Protected-test pair labels were\nnot opened. Homology, prior examples, and sequence pretraining are separate\nexposure questions. Results and exposure sensitivities are retained in the\n[twelve-target report](../twelve_target_comparison_v1/REPORT.md).\n")
    index = markdown(["Target", "Panel", "Three-model results"], [[gene, f"[{4 if gene == 'ERN1' else 3} P + {400 if gene == 'ERN1' else 300} U]({gene}/{gene.lower()}_ipin_panel.csv)", f"[Metrics and ranks]({gene}/RESULTS_v2.md)"] for gene in targets])
    (root / "example/README.md").write_text(f"# Protein-screening examples\n\nThe current application compares the **three frozen iPIN models on twelve human\ntargets: 37 nominated positives and 3,700 unlabeled pairs**. Start with the\n[twelve-target report](twelve_target_comparison_v1/REPORT.md),\n[metric definitions](twelve_target_comparison_v1/METRICS.md), and\n[reproduction guide](twelve_target_comparison_v1/README.md).\n\n{index}\n\nKRAS, CDK2, HIF1A, CTNNB1, TNFRSF1A, and BECN1 extend the original six targets.\nEach has three supported partners and 100 matched/background U controls per\npartner. The original ERN1 panel retains its fourth positive, the homodimer.\nTraining/development exposure and homomer sensitivities are reported explicitly.\nThese panels measure known-partner retrieval; U is unknown and results are\ndescriptive biological cases.\n\n## Historical records\n\nThe [six-target comparison](six_target_comparison_v1/REPORT.md) contains the\noriginal four-predictor results, including the authors' original TUnA comparator.\nIts files and the original six input panels are preserved. The new comparison\nuses the three registered iPIN predictors; original TUnA remains in the historical\nrecord. Original target READMEs describe their preparation; `RESULTS_v2.md` and\n`*_three_model_scores.csv` contain current inference.\n\nThe older `ire1_ipin_panel*.csv` files and scoring scripts are retained examples.\n`score_frozen_models.py` and `score_ire1_ipin_panel2.py` retain their historical\ntwo-pooled-model scope. Use the twelve-target pipeline for current three-model\napplication and arbitrary panel-sequence embedding.\n")
    print("Rendered report, 12 target reports, 6 panel READMEs, example index, and PDF/SVG/PNG figure", flush=True)


if __name__ == "__main__":
    main()
