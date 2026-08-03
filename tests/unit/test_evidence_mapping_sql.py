from __future__ import annotations

import duckdb

from ipin_openppi.reconciliation.evidence_mapping_sql import (
    build_evidence_mapping_relation,
)
from ipin_openppi.reconciliation.policy import ReconciliationProvenance


def test_null_molecule_annotation_produces_zero_not_null_counts() -> None:
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE evidence (
                evidence_id VARCHAR,
                source_key VARCHAR,
                source_dataset VARCHAR,
                source_release VARCHAR,
                record_kind VARCHAR,
                interaction_semantics VARCHAR,
                observation_state VARCHAR,
                participant_count INTEGER,
                original_nary BOOLEAN
            )
            """
        )
        connection.execute(
            """
            INSERT INTO evidence VALUES (
                'e-null-type', 'intact_imex', 'fixture', 'fixture_release',
                'interaction', 'binary', 'reported_interaction', 1, false
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE participant_sequence_mappings_work (
                evidence_id VARCHAR,
                source_key VARCHAR,
                participant_ordinal INTEGER,
                molecule_type_ac VARCHAR,
                mapping_applicability VARCHAR,
                reference_sequence_usable BOOLEAN,
                canonical_projection_usable BOOLEAN,
                mapping_state VARCHAR,
                mapped_sequence_sha256 VARCHAR,
                canonical_projection_sequence_sha256 VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO participant_sequence_mappings_work VALUES (
                'e-null-type', 'intact_imex', 1, NULL,
                'unresolved_entity_type', false, false, 'unresolved',
                NULL, NULL
            )
            """
        )

        build_evidence_mapping_relation(
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

        row = connection.execute(
            """
            SELECT
                protein_participant_count,
                human_protein_count,
                reference_mapped_count,
                canonical_projectable_count,
                ambiguous_count,
                unmapped_count,
                out_of_scope_count,
                not_applicable_count,
                unresolved_count,
                binary_two_human_proteins,
                reference_pair_usable,
                canonical_pair_usable
            FROM evidence_mapping_summaries_work
            """
        ).fetchone()
        assert row == (0, 0, 0, 0, 0, 0, 0, 0, 1, False, False, False)
    finally:
        connection.close()
