"""Known-positive retrieval metrics with explicit, deterministic tie semantics.

U is a reference label, never evidence of noninteraction. AP groups equal scores
at their complete threshold; rank/cutoff metrics average uniform tie orderings.
"""
from __future__ import annotations

import math
import numpy as np

CUTOFFS = (5, 10, 20)


def evaluate(scores, positive, cutoffs=CUTOFFS):
    scores = np.asarray(scores, dtype=np.float64)
    positive = np.asarray(positive)
    if (scores.ndim != 1 or positive.shape != scores.shape or positive.dtype != np.bool_
            or not np.isfinite(scores).all() or not positive.any() or positive.all()):
        raise ValueError("Finite aligned scores, Boolean labels, and both P and U are required")
    n, p = len(scores), int(positive.sum())
    if any(isinstance(k, bool) or not isinstance(k, int) or not 0 < k <= n for k in cutoffs):
        raise ValueError("Cutoffs must be positive integers within the candidate list")
    ps, us = scores[positive], scores[~positive]
    concordance = float(((ps[:, None] > us).astype(float) + .5 * (ps[:, None] == us)).mean())
    order = np.argsort(-scores, kind="stable")
    sorted_scores, labels = scores[order], positive[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_scores)) + 1]
    stops = np.r_[starts[1:], n]
    groups = [(int(start), int(stop), int(labels[start:stop].sum())) for start, stop in zip(starts, stops)]
    cumulative, ap = 0, 0.
    for start, stop, hits in groups:
        cumulative += hits
        ap += (hits / p) * (cumulative / stop)
    first_start, first_stop, first_hits = next(group for group in groups if group[2])
    width = first_stop - first_start
    # The first positive occupies slot j with a negative-hypergeometric law.
    probability, reciprocal_rank = first_hits / width, 0.
    for j in range(1, width - first_hits + 2):
        reciprocal_rank += probability / (first_start + j)
        if j < width - first_hits + 1:
            probability *= (width - j - first_hits + 1) / (width - j)
    result = {"P": p, "U": n - p, "panel_size": n, "P_vs_U_concordance": concordance,
              "average_precision": float(ap),
              "first_positive_rank_min": first_start + 1,
              "first_positive_rank_max": first_stop - first_hits + 1,
              "first_positive_rank_expected": first_start + (width + 1) / (first_hits + 1),
              "reciprocal_rank": float(reciprocal_rank)}
    for k in cutoffs:
        recovered, dcg = 0., 0.
        for start, stop, hits in groups:
            if start >= k:
                break
            slots = min(k, stop) - start
            recovered += slots * hits / (stop - start)
            dcg += hits / (stop - start) * sum(1 / math.log2(rank + 1) for rank in range(start + 1, min(k, stop) + 1))
        ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, p) + 1))
        selected = min(max(k - first_start, 0), width)
        no_hit = 1.
        for j in range(selected):
            if j >= width - first_hits:
                no_hit = 0.
                break
            no_hit *= (width - first_hits - j) / (width - j)
        result.update({f"recovered_P_at_{k}": float(recovered), f"recall_at_{k}": recovered / p,
                       f"known_positive_precision_at_{k}": recovered / k,
                       f"EF_at_{k}": (recovered / k) / (p / n),
                       f"NDCG_at_{k}": float(dcg / ideal),
                       f"target_success_at_{k}": float(1 - no_hit)})
    return result


def positive_ranks(score, population, cutoffs=CUTOFFS):
    values = np.asarray(population, np.float64)
    if values.ndim != 1 or not np.isfinite(values).all() or not math.isfinite(score):
        raise ValueError("Finite rank inputs required")
    above, tied = int((values > score).sum()), int((values == score).sum())
    if not tied:
        raise ValueError("Positive score is absent from its candidate list")
    result = {"rank_min": above + 1, "rank_max": above + tied,
              "rank_mid": above + (tied + 1) / 2, "panel_size": len(values)}
    result.update({f"top{k}_fractional_credit": min(1., max(0., (k - above) / tied)) for k in cutoffs})
    return result
