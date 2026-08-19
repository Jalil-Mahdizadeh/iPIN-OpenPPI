"""Exact frozen-scorer execution over an already released development package."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from scipy import sparse
import torch
from torch.nn import functional as F

from ipin_openppi.stage1.baselines import kmer3_csr

from .release import sha256_file
from .semantics import DETERMINISTIC_SCORERS, validate_scorer_census


SCORE_BATCH = 32_768
INTEROLOG_BATCH = 8_192
DEVELOPMENT_CELLS = (
    "C3_development",
    "source_exclusive:HI-II-14:C3_development",
    "source_exclusive:HuRI:C3_development",
    "C2_development",
    "source_exclusive:HI-II-14:C2_development",
    "source_exclusive:HuRI:C2_development",
    "C1_development",
    "source_exclusive:HI-II-14:C1_development",
    "source_exclusive:HuRI:C1_development",
)
ROW_COLUMNS = (
    "cell_id",
    "pair_id",
    "endpoint_a_sha256",
    "endpoint_b_sha256",
    "endpoint_a_component_id",
    "endpoint_b_component_id",
    "endpoint_a_training_degree",
    "endpoint_b_training_degree",
    "stratum_id",
    "state",
    "sampling_weight_numerator",
    "sampling_weight_denominator",
)


@dataclass(frozen=True)
class EndpointUniverse:
    sequence_sha256: tuple[str, ...]
    sequences: tuple[str, ...]
    lengths: np.ndarray
    components: tuple[str, ...]
    partitions: tuple[str, ...]
    index_by_sha256: Mapping[str, int]


@dataclass(frozen=True)
class TrainingGraph:
    degree: np.ndarray
    component_mass: Mapping[str, int]
    adjacency: sparse.csr_matrix
    edge_u: np.ndarray
    edge_v: np.ndarray
    exposed_indices: np.ndarray
    exposed_position_by_endpoint: np.ndarray


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite score evidence: {path}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _map(values: Sequence[str], index: Mapping[str, int]) -> np.ndarray:
    try:
        return np.fromiter((index[str(value)] for value in values), dtype=np.int32, count=len(values))
    except KeyError as exc:
        raise RuntimeError(f"development endpoint outside frozen universe: {exc}") from exc


def load_endpoint_universe(endpoint_path: Path, partition_path: Path) -> EndpointUniverse:
    endpoints = pq.read_table(
        endpoint_path, columns=["reference_sequence_sha256", "sequence", "sequence_length"]
    ).sort_by([("reference_sequence_sha256", "ascending")])
    partitions = pq.read_table(
        partition_path,
        columns=["reference_sequence_sha256", "component_id", "partition", "sequence_length"],
    ).sort_by([("reference_sequence_sha256", "ascending")])
    endpoint_sha = tuple(map(str, endpoints["reference_sequence_sha256"].to_pylist()))
    partition_sha = tuple(map(str, partitions["reference_sequence_sha256"].to_pylist()))
    if endpoint_sha != partition_sha or len(endpoint_sha) != 17_000 or len(set(endpoint_sha)) != 17_000:
        raise RuntimeError("frozen endpoint/partition universe identity drift")
    lengths = np.asarray(endpoints["sequence_length"].to_numpy(), dtype=np.int64)
    partition_lengths = np.asarray(partitions["sequence_length"].to_numpy(), dtype=np.int64)
    if not np.array_equal(lengths, partition_lengths):
        raise RuntimeError("endpoint length differs across frozen parents")
    partition_values = tuple(map(str, partitions["partition"].to_pylist()))
    if Counter(partition_values) != Counter({"train": 11_900, "development": 2_550, "test": 2_550}):
        raise RuntimeError("frozen endpoint partition counts drift")
    return EndpointUniverse(
        sequence_sha256=endpoint_sha,
        sequences=tuple(map(str, endpoints["sequence"].to_pylist())),
        lengths=lengths,
        components=tuple(map(str, partitions["component_id"].to_pylist())),
        partitions=partition_values,
        index_by_sha256={value: index for index, value in enumerate(endpoint_sha)},
    )


def load_training_graph(positive_path: Path, universe: EndpointUniverse) -> TrainingGraph:
    table = pq.read_table(
        positive_path,
        columns=[
            "endpoint_a_sha256",
            "endpoint_b_sha256",
            "endpoint_a_training_degree",
            "endpoint_b_training_degree",
            "state",
        ],
    )
    if table.num_rows != 16_799 or set(table["state"].to_pylist()) != {"released_positive"}:
        raise RuntimeError("public training-positive graph drift")
    endpoint_a = _map(table["endpoint_a_sha256"].to_pylist(), universe.index_by_sha256)
    endpoint_b = _map(table["endpoint_b_sha256"].to_pylist(), universe.index_by_sha256)
    if np.any(endpoint_a == endpoint_b):
        raise RuntimeError("self-pair entered training graph")
    degree = np.bincount(np.concatenate((endpoint_a, endpoint_b)), minlength=17_000).astype(np.int64)
    for endpoints, column in (
        (endpoint_a, "endpoint_a_training_degree"),
        (endpoint_b, "endpoint_b_training_degree"),
    ):
        if not np.array_equal(degree[endpoints], np.asarray(table[column].to_numpy(), dtype=np.int64)):
            raise RuntimeError("training degree field differs from public training graph")
    exposed = np.flatnonzero(degree > 0).astype(np.int32)
    if exposed.size != 4_675 or np.any(np.asarray(universe.partitions)[exposed] != "train"):
        raise RuntimeError("training-exposed endpoint census drift")
    position = np.full(17_000, -1, dtype=np.int32)
    position[exposed] = np.arange(exposed.size, dtype=np.int32)
    edge_u = position[endpoint_a]
    edge_v = position[endpoint_b]
    if np.any(edge_u < 0) or np.any(edge_v < 0):
        raise RuntimeError("training edge endpoint missing exposed position")
    adjacency = sparse.coo_matrix(
        (
            np.ones(2 * table.num_rows, dtype=np.int8),
            (np.concatenate((endpoint_a, endpoint_b)), np.concatenate((endpoint_b, endpoint_a))),
        ),
        shape=(17_000, 17_000),
    ).tocsr()
    if adjacency.nnz != 2 * table.num_rows:
        raise RuntimeError("duplicate training graph edge")
    component_mass: Counter[str] = Counter()
    for endpoint_index, value in enumerate(degree):
        component_mass[universe.components[endpoint_index]] += int(value)
    return TrainingGraph(
        degree=degree,
        component_mass=dict(component_mass),
        adjacency=adjacency,
        edge_u=edge_u,
        edge_v=edge_v,
        exposed_indices=exposed,
        exposed_position_by_endpoint=position,
    )


def load_cell_rows(package_root: Path, cell_id: str) -> pa.Table:
    if cell_id not in DEVELOPMENT_CELLS:
        raise RuntimeError(f"cell not frozen for development execution: {cell_id}")
    tables: list[pa.Table] = []
    for directory, state in (("positive_pairs", "released_positive"), ("unlabeled_pairs", "unlabeled")):
        dataset = ds.dataset(package_root / directory, format="parquet")
        table = dataset.to_table(columns=list(ROW_COLUMNS), filter=ds.field("cell_id") == cell_id)
        if table.num_rows == 0 or set(table["state"].to_pylist()) != {state}:
            raise RuntimeError(f"missing or invalid {state} rows for {cell_id}")
        tables.append(table)
    output = pa.concat_tables(tables, promote_options="permissive")
    pair_ids = output["pair_id"].to_pylist()
    positive_rows = tables[0].num_rows
    if len(set(map(str, pair_ids[:positive_rows]))) != positive_rows:
        raise RuntimeError("duplicate development positive pair within cell")
    if len(set(map(str, pair_ids[positive_rows:]))) != tables[1].num_rows:
        raise RuntimeError("duplicate development U pair within cell")
    numerator = np.asarray(output["sampling_weight_numerator"].to_numpy(), dtype=np.int64)
    denominator = np.asarray(output["sampling_weight_denominator"].to_numpy(), dtype=np.int64)
    if np.any(numerator <= 0) or np.any(denominator <= 0):
        raise RuntimeError("nonpositive development rational weight")
    if not np.all(numerator[:positive_rows] == 1) or not np.all(denominator[:positive_rows] == 1):
        raise RuntimeError("development positive census weights differ from 1/1")
    return output


def deterministic_scores(
    rows: pa.Table,
    *,
    universe: EndpointUniverse,
    graph: TrainingGraph,
    kmer: sparse.csr_matrix,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pair_ids = tuple(map(str, rows["pair_id"].to_pylist()))
    a = _map(rows["endpoint_a_sha256"].to_pylist(), universe.index_by_sha256)
    b = _map(rows["endpoint_b_sha256"].to_pylist(), universe.index_by_sha256)
    degree_a, degree_b = graph.degree[a], graph.degree[b]
    recorded_a = np.asarray(rows["endpoint_a_training_degree"].to_numpy(), dtype=np.int64)
    recorded_b = np.asarray(rows["endpoint_b_training_degree"].to_numpy(), dtype=np.int64)
    if not np.array_equal(degree_a, recorded_a) or not np.array_equal(degree_b, recorded_b):
        raise RuntimeError("development degree metadata differs from training graph")
    output = np.empty((rows.num_rows, len(DETERMINISTIC_SCORERS)), dtype=np.float64)
    for index, pair_id in enumerate(pair_ids):
        payload = f"ipin-openppi-pu-r-baseline-v1:20260803:baseline:{pair_id}".encode("utf-8")
        output[index, 0] = int.from_bytes(hashlib.sha256(payload).digest(), "big") / (2**256 - 1)
    output[:, 1] = np.log1p(degree_a) + np.log1p(degree_b)
    output[:, 2] = np.log1p(degree_a * degree_b)
    mass_a = np.fromiter(
        (graph.component_mass[universe.components[int(value)]] for value in a),
        dtype=np.int64,
        count=a.size,
    )
    mass_b = np.fromiter(
        (graph.component_mass[universe.components[int(value)]] for value in b),
        dtype=np.int64,
        count=b.size,
    )
    output[:, 3] = np.log1p(mass_a * mass_b)
    for start in range(0, rows.num_rows, 100_000):
        stop = min(start + 100_000, rows.num_rows)
        common = graph.adjacency[a[start:stop]].multiply(graph.adjacency[b[start:stop]]).sum(axis=1)
        output[start:stop, 4] = np.log1p(np.asarray(common).ravel())
        cosine = kmer[a[start:stop]].multiply(kmer[b[start:stop]]).sum(axis=1)
        output[start:stop, 7] = np.asarray(cosine).ravel()
    length_a, length_b = universe.lengths[a], universe.lengths[b]
    output[:, 5] = np.log1p(length_a) + np.log1p(length_b)
    output[:, 6] = -np.abs(np.log1p(length_a) - np.log1p(length_b))
    if not np.isfinite(output[:, :8]).all():
        raise RuntimeError("nonfinite mandatory deterministic score")
    return output, a, b


def build_interolog_matrices(
    kmer: sparse.csr_matrix, graph: TrainingGraph
) -> tuple[np.ndarray, np.ndarray]:
    similarities = (kmer @ kmer[graph.exposed_indices].T).toarray().astype(np.float64, copy=False)
    if similarities.shape != (17_000, 4_675) or not np.isfinite(similarities).all():
        raise RuntimeError("3-mer similarity matrix invalid")
    neighbor = np.zeros_like(similarities)
    neighbors: dict[int, list[int]] = defaultdict(list)
    for u, v in zip(graph.edge_u, graph.edge_v, strict=True):
        neighbors[int(u)].append(int(v))
        neighbors[int(v)].append(int(u))
    for endpoint in range(4_675):
        values = neighbors.get(endpoint)
        if values:
            neighbor[:, endpoint] = similarities[:, values].max(axis=1)
    return similarities, neighbor


def score_interolog_gpu(
    similarities: np.ndarray,
    neighbor_max: np.ndarray,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
    *,
    device: str = "cuda",
) -> np.ndarray:
    similarity_tensor = torch.from_numpy(similarities).to(device=device, dtype=torch.float64)
    neighbor_tensor = torch.from_numpy(neighbor_max).to(device=device, dtype=torch.float64)
    output = np.empty(pair_a.size, dtype=np.float64)
    with torch.inference_mode():
        for start in range(0, pair_a.size, INTEROLOG_BATCH):
            stop = min(start + INTEROLOG_BATCH, pair_a.size)
            a = torch.from_numpy(np.asarray(pair_a[start:stop], dtype=np.int64)).to(device)
            b = torch.from_numpy(np.asarray(pair_b[start:stop], dtype=np.int64)).to(device)
            values = torch.minimum(
                similarity_tensor.index_select(0, a), neighbor_tensor.index_select(0, b)
            ).amax(dim=1)
            output[start:stop] = values.cpu().numpy()
    return output


def _commutative(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    denominator = torch.linalg.vector_norm(a, dim=-1) * torch.linalg.vector_norm(b, dim=-1)
    if torch.any(denominator == 0):
        raise RuntimeError("zero vector makes exact model cosine undefined")
    cosine = ((a * b).sum(dim=-1) / denominator).unsqueeze(-1)
    return torch.cat((a + b, torch.abs(a - b), a * b, cosine), dim=-1)


def optimized_checkpoint_scores(
    *,
    family: str,
    state: Mapping[str, torch.Tensor],
    embeddings: torch.Tensor,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
) -> np.ndarray:
    """Eval-mode scorer algebra equal to the frozen Stage 1 modules.

    Endpoint-only affine transforms are cached once per checkpoint; this changes
    no parameter, feature, arithmetic expression, or checkpoint state.
    """

    device = embeddings.device
    output = np.empty(pair_a.size, dtype=np.float32)
    with torch.inference_mode():
        if family in ("lightweight_esm2_150m_linear", "esm2_650m_linear_ablation"):
            projected = gate_value = None
        else:
            projected = F.gelu(
                F.linear(embeddings, state["projection.weight"], state["projection.bias"]),
                approximate="none",
            )
            gate_value = (
                torch.sigmoid(F.linear(projected, state["gate.weight"], state["gate.bias"]))
                if family == "esm2_650m_partner_gated_primary"
                else None
            )
        for start in range(0, pair_a.size, SCORE_BATCH):
            stop = min(start + SCORE_BATCH, pair_a.size)
            a = torch.from_numpy(np.asarray(pair_a[start:stop], dtype=np.int64)).to(device)
            b = torch.from_numpy(np.asarray(pair_b[start:stop], dtype=np.int64)).to(device)
            if family in ("lightweight_esm2_150m_linear", "esm2_650m_linear_ablation"):
                features = _commutative(embeddings.index_select(0, a), embeddings.index_select(0, b))
                score = F.linear(features, state["output.weight"], state["output.bias"]).squeeze(-1)
            else:
                assert projected is not None
                projected_a = projected.index_select(0, a)
                projected_b = projected.index_select(0, b)
                if gate_value is None:
                    conditioned_a, conditioned_b = projected_a, projected_b
                else:
                    conditioned_a = projected_a * gate_value.index_select(0, b)
                    conditioned_b = projected_b * gate_value.index_select(0, a)
                hidden = F.gelu(
                    F.linear(
                        _commutative(conditioned_a, conditioned_b),
                        state["hidden.weight"],
                        state["hidden.bias"],
                    ),
                    approximate="none",
                )
                score = F.linear(hidden, state["output.weight"], state["output.bias"]).squeeze(-1)
            output[start:stop] = score.cpu().numpy()
    if not np.isfinite(output).all():
        raise RuntimeError("selected checkpoint emitted a nonfinite score")
    return output


def scorer_records(training_registry: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    runs = list(training_registry["run_summaries"])
    ensembles = list(training_registry["ensembles"])
    run_ids = [str(item["run_id"]) for item in runs]
    candidate_ids = [str(item["candidate_id"]) for item in ensembles]
    scorer_ids = list(DETERMINISTIC_SCORERS) + run_ids + candidate_ids
    validate_scorer_census(scorer_ids, run_ids=run_ids, candidate_ids=candidate_ids)
    if len(runs) != 30 or any(item.get("status") != "complete" for item in runs):
        raise RuntimeError("training registry selected-run census drift")
    return runs, ensembles, scorer_ids


def score_cell(
    *,
    project_root: Path,
    package_root: Path,
    output_root: Path,
    cell_id: str,
    universe: EndpointUniverse,
    graph: TrainingGraph,
    kmer: sparse.csr_matrix,
    similarities: np.ndarray,
    neighbor_max: np.ndarray,
    training_registry: Mapping[str, Any],
    embedding_paths: Mapping[str, Path],
) -> dict[str, Any]:
    if output_root.exists():
        raise RuntimeError(f"cell score output already exists: {output_root}")
    output_root.mkdir(parents=True, mode=0o700)
    rows = load_cell_rows(package_root, cell_id)
    positive_rows = int(np.count_nonzero(np.asarray(rows["state"].to_pylist()) == "released_positive"))
    if positive_rows <= 0 or rows.num_rows - positive_rows != 1_000_000:
        raise RuntimeError("development cell P/U row census drift")
    deterministic, pair_a, pair_b = deterministic_scores(
        rows, universe=universe, graph=graph, kmer=kmer
    )
    deterministic[:, 8] = score_interolog_gpu(similarities, neighbor_max, pair_a, pair_b)
    runs, ensembles, scorer_ids = scorer_records(training_registry)
    score_path = output_root / "scores.f64.npy"
    score_matrix = np.lib.format.open_memmap(
        score_path, mode="w+", dtype=np.float64, shape=(rows.num_rows, len(scorer_ids))
    )
    score_matrix[:, : len(DETERMINISTIC_SCORERS)] = deterministic
    embedding_cache: dict[str, torch.Tensor] = {}
    run_column: dict[str, int] = {}
    for column, run in enumerate(runs, start=len(DETERMINISTIC_SCORERS)):
        checkpoint_record = run["selected_checkpoint"]
        checkpoint_path = project_root / str(checkpoint_record["path"])
        if checkpoint_path.stat().st_size != int(checkpoint_record["bytes"]) or sha256_file(
            checkpoint_path
        ) != str(checkpoint_record["sha256"]):
            raise RuntimeError("selected checkpoint hash/size drift before scoring")
        config = json.loads((project_root / str(run["run_config_path"])).read_text(encoding="utf-8"))
        if config["run_id"] != run["run_id"] or config["family"] != run["family"]:
            raise RuntimeError("run config identity drift")
        candidate_id = "esm2_150m" if run["family"] == "lightweight_esm2_150m_linear" else "esm2_650m"
        if candidate_id not in embedding_cache:
            matrix = np.load(embedding_paths[candidate_id], mmap_mode="r", allow_pickle=False)
            expected_shape = (17_000, 640 if candidate_id == "esm2_150m" else 1_280)
            if matrix.dtype != np.float32 or matrix.shape != expected_shape:
                raise RuntimeError("standardized embedding matrix identity drift")
            embedding_cache[candidate_id] = torch.from_numpy(np.array(matrix, copy=True)).cuda()
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if int(checkpoint["pass_index"]) != 5 or int(checkpoint["global_step"]) != 2_445:
            raise RuntimeError("selected checkpoint cursor drift")
        state = {name: value.cuda() for name, value in checkpoint["model_state"].items()}
        score_matrix[:, column] = optimized_checkpoint_scores(
            family=str(run["family"]),
            state=state,
            embeddings=embedding_cache[candidate_id],
            pair_a=pair_a,
            pair_b=pair_b,
        )
        run_column[str(run["run_id"])] = column
    for offset, ensemble in enumerate(ensembles, start=len(DETERMINISTIC_SCORERS) + len(runs)):
        member_columns = [run_column[str(member["run_id"])] for member in ensemble["members"]]
        if len(member_columns) != 3:
            raise RuntimeError("ensemble does not contain exactly three frozen seed runs")
        score_matrix[:, offset] = np.mean(score_matrix[:, member_columns], axis=1, dtype=np.float64)
    score_matrix.flush()
    if not np.isfinite(np.asarray(score_matrix)).all():
        raise RuntimeError("development score matrix contains a nonfinite value")
    rows_path = output_root / "rows.parquet"
    pq.write_table(rows, rows_path, compression="zstd", use_dictionary=True, write_statistics=True)
    scorer_path = output_root / "SCORERS.json"
    _atomic_json(
        scorer_path,
        {
            "schema_version": 1,
            "cell_id": cell_id,
            "scorers": [
                {"column": column, "scorer_id": scorer_id}
                for column, scorer_id in enumerate(scorer_ids)
            ],
        },
    )
    manifest = {
        "schema_version": 1,
        "cell_id": cell_id,
        "positive_rows": positive_rows,
        "unlabeled_rows": rows.num_rows - positive_rows,
        "total_rows": rows.num_rows,
        "scorer_count": len(scorer_ids),
        "score_shape": [rows.num_rows, len(scorer_ids)],
        "score_dtype": "float64",
        "rows": {"path": "rows.parquet", "bytes": rows_path.stat().st_size, "sha256": sha256_file(rows_path)},
        "scores": {"path": "scores.f64.npy", "bytes": score_path.stat().st_size, "sha256": sha256_file(score_path)},
        "scorers": {"path": "SCORERS.json", "bytes": scorer_path.stat().st_size, "sha256": sha256_file(scorer_path)},
        "protected_candidates_accessed": False,
        "protected_truth_accessed": False,
        "training_or_checkpoint_change": False,
    }
    _atomic_json(output_root / "CELL_SCORE_MANIFEST.json", manifest)
    return manifest


def build_kmer_matrix(universe: EndpointUniverse) -> sparse.csr_matrix:
    matrix = kmer3_csr(universe.sequences)
    if matrix.shape != (17_000, 21**3) or matrix.dtype != np.float64:
        raise RuntimeError("frozen contiguous 3-mer matrix drift")
    norms = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
    if np.any(np.abs(norms - 1.0) > 1e-12):
        raise RuntimeError("normalized 3-mer vector norm drift")
    return matrix


def configure_scoring_runtime() -> None:
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise RuntimeError("development scoring must run offline")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("development scoring requires exactly one visible CUDA device")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
