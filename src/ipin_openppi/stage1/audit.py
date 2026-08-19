"""Production audit of the frozen Stage 1 implementation before execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import torch

from .baselines import (
    component_mass_product_score,
    degree_sum_score,
    deterministic_hash_score,
    exact_interolog_score,
    length_ratio_score,
    length_sum_score,
    preferential_attachment_score,
)
from .constants import (
    ALLOWED_SCIENTIFIC_INPUTS,
    CANDIDATES,
    FAMILIES,
    MODEL_SIF_SHA256,
    PASSES,
    POSITIVE_PATH,
    POSITIVE_ROWS,
    POSITIVE_SHA256,
    PROTOCOL_CONFIGURATION_SHA256,
    SEEDS,
    STRATA_PATH,
    STRATA_SHA256,
    TOTAL_STEPS,
    UNLABELED_PATH,
    UNLABELED_ROWS,
    UNLABELED_SHA256,
)
from .embeddings import window_starts
from .models import build_model, parameter_count
from .objective import (
    deterministic_order,
    learning_rate_multiplier,
    order_key,
    positive_repetition_counts,
    rational_weights,
    weighted_pairwise_logistic_loss,
)
from .support import atomic_json, git_commit, require_sha256


def _check(checks: list[dict[str, Any]], check_id: str, condition: bool, detail: Any) -> None:
    checks.append(
        {"check_id": check_id, "detail": detail, "status": "pass" if condition else "fail"}
    )


def audit_stage1_implementation(project_root: Path, output: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    _check(
        checks,
        "authority_identity",
        PROTOCOL_CONFIGURATION_SHA256
        == "3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5"
        and MODEL_SIF_SHA256
        == "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91",
        {"protocol": PROTOCOL_CONFIGURATION_SHA256, "container": MODEL_SIF_SHA256},
    )
    _check(
        checks,
        "public_input_allowlist",
        len(ALLOWED_SCIENTIFIC_INPUTS) == 6
        and all("sealed" not in path and ".private" not in path for path in ALLOWED_SCIENTIFIC_INPUTS),
        sorted(ALLOWED_SCIENTIFIC_INPUTS),
    )
    for path, expected in (
        (POSITIVE_PATH, POSITIVE_SHA256),
        (UNLABELED_PATH, UNLABELED_SHA256),
        (STRATA_PATH, STRATA_SHA256),
    ):
        require_sha256(project_root / path, expected)
    positive = pq.read_table(project_root / POSITIVE_PATH)
    unlabeled = pq.read_table(project_root / UNLABELED_PATH)
    strata = pq.read_table(project_root / STRATA_PATH)
    _check(
        checks,
        "public_P_U_identity",
        positive.num_rows == POSITIVE_ROWS
        and unlabeled.num_rows == UNLABELED_ROWS
        and strata.num_rows == 36
        and set(positive["state"].to_pylist()) == {"released_positive"}
        and set(unlabeled["state"].to_pylist()) == {"unlabeled"},
        {"P": positive.num_rows, "U": unlabeled.num_rows, "strata": strata.num_rows},
    )
    _check(
        checks,
        "exact_two_candidates",
        set(CANDIDATES) == {"esm2_150m", "esm2_650m"}
        and CANDIDATES["esm2_150m"]["hidden_size"] == 640
        and CANDIDATES["esm2_650m"]["hidden_size"] == 1280,
        CANDIDATES,
    )
    starts = window_starts(7570)
    coverage = np.zeros(7570, dtype=np.int64)
    for start in starts:
        coverage[start : start + 1022] += 1
    _check(
        checks,
        "embedding_window_coverage",
        starts[-1] == 7570 - 1022 and bool(np.all(coverage >= 1)),
        {"starts": list(starts), "minimum_coverage": int(coverage.min())},
    )
    _check(
        checks,
        "mandatory_zero_parameter_formulas",
        0 <= deterministic_hash_score("fixture") <= 1
        and degree_sum_score(2, 3) > 0
        and preferential_attachment_score(2, 3) > 0
        and component_mass_product_score(4, 5) > 0
        and length_sum_score(10, 20) > 0
        and length_ratio_score(10, 20) < 0,
        "hash, degree, preferential attachment, component mass, and both length controls",
    )
    interolog = exact_interolog_score(
        np.asarray([0.9, 0.1, 0.3]),
        np.asarray([0.2, 0.8, 0.4]),
        np.asarray([0, 1]),
        np.asarray([1, 2]),
    )
    _check(checks, "exact_interolog_orientation", interolog == 0.8, {"score": interolog})
    family_results: dict[str, Any] = {}
    family_ok = True
    for family in FAMILIES:
        dropout = 0.1 if "nonlinear" in family or "partner_gated" in family else 0.0
        dimension = 640 if family == "lightweight_esm2_150m_linear" else 1280
        model = build_model(family, dropout=dropout, seed=SEEDS[0]).eval()
        generator = torch.Generator().manual_seed(123)
        a = torch.randn(4, dimension, generator=generator)
        b = torch.randn(4, dimension, generator=generator)
        with torch.no_grad():
            difference = float(torch.max(torch.abs(model(a, b) - model(b, a))))
        count = parameter_count(model)
        family_results[family] = {"parameters": count, "swap_max_abs": difference}
        family_ok = family_ok and count < 2_000_000 and difference <= 1e-6
    _check(checks, "four_head_implementations", family_ok, family_results)
    first = build_model("esm2_650m_partner_gated_primary", dropout=0.1, seed=SEEDS[0])
    second = build_model("esm2_650m_partner_gated_primary", dropout=0.1, seed=SEEDS[0])
    _check(
        checks,
        "seeded_xavier_zero_bias_reproducibility",
        all(torch.equal(a, b) for a, b in zip(first.parameters(), second.parameters(), strict=True)),
        {"seed": SEEDS[0]},
    )
    weights = rational_weights(np.asarray([10, 9]), np.asarray([2, 3]))
    score_p = torch.tensor([2.0, 1.0])
    score_u = torch.tensor([1.0, 2.0])
    loss, terms = weighted_pairwise_logistic_loss(
        score_p, score_u, torch.from_numpy(weights), float(weights.mean())
    )
    expected = ((torch.from_numpy(weights) / weights.mean()) * torch.nn.functional.softplus(-(score_p - score_u)).double()).mean()
    _check(
        checks,
        "weighted_P_vs_U_objective",
        torch.equal(loss, expected) and torch.isfinite(terms).all(),
        {"loss": float(loss)},
    )
    pair_ids = ["pair-c", "pair-a", "pair-b"]
    order = deterministic_order(pair_ids, seed=SEEDS[0], pass_index=1, state="U")
    _check(
        checks,
        "exact_order_payload_and_permutation",
        sorted(order.tolist()) == [0, 1, 2]
        and len(order_key(seed=SEEDS[0], pass_index=1, state="U", pair_id="pair-a")) == 32,
        {"order": order.tolist()},
    )
    repetitions_ok = all(
        positive_repetition_counts(pass_index).sum() == UNLABELED_ROWS
        for pass_index in range(1, PASSES + 1)
    )
    _check(
        checks,
        "positive_census_repetition_algebra",
        repetitions_ok,
        {"floor": 119, "ceiling": 120, "ceiling_count": 919},
    )
    matrix_count = sum(len(spec["recipes"]) * len(SEEDS) for spec in FAMILIES.values())
    _check(
        checks,
        "bounded_nonadaptive_matrix",
        matrix_count == 30 and 30 * PASSES * UNLABELED_ROWS == 300_000_000,
        {"runs": matrix_count, "comparisons": 30 * PASSES * UNLABELED_ROWS},
    )
    _check(
        checks,
        "scheduler_fixed_boundaries",
        learning_rate_multiplier(1) == 1 / 123
        and learning_rate_multiplier(123) == 1.0
        and learning_rate_multiplier(TOTAL_STEPS) == 0.1,
        {"steps": TOTAL_STEPS, "warmup": 123, "final_fraction": 0.1},
    )
    _check(
        checks,
        "development_and_protected_absent",
        all(
            fragment
            not in "\n".join(
                (project_root / "src/ipin_openppi/stage1" / filename).read_text(
                    encoding="utf-8"
                )
                for filename in (
                    "baselines.py",
                    "embeddings.py",
                    "models.py",
                    "objective.py",
                    "preparation.py",
                    "support.py",
                    "training.py",
                )
            )
            for fragment in ("development_release.cms", "protected_candidates.cms", "protected_truth.cms")
        ),
        "no sealed package filename in executable Stage 1 modules",
    )
    failures = [record for record in checks if record["status"] != "pass"]
    payload = {
        "checks": checks,
        "code_commit": git_commit(project_root),
        "protocol_configuration_sha256": PROTOCOL_CONFIGURATION_SHA256,
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "summary": {"fail": len(failures), "pass": len(checks) - len(failures), "warning": 0},
    }
    atomic_json(output, payload)
    if failures:
        raise RuntimeError(f"Stage 1 implementation audit failed: {failures}")
    return payload
