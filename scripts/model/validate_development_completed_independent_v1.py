#!/usr/bin/env python3
"""Clean-room validation of the complete frozen development evaluation.

This script intentionally imports no ipin_openppi module. It reads only the
already frozen score/evaluation custody tree plus public training inputs,
embeddings, and selected checkpoints. It performs inference and validation
only: no optimizer, training, decryption, release, or protected path exists.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, Mapping, Sequence

import numpy as np
import pyarrow.parquet as pq
from scipy import sparse
import torch
from torch.nn import functional as F


PRODUCTION_EVIDENCE_COMMIT = "c7ef1736bce641f21297b66d1ac086f825c6a108"
PRODUCTION_REGISTRY_SHA256 = (
    "42aa8b19c4c5cfaf36bfbe1bd19bdf74e7de81df27cccb793809a5ec80d0e189"
)
PRODUCTION_AUDIT_SHA256 = (
    "1724a645e39ec232827aa8d1a8b6142fd257ec9404f133e985f2330e15e073ba"
)
TRAINING_REGISTRY_SHA256 = (
    "11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318"
)
SCORING_MANIFEST_SHA256 = (
    "c82be153593ad46101f1ce49e1c79d341da535c71b34ded748c63e478b10dc99"
)
RESULTS_MANIFEST_SHA256 = (
    "e6b5455e3c1e0346b5b9c9a358db7abc628732b57bab2ec778992d2fbe9c8299"
)
SELECTION_TRACE_SHA256 = (
    "ac583545f2dd3c8305dc477cb2d414e75a31800afcb29ddaedc6276cab165c45"
)
CONFIG_SHA256 = "d74c683bbeb57e8b455efc789f487ca20df7a128ab0ec27b317dc602eda3e57d"

VALIDATION_ROOT = Path(
    "artifacts/validation/development_evaluation/"
    "development_release_and_evaluation_v1"
)
RESULTS_ROOT = Path(
    "artifacts/results/development_evaluation/"
    "development_release_and_evaluation_v1"
)
PRIVATE_EVALUATION_ROOT = Path(
    ".private/development_release_and_evaluation_v1/evaluation"
)
TRAINING_REGISTRY = Path(
    "artifacts/validation/model_execution/stage1_model_execution_v1/"
    "TRAINING_ARTIFACT_REGISTRY.json"
)
ENDPOINTS = Path(
    "data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/"
    "eligible_reference_sequences/part-00000.parquet"
)
PARTITIONS = Path(
    "data/canonical/final_benchmark_component_split_v1/"
    "endpoint_partition_assignments/part-00000.parquet"
)
TRAINING_POSITIVE = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "positive_pairs/part-00000.parquet"
)
TRAINING_UNLABELED = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "unlabeled_pairs/part-00000.parquet"
)
EMBEDDINGS = {
    "esm2_150m": (
        Path(
            "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/"
            "esm2_150m/standardized_embeddings.f32.npy"
        ),
        "deacaf3c087ca8da7ea5bd5fafe5760dfa53978bb58a145b4733e4d3ca949110",
        (17_000, 640),
    ),
    "esm2_650m": (
        Path(
            "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/"
            "esm2_650m/standardized_embeddings.f32.npy"
        ),
        "d54d9d943088a9b0c301242b1c717c668c6561721496ea071cd5c512e5e3475c",
        (17_000, 1_280),
    ),
}
SOURCE_HASHES = {
    "src/ipin_openppi/development_evaluation/scoring.py":
        "874b84270be2fe47211a3936907762ebb6442052eb6928adbdcda50ace60ca5f",
    "src/ipin_openppi/development_evaluation/evaluation.py":
        "df8b4949c3e94120a816ea981ad99dd4138826cd896e33153980ea4763fec38f",
    "src/ipin_openppi/development_evaluation/semantics.py":
        "5e63276dbb769659dcb3ca636f0022c485a05bd82f5fc6855ee6aa5b2ee7bd00",
    "src/ipin_openppi/development_evaluation/completed_audit.py":
        "9ba24d9d1ce7cc1eab9a8c62c1407306a77020c3c579aa119a71b62e9fb8c035",
    "scripts/model/run_development_scoring_v1.py":
        "3adc6b763a1b5862bfc63f68c2f89b3ad734316b0651d550cbd45ac66391c782",
    "scripts/model/evaluate_development_v1.py":
        "f9dfe6a5baa2096794fb9fefcc2ed16229246f1385c601836e76c8896eee9a2e",
    "scripts/model/audit_development_completed_v1.py":
        "18cb40412176bdc412d224f6b5f91ca1a25281aabea3672cf2dccfbee399afd1",
}

CELLS = (
    "C3_development",
    "source_exclusive:HI-II-14:C3_development",
    "source_exclusive:HuRI:C3_development",
    "C2_development",
    "source_exclusive:HI-II-14:C2_development",
    "source_exclusive:HuRI:C2_development",
    "C1_development",
    "source_exclusive:HI-II-14:C1_development",
    "source_exclusive:HuRI:C1_development",
)
PRIMARY_CELLS = ("C3_development", "C2_development", "C1_development")
DETERMINISTIC = (
    "deterministic_hash",
    "training_degree_sum",
    "preferential_attachment",
    "component_degree_mass_product",
    "training_common_neighbors",
    "sequence_length_sum",
    "sequence_length_ratio",
    "within_pair_3mer_cosine",
    "exact_training_interolog_3mer",
)
SHORTCUTS = (
    "training_degree_sum",
    "preferential_attachment",
    "component_degree_mass_product",
    "training_common_neighbors",
    "sequence_length_sum",
    "sequence_length_ratio",
)
SIMPLE_SEQUENCE = ("within_pair_3mer_cosine", "exact_training_interolog_3mer")
COMPLEXITY = {
    "lightweight_esm2_150m_linear": 0,
    "esm2_650m_linear_ablation": 1,
    "esm2_650m_nonlinear_no_gate_ablation": 2,
    "esm2_650m_partner_gated_primary": 3,
}
PARAMETERS = {
    "lightweight_esm2_150m_linear": 1_922,
    "esm2_650m_linear_ablation": 3_842,
    "esm2_650m_nonlinear_no_gate_ablation": 426_625,
    "esm2_650m_partner_gated_primary": 492_417,
}
KMER_ALPHABET = "ACDEFGHIKLMNPQRSTVWYX"
KMER_INDEX = {
    a + b + c: (i * len(KMER_ALPHABET) + j) * len(KMER_ALPHABET) + k
    for i, a in enumerate(KMER_ALPHABET)
    for j, b in enumerate(KMER_ALPHABET)
    for k, c in enumerate(KMER_ALPHABET)
}


@dataclass
class CellView:
    cell_id: str
    rows_path: Path
    score_path: Path
    scores: np.ndarray
    scorer_ids: list[str]
    scorer_index: dict[str, int]
    endpoint_a: np.ndarray
    endpoint_b: np.ndarray


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_regular(project_root: Path, relative: Path) -> Path:
    if relative.is_absolute():
        raise RuntimeError(f"absolute path prohibited: {relative}")
    if any(
        token in relative.as_posix().lower()
        for token in ("private.pem", "protected_candidates", "protected_truth")
    ):
        raise RuntimeError(f"protected or key path prohibited: {relative}")
    if ".private" in relative.parts:
        allowed_prefix = (".private", "development_release_and_evaluation_v1")
        if relative.parts[:2] != allowed_prefix:
            raise RuntimeError(f"private path outside completed evaluation custody: {relative}")
        allowed_log = (
            len(relative.parts) == 3
            and relative.name
            in {"SCORING_CONSOLE.log", "SCORING_RESUME_CONSOLE.log", "EVALUATION_CONSOLE.log"}
        )
        allowed_evaluation = (
            len(relative.parts) >= 4 and relative.parts[2] == "evaluation"
        )
        if not (allowed_log or allowed_evaluation):
            raise RuntimeError(f"development release/key path prohibited: {relative}")
    root = project_root.resolve(strict=True)
    target = (root / relative).absolute()
    target.relative_to(root)
    current = target
    while True:
        if stat.S_ISLNK(current.lstat().st_mode):
            raise RuntimeError(f"symlink prohibited: {current}")
        if current == root:
            break
        current = current.parent
    if not stat.S_ISREG(target.stat(follow_symlinks=False).st_mode):
        raise RuntimeError(f"regular file required: {relative}")
    return target


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def _check(
    checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any
) -> None:
    checks.append(
        {"check_id": check_id, "status": "pass" if condition else "fail", "detail": detail}
    )


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


def _contains_identity(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return (
        '"endpoint_a_sha256"' in text
        or '"endpoint_b_sha256"' in text
        or '"pair_id"' in text
        or "pair:" in text
    )


def _state_arrays(rows: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    states = np.asarray(rows["state"].to_pylist(), dtype=object)
    p = states == "released_positive"
    u = states == "unlabeled"
    numerator = np.asarray(rows["sampling_weight_numerator"].to_numpy(), dtype=np.float64)
    denominator = np.asarray(rows["sampling_weight_denominator"].to_numpy(), dtype=np.float64)
    weights = numerator / denominator
    if (
        not p.any()
        or not u.any()
        or not np.all(p | u)
        or np.any(p & u)
        or not np.all(weights[p] == 1.0)
        or np.any(weights[u] <= 0)
    ):
        raise RuntimeError("invalid clean-room P/U state or rational weights")
    return p, u, weights


def _concordance(p_score: np.ndarray, u_score: np.ndarray, u_weight: np.ndarray) -> float:
    order = np.argsort(u_score, kind="mergesort")
    sorted_scores = u_score[order]
    cumulative = np.concatenate(
        (
            np.asarray([0.0], dtype=np.float64),
            np.cumsum(u_weight[order], dtype=np.float64),
        )
    )
    left = np.searchsorted(sorted_scores, p_score, side="left")
    right = np.searchsorted(sorted_scores, p_score, side="right")
    favorable = cumulative[left] + 0.5 * (cumulative[right] - cumulative[left])
    return float(np.dot(np.ones(p_score.size, dtype=np.float64), favorable)) / (
        float(np.ones(p_score.size, dtype=np.float64).sum(dtype=np.float64))
        * float(np.sum(u_weight, dtype=np.float64))
    )


def _average_precision(
    p_score: np.ndarray, u_score: np.ndarray, u_weight: np.ndarray
) -> float:
    scores = np.concatenate((p_score, u_score))
    positive = np.concatenate(
        (np.ones(p_score.size, dtype=np.float64), np.zeros(u_score.size, dtype=np.float64))
    )
    total = np.concatenate((np.ones(p_score.size, dtype=np.float64), u_weight))
    order = np.argsort(-scores, kind="mergesort")
    scores = scores[order]
    positive = positive[order]
    total = total[order]
    group_end = np.r_[np.flatnonzero(scores[1:] != scores[:-1]), scores.size - 1]
    cumulative_positive = np.cumsum(positive, dtype=np.float64)
    cumulative_total = np.cumsum(total, dtype=np.float64)
    recall = cumulative_positive[group_end] / p_score.size
    precision = cumulative_positive[group_end] / cumulative_total[group_end]
    return float(np.dot(np.diff(np.r_[0.0, recall]), precision))


def _point_metrics(
    rows: Any,
    scores: np.ndarray,
    scorer_ids: Sequence[str],
    row_mask: np.ndarray | None = None,
) -> dict[str, dict[str, float]]:
    p, u, weights = _state_arrays(rows)
    if row_mask is not None:
        selected = np.asarray(row_mask, dtype=bool)
        p &= selected
        u &= selected
    if not p.any() or not u.any():
        return {}
    output: dict[str, dict[str, float]] = {}
    for column, scorer_id in enumerate(scorer_ids):
        concordance = _concordance(
            np.asarray(scores[p, column], dtype=np.float64),
            np.asarray(scores[u, column], dtype=np.float64),
            weights[u],
        )
        output[str(scorer_id)] = {
            "ht_positive_vs_U_concordance": concordance,
            "diagnostic_sampled_P_vs_U_AUROC": concordance,
            "diagnostic_sampled_P_vs_U_AUPRC": _average_precision(
                np.asarray(scores[p, column], dtype=np.float64),
                np.asarray(scores[u, column], dtype=np.float64),
                weights[u],
            ),
        }
    return output


def _degree_bin(value: int) -> str:
    if value <= 2:
        return str(value)
    for lower, upper in ((3, 4), (5, 9), (10, 19), (20, 49), (50, 99)):
        if lower <= value <= upper:
            return f"{lower}-{upper}"
    return "100+"


def _degree_stratum(left: int, right: int) -> str:
    bins = ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")
    rank = {value: index for index, value in enumerate(bins)}
    values = sorted((_degree_bin(left), _degree_bin(right)), key=rank.__getitem__)
    return f"{values[0]}|{values[1]}"


def _degree_hub(
    rows: Any,
    scores: np.ndarray,
    scorer_ids: Sequence[str],
    hubs: Mapping[str, frozenset[str]],
) -> dict[str, Any]:
    p, u, _ = _state_arrays(rows)
    degree_a = np.asarray(rows["endpoint_a_training_degree"].to_numpy(), dtype=np.int64)
    degree_b = np.asarray(rows["endpoint_b_training_degree"].to_numpy(), dtype=np.int64)
    strata = np.asarray(
        [_degree_stratum(int(a), int(b)) for a, b in zip(degree_a, degree_b, strict=True)],
        dtype=object,
    )
    component_a = np.asarray(rows["endpoint_a_component_id"].to_pylist(), dtype=object)
    component_b = np.asarray(rows["endpoint_b_component_id"].to_pylist(), dtype=object)
    degree_output: dict[str, Any] = {}
    for stratum in sorted(set(strata)):
        mask = strata == stratum
        positive_count = int(np.count_nonzero(mask & p))
        components = set(component_a[mask & p]) | set(component_b[mask & p])
        degree_output[str(stratum)] = {
            "positive_rows": positive_count,
            "unlabeled_rows": int(np.count_nonzero(mask & u)),
            "participating_positive_components": len(components),
            "status": (
                "quantitative"
                if positive_count >= 100 and len(components) >= 10
                else "descriptive_below_floor"
            ),
            "metrics": _point_metrics(rows, scores, scorer_ids, row_mask=mask),
        }
    endpoint_a = np.asarray(rows["endpoint_a_sha256"].to_pylist(), dtype=object)
    endpoint_b = np.asarray(rows["endpoint_b_sha256"].to_pylist(), dtype=object)
    hub_output: dict[str, Any] = {}
    for name, endpoints in hubs.items():
        contains = np.fromiter(
            (
                str(a) in endpoints or str(b) in endpoints
                for a, b in zip(endpoint_a, endpoint_b, strict=True)
            ),
            dtype=bool,
            count=rows.num_rows,
        )
        hub_output[name] = {
            "contains_hub": {
                "positive_rows": int(np.count_nonzero(contains & p)),
                "unlabeled_rows": int(np.count_nonzero(contains & u)),
                "metrics": _point_metrics(rows, scores, scorer_ids, row_mask=contains),
            },
            "excludes_hub": {
                "positive_rows": int(np.count_nonzero(~contains & p)),
                "unlabeled_rows": int(np.count_nonzero(~contains & u)),
                "metrics": _point_metrics(rows, scores, scorer_ids, row_mask=~contains),
            },
        }
    return {"degree_pair_strata": degree_output, "hub_views": hub_output}


def _correlations(scores: np.ndarray, scorer_ids: Sequence[str]) -> dict[str, Any]:
    controls = list(DETERMINISTIC[1:])
    index = {value: position for position, value in enumerate(scorer_ids)}
    output: dict[str, Any] = {}
    for scorer_id in scorer_ids:
        values = np.asarray(scores[:, index[scorer_id]], dtype=np.float64)
        record: dict[str, float | None] = {}
        for control in controls:
            comparator = np.asarray(scores[:, index[control]], dtype=np.float64)
            record[control] = (
                None
                if np.std(values) == 0 or np.std(comparator) == 0
                else float(np.corrcoef(values, comparator)[0, 1])
            )
        output[str(scorer_id)] = record
    return {"method": "unweighted_P_and_sampled_U_Pearson_diagnostic", "values": output}


def _commutative(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    denominator = torch.linalg.vector_norm(a, dim=-1) * torch.linalg.vector_norm(b, dim=-1)
    if torch.any(denominator == 0):
        raise RuntimeError("zero vector in clean-room model scoring")
    cosine = ((a * b).sum(dim=-1) / denominator).unsqueeze(-1)
    return torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)


def _model_batch(
    family: str,
    state: Mapping[str, torch.Tensor],
    embeddings: torch.Tensor,
    endpoint_a: torch.Tensor,
    endpoint_b: torch.Tensor,
    projected: torch.Tensor | None,
    gate_value: torch.Tensor | None,
) -> torch.Tensor:
    if family in ("lightweight_esm2_150m_linear", "esm2_650m_linear_ablation"):
        pair = _commutative(
            embeddings.index_select(0, endpoint_a),
            embeddings.index_select(0, endpoint_b),
        )
        return F.linear(pair, state["output.weight"], state["output.bias"]).squeeze(-1)
    if projected is None:
        raise RuntimeError("clean-room nonlinear projection missing")
    a = projected.index_select(0, endpoint_a)
    b = projected.index_select(0, endpoint_b)
    if family == "esm2_650m_partner_gated_primary":
        if gate_value is None:
            raise RuntimeError("clean-room partner gate missing")
        a = a * gate_value.index_select(0, endpoint_b)
        b = b * gate_value.index_select(0, endpoint_a)
    hidden = F.gelu(
        F.linear(_commutative(a, b), state["hidden.weight"], state["hidden.bias"]),
        approximate="none",
    )
    return F.linear(hidden, state["output.weight"], state["output.bias"]).squeeze(-1)


def _kmer_matrix(sequences: Sequence[str]) -> sparse.csr_matrix:
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    for row, sequence in enumerate(sequences):
        mapped = "".join(value if value in KMER_ALPHABET else "X" for value in sequence)
        counts = Counter(
            KMER_INDEX[mapped[index : index + 3]]
            for index in range(max(0, len(mapped) - 2))
        )
        norm = math.sqrt(sum(value * value for value in counts.values()))
        if norm:
            for column, value in sorted(counts.items()):
                rows.append(row)
                columns.append(column)
                values.append(value / norm)
    return sparse.csr_matrix(
        (np.asarray(values), (np.asarray(rows), np.asarray(columns))),
        shape=(len(sequences), len(KMER_ALPHABET) ** 3),
        dtype=np.float64,
    )


def _cell_seed(cell_id: str) -> int:
    payload = f"20260803:bootstrap:{cell_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def _draws(components: Sequence[str], cell_id: str) -> tuple[tuple[str, ...], np.ndarray]:
    ordered = tuple(sorted(set(map(str, components))))
    generator = np.random.Generator(np.random.PCG64DXSM(_cell_seed(cell_id)))
    raw = generator.integers(
        0, len(ordered), size=(2_000, len(ordered)), dtype=np.int64
    )
    counts = np.zeros((2_000, len(ordered)), dtype=np.int32)
    rows = np.arange(2_000, dtype=np.int64)[:, None]
    np.add.at(counts, (rows, raw), 1)
    return ordered, counts


def _percentile(values: np.ndarray) -> list[float]:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    lower, upper = np.percentile(finite, (2.5, 97.5), method="linear")
    return [float(lower), float(upper)]


def _bootstrap_gpu(
    rows: Any,
    scores: np.ndarray,
    scorer_ids: Sequence[str],
    bootstrap_scorers: Sequence[str],
    cell_id: str,
) -> tuple[np.ndarray, np.ndarray]:
    p, u, weights = _state_arrays(rows)
    component_a = tuple(map(str, rows["endpoint_a_component_id"].to_pylist()))
    component_b = tuple(map(str, rows["endpoint_b_component_id"].to_pylist()))
    components, counts = _draws(component_a + component_b, cell_id)
    index = {value: position for position, value in enumerate(components)}
    a = np.fromiter((index[value] for value in component_a), dtype=np.int64)
    b = np.fromiter((index[value] for value in component_b), dtype=np.int64)
    count_tensor = torch.from_numpy(counts).to(device="cuda", dtype=torch.float64)
    p_a = torch.from_numpy(a[p]).cuda()
    p_b = torch.from_numpy(b[p]).cuda()
    u_a = torch.from_numpy(a[u]).cuda()
    u_b = torch.from_numpy(b[u]).cuda()
    design = torch.from_numpy(weights[u]).to(device="cuda", dtype=torch.float64)
    scorer_index = {value: position for position, value in enumerate(scorer_ids)}
    distributions = np.full((len(bootstrap_scorers), 2_000), np.nan, dtype=np.float64)
    with torch.inference_mode():
        for scorer_position, scorer_id in enumerate(bootstrap_scorers):
            column = scorer_index[str(scorer_id)]
            p_score = np.asarray(scores[p, column], dtype=np.float64)
            u_score = np.asarray(scores[u, column], dtype=np.float64)
            order = np.argsort(u_score, kind="mergesort")
            sorted_score = u_score[order]
            left = np.searchsorted(sorted_score, p_score, side="left").astype(np.int64)
            right = np.searchsorted(sorted_score, p_score, side="right").astype(np.int64)
            order_t = torch.from_numpy(order).cuda()
            left_t = torch.from_numpy(left).cuda()
            right_t = torch.from_numpy(right).cuda()
            for start in range(0, 2_000, 16):
                stop = min(start + 16, 2_000)
                selected = count_tensor[start:stop]
                p_left, p_right = selected[:, p_a], selected[:, p_b]
                u_left, u_right = selected[:, u_a], selected[:, u_b]
                p_multiplier = torch.where(p_a == p_b, p_left, p_left * p_right)
                u_multiplier = torch.where(u_a == u_b, u_left, u_left * u_right)
                weighted_u = u_multiplier * design.unsqueeze(0)
                sorted_weight = weighted_u.index_select(1, order_t)
                cumulative = torch.cumsum(sorted_weight, dim=1, dtype=torch.float64)
                zero = torch.zeros((stop - start, 1), dtype=torch.float64, device="cuda")
                prefix = torch.cat((zero, cumulative), dim=1)
                below = prefix.index_select(1, left_t)
                at_or_below = prefix.index_select(1, right_t)
                favorable = below + 0.5 * (at_or_below - below)
                p_mass = p_multiplier.sum(dim=1, dtype=torch.float64)
                u_mass = weighted_u.sum(dim=1, dtype=torch.float64)
                values = (p_multiplier * favorable).sum(dim=1, dtype=torch.float64)
                values = values / (p_mass * u_mass)
                values[(p_mass <= 0) | (u_mass <= 0)] = torch.nan
                distributions[scorer_position, start:stop] = values.cpu().numpy()
    return counts, distributions


def _selection_and_kill(
    point_by_cell: Mapping[str, Mapping[str, Mapping[str, float]]],
    bootstrap_by_cell: Mapping[str, tuple[Sequence[str], np.ndarray]],
    hub_by_cell: Mapping[str, Mapping[str, Any]],
    novel_u: Mapping[str, Any],
    training_registry: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = {
        str(candidate["candidate_id"]): {
            "family": str(candidate["family"]),
            "recipe_id": str(candidate["recipe_id"]),
            "members": [str(member["run_id"]) for member in candidate["members"]],
        }
        for candidate in training_registry["ensembles"]
    }
    metrics = {
        candidate: {
            cell: float(point_by_cell[cell][candidate]["ht_positive_vs_U_concordance"])
            for cell in PRIMARY_CELLS
        }
        for candidate in candidates
    }
    seed_ranges: dict[str, dict[str, float]] = defaultdict(dict)
    eligible: dict[str, bool] = {}
    for candidate, record in candidates.items():
        for cell in PRIMARY_CELLS:
            values = [
                float(point_by_cell[cell][member]["ht_positive_vs_U_concordance"])
                for member in record["members"]
            ]
            seed_ranges[candidate][cell] = float(max(values) - min(values))
        eligible[candidate] = all(value <= 0.02 for value in seed_ranges[candidate].values())

    def selection_key(candidate: str) -> tuple[Any, ...]:
        record = candidates[candidate]
        quantized = tuple(
            -Decimal(str(metrics[candidate][cell])).quantize(
                Decimal("0.001"), rounding=ROUND_HALF_UP
            )
            for cell in PRIMARY_CELLS
        )
        return (*quantized, COMPLEXITY[record["family"]], candidate)

    eligible_candidates = [candidate for candidate in candidates if eligible[candidate]]
    selected = min(eligible_candidates, key=selection_key) if eligible_candidates else None

    def distribution(cell: str, scorer: str) -> np.ndarray:
        scorers, values = bootstrap_by_cell[cell]
        return values[list(scorers).index(scorer)]

    def delta_record(cell: str, left: str, right: str) -> dict[str, Any]:
        delta = metrics[left][cell] - float(
            point_by_cell[cell][right]["ht_positive_vs_U_concordance"]
        )
        interval = _percentile(distribution(cell, left) - distribution(cell, right))
        return {
            "candidate": left,
            "comparator": right,
            "cell": cell,
            "delta": delta,
            "paired_percentile_95": interval,
            "interval_excludes_zero_positive": interval[0] > 0,
        }

    simple_candidates = [
        candidate
        for candidate, record in candidates.items()
        if record["family"]
        in {"lightweight_esm2_150m_linear", "esm2_650m_linear_ablation"}
    ]
    simple_by_cell = {
        cell: max(
            list(SIMPLE_SEQUENCE) + simple_candidates,
            key=lambda scorer: float(
                point_by_cell[cell][scorer]["ht_positive_vs_U_concordance"]
            ),
        )
        for cell in PRIMARY_CELLS
    }
    linear_650 = [
        candidate
        for candidate, record in candidates.items()
        if record["family"] == "esm2_650m_linear_ablation"
    ]
    strongest_650_c3 = max(
        linear_650, key=lambda scorer: metrics[scorer]["C3_development"]
    )
    no_gate_by_recipe = {
        record["recipe_id"]: candidate
        for candidate, record in candidates.items()
        if record["family"] == "esm2_650m_nonlinear_no_gate_ablation"
    }
    partner_candidates = [
        candidate
        for candidate, record in candidates.items()
        if record["family"] == "esm2_650m_partner_gated_primary"
    ]
    partner_trace: dict[str, Any] = {}
    any_qualifying_c3 = False
    any_qualifying_c2 = False
    for candidate in partner_candidates:
        baseline_delta = delta_record(
            "C3_development", candidate, simple_by_cell["C3_development"]
        )
        linear_delta = delta_record("C3_development", candidate, strongest_650_c3)
        no_gate = no_gate_by_recipe[candidates[candidate]["recipe_id"]]
        gate_delta = delta_record("C3_development", candidate, no_gate)
        source_deltas: dict[str, float] = {}
        for source_cell in (
            "source_exclusive:HI-II-14:C3_development",
            "source_exclusive:HuRI:C3_development",
        ):
            source_baseline = max(
                list(SIMPLE_SEQUENCE) + simple_candidates,
                key=lambda scorer: float(
                    point_by_cell[source_cell][scorer]["ht_positive_vs_U_concordance"]
                ),
            )
            source_deltas[source_cell] = float(
                point_by_cell[source_cell][candidate]["ht_positive_vs_U_concordance"]
            ) - float(
                point_by_cell[source_cell][source_baseline]["ht_positive_vs_U_concordance"]
            )
        outside = hub_by_cell["C3_development"]["hub_views"]["top_10_percent"][
            "excludes_hub"
        ]["metrics"]
        outside_delta = float(
            outside[candidate]["ht_positive_vs_U_concordance"]
        ) - float(
            outside[simple_by_cell["C3_development"]]["ht_positive_vs_U_concordance"]
        )
        checks = {
            "C3_vs_strongest_simple_at_least_0_02": baseline_delta["delta"] >= 0.02,
            "C3_vs_strongest_simple_interval_positive": baseline_delta[
                "interval_excludes_zero_positive"
            ],
            "C3_vs_650m_linear_at_least_0_01": linear_delta["delta"] >= 0.01,
            "C3_vs_650m_linear_interval_positive": linear_delta[
                "interval_excludes_zero_positive"
            ],
            "C3_vs_matched_no_gate_at_least_0_005": gate_delta["delta"] >= 0.005,
            "C3_vs_matched_no_gate_interval_positive": gate_delta[
                "interval_excludes_zero_positive"
            ],
            "positive_named_source_direction": any(
                value > 0 for value in source_deltas.values()
            ),
            "positive_outside_top_10_percent_hubs": outside_delta > 0,
            "all_seed_ranges_at_most_0_02": eligible[candidate],
        }
        partner_trace[candidate] = {
            "baseline_delta": baseline_delta,
            "linear_650m_delta": linear_delta,
            "matched_no_gate_delta": gate_delta,
            "named_source_deltas": source_deltas,
            "outside_top_10_percent_hub_delta": outside_delta,
            "checks": checks,
            "partner_gate_retained": all(checks.values()),
        }
        any_qualifying_c3 |= (
            baseline_delta["delta"] >= 0.02
            and baseline_delta["interval_excludes_zero_positive"]
        )
        c2_delta = delta_record(
            "C2_development", candidate, simple_by_cell["C2_development"]
        )
        any_qualifying_c2 |= (
            c2_delta["delta"] >= 0.02
            and c2_delta["interval_excludes_zero_positive"]
        )

    complex_candidates = [
        candidate
        for candidate, record in candidates.items()
        if record["family"]
        in {
            "esm2_650m_nonlinear_no_gate_ablation",
            "esm2_650m_partner_gated_primary",
        }
    ]
    complex_vs_baseline = {
        candidate: delta_record(
            "C3_development", candidate, simple_by_cell["C3_development"]
        )
        for candidate in complex_candidates
    }
    qualifying_complex = [
        candidate
        for candidate, record in complex_vs_baseline.items()
        if record["delta"] >= 0.02 and record["interval_excludes_zero_positive"]
    ]
    best_complex = max(
        complex_candidates, key=lambda candidate: metrics[candidate]["C3_development"]
    )
    best_complex_interval = _percentile(
        distribution("C3_development", best_complex)
    )
    best_shortcut_c1 = max(
        SHORTCUTS,
        key=lambda scorer: float(
            point_by_cell["C1_development"][scorer]["ht_positive_vs_U_concordance"]
        ),
    )
    best_complex_c1 = max(
        complex_candidates, key=lambda candidate: metrics[candidate]["C1_development"]
    )
    shortcut_explains_c1 = float(
        point_by_cell["C1_development"][best_shortcut_c1][
            "ht_positive_vs_U_concordance"
        ]
    ) >= metrics[best_complex_c1]["C1_development"]
    best_complex_simple_delta = delta_record(
        "C3_development", best_complex, simple_by_cell["C3_development"]
    )
    outside = hub_by_cell["C3_development"]["hub_views"]["top_10_percent"][
        "excludes_hub"
    ]["metrics"]
    outside_gain = float(
        outside[best_complex]["ht_positive_vs_U_concordance"]
    ) - float(
        outside[simple_by_cell["C3_development"]]["ht_positive_vs_U_concordance"]
    )
    c1_primary_gain = metrics[best_complex_c1]["C1_development"] - float(
        point_by_cell["C1_development"][simple_by_cell["C1_development"]][
            "ht_positive_vs_U_concordance"
        ]
    )
    c1_novel_gain = float(
        novel_u["metrics"][best_complex_c1]["ht_positive_vs_U_concordance"]
    ) - float(
        novel_u["metrics"][simple_by_cell["C1_development"]][
            "ht_positive_vs_U_concordance"
        ]
    )
    kill = {
        "integrity_custody_or_protected_boundary_violation": False,
        "U_used_as_negative_or_probability_target": False,
        "no_complex_candidate_C3_gain_0_02_with_positive_interval":
            len(qualifying_complex) == 0,
        "best_complex_C3_lower_bound_not_above_0_5":
            best_complex_interval[0] <= 0.5,
        "shortcut_explains_C1_and_no_qualifying_C2_or_C3":
            shortcut_explains_c1 and not any_qualifying_c2 and not any_qualifying_c3,
        "interolog_or_linear_explains_complex_C3":
            best_complex_simple_delta["delta"] < 0.01
            or not best_complex_simple_delta["interval_excludes_zero_positive"],
        "gain_absent_outside_top_10_percent_hubs": outside_gain <= 0,
        "all_candidates_ineligible_or_failed": not eligible_candidates,
        "unsupported_claim_required": False,
        "development_released_before_registry_freeze": False,
        "post_release_training_or_retraining": False,
    }
    stop = any(kill.values())
    partner_retained = [
        candidate
        for candidate, record in partner_trace.items()
        if record["partner_gate_retained"]
    ]
    if stop:
        disposition = "stop_complex_model_claim_and_stop_before_protected_evaluation"
    elif partner_retained and selected in partner_retained:
        disposition = (
            "advance_frozen_partner_gated_scorer_toward_separate_"
            "protected_authorization"
        )
    else:
        disposition = "retain_only_simpler_frozen_baseline"
    return {
        "candidate_metrics": metrics,
        "seed_metric_ranges": dict(seed_ranges),
        "candidate_eligible": eligible,
        "selection_trace": {
            "selected_candidate_id": selected,
            "order": [
                "C3_development",
                "C2_development",
                "C1_development",
                "lower_complexity",
                "candidate_id",
            ],
            "quantization": "decimal_0.001_ROUND_HALF_UP_selection_only",
            "strongest_simple_sequence_baseline_by_primary_cell": simple_by_cell,
        },
        "partner_gate_trace": partner_trace,
        "kill_trace": {
            "criteria": kill,
            "stop_before_protected_evaluation": stop,
            "best_complex_candidate": best_complex,
            "best_complex_C3_percentile_95": best_complex_interval,
            "best_shortcut_C1": best_shortcut_c1,
            "outside_top_10_percent_hub_gain": outside_gain,
            "C1_primary_gain": c1_primary_gain,
            "C1_novel_U_gain": c1_novel_gain,
            "withdraw_C1_gain_claim": c1_primary_gain > 0 and c1_novel_gain <= 0,
        },
        "development_stage_disposition": disposition,
    }


def _registered_artifacts(registry: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = [
        registry["scoring_run_manifest"],
        registry["development_results_manifest"],
    ]
    for cell in registry["cells"]:
        records.extend(
            [cell["manifest"], cell["rows"], cell["scores"], cell["scorers"]]
        )
    for bootstrap in registry["bootstrap"]:
        records.extend(
            [
                bootstrap["component_multiplicities"],
                bootstrap["bootstrap_metrics"],
                bootstrap["bootstrap_scorers"],
            ]
        )
    records.extend(registry["public_results"])
    records.extend(registry["private_logs"])
    return records


def _prepare_cells(
    project_root: Path,
    registry: Mapping[str, Any],
    training_registry: Mapping[str, Any],
    endpoint_index: Mapping[str, int],
) -> tuple[list[CellView], list[str]]:
    runs = list(training_registry["run_summaries"])
    ensembles = list(training_registry["ensembles"])
    scorer_ids = (
        list(DETERMINISTIC)
        + [str(run["run_id"]) for run in runs]
        + [str(candidate["candidate_id"]) for candidate in ensembles]
    )
    if len(scorer_ids) != 49 or len(set(scorer_ids)) != 49:
        raise RuntimeError("clean-room scorer census drift")
    registry_cells = {str(item["cell_id"]): item for item in registry["cells"]}
    output: list[CellView] = []
    positive_total = 0
    unlabeled_total = 0
    for cell_id in CELLS:
        record = registry_cells[cell_id]
        rows_path = _safe_regular(project_root, Path(str(record["rows"]["path"])))
        score_path = _safe_regular(project_root, Path(str(record["scores"]["path"])))
        scorer_path = _safe_regular(project_root, Path(str(record["scorers"]["path"])))
        rows = pq.read_table(rows_path)
        scores = np.load(score_path, mmap_mode="r", allow_pickle=False)
        scorer_payload = _json(scorer_path)
        observed_scorers = [
            str(item["scorer_id"]) for item in scorer_payload["scorers"]
        ]
        observed_columns = [
            int(item["column"]) for item in scorer_payload["scorers"]
        ]
        p, u, _ = _state_arrays(rows)
        positive_total += int(p.sum())
        unlabeled_total += int(u.sum())
        if (
            observed_scorers != scorer_ids
            or observed_columns != list(range(49))
            or scores.dtype != np.float64
            or scores.shape != (rows.num_rows, 49)
            or not np.isfinite(scores).all()
            or int(p.sum()) != int(record["positive_rows"])
            or int(u.sum()) != int(record["unlabeled_rows"])
            or rows.num_rows != int(record["total_rows"])
        ):
            raise RuntimeError(f"clean-room cell/scorer identity drift: {cell_id}")
        scorer_index = {value: index for index, value in enumerate(scorer_ids)}
        for ensemble in ensembles:
            member_columns = [
                scorer_index[str(member["run_id"])]
                for member in ensemble["members"]
            ]
            expected = np.mean(
                scores[:, member_columns], axis=1, dtype=np.float64
            )
            if not np.array_equal(
                expected, np.asarray(scores[:, scorer_index[str(ensemble["candidate_id"])]]),
            ):
                raise RuntimeError(f"clean-room ensemble drift: {cell_id}")
        endpoint_a = np.fromiter(
            (endpoint_index[str(value)] for value in rows["endpoint_a_sha256"].to_pylist()),
            dtype=np.int32,
            count=rows.num_rows,
        )
        endpoint_b = np.fromiter(
            (endpoint_index[str(value)] for value in rows["endpoint_b_sha256"].to_pylist()),
            dtype=np.int32,
            count=rows.num_rows,
        )
        output.append(
            CellView(
                cell_id=cell_id,
                rows_path=rows_path,
                score_path=score_path,
                scores=scores,
                scorer_ids=scorer_ids,
                scorer_index=scorer_index,
                endpoint_a=endpoint_a,
                endpoint_b=endpoint_b,
            )
        )
    if (
        positive_total != 26_108
        or unlabeled_total != 9_000_000
        or positive_total + unlabeled_total != 9_026_108
    ):
        raise RuntimeError("clean-room nine-cell scoring census drift")
    return output, scorer_ids


def _deterministic_score_validation(
    cell_views: Sequence[CellView],
    sequences: Sequence[str],
    lengths: np.ndarray,
    components: Sequence[str],
    degree: np.ndarray,
    component_mass: Mapping[str, int],
    adjacency: sparse.csr_matrix,
    exposed: np.ndarray,
    edge_u: np.ndarray,
    edge_v: np.ndarray,
) -> tuple[bool, float]:
    kmer = _kmer_matrix(sequences)
    norms = np.sqrt(np.asarray(kmer.multiply(kmer).sum(axis=1)).ravel())
    if kmer.shape != (17_000, 21**3) or np.any(np.abs(norms - 1.0) > 1e-12):
        raise RuntimeError("clean-room normalized 3-mer matrix drift")
    similarities = (kmer @ kmer[exposed].T).toarray().astype(np.float64, copy=False)
    neighbor = np.zeros_like(similarities)
    neighbors: dict[int, list[int]] = defaultdict(list)
    for left, right in zip(edge_u, edge_v, strict=True):
        neighbors[int(left)].append(int(right))
        neighbors[int(right)].append(int(left))
    for endpoint in range(exposed.size):
        values = neighbors.get(endpoint)
        if values:
            neighbor[:, endpoint] = similarities[:, values].max(axis=1)
    similarity_t = torch.from_numpy(similarities).to(device="cuda", dtype=torch.float64)
    neighbor_t = torch.from_numpy(neighbor).to(device="cuda", dtype=torch.float64)
    exact = True
    maximum = 0.0
    for cell in cell_views:
        print(f"independent deterministic scores: {cell.cell_id}", flush=True)
        rows = pq.read_table(cell.rows_path)
        pair_ids = tuple(map(str, rows["pair_id"].to_pylist()))
        a, b = cell.endpoint_a, cell.endpoint_b
        pooled_a, pooled_b = degree[a], degree[b]
        recorded_a = np.asarray(
            rows["endpoint_a_training_degree"].to_numpy(), dtype=np.int64
        )
        recorded_b = np.asarray(
            rows["endpoint_b_training_degree"].to_numpy(), dtype=np.int64
        )
        expected_strata = [
            _degree_stratum(int(left), int(right))
            for left, right in zip(recorded_a, recorded_b, strict=True)
        ]
        if (
            np.any(recorded_a < 0)
            or np.any(recorded_b < 0)
            or rows["stratum_id"].to_pylist() != expected_strata
            or (
                not cell.cell_id.startswith("source_exclusive:")
                and (
                    not np.array_equal(recorded_a, pooled_a)
                    or not np.array_equal(recorded_b, pooled_b)
                )
            )
        ):
            raise RuntimeError(f"clean-room degree/stratum drift: {cell.cell_id}")
        observed = np.empty((rows.num_rows, 9), dtype=np.float64)
        observed[:, 0] = np.fromiter(
            (
                int.from_bytes(
                    hashlib.sha256(
                        (
                            "ipin-openppi-pu-r-baseline-v1:20260803:"
                            f"baseline:{pair_id}"
                        ).encode("utf-8")
                    ).digest(),
                    "big",
                )
                / (2**256 - 1)
                for pair_id in pair_ids
            ),
            dtype=np.float64,
            count=rows.num_rows,
        )
        observed[:, 1] = np.log1p(pooled_a) + np.log1p(pooled_b)
        observed[:, 2] = np.log1p(pooled_a * pooled_b)
        mass_a = np.fromiter(
            (component_mass[str(components[int(value)])] for value in a),
            dtype=np.int64,
            count=rows.num_rows,
        )
        mass_b = np.fromiter(
            (component_mass[str(components[int(value)])] for value in b),
            dtype=np.int64,
            count=rows.num_rows,
        )
        observed[:, 3] = np.log1p(mass_a * mass_b)
        for start in range(0, rows.num_rows, 100_000):
            stop = min(start + 100_000, rows.num_rows)
            common = adjacency[a[start:stop]].multiply(
                adjacency[b[start:stop]]
            ).sum(axis=1)
            observed[start:stop, 4] = np.log1p(np.asarray(common).ravel())
            cosine = kmer[a[start:stop]].multiply(kmer[b[start:stop]]).sum(axis=1)
            observed[start:stop, 7] = np.asarray(cosine).ravel()
        observed[:, 5] = np.log1p(lengths[a]) + np.log1p(lengths[b])
        observed[:, 6] = -np.abs(np.log1p(lengths[a]) - np.log1p(lengths[b]))
        with torch.inference_mode():
            for start in range(0, rows.num_rows, 8_192):
                stop = min(start + 8_192, rows.num_rows)
                left = torch.from_numpy(
                    np.asarray(a[start:stop], dtype=np.int64)
                ).cuda()
                right = torch.from_numpy(
                    np.asarray(b[start:stop], dtype=np.int64)
                ).cuda()
                values = torch.minimum(
                    similarity_t.index_select(0, left),
                    neighbor_t.index_select(0, right),
                ).amax(dim=1)
                observed[start:stop, 8] = values.cpu().numpy()
        frozen = np.asarray(cell.scores[:, :9], dtype=np.float64)
        difference = np.abs(observed - frozen)
        maximum = max(maximum, float(difference.max(initial=0.0)))
        exact &= bool(np.array_equal(observed, frozen))
    del similarity_t, neighbor_t, similarities, neighbor, kmer
    torch.cuda.empty_cache()
    return exact, maximum


def _model_score_validation(
    project_root: Path,
    cell_views: Sequence[CellView],
    training_registry: Mapping[str, Any],
) -> tuple[bool, float, float, int]:
    embedding_tensors: dict[str, torch.Tensor] = {}
    for candidate, (relative, expected_hash, expected_shape) in EMBEDDINGS.items():
        path = _safe_regular(project_root, relative)
        matrix = np.load(path, mmap_mode="r", allow_pickle=False)
        if (
            _sha256(path) != expected_hash
            or matrix.dtype != np.float32
            or matrix.shape != expected_shape
        ):
            raise RuntimeError(f"clean-room embedding drift: {candidate}")
        embedding_tensors[candidate] = torch.from_numpy(
            np.array(matrix, copy=True)
        ).cuda()
    exact = True
    maximum = 0.0
    swap_maximum = 0.0
    comparisons = 0
    for run_offset, run in enumerate(training_registry["run_summaries"], start=9):
        run_id = str(run["run_id"])
        family = str(run["family"])
        print(f"independent learned scores: {run_id}", flush=True)
        checkpoint_record = run["selected_checkpoint"]
        checkpoint_path = _safe_regular(
            project_root, Path(str(checkpoint_record["path"]))
        )
        config_path = _safe_regular(project_root, Path(str(run["run_config_path"])))
        if (
            _sha256(checkpoint_path) != str(checkpoint_record["sha256"])
            or checkpoint_path.stat().st_size != int(checkpoint_record["bytes"])
            or _sha256(config_path) != str(run["run_config_sha256"])
        ):
            raise RuntimeError(f"clean-room checkpoint/config hash drift: {run_id}")
        checkpoint = torch.load(
            checkpoint_path, map_location="cpu", weights_only=False
        )
        if (
            int(checkpoint["pass_index"]) != 5
            or int(checkpoint["global_step"]) != 2_445
            or sum(value.numel() for value in checkpoint["model_state"].values())
            != PARAMETERS[family]
            or not all(
                bool(torch.isfinite(value).all())
                for value in checkpoint["model_state"].values()
            )
        ):
            raise RuntimeError(f"clean-room selected checkpoint drift: {run_id}")
        candidate = (
            "esm2_150m"
            if family == "lightweight_esm2_150m_linear"
            else "esm2_650m"
        )
        embeddings = embedding_tensors[candidate]
        state = {
            name: value.cuda() for name, value in checkpoint["model_state"].items()
        }
        projected: torch.Tensor | None = None
        gate_value: torch.Tensor | None = None
        with torch.inference_mode():
            if family not in (
                "lightweight_esm2_150m_linear",
                "esm2_650m_linear_ablation",
            ):
                projected = F.gelu(
                    F.linear(
                        embeddings,
                        state["projection.weight"],
                        state["projection.bias"],
                    ),
                    approximate="none",
                )
                if family == "esm2_650m_partner_gated_primary":
                    gate_value = torch.sigmoid(
                        F.linear(
                            projected,
                            state["gate.weight"],
                            state["gate.bias"],
                        )
                    )
            for cell in cell_views:
                for start in range(0, cell.endpoint_a.size, 32_768):
                    stop = min(start + 32_768, cell.endpoint_a.size)
                    a = torch.from_numpy(
                        np.asarray(cell.endpoint_a[start:stop], dtype=np.int64)
                    ).cuda()
                    b = torch.from_numpy(
                        np.asarray(cell.endpoint_b[start:stop], dtype=np.int64)
                    ).cuda()
                    calculated = _model_batch(
                        family,
                        state,
                        embeddings,
                        a,
                        b,
                        projected,
                        gate_value,
                    ).cpu().numpy()
                    frozen = np.asarray(
                        cell.scores[start:stop, run_offset], dtype=np.float64
                    )
                    difference = np.abs(
                        frozen - calculated.astype(np.float64, copy=False)
                    )
                    maximum = max(
                        maximum, float(difference.max(initial=0.0))
                    )
                    exact &= bool(
                        np.array_equal(
                            frozen, calculated.astype(np.float64, copy=False)
                        )
                    )
                    comparisons += stop - start
                fixture_stop = min(512, cell.endpoint_a.size)
                fixture_a = torch.from_numpy(
                    np.asarray(cell.endpoint_a[:fixture_stop], dtype=np.int64)
                ).cuda()
                fixture_b = torch.from_numpy(
                    np.asarray(cell.endpoint_b[:fixture_stop], dtype=np.int64)
                ).cuda()
                forward = _model_batch(
                    family,
                    state,
                    embeddings,
                    fixture_a,
                    fixture_b,
                    projected,
                    gate_value,
                )
                reverse = _model_batch(
                    family,
                    state,
                    embeddings,
                    fixture_b,
                    fixture_a,
                    projected,
                    gate_value,
                )
                swap_maximum = max(
                    swap_maximum,
                    float(torch.max(torch.abs(forward - reverse)).cpu()),
                )
        del state, projected, gate_value, checkpoint
        torch.cuda.empty_cache()
    del embedding_tensors
    torch.cuda.empty_cache()
    return exact, maximum, swap_maximum, comparisons


def _metric_validation(
    project_root: Path,
    cell_views: Sequence[CellView],
    scorer_ids: Sequence[str],
    hubs: Mapping[str, frozenset[str]],
    training_registry: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, tuple[list[str], np.ndarray]],
    dict[str, Any],
    dict[str, bool],
]:
    primary_public = _json(
        _safe_regular(project_root, RESULTS_ROOT / "PRIMARY_METRICS.json")
    )
    source_public = _json(
        _safe_regular(project_root, RESULTS_ROOT / "SOURCE_EXCLUSIVE_METRICS.json")
    )
    degree_public = _json(
        _safe_regular(project_root, RESULTS_ROOT / "DEGREE_HUB_DIAGNOSTICS.json")
    )
    correlation_public = _json(
        _safe_regular(project_root, RESULTS_ROOT / "DIAGNOSTIC_CORRELATIONS.json")
    )
    bootstrap_public = _json(
        _safe_regular(project_root, RESULTS_ROOT / "BOOTSTRAP_REGISTRY.json")
    )
    novel_public = _json(
        _safe_regular(project_root, RESULTS_ROOT / "C1_NOVEL_U_SENSITIVITY.json")
    )
    point_by_cell: dict[str, Any] = {}
    degree_by_cell: dict[str, Any] = {}
    bootstrap_by_cell: dict[str, tuple[list[str], np.ndarray]] = {}
    exact = {
        "point_metrics": True,
        "degree_hub": True,
        "correlations": True,
        "bootstrap": True,
        "novel_u": True,
    }
    bootstrap_scorers = list(DETERMINISTIC) + [
        str(item["candidate_id"]) for item in training_registry["ensembles"]
    ]
    view_by_id = {cell.cell_id: cell for cell in cell_views}
    for cell_id in CELLS:
        print(f"independent metrics: {cell_id}", flush=True)
        cell = view_by_id[cell_id]
        rows = pq.read_table(cell.rows_path)
        observed_point = _point_metrics(rows, cell.scores, scorer_ids)
        point_by_cell[cell_id] = observed_point
        expected_point = (
            primary_public["cells"][cell_id]["metrics"]
            if cell_id in PRIMARY_CELLS
            else source_public["cells"][cell_id]
        )
        exact["point_metrics"] &= observed_point == expected_point
        if cell_id not in PRIMARY_CELLS:
            continue
        observed_degree = _degree_hub(rows, cell.scores, scorer_ids, hubs)
        degree_by_cell[cell_id] = observed_degree
        exact["degree_hub"] &= observed_degree == degree_public["cells"][cell_id]
        exact["correlations"] &= (
            _correlations(cell.scores, scorer_ids)
            == correlation_public["cells"][cell_id]
        )
        print(f"independent bootstrap: {cell_id}", flush=True)
        bootstrap_root = PRIVATE_EVALUATION_ROOT / "bootstrap" / cell_id
        counts_path = _safe_regular(
            project_root, bootstrap_root / "component_multiplicities.i32.npy"
        )
        distributions_path = _safe_regular(
            project_root, bootstrap_root / "bootstrap_metrics.f64.npy"
        )
        scorer_path = _safe_regular(
            project_root, bootstrap_root / "BOOTSTRAP_SCORERS.json"
        )
        stored_counts = np.load(counts_path, mmap_mode="r", allow_pickle=False)
        stored_distributions = np.load(
            distributions_path, mmap_mode="r", allow_pickle=False
        )
        stored_scorers = [
            str(value) for value in _json(scorer_path)["scorer_ids"]
        ]
        regenerated_counts, regenerated_distributions = _bootstrap_gpu(
            rows,
            cell.scores,
            scorer_ids,
            bootstrap_scorers,
            cell_id,
        )
        intervals = {
            scorer: _percentile(regenerated_distributions[index])
            for index, scorer in enumerate(bootstrap_scorers)
        }
        record = bootstrap_public["cells"][cell_id]
        exact["bootstrap"] &= (
            stored_scorers == bootstrap_scorers
            and stored_counts.shape == regenerated_counts.shape
            and np.array_equal(stored_counts, regenerated_counts)
            and stored_distributions.shape == (19, 2_000)
            and np.array_equal(
                stored_distributions,
                regenerated_distributions,
                equal_nan=True,
            )
            and intervals
            == primary_public["cells"][cell_id][
                "bootstrap_percentile_95_for_controls_and_ensembles"
            ]
            and all(
                int(np.isfinite(regenerated_distributions[index]).sum())
                == int(record["finite_replicates_by_scorer"][scorer])
                for index, scorer in enumerate(bootstrap_scorers)
            )
        )
        bootstrap_by_cell[cell_id] = (
            bootstrap_scorers,
            regenerated_distributions,
        )
        del regenerated_counts, regenerated_distributions
        torch.cuda.empty_cache()

    c1 = view_by_id["C1_development"]
    c1_rows = pq.read_table(c1.rows_path)
    p, u, weights = _state_arrays(c1_rows)
    training_u = pq.read_table(
        _safe_regular(project_root, TRAINING_UNLABELED), columns=["pair_id"]
    )
    training_u_ids = set(map(str, training_u["pair_id"].to_pylist()))
    pair_ids = np.asarray(c1_rows["pair_id"].to_pylist(), dtype=object)
    retained_u = np.fromiter(
        (str(value) not in training_u_ids for value in pair_ids),
        dtype=bool,
        count=c1_rows.num_rows,
    ) & u
    retained_ids = pair_ids[retained_u]
    strata = np.asarray(c1_rows["stratum_id"].to_pylist(), dtype=object)
    novel = {
        "positive_rows": int(p.sum()),
        "retained_U_rows": int(retained_u.sum()),
        "removed_U_rows": int(u.sum() - retained_u.sum()),
        "retained_U_weight_sum": float(weights[retained_u].sum(dtype=np.float64)),
        "retained_nonempty_strata": len(set(strata[retained_u])),
        "retained_pair_id_unique":
            len(set(map(str, retained_ids))) == retained_ids.size,
        "interpretation": "design_weighted_Hajek_ratio_over_realized_novel_U_view",
        "selection_or_stopping_use": False,
        "metrics": _point_metrics(
            c1_rows, c1.scores, scorer_ids, row_mask=p | retained_u
        ),
    }
    exact["novel_u"] &= novel == novel_public["C1_development"]
    return point_by_cell, degree_by_cell, bootstrap_by_cell, novel, exact


def validate(
    project_root: Path,
    output: Path,
    independent_source_commit: str,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=project_root, text=True
    ).strip()
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PRODUCTION_EVIDENCE_COMMIT, head],
        cwd=project_root,
        check=False,
    ).returncode == 0
    _check(
        checks,
        "production_then_independent_commit_order",
        head == independent_source_commit and ancestor,
        {
            "independent_source_commit": independent_source_commit,
            "production_evidence_commit": PRODUCTION_EVIDENCE_COMMIT,
        },
    )

    registry_path = _safe_regular(
        project_root, VALIDATION_ROOT / "DEVELOPMENT_EVALUATION_REGISTRY.json"
    )
    audit_path = _safe_regular(
        project_root,
        VALIDATION_ROOT / "COMPLETED_EVALUATION_PRODUCTION_AUDIT_REPORT.json",
    )
    config_path = _safe_regular(
        project_root, Path("configs/development_release_and_evaluation_execution_v1.yaml")
    )
    training_registry_path = _safe_regular(project_root, TRAINING_REGISTRY)
    scoring_manifest_path = _safe_regular(
        project_root, PRIVATE_EVALUATION_ROOT / "SCORING_RUN_MANIFEST.json"
    )
    results_manifest_path = _safe_regular(
        project_root, RESULTS_ROOT / "DEVELOPMENT_RESULTS_MANIFEST.json"
    )
    selection_path = _safe_regular(
        project_root, RESULTS_ROOT / "SELECTION_AND_KILL_TRACE.json"
    )
    registry = _json(registry_path)
    audit = _json(audit_path)
    training_registry = _json(training_registry_path)
    scoring_manifest = _json(scoring_manifest_path)
    results_manifest = _json(results_manifest_path)
    selection_public = _json(selection_path)
    evidence_ok = (
        _sha256(registry_path) == PRODUCTION_REGISTRY_SHA256
        and _sha256(audit_path) == PRODUCTION_AUDIT_SHA256
        and _sha256(config_path) == CONFIG_SHA256
        and _sha256(training_registry_path) == TRAINING_REGISTRY_SHA256
        and _sha256(scoring_manifest_path) == SCORING_MANIFEST_SHA256
        and _sha256(results_manifest_path) == RESULTS_MANIFEST_SHA256
        and _sha256(selection_path) == SELECTION_TRACE_SHA256
        and registry["status"] == "pass"
        and audit["status"] == "pass"
        and audit["registry_sha256"] == PRODUCTION_REGISTRY_SHA256
        and registry["production_audit_source_commit"]
        == "d6243e18cd62716305b1b392f8620eba554a8ba8"
        and scoring_manifest["cell_count"] == 9
        and scoring_manifest["scorer_count"] == 49
        and results_manifest["stop_before_protected_evaluation"] is True
    )
    _check(
        checks,
        "frozen_production_evidence_and_manifest_gate",
        evidence_ok,
        {
            "production_registry_sha256": _sha256(registry_path),
            "production_audit_sha256": _sha256(audit_path),
            "scoring_manifest_sha256": _sha256(scoring_manifest_path),
            "results_manifest_sha256": _sha256(results_manifest_path),
        },
    )

    source_ok = True
    for relative, expected in SOURCE_HASHES.items():
        source_ok &= (
            _sha256(_safe_regular(project_root, Path(relative))) == expected
        )
    scoring_source = _safe_regular(
        project_root, Path("src/ipin_openppi/development_evaluation/scoring.py")
    ).read_text(encoding="utf-8")
    evaluation_source = _safe_regular(
        project_root, Path("src/ipin_openppi/development_evaluation/evaluation.py")
    ).read_text(encoding="utf-8")
    source_ok &= all(
        token not in scoring_source + evaluation_source
        for token in (
            "torch.optim",
            ".backward(",
            "optimizer.step(",
            "protected_candidates.cms",
            "protected_truth.cms",
            "private.pem",
        )
    )
    _check(
        checks,
        "independent_source_hash_and_inference_only_binding",
        source_ok,
        SOURCE_HASHES,
    )

    registered = _registered_artifacts(registry)
    registered_ok = len(registered) == 57
    unique_records: dict[str, tuple[int, str]] = {}
    for record in registered:
        relative = Path(str(record["path"]))
        path = _safe_regular(project_root, relative)
        observed = (path.stat().st_size, _sha256(path))
        expected = (int(record["bytes"]), str(record["sha256"]))
        registered_ok &= observed == expected
        if relative.as_posix() in unique_records:
            registered_ok &= unique_records[relative.as_posix()] == expected
        unique_records[relative.as_posix()] = expected
    _check(
        checks,
        "independent_all_registered_private_public_hashes_and_bytes",
        registered_ok and len(unique_records) == 57,
        {
            "registered_records": len(registered),
            "unique_registered_files": len(unique_records),
            "registered_bytes": sum(value[0] for value in unique_records.values()),
        },
    )

    public_paths = [
        _safe_regular(project_root, Path(str(record["path"])))
        for record in registry["public_results"]
    ] + [results_manifest_path]
    public_boundary_ok = (
        all(not _contains_identity(path) for path in public_paths)
        and all(
            payload.get("pair_identity_public") is False
            and payload.get("protected_candidates_accessed") is False
            and payload.get("protected_truth_accessed") is False
            and payload.get("training_or_checkpoint_change") is False
            for payload in (
                results_manifest,
                selection_public,
                _json(_safe_regular(project_root, RESULTS_ROOT / "PRIMARY_METRICS.json")),
                _json(
                    _safe_regular(
                        project_root, RESULTS_ROOT / "SOURCE_EXCLUSIVE_METRICS.json"
                    )
                ),
            )
        )
    )
    _check(
        checks,
        "public_aggregate_identity_exclusion_and_closed_flags",
        public_boundary_ok,
        {"public_files_scanned": len(public_paths), "pair_identity_public": False},
    )

    input_hashes = {
        ENDPOINTS: "4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e",
        PARTITIONS: "66db8cd59e7cb8cf06ff3ad785448dfc7d5fdd24643811946246d129b0bd8a67",
        TRAINING_POSITIVE: "4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499",
        TRAINING_UNLABELED: "d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7",
    }
    immutable_ok = all(
        _sha256(_safe_regular(project_root, relative)) == expected
        for relative, expected in input_hashes.items()
    )
    immutable_ok &= all(
        _sha256(_safe_regular(project_root, relative)) == expected_hash
        for relative, expected_hash, _ in EMBEDDINGS.values()
    )
    _check(
        checks,
        "independent_public_input_embedding_and_checkpoint_dependencies",
        immutable_ok,
        {relative.as_posix(): expected for relative, expected in input_hashes.items()},
    )

    endpoints = pq.read_table(
        _safe_regular(project_root, ENDPOINTS),
        columns=["reference_sequence_sha256", "sequence", "sequence_length"],
    ).sort_by([("reference_sequence_sha256", "ascending")])
    partitions = pq.read_table(
        _safe_regular(project_root, PARTITIONS),
        columns=[
            "reference_sequence_sha256",
            "component_id",
            "partition",
            "sequence_length",
        ],
    ).sort_by([("reference_sequence_sha256", "ascending")])
    endpoint_sha = tuple(
        map(str, endpoints["reference_sequence_sha256"].to_pylist())
    )
    if (
        endpoint_sha
        != tuple(map(str, partitions["reference_sequence_sha256"].to_pylist()))
        or len(endpoint_sha) != 17_000
        or len(set(endpoint_sha)) != 17_000
    ):
        raise RuntimeError("clean-room endpoint universe drift")
    sequences = tuple(map(str, endpoints["sequence"].to_pylist()))
    lengths = np.asarray(endpoints["sequence_length"].to_numpy(), dtype=np.int64)
    components = tuple(map(str, partitions["component_id"].to_pylist()))
    partition_values = tuple(map(str, partitions["partition"].to_pylist()))
    endpoint_index = {value: index for index, value in enumerate(endpoint_sha)}
    training_positive = pq.read_table(
        _safe_regular(project_root, TRAINING_POSITIVE),
        columns=["endpoint_a_sha256", "endpoint_b_sha256", "state"],
    )
    train_a = np.fromiter(
        (
            endpoint_index[str(value)]
            for value in training_positive["endpoint_a_sha256"].to_pylist()
        ),
        dtype=np.int32,
        count=training_positive.num_rows,
    )
    train_b = np.fromiter(
        (
            endpoint_index[str(value)]
            for value in training_positive["endpoint_b_sha256"].to_pylist()
        ),
        dtype=np.int32,
        count=training_positive.num_rows,
    )
    degree = np.bincount(
        np.concatenate((train_a, train_b)), minlength=17_000
    ).astype(np.int64)
    adjacency = sparse.coo_matrix(
        (
            np.ones(2 * training_positive.num_rows, dtype=np.int8),
            (
                np.concatenate((train_a, train_b)),
                np.concatenate((train_b, train_a)),
            ),
        ),
        shape=(17_000, 17_000),
    ).tocsr()
    component_mass: Counter[str] = Counter()
    for endpoint, value in enumerate(degree):
        component_mass[components[endpoint]] += int(value)
    exposed = np.flatnonzero(degree > 0).astype(np.int32)
    exposed_position = np.full(17_000, -1, dtype=np.int32)
    exposed_position[exposed] = np.arange(exposed.size, dtype=np.int32)
    edge_u = exposed_position[train_a]
    edge_v = exposed_position[train_b]
    universe_ok = (
        training_positive.num_rows == 16_799
        and set(training_positive["state"].to_pylist()) == {"released_positive"}
        and Counter(partition_values)
        == Counter({"train": 11_900, "development": 2_550, "test": 2_550})
        and exposed.size == 4_675
        and adjacency.nnz == 33_598
        and np.all(edge_u >= 0)
        and np.all(edge_v >= 0)
    )
    degree_by_training = {
        endpoint_sha[index]: int(degree[index])
        for index, partition in enumerate(partition_values)
        if partition == "train"
    }
    ranked = sorted(
        degree_by_training,
        key=lambda endpoint: (-degree_by_training[endpoint], endpoint),
    )
    hubs = {
        "top_1_percent": frozenset(ranked[:119]),
        "top_5_percent": frozenset(ranked[:595]),
        "top_10_percent": frozenset(ranked[:1190]),
    }
    universe_ok &= {
        name: min(degree_by_training[value] for value in values)
        for name, values in hubs.items()
    } == {"top_1_percent": 41, "top_5_percent": 14, "top_10_percent": 7}
    _check(
        checks,
        "independent_endpoint_training_graph_degree_and_hub_reconstruction",
        universe_ok,
        {
            "endpoints": len(endpoint_sha),
            "training_edges": training_positive.num_rows,
            "exposed_endpoints": int(exposed.size),
        },
    )

    cell_views, scorer_ids = _prepare_cells(
        project_root, registry, training_registry, endpoint_index
    )
    _check(
        checks,
        "all_nine_score_matrices_states_finiteness_and_exact_ensembles",
        len(cell_views) == 9 and len(scorer_ids) == 49,
        {
            "cells": len(cell_views),
            "scorers": len(scorer_ids),
            "rows": sum(cell.endpoint_a.size for cell in cell_views),
            "ensembles_checked_all_rows": 10,
        },
    )

    deterministic_exact, deterministic_maximum = _deterministic_score_validation(
        cell_views,
        sequences,
        lengths,
        components,
        degree,
        component_mass,
        adjacency,
        exposed,
        edge_u,
        edge_v,
    )
    _check(
        checks,
        "independent_all_nine_by_nine_deterministic_score_recomputation",
        deterministic_exact and deterministic_maximum == 0.0,
        {
            "score_values_recomputed": 9_026_108 * 9,
            "maximum_absolute_difference": deterministic_maximum,
        },
    )

    model_exact, model_maximum, swap_maximum, model_comparisons = (
        _model_score_validation(project_root, cell_views, training_registry)
    )
    _check(
        checks,
        "independent_all_thirty_checkpoint_scores_and_swap_symmetry",
        model_exact and model_maximum == 0.0 and swap_maximum <= 1e-6,
        {
            "checkpoint_score_values_recomputed": model_comparisons,
            "maximum_absolute_difference": model_maximum,
            "swap_maximum_absolute_difference": swap_maximum,
        },
    )

    point_by_cell, degree_by_cell, bootstrap_by_cell, novel, metric_exact = (
        _metric_validation(
            project_root,
            cell_views,
            scorer_ids,
            hubs,
            training_registry,
        )
    )
    _check(
        checks,
        "independent_all_nine_by_49_point_metrics",
        metric_exact["point_metrics"],
        {"cells": 9, "scorers": 49, "metrics_each": 3},
    )
    _check(
        checks,
        "independent_degree_hub_and_correlation_diagnostics",
        metric_exact["degree_hub"] and metric_exact["correlations"],
        {"primary_cells": 3, "hub_definitions": list(hubs)},
    )
    _check(
        checks,
        "independent_all_primary_component_bootstraps",
        metric_exact["bootstrap"],
        {"primary_cells": 3, "scorers": 19, "replicates": 2_000},
    )
    _check(
        checks,
        "independent_C1_novel_U_census_weights_and_metrics",
        metric_exact["novel_u"],
        {
            "positive_rows": novel["positive_rows"],
            "retained_U_rows": novel["retained_U_rows"],
            "removed_U_rows": novel["removed_U_rows"],
        },
    )

    disposition = _selection_and_kill(
        point_by_cell,
        bootstrap_by_cell,
        degree_by_cell,
        novel,
        training_registry,
    )
    public_disposition = {key: selection_public[key] for key in disposition}
    disposition_ok = (
        disposition == public_disposition
        and disposition["development_stage_disposition"]
        == "stop_complex_model_claim_and_stop_before_protected_evaluation"
        and disposition["kill_trace"]["stop_before_protected_evaluation"] is True
    )
    _check(
        checks,
        "independent_seed_selection_complexity_and_kill_disposition",
        disposition_ok,
        {
            "selected_candidate": disposition["selection_trace"][
                "selected_candidate_id"
            ],
            "best_complex": disposition["kill_trace"]["best_complex_candidate"],
            "disposition": disposition["development_stage_disposition"],
        },
    )

    log_text = "\n".join(
        _safe_regular(project_root, Path(str(record["path"]))).read_text(
            encoding="utf-8"
        )
        for record in registry["private_logs"]
    )
    information_flow_ok = (
        "development_scoring: PASS cells=9" in log_text
        and "development_evaluation: PASS disposition=stop_complex_model_claim" in log_text
        and "protected_candidates" not in log_text
        and "protected_truth" not in log_text
        and "private.pem" not in log_text
        and scoring_manifest["training_or_checkpoint_change"] is False
        and scoring_manifest["protected_candidates_accessed"] is False
        and scoring_manifest["protected_truth_accessed"] is False
        and registry["development_decryption_repeated"] is False
        and registry["protected_candidates_truth_or_private_key_accessed"] is False
    )
    _check(
        checks,
        "development_only_information_flow_and_protected_seal",
        information_flow_ok,
        {
            "development_decryption_repeated": False,
            "training_or_checkpoint_change": False,
            "protected_key_candidate_or_truth_accessed": False,
        },
    )

    failures = [item for item in checks if item["status"] != "pass"]
    report = {
        "schema_version": 1,
        "execution_id": "development_release_and_evaluation_execution_v1",
        "status": "pass" if not failures else "fail",
        "independent_validator_source_commit": independent_source_commit,
        "production_evidence_commit": PRODUCTION_EVIDENCE_COMMIT,
        "production_registry_sha256": PRODUCTION_REGISTRY_SHA256,
        "production_audit_sha256": PRODUCTION_AUDIT_SHA256,
        "check_counts": {
            "pass": len(checks) - len(failures),
            "fail": len(failures),
            "total": len(checks),
        },
        "checks": checks,
        "score_validation_scope": {
            "cells": 9,
            "rows": 9_026_108,
            "deterministic_scorers_recomputed_all_rows": 9,
            "selected_checkpoints_recomputed_all_rows": 30,
            "ensembles_checked_all_rows": 10,
        },
        "development_stage_disposition":
            disposition["development_stage_disposition"],
        "stop_before_protected_evaluation": True,
        "U_interpreted_as_unlabeled_not_negative": True,
        "training_or_checkpoint_change": False,
        "development_decryption_repeated": False,
        "development_release_plaintext_or_key_accessed": False,
        "protected_private_key_candidates_or_truth_accessed": False,
        "pair_identity_public": False,
        "imports_production_development_evaluation_modules": False,
    }
    _write_json(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--independent-source-commit", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=VALIDATION_ROOT
        / "INDEPENDENT_COMPLETED_EVALUATION_VALIDATION_REPORT.json",
    )
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    if (
        os.environ.get("HF_HUB_OFFLINE") != "1"
        or os.environ.get("TRANSFORMERS_OFFLINE") != "1"
        or not torch.cuda.is_available()
        or torch.cuda.device_count() != 1
    ):
        raise RuntimeError("clean-room completed validation requires offline one-GPU runtime")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    output = root / args.output
    report = validate(root, output, str(args.independent_source_commit))
    print(
        "independent_completed_development_validation: "
        f"{report['status'].upper()} checks={report['check_counts']['total']} "
        f"disposition={report['development_stage_disposition']}"
    )
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
