"""Execute the aggregate pre-split feasibility and leakage stress-test."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import tempfile
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import numpy as np
import pyarrow
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import (
    AtomicDatasetDirectory,
    ParquetBatchWriter,
    git_provenance,
    project_root_from,
    require_apptainer,
    stable_id,
)
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.pre_split_audit import AUDIT_VERSION
from ipin_openppi.pre_split_audit.semantics import (
    degree_summary,
    deterministic_components,
    nearest_rank,
    numeric_distribution,
    source_membership_strata,
)
from ipin_openppi.pre_split_audit.support import (
    artifact_inventory,
    load_json,
    load_yaml,
    make_read_only,
    replace_prefix,
    require_hash,
    require_output_paths,
    resolve_inside,
    validate_config,
    verify_manifest_table,
    write_json,
    write_manifest,
)
from ipin_openppi.validation.staging import _write_report


TABLES = (
    "network_degree_summaries",
    "source_composition_summaries",
    "similarity_sensitivity_summaries",
    "leakage_graph_summaries",
    "allocation_feasibility_summaries",
    "claim_assessments",
)
ALIGNMENT_COLUMNS = {
    "query": "VARCHAR",
    "target": "VARCHAR",
    "mismatch": "BIGINT",
    "alnlen": "BIGINT",
    "qstart": "BIGINT",
    "qend": "BIGINT",
    "qlen": "BIGINT",
    "tstart": "BIGINT",
    "tend": "BIGINT",
    "tlen": "BIGINT",
    "evalue": "DOUBLE",
    "bits": "DOUBLE",
}
PARTITION_NAMES = ("train", "development", "test")
PARTITION_CODES = {name: index for index, name in enumerate(PARTITION_NAMES)}


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_table(
    *,
    root: Path,
    table_name: str,
    rows: Iterable[Mapping[str, Any]],
    contract: Any,
    config: Mapping[str, Any],
    metadata: Mapping[str, str],
) -> dict[str, Any]:
    with ParquetBatchWriter(
        root / table_name,
        contract,
        table_name,
        batch_rows=100_000,
        compression=str(config["runtime"]["parquet_compression"]),
        compression_level=int(config["runtime"]["parquet_compression_level"]),
        extra_metadata=metadata,
    ) as writer:
        writer.extend(rows)
    return writer.summary()


def _verify_tool(project_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    tool = config["mmseqs2"]
    binary = resolve_inside(
        project_root,
        str(tool["binary_path"]),
        project_root / "artifacts/cache",
        strict=True,
    )
    info = require_hash(binary, str(tool["binary_sha256"]))
    if not os.access(binary, os.X_OK):
        raise RuntimeError("Pinned MMseqs2 binary is not executable")
    completed = subprocess.run(
        [binary.as_posix(), "version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    version = completed.stdout.strip()
    if version != str(tool["version_stdout"]):
        raise RuntimeError(f"MMseqs2 version mismatch: {version}")
    return {
        "release": str(tool["release"]),
        "upstream_commit": str(tool["upstream_commit"]),
        "binary": binary.as_posix(),
        "binary_bytes": info["bytes"],
        "binary_sha256": info["sha256"],
        "version_stdout": version,
    }


def _verify_inputs(
    *, project_root: Path, config: Mapping[str, Any], verify_hashes: bool
) -> tuple[dict[str, Any], dict[str, list[Path]], dict[str, Path]]:
    inputs = config["inputs"]
    document_keys = (
        "parent_config",
        "parent_canonical_manifest",
        "parent_run_manifest",
        "parent_fasta",
        "parent_normalized_edges",
        "parent_audit_report",
        "parent_validation_report",
        "primary_reconciliation_manifest",
        "benchmark_estimand_policy",
        "accepted_blueprint_amendment",
        "parent_acceptance_decision",
        "authorization_decision",
        "active_gate",
    )
    paths: dict[str, Path] = {}
    documents: dict[str, Any] = {}
    for key in document_keys:
        path = resolve_inside(project_root, str(inputs[key]), project_root, strict=True)
        paths[key] = path
        if verify_hashes:
            documents[key] = require_hash(path, str(inputs[f"{key}_sha256"]))
        else:
            documents[key] = {
                "path": path.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": "smoke_skipped",
            }
    schema = resolve_inside(
        project_root,
        str(inputs["audit_schema"]),
        project_root / "schemas",
        strict=True,
    )
    paths["audit_schema"] = schema
    documents["audit_schema"] = {
        "path": schema.as_posix(),
        "bytes": schema.stat().st_size,
        "sha256": sha256_file(schema),
    }

    parent_manifest = load_json(paths["parent_canonical_manifest"])
    parent_root = resolve_inside(
        project_root,
        str(inputs["parent_canonical_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    reconciliation_manifest = load_json(paths["primary_reconciliation_manifest"])
    reconciliation_root = resolve_inside(
        project_root,
        str(inputs["primary_reconciliation_root"]),
        project_root / "data/canonical",
        strict=True,
    )

    files: dict[str, list[Path]] = {}
    tables: dict[str, Any] = {}
    for config_key in (
        "eligible_reference_sequences",
        "space_iii_gene_eligibility",
        "sequence_component_assignments",
    ):
        table = str(config["parent_tables"][config_key])
        table_files, summary = verify_manifest_table(
            project_root=project_root,
            manifest=parent_manifest,
            table_name=table,
            expected_root=parent_root / table,
            verify_hashes=verify_hashes,
        )
        files[config_key] = table_files
        tables[config_key] = summary
    projection = str(config["parent_tables"]["huri_evidence_gene_pair_projections"])
    projection_files, summary = verify_manifest_table(
        project_root=project_root,
        manifest=reconciliation_manifest,
        table_name=projection,
        expected_root=reconciliation_root / projection,
        verify_hashes=verify_hashes,
    )
    files["huri_evidence_gene_pair_projections"] = projection_files
    tables["huri_evidence_gene_pair_projections"] = summary
    return {"documents": documents, "tables": tables}, files, paths


def _register_views(
    connection: duckdb.DuckDBPyConnection, table_files: Mapping[str, Sequence[Path]]
) -> None:
    for view, paths in table_files.items():
        connection.read_parquet([path.as_posix() for path in paths]).create_view(view)


def _load_parent_state(
    connection: duckdb.DuckDBPyConnection, config: Mapping[str, Any]
) -> tuple[
    list[str],
    dict[str, int],
    dict[int, dict[str, str]],
    dict[int, dict[str, int]],
]:
    expected = config["frozen_parent_expectations"]
    sequence_rows = connection.execute(
        "SELECT reference_sequence_sha256, sequence_length "
        "FROM eligible_reference_sequences ORDER BY reference_sequence_sha256"
    ).fetchall()
    nodes = [str(row[0]) for row in sequence_rows]
    lengths = {str(row[0]): int(row[1]) for row in sequence_rows}
    if len(nodes) != int(expected["eligible_reference_sequences"]) or len(set(nodes)) != len(nodes):
        raise RuntimeError("Frozen eligible endpoint inventory differs from DEC-0018")

    memberships: dict[int, dict[str, str]] = defaultdict(dict)
    sizes: dict[int, dict[str, int]] = defaultdict(dict)
    for raw_threshold, sequence, component, raw_size in connection.execute(
        "SELECT identity_threshold_percent, reference_sequence_sha256, component_id, component_size "
        "FROM sequence_component_assignments ORDER BY identity_threshold_percent, reference_sequence_sha256"
    ).fetchall():
        threshold = int(raw_threshold)
        endpoint = str(sequence)
        component_id = str(component)
        size = int(raw_size)
        if endpoint in memberships[threshold]:
            raise RuntimeError("Duplicate frozen component membership")
        memberships[threshold][endpoint] = component_id
        if component_id in sizes[threshold] and sizes[threshold][component_id] != size:
            raise RuntimeError("Frozen component size is inconsistent")
        sizes[threshold][component_id] = size
    for threshold in map(int, config["leakage_graphs"]["identity_thresholds_percent"]):
        if set(memberships[threshold]) != set(nodes):
            raise RuntimeError(f"Frozen {threshold}% component membership is incomplete")
        if len(sizes[threshold]) != int(expected["component_counts"][threshold]):
            raise RuntimeError(f"Frozen {threshold}% component count differs")
        observed_members = Counter(memberships[threshold].values())
        if dict(observed_members) != sizes[threshold]:
            raise RuntimeError(f"Frozen {threshold}% component sizes differ")
    return nodes, lengths, dict(memberships), dict(sizes)


def _load_positive_pairs(
    connection: duckdb.DuckDBPyConnection, config: Mapping[str, Any]
) -> tuple[dict[str, set[tuple[str, str]]], dict[tuple[str, str], frozenset[str]]]:
    mapping: dict[str, tuple[str, str | None]] = {}
    for gene, state, selected, usable in connection.execute(
        "SELECT ensembl_gene_id, mapping_state, selected_sequence_sha256, eligibility_usable "
        "FROM space_iii_gene_eligibility"
    ).fetchall():
        mapping[str(gene)] = (
            str(state),
            str(selected) if bool(usable) and selected is not None else None,
        )
    expected = config["frozen_parent_expectations"]
    if sum(value[1] is not None for value in mapping.values()) != int(
        expected["eligible_space_iii_genes"]
    ):
        raise RuntimeError("Frozen eligible gene mapping differs from DEC-0018")

    sources = tuple(map(str, config["positive_network"]["source_datasets"]))
    pairs = {source: set() for source in sources}
    for source, unique, raw_a, raw_b, label_authorized in connection.execute(
        "SELECT source_dataset, unique_gene_pair, gene_a, gene_b, label_authorized "
        "FROM huri_evidence_gene_pair_projections"
    ).fetchall():
        source = str(source)
        if source not in pairs or bool(label_authorized):
            raise RuntimeError("Positive projection is outside the accepted source scope")
        if not bool(unique) or raw_a is None or raw_b is None:
            continue
        gene_a = str(raw_a)
        gene_b = str(raw_b)
        if gene_a not in mapping or gene_b not in mapping:
            continue
        sequence_a = mapping[gene_a][1]
        sequence_b = mapping[gene_b][1]
        if sequence_a is None or sequence_b is None or sequence_a == sequence_b:
            continue
        pairs[source].add(tuple(sorted((sequence_a, sequence_b))))

    if len(pairs["HI-II-14"]) != int(expected["distinct_positive_pairs_hi_ii_14"]):
        raise RuntimeError("HI-II-14 positive pair count differs from DEC-0018")
    if len(pairs["HuRI"]) != int(expected["distinct_positive_pairs_huri"]):
        raise RuntimeError("HuRI positive pair count differs from DEC-0018")
    pairs["ALL"] = pairs["HI-II-14"] | pairs["HuRI"]
    if len(pairs["ALL"]) != int(expected["distinct_positive_pairs_all"]):
        raise RuntimeError("ALL positive pair count differs from DEC-0018")
    endpoints = {endpoint for pair in pairs["ALL"] for endpoint in pair}
    if len(endpoints) != int(expected["positive_endpoint_sequences_all"]):
        raise RuntimeError("Positive endpoint count differs from DEC-0018")
    pair_sources = {
        pair: frozenset(
            source for source in ("HI-II-14", "HuRI") if pair in pairs[source]
        )
        for pair in pairs["ALL"]
    }
    return pairs, pair_sources


def _load_parent_edges(
    path: Path, config: Mapping[str, Any]
) -> dict[int, set[tuple[str, str]]]:
    rows = pq.read_table(
        path, columns=["sequence_a_sha256", "sequence_b_sha256", "maximum_identity"]
    ).to_pylist()
    thresholds = map(int, config["leakage_graphs"]["identity_thresholds_percent"])
    output = {
        threshold: {
            (str(row["sequence_a_sha256"]), str(row["sequence_b_sha256"]))
            for row in rows
            if float(row["maximum_identity"]) + 1e-12 >= threshold / 100.0
        }
        for threshold in thresholds
    }
    expected = config["frozen_parent_expectations"]["normalized_edge_counts"]
    for threshold, edges in output.items():
        if len(edges) != int(expected[threshold]):
            raise RuntimeError(f"Frozen {threshold}% edge count differs from DEC-0018")
    return output


def _run_command(command: list[str], step: str) -> dict[str, Any]:
    started = _timestamp()
    completed = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    )
    return {
        "step": step,
        "started_at_utc": started,
        "completed_at_utc": _timestamp(),
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _run_similarity_searches(
    *,
    project_root: Path,
    temporary_run: Path,
    fasta_path: Path,
    binary: Path,
    config: Mapping[str, Any],
) -> tuple[Path, Path, list[dict[str, Any]]]:
    scratch_parent = project_root / "artifacts/tmp"
    scratch_parent.mkdir(parents=True, exist_ok=True)
    tool = config["mmseqs2"]
    logs: list[dict[str, Any]] = []
    full_output = temporary_run / "full_length_sensitivity_alignments.tsv"
    local_output = temporary_run / "local_domain_sensitivity_alignments.tsv"
    with tempfile.TemporaryDirectory(prefix="pre-split-mmseqs-", dir=scratch_parent) as raw:
        work = Path(raw)
        sequence_db = work / "eligible_sequences"
        logs.append(
            _run_command(
                [
                    binary.as_posix(),
                    "createdb",
                    fasta_path.as_posix(),
                    sequence_db.as_posix(),
                    *map(str, tool["createdb_parameters"]),
                ],
                "createdb",
            )
        )
        searches = (
            (
                "full_length_sensitivity",
                tool["full_length_sensitivity_search_parameters"],
                full_output,
            ),
            ("local_domain_sensitivity", tool["local_domain_search_parameters"], local_output),
        )
        for name, parameters, output in searches:
            result_db = work / f"{name}_result"
            search_tmp = work / f"{name}_tmp"
            logs.append(
                _run_command(
                    [
                        binary.as_posix(),
                        "search",
                        sequence_db.as_posix(),
                        sequence_db.as_posix(),
                        result_db.as_posix(),
                        search_tmp.as_posix(),
                        *map(str, parameters),
                    ],
                    f"{name}_search",
                )
            )
            logs.append(
                _run_command(
                    [
                        binary.as_posix(),
                        "convertalis",
                        sequence_db.as_posix(),
                        sequence_db.as_posix(),
                        result_db.as_posix(),
                        output.as_posix(),
                        "--format-mode",
                        "0",
                        "--format-output",
                        ",".join(map(str, tool["alignment_output_fields"])),
                        "--threads",
                        str(config["runtime"]["duckdb_threads"]),
                    ],
                    f"{name}_convertalis",
                )
            )
    for output in (full_output, local_output):
        if output.is_symlink() or not output.is_file():
            raise RuntimeError(f"MMseqs2 did not produce {output.name}")
    return full_output, local_output, logs


def _normalize_search(
    *,
    connection: duckdb.DuckDBPyConnection,
    raw_path: Path,
    normalized_path: Path,
    sequence_lengths: Mapping[str, int],
    minimum_identity: float,
    minimum_coverage: float,
    minimum_span: int,
    maximum_evalue: float,
) -> dict[str, Any]:
    columns_sql = "{" + ",".join(
        f"{_sql_string(name)}:{_sql_string(kind)}" for name, kind in ALIGNMENT_COLUMNS.items()
    ) + "}"
    connection.execute(
        f"""
        CREATE OR REPLACE VIEW raw_sensitivity_alignments AS
        SELECT * FROM read_csv(
          {_sql_string(raw_path.as_posix())}, delim='\\t', header=false,
          columns={columns_sql}, strict_mode=true, null_padding=false
        )
        """
    )
    connection.execute("DROP TABLE IF EXISTS sensitivity_sequence_nodes")
    connection.execute(
        "CREATE TABLE sensitivity_sequence_nodes(sequence_hash VARCHAR PRIMARY KEY, sequence_length BIGINT)"
    )
    connection.executemany(
        "INSERT INTO sensitivity_sequence_nodes VALUES (?, ?)",
        sorted((sequence, int(length)) for sequence, length in sequence_lengths.items()),
    )
    raw_count = int(connection.execute("SELECT count(*) FROM raw_sensitivity_alignments").fetchone()[0])
    invalid = int(
        connection.execute(
            """
            SELECT count(*)
            FROM raw_sensitivity_alignments a
            LEFT JOIN sensitivity_sequence_nodes q ON q.sequence_hash = a.query
            LEFT JOIN sensitivity_sequence_nodes t ON t.sequence_hash = a.target
            WHERE q.sequence_hash IS NULL OR t.sequence_hash IS NULL
               OR a.alnlen <= 0 OR a.mismatch < 0 OR a.mismatch > a.alnlen
               OR a.qlen != q.sequence_length OR a.tlen != t.sequence_length
               OR a.qstart < 1 OR a.qend < 1 OR a.tstart < 1 OR a.tend < 1
               OR a.qstart > a.qlen OR a.qend > a.qlen
               OR a.tstart > a.tlen OR a.tend > a.tlen
               OR ((abs(a.qend-a.qstart)+1) + (abs(a.tend-a.tstart)+1)
                    - a.alnlen - a.mismatch) NOT BETWEEN 0 AND a.alnlen
               OR NOT isfinite(a.evalue) OR NOT isfinite(a.bits)
            """
        ).fetchone()[0]
    )
    if invalid:
        raise RuntimeError(f"Sensitivity alignment table has {invalid} invalid rows")
    scores = connection.execute(
        """
        WITH exact AS (
          SELECT ((abs(qend-qstart)+1) + (abs(tend-tstart)+1) - alnlen - mismatch)::DOUBLE/alnlen AS identity,
                 least((abs(qend-qstart)+1)::DOUBLE/qlen,
                       (abs(tend-tstart)+1)::DOUBLE/tlen) AS minimum_coverage,
                 least(abs(qend-qstart)+1, abs(tend-tstart)+1) AS minimum_span,
                 evalue
          FROM raw_sensitivity_alignments
        )
        SELECT count(*) FILTER (WHERE identity + 1e-12 < ?)::BIGINT,
               count(*) FILTER (WHERE minimum_coverage + 1e-12 < ?)::BIGINT,
               count(*) FILTER (WHERE minimum_span < ?)::BIGINT,
               count(*) FILTER (WHERE evalue > ?)::BIGINT
        FROM exact
        """,
        [minimum_identity, minimum_coverage, minimum_span, maximum_evalue],
    ).fetchone()
    self_queries = int(
        connection.execute(
            "SELECT count(DISTINCT query) FROM raw_sensitivity_alignments WHERE query=target"
        ).fetchone()[0]
    )
    if self_queries != len(sequence_lengths):
        raise RuntimeError("Sensitivity search self matches do not cover all endpoints")

    connection.execute(
        f"""
        COPY (
          WITH exact AS (
            SELECT least(query,target) AS sequence_a_sha256,
                   greatest(query,target) AS sequence_b_sha256,
                   ((abs(qend-qstart)+1) + (abs(tend-tstart)+1) - alnlen - mismatch)::DOUBLE/alnlen AS identity,
                   least((abs(qend-qstart)+1)::DOUBLE/qlen,
                         (abs(tend-tstart)+1)::DOUBLE/tlen) AS minimum_coverage,
                   least(abs(qend-qstart)+1, abs(tend-tstart)+1) AS minimum_span,
                   evalue, bits
            FROM raw_sensitivity_alignments
            WHERE query != target
          ), eligible AS (
            SELECT * FROM exact
            WHERE identity + 1e-12 >= {minimum_identity:.17g}
              AND minimum_coverage + 1e-12 >= {minimum_coverage:.17g}
              AND minimum_span >= {int(minimum_span)}
              AND evalue <= {maximum_evalue:.17g}
          )
          SELECT sequence_a_sha256, sequence_b_sha256,
                 max(identity) AS maximum_identity,
                 max(minimum_coverage) AS maximum_minimum_endpoint_coverage,
                 max(minimum_span)::BIGINT AS maximum_minimum_aligned_span,
                 min(evalue) AS minimum_evalue,
                 max(bits) AS maximum_bits,
                 count(*)::BIGINT AS supporting_alignment_records
          FROM eligible
          GROUP BY sequence_a_sha256, sequence_b_sha256
          ORDER BY sequence_a_sha256, sequence_b_sha256
        ) TO {_sql_string(normalized_path.as_posix())}
        (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    normalized_count = int(pq.ParquetFile(normalized_path).metadata.num_rows)
    return {
        "raw_alignment_records": raw_count,
        "structurally_invalid_records": invalid,
        "below_exact_identity_records": int(scores[0]),
        "below_minimum_endpoint_coverage_records": int(scores[1]),
        "below_minimum_aligned_span_records": int(scores[2]),
        "above_maximum_evalue_records": int(scores[3]),
        "self_match_query_sequences": self_queries,
        "normalized_nonself_edges": normalized_count,
        "raw_alignment_sha256": sha256_file(raw_path),
        "normalized_edges_sha256": sha256_file(normalized_path),
        "minimum_identity": minimum_identity,
        "minimum_endpoint_coverage": minimum_coverage,
        "minimum_aligned_endpoint_span": minimum_span,
        "maximum_evalue": maximum_evalue,
        "identity_uses_integer_derived_identical_over_alnlen": True,
    }


def _edge_sets_from_normalized(
    path: Path, thresholds: Sequence[int]
) -> dict[int, set[tuple[str, str]]]:
    rows = pq.read_table(
        path, columns=["sequence_a_sha256", "sequence_b_sha256", "maximum_identity"]
    ).to_pylist()
    return {
        int(threshold): {
            (str(row["sequence_a_sha256"]), str(row["sequence_b_sha256"]))
            for row in rows
            if float(row["maximum_identity"]) + 1e-12 >= int(threshold) / 100.0
        }
        for threshold in thresholds
    }


def _degree_row(
    *,
    source: str,
    unit: str,
    definition: str,
    threshold: int,
    values: Sequence[int],
    pair_count: int,
) -> dict[str, Any]:
    return {
        "summary_id": stable_id("pre-split-degree", source, unit, definition, threshold),
        "source_dataset": source,
        "summary_unit": unit,
        "leakage_definition": definition,
        "identity_threshold_percent": threshold,
        **degree_summary(values),
        "positive_pair_count": pair_count,
        "entity_rows_emitted": False,
        "pair_rows_emitted": False,
        "split_assignment_constructed": False,
    }


def _endpoint_degree_rows(
    nodes: Sequence[str], pairs_by_source: Mapping[str, set[tuple[str, str]]]
) -> list[dict[str, Any]]:
    output = []
    for source in ("ALL", "HI-II-14", "HuRI"):
        degrees = Counter(endpoint for pair in pairs_by_source[source] for endpoint in pair)
        output.append(
            _degree_row(
                source=source,
                unit="endpoint",
                definition="positive_network",
                threshold=0,
                values=[int(degrees[node]) for node in nodes],
                pair_count=len(pairs_by_source[source]),
            )
        )
    return output


def _component_degree_row(
    *,
    source: str,
    definition: str,
    threshold: int,
    memberships: Mapping[str, str],
    component_ids: Sequence[str],
    pairs: set[tuple[str, str]],
) -> dict[str, Any]:
    loads: Counter[str] = Counter()
    for endpoint_a, endpoint_b in pairs:
        component_a = memberships[endpoint_a]
        component_b = memberships[endpoint_b]
        loads[component_a] += 1
        if component_b != component_a:
            loads[component_b] += 1
    return _degree_row(
        source=source,
        unit="component",
        definition=definition,
        threshold=threshold,
        values=[int(loads[component]) for component in component_ids],
        pair_count=len(pairs),
    )


def _source_rows(
    *,
    strata: Mapping[str, set[tuple[str, str]]],
    definition: str,
    threshold: int,
    memberships: Mapping[str, str] | None,
) -> list[dict[str, Any]]:
    total = sum(len(value) for value in strata.values())
    rows = []
    for stratum in ("HI-II-14_only", "HuRI_only", "both"):
        pairs = strata[stratum]
        within = 0
        if memberships is not None:
            within = sum(memberships[a] == memberships[b] for a, b in pairs)
        rows.append(
            {
                "summary_id": stable_id("pre-split-source", stratum, definition, threshold),
                "source_membership_stratum": stratum,
                "leakage_definition": definition,
                "identity_threshold_percent": threshold,
                "positive_pair_count": len(pairs),
                "positive_pair_fraction": len(pairs) / total,
                "within_component_pair_count": within,
                "cross_component_pair_count": len(pairs) - within,
                "pair_rows_emitted": False,
                "evidence_indicator_constructed": False,
                "split_assignment_constructed": False,
            }
        )
    return rows


def _component_summary(
    *,
    definition: str,
    threshold: int,
    nodes: Sequence[str],
    edges: set[tuple[str, str]],
    accepted_edges: set[tuple[str, str]],
    accepted_memberships: Mapping[str, str],
    memberships: Mapping[str, str],
    component_sizes: Mapping[str, int],
    positive_pairs: set[tuple[str, str]],
) -> dict[str, Any]:
    sizes = list(map(int, component_sizes.values()))
    added = edges - accepted_edges
    within = sum(memberships[a] == memberships[b] for a, b in positive_pairs)
    exposed = {memberships[endpoint] for pair in positive_pairs for endpoint in pair}
    return {
        "summary_id": stable_id("pre-split-leakage", definition, threshold),
        "leakage_definition": definition,
        "identity_threshold_percent": threshold,
        "sequence_count": len(nodes),
        "edge_count": len(edges),
        "added_edge_count_vs_accepted": len(added),
        "added_edges_crossing_accepted_components": sum(
            accepted_memberships[a] != accepted_memberships[b] for a, b in added
        ),
        "component_count": len(sizes),
        "singleton_component_count": sum(size == 1 for size in sizes),
        "largest_component_size": max(sizes),
        "component_size_q50": nearest_rank(sizes, 0.50),
        "component_size_q90": nearest_rank(sizes, 0.90),
        "component_size_q95": nearest_rank(sizes, 0.95),
        "component_size_q99": nearest_rank(sizes, 0.99),
        "positive_pair_count": len(positive_pairs),
        "within_component_positive_pairs": within,
        "cross_component_positive_pairs": len(positive_pairs) - within,
        "positive_exposed_components": len(exposed),
        "component_membership_rows_emitted": False,
        "split_assignment_constructed": False,
    }


def _base_component_order(component_ids: Sequence[str], seed: str) -> list[str]:
    return sorted(
        component_ids,
        key=lambda component: hashlib.sha256(
            f"{seed}:component:{component}".encode("utf-8")
        ).digest(),
    )


def _trial_order_indices(base_count: int, seed: str, trial: int) -> Iterable[int]:
    digest = hashlib.sha256(f"{seed}:trial:{trial}".encode("utf-8")).digest()
    offset = int.from_bytes(digest[:8], "big") % base_count
    stride = max(1, int.from_bytes(digest[8:16], "big") % base_count)
    while math.gcd(stride, base_count) != 1:
        stride = (stride + 1) % base_count or 1
    for index in range(base_count):
        yield (offset + index * stride) % base_count


def _allocation_summary(
    *,
    definition: str,
    threshold: int,
    nodes: Sequence[str],
    memberships: Mapping[str, str],
    component_sizes: Mapping[str, int],
    positive_pairs: set[tuple[str, str]],
    pair_sources: Mapping[tuple[str, str], frozenset[str]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    policy = config["allocation_feasibility"]
    trials = int(policy["trial_count"])
    seed = f"{policy['deterministic_seed']}:{definition}:{threshold}"
    fractions = {name: float(policy["target_fractions"][name]) for name in PARTITION_NAMES}
    tolerance = float(policy["maximum_absolute_sequence_fraction_deviation"])
    pair_floor = int(policy["minimum_released_positive_pairs"])
    component_floor = int(policy["minimum_independent_components"])
    source_floor = int(policy["minimum_pairs_per_source_for_meaningful_diversity"])
    robust_fraction = float(policy["robust_feasibility_trial_fraction"])

    component_ids = sorted(component_sizes)
    component_index = {component: index for index, component in enumerate(component_ids)}
    sizes = np.array([int(component_sizes[component]) for component in component_ids], dtype=np.int64)
    base = _base_component_order(component_ids, seed)
    base_indices = np.array([component_index[component] for component in base], dtype=np.int64)
    node_index = {node: index for index, node in enumerate(nodes)}
    node_components = np.array(
        [component_index[memberships[node]] for node in nodes], dtype=np.int64
    )
    ordered_pairs = sorted(positive_pairs)
    endpoint_a = np.array([node_index[pair[0]] for pair in ordered_pairs], dtype=np.int64)
    endpoint_b = np.array([node_index[pair[1]] for pair in ordered_pairs], dtype=np.int64)
    hi_mask = np.array(
        ["HI-II-14" in pair_sources[pair] for pair in ordered_pairs], dtype=bool
    )
    huri_mask = np.array(["HuRI" in pair_sources[pair] for pair in ordered_pairs], dtype=bool)
    total_sequences = len(nodes)
    target_counts = np.array(
        [fractions[name] * total_sequences for name in PARTITION_NAMES], dtype=np.float64
    )

    metrics = {name: [] for name in (
        "c1_pairs", "c2_pairs", "c3_pairs", "c1_components", "c2_components",
        "c3_components", "c3_hi_ii_14_pairs", "c3_huri_pairs"
    )}
    target_valid = 0
    c1_pass = c2_pass = c3_pass = source_pass = joint_pass = 0
    for trial in range(trials):
        component_partitions = np.empty(len(component_ids), dtype=np.int8)
        counts = np.zeros(3, dtype=np.int64)
        for base_position in _trial_order_indices(len(component_ids), seed, trial):
            component = int(base_indices[base_position])
            relative_deficit = (target_counts - counts) / np.maximum(target_counts, 1.0)
            chosen = int(np.argmax(relative_deficit))
            component_partitions[component] = chosen
            counts[chosen] += sizes[component]
        valid_target = bool(
            np.all(np.abs(counts / total_sequences - target_counts / total_sequences) <= tolerance + 1e-12)
        )
        target_valid += int(valid_target)

        node_partitions = component_partitions[node_components]
        part_a = node_partitions[endpoint_a]
        part_b = node_partitions[endpoint_b]
        train_pairs = (part_a == PARTITION_CODES["train"]) & (part_b == PARTITION_CODES["train"])
        train_degree = np.bincount(
            np.concatenate((endpoint_a[train_pairs], endpoint_b[train_pairs])),
            minlength=len(nodes),
        )
        c1 = train_pairs & (train_degree[endpoint_a] >= 2) & (train_degree[endpoint_b] >= 2)
        a_train_b_test = (part_a == PARTITION_CODES["train"]) & (part_b == PARTITION_CODES["test"])
        b_train_a_test = (part_b == PARTITION_CODES["train"]) & (part_a == PARTITION_CODES["test"])
        c2 = (a_train_b_test & (train_degree[endpoint_a] >= 1)) | (
            b_train_a_test & (train_degree[endpoint_b] >= 1)
        )
        c3 = (part_a == PARTITION_CODES["test"]) & (part_b == PARTITION_CODES["test"])

        trial_values = {
            "c1_pairs": int(np.count_nonzero(c1)),
            "c2_pairs": int(np.count_nonzero(c2)),
            "c3_pairs": int(np.count_nonzero(c3)),
            "c1_components": int(
                len(np.unique(np.concatenate((node_components[endpoint_a[c1]], node_components[endpoint_b[c1]]))))
            ) if np.any(c1) else 0,
            "c2_components": int(
                len(np.unique(np.concatenate((node_components[endpoint_a[c2]], node_components[endpoint_b[c2]]))))
            ) if np.any(c2) else 0,
            "c3_components": int(
                len(np.unique(np.concatenate((node_components[endpoint_a[c3]], node_components[endpoint_b[c3]]))))
            ) if np.any(c3) else 0,
            "c3_hi_ii_14_pairs": int(np.count_nonzero(c3 & hi_mask)),
            "c3_huri_pairs": int(np.count_nonzero(c3 & huri_mask)),
        }
        for key, value in trial_values.items():
            metrics[key].append(value)
        axis_c1 = trial_values["c1_pairs"] >= pair_floor and trial_values["c1_components"] >= component_floor
        axis_c2 = trial_values["c2_pairs"] >= pair_floor and trial_values["c2_components"] >= component_floor
        axis_c3 = trial_values["c3_pairs"] >= pair_floor and trial_values["c3_components"] >= component_floor
        diverse = (
            trial_values["c3_hi_ii_14_pairs"] >= source_floor
            and trial_values["c3_huri_pairs"] >= source_floor
        )
        c1_pass += int(valid_target and axis_c1)
        c2_pass += int(valid_target and axis_c2)
        c3_pass += int(valid_target and axis_c3)
        source_pass += int(valid_target and diverse)
        joint_pass += int(valid_target and axis_c1 and axis_c2 and axis_c3 and diverse)

    joint_fraction = joint_pass / trials
    status = (
        "robustly_feasible"
        if joint_fraction + 1e-12 >= robust_fraction
        else "conditionally_feasible"
        if joint_pass > 0
        else "not_demonstrated"
    )
    encode = lambda key: json.dumps(numeric_distribution(metrics[key]), sort_keys=True)
    return {
        "summary_id": stable_id("pre-split-allocation", definition, threshold),
        "leakage_definition": definition,
        "identity_threshold_percent": threshold,
        "trial_count": trials,
        "target_fraction_valid_trial_count": target_valid,
        "target_fraction_valid_trial_fraction": target_valid / trials,
        "c1_pair_distribution_json": encode("c1_pairs"),
        "c2_pair_distribution_json": encode("c2_pairs"),
        "c3_pair_distribution_json": encode("c3_pairs"),
        "c1_component_distribution_json": encode("c1_components"),
        "c2_component_distribution_json": encode("c2_components"),
        "c3_component_distribution_json": encode("c3_components"),
        "c3_hi_ii_14_pair_distribution_json": encode("c3_hi_ii_14_pairs"),
        "c3_huri_pair_distribution_json": encode("c3_huri_pairs"),
        "c1_floor_pass_trial_fraction": c1_pass / trials,
        "c2_floor_pass_trial_fraction": c2_pass / trials,
        "c3_floor_pass_trial_fraction": c3_pass / trials,
        "c3_source_diversity_pass_trial_fraction": source_pass / trials,
        "joint_floor_pass_trial_fraction": joint_fraction,
        "feasibility_status": status,
        "selected_trial_emitted": False,
        "component_assignment_rows_emitted": False,
        "pair_assignment_rows_emitted": False,
        "c1_c2_c3_labels_constructed": False,
        "split_constructed": False,
    }


def _claim_rows(
    allocation_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for allocation in allocation_rows:
        definition = str(allocation["leakage_definition"])
        threshold = int(allocation["identity_threshold_percent"])
        feasible = allocation["feasibility_status"] == "robustly_feasible"
        rows.append(
            {
                "claim_id": stable_id("pre-split-claim", "c3-operational", definition, threshold),
                "claim_name": "future_c3_operational_sequence_novelty",
                "leakage_definition": definition,
                "identity_threshold_percent": threshold,
                "supported_by_audit": feasible,
                "claim_status": "not_yet_authorized",
                "permitted_wording": (
                    "If a later immutable split passes all gates: both endpoints were absent "
                    f"from training and component-disjoint under {definition} at {threshold}% identity."
                ),
                "prohibited_wording": "unseen biological family or universal family generalization",
                "rationale": (
                    "Aggregate opportunity trials are robust under this operational graph."
                    if feasible
                    else "Aggregate opportunity trials did not robustly retain all prespecified floors."
                ),
                "model_performance_claimed": False,
                "experimental_validation_claimed": False,
            }
        )
    rows.extend(
        [
            {
                "claim_id": stable_id("pre-split-claim", "universal-family"),
                "claim_name": "unseen_biological_family",
                "leakage_definition": "local_domain_union",
                "identity_threshold_percent": 30,
                "supported_by_audit": False,
                "claim_status": "prohibited",
                "permitted_wording": "component-disjoint under a named versioned sequence rule",
                "prohibited_wording": "unseen family, novel family, or family-generalizing performance",
                "rationale": "A heuristic sequence graph is not a universal biological family definition.",
                "model_performance_claimed": False,
                "experimental_validation_claimed": False,
            },
            {
                "claim_id": stable_id("pre-split-claim", "exhaustive-homology"),
                "claim_name": "exhaustive_absence_of_homology",
                "leakage_definition": "sensitive_fl80_union",
                "identity_threshold_percent": 30,
                "supported_by_audit": False,
                "claim_status": "prohibited",
                "permitted_wording": "not recovered by the separately parameterized MMseqs2 sensitivity challenge",
                "prohibited_wording": "proven nonhomologous or exhaustively homology-free",
                "rationale": "MMseqs2 search and operational alignment cutoffs are heuristic sensitivity controls.",
                "model_performance_claimed": False,
                "experimental_validation_claimed": False,
            },
        ]
    )
    return rows


def _build_aggregate_tables(
    *,
    nodes: Sequence[str],
    pairs_by_source: Mapping[str, set[tuple[str, str]]],
    pair_sources: Mapping[tuple[str, str], frozenset[str]],
    accepted_edges: Mapping[int, set[tuple[str, str]]],
    sensitivity_edges: Mapping[int, set[tuple[str, str]]],
    local_edges: Mapping[int, set[tuple[str, str]]],
    accepted_memberships: Mapping[int, Mapping[str, str]],
    accepted_sizes: Mapping[int, Mapping[str, int]],
    config: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    degree_rows = _endpoint_degree_rows(nodes, pairs_by_source)
    strata = source_membership_strata(pairs_by_source["HI-II-14"], pairs_by_source["HuRI"])
    source_rows = _source_rows(
        strata=strata, definition="positive_network", threshold=0, memberships=None
    )
    similarity_rows: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    allocation_rows: list[dict[str, Any]] = []

    definitions: dict[tuple[str, int], tuple[set[tuple[str, str]], Mapping[str, str], Mapping[str, int]]] = {}
    for threshold in map(int, config["leakage_graphs"]["identity_thresholds_percent"]):
        accepted = accepted_edges[threshold]
        sensitivity = sensitivity_edges[threshold]
        union = accepted | sensitivity
        similarity_rows.append(
            {
                "summary_id": stable_id("pre-split-sensitivity", threshold),
                "identity_threshold_percent": threshold,
                "accepted_edge_count": len(accepted),
                "sensitivity_edge_count": len(sensitivity),
                "rediscovered_accepted_edge_count": len(accepted & sensitivity),
                "accepted_edges_not_rediscovered": len(accepted - sensitivity),
                "newly_recovered_qualifying_edges": len(sensitivity - accepted),
                "union_edge_count": len(union),
                "accepted_edge_rediscovery_fraction": len(accepted & sensitivity) / len(accepted),
                "exhaustive_completeness_proven": False,
                "accepted_graph_modified": False,
            }
        )
        sensitive_memberships, sensitive_sizes = deterministic_components(nodes, union)
        local_union = union | local_edges[threshold]
        local_memberships, local_sizes = deterministic_components(nodes, local_union)
        definitions[("frozen_fl80", threshold)] = (
            accepted,
            accepted_memberships[threshold],
            accepted_sizes[threshold],
        )
        definitions[("sensitive_fl80_union", threshold)] = (
            union,
            sensitive_memberships,
            sensitive_sizes,
        )
        definitions[("local_domain_union", threshold)] = (
            local_union,
            local_memberships,
            local_sizes,
        )

    for (definition, threshold), (edges, memberships, sizes) in definitions.items():
        leakage_rows.append(
            _component_summary(
                definition=definition,
                threshold=threshold,
                nodes=nodes,
                edges=edges,
                accepted_edges=accepted_edges[threshold],
                accepted_memberships=accepted_memberships[threshold],
                memberships=memberships,
                component_sizes=sizes,
                positive_pairs=pairs_by_source["ALL"],
            )
        )
        source_rows.extend(
            _source_rows(
                strata=strata,
                definition=definition,
                threshold=threshold,
                memberships=memberships,
            )
        )
        for source in ("ALL", "HI-II-14", "HuRI"):
            degree_rows.append(
                _component_degree_row(
                    source=source,
                    definition=definition,
                    threshold=threshold,
                    memberships=memberships,
                    component_ids=sorted(sizes),
                    pairs=pairs_by_source[source],
                )
            )
        allocation_rows.append(
            _allocation_summary(
                definition=definition,
                threshold=threshold,
                nodes=nodes,
                memberships=memberships,
                component_sizes=sizes,
                positive_pairs=pairs_by_source["ALL"],
                pair_sources=pair_sources,
                config=config,
            )
        )
    return {
        "network_degree_summaries": sorted(degree_rows, key=lambda row: row["summary_id"]),
        "source_composition_summaries": sorted(source_rows, key=lambda row: row["summary_id"]),
        "similarity_sensitivity_summaries": sorted(similarity_rows, key=lambda row: row["summary_id"]),
        "leakage_graph_summaries": sorted(leakage_rows, key=lambda row: row["summary_id"]),
        "allocation_feasibility_summaries": sorted(allocation_rows, key=lambda row: row["summary_id"]),
        "claim_assessments": sorted(_claim_rows(allocation_rows), key=lambda row: row["claim_id"]),
    }


def run_audit(
    *,
    project_root: Path,
    config_path: Path,
    run_root: Path | None = None,
    canonical_root: Path | None = None,
    report_path: Path | None = None,
    allow_dirty: bool = False,
    skip_input_hashes: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    started_at = _timestamp()
    config_path = resolve_inside(
        project_root, config_path, project_root / "configs", strict=True
    )
    config = load_yaml(config_path)
    validate_config(config)
    run_target = resolve_inside(
        project_root,
        run_root or str(config["outputs"]["run_root"]),
        project_root / "artifacts/runs",
        strict=False,
    )
    canonical_target = resolve_inside(
        project_root,
        canonical_root or str(config["outputs"]["canonical_root"]),
        project_root / "data/canonical",
        strict=False,
    )
    report_target = resolve_inside(
        project_root,
        report_path or str(config["outputs"]["audit_report"]),
        project_root / "artifacts/validation",
        strict=False,
    )
    smoke = require_output_paths(
        run_root=run_target,
        canonical_root=canonical_target,
        report_path=report_target,
        allow_dirty=allow_dirty,
        skip_input_hashes=skip_input_hashes,
    )
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production pre-split audit requires a clean Git worktree")
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    if active_container != expected_container:
        raise RuntimeError("Active Apptainer image differs from the audit configuration")
    container_sha = sha256_file(active_container)
    if container_sha != str(config["runtime"]["container_sha256"]):
        raise RuntimeError("Active container hash differs from the audit configuration")
    if platform.machine() != str(config["runtime"]["architecture"]):
        raise RuntimeError("Pre-split audit is running on the wrong architecture")
    tool = _verify_tool(project_root, config)
    verified_inputs, table_files, input_paths = _verify_inputs(
        project_root=project_root, config=config, verify_hashes=not skip_input_hashes
    )

    connection = duckdb.connect(":memory:")
    connection.execute(f"SET memory_limit={_sql_string(str(config['runtime']['duckdb_memory_limit']))}")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    connection.execute("PRAGMA disable_progress_bar")
    try:
        _register_views(connection, table_files)
        nodes, lengths, accepted_memberships, accepted_sizes = _load_parent_state(
            connection, config
        )
        pairs_by_source, pair_sources = _load_positive_pairs(connection, config)
        accepted_edges = _load_parent_edges(input_paths["parent_normalized_edges"], config)

        with AtomicDatasetDirectory(run_target) as temporary_run:
            full_raw, local_raw, command_logs = _run_similarity_searches(
                project_root=project_root,
                temporary_run=temporary_run,
                fasta_path=input_paths["parent_fasta"],
                binary=Path(tool["binary"]),
                config=config,
            )
            full_normalized = temporary_run / "full_length_sensitivity_edges.parquet"
            local_normalized = temporary_run / "local_domain_sensitivity_edges.parquet"
            full_metrics = _normalize_search(
                connection=connection,
                raw_path=full_raw,
                normalized_path=full_normalized,
                sequence_lengths=lengths,
                minimum_identity=0.20,
                minimum_coverage=0.80,
                minimum_span=0,
                maximum_evalue=1e100,
            )
            local_policy = config["leakage_graphs"]["local_domain_union_definition"]
            local_metrics = _normalize_search(
                connection=connection,
                raw_path=local_raw,
                normalized_path=local_normalized,
                sequence_lengths=lengths,
                minimum_identity=0.20,
                minimum_coverage=float(local_policy["minimum_endpoint_coverage"]),
                minimum_span=int(local_policy["minimum_aligned_endpoint_span"]),
                maximum_evalue=float(local_policy["maximum_evalue"]),
            )
            thresholds = list(map(int, config["leakage_graphs"]["identity_thresholds_percent"]))
            sensitivity_edges = _edge_sets_from_normalized(full_normalized, thresholds)
            local_edges = _edge_sets_from_normalized(local_normalized, thresholds)
            table_rows = _build_aggregate_tables(
                nodes=nodes,
                pairs_by_source=pairs_by_source,
                pair_sources=pair_sources,
                accepted_edges=accepted_edges,
                sensitivity_edges=sensitivity_edges,
                local_edges=local_edges,
                accepted_memberships=accepted_memberships,
                accepted_sizes=accepted_sizes,
                config=config,
            )
            commands_path = temporary_run / "MMSEQS_COMMANDS.json"
            write_json(
                commands_path,
                {
                    "schema_version": 1,
                    "tool": tool,
                    "createdb_parameters": config["mmseqs2"]["createdb_parameters"],
                    "full_length_sensitivity_search_parameters": config["mmseqs2"]["full_length_sensitivity_search_parameters"],
                    "local_domain_search_parameters": config["mmseqs2"]["local_domain_search_parameters"],
                    "alignment_output_fields": config["mmseqs2"]["alignment_output_fields"],
                    "executions": command_logs,
                },
            )
            run_files = artifact_inventory(temporary_run, run_target)
            run_manifest = {
                "schema_version": 1,
                "audit_id": config["audit_id"],
                "audit_version": AUDIT_VERSION,
                "status": "complete",
                "scope": "similarity_sensitivity_run_artifacts_not_ppi_candidate_pairs",
                "started_at_utc": started_at,
                "completed_at_utc": _timestamp(),
                "git": git,
                "runtime": {
                    "container_sif_sha256": container_sha,
                    "architecture": platform.machine(),
                    "python": platform.python_version(),
                    "duckdb": duckdb.__version__,
                    "pyarrow": pyarrow.__version__,
                    "numpy": np.__version__,
                },
                "tool": tool,
                "config": {
                    "path": config_path.relative_to(project_root).as_posix(),
                    "sha256": sha256_file(config_path),
                },
                "files": run_files,
                "search_metrics": {
                    "full_length_sensitivity": full_metrics,
                    "local_domain_sensitivity": local_metrics,
                },
                "candidate_pair_materialization_performed": False,
                "positive_pair_rows_emitted": False,
                "evidence_indicator_construction_performed": False,
                "label_construction_performed": False,
                "c1_c2_c3_assignment_performed": False,
                "split_construction_performed": False,
                "model_work_performed": False,
            }
            run_manifest_sha = write_manifest(
                temporary_run / "RUN_MANIFEST.json", run_manifest
            )
            make_read_only(temporary_run)
    finally:
        connection.close()

    metrics = {table: table_rows[table] for table in TABLES}
    contract = load_contract(input_paths["audit_schema"])
    metadata = {
        "audit_version": AUDIT_VERSION,
        "audit_git_commit": str(git["commit"]),
        "container_sif_sha256": container_sha,
        "primary_design": "reference_sequence_positive_unlabeled_ranking",
        "aggregate_only": "true",
        "split_constructed": "false",
    }
    with AtomicDatasetDirectory(canonical_target) as temporary_canonical:
        summaries = {
            table: _write_table(
                root=temporary_canonical,
                table_name=table,
                rows=table_rows[table],
                contract=contract,
                config=config,
                metadata=metadata,
            )
            for table in TABLES
        }
        summaries = replace_prefix(
            summaries, temporary_canonical.as_posix(), canonical_target.as_posix()
        )
        canonical_manifest = {
            "schema_version": 1,
            "audit_id": config["audit_id"],
            "audit_version": AUDIT_VERSION,
            "status": "complete",
            "scope": "aggregate_pre_split_feasibility_and_leakage_only",
            "completed_at_utc": _timestamp(),
            "git": git,
            "runtime": run_manifest["runtime"],
            "inputs": {
                "config": config_path.relative_to(project_root).as_posix(),
                "config_sha256": sha256_file(config_path),
                **verified_inputs,
                "run_manifest": (run_target / "RUN_MANIFEST.json").as_posix(),
                "run_manifest_sha256": run_manifest_sha,
            },
            "tables": summaries,
            "metrics": metrics,
            "primary_design": "reference_sequence_positive_unlabeled_ranking",
            "parent_audit_modified": False,
            "candidate_pair_materialization_performed": False,
            "candidate_sampling_performed": False,
            "positive_pair_rows_emitted": False,
            "endpoint_or_component_metric_rows_emitted": False,
            "evidence_indicator_construction_performed": False,
            "interaction_label_construction_performed": False,
            "negative_label_construction_performed": False,
            "pseudo_negative_sampling_performed": False,
            "selected_allocation_emitted": False,
            "c1_c2_c3_assignment_performed": False,
            "split_construction_performed": False,
            "structural_mapping_performed": False,
            "model_work_performed": False,
            "prevalence_estimation_performed": False,
            "calibration_performed": False,
            "external_panel_inputs_used": False,
            "return_to_governance_required": True,
        }
        canonical_manifest_sha = write_manifest(
            temporary_canonical / "AUDIT_MANIFEST.json", canonical_manifest
        )
        make_read_only(temporary_canonical)

    report = {
        "schema_version": 1,
        "audit_id": config["audit_id"],
        "audit_version": AUDIT_VERSION,
        "task": config["task"],
        "status": "complete",
        "scope": "qualification_smoke" if smoke else "production_full",
        "started_at_utc": started_at,
        "completed_at_utc": _timestamp(),
        "git": git,
        "runtime": run_manifest["runtime"],
        "inputs": {
            "config": config_path.relative_to(project_root).as_posix(),
            "config_sha256": sha256_file(config_path),
            **verified_inputs,
        },
        "outputs": {
            "run_manifest": (run_target / "RUN_MANIFEST.json").as_posix(),
            "run_manifest_sha256": run_manifest_sha,
            "canonical_manifest": (canonical_target / "AUDIT_MANIFEST.json").as_posix(),
            "canonical_manifest_sha256": canonical_manifest_sha,
            "candidate_pair_rows": "not_materialized",
            "positive_pair_rows": "not_emitted",
            "component_membership_rows": "not_emitted",
            "allocation_or_split_rows": "not_emitted",
        },
        "search_metrics": run_manifest["search_metrics"],
        "metrics": metrics,
        "scientific_interpretation": {
            "primary_design_preserved": "reference_sequence_positive_unlabeled_ranking",
            "unreported_eligible_pairs_remain_unlabeled": True,
            "allocation_results_are_opportunity_distributions_not_splits": True,
            "sensitivity_search_is_not_exhaustive_completeness_proof": True,
            "unseen_family_claim_supported": False,
            "external_panel_outcomes_used": False,
            "prevalence_identified": False,
            "calibration_performed": False,
            "model_performance_evaluated": False,
            "experimental_validation_claimed": False,
        },
        "authorizations": {
            "candidate_pair_materialization": False,
            "candidate_sampling": False,
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
    _write_report(report_target, report, project_root)
    return report


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/pre_split_feasibility_and_leakage_stress_test_v1.yaml"),
    )
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--skip-input-hashes", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())

    def absolute(path: Path | None) -> Path | None:
        if path is None or path.is_absolute():
            return path
        return project_root / path

    report = run_audit(
        project_root=project_root,
        config_path=absolute(args.config) or args.config,
        run_root=absolute(args.run_root),
        canonical_root=absolute(args.canonical_root),
        report_path=absolute(args.report),
        allow_dirty=args.allow_dirty,
        skip_input_hashes=args.skip_input_hashes,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
