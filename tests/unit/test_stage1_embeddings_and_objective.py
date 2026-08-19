from __future__ import annotations

import hashlib

import numpy as np
import pytest
import torch

from ipin_openppi.stage1.embeddings import (
    SequenceRecord,
    WindowRecord,
    greedy_window_batches,
    repeat_selection_key,
    window_starts,
)
from ipin_openppi.stage1.objective import (
    deterministic_order,
    learning_rate_multiplier,
    order_key,
    positive_repetition_counts,
    rational_weights,
    weighted_pairwise_logistic_loss,
)


def test_windowing_complete_and_exact_terminal_rule() -> None:
    assert window_starts(1) == (0,)
    assert window_starts(1022) == (0,)
    assert window_starts(1023) == (0, 1)
    assert window_starts(1916) == (0, 894)
    assert window_starts(2000) == (0, 894, 978)
    for length in (1023, 1400, 1917, 7570):
        coverage = np.zeros(length, dtype=np.int64)
        for start in window_starts(length):
            coverage[start : start + 1022] += 1
        assert np.all(coverage >= 1)


def test_greedy_batches_never_exceed_residue_budget() -> None:
    windows = [
        WindowRecord(0, 0, 1000, True),
        WindowRecord(1, 0, 1000, True),
        WindowRecord(2, 0, 1000, True),
        WindowRecord(3, 0, 1000, True),
        WindowRecord(4, 0, 100, True),
    ]
    batches = list(greedy_window_batches(windows))
    assert [sum(item.residues for item in batch) for batch in batches] == [4000, 100]


def test_repeat_selection_payload_is_frozen() -> None:
    expected = hashlib.sha256(b"esm2_150m:abc").digest()
    assert repeat_selection_key("esm2_150m", "abc") == expected


def test_exact_order_payload_and_tie_break() -> None:
    expected = hashlib.sha256(
        b"sha256:ipin-openppi-model-training-v1:20260803:1:U:pair-a"
    ).digest()
    assert order_key(seed=20260803, pass_index=1, state="U", pair_id="pair-a") == expected
    pair_ids = ["pair-c", "pair-a", "pair-b"]
    first = deterministic_order(pair_ids, seed=20260803, pass_index=1, state="U")
    second = deterministic_order(pair_ids, seed=20260803, pass_index=1, state="U")
    assert np.array_equal(first, second)
    assert sorted(first.tolist()) == [0, 1, 2]


@pytest.mark.parametrize("pass_index", range(1, 6))
def test_positive_repetition_algebra(pass_index: int) -> None:
    counts = positive_repetition_counts(pass_index)
    assert counts.min() == 119
    assert counts.max() == 120
    assert int((counts == 120).sum()) == 919
    assert int(counts.sum()) == 2_000_000


def test_rational_weighted_pairwise_loss() -> None:
    numerator = np.asarray([10, 9], dtype=np.int64)
    denominator = np.asarray([2, 3], dtype=np.int64)
    weights = rational_weights(numerator, denominator)
    score_p = torch.tensor([2.0, 1.0])
    score_u = torch.tensor([1.0, 2.0])
    loss, terms = weighted_pairwise_logistic_loss(
        score_p, score_u, torch.from_numpy(weights), float(weights.mean())
    )
    expected_terms = torch.nn.functional.softplus(-(score_p - score_u))
    expected = ((torch.from_numpy(weights) / weights.mean()) * expected_terms.double()).mean()
    assert torch.equal(terms, expected_terms)
    assert torch.equal(loss, expected)


def test_scheduler_boundaries() -> None:
    assert learning_rate_multiplier(1) == pytest.approx(1 / 123)
    assert learning_rate_multiplier(123) == pytest.approx(1.0)
    assert learning_rate_multiplier(2445) == pytest.approx(0.1)
