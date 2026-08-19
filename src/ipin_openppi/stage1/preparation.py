"""Freeze public training arrays, exact orders, and the 30-run matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from .constants import (
    BATCH_COMPARISONS,
    CANDIDATES,
    CHECKPOINT_ROOT,
    EMBEDDING_ROOT,
    FAMILIES,
    MODEL_SIF_SHA256,
    PASSES,
    POSITIVE_PATH,
    POSITIVE_ROWS,
    POSITIVE_SHA256,
    PROTOCOL_CONFIGURATION_SHA256,
    RUN_ROOT,
    SEEDS,
    STAGE_ID,
    STEPS_PER_PASS,
    STRATA_PATH,
    STRATA_SHA256,
    TOTAL_STEPS,
    UNLABELED_PATH,
    UNLABELED_ROWS,
    UNLABELED_SHA256,
)
from .embeddings import ordered_records
from .objective import (
    deterministic_order,
    ordered_pair_id_digest,
    positive_repetition_counts,
    rational_weights,
)
from .support import (
    atomic_json,
    atomic_npz,
    atomic_numpy,
    git_commit,
    require_sha256,
    sha256_file,
)
from .constants import ENDPOINTS_PATH, ENDPOINTS_SHA256


CODE_PATHS = (
    Path("src/ipin_openppi/stage1/constants.py"),
    Path("src/ipin_openppi/stage1/models.py"),
    Path("src/ipin_openppi/stage1/objective.py"),
    Path("src/ipin_openppi/stage1/support.py"),
    Path("src/ipin_openppi/stage1/training.py"),
    Path("scripts/model/train_stage1_models_v1.py"),
)


def _map_endpoints(values: list[str], index_by_sha: dict[str, int]) -> np.ndarray:
    try:
        output = np.fromiter((index_by_sha[value] for value in values), dtype=np.int32, count=len(values))
    except KeyError as exc:
        raise RuntimeError(f"pair endpoint outside frozen sequence universe: {exc}") from exc
    return output


def prepare_stage1(project_root: Path) -> dict[str, Any]:
    endpoint_path = project_root / ENDPOINTS_PATH
    positive_path = project_root / POSITIVE_PATH
    unlabeled_path = project_root / UNLABELED_PATH
    strata_path = project_root / STRATA_PATH
    require_sha256(endpoint_path, ENDPOINTS_SHA256)
    require_sha256(positive_path, POSITIVE_SHA256)
    require_sha256(unlabeled_path, UNLABELED_SHA256)
    require_sha256(strata_path, STRATA_SHA256)

    prepared_root = project_root / RUN_ROOT / "prepared"
    if prepared_root.exists() and any(prepared_root.iterdir()):
        raise RuntimeError(f"refusing to overwrite prepared training snapshot: {prepared_root}")
    prepared_root.mkdir(parents=True, exist_ok=True)
    order_root = prepared_root / "orders"
    config_root = project_root / RUN_ROOT / "configs"
    order_root.mkdir(parents=True, exist_ok=True)
    config_root.mkdir(parents=True, exist_ok=True)

    records = ordered_records(endpoint_path)
    index_by_sha = {record.sequence_sha256: index for index, record in enumerate(records)}
    positive = pq.read_table(
        positive_path,
        columns=[
            "pair_id",
            "endpoint_a_sha256",
            "endpoint_b_sha256",
            "endpoint_a_partition",
            "endpoint_b_partition",
            "state",
            "sampling_weight_numerator",
            "sampling_weight_denominator",
        ],
    )
    unlabeled = pq.read_table(
        unlabeled_path,
        columns=[
            "pair_id",
            "endpoint_a_sha256",
            "endpoint_b_sha256",
            "endpoint_a_partition",
            "endpoint_b_partition",
            "state",
            "stratum_id",
            "sampling_weight_numerator",
            "sampling_weight_denominator",
        ],
    )
    strata = pq.read_table(
        strata_path,
        columns=["stratum_id", "sampling_weight_numerator", "sampling_weight_denominator"],
    )
    if positive.num_rows != POSITIVE_ROWS or unlabeled.num_rows != UNLABELED_ROWS or strata.num_rows != 36:
        raise RuntimeError("public training row-count drift")
    if set(positive["state"].to_pylist()) != {"released_positive"}:
        raise RuntimeError("positive state drift")
    if set(unlabeled["state"].to_pylist()) != {"unlabeled"}:
        raise RuntimeError("U state drift")
    for table in (positive, unlabeled):
        if set(table["endpoint_a_partition"].to_pylist()) != {"train"}:
            raise RuntimeError("non-training endpoint entered public fit input")
        if set(table["endpoint_b_partition"].to_pylist()) != {"train"}:
            raise RuntimeError("non-training endpoint entered public fit input")

    positive_pair_ids = positive["pair_id"].to_pylist()
    unlabeled_pair_ids = unlabeled["pair_id"].to_pylist()
    if len(set(positive_pair_ids)) != POSITIVE_ROWS or len(set(unlabeled_pair_ids)) != UNLABELED_ROWS:
        raise RuntimeError("duplicate public training pair ID")
    if max(map(len, positive_pair_ids + unlabeled_pair_ids[:1])) != 69:
        raise RuntimeError("pair-ID width drift")

    p_numerator = np.asarray(positive["sampling_weight_numerator"].to_numpy(), dtype=np.int64)
    p_denominator = np.asarray(positive["sampling_weight_denominator"].to_numpy(), dtype=np.int64)
    if not np.all(p_numerator == 1) or not np.all(p_denominator == 1):
        raise RuntimeError("positive census weights must remain 1/1")
    u_numerator = np.asarray(unlabeled["sampling_weight_numerator"].to_numpy(), dtype=np.int64)
    u_denominator = np.asarray(unlabeled["sampling_weight_denominator"].to_numpy(), dtype=np.int64)
    weights = rational_weights(u_numerator, u_denominator)
    stratum_weights = {
        str(stratum): (int(numerator), int(denominator))
        for stratum, numerator, denominator in zip(
            strata["stratum_id"].to_pylist(),
            strata["sampling_weight_numerator"].to_pylist(),
            strata["sampling_weight_denominator"].to_pylist(),
            strict=True,
        )
    }
    for stratum, numerator, denominator in zip(
        unlabeled["stratum_id"].to_pylist(), u_numerator, u_denominator, strict=True
    ):
        if stratum_weights[str(stratum)] != (int(numerator), int(denominator)):
            raise RuntimeError("U rational design weight differs from frozen stratum")

    arrays_path = prepared_root / "training_arrays.npz"
    atomic_npz(
        arrays_path,
        positive_endpoint_a=_map_endpoints(positive["endpoint_a_sha256"].to_pylist(), index_by_sha),
        positive_endpoint_b=_map_endpoints(positive["endpoint_b_sha256"].to_pylist(), index_by_sha),
        unlabeled_endpoint_a=_map_endpoints(unlabeled["endpoint_a_sha256"].to_pylist(), index_by_sha),
        unlabeled_endpoint_b=_map_endpoints(unlabeled["endpoint_b_sha256"].to_pylist(), index_by_sha),
        unlabeled_weight_numerator=u_numerator,
        unlabeled_weight_denominator=u_denominator,
    )

    order_records: list[dict[str, Any]] = []
    for seed in SEEDS:
        for pass_index in range(1, PASSES + 1):
            for state, pair_ids in (("P", positive_pair_ids), ("U", unlabeled_pair_ids)):
                print(f"ordering {state}: seed={seed} pass={pass_index}", flush=True)
                order = deterministic_order(
                    pair_ids, seed=seed, pass_index=pass_index, state=state
                )
                path = order_root / f"{state}_seed{seed}_pass{pass_index}.i64.npy"
                atomic_numpy(path, order)
                order_records.append(
                    {
                        "index_order_path": path.relative_to(project_root).as_posix(),
                        "index_order_sha256": sha256_file(path),
                        "ordered_pair_id_sha256": ordered_pair_id_digest(pair_ids, order),
                        "pass_index": pass_index,
                        "rows": len(pair_ids),
                        "seed": seed,
                        "state": state,
                    }
                )
            counts = positive_repetition_counts(pass_index)
            if int(counts.sum()) != UNLABELED_ROWS:
                raise RuntimeError("positive comparison coverage drift")

    order_manifest_path = prepared_root / "ORDER_MANIFEST.json"
    order_manifest = {
        "order_records": order_records,
        "positive_key": "sha256:{salt}:{seed}:{pass_index}:P:{pair_id}",
        "positive_repetitions_per_pass": {"ceiling": 120, "ceiling_count": 919, "floor": 119},
        "schema_version": 1,
        "sort": "full_unsigned_SHA256_digest_ascending_then_pair_id_ascending",
        "unlabeled_key": "sha256:{salt}:{seed}:{pass_index}:U:{pair_id}",
    }
    atomic_json(order_manifest_path, order_manifest)

    code_hashes = {path.as_posix(): sha256_file(project_root / path) for path in CODE_PATHS}
    embedding_inputs: dict[str, Any] = {}
    for candidate_id in CANDIDATES:
        manifest_path = project_root / EMBEDDING_ROOT / candidate_id / "EMBEDDING_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["vector_count"] != 17_000 or manifest["candidate_id"] != candidate_id:
            raise RuntimeError("embedding manifest identity/count drift")
        embedding_inputs[candidate_id] = {
            "manifest_path": manifest_path.relative_to(project_root).as_posix(),
            "manifest_sha256": sha256_file(manifest_path),
            "standardized_matrix_path": manifest["normalization"]["standardized_matrix_path"],
            "standardized_matrix_sha256": manifest["normalization"]["standardized_matrix_sha256"],
        }

    matrix_runs: list[dict[str, Any]] = []
    producer_commit = git_commit(project_root)
    order_by_key = {
        (record["state"], record["seed"], record["pass_index"]): record
        for record in order_records
    }
    for family, family_spec in FAMILIES.items():
        for recipe_id, recipe in family_spec["recipes"].items():
            for seed in SEEDS:
                run_id = f"{family}__{recipe_id}__seed{seed}"
                config = {
                    "batch_comparisons": BATCH_COMPARISONS,
                    "checkpoint_after_each_complete_U_pass": True,
                    "checkpoint_root": (CHECKPOINT_ROOT / run_id).as_posix(),
                    "code_commit": producer_commit,
                    "code_hashes": code_hashes,
                    "container_sha256": MODEL_SIF_SHA256,
                    "embedding": embedding_inputs[family_spec["candidate_id"]],
                    "family": family,
                    "fixed_complete_U_passes": PASSES,
                    "gradient_accumulation_steps": 1,
                    "infrastructure_resume_limit": 1,
                    "numerical_failure_retry": False,
                    "objective": "design_weighted_positive_vs_unlabeled_pairwise_logistic_ranking",
                    "optimizer": {
                        "beta1": 0.9,
                        "beta2": 0.999,
                        "epsilon": 1e-8,
                        "gradient_global_norm_clip": 1.0,
                        "name": "AdamW",
                    },
                    "orders": [
                        order_by_key[(state, seed, pass_index)]
                        for pass_index in range(1, PASSES + 1)
                        for state in ("P", "U")
                    ],
                    "performance_early_stopping": False,
                    "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
                    "recipe": {"recipe_id": recipe_id, **recipe},
                    "run_id": run_id,
                    "run_output_root": (RUN_ROOT / "runs" / run_id).as_posix(),
                    "scheduler": {
                        "final_learning_rate_fraction": 0.1,
                        "name": "linear_warmup_then_cosine_decay",
                        "steps_per_pass": STEPS_PER_PASS,
                        "total_steps": TOTAL_STEPS,
                        "warmup_steps": 123,
                    },
                    "schema_version": 1,
                    "seed": seed,
                    "seed_controls": {
                        "allow_tf32": False,
                        "cublas_workspace_config": ":4096:8",
                        "cudnn_benchmark": False,
                        "cudnn_deterministic": True,
                        "numpy_generator": "PCG64DXSM",
                        "pythonhashseed": seed,
                        "torch_deterministic_algorithms": True,
                    },
                    "selected_checkpoint_rule": "minimum_complete_pass_monitor_earliest_exact_tie",
                    "training_arrays_path": arrays_path.relative_to(project_root).as_posix(),
                    "training_arrays_sha256": sha256_file(arrays_path),
                }
                config_path = config_root / f"{run_id}.json"
                atomic_json(config_path, config)
                matrix_runs.append(
                    {
                        "candidate_id": family_spec["candidate_id"],
                        "config_path": config_path.relative_to(project_root).as_posix(),
                        "config_sha256": sha256_file(config_path),
                        "family": family,
                        "recipe_id": recipe_id,
                        "run_id": run_id,
                        "seed": seed,
                    }
                )
    if len(matrix_runs) != 30:
        raise RuntimeError(f"run matrix is not exactly 30: {len(matrix_runs)}")
    matrix_manifest = {
        "adaptive_search": False,
        "code_commit": producer_commit,
        "comparison_ceiling": 300_000_000,
        "container_sha256": MODEL_SIF_SHA256,
        "maximum_gpu_hours": 100,
        "maximum_project_storage_gib": 100,
        "multi_gpu_or_multi_node": False,
        "order_manifest_path": order_manifest_path.relative_to(project_root).as_posix(),
        "order_manifest_sha256": sha256_file(order_manifest_path),
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "run_count": len(matrix_runs),
        "runs": matrix_runs,
        "schema_version": 1,
        "training_arrays_path": arrays_path.relative_to(project_root).as_posix(),
        "training_arrays_sha256": sha256_file(arrays_path),
    }
    matrix_path = project_root / RUN_ROOT / "MATRIX_MANIFEST.json"
    atomic_json(matrix_path, matrix_manifest)
    print(matrix_path.relative_to(project_root))
    return matrix_manifest
