"""Matched additive endpoint controls; the historical pair head is unchanged."""

import torch
from torch import nn

from ipin_openppi.stage1.models import LinearPairHead


class EndpointHead(nn.Module):
    def __init__(self, dimension=640, hidden=None):
        super().__init__()
        self.unary = nn.Linear(dimension, 1) if hidden is None else nn.Sequential(
            nn.Linear(dimension, hidden), nn.GELU(), nn.Linear(hidden, 1))

    def forward(self, a, b):
        return (self.unary(a) + self.unary(b)).squeeze(-1)


def make_model(name, seed, dimension=640):
    torch.manual_seed(seed)
    if name == "endpoint_linear":
        return EndpointHead(dimension)
    if name == "endpoint_mlp64":
        return EndpointHead(dimension, 64)
    if name == "pair_linear":
        return LinearPairHead(dimension)
    raise ValueError(f"unregistered model: {name}")
