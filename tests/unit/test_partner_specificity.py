from collections import Counter
import hashlib
from pathlib import Path

import numpy as np
import pytest
import torch
import yaml

from ipin_openppi.partner_specificity.data import config, public_inputs, validate_state, verify_records, write_json
from ipin_openppi.partner_specificity.models import make_model
from ipin_openppi.partner_specificity.pipeline import decide
from ipin_openppi.partner_specificity.semantics import (
    Query, anchor_points, assign_folds, bootstrap_anchor_totals, build_queries,
    cell_masks, embedding_indices, interval, normalize, pair_codes, panel_recall,
    quartet_bootstrap_totals, quartet_credit, select_quartets, weighted_concordance,
)


def test_identity_join_uses_explicit_rows_not_manifest_or_lexical_order():
    vectors = [{"sequence_sha256": "c", "row_index": 2},
               {"sequence_sha256": "a", "row_index": 1},
               {"sequence_sha256": "b", "row_index": 0}]
    assert embedding_indices(vectors, ["a", "b", "c"], 3).tolist() == [1, 0, 2]


@pytest.mark.parametrize("vectors,endpoints", [
    ([{"sequence_sha256": "a", "row_index": 0}] * 2, ["a"]),
    ([{"sequence_sha256": "a", "row_index": 0}, {"sequence_sha256": "b", "row_index": 0}], ["a"]),
    ([{"sequence_sha256": "a", "row_index": 9}], ["a"]),
    ([{"sequence_sha256": "a", "row_index": 0}], ["b"]),
    ([{"sequence_sha256": "a", "row_index": 0}], ["a", "a"]),
])
def test_bad_embedding_identities_fail(vectors, endpoints):
    with pytest.raises(ValueError):
        embedding_indices(vectors, endpoints, len(vectors))


def test_component_split_deterministic_and_isolated():
    sizes = {"a": 8, "b": 6, "c": 2, "d": 1, "e": 1, "f": 1}
    folds = assign_folds(sizes, 3, "fixed")
    assert folds == assign_folds(dict(reversed(list(sizes.items()))), 3, "fixed")
    endpoint_folds = np.array([folds[c] for c in sizes for _ in range(sizes[c])])
    a, b = np.triu_indices(len(endpoint_folds), 1)
    for f in range(3):
        fit, cross, heldout = cell_masks(a, b, endpoint_folds, f)
        assert np.all(fit.astype(int) + cross + heldout == 1)
        assert not np.isin(np.r_[a[fit], b[fit]], np.flatnonzero(endpoint_folds == f)).any()
        assert np.all(endpoint_folds[np.r_[a[heldout], b[heldout]]] == f)


def test_normalization_never_fits_heldout_values():
    raw = np.array([[1, 7], [3, 7], [100, -50]], dtype=np.float32)
    fit = np.array([True, True, False])
    x, mean, std = normalize(raw, fit)
    changed = raw.copy()
    changed[2] = 100000
    _, mean2, std2 = normalize(changed, fit)
    np.testing.assert_array_equal(mean, mean2)
    np.testing.assert_array_equal(std, std2)
    np.testing.assert_array_equal(mean, [2, 7])
    assert std[1] == 1e-6 and x.dtype == np.float32
    with pytest.raises(ValueError):
        normalize(raw, np.ones(3, dtype=bool))


def test_weighted_concordance_matches_brute_force_with_ties():
    p, u = np.array([1., 2., 0.]), np.array([1., 0., 3., 2.])
    uw, pw = np.array([100., 1., 3., 7.]), np.array([2., 0., 1.])
    credit = (p[:, None] > u).astype(float) + .5 * (p[:, None] == u)
    expected = np.sum(credit * pw[:, None] * uw) / (pw.sum() * uw.sum())
    assert weighted_concordance(p, u, uw, pw) == pytest.approx(expected)
    assert weighted_concordance([1], [1], [100]) == .5
    assert weighted_concordance([2], [1], [100]) == 1


def fixture_queries():
    a, b = np.array([0, 0, 1, 1, 2]), np.array([1, 2, 2, 3, 3])
    p = np.array([True, False, False, True, True])
    scores, weights = np.array([2., 1., 3., 1., 0.]), np.array([1., 7., 2., 1., 1.])
    return a, b, p, scores, weights, build_queries(a, b, p)


def test_equal_anchor_macro_differs_from_edge_average_and_recall_ties():
    a, b, p, scores, weights, queries = fixture_queries()
    points = anchor_points(scores, queries, weights)
    expected = []
    for q in queries:
        pp, uu = scores[q.positive], scores[q.unlabeled]
        matrix = (pp[:, None] > uu) + .5 * (pp[:, None] == uu)
        expected.append(np.mean(matrix @ weights[q.unlabeled] / weights[q.unlabeled].sum()))
    np.testing.assert_allclose(points, expected)
    assert len(queries) == 3
    # A tied U with the lower canonical key must precede a P: no label tie break.
    q = Query(0, np.array([0]), np.array([2]), np.array([1]), np.array([1]))
    assert panel_recall(np.ones(2), [q], 1, np.array([2, 1]))[0] == 0


def test_partner_propensity_stratification_and_missing_coverage():
    a, b, p, scores, weights, queries = fixture_queries()
    all_same = anchor_points(scores, queries, weights, np.zeros(4, dtype=int))
    np.testing.assert_array_equal(all_same, anchor_points(scores, queries, weights))
    separate = anchor_points(scores, queries, weights, np.arange(4))
    assert np.isnan(separate).all()


def test_component_bootstrap_matches_direct_weighted_comparisons():
    a, b, p, scores, weights, queries = fixture_queries()
    components = np.array([0, 1, 0, 2])  # Shared anchor/partner component.
    draws = np.array([[1, 1, 1], [2, 0, 3], [0, 2, 1], [2, 3, 1]])
    total, mass = bootstrap_anchor_totals(scores, queries, weights, components, draws)
    for i, draw in enumerate(draws):
        numerator, denominator = 0., 0.
        for q in queries:
            anchor = components[q.anchor]
            pm = np.array([1 if components[x] == anchor else draw[components[x]] for x in q.positive_partner])
            um = np.array([1 if components[x] == anchor else draw[components[x]] for x in q.unlabeled_partner]) * weights[q.unlabeled]
            if pm.sum() and um.sum():
                credit = (scores[q.positive, None] > scores[q.unlabeled]) + .5 * (scores[q.positive, None] == scores[q.unlabeled])
                numerator += draw[anchor] * np.sum(credit * pm[:, None] * um) / (pm.sum() * um.sum())
                denominator += draw[anchor]
        assert total[i] == pytest.approx(numerator)
        assert mass[i] == denominator
    assert total[0] / mass[0] == pytest.approx(anchor_points(scores, queries, weights).mean())


def test_quartet_enumerates_both_crosses_and_cancels_unary():
    a, b = np.array([0, 2, 0, 1, 0, 1]), np.array([1, 3, 3, 2, 2, 3])
    p = np.array([True, True, False, False, False, False])
    args = dict(salt="fixed", maximum=20, edge_cap=20, endpoint_cap=20)
    rows, endpoints, count = select_quartets(a, b, p, 4, **args)
    assert count == len(rows) == 2
    assert {tuple(x) for x in rows[:, 2:]} == {(2, 3), (4, 5)}
    unary = np.array([-.3, 12., 2.7, -9.])
    credit, contrast = quartet_credit(unary[a] + unary[b], rows)
    np.testing.assert_allclose(contrast, 0, atol=1e-14)
    np.testing.assert_array_equal(credit, [.5, .5])
    rows2, endpoints2, _ = select_quartets(a, b, p, 4, **args)
    np.testing.assert_array_equal(rows, rows2)
    np.testing.assert_array_equal(endpoints, endpoints2)
    limited, _, _ = select_quartets(a, b, p, 4, **{**args, "edge_cap": 1})
    assert len(limited) == 1
    missing, _, _ = select_quartets(a[:3], b[:3], p[:3], 4, **args)
    assert len(missing) == 0


def test_quartet_resampling_counts_same_component_once():
    credit = np.array([1., .5])
    endpoints = np.array([[0, 1, 2, 3], [0, 1, 2, 3]])
    component = np.array([0, 0, 1, 1])
    draws = np.array([[2, 3], [0, 4]])
    total, mass = quartet_bootstrap_totals(credit, endpoints, component, draws)
    np.testing.assert_array_equal(total, [9, 0])
    np.testing.assert_array_equal(mass, [12, 0])


@pytest.mark.parametrize("name", ["endpoint_linear", "endpoint_mlp64", "pair_linear"])
def test_heads_are_symmetric_deterministic_and_trainable(name):
    first, second = make_model(name, 42, dimension=4), make_model(name, 42, dimension=4)
    a, b = torch.randn(7, 4), torch.randn(7, 4)
    torch.testing.assert_close(first(a, b), first(b, a), rtol=0, atol=0)
    torch.testing.assert_close(first(a, b), second(a, b), rtol=0, atol=0)
    first(a, b).sum().backward()
    assert all(p.grad is not None for p in first.parameters())


def test_explicit_pair_features_can_discriminate_partner_swap():
    model = make_model("pair_linear", 1, dimension=1)
    with torch.no_grad():
        model.output.weight.zero_()
        model.output.bias.zero_()
        model.output.weight[0, 2] = 1  # a*b
    x = torch.tensor([[1.], [1.], [-1.], [-1.]])
    delta = model(x[0:1], x[1:2]) + model(x[2:3], x[3:4]) - model(x[0:1], x[3:4]) - model(x[2:3], x[1:2])
    assert delta.item() == 4


def test_intervals_require_valid_replicates():
    with pytest.raises(RuntimeError):
        interval([np.nan, 1])
    assert interval([.5] * 20) == [.5, .5]


def test_frozen_records_reject_drift_and_symlinks(tmp_path):
    target = tmp_path / "safe.json"
    write_json(target, {"a": 1})
    record = {"path": "safe.json", "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size}
    verify_records(tmp_path, [record])
    with pytest.raises(RuntimeError):
        write_json(target, {"a": 2})
    target.write_text("changed")
    with pytest.raises(RuntimeError):
        verify_records(tmp_path, [record])
    (tmp_path / "link.json").symlink_to(target)
    with pytest.raises(RuntimeError):
        verify_records(tmp_path, [{**record, "path": "link.json"}])


def test_input_allowlist_rejects_protected_or_development_substitution(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = config(root)
    cfg["inputs"]["endpoints"]["path"] = "data/canonical/protected/forbidden.parquet"
    with pytest.raises(RuntimeError, match="allowlist"):
        public_inputs(tmp_path, cfg)


def test_decision_three_way_and_no_protected_authority():
    cfg = config(Path(__file__).resolve().parents[2])
    args = dict(primary_delta=.04, primary_interval=[.01, .07], fold_deltas=[.02]*3,
                seed_deltas=[.03]*3, controls={"length": .01}, propensity_delta=.02,
                quartet={"ci95": [.52, .65], "control_deltas": {"length": .01, "kmer": .03}}, cfg=cfg)
    assert decide(**args)["disposition"].startswith("useful_internal")
    assert not decide(**args)["protected_evaluation_authorized"]
    assert decide(**{**args, "primary_interval": [-.04, .01]})["disposition"].startswith("useful_incremental_gain_excluded")
    assert decide(**{**args, "primary_interval": [-.04, .08]})["disposition"].startswith("inconclusive")


def test_canonical_pair_codes_symmetric_and_self_rejected():
    np.testing.assert_array_equal(pair_codes(np.array([2]), np.array([1]), 4), [6])
    np.testing.assert_array_equal(pair_codes(np.array([1]), np.array([2]), 4), [6])
    with pytest.raises(ValueError):
        pair_codes(np.array([1]), np.array([1]), 4)


def test_released_schema_states_not_notational_shorthand():
    validate_state(["released_positive"], "P")
    validate_state(["unlabeled"], "U")
    for values, state in ((["P"], "P"), (["U"], "U"), (["negative"], "U")):
        with pytest.raises(RuntimeError):
            validate_state(values, state)


def test_reference_validator_does_not_import_production_math_or_models():
    import ast
    path = Path(__file__).resolve().parents[2] / "src/ipin_openppi/partner_specificity/validation.py"
    modules = [n.module or "" for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.ImportFrom)]
    assert not any(m.endswith(("semantics", "models", "pipeline")) for m in modules)


@pytest.mark.parametrize("name", ["endpoint_linear", "endpoint_mlp64", "pair_linear"])
def test_reference_forward_uses_separate_numpy_algebra(name):
    from ipin_openppi.partner_specificity.validation import reference_scores
    model = make_model(name, 33, dimension=4).eval()
    raw = np.random.default_rng(123).normal(size=(8, 4)).astype(np.float32)
    a, b = np.array([0, 1, 2, 3]), np.array([4, 5, 6, 7])
    with torch.no_grad():
        predicted = model(torch.from_numpy(raw[a]), torch.from_numpy(raw[b])).numpy()
    reference = reference_scores(model.state_dict(), name, raw, a, b)
    np.testing.assert_allclose(reference, predicted, atol=1e-6, rtol=0)
