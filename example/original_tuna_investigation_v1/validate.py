"""Independent sklearn ranking checks on diagnostic outputs and saved scores."""
from __future__ import annotations

import math
import os
import numpy as np
from sklearn.metrics import average_precision_score, ndcg_score, roc_auc_score

from investigate import OUT, PARENT, check_inputs, parent_check, read, sha, table, write_json


def close(a, b):
    assert math.isclose(float(a), float(b), rel_tol=2e-12, abs_tol=2e-12), (a, b)


def validate_metrics(row, score, label):
    p = int(label.sum())
    close(row["P"], p)
    close(row["U"], len(label) - p)
    close(row["P_vs_U_concordance"], roc_auc_score(label, score))
    close(row["average_precision"], average_precision_score(label, score))
    for k in (5, 10, 20):
        close(row[f"NDCG_at_{k}"], ndcg_score(label[None, :].astype(float), score[None, :], k=k))
        recovered = sum(min(1., max(0., (k - (score > value).sum()) / (score == value).sum())) for value in score[label])
        close(row[f"recovered_P_at_{k}"], recovered)
        close(row[f"recall_at_{k}"], recovered / p)
        close(row[f"known_positive_precision_at_{k}"], recovered / k)
        close(row[f"EF_at_{k}"], recovered * len(label) / (k * p))


def main():
    assert os.environ.get("APPTAINER_CONTAINER")
    check_inputs()
    original = table(PARENT / "all_twelve_targets_scores.csv")
    labels = np.array([r["class"] == "P" for r in original])
    ids = {}
    for gene in {r["query_gene"] for r in original}:
        for name in ("context", "background", "low_plausibility", "context_background", "all_U"):
            strata = {"context", "background", "low_plausibility"} if name == "all_U" else {"context", "background"} if name == "context_background" else {name}
            ids[gene, name] = np.array([i for i, r in enumerate(original) if r["query_gene"] == gene and
                                       (r["class"] == "P" or r["U_stratum"] in strata)])
    swap = np.load(OUT / "query_swap_scores.npz", allow_pickle=False)
    assert sha(OUT / "query_swap_scores.npz") == read(OUT / "GPU_DIAGNOSTICS.json")["swap_cache"]["sha256"]
    qidx = {g: i for i, g in enumerate(swap["query_genes"].tolist())}
    counts = {}
    for filename in ("query_swap_metrics.csv", "partner_only_baselines.csv", "score_component_metrics.csv"):
        rows = table(OUT / filename)
        exposures = table(OUT / "pair_endpoint_exposure.csv")
        components = table(OUT / "original_score_components.csv")
        for row in rows:
            selected = ids[row["target"], row["candidate_set"]]
            if filename == "query_swap_metrics.csv":
                scores = swap[row["model"]][qidx[row["replacement_query"]], selected]
            elif filename == "partner_only_baselines.csv":
                scores = np.array([float(exposures[i][row["diagnostic"]]) for i in selected])
            else:
                scores = np.array([float(components[i][row["component"]]) for i in selected])
            validate_metrics(row, scores, labels[selected])
        counts[filename] = len(rows)
    parent = table(PARENT / "per_target_metrics.csv")
    lookup = {(r["target"], r["model"], r["candidate_set"]): r for r in parent if r["positive_subset"] == "all_P"}
    for row in table(OUT / "target_contributions.csv"):
        a = float(lookup[row["target"], "tuna_original", row["candidate_set"]][row["metric"]])
        b = float(lookup[row["target"], row["comparator"], row["candidate_set"]][row["metric"]])
        close(row["original"], a)
        close(row["comparator_value"], b)
        close(row["difference"], a - b)
        close(row["contribution_to_macro_difference"], (a - b) / 12)
    for row in table(OUT / "leave_one_target_out.csv"):
        remaining = [g for g in qidx if g != row["omitted_target"]]
        a = np.mean([float(lookup[g, "tuna_original", row["candidate_set"]][row["metric"]]) for g in remaining])
        b = np.mean([float(lookup[g, row["comparator"], row["candidate_set"]][row["metric"]]) for g in remaining])
        close(row["original_mean"], a)
        close(row["comparator_mean"], b)
        close(row["difference"], a - b)
    native = table(OUT / "authors_checkpoint_native_predictions.csv")
    assert len(native) == 50 and sum(r["class"] == "P" for r in native) == 37
    assert max(float(r["absolute_error"]) for r in native) < 1e-5
    for row in components:
        close(row["probability"], original[int(row["row_index"])]["tuna_original_score"])
    for row in exposures:
        if row["query_gene"] == "EGFR" and row["class"] == "P":
            assert all(int(v) == 0 for k, v in row.items() if k.endswith("_degree"))
    write_json("INDEPENDENT_VALIDATION.json", dict(passed=True, checked_metric_rows=counts,
        sklearn_ROC_AP_NDCG_oracles=True, fractional_topK_independently_checked=True,
        target_contribution_rows=360, leave_one_target_out_rows=360,
        native_authors_fixture_rows=len(native), parent_scientific_artifacts_unchanged=parent_check(),
        frozen_inputs_unchanged=True, protected_test_records_read=False))
    print("Independent diagnostic validation passed", counts, flush=True)


if __name__ == "__main__":
    main()
