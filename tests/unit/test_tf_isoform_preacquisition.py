from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str, relative: str):
    path = PROJECT_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_script(
    "validate_preacquisition_manifests_tf_isoform_test",
    "scripts/data/validate_preacquisition_manifests.py",
)
ACQUIRER = load_script(
    "acquire_manifest_assets_tf_isoform_test",
    "scripts/data/acquire_manifest_assets.py",
)


class TFIsoformPreacquisitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest_path = (
            PROJECT_ROOT
            / "data/source_manifests/PREACQUISITION_tf_isoform_y2h_2025_v1.yaml"
        )
        self.index_path = PROJECT_ROOT / "data/source_manifests/PREACQUISITION_INDEX_v6.yaml"
        self.manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        self.index = yaml.safe_load(self.index_path.read_text(encoding="utf-8"))

    def test_manifest_passes_source_specific_guards(self) -> None:
        checks, errors, _, summary = VALIDATOR.validate_manifest(
            PROJECT_ROOT, "tf_isoform_y2h_2025", self.manifest_path
        )
        self.assertEqual(errors, [])
        self.assertEqual(summary["asset_count"], 5)
        self.assertTrue(all(check["passed"] for check in checks))

    def test_fail_closed_and_nonintegration_boundaries(self) -> None:
        guards = self.manifest["guards"]
        self.assertFalse(guards["blank_or_unresolved_outcome_is_negative"])
        self.assertFalse(guards["technical_failure_is_negative"])
        self.assertFalse(guards["outcomes_as_training_labels"])
        self.assertFalse(guards["merge_with_negatome"])
        self.assertFalse(guards["benchmark_construction"])
        self.assertFalse(guards["universal_nonbinding_interpretation"])
        self.assertTrue(guards["preserve_ad_to_db_orientation"])
        self.assertTrue(guards["keep_y2h_and_n2h_separate"])

    def test_minimal_assets_and_provider_checksums_are_pinned(self) -> None:
        assets = self.manifest["assets"]
        self.assertEqual(len(assets), 5)
        self.assertTrue(all(asset["required"] for asset in assets))
        by_id = {asset["asset_id"]: asset for asset in assets}
        self.assertEqual(
            by_id["zenodo_code_and_supplement_v2_1_0"]["expected"]["provider_checksum"],
            {"algorithm": "md5", "value": "b37ea7aa87602527ec6e963e3d2c2c00"},
        )
        self.assertEqual(
            by_id["zenodo_input_data_v2"]["expected"]["provider_checksum"],
            {"algorithm": "md5", "value": "4a2144e5bc86a840e630518f10ae17b9"},
        )

    def test_only_needed_new_host_is_whitelisted(self) -> None:
        self.assertIn("ccsb.dana-farber.org", ACQUIRER.ALLOWED_HOSTS)
        self.assertNotIn("tfisodb.org", ACQUIRER.ALLOWED_HOSTS)
        self.assertNotIn("github.com", ACQUIRER.ALLOWED_HOSTS)

    def test_index_preserves_global_prohibitions(self) -> None:
        authorization = self.index["authorization"]
        self.assertFalse(authorization["label_construction_permitted"])
        self.assertFalse(authorization["benchmark_integration_permitted"])
        self.assertFalse(authorization["benchmark_split_construction_permitted"])
        self.assertFalse(authorization["model_training_permitted"])
        self.assertFalse(authorization["model_tuning_calibration_thresholding_permitted"])
        self.assertFalse(authorization["primary_pu_r_design_change_permitted"])


if __name__ == "__main__":
    unittest.main()
