"""Read-only full-census replay of development selection and training records."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from ipin_openppi.model_optimization.common import SEEDS, historical_integrity, read, recipes, sha, verify, write_new
from ipin_openppi.model_optimization.metrics import point
from ipin_openppi.model_optimization.run import arrays


def audit(project: Path):
    root = project / ".private/model_optimization_v1"
    bundle, runs = root / "bundle", root / "runs"
    frozen = read(bundle / "SEARCH_FREEZE.json")
    verify(bundle, frozen["files"])
    for item in frozen["files"]:
        if item["path"].startswith("code/ipin_openppi/"):
            current = project / "src" / item["path"].removeprefix("code/")
            if sha(current) != item["sha256"]:
                raise RuntimeError("Optimization source drift since prospective freeze")
    events = [json.loads(line) for line in (runs / "events.jsonl").read_text().splitlines()]
    epochs = [x for x in events if x["event"] == "epoch"]
    if len(epochs) != 168 or len({x["run_id"] for x in epochs}) != 36:
        raise RuntimeError("Training event census mismatch")
    for run in {x["run_id"] for x in epochs}:
        expected = 3 if run.startswith("stage1__") else 8
        records = [x for x in epochs if x["run_id"] == run]
        if sorted(x["epoch"] for x in records) != list(range(1, expected + 1)):
            raise RuntimeError("Incomplete per-run epoch history")
        if not all(np.isfinite(x["loss"]) and x["loss"] >= 0 and x["epoch_seconds"] > 0 for x in records):
            raise RuntimeError("Invalid objective or timing record")
    result = read(runs / "RESULTS.json")
    preliminary = [x for x in result["all_evaluations"] if x["stage"] == 1]
    if {x["recipe_id"] for x in preliminary} != {x["id"] for x in recipes(frozen["configuration"])}:
        raise RuntimeError("Recipe coverage mismatch")
    promoted = read(runs / "PROMOTION.json")["selected"]
    if promoted != sorted(preliminary, key=lambda r: (-r["concordance"], r["parameters"], r["recipe_id"]))[:4]:
        raise RuntimeError("Promotion rule mismatch")
    data = arrays(bundle / "data/development_00.npz")
    errors = []
    for group in result["all_ensemble_groups"]:
        if [x["seed"] for x in group["members"]] != list(SEEDS):
            raise RuntimeError("Wrong ensemble seed census")
        predictions = np.column_stack([np.load(runs / x["predictions"], allow_pickle=False).astype(np.float64) for x in group["members"]])
        errors.append(abs(point(predictions.mean(1), data) - group["concordance"]))
        errors.extend(abs(point(predictions[:, j], data) - member["concordance"])
                      for j, member in enumerate(group["members"]))
    if max(errors) > 1e-12:
        raise RuntimeError("Seed or ensemble development selection metric mismatch")
    gate = read(runs / "DEVELOPMENT_GATE.json")
    if not gate["passed"]:
        for path in (
            project / ".private/model_optimization_followup_v1",
            project / ".private/pair_level_pu_r_benchmark_artifacts_v1/followup_evaluations/model_optimization_followup_v1",
        ):
            if path.exists():
                raise RuntimeError("Follow-up namespace exists despite failed gate")
    failed_prefit = project / ".private/model_optimization_v1_prefit_plugin_failure"
    failure = read(failed_prefit / "runs/RESULTS.json")
    if failure["all_evaluations"] or (failed_prefit / "runs/FIRST_FIT.json").exists():
        raise RuntimeError("Pre-fit erratum scope was not truly pre-fit")
    # Published aggregates must be byte-identical to immutable run records.
    for name in ("RESULTS.json", "DEVELOPMENT_GATE.json", "SELECTION.json", "PROMOTION.json", "QUALIFICATION.json", "FIRST_FIT.json", "START.json", "GPU_FIXTURE_TESTS.txt", "events.jsonl"):
        if sha(runs / name) != sha(project / "artifacts/results/model_optimization_v1" / name):
            raise RuntimeError("Published aggregate drift")
    output = {"passed": True, "at_utc": datetime.now(timezone.utc).isoformat(),
              "epochs_verified": 168, "fits_verified": 36, "ensemble_groups_replayed": 8,
              "seed_metrics_replayed": 24, "metric_max_error": max(errors),
              "current_source_matches_prefit_freeze": True, "promotion_rule_verified": True,
              "publication_byte_identical_to_private_aggregates": True,
              "prefit_failure_had_no_fits_or_development_scores": True,
              "gate_passed": gate["passed"], "conditional_followup_not_started": not gate["passed"],
              "historical_integrity": historical_integrity(project)}
    write_new(project / "artifacts/validation/model_optimization_v1/FULL_CENSUS_AUDIT.json", output)
    print({k: v for k, v in output.items() if k != "historical_integrity"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    audit(parser.parse_args().project.resolve())
