from __future__ import annotations

import json
from pathlib import Path

import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.pair_artifacts.construction import _candidate_token
from ipin_openppi.pair_artifacts.evaluator import (
    _project_scorer_inputs,
    _require_private_workspace,
    _require_regular,
    _write_exclusive_json,
    validate_prediction_rows,
    weighted_pairwise_concordance,
)
from ipin_openppi.pair_artifacts.support import deterministic_tar, rational_design


def test_rational_design_and_candidate_token_are_exact() -> None:
    assert rational_design(10, 4) == (2, 5, 5, 2)
    first = _candidate_token("C1_test", "pair:" + "a" * 64)
    second = _candidate_token("C1_test", "pair:" + "a" * 64)
    assert first == second
    assert first.startswith("candidate:")
    assert len(first) == len("candidate:") + 64


def test_prediction_validation_is_complete_unique_and_finite() -> None:
    assert validate_prediction_rows(
        ["candidate:a", "candidate:b"],
        [("candidate:a", 0.1), ("candidate:b", -2.0)],
    ) == {"candidate:a": 0.1, "candidate:b": -2.0}
    with pytest.raises(RuntimeError, match="duplicate=1"):
        validate_prediction_rows(
            ["candidate:a"],
            [("candidate:a", 0.1), ("candidate:a", 0.2)],
        )
    with pytest.raises(RuntimeError, match="nonfinite=1"):
        validate_prediction_rows(["candidate:a"], [("candidate:a", float("nan"))])
    with pytest.raises(RuntimeError, match="missing=1"):
        validate_prediction_rows(["candidate:a", "candidate:b"], [("candidate:a", 0.1)])


def test_weighted_pairwise_concordance_uses_half_ties() -> None:
    observed = weighted_pairwise_concordance(
        positive_scores=[0.0, 1.0],
        unlabeled_scores=[0.0, 0.5, 1.0],
        unlabeled_weights=[1.0, 2.0, 1.0],
    )
    assert observed == pytest.approx(0.5)
    with pytest.raises(ValueError):
        weighted_pairwise_concordance([], [0.0], [1.0])


def test_deterministic_tar_is_byte_reproducible_and_sorted(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    (source / "z").mkdir(parents=True)
    (source / "a").mkdir()
    (source / "z" / "part.txt").write_text("z", encoding="utf-8")
    (source / "a" / "part.txt").write_text("a", encoding="utf-8")
    first = tmp_path / "first.tar"
    second = tmp_path / "second.tar"
    assert deterministic_tar(source, first) == deterministic_tar(source, second)
    assert sha256_file(first) == sha256_file(second)


def test_scorer_projection_discards_evaluator_only_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    parts = source / "protected_candidates"
    parts.mkdir(parents=True)
    pq.write_table(
        pa.table(
            {
                "candidate_token": ["candidate:a", "candidate:b"],
                "endpoint_a_sha256": ["a" * 64, "b" * 64],
                "endpoint_b_sha256": ["c" * 64, "d" * 64],
                "cell_id": ["C1_test", "C2_test"],
                "endpoint_a_training_degree": [1, 2],
                "stratum_id": ["1|2", "2|3"],
            }
        ),
        parts / "part-00000.parquet",
    )
    output = tmp_path / "projection"
    summary = _project_scorer_inputs(source_root=source, target_root=output)
    assert summary["columns"] == [
        "candidate_token",
        "endpoint_a_sha256",
        "endpoint_b_sha256",
        "cell_id",
    ]
    assert summary["rows"] == 2
    assert (
        pq.ParquetFile(output / "part-00000.parquet").schema_arrow.names
        == summary["columns"]
    )


def test_evaluator_rejects_lexical_symlinks(tmp_path: Path) -> None:
    regular = tmp_path / "regular.bin"
    regular.write_bytes(b"frozen")
    linked = tmp_path / "linked.bin"
    linked.symlink_to(regular)
    with pytest.raises(RuntimeError, match="Symbolic-link"):
        _require_regular(linked)

    project = tmp_path / "project"
    private = project / ".private"
    private.mkdir(parents=True, mode=0o700)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    session_link = private / "session"
    session_link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="Symbolic-link"):
        _require_private_workspace(project, session_link, exists=True)


def test_one_first_record_is_exclusive_and_preserves_first_write(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "ledger.json"
    first = {"status": "reserved"}
    _write_exclusive_json(ledger, first)
    with pytest.raises(RuntimeError, match="already exists"):
        _write_exclusive_json(ledger, {"status": "retry"})
    assert json.loads(ledger.read_text(encoding="utf-8")) == first
