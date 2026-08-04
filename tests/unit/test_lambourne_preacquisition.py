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
    "validate_preacquisition_manifests_lambourne_test",
    "scripts/data/validate_preacquisition_manifests.py",
)
ACQUIRER = load_script(
    "acquire_manifest_assets_lambourne_test",
    "scripts/data/acquire_manifest_assets.py",
)


class LambournePreacquisitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest_path = (
            PROJECT_ROOT
            / "data/source_manifests/PREACQUISITION_lambourne_human_y2h_v1.yaml"
        )
        self.index_path = (
            PROJECT_ROOT / "data/source_manifests/PREACQUISITION_INDEX_v5.yaml"
        )
        self.manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        self.index = yaml.safe_load(self.index_path.read_text(encoding="utf-8"))

    def test_manifest_passes_source_specific_semantic_guards(self) -> None:
        checks, errors, _, summary = VALIDATOR.validate_manifest(
            PROJECT_ROOT,
            "lambourne_human_y2h",
            self.manifest_path,
        )
        self.assertEqual(errors, [])
        self.assertEqual(summary["asset_count"], 11)
        self.assertTrue(all(check["passed"] for check in checks))

    def test_training_merging_splits_and_universal_claims_are_prohibited(self) -> None:
        guards = self.manifest["guards"]
        self.assertFalse(guards["outcomes_as_training_labels"])
        self.assertFalse(guards["merge_with_negatome"])
        self.assertFalse(guards["benchmark_split_construction"])
        self.assertFalse(guards["technical_or_na_outcome_is_negative"])
        self.assertFalse(guards["universal_nonbinding_interpretation"])
        authorization = self.index["authorization"]
        self.assertFalse(authorization["label_construction_permitted"])
        self.assertFalse(authorization["benchmark_integration_permitted"])
        self.assertFalse(authorization["benchmark_split_construction_permitted"])
        self.assertFalse(authorization["model_training_permitted"])

    def test_all_assets_are_required_unique_and_versioned(self) -> None:
        assets = self.manifest["assets"]
        self.assertTrue(all(asset["required"] for asset in assets))
        self.assertEqual(len({asset["asset_id"] for asset in assets}), len(assets))
        self.assertEqual(
            len({asset["destination"] for asset in assets}),
            len(assets),
        )
        self.assertTrue(
            all(
                "record-19118078-v2.1" in asset["destination"]
                for asset in assets
                if asset["asset_id"].startswith("archived_")
                or asset["asset_id"] == "zenodo_record_metadata"
            )
        )

    def test_only_scoped_new_hosts_are_whitelisted(self) -> None:
        self.assertIn("zenodo.org", ACQUIRER.ALLOWED_HOSTS)
        self.assertIn("www.ebi.ac.uk", ACQUIRER.ALLOWED_HOSTS)
        self.assertNotIn("github.com", ACQUIRER.ALLOWED_HOSTS)
        self.assertNotIn("example.com", ACQUIRER.ALLOWED_HOSTS)

    def test_zenodo_provider_checksums_are_pinned(self) -> None:
        by_id = {asset["asset_id"]: asset for asset in self.manifest["assets"]}
        self.assertEqual(
            by_id["archived_code_v1_1"]["expected"]["provider_checksum"],
            {"algorithm": "md5", "value": "d10626b8c369113995f9aa1db3d63a62"},
        )
        self.assertEqual(
            by_id["archived_input_data_v2_1"]["expected"]["provider_checksum"],
            {"algorithm": "md5", "value": "db2a81cb84dca6f4e4d2227ea67bbf17"},
        )

    def test_optional_last_modified_omission_is_not_a_false_mismatch(self) -> None:
        expected = {"last_modified": "Fri, 20 Mar 2026 01:01:00 GMT"}
        observed = {
            "http_status": 200,
            "final_url": "https://zenodo.org/api/records/19118078/files/file/content",
            "content_length": None,
            "etag": None,
            "last_modified": None,
        }
        ACQUIRER.verify_response_metadata(expected, observed)
        observed["last_modified"] = "Fri, 20 Mar 2025 01:01:00 GMT"
        with self.assertRaises(ACQUIRER.AcquisitionError):
            ACQUIRER.verify_response_metadata(expected, observed)


if __name__ == "__main__":
    unittest.main()
