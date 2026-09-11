"""Verify fixed state and GPU/CPU development replay before protected access."""
from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time
import unittest

import numpy as np
import pyarrow.parquet as pq
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model_optimization_followup_core_v1 as core
from ipin_openppi.model_optimization.common import historical_integrity
from ipin_openppi.model_optimization.metrics import point
from ipin_openppi.model_optimization.run import configure_cuda


SOURCES = (
    "scripts/benchmark/model_optimization_followup_core_v1.py",
    "scripts/benchmark/prepare_model_optimization_followup_v1.py",
    "scripts/benchmark/run_model_optimization_followup_v1.sh",
    "scripts/benchmark/publish_model_optimization_followup_v1.py",
    "scripts/benchmark/audit_model_optimization_followup_v1.py",
    "scripts/benchmark/protected_final_core_v1.py",
    "scripts/benchmark/protected_final_guard_v1.py",
    "tests/unit/test_model_optimization_followup_v1.py",
    "tests/unit/test_model_optimization_followup_publication_v1.py",
    "tests/unit/test_protected_final_test_v1.py",
    "docs/protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md",
    "governance/decisions/DEC-0053-authorize-fixed-ensemble-followup.md",
)


def historical_check(project):
    previous = historical_integrity(project)
    path = project / "artifacts/results/model_optimization_v1/ARTIFACT_REGISTRY.json"
    if core.sha(path) != "4143e7641660e3a1457d08ab989d1a58a69c5402f558fbf883325fd0fa5dcc56":
        raise RuntimeError("Completed optimization registry drift")
    records = core.read(path)["artifacts"]
    core.verify_records(project, records)
    previous["studies"].append({"study": "model_optimization_v1", "registry_sha256": core.sha(path), "files": len(records)})
    previous["registered_files"] += len(records)
    if previous["registered_files"] != 179:
        raise RuntimeError("Historical closure census drift")
    return previous


def synthetic_tests(project):
    suite = unittest.TestSuite()
    paths = [p for p in SOURCES if p.startswith("tests/")]
    for index, relative in enumerate(paths):
        spec = importlib.util.spec_from_file_location(f"followup_fixture_{index}", project / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "passed": result.wasSuccessful(), "synthetic_only": True, "console": stream.getvalue(),
              "test_sources": [core.record(project / p, project) for p in paths]}
    if not result.wasSuccessful():
        print(stream.getvalue(), file=sys.stderr)
        raise RuntimeError("Synthetic qualification failed before protected access")
    return report


def prepare(project):
    os.umask(0o077)
    private = project / ".private" / core.EXECUTION
    private.mkdir(parents=True, exist_ok=True)
    core.write_new(private / "PREPARATION_STARTED.json", {"started_at_utc": core.now(), "new_fit": False})
    historical = historical_check(project)
    tests = synthetic_tests(project)
    gpu_start = time.monotonic()
    accelerator = configure_cuda()
    torch.set_num_threads(8)
    output = private / "bundle"
    features, code, provenance = output / "features", output / "code", output / "provenance"
    output.mkdir(exist_ok=False)
    for directory in (features, code, provenance):
        directory.mkdir()
    inputs = []

    def checked(path, expected=None):
        if expected is not None and core.sha(path) != expected:
            raise RuntimeError(f"Frozen input checksum drift: {path.relative_to(project)}")
        inputs.append(core.record(path, project))
        return path

    search_root = project / ".private/model_optimization_v1"
    search_path = checked(search_root / "bundle/SEARCH_FREEZE.json", core.SEARCH_SHA)
    search = core.read(search_path)
    core.verify_records(search_root / "bundle", search["files"])
    selection_path = checked(project / "artifacts/results/model_optimization_v1/SELECTION.json", core.SELECTION_SHA)
    selection = core.read(selection_path)["selected"]
    if (selection["recipe_id"] != core.RECIPE or selection["epoch"] != 4
            or [x["seed"] for x in selection["members"]] != list(core.SEEDS)
            or [x["checkpoint_sha256"] for x in selection["members"]] != list(core.CHECKPOINT_SHAS)):
        raise RuntimeError("Selected ensemble drift")
    gate_path = checked(project / "artifacts/results/model_optimization_v1/DEVELOPMENT_GATE.json")
    gate = core.read(gate_path)
    if (gate["passed"] is not False or not gate["complete_search"]
            or gate["selection_sha256"] != core.SELECTION_SHA or gate["search_freeze_sha256"] != core.SEARCH_SHA
            or not all(gate["checks"][k] for k in ("ensemble_gain_positive", "paired_interval_lower_above_zero", "all_bootstrap_replicates_finite"))):
        raise RuntimeError("Completed ensemble promotion evidence mismatch")
    original_bundle = project / "artifacts/runs/protected_final_test_v1/frozen_bundle"
    old_manifest_path = checked(original_bundle / "SCORER_FREEZE.json", "5f25e856ce74e9f93497c17c19eb45ab1cb49fd74a30ceca5b4f874727e0125f")
    old_manifest = core.read(old_manifest_path)
    core.verify_records(original_bundle, old_manifest["files"])
    data = search_root / "bundle/data"
    for old, new in ((data / "endpoints.json", features / "endpoints.json"),
                     (data / "esm2_150m.npy", features / "standardized.npy"),
                     (original_bundle / "features/components.json", features / "components.json"),
                     (original_bundle / "features/public_training_fixture.parquet", features / "public_training_fixture.parquet")):
        shutil.copyfile(checked(old), new)
    if (core.read(features / "endpoints.json") != core.read(original_bundle / "features/endpoints.json")
            or core.sha(features / "standardized.npy") != core.sha(original_bundle / "features/standardized.npy")):
        raise RuntimeError("Original baseline/search endpoint embedding identity mismatch")
    for member, digest in zip(selection["members"], core.CHECKPOINT_SHAS, strict=True):
        shutil.copyfile(checked(search_root / "runs" / member["checkpoint"], digest), features / f"candidate_{member['seed']}.npz")
    source_models = checked(project / "src/ipin_openppi/model_optimization/models.py")
    if core.sha(source_models) != core.sha(search_root / "bundle/code/ipin_openppi/model_optimization/models.py"):
        raise RuntimeError("Model source changed since search freeze")
    shutil.copyfile(source_models, code / "optimization_models_v1.py")
    with np.load(checked(data / "development_00.npz"), allow_pickle=False) as archive:
        development = {k: archive[k].copy() for k in archive.files}
    frozen_columns = [np.load(checked(search_root / "runs" / x["predictions"], x["prediction_sha256"]), allow_pickle=False).astype(np.float64) for x in selection["members"]]
    reference = np.column_stack(frozen_columns)
    reference = np.column_stack((reference.mean(1, dtype=np.float64), reference))
    references = [point(reference[:, j], development) for j in range(4)]
    replays = {}
    for device in ("cuda", "cpu"):
        scorer = core.Scorer(output, device=device)
        actual = scorer.score_indices(development["a"], development["b"])
        errors = np.max(np.abs(actual - reference), axis=0)
        metric_errors = [abs(point(actual[:, j], development) - references[j]) for j in range(4)]
        prefix_a, prefix_b = development["a"][:128], development["b"][:128]
        prefix = scorer.score_indices(prefix_a, prefix_b)
        swap = float(np.max(np.abs(prefix - scorer.score_indices(prefix_b, prefix_a))))
        if float(errors.max()) > 1e-5 or max(metric_errors) > 1e-7 or swap > 1e-6:
            raise RuntimeError(f"{device} frozen development replay failed: scores={errors}, metrics={metric_errors}, swap={swap}")
        if not np.array_equal(prefix, scorer.score_indices(prefix_a, prefix_b)):
            raise RuntimeError("Nondeterministic frozen inference")
        if device == "cuda":
            fixture = pq.read_table(features / "public_training_fixture.parquet")
            np.save(features / "public_training_fixture_reference.npy", scorer.score(fixture), allow_pickle=False)
        replays[device] = {"rows": len(actual), "max_abs_score_errors": errors.tolist(),
                           "concordance_errors": metric_errors, "swap_max_abs": swap, "deterministic_repeat": True}
        del scorer, actual
        if device == "cuda":
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
    replay = {"passed": True, "at_utc": core.now(), "accelerator": accelerator, "replays": replays,
              "qualification_wall_seconds_including_cpu": time.monotonic() - gpu_start,
              "new_fit_or_encoder_inference": False, "protected_pairs_or_truth_accessed": False}
    authorization = project / "governance/decisions/DEC-0053-authorize-fixed-ensemble-followup.md"
    acceptance = {"execution_id": core.EXECUTION, "authorization": "DEC-0053", "recorded_at_utc": core.now(),
                  "authorization_sha256": core.sha(authorization), "accepted_for_one_followup": True,
                  "original_gate_passed": False, "original_gate_sha256": core.sha(gate_path),
                  "search_freeze_sha256": core.SEARCH_SHA, "selection_sha256": core.SELECTION_SHA,
                  "model": core.MODEL, "baseline": core.BASELINE, "development_ensemble_gain": gate["gain"],
                  "development_paired_ci95": gate["paired_gain_ci95"],
                  "amendment_after_development_before_followup_test": True,
                  "individual_seed_checks_retained_as_diagnostics": True,
                  "selection_or_checkpoint_changed": False, "protected_followup_access_started": False}
    for name, payload in (("PREACCESS_SYNTHETIC_TESTS.json", tests), ("GPU_CPU_DEVELOPMENT_REPLAY.json", replay),
                          ("ENSEMBLE_ACCEPTANCE.json", acceptance), ("HISTORICAL_INTEGRITY_BEFORE.json", historical)):
        core.write_new(provenance / name, payload)
    original_results = checked(project / "artifacts/results/protected_final_test_v1/FINAL_TEST_RESULTS.json", core.ORIGINAL_RESULT_SHA)
    shutil.copyfile(original_results, provenance / "ORIGINAL_TEST_RESULTS.json")
    prediction_freeze = checked(project / ".private/protected_final_test_v1/freeze/PREDICTION_FREEZE.json")
    original_result = core.read(original_results)
    if core.sha(prediction_freeze) != original_result["prediction_freeze_sha256"]:
        raise RuntimeError("Original prediction freeze not bound to original result")
    for source in SOURCES:
        shutil.copyfile(checked(project / source), code / Path(source).name)
    image = checked(project / "containers/images/ipin-model-arm64_0.1.0.sif", "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91")
    frozen = {"execution_id": core.EXECUTION, "model": core.MODEL, "baseline": core.BASELINE,
              "frozen_at_utc": core.now(), "scorers": list(core.SCORERS), "cells": list(core.CELLS),
              "checkpoint_sha256": list(core.CHECKPOINT_SHAS), "search_freeze_sha256": core.SEARCH_SHA,
              "selection_sha256": core.SELECTION_SHA, "original_ledger_sha256": core.ORIGINAL_LEDGER_SHA,
              "original_result_sha256": core.ORIGINAL_RESULT_SHA,
              "original_prediction_freeze_sha256": core.sha(prediction_freeze),
              "original_scorer_freeze_sha256": core.sha(old_manifest_path),
              "acceptance_sha256": core.sha(provenance / "ENSEMBLE_ACCEPTANCE.json"),
              "authorization_sha256": core.sha(authorization), "model_container_sha256": core.sha(image),
              "sealed_packages": old_manifest["sealed_packages"], "input_records": inputs,
              "source_inputs": [core.record(project / p, project) for p in SOURCES] + [core.record(source_models, project)],
              "files": [core.record(p, output) for p in sorted(output.rglob("*")) if p.is_file()],
              "protected_pairs_or_truth_accessed": False, "new_fit_or_encoder_inference": False}
    core.write_new(output / "SCORER_FREEZE.json", frozen)
    core.verify_bundle(output)
    validation = project / "artifacts/validation" / core.EXECUTION
    for name in ("PREACCESS_SYNTHETIC_TESTS.json", "GPU_CPU_DEVELOPMENT_REPLAY.json", "ENSEMBLE_ACCEPTANCE.json", "HISTORICAL_INTEGRITY_BEFORE.json"):
        core.write_new(validation / name, core.read(provenance / name))
    core.write_new(validation / "SCORER_FREEZE.json", frozen)
    for path in output.rglob("*"):
        path.chmod(0o500 if path.is_dir() else 0o400)
    output.chmod(0o500)
    print(json.dumps({"scorer_frozen": True, "scorer_freeze_sha256": core.sha(output / "SCORER_FREEZE.json"),
                      "GPU_CPU_development_replay": replays, "synthetic_tests": tests["tests_run"],
                      "prior_registered_files_unchanged": historical["registered_files"], "protected_access": False}), flush=True)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]).resolve(strict=True))
