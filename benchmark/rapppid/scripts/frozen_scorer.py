"""Immutable native-single-pair RAPPPID scoring from qualified endpoint cache."""
from pathlib import Path
import numpy as np
import torch
from common import read
from native_model import load_model, independent_head

SCORERS = ('rapppid_original_released_mult',)
REFERENCES = ('ipin_baseline', 'ipin_optimized')
ALL_SCORERS = SCORERS + REFERENCES


class Scorer:
    def __init__(self, root, device, config=None):
        root = Path(root)
        self.config = config or read(root / 'SCORER_FREEZE.json')
        self.device = device
        self.model = load_model(device)
        self.batch = self.config.get('pair_batch_size', 8192)
        self.lengths = np.asarray(read(root / 'lengths.json'), dtype=np.int64)
        values = np.load(root / 'embeddings.npy', allow_pickle=False)
        assert values.shape == (len(self.lengths), 64) and values.dtype == np.float32 and np.isfinite(values).all()
        self.embeddings = torch.as_tensor(values, device=device)

    @torch.inference_mode()
    def scores(self, a, b):
        a = np.asarray(a, dtype=np.int64); b = np.asarray(b, dtype=np.int64)
        assert a.shape == b.shape and a.ndim == 1
        assert ((a >= 0) & (a < len(self.lengths))).all() and ((b >= 0) & (b < len(self.lengths))).all()
        result = np.empty((len(a), 1), np.float64)
        for start in range(0, len(a), self.batch):
            ia = torch.as_tensor(a[start:start+self.batch], device=self.device)
            ib = torch.as_tensor(b[start:start+self.batch], device=self.device)
            scores = independent_head(self.model, self.embeddings[ia], self.embeddings[ib])
            result[start:start+len(scores), 0] = scores.cpu().numpy()
        assert np.isfinite(result).all() and ((result >= 0) & (result <= 1)).all()
        return result
