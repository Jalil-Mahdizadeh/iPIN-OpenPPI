"""Construct and seal pair-level artifacts under the frozen DEC-0024 protocol."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
import json
import os
from pathlib import Path
import platform
import tempfile
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import (
    AtomicDatasetDirectory,
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.pair_protocol.pipeline import (
    _load_endpoints,
    _load_positive_pairs,
    _primary_cell,
    _register_views,
    _verify_inputs as verify_protocol_inputs,
)
from ipin_openppi.pair_protocol.semantics import (
    c1_role,
    degree_bin,
    degree_pair_stratum,
    hamilton_sample_allocation,
    pair_id,
)
from ipin_openppi.pair_protocol.support import (
    load_yaml as load_protocol_yaml,
    validate_config as validate_protocol_config,
)
from ipin_openppi.sequence_component_audit.support import (
    artifact_inventory,
    make_read_only,
    replace_prefix,
    write_json,
    write_manifest,
)
from ipin_openppi.validation.staging import _write_report

from . import ARTIFACT_PACKAGE_VERSION
from .support import (
    PACKAGE_ID,
    PRIMARY_CELLS,
    SOURCES,
    cms_encrypt,
    dataset_summary,
    deterministic_tar,
    load_yaml,
    private_key_paths,
    rational_design,
    resolve_inside,
    validate_config,
    verify_arrow_schema,
    verify_documents,
    verify_key_pairs,
    write_rows_part,
)


@dataclass(frozen=True)
class CellSpec:
    axis: str
    target_source: str | None
    primary_cell: str
    cell_id: str
    positive_pairs: frozenset[tuple[str, str]]
    degree: Mapping[str, int]
    exposed: frozenset[str]


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sql_string(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _source_membership(sources: frozenset[str]) -> str:
    if sources == frozenset(SOURCES):
        return "both"
    return "HI-II-14_only" if "HI-II-14" in sources else "HuRI_only"


def _primary_state(
    *,
    pair: tuple[str, str],
    partition: Mapping[str, str],
    exposed: set[str],
    hash_role: str | None,
    training_pairs: set[tuple[str, str]],
    primary_sets: Mapping[str, set[tuple[str, str]]],
) -> tuple[str, str | None]:
    if pair in training_pairs:
        return "training", None
    for cell in PRIMARY_CELLS:
        if pair in primary_sets[cell]:
            return cell, None
    left, right = partition[pair[0]], partition[pair[1]]
    if left == right == "train" and hash_role in {"development", "test"}:
        return "quarantine", f"C1_{hash_role}_failed_exposure"
    names = {left, right}
    for heldout in ("development", "test"):
        if names == {"train", heldout}:
            return "quarantine", f"C2_{heldout}_failed_train_exposure"
    if names == {"development", "test"}:
        return "quarantine", "development_test_cross_partition"
    return "quarantine", "outside_primary_evaluation_geometry"


def _prepare_state(
    *,
    partition: Mapping[str, str],
    component: Mapping[str, str],
    positive_pairs: set[tuple[str, str]],
    pair_sources: Mapping[tuple[str, str], frozenset[str]],
    protocol: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    assignment = protocol["pair_assignment"]
    roles = {
        pair: c1_role(
            pair,
            salt=str(assignment["public_salt"]),
            seed=str(assignment["deterministic_seed"]),
        )
        for pair in positive_pairs
        if partition[pair[0]] == partition[pair[1]] == "train"
    }
    training_pairs = {pair for pair, role in roles.items() if role == "train"}
    primary_degree = Counter(endpoint for pair in training_pairs for endpoint in pair)
    primary_exposed = set(primary_degree)
    primary_sets = {
        cell: {
            pair
            for pair in positive_pairs
            if _primary_cell(
                pair,
                partition=partition,
                exposed=primary_exposed,
                role=roles.get(pair),
            )
            == cell
        }
        for cell in PRIMARY_CELLS
    }

    source_visible: dict[str, set[tuple[str, str]]] = {}
    source_degree: dict[str, Counter[str]] = {}
    source_exposed: dict[str, set[str]] = {}
    source_sets: dict[str, dict[str, set[tuple[str, str]]]] = {}
    for target, other in (("HI-II-14", "HuRI"), ("HuRI", "HI-II-14")):
        visible = {
            pair
            for pair in positive_pairs
            if partition[pair[0]] == partition[pair[1]] == "train"
            and roles.get(pair) == "train"
            and other in pair_sources[pair]
        }
        degree = Counter(endpoint for pair in visible for endpoint in pair)
        exposed = set(degree)
        target_only = {
            pair for pair in positive_pairs if pair_sources[pair] == frozenset({target})
        }
        cells = {
            cell: {
                pair
                for pair in target_only
                if _primary_cell(
                    pair,
                    partition=partition,
                    exposed=exposed,
                    role=roles.get(pair),
                )
                == cell
            }
            for cell in PRIMARY_CELLS
        }
        source_visible[target] = visible
        source_degree[target] = degree
        source_exposed[target] = exposed
        source_sets[target] = cells

    expected = config["immutable_parent_expectations"]
    if len(positive_pairs) != int(expected["released_positive_pairs"]):
        raise RuntimeError("Released-positive union changed")
    if len(training_pairs) != int(expected["training_positive_pairs"]):
        raise RuntimeError("Training-positive count changed")
    if len(primary_exposed) != int(expected["training_exposed_endpoints"]):
        raise RuntimeError("Training-exposed endpoint count changed")
    for cell in PRIMARY_CELLS:
        if len(primary_sets[cell]) != int(expected["primary_positive_pairs"][cell]):
            raise RuntimeError(f"Primary positive count changed: {cell}")
    for target in SOURCES:
        if len(source_visible[target]) != int(
            expected["source_visible_training_pairs"][target]
        ):
            raise RuntimeError(f"Source-visible training count changed: {target}")
        if len(source_exposed[target]) != int(
            expected["source_visible_training_endpoints"][target]
        ):
            raise RuntimeError(f"Source-visible endpoint count changed: {target}")
        for cell in PRIMARY_CELLS:
            if len(source_sets[target][cell]) != int(
                expected["source_exclusive_positive_pairs"][target][cell]
            ):
                raise RuntimeError(
                    f"Source-exclusive positive count changed: {target}/{cell}"
                )

    role_sets = [training_pairs, *(primary_sets[cell] for cell in PRIMARY_CELLS)]
    if sum(map(len, role_sets)) != len(set().union(*role_sets)):
        raise RuntimeError("A primary positive pair occupies multiple roles")

    return {
        "roles": roles,
        "training_pairs": training_pairs,
        "primary_degree": primary_degree,
        "primary_exposed": primary_exposed,
        "primary_sets": primary_sets,
        "source_visible": source_visible,
        "source_degree": source_degree,
        "source_exposed": source_exposed,
        "source_sets": source_sets,
        "partition": partition,
        "component": component,
        "positive_pairs": positive_pairs,
        "pair_sources": pair_sources,
    }


def _cell_specs(
    state: Mapping[str, Any],
) -> tuple[CellSpec, list[CellSpec], list[CellSpec]]:
    training = CellSpec(
        axis="primary",
        target_source=None,
        primary_cell="training",
        cell_id="training",
        positive_pairs=frozenset(state["training_pairs"]),
        degree=state["primary_degree"],
        exposed=frozenset(state["primary_exposed"]),
    )
    development: list[CellSpec] = []
    test: list[CellSpec] = []
    for cell in PRIMARY_CELLS:
        spec = CellSpec(
            axis="primary",
            target_source=None,
            primary_cell=cell,
            cell_id=cell,
            positive_pairs=frozenset(state["primary_sets"][cell]),
            degree=state["primary_degree"],
            exposed=frozenset(state["primary_exposed"]),
        )
        (development if cell.endswith("_development") else test).append(spec)
    for target in SOURCES:
        for cell in PRIMARY_CELLS:
            spec = CellSpec(
                axis="source_exclusive",
                target_source=target,
                primary_cell=cell,
                cell_id=f"source_exclusive:{target}:{cell}",
                positive_pairs=frozenset(state["source_sets"][target][cell]),
                degree=state["source_degree"][target],
                exposed=frozenset(state["source_exposed"][target]),
            )
            (development if cell.endswith("_development") else test).append(spec)
    key = lambda spec: (spec.axis, spec.target_source or "", spec.primary_cell)
    return training, sorted(development, key=key), sorted(test, key=key)


def _register_static_tables(
    connection: duckdb.DuckDBPyConnection,
    *,
    partition: Mapping[str, str],
    component: Mapping[str, str],
    positive_pairs: set[tuple[str, str]],
) -> None:
    endpoint_rows = [
        {
            "endpoint": endpoint,
            "component_id": component[endpoint],
            "partition": partition[endpoint],
        }
        for endpoint in sorted(partition)
    ]
    positive_rows = [
        {"endpoint_a": pair[0], "endpoint_b": pair[1]}
        for pair in sorted(positive_pairs)
    ]
    connection.register("_endpoint_catalog_arrow", pa.Table.from_pylist(endpoint_rows))
    connection.execute(
        "CREATE TEMP TABLE endpoint_catalog AS SELECT * FROM _endpoint_catalog_arrow"
    )
    connection.unregister("_endpoint_catalog_arrow")
    connection.register("_positive_union_arrow", pa.Table.from_pylist(positive_rows))
    connection.execute(
        "CREATE TEMP TABLE positive_union AS SELECT * FROM _positive_union_arrow"
    )
    connection.unregister("_positive_union_arrow")


def _register_cell_endpoints(
    connection: duckdb.DuckDBPyConnection,
    *,
    partition: Mapping[str, str],
    component: Mapping[str, str],
    spec: CellSpec,
) -> None:
    rows = []
    for endpoint in sorted(partition):
        degree = int(spec.degree.get(endpoint, 0))
        label = degree_bin(degree)
        rows.append(
            {
                "endpoint": endpoint,
                "component_id": component[endpoint],
                "partition": partition[endpoint],
                "training_degree": degree,
                "degree_bin": label,
                "degree_bin_order": (
                    "0",
                    "1",
                    "2",
                    "3-4",
                    "5-9",
                    "10-19",
                    "20-49",
                    "50-99",
                    "100+",
                ).index(label),
                "exposed": endpoint in spec.exposed,
            }
        )
    connection.register("_cell_endpoints_arrow", pa.Table.from_pylist(rows))
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE cell_endpoints AS "
        "SELECT * FROM _cell_endpoints_arrow"
    )
    connection.unregister("_cell_endpoints_arrow")


def _candidate_base_sql(spec: CellSpec) -> str:
    if spec.primary_cell in {"training", "C1_development", "C1_test"}:
        geometry = """
            SELECT a.endpoint AS endpoint_a, b.endpoint AS endpoint_b
            FROM cell_endpoints a
            JOIN cell_endpoints b ON a.endpoint < b.endpoint
            WHERE a.exposed AND b.exposed
        """
    elif spec.primary_cell.startswith("C2_"):
        heldout = spec.primary_cell.split("_", 1)[1]
        geometry = f"""
            SELECT least(t.endpoint, h.endpoint) AS endpoint_a,
                   greatest(t.endpoint, h.endpoint) AS endpoint_b
            FROM cell_endpoints t
            CROSS JOIN cell_endpoints h
            WHERE t.exposed AND t.partition = 'train'
              AND h.partition = {_sql_string(heldout)}
        """
    elif spec.primary_cell.startswith("C3_"):
        heldout = spec.primary_cell.split("_", 1)[1]
        geometry = f"""
            SELECT a.endpoint AS endpoint_a, b.endpoint AS endpoint_b
            FROM cell_endpoints a
            JOIN cell_endpoints b ON a.endpoint < b.endpoint
            WHERE a.partition = {_sql_string(heldout)}
              AND b.partition = {_sql_string(heldout)}
        """
    else:
        raise RuntimeError(f"Unsupported cell geometry: {spec.primary_cell}")

    return f"""
        WITH geometry AS ({geometry}),
        unlabeled_geometry AS (
            SELECT g.endpoint_a, g.endpoint_b
            FROM geometry g
            LEFT JOIN positive_union p
              ON p.endpoint_a = g.endpoint_a AND p.endpoint_b = g.endpoint_b
            WHERE p.endpoint_a IS NULL
        )
        SELECT
            u.endpoint_a,
            u.endpoint_b,
            a.component_id AS endpoint_a_component_id,
            b.component_id AS endpoint_b_component_id,
            a.partition AS endpoint_a_partition,
            b.partition AS endpoint_b_partition,
            CAST(a.training_degree AS BIGINT) AS endpoint_a_training_degree,
            CAST(b.training_degree AS BIGINT) AS endpoint_b_training_degree,
            CASE
              WHEN a.degree_bin_order <= b.degree_bin_order
              THEN a.degree_bin || '|' || b.degree_bin
              ELSE b.degree_bin || '|' || a.degree_bin
            END AS stratum_id,
            'pair:' || sha256(u.endpoint_a || '|' || u.endpoint_b) AS pair_id
        FROM unlabeled_geometry u
        JOIN cell_endpoints a ON a.endpoint = u.endpoint_a
        JOIN cell_endpoints b ON b.endpoint = u.endpoint_b
    """


def _allocation_rows(
    *,
    connection: duckdb.DuckDBPyConnection,
    spec: CellSpec,
    config: Mapping[str, Any],
    smoke_cap: int | None,
) -> tuple[list[dict[str, Any]], int]:
    populations = {
        str(stratum): int(count)
        for stratum, count in connection.execute(
            f"SELECT stratum_id, count(*) FROM ({_candidate_base_sql(spec)}) "
            "GROUP BY stratum_id ORDER BY stratum_id"
        ).fetchall()
    }
    cap = int(config["sampling"]["sample_caps"][spec.primary_cell])
    realized_cap = min(cap, int(smoke_cap)) if smoke_cap is not None else cap
    allocations = hamilton_sample_allocation(populations, realized_cap)
    rows = []
    for stratum in sorted(allocations):
        population = populations[stratum]
        sample = allocations[stratum]
        p_num, p_den, w_num, w_den = rational_design(population, sample)
        rows.append(
            {
                "package_id": PACKAGE_ID,
                "axis": spec.axis,
                "target_source": spec.target_source,
                "cell_id": spec.cell_id,
                "primary_cell": spec.primary_cell,
                "stratum_id": stratum,
                "unlabeled_population": population,
                "sample_size": sample,
                "inclusion_probability_numerator": p_num,
                "inclusion_probability_denominator": p_den,
                "sampling_weight_numerator": w_num,
                "sampling_weight_denominator": w_den,
            }
        )
    return rows, sum(populations.values())


def _copy_query_part(
    *,
    connection: duckdb.DuckDBPyConnection,
    query: str,
    root: Path,
    table_name: str,
    part_index: int,
    config: Mapping[str, Any],
    contract: Any,
) -> Path:
    directory = root / table_name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"part-{part_index:05d}.parquet"
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    escaped = path.as_posix().replace("'", "''")
    compression = str(config["runtime"]["parquet_compression"]).upper()
    row_group = int(config["runtime"]["parquet_row_group_rows"])
    connection.execute(
        f"COPY ({query}) TO '{escaped}' "
        f"(FORMAT PARQUET, COMPRESSION {compression}, ROW_GROUP_SIZE {row_group})"
    )
    verify_arrow_schema(path=path, contract=contract, table_name=table_name)
    return path


def _register_allocations(
    connection: duckdb.DuckDBPyConnection, rows: Sequence[Mapping[str, Any]]
) -> None:
    minimal = [
        {
            "stratum_id": row["stratum_id"],
            "unlabeled_population": int(row["unlabeled_population"]),
            "sample_size": int(row["sample_size"]),
            "inclusion_probability_numerator": int(
                row["inclusion_probability_numerator"]
            ),
            "inclusion_probability_denominator": int(
                row["inclusion_probability_denominator"]
            ),
            "sampling_weight_numerator": int(row["sampling_weight_numerator"]),
            "sampling_weight_denominator": int(row["sampling_weight_denominator"]),
        }
        for row in rows
    ]
    connection.register("_allocation_arrow", pa.Table.from_pylist(minimal))
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE cell_allocation AS SELECT * FROM _allocation_arrow"
    )
    connection.unregister("_allocation_arrow")


def _sample_query(spec: CellSpec, config: Mapping[str, Any]) -> str:
    salt = str(config["sampling"]["public_salt"])
    seed = str(config["sampling"]["deterministic_seed"])
    target = (
        "CAST(NULL AS VARCHAR)"
        if spec.target_source is None
        else _sql_string(spec.target_source)
    )
    return f"""
        WITH candidates AS ({_candidate_base_sql(spec)}),
        hashed AS (
            SELECT c.*,
                   sha256(
                     {_sql_string(salt)} || ':' || {_sql_string(seed)}
                     || ':unlabeled:' || {_sql_string(spec.cell_id)}
                     || ':' || c.stratum_id || ':' || c.pair_id
                   ) AS sampling_hash_key
            FROM candidates c
        ),
        ranked AS (
            SELECT h.*,
                   row_number() OVER (
                     PARTITION BY h.stratum_id
                     ORDER BY h.sampling_hash_key, h.pair_id
                   ) AS sample_rank
            FROM hashed h
        )
        SELECT
            {_sql_string(PACKAGE_ID)} AS package_id,
            {_sql_string(spec.axis)} AS axis,
            {target} AS target_source,
            {_sql_string(spec.cell_id)} AS cell_id,
            {_sql_string(spec.primary_cell)} AS primary_cell,
            r.pair_id,
            r.endpoint_a AS endpoint_a_sha256,
            r.endpoint_b AS endpoint_b_sha256,
            r.endpoint_a_component_id,
            r.endpoint_b_component_id,
            r.endpoint_a_partition,
            r.endpoint_b_partition,
            r.endpoint_a_training_degree,
            r.endpoint_b_training_degree,
            r.stratum_id,
            r.sampling_hash_key,
            CAST(a.unlabeled_population AS BIGINT) AS unlabeled_population,
            CAST(a.sample_size AS BIGINT) AS sample_size,
            CAST(a.inclusion_probability_numerator AS BIGINT)
              AS inclusion_probability_numerator,
            CAST(a.inclusion_probability_denominator AS BIGINT)
              AS inclusion_probability_denominator,
            CAST(a.sampling_weight_numerator AS BIGINT)
              AS sampling_weight_numerator,
            CAST(a.sampling_weight_denominator AS BIGINT)
              AS sampling_weight_denominator,
            'unlabeled' AS state
        FROM ranked r
        JOIN cell_allocation a USING (stratum_id)
        WHERE r.sample_rank <= a.sample_size
        ORDER BY r.stratum_id, r.sampling_hash_key, r.pair_id
    """


def _positive_rows(
    *,
    spec: CellSpec,
    state: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for pair in sorted(spec.positive_pairs):
        rows.append(
            {
                "package_id": PACKAGE_ID,
                "axis": spec.axis,
                "target_source": spec.target_source,
                "cell_id": spec.cell_id,
                "primary_cell": spec.primary_cell,
                "pair_id": pair_id(pair),
                "endpoint_a_sha256": pair[0],
                "endpoint_b_sha256": pair[1],
                "endpoint_a_component_id": state["component"][pair[0]],
                "endpoint_b_component_id": state["component"][pair[1]],
                "endpoint_a_partition": state["partition"][pair[0]],
                "endpoint_b_partition": state["partition"][pair[1]],
                "endpoint_a_training_degree": int(spec.degree.get(pair[0], 0)),
                "endpoint_b_training_degree": int(spec.degree.get(pair[1], 0)),
                "stratum_id": degree_pair_stratum(
                    int(spec.degree.get(pair[0], 0)),
                    int(spec.degree.get(pair[1], 0)),
                ),
                "state": "released_positive",
                "inclusion_probability_numerator": 1,
                "inclusion_probability_denominator": 1,
                "sampling_weight_numerator": 1,
                "sampling_weight_denominator": 1,
            }
        )
    return rows


def _candidate_token(cell_id: str, pair_identifier: str) -> str:
    import hashlib

    payload = f"{PACKAGE_ID}:{cell_id}:{pair_identifier}"
    return "candidate:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _protected_candidate_query(
    *,
    spec: CellSpec,
    sample_path: Path,
    positive_rows: Sequence[Mapping[str, Any]],
    connection: duckdb.DuckDBPyConnection,
) -> str:
    connection.register(
        "_positive_candidates_arrow", pa.Table.from_pylist(positive_rows)
    )
    sample = sample_path.as_posix().replace("'", "''")
    token_prefix = _sql_string(PACKAGE_ID + ":" + spec.cell_id + ":")
    target = (
        "CAST(NULL AS VARCHAR)"
        if spec.target_source is None
        else _sql_string(spec.target_source)
    )
    return f"""
        WITH combined AS (
            SELECT
              pair_id, endpoint_a_sha256, endpoint_b_sha256,
              endpoint_a_component_id, endpoint_b_component_id,
              endpoint_a_partition, endpoint_b_partition,
              endpoint_a_training_degree, endpoint_b_training_degree, stratum_id
            FROM read_parquet('{sample}')
            UNION ALL
            SELECT
              pair_id, endpoint_a_sha256, endpoint_b_sha256,
              endpoint_a_component_id, endpoint_b_component_id,
              endpoint_a_partition, endpoint_b_partition,
              endpoint_a_training_degree, endpoint_b_training_degree, stratum_id
            FROM _positive_candidates_arrow
        )
        SELECT
          {_sql_string(PACKAGE_ID)} AS package_id,
          {_sql_string(spec.axis)} AS axis,
          {target} AS target_source,
          {_sql_string(spec.cell_id)} AS cell_id,
          {_sql_string(spec.primary_cell)} AS primary_cell,
          'candidate:' || sha256({token_prefix} || pair_id) AS candidate_token,
          endpoint_a_sha256,
          endpoint_b_sha256,
          endpoint_a_component_id,
          endpoint_b_component_id,
          endpoint_a_partition,
          endpoint_b_partition,
          CAST(endpoint_a_training_degree AS BIGINT) AS endpoint_a_training_degree,
          CAST(endpoint_b_training_degree AS BIGINT) AS endpoint_b_training_degree,
          stratum_id
        FROM combined
        ORDER BY candidate_token
    """


def _protected_truth_rows(
    *, spec: CellSpec, state: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    for pair in sorted(spec.positive_pairs):
        sources = state["pair_sources"][pair]
        identifier = pair_id(pair)
        rows.append(
            {
                "package_id": PACKAGE_ID,
                "axis": spec.axis,
                "target_source": spec.target_source,
                "cell_id": spec.cell_id,
                "primary_cell": spec.primary_cell,
                "candidate_token": _candidate_token(spec.cell_id, identifier),
                "pair_id": identifier,
                "source_membership": _source_membership(sources),
                "hi_ii_14_supported": "HI-II-14" in sources,
                "huri_supported": "HuRI" in sources,
                "state": "released_positive",
            }
        )
    return rows


def _source_visible_rows(
    *, target: str, state: Mapping[str, Any]
) -> list[dict[str, Any]]:
    other = "HuRI" if target == "HI-II-14" else "HI-II-14"
    degree = state["source_degree"][target]
    return [
        {
            "package_id": PACKAGE_ID,
            "target_source": target,
            "visible_source": other,
            "pair_id": pair_id(pair),
            "endpoint_a_sha256": pair[0],
            "endpoint_b_sha256": pair[1],
            "endpoint_a_component_id": state["component"][pair[0]],
            "endpoint_b_component_id": state["component"][pair[1]],
            "endpoint_a_training_degree": int(degree[pair[0]]),
            "endpoint_b_training_degree": int(degree[pair[1]]),
            "state": "released_positive",
        }
        for pair in sorted(state["source_visible"][target])
    ]


def _source_role(
    *, pair: tuple[str, str], target: str, state: Mapping[str, Any]
) -> str:
    if pair in state["source_visible"][target]:
        return "visible_training"
    sources = state["pair_sources"][pair]
    if sources != frozenset({target}):
        return "visible_non_target_or_not_target_only"
    for cell in PRIMARY_CELLS:
        if pair in state["source_sets"][target][cell]:
            return cell
    return "quarantine"


def _role_ledger_rows(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for pair in sorted(state["positive_pairs"]):
        role, reason = _primary_state(
            pair=pair,
            partition=state["partition"],
            exposed=set(state["primary_exposed"]),
            hash_role=state["roles"].get(pair),
            training_pairs=set(state["training_pairs"]),
            primary_sets=state["primary_sets"],
        )
        sources = state["pair_sources"][pair]
        rows.append(
            {
                "package_id": PACKAGE_ID,
                "pair_id": pair_id(pair),
                "endpoint_a_sha256": pair[0],
                "endpoint_b_sha256": pair[1],
                "source_membership": _source_membership(sources),
                "hi_ii_14_supported": "HI-II-14" in sources,
                "huri_supported": "HuRI" in sources,
                "c1_hash_role": state["roles"].get(pair),
                "primary_positive_role": role,
                "primary_quarantine_reason": reason,
                "source_exclusive_hi_ii_14_role": _source_role(
                    pair=pair, target="HI-II-14", state=state
                ),
                "source_exclusive_huri_role": _source_role(
                    pair=pair, target="HuRI", state=state
                ),
            }
        )
    return rows


def _package_manifest(
    *,
    package_role: str,
    root: Path,
    table_names: Sequence[str],
    contract: Any,
    cell_counts: Mapping[str, Mapping[str, int]],
    smoke: bool,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "package_role": package_role,
        "status": "qualified_smoke" if smoke else "complete_frozen",
        "pair_state_vocabulary": ["released_positive", "unlabeled"],
        "negative_or_pseudo_negative_state_present": False,
        "tables": {
            name: dataset_summary(root=root, table_name=name, contract=contract)
            for name in table_names
        },
        "cells": dict(sorted(cell_counts.items())),
        "source_assay_publication_fields_in_model_development_tables": False,
        "full_candidate_pair_universe_materialized": False,
        "model_work_performed": False,
    }


def _seal_package(
    *,
    source_root: Path,
    manifest_name: str,
    manifest: Mapping[str, Any],
    archive_path: Path,
    certificate: Path,
    ciphertext: Path,
) -> dict[str, Any]:
    write_manifest(source_root / manifest_name, manifest)
    archive_sha = deterministic_tar(source_root, archive_path)
    ciphertext_sha = cms_encrypt(
        archive=archive_path, certificate=certificate, output=ciphertext
    )
    return {
        "ciphertext_path": ciphertext.name,
        "ciphertext_bytes": ciphertext.stat().st_size,
        "ciphertext_sha256": ciphertext_sha,
        "plaintext_archive_sha256": archive_sha,
        "plaintext_archive_bytes": archive_path.stat().st_size,
        "manifest_name": manifest_name,
    }


def _overlap_summary(
    *,
    connection: duckdb.DuckDBPyConnection,
    sample_files: Sequence[tuple[str, str, Path]],
) -> dict[str, Any]:
    clauses = []
    for boundary, cell_id, path in sample_files:
        escaped = path.as_posix().replace("'", "''")
        clauses.append(
            "SELECT "
            + _sql_string(boundary)
            + " AS boundary, "
            + _sql_string(cell_id)
            + f" AS cell_id, pair_id FROM read_parquet('{escaped}')"
        )
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE all_realized_samples AS "
        + " UNION ALL ".join(clauses)
    )
    distinct_rows, reused_pairs, repeated_rows, max_cells = connection.execute(
        """
        WITH grouped AS (
          SELECT pair_id, count(*) AS rows, count(DISTINCT cell_id) AS cells
          FROM all_realized_samples GROUP BY pair_id
        )
        SELECT count(*), count_if(cells > 1),
               coalesce(sum(rows - 1) FILTER (WHERE cells > 1), 0),
               coalesce(max(cells), 1)
        FROM grouped
        """
    ).fetchone()
    boundary_pairs = {}
    for left, right in (
        ("training", "development"),
        ("training", "protected_test"),
        ("development", "protected_test"),
    ):
        count = connection.execute(
            """
            SELECT count(DISTINCT a.pair_id)
            FROM all_realized_samples a
            JOIN all_realized_samples b USING (pair_id)
            WHERE a.boundary = ? AND b.boundary = ?
            """,
            [left, right],
        ).fetchone()[0]
        boundary_pairs[f"{left}__{right}"] = int(count)
    return {
        "distinct_unlabeled_pair_ids": int(distinct_rows),
        "pair_ids_reused_across_cells": int(reused_pairs),
        "repeated_sample_rows_beyond_first": int(repeated_rows),
        "maximum_cells_for_one_unlabeled_pair": int(max_cells),
        "cross_visibility_boundary_pair_ids": boundary_pairs,
        "interpretation": "permitted_cross_cell_unlabeled_reuse_not_positive_evidence_leakage",
    }


def _construct_into(
    *,
    connection: duckdb.DuckDBPyConnection,
    canonical_root: Path,
    work_root: Path,
    state: Mapping[str, Any],
    config: Mapping[str, Any],
    paths: Mapping[str, Path],
    contract: Any,
    smoke: bool,
    smoke_cap: int | None,
) -> dict[str, Any]:
    training_spec, development_specs, test_specs = _cell_specs(state)
    _register_static_tables(
        connection,
        partition=state["partition"],
        component=state["component"],
        positive_pairs=state["positive_pairs"],
    )
    training_root = canonical_root / "training"
    development_root = work_root / "development"
    candidates_root = work_root / "protected_candidates"
    truth_root = work_root / "protected_truth"
    for root in (training_root, development_root, candidates_root, truth_root):
        root.mkdir(parents=True, exist_ok=False)

    training_positive_rows = _positive_rows(spec=training_spec, state=state)
    write_rows_part(
        root=training_root,
        table_name="positive_pairs",
        part_index=0,
        rows=training_positive_rows,
        contract=contract,
        compression=str(config["runtime"]["parquet_compression"]),
    )

    all_strata: dict[str, list[dict[str, Any]]] = {
        "training": [],
        "development": [],
        "protected_truth": [],
    }
    cell_counts: dict[str, dict[str, int]] = {}
    sample_files: list[tuple[str, str, Path]] = []

    def realize_sample(
        spec: CellSpec, *, root: Path, part_index: int, boundary: str
    ) -> tuple[Path, list[dict[str, Any]], int]:
        _register_cell_endpoints(
            connection,
            partition=state["partition"],
            component=state["component"],
            spec=spec,
        )
        allocation_rows, population = _allocation_rows(
            connection=connection,
            spec=spec,
            config=config,
            smoke_cap=smoke_cap,
        )
        _register_allocations(connection, allocation_rows)
        path = _copy_query_part(
            connection=connection,
            query=_sample_query(spec, config),
            root=root,
            table_name="unlabeled_pairs",
            part_index=part_index,
            config=config,
            contract=contract,
        )
        rows = int(pq.ParquetFile(path).metadata.num_rows)
        if rows != sum(int(row["sample_size"]) for row in allocation_rows):
            raise RuntimeError(
                f"Sample row count differs from allocation: {spec.cell_id}"
            )
        sample_files.append((boundary, spec.cell_id, path))
        cell_counts[spec.cell_id] = {
            "positive_pairs": len(spec.positive_pairs),
            "unlabeled_population": population,
            "unlabeled_sample": rows,
            "nonempty_strata": len(allocation_rows),
        }
        return path, allocation_rows, population

    training_sample, rows, _ = realize_sample(
        training_spec, root=training_root, part_index=0, boundary="training"
    )
    all_strata["training"].extend(rows)
    write_rows_part(
        root=training_root,
        table_name="sampling_strata",
        part_index=0,
        rows=all_strata["training"],
        contract=contract,
        compression=str(config["runtime"]["parquet_compression"]),
    )

    development_positive_rows = [
        row
        for spec in development_specs
        for row in _positive_rows(spec=spec, state=state)
    ]
    write_rows_part(
        root=development_root,
        table_name="positive_pairs",
        part_index=0,
        rows=development_positive_rows,
        contract=contract,
        compression=str(config["runtime"]["parquet_compression"]),
    )
    for index, target in enumerate(SOURCES):
        write_rows_part(
            root=development_root,
            table_name="source_visible_training_positive_pairs",
            part_index=index,
            rows=_source_visible_rows(target=target, state=state),
            contract=contract,
            compression=str(config["runtime"]["parquet_compression"]),
        )
    for index, spec in enumerate(development_specs):
        _, rows, _ = realize_sample(
            spec, root=development_root, part_index=index, boundary="development"
        )
        all_strata["development"].extend(rows)
    write_rows_part(
        root=development_root,
        table_name="sampling_strata",
        part_index=0,
        rows=all_strata["development"],
        contract=contract,
        compression=str(config["runtime"]["parquet_compression"]),
    )

    protected_truth_rows: list[dict[str, Any]] = []
    for index, spec in enumerate(test_specs):
        sample_path, rows, _ = realize_sample(
            spec, root=truth_root, part_index=index, boundary="protected_test"
        )
        all_strata["protected_truth"].extend(rows)
        positive_rows = _positive_rows(spec=spec, state=state)
        protected_truth_rows.extend(_protected_truth_rows(spec=spec, state=state))
        candidate_query = _protected_candidate_query(
            spec=spec,
            sample_path=sample_path,
            positive_rows=positive_rows,
            connection=connection,
        )
        _copy_query_part(
            connection=connection,
            query=candidate_query,
            root=candidates_root,
            table_name="protected_candidates",
            part_index=index,
            config=config,
            contract=contract,
        )
        connection.unregister("_positive_candidates_arrow")
    write_rows_part(
        root=truth_root,
        table_name="protected_positive_truth",
        part_index=0,
        rows=protected_truth_rows,
        contract=contract,
        compression=str(config["runtime"]["parquet_compression"]),
    )
    write_rows_part(
        root=truth_root,
        table_name="sampling_strata",
        part_index=0,
        rows=all_strata["protected_truth"],
        contract=contract,
        compression=str(config["runtime"]["parquet_compression"]),
    )
    write_rows_part(
        root=truth_root,
        table_name="positive_role_ledger",
        part_index=0,
        rows=_role_ledger_rows(state),
        contract=contract,
        compression=str(config["runtime"]["parquet_compression"]),
    )

    overlap = _overlap_summary(connection=connection, sample_files=sample_files)
    positive_union_ids = {pair_id(pair) for pair in state["positive_pairs"]}
    training_sample_ids = {
        str(row[0])
        for row in connection.execute(
            f"SELECT pair_id FROM read_parquet('{training_sample.as_posix()}')"
        ).fetchall()
    }
    leakage_checks = {
        "training_sample_released_positive_overlap": len(
            positive_union_ids & training_sample_ids
        ),
        "primary_positive_role_overlap": 0,
        "development_or_test_endpoint_in_training_positives": sum(
            state["partition"][endpoint] != "train"
            for pair in state["training_pairs"]
            for endpoint in pair
        ),
        "public_protected_test_identity_rows": 0,
    }
    if any(leakage_checks.values()):
        raise RuntimeError(f"Pair-artifact leakage check failed: {leakage_checks}")

    training_manifest = _package_manifest(
        package_role="public_training",
        root=training_root,
        table_names=("positive_pairs", "unlabeled_pairs", "sampling_strata"),
        contract=contract,
        cell_counts={"training": cell_counts["training"]},
        smoke=smoke,
    )
    training_manifest_sha = write_manifest(
        training_root / "TRAINING_PACKAGE_MANIFEST.json", training_manifest
    )

    development_cells = {
        spec.cell_id: cell_counts[spec.cell_id] for spec in development_specs
    }
    test_cells = {spec.cell_id: cell_counts[spec.cell_id] for spec in test_specs}
    development_manifest = _package_manifest(
        package_role="encrypted_development_release",
        root=development_root,
        table_names=(
            "positive_pairs",
            "unlabeled_pairs",
            "sampling_strata",
            "source_visible_training_positive_pairs",
        ),
        contract=contract,
        cell_counts=development_cells,
        smoke=smoke,
    )
    candidate_manifest = _package_manifest(
        package_role="encrypted_protected_test_candidates",
        root=candidates_root,
        table_names=("protected_candidates",),
        contract=contract,
        cell_counts=test_cells,
        smoke=smoke,
    )
    truth_manifest = _package_manifest(
        package_role="encrypted_protected_test_truth",
        root=truth_root,
        table_names=(
            "unlabeled_pairs",
            "protected_positive_truth",
            "sampling_strata",
            "positive_role_ledger",
        ),
        contract=contract,
        cell_counts=test_cells,
        smoke=smoke,
    )

    sealed_root = canonical_root / "sealed"
    sealed_root.mkdir(parents=True, exist_ok=False)
    development_archive = work_root / "development.tar"
    candidate_archive = work_root / "protected_candidates.tar"
    truth_archive = work_root / "protected_truth.tar"
    seals = {
        "development": _seal_package(
            source_root=development_root,
            manifest_name="DEVELOPMENT_PACKAGE_MANIFEST.json",
            manifest=development_manifest,
            archive_path=development_archive,
            certificate=paths["development_release_certificate"],
            ciphertext=sealed_root / "development_release.cms",
        ),
        "protected_candidates": _seal_package(
            source_root=candidates_root,
            manifest_name="PROTECTED_CANDIDATE_PACKAGE_MANIFEST.json",
            manifest=candidate_manifest,
            archive_path=candidate_archive,
            certificate=paths["protected_candidates_certificate"],
            ciphertext=sealed_root / "protected_candidates.cms",
        ),
        "protected_truth": _seal_package(
            source_root=truth_root,
            manifest_name="PROTECTED_TRUTH_PACKAGE_MANIFEST.json",
            manifest=truth_manifest,
            archive_path=truth_archive,
            certificate=paths["protected_truth_certificate"],
            ciphertext=sealed_root / "protected_truth.cms",
        ),
    }

    return {
        "training_manifest": training_manifest,
        "training_manifest_sha256": training_manifest_sha,
        "sealed_packages": seals,
        "cell_counts": dict(sorted(cell_counts.items())),
        "cross_cell_unlabeled_overlap": overlap,
        "leakage_checks": leakage_checks,
        "role_counts": dict(
            sorted(
                Counter(
                    row["primary_positive_role"] for row in _role_ledger_rows(state)
                ).items()
            )
        ),
        "scope": {
            "full_candidate_pair_universe_materialized": False,
            "negative_or_pseudo_negative_constructed": False,
            "frozen_split_modified": False,
            "external_panel_input_used": False,
            "structural_mapping_performed": False,
            "model_work_performed": False,
            "development_released": False,
            "protected_identity_publicly_exposed": False,
        },
    }


def construct_artifacts(
    *,
    project_root: Path,
    config_path: Path,
    run_root: Path | None = None,
    canonical_root: Path | None = None,
    report_path: Path | None = None,
    allow_dirty: bool = False,
    skip_input_hashes: bool = False,
    smoke_cap: int | None = None,
) -> dict[str, Any]:
    require_apptainer()
    started = _timestamp()
    config_path = resolve_inside(
        project_root, config_path, project_root / "configs", strict=True
    )
    config = load_yaml(config_path)
    validate_config(config)
    output = config["outputs"]
    run_target = resolve_inside(
        project_root,
        run_root or str(output["run_root"]),
        project_root / "artifacts/runs",
        strict=False,
    )
    canonical_target = resolve_inside(
        project_root,
        canonical_root or str(output["canonical_root"]),
        project_root / "data/canonical",
        strict=False,
    )
    report_target = resolve_inside(
        project_root,
        report_path or str(output["construction_report"]),
        project_root / "artifacts/validation",
        strict=False,
    )
    smoke = all(
        any(part.startswith("_smoke_") for part in path.parts)
        for path in (run_target, canonical_target, report_target)
    )
    if allow_dirty != smoke:
        raise RuntimeError(
            "--allow-dirty is restricted to consistently named smoke outputs"
        )
    if skip_input_hashes and not smoke:
        raise RuntimeError("--skip-input-hashes is restricted to smoke outputs")
    if smoke_cap is not None and (not smoke or int(smoke_cap) < 50):
        raise RuntimeError("--smoke-cap requires smoke outputs and at least 50 rows")
    if smoke and smoke_cap is None:
        raise RuntimeError("Smoke construction requires --smoke-cap")
    if not smoke and smoke_cap is not None:
        raise RuntimeError("Production construction cannot cap frozen samples")

    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError(
            "Production pair-artifact construction requires a clean worktree"
        )
    active_container = Path(os.environ["APPTAINER_CONTAINER"]).resolve(strict=True)
    expected_container = resolve_inside(
        project_root,
        str(config["runtime"]["container"]),
        project_root / "containers/images",
        strict=True,
    )
    if active_container != expected_container:
        raise RuntimeError("Active container differs from the frozen configuration")
    if sha256_file(active_container) != str(config["runtime"]["container_sha256"]):
        raise RuntimeError(
            "Active container hash differs from the frozen configuration"
        )
    if platform.machine() != str(config["runtime"]["architecture"]):
        raise RuntimeError("Pair artifacts are running on the wrong architecture")

    paths, verified_documents = verify_documents(
        project_root=project_root,
        config=config,
        verify_hashes=not skip_input_hashes,
    )
    keys = private_key_paths(project_root, config)
    fingerprints = verify_key_pairs(paths=paths, keys=keys)
    protocol = load_protocol_yaml(paths["frozen_protocol_config"])
    validate_protocol_config(protocol)
    protocol_inputs, table_files, _ = verify_protocol_inputs(
        project_root=project_root,
        config=protocol,
        verify_hashes=not skip_input_hashes,
    )

    connection = duckdb.connect(":memory:")
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    connection.execute(
        f"SET memory_limit={_sql_string(str(config['runtime']['duckdb_memory_limit']))}"
    )
    connection.execute("PRAGMA disable_progress_bar")
    try:
        _register_views(connection, table_files)
        partition, component, _ = _load_endpoints(connection, protocol)
        positive_pairs, pair_sources = _load_positive_pairs(connection, protocol)
        state = _prepare_state(
            partition=partition,
            component=component,
            positive_pairs=positive_pairs,
            pair_sources=pair_sources,
            protocol=protocol,
            config=config,
        )
        contract = load_contract(paths["artifact_schema"])
        temp_parent = project_root / "artifacts/tmp"
        temp_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="pair_artifacts_seal_", dir=temp_parent
        ) as work_name:
            work_root = Path(work_name)
            with AtomicDatasetDirectory(canonical_target) as temporary_canonical:
                result = _construct_into(
                    connection=connection,
                    canonical_root=temporary_canonical,
                    work_root=work_root,
                    state=state,
                    config=config,
                    paths=paths,
                    contract=contract,
                    smoke=smoke,
                    smoke_cap=smoke_cap,
                )
                package_manifest = {
                    "schema_version": 1,
                    "package_id": PACKAGE_ID,
                    "package_version": ARTIFACT_PACKAGE_VERSION,
                    "status": "qualified_smoke" if smoke else "complete_frozen",
                    "scope": "qualification_smoke" if smoke else "production_full",
                    "completed_at_utc": _timestamp(),
                    "git": git,
                    "runtime": {
                        "container": expected_container.as_posix(),
                        "container_sha256": str(config["runtime"]["container_sha256"]),
                        "architecture": platform.machine(),
                        "duckdb": duckdb.__version__,
                        "openssl": "CMS DER AES-256-CBC",
                    },
                    "inputs": {
                        "config": config_path.relative_to(project_root).as_posix(),
                        "config_sha256": sha256_file(config_path),
                        "documents": verified_documents,
                        "protocol_inputs": protocol_inputs,
                        "public_certificate_fingerprints_sha256": fingerprints,
                    },
                    "artifacts": result,
                    "frozen_protocol_preserved": True,
                    "primary_design": "reference_sequence_positive_unlabeled_ranking",
                    "pair_state_vocabulary": ["released_positive", "unlabeled"],
                    "negative_or_pseudo_negative_state_present": False,
                    "protected_test_candidate_or_truth_identity_public": False,
                    "return_to_governance_required": True,
                }
                package_manifest_sha = write_manifest(
                    temporary_canonical / "PACKAGE_MANIFEST.json", package_manifest
                )
                make_read_only(temporary_canonical)
    finally:
        connection.close()

    with AtomicDatasetDirectory(run_target) as temporary_run:
        run_manifest = {
            "schema_version": 1,
            "package_id": PACKAGE_ID,
            "status": "qualified_smoke" if smoke else "complete",
            "started_at_utc": started,
            "completed_at_utc": _timestamp(),
            "git": git,
            "config": {
                "path": config_path.relative_to(project_root).as_posix(),
                "sha256": sha256_file(config_path),
            },
            "canonical_manifest": (
                canonical_target / "PACKAGE_MANIFEST.json"
            ).as_posix(),
            "canonical_manifest_sha256": package_manifest_sha,
            "scope": result["scope"],
        }
        write_manifest(temporary_run / "RUN_MANIFEST.json", run_manifest)
        make_read_only(temporary_run)

    report = {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "package_version": ARTIFACT_PACKAGE_VERSION,
        "task": str(config["task"]),
        "status": "qualified_smoke" if smoke else "complete_frozen",
        "scope": "qualification_smoke" if smoke else "production_full",
        "started_at_utc": started,
        "completed_at_utc": _timestamp(),
        "git": git,
        "inputs": {
            "config": config_path.relative_to(project_root).as_posix(),
            "config_sha256": sha256_file(config_path),
            "verified_documents": verified_documents,
            "public_certificate_fingerprints_sha256": fingerprints,
        },
        "outputs": {
            "canonical_manifest": (
                canonical_target / "PACKAGE_MANIFEST.json"
            ).as_posix(),
            "canonical_manifest_sha256": package_manifest_sha,
            "run_manifest": (run_target / "RUN_MANIFEST.json").as_posix(),
            "large_pair_artifacts_tracked_by_git": False,
        },
        "construction": result,
        "scientific_interpretation": {
            "unlabeled_rows_are_negatives": False,
            "primary_pu_r_design_preserved": True,
            "c3_claim": config["pair_semantics"]["c3_claim"],
            "unseen_family_or_plm_unseen_claim_supported": False,
            "prevalence_or_calibration_supported": False,
            "cross_cell_unlabeled_reuse_is_positive_leakage": False,
            "exact_full_universe_metrics_available_from_sample_only": False,
        },
    }
    _write_report(report_target, report, project_root)
    return report


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/pair_level_pu_r_benchmark_artifacts_v1.yaml"),
    )
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--construction-report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--skip-input-hashes", action="store_true")
    parser.add_argument("--smoke-cap", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path(__file__))
    report = construct_artifacts(
        project_root=project_root,
        config_path=args.config,
        run_root=args.run_root,
        canonical_root=args.canonical_root,
        report_path=args.construction_report,
        allow_dirty=args.allow_dirty,
        skip_input_hashes=args.skip_input_hashes,
        smoke_cap=args.smoke_cap,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in {"qualified_smoke", "complete_frozen"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
