"""Production validation and registry construction for frozen Stage 1 embeddings."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from .constants import (
    CANDIDATES,
    EMBEDDING_ROOT,
    ENDPOINTS_PATH,
    ENDPOINTS_SHA256,
    MODEL_CACHE_ROOT,
    MODEL_CUSTODY_MANIFEST_PATH,
    MODEL_CUSTODY_MANIFEST_SHA256,
    MODEL_RUNTIME_REPORT_PATH,
    MODEL_RUNTIME_REPORT_SHA256,
    MODEL_SIF_SHA256,
    PARTITIONS_PATH,
    PARTITIONS_SHA256,
    PROTOCOL_CONFIGURATION_SHA256,
    PROTOCOL_ID,
    REPEAT_FRACTION,
    REPEAT_TOLERANCE,
    TOTAL_ENDPOINTS,
    TRAIN_ENDPOINTS,
)
from .embeddings import (
    STRATEGY_ID,
    cache_key,
    greedy_window_batches,
    ordered_records,
    repeat_selection_key,
    windows_for,
)
from .support import (
    assert_no_sensitive_path,
    atomic_json,
    git_commit,
    require_sha256,
    resolve_regular_inside,
    sha256_bytes,
    sha256_file,
)


def _check(
    checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any
) -> None:
    checks.append(
        {"check_id": check_id, "detail": detail, "status": "pass" if condition else "fail"}
    )


def _artifact(project_root: Path, relative: Path) -> dict[str, Any]:
    path = resolve_regular_inside(project_root, relative)
    return {
        "bytes": path.stat().st_size,
        "path": relative.as_posix(),
        "sha256": sha256_file(path),
    }


def _all_finite(matrix: np.ndarray, block_rows: int = 1024) -> bool:
    return all(
        bool(np.isfinite(matrix[start : start + block_rows]).all())
        for start in range(0, matrix.shape[0], block_rows)
    )


def _max_standardization_difference(
    matrix: np.ndarray, standardized: np.ndarray, mean: np.ndarray, std: np.ndarray
) -> float:
    maximum = 0.0
    for start in range(0, matrix.shape[0], 512):
        stop = min(start + 512, matrix.shape[0])
        expected = ((matrix[start:stop].astype(np.float64) - mean) / std).astype(np.float32)
        maximum = max(maximum, float(np.max(np.abs(expected - standardized[start:stop]))))
    return maximum


def audit_embeddings(
    *, project_root: Path, report_path: Path, registry_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate both complete snapshots and freeze a content-addressed registry."""

    checks: list[dict[str, Any]] = []
    require_sha256(project_root / ENDPOINTS_PATH, ENDPOINTS_SHA256)
    require_sha256(project_root / PARTITIONS_PATH, PARTITIONS_SHA256)
    require_sha256(project_root / MODEL_CUSTODY_MANIFEST_PATH, MODEL_CUSTODY_MANIFEST_SHA256)
    require_sha256(project_root / MODEL_RUNTIME_REPORT_PATH, MODEL_RUNTIME_REPORT_SHA256)
    records = ordered_records(project_root / ENDPOINTS_PATH)
    sequence_order = [record.sequence_sha256 for record in records]
    full_windows = windows_for(records)
    expected_full_layout = {
        "batches": sum(1 for _ in greedy_window_batches(full_windows)),
        "residue_window_tokens": sum(item.residues for item in full_windows),
        "windows": len(full_windows),
    }

    partition_table = pq.read_table(
        project_root / PARTITIONS_PATH,
        columns=["reference_sequence_sha256", "partition"],
    )
    partition_by_sha = dict(
        zip(
            partition_table["reference_sequence_sha256"].to_pylist(),
            partition_table["partition"].to_pylist(),
            strict=True,
        )
    )
    training_indices = np.asarray(
        [
            index
            for index, record in enumerate(records)
            if partition_by_sha[record.sequence_sha256] == "train"
        ],
        dtype=np.int64,
    )
    _check(
        checks,
        "endpoint_and_normalization_population",
        len(records) == TOTAL_ENDPOINTS
        and len(partition_by_sha) == TOTAL_ENDPOINTS
        and training_indices.size == TRAIN_ENDPOINTS,
        {"endpoints": len(records), "training_endpoints": int(training_indices.size)},
    )

    custody = json.loads((project_root / MODEL_CUSTODY_MANIFEST_PATH).read_text(encoding="utf-8"))
    custody_by_candidate = {
        item["candidate_id"]: item for item in custody["candidates"]
    }
    registry_artifacts = [
        _artifact(project_root, ENDPOINTS_PATH),
        _artifact(project_root, PARTITIONS_PATH),
        _artifact(project_root, MODEL_CUSTODY_MANIFEST_PATH),
        _artifact(project_root, MODEL_RUNTIME_REPORT_PATH),
    ]
    candidates_registry: list[dict[str, Any]] = []
    total_gpu_hours = 0.0
    total_embedding_bytes = 0

    for candidate_id, specification in CANDIDATES.items():
        output_root = EMBEDDING_ROOT / candidate_id
        manifest_relative = output_root / "EMBEDDING_MANIFEST.json"
        manifest_path = resolve_regular_inside(project_root, manifest_relative)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        custody_files = {
            item["filename"]: item["sha256"]
            for item in custody_by_candidate[candidate_id]["files"]
        }
        expected_tokenizer_hashes = {
            name: custody_files[name]
            for name in (
                "config.json",
                "special_tokens_map.json",
                "tokenizer_config.json",
                "vocab.txt",
            )
        }
        actual_tokenizer_hashes = {
            name: sha256_file(
                resolve_regular_inside(project_root, MODEL_CACHE_ROOT / candidate_id / name)
            )
            for name in expected_tokenizer_hashes
        }
        checkpoint_path = resolve_regular_inside(
            project_root, MODEL_CACHE_ROOT / candidate_id / "model.safetensors"
        )
        binding_ok = (
            manifest["candidate_id"] == candidate_id
            and manifest["repository_revision"] == specification["revision"]
            and manifest["checkpoint_sha256"] == specification["checkpoint_sha256"]
            and manifest["container_sha256"] == MODEL_SIF_SHA256
            and manifest["protocol_configuration_sha256"]
            == PROTOCOL_CONFIGURATION_SHA256
            and manifest["protocol_id"] == PROTOCOL_ID
            and manifest["strategy_id"] == STRATEGY_ID
            and manifest["tokenizer_file_hashes"] == expected_tokenizer_hashes
            and actual_tokenizer_hashes == expected_tokenizer_hashes
            and sha256_file(checkpoint_path) == specification["checkpoint_sha256"]
        )
        _check(
            checks,
            f"{candidate_id}_model_runtime_strategy_binding",
            binding_ok,
            {
                "checkpoint_sha256": manifest["checkpoint_sha256"],
                "code_commit": manifest["code_commit"],
                "container_sha256": manifest["container_sha256"],
                "repository_revision": manifest["repository_revision"],
            },
        )

        matrix_relative = Path(manifest["matrix_path"])
        matrix_path = resolve_regular_inside(project_root, matrix_relative)
        require_sha256(matrix_path, manifest["matrix_sha256"])
        matrix = np.load(matrix_path, mmap_mode="r", allow_pickle=False)
        shape_dtype_finite = (
            matrix.shape == (TOTAL_ENDPOINTS, int(specification["hidden_size"]))
            and matrix.dtype == np.float32
            and _all_finite(matrix)
        )
        _check(
            checks,
            f"{candidate_id}_matrix_shape_dtype_finiteness",
            shape_dtype_finite,
            {"dtype": str(matrix.dtype), "shape": list(matrix.shape)},
        )
        output_directory = project_root / output_root
        expected_output_names = {
            "EMBEDDING_MANIFEST.json",
            "deterministic_repeat_report.json",
            "pooled_embeddings.f32.npy",
            "repeat_embeddings.f32.npy",
            "standardized_embeddings.f32.npy",
            "training_normalization.npz",
        }
        observed_output_names = {
            item.name for item in output_directory.iterdir() if item.is_file()
        }
        extraction_layout_ok = (
            observed_output_names == expected_output_names
            and manifest["embedding_extractions"]
            == "one_complete_population_pass_plus_prespecified_one_percent_repeat"
            and all(
                manifest["full_extraction"][key] == value
                for key, value in expected_full_layout.items()
            )
            and manifest["matrix_bytes"] == matrix_path.stat().st_size
        )
        _check(
            checks,
            f"{candidate_id}_one_complete_extraction_and_file_set",
            extraction_layout_ok,
            {
                "full_layout": expected_full_layout,
                "output_files": sorted(observed_output_names),
            },
        )

        vector_entries = manifest["vectors"]
        vector_ok = len(vector_entries) == TOTAL_ENDPOINTS
        vector_hashes_ok = vector_ok
        cache_keys: set[str] = set()
        if vector_ok:
            for index, (record, entry) in enumerate(zip(records, vector_entries, strict=True)):
                vector = np.ascontiguousarray(matrix[index], dtype=np.float32)
                expected_hash = sha256_bytes(vector.tobytes(order="C"))
                expected_key = cache_key(candidate_id, record.sequence_sha256)
                vector_hashes_ok = vector_hashes_ok and (
                    entry["row_index"] == index
                    and entry["sequence_sha256"] == record.sequence_sha256
                    and entry["sequence_length"] == record.sequence_length
                    and entry["vector_dimension"] == int(specification["hidden_size"])
                    and entry["vector_dtype"] == "float32"
                    and entry["vector_sha256"] == expected_hash
                    and entry["cache_key"] == expected_key
                    and entry["tokenizer_file_hashes"] == expected_tokenizer_hashes
                )
                cache_keys.add(entry["cache_key"])
        _check(
            checks,
            f"{candidate_id}_vector_manifest_complete_unique_and_hashed",
            vector_hashes_ok and len(cache_keys) == TOTAL_ENDPOINTS,
            {"cache_keys": len(cache_keys), "vectors": len(vector_entries)},
        )

        normalizer_relative = Path(manifest["normalization"]["normalizer_path"])
        normalizer_path = resolve_regular_inside(project_root, normalizer_relative)
        require_sha256(normalizer_path, manifest["normalization"]["normalizer_sha256"])
        with np.load(normalizer_path, allow_pickle=False) as normalizer:
            saved_indices = normalizer["training_indices"]
            mean = normalizer["mean"]
            raw_std = normalizer["raw_standard_deviation"]
            std = normalizer["standard_deviation"]
        training = matrix[training_indices].astype(np.float64)
        expected_mean = training.mean(axis=0, dtype=np.float64)
        expected_raw_std = training.std(axis=0, dtype=np.float64, ddof=0)
        expected_std = np.maximum(expected_raw_std, 1e-6)
        normalizer_ok = (
            np.array_equal(saved_indices, training_indices)
            and np.array_equal(mean, expected_mean)
            and np.array_equal(raw_std, expected_raw_std)
            and np.array_equal(std, expected_std)
            and manifest["normalization"]["population"] == TRAIN_ENDPOINTS
            and manifest["normalization"]["heldout_endpoint_statistics_used"] is False
        )
        _check(
            checks,
            f"{candidate_id}_training_only_normalization",
            normalizer_ok,
            {
                "population": int(saved_indices.size),
                "standard_deviation_minimum": float(std.min()),
            },
        )

        standardized_relative = Path(manifest["normalization"]["standardized_matrix_path"])
        standardized_path = resolve_regular_inside(project_root, standardized_relative)
        require_sha256(
            standardized_path, manifest["normalization"]["standardized_matrix_sha256"]
        )
        standardized = np.load(standardized_path, mmap_mode="r", allow_pickle=False)
        standardization_difference = _max_standardization_difference(
            matrix, standardized, mean, std
        )
        _check(
            checks,
            f"{candidate_id}_standardized_matrix_exact",
            standardized.shape == matrix.shape
            and standardized.dtype == np.float32
            and _all_finite(standardized)
            and standardization_difference == 0.0,
            {
                "dtype": str(standardized.dtype),
                "maximum_absolute_difference": standardization_difference,
                "shape": list(standardized.shape),
            },
        )

        repeat_report_relative = Path(manifest["repeat_report_path"])
        repeat_report_path = resolve_regular_inside(project_root, repeat_report_relative)
        require_sha256(repeat_report_path, manifest["repeat_report_sha256"])
        repeat_report = json.loads(repeat_report_path.read_text(encoding="utf-8"))
        repeat_matrix_relative = Path(manifest["repeat_matrix_path"])
        repeat_matrix_path = resolve_regular_inside(project_root, repeat_matrix_relative)
        require_sha256(repeat_matrix_path, manifest["repeat_matrix_sha256"])
        repeated = np.load(repeat_matrix_path, mmap_mode="r", allow_pickle=False)
        repeat_count = math.ceil(TOTAL_ENDPOINTS * REPEAT_FRACTION)
        selected_indices = sorted(
            sorted(
                range(TOTAL_ENDPOINTS),
                key=lambda index: repeat_selection_key(
                    candidate_id, records[index].sequence_sha256
                ),
            )[:repeat_count],
            key=lambda index: (records[index].sequence_length, records[index].sequence_sha256),
        )
        repeat_records = [records[index] for index in selected_indices]
        repeat_windows = windows_for(repeat_records)
        expected_repeat_layout = {
            "batches": sum(1 for _ in greedy_window_batches(repeat_windows)),
            "residue_window_tokens": sum(item.residues for item in repeat_windows),
            "windows": len(repeat_windows),
        }
        observed_differences = np.max(
            np.abs(repeated - matrix[selected_indices]), axis=1
        )
        observed_maximum = float(observed_differences.max(initial=0.0))
        repeat_records_ok = len(repeat_report["records"]) == repeat_count
        if repeat_records_ok:
            for position, (index, entry) in enumerate(
                zip(selected_indices, repeat_report["records"], strict=True)
            ):
                repeat_records_ok = repeat_records_ok and (
                    entry["repeat_row_index"] == position
                    and entry["row_index"] == index
                    and entry["sequence_sha256"] == records[index].sequence_sha256
                    and entry["original_vector_sha256"]
                    == sha256_bytes(
                        np.ascontiguousarray(matrix[index], dtype=np.float32).tobytes(order="C")
                    )
                    and entry["repeat_vector_sha256"]
                    == sha256_bytes(
                        np.ascontiguousarray(repeated[position], dtype=np.float32).tobytes(
                            order="C"
                        )
                    )
                    and entry["maximum_absolute_difference"]
                    == float(observed_differences[position])
                )
        repeat_ok = (
            repeated.shape == (repeat_count, int(specification["hidden_size"]))
            and repeated.dtype == np.float32
            and _all_finite(repeated)
            and repeat_report["repeat_count"] == repeat_count
            and repeat_report["tolerance"] == REPEAT_TOLERANCE
            and repeat_report["maximum_absolute_difference"] == observed_maximum
            and repeat_report["repeat_matrix_path"] == manifest["repeat_matrix_path"]
            and repeat_report["repeat_matrix_sha256"] == manifest["repeat_matrix_sha256"]
            and repeat_report["repeat_matrix_bytes"] == repeat_matrix_path.stat().st_size
            and repeat_report["repeat_matrix_dtype"] == "float32"
            and all(
                manifest["repeat_extraction"][key] == value
                for key, value in expected_repeat_layout.items()
            )
            and observed_maximum <= REPEAT_TOLERANCE
            and repeat_records_ok
        )
        _check(
            checks,
            f"{candidate_id}_bottom_hash_repeat_recomputed",
            repeat_ok,
            {
                "maximum_absolute_difference": observed_maximum,
                "repeat_layout": expected_repeat_layout,
                "repeat_count": repeat_count,
                "tolerance": REPEAT_TOLERANCE,
            },
        )

        candidate_artifacts = [
            _artifact(project_root, relative)
            for relative in (
                manifest_relative,
                matrix_relative,
                normalizer_relative,
                standardized_relative,
                repeat_report_relative,
                repeat_matrix_relative,
            )
        ]
        registry_artifacts.extend(candidate_artifacts)
        embedding_bytes = sum(item["bytes"] for item in candidate_artifacts)
        total_embedding_bytes += embedding_bytes
        candidate_gpu_hours = float(manifest["full_extraction"]["gpu_hours"]) + float(
            manifest["repeat_extraction"]["gpu_hours"]
        )
        total_gpu_hours += candidate_gpu_hours
        candidates_registry.append(
            {
                "artifacts": candidate_artifacts,
                "candidate_id": candidate_id,
                "checkpoint_sha256": specification["checkpoint_sha256"],
                "code_commit": manifest["code_commit"],
                "embedding_bytes": embedding_bytes,
                "gpu_hours": candidate_gpu_hours,
                "manifest_sha256": sha256_file(manifest_path),
                "repository_revision": specification["revision"],
                "tokenizer_file_hashes": expected_tokenizer_hashes,
                "vector_count": TOTAL_ENDPOINTS,
            }
        )

    artifact_paths = [item["path"] for item in registry_artifacts]
    no_sensitive_paths = len(artifact_paths) == len(set(artifact_paths))
    try:
        for path in artifact_paths:
            assert_no_sensitive_path(Path(path))
    except RuntimeError:
        no_sensitive_paths = False
    _check(
        checks,
        "public_label_blind_artifact_boundary",
        no_sensitive_paths,
        {"registered_artifacts": len(artifact_paths)},
    )
    _check(
        checks,
        "embedding_compute_and_storage_budget",
        total_gpu_hours < 100.0 and total_embedding_bytes < 100 * 1024**3,
        {
            "embedding_bytes": total_embedding_bytes,
            "gpu_hours": total_gpu_hours,
            "storage_ceiling_bytes": 100 * 1024**3,
        },
    )

    failures = [item for item in checks if item["status"] != "pass"]
    registry = {
        "artifacts": sorted(registry_artifacts, key=lambda item: item["path"]),
        "candidates": candidates_registry,
        "container_sha256": MODEL_SIF_SHA256,
        "endpoint_order_sha256": sha256_bytes("\n".join(sequence_order).encode("ascii")),
        "generated_by_code_commit": git_commit(project_root),
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "protocol_id": PROTOCOL_ID,
        "schema_version": 1,
        "summary": {
            "candidate_count": len(candidates_registry),
            "embedding_bytes": total_embedding_bytes,
            "gpu_hours": total_gpu_hours,
            "vector_count": len(candidates_registry) * TOTAL_ENDPOINTS,
        },
    }
    atomic_json(registry_path, registry)
    report = {
        "checks": checks,
        "code_commit": git_commit(project_root),
        "embedding_registry_path": registry_path.relative_to(project_root).as_posix(),
        "embedding_registry_sha256": sha256_file(registry_path),
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "summary": {
            "fail": len(failures),
            "pass": len(checks) - len(failures),
            "warning": 0,
        },
    }
    atomic_json(report_path, report)
    if failures:
        raise RuntimeError(f"embedding production audit failed: {failures}")
    return registry, report
