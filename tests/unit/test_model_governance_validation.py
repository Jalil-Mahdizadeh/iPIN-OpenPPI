from __future__ import annotations

from pathlib import Path

from decimal import Decimal
import pytest
import yaml

from ipin_openppi.validation.model_governance import (
    independent_repetition_counts,
    independent_run_budget,
    independent_selection_key,
    independent_window_starts,
)


CONFIG = Path("configs/model_governance_and_baseline_training_protocol_v1.yaml")


def _config() -> dict:
    value = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.mark.parametrize("length", [1, 1022, 1023, 1916, 2000, 2044, 5000])
def test_independent_window_rule_covers_every_residue(length: int) -> None:
    starts = independent_window_starts(length)
    coverage = [0] * length
    for start in starts:
        for index in range(start, min(length, start + 1022)):
            coverage[index] += 1

    assert starts == sorted(set(starts))
    assert starts[0] == 0
    assert starts[-1] == max(0, length - 1022)
    assert min(coverage) >= 1


def test_independent_window_boundary_examples_are_exact() -> None:
    assert independent_window_starts(1022) == [0]
    assert independent_window_starts(1023) == [0, 1]
    assert independent_window_starts(1916) == [0, 894]
    assert independent_window_starts(2000) == [0, 894, 978]


def test_independent_positive_repetition_algebra_is_exact() -> None:
    floor, ceiling, ceiling_count = independent_repetition_counts(2_000_000, 16_799)

    assert (floor, ceiling, ceiling_count) == (119, 120, 919)
    assert ceiling_count * ceiling + (16_799 - ceiling_count) * floor == 2_000_000


def test_independent_search_budget_is_bounded() -> None:
    assert independent_run_budget(_config()) == {
        "runs": 30,
        "comparisons": 300_000_000,
    }


def test_independent_selection_key_prioritizes_c3_then_c2_then_c1() -> None:
    better_c3 = independent_selection_key(
        {"C3_development": 0.6125, "C2_development": 0.1, "C1_development": 0.1},
        3,
        "gated",
    )
    better_secondary = independent_selection_key(
        {"C3_development": 0.6124, "C2_development": 0.9, "C1_development": 0.9},
        0,
        "linear",
    )
    assert better_c3 < better_secondary

    assert independent_selection_key(
        {"C3_development": 0.7, "C2_development": 0.8, "C1_development": 0.1},
        3,
        "z",
    ) < independent_selection_key(
        {"C3_development": 0.7, "C2_development": 0.7, "C1_development": 0.9},
        0,
        "a",
    )


def test_independent_selection_quantization_and_simple_tie_break_are_exact() -> None:
    key = independent_selection_key(
        {"C3_development": 0.6125, "C2_development": 0.5, "C1_development": 0.5},
        0,
        "linear",
    )
    assert key[0] == Decimal("-0.613")

    simple = independent_selection_key(
        {"C3_development": 0.6, "C2_development": 0.6, "C1_development": 0.6},
        0,
        "simple",
    )
    complex_model = independent_selection_key(
        {"C3_development": 0.6, "C2_development": 0.6, "C1_development": 0.6},
        3,
        "complex",
    )
    assert simple < complex_model


@pytest.mark.parametrize(
    "call",
    [
        lambda: independent_window_starts(0),
        lambda: independent_window_starts(10, window=5, stride=6),
        lambda: independent_repetition_counts(0, 1),
        lambda: independent_repetition_counts(1, 0),
        lambda: independent_selection_key(
            {"C3_development": 1.1, "C2_development": 0.5, "C1_development": 0.5},
            0,
            "bad",
        ),
    ],
)
def test_independent_helpers_reject_invalid_inputs(call) -> None:
    with pytest.raises(ValueError):
        call()


def test_independent_validator_does_not_import_production_or_model_frameworks() -> None:
    source = Path("src/ipin_openppi/validation/model_governance.py").read_text(
        encoding="utf-8"
    )

    assert "from ipin_openppi.model_governance" not in source
    assert "import torch" not in source
    assert "import transformers" not in source
