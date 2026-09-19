"""Small independent tests for panel identity and tie-aware comparison metrics."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name("run_comparison.py")
SPEC = importlib.util.spec_from_file_location("six_target_comparison", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ComparisonTests(unittest.TestCase):
    def test_perfect_order(self):
        self.assertEqual(MODULE.concordance([3, 4], [1, 2]), 1.)

    def test_reverse_order(self):
        self.assertEqual(MODULE.concordance([1, 2], [3, 4]), 0.)

    def test_ties_half_credit(self):
        self.assertEqual(MODULE.concordance([1], [1, 1]), .5)
        self.assertEqual(MODULE.concordance([2], [1, 2, 3]), .5)

    def test_empty_class_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.concordance([], [1])

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.concordance([float("nan")], [1])

    def test_midrank_and_topk_tie_credit(self):
        self.assertEqual(MODULE.ranks(2, [3, 2, 2, 1], k=2), (2, 3, 2.5, .5))

    def test_rank_boundaries(self):
        self.assertEqual(MODULE.ranks(4, [1, 2, 3, 4], k=1), (1, 1, 1., 1.))
        self.assertEqual(MODULE.ranks(1, [1, 2, 3, 4], k=1), (4, 4, 4., 0.))

    def test_actual_input_identity(self):
        rows, files, expected = MODULE.load_panels(SCRIPT.resolve().parents[2])
        self.assertEqual(len(rows), 1919)
        self.assertEqual(len(files), 12)
        self.assertEqual(sum(r["class"] == "P" for r in rows), 19)
        self.assertEqual(sum(r["development_exposed_positive"] for r in rows), 1)
        self.assertEqual(sum(r["homomeric"] for r in rows), 1)
        self.assertTrue(expected)
        for gene in MODULE.TARGETS:
            panel = [r for r in rows if r["query_gene"] == gene]
            self.assertEqual(len(panel), 404 if gene == "ERN1" else 303)
            self.assertEqual(len({r["partner_uniprot"] for r in panel}), len(panel))
            for p in (r for r in panel if r["class"] == "P"):
                own = [r for r in panel if r["class"] == "U" and r["anchor_positive_uniprot"] == p["partner_uniprot"]]
                self.assertEqual(len(own), 100)
                self.assertEqual(sum(r["U_stratum"] == "context" for r in own), 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
