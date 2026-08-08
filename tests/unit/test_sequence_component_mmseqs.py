from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb
import pyarrow.parquet as pq
import pytest

from ipin_openppi.sequence_component_audit.pipeline import (
    _normalize_alignments,
    _run_mmseqs,
    _write_fasta,
)
from ipin_openppi.sequence_component_audit.support import load_yaml
from ipin_openppi.validation.sequence_components import _parse_alignments_independently
from ipin_openppi.validation.staging import Checks


CONFIG_PATH = Path(
    "configs/benchmark_eligibility_and_sequence_component_audit_v1.yaml"
)
BINARY_PATH = Path(
    "artifacts/cache/tools/mmseqs2/18-8cc5c/mmseqs/bin/mmseqs"
)


@pytest.mark.skipif(not BINARY_PATH.is_file(), reason="pinned MMseqs2 cache not prepared")
def test_pinned_mmseqs_real_binary_and_exact_normalization(tmp_path: Path) -> None:
    config = load_yaml(CONFIG_PATH)
    sequence_a = "ACDEFGHIKLMNPQRSTVWY" * 5
    sequence_b = sequence_a[:49] + "V" + sequence_a[50:]
    sequence_c = "YWVTSRQPNMLKIHGFEDCA" * 5
    sequences = [sequence_a, sequence_b, sequence_c]
    rows = [
        {
            "reference_sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
            "sequence_length": len(sequence),
            "sequence": sequence,
        }
        for sequence in sequences
    ]
    run_root = tmp_path / "run"
    run_root.mkdir()
    fasta = run_root / "fixture.fasta"
    _write_fasta(fasta, rows)
    alignment, logs = _run_mmseqs(
        project_root=Path.cwd(),
        temporary_run=run_root,
        fasta_path=fasta,
        binary=BINARY_PATH.resolve(strict=True),
        config=config,
    )
    assert [record["step"] for record in logs] == [
        "createdb",
        "search",
        "convertalis",
    ]
    connection = duckdb.connect(":memory:")
    try:
        normalized = run_root / "normalized.parquet"
        metrics = _normalize_alignments(
            connection=connection,
            alignment_path=alignment,
            normalized_path=normalized,
            sequence_rows=rows,
            config=config,
        )
    finally:
        connection.close()
    assert metrics["self_match_query_sequences"] == 3
    checks = Checks()
    independent_edges, independent_metrics = _parse_alignments_independently(
        checks,
        alignment,
        normalized,
        {row["reference_sequence_sha256"]: row["sequence_length"] for row in rows},
        config,
    )
    assert checks.passed
    assert independent_metrics == metrics
    assert metrics["identity_uses_integer_derived_identical_over_alnlen"] is True
    normalized_rows = pq.read_table(normalized).to_pylist()
    identical_pair = tuple(
        sorted((rows[0]["reference_sequence_sha256"], rows[1]["reference_sequence_sha256"]))
    )
    matches = [
        row
        for row in normalized_rows
        if (row["sequence_a_sha256"], row["sequence_b_sha256"])
        == identical_pair
    ]
    assert len(matches) == 1
    assert matches[0]["maximum_identity"] == 0.99
    assert matches[0]["maximum_minimum_endpoint_coverage"] == 1.0
