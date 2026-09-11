"""Pure homology, source visibility and transfer primitives."""

import numpy as np


def alignment_values(fields, lengths):
    """Recompute exact identity from integer spans, columns and mismatches."""
    if len(fields) != 12:
        raise ValueError("alignment must have twelve fields")
    a, b, mismatch, columns, qs, qe, qlen, ts, te, tlen = map(int, fields[:10])
    evalue, bits = map(float, fields[10:])
    if not (0 <= a < len(lengths) and 0 <= b < len(lengths)):
        raise ValueError("alignment endpoint outside public universe")
    if qlen != lengths[a] or tlen != lengths[b] or not (1 <= qs <= qe <= qlen and 1 <= ts <= te <= tlen):
        raise ValueError("alignment length or coordinate mismatch")
    qspan, tspan = qe - qs + 1, te - ts + 1
    identical = qspan + tspan - columns - mismatch
    if not (0 <= mismatch and 0 <= identical <= min(qspan, tspan) <= columns):
        raise ValueError("invalid identity counts")
    if not np.isfinite([evalue, bits]).all() or evalue < 0:
        raise ValueError("invalid alignment significance")
    return a, b, identical, columns, qspan, tspan, qlen, tlen, evalue


def alignment_scores(values):
    a, b, identical, columns, qs, ts, qlen, tlen, evalue = values
    if columns <= 0 or 5 * identical < columns or min(qs, ts) < 40 or evalue > .001:
        return a, b, 0., 0., False
    identity = identical / columns
    local = identity * min(1., min(qs, ts) / 80)
    coverage = identity * np.sqrt((qs / qlen) * (ts / tlen))
    purge = min(qs, ts) >= 80 and 5 * qs >= qlen and 5 * ts >= tlen
    return a, b, local, coverage, purge


def purged_fit_mask(folds, components, fold, edges_a, edges_b):
    heldout = folds == fold
    neighbors = np.r_[edges_b[heldout[edges_a]], edges_a[heldout[edges_b]]]
    banned = np.unique(components[neighbors])
    fit = ~heldout & ~np.isin(components, banned)
    if np.any((heldout[edges_a] & fit[edges_b]) | (heldout[edges_b] & fit[edges_a])):
        raise RuntimeError("purge retained a detected cross-edge")
    return fit


def fit_rows(data, source, fit_endpoints, visible_bit=0):
    """Hide target-only public P as unit-weight U, never use target exclusion."""
    if len(source) != len(data['p_a']) or not np.isin(source, [1, 2, 3]).all():
        raise ValueError("unknown or missing source membership")
    if visible_bit not in (0, 1, 2):
        raise ValueError("unknown visible source")
    p_eligible = fit_endpoints[data['p_a']] & fit_endpoints[data['p_b']]
    visible = np.ones(len(source), dtype=bool) if visible_bit == 0 else (source & visible_bit) != 0
    u_eligible = fit_endpoints[data['u_a']] & fit_endpoints[data['u_b']]
    p_rows = np.flatnonzero(p_eligible & visible)
    hidden = np.flatnonzero(p_eligible & ~visible)
    u_rows = np.flatnonzero(u_eligible)
    a = np.r_[data['u_a'][u_rows], data['p_a'][hidden]]
    b = np.r_[data['u_b'][u_rows], data['p_b'][hidden]]
    order = np.argsort(np.minimum(a, b) * len(fit_endpoints) + np.maximum(a, b))
    return dict(p_rows=p_rows, u_a=a[order], u_b=b[order],
                u_num=np.r_[data['u_num'][u_rows], np.ones(len(hidden), dtype=np.int64)][order],
                u_den=np.r_[data['u_den'][u_rows], np.ones(len(hidden), dtype=np.int64)][order],
                hidden_p_rows=hidden, fit_endpoints=fit_endpoints)


def panel_mask(ev, source, target_bit=0):
    mask = np.ones(len(ev['a']), dtype=bool)
    if target_bit:
        mask[ev['positive']] = source[ev['parent_row'][ev['positive']]] == target_bit
    return mask


def exhaustive_transfer_numpy(similarity, a, b, p_a, p_b):
    """Slow reference-friendly full-edge control; no neighbor truncation."""
    if not len(p_a):
        raise ValueError("empty fitting interaction graph")
    return np.array([np.maximum(np.minimum(similarity[x, p_a], similarity[y, p_b]),
                               np.minimum(similarity[x, p_b], similarity[y, p_a])).max()
                     for x, y in zip(a, b, strict=True)])


def finite_ratio(numerator, denominator):
    return np.divide(numerator, denominator, out=np.full_like(numerator, np.nan, dtype=np.float64),
                     where=denominator > 0)


def summary_interval(values):
    values = np.asarray(values)
    valid = np.isfinite(values)
    return {'valid_replicates': int(valid.sum()),
            'ci95': np.percentile(values[valid], [2.5, 97.5]).tolist() if valid.mean() >= .95 else None}
