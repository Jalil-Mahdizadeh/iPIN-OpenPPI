"""DuckDB orchestration and compact metrics for primary reconciliation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from .huri_sql import build_huri_work_tables
from .mapping_sql import build_mapping_work_tables
from .policy import ReconciliationProvenance, parquet_glob, sql_string
from .sifts_sql import build_sifts_work_table


def setup_input_views(
    connection: duckdb.DuckDBPyConnection, staging_root: Path
) -> None:
    """Register immutable staging tables with explicit source provenance."""

    huri_participants = sql_string(parquet_glob(staging_root, "huri", "participants"))
    intact_participants = sql_string(
        parquet_glob(staging_root, "intact_imex", "participants")
    )
    huri_evidence = sql_string(parquet_glob(staging_root, "huri", "evidence_records"))
    intact_evidence = sql_string(
        parquet_glob(staging_root, "intact_imex", "evidence_records")
    )
    huri_features = sql_string(
        parquet_glob(staging_root, "huri", "participant_features")
    )
    intact_features = sql_string(
        parquet_glob(staging_root, "intact_imex", "participant_features")
    )

    connection.execute(
        f"""
        CREATE TEMP VIEW participants AS
        SELECT 'huri' AS source_key, * FROM read_parquet({huri_participants})
        UNION ALL
        SELECT 'intact_imex' AS source_key, *
        FROM read_parquet({intact_participants})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW evidence AS
        SELECT * FROM read_parquet({huri_evidence})
        UNION ALL
        SELECT * FROM read_parquet({intact_evidence})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW participant_features AS
        SELECT * FROM read_parquet({huri_features})
        UNION ALL
        SELECT * FROM read_parquet({intact_features})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW sequences AS
        SELECT coalesce(isoform_id, uniprot_accession) AS sequence_id, *
        FROM read_parquet({sql_string(parquet_glob(staging_root, 'uniprot', 'protein_sequences'))})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW identifier_mappings AS
        SELECT *
        FROM read_parquet({sql_string(parquet_glob(staging_root, 'uniprot', 'identifier_mappings'))})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW huri_pair_views AS
        SELECT *
        FROM read_parquet({sql_string(parquet_glob(staging_root, 'huri', 'source_pair_views'))})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW sifts_chain_uniprot AS
        SELECT *
        FROM read_parquet({sql_string(parquet_glob(staging_root, 'pdb_sifts', 'sifts_chain_uniprot'))})
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW sifts_chain_taxonomy AS
        SELECT *
        FROM read_parquet({sql_string(parquet_glob(staging_root, 'pdb_sifts', 'sifts_chain_taxonomy'))})
        """
    )


def build_work_tables(
    connection: duckdb.DuckDBPyConnection,
    provenance: ReconciliationProvenance,
    candidate_priority: dict[str, int],
    ensembl_database_mapping: dict[str, str],
) -> None:
    build_mapping_work_tables(
        connection,
        provenance,
        candidate_priority,
        ensembl_database_mapping,
    )
    build_huri_work_tables(connection, provenance)
    build_sifts_work_table(connection, provenance)


OUTPUT_QUERIES: dict[str, str] = {
    "participant_sequence_mappings": (
        "SELECT * FROM participant_sequence_mappings_work "
        "ORDER BY source_key, participant_id"
    ),
    "evidence_mapping_summaries": (
        "SELECT * FROM evidence_mapping_summaries_work "
        "ORDER BY source_key, evidence_id"
    ),
    "huri_evidence_gene_pair_projections": (
        "SELECT * FROM huri_evidence_gene_pair_projections_work "
        "ORDER BY source_dataset, evidence_id"
    ),
    "huri_pair_reconciliation": (
        "SELECT * FROM huri_pair_reconciliation_work "
        "ORDER BY source_dataset, gene_a, gene_b"
    ),
    "sifts_chain_mapping_audit": (
        "SELECT * FROM sifts_chain_mapping_audit_work "
        "ORDER BY pdb_id, chain_id, mapping_id"
    ),
}


def _records(connection: duckdb.DuckDBPyConnection, query: str) -> list[dict[str, Any]]:
    cursor = connection.execute(query)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def collect_metrics(
    connection: duckdb.DuckDBPyConnection,
    provider_counts: dict[str, int],
) -> dict[str, Any]:
    """Collect compact deterministic audit metrics from work relations."""

    participant_states = _records(
        connection,
        """
        SELECT source_key, mapping_state, construct_confidence,
               count(*) AS participants
        FROM participant_sequence_mappings_work
        GROUP BY source_key, mapping_state, construct_confidence
        ORDER BY source_key, mapping_state, construct_confidence
        """,
    )
    participant_totals = _records(
        connection,
        """
        SELECT
            count(*) AS participants,
            count_if(reference_sequence_usable) AS reference_sequence_usable,
            count_if(canonical_projection_usable) AS canonical_projection_usable,
            count_if(strict_construct_eligible) AS strict_construct_eligible,
            count_if(construct_confidence IN ('A', 'B')) AS construct_a_or_b,
            count_if(label_authorized) AS label_authorized
        FROM participant_sequence_mappings_work
        """,
    )[0]
    evidence_totals = _records(
        connection,
        """
        SELECT
            count(*) AS evidence_records,
            count_if(binary_two_human_proteins) AS binary_two_human_proteins,
            count_if(reference_pair_usable) AS reference_pair_usable,
            count_if(canonical_pair_usable) AS canonical_pair_usable,
            count_if(strict_construct_eligible) AS strict_construct_eligible,
            count_if(label_authorized) AS label_authorized
        FROM evidence_mapping_summaries_work
        """,
    )[0]
    huri_projection = _records(
        connection,
        """
        SELECT
            source_dataset,
            count(*) AS detailed_evidence_rows,
            count_if(unique_gene_pair) AS evidence_rows_with_unique_gene_pair,
            count(DISTINCT (gene_a, gene_b))
                FILTER (WHERE unique_gene_pair) AS detailed_unique_gene_pairs,
            count(DISTINCT (orf_a, orf_b))
                FILTER (WHERE unique_orf_pair) AS detailed_unique_orf_pairs,
            count(DISTINCT (ordered_orf_a, ordered_orf_b))
                FILTER (WHERE unique_orf_pair) AS detailed_ordered_orf_pairs,
            count_if(representation_state = 'unresolved_gene_projection')
                AS unresolved_gene_projection_rows
        FROM huri_evidence_gene_pair_projections_work
        GROUP BY source_dataset
        ORDER BY source_dataset
        """,
    )
    huri_pairs = _records(
        connection,
        """
        SELECT
            source_dataset,
            count(*) AS union_gene_pairs,
            count_if(representation_state = 'matched_pair_view') AS matched_pairs,
            count_if(representation_state = 'detailed_only') AS detailed_only_pairs,
            count_if(representation_state = 'pair_view_only') AS pair_view_only_pairs,
            sum(pair_view_row_count) AS pair_view_rows,
            count_if(self_pair AND pair_view_row_count > 0) AS pair_view_self_pairs
        FROM huri_pair_reconciliation_work
        GROUP BY source_dataset
        ORDER BY source_dataset
        """,
    )
    by_dataset = {row["source_dataset"]: row for row in huri_projection}
    for row in huri_pairs:
        by_dataset.setdefault(row["source_dataset"], {}).update(row)
    for dataset, metrics in by_dataset.items():
        metrics["provider_advertised_pairs"] = int(provider_counts[dataset])
        metrics["provider_minus_pair_view_rows"] = int(provider_counts[dataset]) - int(
            metrics["pair_view_rows"]
        )

    sifts = _records(
        connection,
        """
        SELECT
            count(*) AS chain_mapping_rows,
            count_if(has_human_taxonomy) AS human_chain_mapping_rows,
            count(DISTINCT uniprot_accession)
                FILTER (WHERE has_human_taxonomy) AS human_distinct_accessions,
            count(DISTINCT uniprot_accession) FILTER (
                WHERE has_human_taxonomy
                  AND accession_match_state = 'primary_canonical_sequence'
            ) AS human_primary_canonical_accessions,
            count(DISTINCT uniprot_accession) FILTER (
                WHERE has_human_taxonomy
                  AND accession_match_state = 'primary_field_without_canonical'
            ) AS human_primary_field_without_canonical_accessions,
            count(DISTINCT uniprot_accession) FILTER (
                WHERE has_human_taxonomy
                  AND accession_match_state = 'additional_sequence_identifier'
            ) AS human_additional_sequence_accessions,
            count(DISTINCT uniprot_accession) FILTER (
                WHERE has_human_taxonomy AND accession_match_state = 'absent'
            ) AS human_absent_accessions,
            count_if(interval_state = 'complete_descending')
                AS descending_interval_rows,
            count_if(frozen_interval_within_bounds = false)
                AS frozen_out_of_bounds_rows,
            count_if(exact_sequence_identity_verified)
                AS exact_sequence_identity_verified_rows,
            count_if(structural_mapping_authorized)
                AS structural_mapping_authorized_rows,
            count_if(label_authorized) AS label_authorized_rows
        FROM sifts_chain_mapping_audit_work
        """,
    )[0]

    return {
        "participant_mapping_states": participant_states,
        "participant_totals": participant_totals,
        "evidence_totals": evidence_totals,
        "huri_representation_reconciliation": [
            by_dataset[key] for key in sorted(by_dataset)
        ],
        "sifts_release_alignment_audit": sifts,
    }


__all__ = [
    "OUTPUT_QUERIES",
    "ReconciliationProvenance",
    "build_work_tables",
    "collect_metrics",
    "setup_input_views",
]
