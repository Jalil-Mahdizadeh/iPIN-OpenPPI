"""Exact weighted PU concordance and paired component resampling on CUDA."""
from __future__ import annotations

import numpy as np
import torch

from ipin_openppi.development_evaluation.semantics import component_draws, weighted_pairwise_concordance


def point(scores: np.ndarray, data: dict) -> float:
    positive = data["positive"]
    return weighted_pairwise_concordance(scores[positive], scores[~positive], data["weight"][~positive])


def bootstrap(scores: np.ndarray, data: dict, *, cell: str, replicates: int = 2000,
              device="cuda", deadline_check=lambda: None, batch=16) -> np.ndarray:
    if scores.ndim == 1:
        scores = scores[:, None]
    if scores.shape[0] != data["positive"].size or not np.isfinite(scores).all():
        raise ValueError("Invalid score dimensions or values")
    components, counts = component_draws(data["components"], cell_id=cell, replicates=replicates)
    if list(components) != list(data["components"]):
        raise ValueError("Bootstrap component-index order mismatch")
    positive = data["positive"]
    a = torch.as_tensor(data["component_a"], dtype=torch.int64, device=device)
    b = torch.as_tensor(data["component_b"], dtype=torch.int64, device=device)
    pa, pb, ua, ub = a[positive], b[positive], a[~positive], b[~positive]
    weights = torch.as_tensor(data["weight"][~positive], dtype=torch.float64, device=device)
    count_tensor = torch.as_tensor(counts, dtype=torch.float64, device=device)
    output = np.empty((replicates, scores.shape[1]), dtype=np.float64)
    for j in range(scores.shape[1]):
        pscore, uscore = scores[positive, j], scores[~positive, j]
        order = np.argsort(uscore, kind="mergesort")
        sorted_u = uscore[order]
        left = torch.as_tensor(np.searchsorted(sorted_u, pscore, side="left"), dtype=torch.int64, device=device)
        right = torch.as_tensor(np.searchsorted(sorted_u, pscore, side="right"), dtype=torch.int64, device=device)
        ordering = torch.as_tensor(order, dtype=torch.int64, device=device)
        for start in range(0, replicates, batch):
            deadline_check()
            c = count_tensor[start:start + batch]
            p_mult = torch.where(pa == pb, c[:, pa], c[:, pa] * c[:, pb])
            u_mult = torch.where(ua == ub, c[:, ua], c[:, ua] * c[:, ub])
            u_weight = (u_mult * weights).index_select(1, ordering)
            cumulative = torch.cat((torch.zeros((c.shape[0], 1), dtype=torch.float64, device=device),
                                    u_weight.cumsum(dim=1)), dim=1)
            favorable = 0.5 * (cumulative[:, left] + cumulative[:, right])
            denominator = p_mult.sum(1) * u_weight.sum(1)
            values = (favorable * p_mult).sum(1) / denominator
            output[start:start + c.shape[0], j] = values.cpu().numpy()
    return output


def gate(candidate_seed_scores: np.ndarray, data: dict, distributions: np.ndarray, *, seed_range_limit=.02) -> dict:
    baseline_seed = [point(data["baseline"][:, j], data) for j in range(3)]
    candidate_seed = [point(candidate_seed_scores[:, j], data) for j in range(3)]
    baseline = point(data["baseline"].mean(1), data)
    candidate = point(candidate_seed_scores.mean(1), data)
    finite = bool(np.isfinite(distributions).all())
    interval = np.quantile(distributions[:, 1] - distributions[:, 0], [.025, .975]).tolist() if finite else None
    deltas = np.subtract(candidate_seed, baseline_seed).tolist()
    seed_range = float(np.ptp(candidate_seed))
    checks = {
        "ensemble_gain_positive": bool(candidate > baseline),
        "all_three_matched_seed_gains_positive": bool(min(deltas) > 0),
        "candidate_seed_range_at_most_0_02": bool(seed_range <= seed_range_limit),
        "all_bootstrap_replicates_finite": finite,
        "paired_interval_lower_above_zero": bool(finite and interval[0] > 0),
    }
    return {"passed": all(checks.values()), "checks": checks, "baseline_concordance": baseline,
            "candidate_concordance": candidate, "gain": candidate - baseline,
            "paired_gain_ci95": interval, "baseline_seed_concordances": baseline_seed,
            "candidate_seed_concordances": candidate_seed, "matched_seed_gains": deltas,
            "candidate_seed_range": seed_range, "bootstrap_replicates": int(distributions.shape[0]),
            "interval_is_post_selection_development_screen_not_confirmatory": True}
