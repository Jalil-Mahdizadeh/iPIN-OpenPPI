"""Strictly allowlisted aggregate publication; no row, model or key inputs."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re

EXECUTION = "model_optimization_followup_v1"
MODEL = "esm2_150m__residual_wide__epoch04_ensemble3"
BASELINE = "lightweight_esm2_150m_linear__linear_lr3e-4"
SEEDS = (20260803, 20260817, 20260831)
SCORERS = (MODEL,) + tuple(f"candidate_seed{s}" for s in SEEDS) + (BASELINE,) + tuple(f"baseline_seed{s}" for s in SEEDS)
COUNTS = {"C3_test": 2379, "source_exclusive:HI-II-14:C3_test": 269, "source_exclusive:HuRI:C3_test": 1869,
          "C2_test": 13446, "source_exclusive:HI-II-14:C2_test": 1488, "source_exclusive:HuRI:C2_test": 5270,
          "C1_test": 3187, "source_exclusive:HI-II-14:C1_test": 280, "source_exclusive:HuRI:C1_test": 633}
TRUE_FLAGS = {"test_previously_examined", "amendment_after_development_before_followup_test",
              "network_isolation_enforced", "prediction_hashed_before_truth", "one_followup_attempt",
              "baseline_predictions_byte_identical_to_original", "U_is_not_negative", "no_test_tuning"}
FALSE_FLAGS = {"original_first_attempt", "protected_candidate_or_truth_identity_public"}
HASHES = {"scorer_freeze_sha256", "prediction_freeze_sha256", "ledger_sha256", "original_ledger_sha256",
          "original_result_sha256", "acceptance_sha256"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def exclusive(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def interval(value, low, high):
    return value is None or (isinstance(value, list) and len(value) == 2
        and all(finite(v) for v in value) and low <= value[0] <= value[1] <= high)


def validate(result):
    keys = {"execution_id", "package_id", "model", "baseline", "primary_cell", "cells", "generated_at_utc", "authorization"} | TRUE_FLAGS | FALSE_FLAGS | HASHES
    if set(result) != keys or result["execution_id"] != EXECUTION or result["model"] != MODEL or result["baseline"] != BASELINE:
        raise RuntimeError("Unexpected follow-up aggregate schema/model")
    if result["package_id"] != "pair_level_pu_r_benchmark_artifacts_v1" or result["primary_cell"] != "C3_test" or result["authorization"] != "DEC-0053":
        raise RuntimeError("Unexpected follow-up authority or primary comparison")
    if any(result[k] is not True for k in TRUE_FLAGS) or any(result[k] is not False for k in FALSE_FLAGS):
        raise RuntimeError("Invalid follow-up custody/claim flags")
    if any(not isinstance(result[k], str) or not re.fullmatch(r"[0-9a-f]{64}", result[k]) for k in HASHES):
        raise RuntimeError("Invalid provenance digest")
    if (result["original_ledger_sha256"] != "e23a6a8980d3e9d148a40be8e9b3d1316ff1c2c6ed8f7f03ab2bd899b777914f"
            or result["original_result_sha256"] != "6cc8c3ba61039501b3e1b09dfcee442de8f4dfcd0c717a466b15f9e77ef3a02e"):
        raise RuntimeError("Original evaluation provenance drift")
    datetime.fromisoformat(result["generated_at_utc"])
    if set(result["cells"]) != set(COUNTS):
        raise RuntimeError("Incomplete follow-up cells")
    for cell, values in result["cells"].items():
        fields = {"positive_pairs", "sampled_unlabeled_pairs", "metrics", "ensemble_minus_baseline", "bootstrap",
                  "candidate_seed_concordance_range", "baseline_seed_concordance_range", "original_baseline_replay_max_abs"}
        if set(values) != fields or values["positive_pairs"] != COUNTS[cell] or values["sampled_unlabeled_pairs"] != 1000000:
            raise RuntimeError("Unexpected cell fields/counts")
        metrics = values["metrics"]
        if set(metrics) != set(SCORERS):
            raise RuntimeError("Missing or additional scorer")
        for metric in metrics.values():
            if set(metric) != {"ht_P_vs_U_concordance", "percentile_95", "finite_bootstrap_draws"}:
                raise RuntimeError("Unexpected metric fields")
            if (not finite(metric["ht_P_vs_U_concordance"]) or not 0 <= metric["ht_P_vs_U_concordance"] <= 1
                    or not interval(metric["percentile_95"], 0, 1)
                    or type(metric["finite_bootstrap_draws"]) is not int or not 0 <= metric["finite_bootstrap_draws"] <= 2000
                    or (metric["percentile_95"] is None) != (metric["finite_bootstrap_draws"] == 0)):
                raise RuntimeError("Invalid scorer metric")
        bootstrap = values["bootstrap"]
        if (set(bootstrap) != {"seed", "replicates", "participating_components", "multiplicities_sha256"}
                or bootstrap["replicates"] != 2000 or type(bootstrap["participating_components"]) is not int
                or bootstrap["participating_components"] < 1 or type(bootstrap["seed"]) is not int
                or not re.fullmatch(r"[0-9a-f]{64}", bootstrap["multiplicities_sha256"])):
            raise RuntimeError("Invalid bootstrap metadata")
        delta = values["ensemble_minus_baseline"]
        if set(delta) != {"difference", "paired_percentile_95", "finite_paired_draws", "positive_lower_bound"}:
            raise RuntimeError("Unexpected paired comparison fields")
        expected = metrics[MODEL]["ht_P_vs_U_concordance"] - metrics[BASELINE]["ht_P_vs_U_concordance"]
        if (not finite(delta["difference"]) or abs(delta["difference"] - expected) > 1e-14
                or not interval(delta["paired_percentile_95"], -1, 1)
                or type(delta["finite_paired_draws"]) is not int or not 0 <= delta["finite_paired_draws"] <= 2000
                or delta["finite_paired_draws"] > min(metrics[s]["finite_bootstrap_draws"] for s in (MODEL, BASELINE))
                or (delta["paired_percentile_95"] is None) != (delta["finite_paired_draws"] == 0)):
            raise RuntimeError("Invalid paired difference or interval")
        expected_positive = bool(delta["finite_paired_draws"] >= 1900 and delta["paired_percentile_95"] is not None
                                 and delta["paired_percentile_95"][0] > 0 and expected > 0)
        if delta["positive_lower_bound"] is not expected_positive:
            raise RuntimeError("Paired interpretation arithmetic mismatch")
        for kind in ("candidate", "baseline"):
            points = [metrics[f"{kind}_seed{s}"]["ht_P_vs_U_concordance"] for s in SEEDS]
            observed = values[f"{kind}_seed_concordance_range"]
            if not finite(observed) or abs(observed - (max(points) - min(points))) > 1e-14:
                raise RuntimeError("Seed diagnostic arithmetic mismatch")
        error = values["original_baseline_replay_max_abs"]
        if not finite(error) or not 0 <= error <= 1e-12:
            raise RuntimeError("Original baseline replay failed")


def main(root=Path("/")):
    os.umask(0o077)
    source = root / "result.json"
    result = json.loads(source.read_bytes())
    validate(result)
    ledger_path, prediction_path, scorer_path = (root / p for p in ("ledger.json", "prediction_freeze.json", "scorer_freeze.json"))
    ledger, prediction, scorer = (json.loads(p.read_bytes()) for p in (ledger_path, prediction_path, scorer_path))
    if (result["ledger_sha256"] != digest(ledger_path)
            or result["prediction_freeze_sha256"] != digest(prediction_path)
            or result["scorer_freeze_sha256"] != digest(scorer_path)
            or ledger["prediction_freeze_sha256"] != digest(prediction_path)
            or ledger["scorer_freeze_sha256"] != digest(scorer_path)
            or prediction["scorer_freeze_sha256"] != digest(scorer_path)
            or ledger["execution_id"] != EXECUTION or ledger["authorization"] != "DEC-0053"
            or ledger["truth_access_attempt_irrevocably_consumed"] is not True
            or ledger["original_first_attempt"] is not False
            or ledger["original_spent_ledger_sha256"] != result["original_ledger_sha256"]
            or ledger["ensemble_acceptance_sha256"] != result["acceptance_sha256"]
            or scorer["acceptance_sha256"] != result["acceptance_sha256"]
            or prediction["complete_unique_finite_two_column_coverage"] is not True
            or prediction["baseline_predictions_byte_identical_to_original"] is not True
            or prediction["truth_accessed"] is not False):
        raise RuntimeError("Custody hash/authorization chain mismatch")
    target = root / "results/FOLLOWUP_TEST_RESULTS.json"
    receipt_path = root / f"receipts/{EXECUTION}.json"
    completion_path = root / "custody/completion.json"
    if any(p.exists() for p in (target, target.with_suffix(".json.sha256"), receipt_path, receipt_path.with_suffix(".json.sha256"), completion_path)):
        raise RuntimeError("Refuse follow-up publication overwrite")
    exclusive(target, source.read_bytes())
    exclusive(target.with_suffix(".json.sha256"), f"{digest(target)}  {target.name}\n".encode())
    receipt = {"execution_id": EXECUTION, "status": "completed_one_followup_attempt", "authorization": "DEC-0053",
               "published_at_utc": datetime.now(timezone.utc).isoformat(), "results_sha256": digest(target),
               "scorer_freeze_sha256": digest(scorer_path), "prediction_freeze_sha256": digest(prediction_path),
               "ledger_sha256": digest(ledger_path), "original_ledger_sha256": result["original_ledger_sha256"],
               "original_result_sha256": result["original_result_sha256"], "publisher_sha256": digest(Path(__file__)),
               "model": MODEL, "baseline": BASELINE, "scorers": 8, "cells": 9, "candidate_rows": 9028821,
               "test_previously_examined": True, "amendment_after_development_before_followup_test": True,
               "baseline_predictions_byte_identical_to_original": True,
               "protected_identity_output": False, "new_fit_or_test_tuning": False,
               "same_author_not_independent_replication": True}
    exclusive(receipt_path, encode(receipt))
    exclusive(receipt_path.with_suffix(".json.sha256"), f"{digest(receipt_path)}  {receipt_path.name}\n".encode())
    exclusive(completion_path, encode({"execution_id": EXECUTION, "status": "completed",
        "completed_at_utc": receipt["published_at_utc"], "ledger_sha256": digest(ledger_path),
        "results_sha256": digest(target), "receipt_sha256": digest(receipt_path),
        "one_followup_attempt_consumed": True, "original_ledger_unchanged": True}))
    print(json.dumps({"aggregate_publication_complete": True, "results_sha256": digest(target),
                      "receipt_sha256": digest(receipt_path), "completion_record_written": True}))


if __name__ == "__main__":
    main()
