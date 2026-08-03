from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts/data/verify_raw_acquisition_v3.py"
SPEC = importlib.util.spec_from_file_location("verify_raw_acquisition_v3", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProviderCountSemanticsTests(unittest.TestCase):
    def test_advertised_count_difference_is_recorded_not_hidden(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "HuRI.tsv"
            path.write_text("A\tB\nC\tD\n", encoding="utf-8")
            result = MODULE.discrepancy_aware_text_inventory(path, "huri_pairs")
            self.assertEqual(result["portal_advertised_interaction_count"], 52569)
            self.assertEqual(result["downloaded_tsv_row_count"], 2)
            self.assertEqual(result["row_count_minus_advertised_count"], 2 - 52569)
            self.assertFalse(result["advertised_count_matches_tsv_rows"])

    def test_matching_provider_count_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.tsv"
            path.write_text("A\tB\n" * 1159, encoding="utf-8")
            result = MODULE.discrepancy_aware_text_inventory(
                path, "test_space_screen_pairs"
            )
            self.assertTrue(result["advertised_count_matches_tsv_rows"])
            self.assertEqual(result["row_count_minus_advertised_count"], 0)


if __name__ == "__main__":
    unittest.main()
