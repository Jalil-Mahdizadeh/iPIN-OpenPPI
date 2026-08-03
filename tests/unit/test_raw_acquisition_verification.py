from __future__ import annotations

import gzip
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts/data/verify_raw_acquisition.py"
SPEC = importlib.util.spec_from_file_location("verify_raw_acquisition", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RawAcquisitionVerificationTests(unittest.TestCase):
    def test_huri_pair_count_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pairs.tsv"
            path.write_text("a\tb\n", encoding="utf-8")
            with self.assertRaises(MODULE.VerificationError):
                MODULE.text_inventory(path, "huri_pairs")

    def test_fasta_inventory_counts_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sequences.fasta.gz"
            with gzip.open(path, "wb") as handle:
                handle.write(b">A\nAAAA\n>B\nBBBB\n")
            result = MODULE.gzip_inventory(path, "canonical_fasta")
            self.assertEqual(result["prefix_count"], 2)
            self.assertEqual(result["line_count"], 4)

    def test_zip_inventory_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as handle:
                handle.writestr("../escape", "bad")
            with self.assertRaises(MODULE.VerificationError):
                MODULE.zip_inventory(path)

    def test_metalink_local_name(self) -> None:
        self.assertEqual(MODULE.local_name("{urn:test}version"), "version")
        self.assertEqual(MODULE.local_name("version"), "version")


if __name__ == "__main__":
    unittest.main()
