"""Allowlisted aggregate publication only; cannot fit, score or decrypt.

Mount only the completed aggregate JSON, ledger, prediction freeze and public
output destinations. No candidate/truth rows, checkpoints or private keys.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import stat


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exclusive(path, payload):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def encode(payload):
    return (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def main(root=Path("/")):
    os.umask(0o077)
    source = root / "result.json"
    result = json.loads(source.read_bytes())
    ledger_path, freeze_path = root / "ledger.json", root / "prediction_freeze.json"
    ledger, freeze = json.loads(ledger_path.read_bytes()), json.loads(freeze_path.read_bytes())
    expected_keys = {"execution_id", "package_id", "model", "primary_cell", "cells", "generated_at_utc",
                     "scorer_freeze_sha256", "prediction_freeze_sha256", "ledger_sha256",
                     "protected_candidate_or_truth_identity_public", "network_isolation_enforced",
                     "prediction_hashed_before_truth", "one_first_attempt", "U_is_not_negative",
                     "no_full_universe_rank_or_probability_claim", "no_test_tuning"}
    if set(result) != expected_keys or result["execution_id"] != "protected_final_test_v1" or result["primary_cell"] != "C3_test":
        raise RuntimeError("Unexpected aggregate schema")
    if result["protected_candidate_or_truth_identity_public"] is not False:
        raise RuntimeError("Identity-bearing output prohibited")
    for flag in ("network_isolation_enforced", "prediction_hashed_before_truth", "one_first_attempt",
                 "U_is_not_negative", "no_full_universe_rank_or_probability_claim", "no_test_tuning"):
        if result[flag] is not True:
            raise RuntimeError("Incomplete custody/claim affirmation")
    if result["ledger_sha256"] != digest(ledger_path) or result["prediction_freeze_sha256"] != digest(freeze_path):
        raise RuntimeError("Custody hash mismatch")
    if ledger["prediction_freeze_sha256"] != digest(freeze_path) or freeze["scorer_freeze_sha256"] != result["scorer_freeze_sha256"]:
        raise RuntimeError("Prediction/scorer binding mismatch")
    baseline_ids = {"deterministic_hash", "training_degree_sum", "preferential_attachment",
                    "component_degree_mass_product", "training_common_neighbors", "sequence_length_sum",
                    "sequence_length_ratio", "within_pair_3mer_cosine", "exact_training_interolog_3mer",
                    "pooled_150m_cosine", "aac_cosine"}
    model = "lightweight_esm2_150m_linear__linear_lr3e-4"
    scorer_ids = {model, "seed20260803", "seed20260817", "seed20260831"} | baseline_ids
    expected_counts = {"C3_test": 2379, "C2_test": 13446, "C1_test": 3187,
                       "source_exclusive:HI-II-14:C3_test": 269, "source_exclusive:HuRI:C3_test": 1869,
                       "source_exclusive:HI-II-14:C2_test": 1488, "source_exclusive:HuRI:C2_test": 5270,
                       "source_exclusive:HI-II-14:C1_test": 280, "source_exclusive:HuRI:C1_test": 633}
    if result["model"] != model or set(result["cells"]) != set(expected_counts):
        raise RuntimeError("Model/cell census mismatch")

    def finite(value):
        return isinstance(value, (float, int)) and math.isfinite(value)

    def interval(value, lower, upper):
        return value is None or (isinstance(value, list) and len(value) == 2 and all(finite(x) for x in value) and lower <= value[0] <= value[1] <= upper)

    for cell, data in result["cells"].items():
        if set(data) != {"positive_pairs", "sampled_unlabeled_pairs", "metrics", "model_minus_controls", "bootstrap", "seed_concordance_range", "above_every_control_with_positive_paired_lower_bound"}:
            raise RuntimeError("Unexpected cell fields")
        if data["positive_pairs"] != expected_counts[cell] or data["sampled_unlabeled_pairs"] != 1_000_000:
            raise RuntimeError("Cell row-count mismatch")
        if set(data["metrics"]) != scorer_ids or set(data["model_minus_controls"]) != baseline_ids:
            raise RuntimeError("Comparison omissions or additions")
        bootstrap = data["bootstrap"]
        if set(bootstrap) != {"seed", "replicates", "participating_components", "multiplicities_sha256"} or bootstrap["replicates"] != 2000:
            raise RuntimeError("Unexpected bootstrap fields")
        for values in data["metrics"].values():
            if set(values) != {"ht_P_vs_U_concordance", "percentile_95", "finite_bootstrap_draws"}:
                raise RuntimeError("Unexpected scorer metric fields")
            if not finite(values["ht_P_vs_U_concordance"]) or not 0 <= values["ht_P_vs_U_concordance"] <= 1 or not interval(values["percentile_95"], 0, 1) or not 0 <= values["finite_bootstrap_draws"] <= 2000:
                raise RuntimeError("Invalid aggregate metric")
        for name, values in data["model_minus_controls"].items():
            if set(values) != {"model_minus_control", "paired_percentile_95", "finite_paired_draws", "positive_lower_bound"}:
                raise RuntimeError("Unexpected comparison fields")
            expected_delta = data["metrics"][model]["ht_P_vs_U_concordance"] - data["metrics"][name]["ht_P_vs_U_concordance"]
            if abs(values["model_minus_control"] - expected_delta) > 1e-14 or not interval(values["paired_percentile_95"], -1, 1):
                raise RuntimeError("Comparison arithmetic mismatch")
    # Verify that the completion operator's escrow-key paths are masked devices.
    for name in ("development_release", "protected_candidates", "protected_truth"):
        if not stat.S_ISCHR((root / "custody" / f"{name}_private.pem").stat().st_mode):
            raise RuntimeError("Escrow keys are not masked from publication process")
    target = root / "results/FINAL_TEST_RESULTS.json"
    receipt_path = root / "receipts/protected_final_test_v1.json"
    completion_path = root / "custody/protected_evaluation_completion.json"
    if any(path.exists() for path in (target, receipt_path, completion_path)):
        raise RuntimeError("Refuse publication or completion overwrite")
    exclusive(target, source.read_bytes())
    exclusive(target.with_suffix(".json.sha256"), f"{digest(target)}  {target.name}\n".encode())
    receipt = {
        "execution_id": "protected_final_test_v1", "package_id": result["package_id"], "status": "completed_one_first_attempt",
        "published_at_utc": datetime.now(timezone.utc).isoformat(), "model": model,
        "results_sha256": digest(target), "scorer_freeze_sha256": result["scorer_freeze_sha256"],
        "prediction_freeze_sha256": digest(freeze_path), "ledger_sha256": digest(ledger_path),
        "publisher_sha256": digest(Path(__file__)), "scorers": 15, "cells": 9, "candidate_rows": 9028821,
        "prediction_hashed_before_truth": True, "complete_unique_finite_two_column_coverage": True,
        "verified_network_syscall_and_mount_isolation": True, "one_first_attempt": True,
        "separate_cell_metrics_and_paired_2000_component_bootstrap": True, "protected_identity_output": False,
        "U_is_not_negative": True, "sample_is_not_full_universe": True,
        "prevalence_probability_calibration_biological_precision_universal_nonbinding_claims": False,
        "family_PLM_unseen_or_exhaustive_homology_claims": False, "post_test_tuning": False,
        "candidate_key_available_to_scorer_or_metrics": False, "truth_key_available_to_scorer": False,
        "same_author_not_independent_replication": True}
    exclusive(receipt_path, encode(receipt))
    exclusive(receipt_path.with_suffix(".json.sha256"), f"{digest(receipt_path)}  {receipt_path.name}\n".encode())
    exclusive(completion_path, encode({"schema_version": 2, "package_id": result["package_id"],
              "status": "completed", "completed_at_utc": receipt["published_at_utc"],
              "ledger_sha256": digest(ledger_path), "receipt_sha256": digest(receipt_path),
              "results_sha256": digest(target), "one_first_attempt_consumed": True}))
    print(json.dumps({"aggregate_publication_complete": True, "results_sha256": digest(target),
                      "receipt_sha256": digest(receipt_path), "completion_record_written": True}))


if __name__ == "__main__":
    main()
