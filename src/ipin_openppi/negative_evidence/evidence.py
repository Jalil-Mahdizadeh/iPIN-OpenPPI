"""Build reproducible local positive and explicit-negative pair indexes."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import duckdb

from ipin_openppi.ingestion.common import stable_id
from ipin_openppi.reconciliation.policy import sql_string


def unordered_pair(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left <= right else (right, left)


def unordered_sequence_pair_id(left: str, right: str) -> str:
    first, second = unordered_pair(left, right)
    return stable_id("frozen-sequence-pair", first, second)


def unordered_accession_pair_id(left: str, right: str) -> str:
    first, second = unordered_pair(left, right)
    return stable_id("source-accession-pair", first, second)


def _glob(path: Path) -> str:
    return (path / "*.parquet").as_posix()


def register_evidence_views(
    connection: duckdb.DuckDBPyConnection, paths: Mapping[str, Path]
) -> None:
    """Register only the frozen local tables admitted by the audit policy."""
    table_paths = {
        "protein_sequences": paths["protein_sequences"],
        "identifier_mappings": paths["identifier_mappings"],
        "huri_evidence": paths["huri_evidence"],
        "huri_pair_views": paths["huri_pair_views"],
        "intact_evidence": paths["intact_evidence"],
        "intact_participants": paths["intact_participants"],
        "participant_mappings": paths["participant_sequence_mappings"],
        "evidence_summaries": paths["evidence_mapping_summaries"],
    }
    for view, path in table_paths.items():
        connection.execute(
            f"CREATE TEMP VIEW {view} AS SELECT * FROM read_parquet("
            f"{sql_string(_glob(path))})"
        )
    connection.execute(
        """
        CREATE TEMP VIEW combined_evidence AS
        SELECT * FROM huri_evidence
        UNION ALL BY NAME
        SELECT * FROM intact_evidence
        """
    )


def build_positive_pair_index(
    connection: duckdb.DuckDBPyConnection,
    *,
    permitted_pair_views: Iterable[str],
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    """Index current binary mapped positives and reproducible HuRI-family views."""
    connection.execute(
        """
        CREATE TEMP TABLE mapped_positive_evidence_pairs AS
        WITH mapped AS (
            SELECT
                evidence_id,
                source_key,
                min(mapped_sequence_sha256) AS sequence_sha256_a,
                max(mapped_sequence_sha256) AS sequence_sha256_b,
                count(*) AS participant_rows
            FROM participant_mappings
            WHERE reference_sequence_usable
            GROUP BY evidence_id, source_key
        )
        SELECT
            mapped.sequence_sha256_a,
            mapped.sequence_sha256_b,
            evidence.evidence_id,
            evidence.source_key,
            evidence.source_dataset,
            evidence.interaction_semantics,
            evidence.detection_method_ac,
            evidence.detection_method_name
        FROM mapped
        JOIN combined_evidence AS evidence
          ON evidence.evidence_id = mapped.evidence_id
         AND evidence.source_key = mapped.source_key
        JOIN evidence_summaries AS summary
          ON summary.evidence_id = mapped.evidence_id
         AND summary.source_key = mapped.source_key
        WHERE mapped.participant_rows = 2
          AND summary.reference_pair_usable
          AND evidence.observation_state = 'positive'
          AND evidence.participant_count = 2
          AND NOT evidence.original_nary
          AND NOT evidence.is_expanded_projection
        """
    )
    evidence_rows = connection.execute(
        """
        SELECT
            sequence_sha256_a,
            sequence_sha256_b,
            count(*)::BIGINT AS positive_evidence_count,
            count_if(interaction_semantics = 'direct_binary')::BIGINT
                AS qualifying_direct_evidence_count,
            count_if(source_key = 'intact_imex'
                AND interaction_semantics <> 'direct_binary')::BIGINT
                AS broader_intact_evidence_count,
            list(DISTINCT source_key ORDER BY source_key) AS source_keys,
            list(DISTINCT source_dataset ORDER BY source_dataset) AS source_datasets,
            list(DISTINCT interaction_semantics ORDER BY interaction_semantics)
                AS interaction_semantics,
            list(DISTINCT coalesce(detection_method_ac, 'missing') || ':' ||
                coalesce(detection_method_name, 'missing')
                ORDER BY coalesce(detection_method_ac, 'missing') || ':' ||
                    coalesce(detection_method_name, 'missing')) AS detection_methods
        FROM mapped_positive_evidence_pairs
        GROUP BY sequence_sha256_a, sequence_sha256_b
        """
    ).fetchall()
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in evidence_rows:
        key = unordered_pair(str(row[0]), str(row[1]))
        index[key] = {
            "positive_evidence_count": int(row[2]),
            "qualifying_direct_evidence_count": int(row[3]),
            "broader_intact_evidence_count": int(row[4]),
            "permitted_pair_view_count": 0,
            "source_keys": list(row[5]),
            "source_datasets": list(row[6]),
            "interaction_semantics": list(row[7]),
            "detection_methods": list(row[8]),
        }

    allowed = sorted(set(permitted_pair_views))
    if not allowed:
        raise ValueError("At least one permitted HuRI-family pair view is required")
    placeholders = ",".join(sql_string(value) for value in allowed)
    connection.execute(
        f"""
        CREATE TEMP TABLE unique_gene_sequence_map AS
        WITH candidates AS (
            SELECT
                mapping.identifier_versionless AS gene_id,
                sequence.sequence_sha256,
                sequence.uniprot_accession
            FROM identifier_mappings AS mapping
            JOIN protein_sequences AS sequence
              ON sequence.uniprot_accession = mapping.uniprot_accession
             AND sequence.canonical
            WHERE mapping.database = 'Ensembl'
        ), summarized AS (
            SELECT
                gene_id,
                min(sequence_sha256) AS sequence_sha256,
                count(DISTINCT sequence_sha256) AS sequence_hash_count
            FROM candidates
            GROUP BY gene_id
        )
        SELECT gene_id, sequence_sha256
        FROM summarized
        WHERE sequence_hash_count = 1
        """
    )
    view_rows = connection.execute(
        f"""
        WITH mapped_views AS (
            SELECT
                least(a.sequence_sha256, b.sequence_sha256) AS sequence_sha256_a,
                greatest(a.sequence_sha256, b.sequence_sha256) AS sequence_sha256_b,
                pair.source_dataset
            FROM huri_pair_views AS pair
            JOIN unique_gene_sequence_map AS a ON a.gene_id = pair.member_a
            JOIN unique_gene_sequence_map AS b ON b.gene_id = pair.member_b
            WHERE pair.source_dataset IN ({placeholders})
              AND pair.view_membership
        )
        SELECT
            sequence_sha256_a,
            sequence_sha256_b,
            count(*)::BIGINT AS pair_view_count,
            list(DISTINCT source_dataset ORDER BY source_dataset) AS source_datasets
        FROM mapped_views
        GROUP BY sequence_sha256_a, sequence_sha256_b
        """
    ).fetchall()
    for row in view_rows:
        key = unordered_pair(str(row[0]), str(row[1]))
        record = index.setdefault(
            key,
            {
                "positive_evidence_count": 0,
                "qualifying_direct_evidence_count": 0,
                "broader_intact_evidence_count": 0,
                "permitted_pair_view_count": 0,
                "source_keys": [],
                "source_datasets": [],
                "interaction_semantics": [],
                "detection_methods": [],
            },
        )
        record["permitted_pair_view_count"] += int(row[2])
        record["source_keys"] = sorted(set(record["source_keys"]) | {"huri"})
        record["source_datasets"] = sorted(set(record["source_datasets"]) | set(row[3]))
        record["interaction_semantics"] = sorted(
            set(record["interaction_semantics"]) | {"reported_direct_pair_view"}
        )
        record["detection_methods"] = sorted(
            set(record["detection_methods"]) | {"pair_view:no_record_level_assay"}
        )

    metrics = {
        "mapped_positive_evidence_rows": int(
            connection.execute(
                "SELECT count(*) FROM mapped_positive_evidence_pairs"
            ).fetchone()[0]
        ),
        "mapped_positive_evidence_unique_pairs": int(
            connection.execute(
                """
                SELECT count(*) FROM (
                    SELECT sequence_sha256_a, sequence_sha256_b
                    FROM mapped_positive_evidence_pairs GROUP BY ALL
                )
                """
            ).fetchone()[0]
        ),
        "mapped_permitted_pair_view_rows": sum(int(row[2]) for row in view_rows),
        "mapped_permitted_pair_view_unique_pairs": len(view_rows),
        "combined_positive_index_unique_pairs": len(index),
        "permitted_pair_views": allowed,
    }
    return index, metrics


@dataclass(frozen=True)
class IntactNegativeRecord:
    evidence: dict[str, Any]
    participants: tuple[dict[str, Any], ...]
    ordered_source_pair: tuple[str, str] | None
    unordered_source_pair: tuple[str, str] | None
    unordered_sequence_pair: tuple[str, str] | None

    @property
    def evidence_id(self) -> str:
        return str(self.evidence["evidence_id"])


def load_intact_negative_records(
    connection: duckdb.DuckDBPyConnection,
) -> list[IntactNegativeRecord]:
    fields = [
        "evidence_id",
        "source_record_id",
        "publication_ids",
        "participant_count",
        "original_nary",
        "interaction_semantics",
        "detection_method_ac",
        "detection_method_name",
        "host_taxid",
        "host_name",
        "attempted_state",
        "evaluability_state",
        "technical_state",
        "observation_state",
        "orientation_semantics",
        "context_json",
        "missingness_json",
    ]
    cursor = connection.execute(
        f"SELECT {','.join(fields)} FROM intact_evidence "
        "WHERE observation_state = 'negative' ORDER BY evidence_id"
    )
    evidence = {str(row[0]): dict(zip(fields, row)) for row in cursor.fetchall()}
    participant_fields = [
        "evidence_id",
        "participant_ordinal",
        "primary_identifier_db",
        "primary_identifier",
        "taxid",
        "orientation_role",
        "mapped_uniprot_accession",
        "mapped_isoform_id",
        "mapped_sequence_sha256",
        "reference_sequence_usable",
    ]
    participant_rows = connection.execute(
        """
        SELECT
            participant.evidence_id,
            participant.participant_ordinal,
            participant.primary_identifier_db,
            participant.primary_identifier,
            participant.taxid,
            participant.orientation_role,
            mapping.mapped_uniprot_accession,
            mapping.mapped_isoform_id,
            mapping.mapped_sequence_sha256,
            coalesce(mapping.reference_sequence_usable, false)
                AS reference_sequence_usable
        FROM intact_participants AS participant
        LEFT JOIN participant_mappings AS mapping
          ON mapping.participant_id = participant.participant_id
         AND mapping.evidence_id = participant.evidence_id
        WHERE participant.evidence_id IN (
            SELECT evidence_id FROM intact_evidence
            WHERE observation_state = 'negative'
        )
        ORDER BY participant.evidence_id, participant.participant_ordinal
        """
    ).fetchall()
    by_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in participant_rows:
        by_evidence[str(row[0])].append(dict(zip(participant_fields, row)))

    records: list[IntactNegativeRecord] = []
    for evidence_id, evidence_row in evidence.items():
        participants = tuple(by_evidence[evidence_id])
        ordered_source: tuple[str, str] | None = None
        sequence_pair: tuple[str, str] | None = None
        if len(participants) == 2:
            databases = {
                str(participant["primary_identifier_db"] or "").casefold()
                for participant in participants
            }
            identifiers = [
                participant["primary_identifier"] for participant in participants
            ]
            if databases <= {"uniprot", "uniprotkb"} and all(identifiers):
                ordered_source = (str(identifiers[0]), str(identifiers[1]))
            hashes = [
                participant["mapped_sequence_sha256"] for participant in participants
            ]
            if all(
                participant["reference_sequence_usable"] for participant in participants
            ) and all(hashes):
                sequence_pair = unordered_pair(str(hashes[0]), str(hashes[1]))
        records.append(
            IntactNegativeRecord(
                evidence=evidence_row,
                participants=participants,
                ordered_source_pair=ordered_source,
                unordered_source_pair=(
                    unordered_pair(*ordered_source) if ordered_source else None
                ),
                unordered_sequence_pair=sequence_pair,
            )
        )
    return records


def index_intact_negatives(
    records: Iterable[IntactNegativeRecord],
) -> tuple[
    dict[tuple[str, str], list[IntactNegativeRecord]],
    dict[tuple[str, str], list[IntactNegativeRecord]],
]:
    by_source: dict[tuple[str, str], list[IntactNegativeRecord]] = defaultdict(list)
    by_sequence: dict[tuple[str, str], list[IntactNegativeRecord]] = defaultdict(list)
    for record in records:
        if record.unordered_source_pair:
            by_source[record.unordered_source_pair].append(record)
        if record.unordered_sequence_pair:
            by_sequence[record.unordered_sequence_pair].append(record)
    return dict(by_source), dict(by_sequence)
