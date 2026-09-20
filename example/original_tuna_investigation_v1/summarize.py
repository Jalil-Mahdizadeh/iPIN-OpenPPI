"""Create compact descriptive summaries and exportable investigation figures."""
from __future__ import annotations

from collections import defaultdict
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from investigate import ROOT, OUT, PARENT, check_inputs, read, record, table, write_csv, write_json


def mean(rows, key):
    return float(np.mean([float(r[key]) for r in rows]))


def main():
    assert os.environ.get("APPTAINER_CONTAINER")
    check_inputs()
    parent = table(PARENT / "macro_metrics.csv")
    sensitivity = [r for r in parent if r["cohort"] in ("all_twelve", "strict_evidence_eleven")
                   and r["candidate_set"] == "all_U" and r["model"] in ("tuna_original", "tuna_retrained")]
    write_csv("exposure_sensitivity.csv", sensitivity)
    swap = table(OUT / "query_swap_summary.csv")
    controls = table(OUT / "partner_only_baselines.csv")
    component = table(OUT / "score_component_metrics.csv")
    summary = []
    for name in ("context", "background", "low_plausibility", "context_background", "all_U"):
        for model in ("tuna_original", "tuna_retrained"):
            group = [r for r in swap if r["model"] == model and r["candidate_set"] == name]
            for diagnostic, pu, ap in (("actual_query", "actual_P_vs_U", "actual_AP"),
                                       ("mean_of_11_replacement_queries", "mean_replacement_P_vs_U", "mean_replacement_AP"),
                                       ("replacement_query_rank_consensus", "replacement_consensus_P_vs_U", "replacement_consensus_AP")):
                summary.append(dict(candidate_set=name, model=model, diagnostic=diagnostic,
                                    targets=len(group), macro_P_vs_U=mean(group, pu), MAP=mean(group, ap)))
        for diagnostic in ("partner_training_seen", "partner_positive_degree", "partner_positive_degree_fraction"):
            group = [r for r in controls if r["diagnostic"] == diagnostic and r["candidate_set"] == name]
            summary.append(dict(candidate_set=name, model="no_fitted_model", diagnostic=diagnostic,
                                targets=len(group), macro_P_vs_U=mean(group, "P_vs_U_concordance"), MAP=mean(group, "average_precision")))
        for diagnostic in ("raw_logit", "adjusted_logit", "probability"):
            group = [r for r in component if r["component"] == diagnostic and r["candidate_set"] == name]
            summary.append(dict(candidate_set=name, model="tuna_original", diagnostic=diagnostic,
                                targets=len(group), macro_P_vs_U=mean(group, "P_vs_U_concordance"), MAP=mean(group, "average_precision")))
    write_csv("diagnostic_macro_metrics.csv", summary)
    contributions = table(OUT / "target_contributions.csv")
    facts = {}
    for metric in ("P_vs_U_concordance", "average_precision"):
        group = [r for r in contributions if r["candidate_set"] == "all_U" and r["comparator"] == "tuna_retrained" and r["metric"] == metric]
        egfr = next(r for r in group if r["target"] == "EGFR")
        facts[metric + "_EGFR_fraction_of_net_macro_gap"] = float(egfr["contribution_to_macro_difference"]) / mean(group, "difference")
    seen = table(OUT / "endpoint_exposure_summary.csv")
    facts["partner_training_seen"] = {group: {
        "seen": sum(int(r["seen"]) for r in seen if r["group"] == group and r["endpoint"] == "partner" and r["source"] == "training"),
        "total": sum(int(r["pairs"]) for r in seen if r["group"] == group and r["endpoint"] == "partner" and r["source"] == "training")}
        for group in ("P", "context", "background", "low_plausibility")}
    facts["exploratory"] = True
    write_json("SUMMARY.json", facts)

    # Ancillary descriptive endpoint context, after the relative-pair audit:
    # counts of actual TRAIN rows containing an accession, not biological degree.
    audit = table(OUT / "nominated_and_relative_pair_exposure.csv")
    accessions = sorted({r[k] for r in audit for k in ("query_accession", "partner_accession") if r[k]})
    folder = ROOT / "benchmark/tuna/data"
    source = read(folder / "sequences.json")
    by_acc = defaultdict(set)
    for i, values in enumerate(source["accessions"]):
        for acc in values:
            by_acc[acc].add(i)
    endpoint_rows = []
    with np.load(folder / "training.npz", allow_pickle=False) as data:
        pa, pb, ua, ub = (data[k] for k in ("p_a", "p_b", "u_a", "u_b"))
        for acc in accessions:
            ids = list(by_acc[acc])
            endpoint_rows.append(dict(accession=acc, basis="accession", sequence_catalogue_entries=len(ids),
                TRAIN_P_rows=int((np.isin(pa, ids) | np.isin(pb, ids)).sum()),
                TRAIN_U_rows=int((np.isin(ua, ids) | np.isin(ub, ids)).sum())))
    write_csv("ipin_training_endpoint_context.csv", endpoint_rows)
    write_json("SUMMARY_PROVENANCE.json", dict(script=record(OUT / "summarize.py"),
               ancillary_TRAIN_sources=[record(folder / f) for f in ("training.npz", "sequences.json")],
               protected_test_records_read=False, no_model_training=True))

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "svg.fonttype": "none"})
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    blue, orange = "#2574A9", "#D46A2C"
    group = [r for r in contributions if r["candidate_set"] == "all_U" and r["comparator"] == "tuna_retrained"
             and r["metric"] == "P_vs_U_concordance"]
    values = np.array([float(r["difference"]) for r in group])
    axes[0, 0].barh([r["target"] for r in group], values, color=[blue if v > 0 else orange for v in values])
    axes[0, 0].axvline(0, color="0.3", linewidth=.8)
    axes[0, 0].invert_yaxis()
    axes[0, 0].set(xlabel="Original − retrained PU concordance", title="A. Strong differences between targets")
    for j, (cohort, label) in enumerate((("all_twelve", "All 12 targets"), ("strict_evidence_eleven", "EGFR omitted"))):
        for offset, model, color in ((-.16, "tuna_original", blue), (.16, "tuna_retrained", orange)):
            r = next(r for r in sensitivity if r["cohort"] == cohort and r["positive_subset"] == "all_P" and r["model"] == model)
            value = float(r["macro_P_vs_U_concordance"])
            axes[0, 1].bar(j + offset, value, .3, color=color, label=model.replace("tuna_", "").title() if j == 0 else None)
            axes[0, 1].text(j + offset, value + .009, f"{value:.4f}", ha="center", fontsize=9)
    axes[0, 1].set(xticks=[0, 1], xticklabels=["All 12 targets", "EGFR omitted"], ylim=(0, 1),
                   ylabel="Equal-target PU concordance", title="B. The net lead mostly depends on EGFR")
    axes[0, 1].legend(loc="upper right")
    for j, model in enumerate(("tuna_original", "tuna_retrained")):
        group = [r for r in swap if r["model"] == model and r["candidate_set"] == "all_U"]
        for offset, key, color, label in ((-.16, "actual_P_vs_U", blue, "Actual query"),
                                         (.16, "mean_replacement_P_vs_U", orange, "Mean of 11 replacement queries")):
            value = mean(group, key)
            axes[1, 0].bar(j + offset, value, .3, color=color, label=label if j == 0 else None)
            axes[1, 0].text(j + offset, value + .012, f"{value:.3f}", ha="center")
    axes[1, 0].axhline(.5, linestyle="--", color="0.5", linewidth=.8)
    axes[1, 0].set(xticks=[0, 1], xticklabels=["Original TUnA", "Retrained TUnA"], ylim=(0, 1),
                   ylabel="PU concordance against original labels", title="C. Rankings depend on the query target")
    axes[1, 0].legend(loc="upper right", fontsize=8)
    ranks = table(PARENT / "positive_partner_ranks.csv")
    for j, gene in enumerate(("GRB2", "SHC1", "CBL")):
        for offset, model, color in ((-.12, "tuna_original", blue), (.12, "tuna_retrained", orange)):
            r = next(r for r in ranks if r["query_gene"] == "EGFR" and r["partner_gene"] == gene
                     and r["model"] == model and r["candidate_set"] == "all_U")
            rank = float(r["rank_mid"])
            axes[1, 1].scatter(rank, j + offset, color=color, s=65)
            axes[1, 1].annotate(str(int(rank)), (rank, j + offset), xytext=(5, 0), textcoords="offset points", va="center")
    axes[1, 1].set(yticks=[0, 1, 2], yticklabels=["GRB2", "SHC1", "CBL"], xscale="log", xlim=(.7, 453),
                   xlabel="Rank among 453 EGFR candidates (lower is better)", title="D. Original TUnA retrieves the three EGFR positives")
    axes[1, 1].invert_yaxis()
    fig.suptitle("Original TUnA: target-specific strengths in a small example panel", fontsize=15)
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(OUT / f"investigation.{suffix}", dpi=180)
    svg = OUT / "investigation.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)
    print("Summary tables and figures completed", flush=True)


if __name__ == "__main__":
    main()
