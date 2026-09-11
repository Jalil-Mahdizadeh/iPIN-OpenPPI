"""Public aggregate consistency checks; no pair data or model execution."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "artifacts/results/c3_control_shift_investigation_v1"


def read(path):
    return json.loads(path.read_text())


def test_analysis_sources_and_first_result_remain_hash_bound():
    first, second = read(RESULTS / "RESULTS.json"), read(RESULTS / "COMPONENT_SUPPLEMENT.json")
    assert hashlib.sha256((RESULTS / "RESULTS.json").read_bytes()).hexdigest() == second["initial_result_sha256"]
    for doc, script, scope in (
        (first, "c3_control_shift_v1.py", "C3_CONTROL_SHIFT_INVESTIGATION_v1.md"),
        (second, "c3_control_shift_components_v1.py", "C3_CONTROL_SHIFT_COMPONENT_SUPPLEMENT_v1.md"),
    ):
        assert hashlib.sha256((ROOT / "scripts/analysis" / script).read_bytes()).hexdigest() == doc["analysis_code_sha256"]
        assert hashlib.sha256((ROOT / "docs/protocols" / scope).read_bytes()).hexdigest() == doc["scope_document_sha256"]


def test_exact_parity_and_original_bootstrap_reproduction():
    first = read(RESULTS / "RESULTS.json")
    assert first["parity"]["full_development_rows"] == 1_002_265
    assert first["parity"]["protected_CPU_scorer_development_sample_rows"] == 10457
    assert set(first["parity"]["full_row_score_max_abs"].values()) == {0.0}
    assert set(first["parity"]["protected_CPU_scorer_max_abs"].values()) == {0.0}
    for name, values in first["bootstrap"]["scores"].items():
        np.testing.assert_allclose(values["full_ci95"], first["published_comparison"]["C3"][name]["development_ci95"], rtol=0, atol=1e-12)


def test_exhaustive_component_and_positive_group_census():
    first, second = read(RESULTS / "RESULTS.json"), read(RESULTS / "COMPONENT_SUPPLEMENT.json")
    assert len(second["all_positive_participating_component_influences"]) == 353
    groups = second["groups"]
    assert groups["within_component"]["positive_rows"] == 825
    assert groups["within_component"]["unlabeled_rows"] == 66144
    for scope in (("within_component", "between_component"), ("both_in_third", "one_in_third", "neither_in_third")):
        assert sum(groups[x]["positive_rows"] for x in scope) == 2265
        assert sum(groups[x]["unlabeled_rows"] for x in scope) == 1_000_000
        for name, expected in first["development"]["full_concordance"].items():
            actual = sum(groups[x]["positive_fraction"] * groups[x]["positive_group_vs_full_U"][name] for x in scope)
            assert abs(actual - expected) < 1e-12
    for group in groups.values():
        assert sum(group["source_positive_counts"].values()) == group["positive_rows"]


def test_sensitivity_intervals_and_scopes_are_explicit():
    second = read(RESULTS / "COMPONENT_SUPPLEMENT.json")
    assert set(second["sensitivities"]) == {"between_component", "neither_in_third", "neither_in_first_or_third"}
    assert second["bootstrap_replicates"] == 2000
    assert second["test_rows_truth_predictions_keys_opened"] is False
    assert second["new_training_or_test_evaluation"] is False
    for scope in second["sensitivities"].values():
        assert all(0 <= x <= 1 for x in scope["concordance"].values())
        assert all(0 <= lo <= hi <= 1 for lo, hi in scope["ci95"].values())
        assert scope["within_length_bins"]["positive_coverage"] == 1.0
