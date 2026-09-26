"""Check real completed artifacts and the independent macro-metric oracle."""
from pathlib import Path
import numpy as np
from study_io import CELLS, SEEDS, PRIMARY, arrays, configure_cuda, now, read, sha, verify, write
from macro_metrics import qualify_macro

root = Path("/experiment")
catalogue = read(root / "CATALOGUE.json")
meta = read(root / "data/sequences.json")
checked = []
covered = {"ipin_baseline", "ipin_optimized"}
for tag in ("tuna", "rapppid_original", "rapppid_recovery", "partner"):
    directory = root / "predictions" / tag
    complete = read(directory / "COMPLETE.json")
    assert complete["bundle_sha256"] == catalogue[tag]["scorer_freeze_sha256"]
    assert not complete["test_truth_read"] and not complete["training_performed"]
    for item in complete["files"]:
        verify(directory / item["path"], item)
        cohort, cell = Path(item["path"]).stem.split("_")
        candidates = arrays(root / f"data/candidates/{cohort}_{cell}.npz")
        values = arrays(directory / item["path"])
        assert all(x.shape == candidates["a"].shape and np.isfinite(x).all() for x in values.values())
        if tag == "tuna":
            for label, member_prefix in (("selected_31k", "selected_31k_seed"), ("tuna_retrained_ensemble", "tuna_retrained_seed")):
                assert np.array_equal(values[label], np.column_stack([values[member_prefix + str(s)] for s in SEEDS]).mean(1, dtype=np.float64))
        if tag == "rapppid_recovery":
            assert np.array_equal(values["rapppid_recovery_mean_logit"], np.column_stack([values[f"rapppid_recovery_seed_{s}"] for s in SEEDS]).mean(1, dtype=np.float64))
        if tag == "partner":
            for kind in ("cross_attention", "mean_pool"):
                assert np.array_equal(values[kind + "_ensemble"], np.column_stack([values[f"{kind}_seed{s}"] for s in SEEDS]).mean(1, dtype=np.float64))
        covered.update(set(values) & set(PRIMARY))
        checked.append(str((directory / item["path"]).relative_to(root)))
for method in ("plm", "dscript_original", "dscript_retrained"):
    result = read(root / "shards" / method / "rank-000/QUALIFICATION.json")
    assert result["passed"] and max(result["archived_legacy_fixture_errors"].values()) <= result["tolerance"]
    if method.startswith("dscript"):
        directory = root / "features" / method
        complete = read(directory / "COMPLETE.json")
        assert complete["sequence_sha256"] == sha(root / "data/sequences.json")
        assert complete["bundle_sha256"] == catalogue[method]["scorer_freeze_sha256"]
        for item in complete["files"]:
            verify(directory / item["path"], item)
            array = np.load(directory / item["path"], mmap_mode="r", allow_pickle=False)
            assert array.shape == (sum(meta["length"][17000:]), 100)
            assert np.isfinite(array).all()
for cell in CELLS:
    for tag in catalogue:
        values = arrays(root / "legacy" / tag / (cell + ".npz"))
        candidates = arrays(root / f"data/candidates/legacy_{cell}.npz")
        assert all(x.shape == candidates["a"].shape and np.isfinite(x).all() for x in values.values())
metric = qualify_macro(configure_cuda())
assert metric["passed"]
write("/output/PREFLIGHT.json", {"at_utc": now(), "passed": True, "complete_primary_predictors": sorted(covered),
      "pending_primary_predictors": sorted(set(PRIMARY) - covered), "checked_new_prediction_files": checked,
      "archived_prediction_shapes_finite": True, "ensemble_arithmetic_exact": True,
      "added_DSCRIPT_feature_shapes_finite": True, "scoring_pilots_passed": True,
      "macro_metric_independent_oracle": metric, "test_truth_read": False})
print({"preflight_passed": True, "completed_primary_predictors": len(covered), "pending_primary_predictors": len(set(PRIMARY) - covered),
       "macro_metric_independent_oracle": metric}, flush=True)
