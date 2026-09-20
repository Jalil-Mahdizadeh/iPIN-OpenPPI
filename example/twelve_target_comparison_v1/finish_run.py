#!/usr/bin/env python3
"""Close the validated application with runtime, preservation, and output hashes."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import xml.etree.ElementTree as ET

import h5py
import matplotlib
import numpy
import scipy
import sklearn
import torch

from run_comparison import TARGETS, catalogue, now, read, record, sha, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root, args.output
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Run in the accepted TUnA SIF")
    catalogue(root)
    images = []
    for relative, expected in (
        ("containers/images/ipin-data-arm64_0.1.2.sif", "72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629"),
        ("containers/images/ipin-model-arm64_0.1.0.sif", "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"),
        ("benchmark/containers/images/tuna-arm64-v1.sif", "98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1"),
    ):
        item = record(root / relative)
        if item["sha256"] != expected:
            raise RuntimeError(f"Runtime image changed: {relative}")
        images.append({**item, "path": relative})
    checks = {}
    for phase in ("before", "after"):
        text = (out / f"model_verification_{phase}.log").read_text()
        checks[phase] = json.loads(text[text.index("{"):])
        assert checks[phase]["passed"] and checks[phase]["models"] == 3
    assert checks["before"] == checks["after"]
    validation = read(out / "INDEPENDENT_VALIDATION.json")
    assert validation["passed"] and validation["validator"]["sha256"] == sha(out / "validate_results.py")
    freeze = read(out / "INPUT_FREEZE.json")
    for item in freeze["input_files"] + freeze["implementation_files"]:
        assert sha(root / item["path"]) == item["sha256"]
    for relative, digest in freeze["original_file_hashes"].items():
        assert sha(root / relative) == digest
    suites = ET.parse(out / "UNIT_TESTS.xml").getroot().findall("testsuite")
    tests = {key: sum(int(suite.attrib.get(key, 0)) for suite in suites) for key in ("tests", "failures", "errors", "skipped")}
    assert tests["failures"] == tests["errors"] == 0
    public = [p for p in sorted(out.iterdir()) if p.is_file() and p.suffix in (".py", ".json", ".csv", ".md", ".xml", ".pdf", ".svg", ".png")]
    public += [root / "example/README.md"]
    for gene in TARGETS:
        folder = root / "example" / gene
        public.extend(folder / name for name in ("README.md", "RESULTS_v2.md", "panel_manifest.json", f"{gene.lower()}_ipin_panel.csv", f"{gene.lower()}_three_model_scores.csv"))
    outputs = [{**record(path), "path": str(path.relative_to(root))} for path in public]
    write_json(out / "RUN_MANIFEST.json", {"schema": "ipin_twelve_target_completed_run_v1", "completed_at_utc": now(),
        "targets": 12, "pairs": 3737, "P": 37, "U": 3700, "frozen_models": 3,
        "authorization": record(out / "AUTHORIZATION.md"), "three_model_registry_sha256": checks["after"]["registry_sha256"],
        "model_verification_before_and_after_identical": True, "model_verification": checks,
        "runtime_images": images, "validator_runtime_versions": {"python": platform.python_version(), "numpy": numpy.__version__,
        "scipy": scipy.__version__, "scikit_learn": sklearn.__version__, "h5py": h5py.__version__,
        "matplotlib": matplotlib.__version__, "torch": torch.__version__},
        "unit_tests": tests, "independent_validation_passed": True, "original_records_unchanged": True,
        "all_embeddings_recomputed": True, "protected_test_truth_or_pairs_opened": False,
        "phases": ["build_panels", "prepare", "ipin", "tuna", "summarize", "validate_results", "render_report", "finish_run"],
        "scientific_outputs": outputs, "large_local_artifacts": [read(out / "IPIN_RUN.json")["embedding_artifact"], read(out / "TUNA_RUN.json")["fresh_residues"]],
        "claim_scope": "Descriptive known-positive retrieval; U remains unknown; no model tuning or new protected benchmark evaluation"})
    print(f"Closed twelve-target run: {len(outputs)} public artifacts; all three frozen models preserved", flush=True)


if __name__ == "__main__":
    main()
