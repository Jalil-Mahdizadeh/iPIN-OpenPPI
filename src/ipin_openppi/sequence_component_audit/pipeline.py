"""Execute the frozen Space III eligibility and sequence-component audit."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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
import pyarrow
import pyarrow as pa
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import (
    AtomicDatasetDirectory,
    ParquetBatchWriter,
    canonical_json,
    git_provenance,
    project_root_from,
    require_apptainer,
    stable_id,
)
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.sequence_component_audit import SEQUENCE_COMPONENT_AUDIT_VERSION
from ipin_openppi.sequence_component_audit.semantics import (
    classify_gene_mapping,
    classify_positive_projection,
    deterministic_component_memberships,
    exact_unordered_pair_count,
)
from ipin_openppi.sequence_component_audit.support import (
    artifact_inventory,
    load_json,
    load_yaml,
    make_read_only,
    replace_prefix,
    require_hash,
    require_scoped_outputs,
    resolve_inside,
    timestamp_utc,
    validate_config,
    verify_manifest_table,
    write_json,
    write_manifest,
)
from ipin_openppi.sequence_component_audit.tooling import verify_mmseqs_install
from ipin_openppi.validation.staging import _write_report


TABLES = (
    "space_iii_gene_eligibility",
    "eligible_reference_sequences",
    "sequence_component_assignments",
    "positive_mapping_aggregates",
    "positive_component_feasibility",
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
POSITIVE_CLASSES = (
    "unresolved_gene_projection",
    "outside_space_iii",
    "unmapped_endpoint",
    "ambiguous_endpoint",
    "same_reference_sequence",
    "eligible_distinct_reference_sequence_pair",
)


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _parquet_glob(root: Path) -> str:
    return (root / "*.parquet").as_posix()


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
        batch_rows=int(config["runtime"]["parquet_batch_rows"]),
        compression=str(config["runtime"]["parquet_compression"]),
        compression_level=int(config["runtime"]["parquet_compression_level"]),
        extra_metadata=metadata,
    ) as writer:
        writer.extend(rows)
    return writer.summary()


def _verify_sidecar(path: Path) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    tokens = sidecar.read_text(encoding="utf-8").split()
    if tokens != [sha256_file(path), path.name]:
        raise RuntimeError(f"Invalid SHA-256 sidecar for {path}")


def _verify_inputs(
    *,
    project_root: Path,
    config: Mapping[str, Any],
    verify_hashes: bool,
) -> tuple[dict[str, Path], dict[str, Any], dict[str, list[Path]]]:
    inputs = config["inputs"]
    specifications = {
        "primary_parse_manifest": ("primary_parse_manifest_sha256", "data/staging"),
        "primary_staging_validation_report": (
            "primary_staging_validation_report_sha256",
            "artifacts/validation",
        ),
        "primary_reconciliation_manifest": (
            "primary_reconciliation_manifest_sha256",
            "data/canonical",
        ),
        "primary_reconciliation_validation_report": (
            "primary_reconciliation_validation_report_sha256",
            "artifacts/validation",
        ),
        "benchmark_estimand_policy": ("benchmark_estimand_policy_sha256", "configs"),
        "accepted_blueprint_amendment": (
            "accepted_blueprint_amendment_sha256",
            "docs/blueprints",
        ),
        "incorporated_work_unit": (
            "incorporated_work_unit_sha256",
            "docs/blueprints",
        ),
        "authorization_decision": ("authorization_decision_sha256", "governance"),
        "disposition_acceptance": ("disposition_acceptance_sha256", "governance"),
        "resume_checkpoint": ("resume_checkpoint_sha256", "governance"),
        "active_gate": ("active_gate_sha256", "governance"),
        "audit_schema": ("audit_schema_sha256", "schemas"),
    }
    paths: dict[str, Path] = {}
    verified_documents: dict[str, Any] = {}
    for name, (hash_key, boundary) in specifications.items():
        path = resolve_inside(
            project_root,
            str(inputs[name]),
            project_root / boundary,
            strict=True,
        )
        paths[name] = path
        verified_documents[name] = require_hash(path, str(inputs[hash_key]))

    _verify_sidecar(paths["primary_parse_manifest"])
    _verify_sidecar(paths["primary_reconciliation_manifest"])
    _verify_sidecar(paths["primary_reconciliation_validation_report"])
    staging_validation = load_json(paths["primary_staging_validation_report"])
    reconciliation_validation = load_json(paths["primary_reconciliation_validation_report"])
    if staging_validation.get("status") != "pass" or reconciliation_validation.get("status") != "pass":
        raise RuntimeError("A frozen primary input validation report is not passing")
    policy = load_yaml(paths["benchmark_estimand_policy"])
    if (
        policy.get("status") != "accepted_effective"
        or policy.get("primary_design", {}).get("task")
        != "reference_sequence_positive_unlabeled_ranking"
        or policy.get("authorization", {}).get("candidate_pair_materialization") is not False
    ):
        raise RuntimeError("Accepted PU-R policy is absent or no longer fail-closed")
    gate = load_yaml(paths["active_gate"])
    gate_state = gate.get("gates", {}).get("evidence", {}).get(
        "benchmark_eligibility_and_sequence_component_audit", {}
    )
    if gate_state.get("fail_closed") is not True or gate_state.get("primary_design") != "reference_sequence_positive_unlabeled_ranking":
        raise RuntimeError("Active governance gate does not authorize this exact audit")

    staging_root = resolve_inside(
        project_root,
        str(inputs["primary_staging_root"]),
        project_root / "data/staging",
        strict=True,
    )
    reconciliation_root = resolve_inside(
        project_root,
        str(inputs["primary_reconciliation_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    paths["primary_staging_root"] = staging_root
    paths["primary_reconciliation_root"] = reconciliation_root
    parse_manifest = load_json(paths["primary_parse_manifest"])
    reconciliation_manifest = load_json(paths["primary_reconciliation_manifest"])
    if (
        parse_manifest.get("status") != "complete"
        or reconciliation_manifest.get("status") != "complete"
        or parse_manifest.get("label_construction_performed") is not False
        or reconciliation_manifest.get("label_construction_performed") is not False
        or reconciliation_manifest.get("model_training_performed") is not False
    ):
        raise RuntimeError("Frozen primary manifests do not preserve pre-label scope")

    source_tables = config["source_tables"]
    table_files: dict[str, list[Path]] = {}
    table_inventory: dict[str, Any] = {}
    for table_name in (
        "huri_space_membership",
        "protein_sequences",
        "identifier_mappings",
    ):
        table_root = staging_root / str(source_tables[table_name])
        files, inventory = verify_manifest_table(
            project_root=project_root,
            manifest=parse_manifest,
            table_name=table_name,
            expected_root=table_root,
            verify_hashes=verify_hashes,
        )
        table_files[table_name] = files
        table_inventory[table_name] = inventory
    projection_name = "huri_evidence_gene_pair_projections"
    projection_root = reconciliation_root / str(source_tables[projection_name])
    files, inventory = verify_manifest_table(
        project_root=project_root,
        manifest=reconciliation_manifest,
        table_name=projection_name,
        expected_root=projection_root,
        verify_hashes=verify_hashes,
    )
    table_files[projection_name] = files
    table_inventory[projection_name] = inventory
    return paths, {"documents": verified_documents, "tables": table_inventory}, table_files


def _register_input_views(
    connection: duckdb.DuckDBPyConnection, table_files: Mapping[str, Sequence[Path]]
) -> None:
    for table, paths in table_files.items():
        connection.read_parquet([path.as_posix() for path in paths]).create_view(table)


def _build_eligibility(
    connection: duckdb.DuckDBPyConnection,
    config: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, str], set[str], set[str]]:
    policy = config["eligibility_policy"]
    expected = config["expected_preflight"]
    source_counts = connection.execute(
        """
        SELECT count(*)::BIGINT, count(DISTINCT ensembl_gene_id)::BIGINT,
               count(*) FILTER (WHERE in_space_3)::BIGINT,
               count(DISTINCT ensembl_gene_id) FILTER (WHERE in_space_3)::BIGINT,
               count(*) FILTER (WHERE ensembl_gene_id IS NULL OR space_record_id IS NULL)::BIGINT
        FROM huri_space_membership
        """
    ).fetchone()
    if source_counts != (
        int(expected["huri_space_source_rows"]),
        int(expected["huri_space_source_rows"]),
        int(expected["space_iii_genes"]),
        int(expected["space_iii_genes"]),
        0,
    ):
        raise RuntimeError(f"Frozen HuRI Space inventory differs: {source_counts}")
    canonical_counts = connection.execute(
        """
        SELECT count(*)::BIGINT, count(DISTINCT sequence_sha256)::BIGINT,
               count(*) FILTER (WHERE length(sequence) != sequence_length)::BIGINT,
               count(*) FILTER (WHERE sequence_sha256 IS NULL OR sequence IS NULL)::BIGINT
        FROM protein_sequences
        WHERE canonical AND taxid = ? AND source_release = ?
        """,
        [int(policy["frozen_human_taxid"]), str(policy["frozen_uniprot_release"])],
    ).fetchone()
    if canonical_counts != (
        int(expected["frozen_human_canonical_sequence_rows"]),
        int(expected["frozen_human_canonical_distinct_hashes"]),
        0,
        0,
    ):
        raise RuntimeError(f"Frozen human canonical sequence inventory differs: {canonical_counts}")

    space_rows = connection.execute(
        """
        SELECT space_record_id, ensembl_gene_id, raw_file_path, raw_locator
        FROM huri_space_membership
        WHERE in_space_3
        ORDER BY ensembl_gene_id
        """
    ).fetchall()
    candidate_rows = connection.execute(
        """
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
         AND seq.canonical
         AND seq.taxid = ?
         AND seq.source_release = ?
        WHERE sp.in_space_3
        ORDER BY sp.ensembl_gene_id, seq.uniprot_accession, seq.protein_sequence_id
        """,
        [
            str(policy["identifier_database"]),
            str(policy["frozen_uniprot_release"]),
            int(policy["frozen_human_taxid"]),
            str(policy["frozen_uniprot_release"]),
        ],
    ).fetchall()
    candidates_by_gene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        sequence = str(row[5])
        observed_hash = hashlib.sha256(sequence.encode("ascii")).hexdigest()
        if observed_hash != str(row[3]) or len(sequence) != int(row[4]):
            raise RuntimeError(f"Frozen sequence hash/length mismatch for {row[1]}")
        candidates_by_gene[str(row[0])].append(
            {
                "accession": str(row[1]),
                "protein_sequence_id": str(row[2]),
                "hash": str(row[3]),
                "length": int(row[4]),
                "sequence": sequence,
                "release": str(row[6]),
                "raw_file_path": str(row[7]),
                "raw_file_sha256": str(row[8]),
            }
        )

    gene_rows: list[dict[str, Any]] = []
    sequence_groups: dict[str, dict[str, set[str]]] = {}
    sequence_values: dict[str, tuple[str, int, str]] = {}
    state_counts: Counter[str] = Counter()
    eligible_by_gene: dict[str, str] = {}
    ambiguous_genes: set[str] = set()
    unmapped_genes: set[str] = set()
    for space_record_id, gene_id, raw_file_path, raw_locator in space_rows:
        gene = str(gene_id)
        records = candidates_by_gene.get(gene, [])
        accessions = sorted({record["accession"] for record in records})
        hashes = sorted({record["hash"] for record in records})
        state, usable, exclusion = classify_gene_mapping(accessions, hashes)
        state_counts[state] += 1
        selected_hash = hashes[0] if usable else None
        lengths = {record["length"] for record in records if record["hash"] == selected_hash}
        if usable and len(lengths) != 1:
            raise RuntimeError(f"Eligible gene has inconsistent sequence lengths: {gene}")
        selected_length = next(iter(lengths)) if usable else None
        if usable:
            assert selected_hash is not None
            eligible_by_gene[gene] = selected_hash
            group = sequence_groups.setdefault(
                selected_hash,
                {"accessions": set(), "sequence_ids": set(), "genes": set(), "raw_paths": set(), "raw_hashes": set()},
            )
            group["genes"].add(gene)
            for record in records:
                if record["hash"] != selected_hash:
                    raise RuntimeError("Eligible gene retained a distinct sequence hash")
                group["accessions"].add(record["accession"])
                group["sequence_ids"].add(record["protein_sequence_id"])
                group["raw_paths"].add(record["raw_file_path"])
                group["raw_hashes"].add(record["raw_file_sha256"])
                value = (record["sequence"], record["length"], record["release"])
                if selected_hash in sequence_values and sequence_values[selected_hash] != value:
                    raise RuntimeError("One reference hash has conflicting frozen sequence values")
                sequence_values[selected_hash] = value
        elif state == "ambiguous_multiple_sequences":
            ambiguous_genes.add(gene)
        else:
            unmapped_genes.add(gene)
        missingness = {}
        if not usable:
            missingness = {
                "selected_sequence_sha256": exclusion,
                "selected_sequence_length": exclusion,
            }
        gene_rows.append(
            {
                "eligibility_record_id": stable_id("space3-eligibility", gene),
                "ensembl_gene_id": gene,
                "space_record_id": str(space_record_id),
                "in_space_iii": True,
                "mapping_state": state,
                "candidate_uniprot_accessions": accessions,
                "candidate_sequence_sha256s": hashes,
                "candidate_accession_count": len(accessions),
                "candidate_sequence_hash_count": len(hashes),
                "selected_sequence_sha256": selected_hash,
                "selected_sequence_length": selected_length,
                "eligibility_usable": usable,
                "exclusion_reason": exclusion,
                "frozen_uniprot_release": str(policy["frozen_uniprot_release"]),
                "source_raw_file_path": str(raw_file_path),
                "source_raw_locator": str(raw_locator),
                "candidate_pair_materialized": False,
                "evidence_indicator_constructed": False,
                "negative_label_constructed": False,
                "split_assignment_constructed": False,
                "model_use_authorized": False,
                "missingness_json": canonical_json(missingness),
            }
        )

    sequence_rows: list[dict[str, Any]] = []
    standard = set(str(policy["standard_amino_acids"]))
    selenocysteine_sequences = 0
    selenocysteine_residues = 0
    for sequence_hash in sorted(sequence_groups):
        group = sequence_groups[sequence_hash]
        sequence, length, release = sequence_values[sequence_hash]
        symbols = sorted(set(sequence) - standard)
        if set(sequence) - set(str(policy["source_preserved_amino_acids"])):
            raise RuntimeError(f"Unsupported source residue in sequence {sequence_hash}")
        contains_u = "U" in sequence
        selenocysteine_sequences += int(contains_u)
        selenocysteine_residues += sequence.count("U")
        accessions = sorted(group["accessions"])
        genes = sorted(group["genes"])
        sequence_rows.append(
            {
                "reference_sequence_sha256": sequence_hash,
                "sequence_length": length,
                "sequence": sequence,
                "representative_uniprot_accession": accessions[0],
                "uniprot_accessions": accessions,
                "protein_sequence_ids": sorted(group["sequence_ids"]),
                "space_iii_gene_ids": genes,
                "accession_count": len(accessions),
                "gene_count": len(genes),
                "contains_selenocysteine": contains_u,
                "nonstandard_residue_symbols": symbols,
                "frozen_uniprot_release": release,
                "source_raw_file_paths": sorted(group["raw_paths"]),
                "source_raw_file_sha256s": sorted(group["raw_hashes"]),
                "candidate_pair_materialized": False,
                "evidence_indicator_constructed": False,
                "negative_label_constructed": False,
                "split_assignment_constructed": False,
                "model_use_authorized": False,
            }
        )

    eligible_accessions = len(
        {accession for row in sequence_rows for accession in row["uniprot_accessions"]}
    )
    candidate_count = exact_unordered_pair_count(len(sequence_rows))
    observed = {
        "space_iii_genes": len(gene_rows),
        "mapping_states": dict(sorted(state_counts.items())),
        "eligible_space_iii_genes": len(eligible_by_gene),
        "eligible_reference_sequences": len(sequence_rows),
        "eligible_uniprot_accessions": eligible_accessions,
        "exact_unordered_candidate_count": candidate_count,
        "candidate_pair_rows_materialized": False,
        "candidate_universe_tested": False,
        "eligible_sequences_with_selenocysteine": selenocysteine_sequences,
        "eligible_selenocysteine_residues": selenocysteine_residues,
    }
    for key in (
        "space_iii_genes",
        "mapping_states",
        "eligible_space_iii_genes",
        "eligible_reference_sequences",
        "eligible_uniprot_accessions",
        "exact_unordered_candidate_count",
        "eligible_sequences_with_selenocysteine",
        "eligible_selenocysteine_residues",
    ):
        if observed[key] != expected[key]:
            raise RuntimeError(f"Eligibility preflight mismatch for {key}: {observed[key]}")
    return (
        gene_rows,
        sequence_rows,
        observed,
        eligible_by_gene,
        ambiguous_genes,
        unmapped_genes,
    )


def _build_positive_aggregates(
    connection: duckdb.DuckDBPyConnection,
    config: Mapping[str, Any],
    eligible_by_gene: Mapping[str, str],
    ambiguous_genes: set[str],
    unmapped_genes: set[str],
) -> tuple[list[dict[str, Any]], dict[str, set[tuple[str, str]]]]:
    policy = config["positive_mapping_policy"]
    datasets = [str(policy["aggregate_union_name"]), *map(str, policy["source_datasets"])]
    counters = {dataset: Counter() for dataset in datasets}
    pair_sets = {dataset: set() for dataset in datasets}
    rows = connection.execute(
        """
        SELECT source_dataset, unique_gene_pair, gene_a, gene_b, label_authorized
        FROM huri_evidence_gene_pair_projections
        ORDER BY source_dataset, projection_id
        """
    ).fetchall()
    for source_dataset, unique_gene_pair, gene_a, gene_b, label_authorized in rows:
        source = str(source_dataset)
        if source not in policy["source_datasets"] or bool(label_authorized):
            raise RuntimeError("Projection input is outside accepted HuRI evidence scope")
        state, pair = classify_positive_projection(
            unique_gene_pair=bool(unique_gene_pair),
            gene_a=None if gene_a is None else str(gene_a),
            gene_b=None if gene_b is None else str(gene_b),
            eligible_by_gene=eligible_by_gene,
            ambiguous_genes=ambiguous_genes,
            unmapped_genes=unmapped_genes,
        )
        for dataset in (source, str(policy["aggregate_union_name"])):
            counters[dataset]["source_evidence_rows"] += 1
            counters[dataset][state] += 1
            if pair is not None:
                pair_sets[dataset].add(pair)

    aggregate_rows: list[dict[str, Any]] = []
    expected = config["expected_preflight"]["positive_mapping"]
    for dataset in datasets:
        counter = counters[dataset]
        source_rows = int(counter["source_evidence_rows"])
        eligible_rows = int(counter["eligible_distinct_reference_sequence_pair"])
        observed_expected = {
            "source_evidence_rows": source_rows,
            "eligible_reference_sequence_pair_evidence_rows": eligible_rows,
            "distinct_eligible_reference_sequence_pairs": len(pair_sets[dataset]),
            "unresolved_gene_projection_rows": int(counter["unresolved_gene_projection"]),
            "outside_space_iii_rows": int(counter["outside_space_iii"]),
            "unmapped_endpoint_rows": int(counter["unmapped_endpoint"]),
            "ambiguous_endpoint_rows": int(counter["ambiguous_endpoint"]),
            "same_reference_sequence_rows": int(counter["same_reference_sequence"]),
        }
        if observed_expected != expected[dataset]:
            raise RuntimeError(
                f"Positive mapping preflight mismatch for {dataset}: {observed_expected}"
            )
        aggregate_rows.append(
            {
                "aggregate_id": stable_id("positive-mapping-aggregate", dataset),
                "source_dataset": dataset,
                **observed_expected,
                "resolved_unique_gene_pair_rows": source_rows
                - observed_expected["unresolved_gene_projection_rows"],
                "eligible_evidence_fraction": eligible_rows / source_rows,
                "pair_rows_emitted": False,
                "evidence_indicator_constructed": False,
                "interaction_label_constructed": False,
                "negative_label_constructed": False,
                "prevalence_estimated": False,
                "calibration_performed": False,
            }
        )
    return aggregate_rows, pair_sets


def _write_fasta(path: Path, sequence_rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("wt", encoding="ascii", newline="\n") as handle:
        for row in sequence_rows:
            handle.write(f">{row['reference_sequence_sha256']}\n")
            sequence = str(row["sequence"])
            for offset in range(0, len(sequence), 80):
                handle.write(sequence[offset : offset + 80] + "\n")


def _run_command(command: list[str], step: str) -> dict[str, Any]:
    started = timestamp_utc()
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
        "completed_at_utc": timestamp_utc(),
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _run_mmseqs(
    *,
    project_root: Path,
    temporary_run: Path,
    fasta_path: Path,
    binary: Path,
    config: Mapping[str, Any],
) -> tuple[Path, list[dict[str, Any]]]:
    scratch_parent = project_root / "artifacts/tmp"
    scratch_parent.mkdir(parents=True, exist_ok=True)
    tool = config["mmseqs2"]
    alignment_path = temporary_run / "alignments.tsv"
    logs: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="mmseqs-work-", dir=scratch_parent) as raw_work:
        work = Path(raw_work)
        sequence_db = work / "eligible_sequences"
        result_db = work / "search_result"
        search_tmp = work / "search_tmp"
        commands = [
            (
                "createdb",
                [
                    binary.as_posix(),
                    "createdb",
                    fasta_path.as_posix(),
                    sequence_db.as_posix(),
                    *map(str, tool["createdb_parameters"]),
                ],
            ),
            (
                "search",
                [
                    binary.as_posix(),
                    "search",
                    sequence_db.as_posix(),
                    sequence_db.as_posix(),
                    result_db.as_posix(),
                    search_tmp.as_posix(),
                    *map(str, tool["search_parameters"]),
                ],
            ),
            (
                "convertalis",
                [
                    binary.as_posix(),
                    "convertalis",
                    sequence_db.as_posix(),
                    sequence_db.as_posix(),
                    result_db.as_posix(),
                    alignment_path.as_posix(),
                    "--format-mode",
                    "0",
                    "--format-output",
                    ",".join(map(str, tool["alignment_output_fields"])),
                    "--threads",
                    str(config["runtime"]["duckdb_threads"]),
                ],
            ),
        ]
        for step, command in commands:
            logs.append(_run_command(command, step))
    if alignment_path.is_symlink() or not alignment_path.is_file():
        raise RuntimeError("MMseqs2 did not produce a regular alignment table")
    return alignment_path, logs


def _normalize_alignments(
    *,
    connection: duckdb.DuckDBPyConnection,
    alignment_path: Path,
    normalized_path: Path,
    sequence_rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    columns_sql = "{" + ",".join(
        f"{_sql_string(name)}:{_sql_string(kind)}" for name, kind in ALIGNMENT_COLUMNS.items()
    ) + "}"
    connection.execute(
        f"""
        CREATE OR REPLACE VIEW raw_sequence_alignments AS
        SELECT * FROM read_csv(
          {_sql_string(alignment_path.as_posix())}, delim='\\t', header=false,
          columns={columns_sql}, strict_mode=true, null_padding=false
        )
        """
    )
    nodes = pa.table(
        {
            "sequence_hash": [str(row["reference_sequence_sha256"]) for row in sequence_rows],
            "sequence_length": [int(row["sequence_length"]) for row in sequence_rows],
        }
    )
    connection.register("eligible_sequence_nodes_arrow", nodes)
    connection.execute(
        "CREATE OR REPLACE VIEW eligible_sequence_nodes AS SELECT * FROM eligible_sequence_nodes_arrow"
    )
    minimum_identity = float(config["sequence_components"]["search_minimum_identity"])
    minimum_coverage = float(config["sequence_components"]["minimum_endpoint_coverage"])
    raw_records = int(connection.execute("SELECT count(*) FROM raw_sequence_alignments").fetchone()[0])
    structural_invalid = int(
        connection.execute(
            """
            SELECT count(*)
            FROM raw_sequence_alignments a
            LEFT JOIN eligible_sequence_nodes q ON q.sequence_hash = a.query
            LEFT JOIN eligible_sequence_nodes t ON t.sequence_hash = a.target
            WHERE q.sequence_hash IS NULL OR t.sequence_hash IS NULL
               OR a.alnlen <= 0 OR a.mismatch < 0 OR a.mismatch > a.alnlen
               OR a.qlen != q.sequence_length OR a.tlen != t.sequence_length
               OR a.qstart < 1 OR a.qend < 1 OR a.tstart < 1 OR a.tend < 1
               OR a.qstart > a.qlen OR a.qend > a.qlen
               OR a.tstart > a.tlen OR a.tend > a.tlen
               OR ((abs(a.qend - a.qstart) + 1) + (abs(a.tend - a.tstart) + 1) - a.alnlen - a.mismatch)
                    NOT BETWEEN 0 AND a.alnlen
               OR NOT isfinite(a.evalue) OR NOT isfinite(a.bits)
            """,
        ).fetchone()[0]
    )
    if structural_invalid:
        raise RuntimeError(
            f"MMseqs2 alignment table has {structural_invalid} structurally invalid records"
        )
    rejected = connection.execute(
        """
        WITH exact_scores AS (
          SELECT ((abs(qend - qstart) + 1) + (abs(tend - tstart) + 1)
                    - alnlen - mismatch)::DOUBLE / alnlen AS identity,
                 (abs(qend - qstart) + 1)::DOUBLE / qlen AS query_coverage,
                 (abs(tend - tstart) + 1)::DOUBLE / tlen AS target_coverage
          FROM raw_sequence_alignments
        )
        SELECT count(*) FILTER (WHERE identity + 1e-12 < ?)::BIGINT,
               count(*) FILTER (WHERE query_coverage + 1e-12 < ?
                                  OR target_coverage + 1e-12 < ?)::BIGINT,
               count(*) FILTER (WHERE identity + 1e-12 < ?
                                  OR query_coverage + 1e-12 < ?
                                  OR target_coverage + 1e-12 < ?)::BIGINT
        FROM exact_scores
        """,
        [
            minimum_identity,
            minimum_coverage,
            minimum_coverage,
            minimum_identity,
            minimum_coverage,
            minimum_coverage,
        ],
    ).fetchone()
    below_identity, below_endpoint_coverage, exact_criteria_rejected = map(
        int, rejected
    )
    self_queries = int(
        connection.execute(
            "SELECT count(DISTINCT query) FROM raw_sequence_alignments WHERE query = target"
        ).fetchone()[0]
    )
    if self_queries != len(sequence_rows):
        raise RuntimeError("MMseqs2 self matches do not cover every eligible sequence")
    connection.execute(
        f"""
        COPY (
          SELECT least(query, target) AS sequence_a_sha256,
                 greatest(query, target) AS sequence_b_sha256,
                 max(((abs(qend - qstart) + 1) + (abs(tend - tstart) + 1) - alnlen - mismatch)::DOUBLE / alnlen) AS maximum_identity,
                 max(least(
                   (abs(qend - qstart) + 1)::DOUBLE / qlen,
                   (abs(tend - tstart) + 1)::DOUBLE / tlen
                 )) AS maximum_minimum_endpoint_coverage,
                 count(*)::BIGINT AS supporting_alignment_records
          FROM raw_sequence_alignments
          WHERE query != target
            AND ((abs(qend - qstart) + 1) + (abs(tend - tstart) + 1) - alnlen - mismatch)::DOUBLE / alnlen + 1e-12 >= {minimum_identity:.17g}
            AND (abs(qend - qstart) + 1)::DOUBLE / qlen + 1e-12 >= {minimum_coverage:.17g}
            AND (abs(tend - tstart) + 1)::DOUBLE / tlen + 1e-12 >= {minimum_coverage:.17g}
          GROUP BY sequence_a_sha256, sequence_b_sha256
          ORDER BY sequence_a_sha256, sequence_b_sha256
        ) TO {_sql_string(normalized_path.as_posix())}
        (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    edge_rows = int(pq.ParquetFile(normalized_path).metadata.num_rows)
    return {
        "raw_alignment_records": raw_records,
        "structurally_invalid_records": structural_invalid,
        "below_exact_identity_records": below_identity,
        "below_exact_endpoint_coverage_records": below_endpoint_coverage,
        "exact_criteria_rejected_records": exact_criteria_rejected,
        "self_match_query_sequences": self_queries,
        "normalized_nonself_edges": edge_rows,
        "raw_alignment_sha256": sha256_file(alignment_path),
        "normalized_edges_sha256": sha256_file(normalized_path),
        "identity_uses_integer_derived_identical_over_alnlen": True,
        "minimum_endpoint_coverage_reverified": minimum_coverage,
    }


def _nearest_rank(values: Sequence[int], fraction: float) -> int:
    if not values:
        return 0
    return sorted(values)[max(0, math.ceil(fraction * len(values)) - 1)]


def _build_components(
    *,
    connection: duckdb.DuckDBPyConnection,
    normalized_path: Path,
    sequence_rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    connection.execute(
        f"CREATE OR REPLACE VIEW normalized_sequence_edges AS SELECT * FROM read_parquet({_sql_string(normalized_path.as_posix())})"
    )
    nodes = [str(row["reference_sequence_sha256"]) for row in sequence_rows]
    assignment_rows: list[dict[str, Any]] = []
    summaries: dict[int, dict[str, Any]] = {}
    memberships_by_threshold: dict[int, dict[str, Any]] = {}
    for threshold in map(int, config["sequence_components"]["emitted_thresholds_percent"]):
        cursor = connection.execute(
            """
            SELECT sequence_a_sha256, sequence_b_sha256
            FROM normalized_sequence_edges
            WHERE maximum_identity + 1e-12 >= ?
            ORDER BY sequence_a_sha256, sequence_b_sha256
            """,
            [threshold / 100.0],
        )

        def edge_iter() -> Iterable[tuple[str, str]]:
            while batch := cursor.fetchmany(100000):
                for endpoint_a, endpoint_b in batch:
                    yield str(endpoint_a), str(endpoint_b)

        memberships = deterministic_component_memberships(
            sequence_hashes=nodes,
            edges=edge_iter(),
            identity_threshold_percent=threshold,
        )
        memberships_by_threshold[threshold] = memberships
        sizes_by_id: dict[str, int] = {}
        for membership in memberships.values():
            sizes_by_id[membership.component_id] = membership.size
        sizes = sorted(sizes_by_id.values())
        edge_count = int(
            connection.execute(
                "SELECT count(*) FROM normalized_sequence_edges WHERE maximum_identity + 1e-12 >= ?",
                [threshold / 100.0],
            ).fetchone()[0]
        )
        summaries[threshold] = {
            "identity_threshold_percent": threshold,
            "sequence_count": len(nodes),
            "edge_count": edge_count,
            "component_count": len(sizes),
            "singleton_components": sum(size == 1 for size in sizes),
            "largest_component_size": max(sizes),
            "component_size_q50": _nearest_rank(sizes, 0.50),
            "component_size_q90": _nearest_rank(sizes, 0.90),
            "component_size_q95": _nearest_rank(sizes, 0.95),
            "component_size_q99": _nearest_rank(sizes, 0.99),
        }
        for sequence_hash in nodes:
            membership = memberships[sequence_hash]
            assignment_rows.append(
                {
                    "assignment_id": stable_id(
                        "seqcomp-assignment", threshold, sequence_hash
                    ),
                    "identity_threshold_percent": threshold,
                    "reference_sequence_sha256": sequence_hash,
                    "component_id": membership.component_id,
                    "component_representative_sha256": membership.representative,
                    "component_size": membership.size,
                    "component_member_rank": membership.member_rank,
                    "minimum_endpoint_coverage": float(
                        config["sequence_components"]["minimum_endpoint_coverage"]
                    ),
                    "component_algorithm": str(
                        config["sequence_components"]["algorithm"]
                    ),
                    "mmseqs_release": str(config["mmseqs2"]["release"]),
                    "mmseqs_binary_sha256": str(config["mmseqs2"]["binary_sha256"]),
                    "candidate_pair_materialized": False,
                    "evidence_indicator_constructed": False,
                    "negative_label_constructed": False,
                    "split_assignment_constructed": False,
                    "model_use_authorized": False,
                }
            )
    return assignment_rows, summaries, memberships_by_threshold


def _build_feasibility(
    *,
    pair_sets: Mapping[str, set[tuple[str, str]]],
    memberships_by_threshold: Mapping[int, Mapping[str, Any]],
    component_summaries: Mapping[int, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    policy = config["positive_mapping_policy"]
    datasets = [str(policy["aggregate_union_name"]), *map(str, policy["source_datasets"])]
    rows: list[dict[str, Any]] = []
    for dataset in datasets:
        pairs = pair_sets[dataset]
        endpoints = {endpoint for pair in pairs for endpoint in pair}
        for threshold in map(int, config["sequence_components"]["emitted_thresholds_percent"]):
            memberships = memberships_by_threshold[threshold]
            within = sum(
                memberships[a].component_id == memberships[b].component_id
                for a, b in pairs
            )
            exposed_components = {
                memberships[endpoint].component_id for endpoint in endpoints
            }
            summary = component_summaries[threshold]
            rows.append(
                {
                    "aggregate_id": stable_id(
                        "positive-component-feasibility", dataset, threshold
                    ),
                    "source_dataset": dataset,
                    "identity_threshold_percent": threshold,
                    "distinct_eligible_reference_sequence_pairs": len(pairs),
                    "positive_endpoint_sequences": len(endpoints),
                    "positive_exposed_components": len(exposed_components),
                    "within_component_pair_count": within,
                    "cross_component_pair_count": len(pairs) - within,
                    "total_components": int(summary["component_count"]),
                    "singleton_components": int(summary["singleton_components"]),
                    "largest_component_size": int(summary["largest_component_size"]),
                    "total_positive_pair_floor_500_met": len(pairs)
                    >= int(policy["minimum_later_held_out_positive_pairs"]),
                    "total_component_floor_50_met": int(summary["component_count"])
                    >= int(policy["minimum_later_independent_sequence_components"]),
                    "held_out_floor_assessed": False,
                    "later_split_feasibility_determined": False,
                    "pair_rows_emitted": False,
                    "split_assignment_constructed": False,
                    "c1_c2_c3_assignment_constructed": False,
                }
            )
    return rows


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
    started_at = timestamp_utc()
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
    smoke = require_scoped_outputs(
        paths=(run_target, canonical_target, report_target),
        allow_dirty=allow_dirty,
        skip_input_hashes=skip_input_hashes,
    )
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production sequence-component audit requires a clean Git worktree")
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    if active_container != expected_container:
        raise RuntimeError("Active Apptainer image differs from audit configuration")
    container_sha = sha256_file(active_container)
    if container_sha != str(config["runtime"]["container_sha256"]):
        raise RuntimeError("Active Apptainer image SHA-256 differs from audit configuration")
    if platform.machine() != str(config["runtime"]["architecture"]):
        raise RuntimeError("Sequence-component audit is running on the wrong architecture")
    tool_inventory = verify_mmseqs_install(project_root=project_root, config=config)
    binary = Path(tool_inventory["binary"])
    paths, verified_inputs, table_files = _verify_inputs(
        project_root=project_root,
        config=config,
        verify_hashes=not skip_input_hashes,
    )

    connection = duckdb.connect(":memory:")
    connection.execute(f"SET memory_limit={_sql_string(str(config['runtime']['duckdb_memory_limit']))}")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    connection.execute("PRAGMA disable_progress_bar")
    try:
        _register_input_views(connection, table_files)
        (
            gene_rows,
            sequence_rows,
            eligibility_metrics,
            eligible_by_gene,
            ambiguous_genes,
            unmapped_genes,
        ) = _build_eligibility(connection, config)
        positive_rows, pair_sets = _build_positive_aggregates(
            connection,
            config,
            eligible_by_gene,
            ambiguous_genes,
            unmapped_genes,
        )

        with AtomicDatasetDirectory(run_target) as temporary_run:
            fasta_path = temporary_run / "eligible_reference_sequences.fasta"
            _write_fasta(fasta_path, sequence_rows)
            alignment_path, command_logs = _run_mmseqs(
                project_root=project_root,
                temporary_run=temporary_run,
                fasta_path=fasta_path,
                binary=binary,
                config=config,
            )
            normalized_path = temporary_run / "normalized_alignment_edges.parquet"
            alignment_metrics = _normalize_alignments(
                connection=connection,
                alignment_path=alignment_path,
                normalized_path=normalized_path,
                sequence_rows=sequence_rows,
                config=config,
            )
            assignment_rows, component_summaries, memberships = _build_components(
                connection=connection,
                normalized_path=normalized_path,
                sequence_rows=sequence_rows,
                config=config,
            )
            feasibility_rows = _build_feasibility(
                pair_sets=pair_sets,
                memberships_by_threshold=memberships,
                component_summaries=component_summaries,
                config=config,
            )
            command_path = temporary_run / "MMSEQS_COMMANDS.json"
            write_json(
                command_path,
                {
                    "schema_version": 1,
                    "tool": tool_inventory,
                    "configured_createdb_parameters": config["mmseqs2"]["createdb_parameters"],
                    "configured_search_parameters": config["mmseqs2"]["search_parameters"],
                    "alignment_output_fields": config["mmseqs2"]["alignment_output_fields"],
                    "executions": command_logs,
                },
            )
            run_files = artifact_inventory(temporary_run, run_target)
            run_manifest = {
                "schema_version": 1,
                "audit_id": config["audit_id"],
                "audit_version": SEQUENCE_COMPONENT_AUDIT_VERSION,
                "status": "complete",
                "scope": "sequence_similarity_run_artifacts_not_ppi_candidate_pairs",
                "started_at_utc": started_at,
                "completed_at_utc": timestamp_utc(),
                "git": git,
                "runtime": {
                    "container_sif_sha256": container_sha,
                    "architecture": platform.machine(),
                    "python": platform.python_version(),
                    "duckdb": duckdb.__version__,
                    "pyarrow": pyarrow.__version__,
                },
                "tool": tool_inventory,
                "config": {
                    "path": config_path.relative_to(project_root).as_posix(),
                    "sha256": sha256_file(config_path),
                },
                "files": run_files,
                "alignment_metrics": alignment_metrics,
                "candidate_pair_materialization_performed": False,
                "evidence_indicator_construction_performed": False,
                "label_construction_performed": False,
                "split_construction_performed": False,
                "model_work_performed": False,
            }
            run_manifest_sha = write_manifest(
                temporary_run / "RUN_MANIFEST.json", run_manifest
            )
            make_read_only(temporary_run)
    finally:
        connection.close()

    positive_metrics = {row["source_dataset"]: row for row in positive_rows}
    feasibility_metrics = {
        f"{row['source_dataset']}:{row['identity_threshold_percent']}": row
        for row in feasibility_rows
    }
    metrics = {
        "eligibility": eligibility_metrics,
        "alignment": alignment_metrics,
        "components": {str(key): value for key, value in component_summaries.items()},
        "positive_mapping_aggregates": positive_metrics,
        "positive_component_feasibility": feasibility_metrics,
    }
    contract = load_contract(paths["audit_schema"])
    metadata = {
        "audit_version": SEQUENCE_COMPONENT_AUDIT_VERSION,
        "audit_git_commit": str(git["commit"]),
        "container_sif_sha256": container_sha,
        "primary_design": "reference_sequence_positive_unlabeled_ranking",
        "candidate_pair_materialized": "false",
        "split_assignment_constructed": "false",
    }
    table_rows = {
        "space_iii_gene_eligibility": gene_rows,
        "eligible_reference_sequences": sequence_rows,
        "sequence_component_assignments": assignment_rows,
        "positive_mapping_aggregates": positive_rows,
        "positive_component_feasibility": feasibility_rows,
    }
    with AtomicDatasetDirectory(canonical_target) as temporary_canonical:
        table_summaries = {
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
        table_summaries = replace_prefix(
            table_summaries,
            temporary_canonical.as_posix(),
            canonical_target.as_posix(),
        )
        canonical_manifest = {
            "schema_version": 1,
            "audit_id": config["audit_id"],
            "audit_version": SEQUENCE_COMPONENT_AUDIT_VERSION,
            "status": "complete",
            "scope": "preconstruction_eligibility_components_and_aggregate_feasibility",
            "completed_at_utc": timestamp_utc(),
            "git": git,
            "runtime": {
                "container_sif_sha256": container_sha,
                "architecture": platform.machine(),
                "python": platform.python_version(),
                "duckdb": duckdb.__version__,
                "pyarrow": pyarrow.__version__,
            },
            "inputs": {
                "config": config_path.relative_to(project_root).as_posix(),
                "config_sha256": sha256_file(config_path),
                **verified_inputs,
                "run_manifest": (run_target / "RUN_MANIFEST.json").as_posix(),
                "run_manifest_sha256": run_manifest_sha,
            },
            "tables": table_summaries,
            "metrics": metrics,
            "primary_design": "reference_sequence_positive_unlabeled_ranking",
            "output_is_probability": False,
            "candidate_pair_materialization_performed": False,
            "candidate_universe_called_tested": False,
            "evidence_indicator_construction_performed": False,
            "interaction_label_construction_performed": False,
            "negative_label_construction_performed": False,
            "pseudo_negative_sampling_performed": False,
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
        "audit_version": SEQUENCE_COMPONENT_AUDIT_VERSION,
        "task": config["task"],
        "status": "complete",
        "scope": "qualification_smoke" if smoke else "production_full",
        "started_at_utc": started_at,
        "completed_at_utc": timestamp_utc(),
        "git": git,
        "runtime": canonical_manifest["runtime"],
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
        },
        "metrics": metrics,
        "scientific_interpretation": {
            "primary_design_preserved": "reference_sequence_positive_unlabeled_ranking",
            "candidate_count_is_algebraic_not_tested": True,
            "unreported_eligible_pairs_remain_unlabeled": True,
            "component_feasibility_is_pre_split_and_not_a_held_out_guarantee": True,
            "external_panel_outcomes_used": False,
            "universal_nonbinding_interpretation": False,
            "prevalence_identified": False,
            "calibration_performed": False,
            "experimental_validation_claimed": False,
        },
        "authorizations": {
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
    _write_report(report_target, report, project_root)
    return report


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/benchmark_eligibility_and_sequence_component_audit_v1.yaml"),
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
