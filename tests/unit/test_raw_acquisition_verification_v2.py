from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts/data/verify_raw_acquisition_v2.py"
SPEC = importlib.util.spec_from_file_location("verify_raw_acquisition_v2", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HardenedRawPathTests(unittest.TestCase):
    def test_regular_repository_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / "data/raw/source/file.dat"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"payload")
            self.assertEqual(
                MODULE.ensure_repo_path(root, "data/raw/source/file.dat", "data/raw/"),
                path,
            )

    def test_symlinked_parent_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory).resolve()
            raw = root / "data/raw"
            raw.mkdir(parents=True)
            external_file = Path(external) / "file.dat"
            external_file.write_bytes(b"payload")
            (raw / "linked").symlink_to(Path(external), target_is_directory=True)
            with self.assertRaises(MODULE.VerificationError):
                MODULE.ensure_repo_path(root, "data/raw/linked/file.dat", "data/raw/")

    def test_direct_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            raw = root / "data/raw"
            raw.mkdir(parents=True)
            target = raw / "target.dat"
            target.write_bytes(b"payload")
            (raw / "linked.dat").symlink_to(target)
            with self.assertRaises(MODULE.VerificationError):
                MODULE.ensure_repo_path(root, "data/raw/linked.dat", "data/raw/")


if __name__ == "__main__":
    unittest.main()
