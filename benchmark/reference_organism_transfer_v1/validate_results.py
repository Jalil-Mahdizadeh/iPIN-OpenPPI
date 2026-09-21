"""Independently validate source mapping, metrics and bootstrap intervals."""
import argparse
import gzip
import itertools
import math
import zipfile
from collections import defaultdict
from io import BytesIO
from xml.etree import ElementTree as ET

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score

from evaluation_utils import *


def worksheet(data):
    """Read worksheet cells with stdlib XML, independently of openpyxl."""
    with zipfile.ZipFile(BytesIO(data)) as book:
        strings = []
        if "xl/sharedStrings.xml" in book.namelist():
            strings = ["".join(x.itertext()) for x in ET.fromstring(book.read("xl/sharedStrings.xml"))]
        root = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
        rows = {}
        for row in root.findall("./{*}sheetData/{*}row"):
            cells = {}
            for cell in row:
                value = cell.findtext("./{*}v", "")
                if cell.get("t") == "s":
                    value = strings[int(value)]
                elif cell.get("t") == "inlineStr":
                    value = "".join(cell.itertext())
                column = "".join(c for c in cell.get("r", "") if c.isalpha())
                cells[column] = value
            rows[int(row.get("r"))] = cells
        return rows


def source_mapping():
    with gzip.open(OUT / "published_evidence.json.gz", "rt") as handle:
        evidence = json.load(handle)
    ids = defaultdict(set)
    for row in evidence:
        ids[row["interaction_id"]].add(row["pair_id"])
    with zipfile.ZipFile(LOCAL / "PMC4848758_supplements.zip") as zipped:
        ev2 = worksheet(zipped.read("MSB-12-865-s004.xlsx"))
        ev7 = worksheet(zipped.read("MSB-12-865-s009.xlsx"))
    mapping = defaultdict(set)
    for number, row in ev2.items():
        if number < 3 or not row.get("A") or not row.get("C"):
            continue
        key = (row["A"].strip(), str(int(float(row["C"]))))
        for evidence_id in row.get("E", "").split(","):
            mapping[key].update(ids[evidence_id.strip()])
    expected, raw_count = {}, 0
    for number, row in ev7.items():
        if number < 3 or not row.get("A") or not row.get("B"):
            continue
        raw_count += 1
        key = (row["A"].strip(), str(int(float(row["B"]))))
        if len(mapping[key]) == 1:
            expected[number] = (next(iter(mapping[key])), row["F"].strip().lower(), float(row["E"]))
    actual = table(OUT / "assay_comparison.csv")
    require(len(actual) == len(expected), "Independent comparison denominator differs")
    for row in actual:
        expected_row = expected[int(row["ev7_row"])]
        require((row["pair_id"], row["published_call"], float(row["published_assay_score"])) == expected_row,
                "Independent worksheet mapping differs")
    return {"raw_published_rows": raw_count, "uniquely_mapped_rows": len(expected),
            "independent_reader": "stdlib ZIP/XML; builder uses openpyxl"}


def independent_components(rows):
    endpoint_rows = defaultdict(set)
    for i, row in enumerate(rows):
        for name in ("query_sequence_sha256", "partner_sequence_sha256"):
            endpoint_rows[row[name]].add(i)
    remaining = set(range(len(rows)))
    groups = []
    while remaining:
        todo = [min(remaining)]
        group = set()
        while todo:
            i = todo.pop()
            if i in group:
                continue
            group.add(i)
            for name in ("query_sequence_sha256", "partner_sequence_sha256"):
                todo.extend(endpoint_rows[rows[i][name]] - group)
        remaining -= group
        groups.append(group)
    labels = np.empty(len(rows), dtype=int)
    for c, group in enumerate(groups):
        for i in group:
            labels[i] = c
    return labels, groups


def close(actual, expected, message):
    if expected is None or not np.isfinite(expected):
        require(actual in (None, ""), message)
        return 0.0
    error = abs(float(actual) - float(expected))
    require(error < 1e-12, message)
    return error


def bounds(values):
    finite = np.asarray(values)[np.isfinite(values)]
    return np.quantile(finite, [.025, .975]) if len(finite) >= 1000 else [None, None]


def validate():
    require(not (OUT / "RESULT_VALIDATION.json").exists(), "Refusing to replace result validation")
    freeze = read(OUT / "INPUT_FREEZE.json")
    analysis = read(OUT / "ANALYSIS.json")
    checked = freeze["files"] + analysis["outputs"] + analysis["model_outputs"]
    for item in checked:
        verify(item)
    mapping = source_mapping()
    rows = table(OUT / "assay_model_scores.csv")
    original_rows = table(OUT / "assay_comparison.csv")
    require([r["pair_id"] for r in rows] == [r["pair_id"] for r in original_rows], "Assay order changed")
    panels = table(OUT / "panels.csv")
    for name, models in (("ipin_scores.csv", MODELS[:2]), ("tuna_scores.csv", MODELS[2:])):
        scores = table(OUT / name)
        require(len(scores) == len(panels), "Scoring coverage mismatch")
        for row in rows:
            i = int(row["row_index"])
            require(panels[i]["pair_id"] == row["pair_id"], "Pair-to-score mapping differs")
            for model in models:
                close(row[model + "_score"], float(scores[i][model + "_score"]), "Exported model score differs")
    endpoint = {r["sequence_sha256"]: r for r in table(OUT / "exact_endpoint_exposure.csv")}
    unseen = []
    for row in rows:
        flags = [endpoint[row[k]] for k in ("query_sequence_sha256", "partner_sequence_sha256")]
        train = any(boolean(r["exact_TRAIN_endpoint"]) for r in flags)
        dev = any(boolean(r["exact_DEV_endpoint"]) for r in flags)
        require(boolean(row["either_exact_train_endpoint"]) == train and boolean(row["either_exact_development_endpoint"]) == dev,
                "Exposure flag differs")
        if not train and not dev:
            unseen.append(row)
    metrics = table(OUT / "metrics.csv")
    differences = table(OUT / "paired_differences.csv")
    cluster_table = table(OUT / "bootstrap_components.csv")
    max_error, verified_intervals, summaries = 0.0, 0, {}
    for cohort, selected in (("all_mapped_assays", rows), ("no_exact_train_or_development_endpoint", unseen)):
        y = np.array([boolean(r["confirmed"]) for r in selected], dtype=bool)
        c, groups = independent_components(selected)
        expected_labels = {r["pair_id"]: int(label) for r, label in zip(selected, c)}
        actual_labels = {r["pair_id"]: int(r["component"]) for r in cluster_table if r["cohort"] == cohort}
        require(expected_labels == actual_labels, "Independent graph components differ")
        score = {m: np.array([float(r[m + "_score"]) for r in selected]) for m in MODELS}
        both = bool(y.any() and (~y).any())
        distributions = {m: {k: np.full(10000, np.nan) for k in ("AUROC", "AP")} for m in MODELS}
        if len(groups) >= 2 and both:
            rng = np.random.default_rng(20260921)
            counts = rng.multinomial(len(groups), np.full(len(groups), 1 / len(groups)), size=10000)
            for b, count in enumerate(counts):
                # Independent validation explicitly replicates observations and uses sklearn.
                sample = np.repeat(np.arange(len(selected)), count[c])
                labels = y[sample]
                if labels.any() and (~labels).any():
                    for model in MODELS:
                        distributions[model]["AUROC"][b] = roc_auc_score(labels, score[model][sample])
                        distributions[model]["AP"][b] = average_precision_score(labels, score[model][sample])
                if (b + 1) % 2000 == 0:
                    print(f"Independent bootstrap: {cohort}, {b+1}/10000 draws", flush=True)
        for model in MODELS:
            row = next(r for r in metrics if r["cohort"] == cohort and r["model"] == model)
            require(int(row["pairs"]) == len(selected) and int(row["confirmed"]) == int(y.sum()), "Metric denominator differs")
            auc = roc_auc_score(y, score[model]) if both else None
            ap = average_precision_score(y, score[model]) if both else None
            max_error = max(max_error, close(row["AUROC"], auc, "AUROC differs"), close(row["AP"], ap, "AP differs"))
            if both:
                direct = sum(float(a > b) + .5 * float(a == b) for a in score[model][y] for b in score[model][~y]) / (y.sum() * (~y).sum())
                close(row["AUROC"], direct, "Explicit pair-comparison AUROC differs")
            assay = np.array([float(r["published_assay_score"]) for r in selected])
            rho = float(spearmanr(score[model], assay).statistic) if len(set(score[model])) > 1 and len(set(assay)) > 1 else None
            max_error = max(max_error, close(row["Spearman_assay_score"], rho, "Spearman differs"))
            for metric in ("AUROC", "AP"):
                lo, hi = bounds(distributions[model][metric])
                max_error = max(max_error, close(row[metric + "_ci_low"], lo, "Interval lower bound differs"),
                                close(row[metric + "_ci_high"], hi, "Interval upper bound differs"))
                verified_intervals += lo is not None
        for row in (r for r in differences if r["cohort"] == cohort):
            a, b, metric = row["model_a"], row["model_b"], row["metric"]
            lo, hi = bounds(distributions[a][metric] - distributions[b][metric])
            close(row["ci_low"], lo, "Paired lower bound differs")
            close(row["ci_high"], hi, "Paired upper bound differs")
            first = next(r for r in metrics if r["cohort"] == cohort and r["model"] == a)
            second = next(r for r in metrics if r["cohort"] == cohort and r["model"] == b)
            expected = float(first[metric]) - float(second[metric]) if first[metric] and second[metric] else None
            close(row["difference_a_minus_b"], expected, "Paired point difference differs")
            verified_intervals += lo is not None
        summaries[cohort] = {"pairs": len(selected), "components": len(groups),
                             "valid_bootstrap_draws": int(np.isfinite(distributions[MODELS[0]]["AUROC"]).sum())}
    ipin = read(OUT / "IPIN_RUN.json")
    tuna = read(OUT / "TUNA_RUN.json")
    require(ipin["pair_order_symmetry_passed"] and not ipin["preexisting_feature_cache_reads"], "iPIN execution qualification failed")
    require(not tuna["GP_covariance_refitted"] and not tuna["preexisting_feature_cache_reads"], "TUnA execution changed")
    for member in tuna["native_qualification"]:
        require(member["pair_order_symmetry_passed"] and member["parameters_and_buffers_unchanged"] and
                member["native_max_absolute_error"] <= member["tolerance"], "TUnA native qualification failed")
    write_json(OUT / "RESULT_VALIDATION.json", {"at_utc": now(), "status": "passed",
        "source_mapping": mapping, "checked_artifact_records": len(checked),
        "independent_bootstrap_method": "Explicit repeated observations with sklearn AUROC/AP; independent BFS components",
        "verified_intervals": int(verified_intervals), "maximum_point_or_interval_error": max_error,
        "tolerance": 1e-12, "cohorts": summaries, "analysis": record(OUT / "ANALYSIS.json"),
        "script": record(OUT / "validate_results.py"), "model_execution_qualification_passed": True})
    print("Independent source, metric, bootstrap and execution validation passed", flush=True)


if __name__ == "__main__":
    container()
    validate()
