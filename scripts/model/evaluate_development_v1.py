#!/usr/bin/env python3
"""Compute all frozen development metrics and the exact governance trace."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import yaml

from ipin_openppi.development_evaluation.evaluation import (
    _load_bootstrap,
    _read_cell,
    apply_selection_and_kill_rules,
    c1_novel_u_metrics,
    degree_and_hub_diagnostics,
    gpu_bootstrap_distributions,
    point_metrics,
    score_correlations,
)
from ipin_openppi.development_evaluation.release import sha256_file
from ipin_openppi.development_evaluation.scoring import (
    DEVELOPMENT_CELLS,
    load_endpoint_universe,
    load_training_graph,
)
from ipin_openppi.development_evaluation.semantics import DETERMINISTIC_SCORERS, PRIMARY_CELLS, frozen_hub_sets, percentile_95


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite public development result: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--execution-config",
        type=Path,
        default=Path("configs/development_release_and_evaluation_execution_v1.yaml"),
    )
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    config_path = (root / args.execution_config).resolve(strict=True)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    private_root = root / config["development_release"]["evaluation_root"]
    scoring_manifest_path = private_root / "SCORING_RUN_MANIFEST.json"
    scoring_manifest = json.loads(scoring_manifest_path.read_text(encoding="utf-8"))
    if scoring_manifest.get("cell_count") != 9 or scoring_manifest.get("scorer_count") != 49:
        raise RuntimeError("complete frozen scoring manifest required")
    training_registry_path = root / config["frozen_inputs"]["training_registry"]
    if sha256_file(training_registry_path) != config["frozen_inputs"]["training_registry_sha256"]:
        raise RuntimeError("training registry drift before development evaluation")
    training_registry = json.loads(training_registry_path.read_text(encoding="utf-8"))
    endpoint_path = root / config["frozen_inputs"]["endpoints"]
    partition_path = root / config["frozen_inputs"]["partitions"]
    positive_path = root / config["frozen_inputs"]["training_positive"]
    universe = load_endpoint_universe(endpoint_path, partition_path)
    graph = load_training_graph(positive_path, universe)
    degree_by_training_endpoint = {
        sequence: int(graph.degree[index])
        for index, sequence in enumerate(universe.sequence_sha256)
        if universe.partitions[index] == "train"
    }
    hubs = frozen_hub_sets(degree_by_training_endpoint)

    candidate_ids = [str(item["candidate_id"]) for item in training_registry["ensembles"]]
    bootstrap_scorers = list(DETERMINISTIC_SCORERS) + candidate_ids
    point_by_cell = {}
    degree_hub = {}
    correlations = {}
    bootstrap_registry = {}
    bootstrap_by_cell = {}
    cached = {}
    for cell_id in DEVELOPMENT_CELLS:
        cell_root = private_root / "scores" / cell_id.replace(":", "__")
        rows, scores, scorer_ids, _ = _read_cell(cell_root)
        cached[cell_id] = (rows, scores, scorer_ids)
        point_by_cell[cell_id] = point_metrics(rows, scores, scorer_ids)
        if cell_id in PRIMARY_CELLS:
            degree_hub[cell_id] = degree_and_hub_diagnostics(
                rows=rows, scores=scores, scorer_ids=scorer_ids, hub_sets=hubs
            )
            correlations[cell_id] = score_correlations(scores, scorer_ids)
            bootstrap_root = private_root / "bootstrap" / cell_id
            bootstrap_registry[cell_id] = gpu_bootstrap_distributions(
                cell_id=cell_id,
                rows=rows,
                scores=scores,
                scorer_ids=scorer_ids,
                bootstrap_scorer_ids=bootstrap_scorers,
                output_root=bootstrap_root,
            )
            bootstrap_by_cell[cell_id] = _load_bootstrap(bootstrap_root)

    public_training_u = pq.read_table(
        root / config["frozen_inputs"]["training_unlabeled"], columns=["pair_id"]
    )
    public_u_ids = set(map(str, public_training_u["pair_id"].to_pylist()))
    c1_rows, c1_scores, c1_scorers = cached["C1_development"]
    novel_u = c1_novel_u_metrics(
        rows=c1_rows,
        scores=c1_scores,
        scorer_ids=c1_scorers,
        public_training_u_pair_ids=public_u_ids,
    )
    disposition = apply_selection_and_kill_rules(
        point_by_cell=point_by_cell,
        bootstrap_by_cell=bootstrap_by_cell,
        hub_by_cell=degree_hub,
        novel_u=novel_u,
        training_registry=training_registry,
    )

    primary_metrics = {}
    for cell in PRIMARY_CELLS:
        scorer_ids, distributions = bootstrap_by_cell[cell]
        intervals = {
            scorer: list(percentile_95(distributions[index]))
            for index, scorer in enumerate(scorer_ids)
        }
        primary_metrics[cell] = {
            "metrics": point_by_cell[cell],
            "bootstrap_percentile_95_for_controls_and_ensembles": intervals,
            "seed_checkpoint_intervals": "not_required_seed_stability_uses_point_metric_range",
        }
    source_metrics = {
        cell: point_by_cell[cell] for cell in DEVELOPMENT_CELLS if cell not in PRIMARY_CELLS
    }
    output_root = root / config["outputs"]["public_results_root"]
    output_root.mkdir(parents=True, exist_ok=False)
    common = {
        "schema_version": 1,
        "execution_id": config["execution_id"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reporting_order": ["C3", "C2", "C1"],
        "protected_candidates_accessed": False,
        "protected_truth_accessed": False,
        "training_or_checkpoint_change": False,
        "pair_identity_public": False,
    }
    outputs = {
        "PRIMARY_METRICS.json": {**common, "cells": primary_metrics},
        "SOURCE_EXCLUSIVE_METRICS.json": {**common, "cells": source_metrics},
        "DEGREE_HUB_DIAGNOSTICS.json": {**common, "cells": degree_hub},
        "C1_NOVEL_U_SENSITIVITY.json": {**common, "C1_development": novel_u},
        "DIAGNOSTIC_CORRELATIONS.json": {**common, "cells": correlations},
        "BOOTSTRAP_REGISTRY.json": {**common, "cells": bootstrap_registry},
        "SELECTION_AND_KILL_TRACE.json": {**common, **disposition},
    }
    file_records = []
    for name, payload in outputs.items():
        path = output_root / name
        _atomic_json(path, payload)
        file_records.append({"path": name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    result_manifest = {
        **common,
        "execution_config_sha256": sha256_file(config_path),
        "scoring_run_manifest_sha256": sha256_file(scoring_manifest_path),
        "files": file_records,
        "development_stage_disposition": disposition["development_stage_disposition"],
        "stop_before_protected_evaluation": disposition["kill_trace"]["stop_before_protected_evaluation"],
    }
    _atomic_json(output_root / "DEVELOPMENT_RESULTS_MANIFEST.json", result_manifest)
    print(
        "development_evaluation: PASS disposition="
        + disposition["development_stage_disposition"]
    )


if __name__ == "__main__":
    main()
