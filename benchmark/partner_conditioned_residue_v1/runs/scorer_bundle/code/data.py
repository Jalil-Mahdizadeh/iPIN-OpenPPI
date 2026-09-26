"""Identity-checked frozen residue inputs and partition-preserving batching."""
from pathlib import Path
import h5py
import numpy as np
import torch
from common import read, sha


def validate_training(train, meta):
    partition = np.asarray(meta['partition'])
    if len(train['p_a']) != 16799 or len(train['u_a']) != 2000000:
        raise RuntimeError('TRAIN census mismatch')
    for key in ('p_a', 'p_b', 'u_a', 'u_b'):
        indices = np.asarray(train[key])
        if indices.ndim != 1 or not np.issubdtype(indices.dtype, np.integer):
            raise RuntimeError('Invalid TRAIN index dtype/shape')
        if (indices < 0).any() or (indices >= len(partition)).any():
            raise RuntimeError('TRAIN index outside endpoint universe')
        if np.any(partition[indices] != 'train'):
            raise RuntimeError('Non-TRAIN endpoint used for fitting')
    if np.any(train['p_a'] == train['p_b']) or np.any(train['u_a'] == train['u_b']):
        raise RuntimeError('Unexpected TRAIN self pair')
    w = train['u_weight']
    if not np.isfinite(w).all() or (w <= 0).any():
        raise RuntimeError('Invalid TRAIN design weight')


def train_standardization(means, partitions):
    selected = means[np.asarray(partitions) == 'train'].astype(np.float64)
    center = selected.mean(0)
    scale = np.maximum(selected.std(0), 1e-6)
    return center, scale


class ResidueCache:
    def __init__(self, data=Path('/output/data'), device='cuda', load_residues=True):
        self.meta = read(Path(data) / 'sequences.json')
        self.device = torch.device(device)
        lengths = np.asarray(self.meta['length'], np.int64)
        self.lengths = torch.as_tensor(lengths, device=device)
        self.offsets = torch.as_tensor(np.concatenate(([0], lengths.cumsum())), device=device)
        self.global_features = torch.as_tensor(np.load(Path(data) / 'global_standardized.npy', allow_pickle=False), device=device)
        self.values = None
        if load_residues:
            self.values = torch.empty((int(lengths.sum()), 640), dtype=torch.float32, device=device)
            with h5py.File('/cache/residues.h5', 'r') as handle:
                if not handle.attrs.get('complete') or handle.attrs['sequence_manifest_sha256'] != sha(Path(data) / 'sequences.json'):
                    raise RuntimeError('Residue-cache identity/completion mismatch')
                if len(handle) != len(lengths):
                    raise RuntimeError('Residue-cache endpoint census mismatch')
                offset = 0
                for i, length in enumerate(lengths):
                    value = handle[str(i)][:]
                    if value.shape != (length, 640) or value.dtype != np.float32 or not np.isfinite(value).all():
                        raise RuntimeError('Invalid residue matrix')
                    self.values[offset:offset + length] = torch.from_numpy(value).to(device)
                    offset += length

    def pack(self, indices, sample=None):
        ids = torch.as_tensor(indices, device=self.device, dtype=torch.long)
        lengths = self.lengths[ids]
        width = int(lengths.max()) if sample is None else min(sample, int(lengths.max()))
        local = torch.arange(width, device=self.device)[None, :]
        valid = local < lengths[:, None]
        if sample is None:
            positions = local.expand(len(ids), -1)
        else:
            # One random position per nonoverlapping length/W interval. For
            # lengths > W this covers the whole sequence without duplicates.
            random_positions = ((local + torch.rand(len(ids), width, device=self.device))
                                * lengths[:, None] / width).long()
            positions = torch.where(lengths[:, None] > width, random_positions, local)
        positions = torch.minimum(positions, lengths[:, None] - 1)
        values = self.values[self.offsets[ids, None] + positions]
        return values * valid[:, :, None], valid

    def endpoint_tokens(self, model, indices, maximum_padded_residues=32768):
        if model.training:
            raise RuntimeError('Feature caching requires evaluation mode')
        shape = (len(self.meta['length']), model.recipe['tokens'], model.recipe['dimension']) if model.has_local else (len(self.meta['length']), 1, 1)
        result = torch.full(shape, float('nan'), dtype=torch.float32, device=self.device)
        if not model.has_local:
            result[indices] = 0
            return result
        ordered = sorted(map(int, indices), key=lambda i: self.meta['length'][i])
        start = 0
        with torch.inference_mode():
            while start < len(ordered):
                stop = start + 1
                while stop < len(ordered) and stop - start < 64:
                    if (stop + 1 - start) * self.meta['length'][ordered[stop]] > maximum_padded_residues:
                        break
                    stop += 1
                ids = ordered[start:stop]
                residues, valid = self.pack(ids)
                result[ids] = model.encode(residues, valid)
                start = stop
        if not bool(torch.isfinite(result[indices]).all()):
            raise RuntimeError('Incomplete endpoint token features')
        return result


def score_cached(model, globals_, tokens, a, b, batch=1024):
    if model.training:
        raise RuntimeError('Cached scoring requires evaluation mode')
    result = np.empty(len(a), np.float32)
    device = globals_.device
    with torch.inference_mode():
        for start in range(0, len(a), batch):
            stop = min(start + batch, len(a))
            ia = torch.as_tensor(a[start:stop], device=device, dtype=torch.long)
            ib = torch.as_tensor(b[start:stop], device=device, dtype=torch.long)
            scores = model.score(globals_[ia], globals_[ib], tokens[ia], tokens[ib])
            result[start:stop] = scores.cpu().numpy()
    if not np.isfinite(result).all():
        raise RuntimeError('Nonfinite scores')
    return result
