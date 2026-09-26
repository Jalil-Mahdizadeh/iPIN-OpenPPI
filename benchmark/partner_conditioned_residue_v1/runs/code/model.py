"""Symmetric global and partner-conditioned latent-residue ranking heads.

ESM inputs are fixed. Latent tokens are learned summaries, not contact labels.
The cross blocks attend between the two proteins with shared weights.
"""
import torch
from torch import nn
from torch.nn import functional as F


def pair_features(a, b):
    cosine = F.cosine_similarity(a, b, dim=-1, eps=1e-8).unsqueeze(-1)
    return torch.cat((a + b, (a - b).abs(), a * b, cosine), dim=-1)


class ResidualHead(nn.Module):
    def __init__(self, dimension=640):
        super().__init__()
        width = 3 * dimension + 1
        self.linear = nn.Linear(width, 1)
        self.network = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, 256),
                                     nn.GELU(), nn.Dropout(.3), nn.Linear(256, 1))

    def forward(self, a, b):
        x = pair_features(a, b)
        return (self.linear(x) + self.network(x)).squeeze(-1)


class CrossBlock(nn.Module):
    def __init__(self, dimension):
        super().__init__()
        self.attention = nn.MultiheadAttention(dimension, 4, dropout=.1, batch_first=True)
        self.norm1 = nn.LayerNorm(dimension)
        self.norm2 = nn.LayerNorm(dimension)
        self.feedforward = nn.Sequential(nn.Linear(dimension, 4 * dimension), nn.GELU(),
                                         nn.Dropout(.2), nn.Linear(4 * dimension, dimension))
        self.dropout = nn.Dropout(.2)

    def one_direction(self, query, partner):
        message = self.attention(query, partner, partner, need_weights=False)[0]
        x = self.norm1(query + self.dropout(message))
        return self.norm2(x + self.dropout(self.feedforward(x)))

    def forward(self, a, b):
        # Both directions use the original inputs, not an already updated side.
        return self.one_direction(a, b), self.one_direction(b, a)


class PairModel(nn.Module):
    def __init__(self, recipe):
        super().__init__()
        self.recipe = dict(recipe)
        self.global_head = ResidualHead()
        self.has_local = recipe['local_branch']
        if self.has_local:
            d = recipe['dimension']
            self.residue_projection = nn.Sequential(nn.LayerNorm(640), nn.Linear(640, d), nn.GELU())
            self.queries = nn.Parameter(torch.randn(recipe['tokens'], d) * .02)
            self.pool = nn.MultiheadAttention(d, 4, dropout=.1, batch_first=True)
            self.pool_norm = nn.LayerNorm(d)
            self.token_ff = nn.Sequential(nn.Linear(d, 2 * d), nn.GELU(), nn.Linear(2 * d, d))
            self.token_norm = nn.LayerNorm(d)
            self.cross_blocks = nn.ModuleList(CrossBlock(d) for _ in range(recipe['cross_layers']))
            self.local_head = nn.Sequential(nn.LayerNorm(3 * d + 1), nn.Linear(3 * d + 1, 256),
                                            nn.GELU(), nn.Dropout(.2), nn.Linear(256, 1))
            nn.init.zeros_(self.local_head[-1].weight)
            nn.init.zeros_(self.local_head[-1].bias)

    def encode(self, residues, valid):
        if not self.has_local:
            return residues.new_zeros((len(residues), 1, 1))
        x = self.residue_projection(residues)
        q = self.queries.unsqueeze(0).expand(len(x), -1, -1)
        z = self.pool(q, x, x, key_padding_mask=~valid, need_weights=False)[0]
        z = self.pool_norm(q + z)
        return self.token_norm(z + self.token_ff(z))

    def condition(self, a, b):
        for block in self.cross_blocks:
            a, b = block(a, b)
        return a, b

    def score(self, global_a, global_b, tokens_a=None, tokens_b=None):
        result = self.global_head(global_a, global_b)
        if self.has_local:
            a, b = self.condition(tokens_a, tokens_b)
            result = result + self.local_head(pair_features(a.mean(1), b.mean(1))).squeeze(-1)
        return result
