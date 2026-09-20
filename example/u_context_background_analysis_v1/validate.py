"""Independent arithmetic and data alignment checks for the U score comparison."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path

import numpy as np
from scipy import stats


def read(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def check(actual, expected):
    if not np.isclose(float(actual), float(expected), atol=2e-12, rtol=0):
        raise AssertionError((actual, expected))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert os.environ.get("APPTAINER_CONTAINER")
    root, out = args.root, args.output
    parent = root / "example/twelve_target_comparison_v1"
    raw = read(parent / "all_twelve_targets_scores.csv")
    anchor_results = read(out / "per_anchor_scores.csv")
    target_results = read(out / "per_target_scores.csv")
    summaries = read(out / "summary.csv")
    meta = {(r["target"], r["partner_uniprot"]): r for r in read(out / "candidate_annotations.csv")}
    checked_anchors = {}
    for row in anchor_results:
        selected = [r for r in raw if r["class"] == "U" and r["query_gene"] == row["target"]
                    and r["anchor_positive_uniprot"] == row["anchor"]]
        column = row["model"] + "_score"
        x = [float(r[column]) for r in selected if r["U_stratum"] == "context"]
        y = [float(r[column]) for r in selected if r["U_stratum"] == "background"]
        assert len(x) == len(y) == 50
        # Rank-sum identity is independent of the production pairwise matrix.
        ranks = stats.rankdata(x + y)
        a = (sum(ranks[:50]) - 50 * 51 / 2) / 2500
        check(row["A"], a)
        check(row["rank_biserial"], 2 * a - 1)
        check(row["mean_difference"], math.fsum(x) / 50 - math.fsum(y) / 50)
        for name, values in (("context", x), ("background", y)):
            check(row[name + "_mean"], np.mean(values))
            check(row[name + "_median"], np.median(values))
            check(row[name + "_q25"], np.quantile(values, .25))
            check(row[name + "_q75"], np.quantile(values, .75))
            check(row[name + "_sd"], np.std(values, ddof=1))
        check(row["KS_distance"], stats.ks_2samp(x, y).statistic)
        remaining = [float(r[column]) for r in selected if r["U_stratum"] == "background"
                     and meta[row["target"], r["partner_uniprot"]]["meets_anchor_context_rule"] == "False"]
        check(row["A_context_vs_nonmatching_background"],
              stats.mannwhitneyu(x, remaining).statistic / (50 * len(remaining)))
        checked_anchors[row["target"], row["model"], row["anchor"]] = a
    for row in target_results:
        values = [a for (target, model, _), a in checked_anchors.items()
                  if target == row["target"] and model == row["model"]]
        check(row["anchor_matched_A"], np.mean(values))
        selected = [r for r in raw if r["class"] == "U" and r["query_gene"] == row["target"]]
        column = row["model"] + "_score"
        values = [float(r[column]) for r in selected]
        # Sum each context row's expected membership of the top 20.
        top = 0.0
        for r in selected:
            if r["U_stratum"] == "context":
                score = float(r[column])
                greater = sum(s > score for s in values)
                equal = sum(s == score for s in values)
                top += min(1, max(0, (20 - greater) / equal))
        check(row["top20_U_context_fraction"], top / 20)
    bootstrap_checks = 0
    for row in summaries:
        targets = [r for r in target_results if r["model"] == row["model"] and
                   (row["cohort"] == "all_twelve" or r["cohort"] == row["cohort"])]
        values = np.asarray([float(r["anchor_matched_A"]) for r in targets])
        check(row["equal_target_A"], values.mean())
        reference = stats.bootstrap((values,), np.mean, n_resamples=100_000, method="percentile",
                                    rng=np.random.default_rng(20260920)).confidence_interval
        check(row["A_ci95_low"], reference.low)
        check(row["A_ci95_high"], reference.high)
        bootstrap_checks += 1
    # Check simultaneous adjustment directly from the sorted raw p-values.
    main_rows = [r for r in summaries if r["cohort"] == "all_twelve"]
    ordered = sorted(main_rows, key=lambda r: float(r["sign_flip_p"]))
    for i, row in enumerate(ordered):
        check(row["sign_flip_p_holm_three_models"],
              min(1, max((3 - j) * float(ordered[j]["sign_flip_p"]) for j in range(i + 1))))
    for row in read(out / "leave_one_target_out.csv"):
        expected = [float(r["anchor_matched_A"]) for r in target_results
                    if r["model"] == row["model"] and r["target"] != row["omitted_target"]]
        check(row["equal_target_A"], np.mean(expected))
    # Exhaustively average tied top-K membership on a mixed-score fixture.
    from analyze import superiority, top_context_fraction, sign_flip_p
    x, y, k = [4, 2, 2], [3, 2, 1], 4
    observed = []
    labels = [True, True, False]
    for ordering in itertools.permutations(range(3)):
        ordered_labels = [True, False] + [labels[i] for i in ordering] + [False]
        observed.append(sum(ordered_labels[:k]) / k)
    check(top_context_fraction(x, y, k), np.mean(observed))
    for left, right in (([1, 1], [1, 1]), ([1, 3, 3], [2, 3]), ([1], [0, 2, 1])):
        check(superiority(left, right) + superiority(right, left), 1)
        check(superiority(left, right), stats.mannwhitneyu(left, right).statistic / (len(left) * len(right)))
    fixture = np.array([-.2, 0, .1, .3])
    check(sign_flip_p(fixture), stats.permutation_test((fixture,), np.mean,
          permutation_type="samples", n_resamples=np.inf).pvalue)
    parent_manifest = json.loads((parent / "RUN_MANIFEST.json").read_text())
    for item in parent_manifest["scientific_outputs"]:
        assert hashlib.sha256((root / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    record = {"passed": True, "anchor_rows_checked": len(anchor_results),
        "target_rows_checked": len(target_results), "bootstrap_intervals_checked_against_scipy": bootstrap_checks,
        "top20_independent_membership_checks": len(target_results), "leave_one_target_out_checked": 36,
        "holm_adjustment_checked": True, "exhaustive_mixed_tie_fixture_passed": True,
        "parent_artifacts_unchanged": len(parent_manifest["scientific_outputs"])}
    with (out / "INDEPENDENT_VALIDATION.json").open("x") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
