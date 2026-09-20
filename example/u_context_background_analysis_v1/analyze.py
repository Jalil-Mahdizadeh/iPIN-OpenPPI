"""Exploratory context/background score comparison on preserved example data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone

import numpy as np
import scipy
from scipy import stats

MODELS = ("ipin_baseline", "ipin_optimized", "tuna_retrained")
SEED = 20260920
DRAWS = 100_000
PARENT = Path("example/twelve_target_comparison_v1")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with Path(path).open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    with Path(path).open("x") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def superiority(context, background):
    """Fraction of cross-group comparisons won by context, with half for ties."""
    x, y = np.asarray(context), np.asarray(background)
    if not x.size or not y.size or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Finite, nonempty groups required")
    return float(np.mean((x[:, None] > y).astype(float) + 0.5 * (x[:, None] == y)))


def top_context_fraction(context, background, k=20):
    scores = np.r_[context, background]
    labels = np.r_[np.ones(len(context), dtype=bool), np.zeros(len(background), dtype=bool)]
    if not 0 < k <= len(scores):
        raise ValueError("Invalid top-K")
    threshold = np.sort(scores)[-k]
    above, tied = scores > threshold, scores == threshold
    return float((labels[above].sum() + labels[tied].mean() * (k - above.sum())) / k)


def sign_flip_p(effects):
    effects = np.asarray(effects, dtype=float)
    signs = np.asarray(list(itertools.product((-1, 1), repeat=len(effects))))
    null = (signs @ effects) / len(effects)
    observed = abs(effects.mean())
    tolerance = 100 * np.finfo(float).eps * max(1, observed)
    return float(np.mean(np.abs(null) >= observed - tolerance))


def holm(pvalues):
    p = np.asarray(pvalues)
    order = np.argsort(p)
    adjusted = np.empty(len(p))
    adjusted[order] = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return adjusted


def score_description(context, background):
    output = {}
    for name, values in (("context", context), ("background", background)):
        output.update({name + "_" + key: float(value) for key, value in (
            ("mean", np.mean(values)), ("median", np.median(values)),
            ("q25", np.quantile(values, .25)), ("q75", np.quantile(values, .75)),
            ("sd", np.std(values, ddof=1)))})
    output["mean_difference"] = output["context_mean"] - output["background_mean"]
    output["median_difference"] = output["context_median"] - output["background_median"]
    output["A"] = superiority(context, background)
    output["rank_biserial"] = 2 * output["A"] - 1
    output["KS_distance"] = float(stats.ks_2samp(context, background).statistic)
    return output


def context_matches(source, block):
    text = re.sub(r"\{[^}]*\}", "", source["Subcellular location [CC]"].split("Note=", 1)[0]).lower()
    terms = ("cytoplasm", "cytosol") if block["compartment"] == "cytoplasm" else (block["compartment"],)
    return bool(source["Transmembrane"].strip()) == block["transmembrane"] and any(t in text for t in terms)


def prepare(root, out):
    manifest_path = root / PARENT / "RUN_MANIFEST.json"
    parent = json.loads(manifest_path.read_text())
    for artifact in parent["scientific_outputs"]:
        assert sha(root / artifact["path"]) == artifact["sha256"], artifact["path"]
    rows = read_csv(root / PARENT / "all_twelve_targets_scores.csv")
    config = json.loads((root / PARENT / "panel_config.json").read_text())
    targets = config["original_targets"] + [t["gene"] for t in config["new_targets"]]
    assert len(rows) == 3737 and len(targets) == 12
    pool_path = root / PARENT / "sources/reviewed_human.tsv"
    pool_sha = sha(pool_path)
    with pool_path.open() as stream:
        pool = {r["Entry"]: r for r in csv.DictReader(stream, delimiter="\t")}
    metadata, lengths, inputs = [], [], []
    anchors = {}
    for target in targets:
        panel_path = root / "example" / target / "panel_manifest.json"
        panel = json.loads(panel_path.read_text())
        assert panel["pool_source"]["sha256"] == pool_sha
        inputs.append({"path": str(panel_path.relative_to(root)), "sha256": sha(panel_path)})
        annotations = {r["row"]: r for r in panel["rows"]}
        blocks = {b["anchor_accession"]: b for b in panel["U_blocks"] if b["stratum"] == "context"}
        selected = [r for r in rows if r["query_gene"] == target]
        pp = [r for r in selected if r["class"] == "P"]
        uu = [r for r in selected if r["class"] == "U"]
        assert len(uu) == 100 * len(pp)
        assert len({r["partner_sequence_sha256"] for r in uu}) == len(uu)
        anchors[target] = [r["partner_uniprot"] for r in pp]
        for row in uu:
            annotation = annotations[int(row["panel_row"])]
            for key in ("partner_uniprot", "sequence_sha256"):
                row_key = "partner_sequence_sha256" if key == "sequence_sha256" else key
                assert row[row_key] == annotation[key]
            assert row["anchor_positive_uniprot"] == annotation["anchor_positive_uniprot"]
            assert row["U_stratum"] == annotation["stratum"]
            assert row["prior_train_development_pair"] == "False"
            anchor = row["anchor_positive_uniprot"]
            source = pool[row["partner_uniprot"]]
            assert hashlib.sha256(source["Sequence"].encode()).hexdigest() == row["partner_sequence_sha256"]
            matches = context_matches(source, blocks[anchor])
            if row["U_stratum"] == "context":
                assert matches
            metadata.append({"target": target, "partner_uniprot": row["partner_uniprot"],
                "partner_sequence_sha256": row["partner_sequence_sha256"],
                "anchor_positive_uniprot": anchor, "U_stratum": row["U_stratum"],
                "partner_length": int(row["partner_sequence_length"]),
                "anchor_compartment": blocks[anchor]["compartment"],
                "anchor_transmembrane": blocks[anchor]["transmembrane"],
                "partner_transmembrane": bool(source["Transmembrane"].strip()),
                "partner_subcellular_location": source["Subcellular location [CC]"],
                "meets_anchor_context_rule": matches})
        for positive in pp:
            anchor = positive["partner_uniprot"]
            own = [r for r in metadata if r["target"] == target and r["anchor_positive_uniprot"] == anchor]
            ctx = [r for r in own if r["U_stratum"] == "context"]
            bg = [r for r in own if r["U_stratum"] == "background"]
            assert len(ctx) == len(bg) == 50
            plength = int(positive["partner_sequence_length"])
            assert all(.5 <= r["partner_length"] / plength <= 2 for r in own)
            x = [r["partner_length"] for r in ctx]
            y = [r["partner_length"] for r in bg]
            lengths.append({"target": target, "anchor": anchor, "anchor_gene": positive["partner_gene"],
                "context_n": 50, "background_n": 50,
                "context_mean_length": float(np.mean(x)), "background_mean_length": float(np.mean(y)),
                "length_A": superiority(x, y),
                "background_meeting_context_rule": sum(r["meets_anchor_context_rule"] for r in bg)})
    assert len(metadata) == 3700 and len(lengths) == 37
    assert sum(r["U_stratum"] == "context" for r in metadata) == 1850
    for row in rows:
        for model in MODELS:
            row[model + "_score"] = float(row[model + "_score"])
            assert np.isfinite(row[model + "_score"])
    write_csv(out / "candidate_annotations.csv", metadata)
    write_csv(out / "matching_diagnostics.csv", lengths)
    inputs.extend({"path": str(PARENT / name), "sha256": sha(root / PARENT / name)} for name in (
        "RUN_MANIFEST.json", "all_twelve_targets_scores.csv", "per_target_metrics.csv", "panel_config.json"))
    inputs.append({"path": str(pool_path.relative_to(root)), "sha256": pool_sha})
    return rows, targets, anchors, metadata, lengths, inputs, parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Use the accepted data Apptainer image")
    root, out = args.root, args.output
    rows, targets, anchors, metadata, lengths, inputs, parent = prepare(root, out)
    lookup = {(r["target"], r["partner_uniprot"]): r for r in metadata}
    parent_metrics = read_csv(root / PARENT / "per_target_metrics.csv")
    by_anchor, by_target = [], []
    checks = []
    for target in targets:
        panel = [r for r in rows if r["query_gene"] == target and r["class"] == "U"]
        cohort = panel[0]["target_cohort"]
        for model in MODELS:
            key = model + "_score"
            for anchor in anchors[target]:
                own = [r for r in panel if r["anchor_positive_uniprot"] == anchor]
                context = np.asarray([r[key] for r in own if r["U_stratum"] == "context"])
                background = np.asarray([r[key] for r in own if r["U_stratum"] == "background"])
                nonmatching = [r[key] for r in own if r["U_stratum"] == "background" and
                               not lookup[target, r["partner_uniprot"]]["meets_anchor_context_rule"]]
                assert nonmatching
                description = score_description(context, background)
                reference = stats.mannwhitneyu(context, background).statistic / (len(context) * len(background))
                assert np.isclose(reference, description["A"], rtol=0, atol=1e-15)
                by_anchor.append({"target": target, "cohort": cohort, "model": model, "anchor": anchor,
                    "context_n": len(context), "background_n": len(background), **description,
                    "nonmatching_background_n": len(nonmatching),
                    "A_context_vs_nonmatching_background": superiority(context, nonmatching)})
            context = np.asarray([r[key] for r in panel if r["U_stratum"] == "context"])
            background = np.asarray([r[key] for r in panel if r["U_stratum"] == "background"])
            selected = [r for r in by_anchor if r["target"] == target and r["model"] == model]
            a = float(np.mean([r["A"] for r in selected]))
            p_concordance = {r["U_stratum"]: float(r["P_vs_U_concordance"]) for r in parent_metrics
                            if r["target"] == target and r["model"] == model and r["positive_subset"] == "all_P"}
            description = score_description(context, background)
            by_target.append({"target": target, "cohort": cohort, "model": model, "anchors": len(selected),
                "context_n": len(context), "background_n": len(background),
                **{("unstratified_A" if k == "A" else "unstratified_rank_biserial" if k == "rank_biserial" else k): v
                   for k, v in description.items()},
                "anchor_matched_A": a, "anchor_matched_rank_biserial": 2 * a - 1,
                "A_context_vs_nonmatching_background": float(np.mean([r["A_context_vs_nonmatching_background"] for r in selected])),
                "top20_U_context_fraction": top_context_fraction(context, background),
                "P_vs_context_concordance": p_concordance["context"],
                "P_vs_background_concordance": p_concordance["background"]})
    summary, loo = [], []
    for cohort in ("all_twelve", "original_six", "additional_six"):
        selected_targets = [t for t in targets if cohort == "all_twelve" or
                            next(r["cohort"] for r in by_target if r["target"] == t) == cohort]
        draws = np.random.default_rng(SEED).integers(0, len(selected_targets), (DRAWS, len(selected_targets)))
        for model in MODELS:
            selected = [next(r for r in by_target if r["target"] == target and r["model"] == model)
                        for target in selected_targets]
            values = np.asarray([r["anchor_matched_A"] for r in selected])
            lower, upper = np.quantile(values[draws].mean(axis=1), [.025, .975])
            pvalue = sign_flip_p(values - .5) if cohort == "all_twelve" else None
            if pvalue is not None:
                reference = stats.permutation_test((values - .5,), np.mean, permutation_type="samples",
                    n_resamples=np.inf, alternative="two-sided").pvalue
                assert np.isclose(pvalue, reference, rtol=0, atol=1e-15)
                checks.append({"model": model, "exact_sign_flip_matches_scipy": True})
            summary.append({"cohort": cohort, "model": model, "targets": len(selected),
                "anchors": sum(r["anchors"] for r in selected),
                "context_n": sum(r["context_n"] for r in selected),
                "background_n": sum(r["background_n"] for r in selected),
                "equal_target_A": float(values.mean()), "A_ci95_low": float(lower), "A_ci95_high": float(upper),
                "rank_biserial": float(2 * values.mean() - 1),
                "targets_A_above_half": int(np.sum(values > .5)),
                "targets_A_below_half": int(np.sum(values < .5)),
                "min_target_A": float(values.min()), "max_target_A": float(values.max()),
                "sign_flip_p": pvalue, "sign_flip_p_holm_three_models": None,
                **{"mean_" + k: float(np.mean([r[k] for r in selected])) for k in (
                    "top20_U_context_fraction", "P_vs_context_concordance", "P_vs_background_concordance",
                    "A_context_vs_nonmatching_background", "unstratified_A", "mean_difference", "median_difference")}})
            if cohort == "all_twelve":
                for i, target in enumerate(selected_targets):
                    loo.append({"model": model, "omitted_target": target,
                                "equal_target_A": float(np.delete(values, i).mean())})
    for row, pvalue in zip(summary[:3], holm([r["sign_flip_p"] for r in summary[:3]]), strict=True):
        row["sign_flip_p_holm_three_models"] = float(pvalue)
    write_csv(out / "per_anchor_scores.csv", by_anchor)
    write_csv(out / "per_target_scores.csv", by_target)
    write_csv(out / "summary.csv", summary)
    write_csv(out / "leave_one_target_out.csv", loo)
    # Validate key edge cases without relying on the observed results.
    assert superiority([1, 1], [1, 1]) == .5
    assert superiority([2, 3], [0, 1]) == 1
    assert superiority([0, 1], [2, 3]) == 0
    assert top_context_fraction([1] * 50, [1] * 50) == .5
    assert np.allclose(holm([.04, .001, .03]), [.06, .003, .06])
    for artifact in parent["scientific_outputs"]:
        assert sha(root / artifact["path"]) == artifact["sha256"], artifact["path"]
    validation = {"passed": True, "parent_outputs_checked_unchanged": len(parent["scientific_outputs"]),
        "all_111_anchor_A_values_match_scipy_U": len(by_anchor) == 111,
        "all_context_membership_checks_passed": True, "synthetic_tie_and_reversal_checks": True,
        "sign_flip_checks": checks, "rows": {"scores": len(rows), "U": len(metadata),
        "anchors": len(lengths), "target_model": len(by_target)},
        "background_satisfying_context_rule": sum(r["background_meeting_context_rule"] for r in lengths)}
    write_json(out / "VALIDATION.json", validation)
    image = root / "containers/images/ipin-data-arm64_0.1.2.sif"
    expected = (root / "containers/locks/ipin-data-arm64_0.1.2.sif.sha256").read_text().split()[0]
    assert sha(image) == expected
    write_json(out / "ANALYSIS_RUN.json", {"at_utc": datetime.now(timezone.utc).isoformat(),
        "schema": "ipin_context_background_scores_v1", "inputs": inputs,
        "protocol_sha256": sha(out / "PROTOCOL.md"), "analysis_source_sha256": sha(Path(__file__)),
        "runtime": {"python": sys.version, "numpy": np.__version__, "scipy": scipy.__version__,
                    "image": str(image.relative_to(root)), "image_sha256": expected},
        "bootstrap": {"draws": DRAWS, "seed": SEED, "unit": "target", "method": "percentile"},
        "sign_flip_patterns": 4096, "scores_recomputed": False, "protected_test_access": False,
        "outputs": [{"path": str(p.relative_to(root)), "sha256": sha(p)} for p in sorted(out.glob("*.csv"))]})
    print(json.dumps(summary[:3], indent=2))
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
