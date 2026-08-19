"""Pure consequential semantics for the frozen DEC-0028 development stage.

The functions in this module do not open release packages, keys, checkpoints,
or protected artifacts.  They are intentionally small enough for independent
fixture validation before the development key may be resolved.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import hashlib
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


BOOTSTRAP_BASE_SEED = "20260803"
BOOTSTRAP_REPLICATES = 2_000
SELECTION_QUANTUM = Decimal("0.001")
SEEDS = (20260803, 20260817, 20260831)
PRIMARY_CELLS = ("C3_development", "C2_development", "C1_development")
COMPLEXITY_ORDER = {
    "lightweight_esm2_150m_linear": 0,
    "esm2_650m_linear_ablation": 1,
    "esm2_650m_nonlinear_no_gate_ablation": 2,
    "esm2_650m_partner_gated_primary": 3,
}
DETERMINISTIC_SCORERS = (
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


def _finite_1d(name: str, values: Sequence[float] | np.ndarray) -> np.ndarray:
    output = np.asarray(values, dtype=np.float64)
    if output.ndim != 1 or output.size == 0 or not np.isfinite(output).all():
        raise ValueError(f"{name} must be a finite nonempty one-dimensional array")
    return output


def weighted_pairwise_concordance(
    positive_scores: Sequence[float] | np.ndarray,
    unlabeled_scores: Sequence[float] | np.ndarray,
    unlabeled_weights: Sequence[float] | np.ndarray,
    *,
    positive_multipliers: Sequence[float] | np.ndarray | None = None,
    unlabeled_multipliers: Sequence[float] | np.ndarray | None = None,
) -> float:
    """Exact HT P-versus-U concordance with half credit for score ties.

    Optional multipliers implement a component-bootstrap replicate. Positive
    rows have census weight one; U design weights are always retained.
    """

    positives = _finite_1d("positive_scores", positive_scores)
    scores = _finite_1d("unlabeled_scores", unlabeled_scores)
    weights = _finite_1d("unlabeled_weights", unlabeled_weights)
    if scores.size != weights.size or np.any(weights <= 0):
        raise ValueError("U scores and strictly positive design weights must align")
    p_multiplier = (
        np.ones(positives.size, dtype=np.float64)
        if positive_multipliers is None
        else _finite_1d("positive_multipliers", positive_multipliers)
    )
    u_multiplier = (
        np.ones(scores.size, dtype=np.float64)
        if unlabeled_multipliers is None
        else _finite_1d("unlabeled_multipliers", unlabeled_multipliers)
    )
    if p_multiplier.size != positives.size or u_multiplier.size != scores.size:
        raise ValueError("bootstrap multipliers must align with their rows")
    if np.any(p_multiplier < 0) or np.any(u_multiplier < 0):
        raise ValueError("bootstrap multipliers cannot be negative")
    p_mass = float(p_multiplier.sum(dtype=np.float64))
    weighted_u = weights * u_multiplier
    u_mass = float(weighted_u.sum(dtype=np.float64))
    if p_mass <= 0 or u_mass <= 0:
        raise ValueError("bootstrap replicate has zero P or U mass")

    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    cumulative = np.concatenate(
        (np.asarray([0.0], dtype=np.float64), np.cumsum(weighted_u[order], dtype=np.float64))
    )
    left = np.searchsorted(sorted_scores, positives, side="left")
    right = np.searchsorted(sorted_scores, positives, side="right")
    favorable_u_mass = cumulative[left] + 0.5 * (cumulative[right] - cumulative[left])
    numerator = float(np.dot(p_multiplier, favorable_u_mass))
    return numerator / (p_mass * u_mass)


def bootstrap_cell_seed(cell_id: str, base_seed: str = BOOTSTRAP_BASE_SEED) -> int:
    if not cell_id or not base_seed:
        raise ValueError("cell and base seed must be nonempty")
    payload = f"{base_seed}:bootstrap:{cell_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def component_draws(
    component_ids: Sequence[str],
    *,
    cell_id: str,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> tuple[tuple[str, ...], np.ndarray]:
    """Draw participating components with replacement in frozen order."""

    components = tuple(sorted(set(map(str, component_ids))))
    if not components or replicates <= 0:
        raise ValueError("component bootstrap requires components and replicates")
    generator = np.random.Generator(np.random.PCG64DXSM(bootstrap_cell_seed(cell_id)))
    draws = generator.integers(
        0, len(components), size=(replicates, len(components)), dtype=np.int64
    )
    counts = np.zeros((replicates, len(components)), dtype=np.int32)
    rows = np.arange(replicates, dtype=np.int64)[:, None]
    np.add.at(counts, (rows, draws), 1)
    return components, counts


def pair_component_multipliers(
    component_count: Sequence[int] | np.ndarray,
    endpoint_a_component_index: Sequence[int] | np.ndarray,
    endpoint_b_component_index: Sequence[int] | np.ndarray,
) -> np.ndarray:
    """Apply product for distinct components and one count for same-component pairs."""

    counts = np.asarray(component_count)
    a = np.asarray(endpoint_a_component_index, dtype=np.int64)
    b = np.asarray(endpoint_b_component_index, dtype=np.int64)
    if counts.ndim != 1 or a.ndim != 1 or b.ndim != 1 or a.size != b.size:
        raise ValueError("component counts and pair indices must be one-dimensional")
    if np.any(counts < 0) or np.any(a < 0) or np.any(b < 0):
        raise ValueError("component counts and indices cannot be negative")
    if a.size and (a.max() >= counts.size or b.max() >= counts.size):
        raise ValueError("pair component index outside participating components")
    left = counts[a]
    right = counts[b]
    return np.where(a == b, left, left * right)


def bootstrap_concordance_reference(
    *,
    cell_id: str,
    positive_scores: Sequence[float] | np.ndarray,
    unlabeled_scores: Sequence[float] | np.ndarray,
    unlabeled_weights: Sequence[float] | np.ndarray,
    positive_component_a: Sequence[str],
    positive_component_b: Sequence[str],
    unlabeled_component_a: Sequence[str],
    unlabeled_component_b: Sequence[str],
    replicates: int = BOOTSTRAP_REPLICATES,
) -> np.ndarray:
    """Small clean reference implementation used by pre-release fixtures."""

    all_components = tuple(
        map(str, positive_component_a)
    ) + tuple(map(str, positive_component_b)) + tuple(map(str, unlabeled_component_a)) + tuple(
        map(str, unlabeled_component_b)
    )
    components, draws = component_draws(all_components, cell_id=cell_id, replicates=replicates)
    index = {component: position for position, component in enumerate(components)}

    def indexes(values: Sequence[str]) -> np.ndarray:
        try:
            return np.fromiter((index[str(value)] for value in values), dtype=np.int64)
        except KeyError as exc:  # pragma: no cover - defended by all_components
            raise RuntimeError("component mapping failed") from exc

    p_a, p_b = indexes(positive_component_a), indexes(positive_component_b)
    u_a, u_b = indexes(unlabeled_component_a), indexes(unlabeled_component_b)
    output = np.empty(replicates, dtype=np.float64)
    for replicate in range(replicates):
        p_multiplier = pair_component_multipliers(draws[replicate], p_a, p_b)
        u_multiplier = pair_component_multipliers(draws[replicate], u_a, u_b)
        if p_multiplier.sum() == 0 or u_multiplier.sum() == 0:
            output[replicate] = np.nan
        else:
            output[replicate] = weighted_pairwise_concordance(
                positive_scores,
                unlabeled_scores,
                unlabeled_weights,
                positive_multipliers=p_multiplier,
                unlabeled_multipliers=u_multiplier,
            )
    return output


def percentile_95(values: Sequence[float] | np.ndarray) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size == 0:
        raise ValueError("no finite bootstrap replicates")
    lower, upper = np.percentile(array, (2.5, 97.5), method="linear")
    return float(lower), float(upper)


def quantize_selection_metric(value: float) -> Decimal:
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("selection metric must be finite and in [0,1]")
    return Decimal(str(value)).quantize(SELECTION_QUANTUM, rounding=ROUND_HALF_UP)


def selection_key(
    *, candidate_id: str, family: str, metrics: Mapping[str, float]
) -> tuple[Any, ...]:
    """Ascending key whose minimum is the frozen selected candidate."""

    if family not in COMPLEXITY_ORDER:
        raise ValueError(f"unknown frozen family: {family}")
    missing = set(PRIMARY_CELLS) - set(metrics)
    if missing:
        raise ValueError(f"selection metrics missing cells: {sorted(missing)}")
    return (
        *(-quantize_selection_metric(metrics[cell]) for cell in PRIMARY_CELLS),
        COMPLEXITY_ORDER[family],
        str(candidate_id),
    )


def seed_metric_range(values: Mapping[int, float]) -> float:
    if set(values) != set(SEEDS):
        raise ValueError("exactly the three frozen seeds are required")
    scores = _finite_1d("seed metrics", [values[seed] for seed in SEEDS])
    return float(scores.max() - scores.min())


def degree_bin(degree: int) -> str:
    value = int(degree)
    if value < 0:
        raise ValueError("training degree cannot be negative")
    if value <= 2:
        return str(value)
    for lower, upper in ((3, 4), (5, 9), (10, 19), (20, 49), (50, 99)):
        if lower <= value <= upper:
            return f"{lower}-{upper}"
    return "100+"


def degree_pair_stratum(degree_a: int, degree_b: int) -> str:
    ordered_bins = {value: index for index, value in enumerate(
        ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")
    )}
    values = sorted((degree_bin(degree_a), degree_bin(degree_b)), key=ordered_bins.__getitem__)
    return f"{values[0]}|{values[1]}"


def frozen_hub_sets(degree_by_endpoint: Mapping[str, int]) -> dict[str, frozenset[str]]:
    if len(degree_by_endpoint) != 11_900:
        raise ValueError("hub ranks require all 11,900 training-partition endpoints")
    ranked = sorted(degree_by_endpoint, key=lambda endpoint: (-int(degree_by_endpoint[endpoint]), endpoint))
    output = {
        "top_1_percent": frozenset(ranked[:119]),
        "top_5_percent": frozenset(ranked[:595]),
        "top_10_percent": frozenset(ranked[:1190]),
    }
    expected_minimum = {"top_1_percent": 41, "top_5_percent": 14, "top_10_percent": 7}
    for name, endpoints in output.items():
        if min(map(degree_by_endpoint.__getitem__, endpoints)) != expected_minimum[name]:
            raise RuntimeError(f"frozen hub threshold drift: {name}")
    return output


def exact_interolog_reference(
    similarity_a: np.ndarray,
    similarity_b: np.ndarray,
    edge_u: np.ndarray,
    edge_v: np.ndarray,
) -> float:
    left = np.minimum(similarity_a[edge_u], similarity_b[edge_v])
    right = np.minimum(similarity_a[edge_v], similarity_b[edge_u])
    return float(np.maximum(left, right).max(initial=0.0))


def neighbor_max_similarity(
    similarities: np.ndarray, edge_u: np.ndarray, edge_v: np.ndarray
) -> np.ndarray:
    """For every query and graph node, max similarity to one graph neighbor."""

    source = np.asarray(similarities, dtype=np.float64)
    if source.ndim != 2:
        raise ValueError("similarity matrix must be two-dimensional")
    output = np.zeros_like(source)
    for u, v in zip(np.asarray(edge_u, dtype=np.int64), np.asarray(edge_v, dtype=np.int64), strict=True):
        output[:, u] = np.maximum(output[:, u], source[:, v])
        output[:, v] = np.maximum(output[:, v], source[:, u])
    return output


def exact_interolog_from_neighbor_max(
    similarities: np.ndarray,
    neighbor_max: np.ndarray,
    pair_a: Sequence[int] | np.ndarray,
    pair_b: Sequence[int] | np.ndarray,
) -> np.ndarray:
    """Vectorized max-min identity exactly equivalent to edge enumeration."""

    source = np.asarray(similarities, dtype=np.float64)
    neighbor = np.asarray(neighbor_max, dtype=np.float64)
    a = np.asarray(pair_a, dtype=np.int64)
    b = np.asarray(pair_b, dtype=np.int64)
    if source.shape != neighbor.shape or a.shape != b.shape:
        raise ValueError("interolog inputs do not align")
    return np.minimum(source[a], neighbor[b]).max(axis=1)


def sampled_weighted_average_precision(
    positive_scores: Sequence[float] | np.ndarray,
    unlabeled_scores: Sequence[float] | np.ndarray,
    unlabeled_weights: Sequence[float] | np.ndarray,
) -> float:
    """Diagnostic weighted average precision on the sampled P-versus-U view."""

    p = _finite_1d("positive_scores", positive_scores)
    u = _finite_1d("unlabeled_scores", unlabeled_scores)
    w = _finite_1d("unlabeled_weights", unlabeled_weights)
    if u.size != w.size or np.any(w <= 0):
        raise ValueError("U rows and weights do not align")
    scores = np.concatenate((p, u))
    positive_weight = np.concatenate((np.ones(p.size), np.zeros(u.size)))
    total_weight = np.concatenate((np.ones(p.size), w))
    order = np.argsort(-scores, kind="mergesort")
    scores = scores[order]
    positive_weight = positive_weight[order]
    total_weight = total_weight[order]
    # Threshold metrics are evaluated after each complete exact-score tie group.
    group_end = np.r_[np.flatnonzero(scores[1:] != scores[:-1]), scores.size - 1]
    cumulative_positive = np.cumsum(positive_weight, dtype=np.float64)
    cumulative_total = np.cumsum(total_weight, dtype=np.float64)
    recall = cumulative_positive[group_end] / p.size
    precision = cumulative_positive[group_end] / cumulative_total[group_end]
    recall_increment = np.diff(np.r_[0.0, recall])
    return float(np.dot(recall_increment, precision))


def quantitative_stratum_status(
    positive_rows: int, participating_components: int
) -> str:
    return (
        "quantitative"
        if int(positive_rows) >= 100 and int(participating_components) >= 10
        else "descriptive_below_floor"
    )


def validate_scorer_census(scorer_ids: Iterable[str], *, run_ids: Iterable[str], candidate_ids: Iterable[str]) -> None:
    scorers = tuple(scorer_ids)
    if len(scorers) != len(set(scorers)) or len(scorers) != 49:
        raise RuntimeError("development scorer census must contain 49 unique scorers")
    if set(DETERMINISTIC_SCORERS) - set(scorers):
        raise RuntimeError("mandatory deterministic scorer missing")
    if len(set(run_ids)) != 30 or len(set(candidate_ids)) != 10:
        raise RuntimeError("frozen run or candidate census drift")
