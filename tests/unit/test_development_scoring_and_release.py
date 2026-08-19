from __future__ import annotations

import inspect
import json
import os
from pathlib import Path

import numpy as np
import pyarrow as pa
import pytest
import torch

from ipin_openppi.development_evaluation.release import (
    resolve_development_key_only,
    sha256_file,
)
from ipin_openppi.development_evaluation.scoring import (
    load_cell_rows,
    optimized_checkpoint_scores,
    validate_degree_metadata,
)
from ipin_openppi.stage1.models import build_model


@pytest.mark.parametrize(
    ("family", "dimension", "dropout"),
    [
        ("lightweight_esm2_150m_linear", 640, 0.0),
        ("esm2_650m_linear_ablation", 1280, 0.0),
        ("esm2_650m_nonlinear_no_gate_ablation", 1280, 0.1),
        ("esm2_650m_partner_gated_primary", 1280, 0.1),
    ],
)
def test_optimized_checkpoint_scorer_matches_frozen_model(
    family: str, dimension: int, dropout: float
) -> None:
    generator = torch.Generator().manual_seed(31)
    embeddings = torch.randn((11, dimension), generator=generator)
    embeddings += 0.2
    pair_a = np.asarray([0, 3, 7, 9, 4], dtype=np.int32)
    pair_b = np.asarray([2, 8, 1, 5, 10], dtype=np.int32)
    model = build_model(family, dropout=dropout, seed=20260803).eval()
    with torch.inference_mode():
        expected = model(embeddings[pair_a], embeddings[pair_b]).numpy()
        swapped = model(embeddings[pair_b], embeddings[pair_a]).numpy()
    observed = optimized_checkpoint_scores(
        family=family,
        state=model.state_dict(),
        embeddings=embeddings,
        pair_a=pair_a,
        pair_b=pair_b,
    )
    np.testing.assert_allclose(observed, expected, rtol=0, atol=0)
    np.testing.assert_allclose(observed, swapped, rtol=0, atol=0)


def test_development_key_resolver_only_names_and_resolves_one_key(tmp_path: Path) -> None:
    private = tmp_path / ".private"
    key_root = private / "pair_level_pu_r_benchmark_artifacts_v1"
    key_root.mkdir(parents=True)
    os.chmod(private, 0o700)
    os.chmod(key_root, 0o700)
    key = key_root / "development_release_private.pem"
    key.write_text("fixture-only", encoding="utf-8")
    os.chmod(key, 0o600)
    sibling = key_root / "unrelated.pem"
    sibling.write_text("must-not-be-resolved", encoding="utf-8")
    os.chmod(sibling, 0o000)
    observed = resolve_development_key_only(
        tmp_path,
        ".private/pair_level_pu_r_benchmark_artifacts_v1/development_release_private.pem",
    )
    assert observed == key.resolve()
    assert sha256_file(observed) == sha256_file(key)
    source = inspect.getsource(resolve_development_key_only)
    assert "private_key_paths" not in source
    assert "unrelated.pem" not in source


def test_development_key_resolver_rejects_any_other_path(tmp_path: Path) -> None:
    (tmp_path / ".private").mkdir(mode=0o700)
    with pytest.raises(RuntimeError, match="differs from DEC-0032"):
        resolve_development_key_only(tmp_path, ".private/something_else.pem")


def test_issue_0009_permissive_concat_changes_only_nullability_metadata() -> None:
    strict = pa.Table.from_arrays(
        [pa.array([1, 2], type=pa.int64())],
        schema=pa.schema([pa.field("value", pa.int64(), nullable=False)]),
    )
    nullable = pa.Table.from_arrays(
        [pa.array([3, 4], type=pa.int64())],
        schema=pa.schema([pa.field("value", pa.int64(), nullable=True)]),
    )
    observed = pa.concat_tables([strict, nullable], promote_options="permissive")
    assert observed.schema.names == ["value"]
    assert observed.schema.field("value").type == pa.int64()
    assert observed["value"].to_pylist() == [1, 2, 3, 4]
    assert observed.num_rows == strict.num_rows + nullable.num_rows
    assert 'pa.concat_tables(tables, promote_options="permissive")' in inspect.getsource(
        load_cell_rows
    )


def _degree_rows(strata: list[str] | None = None) -> pa.Table:
    return pa.table(
        {
            "endpoint_a_training_degree": np.asarray([1, 0], dtype=np.int64),
            "endpoint_b_training_degree": np.asarray([0, 2], dtype=np.int64),
            "stratum_id": strata or ["0|1", "0|2"],
        }
    )


def test_issue_0010_primary_degree_metadata_requires_pooled_graph_identity() -> None:
    validate_degree_metadata(
        cell_id="C2_development",
        rows=_degree_rows(),
        pooled_degree_a=np.asarray([1, 0], dtype=np.int64),
        pooled_degree_b=np.asarray([0, 2], dtype=np.int64),
    )
    with pytest.raises(RuntimeError, match="primary development degree metadata"):
        validate_degree_metadata(
            cell_id="C2_development",
            rows=_degree_rows(),
            pooled_degree_a=np.asarray([12, 0], dtype=np.int64),
            pooled_degree_b=np.asarray([0, 25], dtype=np.int64),
        )


def test_issue_0010_source_design_degree_is_validated_by_frozen_stratum() -> None:
    validate_degree_metadata(
        cell_id="source_exclusive:HI-II-14:C2_development",
        rows=_degree_rows(),
        pooled_degree_a=np.asarray([12, 0], dtype=np.int64),
        pooled_degree_b=np.asarray([0, 25], dtype=np.int64),
    )
    with pytest.raises(RuntimeError, match="differs from frozen stratum"):
        validate_degree_metadata(
            cell_id="source_exclusive:HI-II-14:C2_development",
            rows=_degree_rows(["0|2", "0|2"]),
            pooled_degree_a=np.asarray([12, 0], dtype=np.int64),
            pooled_degree_b=np.asarray([0, 25], dtype=np.int64),
        )
