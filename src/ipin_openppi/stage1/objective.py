"""Exact public P-versus-U ordering and rational-weight objective helpers."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import torch
from torch.nn import functional as F

from .constants import (
    FINAL_LR_FRACTION,
    PASSES,
    POSITIVE_ROWS,
    TOTAL_STEPS,
    TRAINING_SALT,
    UNLABELED_ROWS,
    WARMUP_STEPS,
)
from .support import atomic_numpy, sha256_bytes, sha256_file


def order_key(*, seed: int, pass_index: int, state: str, pair_id: str) -> bytes:
    if seed not in (20260803, 20260817, 20260831):
        raise RuntimeError("seed not frozen")
    if pass_index not in range(1, PASSES + 1):
        raise RuntimeError("pass index outside 1..5")
    if state not in ("P", "U"):
        raise RuntimeError("state must be P or U")
    payload = f"sha256:{TRAINING_SALT}:{seed}:{pass_index}:{state}:{pair_id}"
    return hashlib.sha256(payload.encode("utf-8")).digest()


def deterministic_order(pair_ids: Sequence[str], *, seed: int, pass_index: int, state: str) -> np.ndarray:
    maximum = max(map(len, pair_ids))
    pair_bytes = np.asarray(pair_ids, dtype=f"S{maximum}")
    keys = np.empty(len(pair_ids), dtype="S32")
    for index, pair_id in enumerate(pair_ids):
        keys[index] = order_key(seed=seed, pass_index=pass_index, state=state, pair_id=pair_id)
    order = np.lexsort((pair_bytes, keys)).astype(np.int64, copy=False)
    if not np.array_equal(np.sort(order), np.arange(len(pair_ids), dtype=np.int64)):
        raise RuntimeError("deterministic order is not a permutation")
    return order


def ordered_pair_id_digest(pair_ids: Sequence[str], order: np.ndarray) -> str:
    digest = hashlib.sha256()
    for index in order:
        encoded = pair_ids[int(index)].encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def positive_positions_for_batch(start: int, stop: int, *, pass_index: int) -> np.ndarray:
    return (np.arange(start, stop, dtype=np.int64) + pass_index - 1) % POSITIVE_ROWS


def positive_repetition_counts(pass_index: int) -> np.ndarray:
    counts = np.bincount(
        positive_positions_for_batch(0, UNLABELED_ROWS, pass_index=pass_index),
        minlength=POSITIVE_ROWS,
    )
    if counts.min() != 119 or counts.max() != 120 or int((counts == 120).sum()) != 919:
        raise RuntimeError("positive repetition algebra drift")
    return counts


def rational_weights(numerators: np.ndarray, denominators: np.ndarray) -> np.ndarray:
    if numerators.dtype.kind not in "iu" or denominators.dtype.kind not in "iu":
        raise RuntimeError("design weights must retain integer numerator/denominator")
    if np.any(numerators <= 0) or np.any(denominators <= 0):
        raise RuntimeError("nonpositive rational design weight")
    return numerators.astype(np.float64) / denominators.astype(np.float64)


def weighted_pairwise_logistic_loss(
    score_positive: torch.Tensor,
    score_unlabeled: torch.Tensor,
    weights: torch.Tensor,
    mean_weight: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    if weights.dtype != torch.float64:
        raise RuntimeError("design weights must be evaluated in float64")
    per_comparison = F.softplus(-(score_positive - score_unlabeled))
    normalized = ((weights / mean_weight) * per_comparison.to(torch.float64)).mean()
    return normalized, per_comparison


def learning_rate_multiplier(step: int) -> float:
    if not 1 <= step <= TOTAL_STEPS:
        raise RuntimeError("scheduler step outside 1..2445")
    if step <= WARMUP_STEPS:
        return step / WARMUP_STEPS
    progress = (step - WARMUP_STEPS) / (TOTAL_STEPS - WARMUP_STEPS)
    return FINAL_LR_FRACTION + (1.0 - FINAL_LR_FRACTION) * 0.5 * (
        1.0 + math.cos(math.pi * progress)
    )
