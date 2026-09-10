"""Fail-closed public inputs, identity joins, census, and pre-execution freezes."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pyarrow.parquet as pq
import yaml

from ipin_openppi.stage1.support import (
    atomic_json, atomic_npz, atomic_numpy, git_commit, resolve_regular_inside, sha256_file,
)
from .semantics import assign_folds, build_queries, cell_masks, embedding_indices, pair_codes, select_quartets


IDENTIFIER = "within_anchor_partner_specificity_v1"
CONFIG = Path("configs/within_anchor_partner_specificity_v1.yaml")
GENERATED = Path("artifacts/runs") / IDENTIFIER
RESULTS = Path("artifacts/results") / IDENTIFIER
VALIDATION = Path("artifacts/validation") / IDENTIFIER


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, payload):
    if path.exists():
        raise RuntimeError(f"refusing to overwrite: {path}")
    atomic_json(path, payload)


def read_json(path):
    return json.loads(path.read_text())


def config(root):
    value = yaml.safe_load(resolve_regular_inside(root, CONFIG).read_text())
    if value["protocol_id"] != IDENTIFIER or value["outputs"] != {
        "generated": str(GENERATED), "results": str(RESULTS), "validation": str(VALIDATION)
    }:
        raise RuntimeError("protocol identity or output namespace drift")
    if value["scientific_boundary"]["protected_access"] is not False or value["scientific_boundary"]["development_rows_used"] is not False:
        raise RuntimeError("scientific boundary drift")
    # This executable supports exactly the frozen recipe, not arbitrary tuning.
    if value["models"] != ["endpoint_linear", "endpoint_mlp64", "pair_linear"] or value["split"]["folds"] != 3:
        raise RuntimeError("unsupported model matrix or folds")
    return value


def artifact(root, path):
    path = resolve_regular_inside(root, path.relative_to(root))
    return {"path": str(path.relative_to(root)), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def verify_records(root, records):
    for record in records:
        path = resolve_regular_inside(root, Path(record["path"]))
        if sha256_file(path) != record["sha256"] or path.stat().st_size != record["bytes"]:
            raise RuntimeError(f"frozen artifact drift: {path}")


def public_inputs(root, cfg):
    # Exact input allowlist, not a recursive data scan. No development/evaluator paths.
    allowed = {
        "endpoints": "data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/eligible_reference_sequences/part-00000.parquet",
        "partitions": "data/canonical/final_benchmark_component_split_v1/endpoint_partition_assignments/part-00000.parquet",
        "positive": "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/positive_pairs/part-00000.parquet",
        "unlabeled": "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/unlabeled_pairs/part-00000.parquet",
        "embeddings": "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/esm2_150m/pooled_embeddings.f32.npy",
        "embedding_manifest": "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/esm2_150m/EMBEDDING_MANIFEST.json",
    }
    if set(cfg["inputs"]) != set(allowed):
        raise RuntimeError("input allowlist drift")
    records = []
    for key, expected_path in allowed.items():
        entry = cfg["inputs"][key]
        if entry["path"] != expected_path:
            raise RuntimeError(f"input outside public allowlist: {key}")
        record = artifact(root, root / entry["path"])
        if record["sha256"] != entry["sha256"]:
            raise RuntimeError(f"input hash mismatch: {key}")
        if "rows" in entry and pq.ParquetFile(root / entry["path"]).metadata.num_rows != entry["rows"]:
            raise RuntimeError(f"input row mismatch: {key}")
        records.append(record)
    return records


def validate_state(values, shorthand):
    expected = {"P": "released_positive", "U": "unlabeled"}[shorthand]
    if set(values) != {expected}:
        raise RuntimeError("row state mismatch")


def load_public(root, cfg):
    partitions = pq.read_table(root / cfg["inputs"]["partitions"]["path"]).to_pydict()
    table = pq.read_table(root / cfg["inputs"]["endpoints"]["path"], columns=[
        "reference_sequence_sha256", "sequence_length", "sequence"]).to_pydict()
    sequences = dict(zip(table["reference_sequence_sha256"], table["sequence"], strict=True))
    lengths = dict(zip(table["reference_sequence_sha256"], table["sequence_length"], strict=True))
    if len(sequences) != cfg["inputs"]["endpoints"]["rows"]:
        raise RuntimeError("duplicate sequence identities")
    mapping = {}
    for i, partition in enumerate(partitions["partition"]):
        if partition == "train":
            sha = partitions["reference_sequence_sha256"][i]
            if sha in mapping:
                raise RuntimeError("duplicate partition identity")
            mapping[sha] = partitions["component_id"][i]
    endpoints = sorted(mapping)
    component_names = sorted(set(mapping.values()))
    sizes = dict(Counter(mapping.values()))
    if len(endpoints) != cfg["split"]["endpoints"] or len(sizes) != cfg["split"]["components"]:
        raise RuntimeError("public endpoint/component census mismatch")
    component_index = {c: i for i, c in enumerate(component_names)}
    endpoint_index = {sha: i for i, sha in enumerate(endpoints)}
    component = np.array([component_index[mapping[e]] for e in endpoints], dtype=np.int64)
    assignments = assign_folds(sizes, cfg["split"]["folds"], cfg["split"]["salt"])
    folds = np.array([assignments[mapping[e]] for e in endpoints], dtype=np.int64)
    result = {"component": component, "fold": folds,
              "length": np.array([lengths[e] for e in endpoints], dtype=np.int64)}
    for state, key in (("P", "positive"), ("U", "unlabeled")):
        prefix = state.lower()
        cols = ["endpoint_a_sha256", "endpoint_b_sha256", "endpoint_a_component_id",
                "endpoint_b_component_id", "endpoint_a_partition", "endpoint_b_partition",
                "sampling_weight_numerator", "sampling_weight_denominator", "state"]
        data = pq.read_table(root / cfg["inputs"][key]["path"], columns=cols).to_pydict()
        validate_state(data["state"], state)
        for side in ("a", "b"):
            ids = data[f"endpoint_{side}_sha256"]
            if any(e not in endpoint_index for e in ids):
                raise RuntimeError("pair endpoint outside public training")
            if set(data[f"endpoint_{side}_partition"]) != {"train"}:
                raise RuntimeError("non-training pair partition")
            if any(mapping[e] != c for e, c in zip(ids, data[f"endpoint_{side}_component_id"], strict=True)):
                raise RuntimeError("pair/component identity mismatch")
            result[f"{prefix}_{side}"] = np.fromiter((endpoint_index[e] for e in ids), dtype=np.int64)
        codes = pair_codes(result[f"{prefix}_a"], result[f"{prefix}_b"], len(endpoints))
        order = np.argsort(codes)
        if len(np.unique(codes)) != len(codes):
            raise RuntimeError("duplicate unordered input pairs")
        for field in ("a", "b"):
            result[f"{prefix}_{field}"] = result[f"{prefix}_{field}"][order]
        result[f"{prefix}_code"] = codes[order]
        for field, suffix in (("sampling_weight_numerator", "num"), ("sampling_weight_denominator", "den")):
            result[f"{prefix}_{suffix}"] = np.asarray(data[field], dtype=np.int64)[order]
            if np.any(result[f"{prefix}_{suffix}"] <= 0):
                raise RuntimeError("nonpositive design weights")
        if state == "P" and not np.array_equal(result["p_num"], result["p_den"]):
            raise RuntimeError("P must be a unit-weight census")
    if np.intersect1d(result["p_code"], result["u_code"]).size:
        raise RuntimeError("P/U overlap")
    manifest = read_json(root / cfg["inputs"]["embedding_manifest"]["path"])
    raw = np.load(root / cfg["inputs"]["embeddings"]["path"], mmap_mode="r", allow_pickle=False)
    if raw.shape != (17000, 640) or raw.dtype != np.float32:
        raise RuntimeError("raw embedding shape/dtype mismatch")
    row_index = embedding_indices(manifest["vectors"], endpoints, len(raw))
    by_sha = {v["sequence_sha256"]: v for v in manifest["vectors"]}
    for endpoint, index in zip(endpoints, row_index, strict=True):
        vector = by_sha[endpoint]
        if hashlib.sha256(raw[index].tobytes()).hexdigest() != vector["vector_sha256"]:
            raise RuntimeError("raw vector identity hash mismatch")
        if lengths[endpoint] != vector["sequence_length"] or hashlib.sha256(sequences[endpoint].encode()).hexdigest() != endpoint:
            raise RuntimeError("sequence identity mismatch")
    raw_public = np.array(raw[row_index], dtype=np.float32, copy=True)
    if not np.isfinite(raw_public).all():
        raise RuntimeError("nonfinite raw embeddings")
    result["storage_row"] = row_index
    metadata = {"endpoints": endpoints, "components": component_names,
                "sequences": [sequences[e] for e in endpoints]}
    return result, metadata, raw_public


def prepare(root, *, resume_preparation=False):
    cfg = config(root)
    if (root / GENERATED).exists():
        raise RuntimeError("preparation namespace already exists; refusing overwrite")
    records = public_inputs(root, cfg)
    frozen_docs = [CONFIG, Path(cfg["authority"]), Path(cfg["protocol"])]
    records += [artifact(root, root / p) for p in frozen_docs]
    if resume_preparation:
        prior = read_json(root / RESULTS / "PREREGISTRATION.json")
        verify_records(root, prior["artifacts"])
        if prior["config"] != cfg or (root / RESULTS / "FEASIBILITY.json").exists():
            raise RuntimeError("preparation restart would change frozen design or census")
        write_json(root / RESULTS / "PREPARATION_RESUME.json", {
            "created_utc": now(), "reason": "schema_label_mapping_corrected_before_any_census_or_model_fit",
            "original_preregistration_preserved": True, "scientific_design_changed": False,
        })
    else:
        if (root / RESULTS).exists():
            raise RuntimeError("preparation namespace already exists; explicit restart review required")
        write_json(root / RESULTS / "PREREGISTRATION.json", {
            "created_utc": now(), "git_head": git_commit(root), "artifacts": records,
            "scope": "local_specification_before_this_study_census_and_model_fits",
            "external_registry": False, "config": cfg,
        })
    arrays, metadata, raw = load_public(root, cfg)
    generated = root / GENERATED
    atomic_npz(generated / "public_arrays.npz", **arrays)
    atomic_numpy(generated / "raw_public_embeddings.npy", raw)
    write_json(generated / "endpoint_metadata.json", metadata)
    census = []
    artifacts = [artifact(root, generated / name) for name in (
        "public_arrays.npz", "raw_public_embeddings.npy", "endpoint_metadata.json")]
    minimum = cfg["feasibility"]
    for fold in range(cfg["split"]["folds"]):
        indices, counts = {}, {}
        for state in ("p", "u"):
            masks = cell_masks(arrays[f"{state}_a"], arrays[f"{state}_b"], arrays["fold"], fold)
            counts[state] = {key: int(mask.sum()) for key, mask in zip(("C1", "C2", "C3"), masks)}
            indices[state] = np.flatnonzero(masks[2])
        evaluate = {key: np.concatenate([arrays[f"{s}_{key}"][indices[s]] for s in ("p", "u")])
                    for key in ("a", "b", "num", "den")}
        evaluate["positive"] = np.arange(len(evaluate["a"])) < len(indices["p"])
        evaluate["parent_row"] = np.concatenate((indices["p"], indices["u"]))
        qcfg = cfg["quartets"]
        qrows, qendpoints, candidates = select_quartets(
            evaluate["a"], evaluate["b"], evaluate["positive"], len(raw),
            salt=f"{cfg['split']['salt']}:quartets:{fold}", maximum=qcfg["maximum_per_fold"],
            edge_cap=qcfg["maximum_uses_per_positive_edge"], endpoint_cap=qcfg["maximum_uses_per_endpoint"])
        evaluate.update(quartet_rows=qrows, quartet_endpoints=qendpoints)
        queries = build_queries(evaluate["a"], evaluate["b"], evaluate["positive"])
        anchors = np.array([q.anchor for q in queries], dtype=np.int64)
        query_components, component_counts = np.unique(arrays["component"][anchors], return_counts=True)
        neff = float(1 / np.sum((component_counts / max(1, len(anchors))) ** 2)) if len(anchors) else 0.
        heldout = np.flatnonzero(arrays["fold"] == fold)
        positive_anchors = np.unique(np.r_[evaluate["a"][evaluate["positive"]], evaluate["b"][evaluate["positive"]]])
        quartet_components = np.unique(arrays["component"][qendpoints])
        checks = {
            "fit_positive": counts["p"]["C1"] >= minimum["minimum_fit_positive_per_fold"],
            "anchors": len(anchors) >= minimum["minimum_eligible_anchors_per_fold"],
            "anchor_components": len(query_components) >= minimum["minimum_anchor_components_per_fold"],
            "quartets": len(qrows) >= minimum["minimum_quartets_per_fold"],
            "quartet_components": len(quartet_components) >= minimum["minimum_quartet_components_per_fold"],
        }
        record = {
            "fold": fold, "cells": counts, "heldout_endpoints": len(heldout),
            "eligible_anchors": len(anchors), "anchor_components": len(query_components),
            "zero_positive_anchors": len(heldout) - len(positive_anchors),
            "positive_but_zero_unlabeled_anchors": len(positive_anchors) - len(anchors),
            "candidate_panel_size_quantiles": np.percentile([len(q.positive) + len(q.unlabeled) for q in queries], [0, 25, 50, 75, 100]).tolist() if queries else [],
            "effective_anchor_components": neff,
            "largest_anchor_component_fraction": float(component_counts.max(initial=0) / max(1, len(anchors))),
            "illustrative_80pct_power_MDE": {str(sd): (1.96 + .8416) * sd / np.sqrt(neff) if neff else None for sd in minimum["synthetic_power_component_effect_sd"]},
            "eligible_quartets_before_caps": candidates, "selected_quartets": len(qrows),
            "quartet_components": len(quartet_components), "quartet_endpoints": len(np.unique(qendpoints)),
            "checks": checks, "pass": all(checks.values()),
        }
        census.append(record)
        path = generated / f"evaluation_fold_{fold}.npz"
        atomic_npz(path, **evaluate)
        artifacts.append(artifact(root, path))
        print(json.dumps(record), flush=True)
    report = {"protocol_id": IDENTIFIER, "created_utc": now(), "folds": census,
              "feasible": all(f["pass"] for f in census), "prepared_artifacts": artifacts,
              "verified_embedding_vectors": len(raw), "verified_public_pair_joins": len(arrays["p_a"]) + len(arrays["u_a"]),
              "no_model_fits_or_scores_created": True, "source_robustness": "unavailable_in_public_training_package"}
    write_json(root / RESULTS / "FEASIBILITY.json", report)
    return report


def freeze(root):
    cfg = config(root)
    prereg = read_json(root / RESULTS / "PREREGISTRATION.json")
    verify_records(root, prereg["artifacts"])
    census = read_json(root / RESULTS / "FEASIBILITY.json")
    if not census["feasible"]:
        raise RuntimeError("feasibility gate failed; fitting prohibited")
    verify_records(root, census["prepared_artifacts"])
    test_path = root / VALIDATION / "unit_tests_data_runtime.xml"
    suites = ET.parse(test_path).getroot().findall(".//testsuite")
    if not suites or any(int(s.get("errors", "0")) or int(s.get("failures", "0")) for s in suites):
        raise RuntimeError("passing complete unit-test report required before execution freeze")
    code = sorted((root / "src/ipin_openppi/partner_specificity").glob("*.py"))
    code += [root / p for p in (
        "src/ipin_openppi/stage1/models.py", "src/ipin_openppi/stage1/support.py",
        "src/ipin_openppi/stage1/baselines.py", "src/ipin_openppi/stage1/constants.py",
        "scripts/model/run_within_anchor_partner_specificity_v1.py",
        "tests/unit/test_partner_specificity.py")]
    records = prereg["artifacts"] + census["prepared_artifacts"]
    records += [artifact(root, p) for p in code]
    records += [artifact(root, root / RESULTS / name) for name in ("PREREGISTRATION.json", "FEASIBILITY.json")]
    records.append(artifact(root, test_path))
    if (root / RESULTS / "PREPARATION_RESUME.json").exists():
        records.append(artifact(root, root / RESULTS / "PREPARATION_RESUME.json"))
    runtime = artifact(root, root / cfg["runtime"]["container"])
    if runtime["sha256"] != cfg["runtime"]["container_sha256"]:
        raise RuntimeError("qualified container hash mismatch")
    records.append(runtime)
    result = {"created_utc": now(), "git_head": git_commit(root), "artifacts": records,
              "fits_exist": False, "performance_inspected": False, "planned_fits": 27}
    if list((root / GENERATED).glob("fit_*")):
        raise RuntimeError("fits already exist before freeze")
    write_json(root / RESULTS / "EXECUTION_FREEZE.json", result)
    return result


def verify_freeze(root):
    value = read_json(root / RESULTS / "EXECUTION_FREEZE.json")
    verify_records(root, value["artifacts"])
    return value
