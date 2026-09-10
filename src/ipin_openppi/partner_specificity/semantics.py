"""Pure, testable split, within-anchor, and endpoint-balanced estimands."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib

import numpy as np


def assign_folds(sizes: dict[str, int], count: int, salt: str) -> dict[str, int]:
    if count < 2 or any(size <= 0 for size in sizes.values()):
        raise ValueError("positive component sizes and at least two folds required")
    totals = [0] * count
    result = {}
    ordered = sorted(sizes, key=lambda c: (-sizes[c], hashlib.sha256(
        f"{salt}:{c}".encode()).digest(), c))
    for component in ordered:
        fold = min(range(count), key=lambda f: (totals[f], f))
        result[component] = fold
        totals[fold] += sizes[component]
    return result


def pair_codes(a: np.ndarray, b: np.ndarray, n: int) -> np.ndarray:
    a, b = np.asarray(a, dtype=np.int64), np.asarray(b, dtype=np.int64)
    if a.shape != b.shape or np.any(a == b) or np.any(a < 0) or np.any(b < 0):
        raise ValueError("invalid pair endpoints")
    if np.any(a >= n) or np.any(b >= n):
        raise ValueError("endpoint outside universe")
    return np.minimum(a, b) * n + np.maximum(a, b)


def cell_masks(a: np.ndarray, b: np.ndarray, folds: np.ndarray, fold: int):
    left, right = folds[a] == fold, folds[b] == fold
    return ~left & ~right, left ^ right, left & right


def normalize(raw: np.ndarray, fit: np.ndarray, floor: float = 1e-6):
    if fit.dtype != bool or fit.shape != (len(raw),) or not fit.any() or fit.all():
        raise ValueError("explicit nonempty fit and heldout endpoint masks required")
    if not np.isfinite(raw).all():
        raise ValueError("nonfinite embeddings")
    fit_values = raw[fit].astype(np.float64)
    mean = fit_values.mean(axis=0)
    std = np.maximum(fit_values.std(axis=0, ddof=0), floor)
    values = ((raw.astype(np.float64) - mean) / std).astype(np.float32)
    return values, mean, std


def embedding_indices(vectors: list[dict], endpoints: list[str], row_count: int):
    if len(vectors) != row_count or len(set(endpoints)) != len(endpoints):
        raise ValueError("embedding/endpoint identity census mismatch")
    lookup = {}
    rows = set()
    for item in vectors:
        sha, row = item["sequence_sha256"], int(item["row_index"])
        if sha in lookup or row in rows or not 0 <= row < row_count:
            raise ValueError("duplicate or invalid embedding identity")
        lookup[sha] = row
        rows.add(row)
    try:
        return np.array([lookup[e] for e in endpoints], dtype=np.int64)
    except KeyError as exc:
        raise ValueError("missing embedding identity") from exc


@dataclass(frozen=True)
class Query:
    anchor: int
    positive: np.ndarray
    positive_partner: np.ndarray
    unlabeled: np.ndarray
    unlabeled_partner: np.ndarray


def build_queries(a: np.ndarray, b: np.ndarray, positive: np.ndarray) -> list[Query]:
    if a.shape != b.shape or a.shape != positive.shape or positive.dtype != bool:
        raise ValueError("pair/state shape mismatch")
    if np.any(a == b):
        raise ValueError("self edges prohibited")
    anchor = np.concatenate((a, b))
    partner = np.concatenate((b, a))
    rows = np.tile(np.arange(len(a)), 2)
    order = np.argsort(anchor, kind="stable")
    starts = np.r_[0, 1 + np.flatnonzero(np.diff(anchor[order])), len(order)]
    result = []
    for start, stop in zip(starts[:-1], starts[1:]):
        idx = order[start:stop]
        p = positive[rows[idx]]
        if p.any() and (~p).any():
            result.append(Query(int(anchor[idx[0]]), rows[idx[p]], partner[idx[p]],
                                rows[idx[~p]], partner[idx[~p]]))
    return result


def weighted_concordance(p, u, weights, p_weights=None) -> float:
    p, u, weights = map(lambda x: np.asarray(x, dtype=np.float64), (p, u, weights))
    pw = np.ones(len(p)) if p_weights is None else np.asarray(p_weights, dtype=np.float64)
    if not len(p) or not len(u) or len(weights) != len(u) or pw.shape != p.shape:
        raise ValueError("nonempty aligned score/weight arrays required")
    if not all(np.isfinite(x).all() for x in (p, u, weights, pw)):
        raise ValueError("nonfinite scores or weights")
    if np.any(weights < 0) or np.any(pw < 0) or weights.sum() <= 0 or pw.sum() <= 0:
        raise ValueError("positive weight masses required")
    order = np.argsort(u, kind="stable")
    cumulative = np.r_[0., np.cumsum(weights[order])]
    left, right = np.searchsorted(u[order], p, side="left"), np.searchsorted(u[order], p, side="right")
    return float(np.dot(pw, (cumulative[left] + cumulative[right]) * .5) / (pw.sum() * weights.sum()))


def anchor_points(scores, queries, weights, bins=None):
    result = []
    for q in queries:
        if bins is None:
            value = weighted_concordance(scores[q.positive], scores[q.unlabeled], weights[q.unlabeled])
        else:
            numerator, denominator = 0., 0
            for bin_id in np.unique(bins[q.positive_partner]):
                p = q.positive[bins[q.positive_partner] == bin_id]
                u = q.unlabeled[bins[q.unlabeled_partner] == bin_id]
                if len(u):
                    numerator += len(p) * weighted_concordance(scores[p], scores[u], weights[u])
                    denominator += len(p)
            value = numerator / denominator if denominator else np.nan
        result.append(value)
    return np.asarray(result, dtype=np.float64)


def bootstrap_anchor_totals(scores, queries, weights, component, multipliers):
    """Recompute query ratios, weighting the anchor and each distinct partner component."""
    replicates = len(multipliers)
    total, mass = np.zeros(replicates), np.zeros(replicates)
    for q in queries:
        comp = component[q.anchor]
        pscore, uscore = scores[q.positive], scores[q.unlabeled]
        order = np.argsort(uscore, kind="stable")
        pm = multipliers[:, component[q.positive_partner]].astype(np.float64)
        um = multipliers[:, component[q.unlabeled_partner[order]]].astype(np.float64)
        pm[:, component[q.positive_partner] == comp] = 1
        um[:, component[q.unlabeled_partner[order]] == comp] = 1
        um *= weights[q.unlabeled[order]]
        prefix = np.concatenate((np.zeros((replicates, 1)), np.cumsum(um, axis=1)), axis=1)
        left = np.searchsorted(uscore[order], pscore, side="left")
        right = np.searchsorted(uscore[order], pscore, side="right")
        numerator = np.sum(pm * (prefix[:, left] + prefix[:, right]) * .5, axis=1)
        denominator = pm.sum(axis=1) * prefix[:, -1]
        valid = denominator > 0
        anchor_mass = multipliers[:, comp] * valid
        values = np.divide(numerator, denominator, out=np.zeros(replicates), where=valid)
        total += anchor_mass * values
        mass += anchor_mass
    return total, mass


def panel_recall(scores, queries, k, tie_keys):
    output = []
    for q in queries:
        rows = np.concatenate((q.positive, q.unlabeled))
        order = np.lexsort((tie_keys[rows], -scores[rows]))
        output.append(float(np.isin(rows[order[:k]], q.positive).sum() / len(q.positive)))
    return np.array(output)


def select_quartets(a, b, positive, n, *, salt, maximum, edge_cap, endpoint_cap):
    """Both alternative matchings, selected only if both crosses are released U."""
    p_rows, u_rows = np.flatnonzero(positive), np.flatnonzero(~positive)
    u_codes = pair_codes(a[u_rows], b[u_rows], n)
    u_order = np.argsort(u_codes)
    u_codes = u_codes[u_order]
    candidates = []
    for i, first in enumerate(p_rows[:-1]):
        second = p_rows[i + 1:]
        aa, bb = int(a[first]), int(b[first])
        distinct = (a[second] != aa) & (a[second] != bb) & (b[second] != aa) & (b[second] != bb)
        second = second[distinct]
        for swap in (False, True):
            c, d = (b[second], a[second]) if swap else (a[second], b[second])
            code1 = np.minimum(aa, d) * n + np.maximum(aa, d)
            code2 = np.minimum(c, bb) * n + np.maximum(c, bb)
            ix1, ix2 = np.searchsorted(u_codes, code1), np.searchsorted(u_codes, code2)
            valid = (ix1 < len(u_codes)) & (ix2 < len(u_codes))
            ii = np.flatnonzero(valid)
            if not len(ii):
                continue
            ii = ii[(u_codes[ix1[ii]] == code1[ii]) & (u_codes[ix2[ii]] == code2[ii])]
            for j in ii:
                endpoints = (aa, bb, int(c[j]), int(d[j]))
                rows = (int(first), int(second[j]), int(u_rows[u_order[ix1[j]]]), int(u_rows[u_order[ix2[j]]]))
                key = hashlib.sha256(f"{salt}:{':'.join(map(str, endpoints))}".encode()).digest()
                candidates.append((key, endpoints, rows))
    candidates.sort()
    edge_uses, endpoint_uses = Counter(), Counter()
    selected_endpoints, selected_rows = [], []
    for _, endpoints, rows in candidates:
        if len(selected_rows) >= maximum:
            break
        if any(edge_uses[e] >= edge_cap for e in rows[:2]) or any(endpoint_uses[e] >= endpoint_cap for e in endpoints):
            continue
        selected_rows.append(rows)
        selected_endpoints.append(endpoints)
        edge_uses.update(rows[:2])
        endpoint_uses.update(endpoints)
    return (np.asarray(selected_rows, dtype=np.int64).reshape(-1, 4),
            np.asarray(selected_endpoints, dtype=np.int64).reshape(-1, 4), len(candidates))


def quartet_credit(scores, rows, tolerance=1e-6):
    delta = scores[rows[:, 0]] + scores[rows[:, 1]] - scores[rows[:, 2]] - scores[rows[:, 3]]
    return (delta > tolerance).astype(np.float64) + .5 * (np.abs(delta) <= tolerance), delta


def quartet_bootstrap_totals(credit, endpoints, component, multipliers):
    total, mass = np.zeros(len(multipliers)), np.zeros(len(multipliers))
    for value, endpoint_row in zip(credit, endpoints, strict=True):
        unique = np.unique(component[endpoint_row])
        weight = np.prod(multipliers[:, unique].astype(np.float64), axis=1)
        total += weight * value
        mass += weight
    return total, mass


def interval(values):
    values = np.asarray(values, dtype=np.float64)
    valid = np.isfinite(values)
    if valid.mean() < .95:
        raise RuntimeError("fewer than 95% valid component replicates")
    return np.percentile(values[valid], [2.5, 97.5]).tolist()
