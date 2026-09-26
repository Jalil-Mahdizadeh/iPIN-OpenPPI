"""Verify historical provenance and freeze this run's read-only dependencies."""
from pathlib import Path
import subprocess
from panel_io import now, read, sha, write_json

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
PANEL = ROOT / "example/twelve_target_comparison_v2"
STUDY = ROOT / "experiments/human_ppi_data_scaling_v1"


def main():
    if (OUT / "INPUT_FREEZE.json").exists():
        raise RuntimeError("This run is already frozen; refusing to overwrite")
    historical = read(PANEL / "RUN_MANIFEST.json")
    expected_panel = {Path(x["path"]).name: x for x in historical["scientific_outputs"]}
    expected_panel.update({Path(x["path"]).name: x for x in historical["large_local_artifacts"]})
    selected = read(STUDY / "runs/SELECTION.json")["selected"]
    assert selected["budget"] == 31188 and selected["epoch"] == 1
    execution = read(STUDY / "audit/EXECUTION_FREEZE.json")
    scorer = read(STUDY / "runs/SCORER_FREEZE.json")
    assert sha(STUDY / "audit/EXECUTION_FREEZE.json") == scorer["execution_sha256"]
    assert sha(STUDY / "runs/SELECTION.json") == scorer["selection_sha256"]
    inputs = []

    def add(path, mount, relative, expected=None):
        item = {"path": str(path.relative_to(ROOT)), "mount": mount,
                "relative_path": str(relative), "bytes": path.stat().st_size, "sha256": sha(path)}
        if expected is not None:
            assert item["sha256"] == expected["sha256"], str(path)
            if "bytes" in expected:
                assert item["bytes"] == expected["bytes"], str(path)
        inputs.append(item)

    panel_names = ["pairs.json", "uniprot_sequences.json", "sequence_order.json",
        "all_twelve_targets_scores.csv", "ipin_scores.csv", "tuna_scores.csv",
        "per_target_metrics.csv", "macro_metrics.csv", "positive_partner_ranks.csv",
        "metrics.py", "analysis_outputs.py", "run_comparison.py", "panel_config.json",
        "METRICS.md", "REPORT.md", "TUNA_RUN.json", "IPIN_RUN.json",
        "INPUT_FREEZE.json", "RUN_MANIFEST.json", "tuna_fresh_residues.h5"]
    for name in panel_names:
        add(PANEL / name, "panel", name, expected_panel.get(name))
    for name in ["SELECTION.json", "SCORER_FREEZE.json"]:
        add(STUDY / "runs" / name, "model", name)
    add(STUDY / "audit/EXECUTION_FREEZE.json", "audit", "EXECUTION_FREEZE.json")
    for member in selected["members"]:
        seed = member["seed"]
        entry = next(x for x in scorer["members"] if x["name"] == f"scaled_31188_seed{seed}")
        assert entry["weights"]["sha256"] == member["checkpoint"]["sha256"]
        add(STUDY / "runs" / entry["weights"]["path"], "model", entry["weights"]["path"], entry["weights"])
    for name in ["adapter.py", "common.py", "training.py", "gpu_guard.py"]:
        expected = next(x for x in execution["native_code"] if x["name"] == name)
        add(ROOT / "benchmark/tuna/scripts" / name, "native", name, expected)
    upstream = ROOT / "benchmark/tuna/upstream/TUnA"
    for item in execution["upstream_code"]:
        if item["name"].startswith("results/bernett/TUnA/"):
            add(upstream / item["name"], "upstream", item["name"], item)
    data_names = ["endpoints.json", "sequences.json", "training_16799.npz", "training_31188.npz",
                  "training_unlabeled.npz", "development/reconciled/C3.npz", "development/added/C3.npz"]
    for name in data_names:
        expected = next(x for x in execution["data_files"] if x["name"] == name)
        add(STUDY / "data" / name, "studydata", name, expected)
    add(ROOT / execution["container"]["path"], "runtime", "tuna.sif", execution["container"])
    for path in sorted((OUT / "scripts").glob("*.py")):
        add(path, "code", path.name)
    add(OUT / "run.sh", "launch", "run.sh")
    baseline = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=no"], cwd=ROOT, text=True)
    (OUT / "output").mkdir()
    write_json(OUT / "INPUT_FREEZE.json", {
        "at_utc": now(), "source_panel": "example/twelve_target_comparison_v2",
        "selected_budget": 31188, "selected_epoch": 1,
        "seeds": [x["seed"] for x in selected["members"]],
        "pair_count": 5587, "P": 37, "U": 5550, "unique_sequences": 4012,
        "embeddings": "Reuse verified historical full-length FP32 ESM residue embeddings; recompute learned endpoint features",
        "scoring": "Mean of three seed mean-field-adjusted logits; exact saved GP covariance",
        "model_selection_or_training": False, "panel_pairs_or_labels_changed": False,
        "old_predictors": "Archived scores, verified and re-evaluated with the original metric code",
        "inputs": inputs, "tracked_status_before": baseline,
    })
    print(f"Frozen {len(inputs)} inputs for 31,188-P epoch-1 panel inference", flush=True)


if __name__ == "__main__":
    main()
