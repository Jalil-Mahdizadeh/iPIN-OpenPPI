"""One fixed-ensemble follow-up; reuse frozen primitives without changing them.

Only this version's staged launcher may access protected rows. Original v1
source, predictions, result and spent ledger are never written by this module.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protected_final_core_v1 as original

if Path(__file__).with_name("optimization_models_v1.py").exists():
    import optimization_models_v1 as models
else:
    from ipin_openppi.model_optimization import models

sha, read, write_new = original.sha, original.read, original.write_new
record, verify_records = original.record, original.verify_records
decrypt, validate_predictions = original.decrypt, original.validate_predictions
pair_identifier, token_for = original.pair_identifier, original.token_for
bootstrap_metrics = original.bootstrap_metrics
PACKAGE, CELLS, P_COUNTS, U_ROWS, COLUMNS = (
    original.PACKAGE, original.CELLS, original.P_COUNTS, original.U_ROWS, original.COLUMNS)
SEEDS = original.SEEDS
EXECUTION = "model_optimization_followup_v1"
RECIPE = "esm2_150m__residual_wide"
MODEL = RECIPE + "__epoch04_ensemble3"
BASELINE = original.MODEL
CANDIDATE_SCORERS = (MODEL,) + tuple(f"candidate_seed{s}" for s in SEEDS)
BASELINE_SCORERS = (BASELINE,) + tuple(f"baseline_seed{s}" for s in SEEDS)
SCORERS = CANDIDATE_SCORERS + BASELINE_SCORERS
ORIGINAL_SCORERS = (BASELINE,) + tuple(f"seed{s}" for s in SEEDS)
SPEC = {"family": "residual_mlp", "width": 256, "dropout": .3}
SEARCH_SHA = "c321841b6d79f4ca4256f14f9f7463a5bf3b5dc0085cfa554a1dc3ba4c906f67"
SELECTION_SHA = "3a4fe7e5a960a6798638ca84cf2433b2fa195c3dfeccd680986ee15ef0ea2ce6"
CHECKPOINT_SHAS = (
    "f46452e84cb30df1c785a6af982f83d37ba892855b5af0a848aac4610890cabc",
    "08a67b0309a2d3d2928c9f188f73180a4e917f457a087ea1206c85bbae828463",
    "2f5fbe82194f88b8afb6ce90c8db1b1b2ed87cd1d03484ffec0375e2774c17f1")
ORIGINAL_LEDGER_SHA = "e23a6a8980d3e9d148a40be8e9b3d1316ff1c2c6ed8f7f03ab2bd899b777914f"
ORIGINAL_RESULT_SHA = "6cc8c3ba61039501b3e1b09dfcee442de8f4dfcd0c717a466b15f9e77ef3a02e"


def now():
    return datetime.now(timezone.utc).isoformat()


def cell_path(root, cell):
    if cell not in CELLS:
        raise RuntimeError("Unexpected follow-up cell")
    return root / f"cell-{CELLS.index(cell):02d}.parquet"


def verify_bundle(bundle):
    manifest = read(bundle / "SCORER_FREEZE.json")
    if (manifest["execution_id"] != EXECUTION or manifest["model"] != MODEL
            or manifest["scorers"] != list(SCORERS) or manifest["cells"] != list(CELLS)
            or manifest["search_freeze_sha256"] != SEARCH_SHA
            or manifest["selection_sha256"] != SELECTION_SHA
            or manifest["original_ledger_sha256"] != ORIGINAL_LEDGER_SHA
            or manifest["original_result_sha256"] != ORIGINAL_RESULT_SHA
            or manifest["checkpoint_sha256"] != list(CHECKPOINT_SHAS)):
        raise RuntimeError("Frozen follow-up identity drift")
    verify_records(bundle, manifest["files"])
    acceptance = read(bundle / "provenance/ENSEMBLE_ACCEPTANCE.json")
    if (acceptance["accepted_for_one_followup"] is not True
            or acceptance["original_gate_passed"] is not False
            or acceptance["authorization"] != "DEC-0053"
            or sha(bundle / "provenance/ENSEMBLE_ACCEPTANCE.json") != manifest["acceptance_sha256"]):
        raise RuntimeError("Invalid ensemble-level authorization")
    return manifest


def open_candidates(bundle, output):
    manifest = verify_bundle(bundle)
    destination = output / "candidates"
    destination.mkdir(mode=0o700, exist_ok=False)
    records, seen = [], set()
    with tempfile.TemporaryDirectory(prefix="candidate-decrypt-", dir=output) as temp:
        workspace = Path(temp)
        decrypt("protected_candidates", manifest, workspace)
        for path in sorted((workspace / "plain/protected_candidates").glob("part-*.parquet")):
            rows = pq.read_table(path, columns=list(COLUMNS))
            cells = set(rows["cell_id"].to_pylist())
            if len(cells) != 1:
                raise RuntimeError("Mixed candidate cell")
            cell = cells.pop()
            if cell not in CELLS or cell in seen or rows.num_rows != P_COUNTS[cell] + U_ROWS:
                raise RuntimeError("Candidate census drift")
            if any(rows[name].null_count for name in COLUMNS):
                raise RuntimeError("Null candidate identity")
            if pc.count_distinct(rows["candidate_token"]).as_py() != rows.num_rows:
                raise RuntimeError("Duplicate candidate tokens")
            seen.add(cell)
            path = cell_path(destination, cell)
            pq.write_table(rows, path, compression="zstd")
            records.append({**record(path, output), "cell_id": cell, "rows": rows.num_rows})
    if seen != set(CELLS):
        raise RuntimeError("Missing candidate cells")
    write_new(output / "SCORING_SESSION.json", {
        "execution_id": EXECUTION, "scorer_freeze_sha256": sha(bundle / "SCORER_FREEZE.json"),
        "created_at_utc": now(), "truth_accessed": False, "columns": list(COLUMNS), "files": records})
    write_new(output / "SCORING_SESSION_HASH.json", {"sha256": sha(output / "SCORING_SESSION.json")})


def session_check(bundle, session):
    verify_bundle(bundle)
    payload = read(session / "SCORING_SESSION.json")
    if (sha(session / "SCORING_SESSION.json") != read(session / "SCORING_SESSION_HASH.json")["sha256"]
            or payload["execution_id"] != EXECUTION or payload["truth_accessed"] is not False
            or payload["scorer_freeze_sha256"] != sha(bundle / "SCORER_FREEZE.json")
            or payload["columns"] != list(COLUMNS)):
        raise RuntimeError("Invalid follow-up scoring session")
    observed = [(r["cell_id"], r["path"], r["rows"]) for r in payload["files"]]
    expected = [(c, str(cell_path(Path("candidates"), c)), U_ROWS + P_COUNTS[c]) for c in CELLS]
    if sorted(observed) != sorted(expected):
        raise RuntimeError("Session file census drift")
    verify_records(session, payload["files"])


class Scorer:
    def __init__(self, bundle, device="cpu"):
        root = bundle / "features"
        ids = read(root / "endpoints.json")
        if len(set(ids)) != len(ids):
            raise RuntimeError("Duplicate endpoint identity")
        self.index = {x: i for i, x in enumerate(ids)}
        self.device = torch.device(device)
        matrix = np.load(root / "standardized.npy", allow_pickle=False)
        if matrix.shape != (len(ids), 640) or matrix.dtype != np.float32:
            raise RuntimeError("Frozen embedding shape or dtype drift")
        if not np.isfinite(matrix).all() or np.any(np.linalg.norm(matrix, axis=1) <= 0):
            raise RuntimeError("Invalid endpoint embeddings")
        self.z = torch.from_numpy(matrix).to(self.device)
        self.heads = []
        for seed in SEEDS:
            head = models.PairHead(640, SPEC)
            models.load_state(root / f"candidate_{seed}.npz", head)
            if sum(p.numel() for p in head.parameters()) != 498053:
                raise RuntimeError("Selected parameter census drift")
            if not all(torch.isfinite(p).all() for p in head.parameters()):
                raise RuntimeError("Nonfinite checkpoint")
            self.heads.append(head.to(self.device).eval())

    def score_indices(self, a, b):
        if a.shape != b.shape or a.ndim != 1 or np.any(a == b):
            raise RuntimeError("Invalid score indices")
        values = np.empty((len(a), 4), np.float64)
        with torch.inference_mode():
            for start in range(0, len(a), 8192):
                stop = min(start + 8192, len(a))
                x, y = self.z[a[start:stop]], self.z[b[start:stop]]
                for j, head in enumerate(self.heads, 1):
                    values[start:stop, j] = head(x, y).cpu().numpy()
        values[:, 0] = values[:, 1:4].mean(axis=1, dtype=np.float64)
        if not np.isfinite(values).all():
            raise RuntimeError("Nonfinite candidate predictions")
        return values

    def score(self, rows, swap=False):
        if tuple(rows.column_names) != COLUMNS:
            raise RuntimeError("Candidate scorer input schema drift")
        a = np.array([self.index[x] for x in rows["endpoint_a_sha256"].to_pylist()], np.int64)
        b = np.array([self.index[x] for x in rows["endpoint_b_sha256"].to_pylist()], np.int64)
        return self.score_indices(b, a) if swap else self.score_indices(a, b)


def score_all(bundle, session, output):
    session_check(bundle, session)
    write_new(output / "SCORING_STARTED.json", {"at_utc": now(), "truth_accessed": False})
    scorer = Scorer(bundle)
    records, symmetry = [], {}
    for cell in CELLS:
        rows = pq.read_table(cell_path(session / "candidates", cell))
        expected = [token_for(cell, pair_identifier(a, b)) for a, b in zip(
            rows["endpoint_a_sha256"].to_pylist(), rows["endpoint_b_sha256"].to_pylist(), strict=True)]
        if rows["candidate_token"].to_pylist() != expected:
            raise RuntimeError("Candidate pair/token/cell identity mismatch")
        scores = scorer.score(rows)
        # Use one unchanged production-sized batch so this tests swapping,
        # not a change of BLAS reduction kernel induced by batch shape.
        swapped = scorer.score(rows.slice(0, min(8192, rows.num_rows)), swap=True)
        error = float(np.max(np.abs(scores[:len(swapped)] - swapped)))
        if error > 1e-6:
            raise RuntimeError("Candidate swap-symmetry failure")
        symmetry[cell] = error
        for j, name in enumerate(CANDIDATE_SCORERS):
            path = cell_path(output / name, cell)
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with path.open("xb") as handle:
                pq.write_table(pa.table({"candidate_token": rows["candidate_token"], "score": scores[:, j]}), handle, compression="zstd")
            records.append({**record(path, output), "cell_id": cell, "scorer_id": name})
        print(json.dumps({"candidate_scoring_complete": cell}), flush=True)
    write_new(output / "PREDICTIONS.json", {"files": records, "symmetry_max_abs": symmetry,
        "session_sha256": sha(session / "SCORING_SESSION.json"), "truth_accessed": False,
        "ensemble_is_exact_fp64_raw_score_mean": True, "generated_at_utc": now()})


def import_baseline(bundle, session, candidate, baseline_input, output):
    manifest = verify_bundle(bundle)
    session_check(bundle, session)
    # No baseline data are available to the candidate-scoring phase. Its full
    # manifest and files must already exist before this import can start.
    candidate_manifest = read(candidate / "PREDICTIONS.json")
    verify_records(candidate, candidate_manifest["files"])
    source_freeze = baseline_input / "PREDICTION_FREEZE.json"
    if sha(source_freeze) != manifest["original_prediction_freeze_sha256"]:
        raise RuntimeError("Original baseline prediction freeze drift")
    frozen = read(source_freeze)
    if frozen["scorer_freeze_sha256"] != manifest["original_scorer_freeze_sha256"]:
        raise RuntimeError("Original scorer provenance drift")
    indexed = {(x["cell_id"], x["scorer_id"]): x for x in frozen["files"]}
    records = []
    for cell in CELLS:
        tokens = pq.read_table(cell_path(session / "candidates", cell), columns=["candidate_token"])["candidate_token"]
        columns = []
        for name, old in zip(BASELINE_SCORERS, ORIGINAL_SCORERS, strict=True):
            source = cell_path(baseline_input / old, cell)
            rec = indexed[(cell, old)]
            if rec["path"] != str(Path(old) / source.name):
                raise RuntimeError("Original baseline file mapping drift")
            verify_records(baseline_input, [rec])
            columns.append(validate_predictions(tokens, pq.read_table(source)))
            destination = cell_path(output / name, cell)
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with destination.open("xb") as handle, source.open("rb") as stream:
                shutil.copyfileobj(stream, handle, 8 * 1024 * 1024)
            if sha(destination) != rec["sha256"]:
                raise RuntimeError("Baseline copy is not byte-identical")
            records.append({**record(destination, output), "cell_id": cell, "scorer_id": name})
        if not np.array_equal(columns[0], np.column_stack(columns[1:]).mean(1, dtype=np.float64)):
            raise RuntimeError("Original baseline is not the exact three-seed mean")
    write_new(output / "PREDICTIONS.json", {"files": records, "truth_accessed": False,
        "original_prediction_freeze_sha256": sha(source_freeze),
        "candidate_manifest_sha256_before_import": sha(candidate / "PREDICTIONS.json"),
        "session_sha256": sha(session / "SCORING_SESSION.json"),
        "byte_identical_to_original": True, "imported_at_utc": now()})


def freeze_predictions(bundle, session, predictions, output):
    session_check(bundle, session)
    records, manifest_hashes = [], {}
    for part, scorers in (("candidate", CANDIDATE_SCORERS), ("baseline", BASELINE_SCORERS)):
        path = predictions / part / "PREDICTIONS.json"
        manifest = read(path)
        verify_records(predictions / part, manifest["files"])
        expected = {(c, s, str(Path(s) / cell_path(Path(), c))) for c in CELLS for s in scorers}
        actual = [(r["cell_id"], r["scorer_id"], r["path"]) for r in manifest["files"]]
        if (len(actual) != len(expected) or set(actual) != expected or manifest["truth_accessed"] is not False
                or manifest["session_sha256"] != sha(session / "SCORING_SESSION.json")):
            raise RuntimeError("Prediction census or session drift")
        if part == "candidate":
            symmetry = manifest["symmetry_max_abs"]
            if set(symmetry) != set(CELLS) or any(not np.isfinite(x) or x > 1e-6 for x in symmetry.values()):
                raise RuntimeError("Invalid symmetry record")
        else:
            if (manifest["byte_identical_to_original"] is not True
                    or manifest["candidate_manifest_sha256_before_import"] != manifest_hashes["candidate"]):
                raise RuntimeError("Baseline import preceded candidate freeze")
        for cell in CELLS:
            tokens = pq.read_table(cell_path(session / "candidates", cell), columns=["candidate_token"])["candidate_token"]
            scores = np.column_stack([validate_predictions(tokens, pq.read_table(cell_path(predictions / part / s, cell))) for s in scorers])
            if not np.array_equal(scores[:, 0], scores[:, 1:].mean(axis=1, dtype=np.float64)):
                raise RuntimeError("Ensemble arithmetic drift")
        manifest_hashes[part] = sha(path)
        records.extend({**r, "path": f"{part}/{r['path']}"} for r in manifest["files"])
    write_new(output / "PREDICTION_FREEZE.json", {
        "execution_id": EXECUTION, "package_id": PACKAGE, "validated_at_utc": now(),
        "scorer_freeze_sha256": sha(bundle / "SCORER_FREEZE.json"),
        "session_sha256": sha(session / "SCORING_SESSION.json"),
        "prediction_manifest_sha256": manifest_hashes, "files": records,
        "truth_accessed": False, "complete_unique_finite_two_column_coverage": True,
        "both_ensembles_are_exact_raw_score_means": True,
        "baseline_predictions_byte_identical_to_original": True, "symmetry_max_abs": symmetry})


def reserve_attempt(bundle, freeze, ledger, original_ledger):
    manifest = verify_bundle(bundle)
    frozen = read(freeze / "PREDICTION_FREEZE.json")
    if (frozen["execution_id"] != EXECUTION or frozen["truth_accessed"] is not False
            or not frozen["complete_unique_finite_two_column_coverage"]
            or frozen["scorer_freeze_sha256"] != sha(bundle / "SCORER_FREEZE.json")
            or sha(original_ledger) != ORIGINAL_LEDGER_SHA):
        raise RuntimeError("Invalid follow-up reservation inputs")
    if (ledger.parent / "completion.json").exists():
        raise RuntimeError("Follow-up already completed")
    write_new(ledger, {
        "schema_version": 1, "execution_id": EXECUTION, "package_id": PACKAGE,
        "reserved_at_utc": now(), "status": "followup_reserved_before_truth_access",
        "authorization": "DEC-0053", "authorization_sha256": manifest["authorization_sha256"],
        "original_spent_ledger_sha256": ORIGINAL_LEDGER_SHA,
        "search_freeze_sha256": SEARCH_SHA, "selection_sha256": SELECTION_SHA,
        "ensemble_acceptance_sha256": manifest["acceptance_sha256"],
        "scorer_freeze_sha256": sha(bundle / "SCORER_FREEZE.json"),
        "prediction_freeze_sha256": sha(freeze / "PREDICTION_FREEZE.json"),
        "truth_access_attempt_irrevocably_consumed": True, "original_first_attempt": False})


def summarize(points, draws):
    metrics = {}
    for j, name in enumerate(SCORERS):
        finite = np.isfinite(draws[j])
        metrics[name] = {"ht_P_vs_U_concordance": float(points[j]),
            "percentile_95": np.percentile(draws[j, finite], [2.5, 97.5]).tolist() if finite.any() else None,
            "finite_bootstrap_draws": int(finite.sum())}
    valid = np.isfinite(draws[0]) & np.isfinite(draws[4])
    ci = np.percentile((draws[0] - draws[4])[valid], [2.5, 97.5]).tolist() if valid.any() else None
    delta = float(points[0] - points[4])
    return {"metrics": metrics, "ensemble_minus_baseline": {
        "difference": delta, "paired_percentile_95": ci, "finite_paired_draws": int(valid.sum()),
        "positive_lower_bound": bool(valid.sum() >= 1900 and ci is not None and ci[0] > 0 and delta > 0)},
        "candidate_seed_concordance_range": float(np.ptp(points[1:4])),
        "baseline_seed_concordance_range": float(np.ptp(points[5:8]))}


def evaluate(bundle, session, predictions, freeze, output, ledger_path=Path("/ledger.json")):
    manifest = verify_bundle(bundle)
    session_check(bundle, session)
    frozen, ledger = read(freeze / "PREDICTION_FREEZE.json"), read(ledger_path)
    if (ledger["execution_id"] != EXECUTION or ledger["authorization"] != "DEC-0053"
            or ledger["original_spent_ledger_sha256"] != ORIGINAL_LEDGER_SHA
            or ledger["prediction_freeze_sha256"] != sha(freeze / "PREDICTION_FREEZE.json")
            or ledger["scorer_freeze_sha256"] != sha(bundle / "SCORER_FREEZE.json")
            or ledger["ensemble_acceptance_sha256"] != manifest["acceptance_sha256"]
            or ledger["truth_access_attempt_irrevocably_consumed"] is not True
            or frozen["scorer_freeze_sha256"] != sha(bundle / "SCORER_FREEZE.json")
            or frozen["session_sha256"] != sha(session / "SCORING_SESSION.json")
            or frozen["truth_accessed"] is not False):
        raise RuntimeError("Invalid frozen predictions or follow-up reservation")
    verify_records(predictions, frozen["files"])
    for part, digest in frozen["prediction_manifest_sha256"].items():
        if sha(predictions / part / "PREDICTIONS.json") != digest:
            raise RuntimeError("Prediction manifest drift")
    # This exclusive marker prevents a second entry even after decryption fails.
    write_new(output / "EVALUATION_ATTEMPT.json", {"execution_id": EXECUTION, "entered_at_utc": now(),
        "ledger_sha256": sha(ledger_path), "automatic_retry_prohibited": True})
    component = dict(zip(read(bundle / "features/endpoints.json"), read(bundle / "features/components.json"), strict=True))
    previous_path = bundle / "provenance/ORIGINAL_TEST_RESULTS.json"
    if sha(previous_path) != ORIGINAL_RESULT_SHA:
        raise RuntimeError("Original comparison reference drift")
    previous = read(previous_path)
    summaries, private_records = {}, []
    with tempfile.TemporaryDirectory(prefix="truth-decrypt-", dir=output) as temp:
        workspace = Path(temp)
        decrypt("protected_truth", manifest, workspace)
        positives = ds.dataset(workspace / "plain/protected_positive_truth", format="parquet")
        unlabeled = ds.dataset(workspace / "plain/unlabeled_pairs", format="parquet")
        for cell in CELLS:
            rows = pq.read_table(cell_path(session / "candidates", cell))
            p = positives.to_table(columns=["candidate_token", "state"], filter=ds.field("cell_id") == cell)
            u = unlabeled.to_table(columns=["pair_id", "sampling_weight_numerator", "sampling_weight_denominator", "state"], filter=ds.field("cell_id") == cell)
            if (p.num_rows != P_COUNTS[cell] or u.num_rows != U_ROWS
                    or set(p["state"].to_pylist()) != {"released_positive"}
                    or set(u["state"].to_pylist()) != {"unlabeled"}):
                raise RuntimeError("Truth census/state drift")
            tokens = pa.concat_arrays([p["candidate_token"].combine_chunks(), pa.array([token_for(cell, pair) for pair in u["pair_id"].to_pylist()])])
            if tokens.null_count or pc.count_distinct(tokens).as_py() != rows.num_rows:
                raise RuntimeError("Truth overlap or duplicate token")
            positions = pc.index_in(tokens, value_set=rows["candidate_token"])
            if positions.null_count:
                raise RuntimeError("Truth outside candidate session")
            scores = np.column_stack([validate_predictions(tokens, pq.read_table(cell_path(
                predictions / ("candidate" if name in CANDIDATE_SCORERS else "baseline") / name, cell))) for name in SCORERS])
            ordered = rows.take(positions)
            ca = [component[x] for x in ordered["endpoint_a_sha256"].to_pylist()]
            cb = [component[x] for x in ordered["endpoint_b_sha256"].to_pylist()]
            numerator, denominator = u["sampling_weight_numerator"].to_numpy(), u["sampling_weight_denominator"].to_numpy()
            if np.any(numerator <= 0) or np.any(denominator <= 0):
                raise RuntimeError("Invalid rational U weights")
            weights = np.concatenate((np.ones(p.num_rows), numerator.astype(np.float64) / denominator))
            positive = np.arange(rows.num_rows) < p.num_rows
            points, draws, metadata = bootstrap_metrics(scores, positive, weights, ca, cb, cell)
            summary = summarize(points, draws)
            errors = []
            for name, old in zip(BASELINE_SCORERS, ORIGINAL_SCORERS, strict=True):
                current, prior = summary["metrics"][name], previous["cells"][cell]["metrics"][old]
                errors.append(abs(current["ht_P_vs_U_concordance"] - prior["ht_P_vs_U_concordance"]))
                if current["finite_bootstrap_draws"] != prior["finite_bootstrap_draws"]:
                    raise RuntimeError("Original baseline bootstrap availability drift")
                if current["percentile_95"] is None or prior["percentile_95"] is None:
                    if current["percentile_95"] != prior["percentile_95"]:
                        raise RuntimeError("Original baseline interval availability drift")
                else:
                    errors.extend(abs(x - y) for x, y in zip(current["percentile_95"], prior["percentile_95"], strict=True))
            if max(errors) > 1e-12 or metadata != previous["cells"][cell]["bootstrap"]:
                raise RuntimeError("Original baseline result/draw replay drift")
            summary.update(positive_pairs=p.num_rows, sampled_unlabeled_pairs=u.num_rows,
                           bootstrap=metadata, original_baseline_replay_max_abs=max(errors))
            summaries[cell] = summary
            array_path = output / f"bootstrap-cell-{CELLS.index(cell):02d}.npz"
            with array_path.open("xb") as handle:
                np.savez(handle, points=points, draws=draws)
            private_records.append(record(array_path, output))
            write_new(output / f"aggregate-cell-{CELLS.index(cell):02d}.json", summary)
            print(json.dumps({"cell_metrics_complete": cell}), flush=True)
    write_new(output / "PRIVATE_BOOTSTRAP_MANIFEST.json", {"files": private_records, "scorers": list(SCORERS)})
    write_new(output / "FOLLOWUP_TEST_RESULTS.json", {
        "execution_id": EXECUTION, "package_id": PACKAGE, "model": MODEL, "baseline": BASELINE,
        "primary_cell": "C3_test", "cells": summaries, "generated_at_utc": now(),
        "scorer_freeze_sha256": sha(bundle / "SCORER_FREEZE.json"),
        "prediction_freeze_sha256": sha(freeze / "PREDICTION_FREEZE.json"),
        "ledger_sha256": sha(ledger_path), "original_ledger_sha256": ORIGINAL_LEDGER_SHA,
        "original_result_sha256": ORIGINAL_RESULT_SHA, "acceptance_sha256": manifest["acceptance_sha256"],
        "authorization": "DEC-0053", "test_previously_examined": True,
        "amendment_after_development_before_followup_test": True,
        "network_isolation_enforced": True, "prediction_hashed_before_truth": True,
        "one_followup_attempt": True, "original_first_attempt": False,
        "baseline_predictions_byte_identical_to_original": True,
        "U_is_not_negative": True, "no_test_tuning": True,
        "protected_candidate_or_truth_identity_public": False})


def qualify(bundle, output):
    verify_bundle(bundle)
    scorer = Scorer(bundle)
    rows = pq.read_table(bundle / "features/public_training_fixture.parquet")
    scores, swapped = scorer.score(rows), scorer.score(rows, swap=True)
    reference = np.load(bundle / "features/public_training_fixture_reference.npy", allow_pickle=False)
    error, symmetry = float(np.max(np.abs(scores - reference))), float(np.max(np.abs(scores - swapped)))
    if error > 1e-5 or symmetry > 1e-6 or not np.array_equal(scores, scorer.score(rows)):
        raise RuntimeError("Restricted scorer qualification failed")
    write_new(output / "SCORER_QUALIFICATION.json", {"passed": True, "rows": rows.num_rows,
        "CPU_vs_GPU_max_abs": error, "swap_max_abs": symmetry, "deterministic_repeat": True,
        "protected_candidates_accessed": False, "protected_truth_accessed": False})


if __name__ == "__main__":
    if os.environ.get("IPIN_EVALUATOR_NETWORK_ISOLATED") != "1":
        raise RuntimeError("Frozen restricted launcher required")
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    bundle, session, output = Path("/bundle"), Path("/session"), Path("/output")
    role = sys.argv[1]
    if role == "qualify":
        qualify(bundle, output)
    elif role == "open":
        open_candidates(bundle, output)
    elif role == "score":
        score_all(bundle, session, output)
    elif role == "import-baseline":
        import_baseline(bundle, session, Path("/candidate"), Path("/original_predictions"), output)
    elif role == "freeze-predictions":
        freeze_predictions(bundle, session, Path("/predictions"), output)
    elif role == "reserve":
        reserve_attempt(bundle, Path("/freeze"), Path("/custody/ledger.json"), Path("/original_ledger.json"))
    elif role == "evaluate":
        evaluate(bundle, session, Path("/predictions"), Path("/freeze"), output)
    else:
        raise RuntimeError("Unknown follow-up phase")
