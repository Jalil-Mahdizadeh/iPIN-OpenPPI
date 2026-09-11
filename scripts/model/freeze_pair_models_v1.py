"""Preserve the two evaluated ensembles; never fit, score pairs or open test truth.

Creation is exclusive. Default verification is read-only and safe to repeat.
Run inside the pinned model Apptainer image with PYTHONPATH=/project/src.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import numpy as np

from ipin_openppi.model_optimization.common import (
    BASELINE, SEEDS, historical_integrity, read, record, sha, verify, write_new,
)

RELEASE = "frozen_pair_models_v1"
BEST = "esm2_150m__residual_wide__epoch04_ensemble3"
PUBLIC = f"artifacts/models/{RELEASE}"
BUNDLE = f".private/{RELEASE}/bundle"
ORIGINAL = "artifacts/runs/protected_final_test_v1/frozen_bundle"
FOLLOWUP = ".private/model_optimization_followup_v1/bundle"
VALIDATION = f"artifacts/validation/{RELEASE}"
TRAINING = "artifacts/validation/model_execution/stage1_model_execution_v1"
EVIDENCE = {
    "original_freeze": ("artifacts/validation/protected_final_test_v1/SCORER_FREEZE.json", "5f25e856ce74e9f93497c17c19eb45ab1cb49fd74a30ceca5b4f874727e0125f"),
    "followup_freeze": ("artifacts/validation/model_optimization_followup_v1/SCORER_FREEZE.json", "44da994b834a5db4a7c831d85b26f44607d92b7c5058e1176c03049f74b9c9ba"),
    "search_freeze": ("artifacts/validation/model_optimization_v1/SEARCH_FREEZE.json", "c321841b6d79f4ca4256f14f9f7463a5bf3b5dc0085cfa554a1dc3ba4c906f67"),
    "selection": ("artifacts/results/model_optimization_v1/SELECTION.json", "3a4fe7e5a960a6798638ca84cf2433b2fa195c3dfeccd680986ee15ef0ea2ce6"),
    "development_gate": ("artifacts/results/model_optimization_v1/DEVELOPMENT_GATE.json", "7414d39086c9fe6fd50edbe0480046697a52cbf08d5a6783995cd3f89f501f4b"),
    "original_result": ("artifacts/results/protected_final_test_v1/FINAL_TEST_RESULTS.json", "6cc8c3ba61039501b3e1b09dfcee442de8f4dfcd0c717a466b15f9e77ef3a02e"),
    "followup_result": ("artifacts/results/model_optimization_followup_v1/FOLLOWUP_TEST_RESULTS.json", "17ee30e6960f64b3a33a87fbdf12c08d226d25b7a7e76289e8781e03b68110f9"),
    "training_registry": (f"{TRAINING}/TRAINING_ARTIFACT_REGISTRY.json", "11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318"),
    "encoder_custody": (f"{TRAINING}/MODEL_CUSTODY_MANIFEST.json", "a32399a1bdff8b56ff15509ec922e58f78a0e0bf6b860093db2f4952f48bbffe"),
}
RELEASE_SOURCES = (
    "scripts/model/freeze_pair_models_v1.py", "tests/unit/test_frozen_pair_models_v1.py",
    "docs/models/FROZEN_PAIR_MODELS_v1.md", "governance/PROJECT_STATUS_v54.md",
    "governance/gates/gate_status_v54.yaml",
    "governance/decisions/DEC-0054-freeze-and-designate-both-models.md",
)


def checked_path(root: Path, item: dict) -> Path:
    """Reject escape/symlink paths as well as hash and byte-count drift."""
    relative = Path(item["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("Unsafe preservation path")
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise RuntimeError("Symlink in preservation path")
    verify(root, [item])
    return path


def copy_checked(project: Path, bundle: Path, source: dict, destination: str) -> dict:
    path = checked_path(project, source)
    target = bundle / destination
    if Path(destination).is_absolute() or ".." in Path(destination).parts:
        raise RuntimeError("Unsafe bundle destination")
    target.parent.mkdir(parents=True, exist_ok=True)
    with path.open("rb") as incoming, target.open("xb") as outgoing:
        shutil.copyfileobj(incoming, outgoing)
    result = record(target, bundle)
    if (result["sha256"], result["bytes"]) != (source["sha256"], source["bytes"]):
        raise RuntimeError("Preservation copy differs from frozen source")
    return {**result, "source": source}


def validate_state(path: Path, optimized: bool) -> int:
    shapes = {"weight": (1, 1921), "bias": (1,)}
    if optimized:
        shapes = {"output.weight": (1, 1921), "output.bias": (1,),
                  "network.0.weight": (1921,), "network.0.bias": (1921,),
                  "network.1.weight": (256, 1921), "network.1.bias": (256,),
                  "network.4.weight": (1, 256), "network.4.bias": (1,)}
    with np.load(path, allow_pickle=False) as state:
        if len(state.files) != len(shapes) or set(state.files) != set(shapes):
            raise RuntimeError("Unexpected head state keys")
        for key, shape in shapes.items():
            if state[key].shape != shape or state[key].dtype != np.float32 or not np.isfinite(state[key]).all():
                raise RuntimeError("Invalid head shape, precision or finite values")
    return sum(int(np.prod(shape)) for shape in shapes.values())


def history(project: Path) -> dict:
    result = historical_integrity(project)
    for name, expected in (
        ("model_optimization_v1", "4143e7641660e3a1457d08ab989d1a58a69c5402f558fbf883325fd0fa5dcc56"),
        ("model_optimization_followup_v1", "eba0ef57678545bd2b39666ba94b6c2a1f0606d8143e13eb7f24a082b514614e"),
    ):
        path = project / f"artifacts/results/{name}/ARTIFACT_REGISTRY.json"
        if sha(path) != expected:
            raise RuntimeError("Historical registry drift")
        items = read(path)["artifacts"]
        verify(project, items)
        result["studies"].append({"study": name, "registry_sha256": expected, "files": len(items)})
        result["registered_files"] += len(items)
    custody = project / ".private/pair_level_pu_r_benchmark_artifacts_v1/followup_evaluations/model_optimization_followup_v1"
    expected_custody = {"ledger.json": "12d50bde100a74f68251ecc1fffe2f5d18f187a9b7ceefb8b633d569d5d28500",
                        "completion.json": "dca3195cfab47859372de4c390287dfdff356fc1502a33da5ec14ed247be0d44"}
    if any(sha(custody / name) != digest for name, digest in expected_custody.items()):
        raise RuntimeError("Consumed follow-up custody drift")
    result["followup_custody_sha256"] = expected_custody
    return result


def evidence(project: Path) -> tuple[dict, dict]:
    records, documents = {}, {}
    for name, (relative, expected) in EVIDENCE.items():
        item = record(project / relative, project)
        if item["sha256"] != expected:
            raise RuntimeError(f"Frozen evidence drift: {name}")
        records[name], documents[name] = item, read(project / relative)
    return records, documents


def validate_roles(registry: dict) -> None:
    if registry["roles"] != {"best_performing_model": BEST, "original_confirmatory_baseline": BASELINE}:
        raise RuntimeError("Model role drift")
    if set(registry["models"]) != {BEST, BASELINE}:
        raise RuntimeError("Frozen model set drift")
    for name, model in registry["models"].items():
        if model["seeds"] != list(SEEDS) or [x["seed"] for x in model["members"]] != list(SEEDS):
            raise RuntimeError("Frozen seed membership/order drift")
        if model["aggregation"] != "arithmetic_mean_of_three_FP32_raw_scores_in_FP64" or model["member_weights"] != [1, 1, 1] or model["weight_divisor"] != 3:
            raise RuntimeError("Frozen ensemble prediction definition drift")
        if model["parameters_per_head"] != (498053 if name == BEST else 1922) or model["status"] != "frozen":
            raise RuntimeError("Head definition drift")
    if registry["claims"]["conclusive_primary_C3_superiority"] or registry["claims"]["optimized_is_original_confirmatory_model"]:
        raise RuntimeError("Evidence role conflation")


def create(project: Path) -> dict:
    if (project / BUNDLE).exists() or (project / PUBLIC).exists():
        raise FileExistsError("Release already exists; verify it, never overwrite it")
    before = history(project)
    tests = ET.parse(project / VALIDATION / "UNIT_TESTS.xml").getroot()
    suites = list(tests.iter("testsuite"))
    if not suites or sum(int(x.attrib["tests"]) for x in suites) != 38 or any(
        int(x.attrib.get(key, 0)) for x in suites for key in ("failures", "errors", "skipped")
    ):
        raise RuntimeError("The 38-case GPU-enabled synthetic qualification must pass first")
    provenance, docs = evidence(project)
    original, followup = docs["original_freeze"], docs["followup_freeze"]
    selection, gate, results = docs["selection"]["selected"], docs["development_gate"], docs["followup_result"]
    if selection["recipe_id"] != "esm2_150m__residual_wide" or selection["epoch"] != 4 or results["model"] != BEST or gate["passed"]:
        raise RuntimeError("Closed selection/failed historical gate drift")
    bundle = project / BUNDLE
    bundle.mkdir(parents=True, exist_ok=False)
    files = []

    def preserve(source, destination):
        item = copy_checked(project, bundle, source, destination)
        files.append(item)
        return {k: item[k] for k in ("path", "bytes", "sha256")}

    def frozen_source(freeze, base, relative):
        item = next(x for x in freeze["files"] if x["path"] == relative)
        return {**item, "path": f"{base}/{relative}"}

    models = {}
    original_members = next(x for x in docs["training_registry"]["ensembles"] if x["candidate_id"] == BASELINE)["members"]
    if original_members != original["checkpoints"]:
        raise RuntimeError("Original training/final-test checkpoint mismatch")
    for name, members, freeze, base in ((BASELINE, original_members, original, ORIGINAL), (BEST, selection["members"], followup, FOLLOWUP)):
        output = []
        for member in members:
            seed = member["seed"]
            relative = f"features/{'candidate' if name == BEST else 'head'}_{seed}.npz"
            state = preserve(frozen_source(freeze, base, relative), f"heads/{'optimized' if name == BEST else 'affine'}/{seed}.npz")
            count = validate_state(bundle / state["path"], name == BEST)
            if name == BEST:
                checkpoint = record(project / ".private/model_optimization_v1/runs" / member["checkpoint"], project)
                if checkpoint["sha256"] != member["checkpoint_sha256"] or state["sha256"] != checkpoint["sha256"]:
                    raise RuntimeError("Selected optimized checkpoint mismatch")
            else:
                checkpoint = member["selected_checkpoint"]
                checked_path(project, checkpoint)
            output.append({"seed": seed, "state": state, "training_checkpoint": checkpoint})
        models[name] = {"status": "frozen", "seeds": list(SEEDS), "members": output,
                        "aggregation": "arithmetic_mean_of_three_FP32_raw_scores_in_FP64",
                        "member_weights": [1, 1, 1], "weight_divisor": 3,
                        "parameters_per_head": count, "inference_mode": "eval_no_grad_no_dropout",
                        "head_family": "residual_mlp" if name == BEST else "affine",
                        "original_scorer_frozen_at_utc": freeze["frozen_at_utc"],
                        "selected_epoch": 4 if name == BEST else None,
                        "selected_pass": None if name == BEST else 5,
                        "original_confirmatory_evaluation": name == BASELINE}
    shared = {}
    for relative in ("features/standardized.npy", "features/endpoints.json"):
        source = frozen_source(original, ORIGINAL, relative)
        other = frozen_source(followup, FOLLOWUP, relative)
        checked_path(project, other)
        if source["sha256"] != other["sha256"]:
            raise RuntimeError("The ensembles did not use identical embedding identities")
        shared[Path(relative).name] = preserve(source, relative)
    for basename in ("training_normalization.npz", "EMBEDDING_MANIFEST.json"):
        source = next(x for x in original["upstream_inputs"] if Path(x["path"]).name == basename)
        shared[basename] = preserve(source, f"features/{basename}")
    encoder = next(x for x in docs["encoder_custody"]["candidates"] if x["candidate_id"] == "esm2_150m")
    for item in encoder["files"]:
        preserve({k: item[k] for k in ("path", "bytes", "sha256")}, f"encoder/{item['filename']}")
    for relative, freeze, base in (("code/protected_final_core_v1.py", original, ORIGINAL),
                                   ("code/optimization_models_v1.py", followup, FOLLOWUP),
                                   ("code/model_optimization_followup_core_v1.py", followup, FOLLOWUP)):
        preserve(frozen_source(freeze, base, relative), relative)
    extraction_source = next(x for x in original["preparation_source_closure"] if x["path"] == "src/ipin_openppi/stage1/embeddings.py")
    preserve(extraction_source, "code/embeddings.py")
    comparison = {cell: {"baseline_concordance": value["metrics"][BASELINE]["ht_P_vs_U_concordance"],
                         "optimized_concordance": value["metrics"][BEST]["ht_P_vs_U_concordance"],
                         **value["ensemble_minus_baseline"]} for cell, value in results["cells"].items()}
    registry = {"schema_version": 1, "release_id": RELEASE, "decision": "DEC-0054",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "bundle_path": BUNDLE,
                "roles": {"best_performing_model": BEST, "original_confirmatory_baseline": BASELINE},
                "designation_scope": "highest_observed_primary_C3_concordance_among_the_two_evaluated_PLM_ensembles",
                "models": models, "shared_inputs": shared, "bundle_files": files, "provenance": provenance,
                "encoder": {k: encoder[k] for k in ("candidate_id", "repository", "repository_revision")},
                "pair_features": ["a+b", "abs(a-b)", "a*b", "exact_cosine(a,b)"],
                "embedding_dimension": 640, "embedding_identity": original["embedding_identity"],
                "optimized_recipe": next(x for x in docs["search_freeze"]["recipes"] if x["id"] == selection["recipe_id"]),
                "model_container_sha256": original["model_container_sha256"],
                "development_C3": {k: gate[k] for k in ("baseline_concordance", "candidate_concordance", "gain", "paired_gain_ci95")},
                "test_comparison": comparison,
                "claims": {"conclusive_primary_C3_superiority": False, "optimized_is_original_confirmatory_model": False,
                           "direct_binding_or_partner_specific_generalization_established": False,
                           "previously_examined_test": True, "original_development_gate_passed": False},
                "new_training_or_benchmark_scoring": False, "test_truth_or_pairs_accessed_for_release": False,
                "weights_publicly_redistributed": False, "historical_integrity": before}
    validate_roles(registry)
    if history(project) != before:
        raise RuntimeError("Historical evidence changed during preservation")
    write_new(bundle / "MODEL_REGISTRY.json", registry)
    for path in sorted(bundle.rglob("*"), reverse=True):
        path.chmod(0o500 if path.is_dir() else 0o400)
    bundle.chmod(0o500)
    target = project / PUBLIC / "MODEL_REGISTRY.json"
    write_new(target, registry)
    with target.with_suffix(".json.sha256").open("x") as handle:
        handle.write(f"{sha(target)}  {target.name}\n")
    audit = verify_release(project, closure=False)
    write_new(project / VALIDATION / "FREEZE_AUDIT.json", audit)
    paths = [*RELEASE_SOURCES, f"{PUBLIC}/MODEL_REGISTRY.json", f"{PUBLIC}/MODEL_REGISTRY.json.sha256",
             f"{VALIDATION}/FREEZE_AUDIT.json", f"{VALIDATION}/UNIT_TESTS.xml"]
    write_new(project / PUBLIC / "ARTIFACT_REGISTRY.json", {"release_id": RELEASE,
              "artifacts": [record(project / x, project) for x in paths]})
    return verify_release(project)


def verify_release(project: Path, *, closure: bool = True) -> dict:
    target = project / PUBLIC / "MODEL_REGISTRY.json"
    registry = read(target)
    if target.with_suffix(".json.sha256").read_text() != f"{sha(target)}  {target.name}\n":
        raise RuntimeError("Public registry checksum drift")
    validate_roles(registry)
    provenance, _ = evidence(project)
    if provenance != registry["provenance"] or history(project) != registry["historical_integrity"]:
        raise RuntimeError("Frozen evidence preservation drift")
    bundle = project / BUNDLE
    if sha(target) != sha(bundle / "MODEL_REGISTRY.json"):
        raise RuntimeError("Private/public registry mismatch")
    expected = {x["path"] for x in registry["bundle_files"]} | {"MODEL_REGISTRY.json"}
    if {str(x.relative_to(bundle)) for x in bundle.rglob("*") if x.is_file()} != expected:
        raise RuntimeError("Unexpected or missing preservation file")
    if any(x.is_symlink() or x.stat().st_mode & 0o222 for x in (bundle, *bundle.rglob("*"))):
        raise RuntimeError("Preservation bundle is not read-only")
    for item in registry["bundle_files"]:
        checked_path(bundle, item)
        checked_path(project, item["source"])
    for name, model in registry["models"].items():
        for member in model["members"]:
            checked_path(bundle, member["state"])
            checked_path(project, member["training_checkpoint"])
            if validate_state(bundle / member["state"]["path"], name == BEST) != model["parameters_per_head"]:
                raise RuntimeError("Parameter census drift")
    if closure:
        verify(project, read(project / PUBLIC / "ARTIFACT_REGISTRY.json")["artifacts"])
    return {"release_id": RELEASE, "passed": True, "registry_sha256": sha(target),
            "models": 2, "state_only_checkpoints": 6, "bundle_files": len(registry["bundle_files"]),
            "bundle_read_only": True, "historical_registered_entries_verified": 210,
            "synthetic_qualification_tests_passed": 38,
            "both_spent_ledgers_and_completions_unchanged": True,
            "new_training_or_benchmark_scoring": False, "test_truth_or_pairs_accessed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--create", action="store_true", help="Exclusive preservation; fails if release exists")
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    print(json.dumps(create(project) if args.create else verify_release(project), indent=2))
