"""Register the unchanged epoch-4 PU-TUnA ensemble as the third iPIN model.

Preservation only: no fitting, encoder inference, benchmark pair scoring, truth
access, or metric recomputation. Run in the pinned TUnA SIF. Creation is exclusive;
the default verifier is read-only. The original v1 release remains authoritative
for the two pooled models and their shared inputs.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import numpy as np
import torch

_spec = importlib.util.spec_from_file_location("freeze_v1", Path(__file__).with_name("freeze_pair_models_v1.py"))
v1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v1)

RELEASE = "frozen_pair_models_v2"
THIRD = "tuna_retrained_ensemble"
SEEDS = (20260803, 20260817, 20260831)
PUBLIC = f"artifacts/models/{RELEASE}"
BUNDLE = f".private/{RELEASE}/bundle"
VALIDATION = f"artifacts/validation/{RELEASE}"
TUNA = "benchmark/tuna"
SOURCE_BUNDLE = f"{TUNA}/runs/scorer_bundle"
SIF = "benchmark/containers/images/tuna-arm64-v1.sif"
SIF_SHA = "98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1"
AGGREGATION = "arithmetic_mean_of_three_FP32_mean_field_adjusted_logits_in_FP64"
ROLES = {"original_confirmatory_baseline": v1.BASELINE,
         "optimized_pooled_model": v1.BEST, "third_frozen_model": THIRD}
PINS = {
    "previous_registry": (f"{v1.PUBLIC}/MODEL_REGISTRY.json", "0b742d43e7da24285a9c2b5587d08cf3c4346073e33dbcaedf604d8a66c9fd83"),
    "previous_artifact_registry": (f"{v1.PUBLIC}/ARTIFACT_REGISTRY.json", "8e699f3d6a7f1ba2030217a0c6d937844506f9d7bae8060a80caf189fa5a61d4"),
    "scorer_freeze": (f"{SOURCE_BUNDLE}/SCORER_FREEZE.json", "e0d903371767f866a1a86392999823481aff083354be9f731c72b5b099e2410f"),
    "execution_freeze": (f"{TUNA}/provenance/EXECUTION_CODE_FREEZE.json", "b7746361b31f12cc6978311ec68bfab7b253b8841b0e831d21776e815dcff5c0"),
    "results": (f"{TUNA}/results/RESULTS.json", "b08d1388b03968144ee2457fc81340a5990594b79a9216fb6a3091661eacb989"),
    "prediction_freeze": (f"{TUNA}/private/freeze/PREDICTION_FREEZE.json", "cef9a5b73b1658f0d1acc98ce8c14af0e7a81d7cdaf3253766912f457b379a21"),
    "evaluation_reservation": (f"{TUNA}/private/evaluation/EVALUATION_RESERVATION.json", "a8d07276943881604c8f54aab0710877ab71f63727b4b9ffcdcb718d3c365640"),
    "residue_manifest": (f"{TUNA}/runs/residue_cache/RESIDUE_CACHE_MANIFEST.json", "f8b7ea5d6bcea150aadbc6ba94bc89261f8b2a7dc0d8d901cabb64bccbfc66db"),
}
UPSTREAM = {
    "TUnA/results/bernett/TUnA/main.py": "61c617dd8d6d6f45291792a152a9d6bc6035a1645930e170756cfdeeaf498efa",
    "TUnA/results/bernett/TUnA/lookahead.py": "8c1ec5a59901d891d421a379cb0d7dfeca3a48c9635b1128d2e4738758026ae2",
    "TUnA/results/bernett/TUnA/utils.py": "34070f3b7b94a41a7aaa952e4ded8d0926283434363f9d381c256abc520b5338",
    "TUnA/results/bernett/TUnA/inference.py": "3648da39032b67bb8b6533bc527d601e51bd7a2c59ce2ec08e1fcbf796cc70ea",
    "TUnA/results/bernett/TUnA/model.py": "56a44effe653ac21a985438d98301463971ad587415f59bbe6fe4c192d4f2c93",
    "uncertaintyAwareDeepLearn/uncertaintyAwareDeepLearn/classic_rffs.py": "f1e898d9dcd93d5b3493811ebb0ac0fdd1f0a29835e749e994b3a9a190898ad1",
    "uncertaintyAwareDeepLearn/uncertaintyAwareDeepLearn/__init__.py": "ea7c9272c64cd4246beb7c8ebd969d40351e5b79551457554d5cfcea398d9273",
    "TUnA/LICENSE": "57b4e93fe477383b8fae57b6c945b1b11693ed7a06e64f2fd25e3d900e72f0ad",
    "uncertaintyAwareDeepLearn/LICENSE": "bf9af2c762f6f862f1dda503de9b29c8726aea2141894dd5a4ab64f88e4c5d1e",
}
RELEASE_SOURCES = (
    "scripts/model/freeze_pair_models_v2.py", "tests/unit/test_frozen_pair_models_v2.py",
    "docs/models/FROZEN_PAIR_MODELS_v2.md", "governance/PROJECT_STATUS_v55.md",
    "governance/gates/gate_status_v55.yaml",
    "governance/decisions/DEC-0055-freeze-tuna-retrained-as-third-ipin-model.md",
)


def pinned(project: Path, relative: str, digest: str) -> dict:
    item = {"path": relative, "sha256": digest, "bytes": (project / relative).stat().st_size}
    v1.checked_path(project, item)
    return item


def inputs(project: Path) -> tuple[dict, dict, dict]:
    records = {name: pinned(project, path, digest) for name, (path, digest) in PINS.items()}
    docs = {name: v1.read(project / item["path"]) for name, item in records.items()}
    previous_audit = v1.verify_release(project)
    freeze = docs["scorer_freeze"]
    if freeze["selected_epoch"] != 4 or freeze["sif_sha256"] != SIF_SHA:
        raise RuntimeError("TUnA checkpoint/runtime identity drift")
    for item in freeze["files"]:
        v1.checked_path(project / SOURCE_BUNDLE, item)
    selection = v1.read(project / SOURCE_BUNDLE / "SELECTION.json")
    recipe = v1.read(project / SOURCE_BUNDLE / "provenance/TRAINING_FREEZE.json")
    if (selection["selected_epoch"] != 4 or not selection["all_three_seeds_retained"]
            or recipe["seeds"] != list(SEEDS) or recipe["evaluation_epochs"] != [4, 8]
            or recipe["upstream_commit"] != "b5bda8fee261a4f27821738db995cf5883dcd133"
            or recipe["gp_commit"] != "18565eb86026800817857e37243ae81f15f089d7"):
        raise RuntimeError("Closed TUnA selection/recipe drift")
    for item in docs["execution_freeze"]["files"]:
        pinned(project, f"{TUNA}/{item['path']}", item["sha256"])
    for relative, digest in UPSTREAM.items():
        pinned(project, f"{TUNA}/upstream/{relative}", digest)
    prediction = docs["prediction_freeze"]
    if (prediction["scorer_freeze_sha256"] != PINS["scorer_freeze"][1]
            or docs["results"]["prediction_freeze_sha256"] != PINS["prediction_freeze"][1]
            or docs["results"]["selected_epoch"] != 4
            or docs["evaluation_reservation"]["prediction_freeze_sha256"] != PINS["prediction_freeze"][1]
            or not prediction["complete_unique_finite_coverage"]):
        raise RuntimeError("Closed TUnA evaluation provenance drift")
    docs.update(selection=selection, recipe=recipe)
    return records, docs, previous_audit


def validate_registry(registry: dict, previous: dict) -> None:
    if registry["roles"] != ROLES or registry["model_order"] != [v1.BASELINE, v1.BEST, THIRD]:
        raise RuntimeError("Three-model identity/role drift")
    if set(registry["models"]) != {v1.BASELINE, v1.BEST, THIRD}:
        raise RuntimeError("Frozen model set drift")
    for name in (v1.BASELINE, v1.BEST):
        if registry["models"][name] != previous["models"][name]:
            raise RuntimeError("Existing frozen model definition changed")
        if registry["model_bundles"][name] != v1.BUNDLE:
            raise RuntimeError("Existing model preservation location changed")
    model = registry["models"][THIRD]
    if model["seeds"] != list(SEEDS) or [x["seed"] for x in model["members"]] != list(SEEDS):
        raise RuntimeError("TUnA seed membership/order drift")
    if (model["status"] != "frozen" or model["selected_epoch"] != 4
            or model["aggregation"] != AGGREGATION or model["member_weights"] != [1, 1, 1]
            or model["weight_divisor"] != 3 or model["sigmoid_applied"]
            or model["gp_covariance_refitted"] or model["training_normalizer_used"]
            or registry["model_bundles"][THIRD] != BUNDLE):
        raise RuntimeError("TUnA prediction definition drift")
    if registry["aliases"] != {"tuna-retrained": THIRD, "ipin_tuna_retrained": THIRD}:
        raise RuntimeError("TUnA model alias drift")
    if (registry["claims"]["conclusive_primary_C3_superiority"]
            or registry["new_training_or_benchmark_scoring"]
            or registry["test_truth_or_pairs_accessed_for_release"]
            or registry["weights_publicly_redistributed"]):
        raise RuntimeError("Preservation scope/claim drift")


def validate_member_records(model: dict, source_inventory: list[dict]) -> None:
    inventory = {item["path"]: item for item in source_inventory}
    for member in model["members"]:
        for key, folder, suffix in (("state", "weights", "pt"), ("endpoint_features", "features", "npy")):
            relative = f"{folder}/tuna_retrained_seed{member['seed']}.{suffix}"
            expected = inventory[relative]
            if member[key] != {k: expected[k] for k in ("path", "bytes", "sha256")}:
                raise RuntimeError("TUnA member does not match the original scorer freeze")


def qualify_states(project: Path, bundle: Path, docs: dict) -> dict:
    """Check real frozen tensors using synthetic residue inputs only, on CPU."""
    sys.path.insert(0, str(bundle / "code"))
    os.environ["TUNA_UPSTREAM_DIR"] = str(bundle / "upstream/TUnA/results/bernett/TUnA")
    spec = importlib.util.spec_from_file_location("frozen_tuna_adapter", bundle / "code/adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    import uncertaintyAwareDeepLearn
    vendor = Path(uncertaintyAwareDeepLearn.__file__).parent
    for name in ("__init__.py", "classic_rffs.py"):
        if v1.sha(vendor / name) != UPSTREAM[f"uncertaintyAwareDeepLearn/uncertaintyAwareDeepLearn/{name}"]:
            raise RuntimeError("Container GP source identity drift")
    torch.set_num_threads(2)
    generator = torch.Generator().manual_seed(20260920)
    lengths = [3, 5, 7]
    residues = [torch.randn(length, 640, generator=generator) * .1 for length in lengths]
    padded = torch.zeros(3, 7, 640)
    for i, values in enumerate(residues):
        padded[i, :len(values)] = values
    selected = next(x for x in docs["selection"]["candidates"] if x["epoch"] == 4)
    reports = []
    scores = []
    for seed, member in zip(SEEDS, selected["members"], strict=True):
        if member["seed"] != seed or member["epoch"] != 4:
            raise RuntimeError("Selected training member drift")
        training = project / f"{TUNA}/runs/training/seed_{seed}/epoch_04.pt"
        if v1.sha(training) != member["checkpoint"]["sha256"]:
            raise RuntimeError("Selected training checkpoint drift")
        state_path = bundle / f"weights/tuna_retrained_seed{seed}.pt"
        state = torch.load(state_path, map_location="cpu", weights_only=True)
        train_state = torch.load(training, map_location="cpu", weights_only=True)
        if set(state) != set(train_state) or any(not torch.equal(t, train_state[k]) for k, t in state.items()):
            raise RuntimeError("Preserved runtime state differs from selected training tensors")
        if any(t.dtype != torch.float32 or not torch.isfinite(t).all() for t in state.values()):
            raise RuntimeError("Invalid checkpoint tensor dtype/finite values")
        if any(state[k].shape != (4096, 4096) for k in ("gp_layer.covariance", "gp_layer.precision")):
            raise RuntimeError("Invalid frozen GP state")
        model = adapter.create(seed=seed, checkpoint=state_path, device="cpu")
        model.gp_layer.fitted = True
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        with torch.inference_mode():
            z = adapter.endpoint_features(model, padded, lengths)
            observed = adapter.cached_scores(model, z, [0, 1, 2], [1, 2, 0])
            reverse = adapter.cached_scores(model, z, [1, 2, 0], [0, 1, 2])
            expected = []
            for left, right in ((0, 1), (1, 2), (2, 0)):
                packed = adapter.native.test_pack([residues[left]], [residues[right]], [0], 512, 640, torch.device("cpu"))
                logit, variance = model.forward(packed[0], packed[1], packed[3], packed[4], packed[5], packed[6], True, False)
                expected.append(float((logit.reshape(-1) / torch.sqrt(1 + math.pi / 8 * variance)).item()))
        error = float(np.max(np.abs(observed.astype(np.float64) - expected)))
        if error > 1e-5 or not np.array_equal(observed, reverse):
            raise RuntimeError("Synthetic native/factorized score or symmetry mismatch")
        if any(not torch.equal(t, state[k]) for k, t in model.state_dict().items()):
            raise RuntimeError("Frozen parameter/buffer changed during synthetic inference")
        features = np.load(bundle / f"features/tuna_retrained_seed{seed}.npy", allow_pickle=False)
        if features.shape != (17000, 64) or features.dtype != np.float32 or not np.isfinite(features).all():
            raise RuntimeError("Invalid preserved endpoint feature matrix")
        scores.append(observed.astype(np.float64))
        reports.append({"seed": seed, "tensor_count": len(state),
                        "parameters_per_head": sum(p.numel() for p in model.parameters()),
                        "training_and_runtime_tensors_identical": True,
                        "native_max_absolute_error": error,
                        "pair_order_symmetry": True, "all_parameters_and_buffers_unchanged": True})
    ensemble = np.column_stack(scores).mean(1, dtype=np.float64)
    if not np.isfinite(ensemble).all():
        raise RuntimeError("Invalid synthetic ensemble")
    return {"passed": True, "device": "cpu", "torch": torch.__version__, "members": reports,
            "fixture": "Three synthetic residue arrays of lengths 3, 5, 7; three synthetic pairs",
            "absolute_tolerance": 1e-5, "gp_covariance_refitted": False,
            "benchmark_pairs_or_truth_read": False, "encoder_inference": False}


def create(project: Path) -> dict:
    if (project / BUNDLE).exists() or (project / PUBLIC).exists():
        raise FileExistsError("Release already exists; verify it, never overwrite it")
    records, docs, previous_audit = inputs(project)
    runtime = pinned(project, SIF, SIF_SHA)
    suites = list(ET.parse(project / VALIDATION / "UNIT_TESTS.xml").getroot().iter("testsuite"))
    if not suites or any(int(s.attrib.get(k, 0)) for s in suites for k in ("failures", "errors")):
        raise RuntimeError("Passing synthetic unit tests are required")
    test_summary = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    if test_summary["tests"] <= test_summary["skipped"]:
        raise RuntimeError("No passing synthetic unit tests")
    bundle = project / BUNDLE
    bundle.mkdir(parents=True, exist_ok=False)
    files = []

    def preserve(source, destination):
        item = v1.copy_checked(project, bundle, source, destination)
        files.append(item)
        return {k: item[k] for k in ("path", "bytes", "sha256")}

    inventory = {x["path"]: x for x in docs["scorer_freeze"]["files"]}

    def from_freeze(relative):
        return {**inventory[relative], "path": f"{SOURCE_BUNDLE}/{relative}"}

    members = []
    selected = next(x for x in docs["selection"]["candidates"] if x["epoch"] == 4)
    for seed, original in zip(SEEDS, selected["members"], strict=True):
        state = preserve(from_freeze(f"weights/tuna_retrained_seed{seed}.pt"), f"weights/tuna_retrained_seed{seed}.pt")
        features = preserve(from_freeze(f"features/tuna_retrained_seed{seed}.npy"), f"features/tuna_retrained_seed{seed}.npy")
        checkpoint = pinned(project, f"{TUNA}/runs/training/seed_{seed}/epoch_04.pt", original["checkpoint"]["sha256"])
        members.append({"seed": seed, "state": state, "endpoint_features": features, "training_checkpoint": checkpoint})
    for relative in ("endpoints.json", "components.json", "SELECTION.json", "FROZEN_SCORER_QUALIFICATION.json", "provenance/TRAINING_FREEZE.json"):
        preserve(from_freeze(relative), relative)
    for key in ("scorer_freeze", "execution_freeze", "results", "prediction_freeze", "evaluation_reservation", "residue_manifest"):
        preserve(records[key], f"provenance/{Path(records[key]['path']).name}")
    for name in ("adapter.py", "esm_cache.py", "common.py", "frozen_scorer.py"):
        preserve(v1.record(project / f"{TUNA}/scripts/{name}", project), f"code/{name}")
    for relative, digest in UPSTREAM.items():
        preserve(pinned(project, f"{TUNA}/upstream/{relative}", digest), f"upstream/{relative}")
    qualification = qualify_states(project, bundle, docs)
    previous = docs["previous_registry"]
    models = copy.deepcopy(previous["models"])
    models[THIRD] = {
        "status": "frozen", "display_name": "iPIN TUnA-retrained (PU-TUnA)",
        "architecture_origin": "Published Bernett TUnA; iPIN TRAIN-only PU adaptation",
        "selected_epoch": 4, "seeds": list(SEEDS), "members": members,
        "member_weights": [1, 1, 1], "weight_divisor": 3, "aggregation": AGGREGATION,
        "member_score": "logit / sqrt(1 + pi * frozen_GP_variance / 8)",
        "sigmoid_applied": False, "gp_covariance_refitted": False, "training_normalizer_used": False,
        "inference_mode": "eval_no_grad_no_dropout; gp_layer.fitted=True; update_precision=False",
        "precision": "FP32 model, attention, residues and GP buffers; FP64 member-score mean; no AMP/TF32",
        "input_pipeline": "Full-context ESM-2 layer-30 residue representations; full-length native TUnA endpoints; symmetric elementwise maximum; 4096 random Fourier features",
        "encoder": copy.deepcopy(previous["encoder"]),
        "encoder_bundle_path": f"{v1.BUNDLE}/encoder",
        "encoder_weights_sha256": "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566",
        "architecture": docs["recipe"]["architecture"],
        "parameters_per_head": qualification["members"][0]["parameters_per_head"],
        "runtime": runtime, "upstream_commit": docs["recipe"]["upstream_commit"], "gp_commit": docs["recipe"]["gp_commit"],
        "selection_rule": docs["recipe"]["selection"], "development_C3": selected["C3_development_concordance"],
        "original_scorer_frozen_at_utc": docs["scorer_freeze"]["at_utc"],
        "original_confirmatory_evaluation": False,
        "test_metrics": {cell: result["metrics"][THIRD] for cell, result in docs["results"]["cells"].items()},
        "paired_test_comparisons": {cell: [r for r in rows if r["candidate"] == THIRD] for cell, rows in docs["results"]["differences"].items()},
    }
    registry = {
        "schema_version": 2, "release_id": RELEASE, "decision": "DEC-0055",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "bundle_path": BUNDLE,
        "model_order": [v1.BASELINE, v1.BEST, THIRD], "roles": ROLES,
        "models": models, "model_bundles": {v1.BASELINE: v1.BUNDLE, v1.BEST: v1.BUNDLE, THIRD: BUNDLE},
        "aliases": {"tuna-retrained": THIRD, "ipin_tuna_retrained": THIRD},
        "previous_release": records["previous_registry"], "previous_release_audit": previous_audit,
        "existing_model_inputs": {k: previous[k] for k in ("shared_inputs", "encoder", "pair_features", "embedding_dimension", "embedding_identity", "optimized_recipe", "model_container_sha256")},
        "bundle_files": files, "provenance": records, "synthetic_qualification": qualification,
        "unit_tests": test_summary, "designation_timing": "post_benchmark_and_example_results",
        "claims": {"conclusive_primary_C3_superiority": False, "previously_examined_test": True,
                   "independent_replication": False, "calibrated_binding_probability": False,
                   "direct_binding_or_partner_specific_generalization_established": False,
                   "TUnA_architecture_is_original_iPIN_work": False},
        "new_training_or_benchmark_scoring": False, "test_truth_or_pairs_accessed_for_release": False,
        "weights_publicly_redistributed": False,
    }
    validate_registry(registry, previous)
    validate_member_records(models[THIRD], docs["scorer_freeze"]["files"])
    v1.write_new(bundle / "MODEL_REGISTRY.json", registry)
    for path in sorted(bundle.rglob("*"), reverse=True):
        path.chmod(0o500 if path.is_dir() else 0o400)
    bundle.chmod(0o500)
    target = project / PUBLIC / "MODEL_REGISTRY.json"
    v1.write_new(target, registry)
    with target.with_suffix(".json.sha256").open("x") as handle:
        handle.write(f"{v1.sha(target)}  {target.name}\n")
    audit = verify_release(project, closure=False)
    v1.write_new(project / VALIDATION / "FREEZE_AUDIT.json", audit)
    paths = [*RELEASE_SOURCES, f"{PUBLIC}/MODEL_REGISTRY.json", f"{PUBLIC}/MODEL_REGISTRY.json.sha256",
             f"{VALIDATION}/FREEZE_AUDIT.json", f"{VALIDATION}/UNIT_TESTS.xml"]
    v1.write_new(project / PUBLIC / "ARTIFACT_REGISTRY.json", {"release_id": RELEASE,
                 "artifacts": [v1.record(project / p, project) for p in paths]})
    return verify_release(project)


def verify_release(project: Path, *, closure: bool = True) -> dict:
    target = project / PUBLIC / "MODEL_REGISTRY.json"
    registry = v1.read(target)
    if target.with_suffix(".json.sha256").read_text() != f"{v1.sha(target)}  {target.name}\n":
        raise RuntimeError("Registry checksum drift")
    records, docs, previous_audit = inputs(project)
    validate_registry(registry, docs["previous_registry"])
    validate_member_records(registry["models"][THIRD], docs["scorer_freeze"]["files"])
    if records != registry["provenance"] or previous_audit != registry["previous_release_audit"]:
        raise RuntimeError("Historical input/registry preservation drift")
    v1.checked_path(project, registry["models"][THIRD]["runtime"])
    bundle = project / BUNDLE
    if v1.sha(bundle / "MODEL_REGISTRY.json") != v1.sha(target):
        raise RuntimeError("Private/public registry mismatch")
    expected = {x["path"] for x in registry["bundle_files"]} | {"MODEL_REGISTRY.json"}
    if {str(x.relative_to(bundle)) for x in bundle.rglob("*") if x.is_file()} != expected:
        raise RuntimeError("Unexpected or missing preservation file")
    if any(x.is_symlink() or x.stat().st_mode & 0o222 for x in (bundle, *bundle.rglob("*"))):
        raise RuntimeError("Preservation bundle is not read-only")
    for item in registry["bundle_files"]:
        v1.checked_path(bundle, item)
        v1.checked_path(project, item["source"])
    for member in registry["models"][THIRD]["members"]:
        v1.checked_path(bundle, member["state"])
        v1.checked_path(bundle, member["endpoint_features"])
        v1.checked_path(project, member["training_checkpoint"])
    if closure:
        v1.verify(project, v1.read(project / PUBLIC / "ARTIFACT_REGISTRY.json")["artifacts"])
    return {"release_id": RELEASE, "passed": True, "models": 3,
            "third_model": THIRD, "registry_sha256": v1.sha(target),
            "new_state_only_checkpoints": 3, "all_registered_member_checkpoints": 9,
            "bundle_files": len(registry["bundle_files"]), "bundle_read_only": True,
            "previous_release_unchanged_and_verified": True, "TUnA_evaluation_records_unchanged": True,
            "synthetic_qualification_passed": registry["synthetic_qualification"]["passed"],
            "unit_tests": registry["unit_tests"], "new_training_or_benchmark_scoring": False,
            "test_truth_or_pairs_accessed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    if Path(os.environ.get("APPTAINER_CONTAINER", "")).name != Path(SIF).name:
        raise RuntimeError("Use the checksum-pinned TUnA Apptainer image")
    project = args.project.resolve(strict=True)
    print(json.dumps(create(project) if args.create else verify_release(project), indent=2))
