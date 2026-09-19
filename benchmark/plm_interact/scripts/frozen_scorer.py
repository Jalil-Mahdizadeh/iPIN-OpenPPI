"""Native probabilities in a fixed canonical sequence-hash pair order."""
from pathlib import Path
import numpy as np
import torch
from transformers import logging
from common import read
from native_model import load_model, tokenizer

SCORERS = ('plm_interact_original_650m_humanv11',)
REFERENCES = ('ipin_baseline', 'ipin_optimized')
ALL_SCORERS = SCORERS + REFERENCES

class Scorer:
    def __init__(self, root, device, config=None):
        root = Path(root)
        self.config = config or read(root/'SCORER_FREEZE.json')
        self.sequences = read(root/'sequences.json')
        self.ids = np.asarray(read(root/'endpoints.json'))
        self.lengths = np.asarray([len(x) for x in self.sequences])
        assert len(self.sequences) == len(self.ids) and self.config['maximum_tokens'] == 1603
        self.batch = self.config['batch_size']
        self.device = device
        self.model = load_model(device)
        self.tokenizer = tokenizer()
        # Native longest-first truncation is explicitly counted in every shard.
        # Avoid millions of repeated tokenizer overflow-information warnings.
        logging.get_logger('transformers.tokenization_utils_base').setLevel(logging.ERROR)

    def scores(self, a, b):
        a = np.asarray(a, np.int64); b = np.asarray(b, np.int64)
        assert a.shape == b.shape and a.ndim == 1
        reverse = self.ids[a] > self.ids[b]
        left = np.where(reverse, b, a); right = np.where(reverse, a, b)
        lengths = np.minimum(self.lengths[left] + self.lengths[right] + 3, 1603)
        order = np.argsort(lengths, kind='stable')
        result = np.empty(len(a), np.float64)
        with torch.inference_mode():
            for start in range(0, len(order), self.batch):
                selected = order[start:start+self.batch]
                features = self.tokenizer([self.sequences[int(i)] for i in left[selected]],
                                          [self.sequences[int(i)] for i in right[selected]],
                                          padding=True, truncation='longest_first', max_length=1603,
                                          return_tensors='pt').to(self.device)
                value = self.model.forward_test(features)
                if not torch.isfinite(value).all(): raise RuntimeError('Nonfinite native probability')
                result[selected] = value.cpu().numpy()
        if not np.isfinite(result).all() or (result < 0).any() or (result > 1).any():
            raise RuntimeError('Invalid original-model score')
        return result[:, None]
