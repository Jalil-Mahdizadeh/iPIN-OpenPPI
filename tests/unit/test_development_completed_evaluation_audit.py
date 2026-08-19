from __future__ import annotations

from pathlib import Path

import numpy as np

from ipin_openppi.development_evaluation.completed_audit import (
    contains_public_pair_identity,
    ensemble_columns_exact,
    scoring_manifest_census,
)


def test_completed_audit_rejects_public_pair_or_endpoint_identity(tmp_path: Path) -> None:
    aggregate = tmp_path / "aggregate.json"
    aggregate.write_text('{"metric": 0.6}\n', encoding="utf-8")
    assert contains_public_pair_identity(aggregate) is False
    aggregate.write_text('{"pair": "pair:' + "a" * 64 + '"}\n', encoding="utf-8")
    assert contains_public_pair_identity(aggregate) is True
    aggregate.write_text('{"endpoint_a_sha256": "secret"}\n', encoding="utf-8")
    assert contains_public_pair_identity(aggregate) is True


def test_completed_audit_checks_every_ensemble_column_exactly() -> None:
    members = np.asarray(
        [
            [0.1, 0.4, 0.7],
            [0.2, 0.5, 0.8],
        ],
        dtype=np.float64,
    )
    scores = np.column_stack((members, np.mean(members, axis=1, dtype=np.float64)))
    scorer_index = {"run_a": 0, "run_b": 1, "run_c": 2, "candidate": 3}
    ensembles = [
        {
            "candidate_id": "candidate",
            "members": [{"run_id": "run_a"}, {"run_id": "run_b"}, {"run_id": "run_c"}],
        }
    ]
    assert ensemble_columns_exact(scores, scorer_index, ensembles) is True
    changed = scores.copy()
    changed[1, 3] += 1e-12
    assert ensemble_columns_exact(changed, scorer_index, ensembles) is False


def test_scoring_census_excludes_release_support_tables() -> None:
    positive_rows = [2265, 312, 1677, 11327, 1601, 4751, 3259, 305, 611]
    cells = [
        {
            "positive_rows": count,
            "unlabeled_rows": 1_000_000,
            "total_rows": 1_000_000 + count,
        }
        for count in positive_rows
    ]
    assert scoring_manifest_census(cells) == {
        "positive_rows": 26_108,
        "unlabeled_rows": 9_000_000,
        "total_rows": 9_026_108,
    }
    release_support_rows = 18_081 + 134
    assert 9_026_108 + release_support_rows == 9_044_323
