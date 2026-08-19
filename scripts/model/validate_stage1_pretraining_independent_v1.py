#!/usr/bin/env python3
"""Clean-room Stage 1 pre-training validation without production imports or PyTorch."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import stat
from typing import Any, Iterable

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq


CONFIG_SHA256 = "3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5"
CONTAINER_SHA256 = "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"
CUSTODY_SHA256 = "a32399a1bdff8b56ff15509ec922e58f78a0e0bf6b860093db2f4952f48bbffe"
RUNTIME_SHA256 = "a96ceb38d5beca8e3c3d640f99341111ed477e9a39e61494e42555c3d17020ec"
REGISTRY_SHA256 = "429e9b3c40827ea5a7513b3599a95d201cdc5eea1e0f99f8c384050cbfcbaed1"
PRODUCTION_AUDIT_SHA256 = "992faf2029a2e2c0288dfc3b4216a7de75e0b04eea4e54f80560c0313055a79a"
EMBEDDING_PRODUCER_COMMIT = "0ab3740b1ce3ddb9f78fdb4ddd07981dff5a9c9c"

ENDPOINT_PATH = Path(
    "data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/"
    "eligible_reference_sequences/part-00000.parquet"
)
PARTITION_PATH = Path(
    "data/canonical/final_benchmark_component_split_v1/"
    "endpoint_partition_assignments/part-00000.parquet"
)
P_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "positive_pairs/part-00000.parquet"
)
U_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "unlabeled_pairs/part-00000.parquet"
)
STRATA_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "sampling_strata/part-00000.parquet"
)
INPUT_HASHES = {
    ENDPOINT_PATH: "4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e",
    PARTITION_PATH: "66db8cd59e7cb8cf06ff3ad785448dfc7d5fdd24643811946246d129b0bd8a67",
    P_PATH: "4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499",
    U_PATH: "d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7",
    STRATA_PATH: "b8e4247ce934d837477513b322af008413ac8d61fa95ccedd16fe2712c1d6427",
}
VALIDATION_ROOT = Path("artifacts/validation/model_execution/stage1_model_execution_v1")
EMBEDDING_ROOT = Path("artifacts/embeddings/model_governance_and_baseline_training_protocol_v1")
CACHE_ROOT = Path("artifacts/cache/models/model_governance_and_baseline_training_protocol_v1")
EXPECTED_CANDIDATES = {
    "esm2_150m": {
        "dimension": 640,
        "revision": "a695f6045e2e32885fa60af20c13cb35398ce30c",
        "weight": "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566",
        "tokenizer": {
            "config.json": "e512f68ec444d99477703a9806639ca83da3dbc19f6c5fe428d6e5b7460972dc",
            "special_tokens_map.json": "3aedcd4211c0d43aec4e607ff60a63255f3174ead795e997350f09a5f8cd9ee1",
            "tokenizer_config.json": "7e9161ecdb548ec45a41cbc6b24aa4476fdd418461f491c4207baa99419a29ad",
            "vocab.txt": "0b82cc0a7c7cf9e567b1e5892d793285b9fbae822c964ca48696f7db44598e03",
        },
    },
    "esm2_650m": {
        "dimension": 1280,
        "revision": "08e4846e537177426273712802403f7ba8261b6c",
        "weight": "a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0",
        "tokenizer": {
            "config.json": "539095c22efc52a09d6147074ba4ca119f76a890df5901213b2b55f7d2f96b2b",
            "special_tokens_map.json": "3aedcd4211c0d43aec4e607ff60a63255f3174ead795e997350f09a5f8cd9ee1",
            "tokenizer_config.json": "7e9161ecdb548ec45a41cbc6b24aa4476fdd418461f491c4207baa99419a29ad",
            "vocab.txt": "0b82cc0a7c7cf9e567b1e5892d793285b9fbae822c964ca48696f7db44598e03",
        },
    },
}
EXPECTED_EMBEDDING_FILES = {
    "EMBEDDING_MANIFEST.json",
    "deterministic_repeat_report.json",
    "pooled_embeddings.f32.npy",
    "repeat_embeddings.f32.npy",
    "standardized_embeddings.f32.npy",
    "training_normalization.npz",
}
FORBIDDEN_FRAGMENTS = (
    "/sealed/",
    ".private",
    "development_release.cms",
    "protected_candidates.cms",
    "protected_truth.cms",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_regular(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or any(fragment in "/" + relative.as_posix() for fragment in FORBIDDEN_FRAGMENTS):
        raise RuntimeError(f"unsafe evidence path: {relative}")
    root = root.resolve(strict=True)
    target = (root / relative).absolute()
    target.relative_to(root)
    current = target
    while True:
        if stat.S_ISLNK(current.lstat().st_mode):
            raise RuntimeError(f"symlink prohibited: {current}")
        if current == root:
            break
        current = current.parent
    if not target.is_file():
        raise RuntimeError(f"regular file required: {relative}")
    return target


def _check(checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any) -> None:
    checks.append(
        {"check_id": check_id, "detail": detail, "status": "pass" if condition else "fail"}
    )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists() or path.exists():
        raise RuntimeError(f"refusing to overwrite validation evidence: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
    temporary.replace(path)


def _window_starts(length: int) -> tuple[int, ...]:
    if length <= 0:
        raise RuntimeError("empty endpoint sequence")
    if length <= 1022:
        return (0,)
    starts = list(range(0, length - 1022 + 1, 894))
    final = length - 1022
    if starts[-1] != final:
        starts.append(final)
    coverage = np.zeros(length, dtype=np.uint16)
    for start in starts:
        coverage[start : start + 1022] += 1
    if starts != sorted(set(starts)) or not np.all(coverage > 0):
        raise RuntimeError("independent window coverage failure")
    return tuple(starts)


def _layout(records: Iterable[tuple[str, int]]) -> dict[str, int]:
    batch_count = 0
    batch_residues = 0
    total_residues = 0
    window_count = 0
    for _, length in records:
        for start in _window_starts(length):
            residues = min(start + 1022, length) - start
            if batch_residues and batch_residues + residues > 4096:
                batch_count += 1
                batch_residues = 0
            batch_residues += residues
            total_residues += residues
            window_count += 1
    if batch_residues:
        batch_count += 1
    return {
        "batches": batch_count,
        "residue_window_tokens": total_residues,
        "windows": window_count,
    }


def _all_finite(matrix: np.ndarray) -> bool:
    return all(
        bool(np.isfinite(matrix[start : start + 1024]).all())
        for start in range(0, matrix.shape[0], 1024)
    )


def _cache_key(candidate: str, revision: str, weight: str, sequence_sha256: str) -> str:
    strategy = "final_hidden_state_residue_mean_fp32_window1022_overlap128_stride894_v1"
    return _bytes_sha256("|".join((candidate, revision, weight, strategy, sequence_sha256)).encode("ascii"))


def _order_key(seed: int, pass_index: int, state: str, pair_id: str) -> bytes:
    payload = f"sha256:ipin-openppi-model-training-v1:{seed}:{pass_index}:{state}:{pair_id}"
    return hashlib.sha256(payload.encode("utf-8")).digest()


def _parameter_counts() -> dict[str, int]:
    return {
        "lightweight_esm2_150m_linear": (3 * 640 + 1) + 1,
        "esm2_650m_linear_ablation": (3 * 1280 + 1) + 1,
        "esm2_650m_nonlinear_no_gate_ablation": (1280 * 256 + 256)
        + (769 * 128 + 128)
        + (128 + 1),
        "esm2_650m_partner_gated_primary": (1280 * 256 + 256)
        + (256 * 256 + 256)
        + (769 * 128 + 128)
        + (128 + 1),
    }


def _source_contract(root: Path) -> tuple[bool, dict[str, Any]]:
    paths = {
        name: root / "src/ipin_openppi/stage1" / name
        for name in ("baselines.py", "models.py", "objective.py", "preparation.py", "training.py")
    }
    sources = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}
    model_tokens = (
        "torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)",
        'F.gelu(self.projection(a), approximate="none")',
        "conditioned_a = projected_a * torch.sigmoid(self.gate(projected_b))",
        "conditioned_b = projected_b * torch.sigmoid(self.gate(projected_a))",
        "self.hidden = nn.Linear(769, 128)",
        "nn.init.xavier_uniform_(parameter, generator=generator)",
        "parameter.zero_()",
    )
    objective_tokens = (
        'payload = f"sha256:{TRAINING_SALT}:{seed}:{pass_index}:{state}:{pair_id}"',
        "F.softplus(-(score_positive - score_unlabeled))",
        "((weights / mean_weight) * per_comparison.to(torch.float64)).mean()",
        "monitor_numerator += torch.sum(batch_weights * per_comparison.detach().to(torch.float64))",
        "monitor_denominator += torch.sum(batch_weights)",
        "for start in range(0, UNLABELED_ROWS, BATCH_COMPARISONS)",
        "positive_rows = np.asarray(p_order[positive_positions], dtype=np.int64)",
    )
    baseline_tokens = (
        "integer / (2**256 - 1)",
        "math.log1p(degree_a) + math.log1p(degree_b)",
        "math.log1p(degree_a * degree_b)",
        "math.log1p(mass_a * mass_b)",
        "math.log1p(len(neighbors_a.intersection(neighbors_b)))",
        'KMER_ALPHABET = "ACDEFGHIKLMNPQRSTVWYX"',
        "np.maximum(forward, reverse).max(initial=0.0)",
    )
    no_sensitive = all(
        fragment not in source
        for source in sources.values()
        for fragment in FORBIDDEN_FRAGMENTS
    )
    condition = (
        all(token in sources["models.py"] for token in model_tokens)
        and all(token in sources["objective.py"] + sources["training.py"] for token in objective_tokens)
        and all(token in sources["baselines.py"] for token in baseline_tokens)
        and no_sensitive
        and "binary_cross_entropy" not in sources["training.py"] + sources["objective.py"]
        and "torch" not in Path(__file__).read_text(encoding="utf-8").split("import pyarrow", 1)[0]
    )
    return condition, {
        "parameter_counts": _parameter_counts(),
        "source_sha256": {name: _sha256(path) for name, path in paths.items()},
    }


def validate(project_root: Path, output: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    _check(
        checks,
        "binding_configuration_and_public_inputs",
        _sha256(_safe_regular(project_root, Path("configs/model_governance_and_baseline_training_protocol_v1.yaml")))
        == CONFIG_SHA256
        and all(_sha256(_safe_regular(project_root, path)) == digest for path, digest in INPUT_HASHES.items()),
        {path.as_posix(): digest for path, digest in INPUT_HASHES.items()},
    )

    registry_path = _safe_regular(project_root, VALIDATION_ROOT / "EMBEDDING_ARTIFACT_REGISTRY.json")
    production_path = _safe_regular(project_root, VALIDATION_ROOT / "EMBEDDING_PRODUCTION_AUDIT_REPORT.json")
    evidence_ok = _sha256(registry_path) == REGISTRY_SHA256 and _sha256(production_path) == PRODUCTION_AUDIT_SHA256
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    production = json.loads(production_path.read_text(encoding="utf-8"))
    _check(
        checks,
        "production_evidence_clean_commit_boundary",
        evidence_ok
        and registry["generated_by_code_commit"] == EMBEDDING_PRODUCER_COMMIT
        and production["status"] == "pass"
        and production["embedding_registry_sha256"] == REGISTRY_SHA256,
        {"producer_commit": registry["generated_by_code_commit"], "registry_sha256": _sha256(registry_path)},
    )

    custody_path = _safe_regular(project_root, VALIDATION_ROOT / "MODEL_CUSTODY_MANIFEST.json")
    runtime_path = _safe_regular(project_root, VALIDATION_ROOT / "MODEL_RUNTIME_QUALIFICATION_REPORT.json")
    sif_path = _safe_regular(project_root, Path("containers/images/ipin-model-arm64_0.1.0.sif"))
    custody = json.loads(custody_path.read_text(encoding="utf-8"))
    custody_files_ok = _sha256(custody_path) == CUSTODY_SHA256 and _sha256(runtime_path) == RUNTIME_SHA256
    for candidate in custody["candidates"]:
        for item in candidate["files"]:
            custody_files_ok = custody_files_ok and _sha256(_safe_regular(project_root, Path(item["path"]))) == item["sha256"]
    _check(
        checks,
        "runtime_checkpoint_and_tokenizer_rehash",
        custody_files_ok and _sha256(sif_path) == CONTAINER_SHA256,
        {"container_bytes": sif_path.stat().st_size, "container_sha256": CONTAINER_SHA256},
    )

    registered_ok = len(registry["artifacts"]) == 16
    registered_paths: set[str] = set()
    for item in registry["artifacts"]:
        path = _safe_regular(project_root, Path(item["path"]))
        registered_ok = registered_ok and path.stat().st_size == item["bytes"] and _sha256(path) == item["sha256"]
        registered_paths.add(item["path"])
    _check(
        checks,
        "embedding_registry_artifacts_rehashed",
        registered_ok and len(registered_paths) == 16,
        {"artifacts": len(registered_paths)},
    )

    endpoint_table = pq.read_table(project_root / ENDPOINT_PATH, columns=["reference_sequence_sha256", "sequence_length", "sequence"])
    records = sorted(
        zip(
            endpoint_table["reference_sequence_sha256"].to_pylist(),
            endpoint_table["sequence_length"].to_pylist(),
            endpoint_table["sequence"].to_pylist(),
            strict=True,
        ),
        key=lambda item: (int(item[1]), str(item[0])),
    )
    endpoint_ok = len(records) == 17_000 and len({str(item[0]) for item in records}) == 17_000
    for digest, length, sequence in records:
        endpoint_ok = endpoint_ok and len(sequence) == int(length) and sequence == sequence.upper() and _bytes_sha256(sequence.encode("ascii")) == digest
    endpoint_order = [str(item[0]) for item in records]
    endpoint_order_hash = _bytes_sha256("\n".join(endpoint_order).encode("ascii"))
    full_layout = _layout((str(digest), int(length)) for digest, length, _ in records)
    _check(
        checks,
        "endpoint_identity_order_and_window_coverage",
        endpoint_ok
        and endpoint_order_hash == registry["endpoint_order_sha256"]
        and full_layout == {"batches": 2690, "residue_window_tokens": 10_542_687, "windows": 19_143},
        {"endpoint_order_sha256": endpoint_order_hash, "layout": full_layout},
    )

    partition_table = pq.read_table(project_root / PARTITION_PATH, columns=["reference_sequence_sha256", "partition"])
    partition_by_sha = dict(zip(partition_table["reference_sequence_sha256"].to_pylist(), partition_table["partition"].to_pylist(), strict=True))
    partition_counts = Counter(partition_by_sha.values())
    training_indices = np.asarray([index for index, digest in enumerate(endpoint_order) if partition_by_sha[digest] == "train"], dtype=np.int64)
    _check(
        checks,
        "partition_census_and_training_only_index",
        partition_counts == Counter({"train": 11_900, "development": 2_550, "protected_test": 2_550}) and training_indices.size == 11_900,
        dict(sorted(partition_counts.items())),
    )

    for candidate, specification in EXPECTED_CANDIDATES.items():
        candidate_root = EMBEDDING_ROOT / candidate
        observed_files = {item.name for item in (project_root / candidate_root).iterdir() if item.is_file()}
        manifest_path = _safe_regular(project_root, candidate_root / "EMBEDDING_MANIFEST.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        model_binding = (
            observed_files == EXPECTED_EMBEDDING_FILES
            and manifest["candidate_id"] == candidate
            and manifest["repository_revision"] == specification["revision"]
            and manifest["checkpoint_sha256"] == specification["weight"]
            and manifest["tokenizer_file_hashes"] == specification["tokenizer"]
            and manifest["container_sha256"] == CONTAINER_SHA256
            and manifest["code_commit"] == EMBEDDING_PRODUCER_COMMIT
            and manifest["protocol_configuration_sha256"] == CONFIG_SHA256
            and all(_sha256(_safe_regular(project_root, CACHE_ROOT / candidate / name)) == digest for name, digest in specification["tokenizer"].items())
            and _sha256(_safe_regular(project_root, CACHE_ROOT / candidate / "model.safetensors")) == specification["weight"]
        )
        _check(checks, f"{candidate}_independent_binding_and_file_set", model_binding, {"files": sorted(observed_files), "revision": manifest["repository_revision"]})

        matrix_path = _safe_regular(project_root, Path(manifest["matrix_path"]))
        matrix = np.load(matrix_path, mmap_mode="r", allow_pickle=False)
        matrix_ok = matrix.shape == (17_000, specification["dimension"]) and matrix.dtype == np.float32 and _all_finite(matrix) and _sha256(matrix_path) == manifest["matrix_sha256"]
        _check(checks, f"{candidate}_independent_matrix_shape_dtype_finiteness", matrix_ok, {"dtype": str(matrix.dtype), "shape": list(matrix.shape)})

        entries = manifest["vectors"]
        vector_ok = len(entries) == 17_000
        cache_keys: set[str] = set()
        for index, entry in enumerate(entries):
            digest, length, _ = records[index]
            vector_hash = _bytes_sha256(np.ascontiguousarray(matrix[index], dtype=np.float32).tobytes(order="C"))
            expected_key = _cache_key(candidate, specification["revision"], specification["weight"], str(digest))
            vector_ok = vector_ok and entry["row_index"] == index and entry["sequence_sha256"] == digest and entry["sequence_length"] == length and entry["vector_sha256"] == vector_hash and entry["cache_key"] == expected_key and entry["vector_dtype"] == "float32" and entry["vector_dimension"] == specification["dimension"] and entry["code_commit"] == EMBEDDING_PRODUCER_COMMIT
            cache_keys.add(entry["cache_key"])
        _check(checks, f"{candidate}_independent_all_vector_hashes", vector_ok and len(cache_keys) == 17_000, {"cache_keys": len(cache_keys), "vectors": len(entries)})

        normalizer_path = _safe_regular(project_root, Path(manifest["normalization"]["normalizer_path"]))
        with np.load(normalizer_path, allow_pickle=False) as normalizer:
            saved_indices = normalizer["training_indices"]
            mean = normalizer["mean"]
            raw_std = normalizer["raw_standard_deviation"]
            std = normalizer["standard_deviation"]
        training = matrix[training_indices].astype(np.float64)
        expected_mean = training.mean(axis=0, dtype=np.float64)
        expected_raw_std = training.std(axis=0, dtype=np.float64, ddof=0)
        expected_std = np.maximum(expected_raw_std, 1e-6)
        normalizer_ok = np.array_equal(saved_indices, training_indices) and np.array_equal(mean, expected_mean) and np.array_equal(raw_std, expected_raw_std) and np.array_equal(std, expected_std) and _sha256(normalizer_path) == manifest["normalization"]["normalizer_sha256"]
        standardized_path = _safe_regular(project_root, Path(manifest["normalization"]["standardized_matrix_path"]))
        standardized = np.load(standardized_path, mmap_mode="r", allow_pickle=False)
        maximum_standardized_difference = 0.0
        for start in range(0, 17_000, 512):
            expected = ((matrix[start : start + 512].astype(np.float64) - mean) / std).astype(np.float32)
            maximum_standardized_difference = max(maximum_standardized_difference, float(np.max(np.abs(expected - standardized[start : start + 512]))))
        _check(checks, f"{candidate}_independent_training_only_normalization", normalizer_ok and standardized.shape == matrix.shape and standardized.dtype == np.float32 and _all_finite(standardized) and maximum_standardized_difference == 0.0 and _sha256(standardized_path) == manifest["normalization"]["standardized_matrix_sha256"], {"maximum_standardized_difference": maximum_standardized_difference, "training_endpoints": int(saved_indices.size)})

        repeat_report_path = _safe_regular(project_root, Path(manifest["repeat_report_path"]))
        repeat_report = json.loads(repeat_report_path.read_text(encoding="utf-8"))
        repeat_path = _safe_regular(project_root, Path(manifest["repeat_matrix_path"]))
        repeated = np.load(repeat_path, mmap_mode="r", allow_pickle=False)
        selected = sorted(sorted(range(17_000), key=lambda index: hashlib.sha256(f"{candidate}:{endpoint_order[index]}".encode("ascii")).digest())[:170], key=lambda index: (int(records[index][1]), endpoint_order[index]))
        differences = np.max(np.abs(repeated - matrix[selected]), axis=1)
        repeat_maximum = float(differences.max(initial=0.0))
        repeat_entries_ok = len(repeat_report["records"]) == 170
        for position, entry in enumerate(repeat_report["records"]):
            index = selected[position]
            repeat_entries_ok = repeat_entries_ok and entry["repeat_row_index"] == position and entry["row_index"] == index and entry["sequence_sha256"] == endpoint_order[index] and entry["maximum_absolute_difference"] == float(differences[position]) and entry["repeat_vector_sha256"] == _bytes_sha256(np.ascontiguousarray(repeated[position]).tobytes(order="C"))
        repeat_layout = _layout((endpoint_order[index], int(records[index][1])) for index in selected)
        repeat_ok = repeated.shape == (170, specification["dimension"]) and repeated.dtype == np.float32 and _all_finite(repeated) and repeat_maximum <= 1e-6 and repeat_report["maximum_absolute_difference"] == repeat_maximum and repeat_report["repeat_count"] == 170 and repeat_entries_ok and all(manifest["repeat_extraction"][key] == value for key, value in repeat_layout.items()) and _sha256(repeat_path) == manifest["repeat_matrix_sha256"]
        _check(checks, f"{candidate}_independent_bottom_hash_repeat", repeat_ok, {"layout": repeat_layout, "maximum_absolute_difference": repeat_maximum})

    p = pq.read_table(project_root / P_PATH, columns=["pair_id", "endpoint_a_partition", "endpoint_b_partition", "state", "sampling_weight_numerator", "sampling_weight_denominator"])
    u = pq.read_table(project_root / U_PATH, columns=["pair_id", "endpoint_a_partition", "endpoint_b_partition", "state", "stratum_id", "unlabeled_population", "sample_size", "inclusion_probability_numerator", "inclusion_probability_denominator", "sampling_weight_numerator", "sampling_weight_denominator"])
    strata = pq.read_table(project_root / STRATA_PATH)
    p_ok = p.num_rows == 16_799 and pc.count_distinct(p["pair_id"]).as_py() == 16_799 and pc.unique(p["state"]).to_pylist() == ["released_positive"] and set(p["endpoint_a_partition"].to_pylist()) == {"train"} and set(p["endpoint_b_partition"].to_pylist()) == {"train"} and np.all(p["sampling_weight_numerator"].to_numpy() == 1) and np.all(p["sampling_weight_denominator"].to_numpy() == 1)
    u_num = u["sampling_weight_numerator"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
    u_den = u["sampling_weight_denominator"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
    inc_num = u["inclusion_probability_numerator"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
    inc_den = u["inclusion_probability_denominator"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
    population = u["unlabeled_population"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
    sample_size = u["sample_size"].to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
    u_ok = u.num_rows == 2_000_000 and pc.count_distinct(u["pair_id"]).as_py() == 2_000_000 and pc.unique(u["state"]).to_pylist() == ["unlabeled"] and pc.unique(u["endpoint_a_partition"]).to_pylist() == ["train"] and pc.unique(u["endpoint_b_partition"]).to_pylist() == ["train"] and np.all(inc_num * population == inc_den * sample_size) and np.all(u_num * sample_size == u_den * population) and np.all(inc_num * u_num == inc_den * u_den) and np.all(u_num > 0) and np.all(u_den > 0)
    stratum_weights = {str(row["stratum_id"]): (int(row["sampling_weight_numerator"]), int(row["sampling_weight_denominator"]), int(row["sample_size"])) for row in strata.to_pylist()}
    observed_counts = Counter(u["stratum_id"].to_pylist())
    stratum_ok = strata.num_rows == 36 and len(stratum_weights) == 36 and all(observed_counts[key] == value[2] for key, value in stratum_weights.items())
    for batch in u.select(["stratum_id", "sampling_weight_numerator", "sampling_weight_denominator"]).to_batches(max_chunksize=65_536):
        for key, numerator, denominator in zip(batch["stratum_id"].to_pylist(), batch["sampling_weight_numerator"].to_pylist(), batch["sampling_weight_denominator"].to_pylist(), strict=True):
            expected_numerator, expected_denominator, _ = stratum_weights[str(key)]
            if (int(numerator), int(denominator)) != (expected_numerator, expected_denominator):
                stratum_ok = False
                break
    _check(checks, "public_P_U_census_state_and_exact_rational_weights", p_ok and u_ok and stratum_ok, {"P": p.num_rows, "U": u.num_rows, "mean_U_weight_float64": float(np.mean(u_num.astype(np.float64) / u_den.astype(np.float64), dtype=np.float64)), "strata": strata.num_rows})

    counts = np.bincount((np.arange(2_000_000, dtype=np.int64) + 4) % 16_799, minlength=16_799)
    fixture_order = sorted(("pair-c", "pair-a", "pair-b"), key=lambda pair_id: (_order_key(20260803, 1, "U", pair_id), pair_id))
    objective_ok = counts.min() == 119 and counts.max() == 120 and int(np.sum(counts == 120)) == 919 and fixture_order == ["pair-c", "pair-b", "pair-a"] and math.isclose(float(np.logaddexp(0.0, -(2.0 - 1.0))), 0.31326168751822286)
    _check(checks, "independent_objective_order_and_positive_coverage", objective_ok, {"ceiling_count": int(np.sum(counts == 120)), "fixture_order": fixture_order, "maximum_repetitions": int(counts.max()), "minimum_repetitions": int(counts.min())})

    source_ok, source_detail = _source_contract(project_root)
    parameter_counts = source_detail["parameter_counts"]
    _check(checks, "independent_model_baseline_objective_source_contract", source_ok and parameter_counts == {"lightweight_esm2_150m_linear": 1922, "esm2_650m_linear_ablation": 3842, "esm2_650m_nonlinear_no_gate_ablation": 426625, "esm2_650m_partner_gated_primary": 492417} and max(parameter_counts.values()) < 2_000_000, source_detail)

    registry_paths = "\n".join(sorted(registered_paths))
    executable_paths = [project_root / "src/ipin_openppi/stage1" / name for name in ("baselines.py", "models.py", "objective.py", "preparation.py", "training.py")]
    no_leakage = all(fragment not in registry_paths and all(fragment not in path.read_text(encoding="utf-8") for path in executable_paths) for fragment in FORBIDDEN_FRAGMENTS)
    allowed_registry_prefixes = ("artifacts/embeddings/", "artifacts/validation/", "data/canonical/benchmark_eligibility", "data/canonical/final_benchmark_component_split")
    no_leakage = no_leakage and all(path.startswith(allowed_registry_prefixes) for path in registered_paths)
    _check(checks, "public_only_visibility_and_absence_of_sensitive_inputs", no_leakage, {"registered_paths": sorted(registered_paths), "source_modules_scanned": [path.name for path in executable_paths]})

    gpu_hours = float(registry["summary"]["gpu_hours"])
    embedding_bytes = int(registry["summary"]["embedding_bytes"])
    _check(checks, "pretraining_compute_storage_and_candidate_budget", len(EXPECTED_CANDIDATES) == 2 and gpu_hours < 100 and embedding_bytes < 100 * 1024**3, {"candidate_count": 2, "embedding_bytes": embedding_bytes, "gpu_hours": gpu_hours})

    failures = [item for item in checks if item["status"] != "pass"]
    report = {
        "checks": checks,
        "independence": {
            "imports_production_stage1_modules": False,
            "imports_torch_or_model_framework": False,
            "method": "clean_room_reimplementation_and_artifact_rehash",
            "production_evidence_commit": "f2277346ee77d2fd22753a7fc1b846e09575420b",
        },
        "protocol_configuration_sha256": CONFIG_SHA256,
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "summary": {"fail": len(failures), "pass": len(checks) - len(failures), "warning": 0},
    }
    _write_json(output, report)
    if failures:
        raise RuntimeError(f"independent pre-training validation failed: {failures}")
    return report


if __name__ == "__main__":
    root = Path.cwd().resolve(strict=True)
    validate(root, root / VALIDATION_ROOT / "INDEPENDENT_PRETRAINING_VALIDATION_REPORT.json")
