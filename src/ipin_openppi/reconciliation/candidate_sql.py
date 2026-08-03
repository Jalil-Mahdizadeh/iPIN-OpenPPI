"""Priority-ordered participant-to-sequence candidate generation."""

from __future__ import annotations

import duckdb

from .policy import sql_string


_ROUTES = {
    "direct_uniprot_exact",
    "direct_uniprot_isoform1_alias",
    "ensembl_protein",
    "ensembl_transcript",
    "ensembl_gene",
}
_ENSEMBL_ROUTES = {
    "ensembl_protein": "raw_ensembl_protein_ids",
    "ensembl_transcript": "raw_ensembl_transcript_ids",
    "ensembl_gene": "raw_ensembl_gene_ids",
}


def _validate_policy(
    candidate_priority: dict[str, int],
    ensembl_database_mapping: dict[str, str],
) -> None:
    if set(candidate_priority) != _ROUTES:
        raise ValueError("Candidate-priority routes differ from the frozen policy")
    if set(candidate_priority.values()) != set(range(1, 6)):
        raise ValueError("Candidate priorities must be the unique integers 1 through 5")
    if set(ensembl_database_mapping) != set(_ENSEMBL_ROUTES):
        raise ValueError("Ensembl database routes differ from the frozen policy")
    ordered = sorted(candidate_priority, key=candidate_priority.get)
    if ordered != [
        "direct_uniprot_exact",
        "direct_uniprot_isoform1_alias",
        "ensembl_protein",
        "ensembl_transcript",
        "ensembl_gene",
    ]:
        raise ValueError("Candidate-priority order differs from the frozen policy")


def build_candidate_relations(
    connection: duckdb.DuckDBPyConnection,
    candidate_priority: dict[str, int],
    ensembl_database_mapping: dict[str, str],
) -> None:
    """Stop after the first route yielding candidates for a participant."""

    _validate_policy(candidate_priority, ensembl_database_mapping)
    priority = {key: int(value) for key, value in candidate_priority.items()}

    connection.execute(
        """
        CREATE TEMP TABLE canonical_sequences AS
        SELECT sequence_id, uniprot_accession, isoform_id, sequence_sha256,
               sequence_length, sequence_view
        FROM sequences
        WHERE canonical
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE feature_summary AS
        SELECT
            participant_id,
            count(*)::BIGINT AS feature_count,
            count_if(start_position IS NOT NULL OR end_position IS NOT NULL)::BIGINT
                AS ranged_feature_count,
            count_if(original_sequence IS NOT NULL OR resulting_sequence IS NOT NULL)::BIGINT
                AS sequence_change_feature_count
        FROM participant_features
        GROUP BY participant_id
        """
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE mapping_candidates AS
        SELECT DISTINCT
            raw.source_key,
            raw.participant_id,
            {priority['direct_uniprot_exact']}::INTEGER AS priority,
            'direct_uniprot_exact' AS route,
            sequence.sequence_id,
            sequence.uniprot_accession,
            sequence.isoform_id,
            sequence.sequence_sha256,
            sequence.sequence_length,
            sequence.sequence_view
        FROM (
            SELECT source_key, participant_id, identifier
            FROM participants, unnest(raw_uniprot_accessions) AS item(identifier)
        ) AS raw
        JOIN sequences AS sequence ON raw.identifier = sequence.sequence_id
        """
    )
    connection.execute(
        f"""
        INSERT INTO mapping_candidates
        SELECT DISTINCT
            raw.source_key,
            raw.participant_id,
            {priority['direct_uniprot_isoform1_alias']}::INTEGER,
            'direct_uniprot_isoform1_alias',
            sequence.sequence_id,
            sequence.uniprot_accession,
            sequence.isoform_id,
            sequence.sequence_sha256,
            sequence.sequence_length,
            sequence.sequence_view
        FROM (
            SELECT source_key, participant_id, identifier
            FROM participants, unnest(raw_uniprot_accessions) AS item(identifier)
        ) AS raw
        JOIN canonical_sequences AS sequence
          ON left(raw.identifier, length(raw.identifier) - 2)
             = sequence.uniprot_accession
        WHERE ends_with(raw.identifier, '-1')
          AND NOT EXISTS (
              SELECT 1 FROM mapping_candidates AS resolved
              WHERE resolved.source_key = raw.source_key
                AND resolved.participant_id = raw.participant_id
          )
        """
    )
    for route in ("ensembl_protein", "ensembl_transcript", "ensembl_gene"):
        column = _ENSEMBL_ROUTES[route]
        connection.execute(
            f"""
            INSERT INTO mapping_candidates
            SELECT DISTINCT
                raw.source_key,
                raw.participant_id,
                {priority[route]}::INTEGER,
                '{route}',
                sequence.sequence_id,
                sequence.uniprot_accession,
                sequence.isoform_id,
                sequence.sequence_sha256,
                sequence.sequence_length,
                sequence.sequence_view
            FROM (
                SELECT source_key, participant_id,
                       split_part(identifier, '.', 1) AS identifier_versionless
                FROM participants, unnest({column}) AS item(identifier)
            ) AS raw
            JOIN identifier_mappings AS mapping
              ON mapping.database = {sql_string(ensembl_database_mapping[route])}
             AND mapping.identifier_versionless = raw.identifier_versionless
            JOIN sequences AS sequence
              ON sequence.sequence_id = mapping.uniprot_accession
            WHERE NOT EXISTS (
                SELECT 1 FROM mapping_candidates AS resolved
                WHERE resolved.source_key = raw.source_key
                  AND resolved.participant_id = raw.participant_id
            )
            """
        )
    connection.execute(
        """
        CREATE TEMP TABLE selected_candidate_summary AS
        SELECT
            source_key,
            participant_id,
            min(priority)::INTEGER AS priority,
            min(route) AS route,
            list(DISTINCT sequence_id ORDER BY sequence_id)
                AS candidate_sequence_ids,
            list(DISTINCT sequence_sha256 ORDER BY sequence_sha256)
                AS candidate_sequence_sha256s,
            list(DISTINCT uniprot_accession ORDER BY uniprot_accession)
                AS candidate_parent_accessions,
            count(DISTINCT sequence_id)::INTEGER AS candidate_sequence_count,
            count(DISTINCT sequence_sha256)::INTEGER AS candidate_hash_count,
            count(DISTINCT uniprot_accession)::INTEGER AS candidate_parent_count,
            CASE WHEN count(DISTINCT sequence_id) = 1
                 THEN min(sequence_id) END AS single_sequence_id,
            CASE WHEN count(DISTINCT uniprot_accession) = 1
                 THEN min(uniprot_accession) END AS single_parent_accession,
            CASE WHEN count(DISTINCT sequence_id) = 1
                 THEN min(isoform_id) END AS single_isoform_id,
            CASE WHEN count(DISTINCT sequence_sha256) = 1
                 THEN min(sequence_sha256) END AS single_sequence_sha256,
            CASE WHEN count(DISTINCT sequence_sha256) = 1
                 THEN min(sequence_length) END AS single_sequence_length,
            CASE WHEN count(DISTINCT sequence_id) = 1
                 THEN min(sequence_view) END AS single_sequence_view
        FROM mapping_candidates
        GROUP BY source_key, participant_id
        """
    )
