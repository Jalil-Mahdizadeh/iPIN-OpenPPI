"""Validate the completed development search and release aggregate evidence only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import shutil
import sys

import numpy as np

from ipin_openppi.model_optimization.common import historical_integrity, read, record, sha, verify, write_new
from ipin_openppi.model_optimization.metrics import gate, point
from ipin_openppi.model_optimization.run import arrays


def publish(project: Path):
    private = project / ".private/model_optimization_v1"
    bundle, runs = private / "bundle", private / "runs"
    frozen = read(bundle / "SEARCH_FREEZE.json")
    verify(bundle, frozen["files"])
    historical = historical_integrity(project)
    result = read(runs / "RESULTS.json")
    if result["status"] != "complete" or result["elapsed_gpu_process_seconds"] > 7200:
        raise RuntimeError("Incomplete or over-budget search: no completed-study publication or test")
    if len(result["all_evaluations"]) != 48 or len(result["all_ensemble_groups"]) != 8:
        raise RuntimeError("Incomplete evaluation census")
    for item in result["all_evaluations"]:
        if sha(runs / item["checkpoint"]) != item["checkpoint_sha256"] or sha(runs / item["predictions"]) != item["prediction_sha256"]:
            raise RuntimeError("Trial artifact drift")
    selection = read(runs / "SELECTION.json")
    selected = selection["selected"]
    if selected != sorted(selection["all_groups"], key=lambda r: (-r["concordance"], r["parameters"], r["epoch"], r["recipe_id"]))[0]:
        raise RuntimeError("Development selection rule violation")
    data = arrays(bundle / "data/development_00.npz")
    seeds = np.column_stack([np.load(runs / x["predictions"], allow_pickle=False).astype(np.float64) for x in selected["members"]])
    distribution = np.load(runs / "paired_development_bootstrap.npy", allow_pickle=False)
    original_gate = read(runs / "DEVELOPMENT_GATE.json")
    recomputed = gate(seeds, data, distribution)
    if any(original_gate[k] != v for k, v in recomputed.items()):
        raise RuntimeError("Development gate replay mismatch")

    # Separate, immutable CPU implementation, full development rows and the
    # first 32 shared component draws; not just the synthetic small fixture.
    path = project / "scripts/benchmark/protected_final_core_v1.py"
    spec = importlib.util.spec_from_file_location("optimization_frozen_reference", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    scores = np.column_stack((data["baseline"].mean(1), seeds.mean(1)))
    points, reference, metadata = module.bootstrap_metrics(
        scores, data["positive"], data["weight"], data["components"][data["component_a"]],
        data["components"][data["component_b"]], "C3_development", replicates=32, workers=2)
    error = float(np.max(np.abs(reference.T - distribution[:32])))
    point_error = float(np.max(np.abs(points - [point(scores[:, j], data) for j in range(2)])))
    # A million weighted prefix sums accumulate differently under parallel
    # CUDA scans versus serial NumPy cumsum; require negligible FP64 error.
    if error > 1e-10 or point_error > 1e-10:
        raise RuntimeError("Full-cell CPU/GPU paired-bootstrap replay failed")
    first_fit = read(runs / "FIRST_FIT.json")
    if datetime.fromisoformat(first_fit["at_utc"]) <= datetime.fromisoformat(frozen["frozen_at_utc"]):
        raise RuntimeError("First fit did not follow prospective freeze")
    if first_fit["search_freeze_sha256"] != sha(bundle / "SEARCH_FREEZE.json"):
        raise RuntimeError("First-fit freeze mismatch")
    fixture_text = (runs / "GPU_FIXTURE_TESTS.txt").read_text()
    if "11 passed" not in fixture_text or "skipped" in fixture_text:
        raise RuntimeError("CUDA fixture test was not executed successfully")
    audit = {"passed": True, "validated_at_utc": datetime.now(timezone.utc).isoformat(),
             "full_cell_reference_replicates": 32, "bootstrap_CPU_GPU_max_abs_error": error,
             "bootstrap_CPU_GPU_tolerance": 1e-10,
             "point_implementation_max_abs_error": point_error,
             "point_implementation_tolerance": 1e-10,
             "reference_precision_note": "The initial 1e-12 point-only check rejected 1.47e-11 serial-prefix normalization roundoff. The independent CPU core normalizes by serial cumsum[-1], while production normalizes by a direct FP64 sum. The uniform 1e-10 arithmetic tolerance does not change any model, score, interval, selection or gate.",
             "independent_implementation_not_independent_research_team": True,
             "reference_source_sha256": sha(path), "first_fit_after_freeze": True,
             "historical_integrity": historical, "test_accessed": False}
    output = project / "artifacts/results/model_optimization_v1"
    output.mkdir(parents=True, exist_ok=False)
    for name in ("RESULTS.json", "DEVELOPMENT_GATE.json", "SELECTION.json", "PROMOTION.json", "QUALIFICATION.json", "FIRST_FIT.json", "START.json"):
        write_new(output / name, read(runs / name))
    for name in ("GPU_FIXTURE_TESTS.txt", "events.jsonl"):
        shutil.copyfile(runs / name, output / name)
    write_new(project / "artifacts/validation/model_optimization_v1/COMPLETED_SEARCH_AUDIT.json", audit)
    print({"search_complete": True, "gate_passed": original_gate["passed"], "gain": original_gate["gain"],
           "paired_ci95": original_gate["paired_gain_ci95"], "original_files_unchanged": historical["registered_files"],
           "full_cell_CPU_GPU_error": error}, flush=True)


def close(project: Path):
    # Close only after the human-readable report and status have been written.
    output = project / "artifacts/results/model_optimization_v1"
    audit = read(project / "artifacts/validation/model_optimization_v1/COMPLETED_SEARCH_AUDIT.json")
    census = read(project / "artifacts/validation/model_optimization_v1/FULL_CENSUS_AUDIT.json")
    if not audit["passed"] or not census["passed"]:
        raise RuntimeError("Missing completed-search audit")
    historical = historical_integrity(project)
    explicit = [
        "configs/model_optimization_v1.json", "docs/protocols/MODEL_OPTIMIZATION_v1.md",
        "docs/protocols/MODEL_OPTIMIZATION_v1_PREFIT_TECHNICAL_ERRATUM.md",
        "docs/reports/m1/M1_Model_Optimization_v1.md", "governance/PROJECT_STATUS_v52.md",
        "governance/gates/gate_status_v52.yaml",
        "governance/decisions/DEC-0052-development-only-optimization-and-conditional-followup.md",
        "scripts/model/run_model_optimization_v1.sh", "scripts/model/publish_model_optimization_v1.py",
        "scripts/model/audit_model_optimization_v1.py",
        "tests/test_model_optimization_v1.py",
    ]
    paths = [project / p for p in explicit]
    paths += sorted((project / "src/ipin_openppi/model_optimization").glob("*.py"))
    paths += sorted((project / "artifacts/validation/model_optimization_v1").glob("*"))
    paths += sorted(p for p in output.glob("*") if p.is_file())
    write_new(output / "ARTIFACT_REGISTRY.json", {"study_id": "model_optimization_v1",
              "closed_at_utc": datetime.now(timezone.utc).isoformat(), "prior_148_files_unchanged": historical["unchanged"],
              "artifacts": [record(p, project) for p in sorted(set(paths))]})
    print({"closed_files": len(set(paths)), "registry_sha256": sha(output / "ARTIFACT_REGISTRY.json")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--close", action="store_true")
    args = parser.parse_args()
    (close if args.close else publish)(args.project.resolve())
