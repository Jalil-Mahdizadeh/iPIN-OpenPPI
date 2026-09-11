"""Synthetic, non-protected qualification of the diagnostic helpers."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

MODULE = Path(__file__).resolve().parents[2] / "scripts/analysis/c3_control_shift_v1.py"
spec = importlib.util.spec_from_file_location("c3_control_shift", MODULE)
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


def test_favorable_mass_weighted_ties():
    scores = np.array([1., 2., 1., 2., 3.])
    p = np.array([True, True, False, False, False])
    weight = np.array([1., 1., 1., 2., 3.])
    np.testing.assert_allclose(diagnostic.favorable_mass(scores, p, weight), [1 / 12, 1 / 3])


def test_component_subset_keeps_draw_universe():
    data = {"components": np.array(["a", "b", "c"]), "positive": np.array([True, False, False]),
            "component_a": np.array([0, 1, 2]), "component_b": np.array([1, 2, 0])}
    result = diagnostic.subset(data, np.array([True, False, True]))
    np.testing.assert_array_equal(result["components"], data["components"])
    np.testing.assert_array_equal(result["component_a"], [0, 2])


@pytest.mark.parametrize("bad", ["test", "train"])
def test_rejects_non_development_endpoints(bad):
    with pytest.raises(RuntimeError, match="Non-development"):
        diagnostic.assert_development({"a": np.array([0]), "b": np.array([1])}, np.array(["development", bad]))


@pytest.mark.parametrize("a,b", [([-1], [1]), ([0], [2]), ([0], [0])])
def test_rejects_invalid_pair(a, b):
    with pytest.raises(RuntimeError):
        diagnostic.assert_development({"a": np.array(a), "b": np.array(b)}, np.array(["development"] * 2))


def test_fixed_length_bins_symmetric_boundaries():
    a, b = np.array([199, 200, 500, 1000]), np.array([1000, 500, 200, 199])
    np.testing.assert_array_equal(diagnostic.length_bins(a, b), [3, 6, 6, 3])
    np.testing.assert_array_equal(diagnostic.length_bins(a, b), diagnostic.length_bins(b, a))


def test_positive_group_decomposition():
    data = {"positive": np.array([True, True, False, False]), "weight": np.array([1., 1., 2., 3.])}
    favorable = np.tile([[.2], [.8]], (1, len(diagnostic.NAMES)))
    first = diagnostic.group_summary(np.array([True, False, True, False]), data, favorable)
    second = diagnostic.group_summary(np.array([False, True, False, True]), data, favorable)
    assert first["HT_U_fraction"] == .4
    for name in diagnostic.NAMES:
        assert first["positive_fraction"] * first["positive_group_vs_full_U"][name] + second["positive_fraction"] * second["positive_group_vs_full_U"][name] == .5


def test_matched_bins_and_missing_U_coverage():
    data = {"positive": np.array([True, True, True, False, False]), "weight": np.ones(5),
            "components": np.array(["a", "b"]), "component_a": np.zeros(5, int), "component_b": np.ones(5, int)}
    scores = np.tile(np.array([3., 1., 4., 2., 2.])[:, None], (1, len(diagnostic.NAMES)))
    result = diagnostic.matched_bins(scores, data, np.array([0, 0, 1, 0, 0]))
    assert result["positive_coverage"] == 2 / 3
    assert set(result["positive_weighted_within_bin_concordance"].values()) == {.5}


def test_weighted_quantiles():
    assert diagnostic.weighted_quantiles(np.array([30, 10, 20]), np.array([1., 8., 1.])) == [10., 10., 20.]
