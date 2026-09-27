"""Read back every published result and independently check consequential data."""
from pathlib import Path
import json
import shutil
import numpy as np
from control_io import MODELS, FIXED, COHORTS, arrays, codes, now, read, record, sha, verify, write
from ipin_openppi.partner_specificity.semantics import (
    weighted_concordance, build_queries, anchor_points, quartet_credit, quartet_bootstrap_totals,
)

STUDY = Path("/study")
REPO = Path("/repo")
OUT = Path("/output")


def check_summary(value, point, draws, point_key="point"):
    reported = value[point_key]
    matches = reported is None if not np.isfinite(point) else (
        reported is not None and np.isclose(reported, point, atol=1e-12, rtol=0))
    if not matches:
        raise RuntimeError("reported point differs from retained bootstrap point")
    good = np.isfinite(draws)
    if value["finite_replicates"] != int(good.sum()):
        raise RuntimeError("finite replicate count mismatch")
    ci = np.quantile(draws[good], [.025, .975]) if good.mean() >= .95 else None
    if ci is None:
        if value["ci95"] is not None:
            raise RuntimeError("interval reported despite sparse finite draws")
    elif not np.allclose(value["ci95"], ci, atol=1e-12, rtol=0):
        raise RuntimeError("reported interval differs from paired draws")


def main():
    inputs = read(STUDY/"INPUT_FREEZE.json")
    for item in inputs["parents"]:
        verify(REPO/item["path"], item)
    for item in inputs["files"]:
        verify(STUDY/item["path"], item)
    implementation = read(STUDY/"IMPLEMENTATION_FREEZE.json")
    for key, base in (("code", STUDY), ("libraries", REPO/"src"),
                      ("native", REPO/"benchmark/tuna/scripts"),
                      ("upstream", REPO/"benchmark/tuna/upstream/TUnA")):
        for item in implementation[key]:
            verify(base/item["path"], item)
    for manifest, base in (("features/FEATURES.json", "features"),
                           ("features/ALIGNMENT.json", "features"),
                           ("training/TRAINING.json", "training"),
                           ("predictions/PREDICTION_FREEZE.json", "predictions")):
        for item in read(STUDY/manifest)["files"]:
            verify(STUDY/base/item["path"], item)
    meta = read(STUDY/"data/sequences.json")
    n = len(meta["sha256"])
    p, u = arrays(STUDY/"data/train/positive.npz"), arrays(STUDY/"data/train/unlabeled.npz")
    training_keys = np.r_[codes(p["p_a"], p["p_b"], n), codes(u["u_a"], u["u_b"], n)]
    point_error, checked_rows = 0., 0
    for fold in ("development", "test"):
        for cell in ("C1", "C2", "C3"):
            for cohort in COHORTS:
                name = f"{fold}_{cohort}_{cell}"
                data_path = (REPO/"experiments/human_ppi_data_scaling_v1" /
                             ("private/test" if fold == "test" else "data/development") /
                             ("reconciled" if cohort == "legacy" else "added") / (cell+".npz"))
                data = arrays(data_path)
                candidate = arrays(STUDY/"data/candidates"/(name+".npz"))
                if not all(np.array_equal(data[k], candidate[k]) for k in ("a", "b")):
                    raise RuntimeError("final candidate-truth identity drift")
                if np.intersect1d(training_keys, codes(data["a"], data["b"], n)).size:
                    raise RuntimeError("train/evaluation candidate overlap")
                prediction = arrays(STUDY/"predictions"/(name+".npz"))
                result = read(STUDY/"results"/f"{cell}_{'test' if fold == 'test' else 'development'}_2_macro.json")
                for model in MODELS:
                    score = prediction[model]
                    point = weighted_concordance(score[data["positive"]], score[~data["positive"]],
                                                 data["weight"][~data["positive"]])
                    delta = abs(point-result["cohorts"][cohort]["models"][model]["PU_concordance"])
                    point_error = max(point_error, delta)
                    if delta > 1e-12:
                        raise RuntimeError("independent full-panel concordance mismatch")
                checked_rows += len(data["a"])
    primary = read(STUDY/"results/RESULTS.json")
    intervals_checked = 0
    for key, result in primary["panels"].items():
        verify(STUDY/"results"/result["bootstrap_file"]["path"], result["bootstrap_file"])
        boot = arrays(STUDY/"results"/result["bootstrap_file"]["path"])
        if list(boot["models"]) != list(MODELS):
            raise RuntimeError("retained bootstrap scorer order mismatch")
        if not np.array_equal(boot["points"], boot["cohort_points"].mean(1)) or not np.array_equal(
                boot["draws"], boot["cohort_draws"].mean(1)):
            raise RuntimeError("macro/cohort aggregation mismatch")
        for cohort, value, point, draws in [
                ("macro", result, boot["points"], boot["draws"]),
                *[(cohort, result["cohorts"][cohort], boot["cohort_points"][:, i], boot["cohort_draws"][:, i])
                  for i, cohort in enumerate(COHORTS)]]:
            for j, name in enumerate(MODELS):
                check_summary(value["models"][name], point[j], draws[j], "PU_concordance")
                intervals_checked += 1
                if j:
                    check_summary(value["paired_differences"][name], point[0]-point[j],
                                  draws[0]-draws[j], "selected_31k_minus_control")
                    intervals_checked += 1
        if result["partition"] == "test" and not result["reference_replay"]["passed"]:
            raise RuntimeError("reference replay did not pass")
    diagnostics = read(STUDY/"results/diagnostics/RESULTS.json")
    components, component = np.unique(meta["extended_component"], return_inverse=True)
    anchor_error, quartet_error = 0., 0.
    for fold, seed in (("development", 20260927), ("test", 20260928)):
        multipliers = np.random.default_rng(seed).poisson(1, (2000, len(components))).astype(np.int16)
        for cohort in COHORTS:
            name = f"{fold}_{cohort}_C3"
            data_path = (REPO/"experiments/human_ppi_data_scaling_v1" /
                         ("private/test" if fold == "test" else "data/development") /
                         ("reconciled" if cohort == "legacy" else "added") / "C3.npz")
            data = arrays(data_path)
            scores = arrays(STUDY/"predictions"/(name+".npz"))
            result = diagnostics["results"][fold][cohort]
            base = STUDY/"results/diagnostics"
            verify(base/result["bootstrap_file"]["path"], result["bootstrap_file"])
            verify(base/result["panel_file"]["path"], result["panel_file"])
            boot = arrays(base/result["bootstrap_file"]["path"])
            panel = arrays(base/result["panel_file"]["path"])
            rows, endpoints = panel["quartet_rows"], panel["quartet_endpoints"]
            if len(rows):
                if not (data["positive"][rows[:, :2]].all() and (~data["positive"][rows[:, 2:]]).all()):
                    raise RuntimeError("quartet P/U construction error")
                if not all(len(set(x)) == 4 for x in endpoints):
                    raise RuntimeError("quartet endpoints are not distinct")
            queries = build_queries(data["a"], data["b"], data["positive"])
            for j, model in enumerate(MODELS):
                point = anchor_points(scores[model], queries, data["weight"]).mean()
                error = abs(point-boot["anchor_points"][j])
                anchor_error = max(anchor_error, error)
                if error > 1e-12:
                    raise RuntimeError("independent anchor point mismatch")
                for metric in ("anchor", "quartet"):
                    check_summary(result[metric]["models"][model],
                                  boot[metric+"_points"][j], boot[metric+"_draws"][j])
                    intervals_checked += 1
                    if j:
                        check_summary(result[metric]["paired_differences"][model],
                                      boot[metric+"_points"][0]-boot[metric+"_points"][j],
                                      boot[metric+"_draws"][0]-boot[metric+"_draws"][j])
                        intervals_checked += 1
                if model in ("selected_31k", "endpoint_mlp64", "within_pair_3mer_cosine"):
                    credit, _ = quartet_credit(scores[model], rows)
                    numerator, denominator = quartet_bootstrap_totals(credit, endpoints, component, multipliers)
                    expected = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan),
                                         where=denominator > 0)
                    difference = np.abs(expected-boot["quartet_draws"][j])
                    error = float(np.max(difference[np.isfinite(difference)], initial=0))
                    quartet_error = max(quartet_error, error)
                    if not np.allclose(expected, boot["quartet_draws"][j], atol=1e-12, rtol=0, equal_nan=True):
                        raise RuntimeError("independent quartet bootstrap mismatch")
        for metric in ("anchor", "quartet"):
            boot = arrays(STUDY/"results/diagnostics"/f"bootstrap_{fold}_macro_{metric}.npz")
            result = diagnostics["results"][fold]["macro"][metric]
            for j, model in enumerate(MODELS):
                check_summary(result["models"][model], boot["points"][j], boot["draws"][j])
                intervals_checked += 1
                if j:
                    check_summary(result["paired_differences"][model],
                                  boot["points"][0]-boot["points"][j], boot["draws"][0]-boot["draws"][j])
                    intervals_checked += 1
    # Compact evidence is publishable; pair arrays, fitted weights and kernels stay local.
    for source, name in (("features/FEATURES.json", "FEATURES.json"),
                         ("features/ALIGNMENT.json", "ALIGNMENT.json"),
                         ("training/TRAINING.json", "TRAINING.json"),
                         ("predictions/PREDICTION_FREEZE.json", "PREDICTION_FREEZE.json")):
        with (OUT/name).open("xb") as f:
            f.write((STUDY/source).read_bytes())
    result = {
        "at_utc": now(), "passed": True, "parent_files_preserved": len(inputs["parents"]),
        "candidate_rows_checked": checked_rows, "predictors": len(MODELS),
        "primary_panels": len(primary["panels"]), "intervals_and_contrasts_checked": intervals_checked,
        "max_independent_full_panel_point_error": point_error,
        "max_independent_anchor_point_error": anchor_error,
        "max_independent_quartet_draw_error": quartet_error,
        "training_candidate_overlap": 0, "historical_inputs_changed": False,
        "prediction_freeze_sha256": sha(STUDY/"predictions/PREDICTION_FREEZE.json"),
        "primary_results": record(STUDY/"results/RESULTS.json", STUDY),
        "diagnostic_results": record(STUDY/"results/diagnostics/RESULTS.json", STUDY),
    }
    write(OUT/"VALIDATION.json", result)
    print(result, flush=True)


if __name__ == "__main__":
    main()
