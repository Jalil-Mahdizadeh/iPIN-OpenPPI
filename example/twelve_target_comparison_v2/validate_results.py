#!/usr/bin/env python3
"""Independent source, pair, metric and frozen-artifact validation."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import re

import h5py
import numpy as np

from run_comparison import MODELS, SEEDS, TARGETS, inputs, now, read, sha, write_json, record
from original_exposure import load as exposure_lookup, check as exposure_check

HERE = Path(__file__).resolve().parent
# This preserved independent oracle uses sklearn AUROC/AP/NDCG and separate
# combinatorial tie arithmetic; it does not call this run's metric evaluator.
spec = importlib.util.spec_from_file_location("previous_independent_oracle", HERE.parent / "twelve_target_comparison_v1/validate_results.py")
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def table(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def flag(row, key):
    return row[key] is True or row[key] == "True"


def selected(panel, subset, candidate_set):
    permitted = {"context": {"context"}, "background": {"background"}, "low_plausibility": {"low_plausibility"},
                 "context_background": {"context", "background"}, "all_U": {"context", "background", "low_plausibility"}}[candidate_set]
    result = []
    for row in panel:
        if subset.startswith("exclude_any_model") and (flag(row, "prior_train_development_pair") or flag(row, "original_tuna_prior_pair")):
            continue
        if row["class"] == "P":
            if subset.startswith("exclude_development") and flag(row, "development_exposed_positive"):
                continue
            if subset.startswith("exclude_prior_train_development") and flag(row, "prior_train_development_pair"):
                continue
            if subset.endswith("and_homomers") and flag(row, "homomeric"):
                continue
            result.append(row)
        elif row["U_stratum"] in permitted:
            result.append(row)
    return result


def sampling(root, out, rows):
    with (out / "sources/reviewed_human_annotations.tsv").open() as stream:
        proteins = {r["Entry"]: r for r in csv.DictReader(stream, delimiter="\t")}
    annotations = table(out / "low_plausibility_annotations.csv")
    assert len(annotations) == 1850
    mapped = {(r["target"], r["partner_uniprot"]): r for r in annotations}
    original, provenance = exposure_lookup(root)
    for gene in TARGETS:
        manifest = read(out / "panels" / gene / "panel_manifest.json")
        parent = read(root / "example" / gene / "panel_manifest.json")
        assert sha(root / manifest["parent_manifest"]["path"]) == manifest["parent_manifest"]["sha256"]
        panel = [r for r in rows if r["query_gene"] == gene]
        assert len(panel) == (604 if gene == "ERN1" else 453)
        assert len({r["partner_uniprot"] for r in panel}) == len(panel)
        assert len({r["partner_sequence_sha256"] for r in panel}) == len(panel)
        originals = table(root / "example" / gene / f"{gene.lower()}_ipin_panel.csv")
        for old, current in zip(originals, panel[:len(originals)], strict=True):
            assert all(current[k] == v for k, v in old.items())
        for old, current in zip(parent["rows"], manifest["rows"][:len(parent["rows"])], strict=True):
            for key in ("partner_uniprot", "class", "sequence_sha256", "stratum", "anchor_positive_uniprot"):
                assert old.get(key, "") == current.get(key, "")
        anchors = {r["partner_uniprot"]: int(r["partner_sequence_length"]) for r in panel if r["class"] == "P"}
        counts = Counter((r["anchor_positive_uniprot"], r["U_stratum"]) for r in panel if r["class"] == "U")
        assert counts == Counter({(a, s): 50 for a in anchors for s in ("context", "background", "low_plausibility")})
        for r in panel:
            q = {"accession": r["query_uniprot"], "sequence_sha256": r["query_sequence_sha256"]}
            p = {"accession": r["partner_uniprot"], "sequence_sha256": r["partner_sequence_sha256"]}
            exposure = exposure_check(original, q, p)
            assert flag(r, "original_tuna_prior_pair") == any(exposure.values())
            if r["U_stratum"] != "low_plausibility":
                continue
            acc, digest = r["partner_uniprot"], r["partner_sequence_sha256"]
            source, annotation = proteins[acc], mapped[gene, acc]
            assert acc not in manifest["excluded_accessions"] and digest not in manifest["excluded_sequence_sha256"]
            assert not any(exposure.values()) and not flag(r, "prior_train_development_pair")
            assert .5 <= len(source["Sequence"]) / anchors[r["anchor_positive_uniprot"]] <= 2
            assert hashlib.sha256(source["Sequence"].encode()).hexdigest() == digest
            assert not source["Transmembrane"]
            assert annotation["uniprot_location"] == source["Subcellular location [CC]"]
            loc = re.sub(r"\{[^}]*\}", "", source["Subcellular location [CC]"]).lower()
            assert not any(t in loc for t in ("cytoplasm", "cytosol", "cell membrane", "nucleus membrane", "nuclear membrane", "cell junction", "synapse", "outer membrane", "intermembrane", "exosome"))
            category = annotation["localization_class"]
            if category in ("secreted", "secretory_lumen"):
                assert source["Signal peptide"] and not any(t in loc for t in ("mitochond", "peroxisom", "nucleus", "nuclear", "chromosome", "nucleol"))
            if category == "mitochondrial_matrix":
                assert "mitochondrion matrix" in loc.split("note=", 1)[0]
            if annotation["evidence_tier"].startswith("B_"):
                assert gene == "EGFR" and annotation["uniprot_experimental_location"] == "True" and annotation["hpa_supported_location"] == "True"
            else:
                assert category in manifest["strict_candidate_classes"]
    for metadata in (out / "sources").glob("*.metadata.json"):
        source = metadata.with_name(metadata.name.removesuffix(".metadata.json"))
        assert sha(source) == read(metadata)["sha256"]
    return dict(Counter(r["evidence_tier"] for r in annotations))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root, args.output
    assert os.environ.get("APPTAINER_CONTAINER")
    raw, snapshot, order, sequences = inputs(root, out)
    rows = table(out / "all_twelve_targets_scores.csv")
    assert len(rows) == len(raw) == 5587 and sum(r["class"] == "P" for r in rows) == 37
    for source, scored in zip(raw, rows, strict=True):
        assert all(scored[k] == str(v) for k, v in source.items())
        assert np.isfinite([float(scored[m + "_score"]) for m in MODELS]).all()
        assert np.mean([float(scored[f"tuna_retrained_seed{s}_score"]) for s in SEEDS]) == float(scored["tuna_retrained_score"])
    tiers = sampling(root, out, rows)
    exposed = reference.exposure_audit(root, rows)
    panels = {g: [r for r in rows if r["query_gene"] == g] for g in TARGETS}
    metrics = table(out / "per_target_metrics.csv")
    for row in metrics:
        reference.check_values(row, reference.oracle(selected(panels[row["target"]], row["positive_subset"], row["candidate_set"]), row["model"]))
    coverage = table(out / "analysis_coverage.csv")
    assert len(coverage) == 12 * 7 * 5
    for row in coverage:
        panel = selected(panels[row["target"]], row["positive_subset"], row["candidate_set"])
        p = sum(r["class"] == "P" for r in panel)
        assert int(row["P"]) == p and int(row["U"]) == len(panel) - p
        assert flag(row, "evaluated") == bool(p)
        found = [r for r in metrics if all(r[k] == row[k] for k in ("target", "positive_subset", "candidate_set"))]
        assert len(found) == (4 if p else 0)
    matched = table(out / "matched_positive_metrics.csv")
    assert len(matched) == 37 * 4 * 5
    for row in matched:
        pool = selected(panels[row["target"]], "all_P", row["candidate_set"])
        own = [r for r in pool if (r["class"] == "P" and r["partner_uniprot"] == row["partner_uniprot"])
               or (r["class"] == "U" and r["anchor_positive_uniprot"] == row["partner_uniprot"])]
        assert len(own) == {"context": 51, "background": 51, "low_plausibility": 51, "context_background": 101, "all_U": 151}[row["candidate_set"]]
        reference.check_values(row, reference.oracle(own, row["model"]))
    macro = table(out / "macro_metrics.csv")
    assert len(macro) == 4 * 7 * 5 * 4
    for row in macro:
        genes = list(TARGETS)
        if row["cohort"] == "original_six": genes = list(TARGETS[:6])
        if row["cohort"] == "additional_six": genes = list(TARGETS[6:])
        if row["cohort"] == "strict_evidence_eleven": genes.remove("EGFR")
        selected_rows = [r for r in metrics if r["target"] in genes and all(r[k] == row[k] for k in ("positive_subset", "candidate_set", "model"))]
        assert int(row["planned_targets"]) == len(genes) and int(row["targets"]) == len(selected_rows)
        assert row["omitted_targets"] == ";".join(g for g in genes if g not in {r["target"] for r in selected_rows})
        mapping = {"macro_P_vs_U_concordance": "P_vs_U_concordance", "MAP": "average_precision", "MRR": "reciprocal_rank", "mean_first_positive_rank": "first_positive_rank_expected"}
        for k in (5, 10, 20):
            mapping.update({f"macro_{m}_at_{k}": f"{m}_at_{k}" for m in ("recall", "known_positive_precision", "EF", "NDCG", "target_success")})
        expected = {k: np.mean([float(r[v]) for r in selected_rows]) for k, v in mapping.items()}
        expected.update(P=sum(int(r["P"]) for r in selected_rows), U=sum(int(r["U"]) for r in selected_rows))
        for k in (5, 10, 20):
            expected[f"total_recovered_P_at_{k}"] = sum(float(r[f"recovered_P_at_{k}"]) for r in selected_rows)
            expected[f"target_success_count_at_{k}"] = sum(float(r[f"target_success_at_{k}"]) for r in selected_rows)
        reference.check_values(row, expected)
    curves = table(out / "retrieval_curves.csv")
    assert len(curves) == 12 * 4 * 5 * 50
    for row in curves:
        k = int(row["K"])
        expected = reference.oracle(selected(panels[row["target"]], "all_P", row["candidate_set"]), row["model"], (k,))
        reference.check_values(row, {"recovered_P": expected[f"recovered_P_at_{k}"], "recall": expected[f"recall_at_{k}"], "target_success": expected[f"target_success_at_{k}"]})
    ranks = table(out / "positive_partner_ranks.csv")
    assert len(ranks) == 37 * 4 * 5
    for row in ranks:
        values = np.sort([float(r[row["model"] + "_score"]) for r in selected(panels[row["query_gene"]], "all_P", row["candidate_set"])])
        lo, hi = np.searchsorted(values, float(row["score"]), "left"), np.searchsorted(values, float(row["score"]), "right")
        a, b = len(values) - hi + 1, len(values) - lo
        reference.check_values(row, {"rank_min": a, "rank_max": b, "rank_mid": (a + b) / 2, "panel_size": len(values),
                                    **{f"top{k}_fractional_credit": min(1., max(0., (k - a + 1) / (b - a + 1))) for k in (5, 10, 20)}})
    for gene in TARGETS:
        assert table(out / f"{gene.lower()}_four_model_scores.csv") == panels[gene]
        for model in MODELS:
            base = {r["candidate_set"]: float(r["P_vs_U_concordance"]) for r in metrics if r["target"] == gene and r["model"] == model and r["positive_subset"] == "all_P"}
            assert math.isclose(base["all_U"], (base["context"] + base["background"] + base["low_plausibility"]) / 3, abs_tol=1e-14)
            assert math.isclose(base["all_U"], (2 * base["context_background"] + base["low_plausibility"]) / 3, abs_tol=1e-14)
    for name in ("IPIN_RUN.json", "TUNA_RUN.json"):
        run = read(out / name)
        assert run["freshly_embedded_sequences"] == len(order) and run["preexisting_feature_cache_reads"] == 0
        for item in run["verified_model_inputs"]:
            assert sha(Path(item["path"])) == item["sha256"]
    run = read(out / "TUNA_RUN.json")
    assert not run["GP_covariance_refitted"] and len(run["native_qualification"]) == 4
    assert all(r["all_parameters_and_buffers_unchanged"] and r["native_max_absolute_error"] <= r["tolerance"] for r in run["native_qualification"])
    assert sha(out / "tuna_fresh_residues.h5") == run["fresh_residues"]["sha256"]
    with h5py.File(out / "tuna_fresh_residues.h5") as archive:
        assert archive.attrs["complete"] and set(archive.keys()) == set(order)
    with np.load(out / "ipin_fresh_embeddings.npz", allow_pickle=False) as archive:
        assert archive["raw"].shape == archive["standardized"].shape == (len(order), 640)
        assert archive["sequence_sha256"].tolist() == order
        assert np.isfinite(archive["raw"]).all() and np.isfinite(archive["standardized"]).all()
    for member in ["tuna_original"] + [f"tuna_retrained_seed{s}" for s in SEEDS]:
        array = np.load(out / f"{member}_fresh_endpoint_features.npy", allow_pickle=False)
        assert array.shape == (len(order), 64) and np.isfinite(array).all()
    for relative, digest in read(out / "INPUT_FREEZE.json")["original_file_hashes"].items():
        assert sha(root / relative) == digest
    write_json(out / "INDEPENDENT_VALIDATION.json", {"at_utc": now(), "passed": True, "pairs": len(rows), "four_model_scores": len(rows) * 4,
        "metric_rows_recomputed": len(metrics), "macro_rows_verified": len(macro), "matched_rows_recomputed": len(matched),
        "curve_rows_recomputed": len(curves), "rank_rows_verified": len(ranks), "evidence_tiers": tiers,
        "original_panels_preserved_as_prefixes": True, "historical_artifacts_unchanged": True,
        "new_U_excluded_from_all_checked_model_training_validation_pairs": True,
        "exact_pair_exposed_iPIN_positives": exposed, "concordance_mixture_identity_passed": True,
        "fresh_embeddings_verified": True, "frozen_models_unchanged": True, "protected_test_truth_read": False,
        "oracle": record(HERE.parent / "twelve_target_comparison_v1/validate_results.py"), "validator": record(Path(__file__))})
    print("Independent numerical, identity, sampling, exposure and artifact audit passed", flush=True)


if __name__ == "__main__":
    main()
