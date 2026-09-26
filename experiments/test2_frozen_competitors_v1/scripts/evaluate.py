"""Freeze complete test2 predictions, then apply the unchanged paired macro metric."""
from pathlib import Path
import csv
import time
import numpy as np
from study_io import CELLS, PRIMARY, arrays, codes, configure_cuda, now, read, record, save, sha, verify, write
from common import concordance
from macro_metrics import macro_bootstrap

ROOT = Path("/experiment")
OUT = Path("/output")
LABELS = {"selected_31k": "Selected 31k TUnA", "ipin_baseline": "Original iPIN", "ipin_optimized": "Optimized iPIN",
    "tuna_retrained_ensemble": "Frozen PU-TUnA (17k, epoch 4)", "tuna_original": "Original TUnA",
    "dscript_original": "Original D-SCRIPT", "dscript_retrained": "PU-D-SCRIPT",
    "plm_interact_original_650m_humanv11": "PLM-interact 650M humanV11",
    "rapppid_original_released_mult": "Original RAPPPID", "rapppid_recovery_mean_logit": "PU-RAPPPID recovery",
    "sprint_native_train_positive_graph": "Native SPRINT (17k graph)",
    "cross_attention_ensemble": "Cross-attention ensemble", "mean_pool_ensemble": "Mean-pooling ensemble"}


def csv_write(path, rows):
    with Path(path).open("x", newline="") as stream:
        writer = csv.DictWriter(stream, list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def validate_completion(path):
    meta = read(path / "COMPLETE.json")
    for item in meta["files"]:
        verify(path / item["path"], item)
    return meta


def collect():
    """Identity-only assembly with no test labels mounted/read by scoring workers."""
    catalogue = read(ROOT / "CATALOGUE.json")
    expected = read(ROOT / "INPUT_FREEZE.json")
    for item in expected["files"]:
        if "/private/candidates/" in item["path"]:
            verify(ROOT / "data/candidates" / Path(item["path"]).name, item)
    all_scores = {(cohort, cell): {} for cell in CELLS for cohort in ("legacy", "added")}
    for key in all_scores:
        cohort, cell = key
        all_scores[key].update(arrays(ROOT / f"predictions/ipin/{cohort}_{cell}.npz"))
    manifests = []
    for tag in ("tuna", "rapppid_original", "rapppid_recovery", "partner"):
        path = ROOT / "predictions" / tag
        completed = validate_completion(path)
        assert completed["bundle_sha256"] == catalogue[tag]["scorer_freeze_sha256"]
        manifests.append(record(path / "COMPLETE.json", ROOT))
        for cohort, cell in all_scores:
            source = path / f"{cohort}_{cell}.npz" if tag == "tuna" or cohort == "added" else ROOT / "legacy" / tag / f"{cell}.npz"
            all_scores[cohort, cell].update(arrays(source))
    for tag, workers in (("plm", 16), ("dscript_original", 4), ("dscript_retrained", 4)):
        completion = []
        for rank in range(workers):
            path = ROOT / "shards" / tag / f"rank-{rank:03d}"
            item = validate_completion(path)
            assert (item["rank"], item["workers"], item["method"]) == (rank, workers, tag)
            assert item["bundle_sha256"] == catalogue[tag]["scorer_freeze_sha256"]
            assert item["learned_parameters_unchanged"] and not item["test_truth_read"]
            completion.append((path, item))
            manifests.append(record(path / "COMPLETE.json", ROOT))
        for cell in CELLS:
            all_scores["legacy", cell].update(arrays(ROOT / "legacy" / tag / f"{cell}.npz"))
            total = len(arrays(ROOT / f"data/candidates/added_{cell}.npz")["a"])
            names = catalogue[tag]["scorers"]
            values = np.full((total, len(names)), np.nan, dtype=np.float64)
            seen = np.zeros(total, bool)
            for path, item in completion:
                part = next(p for p in item["files"] if p["cell"] == cell)
                left, right = part["left"], part["right"]
                assert 0 <= left < right <= total and not seen[left:right].any() and part["scorers"] == names
                scores = np.load(path / part["path"], allow_pickle=False)
                assert scores.shape == (right - left, len(names))
                values[left:right] = scores
                seen[left:right] = True
            assert seen.all() and np.isfinite(values).all()
            all_scores["added", cell].update({name: values[:, j] for j, name in enumerate(names)})
    sprint = ROOT / "sprint"
    completed = read(sprint / "COMPLETE.json")
    assert completed["input_sha256"] == sha(sprint / "INPUTS.json")
    assert completed["scores_sha256"] == sha(sprint / "scores.txt")
    assert completed["unchanged_training_graph_positive_pairs"] == 16799
    manifests.append(record(sprint / "COMPLETE.json", ROOT))
    with (sprint / "scores.txt").open() as stream:
        for part in read(sprint / "INPUTS.json")["parts"]:
            verify(ROOT / f"data/candidates/{part['cohort']}_{part['cell']}.npz", {"sha256": part["candidate_sha256"]})
            values = np.empty(part["rows"], np.float64)
            for i in range(len(values)):
                value, marker = next(stream).split()
                assert marker == "1"
                values[i] = float(value)
            assert np.isfinite(values).all() and (values >= 0).all()
            all_scores[part["cohort"], part["cell"]]["sprint_native_train_positive_graph"] = values
        assert stream.read() == ""
    files = []
    for (cohort, cell), scores in all_scores.items():
        candidates = arrays(ROOT / f"data/candidates/{cohort}_{cell}.npz")
        assert set(PRIMARY) <= set(scores)
        assert all(v.shape == candidates["a"].shape and np.isfinite(v).all() for v in scores.values())
        path = OUT / "predictions" / f"{cohort}_{cell}.npz"
        save(path, **scores)
        files.append({**record(path, OUT), "cohort": cohort, "cell": cell,
                      "candidate_sha256": sha(ROOT / f"data/candidates/{cohort}_{cell}.npz"), "rows": len(candidates["a"])})
    write(OUT / "PREDICTION_FREEZE.json", {"at_utc": now(), "complete_finite_candidate_coverage": True,
        "test_truth_read_during_scoring_or_assembly": False, "primary_models": list(PRIMARY), "files": files,
        "completion_manifests": manifests, "input_freeze_sha256": sha(ROOT / "INPUT_FREEZE.json"),
        "protocol_sha256": sha(ROOT / "PROTOCOL.json"), "new_training_or_selection": False})
    return all_scores


def summarize(points, draws, metadata):
    models, differences = {}, {}
    for j, name in enumerate(PRIMARY):
        valid = draws[j, np.isfinite(draws[j])]
        models[name] = {"PU_concordance": float(points[j]), "ci95": np.quantile(valid, [.025, .975]).tolist(), "finite_replicates": len(valid)}
        if j:
            delta = draws[0] - draws[j]
            valid = delta[np.isfinite(delta)]
            differences[name] = {"selected_31k_minus_reference": float(points[0] - points[j]),
                "paired_ci95": np.quantile(valid, [.025, .975]).tolist(), "finite_replicates": len(valid)}
    return {"models": models, "paired_differences": differences, "bootstrap": metadata}


def plot_c3(report):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), constrained_layout=True)
    for i, name in enumerate(PRIMARY):
        value = report["models"][name]
        color = "#00876c" if name == "selected_31k" else "#457b9d"
        axes[0].plot(value["ci95"], [i, i], color=color, linewidth=2)
        axes[0].plot(value["PU_concordance"], i, "o", color=color)
    axes[0].set(yticks=range(len(PRIMARY)), yticklabels=[LABELS[n] for n in PRIMARY],
                xlabel="C3 test2 macro P/U concordance", title="Frozen predictor scores")
    for i, name in enumerate(PRIMARY[1:]):
        value = report["paired_differences"][name]
        color = "#00876c" if value["paired_ci95"][0] > 0 else "#8d99ae"
        axes[1].plot(value["paired_ci95"], [i, i], color=color, linewidth=2)
        axes[1].plot(value["selected_31k_minus_reference"], i, "o", color=color)
    axes[1].axvline(0, color="black", linewidth=.8)
    axes[1].set(yticks=range(len(PRIMARY)-1), yticklabels=[LABELS[n] for n in PRIMARY[1:]],
                xlabel="Selected 31k minus reference", title="Paired differences")
    for ax in axes:
        ax.invert_yaxis()
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="y", labelsize=9)
    fig.suptitle("Test2 C3: equal-cohort macro; pointwise 95% component-bootstrap intervals")
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / ("C3_comparison." + suffix), dpi=180)
    plt.close(fig)


def main():
    started = time.monotonic()
    OUT.mkdir(exist_ok=True)
    if (OUT / "COMPLETE.json").exists():
        return
    if (OUT / "PREDICTION_FREEZE.json").exists():
        frozen = read(OUT / "PREDICTION_FREEZE.json")
        assert frozen["input_freeze_sha256"] == sha(ROOT / "INPUT_FREEZE.json")
        for item in frozen["files"]:
            verify(OUT / item["path"], item)
        predictions = {(x["cohort"], x["cell"]): arrays(OUT / x["path"]) for x in frozen["files"]}
    else:
        predictions = collect()
    # Labels are opened only after a complete immutable prediction freeze.
    inputs = read(ROOT / "INPUT_FREEZE.json")
    for item in inputs["files"]:
        if "/private/test/" in item["path"]:
            verify(Path("/truth") / item["path"].split("/private/test/")[1], item)
    meta = read("/studydata/sequences.json")
    assert sha("/studydata/sequences.json") == sha(ROOT / "data/sequences.json")
    components = np.array(meta["extended_component"])
    device = configure_cuda()
    results, cohorts, seed_points = {}, [], []
    for cell in CELLS:
        legacy = arrays(f"/truth/reconciled/{cell}.npz")
        added = arrays(f"/truth/added/{cell}.npz")
        for cohort, data in (("legacy", legacy), ("added", added)):
            candidate = arrays(ROOT / f"data/candidates/{cohort}_{cell}.npz")
            assert np.array_equal(candidate["a"], data["a"]) and np.array_equal(candidate["b"], data["b"])
            for name, score in predictions[cohort, cell].items():
                point = concordance(score, data["positive"], data["weight"])
                record_ = {"cell": cell, "cohort": "reconciled_legacy" if cohort == "legacy" else "added",
                           "model": name, "P": int(data["positive"].sum()), "U": int((~data["positive"]).sum()), "PU_concordance": point}
                (cohorts if name in PRIMARY else seed_points).append(record_)
        merged = {key: np.r_[legacy[key], added[key]] for key in ("a", "b", "positive", "weight")}
        score = np.concatenate([np.column_stack([predictions[group, cell][name] for name in PRIMARY]) for group in ("legacy", "added")])
        group = np.r_[np.zeros(len(legacy["a"]), int), np.ones(len(added["a"]), int)]
        views = [("test_2_macro", np.ones(len(group), bool))]
        if cell == "C1":
            old_dev = arrays("/studydata/legacy/development_02.npz")
            new_dev = arrays("/studydata/development/added/C1.npz")
            n = len(meta["sha256"])
            dev_keys = np.r_[codes(old_dev["a"], old_dev["b"], n), codes(new_dev["a"], new_dev["b"], n)]
            views.append(("test_2_macro_no_dev_overlap", ~np.isin(codes(merged["a"], merged["b"], n), dev_keys)))
        for view, keep in views:
            target = OUT / f"{cell}_{view}.json"
            if target.exists():
                report = read(target)
            else:
                points, draws, metadata = macro_bootstrap(score[keep], merged["positive"][keep], merged["weight"][keep], group[keep],
                    components[merged["a"][keep]].tolist(), components[merged["b"][keep]].tolist(), cell + "_" + view,
                    replicates=2000, device=device)
                report = summarize(points, draws, metadata)
                report["excluded_candidate_rows"] = int((~keep).sum())
                report["cohort_counts"] = [{"cohort": c, "P": int((merged["positive"] & (group == c) & keep).sum()),
                                           "U": int((~merged["positive"] & (group == c) & keep).sum())} for c in (0, 1)]
                save(OUT / f"bootstrap_{cell}_{view}.npz", points=points, draws=draws)
                write(target, report)
            results[cell + ":" + view] = report
            print({"evaluated": cell + ":" + view, "selected_31k": report["models"]["selected_31k"]}, flush=True)
    write(OUT / "RESULTS.json", {"at_utc": now(), "primary_cell": "C3", "primary_models": list(PRIMARY), "test": results,
        "metric": "Equal-cohort macro of design-weighted P/U concordance", "cohort_points": cohorts,
        "intervals": "Paired component bootstrap, 2000 common draws; pointwise 95%, not multiplicity-adjusted",
        "test2_is_fresh_independent": False, "new_training_or_model_selection": False,
        "prediction_freeze_sha256": sha(OUT / "PREDICTION_FREEZE.json")})
    rows, differences = [], []
    for panel, report in results.items():
        for model, value in report["models"].items():
            rows.append({"panel": panel, "model": model, "PU_concordance": value["PU_concordance"], "ci95_low": value["ci95"][0], "ci95_high": value["ci95"][1]})
        for model, value in report["paired_differences"].items():
            differences.append({"panel": panel, "reference_model": model, "selected_31k_minus_reference": value["selected_31k_minus_reference"],
                                "ci95_low": value["paired_ci95"][0], "ci95_high": value["paired_ci95"][1]})
    csv_write(OUT / "scores.csv", rows)
    csv_write(OUT / "paired_differences.csv", differences)
    csv_write(OUT / "cohort_scores.csv", cohorts)
    csv_write(OUT / "member_scores.csv", seed_points)
    lines = ["# Frozen competitors on test2", "", f"Completed {now()}. All 13 frozen predictors cover all 3,774,966 requested candidate rows.", "",
        "The primary score is the existing test2 macro: equal weight to weighted P-versus-U concordance in the reconciled legacy and added cohorts. C3 is primary. U is unlabeled, and test2 is a previously examined historical follow-up.", "",
        "| Predictor | C1 test2 | C2 test2 | C3 test2 |", "|---|---:|---:|---:|"]
    for name in PRIMARY:
        lines.append("| " + LABELS[name] + " | " + " | ".join(f"{results[c + ':test_2_macro']['models'][name]['PU_concordance']:.6f}" for c in CELLS) + " |")
    lines += ["", "## Paired C3 comparisons", "", "Positive differences favor selected 31k. Intervals are pointwise and are not corrected for multiple comparisons.", "",
              "| Reference | Selected 31k minus reference | Paired 95% interval |", "|---|---:|---:|"]
    for name, value in results["C3:test_2_macro"]["paired_differences"].items():
        low, high = value["paired_ci95"]
        lines.append(f"| {LABELS[name]} | {value['selected_31k_minus_reference']:+.6f} | [{low:+.6f}, {high:+.6f}] |")
    lines += ["", "## Reconciled legacy and added cohorts", "", "| Cell / cohort | P | U | Predictor | Weighted P/U concordance |", "|---|---:|---:|---|---:|"]
    for row in cohorts:
        lines.append(f"| {row['cell']} / {row['cohort']} | {row['P']} | {row['U']} | {LABELS[row['model']]} | {row['PU_concordance']:.6f} |")
    lines += ["", "## C1 sensitivity: remove development-overlapping candidate identities", "", "| Predictor | C1 macro without development overlap |", "|---|---:|"]
    sensitivity = results["C1:test_2_macro_no_dev_overlap"]
    for name in PRIMARY:
        lines.append(f"| {LABELS[name]} | {sensitivity['models'][name]['PU_concordance']:.6f} |")
    lines += ["", f"Removed {sensitivity['excluded_candidate_rows']:,} candidate rows only in this separate sensitivity view; the complete requested test2 panels remain unchanged.", "",
        "## Scope and provenance", "",
        "All predictors retain their existing weights, training graphs, selections, score definitions, and published length policies. Selected 31k is the fixed three-seed epoch-1 model. Competitor PU adaptations generally use the earlier 16,799-P corpus; this compares existing predictors and does not isolate architecture from training-data differences.", "",
        "Unchanged legacy predictions were verified against their original manifests and aligned by exact endpoint-pair identity. Added pairs were scored with the frozen predictors after sequence-only feature extension. D-SCRIPT and PLM-interact retain their native score scales; no score inversion or calibration was applied. RAPPPID retains its declared singleton inference policy and recovery-checkpoint caveat.", "",
        "Selected 31k and frozen PU-TUnA use the exact saved GP covariance, setting the unpersisted fitted flag before eval. This follows the completed scaling-study replay audit and may differ slightly from the earlier published reload-order results. SPRINT retains the same 16,799-P training graph but recomputes transductive HSP preprocessing on the expanded 17,583-sequence corpus, including all legacy scores.", "",
        "The selected cross-attention and mean-pooling ensembles are included. Unpromoted development-only recipes and candidate methods that only have planning notes were not promoted or newly trained here. Released predictors may have external interaction-training exposure. C1 retains the previously disclosed shared-development-identity issue, reported separately above.", "",
        "`scores.csv` contains macro scores and intervals, `paired_differences.csv` contains all paired contrasts, `cohort_scores.csv` contains the two constituent cohorts, and `member_scores.csv` reports individual seed point estimates. `PREDICTION_FREEZE.json` records complete finite prediction coverage before label-based evaluation. All source data and previous results remain read-only.", ""]
    (OUT / "RESULTS.md").write_text("\n".join(lines))
    plot_c3(results["C3:test_2_macro"])
    write(OUT / "COMPLETE.json", {"at_utc": now(), "elapsed_seconds": time.monotonic() - started,
          "results": record(OUT / "RESULTS.json", OUT), "predictors": len(PRIMARY), "candidate_rows": 3774966})


if __name__ == "__main__":
    main()
