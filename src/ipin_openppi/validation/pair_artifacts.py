"""Independent validation of sealed pair-level PU-R benchmark artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import (
    git_provenance,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.pair_artifacts.support import (
    PACKAGE_ID,
    PRIMARY_CELLS,
    SOURCES,
    cms_decrypt,
    deterministic_tar,
    extract_verified_tar,
    load_json,
    load_yaml,
    private_key_paths,
    resolve_inside,
    validate_config,
    verify_arrow_schema,
    verify_documents,
    verify_key_pairs,
)
from ipin_openppi.validation.pair_protocol import (
    _independent_bin,
    _independent_pair_id,
    _independent_state,
    _load_verified_inputs,
    _register,
)
from ipin_openppi.validation.staging import _write_report


@dataclass
class Checks:
    records: list[dict[str, Any]] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: Mapping[str, Any]) -> None:
        self.records.append(
            {
                "check": name,
                "status": "pass" if passed else "fail",
                "detail": dict(detail),
            }
        )

    @property
    def passed(self) -> bool:
        return all(record["status"] == "pass" for record in self.records)

    def counts(self) -> dict[str, int]:
        return {
            "pass": sum(record["status"] == "pass" for record in self.records),
            "warning": 0,
            "fail": sum(record["status"] == "fail" for record in self.records),
        }


@dataclass(frozen=True)
class IndependentSpec:
    axis: str
    target_source: str | None
    primary_cell: str
    cell_id: str
    positives: frozenset[tuple[str, str]]
    degree: Mapping[str, int]
    exposed: frozenset[str]


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _q(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _verify_sidecar(path: Path) -> str:
    digest = sha256_file(path)
    sidecar = path.with_name(path.name + ".sha256")
    if sidecar.read_text(encoding="utf-8").strip().split() != [digest, path.name]:
        raise RuntimeError(f"Sidecar mismatch: {path}")
    return digest


def _verify_table_summary(
    *,
    package_root: Path,
    summary: Mapping[str, Any],
    contract: Any,
) -> dict[str, Any]:
    table_name = str(summary["table"])
    rows = 0
    files = []
    for index, record in enumerate(summary["files"]):
        relative = Path(str(record["path"]))
        path = (package_root / relative).resolve(strict=True)
        path.relative_to(package_root.resolve(strict=True))
        if (
            path.parent != (package_root / table_name).resolve(strict=True)
            or path.name != f"part-{index:05d}.parquet"
            or path.is_symlink()
        ):
            raise RuntimeError(f"Unsafe or noncontiguous table part: {path}")
        observed_rows = int(pq.ParquetFile(path).metadata.num_rows)
        if (
            observed_rows != int(record["rows"])
            or path.stat().st_size != int(record["bytes"])
            or sha256_file(path) != str(record["sha256"])
        ):
            raise RuntimeError(f"Table part integrity mismatch: {path}")
        verify_arrow_schema(path=path, contract=contract, table_name=table_name)
        rows += observed_rows
        files.append(path)
    if (
        rows != int(summary["rows"])
        or len(files) != int(summary["parts"])
        or str(summary["schema_sha256"]) != contract.sha256
    ):
        raise RuntimeError(f"Table aggregate/schema mismatch: {table_name}")
    return {"rows": rows, "files": files}


def _verify_inner_package(
    *, root: Path, manifest_name: str, contract: Any
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    path = root / manifest_name
    manifest = load_json(path)
    _verify_sidecar(path)
    if (
        manifest.get("package_id") != PACKAGE_ID
        or manifest.get("negative_or_pseudo_negative_state_present") is not False
        or manifest.get("full_candidate_pair_universe_materialized") is not False
        or manifest.get("model_work_performed") is not False
    ):
        raise RuntimeError(f"Unsafe inner package manifest: {manifest_name}")
    tables = {
        name: _verify_table_summary(
            package_root=root, summary=summary, contract=contract
        )
        for name, summary in manifest["tables"].items()
    }
    return manifest, tables


def _decrypt_package(
    *,
    canonical_root: Path,
    top_manifest: Mapping[str, Any],
    role: str,
    certificate: Path,
    private_key: Path,
    output_root: Path,
    manifest_name: str,
    contract: Any,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], str]:
    record = top_manifest["artifacts"]["sealed_packages"][role]
    ciphertext = canonical_root / "sealed" / str(record["ciphertext_path"])
    if sha256_file(ciphertext) != str(record["ciphertext_sha256"]):
        raise RuntimeError(f"Ciphertext hash mismatch: {role}")
    archive = output_root.parent / f"{role}.tar"
    observed_archive_sha = cms_decrypt(
        ciphertext=ciphertext,
        certificate=certificate,
        private_key=private_key,
        output=archive,
    )
    if observed_archive_sha != str(record["plaintext_archive_sha256"]):
        raise RuntimeError(f"Plaintext archive hash mismatch: {role}")
    extract_verified_tar(archive, output_root)
    rebuilt = output_root.parent / f"{role}.rebuilt.tar"
    rebuilt_sha = deterministic_tar(output_root, rebuilt)
    if rebuilt_sha != observed_archive_sha:
        raise RuntimeError(f"Deterministic archive reconstruction mismatch: {role}")
    manifest, tables = _verify_inner_package(
        root=output_root, manifest_name=manifest_name, contract=contract
    )
    return manifest, tables, observed_archive_sha


def _source_state(state: Mapping[str, Any]) -> dict[str, Any]:
    partition = state["partition"]
    roles = state["roles"]
    pair_sources = state["pair_sources"]

    def cell_for(pair: tuple[str, str], exposure: set[str]) -> str | None:
        left, right = partition[pair[0]], partition[pair[1]]
        role = roles.get(pair)
        if left == right == "train":
            if (
                role in {"development", "test"}
                and pair[0] in exposure
                and pair[1] in exposure
            ):
                return "C1_" + str(role)
            return None
        for heldout in ("development", "test"):
            if {left, right} == {"train", heldout}:
                train_endpoint = pair[0] if left == "train" else pair[1]
                return "C2_" + heldout if train_endpoint in exposure else None
            if left == right == heldout:
                return "C3_" + heldout
        return None

    output: dict[str, Any] = {}
    for target, other in (("HI-II-14", "HuRI"), ("HuRI", "HI-II-14")):
        visible = {
            pair
            for pair in state["positive_pairs"]
            if partition[pair[0]] == partition[pair[1]] == "train"
            and roles.get(pair) == "train"
            and other in pair_sources[pair]
        }
        degree = Counter(endpoint for pair in visible for endpoint in pair)
        exposed = set(degree)
        target_only = {
            pair
            for pair in state["positive_pairs"]
            if pair_sources[pair] == frozenset({target})
        }
        cells = {
            cell: {pair for pair in target_only if cell_for(pair, exposed) == cell}
            for cell in PRIMARY_CELLS
        }
        output[target] = {
            "visible": visible,
            "degree": degree,
            "exposed": exposed,
            "cells": cells,
        }
    return output


def _specs(
    state: Mapping[str, Any], sources: Mapping[str, Any]
) -> tuple[IndependentSpec, list[IndependentSpec], list[IndependentSpec]]:
    training = IndependentSpec(
        "primary",
        None,
        "training",
        "training",
        frozenset(state["training_positive"]),
        state["degree"],
        frozenset(state["exposed"]),
    )
    development = []
    test = []
    for cell in PRIMARY_CELLS:
        spec = IndependentSpec(
            "primary",
            None,
            cell,
            cell,
            frozenset(state["primary_sets"][cell]),
            state["degree"],
            frozenset(state["exposed"]),
        )
        (development if cell.endswith("_development") else test).append(spec)
    for target in SOURCES:
        for cell in PRIMARY_CELLS:
            spec = IndependentSpec(
                "source_exclusive",
                target,
                cell,
                f"source_exclusive:{target}:{cell}",
                frozenset(sources[target]["cells"][cell]),
                sources[target]["degree"],
                frozenset(sources[target]["exposed"]),
            )
            (development if cell.endswith("_development") else test).append(spec)
    key = lambda spec: (spec.axis, spec.target_source or "", spec.primary_cell)
    return training, sorted(development, key=key), sorted(test, key=key)


def _expected_positive_keys(specs: Sequence[IndependentSpec]) -> set[tuple[str, str]]:
    return {
        (spec.cell_id, _independent_pair_id(pair))
        for spec in specs
        for pair in spec.positives
    }


def _read_keys(glob_path: Path) -> set[tuple[str, str]]:
    connection = duckdb.connect(":memory:")
    try:
        return {
            (str(cell), str(identifier))
            for cell, identifier in connection.execute(
                f"SELECT cell_id, pair_id FROM read_parquet('{glob_path.as_posix()}')"
            ).fetchall()
        }
    finally:
        connection.close()


def _register_independent_tables(
    connection: duckdb.DuckDBPyConnection, state: Mapping[str, Any]
) -> None:
    endpoint_rows = [
        {
            "endpoint": endpoint,
            "component_id": state["component"][endpoint],
            "partition": state["partition"][endpoint],
        }
        for endpoint in sorted(state["partition"])
    ]
    positive_rows = [
        {"endpoint_a": pair[0], "endpoint_b": pair[1]}
        for pair in sorted(state["positive_pairs"])
    ]
    connection.register(
        "_validator_endpoint_arrow", pa.Table.from_pylist(endpoint_rows)
    )
    connection.execute(
        "CREATE TEMP TABLE validator_endpoint_catalog AS "
        "SELECT * FROM _validator_endpoint_arrow"
    )
    connection.unregister("_validator_endpoint_arrow")
    connection.register(
        "_validator_positive_arrow", pa.Table.from_pylist(positive_rows)
    )
    connection.execute(
        "CREATE TEMP TABLE validator_positive_union AS "
        "SELECT * FROM _validator_positive_arrow"
    )
    connection.unregister("_validator_positive_arrow")


def _register_spec_endpoints(
    connection: duckdb.DuckDBPyConnection,
    spec: IndependentSpec,
    state: Mapping[str, Any],
) -> None:
    bins = ("0", "1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+")
    rows = []
    for endpoint in sorted(state["partition"]):
        degree = int(spec.degree.get(endpoint, 0))
        label = _independent_bin(degree)
        rows.append(
            {
                "endpoint": endpoint,
                "component_id": state["component"][endpoint],
                "partition": state["partition"][endpoint],
                "training_degree": degree,
                "degree_bin": label,
                "degree_bin_order": bins.index(label),
                "exposed": endpoint in spec.exposed,
            }
        )
    connection.register("_validator_cell_arrow", pa.Table.from_pylist(rows))
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE validator_cell_endpoints AS "
        "SELECT * FROM _validator_cell_arrow"
    )
    connection.unregister("_validator_cell_arrow")


def _candidate_sql(spec: IndependentSpec) -> str:
    if spec.primary_cell in {"training", "C1_development", "C1_test"}:
        geometry = """
          SELECT a.endpoint endpoint_a, b.endpoint endpoint_b
          FROM validator_cell_endpoints a
          JOIN validator_cell_endpoints b ON a.endpoint < b.endpoint
          WHERE a.exposed AND b.exposed
        """
    elif spec.primary_cell.startswith("C2_"):
        heldout = spec.primary_cell.split("_", 1)[1]
        geometry = f"""
          SELECT least(t.endpoint,h.endpoint) endpoint_a,
                 greatest(t.endpoint,h.endpoint) endpoint_b
          FROM validator_cell_endpoints t
          CROSS JOIN validator_cell_endpoints h
          WHERE t.exposed AND t.partition='train' AND h.partition={_q(heldout)}
        """
    else:
        heldout = spec.primary_cell.split("_", 1)[1]
        geometry = f"""
          SELECT a.endpoint endpoint_a, b.endpoint endpoint_b
          FROM validator_cell_endpoints a
          JOIN validator_cell_endpoints b ON a.endpoint < b.endpoint
          WHERE a.partition={_q(heldout)} AND b.partition={_q(heldout)}
        """
    return f"""
      WITH geometry AS ({geometry})
      SELECT
        g.endpoint_a,
        g.endpoint_b,
        CASE WHEN a.degree_bin_order <= b.degree_bin_order
          THEN a.degree_bin || '|' || b.degree_bin
          ELSE b.degree_bin || '|' || a.degree_bin END stratum_id,
        'pair:' || sha256(g.endpoint_a || '|' || g.endpoint_b) pair_id
      FROM geometry g
      JOIN validator_cell_endpoints a ON a.endpoint=g.endpoint_a
      JOIN validator_cell_endpoints b ON b.endpoint=g.endpoint_b
      LEFT JOIN validator_positive_union p
        ON p.endpoint_a=g.endpoint_a AND p.endpoint_b=g.endpoint_b
      WHERE p.endpoint_a IS NULL
    """


def _validate_one_sample(
    *,
    connection: duckdb.DuckDBPyConnection,
    spec: IndependentSpec,
    state: Mapping[str, Any],
    sample_glob: Path,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    _register_spec_endpoints(connection, spec, state)
    sample_path = sample_glob.as_posix().replace("'", "''")
    salt = str(config["sampling"]["public_salt"])
    seed = str(config["sampling"]["deterministic_seed"])
    sample_checks = connection.execute(
        f"""
        WITH sample AS (
          SELECT * FROM read_parquet('{sample_path}') WHERE cell_id={_q(spec.cell_id)}
        ),
        checked AS (
          SELECT s.*,
            'pair:' || sha256(endpoint_a_sha256 || '|' || endpoint_b_sha256)
              AS expected_pair_id,
            sha256({_q(salt)} || ':' || {_q(seed)} || ':unlabeled:'
              || cell_id || ':' || stratum_id || ':' || pair_id)
              AS expected_hash
          FROM sample s
        )
        SELECT
          count(*),
          count(DISTINCT pair_id),
          count_if(state <> 'unlabeled'),
          count_if(pair_id <> expected_pair_id),
          count_if(sampling_hash_key <> expected_hash)
        FROM checked
        """
    ).fetchone()
    if any(int(value) for value in sample_checks[2:]) or int(sample_checks[0]) != int(
        sample_checks[1]
    ):
        raise RuntimeError(f"Row-level sample formula failed: {spec.cell_id}")

    strata_rows = connection.execute(
        f"""
        SELECT stratum_id, unlabeled_population, sample_size,
          inclusion_probability_numerator, inclusion_probability_denominator,
          sampling_weight_numerator, sampling_weight_denominator,
          count(*) observed_rows,
          max(sampling_hash_key) max_hash,
          max_by(pair_id, sampling_hash_key || ':' || pair_id) max_pair
        FROM read_parquet('{sample_path}')
        WHERE cell_id={_q(spec.cell_id)}
        GROUP BY ALL ORDER BY stratum_id
        """
    ).fetchall()
    thresholds = []
    for row in strata_rows:
        (
            stratum,
            population,
            sample,
            p_num,
            p_den,
            w_num,
            w_den,
            observed,
            max_hash,
            max_pair,
        ) = row
        probability = Fraction(int(sample), int(population))
        weight = 1 / probability
        if (
            int(observed) != int(sample)
            or (int(p_num), int(p_den))
            != (probability.numerator, probability.denominator)
            or (int(w_num), int(w_den)) != (weight.numerator, weight.denominator)
        ):
            raise RuntimeError(
                f"Sample rational design mismatch: {spec.cell_id}/{stratum}"
            )
        thresholds.append(
            {
                "stratum_id": str(stratum),
                "unlabeled_population": int(population),
                "sample_size": int(sample),
                "max_hash": str(max_hash),
                "max_pair": str(max_pair),
            }
        )
    connection.register("_validator_threshold_arrow", pa.Table.from_pylist(thresholds))
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE validator_threshold AS "
        "SELECT * FROM _validator_threshold_arrow"
    )
    connection.unregister("_validator_threshold_arrow")
    population_rows = connection.execute(
        f"""
        WITH candidates AS ({_candidate_sql(spec)}),
        hashed AS (
          SELECT c.*, sha256({_q(salt)} || ':' || {_q(seed)} || ':unlabeled:'
            || {_q(spec.cell_id)} || ':' || c.stratum_id || ':' || c.pair_id) hash_key
          FROM candidates c
        ),
        sample AS (
          SELECT pair_id FROM read_parquet('{sample_path}')
          WHERE cell_id={_q(spec.cell_id)}
        )
        SELECT h.stratum_id, count(*) population,
          count_if(
            h.hash_key < t.max_hash
            OR (h.hash_key = t.max_hash AND h.pair_id <= t.max_pair)
          ) at_or_below_threshold,
          count(s.pair_id) selected_rows_present_in_candidate_universe
        FROM hashed h
        LEFT JOIN sample s USING (pair_id)
        JOIN validator_threshold t USING (stratum_id)
        GROUP BY h.stratum_id ORDER BY h.stratum_id
        """
    ).fetchall()
    observed = {
        str(stratum): (int(population), int(below), int(selected))
        for stratum, population, below, selected in population_rows
    }
    expected = {
        row["stratum_id"]: (
            row["unlabeled_population"],
            row["sample_size"],
            row["sample_size"],
        )
        for row in thresholds
    }
    if observed != expected:
        raise RuntimeError(f"Bottom-hash threshold/population mismatch: {spec.cell_id}")

    geometry_failures = connection.execute(
        f"""
        SELECT count(*)
        FROM read_parquet('{sample_path}') s
        LEFT JOIN validator_cell_endpoints a ON a.endpoint=s.endpoint_a_sha256
        LEFT JOIN validator_cell_endpoints b ON b.endpoint=s.endpoint_b_sha256
        LEFT JOIN validator_positive_union p
          ON p.endpoint_a=s.endpoint_a_sha256 AND p.endpoint_b=s.endpoint_b_sha256
        WHERE s.cell_id={_q(spec.cell_id)}
          AND (
            a.endpoint IS NULL OR b.endpoint IS NULL OR p.endpoint_a IS NOT NULL
            OR s.endpoint_a_sha256 >= s.endpoint_b_sha256
            OR s.endpoint_a_component_id <> a.component_id
            OR s.endpoint_b_component_id <> b.component_id
            OR s.endpoint_a_partition <> a.partition
            OR s.endpoint_b_partition <> b.partition
            OR s.endpoint_a_training_degree <> a.training_degree
            OR s.endpoint_b_training_degree <> b.training_degree
          )
        """
    ).fetchone()[0]
    if int(geometry_failures):
        raise RuntimeError(f"Sample endpoint/provenance mismatch: {spec.cell_id}")
    return {
        "rows": int(sample_checks[0]),
        "strata": len(thresholds),
        "unlabeled_population": sum(row["unlabeled_population"] for row in thresholds),
        "bottom_hash_exact": True,
    }


def _role_for(
    pair: tuple[str, str], state: Mapping[str, Any]
) -> tuple[str, str | None]:
    if pair in state["training_positive"]:
        return "training", None
    for cell in PRIMARY_CELLS:
        if pair in state["primary_sets"][cell]:
            return cell, None
    left, right = state["partition"][pair[0]], state["partition"][pair[1]]
    role = state["roles"].get(pair)
    if left == right == "train" and role in {"development", "test"}:
        return "quarantine", f"C1_{role}_failed_exposure"
    for heldout in ("development", "test"):
        if {left, right} == {"train", heldout}:
            return "quarantine", f"C2_{heldout}_failed_train_exposure"
    if {left, right} == {"development", "test"}:
        return "quarantine", "development_test_cross_partition"
    return "quarantine", "outside_primary_evaluation_geometry"


def _validate_role_ledger(
    *, ledger_glob: Path, state: Mapping[str, Any], source_state: Mapping[str, Any]
) -> dict[str, int]:
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            f"SELECT * FROM read_parquet('{ledger_glob.as_posix()}') ORDER BY pair_id"
        ).fetchall()
        names = [item[0] for item in connection.description]
    finally:
        connection.close()
    observed = [dict(zip(names, row)) for row in rows]
    observed_by_id = {str(row["pair_id"]): row for row in observed}
    if len(observed) != len(state["positive_pairs"]) or len(observed_by_id) != len(
        observed
    ):
        raise RuntimeError("Role ledger does not cover the positive union")
    counts = Counter()
    for pair in sorted(state["positive_pairs"]):
        identifier = _independent_pair_id(pair)
        row = observed_by_id.get(identifier)
        if row is None:
            raise RuntimeError("Role ledger is missing an independently expected pair")
        role, reason = _role_for(pair, state)
        sources = state["pair_sources"][pair]
        membership = (
            "both"
            if len(sources) == 2
            else "HI-II-14_only" if "HI-II-14" in sources else "HuRI_only"
        )
        if (
            row["pair_id"] != identifier
            or row["endpoint_a_sha256"] != pair[0]
            or row["endpoint_b_sha256"] != pair[1]
            or row["source_membership"] != membership
            or bool(row["hi_ii_14_supported"]) != ("HI-II-14" in sources)
            or bool(row["huri_supported"]) != ("HuRI" in sources)
            or row["c1_hash_role"] != state["roles"].get(pair)
            or row["primary_positive_role"] != role
            or row["primary_quarantine_reason"] != reason
        ):
            raise RuntimeError(
                "Role ledger fields differ from independent reconstruction"
            )
        for target, field in (
            ("HI-II-14", "source_exclusive_hi_ii_14_role"),
            ("HuRI", "source_exclusive_huri_role"),
        ):
            if pair in source_state[target]["visible"]:
                expected_source_role = "visible_training"
            elif sources != frozenset({target}):
                expected_source_role = "visible_non_target_or_not_target_only"
            else:
                expected_source_role = "quarantine"
                for cell in PRIMARY_CELLS:
                    if pair in source_state[target]["cells"][cell]:
                        expected_source_role = cell
                        break
            if row[field] != expected_source_role:
                raise RuntimeError(f"Source role ledger mismatch for target {target}")
        counts[role] += 1
    return dict(sorted(counts.items()))


def _candidate_union_check(
    *,
    connection: duckdb.DuckDBPyConnection,
    candidates_glob: Path,
    unlabeled_glob: Path,
    truth_glob: Path,
) -> dict[str, int]:
    candidates = candidates_glob.as_posix()
    unlabeled = unlabeled_glob.as_posix()
    truth = truth_glob.as_posix()
    row = connection.execute(
        f"""
        WITH expected AS (
          SELECT cell_id,
            'candidate:' || sha256('{PACKAGE_ID}:' || cell_id || ':' || pair_id)
              candidate_token
          FROM read_parquet('{unlabeled}')
          UNION ALL
          SELECT cell_id, candidate_token FROM read_parquet('{truth}')
        ),
        observed AS (
          SELECT cell_id, candidate_token FROM read_parquet('{candidates}')
        ),
        missing AS (SELECT * FROM expected EXCEPT SELECT * FROM observed),
        extra AS (SELECT * FROM observed EXCEPT SELECT * FROM expected)
        SELECT
          (SELECT count(*) FROM expected),
          (SELECT count(*) FROM observed),
          (SELECT count(*) FROM missing),
          (SELECT count(*) FROM extra),
          (SELECT count(*) FROM (
            SELECT cell_id,candidate_token,count(*) n FROM observed
            GROUP BY ALL HAVING n <> 1
          ))
        """
    ).fetchone()
    return {
        "expected": int(row[0]),
        "observed": int(row[1]),
        "missing": int(row[2]),
        "extra": int(row[3]),
        "duplicates": int(row[4]),
    }


def validate_artifacts(
    *,
    project_root: Path,
    config_path: Path,
    package_manifest_path: Path,
    construction_report_path: Path,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    require_apptainer()
    config = load_yaml(config_path)
    validate_config(config)
    paths, verified_documents = verify_documents(
        project_root=project_root, config=config, verify_hashes=True
    )
    keys = private_key_paths(project_root, config)
    fingerprints = verify_key_pairs(paths=paths, keys=keys)
    git = git_provenance(project_root)
    if not allow_dirty and not git["tracked_worktree_clean"]:
        raise RuntimeError("Production artifact validation requires a clean worktree")

    package_manifest_path = package_manifest_path.resolve(strict=True)
    construction_report_path = construction_report_path.resolve(strict=True)
    top_manifest_sha = _verify_sidecar(package_manifest_path)
    construction_report_sha = _verify_sidecar(construction_report_path)
    top_manifest = load_json(package_manifest_path)
    construction_report = load_json(construction_report_path)
    canonical_root = package_manifest_path.parent
    smoke = top_manifest.get("status") == "qualified_smoke"
    if allow_dirty != smoke:
        raise RuntimeError("--allow-dirty is restricted to smoke package validation")
    contract = load_contract(paths["artifact_schema"])

    training_manifest, training_tables = _verify_inner_package(
        root=canonical_root / "training",
        manifest_name="TRAINING_PACKAGE_MANIFEST.json",
        contract=contract,
    )
    with tempfile.TemporaryDirectory(
        prefix="pair_artifact_validation_", dir=(project_root / "artifacts/tmp")
    ) as temp_name:
        temp = Path(temp_name)
        development_manifest, development_tables, development_archive_sha = (
            _decrypt_package(
                canonical_root=canonical_root,
                top_manifest=top_manifest,
                role="development",
                certificate=paths["development_release_certificate"],
                private_key=keys["development"],
                output_root=temp / "development",
                manifest_name="DEVELOPMENT_PACKAGE_MANIFEST.json",
                contract=contract,
            )
        )
        candidate_manifest, candidate_tables, candidate_archive_sha = _decrypt_package(
            canonical_root=canonical_root,
            top_manifest=top_manifest,
            role="protected_candidates",
            certificate=paths["protected_candidates_certificate"],
            private_key=keys["protected_candidates"],
            output_root=temp / "protected_candidates",
            manifest_name="PROTECTED_CANDIDATE_PACKAGE_MANIFEST.json",
            contract=contract,
        )
        truth_manifest, truth_tables, truth_archive_sha = _decrypt_package(
            canonical_root=canonical_root,
            top_manifest=top_manifest,
            role="protected_truth",
            certificate=paths["protected_truth_certificate"],
            private_key=keys["protected_truth"],
            output_root=temp / "protected_truth",
            manifest_name="PROTECTED_TRUTH_PACKAGE_MANIFEST.json",
            contract=contract,
        )

        protocol = load_yaml(paths["frozen_protocol_config"])
        input_files, independent_inputs = _load_verified_inputs(
            project_root=project_root, config=protocol
        )
        connection = duckdb.connect(":memory:")
        connection.execute(
            f"SET memory_limit={_q(str(config['runtime']['duckdb_memory_limit']))}"
        )
        connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
        _register(connection, input_files)
        state = _independent_state(connection, protocol)
        source_state = _source_state(state)
        training_spec, development_specs, test_specs = _specs(state, source_state)
        _register_independent_tables(connection, state)

        checks = Checks()
        checks.add(
            "top_manifest_and_construction_report",
            top_manifest.get("package_id") == PACKAGE_ID
            and construction_report.get("package_id") == PACKAGE_ID
            and top_manifest.get("status")
            == ("qualified_smoke" if smoke else "complete_frozen")
            and construction_report.get("status")
            == ("qualified_smoke" if smoke else "complete_frozen"),
            {
                "package_manifest_sha256": top_manifest_sha,
                "construction_report_sha256": construction_report_sha,
            },
        )
        checks.add(
            "three_distinct_keypairs_and_ciphertexts",
            len(set(fingerprints.values())) == 3
            and len(
                {
                    development_archive_sha,
                    candidate_archive_sha,
                    truth_archive_sha,
                }
            )
            == 3,
            {"certificate_fingerprints_sha256": fingerprints},
        )
        checks.add(
            "inner_manifests_and_table_integrity",
            all(
                manifest.get("status")
                == ("qualified_smoke" if smoke else "complete_frozen")
                for manifest in (
                    training_manifest,
                    development_manifest,
                    candidate_manifest,
                    truth_manifest,
                )
            ),
            {
                "training_tables": sorted(training_tables),
                "development_tables": sorted(development_tables),
                "candidate_tables": sorted(candidate_tables),
                "truth_tables": sorted(truth_tables),
            },
        )
        expected = config["immutable_parent_expectations"]
        checks.add(
            "independent_parent_endpoint_component_positive_counts",
            len(state["partition"]) == int(expected["eligible_reference_sequences"])
            and len(state["component_partition"])
            == int(expected["hard_partition_components"])
            and len(state["positive_pairs"]) == int(expected["released_positive_pairs"])
            and len(state["training_positive"])
            == int(expected["training_positive_pairs"]),
            {
                "endpoints": len(state["partition"]),
                "components": len(state["component_partition"]),
                "positive_pairs": len(state["positive_pairs"]),
                "training_pairs": len(state["training_positive"]),
            },
        )

        training_keys = _read_keys(
            canonical_root / "training/positive_pairs/part-*.parquet"
        )
        development_keys = _read_keys(
            temp / "development/positive_pairs/part-*.parquet"
        )
        test_truth_keys = _read_keys(
            temp / "protected_truth/protected_positive_truth/part-*.parquet"
        )
        expected_training = _expected_positive_keys([training_spec])
        expected_development = _expected_positive_keys(development_specs)
        expected_test = _expected_positive_keys(test_specs)
        checks.add(
            "exact_training_development_test_positive_assignments",
            training_keys == expected_training
            and development_keys == expected_development
            and test_truth_keys == expected_test,
            {
                "training": len(training_keys),
                "development": len(development_keys),
                "protected_test": len(test_truth_keys),
            },
        )
        checks.add(
            "positive_role_exclusivity_and_training_endpoint_boundary",
            not (
                {identifier for _, identifier in training_keys}
                & {identifier for _, identifier in development_keys | test_truth_keys}
            )
            and all(
                state["partition"][endpoint] == "train"
                for pair in state["training_positive"]
                for endpoint in pair
            ),
            {
                "training_evaluation_positive_overlap": len(
                    {identifier for _, identifier in training_keys}
                    & {
                        identifier
                        for _, identifier in development_keys | test_truth_keys
                    }
                )
            },
        )

        visible_glob = (
            temp / "development/source_visible_training_positive_pairs/part-*.parquet"
        )
        visible_rows = connection.execute(
            f"SELECT target_source,pair_id FROM read_parquet('{visible_glob.as_posix()}')"
        ).fetchall()
        expected_visible = {
            (target, _independent_pair_id(pair))
            for target in SOURCES
            for pair in source_state[target]["visible"]
        }
        checks.add(
            "source_visible_training_artifacts",
            {(str(target), str(identifier)) for target, identifier in visible_rows}
            == expected_visible,
            {target: len(source_state[target]["visible"]) for target in SOURCES},
        )

        role_counts = _validate_role_ledger(
            ledger_glob=temp / "protected_truth/positive_role_ledger/part-*.parquet",
            state=state,
            source_state=source_state,
        )
        checks.add(
            "complete_independent_positive_role_ledger",
            sum(role_counts.values()) == len(state["positive_pairs"]),
            role_counts,
        )

        sample_results = {}
        sample_groups = (
            [
                (
                    training_spec,
                    canonical_root / "training/unlabeled_pairs/part-*.parquet",
                )
            ]
            + [
                (
                    spec,
                    temp / "development/unlabeled_pairs/part-*.parquet",
                )
                for spec in development_specs
            ]
            + [
                (
                    spec,
                    temp / "protected_truth/unlabeled_pairs/part-*.parquet",
                )
                for spec in test_specs
            ]
        )
        for spec, sample_glob in sample_groups:
            sample_results[spec.cell_id] = _validate_one_sample(
                connection=connection,
                spec=spec,
                state=state,
                sample_glob=sample_glob,
                config=config,
            )
        checks.add(
            "independent_candidate_populations_bottom_hashes_probabilities_weights",
            len(sample_results) == 19
            and all(result["bottom_hash_exact"] for result in sample_results.values()),
            {
                "cells": len(sample_results),
                "sample_rows": sum(
                    result["rows"] for result in sample_results.values()
                ),
                "unlabeled_population_sum_across_cells": sum(
                    result["unlabeled_population"] for result in sample_results.values()
                ),
            },
        )

        all_unlabeled = (
            f"SELECT 'training' boundary,cell_id,pair_id FROM read_parquet("
            f"'{(canonical_root / 'training/unlabeled_pairs/part-*.parquet').as_posix()}') "
            f"UNION ALL SELECT 'development',cell_id,pair_id FROM read_parquet("
            f"'{(temp / 'development/unlabeled_pairs/part-*.parquet').as_posix()}') "
            f"UNION ALL SELECT 'protected_test',cell_id,pair_id FROM read_parquet("
            f"'{(temp / 'protected_truth/unlabeled_pairs/part-*.parquet').as_posix()}')"
        )
        connection.execute(
            "CREATE TEMP TABLE independent_all_unlabeled AS " + all_unlabeled
        )
        positive_overlap = connection.execute(
            """
            SELECT count(*)
            FROM independent_all_unlabeled u
            JOIN (
              SELECT 'pair:' || sha256(endpoint_a || '|' || endpoint_b) pair_id
              FROM validator_positive_union
            ) p USING (pair_id)
            """
        ).fetchone()[0]
        overlap = connection.execute(
            """
            WITH grouped AS (
              SELECT pair_id,count(*) AS n_rows,count(DISTINCT cell_id) AS n_cells
              FROM independent_all_unlabeled GROUP BY pair_id
            )
            SELECT count(*),count_if(n_cells>1),
              coalesce(sum(n_rows-1) FILTER (WHERE n_cells>1),0),coalesce(max(n_cells),1)
            FROM grouped
            """
        ).fetchone()
        boundary_overlap = {}
        for left, right in (
            ("training", "development"),
            ("training", "protected_test"),
            ("development", "protected_test"),
        ):
            boundary_overlap[f"{left}__{right}"] = int(
                connection.execute(
                    """
                    SELECT count(DISTINCT a.pair_id)
                    FROM independent_all_unlabeled a
                    JOIN independent_all_unlabeled b USING (pair_id)
                    WHERE a.boundary=? AND b.boundary=?
                    """,
                    [left, right],
                ).fetchone()[0]
            )
        overlap_summary = {
            "distinct_unlabeled_pair_ids": int(overlap[0]),
            "pair_ids_reused_across_cells": int(overlap[1]),
            "repeated_sample_rows_beyond_first": int(overlap[2]),
            "maximum_cells_for_one_unlabeled_pair": int(overlap[3]),
            "cross_visibility_boundary_pair_ids": boundary_overlap,
            "interpretation": "permitted_cross_cell_unlabeled_reuse_not_positive_evidence_leakage",
        }
        checks.add(
            "zero_positive_as_unlabeled_and_reported_cross_cell_reuse",
            int(positive_overlap) == 0
            and overlap_summary
            == top_manifest["artifacts"]["cross_cell_unlabeled_overlap"],
            {
                "positive_as_unlabeled": int(positive_overlap),
                **overlap_summary,
            },
        )

        candidate_union = _candidate_union_check(
            connection=connection,
            candidates_glob=temp
            / "protected_candidates/protected_candidates/part-*.parquet",
            unlabeled_glob=temp / "protected_truth/unlabeled_pairs/part-*.parquet",
            truth_glob=temp / "protected_truth/protected_positive_truth/part-*.parquet",
        )
        checks.add(
            "protected_candidate_union_exact_and_role_free",
            candidate_union["expected"] == candidate_union["observed"]
            and not any(
                candidate_union[key] for key in ("missing", "extra", "duplicates")
            )
            and "state"
            not in pq.ParquetFile(
                temp / "protected_candidates/protected_candidates/part-00000.parquet"
            ).schema_arrow.names
            and "pair_id"
            not in pq.ParquetFile(
                temp / "protected_candidates/protected_candidates/part-00000.parquet"
            ).schema_arrow.names,
            candidate_union,
        )

        public_files = sorted(
            path.relative_to(canonical_root).as_posix()
            for path in canonical_root.rglob("*")
            if path.is_file()
        )
        allowed_public_prefixes = (
            "training/",
            "sealed/",
            "PACKAGE_MANIFEST.json",
            "PACKAGE_MANIFEST.json.sha256",
        )
        unexpected_public = [
            path
            for path in public_files
            if not path.startswith(allowed_public_prefixes)
        ]
        public_json = package_manifest_path.read_text(encoding="utf-8") + (
            canonical_root / "training/TRAINING_PACKAGE_MANIFEST.json"
        ).read_text(encoding="utf-8")
        published_pair_ids = set(re.findall(r"pair:[0-9a-f]{64}", public_json))
        protected_pair_ids = {
            identifier for _, identifier in expected_development | expected_test
        }
        checks.add(
            "protected_identities_absent_from_public_workflows",
            not unexpected_public
            and not (published_pair_ids & protected_pair_ids)
            and not (canonical_root / "development").exists()
            and not (canonical_root / "protected_test").exists(),
            {
                "unexpected_public_files": unexpected_public,
                "protected_pair_ids_in_public_json": len(
                    published_pair_ids & protected_pair_ids
                ),
                "ciphertext_packages": 3,
            },
        )

        checks.add(
            "scope_and_claim_boundaries",
            all(value is False for value in top_manifest["artifacts"]["scope"].values())
            and top_manifest.get("negative_or_pseudo_negative_state_present") is False
            and all(value == "prohibited" for value in config["claims"].values()),
            top_manifest["artifacts"]["scope"],
        )
        connection.close()

        result_copy = {
            "training_manifest": training_manifest,
            "development_manifest": development_manifest,
            "candidate_manifest": candidate_manifest,
            "truth_manifest": truth_manifest,
            "sample_results": sample_results,
            "overlap_summary": overlap_summary,
            "candidate_union": candidate_union,
            "role_counts": role_counts,
        }

    status = "pass" if checks.passed else "fail"
    return {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "status": status,
        "scope": "qualification_smoke" if smoke else "production_full",
        "completed_at_utc": _timestamp(),
        "validator_git": git,
        "production_git": top_manifest.get("git"),
        "config": config_path.as_posix(),
        "config_sha256": sha256_file(config_path),
        "package_manifest": package_manifest_path.as_posix(),
        "package_manifest_sha256": top_manifest_sha,
        "construction_report": construction_report_path.as_posix(),
        "construction_report_sha256": construction_report_sha,
        "verified_documents": verified_documents,
        "independent_parent_inputs": independent_inputs,
        "check_counts": checks.counts(),
        "checks": checks.records,
        "independent_results": result_copy,
        "interpretation": {
            "unlabeled_is_negative": False,
            "cross_cell_unlabeled_reuse_is_positive_leakage": False,
            "protected_candidate_and_truth_separately_sealed": True,
            "public_pair_keyed_test_submission_supported": False,
            "scorer_execution_inside_sealed_evaluator_required": True,
            "exact_full_universe_metrics_from_sample_supported": False,
            "model_work_performed": False,
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/pair_level_pu_r_benchmark_artifacts_v1.yaml"),
    )
    parser.add_argument("--package-manifest", type=Path)
    parser.add_argument("--construction-report", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path.cwd())
    config_path = (
        args.config
        if args.config.is_absolute()
        else (project_root / args.config).resolve(strict=True)
    )
    config = load_yaml(config_path)
    package_manifest = (
        args.package_manifest
        or Path(str(config["outputs"]["canonical_root"])) / "PACKAGE_MANIFEST.json"
    )
    construction_report = args.construction_report or Path(
        str(config["outputs"]["construction_report"])
    )
    report_path = args.report or Path(str(config["outputs"]["validation_report"]))
    package_manifest = (
        package_manifest
        if package_manifest.is_absolute()
        else project_root / package_manifest
    )
    construction_report = (
        construction_report
        if construction_report.is_absolute()
        else project_root / construction_report
    )
    report_path = (
        report_path if report_path.is_absolute() else project_root / report_path
    )
    result = validate_artifacts(
        project_root=project_root,
        config_path=config_path,
        package_manifest_path=package_manifest,
        construction_report_path=construction_report,
        allow_dirty=bool(args.allow_dirty),
    )
    _write_report(report_path, result, project_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
