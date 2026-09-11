"""Data-informed supplement to the development-only control-shift investigation."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import time

import numpy as np
import torch

from c3_control_shift_v1 import (
    ANCHORS, NAMES, SEARCH, assert_development, checked, favorable_mass,
    group_summary, length_bins, load_endpoint_universe, load_npz, matched_bins,
    read, record, sha, subset, write_new, ENDPOINTS_PATH, PARTITIONS_PATH,
)
from ipin_openppi.model_optimization.metrics import bootstrap, point

FIRST_SHA = "401d259d44c2874c4ee7d3a04c84a08325db7b323bf87764f7db6e01730c8db6"


def run(args):
    started = time.monotonic()
    if not torch.cuda.is_available() or (args.project / ".private").exists():
        raise RuntimeError("Require actual GPU and allowlisted mounts without repository .private")
    if sha(args.first) != FIRST_SHA:
        raise RuntimeError("Initial diagnostic result drift")
    first, inputs = read(args.first), []
    if sha(args.project / SEARCH) != ANCHORS[SEARCH]:
        raise RuntimeError("Search freeze drift")
    search = read(args.project / SEARCH)
    for relative in (ENDPOINTS_PATH, PARTITIONS_PATH):
        checked(args.project / relative, next(x for x in search["input_records"] if x["path"] == str(relative)), inputs)
    universe = load_endpoint_universe(args.project / ENDPOINTS_PATH, args.project / PARTITIONS_PATH)
    partitions, components = np.array(universe.partitions), np.array(universe.components)
    cells = {}
    for number in (0, 3, 4):
        filename = f"development_{number:02d}.npz"
        cells[number] = load_npz(checked(args.development / filename, next(x for x in search["files"] if x["path"] == f"data/{filename}"), inputs))
        assert_development(cells[number], partitions)
    for filename in ("SCORERS.json", "scores.f64.npy"):
        checked(args.scores / filename, next(x for x in search["input_records"] if x["path"].endswith(f"/C3_development/{filename}")), inputs)
    data = cells[0]
    a, b, p = data["a"], data["b"], data["positive"]
    columns = {x["scorer_id"]: x["column"] for x in read(args.scores / "SCORERS.json")["scorers"]}
    matrix = np.load(args.scores / "scores.f64.npy", mmap_mode="r", allow_pickle=False)
    scores = np.asarray(matrix[:, [columns[name] for name in NAMES]])
    favorable = np.column_stack([favorable_mass(scores[:, j], p, data["weight"]) for j in range(len(NAMES))])
    for j, name in enumerate(NAMES):
        if abs(favorable[:, j].mean() - first["development"]["full_concordance"][name]) > 1e-12:
            raise RuntimeError("Initial development concordance drift")
    sizes = Counter(components[partitions == "development"])
    ranked = sorted(sizes, key=lambda key: (-sizes[key], key))
    if [sizes[x] for x in ranked[:3]] != [643, 78, 61]:
        raise RuntimeError("Data-informed component identity/size drift")
    ca, cb = data["component_a"], data["component_b"]
    index = {key: i for i, key in enumerate(data["components"])}
    first_touch = (ca == index[ranked[0]]) | (cb == index[ranked[0]])
    third_a, third_b = ca == index[ranked[2]], cb == index[ranked[2]]
    third_touch, same = third_a | third_b, ca == cb
    keys = np.minimum(a, b) * len(components) + np.maximum(a, b)
    sources = {}
    for number, name in ((3, "HI-II-14_exclusive"), (4, "HuRI_exclusive")):
        cell = cells[number]
        aa, bb = cell["a"][cell["positive"]], cell["b"][cell["positive"]]
        sources[name] = p & np.isin(keys, np.minimum(aa, bb) * len(components) + np.maximum(aa, bb))
    sources["both_sources"] = p & ~sources["HI-II-14_exclusive"] & ~sources["HuRI_exclusive"]
    masks = {"within_component": same, "between_component": ~same,
             "both_in_third": third_a & third_b, "one_in_third": third_a ^ third_b,
             "neither_in_third": ~third_touch, "neither_in_first_or_third": ~(first_touch | third_touch)}
    groups = {}
    for name, mask in masks.items():
        groups[name] = {**group_summary(mask, data, favorable),
                        "source_positive_counts": {source: int(np.sum(mask & values)) for source, values in sources.items()}}
    influence = []
    for rank, component in enumerate(ranked, 1):
        mask = (ca == index[component]) | (cb == index[component])
        if not np.any(mask & p):
            continue
        influence.append({"endpoint_size_rank": rank, "endpoints": sizes[component],
                          **group_summary(mask, data, favorable)})
    sensitivities = {}
    bins = length_bins(universe.lengths[a], universe.lengths[b])
    for name in ("between_component", "neither_in_third", "neither_in_first_or_third"):
        keep = masks[name]
        reduced, local_scores = subset(data, keep), scores[keep]
        values = {scorer: point(local_scores[:, j], reduced) for j, scorer in enumerate(NAMES)}
        print(f"{name}: {values}", flush=True)
        draws = bootstrap(local_scores[:, :5], reduced, cell="C3_development", replicates=2000)
        if not np.isfinite(draws).all():
            raise RuntimeError("Nonfinite sensitivity bootstrap")
        sensitivities[name] = {"positive_rows": int(reduced["positive"].sum()),
                               "unlabeled_rows": int((~reduced["positive"]).sum()),
                               "concordance": values,
                               "ci95": {scorer: np.quantile(draws[:, j], [.025, .975]).tolist() for j, scorer in enumerate(NAMES[:5])},
                               "within_length_bins": matched_bins(local_scores, reduced, bins[keep])}
    return {"status": "data_informed_post_hoc_development_only_supplement",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "initial_result_sha256": FIRST_SHA, "input_records": inputs,
            "groups": groups, "sensitivities": sensitivities,
            "all_positive_participating_component_influences": influence,
            "component_contributions_overlap_and_must_not_be_summed": True,
            "bootstrap_replicates": 2000, "bootstrap_universe": "original_C3_development_components",
            "runtime": {"GPU": torch.cuda.get_device_name(), "elapsed_seconds": time.monotonic() - started},
            "test_rows_truth_predictions_keys_opened": False, "new_training_or_test_evaluation": False,
            "analysis_code_sha256": sha(Path(__file__)),
            "scope_document_sha256": sha(args.project / "docs/protocols/C3_CONTROL_SHIFT_COMPONENT_SUPPLEMENT_v1.md")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("/project"))
    parser.add_argument("--development", type=Path, default=Path("/development"))
    parser.add_argument("--scores", type=Path, default=Path("/scores"))
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite diagnostic evidence")
    write_new(args.output, run(args))
