#!/usr/bin/env python3
"""Independent sorted-U metric and artifact verification, without old caches."""
import csv
import json
from pathlib import Path

import numpy as np

from run_comparison import MODELS, TARGETS, SEEDS, now, read, record, sha, write_json


def table(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    out = Path(__file__).resolve().parent
    root = out.parents[1]
    raw = read(out / "pairs.json")
    scored = table(out / "all_six_targets_scores.csv")
    metrics = table(out / "per_target_metrics.csv")
    rank_rows = table(out / "positive_partner_ranks.csv")
    assert len(scored) == len(raw) == 1919
    assert len(metrics) == 6 * 4 * 3 * 3 and len(rank_rows) == 19 * 4
    for original, result in zip(raw, scored, strict=True):
        for key, value in original.items():
            assert result[key] == str(value), (key, value, result[key])
        values = np.asarray([float(result[m + "_score"]) for m in MODELS])
        assert np.isfinite(values).all()
        member = np.asarray([float(result[f"tuna_retrained_seed{s}_score"]) for s in SEEDS], np.float64)
        assert member.mean(dtype=np.float64) == float(result["tuna_retrained_score"])
    for metric in metrics:
        panel = [r for r in scored if r["query_gene"] == metric["target"]]
        p = [r for r in panel if r["class"] == "P"]
        subset = metric["positive_subset"]
        if subset != "all_P":
            p = [r for r in p if r["development_exposed_positive"] == "False"]
        if subset == "exclude_development_P_and_homomers":
            p = [r for r in p if r["homomeric"] == "False"]
        u = [r for r in panel if r["class"] == "U" and (metric["U_stratum"] == "all_U" or r["U_stratum"] == metric["U_stratum"])]
        key = metric["model"] + "_score"
        ps = np.asarray([float(r[key]) for r in p])
        us = np.sort(np.asarray([float(r[key]) for r in u]))
        # Independent algorithm: counts below/equal from binary searches,
        # rather than the production pairwise comparison matrix.
        value = ((np.searchsorted(us, ps, side="left") + np.searchsorted(us, ps, side="right")) / (2 * len(us))).mean()
        assert abs(value - float(metric["P_vs_U_concordance"])) < 1e-14
        assert (len(p), len(u)) == (int(metric["P"]), int(metric["U"]))
    for row in rank_rows:
        panel = [r for r in scored if r["query_gene"] == row["query_gene"]]
        score = float(row["score"])
        values = np.sort([float(r[row["model"] + "_score"]) for r in panel])
        lo, hi = np.searchsorted(values, score, side="left"), np.searchsorted(values, score, side="right")
        rank_min, rank_max = len(values) - hi + 1, len(values) - lo
        assert rank_min == int(row["rank_min"]) and rank_max == int(row["rank_max"])
        assert (rank_min + rank_max) / 2 == float(row["rank_mid"])
    for gene in TARGETS:
        name = gene.lower() + "_four_model_scores.csv"
        assert (out / name).read_bytes() == (root / "example" / gene / name).read_bytes()
        panel = table(out / name)
        assert len(panel) == (404 if gene == "ERN1" else 303)
    for meta in ("IPIN_RUN.json", "TUNA_RUN.json"):
        run = read(out / meta)
        assert run["freshly_embedded_sequences"] == 1829 and run["preexisting_feature_cache_reads"] == 0
        for item in run["verified_model_inputs"]:
            path = root / Path(item["path"]).relative_to("/project")
            assert sha(path) == item["sha256"], path
    for rel, expected in read(out / "INPUT_FREEZE.json")["original_file_hashes"].items():
        assert sha(root / rel) == expected, rel
    with np.load(out / "ipin_fresh_embeddings.npz", allow_pickle=False) as archive:
        assert archive["raw"].shape == archive["standardized"].shape == (1829, 640)
        assert np.isfinite(archive["raw"]).all() and np.isfinite(archive["standardized"]).all()
        order = archive["sequence_sha256"].tolist()
        assert len(set(order)) == 1829 and order == read(out / "sequence_order.json")
    for name in ["tuna_original"] + [f"tuna_retrained_seed{s}" for s in SEEDS]:
        array = np.load(out / f"{name}_fresh_endpoint_features.npy", allow_pickle=False)
        assert array.shape == (1829, 64) and np.isfinite(array).all()
    run = read(out / "TUNA_RUN.json")
    assert sha(out / "tuna_fresh_residues.h5") == run["fresh_residues"]["sha256"]
    assert run["GP_covariance_refitted"] is False
    assert len(run["native_qualification"]) == 4
    assert all(q["native_max_absolute_error"] <= q["tolerance"] and q["all_parameters_and_buffers_unchanged"] for q in run["native_qualification"])
    result = {"at_utc": now(), "passed": True, "complete_pair_rows": 1919,
              "four_model_scores": 7676, "independently_recomputed_metric_cells": len(metrics),
              "independently_verified_positive_rank_rows": len(rank_rows),
              "all_six_published_CSVs_byte_identical": True,
              "new_embedding_artifacts_verified": True, "frozen_weights_and_original_files_unchanged": True,
              "validator": record(Path(__file__))}
    write_json(out / "INDEPENDENT_VALIDATION.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
