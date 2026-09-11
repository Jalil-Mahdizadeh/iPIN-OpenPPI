"""Post-hoc development-only diagnosis; never opens test rows or changes models.

Run with the pinned model Apptainer image and the allowlisted mounts documented
in the report. Public test aggregates are read, never recomputed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import time

import numpy as np
import pyarrow.parquet as pq
from scipy import sparse
import torch

from ipin_openppi.development_evaluation.scoring import load_endpoint_universe, score_interolog_gpu
from ipin_openppi.model_optimization.common import BASELINE, read, record, sha, write_new
from ipin_openppi.model_optimization.metrics import bootstrap, point
from ipin_openppi.stage1.constants import ENDPOINTS_PATH, PARTITIONS_PATH

STUDY = "c3_control_shift_investigation_v1"
DEV = "artifacts/results/development_evaluation/development_embedding_identity_correction_v2"
SEARCH = "artifacts/validation/model_optimization_v1/SEARCH_FREEZE.json"
FREEZE = "artifacts/validation/protected_final_test_v1/SCORER_FREEZE.json"
TEST = "artifacts/results/protected_final_test_v1/FINAL_TEST_RESULTS.json"
NAMES = ("within_pair_3mer_cosine", "exact_training_interolog_3mer",
         "sequence_length_ratio", "sequence_length_sum", BASELINE, "deterministic_hash")
ANCHORS = {
    SEARCH: "c321841b6d79f4ca4256f14f9f7463a5bf3b5dc0085cfa554a1dc3ba4c906f67",
    FREEZE: "5f25e856ce74e9f93497c17c19eb45ab1cb49fd74a30ceca5b4f874727e0125f",
    TEST: "6cc8c3ba61039501b3e1b09dfcee442de8f4dfcd0c717a466b15f9e77ef3a02e",
    f"{DEV}/PRIMARY_METRICS.json": "afe7b4af1315d350dfc3d5288eaa0f6d49771b6ebd6baa96f75f1278d698bff8",
}


def module_from(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checked(path: Path, item: dict, inputs: list) -> Path:
    if path.is_symlink() or path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
        raise RuntimeError(f"Input drift: {item['path']}")
    inputs.append(item)
    return path


def load_npz(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def assert_development(data: dict, partitions: np.ndarray) -> None:
    for key in ("a", "b"):
        values = data[key]
        if values.ndim != 1 or values.dtype.kind not in "iu" or np.any(values < 0) or np.any(values >= len(partitions)):
            raise RuntimeError("Invalid development endpoint index")
        if np.any(partitions[values] != "development"):
            raise RuntimeError("Non-development endpoint: stop before any scoring")
    if data["a"].shape != data["b"].shape or np.any(data["a"] == data["b"]):
        raise RuntimeError("Invalid development pairs")


def favorable_mass(scores: np.ndarray, positive: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """Each positive's tie-aware concordance against the SAME full HT U pool."""
    u, p = scores[~positive], scores[positive]
    order = np.argsort(u, kind="mergesort")
    cumulative = np.concatenate(([0.0], np.cumsum(weight[~positive][order])))
    left = np.searchsorted(u[order], p, side="left")
    right = np.searchsorted(u[order], p, side="right")
    return (cumulative[left] + cumulative[right]) / (2 * cumulative[-1])


def subset(data: dict, keep: np.ndarray) -> dict:
    # Retain the ORIGINAL component universe, so draws pair across sensitivities.
    return {key: (value if key == "components" else value[keep]) for key, value in data.items()}


def group_summary(mask: np.ndarray, data: dict, favorable: np.ndarray) -> dict:
    p, w = data["positive"], data["weight"]
    n = int(np.sum(mask & p))
    return {"positive_rows": n, "positive_fraction": float(n / p.sum()),
            "unlabeled_rows": int(np.sum(mask & ~p)),
            "HT_U_fraction": float(w[mask & ~p].sum() / w[~p].sum()),
            "positive_group_vs_full_U": {
                name: float(favorable[mask[p], j].mean()) if n else None
                for j, name in enumerate(NAMES)}}


def weighted_quantiles(values: np.ndarray, weights: np.ndarray) -> list:
    order = np.argsort(values, kind="mergesort")
    cumulative = np.cumsum(weights[order])
    indices = np.searchsorted(cumulative, np.array([.1, .5, .9]) * cumulative[-1])
    return values[order[indices]].astype(float).tolist()


def length_bins(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aa, bb = np.searchsorted([200, 500, 1000], a, side="right"), np.searchsorted([200, 500, 1000], b, side="right")
    return 4 * np.minimum(aa, bb) + np.maximum(aa, bb)


def matched_bins(scores: np.ndarray, data: dict, bins: np.ndarray) -> dict:
    result, numerators, covered = {}, np.zeros(len(NAMES)), 0
    for value in sorted(np.unique(bins)):
        mask = bins == value
        n_p, n_u = int(np.sum(mask & data["positive"])), int(np.sum(mask & ~data["positive"]))
        if not n_p or not n_u:
            result[str(value)] = {"positive_rows": n_p, "unlabeled_rows": n_u, "concordance": None}
            continue
        local = subset(data, mask)
        auc = np.array([point(scores[mask, j], local) for j in range(len(NAMES))])
        numerators += n_p * auc
        covered += n_p
        result[str(value)] = {"positive_rows": n_p, "unlabeled_rows": n_u,
                              "concordance": dict(zip(NAMES, auc.tolist()))}
    return {"bins": result, "positive_coverage": float(covered / data["positive"].sum()),
            "positive_weighted_within_bin_concordance": dict(zip(NAMES, (numerators / covered).tolist())) if covered else None}


def aggregate_comparison(project: Path) -> dict:
    development, test = read(project / DEV / "PRIMARY_METRICS.json"), read(project / TEST)
    source = read(project / DEV / "SOURCE_EXCLUSIVE_METRICS.json")
    result = {}
    for exposure in ("C1", "C2", "C3"):
        result[exposure] = {}
        for name in NAMES:
            d = development["cells"][f"{exposure}_development"]
            t = test["cells"][f"{exposure}_test"]["metrics"][name]
            result[exposure][name] = {
                "development": d["metrics"][name]["ht_positive_vs_U_concordance"],
                "development_ci95": d["bootstrap_percentile_95_for_controls_and_ensembles"][name],
                "test": t["ht_P_vs_U_concordance"], "test_ci95": t["percentile_95"]}
    for label in ("HI-II-14", "HuRI"):
        d = source["cells"][f"source_exclusive:{label}:C3_development"]
        t = test["cells"][f"source_exclusive:{label}:C3_test"]["metrics"]
        result[f"{label}_exclusive_C3"] = {
            name: {"development": d[name]["ht_positive_vs_U_concordance"],
                   "test": t[name]["ht_P_vs_U_concordance"]} for name in NAMES}
    return result


def investigate(args) -> dict:
    started = time.monotonic()
    if not torch.cuda.is_available():
        raise RuntimeError("Actual CUDA GPU required; no CPU fallback")
    if (args.project / ".private").exists():
        raise RuntimeError("Use allowlisted mounts: repository .private must not be visible")
    inputs = []
    for relative, expected in ANCHORS.items():
        item = record(args.project / relative, args.project)
        if item["sha256"] != expected:
            raise RuntimeError(f"Anchor drift: {relative}")
        inputs.append(item)
    search, freeze = read(args.project / SEARCH), read(args.project / FREEZE)
    for relative in (ENDPOINTS_PATH, PARTITIONS_PATH):
        item = next(x for x in search["input_records"] if x["path"] == str(relative))
        checked(args.project / relative, item, inputs)
    source_path = args.project / DEV / "SOURCE_EXCLUSIVE_METRICS.json"
    inputs.append(record(source_path, args.project))
    universe = load_endpoint_universe(args.project / ENDPOINTS_PATH, args.project / PARTITIONS_PATH)
    partitions = np.array(universe.partitions)
    for item in freeze["files"]:
        if item["path"].startswith("features/"):
            checked(args.frozen / item["path"], item, inputs)
    if read(args.frozen / "features/endpoints.json") != list(universe.sequence_sha256):
        raise RuntimeError("Frozen feature endpoint order drift")
    data_cells = {}
    for number in (0, 3, 4):
        name = f"development_{number:02d}.npz"
        item = next(x for x in search["files"] if x["path"] == f"data/{name}")
        data_cells[number] = load_npz(checked(args.development / name, item, inputs))
        assert_development(data_cells[number], partitions)
    data = data_cells[0]
    for filename in ("SCORERS.json", "scores.f64.npy", "rows.parquet", "CELL_SCORE_MANIFEST.json"):
        suffix = f"/C3_development/{filename}"
        item = next(x for x in search["input_records"] if x["path"].endswith(suffix))
        checked(args.scores / filename, item, inputs)
    columns = {x["scorer_id"]: x["column"] for x in read(args.scores / "SCORERS.json")["scorers"]}
    matrix = np.load(args.scores / "scores.f64.npy", mmap_mode="r", allow_pickle=False)
    scores = np.asarray(matrix[:, [columns[name] for name in NAMES]])
    if not np.array_equal(scores[:, 4], data["baseline"].mean(1)):
        raise RuntimeError("Development NPZ/cache baseline alignment drift")
    a, b, p = data["a"], data["b"], data["positive"]
    if p.sum() != 2265 or (~p).sum() != 1_000_000:
        raise RuntimeError("Development C3 row census drift")
    components = np.array(universe.components)
    if not np.array_equal(data["components"][data["component_a"]], components[a]) or not np.array_equal(data["components"][data["component_b"]], components[b]):
        raise RuntimeError("Component index alignment drift")
    published = aggregate_comparison(args.project)
    favorable = np.column_stack([favorable_mass(scores[:, j], p, data["weight"]) for j in range(len(NAMES))])
    observed = favorable.mean(0)
    error = max(abs(observed[j] - published["C3"][name]["development"]) for j, name in enumerate(NAMES))
    if error > 1e-9:
        raise RuntimeError("Published concordance not reproduced")
    print("Inputs and six published development metrics verified", flush=True)

    lengths = universe.lengths
    kmer = sparse.load_npz(args.frozen / "features/kmer.npz")
    kscore = np.empty(a.size)
    for start in range(0, a.size, 8192):
        aa, bb = a[start:start + 8192], b[start:start + 8192]
        kscore[start:start + 8192] = np.asarray(kmer[aa].multiply(kmer[bb]).sum(axis=1)).ravel()
    sim = np.load(args.frozen / "features/similarities.npy", allow_pickle=False)
    neighbor = np.load(args.frozen / "features/neighbor.npy", allow_pickle=False)
    gpu = score_interolog_gpu(sim, neighbor, a, b)
    parity = {"full_development_rows": int(a.size), "published_concordance_max_abs": error,
              "full_row_score_max_abs": {
                  NAMES[0]: float(np.max(np.abs(kscore - scores[:, 0]))),
                  NAMES[1]: float(np.max(np.abs(gpu - scores[:, 1]))),
                  NAMES[2]: float(np.max(np.abs(-np.abs(np.log1p(lengths[a]) - np.log1p(lengths[b])) - scores[:, 2]))),
                  NAMES[3]: float(np.max(np.abs(np.log1p(lengths[a]) + np.log1p(lengths[b]) - scores[:, 3])))}}
    del sim, neighbor, gpu, kmer, kscore
    core = module_from(args.project / "scripts/benchmark/protected_final_core_v1.py", "frozen_core")
    sample = np.concatenate((np.flatnonzero(p), np.flatnonzero(~p)[np.linspace(0, (~p).sum() - 1, 8192, dtype=int)]))
    rows = pq.read_table(args.scores / "rows.parquet").take(sample)
    ids = np.array(universe.sequence_sha256)
    if rows["endpoint_a_sha256"].to_pylist() != ids[a[sample]].tolist() or rows["endpoint_b_sha256"].to_pylist() != ids[b[sample]].tolist():
        raise RuntimeError("Development pair identity/order drift")
    cpu_scorer = core.Scorer(args.frozen)
    replay = cpu_scorer.score(rows)
    parity["protected_CPU_scorer_development_sample_rows"] = int(sample.size)
    parity["protected_CPU_scorer_max_abs"] = {
        name: float(np.max(np.abs(replay[:, core.SCORERS.index(name)] - scores[sample, j])))
        for j, name in enumerate(NAMES) if name != BASELINE}
    if max(*parity["full_row_score_max_abs"].values(), *parity["protected_CPU_scorer_max_abs"].values()) > 1e-12:
        raise RuntimeError("Control score parity failed; stop before interpreting shift")
    del replay, cpu_scorer, rows
    print("Full development control parity and protected CPU scorer replay passed", flush=True)

    partition_summary = {}
    for partition in ("train", "development", "test"):
        mask = partitions == partition
        counts = Counter(components[mask])
        partition_summary[partition] = {
            "endpoints": int(mask.sum()), "components": len(counts),
            "singleton_components": sum(x == 1 for x in counts.values()),
            "largest_component": max(counts.values()),
            "endpoint_length_p10_p50_p90": np.quantile(lengths[mask], [.1, .5, .9]).tolist()}
    counts = Counter(components[partitions == "development"])
    ranked = sorted(counts, key=lambda key: (-counts[key], key))[:10]
    top = []
    for rank, component in enumerate(ranked, 1):
        mask = (components[a] == component) | (components[b] == component)
        top.append({"endpoint_size_rank": rank, "endpoints": counts[component], **group_summary(mask, data, favorable)})
    giant_a, giant_b = components[a] == ranked[0], components[b] == ranked[0]
    touch = giant_a | giant_b
    groups = {"both_in_largest": giant_a & giant_b, "one_in_largest": giant_a ^ giant_b, "neither_in_largest": ~touch}
    summaries = {key: group_summary(mask, data, favorable) for key, mask in groups.items()}
    reconstruction = np.array([sum(value["positive_fraction"] * (value["positive_group_vs_full_U"][name] or 0) for value in summaries.values()) for name in NAMES])
    if not np.allclose(reconstruction, observed, rtol=0, atol=1e-12):
        raise RuntimeError("Positive-group decomposition failed")
    keep = ~touch
    reduced = subset(data, keep)
    reduced_scores = scores[keep]
    reduced_points = {name: point(reduced_scores[:, j], reduced) for j, name in enumerate(NAMES)}
    source_summary = {}
    pair_key = np.minimum(a, b) * len(lengths) + np.maximum(a, b)
    source_masks = []
    for index, label in ((3, "HI-II-14_exclusive"), (4, "HuRI_exclusive")):
        cell = data_cells[index]
        aa, bb = cell["a"][cell["positive"]], cell["b"][cell["positive"]]
        keys = np.minimum(aa, bb) * len(lengths) + np.maximum(aa, bb)
        mask = p & np.isin(pair_key, keys)
        if mask.sum() != keys.size:
            raise RuntimeError("Source-exclusive positive membership mismatch")
        source_masks.append(mask)
        source_summary[label] = {"positive_rows": int(mask.sum()), "touching_largest": int(np.sum(mask & touch))}
    both = p & ~source_masks[0] & ~source_masks[1]
    source_summary["both_sources"] = {"positive_rows": int(both.sum()), "touching_largest": int(np.sum(both & touch))}
    same = components[a] == components[b]
    covariates = {}
    for name, value in (("min_endpoint_length", np.minimum(lengths[a], lengths[b])),
                        ("max_endpoint_length", np.maximum(lengths[a], lengths[b]))):
        covariates[name] = {label: weighted_quantiles(value[mask], data["weight"][mask])
                            for label, mask in (("P", p), ("HT_U", ~p), ("P_without_largest", p & keep), ("HT_U_without_largest", ~p & keep))}
    bins = length_bins(lengths[a], lengths[b])
    result = {"study_id": STUDY, "status": "post_hoc_development_only_diagnostic",
              "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "access": {"test_aggregate_results_read": True, "test_rows_truth_predictions_keys_opened": False,
                         "new_training_or_test_evaluation": False, "repository_private_tree_mounted": False},
              "runtime": {"torch": torch.__version__, "CUDA": torch.version.cuda,
                          "GPU": torch.cuda.get_device_name(), "container_sha256": freeze["model_container_sha256"]},
              "input_records": inputs, "published_comparison": published, "parity": parity,
              "label_blind_endpoint_partition_summary": partition_summary,
              "development": {"full_concordance": dict(zip(NAMES, observed.tolist())),
                              "ten_largest_components": top, "largest_component_groups": summaries,
                              "largest_component_source_membership": source_summary,
                              "same_component": group_summary(same, data, favorable),
                              "length_p10_p50_p90": covariates,
                              "within_length_bin_full": matched_bins(scores, data, bins),
                              "within_length_bin_without_largest": matched_bins(reduced_scores, reduced, bins[keep]),
                              "both_P_and_U_without_largest": {"positive_rows": int(reduced["positive"].sum()),
                                  "unlabeled_rows": int((~reduced["positive"]).sum()), "concordance": reduced_points}}}
    print("Component decomposition: " + str(summaries), flush=True)
    print("Without largest component: " + str(reduced_points), flush=True)
    # Bootstrap the five interpretable controls/model; the hash remains a point sentinel.
    distributions = []
    for label, values, cell_data in (("full", scores, data), ("without_largest", reduced_scores, reduced)):
        print(f"Starting 2000-replicate CUDA component bootstrap: {label}", flush=True)
        draws = bootstrap(values[:, :5], cell_data, cell="C3_development", replicates=2000)
        if not np.isfinite(draws).all():
            raise RuntimeError("Nonfinite component-bootstrap replicate")
        distributions.append(draws)
    result["bootstrap"] = {"replicates": 2000, "method": "existing_C3_development_component_pigeonhole_common_draws",
                           "not_a_dev_test_difference_interval": True,
                           "scores": {name: {"full_ci95": np.quantile(distributions[0][:, j], [.025, .975]).tolist(),
                                             "without_largest_ci95": np.quantile(distributions[1][:, j], [.025, .975]).tolist(),
                                             "without_minus_full_paired_sensitivity_ci95": np.quantile(distributions[1][:, j] - distributions[0][:, j], [.025, .975]).tolist()}
                                      for j, name in enumerate(NAMES[:5])}}
    result["runtime"]["elapsed_seconds"] = time.monotonic() - started
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("/project"))
    parser.add_argument("--development", type=Path, default=Path("/development"))
    parser.add_argument("--scores", type=Path, default=Path("/scores"))
    parser.add_argument("--frozen", type=Path, default=Path("/frozen"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite diagnostic evidence")
    result = investigate(args)
    result["analysis_code_sha256"] = sha(Path(__file__))
    result["scope_document_sha256"] = sha(args.project / "docs/protocols/C3_CONTROL_SHIFT_INVESTIGATION_v1.md")
    write_new(args.output, result)
    print(f"Completed: {args.output}", flush=True)


if __name__ == "__main__":
    main()
