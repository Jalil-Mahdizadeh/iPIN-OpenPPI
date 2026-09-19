"""Native released 650M model, with no fitting or altered learned parameters."""
from pathlib import Path
import hashlib
import torch
from torch import nn
from torch.nn import functional as F
from transformers import AutoConfig, AutoModelForMaskedLM, AutoTokenizer
from common import ORIGINAL_SHA, sha

ASSETS = Path('/opt/plm_interact/assets')

class NativePLM(nn.Module):
    def __init__(self):
        super().__init__()
        config = AutoConfig.from_pretrained(ASSETS/'esm2_650m', local_files_only=True)
        self.esm_mask = AutoModelForMaskedLM.from_config(config)
        self.classifier = nn.Linear(1280, 1)

    def forward_test(self, features):
        hidden = self.esm_mask.base_model(**features, return_dict=True).last_hidden_state[:, 0, :]
        return torch.sigmoid(self.classifier(F.relu(hidden)).view(-1))

def load_model(device):
    path = ASSETS/'humanV11/pytorch_model.bin'
    if sha(path) != ORIGINAL_SHA: raise RuntimeError('Released checkpoint bytes changed')
    state = torch.load(path, map_location='cpu', weights_only=True, mmap=True)
    model = NativePLM()
    model.load_state_dict(state, strict=True)
    for key, value in model.state_dict().items():
        if not torch.equal(value, state[key]): raise RuntimeError(f'Checkpoint tensor changed: {key}')
    del state
    return model.to(device).eval().requires_grad_(False)

def tokenizer():
    return AutoTokenizer.from_pretrained(ASSETS/'esm2_650m', local_files_only=True)

def learned_digest(model):
    result = hashlib.sha256()
    for name, tensor in sorted(model.named_parameters()):
        value = tensor.detach().cpu().contiguous()
        result.update(name.encode()); result.update(str(tuple(value.shape)).encode())
        result.update(str(value.dtype).encode()); result.update(value.numpy().tobytes())
    return result.hexdigest()
