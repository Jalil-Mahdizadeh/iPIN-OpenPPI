"""Aggregate-publication fixtures; no real protected or model input access."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/benchmark/publish_protected_final_test_v1.py"
spec = importlib.util.spec_from_file_location("final_publication", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicationFixtures(unittest.TestCase):
    def make_fixture(self, root):
        for name in ("custody", "results", "receipts"):
            (root / name).mkdir()
        for name in ("development_release", "protected_candidates", "protected_truth"):
            (root / "custody" / f"{name}_private.pem").symlink_to("/dev/null")
        frozen = {"scorer_freeze_sha256": "0" * 64}
        module.exclusive(root / "prediction_freeze.json", module.encode(frozen))
        module.exclusive(root / "ledger.json", module.encode({"prediction_freeze_sha256": module.digest(root / "prediction_freeze.json")}))
        model = "lightweight_esm2_150m_linear__linear_lr3e-4"
        baselines = ("deterministic_hash", "training_degree_sum", "preferential_attachment", "component_degree_mass_product",
                     "training_common_neighbors", "sequence_length_sum", "sequence_length_ratio", "within_pair_3mer_cosine",
                     "exact_training_interolog_3mer", "pooled_150m_cosine", "aac_cosine")
        cells = {}
        counts = {"C3_test": 2379, "C2_test": 13446, "C1_test": 3187,
                  "source_exclusive:HI-II-14:C3_test": 269, "source_exclusive:HuRI:C3_test": 1869,
                  "source_exclusive:HI-II-14:C2_test": 1488, "source_exclusive:HuRI:C2_test": 5270,
                  "source_exclusive:HI-II-14:C1_test": 280, "source_exclusive:HuRI:C1_test": 633}
        for cell, n in counts.items():
            cells[cell] = {"positive_pairs": n, "sampled_unlabeled_pairs": 1000000,
                           "metrics": {s: {"ht_P_vs_U_concordance": .5, "percentile_95": [.4, .6], "finite_bootstrap_draws": 2000}
                                       for s in (model, "seed20260803", "seed20260817", "seed20260831") + baselines},
                           "model_minus_controls": {s: {"model_minus_control": 0., "paired_percentile_95": [-.1, .1], "finite_paired_draws": 2000, "positive_lower_bound": False} for s in baselines},
                           "bootstrap": {"seed": 1, "replicates": 2000, "participating_components": 100, "multiplicities_sha256": "0" * 64},
                           "seed_concordance_range": 0., "above_every_control_with_positive_paired_lower_bound": False}
        result = {"execution_id": "protected_final_test_v1", "package_id": "pair_level_pu_r_benchmark_artifacts_v1", "model": model,
                  "primary_cell": "C3_test", "cells": cells, "generated_at_utc": "synthetic",
                  "scorer_freeze_sha256": "0" * 64, "prediction_freeze_sha256": module.digest(root / "prediction_freeze.json"),
                  "ledger_sha256": module.digest(root / "ledger.json"), "protected_candidate_or_truth_identity_public": False}
        for flag in ("network_isolation_enforced", "prediction_hashed_before_truth", "one_first_attempt", "U_is_not_negative",
                     "no_full_universe_rank_or_probability_claim", "no_test_tuning"):
            result[flag] = True
        return result

    def test_valid_aggregate_published_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.make_fixture(root)
            module.exclusive(root / "result.json", module.encode(result))
            module.main(root)
            self.assertEqual((root / "result.json").read_bytes(), (root / "results/FINAL_TEST_RESULTS.json").read_bytes())
            self.assertTrue((root / "custody/protected_evaluation_completion.json").is_file())
            with self.assertRaises(RuntimeError):
                module.main(root)

    def test_unknown_fields_and_missing_controls_rejected(self):
        for variant in ("unknown", "identity", "missing_control", "delta"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = self.make_fixture(root)
                if variant == "unknown":
                    result["raw_rows"] = []
                elif variant == "identity":
                    result["protected_candidate_or_truth_identity_public"] = True
                elif variant == "missing_control":
                    result["cells"]["C3_test"]["metrics"].pop("aac_cosine")
                else:
                    result["cells"]["C3_test"]["model_minus_controls"]["aac_cosine"]["model_minus_control"] = .1
                module.exclusive(root / "result.json", module.encode(result))
                with self.assertRaises(RuntimeError):
                    module.main(root)
                self.assertFalse((root / "results/FINAL_TEST_RESULTS.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
