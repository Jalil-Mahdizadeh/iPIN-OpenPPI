#!/usr/bin/env python3
"""Post-readout arithmetic audit of already frozen supporting metrics.

No new estimand, model, split, or decision rule. This additional validator was
written after the readout; it is not part of the pre-fit execution freeze.
It imports no production metric/model/decision functions.
"""

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    root = Path.cwd()
    run = root / "artifacts/runs/within_anchor_partner_specificity_v1"
    results = root / "artifacts/results/within_anchor_partner_specificity_v1"
    output = root / "artifacts/validation/within_anchor_partner_specificity_v1/SUPPORTING_METRIC_AUDIT.json"
    if output.exists():
        raise RuntimeError("refusing to overwrite audit")
    report = json.loads((results / "RESULTS.json").read_text())
    cfg = json.loads((results / "PREREGISTRATION.json").read_text())["config"]
    data = dict(np.load(run / "public_arrays.npz", allow_pickle=False))
    component, folds = data["component"], data["fold"]
    draws = np.load(run / "component_multipliers.npy", allow_pickle=False)
    boot = dict(np.load(run / "bootstrap_metrics.npz", allow_pickle=False))
    names = cfg["models"] + ["length_ratio", "kmer3_cosine", "pooled_cosine"]
    quartet_total = np.zeros((len(draws), len(names)))
    quartet_mass = np.zeros(len(draws))
    propensity = {name: [] for name in ("pair_linear", "endpoint_mlp64")}
    for fold in range(3):
        ev = dict(np.load(run / f"evaluation_fold_{fold}.npz", allow_pickle=False))
        scored = dict(np.load(run / f"scores_fold_{fold}.npz", allow_pickle=False))
        columns, scores = list(scored["columns"]), scored["scores"]
        unary = np.mean([scored[f"endpoint_mlp64__{seed}"] for seed in cfg["training"]["seeds"]], axis=0)
        boundaries = np.quantile(unary[folds != fold], [.2, .4, .6, .8])
        np.testing.assert_array_equal(boundaries, scored["propensity_boundaries"])
        bins = np.searchsorted(boundaries, unary, side="right")
        np.testing.assert_array_equal(bins, scored["propensity_bins"])
        a, b, positive = ev["a"], ev["b"], ev["positive"]
        weights = ev["num"].astype(float) / ev["den"]
        code = np.minimum(a, b) * len(component) + np.maximum(a, b)
        incidence = defaultdict(list)
        for row, (left, right) in enumerate(zip(a, b, strict=True)):
            incidence[int(left)].append((row, int(right)))
            incidence[int(right)].append((row, int(left)))
        recalls = {name: {k: [] for k in (10, 100)} for name in cfg["models"]}
        for anchor in sorted(incidence):
            edges = np.array(incidence[anchor])
            pe, ue = edges[positive[edges[:, 0]]], edges[~positive[edges[:, 0]]]
            if not len(pe) or not len(ue):
                continue
            mask = bins[pe[:, 1], None] == bins[ue[:, 1]]
            u_weights = mask * weights[ue[:, 0]]
            denominator = u_weights.sum(axis=1)
            for name in propensity:
                s = scores[:, columns.index(name)]
                credits = (s[pe[:, 0], None] > s[ue[:, 0]]).astype(float) + .5 * (s[pe[:, 0], None] == s[ue[:, 0]])
                valid = denominator > 0
                propensity[name].append(float(((credits * u_weights).sum(axis=1)[valid] / denominator[valid]).mean()) if valid.any() else np.nan)
            for name in recalls:
                ordered = sorted(edges[:, 0], key=lambda i: (-scores[i, columns.index(name)], code[i]))
                for k in recalls[name]:
                    recalls[name][k].append(float(positive[ordered[:k]].sum() / len(pe)))
        for name in recalls:
            for k in recalls[name]:
                np.testing.assert_allclose(np.mean(recalls[name][k]), report["folds"][fold]["panel_recall"][name][str(k)], rtol=0, atol=1e-12)
        rows, endpoints = ev["quartet_rows"], ev["quartet_endpoints"]
        qweights = np.ones((len(rows), len(draws)))
        for i, proteins in enumerate(endpoints):
            for c in set(component[proteins]):
                qweights[i] *= draws[:, c]
        contrast = scores[rows[:, 0]] + scores[rows[:, 1]] - scores[rows[:, 2]] - scores[rows[:, 3]]
        credit = np.where(np.abs(contrast) <= 1e-6, .5, (contrast > 0).astype(float))
        quartet_total += qweights.T @ credit[:, [columns.index(n) for n in names]]
        quartet_mass += qweights.sum(axis=0)
    for i, name in enumerate(names):
        np.testing.assert_allclose(quartet_total[:, i] / quartet_mass, boot[f"quartet_{name}"], rtol=0, atol=1e-12)
    pair, unary = [np.asarray(propensity[n]) for n in ("pair_linear", "endpoint_mlp64")]
    valid = np.isfinite(pair) & np.isfinite(unary)
    np.testing.assert_allclose(np.mean(pair[valid] - unary[valid]), report["propensity_sensitivity"]["delta"], rtol=0, atol=1e-12)
    assert int(valid.sum()) == report["propensity_sensitivity"]["eligible_anchors"]
    for name, expected in report["model_ci95"].items():
        np.testing.assert_allclose(np.nanpercentile(boot[f"anchor_{name}"], [2.5, 97.5]), expected, rtol=0, atol=1e-12)
    np.testing.assert_allclose(np.nanpercentile(boot["quartet_pair_linear"], [2.5, 97.5]), report["quartets"]["ci95"], rtol=0, atol=1e-12)
    for name, expected in report["quartets"]["paired_control_ci95"].items():
        np.testing.assert_allclose(np.nanpercentile(boot["quartet_pair_linear"] - boot[f"quartet_{name}"], [2.5, 97.5]), expected, rtol=0, atol=1e-12)
    training = json.loads((results / "TRAINING_COMPLETE.json").read_text())
    orders = defaultdict(set)
    freeze_hash = digest(results / "EXECUTION_FREEZE.json")
    for fit in training["runs"]:
        checkpoint = torch.load(root / fit["checkpoint"]["path"], weights_only=True, map_location="cpu")
        assert checkpoint["execution_freeze_sha256"] == freeze_hash
        for label in ("p", "u"):
            count = int(np.sum((folds[data[f"{label}_a"]] != fit["fold"]) & (folds[data[f"{label}_b"]] != fit["fold"])))
            assert count == fit[f"fit_{label.upper()}"]
        for monitor in fit["monitors"]:
            orders[(fit["fold"], fit["seed"], monitor["pass"])].add(json.dumps(monitor["order_hashes"], sort_keys=True))
    assert len(orders) == 45 and all(len(x) == 1 for x in orders.values())
    result = {"pass": True, "created_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "post_readout_arithmetic_validation_only_no_new_metrics_or_decision_rules",
              "source_sha256": digest(Path(__file__)), "result_sha256": digest(results / "RESULTS.json"),
              "all_quartet_component_replicates_checked": len(draws), "quartet_scorers_checked": len(names),
              "all_propensity_bins_and_matched_anchor_metrics_checked": True,
              "all_reported_panel_recalls_and_intervals_checked": True,
              "all_checkpoint_freeze_identities_and_fit_counts_checked": True,
              "matched_training_orders_checked": len(orders)}
    with output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
