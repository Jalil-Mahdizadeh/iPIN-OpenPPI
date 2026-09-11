"""Pre-fit fixtures: no research fits or protected data access."""
import numpy as np
import pytest
import torch

from ipin_openppi.development_evaluation.semantics import component_draws, pair_component_multipliers, weighted_pairwise_concordance
from ipin_openppi.model_optimization.common import recipes, read, verify
from ipin_openppi.model_optimization.metrics import bootstrap, gate
from ipin_openppi.model_optimization.models import build, load_state, save_state
from ipin_openppi.model_optimization.run import lr_at, training_orders


@pytest.mark.parametrize("family", ["linear", "mlp", "residual_mlp", "bilinear"])
def test_exact_symmetry_replay_and_gradients(family, tmp_path):
    spec = {"family": family, "width": 8, "dropout": .2}
    model = build(6, spec, 7).eval()
    a, b = torch.randn(13, 6), torch.randn(13, 6)
    torch.testing.assert_close(model(a, b), model(b, a), atol=0, rtol=0)
    loss = torch.nn.functional.softplus(-(model(a, b) - model(a, a))).mean()
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    path = tmp_path / "state.npz"
    save_state(path, model)
    other = build(6, spec, 42).eval()
    load_state(path, other)
    torch.testing.assert_close(model(a, b), other(a, b), atol=0, rtol=0)


def fixture():
    return {"positive": np.array([True, True, True, False, False, False, False]),
            "weight": np.array([1., 1., 1., 2., 3., 4., 1.]),
            "component_a": np.array([0, 1, 2, 0, 1, 2, 0]),
            "component_b": np.array([0, 1, 2, 0, 1, 2, 2]),
            "components": np.array(["a", "b", "c"])}


@pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CPU pre-fit suite; CUDA replay is required by runner"))])
def test_bootstrap_ties_weights_and_same_component_against_reference(device):
    data = fixture()
    scores = np.array([1., 2., 0., 0., 1., 2., 1.])
    actual = bootstrap(scores, data, cell="fixture", replicates=41, device=device, batch=7)[:, 0]
    _, counts = component_draws(data["components"], cell_id="fixture", replicates=41)
    expected = []
    p = data["positive"]
    for count in counts:
        multipliers = pair_component_multipliers(count, data["component_a"], data["component_b"])
        expected.append(weighted_pairwise_concordance(scores[p], scores[~p], data["weight"][~p],
                                                      positive_multipliers=multipliers[p], unlabeled_multipliers=multipliers[~p]))
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0)


def test_permutations_visit_every_unlabeled_row_and_are_reproducible():
    p, u = training_orders(42, 1, 7, 101)
    p2, u2 = training_orders(42, 1, 7, 101)
    assert np.array_equal(p, p2) and np.array_equal(u, u2)
    assert np.array_equal(np.sort(u), np.arange(101))
    assert np.bincount(p).max() - np.bincount(p).min() == 1
    assert not np.array_equal(u, training_orders(42, 2, 7, 101)[1])


def test_schedule_is_bounded_with_declared_floor():
    values = [lr_at(i, 100, .001) for i in range(100)]
    assert min(values) > 0 and max(values) == .001
    assert values[-1] == pytest.approx(.0001)


def test_gate_rejects_zero_gain_or_unstable_seed_or_crossing_interval():
    data = fixture()
    base = np.array([1., 2., 0., 0., 1., 2., 1.])
    data["baseline"] = np.column_stack([base] * 3)
    improved = base.copy()
    improved[data["positive"]] += 3
    candidate = np.column_stack([improved] * 3)
    draws = np.tile([.5, .8], (2000, 1))
    assert gate(candidate, data, draws)["passed"]
    assert not gate(data["baseline"], data, draws)["passed"]
    candidate[:, 2] = base
    assert not gate(candidate, data, draws)["passed"]
    assert not gate(np.column_stack([improved] * 3), data, draws[:, ::-1])["passed"]


def test_manifest_path_escape_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="Unsafe"):
        verify(tmp_path, [{"path": "../secret", "bytes": 0, "sha256": "0" * 64}])


def test_recipe_census():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    result = recipes(read(root / "configs/model_optimization_v1.json"))
    assert len(result) == 24
    assert len({x["family"] for x in result}) == 4
    assert len({x["encoder"] for x in result}) == 2
