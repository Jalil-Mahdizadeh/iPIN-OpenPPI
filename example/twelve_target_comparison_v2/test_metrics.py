"""Independent small-ranking oracles, including ties crossing screening budgets."""
import importlib.util
import itertools
import math
from pathlib import Path
import unittest

import numpy as np

SPEC = importlib.util.spec_from_file_location("twelve_metrics", Path(__file__).with_name("metrics.py"))
METRICS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(METRICS)


class RetrievalMetricsTests(unittest.TestCase):
    def test_perfect_and_reversed(self):
        for labels, concordance, ap in (([1, 1, 0, 0], 1., 1.), ([0, 0, 1, 1], 0., (1 / 3 + 2 / 4) / 2)):
            result = METRICS.evaluate([4, 3, 2, 1], np.asarray(labels, bool), (1, 2, 4))
            self.assertEqual(result["P_vs_U_concordance"], concordance)
            self.assertAlmostEqual(result["average_precision"], ap)
            self.assertEqual(result["recall_at_4"], 1.)
            self.assertEqual(result["EF_at_4"], 1.)

    def test_all_tied_against_exhaustive_random_orderings(self):
        # Two positives among five tied candidates. Enumerate every possible
        # position set; the expected reciprocal is NOT reciprocal(midrank).
        placements = list(itertools.combinations(range(1, 6), 2))
        result = METRICS.evaluate([1.] * 5, np.asarray([1, 0, 0, 1, 0], bool), (1, 2, 4))
        self.assertEqual(result["P_vs_U_concordance"], .5)
        self.assertEqual(result["average_precision"], .4)
        self.assertAlmostEqual(result["first_positive_rank_expected"], np.mean([min(x) for x in placements]))
        self.assertAlmostEqual(result["reciprocal_rank"], np.mean([1 / min(x) for x in placements]))
        for k in (1, 2, 4):
            hits = [sum(rank <= k for rank in positions) for positions in placements]
            self.assertAlmostEqual(result[f"recovered_P_at_{k}"], np.mean(hits))
            self.assertAlmostEqual(result[f"target_success_at_{k}"], np.mean([hit > 0 for hit in hits]))
            ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, 2) + 1))
            oracle = np.mean([sum(1 / math.log2(rank + 1) for rank in x if rank <= k) / ideal for x in placements])
            self.assertAlmostEqual(result[f"NDCG_at_{k}"], oracle)

    def test_offset_tied_first_positive_group(self):
        result = METRICS.evaluate([5, 4, 3, 3, 3, 1], np.asarray([0, 0, 1, 0, 1, 0], bool), (2, 3, 5))
        self.assertEqual(result["first_positive_rank_min"], 3)
        self.assertEqual(result["first_positive_rank_max"], 4)
        self.assertAlmostEqual(result["first_positive_rank_expected"], 10 / 3)
        self.assertAlmostEqual(result["reciprocal_rank"], (1 / 3 + 1 / 3 + 1 / 4) / 3)
        self.assertAlmostEqual(result["target_success_at_3"], 2 / 3)
        self.assertEqual(result["target_success_at_2"], 0.)
        self.assertEqual(result["target_success_at_5"], 1.)

    def test_invariance_to_row_order_and_monotone_score_transform(self):
        scores = np.asarray([.3, 1., -.5, .3, 2., 1.])
        labels = np.asarray([1, 0, 0, 0, 1, 1], bool)
        reference = METRICS.evaluate(scores, labels, (1, 3, 6))
        for order in (np.arange(6)[::-1], np.asarray([2, 5, 3, 0, 1, 4])):
            self.assertEqual(reference, METRICS.evaluate(scores[order] * 2 + 7, labels[order], (1, 3, 6)))

    def test_positive_rank_tie_boundary(self):
        self.assertEqual(METRICS.positive_ranks(3., [4., 3., 3., 3., 2.], (2, 3))["top2_fractional_credit"], 1 / 3)
        self.assertEqual(METRICS.positive_ranks(3., [4., 3., 3., 3., 2.], (2, 3))["rank_mid"], 3.)

    def test_reject_invalid_inputs(self):
        for scores, labels in (([1., np.nan], [1, 0]), ([1., 2.], [1, 1]), ([1., 2.], [0, 0]), ([1.], [1, 0])):
            with self.assertRaises(ValueError):
                METRICS.evaluate(scores, np.asarray(labels, bool), (1,))
        with self.assertRaises(ValueError):
            METRICS.evaluate([1., 2.], np.asarray([1, 0]), (1,))
        with self.assertRaises(ValueError):
            METRICS.evaluate([1., 2.], np.asarray([1, 0], bool), (3,))


if __name__ == "__main__":
    unittest.main()
