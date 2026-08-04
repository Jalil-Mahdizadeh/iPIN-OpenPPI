from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts/data/verify_raw_acquisition_scoped_v1.py"
SPEC = importlib.util.spec_from_file_location("verify_raw_acquisition_scoped_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScopedRawAcquisitionVerificationTests(unittest.TestCase):
    def _write_manifest(self, root: Path, run_id: str, paths: list[str]) -> None:
        records = []
        for relative in paths:
            records.append(
                {
                    "destination": relative,
                    "sidecar": f"{relative}.acquisition.json",
                }
            )
        path = (
            root
            / "data/source_manifests/acquisitions"
            / run_id
            / "ACQUISITION_MANIFEST.json"
        )
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps({"status": "pass", "errors": [], "records": records}),
            encoding="utf-8",
        )

    def _write_raw_pair(self, root: Path, relative: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"payload")
        Path(f"{path}.acquisition.json").write_text("{}", encoding="utf-8")

    def test_non_uniprot_acquisition_is_explicitly_not_applicable(self) -> None:
        result = MODULE.selected_source_uniprot_metalink(
            [{"source_key": "negatome"}], Path("/")
        )
        self.assertEqual(result["status"], "not_applicable_source_not_selected")
        self.assertEqual(result["selected_sources"], ["negatome"])

    def test_other_manifest_backed_acquisition_is_permitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "data/raw").mkdir(parents=True)
            (root / "data/raw/README.md").write_text("raw", encoding="utf-8")
            first = "data/raw/first/payload.txt"
            second = "data/raw/second/payload.txt"
            self._write_raw_pair(root, first)
            self._write_raw_pair(root, second)
            self._write_manifest(root, "first-run", [first])
            self._write_manifest(root, "second-run", [second])
            expected = {Path(first), Path(f"{first}.acquisition.json")}
            result = MODULE.manifest_backed_raw_tree_inventory(root, expected)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["other_manifest_backed_file_count"], 2)

    def test_unmanifested_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "data/raw").mkdir(parents=True)
            selected = "data/raw/selected/payload.txt"
            self._write_raw_pair(root, selected)
            self._write_manifest(root, "selected-run", [selected])
            unexpected = root / "data/raw/untracked.txt"
            unexpected.write_text("unexpected", encoding="utf-8")
            expected = {Path(selected), Path(f"{selected}.acquisition.json")}
            with self.assertRaises(MODULE.VerificationError):
                MODULE.manifest_backed_raw_tree_inventory(root, expected)


if __name__ == "__main__":
    unittest.main()
