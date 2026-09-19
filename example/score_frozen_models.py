#!/usr/bin/env python3
"""Score the example protein pairs with both frozen iPIN-OpenPPI models.

Run from the repository root with the checksum-pinned model SIF::

    apptainer exec --cleanenv --containall --no-home \
      --bind "$PWD:/project" --pwd /project \
      containers/images/ipin-model-arm64_0.1.0.sif \
      python example/score_frozen_models.py

The input accessions must belong to the frozen 17,000-protein endpoint universe.
Scores are raw ranking scores, not probabilities or calibrated predictions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import torch
from torch.nn import functional as F


BEST_MODEL = "esm2_150m__residual_wide__epoch04_ensemble3"
BASELINE_MODEL = "lightweight_esm2_150m_linear__linear_lr3e-4"
SEEDS = (20260803, 20260817, 20260831)
ENDPOINT_TABLE_SHA256 = "4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e"
REQUIRED_COLUMNS = ("query_uniprot", "partner_uniprot")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_file(root: Path, record: dict[str, Any]) -> Path:
    relative = Path(record["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"unsafe frozen artifact path: {relative}")
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"missing or unsafe frozen artifact: {path}")
    if path.stat().st_size != int(record["bytes"]):
        raise RuntimeError(f"frozen artifact byte-count drift: {path}")
    if sha256_file(path) != record["sha256"]:
        raise RuntimeError(f"frozen artifact checksum drift: {path}")
    return path


def load_registry(project_root: Path, bundle: Path) -> dict[str, Any]:
    public_path = project_root / "artifacts/models/frozen_pair_models_v1/MODEL_REGISTRY.json"
    checksum_path = public_path.with_suffix(".json.sha256")
    expected_line = f"{sha256_file(public_path)}  {public_path.name}\n"
    if checksum_path.read_text(encoding="utf-8") != expected_line:
        raise RuntimeError("public frozen-model registry checksum drift")
    if sha256_file(public_path) != sha256_file(bundle / "MODEL_REGISTRY.json"):
        raise RuntimeError("public/private frozen-model registry mismatch")
    registry = json.loads(public_path.read_text(encoding="utf-8"))
    if registry["roles"] != {
        "best_performing_model": BEST_MODEL,
        "original_confirmatory_baseline": BASELINE_MODEL,
    }:
        raise RuntimeError("frozen model roles differ from the v1 release")
    for model_id in (BEST_MODEL, BASELINE_MODEL):
        model = registry["models"][model_id]
        if model["status"] != "frozen" or tuple(model["seeds"]) != SEEDS:
            raise RuntimeError(f"frozen model membership drift: {model_id}")
        if model["aggregation"] != "arithmetic_mean_of_three_FP32_raw_scores_in_FP64":
            raise RuntimeError(f"frozen ensemble definition drift: {model_id}")
    return registry


def read_pairs(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in columns]
        if missing:
            raise RuntimeError(f"input CSV is missing columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise RuntimeError("input CSV contains no protein pairs")
    for row_number, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            row[column] = row[column].strip()
            if not row[column]:
                raise RuntimeError(f"empty {column} at CSV row {row_number}")
    return rows, columns


def accession_to_endpoint(endpoint_table: Path, accessions: set[str]) -> dict[str, str]:
    if sha256_file(endpoint_table) != ENDPOINT_TABLE_SHA256:
        raise RuntimeError("frozen endpoint table checksum drift")
    table = pq.read_table(
        endpoint_table,
        columns=["reference_sequence_sha256", "uniprot_accessions"],
    )
    candidates: dict[str, set[str]] = {accession: set() for accession in accessions}
    for row in table.to_pylist():
        endpoint = str(row["reference_sequence_sha256"])
        for accession in row["uniprot_accessions"]:
            if accession in candidates:
                candidates[accession].add(endpoint)
    invalid = {accession: values for accession, values in candidates.items() if len(values) != 1}
    if invalid:
        detail = ", ".join(
            f"{accession} ({len(values)} matches)" for accession, values in sorted(invalid.items())
        )
        raise RuntimeError(f"accessions do not map uniquely to frozen endpoints: {detail}")
    return {accession: next(iter(values)) for accession, values in candidates.items()}


def pair_features(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    denominator = torch.linalg.vector_norm(a, dim=-1) * torch.linalg.vector_norm(b, dim=-1)
    if torch.any(denominator <= 0):
        raise RuntimeError("undefined exact cosine for a zero-norm endpoint vector")
    cosine = ((a * b).sum(dim=-1) / denominator).unsqueeze(-1)
    return torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)


def load_state(path: Path, expected: dict[str, tuple[int, ...]]) -> dict[str, torch.Tensor]:
    with np.load(path, allow_pickle=False) as archive:
        if set(archive.files) != set(expected):
            raise RuntimeError(f"unexpected state keys in {path}")
        state: dict[str, torch.Tensor] = {}
        for name, shape in expected.items():
            value = archive[name]
            if value.shape != shape or value.dtype != np.float32 or not np.isfinite(value).all():
                raise RuntimeError(f"invalid frozen parameter {name} in {path}")
            state[name] = torch.from_numpy(value.copy())
    return state


def affine_member(features: torch.Tensor, state: dict[str, torch.Tensor]) -> np.ndarray:
    return F.linear(features, state["weight"], state["bias"]).squeeze(-1).numpy()


def optimized_member(features: torch.Tensor, state: dict[str, torch.Tensor]) -> np.ndarray:
    residual = F.linear(features, state["output.weight"], state["output.bias"])
    hidden = F.layer_norm(
        features,
        (features.shape[-1],),
        state["network.0.weight"],
        state["network.0.bias"],
        1e-5,
    )
    hidden = F.linear(hidden, state["network.1.weight"], state["network.1.bias"])
    hidden = F.gelu(hidden)
    hidden = F.linear(hidden, state["network.4.weight"], state["network.4.bias"])
    return (residual + hidden).squeeze(-1).numpy()


def ensemble_scores(
    features: torch.Tensor,
    bundle: Path,
    registry: dict[str, Any],
    model_id: str,
) -> np.ndarray:
    optimized = model_id == BEST_MODEL
    expected = (
        {
            "output.weight": (1, 1921),
            "output.bias": (1,),
            "network.0.weight": (1921,),
            "network.0.bias": (1921,),
            "network.1.weight": (256, 1921),
            "network.1.bias": (256,),
            "network.4.weight": (1, 256),
            "network.4.bias": (1,),
        }
        if optimized
        else {"weight": (1, 1921), "bias": (1,)}
    )
    members: list[np.ndarray] = []
    for member in registry["models"][model_id]["members"]:
        if int(member["seed"]) not in SEEDS:
            raise RuntimeError(f"unexpected frozen seed in {model_id}")
        path = checked_file(bundle, member["state"])
        state = load_state(path, expected)
        with torch.inference_mode():
            score = optimized_member(features, state) if optimized else affine_member(features, state)
        members.append(score.astype(np.float64))
    values = np.column_stack(members).mean(axis=1, dtype=np.float64)
    if not np.isfinite(values).all():
        raise RuntimeError(f"nonfinite ensemble prediction from {model_id}")
    return values


def write_scores(
    output_path: Path,
    rows: list[dict[str, str]],
    columns: list[str],
    optimized: np.ndarray,
    baseline: np.ndarray,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[*columns, "optimized_score", "baseline_score"],
            lineterminator="\n",
        )
        writer.writeheader()
        for row, optimized_score, baseline_score in zip(rows, optimized, baseline, strict=True):
            writer.writerow(
                {
                    **row,
                    "optimized_score": format(float(optimized_score), ".17g"),
                    "baseline_score": format(float(baseline_score), ".17g"),
                }
            )
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output_path)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=script_dir / "ire1_ipin_panel.csv")
    parser.add_argument("--output", type=Path, default=script_dir / "ire1_ipin_panel_scores.csv")
    args = parser.parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    if input_path == output_path:
        raise RuntimeError("input and output CSV paths must differ")

    bundle = project_root / ".private/frozen_pair_models_v1/bundle"
    endpoint_table = (
        project_root
        / "data/canonical/benchmark_eligibility_and_sequence_component_audit_v1"
        / "eligible_reference_sequences/part-00000.parquet"
    )
    registry = load_registry(project_root, bundle)
    rows, columns = read_pairs(input_path)
    accessions = {
        row[column]
        for row in rows
        for column in REQUIRED_COLUMNS
    }
    endpoint_by_accession = accession_to_endpoint(endpoint_table, accessions)

    endpoint_record = registry["shared_inputs"]["endpoints.json"]
    matrix_record = registry["shared_inputs"]["standardized.npy"]
    endpoint_ids = json.loads(checked_file(bundle, endpoint_record).read_text(encoding="utf-8"))
    if len(endpoint_ids) != 17_000 or len(set(endpoint_ids)) != len(endpoint_ids):
        raise RuntimeError("frozen endpoint identity census drift")
    index = {endpoint: position for position, endpoint in enumerate(endpoint_ids)}
    a = np.asarray(
        [index[endpoint_by_accession[row["query_uniprot"]]] for row in rows],
        dtype=np.int64,
    )
    b = np.asarray(
        [index[endpoint_by_accession[row["partner_uniprot"]]] for row in rows],
        dtype=np.int64,
    )
    matrix = np.load(checked_file(bundle, matrix_record), mmap_mode="r", allow_pickle=False)
    if matrix.shape != (17_000, 640) or matrix.dtype != np.float32:
        raise RuntimeError("frozen standardized embedding shape or dtype drift")
    left = torch.from_numpy(np.asarray(matrix[a], dtype=np.float32).copy())
    right = torch.from_numpy(np.asarray(matrix[b], dtype=np.float32).copy())
    features = pair_features(left, right)
    if features.shape != (len(rows), 1921) or features.dtype != torch.float32:
        raise RuntimeError("pair feature shape or precision drift")

    optimized = ensemble_scores(features, bundle, registry, BEST_MODEL)
    baseline = ensemble_scores(features, bundle, registry, BASELINE_MODEL)
    write_scores(output_path, rows, columns, optimized, baseline)
    print(f"Scored {len(rows)} pairs with {BEST_MODEL} and {BASELINE_MODEL}.")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
