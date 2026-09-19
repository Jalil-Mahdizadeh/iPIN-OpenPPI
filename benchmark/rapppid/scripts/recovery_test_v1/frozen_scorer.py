"""Exactly the three selected recovery states, with unchanged singleton logits."""
from pathlib import Path
import numpy as np
import torch
from common import SEEDS, read, sha
from model import fresh, learned_digest, scores

SCORERS = ('rapppid_recovery_mean_logit',) + tuple(f'rapppid_recovery_seed_{s}' for s in SEEDS)
REFERENCES = ('rapppid_original_released_mult', 'ipin_baseline', 'ipin_optimized')
ALL_SCORERS = SCORERS + REFERENCES


class Scorer:
    def __init__(self, root, device, config=None):
        root = Path(root)
        self.config = config or read(root / 'SCORER_FREEZE.json')
        self.lengths = np.asarray(read(root / 'lengths.json'), dtype=np.int64)
        self.models, self.embeddings = [], []
        self.batch = 8192
        assert len(self.lengths) == 17000
        for member in self.config['members']:
            seed = member['seed']
            path = root / 'checkpoints' / f'seed_{seed}.pt'
            assert sha(path) == member['checkpoint_sha256']
            state = torch.load(path, map_location='cpu', weights_only=True)
            assert state['seed'] == seed and state['protocol_sha256'] == self.config['training_protocol_sha256']
            model = fresh(seed, device).eval()
            model.load_state_dict(state['model'], strict=True)
            model.requires_grad_(False)
            assert learned_digest(model) == member['learned_state_sha256']
            values = np.load(root / f'embeddings_{seed}.npy', allow_pickle=False)
            assert values.shape == (17000, 64) and values.dtype == np.float32 and np.isfinite(values).all()
            self.models.append(model)
            self.embeddings.append(torch.as_tensor(values, device=device))
        assert [m['seed'] for m in self.config['members']] == list(SEEDS)

    def verify_state(self):
        for model, member in zip(self.models, self.config['members'], strict=True):
            assert learned_digest(model) == member['learned_state_sha256']

    @torch.inference_mode()
    def scores(self, a, b):
        a = np.asarray(a, np.int64); b = np.asarray(b, np.int64)
        assert a.shape == b.shape and a.ndim == 1
        assert ((a >= 0) & (a < 17000)).all() and ((b >= 0) & (b < 17000)).all()
        members = np.column_stack([scores(m, e, a, b, batch=self.batch)
                                   for m, e in zip(self.models, self.embeddings, strict=True)])
        result = np.column_stack([members.mean(1, dtype=np.float64), members])
        assert result.shape == (len(a), 4) and np.isfinite(result).all()
        return result
