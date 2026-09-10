"""Separately implemented numerical checks; no production model/metric imports.

This is same-author reference validation, not an external scientific review.
All learned score values and anchor point metrics are checked. Sixteen complete
component replicates are recomputed by direct P-by-U comparisons, independently
of the production sorted-prefix bootstrap; all saved replicates' CIs are checked.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import math

import numpy as np
import pyarrow.parquet as pq
from scipy.special import erf

from .data import GENERATED, RESULTS, VALIDATION, artifact, config, now, read_json, verify_freeze, verify_records, write_json


def reference_scores(state, name, raw, a, b):
    """FP64 NumPy/SciPy forward, algebraically independent of Torch model code."""
    w = {key: value.numpy().astype(np.float64) for key, value in state.items()}
    x = raw.astype(np.float64)
    if name == "endpoint_linear":
        unary = (x @ w["unary.weight"].T + w["unary.bias"]).ravel()
        return unary[a] + unary[b]
    if name == "endpoint_mlp64":
        z = x @ w["unary.0.weight"].T + w["unary.0.bias"]
        z = .5 * z * (1 + erf(z / math.sqrt(2)))
        unary = (z @ w["unary.2.weight"].T + w["unary.2.bias"]).ravel()
        return unary[a] + unary[b]
    if name != "pair_linear":
        raise RuntimeError("unregistered reference head")
    out = np.empty(len(a))
    for start in range(0, len(a), 4096):
        stop = min(len(a), start + 4096)
        left, right = x[a[start:stop]], x[b[start:stop]]
        cosine = np.sum(left * right, axis=1) / (np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1))
        features = np.concatenate((left + right, np.abs(left - right), left * right, cosine[:, None]), axis=1)
        out[start:stop] = (features @ w["output.weight"].T + w["output.bias"]).ravel()
    return out


def reference_anchor(scores, p_rows, u_rows, weights, p_multiplier=None, u_multiplier=None):
    comparison = (scores[p_rows, None] > scores[u_rows]).astype(np.float64)
    comparison += .5 * (scores[p_rows, None] == scores[u_rows])
    pw = np.ones(len(p_rows)) if p_multiplier is None else p_multiplier
    uw = weights[u_rows] * (1 if u_multiplier is None else u_multiplier)
    denominator = pw.sum() * uw.sum()
    return float(np.sum(comparison * pw[:, None] * uw) / denominator) if denominator else np.nan


def validate(root):
    import torch
    cfg = config(root)
    verify_freeze(root)
    report, training = read_json(root / RESULTS / "RESULTS.json"), read_json(root / RESULTS / "TRAINING_COMPLETE.json")
    for payload in (training, read_json(root / RESULTS / "SCORING_COMPLETE.json")):
        verify_records(root, payload["artifacts"])
    verify_records(root, report["bootstrap_artifacts"])
    data = np.load(root / GENERATED / "public_arrays.npz", allow_pickle=False)
    metadata = read_json(root / GENERATED / "endpoint_metadata.json")
    public = np.load(root / GENERATED / "raw_public_embeddings.npy", allow_pickle=False)
    raw = np.load(root / cfg["inputs"]["embeddings"]["path"], mmap_mode="r", allow_pickle=False)
    manifest = read_json(root / cfg["inputs"]["embedding_manifest"]["path"])
    lookup = {v["sequence_sha256"]: v["row_index"] for v in manifest["vectors"]}
    if len(lookup) != 17000 or sorted(lookup.values()) != list(range(17000)):
        raise RuntimeError("reference embedding bijection failed")
    expected_public = np.stack([raw[lookup[e]] for e in metadata["endpoints"]])
    np.testing.assert_array_equal(public, expected_public)
    n = len(public)
    endpoint_lookup = {e: i for i, e in enumerate(metadata["endpoints"])}
    for state, key in (("p", "positive"), ("u", "unlabeled")):
        source = pq.read_table(root / cfg["inputs"][key]["path"], columns=[
            "endpoint_a_sha256", "endpoint_b_sha256", "sampling_weight_numerator", "sampling_weight_denominator"]).to_pydict()
        aa = np.array([endpoint_lookup[e] for e in source["endpoint_a_sha256"]])
        bb = np.array([endpoint_lookup[e] for e in source["endpoint_b_sha256"]])
        order = np.argsort(np.minimum(aa, bb) * n + np.maximum(aa, bb))
        np.testing.assert_array_equal(aa[order], data[f"{state}_a"])
        np.testing.assert_array_equal(bb[order], data[f"{state}_b"])
        for name, column in (("num", "sampling_weight_numerator"), ("den", "sampling_weight_denominator")):
            np.testing.assert_array_equal(np.array(source[column])[order], data[f"{state}_{name}"])
    partitions = pq.read_table(root / cfg["inputs"]["partitions"]["path"], columns=[
        "reference_sequence_sha256", "component_id", "partition"]).to_pydict()
    mapping = {e: c for e, c, p in zip(partitions["reference_sequence_sha256"], partitions["component_id"], partitions["partition"], strict=True) if p == "train"}
    sizes = Counter(mapping.values())
    totals, assignments = [0, 0, 0], {}
    for c in sorted(sizes, key=lambda c: (-sizes[c], hashlib.sha256((cfg["split"]["salt"] + ":" + c).encode()).digest(), c)):
        fold = totals.index(min(totals))
        assignments[c] = fold
        totals[fold] += sizes[c]
    np.testing.assert_array_equal(data["fold"], [assignments[mapping[e]] for e in metadata["endpoints"]])
    np.testing.assert_array_equal(data["component"], [metadata["components"].index(mapping[e]) for e in metadata["endpoints"]])
    draws = np.load(root / GENERATED / "component_multipliers.npy", allow_pickle=False)
    expected_draws = np.random.Generator(np.random.PCG64DXSM(cfg["evaluation"]["bootstrap"]["seed"])).poisson(1, draws.shape)
    np.testing.assert_array_equal(draws, expected_draws)
    saved_boot = np.load(root / GENERATED / "bootstrap_metrics.npz", allow_pickle=False)
    ref_totals = {name: np.zeros(16) for name in ("pair_linear", "endpoint_mlp64")}
    ref_masses = {name: np.zeros(16) for name in ref_totals}
    points, qpoints, max_difference, learned_values = {}, {}, 0., 0
    for fold in range(3):
        norm = np.load(root / GENERATED / f"normalization_fold_{fold}.npz", allow_pickle=False)
        fitting = np.flatnonzero(data["fold"] != fold)
        np.testing.assert_array_equal(norm["fit_endpoints"], fitting)
        fit_values = expected_public[fitting].astype(np.float64)
        mean, std = fit_values.mean(0), np.maximum(fit_values.std(0), 1e-6)
        np.testing.assert_array_equal(mean, norm["mean"])
        np.testing.assert_array_equal(std, norm["std"])
        normalized = ((expected_public.astype(np.float64) - mean) / std).astype(np.float32)
        ev = np.load(root / GENERATED / f"evaluation_fold_{fold}.npz", allow_pickle=False)
        a, b, positive = ev["a"], ev["b"], ev["positive"]
        if not np.all((data["fold"][a] == fold) & (data["fold"][b] == fold)):
            raise RuntimeError("non-C3 evaluation row")
        for state, mask in (("p", positive), ("u", ~positive)):
            parent = ev["parent_row"][mask]
            expected = np.flatnonzero((data["fold"][data[f"{state}_a"]] == fold) & (data["fold"][data[f"{state}_b"]] == fold))
            np.testing.assert_array_equal(parent, expected)
            for field in ("a", "b", "num", "den"):
                np.testing.assert_array_equal(ev[field][mask], data[f"{state}_{field}"][parent])
        scores = np.load(root / GENERATED / f"scores_fold_{fold}.npz", allow_pickle=False)
        columns = list(scores["columns"])
        expected_columns = [f"{name}__{seed}" for name in cfg["models"] for seed in cfg["training"]["seeds"]] + cfg["models"] + ["length_ratio", "kmer3_cosine", "pooled_cosine"]
        if columns != expected_columns:
            raise RuntimeError("scorer set/order drift")
        for name in cfg["models"]:
            for seed in cfg["training"]["seeds"]:
                checkpoint = torch.load(root / GENERATED / f"fit_f{fold}_{name}_s{seed}.pt", map_location="cpu", weights_only=True)
                predicted = reference_scores(checkpoint["state_dict"], name, normalized, a, b)
                stored = scores["scores"][:, columns.index(f"{name}__{seed}")]
                difference = float(np.max(np.abs(predicted - stored)))
                max_difference = max(difference, max_difference)
                if difference > 1e-4:
                    raise RuntimeError(f"reference forward mismatch: {name}, {difference}")
                learned_values += len(stored)
            expected = scores["scores"][:, [columns.index(f"{name}__{s}") for s in cfg["training"]["seeds"]]].mean(1)
            np.testing.assert_array_equal(expected, scores["scores"][:, columns.index(name)])
        rows, endpoints = ev["quartet_rows"], ev["quartet_endpoints"]
        if len(rows) > cfg["quartets"]["maximum_per_fold"] or any(len(set(e)) != 4 for e in endpoints):
            raise RuntimeError("invalid quartet count/endpoints")
        if not positive[rows[:, :2]].all() or positive[rows[:, 2:]].any():
            raise RuntimeError("quartet P/U role mismatch")
        codes = np.minimum(a, b) * n + np.maximum(a, b)
        for j, sides in enumerate(((0, 1), (2, 3), (0, 3), (2, 1))):
            left, right = endpoints[:, sides[0]], endpoints[:, sides[1]]
            np.testing.assert_array_equal(codes[rows[:, j]], np.minimum(left, right) * n + np.maximum(left, right))
        if max(Counter(rows[:, :2].ravel()).values()) > cfg["quartets"]["maximum_uses_per_positive_edge"] or max(Counter(endpoints.ravel()).values()) > cfg["quartets"]["maximum_uses_per_endpoint"]:
            raise RuntimeError("quartet reuse cap exceeded")
        weights = ev["num"].astype(np.float64) / ev["den"]
        # Independent endpoint incidence construction, not build_queries().
        incidence = {}
        for row, (left, right) in enumerate(zip(a, b, strict=True)):
            incidence.setdefault(int(left), []).append((row, int(right)))
            incidence.setdefault(int(right), []).append((row, int(left)))
        anchor_file = np.load(root / GENERATED / f"anchor_metrics_fold_{fold}.npz", allow_pickle=False)
        checked_anchors, local_points = [], {name: [] for name in columns}
        for anchor in sorted(incidence):
            incident = np.array(incidence[anchor])
            prows, urows = incident[positive[incident[:, 0]], 0], incident[~positive[incident[:, 0]], 0]
            if not len(prows) or not len(urows):
                continue
            checked_anchors.append(anchor)
            for i, name in enumerate(columns):
                values = scores["scores"][:, i]
                local_points[name].append(reference_anchor(values, prows, urows, weights))
                if name in ref_totals:
                    pp = np.where(a[prows] == anchor, b[prows], a[prows])
                    up = np.where(a[urows] == anchor, b[urows], a[urows])
                    for replicate in range(16):
                        multiplier = draws[replicate]
                        ac = data["component"][anchor]
                        pm = np.where(data["component"][pp] == ac, 1, multiplier[data["component"][pp]])
                        um = np.where(data["component"][up] == ac, 1, multiplier[data["component"][up]])
                        value = reference_anchor(values, prows, urows, weights, pm, um)
                        if np.isfinite(value):
                            ref_totals[name][replicate] += multiplier[ac] * value
                            ref_masses[name][replicate] += multiplier[ac]
        np.testing.assert_array_equal(checked_anchors, anchor_file["anchors"])
        for i, name in enumerate(columns):
            np.testing.assert_allclose(local_points[name], anchor_file[name], rtol=0, atol=1e-12)
            points.setdefault(name, []).extend(local_points[name])
            value = scores["scores"][:, i]
            delta = value[rows[:, 0]] + value[rows[:, 1]] - value[rows[:, 2]] - value[rows[:, 3]]
            credit = np.where(np.abs(delta) <= 1e-6, .5, (delta > 0).astype(float))
            qpoints.setdefault(name, []).extend(credit)
        print(f"reference-validated fold {fold}: all scores and {len(checked_anchors)} anchors", flush=True)
    for name in points:
        np.testing.assert_allclose(np.mean(points[name]), report["macro_concordance"][name], rtol=0, atol=1e-12)
        np.testing.assert_allclose(np.mean(qpoints[name]), report["quartets"]["all_points"][name], rtol=0, atol=1e-12)
    for name in ref_totals:
        np.testing.assert_allclose(ref_totals[name] / ref_masses[name], saved_boot[f"anchor_{name}"][:16], rtol=0, atol=1e-12)
    paired = saved_boot["anchor_pair_linear"] - saved_boot["anchor_endpoint_mlp64"]
    np.testing.assert_array_equal(paired, saved_boot["primary_delta"])
    np.testing.assert_allclose(np.nanpercentile(paired, [2.5, 97.5]), report["primary_delta_ci95"], rtol=0, atol=1e-12)
    for run in training["runs"]:
        if len(run["monitors"]) != 5 or [m["pass"] for m in run["monitors"]] != list(range(1, 6)):
            raise RuntimeError("incomplete fit")
        if any(m["U_comparisons"] != run["fit_U"] for m in run["monitors"]):
            raise RuntimeError("training U coverage mismatch")
        if any(not np.isfinite(m["training_loss"]) for m in run["monitors"]):
            raise RuntimeError("nonfinite training history")
    result = {"created_utc": now(), "pass": True, "validator_independence": "same_author_separate_forward_and_metric_formulas_not_external_review",
              "public_vector_values_checked": int(public.size), "public_pair_joins_checked": len(data["p_a"]) + len(data["u_a"]),
              "learned_score_values_checked": learned_values, "forward_fp64_max_absolute_difference": max_difference,
              "forward_absolute_tolerance": 1e-4, "all_anchor_points_and_quartet_points_checked": True,
              "full_direct_bootstrap_replicates_checked": 16, "bootstrap_draws_reproduced": len(draws),
              "result_artifact": artifact(root, root / RESULTS / "RESULTS.json"),
              "checks": ["frozen_hashes", "raw_embedding_join", "public_pair_join_and_weights", "component_folds", "fit_only_normalization",
                         "C3_rows_and_panel", "checkpoint_forward", "seed_ensemble", "quartet_eligibility_and_caps", "all_anchor_points",
                         "all_quartet_points", "direct_bootstrap_reference", "paired_intervals", "complete_fits"]}
    write_json(root / VALIDATION / "REFERENCE_VALIDATION.json", result)
    return result
