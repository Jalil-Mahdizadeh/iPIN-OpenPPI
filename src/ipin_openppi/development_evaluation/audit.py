"""Production pre-release audit for the DEC-0032 executable boundary."""

from __future__ import annotations

import inspect
import json
import math
from pathlib import Path
import tempfile
from typing import Any

import numpy as np
import pyarrow as pa
import torch
import yaml

from ipin_openppi.stage1.models import build_model

from .evaluation import _load_bootstrap, gpu_bootstrap_distributions
from .release import resolve_development_key_only, sha256_file
from .scoring import optimized_checkpoint_scores, scorer_records, validate_degree_metadata
from .semantics import (
    DETERMINISTIC_SCORERS,
    bootstrap_concordance_reference,
    component_draws,
    exact_interolog_from_neighbor_max,
    exact_interolog_reference,
    neighbor_max_similarity,
    pair_component_multipliers,
    quantize_selection_metric,
    selection_key,
    weighted_pairwise_concordance,
)


EXECUTION_ID = "development_release_and_evaluation_execution_v1"


def _check(checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any) -> None:
    checks.append(
        {"check_id": check_id, "status": "pass" if condition else "fail", "detail": detail}
    )


def _verified(project_root: Path, relative: str, expected: str) -> bool:
    path = project_root / relative
    return path.is_file() and not path.is_symlink() and sha256_file(path) == expected


def _fixture_rows() -> tuple[pa.Table, np.ndarray, list[str]]:
    scorer_ids = list(DETERMINISTIC_SCORERS) + [f"candidate_{index:02d}" for index in range(10)]
    scores = np.asarray(
        [
            np.linspace(0.8, 1.0, 19),
            np.linspace(0.3, 0.5, 19),
            np.linspace(0.1, 0.2, 19),
            np.linspace(0.6, 0.7, 19),
            np.linspace(0.3, 0.5, 19),
            np.linspace(0.0, 0.1, 19),
        ],
        dtype=np.float64,
    )
    rows = pa.table(
        {
            "state": ["released_positive", "released_positive", "unlabeled", "unlabeled", "unlabeled", "unlabeled"],
            "sampling_weight_numerator": np.asarray([1, 1, 2, 1, 3, 1], dtype=np.int64),
            "sampling_weight_denominator": np.ones(6, dtype=np.int64),
            "endpoint_a_component_id": ["a", "b", "a", "b", "c", "a"],
            "endpoint_b_component_id": ["b", "b", "a", "c", "c", "c"],
        }
    )
    return rows, scores, scorer_ids


def run_audit(project_root: Path, config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    _check(
        checks,
        "execution_projection_identity",
        config.get("execution_id") == EXECUTION_ID
        and config.get("status") == "authorized_pre_release_validation_required"
        and config["runtime"]["maximum_gpu_count"] == 1
        and config["runtime"]["maximum_gpu_hours"] == 30
        and config["runtime"]["maximum_new_governed_storage_gib"] == 100,
        {"execution_config_sha256": sha256_file(config_path)},
    )
    hash_checks = []
    for section in ("authority", "frozen_inputs"):
        values = config[section]
        for key, value in values.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            if path_key in values:
                ok = _verified(project_root, str(values[path_key]), str(value))
                hash_checks.append((f"{section}.{path_key}", ok))
    for section, path_key, sha_key in (
        ("development_release", "ciphertext", "ciphertext_sha256"),
        ("development_release", "certificate", "certificate_sha256"),
        ("protected_boundary", "protected_candidates_ciphertext", "protected_candidates_ciphertext_sha256"),
        ("protected_boundary", "protected_truth_ciphertext", "protected_truth_ciphertext_sha256"),
    ):
        values = config[section]
        hash_checks.append(
            (f"{section}.{path_key}", _verified(project_root, values[path_key], values[sha_key]))
        )
    _check(
        checks,
        "all_authority_public_and_sealed_hashes",
        all(ok for _, ok in hash_checks),
        {name: ok for name, ok in hash_checks},
    )

    registry_path = project_root / config["frozen_inputs"]["training_registry"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    runs, ensembles, scorer_ids = scorer_records(registry)
    checkpoint_ok = True
    for run in runs:
        checkpoint = run["selected_checkpoint"]
        path = project_root / checkpoint["path"]
        checkpoint_ok &= (
            path.is_file()
            and not path.is_symlink()
            and path.stat().st_size == checkpoint["bytes"]
            and sha256_file(path) == checkpoint["sha256"]
            and checkpoint["pass_index"] == 5
        )
    ensemble_ok = all(
        len(item["members"]) == 3
        and {member["seed"] for member in item["members"]} == {20260803, 20260817, 20260831}
        for item in ensembles
    )
    _check(
        checks,
        "exact_9_30_10_scorer_census_and_checkpoint_hashes",
        len(DETERMINISTIC_SCORERS) == 9
        and len(runs) == 30
        and len(ensembles) == 10
        and len(scorer_ids) == 49
        and checkpoint_ok
        and ensemble_ok,
        {"deterministic": 9, "selected_checkpoints": len(runs), "ensembles": len(ensembles)},
    )

    release_source = (project_root / "src/ipin_openppi/development_evaluation/release.py").read_text(
        encoding="utf-8"
    )
    resolver_source = inspect.getsource(resolve_development_key_only)
    _check(
        checks,
        "development_only_non_enumerating_key_resolver",
        "private_key_paths(" not in release_source
        and "import private_key_paths" not in release_source
        and "development_release_private.pem" in resolver_source
        and "protected_candidates_private_key" not in release_source
        and "protected_truth_private_key" not in release_source,
        {
            "resolver": "resolve_development_key_only",
            "protected_private_key_path_tokens": 0,
            "private_key_hash_recorded": False,
        },
    )

    scoring_source = (project_root / "src/ipin_openppi/development_evaluation/scoring.py").read_text(
        encoding="utf-8"
    )
    evaluation_source = (
        project_root / "src/ipin_openppi/development_evaluation/evaluation.py"
    ).read_text(encoding="utf-8")
    _check(
        checks,
        "no_training_optimizer_or_new_architecture_path",
        "torch.optim" not in scoring_source
        and ".backward(" not in scoring_source
        and "optimizer.step" not in scoring_source
        and "build_model(" not in scoring_source
        and "protected_candidates.cms" not in scoring_source + evaluation_source
        and "protected_truth.cms" not in scoring_source + evaluation_source,
        {"score_only_selected_checkpoint_state": True, "encoder_inference": False},
    )

    strict_schema = pa.schema([pa.field("value", pa.int64(), nullable=False)])
    nullable_schema = pa.schema([pa.field("value", pa.int64(), nullable=True)])
    strict_table = pa.Table.from_arrays([pa.array([1, 2], type=pa.int64())], schema=strict_schema)
    nullable_table = pa.Table.from_arrays([pa.array([3, 4], type=pa.int64())], schema=nullable_schema)
    promoted = pa.concat_tables(
        [strict_table, nullable_table], promote_options="permissive"
    )
    _check(
        checks,
        "issue_0009_nullability_only_concat_preserves_rows_values_and_type",
        'pa.concat_tables(tables, promote_options="permissive")' in scoring_source
        and promoted.schema.names == ["value"]
        and promoted.schema.field("value").type == pa.int64()
        and promoted["value"].to_pylist() == [1, 2, 3, 4]
        and promoted.num_rows == 4,
        {
            "authorized_change": "promote_options=permissive",
            "input_nullability": [False, True],
            "output_values": promoted["value"].to_pylist(),
            "output_type": str(promoted.schema.field("value").type),
        },
    )

    degree_rows = pa.table(
        {
            "endpoint_a_training_degree": np.asarray([1, 0], dtype=np.int64),
            "endpoint_b_training_degree": np.asarray([0, 2], dtype=np.int64),
            "stratum_id": ["0|1", "0|2"],
        }
    )
    source_semantics_ok = True
    try:
        validate_degree_metadata(
            cell_id="source_exclusive:HI-II-14:C2_development",
            rows=degree_rows,
            pooled_degree_a=np.asarray([12, 0], dtype=np.int64),
            pooled_degree_b=np.asarray([0, 25], dtype=np.int64),
        )
    except RuntimeError:
        source_semantics_ok = False
    primary_mismatch_rejected = False
    try:
        validate_degree_metadata(
            cell_id="C2_development",
            rows=degree_rows,
            pooled_degree_a=np.asarray([12, 0], dtype=np.int64),
            pooled_degree_b=np.asarray([0, 25], dtype=np.int64),
        )
    except RuntimeError:
        primary_mismatch_rejected = True
    bad_stratum = degree_rows.set_column(
        2, "stratum_id", pa.array(["0|2", "0|2"], type=pa.string())
    )
    source_stratum_mismatch_rejected = False
    try:
        validate_degree_metadata(
            cell_id="source_exclusive:HI-II-14:C2_development",
            rows=bad_stratum,
            pooled_degree_a=np.asarray([12, 0], dtype=np.int64),
            pooled_degree_b=np.asarray([0, 25], dtype=np.int64),
        )
    except RuntimeError:
        source_stratum_mismatch_rejected = True
    _check(
        checks,
        "issue_0010_source_design_degree_guard_and_pooled_scorer_features",
        source_semantics_ok
        and primary_mismatch_rejected
        and source_stratum_mismatch_rejected
        and "degree_a, degree_b = graph.degree[a], graph.degree[b]" in scoring_source
        and "output[:, 1] = np.log1p(degree_a) + np.log1p(degree_b)" in scoring_source,
        {
            "source_visible_design_metadata_accepted": source_semantics_ok,
            "primary_pooled_degree_mismatch_rejected": primary_mismatch_rejected,
            "source_stratum_mismatch_rejected": source_stratum_mismatch_rejected,
            "scorer_degree_source": "pooled_16799_training_positive_graph",
        },
    )

    # Exact HT and half-tie fixture, independently expanded over P x U.
    p = np.asarray([0.5, 1.0])
    u = np.asarray([0.0, 0.5, 2.0])
    w = np.asarray([1.0, 2.0, 1.0])
    brute = sum(
        weight * (float(p_score > u_score) + 0.5 * float(p_score == u_score))
        for p_score in p
        for u_score, weight in zip(u, w, strict=True)
    ) / (p.size * w.sum())
    observed = weighted_pairwise_concordance(p, u, w)
    _check(
        checks,
        "exact_HT_concordance_and_half_ties",
        observed == brute == 0.625,
        {"fixture_metric": observed},
    )

    components, counts = component_draws(["c", "a", "b"], cell_id="fixture", replicates=17)
    multiplier = pair_component_multipliers(counts[0], [0, 0, 1], [0, 1, 1])
    bootstrap_reference = bootstrap_concordance_reference(
        cell_id="fixture",
        positive_scores=[0.8, 0.3],
        unlabeled_scores=[0.1, 0.6, 0.3, 0.0],
        unlabeled_weights=[2.0, 1.0, 3.0, 1.0],
        positive_component_a=["a", "b"],
        positive_component_b=["b", "b"],
        unlabeled_component_a=["a", "b", "c", "a"],
        unlabeled_component_b=["a", "c", "c", "c"],
        replicates=17,
    )
    _check(
        checks,
        "PCG64DXSM_component_draw_and_pigeonhole_reference",
        components == ("a", "b", "c")
        and np.all(counts.sum(axis=1) == 3)
        and multiplier[0] == counts[0, 0]
        and np.isfinite(bootstrap_reference).any(),
        {"replicates": 17, "first_pair_multipliers": multiplier.tolist()},
    )

    similarity = np.asarray(
        [[1.0, 0.2, 0.3, 0.4], [0.1, 1.0, 0.8, 0.2], [0.6, 0.1, 1.0, 0.9]]
    )
    edge_u, edge_v = np.asarray([0, 1, 2]), np.asarray([1, 2, 3])
    neighbor = neighbor_max_similarity(similarity, edge_u, edge_v)
    fast = exact_interolog_from_neighbor_max(similarity, neighbor, [0, 1], [1, 2])
    direct = np.asarray(
        [
            exact_interolog_reference(similarity[0], similarity[1], edge_u, edge_v),
            exact_interolog_reference(similarity[1], similarity[2], edge_u, edge_v),
        ]
    )
    _check(
        checks,
        "exact_orientation_invariant_interolog_identity",
        np.array_equal(fast, direct),
        {"scores": fast.tolist()},
    )

    model_ok = True
    model_differences = {}
    for family, dimension, dropout in (
        ("lightweight_esm2_150m_linear", 640, 0.0),
        ("esm2_650m_linear_ablation", 1280, 0.0),
        ("esm2_650m_nonlinear_no_gate_ablation", 1280, 0.1),
        ("esm2_650m_partner_gated_primary", 1280, 0.1),
    ):
        generator = torch.Generator().manual_seed(71)
        embeddings = torch.randn((13, dimension), generator=generator) + 0.2
        pair_a = np.asarray([0, 3, 7, 9, 4], dtype=np.int32)
        pair_b = np.asarray([2, 8, 1, 5, 10], dtype=np.int32)
        model = build_model(family, dropout=dropout, seed=20260803).eval()
        with torch.inference_mode():
            expected = model(embeddings[pair_a], embeddings[pair_b]).numpy()
            swapped = model(embeddings[pair_b], embeddings[pair_a]).numpy()
        fast_score = optimized_checkpoint_scores(
            family=family,
            state=model.state_dict(),
            embeddings=embeddings,
            pair_a=pair_a,
            pair_b=pair_b,
        )
        difference = float(np.max(np.abs(expected - fast_score)))
        swap = float(np.max(np.abs(expected - swapped)))
        model_differences[family] = {"optimized_max_abs": difference, "swap_max_abs": swap}
        model_ok &= difference == 0.0 and swap == 0.0
    _check(
        checks,
        "all_four_model_families_exact_and_swap_symmetric",
        model_ok,
        model_differences,
    )

    fixture_rows, fixture_scores, fixture_scorers = _fixture_rows()
    with tempfile.TemporaryDirectory(prefix="development_bootstrap_fixture_") as temporary:
        bootstrap_record = gpu_bootstrap_distributions(
            cell_id="fixture",
            rows=fixture_rows,
            scores=fixture_scores,
            scorer_ids=fixture_scorers,
            bootstrap_scorer_ids=fixture_scorers,
            output_root=Path(temporary) / "bootstrap",
        )
        _, gpu_values = _load_bootstrap(Path(temporary) / "bootstrap")
        reference = bootstrap_concordance_reference(
            cell_id="fixture",
            positive_scores=fixture_scores[:2, 0],
            unlabeled_scores=fixture_scores[2:, 0],
            unlabeled_weights=[2.0, 1.0, 3.0, 1.0],
            positive_component_a=["a", "b"],
            positive_component_b=["b", "b"],
            unlabeled_component_a=["a", "b", "c", "a"],
            unlabeled_component_b=["a", "c", "c", "c"],
            replicates=2_000,
        )
        finite = np.isfinite(reference)
        bootstrap_equal = np.array_equal(np.isnan(gpu_values[0]), np.isnan(reference)) and np.allclose(
            gpu_values[0, finite], reference[finite], rtol=0, atol=1e-15
        )
    _check(
        checks,
        "GPU_bootstrap_equals_CPU_reference_with_identical_draws",
        bootstrap_equal and bootstrap_record["replicates"] == 2_000,
        {"finite_replicates": int(finite.sum()), "maximum_absolute_difference": float(np.max(np.abs(gpu_values[0, finite] - reference[finite])))},
    )

    ensemble_fixture = np.mean(
        np.asarray([[0.1, 0.4], [0.2, 0.5], [0.3, 0.6]], dtype=np.float64), axis=0
    )
    selection_a = selection_key(
        candidate_id="a",
        family="lightweight_esm2_150m_linear",
        metrics={"C3_development": 0.6125, "C2_development": 0.7, "C1_development": 0.8},
    )
    selection_b = selection_key(
        candidate_id="b",
        family="esm2_650m_partner_gated_primary",
        metrics={"C3_development": 0.6124, "C2_development": 0.9, "C1_development": 0.9},
    )
    _check(
        checks,
        "ensemble_arithmetic_and_selection_quantization",
        np.allclose(ensemble_fixture, np.asarray([0.2, 0.5]), rtol=0, atol=1e-15)
        and quantize_selection_metric(0.6125).as_tuple().exponent == -3
        and selection_a < selection_b,
        {"ensemble_fixture": ensemble_fixture.tolist(), "selection_a_precedes_b": selection_a < selection_b},
    )

    policy_tokens = (
        "C3_vs_strongest_simple_at_least_0_02",
        "C3_vs_650m_linear_at_least_0_01",
        "C3_vs_matched_no_gate_at_least_0_005",
        "positive_named_source_direction",
        "positive_outside_top_10_percent_hubs",
        "withdraw_C1_gain_claim",
        "stop_before_protected_evaluation",
    )
    _check(
        checks,
        "complexity_kill_source_contains_every_consequential_gate",
        all(token in evaluation_source for token in policy_tokens),
        {"tokens": list(policy_tokens)},
    )

    failed = [item for item in checks if item["status"] != "pass"]
    return {
        "schema_version": 1,
        "execution_id": EXECUTION_ID,
        "status": "pass" if not failed else "fail",
        "execution_config_sha256": sha256_file(config_path),
        "check_counts": {"pass": len(checks) - len(failed), "fail": len(failed), "total": len(checks)},
        "checks": checks,
        "development_private_key_resolved_or_accessed": False,
        "protected_private_key_resolved_or_accessed": False,
        "development_plaintext_accessed": False,
        "protected_candidates_or_truth_accessed": False,
    }
