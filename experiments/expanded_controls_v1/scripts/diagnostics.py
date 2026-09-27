"""C3 partner ranking and endpoint-balanced swaps of the frozen current scores."""
import csv
import hashlib
from pathlib import Path
import numpy as np
from control_io import ROOT, OUT, COHORTS, MODELS, cuda, now, protocol, read, record, save, sha, summary, write
from diagnostic_math import anchor_bootstrap, quartet_estimates
from evaluate import load_panel, verify_predictions_and_truth
from ipin_openppi.partner_specificity.semantics import select_quartets, quartet_credit


def model_results(points, draws):
    return {
        "models": {name: summary(points[j], draws[j]) for j, name in enumerate(MODELS)},
        "paired_differences": {name: summary(points[0]-points[j], draws[0]-draws[j])
                               for j, name in enumerate(MODELS[1:], 1)},
    }


def main():
    verify_predictions_and_truth()
    device = cuda()
    cfg = protocol()["partner_diagnostics"]
    meta = read("/sequences/sequences.json")
    components, component = np.unique(meta["extended_component"], return_inverse=True)
    results = {}
    for fold, seed in (("development", 20260927), ("test", 20260928)):
        rng = np.random.default_rng(seed)
        multipliers = rng.poisson(1, (2000, len(components))).astype(np.int16)
        multiplier_hash = hashlib.sha256(multipliers.astype("<i2").tobytes()).hexdigest()
        parts = {"anchor": [], "quartet": []}
        fold_results = {}
        for cohort in COHORTS:
            key = fold+"_"+cohort+"_C3"
            target = OUT/(key+".json")
            if target.exists():
                raise RuntimeError("diagnostic already exists; refusing adaptive replacement")
            data, scores = load_panel(fold, "C3", cohort)
            print({"diagnostic": key, "stage": "within_anchor"}, flush=True)
            ap, ad, support = anchor_bootstrap(scores, data, component, multipliers, device=device)
            anchor_ok = support["anchors"] >= cfg["minimum_anchors"] and support["anchor_components"] >= cfg["minimum_anchor_components"]
            rows, endpoints, possible = select_quartets(
                data["a"], data["b"], data["positive"], len(component),
                salt=f"expanded-controls-v1:{fold}:C3:{cohort}",
                maximum=2000, edge_cap=10, endpoint_cap=50)
            print({"diagnostic": key, "stage": "quartets", "eligible_matchings": possible,
                   "selected_quartets": len(rows)}, flush=True)
            qp, qd, credit = quartet_estimates(scores, rows, endpoints, component, multipliers)
            qcomponents = len(np.unique(component[endpoints])) if len(endpoints) else 0
            quartet_ok = len(rows) >= cfg["minimum_quartets"] and qcomponents >= cfg["minimum_quartet_components"]
            cancellation = {}
            for name in ("endpoint_linear", "endpoint_mlp64"):
                j = MODELS.index(name)
                _, contrast = quartet_credit(scores[:, j], rows)
                error = float(np.max(np.abs(contrast), initial=0))
                if error > 1e-6 or (len(rows) and not np.all(credit[:, j] == .5)):
                    raise RuntimeError("additive endpoint control failed exact quartet cancellation")
                cancellation[name] = error
            # The algebraic null must hold for raw unary scores, not a sigmoid
            # or another nonlinear transformation of their pairwise sum.
            archive = OUT/f"bootstrap_{key}.npz"
            save(archive, anchor_points=ap, anchor_draws=ad, quartet_points=qp, quartet_draws=qd,
                 models=np.asarray(MODELS))
            panel_path = OUT/"diagnostic_panels"/(key+".npz")
            save(panel_path, quartet_rows=rows, quartet_endpoints=endpoints)
            result = {
                "partition": fold, "cell": "C3", "cohort": cohort,
                "anchor": {**model_results(ap, ad), **support, "support_floor_met": bool(anchor_ok)},
                "quartet": {**model_results(qp, qd), "selected": len(rows),
                            "eligible_matchings": possible, "participating_components": qcomponents,
                            "support_floor_met": bool(quartet_ok), "unary_cancellation_max_error": cancellation},
                "bootstrap": {"scheme": "paired Poisson(1) extended-component multipliers",
                              "seed": seed, "replicates": 2000, "components": len(components),
                              "multipliers_sha256": multiplier_hash},
                "bootstrap_file": record(archive, OUT),
                "panel_file": record(panel_path, OUT),
                "prediction_freeze_sha256": sha("/predictions/PREDICTION_FREEZE.json"),
            }
            write(target, result)
            fold_results[cohort] = result
            parts["anchor"].append((ap, ad, anchor_ok))
            parts["quartet"].append((qp, qd, quartet_ok))
        macro = {}
        for metric, part in parts.items():
            points = np.mean([x[0] for x in part], axis=0)
            draws = np.mean([x[1] for x in part], axis=0)
            macro[metric] = {**model_results(points, draws),
                             "support_floor_met": bool(all(x[2] for x in part)),
                             "cohort_weights": [.5, .5]}
            save(OUT/f"bootstrap_{fold}_macro_{metric}.npz",
                 points=points, draws=draws, models=np.asarray(MODELS))
        fold_results["macro"] = macro
        results[fold] = fold_results
    write(OUT/"RESULTS.json", {
        "at_utc": now(), "models": list(MODELS), "results": results, "cell": "C3",
        "reference": "Frozen selected 31k ensemble, exact saved covariance and native mean-field logits.",
        "primary_diagnostic_comparator": "endpoint_mlp64",
        "uncertainty": "2000 paired Poisson component draws; pointwise percentile95, not multiplicity-adjusted",
        "scope": "Direct dev2/test2 diagnostic; no internal refits, homology purging or source restriction.",
        "interpretation": "Within-anchor sampled-P/U ranking and selected-quartet preference; alternative edges remain unlabeled.",
        "protocol_sha256": sha(ROOT/"PROTOCOL.json"),
        "prediction_freeze_sha256": sha("/predictions/PREDICTION_FREEZE.json"),
        "test2_is_fresh_independent": False,
    })
    with (OUT/"scores.csv").open("x", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["partition", "cohort", "metric", "model", "estimate",
                         "ci95_low", "ci95_high", "finite_replicates", "support_floor_met"])
        for fold, cohorts in results.items():
            for cohort, value in cohorts.items():
                for metric in ("anchor", "quartet"):
                    for name, estimate in value[metric]["models"].items():
                        writer.writerow([fold, cohort, metric, name, estimate["point"],
                                         *(estimate["ci95"] or [None, None]), estimate["finite_replicates"],
                                         value[metric]["support_floor_met"]])
    with (OUT/"paired_differences.csv").open("x", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["partition", "cohort", "metric", "control", "selected_31k_minus_control",
                         "ci95_low", "ci95_high", "finite_replicates", "support_floor_met"])
        for fold, cohorts in results.items():
            for cohort, value in cohorts.items():
                for metric in ("anchor", "quartet"):
                    for name, estimate in value[metric]["paired_differences"].items():
                        writer.writerow([fold, cohort, metric, name, estimate["point"],
                                         *(estimate["ci95"] or [None, None]), estimate["finite_replicates"],
                                         value[metric]["support_floor_met"]])
    render(results)
    print({"partner_diagnostics_complete": True}, flush=True)


def render(results):
    def fmt(value):
        if value["point"] is None:
            return "NA"
        point = f"{value['point']:.6f}"
        return point if value["ci95"] is None else point+f" [{value['ci95'][0]:.6f}, {value['ci95'][1]:.6f}]"
    lines = [
        "# Direct C3 partner diagnostics", "",
        "These analyses use the frozen 31k TUnA scores and train2 controls on the existing",
        "dev2/test2 candidate panels. They do not reproduce the historical internal refits.",
        "All alternative edges remain unlabeled. Intervals are paired pointwise 95% intervals.",
        "", "## Test2 equal-cohort macro", "",
        "| Predictor | Within-anchor concordance [95% CI] | Selected-quartet preference [95% CI] |",
        "|---|---|---|",
    ]
    for name in MODELS:
        lines.append("| "+name+" | "+fmt(results["test"]["macro"]["anchor"]["models"][name])+
                     " | "+fmt(results["test"]["macro"]["quartet"]["models"][name])+" |")
    lines += ["", "## Support", "", "| Partition / cohort | Anchors | Anchor components | Quartets | Quartet components |",
              "|---|---:|---:|---:|---:|"]
    for fold in ("development", "test"):
        for cohort in COHORTS:
            row = results[fold][cohort]
            lines.append(f"| {fold}/{cohort} | {row['anchor']['anchors']} | {row['anchor']['anchor_components']} | "
                         f"{row['quartet']['selected']} | {row['quartet']['participating_components']} |")
    lines += [
        "", "Every model's cohort and macro results, paired differences, finite replicate counts,",
        "support-floor flags and additive-control cancellation checks are recorded in RESULTS.json.",
        "The reference scores use their native raw scale; nonlinear score transformations can",
        "change quartet preferences even when ordinary ranking is unchanged.",
        "", "Within-anchor means weight eligible anchors equally within each cohort.",
        "Macro results weight the two cohort-specific metrics equally; they do not pool anchor",
        "populations or claim independent cohorts. Quartets are a capped, deterministically",
        "selected candidate-panel sample and have no full-population sampling-weight claim.",
        "Sparse panels do not support inferential conclusions when the recorded floors fail.", "",
    ]
    (OUT/"RESULTS.md").write_text("\n".join(lines))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 8), sharey=True, constrained_layout=True)
    for ax, metric, title in zip(axes, ("anchor", "quartet"),
                                 ("Within-anchor concordance", "Selected-quartet preference"), strict=True):
        for j, name in enumerate(MODELS):
            value = results["test"]["macro"][metric]["models"][name]
            if value["point"] is None:
                continue
            color = "#00876c" if name == "selected_31k" else "#596b7a"
            if value["ci95"] is not None:
                ax.hlines(j, *value["ci95"], color=color)
            ax.plot(value["point"], j, "o", color=color)
        ax.axvline(.5, linestyle="--", color="#aaaaaa", linewidth=.8)
        ax.set(title=title, xlabel="Test2 C3 equal-cohort macro")
    axes[0].set_yticks(range(len(MODELS)), [x.replace("_", " ") for x in MODELS])
    axes[0].invert_yaxis()
    fig.suptitle("Direct partner diagnostics of frozen scores\nPointwise 95% paired Poisson-component intervals")
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(OUT/f"partner_diagnostics.{suffix}", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
