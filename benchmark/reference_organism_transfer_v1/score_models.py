"""Run unchanged qualified predictors on the frozen published reference pairs."""
import argparse
import gzip
import json
import os
from pathlib import Path

from evaluation_utils import *


def freeze():
    rows = check_selection()
    require(read(OUT / "EXPOSURE_AUDIT.json")["protected_test_pairs_or_truth_read"] is False,
            "TRAIN/development exposure audit required")
    require(read(OUT / "METRIC_SELFTEST.json")["status"] == "passed", "Metric self-test required")
    require(not any((OUT / name).exists() for name in ("ipin_scores.csv", "tuna_scores.csv", "INPUT_FREEZE.json")),
            "Freeze must precede model inference")
    registry = ROOT / "artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json"
    require(sha(registry) == REGISTRY_SHA, "Registered model identities changed")
    names = [
        "prepare.py", "acquire_comparison.py", "build_comparison.py", "evaluation_utils.py",
        "audit_exposure.py", "score_models.py", "analyze.py", "validate_results.py",
        "config.json", "PROTOCOL.md", "EVALUATION_PROTOCOL.md", "SOURCE_PREPARATION.json", "VALIDATION.json",
        "COMPARISON_SOURCES.json", "COMPARISON_VALIDATION.json", "PANEL_SELECTION.json",
        "published_pairs.csv", "published_proteins.csv", "published_evidence.json.gz", "published_sequences.json.gz",
        "panels.csv", "assay_comparison.csv", "comparison_mapping_audit.csv", "selected_sequences.json.gz",
        "EXPOSURE_AUDIT.json", "HOMOLOGY_INPUT_FREEZE.json", "exact_endpoint_exposure.csv",
        "exact_pair_exposure.csv", "training_sequence_similarity.csv", "METRIC_SELFTEST.json",
    ]
    files = [record(OUT / name) for name in names]
    dependencies = [
        "benchmark/nonhuman_transfer_v1/study_utils.py", "benchmark/nonhuman_transfer_v1/config.json",
        "benchmark/nonhuman_transfer_v1/score_models.py", "benchmark/nonhuman_transfer_v1/audit_exposure.py",
        "example/twelve_target_comparison_v2/run_comparison.py", "example/score_frozen_models.py",
        "src/ipin_openppi/stage1/embeddings.py", "artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json",
    ]
    files.extend(record(ROOT / name) for name in dependencies)
    files.extend(read(OUT / "COMPARISON_SOURCES.json")["sources"])
    with gzip.open(OUT / "selected_sequences.json.gz", "rt") as handle:
        sequences = json.load(handle)
    comparison = read(OUT / "PANEL_SELECTION.json")["comparison"]
    write_json(OUT / "INPUT_FREEZE.json", {
        "at_utc": now(), "no_model_inference_yet": True, "files": files,
        "pairs": len(rows), "unique_sequences": len(sequences), "comparison": comparison,
        "primary_endpoint": "published_assay_confirmation", "models": list(MODELS),
        "model_registry_sha256": REGISTRY_SHA, "other_reference_taxids_scored": False,
        "new_candidate_pairs_generated": False, "bootstrap_draws": 10000, "bootstrap_seed": 20260921,
        "protected_test_records_read": False,
    })
    print(f"Frozen: {len(rows):,} published pairs; {comparison['included_assay_rows']} assay outcomes", flush=True)


def score(phase):
    check_selection()
    freeze_record = read(OUT / "INPUT_FREEZE.json")
    for item in freeze_record["files"]:
        verify(item)
    require(freeze_record["primary_endpoint"] == "published_assay_confirmation", "Unexpected endpoint")
    outputs = ("ipin_scores.csv", "ipin_fresh_embeddings.npz", "IPIN_RUN.json") if phase == "ipin" else (
        "tuna_scores.csv", "TUNA_RUN.json", "TUNA_ESM_QUALIFICATION.json", "sequence_order.json")
    require(not any((OUT / name).exists() for name in outputs), "Refusing to overwrite inference outputs")
    module = qualified_module("score_models")
    if phase == "ipin":
        module.parent().ipin(ROOT, OUT)
    else:
        module.tuna()
    write_json(OUT / (phase.upper() + "_DISPATCH.json"), {
        "at_utc": now(), "input_freeze": record(OUT / "INPUT_FREEZE.json"),
        "wrapper": record(Path(__file__)), "qualified_implementation": record(ROOT / "benchmark/nonhuman_transfer_v1/score_models.py"),
        "runtime_container": os.environ["APPTAINER_CONTAINER"], "published_reference_pairs_only": True,
    })


if __name__ == "__main__":
    container()
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("freeze", "ipin", "tuna"))
    phase = parser.parse_args().phase
    freeze() if phase == "freeze" else score(phase)
