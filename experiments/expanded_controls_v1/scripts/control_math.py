"""Pure control definitions and exact accelerated full-edge transfer."""
from collections import Counter
import numpy as np
from scipy import sparse

from ipin_openppi.stage1.baselines import KMER_ALPHABET, map_kmer_residue


def graph(n, a, b, component):
    a, b = np.asarray(a), np.asarray(b)
    if len(a) != len(b) or np.any(a == b) or len(np.unique(np.minimum(a, b)*n+np.maximum(a, b))) != len(a):
        raise ValueError("training graph requires unique undirected nonself edges")
    adjacency = sparse.csr_matrix(
        (np.ones(2*len(a), dtype=np.int64), (np.r_[a, b], np.r_[b, a])), shape=(n, n))
    degree = np.asarray(adjacency.sum(1)).ravel()
    groups, inv = np.unique(component, return_inverse=True)
    masses = np.bincount(inv, weights=degree).astype(np.int64)[inv]
    return adjacency, degree, masses


def composition(sequences):
    index = {x: i for i, x in enumerate(KMER_ALPHABET)}
    counts = np.zeros((len(sequences), len(index)), np.float64)
    for i, seq in enumerate(sequences):
        for aa, count in Counter(map(map_kmer_residue, seq)).items():
            counts[i, index[aa]] = count
    return unit(counts)


def unit(matrix):
    x = np.asarray(matrix, dtype=np.float64)
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    if not np.isfinite(x).all() or np.any(norm <= 0):
        raise ValueError("finite nonzero endpoint vectors required")
    return x / norm


def neighbor_max_numpy(sim, edge_a, edge_b):
    """N[x,u]=max over all training neighbors v of K[x,v]."""
    sim = np.asarray(sim)
    output = np.full_like(sim, -np.inf)
    for a, b in zip(edge_a, edge_b, strict=True):
        output[:, a] = np.maximum(output[:, a], sim[:, b])
        output[:, b] = np.maximum(output[:, b], sim[:, a])
    return output


def transfer_numpy(sim, neighbor, a, b):
    return np.minimum(sim[a], neighbor[b]).max(1)


def neighbor_max_cuda(sim, edge_a, edge_b, batch=256):
    import torch
    index = torch.as_tensor(np.r_[edge_a, edge_b], device=sim.device)
    source = torch.as_tensor(np.r_[edge_b, edge_a], device=sim.device)
    output = torch.empty_like(sim)
    for start in range(0, len(sim), batch):
        stop = min(start + batch, len(sim))
        block = torch.full((stop-start, sim.shape[1]), -torch.inf, dtype=sim.dtype, device=sim.device)
        block.scatter_reduce_(1, index.expand(stop-start, -1), sim[start:stop, source],
                              reduce="amax", include_self=True)
        output[start:stop] = block
    return output


def transfer_cuda(sim, neighbor, a, b, batch=256):
    import torch
    output = np.empty(len(a), np.float64)
    for start in range(0, len(a), batch):
        stop = min(start + batch, len(a))
        aa = torch.as_tensor(a[start:stop], device=sim.device)
        bb = torch.as_tensor(b[start:stop], device=sim.device)
        output[start:stop] = torch.minimum(sim[aa], neighbor[bb]).amax(1).cpu().numpy()
    return output
