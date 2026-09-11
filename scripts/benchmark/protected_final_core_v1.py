"""Frozen one-attempt comparison harness. All row-bearing output is private."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from scipy import sparse
import torch
import torch.nn.functional as F


PACKAGE = "pair_level_pu_r_benchmark_artifacts_v1"
MODEL = "lightweight_esm2_150m_linear__linear_lr3e-4"
SEEDS = (20260803, 20260817, 20260831)
BASELINES = ("deterministic_hash", "training_degree_sum", "preferential_attachment",
             "component_degree_mass_product", "training_common_neighbors",
             "sequence_length_sum", "sequence_length_ratio", "within_pair_3mer_cosine",
             "exact_training_interolog_3mer", "pooled_150m_cosine", "aac_cosine")
SCORERS = (MODEL,) + tuple(f"seed{seed}" for seed in SEEDS) + BASELINES
CELLS = tuple(cell for c in (3, 2, 1) for cell in
              (f"C{c}_test", f"source_exclusive:HI-II-14:C{c}_test",
               f"source_exclusive:HuRI:C{c}_test"))
P_COUNTS = dict(zip(CELLS, (2379, 269, 1869, 13446, 1488, 5270, 3187, 280, 633)))
U_ROWS = 1_000_000
COLUMNS = ("candidate_token", "endpoint_a_sha256", "endpoint_b_sha256", "cell_id")


def sha(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def write_new(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def record(path: Path, root: Path) -> dict:
    return {"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha(path)}


def verify_records(root: Path, records) -> None:
    for item in records:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("Unsafe manifest path")
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise RuntimeError("Frozen artifact drift")


def verify_bundle(bundle: Path) -> dict:
    manifest = read(bundle / "SCORER_FREEZE.json")
    if manifest["model"] != MODEL or manifest["scorers"] != list(SCORERS) or manifest["cells"] != list(CELLS):
        raise RuntimeError("Frozen scorer/cell census drift")
    verify_records(bundle, manifest["files"])
    return manifest


def cell_path(root: Path, cell: str) -> Path:
    if cell not in CELLS:
        raise RuntimeError("Unexpected protected cell")
    return root / f"cell-{CELLS.index(cell):02d}.parquet"


def pair_identifier(a: str, b: str) -> str:
    if a == b:
        raise RuntimeError("Self-pair")
    return "pair:" + hashlib.sha256("|".join(sorted((a, b))).encode()).hexdigest()


def token_for(cell: str, pair: str) -> str:
    return "candidate:" + hashlib.sha256(f"{PACKAGE}:{cell}:{pair}".encode()).hexdigest()


def decrypt(role: str, manifest: dict, target: Path, *, cipher=Path("/cipher.cms"), cert=Path("/certificate.pem"), key=Path("/key.pem")) -> None:
    item = manifest["sealed_packages"][role]
    if sha(cipher) != item["ciphertext_sha256"] or sha(cert) != item["certificate_sha256"]:
        raise RuntimeError("Sealed input integrity failure")
    archive = target / "archive.tar"
    subprocess.run(["openssl", "cms", "-decrypt", "-binary", "-inform", "DER",
                    "-in", str(cipher), "-recip", str(cert), "-inkey", str(key),
                    "-out", str(archive)], check=True, capture_output=True)
    if sha(archive) != item["plaintext_archive_sha256"]:
        raise RuntimeError("Plaintext archive integrity failure")
    with tarfile.open(archive, "r:") as handle:
        for member in handle.getmembers():
            p = Path(member.name)
            if p.is_absolute() or ".." in p.parts or not (member.isfile() or member.isdir()):
                raise RuntimeError("Unsafe archive entry")
        # Authenticated archive; filter and explicit checks prohibit links/devices.
        handle.extractall(target / "plain", filter="data")


def open_candidates(bundle: Path, output: Path) -> None:
    manifest = verify_bundle(bundle)
    destination = output / "candidates"
    destination.mkdir(mode=0o700, exist_ok=False)
    records, seen_cells = [], set()
    with tempfile.TemporaryDirectory(prefix="candidate-decrypt-", dir=output) as temp:
        workspace = Path(temp)
        decrypt("protected_candidates", manifest, workspace)
        for path in sorted((workspace / "plain/protected_candidates").glob("part-*.parquet")):
            rows = pq.read_table(path, columns=list(COLUMNS))
            values = set(rows["cell_id"].to_pylist())
            if len(values) != 1:
                raise RuntimeError("Mixed candidate part")
            cell = values.pop()
            if cell in seen_cells or cell not in CELLS or rows.num_rows != U_ROWS + P_COUNTS[cell]:
                raise RuntimeError("Candidate census drift")
            seen_cells.add(cell)
            tokens = rows["candidate_token"]
            if tokens.null_count or pc.count_distinct(tokens).as_py() != rows.num_rows:
                raise RuntimeError("Invalid candidate tokens")
            target = cell_path(destination, cell)
            pq.write_table(rows, target, compression="zstd")
            records.append({**record(target, output), "cell_id": cell, "rows": rows.num_rows})
    if seen_cells != set(CELLS):
        raise RuntimeError("Incomplete candidate cells")
    write_new(output / "SCORING_SESSION.json", {
        "package_id": PACKAGE, "scorer_freeze_sha256": sha(bundle / "SCORER_FREEZE.json"),
        "candidate_archive_sha256": manifest["sealed_packages"]["protected_candidates"]["plaintext_archive_sha256"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "truth_accessed": False,
        "unprojected_candidate_metadata_retained": False, "columns": list(COLUMNS), "files": records})
    write_new(output / "SCORING_SESSION_HASH.json", {"sha256": sha(output / "SCORING_SESSION.json")})


def session_check(bundle: Path, session: Path) -> dict:
    verify_bundle(bundle)
    if sha(session / "SCORING_SESSION.json") != read(session / "SCORING_SESSION_HASH.json")["sha256"]:
        raise RuntimeError("Session hash drift")
    payload = read(session / "SCORING_SESSION.json")
    if payload["scorer_freeze_sha256"] != sha(bundle / "SCORER_FREEZE.json") or payload["truth_accessed"] or payload["unprojected_candidate_metadata_retained"] or payload["columns"] != list(COLUMNS):
        raise RuntimeError("Invalid scoring session")
    verify_records(session, payload["files"])
    return payload


def head_scores(z: np.ndarray, parameters, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    tensor = torch.from_numpy(z)
    values = np.empty((a.size, 3), np.float64)
    with torch.inference_mode():
        for start in range(0, a.size, 8192):
            stop = min(start + 8192, a.size)
            x, y = tensor[a[start:stop]], tensor[b[start:stop]]
            denominator = torch.linalg.vector_norm(x, dim=-1) * torch.linalg.vector_norm(y, dim=-1)
            if torch.any(denominator <= 0):
                raise RuntimeError("Undefined frozen head cosine")
            cosine = ((x * y).sum(dim=-1) / denominator).unsqueeze(-1)
            features = torch.cat((x + y, torch.abs(x - y), x * y, cosine), dim=-1)
            for index, (weight, bias) in enumerate(parameters):
                values[start:stop, index] = F.linear(features, torch.from_numpy(weight), torch.from_numpy(bias)).squeeze(-1).numpy()
    return values


def interolog(sim, neighbor, a, b):
    result = np.empty(a.size, np.float64)
    for start in range(0, a.size, 512):
        stop = min(start + 512, a.size)
        result[start:stop] = np.minimum(sim[a[start:stop]], neighbor[b[start:stop]]).max(axis=1)
    return result


class Scorer:
    def __init__(self, bundle: Path):
        root = bundle / "features"
        self.ids = read(root / "endpoints.json")
        self.index = {value: i for i, value in enumerate(self.ids)}
        self.z = np.load(root / "standardized.npy", allow_pickle=False)
        self.pooled = np.load(root / "pooled_unit.npy", allow_pickle=False)
        self.aac = np.load(root / "aac_unit.npy", allow_pickle=False)
        self.degree = np.load(root / "degree.npy", allow_pickle=False)
        self.mass = np.load(root / "component_mass.npy", allow_pickle=False)
        self.length = np.load(root / "length.npy", allow_pickle=False)
        self.adjacency = sparse.load_npz(root / "adjacency.npz")
        self.kmer = sparse.load_npz(root / "kmer.npz")
        self.sim = np.load(root / "similarities.npy", allow_pickle=False)
        self.neighbor = np.load(root / "neighbor.npy", allow_pickle=False)
        self.parameters = []
        for seed in SEEDS:
            with np.load(root / f"head_{seed}.npz", allow_pickle=False) as p:
                self.parameters.append((p["weight"].copy(), p["bias"].copy()))

    def score(self, rows, swap=False):
        left = rows["endpoint_b_sha256" if swap else "endpoint_a_sha256"].to_pylist()
        right = rows["endpoint_a_sha256" if swap else "endpoint_b_sha256"].to_pylist()
        a = np.array([self.index[x] for x in left], dtype=np.int64)
        b = np.array([self.index[x] for x in right], dtype=np.int64)
        output = np.empty((rows.num_rows, len(SCORERS)), np.float64)
        output[:, 1:4] = head_scores(self.z, self.parameters, a, b)
        output[:, 0] = output[:, 1:4].mean(axis=1, dtype=np.float64)
        for i, (x, y) in enumerate(zip(left, right, strict=True)):
            pair = pair_identifier(x, y)
            output[i, 4] = int.from_bytes(hashlib.sha256(f"ipin-openppi-pu-r-baseline-v1:20260803:baseline:{pair}".encode()).digest(), "big") / (2**256 - 1)
        da, db = self.degree[a], self.degree[b]
        output[:, 5] = np.log1p(da) + np.log1p(db)
        output[:, 6] = np.log1p(da * db)
        output[:, 7] = np.log1p(self.mass[a] * self.mass[b])
        output[:, 9] = np.log1p(self.length[a]) + np.log1p(self.length[b])
        output[:, 10] = -np.abs(np.log1p(self.length[a]) - np.log1p(self.length[b]))
        for start in range(0, a.size, 8192):
            stop = min(start + 8192, a.size)
            aa, bb = a[start:stop], b[start:stop]
            output[start:stop, 8] = np.log1p(np.asarray(self.adjacency[aa].multiply(self.adjacency[bb]).sum(axis=1)).ravel())
            output[start:stop, 11] = np.asarray(self.kmer[aa].multiply(self.kmer[bb]).sum(axis=1)).ravel()
            output[start:stop, 13] = np.einsum("ij,ij->i", self.pooled[aa], self.pooled[bb])
            output[start:stop, 14] = np.einsum("ij,ij->i", self.aac[aa], self.aac[bb])
        output[:, 12] = interolog(self.sim, self.neighbor, a, b)
        if not np.isfinite(output).all():
            raise RuntimeError("Nonfinite score")
        return output


def score_all(bundle: Path, session: Path, output: Path) -> None:
    session_check(bundle, session)
    scorer = Scorer(bundle)
    records, symmetry = [], {}
    for cell in CELLS:
        rows = pq.read_table(cell_path(session / "candidates", cell))
        if tuple(rows.column_names) != COLUMNS:
            raise RuntimeError("Scorer input schema drift")
        # Full token recomputation catches identity, cell and cross-cell duplication.
        expected = [token_for(cell, pair_identifier(a, b)) for a, b in
                    zip(rows["endpoint_a_sha256"].to_pylist(), rows["endpoint_b_sha256"].to_pylist(), strict=True)]
        if rows["candidate_token"].to_pylist() != expected:
            raise RuntimeError("Candidate identity mismatch")
        values = scorer.score(rows)
        # Fixed label-blind prefix of opaque-token-sorted input, not metric-selected.
        reverse = scorer.score(rows.slice(0, 128), swap=True)
        error = float(np.max(np.abs(values[:128] - reverse)))
        if error > 1e-6:
            raise RuntimeError("Swap symmetry failure")
        symmetry[cell] = error
        for index, scorer_id in enumerate(SCORERS):
            path = cell_path(output / scorer_id, cell)
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if path.exists():
                raise RuntimeError("Refuse prediction overwrite")
            pq.write_table(pa.table({"candidate_token": rows["candidate_token"], "score": values[:, index]}), path, compression="zstd")
            records.append({**record(path, output), "cell_id": cell, "scorer_id": scorer_id})
        print(json.dumps({"cell_scoring_complete": cell}), flush=True)
    write_new(output / "PREDICTIONS.json", {"files": records, "symmetry_max_abs": symmetry,
              "session_sha256": sha(session / "SCORING_SESSION.json"), "truth_accessed": False})


def validate_predictions(tokens, table):
    if table.column_names != ["candidate_token", "score"] or table.num_rows != len(tokens):
        raise RuntimeError("Prediction schema or row census drift")
    actual = table["candidate_token"]
    if actual.null_count or pc.count_distinct(actual).as_py() != table.num_rows:
        raise RuntimeError("Duplicate or null prediction tokens")
    position = pc.index_in(tokens, value_set=actual)
    if position.null_count:
        raise RuntimeError("Missing or unknown prediction tokens")
    scores = np.asarray(table["score"].take(position).to_numpy(), dtype=np.float64)
    if not np.isfinite(scores).all():
        raise RuntimeError("Nonfinite predictions")
    return scores


def freeze_predictions(bundle, session, predictions, output):
    session_check(bundle, session)
    manifest = read(predictions / "PREDICTIONS.json")
    verify_records(predictions, manifest["files"])
    expected = {(cell, scorer) for cell in CELLS for scorer in SCORERS}
    observed = [(r["cell_id"], r["scorer_id"]) for r in manifest["files"]]
    if len(observed) != len(expected) or set(observed) != expected or manifest["truth_accessed"] or manifest["session_sha256"] != sha(session / "SCORING_SESSION.json"):
        raise RuntimeError("Prediction manifest coverage drift")
    for cell in CELLS:
        tokens = pq.read_table(cell_path(session / "candidates", cell), columns=["candidate_token"])["candidate_token"]
        for scorer in SCORERS:
            validate_predictions(tokens, pq.read_table(cell_path(predictions / scorer, cell)))
    if set(manifest["symmetry_max_abs"]) != set(CELLS) or any(x > 1e-6 for x in manifest["symmetry_max_abs"].values()):
        raise RuntimeError("Symmetry audit drift")
    write_new(output / "PREDICTION_FREEZE.json", {
        "package_id": PACKAGE, "scorer_freeze_sha256": sha(bundle / "SCORER_FREEZE.json"),
        "prediction_manifest_sha256": sha(predictions / "PREDICTIONS.json"),
        "session_sha256": sha(session / "SCORING_SESSION.json"), "files": manifest["files"],
        "validated_at_utc": datetime.now(timezone.utc).isoformat(), "truth_accessed": False,
        "complete_unique_finite_two_column_coverage": True, "symmetry_max_abs": manifest["symmetry_max_abs"]})


def reserve_attempt(bundle, freeze, ledger):
    verify_bundle(bundle)
    frozen = read(freeze / "PREDICTION_FREEZE.json")
    if frozen["scorer_freeze_sha256"] != sha(bundle / "SCORER_FREEZE.json") or frozen["truth_accessed"] or not frozen["complete_unique_finite_two_column_coverage"]:
        raise RuntimeError("Invalid prediction freeze before reservation")
    if (ledger.parent / "protected_evaluation_completion.json").exists():
        raise RuntimeError("Package already has completed final evaluation")
    write_new(ledger, {
        "schema_version": 2, "package_id": PACKAGE, "execution_id": "protected_final_test_v1",
        "reserved_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "one_first_attempt_reserved_before_truth_access",
        "scoring_artifact_sha256": sha(bundle / "SCORER_FREEZE.json"),
        "prediction_artifact_sha256": frozen["prediction_manifest_sha256"],
        "prediction_freeze_sha256": sha(freeze / "PREDICTION_FREEZE.json"),
        "prediction_hashed_before_truth_access": True,
        "truth_access_attempt_irrevocably_consumed": True})


def bootstrap_metrics(scores, positive, weights, component_a, component_b, cell, replicates=2000, workers=4):
    """Sort once per scorer; exact ties and paired frozen component draws."""
    components = sorted(set(component_a) | set(component_b))
    index = {x: i for i, x in enumerate(components)}
    a = np.array([index[x] for x in component_a], np.int64)
    b = np.array([index[x] for x in component_b], np.int64)
    seed = int.from_bytes(hashlib.sha256(f"20260803:bootstrap:{cell}".encode()).digest()[:8], "big")
    generator = np.random.Generator(np.random.PCG64DXSM(seed))
    draws = generator.integers(0, len(components), (replicates, len(components)), dtype=np.int64)
    counts = np.zeros((replicates, len(components)), np.int32)
    np.add.at(counts, (np.arange(replicates)[:, None], draws), 1)
    mask = np.asarray(positive, bool)
    p_a, p_b, u_a, u_b = a[mask], b[mask], a[~mask], b[~mask]
    design = np.asarray(weights, np.float64)[~mask]
    if not mask.any() or mask.all() or np.any(design <= 0) or not np.isfinite(scores).all() or not np.isfinite(design).all():
        raise RuntimeError("Invalid metric inputs")

    def one(column):
        p, u = scores[mask, column], scores[~mask, column]
        order = np.argsort(u, kind="mergesort")
        left, right = np.searchsorted(u[order], p, "left"), np.searchsorted(u[order], p, "right")
        ua, ub, w = u_a[order], u_b[order], design[order]
        same = ua == ub
        prefix = np.concatenate(([0.0], np.cumsum(w, dtype=np.float64)))
        point = float(np.mean((prefix[left] + prefix[right]) * 0.5) / prefix[-1])
        result = np.full(replicates, np.nan, np.float64)
        for r, count in enumerate(counts):
            pm = np.where(p_a == p_b, count[p_a], count[p_a] * count[p_b])
            um = np.where(same, count[ua], count[ua] * count[ub])
            prefix = np.concatenate(([0.0], np.cumsum(w * um, dtype=np.float64)))
            if pm.sum() > 0 and prefix[-1] > 0:
                result[r] = np.dot(pm, (prefix[left] + prefix[right]) * 0.5) / (pm.sum() * prefix[-1])
        return point, result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one, range(scores.shape[1])))
    return np.array([x[0] for x in results]), np.array([x[1] for x in results]), {
        "seed": seed, "replicates": replicates, "participating_components": len(components),
        "multiplicities_sha256": hashlib.sha256(counts.astype("<i4").tobytes()).hexdigest()}


def evaluate(bundle, session, predictions, freeze, output):
    manifest = verify_bundle(bundle)
    session_check(bundle, session)
    frozen = read(freeze / "PREDICTION_FREEZE.json")
    if frozen["prediction_manifest_sha256"] != sha(predictions / "PREDICTIONS.json") or frozen["scorer_freeze_sha256"] != sha(bundle / "SCORER_FREEZE.json"):
        raise RuntimeError("Prediction freeze drift")
    verify_records(predictions, frozen["files"])
    ledger = read(Path("/ledger.json"))
    if ledger["prediction_freeze_sha256"] != sha(freeze / "PREDICTION_FREEZE.json") or ledger["package_id"] != PACKAGE or not ledger["truth_access_attempt_irrevocably_consumed"]:
        raise RuntimeError("Missing valid one-first reservation")
    endpoint_ids = read(bundle / "features/endpoints.json")
    component_ids = read(bundle / "features/components.json")
    component = dict(zip(endpoint_ids, component_ids, strict=True))
    summaries = {}
    with tempfile.TemporaryDirectory(prefix="truth-decrypt-", dir=output) as temp:
        workspace = Path(temp)
        decrypt("protected_truth", manifest, workspace)
        root = workspace / "plain"
        positives = ds.dataset(root / "protected_positive_truth", format="parquet")
        unlabeled = ds.dataset(root / "unlabeled_pairs", format="parquet")
        for cell in CELLS:
            rows = pq.read_table(cell_path(session / "candidates", cell))
            tokens = rows["candidate_token"]
            p = positives.to_table(columns=["candidate_token", "state"], filter=ds.field("cell_id") == cell)
            u = unlabeled.to_table(columns=["pair_id", "sampling_weight_numerator", "sampling_weight_denominator", "state"], filter=ds.field("cell_id") == cell)
            if p.num_rows != P_COUNTS[cell] or u.num_rows != U_ROWS or set(p["state"].to_pylist()) != {"released_positive"} or set(u["state"].to_pylist()) != {"unlabeled"}:
                raise RuntimeError("Truth census/state drift")
            ut = pa.array([token_for(cell, pair) for pair in u["pair_id"].to_pylist()])
            all_tokens = pa.concat_arrays([p["candidate_token"].combine_chunks(), ut])
            if pc.count_distinct(all_tokens).as_py() != rows.num_rows:
                raise RuntimeError("Truth overlap or duplicate")
            positions = pc.index_in(all_tokens, value_set=tokens)
            if positions.null_count:
                raise RuntimeError("Truth outside scoring session")
            scores = np.column_stack([validate_predictions(all_tokens, pq.read_table(cell_path(predictions / scorer, cell))) for scorer in SCORERS])
            ordered = rows.take(positions)
            ca = [component[x] for x in ordered["endpoint_a_sha256"].to_pylist()]
            cb = [component[x] for x in ordered["endpoint_b_sha256"].to_pylist()]
            numerator, denominator = u["sampling_weight_numerator"].to_numpy(), u["sampling_weight_denominator"].to_numpy()
            if np.any(numerator <= 0) or np.any(denominator <= 0):
                raise RuntimeError("Invalid rational U weights")
            weights = np.concatenate((np.ones(p.num_rows), numerator.astype(np.float64) / denominator))
            mask = np.arange(rows.num_rows) < p.num_rows
            points, draws, metadata = bootstrap_metrics(scores, mask, weights, ca, cb, cell)
            metrics, differences = {}, {}
            for i, scorer in enumerate(SCORERS):
                finite = np.isfinite(draws[i])
                interval = np.percentile(draws[i, finite], (2.5, 97.5)).tolist() if finite.any() else None
                metrics[scorer] = {"ht_P_vs_U_concordance": float(points[i]), "percentile_95": interval, "finite_bootstrap_draws": int(finite.sum())}
                if scorer in BASELINES:
                    valid = finite & np.isfinite(draws[0])
                    ci = np.percentile((draws[0] - draws[i])[valid], (2.5, 97.5)).tolist() if valid.any() else None
                    differences[scorer] = {"model_minus_control": float(points[0] - points[i]), "paired_percentile_95": ci,
                                           "finite_paired_draws": int(valid.sum()), "positive_lower_bound": bool(valid.sum() >= 1900 and ci and ci[0] > 0)}
            summaries[cell] = {"positive_pairs": p.num_rows, "sampled_unlabeled_pairs": u.num_rows,
                               "metrics": metrics, "model_minus_controls": differences, "bootstrap": metadata,
                               "seed_concordance_range": float(np.ptp(points[1:4])),
                               "above_every_control_with_positive_paired_lower_bound": all(x["positive_lower_bound"] for x in differences.values())}
            # Private per-cell checkpoint, never used to retune or resume truth.
            write_new(output / f"aggregate-cell-{CELLS.index(cell):02d}.json", summaries[cell])
            print(json.dumps({"cell_metrics_complete": cell}), flush=True)
    write_new(output / "FINAL_TEST_RESULTS.json", {
        "execution_id": "protected_final_test_v1", "package_id": PACKAGE, "model": MODEL,
        "primary_cell": "C3_test", "cells": summaries, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scorer_freeze_sha256": sha(bundle / "SCORER_FREEZE.json"), "prediction_freeze_sha256": sha(freeze / "PREDICTION_FREEZE.json"),
        "ledger_sha256": sha(Path("/ledger.json")), "protected_candidate_or_truth_identity_public": False,
        "network_isolation_enforced": True, "prediction_hashed_before_truth": True, "one_first_attempt": True,
        "U_is_not_negative": True, "no_full_universe_rank_or_probability_claim": True, "no_test_tuning": True})


if __name__ == "__main__":
    if os.environ.get("IPIN_EVALUATOR_NETWORK_ISOLATED") != "1":
        raise RuntimeError("Restricted launcher required")
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    role = sys.argv[1]
    if role == "open":
        open_candidates(Path("/bundle"), Path("/output"))
    elif role == "score":
        score_all(Path("/bundle"), Path("/session"), Path("/output"))
    elif role == "freeze-predictions":
        freeze_predictions(Path("/bundle"), Path("/session"), Path("/predictions"), Path("/output"))
    elif role == "evaluate":
        evaluate(Path("/bundle"), Path("/session"), Path("/predictions"), Path("/freeze"), Path("/output"))
    elif role == "reserve":
        reserve_attempt(Path("/bundle"), Path("/freeze"), Path("/custody/protected_evaluation_ledger.json"))
    elif role == "qualify":
        verify_bundle(Path("/bundle"))
        scorer = Scorer(Path("/bundle"))
        rows = pq.read_table("/bundle/features/public_training_fixture.parquet")
        values = scorer.score(rows)
        swapped = scorer.score(rows, swap=True)
        reference = np.load("/bundle/features/public_training_fixture_reference.npy", allow_pickle=False)
        error = float(np.max(np.abs(values[:, 1:4] - reference)))
        symmetry = float(np.max(np.abs(values - swapped)))
        if error > 1e-6 or symmetry > 1e-6:
            raise RuntimeError("Restricted public-fixture scorer qualification failed")
        write_new(Path("/output/SCORER_QUALIFICATION.json"), {"pass": True, "public_training_fixture_rows": rows.num_rows,
                  "CPU_reference_max_abs": error, "all_scorer_swap_max_abs": symmetry,
                  "protected_candidates_accessed": False, "protected_truth_accessed": False})
    else:
        raise RuntimeError("Unknown final evaluation role")
