#!/usr/bin/env python3
"""Clean-room independent validation of the DEC-0032 pre-release boundary.

This script intentionally imports no ``ipin_openppi`` module.  It rehashes the
frozen implementation, reconstructs consequential mathematics independently,
and inspects selected checkpoints with a clean-room functional forward.
"""

from __future__ import annotations

import ast
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from torch.nn import functional as F
import yaml


EXECUTION_ID = "development_release_and_evaluation_execution_v1"
CONFIG = Path("configs/development_release_and_evaluation_execution_v1.yaml")
CONFIG_SHA256 = "d74c683bbeb57e8b455efc789f487ca20df7a128ab0ec27b317dc602eda3e57d"
PRODUCTION_AUDIT = Path(
    "artifacts/validation/development_evaluation/development_release_and_evaluation_v1/"
    "PRE_RELEASE_PRODUCTION_AUDIT_REPORT.json"
)
PRODUCTION_AUDIT_SHA256 = "609de99b92e4b4be56a98b61823618056be1cb8bf156cbe51c273f505a0c7ad9"
PRODUCTION_CODE_COMMIT = "21aa040484eec533a8f519f1e70c11a817317ba7"
PRODUCTION_EVIDENCE_COMMIT = "9e17cfa0ac3e2654c80dfc176c0b45e35a1f0d50"
TRAINING_REGISTRY_SHA256 = "11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318"
SOURCE_HASHES = {
    "src/ipin_openppi/development_evaluation/release.py": "24a21cd7c983bdf8f4195cb4136171bbb5f68cc6deca5bdc44a31d8df38882e9",
    "src/ipin_openppi/development_evaluation/scoring.py": "a224df19af1022623720928a4d777d1ba727d61295a27f32516e679dda8f3107",
    "src/ipin_openppi/development_evaluation/semantics.py": "5e63276dbb769659dcb3ca636f0022c485a05bd82f5fc6855ee6aa5b2ee7bd00",
    "src/ipin_openppi/development_evaluation/evaluation.py": "df8b4949c3e94120a816ea981ad99dd4138826cd896e33153980ea4763fec38f",
}
OUTPUT = Path(
    "artifacts/validation/development_evaluation/development_release_and_evaluation_v1/"
    "PRE_RELEASE_INDEPENDENT_VALIDATION_REPORT.json"
)
FAMILIES = {
    "lightweight_esm2_150m_linear": 1_922,
    "esm2_650m_linear_ablation": 3_842,
    "esm2_650m_nonlinear_no_gate_ablation": 426_625,
    "esm2_650m_partner_gated_primary": 492_417,
}
SEEDS = (20260803, 20260817, 20260831)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_regular(project_root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".private" in relative.parts:
        raise RuntimeError(f"private or absolute path prohibited: {relative}")
    root = project_root.resolve(strict=True)
    target = (root / relative).absolute()
    target.relative_to(root)
    current = target
    while True:
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"symlink prohibited: {current}")
        if current == root:
            break
        current = current.parent
    if not stat.S_ISREG(target.stat(follow_symlinks=False).st_mode):
        raise RuntimeError(f"regular file required: {relative}")
    return target


def _check(checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any) -> None:
    checks.append(
        {"check_id": check_id, "status": "pass" if condition else "fail", "detail": detail}
    )


def _all_finite(value: Any) -> bool:
    if torch.is_tensor(value):
        return bool(torch.isfinite(value).all())
    if isinstance(value, np.ndarray):
        return bool(np.isfinite(value).all()) if value.dtype.kind in "fci" else True
    if isinstance(value, dict):
        return all(_all_finite(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return all(_all_finite(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def _commutative(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    denominator = torch.linalg.vector_norm(a, dim=-1) * torch.linalg.vector_norm(b, dim=-1)
    if torch.any(denominator == 0):
        raise RuntimeError("zero clean-room embedding vector")
    cosine = ((a * b).sum(dim=-1) / denominator).unsqueeze(-1)
    return torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)


def _independent_score(
    family: str, state: Mapping[str, torch.Tensor], a: torch.Tensor, b: torch.Tensor
) -> torch.Tensor:
    if family in ("lightweight_esm2_150m_linear", "esm2_650m_linear_ablation"):
        return F.linear(_commutative(a, b), state["output.weight"], state["output.bias"]).squeeze(-1)
    projected_a = F.gelu(F.linear(a, state["projection.weight"], state["projection.bias"]), approximate="none")
    projected_b = F.gelu(F.linear(b, state["projection.weight"], state["projection.bias"]), approximate="none")
    if family == "esm2_650m_partner_gated_primary":
        conditioned_a = projected_a * torch.sigmoid(
            F.linear(projected_b, state["gate.weight"], state["gate.bias"])
        )
        conditioned_b = projected_b * torch.sigmoid(
            F.linear(projected_a, state["gate.weight"], state["gate.bias"])
        )
    else:
        conditioned_a, conditioned_b = projected_a, projected_b
    hidden = F.gelu(
        F.linear(_commutative(conditioned_a, conditioned_b), state["hidden.weight"], state["hidden.bias"]),
        approximate="none",
    )
    return F.linear(hidden, state["output.weight"], state["output.bias"]).squeeze(-1)


def _ht(
    p_score: Sequence[float],
    u_score: Sequence[float],
    u_weight: Sequence[float],
    p_multiplier: Sequence[float] | None = None,
    u_multiplier: Sequence[float] | None = None,
) -> float:
    p = np.asarray(p_score, dtype=np.float64)
    u = np.asarray(u_score, dtype=np.float64)
    weight = np.asarray(u_weight, dtype=np.float64)
    pm = np.ones(p.size) if p_multiplier is None else np.asarray(p_multiplier, dtype=np.float64)
    um = np.ones(u.size) if u_multiplier is None else np.asarray(u_multiplier, dtype=np.float64)
    numerator = 0.0
    for pi, p_value in enumerate(p):
        for ui, u_value in enumerate(u):
            numerator += pm[pi] * weight[ui] * um[ui] * (
                float(p_value > u_value) + 0.5 * float(p_value == u_value)
            )
    return numerator / (pm.sum() * np.dot(weight, um))


def _cell_seed(cell_id: str) -> int:
    return int.from_bytes(
        hashlib.sha256(f"20260803:bootstrap:{cell_id}".encode("utf-8")).digest()[:8],
        "big",
    )


def _draw_counts(component_count: int, cell_id: str, replicates: int) -> np.ndarray:
    generator = np.random.Generator(np.random.PCG64DXSM(_cell_seed(cell_id)))
    raw = generator.integers(0, component_count, size=(replicates, component_count), dtype=np.int64)
    return np.stack([np.bincount(row, minlength=component_count) for row in raw])


def _pair_multiplier(counts: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.where(a == b, counts[a], counts[a] * counts[b])


def _bootstrap_fixture(replicates: int = 2_000) -> np.ndarray:
    p_score = [0.8, 0.3]
    u_score = [0.1, 0.6, 0.3, 0.0]
    u_weight = [2.0, 1.0, 3.0, 1.0]
    # Lexicographic components a,b,c.
    p_a, p_b = np.asarray([0, 1]), np.asarray([1, 1])
    u_a, u_b = np.asarray([0, 1, 2, 0]), np.asarray([0, 2, 2, 2])
    draws = _draw_counts(3, "fixture", replicates)
    values = np.full(replicates, np.nan, dtype=np.float64)
    for index, counts in enumerate(draws):
        pm = _pair_multiplier(counts, p_a, p_b)
        um = _pair_multiplier(counts, u_a, u_b)
        if pm.sum() and np.dot(u_weight, um):
            values[index] = _ht(p_score, u_score, u_weight, pm, um)
    return values


def _string_constants(tree: ast.AST) -> list[str]:
    return [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite independent evidence: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def validate(project_root: Path, output: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    config_path = _safe_regular(project_root, CONFIG)
    audit_path = _safe_regular(project_root, PRODUCTION_AUDIT)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    _check(
        checks,
        "frozen_production_commit_config_and_audit",
        _sha256(config_path) == CONFIG_SHA256
        and _sha256(audit_path) == PRODUCTION_AUDIT_SHA256
        and audit.get("status") == "pass"
        and audit.get("execution_id") == EXECUTION_ID
        and audit.get("development_private_key_resolved_or_accessed") is False
        and audit.get("protected_private_key_resolved_or_accessed") is False,
        {
            "production_code_commit": PRODUCTION_CODE_COMMIT,
            "production_evidence_commit": PRODUCTION_EVIDENCE_COMMIT,
            "config_sha256": _sha256(config_path),
            "production_audit_sha256": _sha256(audit_path),
        },
    )

    immutable_ok = True
    immutable_records = {}
    for section in ("authority", "frozen_inputs"):
        record = config[section]
        for hash_key, expected in record.items():
            if not hash_key.endswith("_sha256") or hash_key[: -len("_sha256")] not in record:
                continue
            path_key = hash_key[: -len("_sha256")]
            observed = _sha256(_safe_regular(project_root, Path(str(record[path_key]))))
            immutable_records[f"{section}.{path_key}"] = observed
            immutable_ok &= observed == expected
    for section, path_key, hash_key in (
        ("development_release", "ciphertext", "ciphertext_sha256"),
        ("development_release", "certificate", "certificate_sha256"),
        ("protected_boundary", "protected_candidates_ciphertext", "protected_candidates_ciphertext_sha256"),
        ("protected_boundary", "protected_truth_ciphertext", "protected_truth_ciphertext_sha256"),
    ):
        record = config[section]
        observed = _sha256(_safe_regular(project_root, Path(record[path_key])))
        immutable_records[f"{section}.{path_key}"] = observed
        immutable_ok &= observed == record[hash_key]
    _check(
        checks,
        "independent_authority_input_embedding_and_sealed_hashes",
        immutable_ok,
        immutable_records,
    )

    source_ok = True
    source_text = {}
    for relative, expected in SOURCE_HASHES.items():
        path = _safe_regular(project_root, Path(relative))
        source_ok &= _sha256(path) == expected
        source_text[relative] = path.read_text(encoding="utf-8")
    _check(checks, "independent_exact_production_source_freeze", source_ok, SOURCE_HASHES)

    release_text = source_text["src/ipin_openppi/development_evaluation/release.py"]
    release_tree = ast.parse(release_text)
    imports = []
    calls = []
    for node in ast.walk(release_tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    private_pem_strings = sorted(
        value for value in _string_constants(release_tree) if ".private/" in value and value.endswith(".pem")
    )
    release_boundary_ok = (
        "private_key_paths" not in imports
        and "private_key_paths" not in calls
        and "glob" not in calls
        and "rglob" not in calls
        and private_pem_strings
        == [".private/pair_level_pu_r_benchmark_artifacts_v1/development_release_private.pem"]
        and release_text.count("resolve_development_key_only(") == 2
    )
    config_private_pems = sorted(
        value
        for value in _string_constants(ast.parse(repr(config)))
        if ".private/" in value and value.endswith(".pem")
    )
    # repr(config) is not Python syntax for booleans? It is; retain a direct fallback.
    direct_private_pems = sorted(
        value
        for value in _walk_strings(config)
        if value.startswith(".private/") and value.endswith(".pem")
    )
    _check(
        checks,
        "independent_non_enumerating_development_only_key_call_graph",
        release_boundary_ok
        and direct_private_pems
        == [".private/pair_level_pu_r_benchmark_artifacts_v1/development_release_private.pem"]
        and config["protected_boundary"]["private_key_resolution_or_access"] == "prohibited"
        and config["protected_boundary"]["decryption"] == "prohibited",
        {"private_pem_paths": direct_private_pems, "resolver_calls_in_source": 2},
    )

    scoring_text = source_text["src/ipin_openppi/development_evaluation/scoring.py"]
    evaluation_text = source_text["src/ipin_openppi/development_evaluation/evaluation.py"]
    score_only_ok = all(
        token not in scoring_text
        for token in ("torch.optim", ".backward(", "optimizer.step", "build_model(")
    ) and all(
        token not in scoring_text + evaluation_text
        for token in ("protected_candidates.cms", "protected_truth.cms", "private.pem")
    )
    model_tokens = (
        "projected_a * gate_value.index_select(0, b)",
        "projected_b * gate_value.index_select(0, a)",
        "torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)",
        "np.mean(score_matrix[:, member_columns], axis=1, dtype=np.float64)",
    )
    _check(
        checks,
        "independent_score_only_model_and_ensemble_source",
        score_only_ok and all(token in scoring_text for token in model_tokens),
        {"optimizer_or_training_path": False, "required_model_tokens": list(model_tokens)},
    )

    registry_path = _safe_regular(project_root, Path(config["frozen_inputs"]["training_registry"]))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    run_by_id = {item["run_id"]: item for item in registry["run_summaries"]}
    checkpoint_ok = len(run_by_id) == 30
    family_counts: Counter[str] = Counter()
    maximum_swap = 0.0
    embedding_cache: dict[str, torch.Tensor] = {}
    for run_id, run in run_by_id.items():
        family = str(run["family"])
        family_counts[family] += 1
        checkpoint_record = run["selected_checkpoint"]
        checkpoint_path = _safe_regular(project_root, Path(checkpoint_record["path"]))
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        checkpoint_ok &= (
            _sha256(checkpoint_path) == checkpoint_record["sha256"]
            and checkpoint_path.stat().st_size == checkpoint_record["bytes"]
            and checkpoint_record["pass_index"] == 5
            and checkpoint["pass_index"] == 5
            and checkpoint["global_step"] == 2_445
            and _all_finite(checkpoint["model_state"])
            and sum(value.numel() for value in checkpoint["model_state"].values()) == FAMILIES[family]
        )
        candidate = "esm2_150m" if family == "lightweight_esm2_150m_linear" else "esm2_650m"
        if candidate not in embedding_cache:
            embedding_record = next(
                item
                for item in registry["artifacts"]
                if item["path"].endswith(f"/{candidate}/standardized_embeddings.f32.npy")
            )
            matrix_path = _safe_regular(project_root, Path(embedding_record["path"]))
            matrix = np.load(matrix_path, mmap_mode="r", allow_pickle=False)
            embedding_cache[candidate] = torch.from_numpy(np.array(matrix[:32], copy=True))
        fixture = embedding_cache[candidate]
        with torch.inference_mode():
            forward = _independent_score(family, checkpoint["model_state"], fixture[:16], fixture[16:32])
            reverse = _independent_score(family, checkpoint["model_state"], fixture[16:32], fixture[:16])
        difference = float(torch.max(torch.abs(forward - reverse)))
        maximum_swap = max(maximum_swap, difference)
        checkpoint_ok &= torch.isfinite(forward).all() and difference <= 1e-6
    _check(
        checks,
        "independent_all_30_checkpoint_hash_state_and_functional_symmetry",
        checkpoint_ok
        and family_counts
        == Counter(
            {
                "lightweight_esm2_150m_linear": 6,
                "esm2_650m_linear_ablation": 6,
                "esm2_650m_nonlinear_no_gate_ablation": 9,
                "esm2_650m_partner_gated_primary": 9,
            }
        ),
        {"family_counts": dict(family_counts), "swap_max_absolute_difference": maximum_swap},
    )

    ensemble_ok = len(registry["ensembles"]) == 10
    candidate_ids = set()
    for ensemble in registry["ensembles"]:
        candidate_ids.add(ensemble["candidate_id"])
        members = ensemble["members"]
        ensemble_ok &= (
            ensemble["ensemble_score"] == "arithmetic_mean_of_three_frozen_seed_scores"
            and len(members) == 3
            and tuple(member["seed"] for member in members) == SEEDS
            and all(member["selected_checkpoint"] == run_by_id[member["run_id"]]["selected_checkpoint"] for member in members)
        )
    _check(
        checks,
        "independent_exact_9_30_10_scorer_census",
        len(config["scorers"]["deterministic"]) == 9
        and config["scorers"]["deterministic_count"] == 9
        and len(run_by_id) == 30
        and ensemble_ok
        and len(candidate_ids) == 10,
        {"deterministic": 9, "selected_checkpoints": len(run_by_id), "ensembles": len(candidate_ids)},
    )

    metric = _ht([0.5, 1.0], [0.0, 0.5, 2.0], [1.0, 2.0, 1.0])
    audit_by_id = {item["check_id"]: item for item in audit["checks"]}
    production_metric = audit_by_id["exact_HT_concordance_and_half_ties"]["detail"]["fixture_metric"]
    _check(
        checks,
        "independent_HT_formula_half_ties_and_production_fixture",
        metric == 0.625 == production_metric,
        {"independent_fixture": metric, "production_fixture": production_metric},
    )

    bootstrap = _bootstrap_fixture()
    gpu_detail = audit_by_id["GPU_bootstrap_equals_CPU_reference_with_identical_draws"]["detail"]
    bootstrap_ok = (
        bootstrap.shape == (2_000,)
        and int(np.isfinite(bootstrap).sum()) == gpu_detail["finite_replicates"]
        and float(gpu_detail["maximum_absolute_difference"]) <= 1e-15
    )
    _check(
        checks,
        "independent_PCG64DXSM_pigeonhole_bootstrap_reconstruction",
        bootstrap_ok,
        {
            "cell_seed": _cell_seed("fixture"),
            "finite_replicates": int(np.isfinite(bootstrap).sum()),
            "production_GPU_CPU_maximum_absolute_difference": gpu_detail["maximum_absolute_difference"],
        },
    )

    similarity = np.asarray(
        [[1.0, 0.2, 0.3, 0.4], [0.1, 1.0, 0.8, 0.2], [0.6, 0.1, 1.0, 0.9]],
        dtype=np.float64,
    )
    edges = ((0, 1), (1, 2), (2, 3))
    direct = max(
        max(min(similarity[0, u], similarity[1, v]), min(similarity[0, v], similarity[1, u]))
        for u, v in edges
    )
    neighbor = np.zeros(4)
    for u in range(4):
        adjacent = [v for left, right in edges for v in ([right] if left == u else [left] if right == u else [])]
        neighbor[u] = max((similarity[1, v] for v in adjacent), default=0.0)
    identity = max(min(similarity[0, u], neighbor[u]) for u in range(4))
    _check(
        checks,
        "independent_exact_interolog_max_min_identity",
        direct == identity == 1.0,
        {"edge_enumeration": direct, "neighbor_max_identity": identity},
    )

    evaluation = config["evaluation"]
    threshold = config["complexity_thresholds"]
    policy_ok = (
        evaluation["primary_cells"] == ["C3_development", "C2_development", "C1_development"]
        and evaluation["bootstrap"]["replicates"] == 2_000
        and evaluation["bootstrap"]["generator"] == "PCG64DXSM"
        and evaluation["selection_quantization"] == "decimal_0.001_ROUND_HALF_UP"
        and Decimal("0.6125").quantize(Decimal("0.001"), rounding=ROUND_HALF_UP) == Decimal("0.613")
        and threshold["partner_vs_strongest_simple_sequence_C3"] == 0.02
        and threshold["partner_vs_650m_linear_C3"] == 0.01
        and threshold["partner_vs_matched_no_gate_C3"] == 0.005
        and config["c1_novel_U"]["resampling_or_selection_use"] == "prohibited"
        and config["degree_and_hub"]["quantitative_floor"] == {
            "positive_pairs": 100,
            "participating_components": 10,
        }
    )
    required_policy_tokens = (
        "C3_vs_strongest_simple_at_least_0_02",
        "C3_vs_650m_linear_at_least_0_01",
        "C3_vs_matched_no_gate_at_least_0_005",
        "positive_named_source_direction",
        "positive_outside_top_10_percent_hubs",
        "withdraw_C1_gain_claim",
        "stop_before_protected_evaluation",
    )
    policy_ok &= all(token in evaluation_text for token in required_policy_tokens)
    _check(
        checks,
        "independent_metric_selection_stratification_complexity_and_kill_projection",
        policy_ok,
        {"required_policy_tokens": list(required_policy_tokens), "thresholds": threshold},
    )

    active_gate = yaml.safe_load(
        _safe_regular(project_root, Path(config["authority"]["active_gate"])).read_text(encoding="utf-8")
    )
    _check(
        checks,
        "independent_pre_release_information_flow_and_closed_protected_boundary",
        active_gate["gates"]["development"]["decrypt_authorized_now"] is False
        and active_gate["gates"]["protected_test"]["candidate_or_truth_access_authorized"] is False
        and active_gate["gates"]["protected_test"]["private_key_access_authorized"] is False
        and audit["development_plaintext_accessed"] is False
        and audit["protected_candidates_or_truth_accessed"] is False,
        {
            "development_key_accessed": False,
            "development_plaintext_accessed": False,
            "protected_private_key_accessed": False,
            "protected_candidates_or_truth_accessed": False,
        },
    )

    failures = [item for item in checks if item["status"] != "pass"]
    report = {
        "schema_version": 1,
        "execution_id": EXECUTION_ID,
        "status": "pass" if not failures else "fail",
        "summary": {"pass": len(checks) - len(failures), "fail": len(failures), "warning": 0},
        "checks": checks,
        "independence": {
            "imports_production_development_modules": False,
            "imports_production_metric_or_selection": False,
            "method": "clean_room_hash_AST_formula_bootstrap_and_functional_checkpoint_reconstruction",
            "production_code_commit": PRODUCTION_CODE_COMMIT,
            "production_evidence_commit": PRODUCTION_EVIDENCE_COMMIT,
        },
        "development_private_key_resolved_or_accessed": False,
        "protected_private_key_resolved_or_accessed": False,
        "development_plaintext_accessed": False,
        "protected_candidates_or_truth_accessed": False,
    }
    _write_json(output, report)
    if failures:
        raise RuntimeError(f"independent development pre-release validation failed: {failures}")
    return report


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [item for child in value.values() for item in _walk_strings(child)]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [item for child in value for item in _walk_strings(child)]
    return []


if __name__ == "__main__":
    root = Path.cwd().resolve(strict=True)
    report = validate(root, root / OUTPUT)
    print(
        "development_prerelease_independent_validation: "
        f"{report['status'].upper()} checks={report['summary']['pass']}"
    )
