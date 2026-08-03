from __future__ import annotations

import duckdb
import pytest

from ipin_openppi.reconciliation.candidate_sql import build_candidate_relations
from ipin_openppi.reconciliation.participant_mapping_sql import (
    build_participant_mapping_relation,
)
from ipin_openppi.reconciliation.pipeline import (
    _iter_manifest_files,
    _require_scoped_nonproduction_output,
)
from ipin_openppi.reconciliation.policy import ReconciliationProvenance


PRIORITY = {
    "direct_uniprot_exact": 1,
    "direct_uniprot_isoform1_alias": 2,
    "ensembl_protein": 3,
    "ensembl_transcript": 4,
    "ensembl_gene": 5,
}
DATABASES = {
    "ensembl_protein": "Ensembl_PRO",
    "ensembl_transcript": "Ensembl_TRS",
    "ensembl_gene": "Ensembl",
}


def test_nonproduction_overrides_require_scoped_smoke_output(tmp_path) -> None:
    with pytest.raises(RuntimeError, match=r"_smoke_\*"):
        _require_scoped_nonproduction_output(
            output_root=None,
            allow_dirty=True,
            skip_staging_sha256=False,
        )
    with pytest.raises(RuntimeError, match=r"_smoke_\*"):
        _require_scoped_nonproduction_output(
            output_root=tmp_path / "production",
            allow_dirty=False,
            skip_staging_sha256=True,
        )
    _require_scoped_nonproduction_output(
        output_root=tmp_path / "_smoke_mapping",
        allow_dirty=True,
        skip_staging_sha256=True,
    )


def test_manifest_file_discovery_stops_at_table_summary() -> None:
    report = {
        "source": {
            "table": "records",
            "rows": 1,
            "files": [{"path": "part.parquet"}],
            "schema_name": "schema",
            "schema_version": 1,
            "schema_sha256": "a" * 64,
            "nested": {"files": [{"path": "must-not-be-seen"}]},
        }
    }
    assert list(_iter_manifest_files(report)) == [{"path": "part.parquet"}]


def _fixture_connection() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE participants (
            source_key VARCHAR,
            participant_id VARCHAR,
            evidence_id VARCHAR,
            participant_ordinal INTEGER,
            taxid BIGINT,
            molecule_type_ac VARCHAR,
            molecule_type_name VARCHAR,
            raw_uniprot_accessions VARCHAR[],
            raw_ensembl_gene_ids VARCHAR[],
            raw_ensembl_transcript_ids VARCHAR[],
            raw_ensembl_protein_ids VARCHAR[],
            raw_orf_ids VARCHAR[],
            raw_file_path VARCHAR,
            raw_locator VARCHAR
        )
        """
    )
    rows = [
        (
            "huri",
            "p-direct",
            "e-direct",
            1,
            9606,
            "MI:0326",
            "protein",
            ["P1"],
            [],
            [],
            [],
            [],
            "raw.tsv",
            "row:1",
        ),
        (
            "huri",
            "p-alias",
            "e-alias",
            1,
            9606,
            "MI:0326",
            "protein",
            ["P2-1"],
            [],
            [],
            [],
            [],
            "raw.tsv",
            "row:2",
        ),
        (
            "huri",
            "p-canonical-only",
            "e-canonical-only",
            1,
            9606,
            "MI:0326",
            "protein",
            [],
            ["ENSG3.7"],
            [],
            [],
            [],
            "raw.tsv",
            "row:3",
        ),
        (
            "huri",
            "p-unmapped",
            "e-unmapped",
            1,
            9606,
            "MI:0326",
            "protein",
            ["MISSING"],
            [],
            [],
            [],
            [],
            "raw.tsv",
            "row:4",
        ),
        (
            "intact_imex",
            "p-small-molecule",
            "e-small-molecule",
            1,
            9606,
            "MI:0328",
            "small molecule",
            ["P1"],
            [],
            [],
            [],
            [],
            "raw.xml",
            "entry:5",
        ),
    ]
    connection.executemany(
        "INSERT INTO participants VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    connection.execute(
        """
        CREATE TABLE evidence (
            evidence_id VARCHAR,
            source_key VARCHAR,
            source_dataset VARCHAR,
            source_release VARCHAR
        )
        """
    )
    connection.executemany(
        "INSERT INTO evidence VALUES (?, ?, ?, ?)",
        [(row[2], row[0], "fixture", "fixture_release") for row in rows],
    )
    connection.execute(
        """
        CREATE TABLE participant_features (
            participant_id VARCHAR,
            start_position BIGINT,
            end_position BIGINT,
            original_sequence VARCHAR,
            resulting_sequence VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE sequences (
            sequence_id VARCHAR,
            uniprot_accession VARCHAR,
            isoform_id VARCHAR,
            sequence_sha256 VARCHAR,
            sequence_length BIGINT,
            sequence_view VARCHAR,
            canonical BOOLEAN
        )
        """
    )
    connection.executemany(
        "INSERT INTO sequences VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("P1", "P1", None, "1" * 64, 10, "canonical", True),
            ("P2", "P2", None, "2" * 64, 20, "canonical", True),
            ("P3", "P3", None, "3" * 64, 30, "canonical", True),
            ("I3A", "P3", "I3A", "4" * 64, 25, "additional_isoform", False),
            ("I3B", "P3", "I3B", "5" * 64, 28, "additional_isoform", False),
        ],
    )
    connection.execute(
        """
        CREATE TABLE identifier_mappings (
            database VARCHAR,
            identifier_versionless VARCHAR,
            uniprot_accession VARCHAR
        )
        """
    )
    connection.executemany(
        "INSERT INTO identifier_mappings VALUES (?, ?, ?)",
        [("Ensembl", "ENSG3", "I3A"), ("Ensembl", "ENSG3", "I3B")],
    )
    return connection


def test_participant_mapping_uses_derived_states_not_staging_placeholders() -> None:
    connection = _fixture_connection()
    try:
        build_candidate_relations(connection, PRIORITY, DATABASES)
        build_participant_mapping_relation(
            connection,
            ReconciliationProvenance(
                parse_manifest_sha256="a" * 64,
                version="0.1.0",
                git_commit="b" * 40,
                container_sif_sha256="c" * 64,
                schema_version=1,
                schema_sha256="d" * 64,
                frozen_taxid=9606,
                protein_molecule_type_ac="MI:0326",
                sifts_declared_uniprot_release="2026.03",
                frozen_uniprot_release="2026_02",
            ),
        )
        observed = dict(
            connection.execute(
                """
                SELECT participant_id, mapping_state
                FROM participant_sequence_mappings_work
                """
            ).fetchall()
        )
        assert observed == {
            "p-direct": "direct_identifier_unique",
            "p-alias": "canonical_isoform_alias_unique",
            "p-canonical-only": "canonical_projection_only",
            "p-unmapped": "unmapped",
            "p-small-molecule": "not_applicable",
        }
        assert (
            connection.execute(
                """
            SELECT count(*) FROM participant_sequence_mappings_work
            WHERE strict_construct_eligible OR label_authorized
               OR construct_confidence IN ('A', 'B')
            """
            ).fetchone()[0]
            == 0
        )
    finally:
        connection.close()
