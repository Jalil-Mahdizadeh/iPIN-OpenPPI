"""Inference from frozen endpoint tokens and new PPI heads only."""
from pathlib import Path
import numpy as np
import torch
from common import read
from model import PairModel
from data import score_cached

REFERENCES = ('ipin_baseline', 'ipin_optimized', 'tuna_retrained_ensemble')
# Each isolated final-comparison process mounts one already-frozen bundle.
SCORERS = tuple(read('/bundle/SCORER_FREEZE.json')['scorers']) if Path('/bundle/SCORER_FREEZE.json').is_file() else ()
ALL_SCORERS = SCORERS + REFERENCES


class Scorer:
    def __init__(self, bundle, device='cuda', specification=None):
        self.root = Path(bundle)
        self.specification = specification or read(self.root / 'SCORER_FREEZE.json')
        self.names = self.specification['scorers']
        self.globals = torch.as_tensor(np.load(self.root / 'global_standardized.npy', allow_pickle=False), device=device)
        if self.globals.shape != (17000, 640) or not bool(torch.isfinite(self.globals).all()):
            raise RuntimeError('Invalid frozen global features')
        self.members = []
        for member in self.specification['members']:
            model = PairModel(member['recipe']).to(device)
            model.load_state_dict(torch.load(self.root / member['checkpoint'], map_location=device, weights_only=True), strict=True)
            model.eval()
            features = torch.as_tensor(np.load(self.root / member['features'], allow_pickle=False), device=device)
            shape = (17000, member['recipe']['tokens'], member['recipe']['dimension']) if model.has_local else (17000, 1, 1)
            if tuple(features.shape) != shape or not bool(torch.isfinite(features).all()):
                raise RuntimeError('Invalid frozen latent features')
            self.members.append((member, model, features))

    def scores(self, a, b):
        a, b = np.asarray(a, np.int64), np.asarray(b, np.int64)
        if a.shape != b.shape or a.ndim != 1 or (a < 0).any() or (b < 0).any() or (a >= 17000).any() or (b >= 17000).any():
            raise RuntimeError('Invalid inference endpoint indices')
        result = np.empty((len(a), len(self.names)), np.float64)
        for member, model, features in self.members:
            result[:, self.names.index(member['name'])] = score_cached(model, self.globals, features, a, b)
        for ensemble in self.specification['ensembles']:
            columns = [self.names.index(m['name']) for m in self.specification['members'] if m['ensemble'] == ensemble]
            if len(columns) != 3:
                raise RuntimeError('Every ensemble must retain all three seeds')
            result[:, self.names.index(ensemble)] = result[:, columns].mean(axis=1, dtype=np.float64)
        if not np.isfinite(result).all():
            raise RuntimeError('Nonfinite frozen model score')
        return result
