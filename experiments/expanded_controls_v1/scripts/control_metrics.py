"""Original macro bootstrap with its constituent-cohort draws retained."""
import numpy as np
import torch
from benchmark_metrics import component_counts
from common import concordance


def cohort_bootstrap(scores, positive, weights, cohort, component_a, component_b,
                     cell, replicates=2000, device="cuda", batch=8):
    a, b, counts, metadata = component_counts(component_a, component_b, cell, replicates)
    counts = torch.as_tensor(counts, device=device, dtype=torch.float64)
    points = np.empty((scores.shape[1], 2))
    draws = np.full((scores.shape[1], 2, replicates), np.nan)
    for j in range(scores.shape[1]):
        for c in (0, 1):
            pmask, umask = positive & (cohort == c), (~positive) & (cohort == c)
            use = cohort == c
            points[j, c] = concordance(scores[use, j], positive[use], weights[use])
            p, u = scores[pmask, j], scores[umask, j]
            order = np.argsort(u, kind="stable")
            left = torch.as_tensor(np.searchsorted(u[order], p, "left"), device=device)
            right = torch.as_tensor(np.searchsorted(u[order], p, "right"), device=device)
            pa, pb = torch.as_tensor(a[pmask], device=device), torch.as_tensor(b[pmask], device=device)
            ua, ub = torch.as_tensor(a[umask][order], device=device), torch.as_tensor(b[umask][order], device=device)
            w = torch.as_tensor(weights[umask][order], device=device)
            for start in range(0, replicates, batch):
                count = counts[start:start+batch]
                pw = torch.where(pa == pb, count[:, pa], count[:, pa]*count[:, pb])
                uw = torch.where(ua == ub, count[:, ua], count[:, ua]*count[:, ub])*w
                prefix = torch.cat([torch.zeros(len(count), 1, device=device, dtype=torch.float64),
                                    torch.cumsum(uw, 1)], 1)
                den = pw.sum(1)*prefix[:, -1]
                result = (pw*(prefix[:, left]+prefix[:, right])*.5).sum(1)/den
                result[den <= 0] = float("nan")
                draws[j, c, start:start+len(count)] = result.cpu().numpy()
    return points, draws, metadata
