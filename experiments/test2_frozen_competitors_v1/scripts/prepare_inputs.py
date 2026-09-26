"""Freeze existing predictors and align archived scores to immutable test2 identities."""
from pathlib import Path
import hashlib
import shutil
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from study_io import CELLS, PRIMARY, arrays, codes, now, read, record, save, sha, verify, write

REPO = Path("/repo")
OUT = Path("/output")
STUDY = REPO / "experiments/human_ppi_data_scaling_v1"
BUNDLES = {
    "dscript_original": ("dscript/runs/original-v1", "dscript/private/original-v1", "dscript-native-arm64-v1.sif"),
    "dscript_retrained": ("dscript/runs/retrained-v1", "dscript/private/retrained-v1", "dscript-native-arm64-v1.sif"),
    "plm": ("plm_interact/runs/original-v1", "plm_interact/private/original-v1", "plm-interact-native-arm64-v1.sif"),
    "rapppid_original": ("rapppid/runs/original-v1", "rapppid/private/original-v1", "rapppid-native-arm64-v1.sif"),
    "rapppid_recovery": ("rapppid/runs/recovery-test-v1", "rapppid/private/recovery-test-v1", "rapppid-native-arm64-v1.sif"),
    "sprint": ("sprint/runs/original-v1", "sprint/private/original-v1", "sprint-native-arm64-v1.sif"),
    "tuna": ("tuna/runs", "tuna/private", "tuna-arm64-v1.sif"),
    "partner": ("partner_conditioned_residue_v1/runs", "partner_conditioned_residue_v1/private", "tuna-arm64-v1.sif"),
}


def main():
    assert not (OUT / "INPUT_FREEZE.json").exists()
    inputs = {}

    def keep(path, expected=None):
        path = Path(path)
        relative = str(path.relative_to(REPO))
        if relative not in inputs:
            item = record(path, REPO)
            if expected:
                assert item["sha256"] == expected["sha256"], relative
                if "bytes" in expected:
                    assert item["bytes"] == expected["bytes"], relative
            inputs[relative] = item
        return inputs[relative]

    execution = read(STUDY / "audit/EXECUTION_FREEZE.json")
    corpus = read(STUDY / "audit/CORPUS_FREEZE.json")
    candidates = read(STUDY / "audit/CANDIDATE_FREEZE.json")
    for name in ("EXECUTION_FREEZE.json", "CORPUS_FREEZE.json", "CANDIDATE_FREEZE.json", "CORPUS_VALIDATION.json"):
        keep(STUDY / "audit" / name)
    for name in ("sequences.json", "endpoints.json", "PROTOCOL.json", "legacy/development_02.npz", "development/added/C1.npz"):
        expected = next(x for x in execution["data_files"] if x["name"] == name)
        keep(STUDY / "data" / name, expected)
    meta = read(STUDY / "data/sequences.json")
    n = len(meta["sha256"])
    assert n == 17583 and len(set(meta["sha256"])) == n
    for h, s, length in zip(meta["sha256"], meta["sequence"], meta["length"], strict=True):
        assert hashlib.sha256(s.encode()).hexdigest() == h and len(s) == length
    (OUT / "data").mkdir(exist_ok=True)
    shutil.copyfile(STUDY / "data/sequences.json", OUT / "data/sequences.json")
    shutil.copyfile(STUDY / "data/endpoints.json", OUT / "data/endpoints.json")
    census = {}
    for item in candidates["files"]:
        path = STUDY / "private/candidates" / item["name"]
        keep(path, item)
        data = arrays(path)
        assert set(data) == {"a", "b"} and len(data["a"]) == len(data["b"])
        assert all(((data[k] >= 0) & (data[k] < n)).all() for k in data)
        (OUT / "data/candidates").mkdir(exist_ok=True)
        shutil.copyfile(path, OUT / "data/candidates" / item["name"])
        census[Path(item["name"]).stem] = {"rows": len(data["a"]), "endpoints": len(np.unique(np.r_[data["a"], data["b"]]))}
    for item in corpus["test_files"]:
        keep(STUDY / item["path"], item)
    selection = read(STUDY / "runs/SELECTION.json")
    assert selection["selected"]["budget"] == 31188 and selection["selected"]["epoch"] == 1
    for name in ("SELECTION.json", "SCORER_FREEZE.json", "PREDICTION_FREEZE.json"):
        keep(STUDY / "runs" / name)
    selected_freeze = read(STUDY / "runs/SCORER_FREEZE.json")
    for member in selected_freeze["members"]:
        if member["name"].startswith(("scaled_31188_", "baseline_")):
            for key in ("weights", "features"):
                keep(STUDY / "runs" / member[key]["path"], member[key])
    prediction_freeze = read(STUDY / "runs/PREDICTION_FREEZE.json")
    for cell in CELLS:
        for cohort in ("legacy", "added"):
            rel = f"predictions/test_{cohort}_{cell}.npz"
            entry = next(x["prediction"] for x in prediction_freeze["files"] if x["prediction"]["path"] == rel)
            keep(STUDY / "runs" / rel, entry)
            scores = arrays(STUDY / "runs" / rel)
            save(OUT / "predictions/ipin" / f"{cohort}_{cell}.npz",
                 ipin_baseline=scores["ipin_original"], ipin_optimized=scores["ipin_optimized"])
    cache = read(STUDY / "runs/residue_cache/RESIDUE_CACHE_MANIFEST.json")
    keep(STUDY / "runs/residue_cache/RESIDUE_CACHE_MANIFEST.json")
    keep(STUDY / "runs/residue_cache/residues.h5", cache["cache"])
    assert cache["sequences_sha256"] == sha(STUDY / "data/sequences.json")
    # One historical candidate mapping is shared byte-for-byte across methods.
    session = REPO / "benchmark/tuna/private/session"
    session_manifest = read(session / "SESSION.json")
    keep(session / "SESSION.json")
    identities, orders, fixture_parts = {}, {}, []
    for cell in CELLS:
        item = next(x for x in session_manifest["files"] if x["cell"] == cell + "_test")
        keep(session / item["path"], item)
        tab = pq.read_table(session / item["path"])
        ids = pa.array(meta["sha256"])
        aa = pc.index_in(tab["endpoint_a_sha256"], value_set=ids)
        bb = pc.index_in(tab["endpoint_b_sha256"], value_set=ids)
        assert not aa.null_count and not bb.null_count
        code = codes(aa.to_numpy(), bb.to_numpy(), n)
        order = np.argsort(code, kind="stable")
        assert len(np.unique(code)) == len(code)
        target = arrays(OUT / "data/candidates" / f"legacy_{cell}.npz")
        expected = codes(target["a"], target["b"], n)
        lookup = np.searchsorted(code[order], expected)
        assert (lookup < len(code)).all() and np.array_equal(code[order][lookup], expected)
        orders[cell] = order[lookup]
        identities[cell] = tab["candidate_token"]
        indices = np.unique(np.linspace(0, len(expected) - 1, 24, dtype=int))
        fixture_parts.append((cell, indices, target["a"][indices], target["b"][indices]))
    save(OUT / "data/fixtures.npz", a=np.concatenate([x[2] for x in fixture_parts]), b=np.concatenate([x[3] for x in fixture_parts]))
    catalogue = {}
    for tag, (run, private, image) in BUNDLES.items():
        print("Verifying frozen comparator", tag, flush=True)
        bundle = REPO / "benchmark" / run / "scorer_bundle"
        frozen = read(bundle / "SCORER_FREEZE.json")
        keep(bundle / "SCORER_FREEZE.json")
        assert read(bundle / "endpoints.json") == meta["sha256"][:17000]
        for item in frozen["files"]:
            keep(bundle / item["path"], item)
        image_path = REPO / "benchmark/containers/images" / image
        expected = {"sha256": frozen["sif_sha256"]} if "sif_sha256" in frozen else execution["container"]
        keep(image_path, expected)
        old_root = REPO / "benchmark" / private
        archived = read(old_root / "predictions/PREDICTIONS.json")
        keep(old_root / "predictions/PREDICTIONS.json")
        assert archived["scorer_freeze_sha256"] == sha(bundle / "SCORER_FREEZE.json")
        old_session = read(old_root / "session/SESSION.json")
        keep(old_root / "session/SESSION.json")
        assert archived["session_sha256"] == sha(old_root / "session/SESSION.json")
        names = frozen["scorers"]
        fixtures = {name: [] for name in names}
        for cell, indices, _, _ in fixture_parts:
            p = next(x for x in archived["files"] if x["cell"] == cell + "_test")
            keep(old_root / "predictions" / p["path"], p)
            old_id = next(x for x in old_session["files"] if x["cell"] == cell + "_test")
            ref_id = next(x for x in session_manifest["files"] if x["cell"] == cell + "_test")
            assert old_id["sha256"] == ref_id["sha256"]
            table = pq.read_table(old_root / "predictions" / p["path"])
            assert table["candidate_token"].equals(identities[cell])
            values = {name: table[name].to_numpy()[orders[cell]].astype(np.float64) for name in names}
            assert all(np.isfinite(v).all() for v in values.values())
            save(OUT / "legacy" / tag / f"{cell}.npz", **values)
            for name in names:
                fixtures[name].append(values[name][indices])
        save(OUT / "data" / f"fixtures_{tag}.npz", **{name: np.concatenate(v) for name, v in fixtures.items()})
        catalogue[tag] = {"bundle": str(bundle.relative_to(REPO)), "private": str(old_root.relative_to(REPO)),
                          "image": str(image_path.relative_to(REPO)), "scorers": names,
                          "scorer_freeze_sha256": sha(bundle / "SCORER_FREEZE.json")}
    # Preserve qualified metric and model adapter sources as read-only references.
    for folder in (REPO / "benchmark/tuna/scripts", STUDY / "scripts"):
        for name in (("adapter.py", "training.py", "common.py", "gpu_guard.py", "benchmark_metrics.py") if folder.name == "scripts" and folder.parent.name == "tuna" else ("macro_metrics.py", "study.py")):
            keep(folder / name)
    write(OUT / "CATALOGUE.json", catalogue)
    write(OUT / "PROTOCOL.json", {"at_utc": now(), "primary_models": list(PRIMARY), "test_cells": list(CELLS),
        "primary_cell": "C3", "primary_metric": "0.5 weighted P/U concordance on reconciled legacy + 0.5 on added test cohort",
        "bootstrap_replicates": 2000, "paired_component_bootstrap": "Use the frozen scaling study component graph and deterministic draws, shared across all models",
        "C1_sensitivity": "Remove every legacy or added C1 development candidate identity, without altering the complete requested test2",
        "no_training_or_model_selection": True, "selected": {"budget": 31188, "epoch": 1, "seeds": [x["seed"] for x in selection["selected"]["members"]]},
        "tuna_covariance": "Preserve exact saved GP covariance: set fitted before eval; do not reproduce the historical reload-order drift",
        "legacy_predictions": "Reuse verified, identity-aligned archived scores; recompute selected/frozen PU-TUnA with exact covariance",
        "sprint": "Unchanged native algorithm and 16,799-P graph; recompute transductive HSP preprocessing on all 17,583 frozen sequences and score both cohorts",
        "test2_is_fresh_independent": False, "U_is_confirmed_negative": False,
        "excluded_planning_only_methods": ["Topsy-Turvy", "TT3D", "PIPR", "PPITrans", "PPLM", "MINT"],
        "development_only_unpromoted_recipes": ["attention_pool", "cross_attention_wide"], "candidates": census})
    write(OUT / "INPUT_FREEZE.json", {"at_utc": now(), "files": list(inputs.values()), "historical_files_modified": False,
        "candidate_identity_alignment_verified": True, "sequence_prefix_17000_preserved": True, "new_sequence_endpoints": 583})
    print({"prepared": True, "predictors": len(PRIMARY), "candidate_counts": census, "frozen_inputs": len(inputs)}, flush=True)


if __name__ == "__main__":
    main()
