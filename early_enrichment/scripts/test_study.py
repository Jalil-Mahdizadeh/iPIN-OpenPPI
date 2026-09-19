"""Small independent tests; qualification also checks the real frozen GPU scorer."""
import itertools
import unittest
import numpy as np
import torch

from common import BUDGETS, SPEC, destination, earliest_best, head, lr_at, ranking
from training import QuerySampler, cutoff_credit, oriented_csr


class StudyTests(unittest.TestCase):
    def test_cutoff_ties(self):
        np.testing.assert_allclose(cutoff_credit([5, 4, 4, 4, 1], 2), [1, 1/3, 1/3, 1/3, 0])

    def test_credit_sum(self):
        rng = np.random.default_rng(1)
        for n in (40, 81, 800):
            for k in (10, 20, 30, 40):
                self.assertAlmostEqual(cutoff_credit(rng.integers(0, 10, n), k).sum(), k)

    def test_no_tie_weights(self):
        np.testing.assert_array_equal(cutoff_credit([4, 3, 2, 1], 2), [1, 1, 0, 0])

    def test_self_orientation_once(self):
        ptr, partner, rows = oriented_csr(np.array([0, 0]), np.array([0, 1]), 2)
        np.testing.assert_array_equal(ptr, [0, 2, 3])
        np.testing.assert_array_equal(partner, [0, 1, 0])
        np.testing.assert_array_equal(rows, [0, 1, 1])

    def sampler(self):
        return QuerySampler(dict(p_a=np.array([0, 0]), p_b=np.array([1, 2]),
                                 u_a=np.array([0, 0, 1, 1, 2]), u_b=np.array([3, 4, 3, 4, 4])), 5)

    def test_same_query_membership(self):
        s = self.sampler()
        qi, q, pi, ui = s.draw(1, 2, 10000)
        self.assertTrue(np.all((pi >= s.pp[q]) & (pi < s.pp[q + 1])))
        self.assertTrue(np.all((ui >= s.up[q]) & (ui < s.up[q + 1])))
        self.assertTrue(np.all(np.bincount(qi) > 3000))

    def test_matched_samples(self):
        s = self.sampler()
        for a, b in zip(s.draw(42, 1, 100), s.draw(42, 1, 100)):
            np.testing.assert_array_equal(a, b)

    def test_shortlist_normalization(self):
        s = self.sampler()
        weights, info = s.shortlist_weights(np.array([9, 1, 8, 7, 4, 3, 2]), cutoff=2)
        for q in s.queries:
            self.assertAlmostEqual(float(weights[s.up[q]:s.up[q + 1]].mean()), 1, places=6)
        self.assertGreater(weights.min(), 0)
        self.assertLessEqual(weights.max(), 3)

    def test_early_U_upweighted(self):
        s = self.sampler()
        weights, _ = s.shortlist_weights(np.array([9, 1, 8, 7, 4, 3, 2]), cutoff=2)
        self.assertGreater(weights[0], weights[1])

    def test_macro_EF(self):
        p = np.array([True, False, True, False])
        actual = ranking.rank_metrics([4, 3, 2, 1], p, budgets=(1, 2, 3))
        np.testing.assert_allclose(actual[:, 0], [2, 1, 4/3])
        np.testing.assert_allclose(actual[:, 1], [1, 1, 2])
        np.testing.assert_allclose(actual[:, 2], [.5, .5, 1])

    def test_tie_metrics_brute_force(self):
        positives = np.array([True, False, True, False])
        expected = []
        for permutation in itertools.permutations(range(4)):
            h = positives[list(permutation)][:2].sum()
            expected.append([h, h/2, float(h > 0)])
        actual = ranking.rank_metrics(np.zeros(4), positives, budgets=(2,))[0]
        np.testing.assert_allclose(actual[[1, 2, 4]], np.mean(expected, axis=0))

    def test_symmetric_network(self):
        m = head.build(5, SPEC, 123).eval()
        a, b = torch.randn(8, 5), torch.randn(8, 5)
        torch.testing.assert_close(m(a, b), m(b, a), rtol=0, atol=0)

    def test_scheduler(self):
        self.assertAlmostEqual(lr_at(0, 100, 1), .2)
        self.assertAlmostEqual(lr_at(4, 100, 1), 1)
        self.assertAlmostEqual(lr_at(99, 100, 1), .1)

    def test_bootstrap_paired(self):
        values = np.arange(20.).reshape(10, 2)
        result = ranking.cluster_draws(values, np.repeat(np.arange(5), 2), 50, seed=42)
        np.testing.assert_allclose(result[:, 1] - result[:, 0], 1)

    def test_output_guard(self):
        with self.assertRaises(ValueError):
            destination('../combo/no-write')

    def test_earliest_checkpoint_tie(self):
        rows = [dict(epoch=8, EF20=2.0), dict(epoch=4, EF20=2.0 - 1e-13)]
        self.assertEqual(earliest_best(rows)['epoch'], 4)

    def test_independent_metrics(self):
        from evaluation import independent_recovery
        rng = np.random.default_rng(42)
        for _ in range(20):
            scores = rng.integers(0, 15, 100)
            p = np.arange(100) < 20
            np.testing.assert_allclose(independent_recovery(scores, p),
                                       ranking.rank_metrics(scores, p)[:, :4], rtol=0, atol=1e-12)

    def test_token_join(self):
        from evaluation import align
        np.testing.assert_array_equal(align(np.array(['c', 'a', 'b']), np.array(['b', 'c', 'a'])), [2, 0, 1])

    def test_duplicate_token_rejected(self):
        from evaluation import align
        with self.assertRaises(AssertionError):
            align(np.array(['a', 'a']), np.array(['a', 'b']))


if __name__ == '__main__':
    unittest.main()
