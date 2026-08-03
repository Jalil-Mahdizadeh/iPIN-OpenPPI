"""Evidence-level sequence-mapping coverage and pair projection relation."""

from __future__ import annotations

import duckdb

from .policy import ReconciliationProvenance, sql_string


def build_evidence_mapping_relation(
    connection: duckdb.DuckDBPyConnection,
    provenance: ReconciliationProvenance,
) -> None:
    parse_sha = sql_string(provenance.parse_manifest_sha256)
    version = sql_string(provenance.version)
    git_commit = sql_string(provenance.git_commit)
    container_sha = sql_string(provenance.container_sif_sha256)
    schema_sha = sql_string(provenance.schema_sha256)
    protein_ac = sql_string(provenance.protein_molecule_type_ac)

    connection.execute(
        f"""
        CREATE TEMP TABLE evidence_mapping_summaries_work AS
        WITH aggregate AS (
            SELECT
                evidence.evidence_id,
                evidence.source_key,
                evidence.source_dataset,
                evidence.source_release,
                evidence.record_kind,
                evidence.interaction_semantics,
                evidence.observation_state,
                evidence.participant_count,
                evidence.original_nary,
                count(*) FILTER (
                    WHERE mapping.molecule_type_ac = {protein_ac}
                )::INTEGER AS protein_participant_count,
                count(*) FILTER (
                    WHERE mapping.mapping_applicability = 'human_protein'
                )::INTEGER AS human_protein_count,
                count(*) FILTER (
                    WHERE mapping.reference_sequence_usable
                )::INTEGER AS reference_mapped_count,
                count(*) FILTER (
                    WHERE mapping.canonical_projection_usable
                )::INTEGER AS canonical_projectable_count,
                count(*) FILTER (
                    WHERE mapping.mapping_state = 'ambiguous'
                )::INTEGER AS ambiguous_count,
                count(*) FILTER (
                    WHERE mapping.mapping_state = 'unmapped'
                )::INTEGER AS unmapped_count,
                count(*) FILTER (
                    WHERE mapping.mapping_state = 'out_of_scope'
                )::INTEGER AS out_of_scope_count,
                count(*) FILTER (
                    WHERE mapping.mapping_state = 'not_applicable'
                )::INTEGER AS not_applicable_count,
                count(*) FILTER (
                    WHERE mapping.mapping_state = 'unresolved'
                )::INTEGER AS unresolved_count,
                max(CASE WHEN mapping.participant_ordinal = 1
                    THEN mapping.mapped_sequence_sha256 END) AS reference_hash_a,
                max(CASE WHEN mapping.participant_ordinal = 2
                    THEN mapping.mapped_sequence_sha256 END) AS reference_hash_b,
                max(CASE WHEN mapping.participant_ordinal = 1
                    THEN mapping.canonical_projection_sequence_sha256 END)
                    AS canonical_hash_a,
                max(CASE WHEN mapping.participant_ordinal = 2
                    THEN mapping.canonical_projection_sequence_sha256 END)
                    AS canonical_hash_b
            FROM evidence
            JOIN participant_sequence_mappings_work AS mapping
              ON mapping.evidence_id = evidence.evidence_id
             AND mapping.source_key = evidence.source_key
            GROUP BY
                evidence.evidence_id,
                evidence.source_key,
                evidence.source_dataset,
                evidence.source_release,
                evidence.record_kind,
                evidence.interaction_semantics,
                evidence.observation_state,
                evidence.participant_count,
                evidence.original_nary
        ),
        classified AS (
            SELECT
                aggregate.*,
                participant_count = 2 AND human_protein_count = 2
                    AS binary_two_human_proteins,
                human_protein_count > 0
                    AND reference_mapped_count = human_protein_count
                    AS all_human_proteins_reference_resolved,
                human_protein_count > 0
                    AND canonical_projectable_count = human_protein_count
                    AS all_human_proteins_canonical_projectable,
                participant_count = 2 AND human_protein_count = 2
                    AND reference_mapped_count = 2 AS reference_pair_usable,
                participant_count = 2 AND human_protein_count = 2
                    AND canonical_projectable_count = 2 AS canonical_pair_usable
            FROM aggregate
        )
        SELECT
            concat('evidence-map:', substr(sha256(evidence_id), 1, 32))
                AS mapping_summary_id,
            evidence_id,
            source_key,
            source_dataset,
            source_release,
            record_kind,
            interaction_semantics,
            observation_state,
            participant_count::INTEGER AS participant_count,
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
            all_human_proteins_reference_resolved,
            all_human_proteins_canonical_projectable,
            reference_pair_usable,
            canonical_pair_usable,
            CASE WHEN reference_pair_usable THEN concat(
                'reference-unordered:', substr(sha256(concat(
                    least(reference_hash_a, reference_hash_b), '|',
                    greatest(reference_hash_a, reference_hash_b)
                )), 1, 32)) END AS mapped_unordered_sequence_pair_id,
            CASE WHEN reference_pair_usable THEN concat(
                'reference-ordered:', substr(sha256(concat(
                    reference_hash_a, '|', reference_hash_b
                )), 1, 32)) END AS mapped_ordered_sequence_pair_id,
            CASE WHEN canonical_pair_usable THEN concat(
                'canonical-unordered:', substr(sha256(concat(
                    least(canonical_hash_a, canonical_hash_b), '|',
                    greatest(canonical_hash_a, canonical_hash_b)
                )), 1, 32)) END AS canonical_unordered_sequence_pair_id,
            CASE WHEN canonical_pair_usable THEN concat(
                'canonical-ordered:', substr(sha256(concat(
                    canonical_hash_a, '|', canonical_hash_b
                )), 1, 32)) END AS canonical_ordered_sequence_pair_id,
            false AS strict_construct_eligible,
            original_nary,
            false AS label_authorized,
            {parse_sha} AS input_parse_manifest_sha256,
            {version} AS reconciliation_version,
            {git_commit} AS reconciliation_git_commit,
            {container_sha} AS container_sif_sha256,
            {provenance.schema_version}::INTEGER AS schema_version,
            {schema_sha} AS schema_sha256
        FROM classified
        """
    )
