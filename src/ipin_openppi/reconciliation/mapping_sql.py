"""Build participant and evidence mapping relations in dependency order."""

from __future__ import annotations

import duckdb

from .candidate_sql import build_candidate_relations
from .evidence_mapping_sql import build_evidence_mapping_relation
from .participant_mapping_sql import build_participant_mapping_relation
from .policy import ReconciliationProvenance


def build_mapping_work_tables(
    connection: duckdb.DuckDBPyConnection,
    provenance: ReconciliationProvenance,
    candidate_priority: dict[str, int],
    ensembl_database_mapping: dict[str, str],
) -> None:
    build_candidate_relations(
        connection,
        candidate_priority,
        ensembl_database_mapping,
    )
    build_participant_mapping_relation(connection, provenance)
    build_evidence_mapping_relation(connection, provenance)
