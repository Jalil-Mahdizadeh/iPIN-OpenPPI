"""Exactly swap-symmetric frozen Stage 1 pair heads."""

from __future__ import annotations

import math
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F

from .constants import FAMILIES, PARAMETER_CEILING


def exact_cosine(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    denominator = torch.linalg.vector_norm(a, dim=-1) * torch.linalg.vector_norm(b, dim=-1)
    if torch.any(denominator == 0):
        raise RuntimeError("zero vector makes exact cosine undefined")
    return (a * b).sum(dim=-1) / denominator


def commutative_features(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    cosine = exact_cosine(a, b).unsqueeze(-1)
    return torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)


class LinearPairHead(nn.Module):
    def __init__(self, embedding_dimension: int) -> None:
        super().__init__()
        self.output = nn.Linear(3 * embedding_dimension + 1, 1)

    def forward(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return self.output(commutative_features(a, b)).squeeze(-1)


class NonlinearPairHead(nn.Module):
    def __init__(self, embedding_dimension: int, *, dropout: float, partner_gate: bool) -> None:
        super().__init__()
        if embedding_dimension != 1280:
            raise RuntimeError("nonlinear Stage 1 heads require 1,280-dimensional ESM-2 embeddings")
        self.projection = nn.Linear(embedding_dimension, 256)
        self.gate = nn.Linear(256, 256) if partner_gate else None
        self.hidden = nn.Linear(769, 128)
        self.dropout = nn.Dropout(dropout)
        self.output = nn.Linear(128, 1)

    def forward(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        projected_a = F.gelu(self.projection(a), approximate="none")
        projected_b = F.gelu(self.projection(b), approximate="none")
        if self.gate is None:
            conditioned_a, conditioned_b = projected_a, projected_b
        else:
            conditioned_a = projected_a * torch.sigmoid(self.gate(projected_b))
            conditioned_b = projected_b * torch.sigmoid(self.gate(projected_a))
        pair = commutative_features(conditioned_a, conditioned_b)
        hidden = F.gelu(self.hidden(pair), approximate="none")
        return self.output(self.dropout(hidden)).squeeze(-1)


def initialize_exact(module: nn.Module, seed: int) -> None:
    generator = torch.Generator(device="cpu").manual_seed(seed)
    with torch.no_grad():
        for name, parameter in module.named_parameters():
            if name.endswith("weight"):
                nn.init.xavier_uniform_(parameter, generator=generator)
            elif name.endswith("bias"):
                parameter.zero_()
            else:
                raise RuntimeError(f"unrecognized parameter for initialization: {name}")


def build_model(family: str, *, dropout: float, seed: int) -> nn.Module:
    if family not in FAMILIES:
        raise RuntimeError(f"model family not frozen: {family}")
    dimension = 640 if FAMILIES[family]["candidate_id"] == "esm2_150m" else 1280
    if family.endswith("linear") or family == "esm2_650m_linear_ablation":
        model: nn.Module = LinearPairHead(dimension)
    elif family == "esm2_650m_nonlinear_no_gate_ablation":
        model = NonlinearPairHead(dimension, dropout=dropout, partner_gate=False)
    elif family == "esm2_650m_partner_gated_primary":
        model = NonlinearPairHead(dimension, dropout=dropout, partner_gate=True)
    else:
        raise RuntimeError(f"unhandled frozen model family: {family}")
    initialize_exact(model, seed)
    count = sum(parameter.numel() for parameter in model.parameters())
    if count >= PARAMETER_CEILING:
        raise RuntimeError(f"trainable parameter ceiling exceeded: {count}")
    return model


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def score_indexed_pairs(
    model: nn.Module,
    embeddings: torch.Tensor,
    endpoint_a: torch.Tensor,
    endpoint_b: torch.Tensor,
) -> torch.Tensor:
    return model(embeddings.index_select(0, endpoint_a), embeddings.index_select(0, endpoint_b))
