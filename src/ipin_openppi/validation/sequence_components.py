"""Independent fail-closed validation of eligibility and sequence components."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import stat
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import git_provenance, project_root_from, require_apptainer, stable_id
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.sequence_component_audit import SEQUENCE_COMPONENT_AUDIT_VERSION
from ipin_openppi.sequence_component_audit.pipeline import TABLES, _verify_inputs
from ipin_openppi.sequence_component_audit.support import (
    load_json,
    load_yaml,
    require_scoped_outputs,
    resolve_inside,
    validate_config,
)
from ipin_openppi.sequence_component_audit.tooling import verify_mmseqs_install
from ipin_openppi.validation.staging import Checks, _write_report


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _check_sidecar(checks: Checks, path: Path, check_id: str) -> str:
    digest = sha256_file(path)
    sidecar = path.with_name(path.name + ".sha256")
    tokens = sidecar.read_text(encoding="utf-8").split()
    checks.require(
        check_id,
        tokens == [digest, path.name],
        observed={"digest": digest, "tokens": tokens},
        expected={"digest": digest, "tokens": [digest, path.name]},
    )
    return digest


def _validate_run_inventory(
    checks: Checks, project_root: Path, run_root: Path, manifest: Mapping[str, Any]
) -> dict[str, Path]:
    declared: dict[str, Path] = {}
    errors = 0
    for record in manifest.get("files", []):
        path = Path(str(record.get("path")))
        if not path.is_absolute():
            path = project_root / path
        try:
            path = path.resolve(strict=True)
            path.relative_to(run_root)
            info = path.stat(follow_symlinks=False)
            if (
                path.is_symlink()
                or not stat.S_ISREG(info.st_mode)
                or info.st_mode & 0o222
                or info.st_size != int(record["bytes"])
                or sha256_file(path) != str(record["sha256"])
                or path.as_posix() in declared
            ):
                errors += 1
            declared[path.as_posix()] = path
        except Exception:
            errors += 1
    excluded = {run_root / "RUN_MANIFEST.json", run_root / "RUN_MANIFEST.json.sha256"}
    actual = {
        path.resolve().as_posix()
        for path in run_root.rglob("*")
        if path.is_file() and path not in excluded
    }
    checks.require(
        "inventory.run_files_complete_hashed_read_only",
        errors == 0 and set(declared) == actual,
        observed={"errors": errors, "declared": len(declared), "actual": len(actual)},
        expected={"errors": 0, "declared_equals_actual": True},
    )
    return declared


def _validate_canonical_inventory(
    checks: Checks,
    project_root: Path,
    canonical_root: Path,
    manifest: Mapping[str, Any],
    contract: Any,
) -> dict[str, list[Path]]:
    observed_tables = set(manifest.get("tables", {}))
    checks.require(
        "inventory.canonical_table_set",
        observed_tables == set(TABLES),
        observed=sorted(observed_tables),
        expected=sorted(TABLES),
    )
    result: dict[str, list[Path]] = {}
    for table in TABLES:
        summary = manifest["tables"][table]
        paths: list[Path] = []
        errors = 0
        rows = 0
        for index, record in enumerate(summary.get("files", [])):
            path = Path(str(record["path"]))
            if not path.is_absolute():
                path = project_root / path
            try:
                path = path.resolve(strict=True)
                path.relative_to(canonical_root)
                info = path.stat(follow_symlinks=False)
                parquet_rows = int(pq.ParquetFile(path).metadata.num_rows)
                expected_schema = contract.arrow_schema(table)
                expected_metadata = dict(expected_schema.metadata or {})
                expected_metadata.update(
                    {
                        b"ipin.audit_version": SEQUENCE_COMPONENT_AUDIT_VERSION.encode(),
                        b"ipin.audit_git_commit": str(manifest["git"]["commit"]).encode(),
                        b"ipin.container_sif_sha256": str(
                            manifest["runtime"]["container_sif_sha256"]
                        ).encode(),
                        b"ipin.primary_design": b"reference_sequence_positive_unlabeled_ranking",
                        b"ipin.candidate_pair_materialized": b"false",
                        b"ipin.split_assignment_constructed": b"false",
                    }
                )
                observed_schema = pq.read_schema(path)
                if (
                    path.parent != canonical_root / table
                    or path.name != f"part-{index:05d}.parquet"
                    or path.is_symlink()
                    or not stat.S_ISREG(info.st_mode)
                    or info.st_mode & 0o222
                    or info.st_size != int(record["bytes"])
                    or parquet_rows != int(record["rows"])
                    or sha256_file(path) != str(record["sha256"])
                    or not observed_schema.remove_metadata().equals(
                        expected_schema.remove_metadata()
                    )
                    or dict(observed_schema.metadata or {}) != expected_metadata
                ):
                    errors += 1
                rows += parquet_rows
                paths.append(path)
            except Exception:
                errors += 1
        checks.require(
            f"inventory.{table}.parts_hash_schema_read_only",
            errors == 0
            and rows == int(summary.get("rows", -1))
            and len(paths) == int(summary.get("parts", -1)),
            observed={"errors": errors, "rows": rows, "parts": len(paths)},
            expected={
                "errors": 0,
                "rows": int(summary.get("rows", -1)),
                "parts": int(summary.get("parts", -1)),
            },
        )
        result[table] = paths
    return result


def _register_views(
    connection: duckdb.DuckDBPyConnection,
    input_files: Mapping[str, Sequence[Path]],
    output_files: Mapping[str, Sequence[Path]],
) -> None:
    for table, paths in input_files.items():
        connection.read_parquet([path.as_posix() for path in paths]).create_view(table)
    for table, paths in output_files.items():
        connection.read_parquet([path.as_posix() for path in paths]).create_view(
            f"audit_{table}"
        )


def _independent_eligibility(
    checks: Checks, connection: duckdb.DuckDBPyConnection, config: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, tuple[str, str | None]]]:
    policy = config["eligibility_policy"]
    connection.execute(
        """
        CREATE OR REPLACE TEMP VIEW independent_candidates AS
        SELECT DISTINCT sp.ensembl_gene_id, seq.uniprot_accession,
               seq.protein_sequence_id, seq.sequence_sha256, seq.sequence_length,
               seq.sequence, seq.source_release, seq.raw_file_path,
               seq.raw_file_sha256
        FROM huri_space_membership sp
        JOIN identifier_mappings identifiers
          ON identifiers.database = ?
         AND identifiers.identifier_versionless = sp.ensembl_gene_id
         AND identifiers.source_release = ?
        JOIN protein_sequences seq
          ON seq.uniprot_accession = identifiers.uniprot_accession
         AND seq.canonical AND seq.taxid = ? AND seq.source_release = ?
        WHERE sp.in_space_3
        """,
        [
            str(policy["identifier_database"]),
            str(policy["frozen_uniprot_release"]),
            int(policy["frozen_human_taxid"]),
            str(policy["frozen_uniprot_release"]),
        ],
    )
    connection.execute(
        """
        CREATE OR REPLACE TEMP VIEW independent_gene_eligibility AS
        WITH grouped AS (
          SELECT sp.space_record_id, sp.ensembl_gene_id,
                 sp.raw_file_path, sp.raw_locator,
                 count(DISTINCT c.uniprot_accession)::INTEGER AS accession_count,
                 count(DISTINCT c.sequence_sha256)::INTEGER AS hash_count,
                 coalesce(
                   list(DISTINCT c.uniprot_accession ORDER BY c.uniprot_accession)
                     FILTER (WHERE c.uniprot_accession IS NOT NULL),
                   []::VARCHAR[]
                 ) AS accessions,
                 coalesce(
                   list(DISTINCT c.sequence_sha256 ORDER BY c.sequence_sha256)
                     FILTER (WHERE c.sequence_sha256 IS NOT NULL),
                   []::VARCHAR[]
                 ) AS hashes,
                 CASE WHEN count(DISTINCT c.sequence_sha256) = 1
                      THEN min(c.sequence_sha256) ELSE NULL END AS selected_hash,
                 CASE WHEN count(DISTINCT c.sequence_sha256) = 1
                      THEN min(c.sequence_length) ELSE NULL END AS selected_length
          FROM huri_space_membership sp
          LEFT JOIN independent_candidates c USING (ensembl_gene_id)
          WHERE sp.in_space_3
          GROUP BY sp.space_record_id, sp.ensembl_gene_id,
                   sp.raw_file_path, sp.raw_locator
        )
        SELECT *,
          CASE
            WHEN hash_count = 0 THEN 'unmapped'
            WHEN hash_count > 1 THEN 'ambiguous_multiple_sequences'
            WHEN accession_count > 1 THEN 'sequence_equivalent_accessions'
            ELSE 'unique_reference_sequence'
          END AS mapping_state,
          hash_count = 1 AS eligibility_usable,
          CASE
            WHEN hash_count = 0 THEN 'unmapped'
            WHEN hash_count > 1 THEN 'ambiguous_multiple_sequences'
            ELSE 'none'
          END AS exclusion_reason
        FROM grouped
        """
    )
    mismatch = int(
        connection.execute(
            """
            SELECT count(*) FROM audit_space_iii_gene_eligibility audit
            FULL OUTER JOIN independent_gene_eligibility expected
              USING (ensembl_gene_id)
            WHERE audit.space_record_id IS DISTINCT FROM expected.space_record_id
               OR audit.in_space_iii IS DISTINCT FROM true
               OR audit.mapping_state IS DISTINCT FROM expected.mapping_state
               OR audit.candidate_uniprot_accessions IS DISTINCT FROM expected.accessions
               OR audit.candidate_sequence_sha256s IS DISTINCT FROM expected.hashes
               OR audit.candidate_accession_count IS DISTINCT FROM expected.accession_count
               OR audit.candidate_sequence_hash_count IS DISTINCT FROM expected.hash_count
               OR audit.selected_sequence_sha256 IS DISTINCT FROM expected.selected_hash
               OR audit.selected_sequence_length IS DISTINCT FROM expected.selected_length
               OR audit.eligibility_usable IS DISTINCT FROM expected.eligibility_usable
               OR audit.exclusion_reason IS DISTINCT FROM expected.exclusion_reason
               OR audit.source_raw_file_path IS DISTINCT FROM expected.raw_file_path
               OR audit.source_raw_locator IS DISTINCT FROM expected.raw_locator
            """
        ).fetchone()[0]
    )
    identifier_errors = 0
    for record_id, gene_id in connection.execute(
        "SELECT eligibility_record_id, ensembl_gene_id FROM audit_space_iii_gene_eligibility"
    ).fetchall():
        identifier_errors += int(
            str(record_id) != stable_id("space3-eligibility", str(gene_id))
        )
    checks.require(
        "eligibility.every_gene_independently_recomputed",
        mismatch == 0 and identifier_errors == 0,
        observed={"row_mismatches": mismatch, "identifier_errors": identifier_errors},
        expected={"row_mismatches": 0, "identifier_errors": 0},
    )
    connection.execute(
        """
        CREATE OR REPLACE TEMP VIEW independent_eligible_sequences AS
        SELECT c.sequence_sha256,
               min(c.sequence_length)::BIGINT AS sequence_length,
               min(c.sequence) AS sequence,
               min(c.uniprot_accession) AS representative_accession,
               list(DISTINCT c.uniprot_accession ORDER BY c.uniprot_accession) AS accessions,
               list(DISTINCT c.protein_sequence_id ORDER BY c.protein_sequence_id) AS sequence_ids,
               list(DISTINCT c.ensembl_gene_id ORDER BY c.ensembl_gene_id) AS gene_ids,
               list(DISTINCT c.raw_file_path ORDER BY c.raw_file_path) AS raw_paths,
               list(DISTINCT c.raw_file_sha256 ORDER BY c.raw_file_sha256) AS raw_hashes,
               min(c.source_release) AS source_release,
               count(DISTINCT c.uniprot_accession)::INTEGER AS accession_count,
               count(DISTINCT c.ensembl_gene_id)::INTEGER AS gene_count,
               count(DISTINCT c.sequence)::INTEGER AS distinct_sequences,
               count(DISTINCT c.sequence_length)::INTEGER AS distinct_lengths
        FROM independent_candidates c
        JOIN independent_gene_eligibility g USING (ensembl_gene_id)
        WHERE g.eligibility_usable AND c.sequence_sha256 = g.selected_hash
        GROUP BY c.sequence_sha256
        """
    )
    sequence_mismatch = int(
        connection.execute(
            """
            SELECT count(*) FROM audit_eligible_reference_sequences audit
            FULL OUTER JOIN independent_eligible_sequences expected
              ON audit.reference_sequence_sha256 = expected.sequence_sha256
            WHERE audit.sequence_length IS DISTINCT FROM expected.sequence_length
               OR audit.sequence IS DISTINCT FROM expected.sequence
               OR audit.representative_uniprot_accession IS DISTINCT FROM expected.representative_accession
               OR audit.uniprot_accessions IS DISTINCT FROM expected.accessions
               OR audit.protein_sequence_ids IS DISTINCT FROM expected.sequence_ids
               OR audit.space_iii_gene_ids IS DISTINCT FROM expected.gene_ids
               OR audit.accession_count IS DISTINCT FROM expected.accession_count
               OR audit.gene_count IS DISTINCT FROM expected.gene_count
               OR audit.frozen_uniprot_release IS DISTINCT FROM expected.source_release
               OR audit.source_raw_file_paths IS DISTINCT FROM expected.raw_paths
               OR audit.source_raw_file_sha256s IS DISTINCT FROM expected.raw_hashes
               OR expected.distinct_sequences != 1 OR expected.distinct_lengths != 1
            """
        ).fetchone()[0]
    )
    residue_errors = 0
    seleno_sequences = 0
    seleno_residues = 0
    standard = set(str(policy["standard_amino_acids"]))
    allowed = set(str(policy["source_preserved_amino_acids"]))
    for sequence_hash, sequence, length, contains_u, symbols in connection.execute(
        """
        SELECT reference_sequence_sha256, sequence, sequence_length,
               contains_selenocysteine, nonstandard_residue_symbols
        FROM audit_eligible_reference_sequences
        """
    ).fetchall():
        sequence = str(sequence)
        observed_hash = hashlib.sha256(sequence.encode("ascii")).hexdigest()
        expected_symbols = sorted(set(sequence) - standard)
        residue_errors += int(
            observed_hash != str(sequence_hash)
            or len(sequence) != int(length)
            or bool(contains_u) != ("U" in sequence)
            or list(symbols) != expected_symbols
            or bool(set(sequence) - allowed)
        )
        seleno_sequences += int("U" in sequence)
        seleno_residues += sequence.count("U")
    checks.require(
        "eligibility.distinct_sequences_independently_recomputed",
        sequence_mismatch == 0 and residue_errors == 0,
        observed={"row_mismatches": sequence_mismatch, "residue_errors": residue_errors},
        expected={"row_mismatches": 0, "residue_errors": 0},
    )
    state_counts = {
        str(state): int(count)
        for state, count in connection.execute(
            "SELECT mapping_state, count(*) FROM independent_gene_eligibility GROUP BY mapping_state ORDER BY mapping_state"
        ).fetchall()
    }
    sequence_count = int(
        connection.execute("SELECT count(*) FROM independent_eligible_sequences").fetchone()[0]
    )
    accession_count = int(
        connection.execute(
            "SELECT count(DISTINCT accession) FROM independent_eligible_sequences, unnest(accessions) u(accession)"
        ).fetchone()[0]
    )
    metrics = {
        "space_iii_genes": sum(state_counts.values()),
        "mapping_states": state_counts,
        "eligible_space_iii_genes": state_counts.get("unique_reference_sequence", 0)
        + state_counts.get("sequence_equivalent_accessions", 0),
        "eligible_reference_sequences": sequence_count,
        "eligible_uniprot_accessions": accession_count,
        "exact_unordered_candidate_count": sequence_count * (sequence_count - 1) // 2,
        "candidate_pair_rows_materialized": False,
        "candidate_universe_tested": False,
        "eligible_sequences_with_selenocysteine": seleno_sequences,
        "eligible_selenocysteine_residues": seleno_residues,
    }
    mapping_by_gene = {
        str(gene): (str(state), None if selected is None else str(selected))
        for gene, state, selected in connection.execute(
            "SELECT ensembl_gene_id, mapping_state, selected_hash FROM independent_gene_eligibility"
        ).fetchall()
    }
    return metrics, mapping_by_gene


def _parse_alignments_independently(
    checks: Checks,
    alignment_path: Path,
    normalized_path: Path,
    sequence_lengths: Mapping[str, int],
    config: Mapping[str, Any],
) -> tuple[dict[tuple[str, str], tuple[float, float, int]], dict[str, Any]]:
    minimum_identity = float(config["sequence_components"]["search_minimum_identity"])
    minimum_coverage = float(config["sequence_components"]["minimum_endpoint_coverage"])
    edges: dict[tuple[str, str], tuple[float, float, int]] = {}
    self_queries: set[str] = set()
    records = 0
    errors = 0
    with alignment_path.open("rt", encoding="utf-8", newline="") as handle:
        for fields in csv.reader(handle, delimiter="\t"):
            records += 1
            try:
                if len(fields) != 12:
                    raise ValueError("wrong field count")
                query, target = fields[:2]
                mismatch, alnlen, qstart, qend, qlen, tstart, tend, tlen = map(
                    int, fields[2:10]
                )
                evalue, bits = map(float, fields[10:12])
                if query not in sequence_lengths or target not in sequence_lengths:
                    raise ValueError("unknown endpoint")
                if (
                    alnlen <= 0
                    or mismatch < 0
                    or mismatch > alnlen
                    or qlen != sequence_lengths[query]
                    or tlen != sequence_lengths[target]
                    or not (1 <= qstart <= qlen and 1 <= qend <= qlen)
                    or not (1 <= tstart <= tlen and 1 <= tend <= tlen)
                    or not math.isfinite(evalue)
                    or not math.isfinite(bits)
                ):
                    raise ValueError("invalid alignment values")
                query_span = abs(qend - qstart) + 1
                target_span = abs(tend - tstart) + 1
                derived_identical = query_span + target_span - alnlen - mismatch
                if derived_identical < 0:
                    raise ValueError("negative derived identical-residue count")
                identity = derived_identical / alnlen
                min_coverage = min(
                    query_span / qlen,
                    target_span / tlen,
                )
                if identity + 1e-12 < minimum_identity or min_coverage + 1e-12 < minimum_coverage:
                    raise ValueError("alignment below frozen search criteria")
                if query == target:
                    self_queries.add(query)
                    continue
                key = tuple(sorted((query, target)))
                old_identity, old_coverage, old_count = edges.get(key, (0.0, 0.0, 0))
                edges[key] = (
                    max(old_identity, identity),
                    max(old_coverage, min_coverage),
                    old_count + 1,
                )
            except Exception:
                errors += 1
    normalized_errors = 0
    normalized_rows = 0
    for batch in pq.ParquetFile(normalized_path).iter_batches(batch_size=100000):
        for row in batch.to_pylist():
            normalized_rows += 1
            key = (str(row["sequence_a_sha256"]), str(row["sequence_b_sha256"]))
            expected = edges.get(key)
            if (
                expected is None
                or abs(float(row["maximum_identity"]) - expected[0]) > 1e-12
                or abs(float(row["maximum_minimum_endpoint_coverage"]) - expected[1]) > 1e-12
                or int(row["supporting_alignment_records"]) != expected[2]
            ):
                normalized_errors += 1
    checks.require(
        "alignment.raw_and_normalized_edges_independently_recomputed",
        errors == 0
        and len(self_queries) == len(sequence_lengths)
        and normalized_errors == 0
        and normalized_rows == len(edges),
        observed={
            "raw_records": records,
            "raw_errors": errors,
            "self_queries": len(self_queries),
            "normalized_rows": normalized_rows,
            "independent_edges": len(edges),
            "normalized_errors": normalized_errors,
        },
        expected={
            "raw_errors": 0,
            "self_queries": len(sequence_lengths),
            "normalized_rows_equals_independent_edges": True,
            "normalized_errors": 0,
        },
    )
    metrics = {
        "raw_alignment_records": records,
        "self_match_query_sequences": len(self_queries),
        "normalized_nonself_edges": len(edges),
        "raw_alignment_sha256": sha256_file(alignment_path),
        "normalized_edges_sha256": sha256_file(normalized_path),
        "identity_uses_integer_derived_identical_over_alnlen": True,
        "minimum_endpoint_coverage_reverified": minimum_coverage,
    }
    return edges, metrics


class _IndependentDisjointSet:
    def __init__(self, nodes: Iterable[str]) -> None:
        self.parent = {node: node for node in sorted(set(nodes))}

    def root(self, node: str) -> str:
        path: list[str] = []
        while self.parent[node] != node:
            path.append(node)
            node = self.parent[node]
        for member in path:
            self.parent[member] = node
        return node

    def merge(self, endpoint_a: str, endpoint_b: str) -> None:
        root_a, root_b = self.root(endpoint_a), self.root(endpoint_b)
        if root_a != root_b:
            keep, remove = sorted((root_a, root_b))
            self.parent[remove] = keep

    def groups(self) -> list[tuple[str, ...]]:
        values: dict[str, list[str]] = {}
        for node in sorted(self.parent):
            values.setdefault(self.root(node), []).append(node)
        return sorted(tuple(group) for group in values.values())


def _nearest_rank(values: Sequence[int], fraction: float) -> int:
    return sorted(values)[max(0, math.ceil(fraction * len(values)) - 1)]


def _independent_components(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    edges: Mapping[tuple[str, str], tuple[float, float, int]],
    sequence_hashes: Sequence[str],
    config: Mapping[str, Any],
) -> tuple[dict[int, dict[str, tuple[str, str, int, int]]], dict[str, Any]]:
    expected_assignments: dict[int, dict[str, tuple[str, str, int, int]]] = {}
    summaries: dict[str, Any] = {}
    errors = 0
    for threshold in map(int, config["sequence_components"]["emitted_thresholds_percent"]):
        disjoint = _IndependentDisjointSet(sequence_hashes)
        retained_edges = 0
        for (endpoint_a, endpoint_b), (identity, _, _) in sorted(edges.items()):
            if identity + 1e-12 >= threshold / 100.0:
                disjoint.merge(endpoint_a, endpoint_b)
                retained_edges += 1
        assignments: dict[str, tuple[str, str, int, int]] = {}
        groups = disjoint.groups()
        for members in groups:
            component_id = stable_id(f"seqcomp-{threshold}", *members)
            for rank, sequence_hash in enumerate(members, start=1):
                assignments[sequence_hash] = (
                    component_id,
                    members[0],
                    len(members),
                    rank,
                )
        expected_assignments[threshold] = assignments
        sizes = [len(group) for group in groups]
        summaries[str(threshold)] = {
            "identity_threshold_percent": threshold,
            "sequence_count": len(sequence_hashes),
            "edge_count": retained_edges,
            "component_count": len(groups),
            "singleton_components": sum(size == 1 for size in sizes),
            "largest_component_size": max(sizes),
            "component_size_q50": _nearest_rank(sizes, 0.50),
            "component_size_q90": _nearest_rank(sizes, 0.90),
            "component_size_q95": _nearest_rank(sizes, 0.95),
            "component_size_q99": _nearest_rank(sizes, 0.99),
        }
    output_rows = connection.execute(
        """
        SELECT identity_threshold_percent, reference_sequence_sha256,
               assignment_id, component_id, component_representative_sha256,
               component_size, component_member_rank,
               minimum_endpoint_coverage, component_algorithm,
               mmseqs_release, mmseqs_binary_sha256,
               candidate_pair_materialized, evidence_indicator_constructed,
               negative_label_constructed, split_assignment_constructed,
               model_use_authorized
        FROM audit_sequence_component_assignments
        """
    ).fetchall()
    seen: set[tuple[int, str]] = set()
    for row in output_rows:
        threshold, sequence_hash = int(row[0]), str(row[1])
        key = (threshold, sequence_hash)
        expected = expected_assignments.get(threshold, {}).get(sequence_hash)
        errors += int(
            key in seen
            or expected is None
            or str(row[2]) != stable_id("seqcomp-assignment", threshold, sequence_hash)
            or tuple((str(row[3]), str(row[4]), int(row[5]), int(row[6]))) != expected
            or float(row[7]) != float(config["sequence_components"]["minimum_endpoint_coverage"])
            or str(row[8]) != str(config["sequence_components"]["algorithm"])
            or str(row[9]) != str(config["mmseqs2"]["release"])
            or str(row[10]) != str(config["mmseqs2"]["binary_sha256"])
            or any(bool(value) for value in row[11:])
        )
        seen.add(key)
    expected_keys = {
        (threshold, sequence_hash)
        for threshold, assignments in expected_assignments.items()
        for sequence_hash in assignments
    }
    checks.require(
        "components.every_assignment_independently_recomputed",
        errors == 0 and seen == expected_keys,
        observed={"errors": errors, "rows": len(seen), "expected_rows": len(expected_keys)},
        expected={"errors": 0, "rows_equal": True},
    )
    nested_errors = 0
    for high, low in ((40, 30), (30, 20)):
        low_components_by_high: dict[str, set[str]] = {}
        for sequence_hash in sequence_hashes:
            high_id = expected_assignments[high][sequence_hash][0]
            low_id = expected_assignments[low][sequence_hash][0]
            low_components_by_high.setdefault(high_id, set()).add(low_id)
        nested_errors += sum(len(values) != 1 for values in low_components_by_high.values())
    checks.require(
        "components.lower_thresholds_only_merge_components",
        nested_errors == 0,
        observed=nested_errors,
        expected=0,
    )
    return expected_assignments, summaries


def _independent_positive_metrics(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    mapping_by_gene: Mapping[str, tuple[str, str | None]],
    components: Mapping[int, Mapping[str, tuple[str, str, int, int]]],
    component_summaries: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    policy = config["positive_mapping_policy"]
    datasets = [str(policy["aggregate_union_name"]), *map(str, policy["source_datasets"])]
    counters = {dataset: Counter() for dataset in datasets}
    pairs = {dataset: set() for dataset in datasets}
    for source, unique, raw_a, raw_b, label_authorized in connection.execute(
        "SELECT source_dataset, unique_gene_pair, gene_a, gene_b, label_authorized FROM huri_evidence_gene_pair_projections"
    ).fetchall():
        source = str(source)
        gene_a = None if raw_a is None else str(raw_a)
        gene_b = None if raw_b is None else str(raw_b)
        if source not in policy["source_datasets"] or bool(label_authorized):
            raise RuntimeError("Unexpected positive projection scope")
        pair: tuple[str, str] | None = None
        if not bool(unique) or not gene_a or not gene_b:
            state = "unresolved_gene_projection"
        elif gene_a not in mapping_by_gene or gene_b not in mapping_by_gene:
            state = "outside_space_iii"
        elif mapping_by_gene[gene_a][0] == "unmapped" or mapping_by_gene[gene_b][0] == "unmapped":
            state = "unmapped_endpoint"
        elif mapping_by_gene[gene_a][0] == "ambiguous_multiple_sequences" or mapping_by_gene[gene_b][0] == "ambiguous_multiple_sequences":
            state = "ambiguous_endpoint"
        else:
            sequence_a = mapping_by_gene[gene_a][1]
            sequence_b = mapping_by_gene[gene_b][1]
            assert sequence_a is not None and sequence_b is not None
            normalized = tuple(sorted((sequence_a, sequence_b)))
            if normalized[0] == normalized[1]:
                state = "same_reference_sequence"
            else:
                state = "eligible_distinct_reference_sequence_pair"
                pair = normalized
        for dataset in (source, str(policy["aggregate_union_name"])):
            counters[dataset]["source_evidence_rows"] += 1
            counters[dataset][state] += 1
            if pair is not None:
                pairs[dataset].add(pair)

    output_mapping = {
        str(row[1]): row
        for row in connection.execute(
            "SELECT * FROM audit_positive_mapping_aggregates"
        ).fetchall()
    }
    columns = [
        item[0]
        for item in connection.execute("DESCRIBE audit_positive_mapping_aggregates").fetchall()
    ]
    mapping_metrics: dict[str, Any] = {}
    mapping_errors = 0
    for dataset in datasets:
        counter = counters[dataset]
        source_rows = int(counter["source_evidence_rows"])
        values = {
            "aggregate_id": stable_id("positive-mapping-aggregate", dataset),
            "source_dataset": dataset,
            "source_evidence_rows": source_rows,
            "resolved_unique_gene_pair_rows": source_rows
            - int(counter["unresolved_gene_projection"]),
            "eligible_reference_sequence_pair_evidence_rows": int(
                counter["eligible_distinct_reference_sequence_pair"]
            ),
            "distinct_eligible_reference_sequence_pairs": len(pairs[dataset]),
            "unresolved_gene_projection_rows": int(counter["unresolved_gene_projection"]),
            "outside_space_iii_rows": int(counter["outside_space_iii"]),
            "unmapped_endpoint_rows": int(counter["unmapped_endpoint"]),
            "ambiguous_endpoint_rows": int(counter["ambiguous_endpoint"]),
            "same_reference_sequence_rows": int(counter["same_reference_sequence"]),
            "eligible_evidence_fraction": int(
                counter["eligible_distinct_reference_sequence_pair"]
            )
            / source_rows,
            "pair_rows_emitted": False,
            "evidence_indicator_constructed": False,
            "interaction_label_constructed": False,
            "negative_label_constructed": False,
            "prevalence_estimated": False,
            "calibration_performed": False,
        }
        observed = dict(zip(columns, output_mapping[dataset]))
        mapping_errors += int(observed != values)
        mapping_metrics[dataset] = values
    checks.require(
        "positive_mapping.aggregate_only_recomputation",
        mapping_errors == 0 and len(output_mapping) == len(datasets),
        observed={"errors": mapping_errors, "rows": len(output_mapping)},
        expected={"errors": 0, "rows": len(datasets)},
    )

    feasibility_columns = [
        item[0]
        for item in connection.execute("DESCRIBE audit_positive_component_feasibility").fetchall()
    ]
    output_feasibility = {
        (str(row[1]), int(row[2])): dict(zip(feasibility_columns, row))
        for row in connection.execute(
            "SELECT * FROM audit_positive_component_feasibility"
        ).fetchall()
    }
    feasibility_metrics: dict[str, Any] = {}
    feasibility_errors = 0
    for dataset in datasets:
        endpoints = {endpoint for pair in pairs[dataset] for endpoint in pair}
        for threshold in map(int, config["sequence_components"]["emitted_thresholds_percent"]):
            assignments = components[threshold]
            within = sum(assignments[a][0] == assignments[b][0] for a, b in pairs[dataset])
            exposed = {assignments[endpoint][0] for endpoint in endpoints}
            summary = component_summaries[str(threshold)]
            values = {
                "aggregate_id": stable_id("positive-component-feasibility", dataset, threshold),
                "source_dataset": dataset,
                "identity_threshold_percent": threshold,
                "distinct_eligible_reference_sequence_pairs": len(pairs[dataset]),
                "positive_endpoint_sequences": len(endpoints),
                "positive_exposed_components": len(exposed),
                "within_component_pair_count": within,
                "cross_component_pair_count": len(pairs[dataset]) - within,
                "total_components": int(summary["component_count"]),
                "singleton_components": int(summary["singleton_components"]),
                "largest_component_size": int(summary["largest_component_size"]),
                "total_positive_pair_floor_500_met": len(pairs[dataset])
                >= int(policy["minimum_later_held_out_positive_pairs"]),
                "total_component_floor_50_met": int(summary["component_count"])
                >= int(policy["minimum_later_independent_sequence_components"]),
                "held_out_floor_assessed": False,
                "later_split_feasibility_determined": False,
                "pair_rows_emitted": False,
                "split_assignment_constructed": False,
                "c1_c2_c3_assignment_constructed": False,
            }
            feasibility_errors += int(output_feasibility.get((dataset, threshold)) != values)
            feasibility_metrics[f"{dataset}:{threshold}"] = values
    checks.require(
        "positive_mapping.component_feasibility_aggregate_only",
        feasibility_errors == 0 and len(output_feasibility) == len(feasibility_metrics),
        observed={"errors": feasibility_errors, "rows": len(output_feasibility)},
        expected={"errors": 0, "rows": len(feasibility_metrics)},
    )
    return mapping_metrics, feasibility_metrics


def _scope_guards(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    manifest: Mapping[str, Any],
    audit_report: Mapping[str, Any],
) -> None:
    guard_columns = {
        "audit_space_iii_gene_eligibility": [
            "candidate_pair_materialized",
            "evidence_indicator_constructed",
            "negative_label_constructed",
            "split_assignment_constructed",
            "model_use_authorized",
        ],
        "audit_eligible_reference_sequences": [
            "candidate_pair_materialized",
            "evidence_indicator_constructed",
            "negative_label_constructed",
            "split_assignment_constructed",
            "model_use_authorized",
        ],
        "audit_sequence_component_assignments": [
            "candidate_pair_materialized",
            "evidence_indicator_constructed",
            "negative_label_constructed",
            "split_assignment_constructed",
            "model_use_authorized",
        ],
        "audit_positive_mapping_aggregates": [
            "pair_rows_emitted",
            "evidence_indicator_constructed",
            "interaction_label_constructed",
            "negative_label_constructed",
            "prevalence_estimated",
            "calibration_performed",
        ],
        "audit_positive_component_feasibility": [
            "held_out_floor_assessed",
            "later_split_feasibility_determined",
            "pair_rows_emitted",
            "split_assignment_constructed",
            "c1_c2_c3_assignment_constructed",
        ],
    }
    true_guards = 0
    for table, columns in guard_columns.items():
        expression = " OR ".join(columns)
        true_guards += int(
            connection.execute(f"SELECT count(*) FROM {table} WHERE {expression}").fetchone()[0]
        )
    manifest_false = all(
        manifest.get(key) is False
        for key in (
            "candidate_pair_materialization_performed",
            "candidate_universe_called_tested",
            "evidence_indicator_construction_performed",
            "interaction_label_construction_performed",
            "negative_label_construction_performed",
            "pseudo_negative_sampling_performed",
            "c1_c2_c3_assignment_performed",
            "split_construction_performed",
            "structural_mapping_performed",
            "model_work_performed",
            "prevalence_estimation_performed",
            "calibration_performed",
            "external_panel_inputs_used",
        )
    )
    report_authorizations = audit_report.get("authorizations", {})
    report_false = all(
        report_authorizations.get(key) is False
        for key in (
            "candidate_pair_materialization",
            "evidence_indicator_construction",
            "interaction_label_construction",
            "negative_label_construction",
            "pseudo_negative_sampling",
            "c1_c2_c3_assignment",
            "split_construction",
            "structural_mapping",
            "model_work",
        )
    )
    checks.require(
        "governance.primary_pu_r_and_all_downstream_guards",
        true_guards == 0
        and manifest_false
        and report_false
        and manifest.get("primary_design")
        == "reference_sequence_positive_unlabeled_ranking"
        and manifest.get("return_to_governance_required") is True,
        observed={
            "true_row_guards": true_guards,
            "manifest_false": manifest_false,
            "report_false": report_false,
        },
        expected={"true_row_guards": 0, "manifest_false": True, "report_false": True},
    )


def validate_audit(
    *,
    project_root: Path,
    config_path: Path,
    run_root: Path | None = None,
    canonical_root: Path | None = None,
    audit_report_path: Path | None = None,
) -> dict[str, Any]:
    require_apptainer()
    config_path = resolve_inside(
        project_root, config_path, project_root / "configs", strict=True
    )
    config = load_yaml(config_path)
    validate_config(config)
    run_root = resolve_inside(
        project_root,
        run_root or str(config["outputs"]["run_root"]),
        project_root / "artifacts/runs",
        strict=True,
    )
    canonical_root = resolve_inside(
        project_root,
        canonical_root or str(config["outputs"]["canonical_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    audit_report_path = resolve_inside(
        project_root,
        audit_report_path or str(config["outputs"]["audit_report"]),
        project_root / "artifacts/validation",
        strict=True,
    )
    checks = Checks()
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    container_sha = sha256_file(active_container)
    checks.require(
        "runtime.pinned_container_and_architecture",
        container_sha == str(config["runtime"]["container_sha256"])
        and platform.machine() == str(config["runtime"]["architecture"]),
        observed={"sha256": container_sha, "architecture": platform.machine()},
        expected={
            "sha256": str(config["runtime"]["container_sha256"]),
            "architecture": str(config["runtime"]["architecture"]),
        },
    )
    tool_inventory = verify_mmseqs_install(project_root=project_root, config=config)
    run_manifest_path = run_root / "RUN_MANIFEST.json"
    canonical_manifest_path = canonical_root / "AUDIT_MANIFEST.json"
    run_manifest_sha = _check_sidecar(checks, run_manifest_path, "inventory.run_manifest_sidecar")
    canonical_manifest_sha = _check_sidecar(
        checks, canonical_manifest_path, "inventory.canonical_manifest_sidecar"
    )
    run_manifest = load_json(run_manifest_path)
    canonical_manifest = load_json(canonical_manifest_path)
    audit_report = load_json(audit_report_path)
    _validate_run_inventory(checks, project_root, run_root, run_manifest)
    contract = load_contract(
        resolve_inside(
            project_root,
            str(config["inputs"]["audit_schema"]),
            project_root / "schemas",
            strict=True,
        )
    )
    output_files = _validate_canonical_inventory(
        checks, project_root, canonical_root, canonical_manifest, contract
    )
    _, verified_inputs, input_files = _verify_inputs(
        project_root=project_root, config=config, verify_hashes=True
    )
    current_git = git_provenance(project_root)
    production_git_ok = (
        run_manifest.get("git", {}).get("commit") == current_git["commit"]
        and canonical_manifest.get("git", {}).get("commit") == current_git["commit"]
        and run_manifest.get("git", {}).get("tracked_worktree_clean") is True
        and canonical_manifest.get("git", {}).get("tracked_worktree_clean") is True
    )
    checks.require(
        "provenance.production_commit_and_clean_worktree",
        production_git_ok,
        observed={
            "current_commit": current_git["commit"],
            "run_commit": run_manifest.get("git", {}).get("commit"),
            "canonical_commit": canonical_manifest.get("git", {}).get("commit"),
            "production_clean": production_git_ok,
        },
        expected={"commits_equal": True, "production_clean": True},
    )
    config_sha = sha256_file(config_path)
    provenance_matches = (
        audit_report.get("outputs", {}).get("run_manifest_sha256") == run_manifest_sha
        and audit_report.get("outputs", {}).get("canonical_manifest_sha256")
        == canonical_manifest_sha
        and canonical_manifest.get("inputs", {}).get("run_manifest_sha256")
        == run_manifest_sha
        and run_manifest.get("tool", {}).get("binary_sha256")
        == tool_inventory["binary_sha256"]
        and canonical_manifest.get("inputs", {}).get("documents")
        == verified_inputs["documents"]
        and canonical_manifest.get("inputs", {}).get("tables")
        == verified_inputs["tables"]
        and run_manifest.get("config", {}).get("sha256") == config_sha
        and canonical_manifest.get("inputs", {}).get("config_sha256") == config_sha
        and audit_report.get("inputs", {}).get("config_sha256") == config_sha
    )
    checks.require(
        "provenance.report_manifest_and_tool_hashes",
        provenance_matches,
        observed={"all_match": provenance_matches},
        expected={"all_match": True},
    )

    connection = duckdb.connect(":memory:")
    connection.execute(f"SET memory_limit={_sql_string(str(config['runtime']['duckdb_memory_limit']))}")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    connection.execute("PRAGMA disable_progress_bar")
    try:
        _register_views(connection, input_files, output_files)
        eligibility_metrics, mapping_by_gene = _independent_eligibility(
            checks, connection, config
        )
        sequence_lengths = {
            str(sequence_hash): int(length)
            for sequence_hash, length in connection.execute(
                "SELECT reference_sequence_sha256, sequence_length FROM audit_eligible_reference_sequences"
            ).fetchall()
        }
        alignment_path = run_root / "alignments.tsv"
        normalized_path = run_root / "normalized_alignment_edges.parquet"
        edges, alignment_metrics = _parse_alignments_independently(
            checks, alignment_path, normalized_path, sequence_lengths, config
        )
        components, component_summaries = _independent_components(
            checks,
            connection,
            edges,
            sorted(sequence_lengths),
            config,
        )
        positive_metrics, feasibility_metrics = _independent_positive_metrics(
            checks,
            connection,
            mapping_by_gene,
            components,
            component_summaries,
            config,
        )
        _scope_guards(checks, connection, canonical_manifest, audit_report)
    finally:
        connection.close()

    metrics = {
        "eligibility": eligibility_metrics,
        "alignment": alignment_metrics,
        "components": component_summaries,
        "positive_mapping_aggregates": positive_metrics,
        "positive_component_feasibility": feasibility_metrics,
    }
    checks.require(
        "metrics.manifest_and_report_match_independent_recomputation",
        canonical_manifest.get("metrics") == metrics
        and audit_report.get("metrics") == metrics
        and run_manifest.get("alignment_metrics") == alignment_metrics,
        observed={
            "canonical_matches": canonical_manifest.get("metrics") == metrics,
            "report_matches": audit_report.get("metrics") == metrics,
            "run_alignment_matches": run_manifest.get("alignment_metrics")
            == alignment_metrics,
        },
        expected={"canonical_matches": True, "report_matches": True, "run_alignment_matches": True},
    )
    return {
        "schema_version": 1,
        "gate_id": "benchmark_eligibility_and_sequence_component_audit_v1_validation",
        "audit_id": config["audit_id"],
        "audit_version": SEQUENCE_COMPONENT_AUDIT_VERSION,
        "status": "pass" if checks.passed else "fail",
        "scope": "production_full_independent_validation",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {
            "container_sif_sha256": container_sha,
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "duckdb": duckdb.__version__,
        },
        "run_manifest": run_manifest_path.as_posix(),
        "run_manifest_sha256": run_manifest_sha,
        "canonical_manifest": canonical_manifest_path.as_posix(),
        "canonical_manifest_sha256": canonical_manifest_sha,
        "audit_report": audit_report_path.as_posix(),
        "audit_report_sha256": sha256_file(audit_report_path),
        "config": config_path.as_posix(),
        "config_sha256": sha256_file(config_path),
        "tool": tool_inventory,
        "metrics": metrics,
        "check_counts": checks.counts(),
        "checks": checks.records,
        "interpretation": (
            "Pass independently validates frozen Space III eligibility, the exact "
            "algebraic endpoint-pair count, MMseqs2 alignment criteria, every 40/30/20% "
            "component assignment, and aggregate HuRI positive coverage. It creates no "
            "candidate-pair rows, labels, C1/C2/C3 assignments, splits, prevalence, "
            "calibration, structures, or models."
        ),
        "authorizations": {
            "audit_technical_validation_passed": checks.passed,
            "candidate_pair_materialization": False,
            "evidence_indicator_construction": False,
            "interaction_label_construction": False,
            "negative_label_construction": False,
            "pseudo_negative_sampling": False,
            "c1_c2_c3_assignment": False,
            "split_construction": False,
            "structural_mapping": False,
            "model_work": False,
            "return_to_governance_required": True,
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/benchmark_eligibility_and_sequence_component_audit_v1.yaml"),
    )
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())

    def absolute(path: Path | None) -> Path | None:
        if path is None or path.is_absolute():
            return path
        return project_root / path

    result = validate_audit(
        project_root=project_root,
        config_path=absolute(args.config) or args.config,
        run_root=absolute(args.run_root),
        canonical_root=absolute(args.canonical_root),
        audit_report_path=absolute(args.audit_report),
    )
    report_path = absolute(args.report) or project_root / str(
        load_yaml(absolute(args.config) or args.config)["outputs"]["validation_report"]
    )
    _write_report(report_path, result, project_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
