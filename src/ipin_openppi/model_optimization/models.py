"""Small symmetric heads for existing, training-standardized frozen PLM vectors."""
from __future__ import annotations

import math
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


def features(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    denominator = torch.linalg.vector_norm(a, dim=-1) * torch.linalg.vector_norm(b, dim=-1)
    # Nonzero finite endpoint vectors are checked before fitting, avoiding a
    # device synchronization for every pair batch. No epsilon approximation.
    cosine = ((a * b).sum(-1) / denominator).unsqueeze(-1)
    return torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)


class PairHead(nn.Module):
    def __init__(self, dimension: int, spec: dict):
        super().__init__()
        self.family = spec["family"]
        width = spec["width"]
        n = 3 * dimension + 1
        if self.family in ("linear", "residual_mlp", "bilinear"):
            self.output = nn.Linear(n, 1)
        if self.family in ("mlp", "residual_mlp"):
            self.network = nn.Sequential(nn.LayerNorm(n), nn.Linear(n, width),
                                         nn.GELU(), nn.Dropout(spec["dropout"]), nn.Linear(width, 1))
        if self.family == "bilinear":
            self.projection = nn.Linear(dimension, width, bias=False)
            self.interaction = nn.Linear(width, 1, bias=False)
            self.rank_scale = math.sqrt(width)
        if self.family not in ("linear", "mlp", "residual_mlp", "bilinear"):
            raise ValueError("Unknown prospective family")

    def forward(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        pair = features(a, b)
        if self.family == "mlp":
            return self.network(pair).squeeze(-1)
        result = self.output(pair).squeeze(-1)
        if self.family == "residual_mlp":
            result = result + self.network(pair).squeeze(-1)
        elif self.family == "bilinear":
            product = self.projection(a) * self.projection(b)
            result = result + self.interaction(product).squeeze(-1) / self.rank_scale
        return result


def build(dimension: int, spec: dict, seed: int) -> PairHead:
    torch.manual_seed(seed)
    model = PairHead(dimension, spec)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    with torch.no_grad():
        for module in model.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight, generator=generator)
                if module.bias is not None:
                    module.bias.zero_()
    return model


def save_state(path, model: nn.Module) -> None:
    # Safe, portable state only; no pickle or optimizer objects in scorer bundle.
    with path.open("xb") as handle:
        np.savez(handle, **{k: v.detach().cpu().numpy() for k, v in model.state_dict().items()})


def load_state(path, model: nn.Module) -> None:
    with np.load(path, allow_pickle=False) as values:
        model.load_state_dict({k: torch.from_numpy(values[k].copy()) for k in values.files}, strict=True)
