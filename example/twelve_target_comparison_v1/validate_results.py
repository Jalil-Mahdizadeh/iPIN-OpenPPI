#!/usr/bin/env python3
"""Independent numerical, input-identity, source, exposure, and artifact audit."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
from pathlib import Path
import re

import h5py
import numpy as np
from sklearn.metrics import average_precision_score, ndcg_score, roc_auc_score

from run_comparison import CONFIG, MODELS, SEEDS, TARGETS, catalogue, now, read, record, sha, write_json


def table(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def flag(row, key):
    return row[key] is True or row[key] == "True"


def select(panel, subset, stratum):
    result = []
    for row in panel:
        if row["class"] == "U":
            if stratum == "all_U" or row["U_stratum"] == stratum:
                result.append(row)
            continue
        if subset.startswith("exclude_development") and flag(row, "development_exposed_positive"):
            continue
        if subset.startswith("exclude_prior_train_development") and flag(row, "prior_train_development_pair"):
            continue
        if subset.endswith("and_homomers") and flag(row, "homomeric"):
            continue
        result.append(row)
    return result


def oracle(panel, model, cutoffs=(5, 10, 20)):
    score = np.asarray([float(r[model + "_score"]) for r in panel])
    label = np.asarray([r["class"] == "P" for r in panel])
    p, n = int(label.sum()), len(label)
    assert np.isfinite(score).all() and 0 < p < n
    # Independent trusted implementations for the three full ranking metrics.
    result = {"P": p, "U": n - p, "panel_size": n,
              "P_vs_U_concordance": roc_auc_score(label, score),
              "average_precision": average_precision_score(label, score)}
    best = max(score[label])
    g, t, m = int((score > best).sum()), int((score == best).sum()), int(((score == best) & label).sum())
    mass = [math.comb(t - j, m - 1) / math.comb(t, m) for j in range(1, t - m + 2)]
    result.update(first_positive_rank_min=g + 1, first_positive_rank_max=g + t - m + 1,
                  first_positive_rank_expected=sum((g + j) * prob for j, prob in enumerate(mass, 1)),
                  reciprocal_rank=sum(prob / (g + j) for j, prob in enumerate(mass, 1)))
    for k in cutoffs:
        recovered = sum(min(1., max(0., (k - int((score > value).sum())) / int((score == value).sum()))) for value in score[label])
        result.update({f"recovered_P_at_{k}": recovered, f"recall_at_{k}": recovered / p,
                       f"known_positive_precision_at_{k}": recovered / k,
                       f"EF_at_{k}": recovered * n / (k * p),
                       f"NDCG_at_{k}": ndcg_score(label[None, :].astype(float), score[None, :], k=k, ignore_ties=False),
                       f"target_success_at_{k}": sum(prob for j, prob in enumerate(mass, 1) if g + j <= k)})
    return result


def check_values(observed, expected):
    for key, value in expected.items():
        if not math.isclose(float(observed[key]), float(value), abs_tol=2e-12, rel_tol=2e-12):
            raise AssertionError((key, observed[key], value, observed.get("target"), observed.get("model")))


def exposure_audit(root, rows):
    folder = root / "benchmark/tuna/data"
    reference = read(folder / "sequences.json")
    records = {Path(r["path"]).name: r for r in read(folder / "DATA_MANIFEST.json")["outputs"]}
    identifiers = {}
    for i, (digest, accessions) in enumerate(zip(reference["sha256"], reference["accessions"], strict=True)):
        for key in [digest, *accessions]:
            identifiers.setdefault(key, set()).add(i)
    pairs = {}
    for gene in TARGETS:
        row = next(r for r in rows if r["query_gene"] == gene)
        query_ids = identifiers.get(row["query_uniprot"], set()) | identifiers.get(row["query_sequence_sha256"], set())
        pairs[gene] = {"query": query_ids, **{key: set() for key in ("TRAIN_P", "TRAIN_U", "DEV_P", "DEV_U")}}
    for name in ("training.npz", "development_00.npz", "development_01.npz", "development_02.npz"):
        assert sha(folder / name) == records[name]["sha256"]
        with np.load(folder / name, allow_pickle=False) as archive:
            if name == "training.npz":
                groups = [(key, archive[prefix + "_a"], archive[prefix + "_b"]) for key, prefix in (("TRAIN_P", "p"), ("TRAIN_U", "u"))]
            else:
                groups = [(key, archive["a"][archive["positive"] == positive], archive["b"][archive["positive"] == positive])
                          for key, positive in (("DEV_P", True), ("DEV_U", False))]
            for key, left, right in groups:
                for groups_by_gene in pairs.values():
                    ids = list(groups_by_gene["query"])
                    groups_by_gene[key].update(right[np.isin(left, ids)].tolist())
                    groups_by_gene[key].update(left[np.isin(right, ids)].tolist())
    exposed = []
    for row in rows:
        partner = identifiers.get(row["partner_uniprot"], set()) | identifiers.get(row["partner_sequence_sha256"], set())
        observed = {key: bool(partner & neighbors) for key, neighbors in pairs[row["query_gene"]].items() if key != "query"}
        assert flag(row, "development_exposed_positive") == observed["DEV_P"]
        assert flag(row, "training_exposed_positive") == observed["TRAIN_P"]
        assert flag(row, "prior_train_development_pair") == any(observed.values())
        if row["class"] == "U":
            assert not any(observed.values())
        elif any(observed.values()):
            exposed.append({"target": row["query_gene"], "partner": row["partner_gene"], **observed})
    return exposed


def sampling_audit(root, out):
    with (out / "sources/reviewed_human.tsv").open(newline="") as stream:
        pool = {r["Entry"]: r for r in csv.DictReader(stream, delimiter="\t")}
    for target in CONFIG["new_targets"]:
        manifest = read(root / "example" / target["gene"] / "panel_manifest.json")
        used = set()
        for block in manifest["U_blocks"]:
            selected = manifest["rows"][block["first_data_row"] - 1:block["last_data_row"]]
            assert len(selected) == 50
            anchor_length = len(pool[block["anchor_accession"]]["Sequence"])
            for row in selected:
                acc = row["partner_uniprot"]
                candidate = pool[acc]
                digest = row["sequence_sha256"]
                assert row["class"] == "U" and row["stratum"] == block["stratum"]
                assert row["anchor_positive_uniprot"] == block["anchor_accession"]
                assert acc not in manifest["excluded_accessions"] and digest not in manifest["excluded_sequence_sha256"]
                assert acc not in used
                used.add(acc)
                assert anchor_length / 2 <= len(candidate["Sequence"]) <= 2 * anchor_length
                if block["stratum"] == "context":
                    text = re.sub(r"\{[^}]*\}", "", candidate["Subcellular location [CC]"].split("Note=", 1)[0]).lower()
                    terms = ("cytoplasm", "cytosol") if block["compartment"] == "cytoplasm" else (block["compartment"],)
                    assert any(term in text for term in terms)
                    assert bool(candidate["Transmembrane"]) == block["transmembrane"]
        assert len(used) == 300


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root, args.output
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Scientific validation requires an accepted SIF")
    catalogue(root)
    frozen = read(out / "INPUT_FREEZE.json")
    rows = table(out / "all_twelve_targets_scores.csv")
    raw = read(out / "pairs.json")
    assert len(rows) == len(raw) == 3737 and sum(r["class"] == "P" for r in rows) == 37
    for original, scored in zip(raw, rows, strict=True):
        assert all(scored[key] == str(value) for key, value in original.items())
        assert np.isfinite([float(scored[m + "_score"]) for m in MODELS]).all()
        assert np.mean([float(scored[f"tuna_retrained_seed{s}_score"]) for s in SEEDS], dtype=np.float64) == float(scored["tuna_retrained_score"])
    assert sha(out / "pairs.json") == frozen["pair_manifest_sha256"]
    assert sha(out / "uniprot_sequences.json") == frozen["sequence_snapshot"]["sha256"]
    assert sha(out / "METRICS.md") == frozen["metric_protocol_sha256"]
    for item in frozen["input_files"] + frozen["implementation_files"]:
        assert sha(root / item["path"]) == item["sha256"], item["path"]
    for relative, digest in frozen["original_file_hashes"].items():
        assert sha(root / relative) == digest, relative
    build = read(out / "PANEL_BUILD.json")
    assert sha(out / "build_panels.py") == build["builder_sha256"]
    assert sha(out / "panel_config.json") == build["configuration_sha256"]
    for item in build["new_targets"]:
        assert sha(root / "example" / item["target"] / "panel_manifest.json") == item["manifest_sha256"]
    for metadata_path in (out / "sources").glob("*.metadata.json"):
        source = metadata_path.with_name(metadata_path.name.removesuffix(".metadata.json"))
        assert sha(source) == read(metadata_path)["sha256"]
    panels = {gene: [r for r in rows if r["query_gene"] == gene] for gene in TARGETS}
    snapshot = read(out / "uniprot_sequences.json")["records"]
    for gene, panel in panels.items():
        name = gene.lower() + "_three_model_scores.csv"
        assert (out / name).read_bytes() == (root / "example" / gene / name).read_bytes()
        assert len(panel) == (404 if gene == "ERN1" else 303)
        assert len({r["partner_uniprot"] for r in panel}) == len(panel)
        assert len({r["partner_sequence_sha256"] for r in panel}) == len(panel)
        for row in panel:
            for side in ("query", "partner"):
                protein = snapshot[row[side + "_uniprot"]]
                assert protein["sequence_sha256"] == row[side + "_sequence_sha256"]
                assert protein["sequence_length"] == int(row[side + "_sequence_length"])
        for model in MODELS:
            score = np.asarray([float(r[model + "_score"]) for r in panel])
            ascending = np.sort(score)
            ranks = len(score) - (np.searchsorted(ascending, score, "left") + np.searchsorted(ascending, score, "right")) / 2 + .5
            assert np.array_equal(ranks, [float(r[model + "_rank"]) for r in panel])
    exposed = exposure_audit(root, rows)
    sampling_audit(root, out)
    metrics = table(out / "per_target_metrics.csv")
    assert len(metrics) == 12 * 3 * 5 * 3
    for metric in metrics:
        panel = select(panels[metric["target"]], metric["positive_subset"], metric["U_stratum"])
        check_values(metric, oracle(panel, metric["model"]))
    matched = table(out / "matched_positive_metrics.csv")
    assert len(matched) == 37 * 3 * 3
    for metric in matched:
        panel = panels[metric["target"]]
        positive = [r for r in panel if r["class"] == "P" and r["partner_uniprot"] == metric["partner_uniprot"]]
        controls = [r for r in panel if r["class"] == "U" and r["anchor_positive_uniprot"] == metric["partner_uniprot"]
                    and (metric["U_stratum"] == "all_U" or r["U_stratum"] == metric["U_stratum"])]
        assert len(positive) == 1 and len(controls) == (100 if metric["U_stratum"] == "all_U" else 50)
        check_values(metric, oracle(positive + controls, metric["model"]))
    macro = table(out / "macro_metrics.csv")
    assert len(macro) == 3 * 3 * 5 * 3
    for row in macro:
        genes = TARGETS if row["cohort"] == "all_twelve" else (CONFIG["original_targets"] if row["cohort"] == "original_six" else [t["gene"] for t in CONFIG["new_targets"]])
        selected = [r for r in metrics if r["target"] in genes and all(r[key] == row[key] for key in ("model", "positive_subset", "U_stratum"))]
        mapping = {"macro_P_vs_U_concordance": "P_vs_U_concordance", "MAP": "average_precision", "MRR": "reciprocal_rank", "mean_first_positive_rank": "first_positive_rank_expected"}
        mapping.update({f"macro_{metric}_at_{k}": f"{metric}_at_{k}" for metric, k in itertools.product(("recall", "known_positive_precision", "EF", "NDCG", "target_success"), (5, 10, 20))})
        expected = {key: sum(float(r[value]) for r in selected) / len(selected) for key, value in mapping.items()}
        expected.update(targets=len(selected), P=sum(int(r["P"]) for r in selected), U=sum(int(r["U"]) for r in selected))
        for k in (5, 10, 20):
            expected[f"total_recovered_P_at_{k}"] = sum(float(r[f"recovered_P_at_{k}"]) for r in selected)
            expected[f"target_success_count_at_{k}"] = sum(float(r[f"target_success_at_{k}"]) for r in selected)
        check_values(row, expected)
    curves = table(out / "retrieval_curves.csv")
    assert len(curves) == 12 * 3 * 50
    for row in curves:
        k = int(row["K"])
        expected = oracle(panels[row["target"]], row["model"], (k,))
        check_values(row, {"recovered_P": expected[f"recovered_P_at_{k}"], "recall": expected[f"recall_at_{k}"], "target_success": expected[f"target_success_at_{k}"]})
    ranks = table(out / "positive_partner_ranks.csv")
    assert len(ranks) == 37 * 3
    for row in ranks:
        scores = np.sort([float(r[row["model"] + "_score"]) for r in panels[row["query_gene"]]])
        lo, hi = np.searchsorted(scores, float(row["score"]), "left"), np.searchsorted(scores, float(row["score"]), "right")
        minimum, maximum = len(scores) - hi + 1, len(scores) - lo
        expected = {"rank_min": minimum, "rank_max": maximum, "rank_mid": (minimum + maximum) / 2}
        expected.update({f"top{k}_fractional_credit": min(1., max(0., (k - minimum + 1) / (maximum - minimum + 1))) for k in (5, 10, 20)})
        check_values(row, expected)
    unique = frozen["unique_sequences"]
    with np.load(out / "ipin_fresh_embeddings.npz", allow_pickle=False) as archive:
        assert archive["raw"].shape == archive["standardized"].shape == (unique, 640)
        assert np.isfinite(archive["raw"]).all() and np.isfinite(archive["standardized"]).all()
        order = archive["sequence_sha256"].tolist()
        assert len(set(order)) == unique and order == read(out / "sequence_order.json")
    for name in ("IPIN_RUN.json", "TUNA_RUN.json"):
        run = read(out / name)
        assert run["freshly_embedded_sequences"] == unique and run["preexisting_feature_cache_reads"] == 0
        for item in run["verified_model_inputs"]:
            assert sha(root / Path(item["path"]).relative_to("/project")) == item["sha256"]
    run = read(out / "TUNA_RUN.json")
    assert run["GP_covariance_refitted"] is False and len(run["native_qualification"]) == 3
    assert all(r["all_parameters_and_buffers_unchanged"] and r["native_max_absolute_error"] <= r["tolerance"] for r in run["native_qualification"])
    assert sha(out / "tuna_fresh_residues.h5") == run["fresh_residues"]["sha256"]
    with h5py.File(out / "tuna_fresh_residues.h5", "r") as archive:
        assert archive.attrs["complete"] and set(archive.keys()) == set(order)
    for seed in SEEDS:
        array = np.load(out / f"tuna_retrained_seed{seed}_fresh_endpoint_features.npy", allow_pickle=False)
        assert array.shape == (unique, 64) and np.isfinite(array).all()
    write_json(out / "INDEPENDENT_VALIDATION.json", {"at_utc": now(), "passed": True, "pairs": len(rows), "three_model_scores": len(rows) * 3,
               "metric_rows_independently_recomputed": len(metrics), "matched_metric_rows_independently_recomputed": len(matched),
               "macro_rows_verified": len(macro), "curve_rows_verified": len(curves), "positive_rank_rows_verified": len(ranks),
               "all_twelve_published_CSVs_byte_identical": True, "original_files_unchanged": True,
               "all_U_absent_from_checked_TRAIN_development_pairs": True, "exact_pair_exposed_positives": exposed,
               "new_U_length_compartment_transmembrane_exclusion_constraints_verified": True,
               "frozen_parameters_unchanged": True, "fresh_embedding_artifacts_verified": True, "protected_test_pairs_or_truth_read": False,
               "validator": record(Path(__file__))})
    print("Independent metrics, source, exposure, identity, and artifact validation passed", flush=True)


if __name__ == "__main__":
    main()
