#!/usr/bin/env python3
"""Close the versioned application after validation, figures and preservation."""
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

from run_comparison import TARGETS, catalogue, inputs, now, read, record, sha, write_json

HERE = Path(__file__).resolve().parent


def main():
    assert os.environ.get("APPTAINER_CONTAINER")
    root, out = HERE.parents[1], HERE
    catalogue(root)
    rows, snapshot, order, sequences = inputs(root, out)
    before, after = (read(out / f"MODEL_VERIFICATION_{phase}.json") for phase in ("BEFORE", "AFTER"))
    assert before == after and after["passed"] and after["models"] == 3
    validation = read(out / "INDEPENDENT_VALIDATION.json")
    assert validation["passed"] and validation["validator"]["sha256"] == sha(out / "validate_results.py")
    evidence = read(out / "EVIDENCE_VALIDATION.json")
    assert evidence["passed"] and evidence["validator"]["sha256"] == sha(out / "validate_evidence.py")
    images = []
    for relative, expected in (
        ("containers/images/ipin-data-arm64_0.1.2.sif", "72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629"),
        ("containers/images/ipin-model-arm64_0.1.0.sif", "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"),
        ("benchmark/containers/images/tuna-arm64-v1.sif", "98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1"),
    ):
        item = record(root / relative)
        assert item["sha256"] == expected
        images.append({**item, "path": relative})
    tests = {}
    for name in ("UNIT_TESTS.xml", "APPLICATION_TESTS.xml"):
        suites = ET.parse(out / name).getroot().findall("testsuite")
        result = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
        assert result["errors"] == result["failures"] == 0
        tests[name] = result
    plan = read(out / "INPUT_FREEZE.json")
    for relative, digest in plan["original_file_hashes"].items():
        assert sha(root / relative) == digest
    public = [p for p in sorted(out.iterdir()) if p.is_file() and p.suffix in (".py", ".json", ".csv", ".md", ".xml", ".png", ".pdf", ".svg")]
    public += sorted((out / "panels").rglob("*.json")) + sorted((out / "panels").rglob("*.csv"))
    public += [root / "example" / g / "RESULTS_v3.md" for g in TARGETS]
    outputs = [{**record(p), "path": str(p.relative_to(root))} for p in public]
    write_json(out / "RUN_MANIFEST.json", {
        "schema": "ipin_twelve_target_completed_run_v2", "completed_at_utc": now(),
        "targets": 12, "pairs": 5587, "P": 37, "U": 5550, "U_per_positive_per_stratum": 50,
        "context_U": 1850, "background_U": 1850, "low_plausibility_U": 1850,
        "frozen_ipin_models": 3, "additional_original_tuna_comparator": True, "model_level_scores": 22348,
        "new_U_tier_A": 1711, "new_U_tier_B_EGFR": 139,
        "three_model_registry_sha256": after["registry_sha256"],
        "model_verification_before_after_identical": True, "model_verification": {"before": before, "after": after},
        "runtime_images": images, "runtime_versions": {"python": platform.python_version(), "numpy": numpy.__version__,
            "scipy": scipy.__version__, "scikit_learn": sklearn.__version__, "h5py": h5py.__version__,
            "matplotlib": matplotlib.__version__, "torch": torch.__version__},
        "tests": tests, "independent_validation_passed": True,
        "original_artifacts_preserved": len(plan["original_file_hashes"]),
        "all_embeddings_recomputed": True, "unique_sequences": len(order),
        "protected_test_truth_or_pairs_read": False, "new_training_or_model_selection": False,
        "scientific_outputs": outputs,
        "large_local_artifacts": [read(out / "IPIN_RUN.json")["embedding_artifact"], read(out / "TUNA_RUN.json")["fresh_residues"]],
        "claim_scope": "Descriptive known-positive retrieval on deliberately different unlabeled candidate sets; evidence tiers are not negative labels."})
    print(f"Completed run closed: {len(outputs)} public artifacts, {len(plan['original_file_hashes'])} historical artifacts preserved", flush=True)


if __name__ == "__main__":
    main()
