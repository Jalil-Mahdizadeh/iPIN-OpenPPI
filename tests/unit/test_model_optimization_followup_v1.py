"""Synthetic-only fixed-ensemble, import, token and one-attempt custody tests."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import torch
from torch.nn import functional as F

CODE = Path("/bundle/code") if Path("/bundle/code/model_optimization_followup_core_v1.py").exists() else Path(__file__).resolve().parents[2] / "scripts/benchmark"
sys.path.insert(0, str(CODE))
spec = importlib.util.spec_from_file_location("followup_fixture_core", CODE / "model_optimization_followup_core_v1.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class FollowupFixtures(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2)

    def test_ensemble_metric_is_not_mean_of_member_metrics(self):
        member_scores = np.array([[2, 2, 2], [2, 2, 2], [3, 0, 1], [0, 3, 1]], np.float64)
        scores = np.column_stack((member_scores.mean(1), member_scores))
        point, _, _ = core.bootstrap_metrics(scores, [1, 1, 0, 0], np.ones(4),
                                             ["a"] * 4, ["b"] * 4, "fixture", replicates=5, workers=1)
        self.assertEqual(point[0], 1.)
        self.assertGreater(point[0], point[1:].mean())

    def test_fixed_residual_scorer_matches_explicit_math(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            features = root / "features"
            features.mkdir()
            rng = np.random.default_rng(48)
            z = rng.normal(size=(15, 640)).astype(np.float32)
            np.save(features / "standardized.npy", z, allow_pickle=False)
            core.write_new(features / "endpoints.json", [f"synthetic-{i}" for i in range(15)])
            for seed in core.SEEDS:
                head = core.models.build(640, core.SPEC, seed)
                core.models.save_state(features / f"candidate_{seed}.npz", head)
            scorer = core.Scorer(root)
            a, b = np.array([0, 1, 6, 8]), np.array([7, 8, 2, 4])
            observed = scorer.score_indices(a, b)
            np.testing.assert_array_equal(observed, scorer.score_indices(b, a))
            np.testing.assert_array_equal(observed, scorer.score_indices(a, b))
            np.testing.assert_array_equal(observed[:, 0], observed[:, 1:].mean(1, dtype=np.float64))
            x, y = torch.from_numpy(z[a]), torch.from_numpy(z[b])
            cosine = ((x * y).sum(1) / (torch.linalg.vector_norm(x, dim=1) * torch.linalg.vector_norm(y, dim=1)))[:, None]
            pair = torch.cat((x + y, torch.abs(x - y), x * y, cosine), dim=1)
            expected = []
            for head in scorer.heads:
                p = head.state_dict()
                h = F.layer_norm(pair, (1921,), p["network.0.weight"], p["network.0.bias"], eps=1e-5)
                h = F.gelu(F.linear(h, p["network.1.weight"], p["network.1.bias"]))
                values = F.linear(pair, p["output.weight"], p["output.bias"]) + F.linear(h, p["network.4.weight"], p["network.4.bias"])
                expected.append(values[:, 0].numpy())
            np.testing.assert_array_equal(observed[:, 1:], np.column_stack(expected).astype(np.float64))
            with self.assertRaises(RuntimeError):
                scorer.score_indices(a, a)

    def test_nonfinite_state_and_zero_vectors_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "features").mkdir()
            core.write_new(root / "features/endpoints.json", ["a", "b"])
            np.save(root / "features/standardized.npy", np.zeros((2, 640), np.float32), allow_pickle=False)
            with self.assertRaises(RuntimeError):
                core.Scorer(root)
            np.save(root / "features/standardized.npy", np.ones((2, 640), np.float32), allow_pickle=False)
            for seed in core.SEEDS:
                head = core.models.build(640, core.SPEC, seed)
                with torch.no_grad():
                    head.output.bias.fill_(float("nan"))
                core.models.save_state(root / "features" / f"candidate_{seed}.npz", head)
            with self.assertRaises(RuntimeError):
                core.Scorer(root)

    def test_paired_decision_is_ensemble_level(self):
        points = np.array([.8, .81, .77, .76, .78, .78, .79, .78])
        draws = np.repeat(points[:, None], 2000, axis=1)
        result = core.summarize(points, draws)
        self.assertTrue(result["ensemble_minus_baseline"]["positive_lower_bound"])
        self.assertAlmostEqual(result["ensemble_minus_baseline"]["difference"], .02)
        self.assertLess(points[2], points[6])
        draws[0, :101] = np.nan
        self.assertFalse(core.summarize(points, draws)["ensemble_minus_baseline"]["positive_lower_bound"])

    def test_bundle_rejects_wrong_model_and_unaccepted_amendment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core.write_new(root / "provenance/ENSEMBLE_ACCEPTANCE.json", {
                "accepted_for_one_followup": True, "original_gate_passed": False, "authorization": "DEC-0053"})
            manifest = {"execution_id": core.EXECUTION, "model": core.MODEL, "scorers": list(core.SCORERS),
                        "cells": list(core.CELLS), "search_freeze_sha256": core.SEARCH_SHA,
                        "selection_sha256": core.SELECTION_SHA, "original_ledger_sha256": core.ORIGINAL_LEDGER_SHA,
                        "original_result_sha256": core.ORIGINAL_RESULT_SHA, "checkpoint_sha256": list(core.CHECKPOINT_SHAS),
                        "files": [], "acceptance_sha256": core.sha(root / "provenance/ENSEMBLE_ACCEPTANCE.json")}
            core.write_new(root / "SCORER_FREEZE.json", manifest)
            core.verify_bundle(root)
            with patch.object(core, "MODEL", "wrong-model"), self.assertRaises(RuntimeError):
                core.verify_bundle(root)
            with patch.object(core, "read", side_effect=[manifest, {"accepted_for_one_followup": False}]), self.assertRaises(RuntimeError):
                core.verify_bundle(root)

    def test_synthetic_end_to_end_preserves_original_and_refuses_reentry(self):
        cell = "C3_test"
        with tempfile.TemporaryDirectory() as directory, patch.object(core, "CELLS", (cell,)), patch.object(core, "P_COUNTS", {cell: 1}), patch.object(core, "U_ROWS", 2):
            root = Path(directory)
            bundle, session, predictions, freeze, output, baseline_input = [root / p for p in ("bundle", "session", "predictions", "freeze", "evaluation", "original_predictions")]
            for folder in (bundle, session, predictions / "candidate", predictions / "baseline", freeze, output, baseline_input):
                folder.mkdir(parents=True)
            core.write_new(bundle / "SCORER_FREEZE.json", {"synthetic": True})
            core.write_new(bundle / "features/endpoints.json", ["a", "b", "c"])
            core.write_new(bundle / "features/components.json", ["ca", "cb", "cc"])
            old_ledger = root / "original_ledger.json"
            core.write_new(old_ledger, {"original_attempt": "spent"})
            before = old_ledger.read_bytes()
            left, right = ["a", "a", "b"], ["b", "c", "c"]
            pairs = [core.pair_identifier(a, b) for a, b in zip(left, right)]
            tokens = [core.token_for(cell, p) for p in pairs]
            candidates = pa.table({"candidate_token": tokens, "endpoint_a_sha256": left,
                                   "endpoint_b_sha256": right, "cell_id": [cell] * 3})
            old_records = []
            for old in core.ORIGINAL_SCORERS:
                path = core.cell_path(baseline_input / old, cell)
                path.parent.mkdir()
                pq.write_table(pa.table({"candidate_token": tokens[::-1], "score": [.5] * 3}), path)
                old_records.append({**core.record(path, baseline_input), "cell_id": cell, "scorer_id": old})
            core.write_new(baseline_input / "PREDICTION_FREEZE.json", {"scorer_freeze_sha256": "old-freeze", "files": old_records})
            manifest = {"original_prediction_freeze_sha256": core.sha(baseline_input / "PREDICTION_FREEZE.json"),
                        "original_scorer_freeze_sha256": "old-freeze", "authorization_sha256": "a" * 64,
                        "acceptance_sha256": "b" * 64}
            points, draws, meta = core.bootstrap_metrics(np.ones((3, 8)), [True, False, False], [1., 1.5, 2.],
                ["ca", "ca", "cb"], ["cb", "cc", "cc"], cell)
            summary = core.summarize(points, draws)
            old_metrics = {old: summary["metrics"][new] for old, new in zip(core.ORIGINAL_SCORERS, core.BASELINE_SCORERS)}
            prior = bundle / "provenance/ORIGINAL_TEST_RESULTS.json"
            core.write_new(prior, {"cells": {cell: {"metrics": old_metrics, "bootstrap": meta}}})

            def fixture_decrypt(role, frozen, target):
                if role == "protected_candidates":
                    folder = target / "plain/protected_candidates"
                    folder.mkdir(parents=True)
                    pq.write_table(candidates.append_column("forbidden_metadata", pa.array(["P", "U", "U"])), folder / "part-00000.parquet")
                else:
                    folder = target / "plain/protected_positive_truth"
                    folder.mkdir(parents=True)
                    pq.write_table(pa.table({"candidate_token": tokens[:1], "state": ["released_positive"], "cell_id": [cell]}), folder / "part-00000.parquet")
                    folder = target / "plain/unlabeled_pairs"
                    folder.mkdir(parents=True)
                    pq.write_table(pa.table({"pair_id": pairs[1:], "state": ["unlabeled"] * 2, "cell_id": [cell] * 2,
                        "sampling_weight_numerator": [3, 2], "sampling_weight_denominator": [2, 1]}), folder / "part-00000.parquet")

            with patch.object(core, "verify_bundle", return_value=manifest), patch.object(core, "decrypt", fixture_decrypt), patch.object(core, "ORIGINAL_LEDGER_SHA", core.sha(old_ledger)), patch.object(core, "ORIGINAL_RESULT_SHA", core.sha(prior)):
                core.open_candidates(bundle, session)
                self.assertEqual(pq.read_table(core.cell_path(session / "candidates", cell)).column_names, list(core.COLUMNS))
                fake = SimpleNamespace(score=lambda rows, swap=False: np.ones((rows.num_rows, 4)))
                with patch.object(core, "Scorer", return_value=fake):
                    core.score_all(bundle, session, predictions / "candidate")
                core.import_baseline(bundle, session, predictions / "candidate", baseline_input, predictions / "baseline")
                for old, new in zip(core.ORIGINAL_SCORERS, core.BASELINE_SCORERS):
                    self.assertEqual(core.sha(core.cell_path(baseline_input / old, cell)), core.sha(core.cell_path(predictions / "baseline" / new, cell)))
                core.freeze_predictions(bundle, session, predictions, freeze)
                ledger = root / "new_custody/ledger.json"
                core.reserve_attempt(bundle, freeze, ledger, old_ledger)
                with self.assertRaises(FileExistsError):
                    core.reserve_attempt(bundle, freeze, ledger, old_ledger)
                core.evaluate(bundle, session, predictions, freeze, output, ledger)
                result = core.read(output / "FOLLOWUP_TEST_RESULTS.json")
                self.assertEqual(result["cells"][cell]["ensemble_minus_baseline"]["difference"], 0.)
                self.assertFalse(result["original_first_attempt"])
                with self.assertRaises(FileExistsError):
                    core.evaluate(bundle, session, predictions, freeze, output, ledger)
                self.assertEqual(before, old_ledger.read_bytes())
                self.assertFalse(list(session.glob("candidate-decrypt-*")))
                self.assertFalse(list(output.glob("truth-decrypt-*")))
                self.assertTrue(core.read(ledger)["truth_access_attempt_irrevocably_consumed"])
                # Mutated predictions fail before any further truth access.
                target = core.cell_path(predictions / "candidate" / core.MODEL, cell)
                with target.open("ab") as stream:
                    stream.write(b"synthetic-tampering")
                with self.assertRaises(RuntimeError):
                    core.freeze_predictions(bundle, session, predictions, root / "another-freeze")


if __name__ == "__main__":
    unittest.main(argv=[__file__], verbosity=2)
