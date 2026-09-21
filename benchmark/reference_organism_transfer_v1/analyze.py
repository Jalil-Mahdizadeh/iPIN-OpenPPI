"""Evaluate fixed predictors against published reference-organism assay outcomes."""
import argparse
import math
from collections import Counter

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score

from evaluation_utils import *


def weighted_metrics(labels, scores, weights):
    """Tie-aware AUROC and threshold-group AP for many bootstrap weights."""
    y = np.asarray(labels, dtype=bool)
    s = np.asarray(scores, dtype=np.float64)
    w = np.atleast_2d(np.asarray(weights, dtype=np.float64))
    require(w.shape[1] == len(y) == len(s), "Metric dimensions differ")
    require(np.isfinite(s).all() and np.isfinite(w).all() and (w >= 0).all(), "Invalid metric inputs")
    wp, wn = w[:, y], w[:, ~y]
    positives, negatives = wp.sum(axis=1), wn.sum(axis=1)
    valid = (positives > 0) & (negatives > 0)
    auc = np.full(len(w), np.nan)
    ap = np.full(len(w), np.nan)
    if not valid.any():
        return auc, ap
    comparisons = (s[y, None] > s[None, ~y]).astype(float) + .5 * (s[y, None] == s[None, ~y])
    numerator = np.einsum("bi,ij,bj->b", wp, comparisons, wn, optimize=True)
    auc[valid] = numerator[valid] / (positives[valid] * negatives[valid])
    order = np.argsort(-s, kind="stable")
    ends = np.r_[np.flatnonzero(np.diff(s[order]) != 0), len(s) - 1]
    cumulative_p = np.cumsum(w[:, order] * y[order], axis=1)[:, ends]
    cumulative_n = np.cumsum(w[:, order], axis=1)[:, ends]
    increments = np.diff(np.c_[np.zeros(len(w)), cumulative_p], axis=1)
    precision = np.divide(cumulative_p, cumulative_n, out=np.zeros_like(cumulative_p), where=cumulative_n > 0)
    ap[valid] = (increments[valid] * precision[valid]).sum(axis=1) / positives[valid]
    return auc, ap


def selftest():
    require(not (OUT / "METRIC_SELFTEST.json").exists(), "Refusing to replace metric self-test")
    rng = np.random.default_rng(20260921)
    y = np.array([True, False] * 9)
    cases = [np.zeros(18), y.astype(float), -y.astype(float)]
    cases += [rng.integers(0, 5, 18).astype(float) for _ in range(12)]
    weights = np.r_[np.ones((1, 18)), rng.integers(0, 4, (20, 18))]
    max_error, checked = 0.0, 0
    for s in cases:
        auc, ap = weighted_metrics(y, s, weights)
        for i, w in enumerate(weights):
            if not (w[y].sum() and w[~y].sum()):
                continue
            expected = [roc_auc_score(y, s, sample_weight=w), average_precision_score(y, s, sample_weight=w)]
            error = max(abs(auc[i] - expected[0]), abs(ap[i] - expected[1]))
            require(error < 1e-12, "Weighted metric check failed")
            max_error = max(max_error, error)
            checked += 1
    write_json(OUT / "METRIC_SELFTEST.json", {"status": "passed", "cases": checked,
        "maximum_absolute_error": max_error, "tolerance": 1e-12,
        "checks": ["weighted_AUROC_against_sklearn", "weighted_AP_against_sklearn", "ties", "perfect", "reversed", "zero_weight_observations"],
        "model_scores_read": False, "script": record(OUT / "analyze.py")})
    print(f"Metric self-test passed: {checked} weighted cases; maximum error {max_error:.3g}")


def components(rows):
    parents = list(range(len(rows)))

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    owner = {}
    for i, row in enumerate(rows):
        for field in ("query_sequence_sha256", "partner_sequence_sha256"):
            endpoint = row[field]
            if endpoint in owner:
                a, b = find(i), find(owner[endpoint])
                parents[max(a, b)] = min(a, b)
            owner[endpoint] = i
    roots = [find(i) for i in range(len(rows))]
    index = {r: i for i, r in enumerate(sorted(set(roots)))}
    return np.array([index[r] for r in roots], dtype=int)


def interval(values):
    values = np.asarray(values)
    values = values[np.isfinite(values)]
    if len(values) < 1000:
        return (None, None)
    return tuple(float(v) for v in np.quantile(values, [.025, .975]))


def number(value):
    return float(value) if np.isfinite(value) else None


def plot(metrics, comparison, prediction):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve
    y = np.array([boolean(r["confirmed"]) for r in comparison])
    indices = np.array([int(r["row_index"]) for r in comparison])
    colors = ["#0072B2", "#D55E00", "#009E73"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    full = [r for r in metrics if r["cohort"] == "all_mapped_assays"]
    for i, (model, color) in enumerate(zip(MODELS, colors)):
        row = next(r for r in full if r["model"] == model)
        fpr, tpr, _ = roc_curve(y, prediction[model][indices])
        axes[0].plot(fpr, tpr, color=color, label=f"{MODEL_NAMES[model]} ({row['AUROC']:.3f})")
        point = row["AUROC"]
        lo, hi = row["AUROC_ci_low"], row["AUROC_ci_high"]
        axes[1].plot([lo, hi], [i, i], color=color, linewidth=2) if lo is not None else None
        axes[1].plot(point, i, "o", color=color)
    axes[0].plot([0, 1], [0, 1], "--", color="0.6", linewidth=1)
    axes[0].set(xlabel="Fraction of unconfirmed assays retrieved", ylabel="Fraction of confirmed assays retrieved",
                title=f"Published assay calls (n={len(comparison)})", xlim=(0, 1), ylim=(0, 1))
    axes[0].legend(fontsize=8, loc="lower right")
    axes[1].axvline(.5, color="0.6", linestyle="--", linewidth=1)
    axes[1].set(yticks=range(3), yticklabels=[MODEL_NAMES[m] for m in MODELS], xlabel="AUROC",
                title="95% component-bootstrap intervals", xlim=(0, 1), ylim=(-.6, 2.6))
    axes[1].invert_yaxis()
    fig.suptitle("Frozen human PPI models: human–S288C assay confirmation", fontsize=12)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    for extension in ("png", "pdf", "svg"):
        fig.savefig(OUT / ("assay_confirmation." + extension), dpi=180)
    plt.close(fig)


def analyze():
    require(not (OUT / "ANALYSIS.json").exists(), "Refusing to replace analysis")
    freeze = read(OUT / "INPUT_FREEZE.json")
    for item in freeze["files"]:
        verify(item)
    panels = table(OUT / "panels.csv")
    comparison = table(OUT / "assay_comparison.csv")
    predictions = {}
    for file, models in (("ipin_scores.csv", MODELS[:2]), ("tuna_scores.csv", MODELS[2:])):
        scores = table(OUT / file)
        require([int(r["row_index"]) for r in scores] == list(range(len(panels))), "Score row ordering mismatch")
        for model in models:
            predictions[model] = np.array([float(r[model + "_score"]) for r in scores])
            require(np.isfinite(predictions[model]).all(), "Nonfinite model scores")
    exposure = {r["sequence_sha256"]: r for r in table(OUT / "exact_endpoint_exposure.csv")}
    for row in comparison:
        endpoints = [exposure[row[k]] for k in ("query_sequence_sha256", "partner_sequence_sha256")]
        row["either_exact_train_endpoint"] = any(boolean(r["exact_TRAIN_endpoint"]) for r in endpoints)
        row["either_exact_development_endpoint"] = any(boolean(r["exact_DEV_endpoint"]) for r in endpoints)
        for model in MODELS:
            row[model + "_score"] = float(predictions[model][int(row["row_index"])])
    write_csv(OUT / "assay_model_scores.csv", comparison)
    write_csv(OUT / "all_model_scores.csv", [{**row, **{m + "_score": float(predictions[m][i]) for m in MODELS}}
                                           for i, row in enumerate(panels)])
    metrics, differences, cluster_rows, bootstrap_details = [], [], [], {}
    cohorts = {"all_mapped_assays": comparison,
               "no_exact_train_or_development_endpoint": [r for r in comparison if
                   not r["either_exact_train_endpoint"] and not r["either_exact_development_endpoint"]]}
    for cohort, rows in cohorts.items():
        y = np.array([boolean(r["confirmed"]) for r in rows], dtype=bool)
        cluster = components(rows)
        cluster_count = len(set(cluster))
        max_size = max(Counter(cluster).values(), default=0)
        for row, c in zip(rows, cluster):
            cluster_rows.append({"cohort": cohort, "pair_id": row["pair_id"], "component": int(c)})
        rng = np.random.default_rng(20260921)
        weights = np.empty((0, len(rows)))
        if cluster_count >= 2 and y.any() and (~y).any():
            sampled = rng.multinomial(cluster_count, np.full(cluster_count, 1 / cluster_count), size=10000)
            weights = sampled[:, cluster]
        boot = {}
        for model in MODELS:
            scores = np.array([r[model + "_score"] for r in rows], dtype=float)
            point_auc, point_ap = weighted_metrics(y, scores, np.ones((1, len(rows))))
            auc, ap = weighted_metrics(y, scores, weights)
            boot[model] = {"AUROC": auc, "AP": ap}
            auc_ci, ap_ci = interval(auc), interval(ap)
            continuous = np.array([float(r["published_assay_score"]) for r in rows])
            rho = float(spearmanr(scores, continuous).statistic) if len(set(scores)) > 1 and len(set(continuous)) > 1 else np.nan
            metrics.append({"cohort": cohort, "model": model, "pairs": len(rows), "confirmed": int(y.sum()),
                "unconfirmed": int((~y).sum()), "AP_prevalence_reference": float(y.mean()) if len(y) else None,
                "AUROC": number(point_auc[0]), "AUROC_ci_low": auc_ci[0], "AUROC_ci_high": auc_ci[1],
                "AP": number(point_ap[0]), "AP_ci_low": ap_ci[0], "AP_ci_high": ap_ci[1],
                "Spearman_assay_score": number(rho), "components": cluster_count,
                "largest_component_pairs": max_size, "valid_bootstrap_draws": int(np.isfinite(auc).sum())})
        bootstrap_details[cohort] = {"components": cluster_count, "largest_component_pairs": max_size,
                                     "requested_draws": 10000, "valid_draws": int(np.isfinite(boot[MODELS[0]]["AUROC"]).sum())}
        for a, b in ((MODELS[1], MODELS[0]), (MODELS[2], MODELS[0]), (MODELS[2], MODELS[1])):
            first = next(r for r in metrics if r["cohort"] == cohort and r["model"] == a)
            second = next(r for r in metrics if r["cohort"] == cohort and r["model"] == b)
            for metric in ("AUROC", "AP"):
                lo, hi = interval(boot[a][metric] - boot[b][metric])
                differences.append({"cohort": cohort, "model_a": a, "model_b": b, "metric": metric,
                    "difference_a_minus_b": first[metric] - second[metric] if first[metric] is not None and second[metric] is not None else None,
                    "ci_low": lo, "ci_high": hi})
    write_csv(OUT / "metrics.csv", metrics)
    write_csv(OUT / "paired_differences.csv", differences)
    write_csv(OUT / "bootstrap_components.csv", cluster_rows)
    plot(metrics, comparison, predictions)
    names = ["assay_model_scores.csv", "all_model_scores.csv", "metrics.csv", "paired_differences.csv", "bootstrap_components.csv",
             "assay_confirmation.png", "assay_confirmation.pdf", "assay_confirmation.svg"]
    result = {"at_utc": now(), "status": "analyzed", "endpoint": "published_assay_confirmation",
              "metrics": metrics, "paired_differences": differences, "bootstrap": bootstrap_details,
              "bootstrap_seed": 20260921, "input_freeze": record(OUT / "INPUT_FREEZE.json"),
              "model_outputs": [record(OUT / p) for p in ("ipin_scores.csv", "tuna_scores.csv")],
              "script": record(OUT / "analyze.py"), "outputs": [record(OUT / p) for p in names],
              "published_pairs_scored": len(panels), "biological_noninteraction_claim": False}
    write_json(OUT / "ANALYSIS.json", result)
    print(json.dumps({"primary_metrics": metrics[:3], "bootstrap": bootstrap_details}, sort_keys=True))


if __name__ == "__main__":
    container()
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("selftest", "analyze"))
    selftest() if parser.parse_args().phase == "selftest" else analyze()
