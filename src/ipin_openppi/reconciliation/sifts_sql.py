"""Release- and interval-aware SIFTS mapping audit relations."""

from __future__ import annotations

import duckdb

from .policy import ReconciliationProvenance, sql_string


def build_sifts_work_table(
    connection: duckdb.DuckDBPyConnection,
    provenance: ReconciliationProvenance,
) -> None:
    human_taxid = int(provenance.frozen_taxid)
    parse_sha = sql_string(provenance.parse_manifest_sha256)
    version = sql_string(provenance.version)
    git_commit = sql_string(provenance.git_commit)
    container_sha = sql_string(provenance.container_sif_sha256)
    schema_sha = sql_string(provenance.schema_sha256)
    sifts_release = sql_string(provenance.sifts_declared_uniprot_release)
    frozen_release = sql_string(provenance.frozen_uniprot_release)

    connection.execute(
        f"""
        CREATE TEMP TABLE sifts_chain_mapping_audit_work AS
        WITH chain_taxonomy AS (
            SELECT
                pdb_id,
                chain_id,
                list(DISTINCT taxid::VARCHAR ORDER BY taxid::VARCHAR)
                    AS chain_taxids,
                bool_or(taxid = {human_taxid}) AS has_human_taxonomy,
                bool_or(taxid <> {human_taxid}) AS has_other_taxonomy
            FROM sifts_chain_taxonomy
            GROUP BY pdb_id, chain_id
        ),
        primary_accessions AS (
            SELECT DISTINCT uniprot_accession FROM sequences
        ),
        additional_sequences AS (
            SELECT sequence_id, uniprot_accession, isoform_id,
                   sequence_sha256, sequence_length
            FROM sequences
            WHERE isoform_id IS NOT NULL
        ),
        joined AS (
            SELECT
                mapping.*,
                coalesce(taxonomy.chain_taxids, []::VARCHAR[]) AS chain_taxids,
                coalesce(taxonomy.has_human_taxonomy, false)
                    AS has_human_taxonomy,
                coalesce(taxonomy.has_other_taxonomy, false)
                    AS has_other_taxonomy,
                primary_accessions.uniprot_accession IS NOT NULL
                    AS has_primary_accession,
                canonical.sequence_id AS canonical_sequence_id,
                canonical.uniprot_accession AS canonical_accession,
                canonical.isoform_id AS canonical_isoform_id,
                canonical.sequence_sha256 AS canonical_sequence_sha256,
                canonical.sequence_length AS canonical_sequence_length,
                additional.sequence_id AS additional_sequence_id,
                additional.uniprot_accession AS additional_accession,
                additional.isoform_id AS additional_isoform_id,
                additional.sequence_sha256 AS additional_sequence_sha256,
                additional.sequence_length AS additional_sequence_length
            FROM sifts_chain_uniprot AS mapping
            LEFT JOIN chain_taxonomy AS taxonomy
              ON taxonomy.pdb_id = mapping.pdb_id
             AND taxonomy.chain_id = mapping.chain_id
            LEFT JOIN primary_accessions
              ON primary_accessions.uniprot_accession = mapping.uniprot_accession
            LEFT JOIN canonical_sequences AS canonical
              ON canonical.uniprot_accession = mapping.uniprot_accession
            LEFT JOIN additional_sequences AS additional
              ON primary_accessions.uniprot_accession IS NULL
             AND additional.sequence_id = mapping.uniprot_accession
        ),
        classified AS (
            SELECT
                joined.*,
                CASE
                    WHEN has_human_taxonomy AND has_other_taxonomy
                        THEN 'human_and_other'
                    WHEN has_human_taxonomy THEN 'human_only'
                    WHEN has_other_taxonomy THEN 'nonhuman_only'
                    ELSE 'no_taxonomy'
                END AS taxonomy_resolution,
                CASE
                    WHEN canonical_sequence_id IS NOT NULL
                        THEN 'primary_canonical_sequence'
                    WHEN has_primary_accession
                        THEN 'primary_field_without_canonical'
                    WHEN additional_sequence_id IS NOT NULL
                        THEN 'additional_sequence_identifier'
                    ELSE 'absent'
                END AS accession_match_state,
                coalesce(canonical_sequence_id, additional_sequence_id)
                    AS frozen_sequence_id,
                coalesce(canonical_accession, additional_accession)
                    AS frozen_uniprot_accession,
                coalesce(canonical_isoform_id, additional_isoform_id)
                    AS frozen_isoform_id,
                coalesce(canonical_sequence_sha256, additional_sequence_sha256)
                    AS frozen_sequence_sha256,
                coalesce(canonical_sequence_length, additional_sequence_length)
                    AS frozen_sequence_length,
                CASE
                    WHEN uniprot_begin IS NULL OR uniprot_end IS NULL
                        THEN 'incomplete'
                    WHEN uniprot_begin > uniprot_end
                        THEN 'complete_descending'
                    ELSE 'complete_ascending'
                END AS interval_state
            FROM joined
        )
        SELECT
            concat('sifts-chain-audit:', substr(sha256(mapping_id), 1, 32))
                AS audit_record_id,
            mapping_id,
            pdb_id,
            chain_id,
            uniprot_accession,
            source_snapshot,
            {sifts_release} AS sifts_declared_uniprot_release,
            {frozen_release} AS frozen_uniprot_release,
            chain_taxids,
            taxonomy_resolution,
            has_human_taxonomy,
            has_human_taxonomy AND has_other_taxonomy AS mixed_taxonomy,
            accession_match_state,
            frozen_sequence_id,
            frozen_uniprot_accession,
            frozen_isoform_id,
            frozen_sequence_sha256,
            frozen_sequence_length,
            uniprot_begin,
            uniprot_end,
            interval_state,
            CASE
                WHEN frozen_sequence_length IS NOT NULL
                 AND interval_state = 'complete_ascending'
                    THEN uniprot_begin >= 1
                     AND uniprot_end <= frozen_sequence_length
            END AS frozen_interval_within_bounds,
            false AS exact_sequence_identity_verified,
            false AS release_aligned,
            CASE
                WHEN taxonomy_resolution = 'no_taxonomy'
                    THEN 'unresolved_taxonomy'
                WHEN NOT has_human_taxonomy
                    THEN 'out_of_scope_nonhuman'
                WHEN interval_state = 'complete_descending'
                    THEN 'blocked_descending_interval'
                WHEN frozen_sequence_id IS NULL
                    THEN 'unmatched_frozen_sequence'
                ELSE 'blocked_release_mismatch'
            END AS structural_mapping_state,
            false AS structural_mapping_authorized,
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
