"""Close this exploratory investigation after validation and preservation checks."""
from __future__ import annotations

from datetime import datetime, timezone
import os
import platform

import numpy
import scipy
import sklearn

from investigate import ROOT, OUT, PARENT, check_inputs, parent_check, read, record, sha, write_json


def main():
    assert os.environ.get("APPTAINER_CONTAINER")
    assert not (OUT / "FINAL_MANIFEST.json").exists(), "Completed records are immutable"
    check_inputs()
    for name in ("INDEPENDENT_VALIDATION.json", "FOLLOWUP_VALIDATION.json", "GPU_DIAGNOSTICS.json", "HOMOLOGY_RUN.json"):
        assert read(OUT / name)["passed"]
    historical = read(PARENT / "INPUT_FREEZE.json")["original_file_hashes"]
    for path, digest in historical.items():
        assert sha(ROOT / path) == digest, path
    images = {
        "containers/images/ipin-data-arm64_0.1.2.sif": "72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629",
        "benchmark/containers/images/tuna-arm64-v1.sif": "98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1"}
    for path, digest in images.items():
        assert sha(ROOT / path) == digest
    for filename, keys in (("HOMOLOGY_INPUT_FREEZE.json", ("primary_freeze", "protocol", "script", "binary")),
                           ("RELATIVE_PAIR_AUDIT_INPUTS.json", ("script",)),
                           ("SUMMARY_PROVENANCE.json", ("script",))):
        data = read(OUT / filename)
        for key in keys:
            assert sha(ROOT / data[key]["path"]) == data[key]["sha256"]
        for item in data.get("inputs", []) + data.get("local_inputs", []) + data.get("ancillary_TRAIN_sources", []):
            assert sha(ROOT / item["path"]) == item["sha256"]
    outputs = [record(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.suffix in
               (".py", ".md", ".json", ".csv", ".tsv", ".png", ".pdf", ".svg")]
    write_json("FINAL_MANIFEST.json", dict(schema="original_tuna_investigation_v1",
        completed_at_utc=datetime.now(timezone.utc).isoformat(), exploratory=True,
        primary_analysis_after_parent_scores=True, homology_followup_after_initial_diagnostics=True,
        scientific_outputs=outputs, parent_scientific_artifacts_preserved=parent_check(),
        earlier_historical_artifacts_preserved=len(historical), registry_unchanged=True,
        no_model_training_or_selection=True, frozen_parameters_and_covariances_unchanged=True,
        cached_parent_residue_and_endpoint_arrays_reused=True, protected_test_records_read=False,
        models_in_query_replacement=("tuna_original", "tuna_retrained"),
        same_actual_pair_scores_reproduced_for_all_four_TUnA_members=True,
        scientific_runtime_images=images, versions=dict(python=platform.python_version(),
        numpy=numpy.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__),
        primary_metric_validation_passed=True, followup_validation_passed=True,
        interpretation="Reproducible query-dependent example strength; plausible transfer from related TRAIN protein pairs; EGFR dominates net macro lead; no causal attribution or general superiority established."))
    print(f"Closed investigation: {len(outputs)} public scientific artifacts", flush=True)


if __name__ == "__main__":
    main()
