"""Participant-level sequence mapping and construct-confidence relation."""

from __future__ import annotations

import duckdb

from .policy import ReconciliationProvenance, sql_string


def build_participant_mapping_relation(
    connection: duckdb.DuckDBPyConnection,
    provenance: ReconciliationProvenance,
) -> None:
    parse_sha = sql_string(provenance.parse_manifest_sha256)
    version = sql_string(provenance.version)
    git_commit = sql_string(provenance.git_commit)
    container_sha = sql_string(provenance.container_sif_sha256)
    schema_sha = sql_string(provenance.schema_sha256)
    protein_ac = sql_string(provenance.protein_molecule_type_ac)
    human_taxid = int(provenance.frozen_taxid)

    connection.execute(
        f"""
        CREATE TEMP TABLE participant_sequence_mappings_work AS
        WITH base AS (
            SELECT
                participant.participant_id,
                participant.evidence_id,
                participant.source_key,
                evidence.source_dataset,
                evidence.source_release,
                participant.participant_ordinal,
                participant.taxid,
                participant.molecule_type_ac,
                participant.molecule_type_name,
                participant.raw_uniprot_accessions,
                participant.raw_ensembl_gene_ids,
                participant.raw_ensembl_transcript_ids,
                participant.raw_ensembl_protein_ids,
                participant.raw_orf_ids,
                participant.raw_file_path,
                participant.raw_locator,
                coalesce(feature.feature_count, 0)::BIGINT AS feature_count,
                coalesce(feature.ranged_feature_count, 0)::BIGINT
                    AS ranged_feature_count,
                coalesce(feature.sequence_change_feature_count, 0)::BIGINT
                    AS sequence_change_feature_count,
                CASE
                    WHEN participant.molecule_type_ac IS NULL
                        THEN 'unresolved_entity_type'
                    WHEN participant.molecule_type_ac <> {protein_ac}
                        THEN 'nonprotein_entity'
                    WHEN participant.taxid IS NULL OR participant.taxid <= 0
                        THEN 'unresolved_taxon_protein'
                    WHEN participant.taxid <> {human_taxid}
                        THEN 'nonhuman_protein'
                    ELSE 'human_protein'
                END AS mapping_applicability,
                coalesce(selected.route, 'none') AS selected_route,
                coalesce(selected.candidate_sequence_ids, []::VARCHAR[])
                    AS candidate_sequence_ids,
                coalesce(selected.candidate_sequence_sha256s, []::VARCHAR[])
                    AS candidate_sequence_sha256s,
                coalesce(selected.candidate_parent_accessions, []::VARCHAR[])
                    AS candidate_parent_accessions,
                coalesce(selected.candidate_sequence_count, 0)::INTEGER
                    AS candidate_sequence_count,
                coalesce(selected.candidate_hash_count, 0)::INTEGER
                    AS candidate_hash_count,
                coalesce(selected.candidate_parent_count, 0)::INTEGER
                    AS candidate_parent_count,
                selected.priority,
                selected.single_sequence_id,
                selected.single_parent_accession,
                selected.single_isoform_id,
                selected.single_sequence_sha256,
                selected.single_sequence_length,
                selected.single_sequence_view,
                canonical.sequence_sha256 AS canonical_sequence_sha256
            FROM participants AS participant
            JOIN evidence
              ON evidence.evidence_id = participant.evidence_id
             AND evidence.source_key = participant.source_key
            LEFT JOIN feature_summary AS feature
              ON feature.participant_id = participant.participant_id
            LEFT JOIN selected_candidate_summary AS selected
              ON selected.source_key = participant.source_key
             AND selected.participant_id = participant.participant_id
            LEFT JOIN canonical_sequences AS canonical
              ON selected.candidate_parent_count = 1
             AND canonical.uniprot_accession = selected.single_parent_accession
        ),
        classified AS (
            SELECT
                base.*,
                CASE
                    WHEN mapping_applicability = 'nonprotein_entity'
                        THEN 'not_applicable'
                    WHEN mapping_applicability = 'unresolved_entity_type'
                        THEN 'unresolved'
                    WHEN mapping_applicability = 'nonhuman_protein'
                        THEN 'out_of_scope'
                    WHEN mapping_applicability = 'unresolved_taxon_protein'
                        THEN 'unresolved'
                    WHEN candidate_sequence_count = 0
                        THEN 'unmapped'
                    WHEN candidate_sequence_count = 1 AND priority = 1
                        THEN 'direct_identifier_unique'
                    WHEN candidate_sequence_count = 1 AND priority = 2
                        THEN 'canonical_isoform_alias_unique'
                    WHEN candidate_sequence_count = 1
                        THEN 'cross_reference_unique'
                    WHEN candidate_hash_count = 1
                        THEN 'sequence_equivalent_candidates'
                    WHEN candidate_parent_count = 1
                         AND canonical_sequence_sha256 IS NOT NULL
                        THEN 'canonical_projection_only'
                    ELSE 'ambiguous'
                END AS resolved_mapping_state,
                mapping_applicability = 'human_protein'
                    AND candidate_hash_count = 1 AS reference_sequence_usable,
                mapping_applicability = 'human_protein'
                    AND canonical_sequence_sha256 IS NOT NULL
                    AS canonical_projection_usable
            FROM base
        ),
        confidence AS (
            SELECT
                classified.*,
                CASE
                    WHEN mapping_applicability IN (
                        'nonprotein_entity', 'nonhuman_protein'
                    ) THEN 'not_applicable'
                    WHEN resolved_mapping_state = 'unmapped' THEN 'unmapped'
                    WHEN resolved_mapping_state IN ('ambiguous', 'unresolved')
                        THEN 'D'
                    WHEN reference_sequence_usable OR canonical_projection_usable
                        THEN 'C'
                    ELSE 'D'
                END AS resolved_construct_confidence
            FROM classified
        )
        SELECT
            concat('participant-map:', substr(sha256(participant_id), 1, 32))
                AS mapping_record_id,
            participant_id,
            evidence_id,
            source_key,
            source_dataset,
            source_release,
            participant_ordinal::INTEGER AS participant_ordinal,
            taxid,
            molecule_type_ac,
            molecule_type_name,
            mapping_applicability,
            selected_route,
            resolved_mapping_state AS mapping_state,
            candidate_sequence_ids,
            candidate_sequence_sha256s,
            candidate_parent_accessions,
            candidate_sequence_count,
            candidate_hash_count,
            candidate_parent_count,
            candidate_sequence_count AS all_candidate_sequence_count,
            candidate_hash_count AS all_candidate_hash_count,
            candidate_parent_count AS all_candidate_parent_count,
            CASE WHEN reference_sequence_usable AND candidate_sequence_count = 1
                 THEN single_sequence_id END AS mapped_sequence_id,
            CASE WHEN reference_sequence_usable AND candidate_parent_count = 1
                 THEN single_parent_accession END AS mapped_uniprot_accession,
            CASE WHEN reference_sequence_usable AND candidate_sequence_count = 1
                 THEN single_isoform_id END AS mapped_isoform_id,
            CASE WHEN reference_sequence_usable
                 THEN single_sequence_sha256 END AS mapped_sequence_sha256,
            CASE WHEN reference_sequence_usable
                 THEN single_sequence_length END AS mapped_sequence_length,
            CASE WHEN reference_sequence_usable AND candidate_sequence_count = 1
                 THEN single_sequence_view END AS mapped_sequence_view,
            reference_sequence_usable,
            CASE WHEN canonical_projection_usable
                 THEN single_parent_accession END AS canonical_projection_accession,
            CASE WHEN canonical_projection_usable
                 THEN canonical_sequence_sha256 END
                 AS canonical_projection_sequence_sha256,
            canonical_projection_usable,
            raw_uniprot_accessions,
            raw_ensembl_gene_ids,
            raw_ensembl_transcript_ids,
            raw_ensembl_protein_ids,
            raw_orf_ids,
            feature_count,
            ranged_feature_count,
            sequence_change_feature_count,
            resolved_construct_confidence AS construct_confidence,
            CASE
                WHEN resolved_construct_confidence = 'C'
                 AND reference_sequence_usable
                    THEN 'reference_sequence_resolved_but_exact_construct_sequence_and_boundaries_not_reported'
                WHEN resolved_construct_confidence = 'C'
                 AND canonical_projection_usable
                    THEN 'canonical_projection_only_exact_construct_sequence_and_boundaries_not_reported'
                WHEN resolved_construct_confidence = 'D'
                    THEN 'ambiguous_or_unresolved_identifier_taxon_or_sequence_mapping'
                WHEN resolved_construct_confidence = 'unmapped'
                    THEN 'no_frozen_human_reference_sequence_candidate'
                ELSE 'construct_mapping_not_applicable_to_source_entity'
            END AS construct_confidence_basis,
            NULL::VARCHAR AS construct_sequence_sha256,
            NULL::BIGINT AS construct_start,
            NULL::BIGINT AS construct_end,
            false AS strict_construct_eligible,
            list_filter([
                CASE WHEN candidate_sequence_count > 1
                    THEN 'selected_route_multiple_sequence_ids' END,
                CASE WHEN candidate_hash_count > 1
                    THEN 'selected_route_multiple_sequence_hashes' END,
                CASE WHEN candidate_parent_count > 1
                    THEN 'selected_route_multiple_parent_accessions' END,
                CASE WHEN mapping_applicability = 'unresolved_taxon_protein'
                    THEN 'source_taxon_unresolved' END,
                CASE WHEN mapping_applicability = 'nonhuman_protein'
                    THEN 'outside_frozen_human_taxon' END,
                CASE WHEN mapping_applicability IN (
                    'nonprotein_entity', 'unresolved_entity_type'
                ) THEN 'nonprotein_or_unresolved_entity' END,
                CASE WHEN resolved_mapping_state = 'unmapped'
                    THEN 'no_frozen_sequence_candidate' END,
                CASE WHEN resolved_construct_confidence IN ('C', 'D')
                    THEN 'no_exact_construct_sequence_or_boundaries' END
            ], flag -> flag IS NOT NULL) AS conflict_flags,
            false AS label_authorized,
            raw_file_path AS staging_raw_file_path,
            raw_locator AS staging_raw_locator,
            {parse_sha} AS input_parse_manifest_sha256,
            {version} AS reconciliation_version,
            {git_commit} AS reconciliation_git_commit,
            {container_sha} AS container_sif_sha256,
            {provenance.schema_version}::INTEGER AS schema_version,
            {schema_sha} AS schema_sha256,
            to_json(struct_pack(
                construct_sequence := 'not_reported',
                construct_boundaries := 'not_reported',
                exact_construct_confidence := 'not_assignable_from_frozen_sources'
            ))::VARCHAR AS missingness_json
        FROM confidence
        """
    )
