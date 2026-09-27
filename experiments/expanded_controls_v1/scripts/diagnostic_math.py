"""Paired anchor/bootstrap estimands with an independent CPU reference."""
import numpy as np
import torch
from ipin_openppi.partner_specificity.semantics import (
    anchor_points, build_queries, quartet_credit, quartet_bootstrap_totals,
)


def anchor_bootstrap(scores, data, component, multipliers, device="cuda", batch=256):
    queries = build_queries(data["a"], data["b"], data["positive"])
    m, r = scores.shape[1], len(multipliers)
    if not queries:
        return np.full(m, np.nan), np.full((m, r), np.nan), {
            "anchors": 0, "anchor_components": 0}
    point = np.array([anchor_points(scores[:, j], queries, data["weight"]).mean() for j in range(m)])
    counts = torch.as_tensor(multipliers, dtype=torch.float64, device=device)
    total = torch.zeros((r, m), dtype=torch.float64, device=device)
    mass = torch.zeros_like(total)
    for q in queries:
        comp = int(component[q.anchor])
        p = scores[q.positive].T
        u = scores[q.unlabeled].T
        order = np.argsort(u, axis=1, kind="stable")
        ordered = np.take_along_axis(u, order, 1)
        left = torch.as_tensor(np.stack([np.searchsorted(ordered[j], p[j], "left") for j in range(m)]),
                               device=device)
        right = torch.as_tensor(np.stack([np.searchsorted(ordered[j], p[j], "right") for j in range(m)]),
                                device=device)
        pc = torch.as_tensor(component[q.positive_partner], device=device)
        uc = torch.as_tensor(component[q.unlabeled_partner][order], device=device)
        weight = torch.as_tensor(data["weight"][q.unlabeled][order], device=device)
        for start in range(0, r, batch):
            count = counts[start:start+batch]
            pw = torch.where(pc == comp, 1., count[:, pc])
            uw = torch.where(uc[None] == comp, 1., count[:, uc]) * weight
            prefix = torch.cat([torch.zeros((len(count), m, 1), device=device, dtype=torch.float64),
                                torch.cumsum(uw, -1)], -1)
            credit = .5 * (torch.gather(prefix, -1, left.expand(len(count), -1, -1)) +
                           torch.gather(prefix, -1, right.expand(len(count), -1, -1)))
            den = pw.sum(-1)[:, None] * prefix[:, :, -1]
            valid = den > 0
            numerator = (credit * pw[:, None]).sum(-1)
            anchor_weight = count[:, comp, None] * valid
            total[start:start+len(count)] += torch.where(valid, numerator / den, 0.) * anchor_weight
            mass[start:start+len(count)] += anchor_weight
    draws = torch.where(mass > 0, total / mass, torch.nan).T.cpu().numpy()
    return point, draws, {"anchors": len(queries),
                         "anchor_components": len(np.unique(component[[q.anchor for q in queries]]))}


def quartet_estimates(scores, rows, endpoints, component, multipliers, tolerance=1e-6):
    m, r = scores.shape[1], len(multipliers)
    if not len(rows):
        return np.full(m, np.nan), np.full((m, r), np.nan), np.empty((0, m))
    credits = np.column_stack([quartet_credit(scores[:, j], rows, tolerance)[0] for j in range(m)])
    weights = np.ones((r, len(rows)), np.float64)
    for j, endpoint in enumerate(endpoints):
        weights[:, j] = np.prod(multipliers[:, np.unique(component[endpoint])].astype(np.float64), axis=1)
    denominator = weights.sum(1)
    numerator = weights @ credits
    draws = np.divide(numerator, denominator[:, None],
                      out=np.full_like(numerator, np.nan), where=denominator[:, None] > 0)
    return credits.mean(0), draws.T, credits
