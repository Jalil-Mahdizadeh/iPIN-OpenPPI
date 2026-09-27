"""Evaluate immutable candidate predictions with the frozen test2 estimand."""
import csv
from pathlib import Path
import numpy as np
from control_io import (
    ROOT, OUT, CELLS, COHORTS, FIXED, ADDITIONAL, MODELS, arrays, codes, cuda,
    now, phase_guard, read, record, save, sha, summary, verify, write,
)
from control_metrics import cohort_bootstrap


def load_panel(fold, cell, cohort):
    name = f"{fold}_{cohort}_{cell}"
    path = Path("/truth" if fold == "test" else "/devtruth") / (
        "reconciled" if cohort == "legacy" else "added") / (cell+".npz")
    data = arrays(path)
    candidate = arrays(Path("/candidates")/(name+".npz"))
    if set(data) != {"a", "b", "positive", "weight"}:
        raise RuntimeError("unexpected evaluation schema")
    if not np.array_equal(data["a"], candidate["a"]) or not np.array_equal(data["b"], candidate["b"]):
        raise RuntimeError("candidate/truth row identity mismatch")
    if data["positive"].dtype != bool or not np.isfinite(data["weight"]).all() or np.any(data["weight"] <= 0):
        raise RuntimeError("invalid evaluation states or design weights")
    if not np.all(data["weight"][data["positive"]] == 1):
        raise RuntimeError("primary metric assumes census unit-weight positives")
    scores = arrays(Path("/predictions")/(name+".npz"))
    if set(scores) != set(MODELS) or any(x.shape != data["a"].shape or not np.isfinite(x).all() for x in scores.values()):
        raise RuntimeError("incomplete prediction coverage")
    return data, np.column_stack([scores[name] for name in MODELS])


def verify_predictions_and_truth():
    phase_guard()
    frozen = read("/predictions/PREDICTION_FREEZE.json")
    if not frozen["complete_finite_identity_aligned_coverage"] or frozen["evaluation_truth_mounted"]:
        raise RuntimeError("invalid prediction freeze")
    if frozen["implementation_freeze_sha256"] != sha(ROOT/"IMPLEMENTATION_FREEZE.json"):
        raise RuntimeError("implementation changed after scoring")
    if frozen["protocol_sha256"] != sha(ROOT/"PROTOCOL.json") or frozen["models"] != list(MODELS):
        raise RuntimeError("protocol or scorer catalogue changed")
    for item in frozen["files"]:
        verify(Path("/predictions")/item["path"], item)
        candidate = Path("/candidates")/item["path"]
        if sha(candidate) != item["candidate_sha256"]:
            raise RuntimeError("candidate changed after prediction freeze")
    for item in read(ROOT/"INPUT_FREEZE.json")["parents"]:
        path = item["path"]
        if "/private/test/" in path:
            verify(Path("/truth")/path.split("/private/test/")[1], item)
        elif "/data/development/" in path:
            verify(Path("/devtruth")/path.split("/data/development/")[1], item)
    return frozen


def estimates(points, draws):
    models = {}
    for j, name in enumerate(MODELS):
        values = summary(points[j], draws[j])
        models[name] = {"PU_concordance": values.pop("point"), **values}
    differences = {}
    for j, name in enumerate(MODELS[1:], 1):
        values = summary(points[0]-points[j], draws[0]-draws[j])
        differences[name] = {"selected_31k_minus_control": values.pop("point"), **values,
                             "family": "original_fixed" if name in FIXED else "additional_diagnostic"}
    return {"models": models, "paired_differences": differences}


def main():
    frozen = verify_predictions_and_truth()
    device = cuda()
    if not (OUT/"EVALUATION_RESERVATION.json").exists():
        write(OUT/"EVALUATION_RESERVATION.json", {
            "at_utc": now(), "prediction_freeze_sha256": sha("/predictions/PREDICTION_FREEZE.json"),
            "truth_first_deserialized_after_prediction_freeze": True,
        })
    meta = read("/sequences/sequences.json")
    components = np.asarray(meta["extended_component"])
    reference = read("/reference/RESULTS.json")
    reference_index = reference["primary_models"].index("selected_31k")
    panels = {}
    for fold in ("development", "test"):
        for cell in CELLS:
            parts = [load_panel(fold, cell, c) for c in COHORTS]
            data = {key: np.concatenate([part[0][key] for part in parts]) for key in parts[0][0]}
            scores = np.concatenate([part[1] for part in parts])
            cohort = np.repeat(np.arange(2), [len(part[0]["a"]) for part in parts])
            view = f"{'test' if fold == 'test' else 'development'}_2_macro"
            views = [(view, np.ones(len(cohort), bool))]
            if fold == "test" and cell == "C1":
                d = [arrays(f"/candidates/development_{c}_C1.npz") for c in COHORTS]
                keys = np.concatenate([codes(x["a"], x["b"], len(components)) for x in d])
                keep = ~np.isin(codes(data["a"], data["b"], len(components)), keys)
                views.append(("test_2_macro_no_dev_overlap", keep))
            for view, keep in views:
                key, target = cell+":"+view, OUT/f"{cell}_{view}.json"
                if target.exists():
                    result = read(target)
                    verify(OUT/result["bootstrap_file"]["path"], result["bootstrap_file"])
                    if result["prediction_freeze_sha256"] != sha("/predictions/PREDICTION_FREEZE.json"):
                        raise RuntimeError("existing result belongs to another prediction freeze")
                else:
                    print({"evaluating": key, "predictors": len(MODELS), "rows": int(keep.sum())}, flush=True)
                    cp, cd, bmeta = cohort_bootstrap(
                        scores[keep], data["positive"][keep], data["weight"][keep], cohort[keep],
                        components[data["a"][keep]].tolist(), components[data["b"][keep]].tolist(),
                        cell+"_"+view, device=device)
                    points, draws = cp.mean(1), cd.mean(1)
                    replay = None
                    if fold == "test":
                        old = arrays(Path("/reference")/f"bootstrap_{cell}_{view}.npz")
                        old_report = reference["test"][key]
                        error = float(np.max(np.abs(draws[0]-old["draws"][reference_index])))
                        if (not np.isfinite(error) or error > 1e-12 or
                                abs(points[0]-old["points"][reference_index]) > 1e-12 or
                                bmeta != old_report["bootstrap"] or
                                int((~keep).sum()) != old_report["excluded_candidate_rows"]):
                            raise RuntimeError("current reference paired-draw replay failed")
                        replay = {"passed": True, "max_reference_draw_error": error,
                                  "point_error": float(abs(points[0]-old["points"][reference_index]))}
                    bootstrap = OUT/f"bootstrap_{cell}_{view}.npz"
                    save(bootstrap, points=points, draws=draws, cohort_points=cp, cohort_draws=cd,
                         models=np.asarray(MODELS))
                    result = {
                        "partition": fold, "cell": cell, "view": view, **estimates(points, draws),
                        "cohorts": {name: estimates(cp[:, i], cd[:, i]) for i, name in enumerate(COHORTS)},
                        "cohort_counts": {name: {
                            "P": int((keep & (cohort == i) & data["positive"]).sum()),
                            "U": int((keep & (cohort == i) & ~data["positive"]).sum())}
                            for i, name in enumerate(COHORTS)},
                        "excluded_candidate_rows": int((~keep).sum()),
                        "bootstrap": bmeta, "bootstrap_file": record(bootstrap, OUT),
                        "reference_replay": replay,
                        "prediction_freeze_sha256": sha("/predictions/PREDICTION_FREEZE.json"),
                    }
                    write(target, result)
                panels[key] = result
                print({"completed": key, "selected_31k": result["models"]["selected_31k"]}, flush=True)
    write(OUT/"RESULTS.json", {
        "at_utc": now(), "models": list(MODELS), "original_fixed_controls": list(FIXED),
        "additional_diagnostic_controls": list(ADDITIONAL), "panels": panels,
        "primary_cell": "C3", "metric": "Equal-cohort macro design-weighted P/U concordance",
        "intervals": "2000 paired extended-component draws; pointwise 95%, not multiplicity-adjusted",
        "protocol_sha256": sha(ROOT/"PROTOCOL.json"),
        "prediction_freeze_sha256": sha("/predictions/PREDICTION_FREEZE.json"),
        "test2_is_fresh_independent": False, "U_is_confirmed_negative": False,
    })
    write_csvs(panels)
    render(panels)
    print({"primary_evaluation_complete": True, "panels": len(panels)}, flush=True)


def write_csvs(panels):
    for filename, contrasts in (("scores.csv", False), ("paired_differences.csv", True)):
        with (OUT/filename).open("x", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["panel", "cohort", "model", "estimate", "ci95_low", "ci95_high", "finite_replicates"])
            for key, report in panels.items():
                for cohort, values in [("macro", report), *report["cohorts"].items()]:
                    field = "paired_differences" if contrasts else "models"
                    point_key = "selected_31k_minus_control" if contrasts else "PU_concordance"
                    for name, value in values[field].items():
                        writer.writerow([key, cohort, name, value[point_key],
                                         *(value["ci95"] or [None, None]), value["finite_replicates"]])


def render(panels):
    lines = [
        "# Expanded control evaluation", "",
        "The frozen 31,188-P TUnA ensemble is compared with all eleven original fixed controls,",
        "two train2-fitted additive endpoint controls, and three additional transfer kernels.",
        "C3 is primary. These are follow-up results on previously examined development/test data.",
        "U is unlabeled, and all intervals are pointwise 95% component-bootstrap intervals.", "",
        "## Test2 macro scores", "", "| Predictor | C1 | C2 | C3 |", "|---|---:|---:|---:|",
    ]
    for name in MODELS:
        lines.append("| "+name+" | "+" | ".join(
            f"{panels[c+':test_2_macro']['models'][name]['PU_concordance']:.6f}" for c in CELLS)+" |")
    lines += ["", "## Primary C3 paired comparisons", "",
              "| Control | Selected 31k minus control | Paired 95% interval |", "|---|---:|---|"]
    for name, value in panels["C3:test_2_macro"]["paired_differences"].items():
        ci = value["ci95"]
        interval = f"[{ci[0]:+.6f}, {ci[1]:+.6f}]" if ci else "Insufficient finite draws"
        lines.append(f"| {name} | {value['selected_31k_minus_control']:+.6f} | {interval} |")
    lines += ["", "## Development2 macro scores", "", "| Predictor | C1 | C2 | C3 |", "|---|---:|---:|---:|"]
    for name in MODELS:
        lines.append("| "+name+" | "+" | ".join(
            f"{panels[c+':development_2_macro']['models'][name]['PU_concordance']:.6f}" for c in CELLS)+" |")
    lines += [
        "", "The CSVs and RESULTS.json contain every interval, paired difference, both constituent",
        "cohorts, and the C1 sensitivity excluding development-overlapping identities.",
        "Reference test2 points and all 2,000 paired draws are replayed against the completed",
        "frozen-competitor study. Development uses the same exact saved GP covariance policy.",
        "", "The network and transfer controls use only the 31,188 train2 positive edges.",
        "Pooled controls use the manuscript's raw windowed embeddings, not TUnA endpoint features.",
        "Endpoint controls retain the historical architectures and fixed five-pass fitting recipe.",
        "These comparisons do not capacity-match TUnA or establish physical binding specificity.",
        "Separate C3 within-anchor and selected-quartet results are in diagnostics/.", "",
    ]
    (OUT/"RESULTS.md").write_text("\n".join(lines))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels = [name.replace("_", " ") for name in MODELS]
    fig, axes = plt.subplots(1, 3, figsize=(14, 8), sharey=True, constrained_layout=True)
    for ax, cell in zip(axes, CELLS, strict=True):
        result = panels[cell+":test_2_macro"]["models"]
        for j, name in enumerate(MODELS):
            v = result[name]; ci = v["ci95"]; p = v["PU_concordance"]
            color = "#00876c" if name == "selected_31k" else "#596b7a"
            if ci is not None:
                ax.hlines(j, *ci, color=color)
            ax.plot(p, j, "o", color=color)
        ax.axvline(.5, color="#aaaaaa", linewidth=.8, linestyle="--")
        ax.set(title=cell, xlabel="Test2 macro P/U concordance")
    axes[0].set_yticks(range(len(MODELS)), labels)
    axes[0].invert_yaxis()
    fig.suptitle("Frozen selected 31k model and train2 controls\nPointwise 95% paired component-bootstrap intervals")
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(OUT/f"control_scores.{suffix}", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
