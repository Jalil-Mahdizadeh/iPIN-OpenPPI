"""Frozen development metrics, diagnostics, selection, and kill-rule trace."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pyarrow.parquet as pq
import torch

from .release import sha256_file
from .semantics import (
    DETERMINISTIC_SCORERS,
    PRIMARY_CELLS,
    bootstrap_cell_seed,
    component_draws,
    degree_pair_stratum,
    frozen_hub_sets,
    percentile_95,
    quantitative_stratum_status,
    sampled_weighted_average_precision,
    seed_metric_range,
    selection_key,
    weighted_pairwise_concordance,
)


BOOTSTRAP_SCORER_COUNT = 19
BOOTSTRAP_BATCH = 16
SIMPLE_SEQUENCE_DETERMINISTIC = (
    "within_pair_3mer_cosine",
    "exact_training_interolog_3mer",
)
SHORTCUT_SCORERS = (
    "training_degree_sum",
    "preferential_attachment",
    "component_degree_mass_product",
    "training_common_neighbors",
    "sequence_length_sum",
    "sequence_length_ratio",
)


def _read_cell(cell_root: Path) -> tuple[Any, np.ndarray, list[str], dict[str, int]]:
    manifest = json.loads((cell_root / "CELL_SCORE_MANIFEST.json").read_text(encoding="utf-8"))
    rows_path = cell_root / str(manifest["rows"]["path"])
    scores_path = cell_root / str(manifest["scores"]["path"])
    scorers_path = cell_root / str(manifest["scorers"]["path"])
    for path, record in (
        (rows_path, manifest["rows"]),
        (scores_path, manifest["scores"]),
        (scorers_path, manifest["scorers"]),
    ):
        if path.stat().st_size != int(record["bytes"]) or sha256_file(path) != str(record["sha256"]):
            raise RuntimeError(f"private cell artifact drift: {path}")
    rows = pq.read_table(rows_path)
    scores = np.load(scores_path, mmap_mode="r", allow_pickle=False)
    scorer_payload = json.loads(scorers_path.read_text(encoding="utf-8"))
    scorer_ids = [str(item["scorer_id"]) for item in scorer_payload["scorers"]]
    if scores.shape != (rows.num_rows, 49) or scores.dtype != np.float64 or len(scorer_ids) != 49:
        raise RuntimeError("private development score matrix identity drift")
    if not np.isfinite(scores).all():
        raise RuntimeError("nonfinite private development score")
    return rows, scores, scorer_ids, {value: index for index, value in enumerate(scorer_ids)}


def _state_masks(rows: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    state = np.asarray(rows["state"].to_pylist(), dtype=object)
    p_mask = state == "released_positive"
    u_mask = state == "unlabeled"
    if np.any(p_mask & u_mask) or not np.all(p_mask | u_mask) or not p_mask.any() or not u_mask.any():
        raise RuntimeError("development P/U state masks invalid")
    numerator = np.asarray(rows["sampling_weight_numerator"].to_numpy(), dtype=np.float64)
    denominator = np.asarray(rows["sampling_weight_denominator"].to_numpy(), dtype=np.float64)
    weights = numerator / denominator
    if not np.all(weights[p_mask] == 1.0) or np.any(weights[u_mask] <= 0):
        raise RuntimeError("development rational design weights invalid")
    return p_mask, u_mask, weights


def point_metrics(
    rows: Any,
    scores: np.ndarray,
    scorer_ids: Sequence[str],
    *,
    row_mask: np.ndarray | None = None,
) -> dict[str, dict[str, float]]:
    p_mask, u_mask, weights = _state_masks(rows)
    if row_mask is not None:
        selected = np.asarray(row_mask, dtype=bool)
        if selected.shape != p_mask.shape:
            raise ValueError("point-metric row mask shape drift")
        p_mask &= selected
        u_mask &= selected
    if not p_mask.any() or not u_mask.any():
        return {}
    output: dict[str, dict[str, float]] = {}
    for column, scorer_id in enumerate(scorer_ids):
        concordance = weighted_pairwise_concordance(
            scores[p_mask, column], scores[u_mask, column], weights[u_mask]
        )
        output[str(scorer_id)] = {
            "ht_positive_vs_U_concordance": concordance,
            "diagnostic_sampled_P_vs_U_AUROC": concordance,
            "diagnostic_sampled_P_vs_U_AUPRC": sampled_weighted_average_precision(
                scores[p_mask, column], scores[u_mask, column], weights[u_mask]
            ),
        }
    return output


def _component_indexes(rows: Any) -> tuple[tuple[str, ...], np.ndarray, np.ndarray, np.ndarray]:
    p_mask, u_mask, weights = _state_masks(rows)
    component_a = tuple(map(str, rows["endpoint_a_component_id"].to_pylist()))
    component_b = tuple(map(str, rows["endpoint_b_component_id"].to_pylist()))
    components = tuple(sorted(set(component_a) | set(component_b)))
    index = {component: position for position, component in enumerate(components)}
    a = np.fromiter((index[value] for value in component_a), dtype=np.int64, count=len(component_a))
    b = np.fromiter((index[value] for value in component_b), dtype=np.int64, count=len(component_b))
    return components, a, b, weights


def gpu_bootstrap_distributions(
    *,
    cell_id: str,
    rows: Any,
    scores: np.ndarray,
    scorer_ids: Sequence[str],
    bootstrap_scorer_ids: Sequence[str],
    output_root: Path,
) -> dict[str, Any]:
    """Exact paired 2,000-draw pigeonhole bootstrap on one CUDA GPU."""

    output_root.mkdir(parents=True, mode=0o700, exist_ok=False)
    p_mask, u_mask, _ = _state_masks(rows)
    components, pair_a, pair_b, weights = _component_indexes(rows)
    drawn_components, counts = component_draws(components, cell_id=cell_id, replicates=2_000)
    if drawn_components != components or counts.shape != (2_000, len(components)):
        raise RuntimeError("component draw identity drift")
    counts_path = output_root / "component_multiplicities.i32.npy"
    np.save(counts_path, counts, allow_pickle=False)
    scorer_index = {value: index for index, value in enumerate(scorer_ids)}
    if len(bootstrap_scorer_ids) != BOOTSTRAP_SCORER_COUNT:
        raise RuntimeError("bootstrap scorer census must be nine controls plus ten ensembles")
    distributions = np.full((len(bootstrap_scorer_ids), 2_000), np.nan, dtype=np.float64)

    device = torch.device("cuda")
    draw_tensor = torch.from_numpy(counts).to(device=device, dtype=torch.float64)
    p_a = torch.from_numpy(pair_a[p_mask]).to(device=device)
    p_b = torch.from_numpy(pair_b[p_mask]).to(device=device)
    u_a = torch.from_numpy(pair_a[u_mask]).to(device=device)
    u_b = torch.from_numpy(pair_b[u_mask]).to(device=device)
    design_weights = torch.from_numpy(weights[u_mask]).to(device=device, dtype=torch.float64)

    with torch.inference_mode():
        for scorer_position, scorer_id in enumerate(bootstrap_scorer_ids):
            column = scorer_index[str(scorer_id)]
            positive_scores = np.asarray(scores[p_mask, column], dtype=np.float64)
            unlabeled_scores = np.asarray(scores[u_mask, column], dtype=np.float64)
            order = np.argsort(unlabeled_scores, kind="mergesort")
            sorted_scores = unlabeled_scores[order]
            left = np.searchsorted(sorted_scores, positive_scores, side="left").astype(np.int64)
            right = np.searchsorted(sorted_scores, positive_scores, side="right").astype(np.int64)
            order_tensor = torch.from_numpy(order).to(device=device)
            left_tensor = torch.from_numpy(left).to(device=device)
            right_tensor = torch.from_numpy(right).to(device=device)
            for start in range(0, 2_000, BOOTSTRAP_BATCH):
                stop = min(start + BOOTSTRAP_BATCH, 2_000)
                batch_counts = draw_tensor[start:stop]
                p_left, p_right = batch_counts[:, p_a], batch_counts[:, p_b]
                u_left, u_right = batch_counts[:, u_a], batch_counts[:, u_b]
                p_multiplier = torch.where(p_a == p_b, p_left, p_left * p_right)
                u_multiplier = torch.where(u_a == u_b, u_left, u_left * u_right)
                weighted_u = u_multiplier * design_weights.unsqueeze(0)
                sorted_weight = weighted_u.index_select(1, order_tensor)
                cumulative = torch.cumsum(sorted_weight, dim=1, dtype=torch.float64)
                zero = torch.zeros((stop - start, 1), dtype=torch.float64, device=device)
                prefix = torch.cat((zero, cumulative), dim=1)
                below = prefix.index_select(1, left_tensor)
                at_or_below = prefix.index_select(1, right_tensor)
                favorable = below + 0.5 * (at_or_below - below)
                p_mass = p_multiplier.sum(dim=1, dtype=torch.float64)
                u_mass = weighted_u.sum(dim=1, dtype=torch.float64)
                numerator = (p_multiplier * favorable).sum(dim=1, dtype=torch.float64)
                value = numerator / (p_mass * u_mass)
                invalid = (p_mass <= 0) | (u_mass <= 0)
                value[invalid] = torch.nan
                distributions[scorer_position, start:stop] = value.cpu().numpy()
    distribution_path = output_root / "bootstrap_metrics.f64.npy"
    np.save(distribution_path, distributions, allow_pickle=False)
    scorer_path = output_root / "BOOTSTRAP_SCORERS.json"
    scorer_path.write_text(
        json.dumps({"cell_id": cell_id, "scorer_ids": list(bootstrap_scorer_ids)}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return {
        "cell_id": cell_id,
        "seed": bootstrap_cell_seed(cell_id),
        "replicates": 2_000,
        "participating_components": len(components),
        "scorer_count": len(bootstrap_scorer_ids),
        "finite_replicates_by_scorer": {
            scorer_id: int(np.isfinite(distributions[index]).sum())
            for index, scorer_id in enumerate(bootstrap_scorer_ids)
        },
        "component_multiplicities_sha256": sha256_file(counts_path),
        "bootstrap_metrics_sha256": sha256_file(distribution_path),
        "bootstrap_scorers_sha256": sha256_file(scorer_path),
    }


def _load_bootstrap(
    bootstrap_root: Path,
) -> tuple[list[str], np.ndarray]:
    scorer_ids = json.loads((bootstrap_root / "BOOTSTRAP_SCORERS.json").read_text(encoding="utf-8"))[
        "scorer_ids"
    ]
    values = np.load(bootstrap_root / "bootstrap_metrics.f64.npy", allow_pickle=False)
    if values.shape != (19, 2_000):
        raise RuntimeError("private bootstrap distribution shape drift")
    return list(map(str, scorer_ids)), values


def degree_and_hub_diagnostics(
    *,
    rows: Any,
    scores: np.ndarray,
    scorer_ids: Sequence[str],
    hub_sets: Mapping[str, frozenset[str]],
) -> dict[str, Any]:
    p_mask, u_mask, _ = _state_masks(rows)
    degree_a = np.asarray(rows["endpoint_a_training_degree"].to_numpy(), dtype=np.int64)
    degree_b = np.asarray(rows["endpoint_b_training_degree"].to_numpy(), dtype=np.int64)
    strata = np.asarray(
        [degree_pair_stratum(int(a), int(b)) for a, b in zip(degree_a, degree_b, strict=True)],
        dtype=object,
    )
    component_a = np.asarray(rows["endpoint_a_component_id"].to_pylist(), dtype=object)
    component_b = np.asarray(rows["endpoint_b_component_id"].to_pylist(), dtype=object)
    degree_output: dict[str, Any] = {}
    for stratum in sorted(set(strata)):
        mask = strata == stratum
        positive_count = int(np.count_nonzero(mask & p_mask))
        components = set(component_a[mask & p_mask]) | set(component_b[mask & p_mask])
        metrics = point_metrics(rows, scores, scorer_ids, row_mask=mask)
        degree_output[str(stratum)] = {
            "positive_rows": positive_count,
            "unlabeled_rows": int(np.count_nonzero(mask & u_mask)),
            "participating_positive_components": len(components),
            "status": quantitative_stratum_status(positive_count, len(components)),
            "metrics": metrics,
        }
    endpoint_a = np.asarray(rows["endpoint_a_sha256"].to_pylist(), dtype=object)
    endpoint_b = np.asarray(rows["endpoint_b_sha256"].to_pylist(), dtype=object)
    hub_output: dict[str, Any] = {}
    for name, endpoints in hub_sets.items():
        contains = np.fromiter(
            (str(a) in endpoints or str(b) in endpoints for a, b in zip(endpoint_a, endpoint_b, strict=True)),
            dtype=bool,
            count=rows.num_rows,
        )
        hub_output[name] = {
            "contains_hub": {
                "positive_rows": int(np.count_nonzero(contains & p_mask)),
                "unlabeled_rows": int(np.count_nonzero(contains & u_mask)),
                "metrics": point_metrics(rows, scores, scorer_ids, row_mask=contains),
            },
            "excludes_hub": {
                "positive_rows": int(np.count_nonzero(~contains & p_mask)),
                "unlabeled_rows": int(np.count_nonzero(~contains & u_mask)),
                "metrics": point_metrics(rows, scores, scorer_ids, row_mask=~contains),
            },
        }
    return {"degree_pair_strata": degree_output, "hub_views": hub_output}


def c1_novel_u_metrics(
    *,
    rows: Any,
    scores: np.ndarray,
    scorer_ids: Sequence[str],
    public_training_u_pair_ids: set[str],
) -> dict[str, Any]:
    p_mask, u_mask, weights = _state_masks(rows)
    pair_ids = np.asarray(rows["pair_id"].to_pylist(), dtype=object)
    retained_u = np.fromiter(
        (str(value) not in public_training_u_pair_ids for value in pair_ids),
        dtype=bool,
        count=rows.num_rows,
    ) & u_mask
    view = p_mask | retained_u
    strata = np.asarray(rows["stratum_id"].to_pylist(), dtype=object)
    retained_ids = pair_ids[retained_u]
    return {
        "positive_rows": int(p_mask.sum()),
        "retained_U_rows": int(retained_u.sum()),
        "removed_U_rows": int(u_mask.sum() - retained_u.sum()),
        "retained_U_weight_sum": float(weights[retained_u].sum(dtype=np.float64)),
        "retained_nonempty_strata": len(set(strata[retained_u])),
        "retained_pair_id_unique": len(set(map(str, retained_ids))) == retained_ids.size,
        "interpretation": "design_weighted_Hajek_ratio_over_realized_novel_U_view",
        "selection_or_stopping_use": False,
        "metrics": point_metrics(rows, scores, scorer_ids, row_mask=view),
    }


def score_correlations(scores: np.ndarray, scorer_ids: Sequence[str]) -> dict[str, Any]:
    controls = [
        "training_degree_sum",
        "preferential_attachment",
        "component_degree_mass_product",
        "training_common_neighbors",
        "sequence_length_sum",
        "sequence_length_ratio",
        "within_pair_3mer_cosine",
        "exact_training_interolog_3mer",
    ]
    index = {value: position for position, value in enumerate(scorer_ids)}
    output: dict[str, Any] = {}
    for scorer_id in scorer_ids:
        values = np.asarray(scores[:, index[scorer_id]], dtype=np.float64)
        record: dict[str, float | None] = {}
        for control in controls:
            comparator = np.asarray(scores[:, index[control]], dtype=np.float64)
            if np.std(values) == 0 or np.std(comparator) == 0:
                record[control] = None
            else:
                record[control] = float(np.corrcoef(values, comparator)[0, 1])
        output[str(scorer_id)] = record
    return {"method": "unweighted_P_and_sampled_U_Pearson_diagnostic", "values": output}


def _candidate_metadata(training_registry: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(candidate["candidate_id"]): {
            "family": str(candidate["family"]),
            "recipe_id": str(candidate["recipe_id"]),
            "members": [str(member["run_id"]) for member in candidate["members"]],
        }
        for candidate in training_registry["ensembles"]
    }


def apply_selection_and_kill_rules(
    *,
    point_by_cell: Mapping[str, Mapping[str, Mapping[str, float]]],
    bootstrap_by_cell: Mapping[str, tuple[Sequence[str], np.ndarray]],
    hub_by_cell: Mapping[str, Mapping[str, Any]],
    novel_u: Mapping[str, Any],
    training_registry: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = _candidate_metadata(training_registry)
    metrics = {
        candidate_id: {
            cell: float(point_by_cell[cell][candidate_id]["ht_positive_vs_U_concordance"])
            for cell in PRIMARY_CELLS
        }
        for candidate_id in candidates
    }
    seed_ranges: dict[str, dict[str, float]] = defaultdict(dict)
    eligible: dict[str, bool] = {}
    for candidate_id, record in candidates.items():
        for cell in PRIMARY_CELLS:
            seed_ranges[candidate_id][cell] = seed_metric_range(
                {
                    int(member.rsplit("seed", 1)[1]): float(
                        point_by_cell[cell][member]["ht_positive_vs_U_concordance"]
                    )
                    for member in record["members"]
                }
            )
        eligible[candidate_id] = all(value <= 0.02 for value in seed_ranges[candidate_id].values())
    eligible_candidates = [candidate for candidate in candidates if eligible[candidate]]
    selected = (
        min(
            eligible_candidates,
            key=lambda candidate: selection_key(
                candidate_id=candidate,
                family=candidates[candidate]["family"],
                metrics=metrics[candidate],
            ),
        )
        if eligible_candidates
        else None
    )

    def distribution(cell: str, scorer: str) -> np.ndarray:
        scorer_ids, values = bootstrap_by_cell[cell]
        return values[list(scorer_ids).index(scorer)]

    def delta_record(cell: str, left: str, right: str) -> dict[str, Any]:
        delta = metrics[left][cell] - float(
            point_by_cell[cell][right]["ht_positive_vs_U_concordance"]
        )
        values = distribution(cell, left) - distribution(cell, right)
        lower, upper = percentile_95(values)
        return {
            "candidate": left,
            "comparator": right,
            "cell": cell,
            "delta": delta,
            "paired_percentile_95": [lower, upper],
            "interval_excludes_zero_positive": lower > 0,
        }

    simple_candidates = [
        candidate for candidate, record in candidates.items() if record["family"] in {
            "lightweight_esm2_150m_linear", "esm2_650m_linear_ablation"
        }
    ]
    simple_by_cell: dict[str, str] = {}
    for cell in PRIMARY_CELLS:
        choices = list(SIMPLE_SEQUENCE_DETERMINISTIC) + simple_candidates
        simple_by_cell[cell] = max(
            choices,
            key=lambda scorer: float(point_by_cell[cell][scorer]["ht_positive_vs_U_concordance"]),
        )
    linear_650 = [
        candidate for candidate, record in candidates.items() if record["family"] == "esm2_650m_linear_ablation"
    ]
    strongest_650_c3 = max(linear_650, key=lambda scorer: metrics[scorer]["C3_development"])
    no_gate_by_recipe = {
        record["recipe_id"]: candidate
        for candidate, record in candidates.items()
        if record["family"] == "esm2_650m_nonlinear_no_gate_ablation"
    }
    partner_candidates = [
        candidate for candidate, record in candidates.items() if record["family"] == "esm2_650m_partner_gated_primary"
    ]
    partner_trace: dict[str, Any] = {}
    any_qualifying_c3 = False
    any_qualifying_c2 = False
    for candidate in partner_candidates:
        baseline_delta = delta_record("C3_development", candidate, simple_by_cell["C3_development"])
        linear_delta = delta_record("C3_development", candidate, strongest_650_c3)
        no_gate = no_gate_by_recipe[candidates[candidate]["recipe_id"]]
        gate_delta = delta_record("C3_development", candidate, no_gate)
        named_source_deltas = {}
        for source_cell in (
            "source_exclusive:HI-II-14:C3_development",
            "source_exclusive:HuRI:C3_development",
        ):
            source_choices = list(SIMPLE_SEQUENCE_DETERMINISTIC) + simple_candidates
            source_baseline = max(
                source_choices,
                key=lambda scorer: float(
                    point_by_cell[source_cell][scorer]["ht_positive_vs_U_concordance"]
                ),
            )
            named_source_deltas[source_cell] = metrics[candidate]["C3_development"] * 0 + (
                float(point_by_cell[source_cell][candidate]["ht_positive_vs_U_concordance"])
                - float(point_by_cell[source_cell][source_baseline]["ht_positive_vs_U_concordance"])
            )
        outside = hub_by_cell["C3_development"]["hub_views"]["top_10_percent"]["excludes_hub"][
            "metrics"
        ]
        outside_delta = float(outside[candidate]["ht_positive_vs_U_concordance"]) - float(
            outside[simple_by_cell["C3_development"]]["ht_positive_vs_U_concordance"]
        )
        checks = {
            "C3_vs_strongest_simple_at_least_0_02": baseline_delta["delta"] >= 0.02,
            "C3_vs_strongest_simple_interval_positive": baseline_delta[
                "interval_excludes_zero_positive"
            ],
            "C3_vs_650m_linear_at_least_0_01": linear_delta["delta"] >= 0.01,
            "C3_vs_650m_linear_interval_positive": linear_delta["interval_excludes_zero_positive"],
            "C3_vs_matched_no_gate_at_least_0_005": gate_delta["delta"] >= 0.005,
            "C3_vs_matched_no_gate_interval_positive": gate_delta["interval_excludes_zero_positive"],
            "positive_named_source_direction": any(value > 0 for value in named_source_deltas.values()),
            "positive_outside_top_10_percent_hubs": outside_delta > 0,
            "all_seed_ranges_at_most_0_02": eligible[candidate],
        }
        retained = all(checks.values())
        partner_trace[candidate] = {
            "baseline_delta": baseline_delta,
            "linear_650m_delta": linear_delta,
            "matched_no_gate_delta": gate_delta,
            "named_source_deltas": named_source_deltas,
            "outside_top_10_percent_hub_delta": outside_delta,
            "checks": checks,
            "partner_gate_retained": retained,
        }
        any_qualifying_c3 |= (
            baseline_delta["delta"] >= 0.02 and baseline_delta["interval_excludes_zero_positive"]
        )
        c2_delta = delta_record("C2_development", candidate, simple_by_cell["C2_development"])
        any_qualifying_c2 |= c2_delta["delta"] >= 0.02 and c2_delta[
            "interval_excludes_zero_positive"
        ]

    complex_candidates = [
        candidate for candidate, record in candidates.items() if record["family"] in {
            "esm2_650m_nonlinear_no_gate_ablation", "esm2_650m_partner_gated_primary"
        }
    ]
    complex_vs_baseline = {
        candidate: delta_record("C3_development", candidate, simple_by_cell["C3_development"])
        for candidate in complex_candidates
    }
    qualifying_complex = [
        candidate
        for candidate, record in complex_vs_baseline.items()
        if record["delta"] >= 0.02 and record["interval_excludes_zero_positive"]
    ]
    best_complex = max(complex_candidates, key=lambda value: metrics[value]["C3_development"])
    best_complex_interval = percentile_95(distribution("C3_development", best_complex))
    best_shortcut_c1 = max(
        SHORTCUT_SCORERS,
        key=lambda scorer: float(
            point_by_cell["C1_development"][scorer]["ht_positive_vs_U_concordance"]
        ),
    )
    best_complex_c1 = max(complex_candidates, key=lambda value: metrics[value]["C1_development"])
    shortcut_explains_c1 = float(
        point_by_cell["C1_development"][best_shortcut_c1]["ht_positive_vs_U_concordance"]
    ) >= metrics[best_complex_c1]["C1_development"]
    best_complex_simple_delta = delta_record(
        "C3_development", best_complex, simple_by_cell["C3_development"]
    )
    outside_metrics = hub_by_cell["C3_development"]["hub_views"]["top_10_percent"]["excludes_hub"][
        "metrics"
    ]
    outside_gain = float(outside_metrics[best_complex]["ht_positive_vs_U_concordance"]) - float(
        outside_metrics[simple_by_cell["C3_development"]]["ht_positive_vs_U_concordance"]
    )
    c1_primary_gain = metrics[best_complex_c1]["C1_development"] - float(
        point_by_cell["C1_development"][simple_by_cell["C1_development"]][
            "ht_positive_vs_U_concordance"
        ]
    )
    c1_novel_gain = float(
        novel_u["metrics"][best_complex_c1]["ht_positive_vs_U_concordance"]
    ) - float(
        novel_u["metrics"][simple_by_cell["C1_development"]]["ht_positive_vs_U_concordance"]
    )

    kill = {
        "integrity_custody_or_protected_boundary_violation": False,
        "U_used_as_negative_or_probability_target": False,
        "no_complex_candidate_C3_gain_0_02_with_positive_interval": len(qualifying_complex) == 0,
        "best_complex_C3_lower_bound_not_above_0_5": best_complex_interval[0] <= 0.5,
        "shortcut_explains_C1_and_no_qualifying_C2_or_C3": shortcut_explains_c1
        and not any_qualifying_c2
        and not any_qualifying_c3,
        "interolog_or_linear_explains_complex_C3": best_complex_simple_delta["delta"] < 0.01
        or not best_complex_simple_delta["interval_excludes_zero_positive"],
        "gain_absent_outside_top_10_percent_hubs": outside_gain <= 0,
        "all_candidates_ineligible_or_failed": not eligible_candidates,
        "unsupported_claim_required": False,
        "development_released_before_registry_freeze": False,
        "post_release_training_or_retraining": False,
    }
    stop_before_protected = any(kill.values())
    partner_retained = [
        candidate for candidate, record in partner_trace.items() if record["partner_gate_retained"]
    ]
    if stop_before_protected:
        disposition = "stop_complex_model_claim_and_stop_before_protected_evaluation"
    elif partner_retained and selected in partner_retained:
        disposition = "advance_frozen_partner_gated_scorer_toward_separate_protected_authorization"
    else:
        disposition = "retain_only_simpler_frozen_baseline"
    return {
        "candidate_metrics": metrics,
        "seed_metric_ranges": dict(seed_ranges),
        "candidate_eligible": eligible,
        "selection_trace": {
            "selected_candidate_id": selected,
            "order": ["C3_development", "C2_development", "C1_development", "lower_complexity", "candidate_id"],
            "quantization": "decimal_0.001_ROUND_HALF_UP_selection_only",
            "strongest_simple_sequence_baseline_by_primary_cell": simple_by_cell,
        },
        "partner_gate_trace": partner_trace,
        "kill_trace": {
            "criteria": kill,
            "stop_before_protected_evaluation": stop_before_protected,
            "best_complex_candidate": best_complex,
            "best_complex_C3_percentile_95": list(best_complex_interval),
            "best_shortcut_C1": best_shortcut_c1,
            "outside_top_10_percent_hub_gain": outside_gain,
            "C1_primary_gain": c1_primary_gain,
            "C1_novel_U_gain": c1_novel_gain,
            "withdraw_C1_gain_claim": c1_primary_gain > 0 and c1_novel_gain <= 0,
        },
        "development_stage_disposition": disposition,
    }
