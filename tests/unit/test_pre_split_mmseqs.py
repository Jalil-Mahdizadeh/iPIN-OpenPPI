from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb
import pyarrow.parquet as pq
import pytest

from ipin_openppi.pre_split_audit.pipeline import (
    _normalize_search,
    _run_similarity_searches,
)
from ipin_openppi.pre_split_audit.support import load_yaml


CONFIG = Path("configs/pre_split_feasibility_and_leakage_stress_test_v1.yaml")
BINARY = Path("artifacts/cache/tools/mmseqs2/18-8cc5c/mmseqs/bin/mmseqs")


@pytest.mark.skipif(not BINARY.is_file(), reason="pinned MMseqs2 cache not prepared")
def test_separately_parameterized_searches_and_exact_normalization(tmp_path: Path) -> None:
    config = load_yaml(CONFIG)
    sequence_a = "ACDEFGHIKLMNPQRSTVWY" * 5
    sequence_b = sequence_a[:49] + "V" + sequence_a[50:]
    sequence_c = "YWVTSRQPNMLKIHGFEDCA" * 5
    sequences = [sequence_a, sequence_b, sequence_c]
    hashes = [hashlib.sha256(sequence.encode("ascii")).hexdigest() for sequence in sequences]
    fasta = tmp_path / "fixture.fasta"
    fasta.write_text(
        "".join(f">{digest}\n{sequence}\n" for digest, sequence in zip(hashes, sequences)),
        encoding="ascii",
    )
    run_root = tmp_path / "run"
    run_root.mkdir()
    full_raw, local_raw, logs = _run_similarity_searches(
        project_root=Path.cwd(),
        temporary_run=run_root,
        fasta_path=fasta,
        binary=BINARY.resolve(strict=True),
        config=config,
    )
    assert [record["step"] for record in logs] == [
        "createdb",
        "full_length_sensitivity_search",
        "full_length_sensitivity_convertalis",
        "local_domain_sensitivity_search",
        "local_domain_sensitivity_convertalis",
    ]

    connection = duckdb.connect(":memory:")
    try:
        full_path = run_root / "full.parquet"
        local_path = run_root / "local.parquet"
        full = _normalize_search(
            connection=connection,
            raw_path=full_raw,
            normalized_path=full_path,
            sequence_lengths=dict(zip(hashes, map(len, sequences))),
            minimum_identity=0.20,
            minimum_coverage=0.80,
            minimum_span=0,
            maximum_evalue=1e100,
        )
        local = _normalize_search(
            connection=connection,
            raw_path=local_raw,
            normalized_path=local_path,
            sequence_lengths=dict(zip(hashes, map(len, sequences))),
            minimum_identity=0.20,
            minimum_coverage=0.20,
            minimum_span=80,
            maximum_evalue=0.001,
        )
    finally:
        connection.close()
    assert full["structurally_invalid_records"] == 0
    assert local["structurally_invalid_records"] == 0
    assert full["self_match_query_sequences"] == 3
    assert local["self_match_query_sequences"] == 3
    expected = tuple(sorted((hashes[0], hashes[1])))
    full_pairs = {
        (row["sequence_a_sha256"], row["sequence_b_sha256"])
        for row in pq.read_table(full_path).to_pylist()
    }
    local_pairs = {
        (row["sequence_a_sha256"], row["sequence_b_sha256"])
        for row in pq.read_table(local_path).to_pylist()
    }
    assert expected in full_pairs
    assert expected in local_pairs
