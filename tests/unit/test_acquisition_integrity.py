from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts/data/acquire_manifest_assets.py"
SPEC = importlib.util.spec_from_file_location("acquire_manifest_assets", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AcquisitionIntegrityTests(unittest.TestCase):
    def test_destination_must_remain_beneath_raw_zone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            raw = root / "data/raw"
            raw.mkdir(parents=True)
            destination = MODULE.resolve_destination(root, raw, "data/raw/source/release/file.tsv")
            self.assertEqual(destination, raw / "source/release/file.tsv")
            with self.assertRaises(MODULE.AcquisitionError):
                MODULE.resolve_destination(root, raw, "data/raw/../../escape.tsv")

    def test_destination_rejects_symlinked_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory).resolve()
            raw = root / "data/raw"
            raw.mkdir(parents=True)
            (raw / "linked").symlink_to(Path(external), target_is_directory=True)
            with self.assertRaises(MODULE.AcquisitionError):
                MODULE.resolve_destination(root, raw, "data/raw/linked/file.tsv")

    def test_safe_zip_is_inspected_without_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "safe.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
                handle.writestr("folder/data.txt", "safe payload")
            result = MODULE.inspect_payload(archive, "psi_mi_xml_3_zip")
            self.assertEqual(result["detected_container_format"], "zip")
            self.assertEqual(result["archive"]["member_count"], 1)
            self.assertFalse(result["archive"]["extracted"])

    def test_zip_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "unsafe.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
                handle.writestr("../escape.txt", "unsafe payload")
            with self.assertRaises(MODULE.AcquisitionError):
                MODULE.inspect_zip(archive)

    def test_format_detection_and_declared_container(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = Path(directory) / "data.tsv"
            text.write_text("a\tb\n", encoding="utf-8")
            self.assertEqual(MODULE.detect_format(text), "text")
            with self.assertRaises(MODULE.AcquisitionError):
                MODULE.inspect_payload(text, "fasta_gzip")

    def test_negatome_https_opener_uses_pinned_verified_certificate(self) -> None:
        opener, record = MODULE.build_https_opener(
            PROJECT_ROOT,
            "https://mips.helmholtz-muenchen.de/proj/ppi/negatome/manual.txt",
        )
        self.assertIsNotNone(opener)
        self.assertTrue(record["hostname_verification"])
        self.assertTrue(record["certificate_verification"])
        self.assertFalse(record["insecure_mode"])
        self.assertEqual(
            record["additional_ca_pem_sha256"],
            "cdc78c3185ce918c8e87f9b2559197d641288e564c5a8b789cd796abdea298d4",
        )



if __name__ == "__main__":
    unittest.main()
