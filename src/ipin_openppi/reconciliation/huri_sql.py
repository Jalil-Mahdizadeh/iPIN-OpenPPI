"""HuRI detailed-evidence to provider-pair representation reconciliation."""

from __future__ import annotations

import duckdb

from .policy import ReconciliationProvenance, sql_string


def build_huri_work_tables(
    connection: duckdb.DuckDBPyConnection,
    provenance: ReconciliationProvenance,
) -> None:
    parse_sha = sql_string(provenance.parse_manifest_sha256)
    version = sql_string(provenance.version)
    git_commit = sql_string(provenance.git_commit)
    container_sha = sql_string(provenance.container_sif_sha256)
    schema_sha = sql_string(provenance.schema_sha256)

    connection.execute(
        f"""
        CREATE TEMP TABLE huri_evidence_gene_pair_projections_work AS
        WITH participant_pairs AS (
            SELECT
                evidence.evidence_id,
                evidence.source_dataset,
                coalesce(first(list_sort(list_distinct(list_transform(
                    participant.raw_ensembl_gene_ids,
                    item -> split_part(item, '.', 1)
                )))) FILTER (WHERE participant.participant_ordinal = 1),
                    []::VARCHAR[]) AS participant_a_gene_ids,
                coalesce(first(list_sort(list_distinct(list_transform(
                    participant.raw_ensembl_gene_ids,
                    item -> split_part(item, '.', 1)
                )))) FILTER (WHERE participant.participant_ordinal = 2),
                    []::VARCHAR[]) AS participant_b_gene_ids,
                coalesce(first(list_sort(list_distinct(participant.raw_orf_ids)))
                    FILTER (WHERE participant.participant_ordinal = 1),
                    []::VARCHAR[]) AS participant_a_orf_ids,
                coalesce(first(list_sort(list_distinct(participant.raw_orf_ids)))
                    FILTER (WHERE participant.participant_ordinal = 2),
                    []::VARCHAR[]) AS participant_b_orf_ids
            FROM evidence
            JOIN participants AS participant
              ON participant.evidence_id = evidence.evidence_id
             AND participant.source_key = evidence.source_key
            WHERE evidence.source_key = 'huri'
            GROUP BY evidence.evidence_id, evidence.source_dataset
        ),
        projected AS (
            SELECT
                participant_pairs.*,
                array_length(participant_a_gene_ids) = 1
                    AND array_length(participant_b_gene_ids) = 1
                    AS unique_gene_pair,
                array_length(participant_a_orf_ids) = 1
                    AND array_length(participant_b_orf_ids) = 1
                    AS unique_orf_pair,
                CASE WHEN array_length(participant_a_gene_ids) = 1
                    THEN participant_a_gene_ids[1] END AS ordered_gene_a,
                CASE WHEN array_length(participant_b_gene_ids) = 1
                    THEN participant_b_gene_ids[1] END AS ordered_gene_b,
                CASE WHEN array_length(participant_a_orf_ids) = 1
                    THEN participant_a_orf_ids[1] END AS ordered_orf_a,
                CASE WHEN array_length(participant_b_orf_ids) = 1
                    THEN participant_b_orf_ids[1] END AS ordered_orf_b
            FROM participant_pairs
        ),
        normalized AS (
            SELECT
                projected.*,
                CASE WHEN unique_gene_pair
                    THEN least(ordered_gene_a, ordered_gene_b) END AS gene_a,
                CASE WHEN unique_gene_pair
                    THEN greatest(ordered_gene_a, ordered_gene_b) END AS gene_b,
                CASE WHEN unique_orf_pair
                    THEN least(ordered_orf_a, ordered_orf_b) END AS orf_a,
                CASE WHEN unique_orf_pair
                    THEN greatest(ordered_orf_a, ordered_orf_b) END AS orf_b
            FROM projected
        ),
        pair_view_counts AS (
            SELECT
                source_dataset,
                least(member_a, member_b) AS gene_a,
                greatest(member_a, member_b) AS gene_b,
                count(*)::INTEGER AS membership_count
            FROM huri_pair_views
            GROUP BY source_dataset, gene_a, gene_b
        )
        SELECT
            concat('huri-gene-projection:', substr(
                sha256(normalized.evidence_id), 1, 32
            )) AS projection_id,
            normalized.evidence_id,
            normalized.source_dataset,
            normalized.participant_a_gene_ids,
            normalized.participant_b_gene_ids,
            normalized.participant_a_orf_ids,
            normalized.participant_b_orf_ids,
            normalized.ordered_gene_a,
            normalized.ordered_gene_b,
            normalized.gene_a,
            normalized.gene_b,
            CASE WHEN normalized.unique_gene_pair THEN concat(
                'ensembl-pair:', substr(sha256(concat(
                    normalized.gene_a, '|', normalized.gene_b
                )), 1, 32)) END AS unordered_gene_pair_id,
            CASE WHEN normalized.unique_gene_pair THEN concat(
                'ensembl-ordered:', substr(sha256(concat(
                    normalized.ordered_gene_a, '|', normalized.ordered_gene_b
                )), 1, 32)) END AS ordered_gene_pair_id,
            normalized.ordered_orf_a,
            normalized.ordered_orf_b,
            normalized.orf_a,
            normalized.orf_b,
            CASE WHEN normalized.unique_orf_pair THEN concat(
                'orf-pair:', substr(sha256(concat(
                    normalized.orf_a, '|', normalized.orf_b
                )), 1, 32)) END AS unordered_orf_pair_id,
            CASE WHEN normalized.unique_orf_pair THEN concat(
                'orf-ordered:', substr(sha256(concat(
                    normalized.ordered_orf_a, '|', normalized.ordered_orf_b
                )), 1, 32)) END AS ordered_orf_pair_id,
            CASE WHEN normalized.unique_gene_pair
                THEN normalized.gene_a = normalized.gene_b END AS self_pair,
            normalized.unique_gene_pair,
            normalized.unique_orf_pair,
            coalesce(pair_view_counts.membership_count, 0)::INTEGER
                AS source_pair_view_membership_count,
            CASE
                WHEN NOT normalized.unique_gene_pair
                    THEN 'unresolved_gene_projection'
                WHEN coalesce(pair_view_counts.membership_count, 0) > 0
                    THEN 'matched_pair_view'
                ELSE 'detailed_only'
            END AS representation_state,
            false AS label_authorized,
            {parse_sha} AS input_parse_manifest_sha256,
            {version} AS reconciliation_version,
            {git_commit} AS reconciliation_git_commit,
            {container_sha} AS container_sif_sha256,
            {provenance.schema_version}::INTEGER AS schema_version,
            {schema_sha} AS schema_sha256
        FROM normalized
        LEFT JOIN pair_view_counts
          ON pair_view_counts.source_dataset = normalized.source_dataset
         AND pair_view_counts.gene_a = normalized.gene_a
         AND pair_view_counts.gene_b = normalized.gene_b
        """
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE huri_pair_reconciliation_work AS
        WITH detailed AS (
            SELECT
                source_dataset,
                gene_a,
                gene_b,
                count(*)::BIGINT AS detailed_evidence_count,
                count(DISTINCT unordered_orf_pair_id)
                    FILTER (WHERE unordered_orf_pair_id IS NOT NULL)::BIGINT
                    AS unique_unordered_orf_pair_count,
                count(DISTINCT ordered_orf_pair_id)
                    FILTER (WHERE ordered_orf_pair_id IS NOT NULL)::BIGINT
                    AS unique_ordered_orf_pair_count,
                count(DISTINCT ordered_gene_pair_id)
                    FILTER (WHERE ordered_gene_pair_id IS NOT NULL)::BIGINT
                    AS unique_ordered_gene_orientation_count
            FROM huri_evidence_gene_pair_projections_work
            WHERE unique_gene_pair
            GROUP BY source_dataset, gene_a, gene_b
        ),
        pair_view AS (
            SELECT
                source_dataset,
                least(member_a, member_b) AS gene_a,
                greatest(member_a, member_b) AS gene_b,
                count(*)::BIGINT AS pair_view_row_count
            FROM huri_pair_views
            GROUP BY source_dataset, gene_a, gene_b
        ),
        pair_keys AS (
            SELECT source_dataset, gene_a, gene_b FROM detailed
            UNION
            SELECT source_dataset, gene_a, gene_b FROM pair_view
        )
        SELECT
            concat('huri-pair-reconciliation:', substr(sha256(concat(
                pair_keys.source_dataset, '|', pair_keys.gene_a, '|', pair_keys.gene_b
            )), 1, 32)) AS reconciliation_record_id,
            pair_keys.source_dataset,
            pair_keys.gene_a,
            pair_keys.gene_b,
            concat('ensembl-pair:', substr(sha256(concat(
                pair_keys.gene_a, '|', pair_keys.gene_b
            )), 1, 32)) AS unordered_gene_pair_id,
            CASE
                WHEN detailed.detailed_evidence_count IS NOT NULL
                 AND pair_view.pair_view_row_count IS NOT NULL
                    THEN 'matched_pair_view'
                WHEN detailed.detailed_evidence_count IS NOT NULL
                    THEN 'detailed_only'
                ELSE 'pair_view_only'
            END AS representation_state,
            coalesce(detailed.detailed_evidence_count, 0)::BIGINT
                AS detailed_evidence_count,
            coalesce(detailed.unique_unordered_orf_pair_count, 0)::BIGINT
                AS unique_unordered_orf_pair_count,
            coalesce(detailed.unique_ordered_orf_pair_count, 0)::BIGINT
                AS unique_ordered_orf_pair_count,
            coalesce(detailed.unique_ordered_gene_orientation_count, 0)::BIGINT
                AS unique_ordered_gene_orientation_count,
            coalesce(pair_view.pair_view_row_count, 0)::BIGINT
                AS pair_view_row_count,
            pair_keys.gene_a = pair_keys.gene_b AS self_pair,
            false AS label_authorized,
            {parse_sha} AS input_parse_manifest_sha256,
            {version} AS reconciliation_version,
            {git_commit} AS reconciliation_git_commit,
            {container_sha} AS container_sif_sha256,
            {provenance.schema_version}::INTEGER AS schema_version,
            {schema_sha} AS schema_sha256
        FROM pair_keys
        LEFT JOIN detailed USING (source_dataset, gene_a, gene_b)
        LEFT JOIN pair_view USING (source_dataset, gene_a, gene_b)
        """
    )
