"""Independent row-level checks for the primary reconciliation artifact."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import duckdb

from ipin_openppi.ingestion.schema import SchemaContract
from ipin_openppi.validation.staging import Checks


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _view_name(table: str) -> str:
    return f"canonical_{table}"


def _query_scalar(connection: duckdb.DuckDBPyConnection, sql: str) -> int:
    row = connection.execute(sql).fetchone()
    return 0 if row is None or row[0] is None else int(row[0])


def _record_zero_counts(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    prefix: str,
    sql: str,
) -> None:
    cursor = connection.execute(sql)
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError(f"Validation query returned no aggregate row: {prefix}")
    for description, value in zip(cursor.description, row, strict=True):
        observed = 0 if value is None else int(value)
        check_name = str(description[0])
        checks.require(
            f"{prefix}.{check_name}",
            observed == 0,
            observed=observed,
            expected=0,
        )


def register_canonical_views(
    connection: duckdb.DuckDBPyConnection,
    table_paths: Mapping[str, list[Path]],
) -> None:
    for table, paths in sorted(table_paths.items()):
        connection.read_parquet([path.as_posix() for path in paths]).create_view(
            _view_name(table)
        )


def register_staging_views(
    connection: duckdb.DuckDBPyConnection,
    staging_root: Path,
) -> None:
    def parquet_glob(source: str, table: str) -> str:
        return (staging_root / source / table / "*.parquet").as_posix()

    huri_participants = _sql_string(parquet_glob("huri", "participants"))
    intact_participants = _sql_string(parquet_glob("intact_imex", "participants"))
    huri_evidence = _sql_string(parquet_glob("huri", "evidence_records"))
    intact_evidence = _sql_string(parquet_glob("intact_imex", "evidence_records"))
    huri_features = _sql_string(parquet_glob("huri", "participant_features"))
    intact_features = _sql_string(parquet_glob("intact_imex", "participant_features"))
    sequences = _sql_string(parquet_glob("uniprot", "protein_sequences"))
    identifiers = _sql_string(parquet_glob("uniprot", "identifier_mappings"))
    pair_views = _sql_string(parquet_glob("huri", "source_pair_views"))
    sifts_chain = _sql_string(parquet_glob("pdb_sifts", "sifts_chain_uniprot"))
    sifts_taxonomy = _sql_string(parquet_glob("pdb_sifts", "sifts_chain_taxonomy"))

    connection.execute(
        f"""
        CREATE TEMP VIEW staging_participants AS
        SELECT 'huri' AS source_key, * FROM read_parquet({huri_participants})
        UNION ALL
        SELECT 'intact_imex' AS source_key, *
        FROM read_parquet({intact_participants})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW staging_evidence AS
        SELECT * FROM read_parquet({huri_evidence})
        UNION ALL
        SELECT * FROM read_parquet({intact_evidence})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW staging_features AS
        SELECT 'huri' AS source_key, * FROM read_parquet({huri_features})
        UNION ALL
        SELECT 'intact_imex' AS source_key, *
        FROM read_parquet({intact_features})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW staging_sequences AS
        SELECT coalesce(isoform_id, uniprot_accession) AS sequence_id, *
        FROM read_parquet({sequences})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW staging_identifier_mappings AS
        SELECT * FROM read_parquet({identifiers})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW staging_huri_pair_views AS
        SELECT * FROM read_parquet({pair_views})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW staging_sifts_chain AS
        SELECT * FROM read_parquet({sifts_chain})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW staging_sifts_taxonomy AS
        SELECT * FROM read_parquet({sifts_taxonomy})
        """
    )


def validate_contract_rows(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    contract: SchemaContract,
    table_paths: Mapping[str, list[Path]],
) -> None:
    for table in sorted(table_paths):
        view = _view_name(table)
        spec = contract.table_spec(table)
        required = [str(value) for value in spec.get("required_non_null", [])]
        if required:
            expressions = ", ".join(
                f'count(*) FILTER (WHERE "{column}" IS NULL) AS "{column}"'
                for column in required
            )
            row = connection.execute(f"SELECT {expressions} FROM {view}").fetchone()
            assert row is not None
            null_counts = {
                column: int(value)
                for column, value in zip(required, row, strict=True)
                if int(value)
            }
        else:
            null_counts = {}
        checks.require(
            f"contract.{table}.required_non_null",
            not null_counts,
            observed=null_counts,
            expected={},
        )

        invalid_enums: dict[str, int] = {}
        for column, enum_name in spec.get("enum_columns", {}).items():
            allowed = [str(value) for value in contract.document["enums"][enum_name]]
            placeholders = ",".join("?" for _ in allowed)
            count = int(
                connection.execute(
                    f'SELECT count(*) FROM {view} WHERE "{column}" IS NOT NULL '
                    f'AND "{column}" NOT IN ({placeholders})',
                    allowed,
                ).fetchone()[0]
            )
            if count:
                invalid_enums[str(column)] = count
        checks.require(
            f"contract.{table}.enum_values",
            not invalid_enums,
            observed=invalid_enums,
            expected={},
        )

        primary_key = [str(value) for value in spec.get("primary_key", [])]
        if primary_key:
            columns = ", ".join(f'"{value}"' for value in primary_key)
            duplicates = _query_scalar(
                connection,
                f"SELECT coalesce(sum(n - 1), 0) FROM ("
                f"SELECT {columns}, count(*) AS n FROM {view} "
                f"GROUP BY {columns} HAVING count(*) > 1)",
            )
            checks.require(
                f"contract.{table}.primary_key_unique",
                duplicates == 0,
                observed=duplicates,
                expected=0,
            )


def validate_uniform_provenance_and_authorization(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    contract: SchemaContract,
    table_paths: Mapping[str, list[Path]],
    manifest: Mapping[str, Any],
) -> None:
    parse_sha = _sql_string(str(manifest["inputs"]["parse_manifest_sha256"]))
    version = _sql_string(str(manifest["runtime"]["reconciliation_version"]))
    git_commit = _sql_string(str(manifest["git"]["commit"]))
    container_sha = _sql_string(str(manifest["runtime"]["container_sif_sha256"]))
    schema_sha = _sql_string(contract.sha256)
    for table in sorted(table_paths):
        view = _view_name(table)
        _record_zero_counts(
            checks,
            connection,
            f"provenance.{table}",
            f"""
            SELECT
                count(*) FILTER (WHERE input_parse_manifest_sha256
                    IS DISTINCT FROM {parse_sha}) AS parse_manifest_sha256,
                count(*) FILTER (WHERE reconciliation_version
                    IS DISTINCT FROM {version}) AS reconciliation_version,
                count(*) FILTER (WHERE reconciliation_git_commit
                    IS DISTINCT FROM {git_commit}) AS reconciliation_git_commit,
                count(*) FILTER (WHERE container_sif_sha256
                    IS DISTINCT FROM {container_sha}) AS container_sif_sha256,
                count(*) FILTER (WHERE schema_version
                    IS DISTINCT FROM {contract.version}) AS schema_version,
                count(*) FILTER (WHERE schema_sha256
                    IS DISTINCT FROM {schema_sha}) AS schema_sha256,
                count(*) FILTER (WHERE label_authorized)
                    AS label_authorized
            FROM {view}
            """,
        )


def validate_participant_mappings(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    *,
    human_taxid: int,
    protein_molecule_type_ac: str,
) -> None:
    mappings = _view_name("participant_sequence_mappings")
    protein_ac = _sql_string(protein_molecule_type_ac)
    connection.execute(
        """
        CREATE TEMP VIEW staging_participants_enriched AS
        SELECT
            participant.*,
            evidence.source_dataset,
            evidence.source_release
        FROM staging_participants AS participant
        JOIN staging_evidence AS evidence
          ON evidence.source_key = participant.source_key
         AND evidence.evidence_id = participant.evidence_id
        """
    )
    _record_zero_counts(
        checks,
        connection,
        "participant.source_link",
        f"""
        SELECT
            count(*) FILTER (WHERE source.participant_id IS NULL)
                AS extra_mapping_rows,
            count(*) FILTER (WHERE mapping.participant_id IS NULL)
                AS missing_mapping_rows,
            count(*) FILTER (
                WHERE source.participant_id IS NOT NULL
                  AND mapping.participant_id IS NOT NULL
                  AND (
                    mapping.evidence_id IS DISTINCT FROM source.evidence_id OR
                    mapping.source_dataset IS DISTINCT FROM source.source_dataset OR
                    mapping.source_release IS DISTINCT FROM source.source_release OR
                    mapping.participant_ordinal IS DISTINCT FROM source.participant_ordinal OR
                    mapping.taxid IS DISTINCT FROM source.taxid OR
                    mapping.molecule_type_ac IS DISTINCT FROM source.molecule_type_ac OR
                    mapping.molecule_type_name IS DISTINCT FROM source.molecule_type_name OR
                    mapping.raw_uniprot_accessions IS DISTINCT FROM source.raw_uniprot_accessions OR
                    mapping.raw_ensembl_gene_ids IS DISTINCT FROM source.raw_ensembl_gene_ids OR
                    mapping.raw_ensembl_transcript_ids IS DISTINCT FROM source.raw_ensembl_transcript_ids OR
                    mapping.raw_ensembl_protein_ids IS DISTINCT FROM source.raw_ensembl_protein_ids OR
                    mapping.raw_orf_ids IS DISTINCT FROM source.raw_orf_ids OR
                    mapping.staging_raw_file_path IS DISTINCT FROM source.raw_file_path OR
                    mapping.staging_raw_locator IS DISTINCT FROM source.raw_locator
                  )
            ) AS copied_source_field_mismatches
        FROM staging_participants_enriched AS source
        FULL OUTER JOIN {mappings} AS mapping
          ON mapping.source_key = source.source_key
         AND mapping.participant_id = source.participant_id
        """,
    )
    _record_zero_counts(
        checks,
        connection,
        "participant.feature_counts",
        f"""
        WITH expected AS (
            SELECT
                participant_id,
                count(*)::BIGINT AS feature_count,
                count(*) FILTER (
                    WHERE start_position IS NOT NULL OR end_position IS NOT NULL
                )::BIGINT AS ranged_feature_count,
                count(*) FILTER (
                    WHERE original_sequence IS NOT NULL
                       OR resulting_sequence IS NOT NULL
                )::BIGINT AS sequence_change_feature_count
            FROM staging_features
            GROUP BY participant_id
        )
        SELECT
            count(*) FILTER (
                WHERE mapping.feature_count IS DISTINCT FROM
                    coalesce(expected.feature_count, 0)
            ) AS feature_count_mismatches,
            count(*) FILTER (
                WHERE mapping.ranged_feature_count IS DISTINCT FROM
                    coalesce(expected.ranged_feature_count, 0)
            ) AS ranged_feature_count_mismatches,
            count(*) FILTER (
                WHERE mapping.sequence_change_feature_count IS DISTINCT FROM
                    coalesce(expected.sequence_change_feature_count, 0)
            ) AS sequence_change_feature_count_mismatches
        FROM {mappings} AS mapping
        LEFT JOIN expected USING (participant_id)
        """,
    )
    _record_zero_counts(
        checks,
        connection,
        "participant.mapping_semantics",
        f"""
        WITH expected AS (
            SELECT
                *,
                CASE
                    WHEN molecule_type_ac IS NULL THEN 'unresolved_entity_type'
                    WHEN molecule_type_ac <> {protein_ac} THEN 'nonprotein_entity'
                    WHEN taxid IS NULL OR taxid <= 0 THEN 'unresolved_taxon_protein'
                    WHEN taxid <> {human_taxid} THEN 'nonhuman_protein'
                    ELSE 'human_protein'
                END AS expected_applicability
            FROM {mappings}
        ), classified AS (
            SELECT
                *,
                CASE
                    WHEN expected_applicability = 'nonprotein_entity'
                        THEN 'not_applicable'
                    WHEN expected_applicability = 'unresolved_entity_type'
                        THEN 'unresolved'
                    WHEN expected_applicability = 'nonhuman_protein'
                        THEN 'out_of_scope'
                    WHEN expected_applicability = 'unresolved_taxon_protein'
                        THEN 'unresolved'
                    WHEN candidate_sequence_count = 0 THEN 'unmapped'
                    WHEN candidate_sequence_count = 1
                         AND selected_route = 'direct_uniprot_exact'
                        THEN 'direct_identifier_unique'
                    WHEN candidate_sequence_count = 1
                         AND selected_route = 'direct_uniprot_isoform1_alias'
                        THEN 'canonical_isoform_alias_unique'
                    WHEN candidate_sequence_count = 1
                        THEN 'cross_reference_unique'
                    WHEN candidate_hash_count = 1
                        THEN 'sequence_equivalent_candidates'
                    WHEN candidate_parent_count = 1
                         AND canonical_projection_sequence_sha256 IS NOT NULL
                        THEN 'canonical_projection_only'
                    ELSE 'ambiguous'
                END AS expected_mapping_state,
                expected_applicability = 'human_protein'
                    AND candidate_hash_count = 1 AS expected_reference_usable,
                expected_applicability = 'human_protein'
                    AND canonical_projection_sequence_sha256 IS NOT NULL
                    AS expected_canonical_usable
            FROM expected
        ), confidence AS (
            SELECT
                *,
                CASE
                    WHEN expected_applicability IN (
                        'nonprotein_entity', 'nonhuman_protein'
                    ) THEN 'not_applicable'
                    WHEN expected_mapping_state = 'unmapped' THEN 'unmapped'
                    WHEN expected_mapping_state IN ('ambiguous', 'unresolved')
                        THEN 'D'
                    WHEN expected_reference_usable OR expected_canonical_usable
                        THEN 'C'
                    ELSE 'D'
                END AS expected_construct_confidence
            FROM classified
        )
        SELECT
            count(*) FILTER (
                WHERE mapping_record_id IS DISTINCT FROM concat(
                    'participant-map:', substr(sha256(participant_id), 1, 32)
                )
            ) AS deterministic_record_id_mismatches,
            count(*) FILTER (
                WHERE mapping_applicability IS DISTINCT FROM expected_applicability
            ) AS applicability_mismatches,
            count(*) FILTER (
                WHERE mapping_state IS DISTINCT FROM expected_mapping_state
            ) AS mapping_state_mismatches,
            count(*) FILTER (
                WHERE reference_sequence_usable
                    IS DISTINCT FROM expected_reference_usable
            ) AS reference_usable_mismatches,
            count(*) FILTER (
                WHERE canonical_projection_usable
                    IS DISTINCT FROM expected_canonical_usable
            ) AS canonical_usable_mismatches,
            count(*) FILTER (
                WHERE construct_confidence
                    IS DISTINCT FROM expected_construct_confidence
            ) AS construct_confidence_mismatches,
            count(*) FILTER (
                WHERE candidate_sequence_count
                    IS DISTINCT FROM array_length(candidate_sequence_ids)
                   OR candidate_hash_count
                    IS DISTINCT FROM array_length(candidate_sequence_sha256s)
                   OR candidate_parent_count
                    IS DISTINCT FROM array_length(candidate_parent_accessions)
            ) AS candidate_list_count_mismatches,
            count(*) FILTER (
                WHERE candidate_sequence_ids
                    IS DISTINCT FROM list_sort(list_distinct(candidate_sequence_ids))
                   OR candidate_sequence_sha256s
                    IS DISTINCT FROM list_sort(list_distinct(candidate_sequence_sha256s))
                   OR candidate_parent_accessions
                    IS DISTINCT FROM list_sort(list_distinct(candidate_parent_accessions))
            ) AS candidate_list_order_or_distinct_mismatches,
            count(*) FILTER (
                WHERE all_candidate_sequence_count
                        IS DISTINCT FROM candidate_sequence_count
                   OR all_candidate_hash_count IS DISTINCT FROM candidate_hash_count
                   OR all_candidate_parent_count
                        IS DISTINCT FROM candidate_parent_count
            ) AS route_pruning_count_mismatches,
            count(*) FILTER (
                WHERE (selected_route = 'none')
                    IS DISTINCT FROM (candidate_sequence_count = 0)
            ) AS selected_route_presence_mismatches,
            count(*) FILTER (
                WHERE candidate_hash_count > candidate_sequence_count
                   OR candidate_parent_count > candidate_sequence_count
                   OR candidate_sequence_count < 0
                   OR candidate_hash_count < 0
                   OR candidate_parent_count < 0
            ) AS impossible_candidate_counts,
            count(*) FILTER (
                WHERE (reference_sequence_usable AND (
                        mapped_sequence_sha256 IS NULL
                        OR mapped_sequence_length IS NULL
                    )) OR
                    (NOT reference_sequence_usable AND (
                        mapped_sequence_id IS NOT NULL
                        OR mapped_uniprot_accession IS NOT NULL
                        OR mapped_isoform_id IS NOT NULL
                        OR mapped_sequence_sha256 IS NOT NULL
                        OR mapped_sequence_length IS NOT NULL
                        OR mapped_sequence_view IS NOT NULL
                    ))
            ) AS mapped_reference_field_mismatches,
            count(*) FILTER (
                WHERE (canonical_projection_usable AND (
                        canonical_projection_accession IS NULL
                        OR canonical_projection_sequence_sha256 IS NULL
                    )) OR
                    (NOT canonical_projection_usable AND (
                        canonical_projection_accession IS NOT NULL
                        OR canonical_projection_sequence_sha256 IS NOT NULL
                    ))
            ) AS canonical_projection_field_mismatches,
            count(*) FILTER (
                WHERE construct_confidence IN ('A', 'B')
                   OR construct_sequence_sha256 IS NOT NULL
                   OR construct_start IS NOT NULL
                   OR construct_end IS NOT NULL
                   OR strict_construct_eligible
                   OR label_authorized
            ) AS prohibited_construct_or_label_claims,
            count(*) FILTER (
                WHERE missingness_json IS DISTINCT FROM
                    '{{"construct_sequence":"not_reported",'
                    '"construct_boundaries":"not_reported",'
                    '"exact_construct_confidence":'
                    '"not_assignable_from_frozen_sources"}}'
            ) AS construct_missingness_mismatches
        FROM confidence
        """,
    )
    _record_zero_counts(
        checks,
        connection,
        "participant.frozen_sequence_references",
        f"""
        SELECT
            (SELECT count(*) FROM {mappings} AS mapping,
                unnest(mapping.candidate_sequence_ids) AS candidate(sequence_id)
             LEFT JOIN staging_sequences AS sequence USING (sequence_id)
             WHERE sequence.sequence_id IS NULL) AS candidate_sequence_orphans,
            (SELECT count(*) FROM {mappings} AS mapping,
                unnest(mapping.candidate_sequence_sha256s) AS candidate(sequence_sha256)
             LEFT JOIN (
                SELECT DISTINCT sequence_sha256 FROM staging_sequences
             ) AS sequence USING (sequence_sha256)
             WHERE sequence.sequence_sha256 IS NULL) AS candidate_hash_orphans,
            (SELECT count(*) FROM {mappings} AS mapping,
                unnest(mapping.candidate_parent_accessions) AS candidate(uniprot_accession)
             LEFT JOIN (
                SELECT DISTINCT uniprot_accession FROM staging_sequences
             ) AS sequence USING (uniprot_accession)
             WHERE sequence.uniprot_accession IS NULL) AS candidate_parent_orphans,
            (SELECT count(*) FROM {mappings} AS mapping
             LEFT JOIN (
                SELECT DISTINCT sequence_sha256 FROM staging_sequences
             ) AS sequence
               ON sequence.sequence_sha256 = mapping.mapped_sequence_sha256
             WHERE mapping.reference_sequence_usable
               AND sequence.sequence_sha256 IS NULL) AS mapped_hash_orphans,
            (SELECT count(*) FROM {mappings} AS mapping
             LEFT JOIN staging_sequences AS sequence
               ON sequence.canonical
              AND sequence.uniprot_accession = mapping.canonical_projection_accession
              AND sequence.sequence_sha256 =
                    mapping.canonical_projection_sequence_sha256
             WHERE mapping.canonical_projection_usable
               AND sequence.sequence_id IS NULL) AS canonical_projection_orphans
        """,
    )


def validate_evidence_summaries(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    *,
    protein_molecule_type_ac: str,
) -> None:
    evidence = _view_name("evidence_mapping_summaries")
    mappings = _view_name("participant_sequence_mappings")
    protein_ac = _sql_string(protein_molecule_type_ac)
    _record_zero_counts(
        checks,
        connection,
        "evidence.source_link",
        f"""
        SELECT
            count(*) FILTER (WHERE source.evidence_id IS NULL)
                AS extra_summary_rows,
            count(*) FILTER (WHERE summary.evidence_id IS NULL)
                AS missing_summary_rows,
            count(*) FILTER (
                WHERE source.evidence_id IS NOT NULL
                  AND summary.evidence_id IS NOT NULL
                  AND (
                    summary.source_dataset IS DISTINCT FROM source.source_dataset OR
                    summary.source_release IS DISTINCT FROM source.source_release OR
                    summary.record_kind IS DISTINCT FROM source.record_kind OR
                    summary.interaction_semantics
                        IS DISTINCT FROM source.interaction_semantics OR
                    summary.observation_state IS DISTINCT FROM source.observation_state OR
                    summary.participant_count IS DISTINCT FROM source.participant_count OR
                    summary.original_nary IS DISTINCT FROM source.original_nary
                  )
            ) AS copied_source_field_mismatches
        FROM staging_evidence AS source
        FULL OUTER JOIN {evidence} AS summary
          ON summary.source_key = source.source_key
         AND summary.evidence_id = source.evidence_id
        """,
    )
    _record_zero_counts(
        checks,
        connection,
        "evidence.recomputed_semantics",
        f"""
        WITH aggregate AS (
            SELECT
                source.evidence_id,
                source.source_key,
                source.participant_count,
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
                max(mapping.mapped_sequence_sha256) FILTER (
                    WHERE mapping.participant_ordinal = 1
                ) AS reference_hash_a,
                max(mapping.mapped_sequence_sha256) FILTER (
                    WHERE mapping.participant_ordinal = 2
                ) AS reference_hash_b,
                max(mapping.canonical_projection_sequence_sha256) FILTER (
                    WHERE mapping.participant_ordinal = 1
                ) AS canonical_hash_a,
                max(mapping.canonical_projection_sequence_sha256) FILTER (
                    WHERE mapping.participant_ordinal = 2
                ) AS canonical_hash_b
            FROM staging_evidence AS source
            JOIN {mappings} AS mapping
              ON mapping.source_key = source.source_key
             AND mapping.evidence_id = source.evidence_id
            GROUP BY source.evidence_id, source.source_key, source.participant_count
        ), expected AS (
            SELECT
                *,
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
            count(*) FILTER (
                WHERE summary.mapping_summary_id IS DISTINCT FROM concat(
                    'evidence-map:', substr(sha256(summary.evidence_id), 1, 32)
                )
            ) AS deterministic_record_id_mismatches,
            count(*) FILTER (
                WHERE summary.protein_participant_count
                        IS DISTINCT FROM expected.protein_participant_count
                   OR summary.human_protein_count
                        IS DISTINCT FROM expected.human_protein_count
                   OR summary.reference_mapped_count
                        IS DISTINCT FROM expected.reference_mapped_count
                   OR summary.canonical_projectable_count
                        IS DISTINCT FROM expected.canonical_projectable_count
                   OR summary.ambiguous_count
                        IS DISTINCT FROM expected.ambiguous_count
                   OR summary.unmapped_count
                        IS DISTINCT FROM expected.unmapped_count
                   OR summary.out_of_scope_count
                        IS DISTINCT FROM expected.out_of_scope_count
                   OR summary.not_applicable_count
                        IS DISTINCT FROM expected.not_applicable_count
                   OR summary.unresolved_count
                        IS DISTINCT FROM expected.unresolved_count
            ) AS participant_count_aggregation_mismatches,
            count(*) FILTER (
                WHERE summary.binary_two_human_proteins
                        IS DISTINCT FROM expected.binary_two_human_proteins
                   OR summary.all_human_proteins_reference_resolved
                        IS DISTINCT FROM expected.all_human_proteins_reference_resolved
                   OR summary.all_human_proteins_canonical_projectable
                        IS DISTINCT FROM expected.all_human_proteins_canonical_projectable
                   OR summary.reference_pair_usable
                        IS DISTINCT FROM expected.reference_pair_usable
                   OR summary.canonical_pair_usable
                        IS DISTINCT FROM expected.canonical_pair_usable
            ) AS usability_flag_mismatches,
            count(*) FILTER (
                WHERE summary.mapped_unordered_sequence_pair_id IS DISTINCT FROM
                    CASE WHEN expected.reference_pair_usable THEN concat(
                        'reference-unordered:', substr(sha256(concat(
                            least(expected.reference_hash_a, expected.reference_hash_b),
                            '|',
                            greatest(expected.reference_hash_a, expected.reference_hash_b)
                        )), 1, 32)) END
                   OR summary.mapped_ordered_sequence_pair_id IS DISTINCT FROM
                    CASE WHEN expected.reference_pair_usable THEN concat(
                        'reference-ordered:', substr(sha256(concat(
                            expected.reference_hash_a, '|', expected.reference_hash_b
                        )), 1, 32)) END
                   OR summary.canonical_unordered_sequence_pair_id IS DISTINCT FROM
                    CASE WHEN expected.canonical_pair_usable THEN concat(
                        'canonical-unordered:', substr(sha256(concat(
                            least(expected.canonical_hash_a, expected.canonical_hash_b),
                            '|',
                            greatest(expected.canonical_hash_a, expected.canonical_hash_b)
                        )), 1, 32)) END
                   OR summary.canonical_ordered_sequence_pair_id IS DISTINCT FROM
                    CASE WHEN expected.canonical_pair_usable THEN concat(
                        'canonical-ordered:', substr(sha256(concat(
                            expected.canonical_hash_a, '|', expected.canonical_hash_b
                        )), 1, 32)) END
            ) AS deterministic_pair_id_mismatches,
            count(*) FILTER (
                WHERE summary.strict_construct_eligible OR summary.label_authorized
            ) AS prohibited_construct_or_label_claims
        FROM {evidence} AS summary
        JOIN expected
          ON expected.source_key = summary.source_key
         AND expected.evidence_id = summary.evidence_id
        """,
    )


def validate_huri_reconciliation(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
) -> None:
    projections = _view_name("huri_evidence_gene_pair_projections")
    pairs = _view_name("huri_pair_reconciliation")
    connection.execute(
        f"""
        CREATE TEMP TABLE expected_huri_projections AS
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
            FROM staging_evidence AS evidence
            JOIN staging_participants AS participant
              ON participant.source_key = evidence.source_key
             AND participant.evidence_id = evidence.evidence_id
            WHERE evidence.source_key = 'huri'
            GROUP BY evidence.evidence_id, evidence.source_dataset
        ), projected AS (
            SELECT
                *,
                array_length(participant_a_gene_ids) = 1
                    AND array_length(participant_b_gene_ids) = 1 AS unique_gene_pair,
                array_length(participant_a_orf_ids) = 1
                    AND array_length(participant_b_orf_ids) = 1 AS unique_orf_pair,
                CASE WHEN array_length(participant_a_gene_ids) = 1
                    THEN participant_a_gene_ids[1] END AS ordered_gene_a,
                CASE WHEN array_length(participant_b_gene_ids) = 1
                    THEN participant_b_gene_ids[1] END AS ordered_gene_b,
                CASE WHEN array_length(participant_a_orf_ids) = 1
                    THEN participant_a_orf_ids[1] END AS ordered_orf_a,
                CASE WHEN array_length(participant_b_orf_ids) = 1
                    THEN participant_b_orf_ids[1] END AS ordered_orf_b
            FROM participant_pairs
        ), normalized AS (
            SELECT
                *,
                CASE WHEN unique_gene_pair
                    THEN least(ordered_gene_a, ordered_gene_b) END AS gene_a,
                CASE WHEN unique_gene_pair
                    THEN greatest(ordered_gene_a, ordered_gene_b) END AS gene_b,
                CASE WHEN unique_orf_pair
                    THEN least(ordered_orf_a, ordered_orf_b) END AS orf_a,
                CASE WHEN unique_orf_pair
                    THEN greatest(ordered_orf_a, ordered_orf_b) END AS orf_b
            FROM projected
        ), pair_view AS (
            SELECT
                source_dataset,
                least(member_a, member_b) AS gene_a,
                greatest(member_a, member_b) AS gene_b,
                count(*)::INTEGER AS membership_count
            FROM staging_huri_pair_views
            GROUP BY source_dataset, gene_a, gene_b
        )
        SELECT
            normalized.*,
            coalesce(pair_view.membership_count, 0)::INTEGER
                AS source_pair_view_membership_count,
            CASE
                WHEN NOT normalized.unique_gene_pair
                    THEN 'unresolved_gene_projection'
                WHEN coalesce(pair_view.membership_count, 0) > 0
                    THEN 'matched_pair_view'
                ELSE 'detailed_only'
            END AS representation_state
        FROM normalized
        LEFT JOIN pair_view USING (source_dataset, gene_a, gene_b)
        """
    )
    _record_zero_counts(
        checks,
        connection,
        "huri.projection_semantics",
        f"""
        SELECT
            count(*) FILTER (WHERE expected.evidence_id IS NULL)
                AS extra_projection_rows,
            count(*) FILTER (WHERE observed.evidence_id IS NULL)
                AS missing_projection_rows,
            count(*) FILTER (
                WHERE expected.evidence_id IS NOT NULL
                  AND observed.evidence_id IS NOT NULL
                  AND (
                    observed.projection_id IS DISTINCT FROM concat(
                        'huri-gene-projection:',
                        substr(sha256(observed.evidence_id), 1, 32)
                    ) OR
                    observed.source_dataset IS DISTINCT FROM expected.source_dataset OR
                    observed.participant_a_gene_ids
                        IS DISTINCT FROM expected.participant_a_gene_ids OR
                    observed.participant_b_gene_ids
                        IS DISTINCT FROM expected.participant_b_gene_ids OR
                    observed.participant_a_orf_ids
                        IS DISTINCT FROM expected.participant_a_orf_ids OR
                    observed.participant_b_orf_ids
                        IS DISTINCT FROM expected.participant_b_orf_ids OR
                    observed.ordered_gene_a IS DISTINCT FROM expected.ordered_gene_a OR
                    observed.ordered_gene_b IS DISTINCT FROM expected.ordered_gene_b OR
                    observed.gene_a IS DISTINCT FROM expected.gene_a OR
                    observed.gene_b IS DISTINCT FROM expected.gene_b OR
                    observed.ordered_orf_a IS DISTINCT FROM expected.ordered_orf_a OR
                    observed.ordered_orf_b IS DISTINCT FROM expected.ordered_orf_b OR
                    observed.orf_a IS DISTINCT FROM expected.orf_a OR
                    observed.orf_b IS DISTINCT FROM expected.orf_b OR
                    observed.unique_gene_pair IS DISTINCT FROM expected.unique_gene_pair OR
                    observed.unique_orf_pair IS DISTINCT FROM expected.unique_orf_pair OR
                    observed.source_pair_view_membership_count
                        IS DISTINCT FROM expected.source_pair_view_membership_count OR
                    observed.representation_state
                        IS DISTINCT FROM expected.representation_state
                  )
            ) AS reconstructed_field_mismatches,
            count(*) FILTER (
                WHERE observed.unique_gene_pair AND (
                    observed.unordered_gene_pair_id IS DISTINCT FROM concat(
                        'ensembl-pair:', substr(sha256(concat(
                            observed.gene_a, '|', observed.gene_b
                        )), 1, 32)
                    ) OR
                    observed.ordered_gene_pair_id IS DISTINCT FROM concat(
                        'ensembl-ordered:', substr(sha256(concat(
                            observed.ordered_gene_a, '|', observed.ordered_gene_b
                        )), 1, 32)
                    ) OR
                    observed.self_pair IS DISTINCT FROM
                        (observed.gene_a = observed.gene_b)
                ) OR (NOT observed.unique_gene_pair AND (
                    observed.unordered_gene_pair_id IS NOT NULL OR
                    observed.ordered_gene_pair_id IS NOT NULL OR
                    observed.self_pair IS NOT NULL
                ))
            ) AS gene_pair_identifier_mismatches,
            count(*) FILTER (
                WHERE observed.unique_orf_pair AND (
                    observed.unordered_orf_pair_id IS DISTINCT FROM concat(
                        'orf-pair:', substr(sha256(concat(
                            observed.orf_a, '|', observed.orf_b
                        )), 1, 32)
                    ) OR
                    observed.ordered_orf_pair_id IS DISTINCT FROM concat(
                        'orf-ordered:', substr(sha256(concat(
                            observed.ordered_orf_a, '|', observed.ordered_orf_b
                        )), 1, 32)
                    )
                ) OR (NOT observed.unique_orf_pair AND (
                    observed.unordered_orf_pair_id IS NOT NULL OR
                    observed.ordered_orf_pair_id IS NOT NULL
                ))
            ) AS orf_pair_identifier_mismatches
        FROM expected_huri_projections AS expected
        FULL OUTER JOIN {projections} AS observed USING (evidence_id)
        """,
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE expected_huri_pairs AS
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
            FROM {projections}
            WHERE unique_gene_pair
            GROUP BY source_dataset, gene_a, gene_b
        ), pair_view AS (
            SELECT
                source_dataset,
                least(member_a, member_b) AS gene_a,
                greatest(member_a, member_b) AS gene_b,
                count(*)::BIGINT AS pair_view_row_count
            FROM staging_huri_pair_views
            GROUP BY source_dataset, gene_a, gene_b
        ), keys AS (
            SELECT source_dataset, gene_a, gene_b FROM detailed
            UNION
            SELECT source_dataset, gene_a, gene_b FROM pair_view
        )
        SELECT
            keys.*,
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
                AS pair_view_row_count
        FROM keys
        LEFT JOIN detailed USING (source_dataset, gene_a, gene_b)
        LEFT JOIN pair_view USING (source_dataset, gene_a, gene_b)
        """
    )
    _record_zero_counts(
        checks,
        connection,
        "huri.pair_reconciliation_semantics",
        f"""
        SELECT
            count(*) FILTER (WHERE expected.source_dataset IS NULL)
                AS extra_pair_rows,
            count(*) FILTER (WHERE observed.source_dataset IS NULL)
                AS missing_pair_rows,
            count(*) FILTER (
                WHERE expected.source_dataset IS NOT NULL
                  AND observed.source_dataset IS NOT NULL
                  AND (
                    observed.reconciliation_record_id IS DISTINCT FROM concat(
                        'huri-pair-reconciliation:', substr(sha256(concat(
                            observed.source_dataset, '|',
                            observed.gene_a, '|', observed.gene_b
                        )), 1, 32)
                    ) OR
                    observed.unordered_gene_pair_id IS DISTINCT FROM concat(
                        'ensembl-pair:', substr(sha256(concat(
                            observed.gene_a, '|', observed.gene_b
                        )), 1, 32)
                    ) OR
                    observed.representation_state
                        IS DISTINCT FROM expected.representation_state OR
                    observed.detailed_evidence_count
                        IS DISTINCT FROM expected.detailed_evidence_count OR
                    observed.unique_unordered_orf_pair_count
                        IS DISTINCT FROM expected.unique_unordered_orf_pair_count OR
                    observed.unique_ordered_orf_pair_count
                        IS DISTINCT FROM expected.unique_ordered_orf_pair_count OR
                    observed.unique_ordered_gene_orientation_count
                        IS DISTINCT FROM expected.unique_ordered_gene_orientation_count OR
                    observed.pair_view_row_count
                        IS DISTINCT FROM expected.pair_view_row_count OR
                    observed.self_pair IS DISTINCT FROM
                        (observed.gene_a = observed.gene_b)
                  )
            ) AS reconstructed_field_mismatches
        FROM expected_huri_pairs AS expected
        FULL OUTER JOIN {pairs} AS observed
          ON observed.source_dataset = expected.source_dataset
         AND observed.gene_a = expected.gene_a
         AND observed.gene_b = expected.gene_b
        """,
    )


def validate_sifts_audit(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    *,
    human_taxid: int,
    sifts_release: str,
    frozen_release: str,
) -> None:
    audit = _view_name("sifts_chain_mapping_audit")
    connection.execute(
        f"""
        CREATE TEMP TABLE expected_sifts_audit AS
        WITH taxonomy AS (
            SELECT
                pdb_id,
                chain_id,
                list(DISTINCT taxid::VARCHAR ORDER BY taxid::VARCHAR)
                    AS chain_taxids,
                bool_or(taxid = {human_taxid}) AS has_human_taxonomy,
                bool_or(taxid <> {human_taxid}) AS has_other_taxonomy
            FROM staging_sifts_taxonomy
            GROUP BY pdb_id, chain_id
        ), primary_accessions AS (
            SELECT DISTINCT uniprot_accession FROM staging_sequences
        ), additional AS (
            SELECT sequence_id, uniprot_accession, isoform_id,
                   sequence_sha256, sequence_length
            FROM staging_sequences
            WHERE isoform_id IS NOT NULL
        ), joined AS (
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
            FROM staging_sifts_chain AS mapping
            LEFT JOIN taxonomy USING (pdb_id, chain_id)
            LEFT JOIN primary_accessions
              ON primary_accessions.uniprot_accession = mapping.uniprot_accession
            LEFT JOIN staging_sequences AS canonical
              ON canonical.canonical
             AND canonical.uniprot_accession = mapping.uniprot_accession
            LEFT JOIN additional
              ON primary_accessions.uniprot_accession IS NULL
             AND additional.sequence_id = mapping.uniprot_accession
        ), classified AS (
            SELECT
                *,
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
        SELECT * FROM classified
        """
    )
    _record_zero_counts(
        checks,
        connection,
        "sifts.source_and_mapping_semantics",
        f"""
        SELECT
            count(*) FILTER (WHERE expected.mapping_id IS NULL)
                AS extra_audit_rows,
            count(*) FILTER (WHERE observed.mapping_id IS NULL)
                AS missing_audit_rows,
            count(*) FILTER (
                WHERE expected.mapping_id IS NOT NULL
                  AND observed.mapping_id IS NOT NULL
                  AND (
                    observed.audit_record_id IS DISTINCT FROM concat(
                        'sifts-chain-audit:',
                        substr(sha256(observed.mapping_id), 1, 32)
                    ) OR
                    observed.pdb_id IS DISTINCT FROM expected.pdb_id OR
                    observed.chain_id IS DISTINCT FROM expected.chain_id OR
                    observed.uniprot_accession
                        IS DISTINCT FROM expected.uniprot_accession OR
                    observed.source_snapshot IS DISTINCT FROM expected.source_snapshot OR
                    observed.chain_taxids IS DISTINCT FROM expected.chain_taxids OR
                    observed.taxonomy_resolution
                        IS DISTINCT FROM expected.taxonomy_resolution OR
                    observed.has_human_taxonomy
                        IS DISTINCT FROM expected.has_human_taxonomy OR
                    observed.mixed_taxonomy IS DISTINCT FROM
                        (expected.has_human_taxonomy AND expected.has_other_taxonomy) OR
                    observed.accession_match_state
                        IS DISTINCT FROM expected.accession_match_state OR
                    observed.frozen_sequence_id
                        IS DISTINCT FROM expected.frozen_sequence_id OR
                    observed.frozen_uniprot_accession
                        IS DISTINCT FROM expected.frozen_uniprot_accession OR
                    observed.frozen_isoform_id
                        IS DISTINCT FROM expected.frozen_isoform_id OR
                    observed.frozen_sequence_sha256
                        IS DISTINCT FROM expected.frozen_sequence_sha256 OR
                    observed.frozen_sequence_length
                        IS DISTINCT FROM expected.frozen_sequence_length OR
                    observed.uniprot_begin IS DISTINCT FROM expected.uniprot_begin OR
                    observed.uniprot_end IS DISTINCT FROM expected.uniprot_end OR
                    observed.interval_state IS DISTINCT FROM expected.interval_state OR
                    observed.frozen_interval_within_bounds IS DISTINCT FROM
                        CASE
                            WHEN expected.frozen_sequence_length IS NOT NULL
                             AND expected.interval_state = 'complete_ascending'
                                THEN expected.uniprot_begin >= 1
                                 AND expected.uniprot_end <=
                                        expected.frozen_sequence_length
                        END
                  )
            ) AS reconstructed_field_mismatches
        FROM expected_sifts_audit AS expected
        FULL OUTER JOIN {audit} AS observed USING (mapping_id)
        """,
    )
    sifts_release_sql = _sql_string(sifts_release)
    frozen_release_sql = _sql_string(frozen_release)
    _record_zero_counts(
        checks,
        connection,
        "sifts.release_interval_authorization",
        f"""
        SELECT
            count(*) FILTER (
                WHERE sifts_declared_uniprot_release
                        IS DISTINCT FROM {sifts_release_sql}
                   OR frozen_uniprot_release IS DISTINCT FROM {frozen_release_sql}
                   OR release_aligned
            ) AS release_guard_mismatches,
            count(*) FILTER (WHERE exact_sequence_identity_verified)
                AS unsupported_exact_identity_claims,
            count(*) FILTER (WHERE structural_mapping_authorized)
                AS prohibited_structural_mapping_authorizations,
            count(*) FILTER (WHERE label_authorized)
                AS prohibited_label_authorizations,
            count(*) FILTER (
                WHERE structural_mapping_state IS DISTINCT FROM CASE
                    WHEN taxonomy_resolution = 'no_taxonomy'
                        THEN 'unresolved_taxonomy'
                    WHEN NOT has_human_taxonomy
                        THEN 'out_of_scope_nonhuman'
                    WHEN interval_state = 'complete_descending'
                        THEN 'blocked_descending_interval'
                    WHEN frozen_sequence_id IS NULL
                        THEN 'unmatched_frozen_sequence'
                    ELSE 'blocked_release_mismatch'
                END
            ) AS structural_mapping_state_mismatches
        FROM {audit}
        """,
    )


def collect_output_metrics(
    connection: duckdb.DuckDBPyConnection,
    provider_counts: Mapping[str, Any],
) -> dict[str, Any]:
    participants = _view_name("participant_sequence_mappings")
    evidence = _view_name("evidence_mapping_summaries")
    projections = _view_name("huri_evidence_gene_pair_projections")
    pairs = _view_name("huri_pair_reconciliation")
    sifts = _view_name("sifts_chain_mapping_audit")

    participant_state_rows = connection.execute(
        f"""
        SELECT source_key, mapping_state, construct_confidence, count(*)
        FROM {participants}
        GROUP BY source_key, mapping_state, construct_confidence
        ORDER BY source_key, mapping_state, construct_confidence
        """
    ).fetchall()
    participant_states = {
        "|".join(str(value) for value in row[:3]): int(row[3])
        for row in participant_state_rows
    }

    row = connection.execute(
        f"""
        SELECT
            count(*),
            count(*) FILTER (WHERE reference_sequence_usable),
            count(*) FILTER (WHERE canonical_projection_usable),
            count(*) FILTER (WHERE strict_construct_eligible),
            count(*) FILTER (WHERE construct_confidence IN ('A', 'B')),
            count(*) FILTER (WHERE label_authorized)
        FROM {participants}
        """
    ).fetchone()
    assert row is not None
    participant_totals = dict(
        zip(
            (
                "participants",
                "reference_sequence_usable",
                "canonical_projection_usable",
                "strict_construct_eligible",
                "construct_a_or_b",
                "label_authorized",
            ),
            (int(value) for value in row),
            strict=True,
        )
    )

    row = connection.execute(
        f"""
        SELECT
            count(*),
            count(*) FILTER (WHERE binary_two_human_proteins),
            count(*) FILTER (WHERE reference_pair_usable),
            count(*) FILTER (WHERE canonical_pair_usable),
            count(*) FILTER (WHERE strict_construct_eligible),
            count(*) FILTER (WHERE label_authorized)
        FROM {evidence}
        """
    ).fetchone()
    assert row is not None
    evidence_totals = dict(
        zip(
            (
                "evidence_records",
                "binary_two_human_proteins",
                "reference_pair_usable",
                "canonical_pair_usable",
                "strict_construct_eligible",
                "label_authorized",
            ),
            (int(value) for value in row),
            strict=True,
        )
    )

    cursor = connection.execute(
        f"""
        SELECT
            source_dataset,
            count(*) AS detailed_evidence_rows,
            count(*) FILTER (WHERE unique_gene_pair)
                AS evidence_rows_with_unique_gene_pair,
            count(DISTINCT (gene_a, gene_b)) FILTER (WHERE unique_gene_pair)
                AS detailed_unique_gene_pairs,
            count(DISTINCT (orf_a, orf_b)) FILTER (WHERE unique_orf_pair)
                AS detailed_unique_orf_pairs,
            count(DISTINCT (ordered_orf_a, ordered_orf_b))
                FILTER (WHERE unique_orf_pair) AS detailed_ordered_orf_pairs,
            count(*) FILTER (
                WHERE representation_state = 'unresolved_gene_projection'
            ) AS unresolved_gene_projection_rows
        FROM {projections}
        GROUP BY source_dataset
        ORDER BY source_dataset
        """
    )
    projection_columns = [str(value[0]) for value in cursor.description]
    huri: dict[str, dict[str, int]] = {}
    for values in cursor.fetchall():
        record = dict(zip(projection_columns, values, strict=True))
        dataset = str(record.pop("source_dataset"))
        huri[dataset] = {key: int(value) for key, value in record.items()}

    cursor = connection.execute(
        f"""
        SELECT
            source_dataset,
            count(*) AS union_gene_pairs,
            count(*) FILTER (WHERE representation_state = 'matched_pair_view')
                AS matched_pairs,
            count(*) FILTER (WHERE representation_state = 'detailed_only')
                AS detailed_only_pairs,
            count(*) FILTER (WHERE representation_state = 'pair_view_only')
                AS pair_view_only_pairs,
            sum(pair_view_row_count) AS pair_view_rows,
            count(*) FILTER (WHERE self_pair AND pair_view_row_count > 0)
                AS pair_view_self_pairs
        FROM {pairs}
        GROUP BY source_dataset
        ORDER BY source_dataset
        """
    )
    pair_columns = [str(value[0]) for value in cursor.description]
    for values in cursor.fetchall():
        record = dict(zip(pair_columns, values, strict=True))
        dataset = str(record.pop("source_dataset"))
        huri.setdefault(dataset, {}).update(
            {key: int(value) for key, value in record.items()}
        )
    for dataset, metrics in huri.items():
        advertised = int(provider_counts[dataset])
        metrics["provider_advertised_pairs"] = advertised
        metrics["provider_minus_pair_view_rows"] = advertised - int(
            metrics["pair_view_rows"]
        )

    row = connection.execute(
        f"""
        SELECT
            count(*),
            count(*) FILTER (WHERE has_human_taxonomy),
            count(DISTINCT uniprot_accession)
                FILTER (WHERE has_human_taxonomy),
            count(DISTINCT uniprot_accession) FILTER (
                WHERE has_human_taxonomy
                  AND accession_match_state = 'primary_canonical_sequence'
            ),
            count(DISTINCT uniprot_accession) FILTER (
                WHERE has_human_taxonomy
                  AND accession_match_state = 'primary_field_without_canonical'
            ),
            count(DISTINCT uniprot_accession) FILTER (
                WHERE has_human_taxonomy
                  AND accession_match_state = 'additional_sequence_identifier'
            ),
            count(DISTINCT uniprot_accession) FILTER (
                WHERE has_human_taxonomy AND accession_match_state = 'absent'
            ),
            count(*) FILTER (WHERE interval_state = 'complete_descending'),
            count(*) FILTER (WHERE frozen_interval_within_bounds = false),
            count(*) FILTER (WHERE exact_sequence_identity_verified),
            count(*) FILTER (WHERE structural_mapping_authorized),
            count(*) FILTER (WHERE label_authorized)
        FROM {sifts}
        """
    ).fetchone()
    assert row is not None
    sifts_metrics = dict(
        zip(
            (
                "chain_mapping_rows",
                "human_chain_mapping_rows",
                "human_distinct_accessions",
                "human_primary_canonical_accessions",
                "human_primary_field_without_canonical_accessions",
                "human_additional_sequence_accessions",
                "human_absent_accessions",
                "descending_interval_rows",
                "frozen_out_of_bounds_rows",
                "exact_sequence_identity_verified_rows",
                "structural_mapping_authorized_rows",
                "label_authorized_rows",
            ),
            (int(value) for value in row),
            strict=True,
        )
    )
    return {
        "participant_mapping_states": participant_states,
        "participant_totals": participant_totals,
        "evidence_totals": evidence_totals,
        "huri_representation_reconciliation": huri,
        "sifts_release_alignment_audit": sifts_metrics,
    }


def normalize_manifest_metrics(manifest_metrics: Mapping[str, Any]) -> dict[str, Any]:
    participant_states = {
        "|".join(
            (
                str(row["source_key"]),
                str(row["mapping_state"]),
                str(row["construct_confidence"]),
            )
        ): int(row["participants"])
        for row in manifest_metrics["participant_mapping_states"]
    }
    huri = {}
    for row in manifest_metrics["huri_representation_reconciliation"]:
        record = dict(row)
        dataset = str(record.pop("source_dataset"))
        huri[dataset] = {key: int(value) for key, value in record.items()}
    return {
        "participant_mapping_states": participant_states,
        "participant_totals": {
            key: int(value)
            for key, value in manifest_metrics["participant_totals"].items()
        },
        "evidence_totals": {
            key: int(value)
            for key, value in manifest_metrics["evidence_totals"].items()
        },
        "huri_representation_reconciliation": huri,
        "sifts_release_alignment_audit": {
            key: int(value)
            for key, value in manifest_metrics["sifts_release_alignment_audit"].items()
        },
    }


__all__ = [
    "collect_output_metrics",
    "normalize_manifest_metrics",
    "register_canonical_views",
    "register_staging_views",
    "validate_contract_rows",
    "validate_evidence_summaries",
    "validate_huri_reconciliation",
    "validate_participant_mappings",
    "validate_sifts_audit",
    "validate_uniform_provenance_and_authorization",
]
