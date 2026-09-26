"""Preserve selected 31k TUnA and designate the primary human iPIN predictor.

Creation copies the already selected states and aggregate evidence. Verification
is read-only. Neither mode trains, selects, opens pair/truth data, or reruns a
benchmark. Real-state qualification uses synthetic residue inputs on CPU only.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import numpy as np
import torch

_spec = importlib.util.spec_from_file_location("freeze_v2", Path(__file__).with_name("freeze_pair_models_v2.py"))
v2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v2)
v1 = v2.v1

RELEASE = "frozen_pair_models_v3"
PRIMARY = "ipin_tuna_31k_ensemble"
DISPLAY = "iPIN-TUnA-31k"
SEEDS = v2.SEEDS
PUBLIC = f"artifacts/models/{RELEASE}"
BUNDLE = f".private/{RELEASE}/bundle"
VALIDATION = f"artifacts/validation/{RELEASE}"
STUDY = "experiments/human_ppi_data_scaling_v1"
COMPARISON = "experiments/test2_frozen_competitors_v1"
PANEL = "experiments/twelve_target_selected_31k_v1"
ALIASES = {"iPIN-TUnA-31k": PRIMARY, "ipin-tuna-31k": PRIMARY, "selected_31k": PRIMARY}
ROLES = {**v2.ROLES, "primary_model": PRIMARY, "default_model": PRIMARY}
PINS = {
    "previous_registry": (f"{v2.PUBLIC}/MODEL_REGISTRY.json", "faf2d585dbfee34ca3fe19487bc7a821f744014cdcdb94e95e4b657097110878"),
    "previous_artifact_registry": (f"{v2.PUBLIC}/ARTIFACT_REGISTRY.json", "856fe77d881ebc2f2a2eb75f420ca0e29b78ba1ce8b28a36e59f231b076648be"),
    "selection": (f"{STUDY}/runs/SELECTION.json", "3a2b76cf605c94263b9141410c054b5aa79b34a416fcfe7bd784a370338c4f36"),
    "scorer_freeze": (f"{STUDY}/runs/SCORER_FREEZE.json", "8e8704f77eecca395f2d7cea24931a19c2d573255339a6b51be7865366aad48d"),
    "execution_freeze": (f"{STUDY}/audit/EXECUTION_FREEZE.json", "be67d329b7efa320b2149294cffaa922ea20415c034f1ba5ffcb1007f418bec2"),
    "corpus_freeze": (f"{STUDY}/audit/CORPUS_FREEZE.json", "808e86b4e067dd83392f150e834bd5bc72d96e359cde706c4f5082630ae69f6b"),
    "sequences": (f"{STUDY}/data/sequences.json", "258e5144efc210a27205ee08fdb107a3930ceca108b65bd581f94c956a7325c6"),
    "residue_manifest": (f"{STUDY}/runs/residue_cache/RESIDUE_CACHE_MANIFEST.json", "14406efa758fc0504c8cc11797d4f62c1e4ec5138e475f7153f82ca2a988e0be"),
    "covariance_replay": (f"{STUDY}/audit/SCORER_REPLAY_REVIEW.json", "947cecec88005c825fa64f28bdee90584fee2a80acccc1b0f308ebaee1d3c20f"),
    "results": (f"{COMPARISON}/results/RESULTS.json", "dc9945534fcf2da625c40d59a4b5da1f1a86867920bed5e2bd87423b39afc914"),
    "prediction_freeze": (f"{COMPARISON}/results/PREDICTION_FREEZE.json", "d0298fa647e15e9605d004cf6b011100eab89df32e8a9570244a617bf034daed"),
    "protocol": (f"{COMPARISON}/PROTOCOL.json", "ed2311cc4a0e884d91945c01538b2e927c6ff241ad972dbe3266973f4ae1229c"),
    "preservation": (f"{COMPARISON}/PRESERVATION.json", "6c801df38aaea913740ffa0d197d161242ccde18456a9b878eedd2f0cfa0b8e7"),
    "scoring_completion": (f"{COMPARISON}/predictions/tuna/COMPLETE.json", "bd4cc15afd26b9eb3ba2bbd3572340d37aae782747fe4dbd6275dc9c614efc68"),
}
RELEASE_SOURCES = (
    "scripts/model/freeze_pair_models_v3.py", "tests/unit/test_frozen_pair_models_v3.py",
    "docs/models/FROZEN_PAIR_MODELS_v3.md", "docs/reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md",
    "governance/PROJECT_STATUS_v56.md", "governance/gates/gate_status_v56.yaml",
    "governance/decisions/DEC-0056-designate-ipin-tuna-31k-primary-model.md",
)


def inputs(project: Path) -> tuple[dict, dict, dict]:
    records = {k: v2.pinned(project, p, h) for k, (p, h) in PINS.items()}
    docs = {k: v1.read(project / r["path"]) for k, r in records.items()}
    prior = v2.verify_release(project)
    selection, freeze = docs["selection"], docs["scorer_freeze"]
    selected = selection["selected"]
    if (selected["budget"], selected["epoch"], [m["seed"] for m in selected["members"]]) != (31188, 1, list(SEEDS)):
        raise RuntimeError("Selected 31k checkpoint identity drift")
    if (freeze["selection_sha256"] != records["selection"]["sha256"]
            or selection["execution_sha256"] != records["execution_freeze"]["sha256"]
            or freeze["execution_sha256"] != records["execution_freeze"]["sha256"]
            or freeze["baseline_registry_sha256"] != records["previous_registry"]["sha256"]
            or any(x[k] for x in (selection, freeze) for k in ("test_pairs_read", "test_truth_read"))):
        raise RuntimeError("Development selection/scorer provenance drift")
    sources = {m["name"]: m for m in freeze["members"]}
    for member in selected["members"]:
        original = sources[f"scaled_31188_seed{member['seed']}"]
        if original["seed"] != member["seed"] or original["weights"]["sha256"] != member["checkpoint"]["sha256"]:
            raise RuntimeError("Training checkpoint and frozen state mismatch")
        for item in (original["weights"], original["features"], member["checkpoint"]):
            v1.checked_path(project / STUDY / "runs", item)
    if len(docs["sequences"]["sha256"]) != 17583:
        raise RuntimeError("Endpoint universe drift")
    if docs["sequences"]["sha256"][:17000] != v1.read(project / v2.BUNDLE / "endpoints.json"):
        raise RuntimeError("Legacy endpoint ordering drift")
    replay, result, prediction = docs["covariance_replay"], docs["results"], docs["prediction_freeze"]
    checks = docs["scoring_completion"]["checks"]
    if (not replay["exact_saved_covariance_retained"] or replay["training_performed"]
            or replay["selection_sha256"] != records["selection"]["sha256"]
            or not checks["exact_saved_covariance_preserved"] or not checks["parameters_and_buffers_unchanged"]
            or (checks["selected_budget"], checks["selected_epoch"]) != (31188, 1)
            or result["prediction_freeze_sha256"] != records["prediction_freeze"]["sha256"]
            or result["test2_is_fresh_independent"] or result["new_training_or_model_selection"]
            or prediction["protocol_sha256"] != records["protocol"]["sha256"]
            or not prediction["complete_finite_candidate_coverage"]
            or sum(x["rows"] for x in prediction["files"]) != 3774966
            or not docs["preservation"]["passed"]
            or docs["preservation"]["results_sha256"] != records["results"]["sha256"]):
        raise RuntimeError("Completed evaluation/covariance provenance drift")
    return records, docs, prior


def validate_registry(registry: dict, previous: dict) -> None:
    if (registry["release_id"] != RELEASE or registry["primary_model"] != PRIMARY
            or registry["default_model"] != PRIMARY or registry["roles"] != ROLES
            or registry["model_order"] != previous["model_order"] + [PRIMARY]
            or set(registry["models"]) != set(previous["models"]) | {PRIMARY}
            or registry["aliases"] != {**previous["aliases"], **ALIASES}):
        raise RuntimeError("Primary model identity/role drift")
    for name in previous["model_order"]:
        if (registry["models"][name] != previous["models"][name]
                or registry["model_bundles"][name] != previous["model_bundles"][name]):
            raise RuntimeError("Historical frozen model changed")
    model = registry["models"][PRIMARY]
    required = {
        "display_name": DISPLAY, "status": "frozen", "training_positive_pairs": 31188,
        "selected_epoch": 1, "seeds": list(SEEDS), "member_weights": [1, 1, 1], "weight_divisor": 3,
        "aggregation": v2.AGGREGATION, "sigmoid_applied": False, "gp_covariance_refitted": False,
        "gp_fitted_before_eval": True, "update_precision": False, "training_normalizer_used": False,
        "benchmark_result_id": "selected_31k", "endpoint_feature_shape": [17583, 64],
    }
    if any(model.get(k) != value for k, value in required.items()) or registry["model_bundles"][PRIMARY] != BUNDLE:
        raise RuntimeError("Primary prediction definition drift")
    if [m["seed"] for m in model["members"]] != list(SEEDS):
        raise RuntimeError("Primary seed membership/order drift")
    claims = registry["claims"]
    if (not claims["best_observed_test2_macro_C1_C2_C3"] or not claims["pointwise_C3_intervals_above_zero"]
            or not claims["previously_examined_test"] or not claims["PLM_interact_higher_on_added_C3"]
            or any(claims[k] for k in ("independent_replication", "multiplicity_adjusted_intervals",
                                      "universal_superiority", "calibrated_binding_probability",
                                      "direct_binding_or_partner_specific_generalization_established",
                                      "TUnA_architecture_is_original_iPIN_work"))
            or any(registry[k] for k in ("new_training_or_benchmark_scoring", "test_truth_or_pairs_accessed_for_release",
                                        "weights_publicly_redistributed"))):
        raise RuntimeError("Promotion scope/claim drift")


def validate_members(model: dict, freeze: dict, selection: dict) -> None:
    sources = {m["name"]: m for m in freeze["members"]}
    selected = {m["seed"]: m for m in selection["selected"]["members"]}
    for member in model["members"]:
        seed = member["seed"]
        original = sources[f"scaled_31188_seed{seed}"]
        for key, source_key, folder, suffix in (("state", "weights", "weights", "pt"),
                                               ("endpoint_features", "features", "features", "npy")):
            expected = {**original[source_key], "path": f"{folder}/ipin_tuna_31k_seed{seed}.{suffix}"}
            if member[key] != expected:
                raise RuntimeError("Primary member differs from selected scorer freeze")
        checkpoint = {**selected[seed]["checkpoint"], "path": f"{STUDY}/runs/{selected[seed]['checkpoint']['path']}"}
        if member["training_checkpoint"] != checkpoint or member["state"]["sha256"] != checkpoint["sha256"]:
            raise RuntimeError("Primary training checkpoint drift")


def qualify_states(project: Path, bundle: Path, docs: dict) -> dict:
    """Compare native and cached inference, symmetry and state on synthetic data."""
    sys.path.insert(0, str(bundle / "code"))
    os.environ["TUNA_UPSTREAM_DIR"] = str(bundle / "upstream/TUnA/results/bernett/TUnA")
    spec = importlib.util.spec_from_file_location("primary_tuna_adapter", bundle / "code/adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    import uncertaintyAwareDeepLearn
    vendor = Path(uncertaintyAwareDeepLearn.__file__).parent
    for name in ("__init__.py", "classic_rffs.py"):
        if v1.sha(vendor / name) != v2.UPSTREAM[f"uncertaintyAwareDeepLearn/uncertaintyAwareDeepLearn/{name}"]:
            raise RuntimeError("Container GP implementation drift")
    torch.set_num_threads(2)
    generator = torch.Generator().manual_seed(20260926)
    lengths = [3, 5, 7]
    residues = [torch.randn(n, 640, generator=generator) * .1 for n in lengths]
    padded = torch.zeros(3, 7, 640)
    for i, x in enumerate(residues):
        padded[i, :len(x)] = x
    reports, scores = [], []
    for seed in SEEDS:
        path = bundle / f"weights/ipin_tuna_31k_seed{seed}.pt"
        state = torch.load(path, map_location="cpu", weights_only=True)
        if any(t.dtype != torch.float32 or not torch.isfinite(t).all() for t in state.values()):
            raise RuntimeError("Invalid checkpoint precision/values")
        if any(state[k].shape != (4096, 4096) for k in ("gp_layer.covariance", "gp_layer.precision")):
            raise RuntimeError("Invalid GP state")
        model = adapter.create(seed=seed, checkpoint=path, device="cpu")
        adapter.enable_sdpa(model)
        model.gp_layer.fitted = True
        model.eval().requires_grad_(False)
        with torch.inference_mode():
            z = adapter.endpoint_features(model, padded, lengths)
            actual = adapter.cached_scores(model, z, [0, 1, 2], [1, 2, 0])
            reverse = adapter.cached_scores(model, z, [1, 2, 0], [0, 1, 2])
            # The authors' native_scores helper applies sigmoid. This preserved
            # PU predictor averages adjusted logits, so compare that exact scale.
            expected = []
            for left, right in ((0, 1), (1, 2), (2, 0)):
                packed = adapter.native.test_pack([residues[left]], [residues[right]], [0], 512, 640, model.device)
                logit, variance = model.forward(packed[0], packed[1], packed[3], packed[4], packed[5], packed[6], True, False)
                expected.append(float((logit.reshape(-1) / torch.sqrt(1 + np.pi / 8 * variance)).item()))
        error = float(np.max(np.abs(actual.astype(np.float64) - expected)))
        if error > 1e-5 or not np.array_equal(actual, reverse):
            raise RuntimeError(f"Synthetic native/cached inference mismatch: max_error={error}, symmetric={np.array_equal(actual, reverse)}")
        if any(not torch.equal(value, state[k]) for k, value in model.state_dict().items()):
            raise RuntimeError("Synthetic inference changed parameters or GP buffers")
        features = np.load(bundle / f"features/ipin_tuna_31k_seed{seed}.npy", allow_pickle=False)
        if features.shape != (17583, 64) or features.dtype != np.float32 or not np.isfinite(features).all():
            raise RuntimeError("Invalid preserved endpoint features")
        scores.append(actual.astype(np.float64))
        reports.append({"seed": seed, "native_max_absolute_error": error, "pair_order_symmetry": True,
                        "parameters_and_buffers_unchanged": True, "parameters_per_head": sum(p.numel() for p in model.parameters())})
    if not np.isfinite(np.column_stack(scores).mean(1, dtype=np.float64)).all():
        raise RuntimeError("Invalid ensemble scores")
    return {"passed": True, "device": "cpu", "torch": torch.__version__, "members": reports,
            "fixture": "Synthetic residue arrays of lengths 3, 5, 7; three synthetic pairs", "absolute_tolerance": 1e-5,
            "exact_saved_covariance_retained": True, "encoder_inference": False, "benchmark_pairs_or_truth_read": False}


def create(project: Path) -> dict:
    if (project / BUNDLE).exists() or (project / PUBLIC).exists():
        raise FileExistsError("Release already exists; verify it, never overwrite it")
    records, docs, prior_audit = inputs(project)
    runtime = v2.pinned(project, v2.SIF, v2.SIF_SHA)
    suites = list(ET.parse(project / VALIDATION / "UNIT_TESTS.xml").getroot().iter("testsuite"))
    summary = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    if summary["failures"] or summary["errors"] or summary["tests"] <= summary["skipped"]:
        raise RuntimeError("Passing synthetic unit tests required")
    bundle = project / BUNDLE
    bundle.mkdir(parents=True, exist_ok=False)
    files = []

    def preserve(source, destination):
        item = v1.copy_checked(project, bundle, source, destination)
        files.append(item)
        return {k: item[k] for k in ("path", "bytes", "sha256")}

    inventory = {m["name"]: m for m in docs["scorer_freeze"]["members"]}
    members = []
    for selected in docs["selection"]["selected"]["members"]:
        seed = selected["seed"]
        original = inventory[f"scaled_31188_seed{seed}"]
        member = {"seed": seed}
        for key, source_key, folder, suffix in (("state", "weights", "weights", "pt"),
                                               ("endpoint_features", "features", "features", "npy")):
            source = {**original[source_key], "path": f"{STUDY}/runs/{original[source_key]['path']}"}
            member[key] = preserve(source, f"{folder}/ipin_tuna_31k_seed{seed}.{suffix}")
        member["training_checkpoint"] = {**selected["checkpoint"], "path": f"{STUDY}/runs/{selected['checkpoint']['path']}"}
        members.append(member)
    preserve(records["sequences"], "sequences.json")
    for key, item in records.items():
        if key != "sequences":
            preserve(item, f"provenance/{key}.json")
    # Preserve exact native code used in the scaling run, including SDPA setup.
    native_inventory = {x["name"]: x["sha256"] for x in docs["execution_freeze"]["native_code"]}
    for name in ("adapter.py", "common.py", "esm_cache.py", "training.py"):
        preserve(v2.pinned(project, f"benchmark/tuna/scripts/{name}", native_inventory[name]), f"code/{name}")
    for relative, digest in v2.UPSTREAM.items():
        preserve(v2.pinned(project, f"benchmark/tuna/upstream/{relative}", digest), f"upstream/{relative}")
    qualification = qualify_states(project, bundle, docs)
    evidence = []
    public = project / PUBLIC
    # Aggregate-only evidence; endpoint identities, feature arrays and score rows stay local.
    for key in ("selection", "scorer_freeze", "execution_freeze", "corpus_freeze", "residue_manifest", "covariance_replay"):
        evidence.append(v1.copy_checked(project, public, records[key], f"evidence/scaling/{key}.json"))
    for key in ("results", "prediction_freeze", "protocol", "preservation", "scoring_completion"):
        evidence.append(v1.copy_checked(project, public, records[key], f"evidence/test2/{key}.json"))
    for name in ("RESULTS.md", "scores.csv", "paired_differences.csv", "cohort_scores.csv", "member_scores.csv",
                 "C3_comparison.png", "C3_comparison.pdf"):
        evidence.append(v1.copy_checked(project, public, v1.record(project / COMPARISON / "results" / name, project), f"evidence/test2/{name}"))
    for name in ("REPORT.md", "primary_comparison.csv", "VALIDATION.json", "EXPOSURE_AUDIT.json"):
        evidence.append(v1.copy_checked(project, public, v1.record(project / PANEL / "output" / name, project), f"evidence/twelve_targets/{name}"))
    previous = docs["previous_registry"]
    old_tuna = previous["models"][v2.THIRD]
    model = {k: copy.deepcopy(old_tuna[k]) for k in (
        "architecture_origin", "architecture", "member_score", "precision", "input_pipeline", "encoder",
        "encoder_bundle_path", "encoder_weights_sha256", "upstream_commit", "gp_commit")}
    model.update({
        "display_name": DISPLAY, "status": "frozen", "training_positive_pairs": 31188,
        "selected_epoch": 1, "seeds": list(SEEDS), "members": members, "member_weights": [1, 1, 1], "weight_divisor": 3,
        "aggregation": v2.AGGREGATION, "sigmoid_applied": False, "gp_covariance_refitted": False,
        "gp_fitted_before_eval": True, "update_precision": False, "training_normalizer_used": False,
        "inference_mode": "Set gp_layer.fitted=True BEFORE eval; inference mode; no dropout, AMP or TF32; SDPA enabled",
        "benchmark_result_id": "selected_31k", "endpoint_feature_shape": [17583, 64],
        "runtime": runtime, "parameters_per_head": qualification["members"][0]["parameters_per_head"],
        "selection_rule": docs["selection"]["selection_rule"], "selection_tie_break": docs["selection"]["tie_break"],
        "selection_metrics_C3_development": docs["selection"]["selected"]["metrics"],
        "selection_at_utc": docs["selection"]["at_utc"], "test2_metrics": {
            cell: docs["results"]["test"][f"{cell}:test_2_macro"]["models"]["selected_31k"] for cell in ("C1", "C2", "C3")},
        "test2_paired_C3_differences": docs["results"]["test"]["C3:test_2_macro"]["paired_differences"],
    })
    models = copy.deepcopy(previous["models"])
    models[PRIMARY] = model
    registry = {
        "schema_version": 3, "release_id": RELEASE, "decision": "DEC-0056",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "bundle_path": BUNDLE,
        "primary_model": PRIMARY, "default_model": PRIMARY, "roles": ROLES,
        "model_order": previous["model_order"] + [PRIMARY], "models": models,
        "model_bundles": {**previous["model_bundles"], PRIMARY: BUNDLE},
        "aliases": {**previous["aliases"], **ALIASES}, "historical_reference_models": previous["model_order"],
        "previous_release": records["previous_registry"], "previous_release_audit": prior_audit,
        "bundle_files": files, "public_evidence": evidence, "provenance": records,
        "synthetic_qualification": qualification, "unit_tests": summary,
        "designation_timing": "User-authorized promotion after completed scaling, twelve-target and test2 comparisons",
        "claims": {"best_observed_test2_macro_C1_C2_C3": True, "pointwise_C3_intervals_above_zero": True,
                   "previously_examined_test": True, "PLM_interact_higher_on_added_C3": True,
                   "multiplicity_adjusted_intervals": False, "universal_superiority": False,
                   "independent_replication": False, "calibrated_binding_probability": False,
                   "direct_binding_or_partner_specific_generalization_established": False,
                   "TUnA_architecture_is_original_iPIN_work": False},
        "new_training_or_benchmark_scoring": False, "test_truth_or_pairs_accessed_for_release": False,
        "weights_publicly_redistributed": False,
    }
    validate_registry(registry, previous)
    validate_members(model, docs["scorer_freeze"], docs["selection"])
    v1.write_new(bundle / "MODEL_REGISTRY.json", registry)
    for path in sorted(bundle.rglob("*"), reverse=True):
        path.chmod(0o500 if path.is_dir() else 0o400)
    bundle.chmod(0o500)
    target = public / "MODEL_REGISTRY.json"
    v1.write_new(target, registry)
    with target.with_suffix(".json.sha256").open("x") as stream:
        stream.write(f"{v1.sha(target)}  {target.name}\n")
    audit = verify_release(project, closure=False)
    v1.write_new(project / VALIDATION / "FREEZE_AUDIT.json", audit)
    paths = [*RELEASE_SOURCES, f"{PUBLIC}/MODEL_REGISTRY.json", f"{PUBLIC}/MODEL_REGISTRY.json.sha256",
             f"{VALIDATION}/FREEZE_AUDIT.json", f"{VALIDATION}/UNIT_TESTS.xml"]
    paths += [f"{PUBLIC}/{x['path']}" for x in evidence]
    v1.write_new(public / "ARTIFACT_REGISTRY.json", {"release_id": RELEASE,
        "artifacts": [v1.record(project / path, project) for path in paths]})
    return verify_release(project)


def verify_release(project: Path, *, closure: bool = True) -> dict:
    target = project / PUBLIC / "MODEL_REGISTRY.json"
    registry = v1.read(target)
    if target.with_suffix(".json.sha256").read_text() != f"{v1.sha(target)}  {target.name}\n":
        raise RuntimeError("Registry checksum drift")
    records, docs, prior = inputs(project)
    validate_registry(registry, docs["previous_registry"])
    validate_members(registry["models"][PRIMARY], docs["scorer_freeze"], docs["selection"])
    if records != registry["provenance"] or prior != registry["previous_release_audit"]:
        raise RuntimeError("Original source/previous release drift")
    v1.checked_path(project, registry["models"][PRIMARY]["runtime"])
    bundle = project / BUNDLE
    if v1.sha(bundle / "MODEL_REGISTRY.json") != v1.sha(target):
        raise RuntimeError("Public/private registry mismatch")
    expected = {x["path"] for x in registry["bundle_files"]} | {"MODEL_REGISTRY.json"}
    if {str(p.relative_to(bundle)) for p in bundle.rglob("*") if p.is_file()} != expected:
        raise RuntimeError("Missing or unexpected bundle file")
    if any(p.is_symlink() or p.stat().st_mode & 0o222 for p in (bundle, *bundle.rglob("*"))):
        raise RuntimeError("Bundle is not read-only")
    for item in registry["bundle_files"]:
        v1.checked_path(bundle, item)
        v1.checked_path(project, item["source"])
    for item in registry["public_evidence"]:
        v1.checked_path(project / PUBLIC, item)
        v1.checked_path(project, item["source"])
    if closure:
        v1.verify(project, v1.read(project / PUBLIC / "ARTIFACT_REGISTRY.json")["artifacts"])
    return {"release_id": RELEASE, "passed": True, "models": 4, "primary_model": PRIMARY, "default_model": PRIMARY,
            "registry_sha256": v1.sha(target), "all_registered_member_checkpoints": 12,
            "bundle_files": len(registry["bundle_files"]), "bundle_read_only": True,
            "previous_releases_unchanged_and_verified": True, "source_studies_unchanged": True,
            "synthetic_qualification_passed": registry["synthetic_qualification"]["passed"], "unit_tests": registry["unit_tests"],
            "new_training_or_benchmark_scoring": False, "test_truth_or_pairs_accessed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    if Path(os.environ.get("APPTAINER_CONTAINER", "")).name != Path(v2.SIF).name:
        raise RuntimeError("Use the checksum-pinned TUnA Apptainer image")
    project = args.project.resolve(strict=True)
    print(json.dumps(create(project) if args.create else verify_release(project), indent=2))
