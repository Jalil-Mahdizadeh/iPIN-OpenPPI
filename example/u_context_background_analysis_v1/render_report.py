"""Render a descriptive report and standalone scientific figure from fixed tables."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.ticker import PercentFormatter
import numpy as np

NAMES = {"ipin_baseline": "Original iPIN", "ipin_optimized": "Optimized iPIN", "tuna_retrained": "TUnA-retrained"}
COLORS = ("#335c81", "#258b83", "#8b529e")


def read(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def percent(value):
    return f"{100 * float(value):.1f}%"


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"] +
                     ["| " + " | ".join(map(str, row)) + " |" for row in rows])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert os.environ.get("APPTAINER_CONTAINER")
    out = args.output
    if (out / "FINAL_MANIFEST.json").exists():
        raise RuntimeError("This analysis is closed; preserve its reports and figures")
    summaries = read(out / "summary.csv")
    main_rows = [r for r in summaries if r["cohort"] == "all_twelve"]
    per_target = read(out / "per_target_scores.csv")
    diagnostics = read(out / "matching_diagnostics.csv")
    candidates = read(out / "candidate_annotations.csv")
    loo = read(out / "leave_one_target_out.csv")
    targets = list(dict.fromkeys(r["target"] for r in per_target))
    background_matches = sum(int(r["background_meeting_context_rule"]) for r in diagnostics)
    protein_counts = Counter(r["partner_sequence_sha256"] for r in candidates)
    repeated = sum(count > 1 for count in protein_counts.values())
    length_a = np.mean([np.mean([float(r["length_A"]) for r in diagnostics if r["target"] == t]) for t in targets])
    values = np.array([[float(next(r["anchor_matched_A"] for r in per_target if
                                  r["target"] == t and r["model"] == model)) for model in NAMES] for t in targets])

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.hashsalt": "ipin-u-context-background-v1"})
    fig = plt.figure(figsize=(12.8, 8.0), facecolor="white")
    grid = fig.add_gridspec(2, 2, width_ratios=(1, 1.25), height_ratios=(1, .95), wspace=.58, hspace=.48)
    ax = fig.add_subplot(grid[:, 0])
    heat = ax.imshow(values, aspect="auto", cmap="RdBu", norm=TwoSlopeNorm(vmin=.30, vcenter=.50, vmax=.70))
    ax.set_yticks(range(len(targets)), targets)
    ax.set_xticks(range(3), ["Original", "Optimized", "TUnA retrained"])
    ax.tick_params(axis="both", length=0, pad=8)
    ax.set_title("Within each target", loc="left", weight="bold", pad=15)
    for i in range(len(targets)):
        for j in range(3):
            ax.text(j, i, percent(values[i, j]), ha="center", va="center",
                    color="white" if abs(values[i, j] - .5) > .125 else "#1e293b", fontsize=10)
    ax.axhline(5.5, color="white", linewidth=3)
    bar = fig.colorbar(heat, ax=ax, orientation="horizontal", fraction=.05, pad=.09)
    bar.set_ticks([.3, .4, .5, .6, .7])
    bar.ax.xaxis.set_major_formatter(PercentFormatter(1))
    bar.set_label("Context score exceeds background score")

    ax = fig.add_subplot(grid[0, 1])
    for i, row in enumerate(main_rows):
        a, low, high = [float(row[k]) for k in ("equal_target_A", "A_ci95_low", "A_ci95_high")]
        ax.errorbar(a, 2 - i, xerr=np.array([[a - low], [high - a]]), fmt="o", color=COLORS[i],
                    markersize=8, capsize=4, linewidth=2)
        ax.annotate(f"{percent(a)}  [{percent(low)}, {percent(high)}]", (a, 2 - i),
                    xytext=(0, 15), textcoords="offset points", ha="center", fontsize=10)
    ax.axvline(.5, color="#94a3b8", linestyle="--", linewidth=1.3)
    ax.set_yticks([2, 1, 0], list(NAMES.values()))
    ax.set_xlim(.47, .67)
    ax.set_ylim(-.6, 2.7)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Equal-target average and 95% interval", loc="left", weight="bold", pad=15)
    ax.set_xlabel("50% = no directional score advantage")
    ax.grid(axis="x", alpha=.15)

    ax = fig.add_subplot(grid[1, 1])
    y = np.arange(3)
    context = [100 * float(r["mean_P_vs_context_concordance"]) for r in main_rows]
    background = [100 * float(r["mean_P_vs_background_concordance"]) for r in main_rows]
    ax.barh(y + .17, context, height=.3, color="#335c81", label="P vs context U")
    ax.barh(y - .17, background, height=.3, color="#dd9861", label="P vs background U")
    ax.set_yticks(y, list(NAMES.values()))
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(PercentFormatter())
    for i, (c, b) in enumerate(zip(context, background, strict=True)):
        ax.text(c + 1, i + .17, f"{c:.1f}%", va="center", fontsize=10)
        ax.text(b + 1, i - .17, f"{b:.1f}%", va="center", fontsize=10)
    ax.set_title("Known partners are harder to recover\nagainst context U", loc="left", weight="bold", pad=16)
    ax.set_xlabel("Mean P-versus-U concordance; higher is better")
    ax.set_ylim(2.9, -.6)
    ax.legend(loc="lower left", frameon=False, fontsize=9, ncol=2)
    fig.suptitle("Context U receives modestly higher scores", fontsize=18, weight="bold", x=.07, ha="left", y=.98)
    fig.text(.07, .025, "12 targets · 37 matched anchors · 1,850 U pairs per group · three frozen models\n"
             "Intervals resample whole targets. Exploratory score analysis; U interaction status remains unknown.",
             fontsize=10, color="#475569")
    fig.subplots_adjust(top=.88, bottom=.16, left=.10, right=.97)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out / f"score_comparison.{ext}", dpi=180, bbox_inches="tight")
    plt.close(fig)
    # Normalize newly generated XML whitespace before closing its artifact hash.
    svg = out / "score_comparison.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")

    overall = table(["Model", "Context wins", "95% target-bootstrap interval", "Targets above 50%", "Exploratory Holm p"],
        [[NAMES[r["model"]], percent(r["equal_target_A"]), f"{percent(r['A_ci95_low'])}–{percent(r['A_ci95_high'])}",
          f"{r['targets_A_above_half']}/12", f"{float(r['sign_flip_p_holm_three_models']):.4f}"] for r in main_rows])
    target_table = table(["Target", *NAMES.values()], [[t, *[percent(v) for v in row]] for t, row in zip(targets, values, strict=True)])
    retrieval_table = table(["Model", "P vs context U", "P vs background U", "Difference (context − background)", "Context among top 20 U"],
        [[NAMES[r["model"]], f"{float(r['mean_P_vs_context_concordance']):.3f}",
          f"{float(r['mean_P_vs_background_concordance']):.3f}",
          f"{100 * (float(r['mean_P_vs_context_concordance']) - float(r['mean_P_vs_background_concordance'])):.1f} percentage points",
          percent(r["mean_top20_U_context_fraction"])] for r in main_rows])
    sensitivity = table(["Model", "Original six", "Additional six", "Background failing context rule only", "Leave-one-target-out range"],
        [[NAMES[r["model"]],
          *[percent(next(s["equal_target_A"] for s in summaries if s["cohort"] == c and s["model"] == r["model"])) for c in ("original_six", "additional_six")],
          percent(r["mean_A_context_vs_nonmatching_background"]),
          f"{percent(min(float(s['equal_target_A']) for s in loo if s['model'] == r['model']))}–{percent(max(float(s['equal_target_A']) for s in loo if s['model'] == r['model']))}"] for r in main_rows])
    report = f"""# Do context and background U receive different scores?

**Yes: context U receives modestly higher scores on average in all three models.**
The effect is about a 58% chance that context wins a matched score comparison,
versus 50% for no directional advantage. The distributions substantially overlap,
and individual targets can show the reverse direction. This finding concerns
model scores; actual biological interaction rates in either U group are unknown.

This is a new exploratory analysis of the existing [twelve-target results](../twelve_target_comparison_v1/REPORT.md).
It uses all 1,850 context and 1,850 background pairs. Each of 37 positive anchors
contributes a 50-versus-50 comparison; anchors are averaged within targets and
the 12 targets receive equal weight. Scores are compared only within the same
target, anchor, and model. Ties contribute half a win.

## Main result

{overall}

The interval comes from 100,000 whole-target bootstrap draws. The p-values use
all 4,096 target-effect sign flips and Holm correction for the three models.
All adjusted values are below 0.05 under the stated reference assumptions.
These are exploratory summaries of a deliberately selected panel. Statistical
significance is not a biological effect-size threshold or proof of interaction.
Rank-biserial effects are approximately 0.16 for all three models.

![U score comparison](score_comparison.png)

Standalone exports: [PDF](score_comparison.pdf), [SVG](score_comparison.svg).

## Target-specific results

Each value is the anchor-matched fraction of comparisons in which context wins.
Values below 50% favor background. There are no per-target significance claims.

{target_table}

The baseline direction is consistent across all 12 targets. Optimized iPIN has
small reversals for EGFR and CTNNB1. TUnA-retrained has larger reversals for EGFR,
BCL2, and BECN1, so the average does not describe every biological case.

## Consequence for positive-partner retrieval

The preserved parent metrics also show lower P-versus-U concordance against
context candidates. Thus context U is harder, on average, for these models to
rank below the nominated positives. All nominated P, including the parent
report's disclosed TRAIN/development overlaps, remain in this descriptive check.

{retrieval_table}

Each target's top 20 U is selected from its combined context/background U list.
The expected context share under group-blind ranking is 50%; exact score ties
receive fractional boundary credit. This check is descriptive.

## Matching and sensitivity

**{background_matches}/1,850 background candidates ({percent(background_matches / 1850)}) happen to meet
their own anchor's context criteria.** Background means unrestricted by those
criteria, rather than known to occupy a different location. Every selected
context candidate passes its recorded context rule.

{sensitivity}

Removing these coincidentally matching background candidates strengthens the
directional difference to about 60–61%. This changes the comparison group; it
does not replace the original 50-versus-50 analysis and has no extra p-values.
The direction also survives omitting any one target and is similar in the
original and additional cohorts.

Length matching permits a twofold window, rather than exact length equality.
The equal-target length-comparison probability is {percent(length_a)}; individual
anchor groups can still differ in length. [Matching diagnostics](matching_diagnostics.csv)
retain these differences. The analysis cannot isolate a causal effect of cellular
location from length, membrane features, protein-family composition, or other
sequence properties. Context groups were also allocated before background
groups without replacement.

## Interpretation and limits

There is a reproducible, modest score shift in these fixed panels, with
substantial distribution overlap and meaningful target-to-target variation.
The models may respond to properties associated with the matching criteria.
This is not experimental evidence that context U contains more true binders,
or that background U consists of noninteractors.

The 3,700 U rows contain {len(protein_counts):,} unique partner sequences;
{repeated} sequences recur across targets. The panels and anchors were manually
chosen, some targets and partners are related, and the models share training
history. Whole-target resampling avoids pretending every pair is an independent
biological experiment, but it does not eliminate dependence across targets.
Intervals assume exchangeable target sampling; the sign-flip reference assumes
independent, sign-symmetric target effects under the null. These assumptions
are approximate here. No randomized group assignment, causal interpretation,
proteome-wide generalization, or independent three-model replication is claimed.

## Reproducibility

[PROTOCOL.md](PROTOCOL.md) records the analysis choices before this comparison
was computed, after the parent retrieval results were known. The
[run record](ANALYSIS_RUN.json) binds inputs, source, runtime image, versions,
bootstrap seed, and tables. The [independent checks](INDEPENDENT_VALIDATION.json)
validate rank-sum effects, bootstrap intervals with SciPy, top-20 tie credit,
multiple-testing adjustment, and preservation of all 110 parent artifacts.

Statistical implementation references: [Mann-Whitney statistic](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.stats.mannwhitneyu.html),
[paired/sign-flip permutation](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.stats.permutation_test.html),
and [percentile bootstrap](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.stats.bootstrap.html).
"""
    with (out / "REPORT.md").open("w") as stream:
        stream.write(report)
    print("Report and PNG/PDF/SVG figures written")


if __name__ == "__main__":
    main()
