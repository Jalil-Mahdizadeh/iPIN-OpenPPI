"""Exercise scientific failure modes introduced by the third U stratum."""
import unittest
import numpy as np

from analysis_outputs import candidate_list, SETS
from metrics import evaluate
from selection import candidate_evidence, pair_evidence


def protein(location, hpa="", signal="", transmembrane=False):
    return {"location": location.lower(), "location_raw": location,
            "transmembrane": transmembrane, "signal_peptide": signal,
            "hpa": {"Supported": hpa}}


class ExtensionTests(unittest.TestCase):
    def test_multilocalization_and_membrane_veto(self):
        for p in (protein("Mitochondrion matrix. Cytoplasm."),
                  protein("Mitochondrion matrix.", "Mitochondria;Cytosol"),
                  protein("Mitochondrion matrix.", "Mitochondria", transmembrane=True)):
            self.assertIsNone(candidate_evidence(p))
        self.assertIsNone(candidate_evidence(protein("Secreted.")))

    def test_receptor_sides_and_secondary_location_are_not_ignored(self):
        matrix = protein("Mitochondrion matrix {ECO:0000269|PubMed:1}.", "Mitochondria")
        self.assertIsNone(pair_evidence("TP53", matrix, True))
        self.assertIsNone(pair_evidence("EGFR", matrix, False))
        self.assertEqual(pair_evidence("EGFR", matrix, True)["evidence_tier"], "B_secondary_location_overlap")
        secreted = protein("Secreted.", signal="SIGNAL 1..20")
        self.assertIsNone(pair_evidence("ERN1", secreted, True))
        self.assertIsNone(pair_evidence("EGFR", secreted, True))
        self.assertIsNone(pair_evidence("TNFRSF1A", secreted, True))
        self.assertTrue(pair_evidence("BCL2", secreted, True)["evidence_tier"].startswith("A_"))

    def test_all_sets_and_exposed_pairs_removal(self):
        base = {"prior_train_development_pair": False, "original_tuna_prior_pair": False,
                "development_exposed_positive": False, "homomeric": False}
        p = {**base, "class": "P", "U_stratum": ""}
        u = [{**base, "class": "U", "U_stratum": s} for s in ("context", "background", "low_plausibility")]
        self.assertEqual([len(candidate_list([p] + u, "all_P", name)) for name in SETS], [2, 2, 2, 3, 4])
        p["original_tuna_prior_pair"] = True
        u[0]["original_tuna_prior_pair"] = True
        result = candidate_list([p] + u, "exclude_any_model_prior_pairs", "all_U")
        self.assertEqual(len(result), 2)
        self.assertTrue(all(r["class"] == "U" for r in result))

    def test_concordance_mixture_and_added_U_rank_effect(self):
        positive = [2., 5.]
        strata = ([3., 4.], [1., 5.], [-1., 2.])
        def run(u):
            return evaluate(positive + list(u), np.array([True] * 2 + [False] * len(u)), (2,))
        separate = [run(u) for u in strata]
        joined = run(sum((list(u) for u in strata), []))
        self.assertAlmostEqual(joined["P_vs_U_concordance"], np.mean([r["P_vs_U_concordance"] for r in separate]))
        self.assertLessEqual(joined["recovered_P_at_2"], run(strata[0] + strata[1])["recovered_P_at_2"])


if __name__ == "__main__":
    unittest.main()
