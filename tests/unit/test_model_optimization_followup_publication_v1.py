"""Aggregate schema, arithmetic, custody-chain and overwrite rejection fixtures."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

CODE = Path("/bundle/code") if Path("/bundle/code/publish_model_optimization_followup_v1.py").exists() else Path(__file__).resolve().parents[2] / "scripts/benchmark"
spec = importlib.util.spec_from_file_location("followup_publication_fixture", CODE / "publish_model_optimization_followup_v1.py")
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


def result_fixture():
    metrics = {s: {"ht_P_vs_U_concordance": .5, "percentile_95": [.4, .6], "finite_bootstrap_draws": 2000} for s in pub.SCORERS}
    cells = {cell: {"positive_pairs": n, "sampled_unlabeled_pairs": 1000000,
        "metrics": copy.deepcopy(metrics), "ensemble_minus_baseline": {"difference": 0., "paired_percentile_95": [-.1, .1],
            "finite_paired_draws": 2000, "positive_lower_bound": False},
        "bootstrap": {"seed": 1, "replicates": 2000, "participating_components": 30, "multiplicities_sha256": "0" * 64},
        "candidate_seed_concordance_range": 0., "baseline_seed_concordance_range": 0., "original_baseline_replay_max_abs": 0.}
        for cell, n in pub.COUNTS.items()}
    result = {"execution_id": pub.EXECUTION, "package_id": "pair_level_pu_r_benchmark_artifacts_v1", "model": pub.MODEL,
        "baseline": pub.BASELINE, "primary_cell": "C3_test", "cells": cells, "generated_at_utc": "2026-09-11T00:00:00+00:00", "authorization": "DEC-0053"}
    result.update({k: True for k in pub.TRUE_FLAGS})
    result.update({k: False for k in pub.FALSE_FLAGS})
    result.update({k: "0" * 64 for k in pub.HASHES})
    result["original_ledger_sha256"] = "e23a6a8980d3e9d148a40be8e9b3d1316ff1c2c6ed8f7f03ab2bd899b777914f"
    result["original_result_sha256"] = "6cc8c3ba61039501b3e1b09dfcee442de8f4dfcd0c717a466b15f9e77ef3a02e"
    return result


class FollowupPublicationFixtures(unittest.TestCase):
    def test_complete_schema_accepted(self):
        pub.validate(result_fixture())

    def test_identity_omissions_nonfinite_and_arithmetic_rejected(self):
        for variant in ("identity", "unknown", "missing_cell", "missing_seed", "nan", "gain", "claim", "range", "count", "first_attempt"):
            with self.subTest(variant=variant):
                result = result_fixture()
                cell = result["cells"]["C3_test"]
                if variant == "identity":
                    result["protected_candidate_or_truth_identity_public"] = True
                elif variant == "unknown":
                    result["raw_rows"] = []
                elif variant == "missing_cell":
                    result["cells"].pop("C2_test")
                elif variant == "missing_seed":
                    cell["metrics"].pop("candidate_seed20260831")
                elif variant == "nan":
                    cell["metrics"][pub.MODEL]["ht_P_vs_U_concordance"] = float("nan")
                elif variant == "gain":
                    cell["ensemble_minus_baseline"]["difference"] = .1
                elif variant == "claim":
                    cell["ensemble_minus_baseline"]["positive_lower_bound"] = True
                elif variant == "range":
                    cell["candidate_seed_concordance_range"] = .3
                elif variant == "count":
                    cell["ensemble_minus_baseline"]["finite_paired_draws"] = 2001
                else:
                    result["original_first_attempt"] = True
                with self.assertRaises(RuntimeError):
                    pub.validate(result)

    def test_publish_once_with_separate_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = result_fixture()
            pub.exclusive(root / "scorer_freeze.json", pub.encode({"acceptance_sha256": result["acceptance_sha256"]}))
            result["scorer_freeze_sha256"] = pub.digest(root / "scorer_freeze.json")
            prediction = {"scorer_freeze_sha256": result["scorer_freeze_sha256"],
                "complete_unique_finite_two_column_coverage": True, "baseline_predictions_byte_identical_to_original": True, "truth_accessed": False}
            pub.exclusive(root / "prediction_freeze.json", pub.encode(prediction))
            result["prediction_freeze_sha256"] = pub.digest(root / "prediction_freeze.json")
            ledger = {"execution_id": pub.EXECUTION, "authorization": "DEC-0053", "truth_access_attempt_irrevocably_consumed": True,
                "original_first_attempt": False, "original_spent_ledger_sha256": result["original_ledger_sha256"],
                "ensemble_acceptance_sha256": result["acceptance_sha256"], "scorer_freeze_sha256": result["scorer_freeze_sha256"],
                "prediction_freeze_sha256": result["prediction_freeze_sha256"]}
            pub.exclusive(root / "ledger.json", pub.encode(ledger))
            result["ledger_sha256"] = pub.digest(root / "ledger.json")
            pub.exclusive(root / "result.json", pub.encode(result))
            pub.main(root)
            self.assertEqual((root / "result.json").read_bytes(), (root / "results/FOLLOWUP_TEST_RESULTS.json").read_bytes())
            self.assertTrue((root / "custody/completion.json").exists())
            self.assertFalse((root / "custody/protected_evaluation_completion.json").exists())
            with self.assertRaises(RuntimeError):
                pub.main(root)


if __name__ == "__main__":
    unittest.main(argv=[__file__], verbosity=2)
