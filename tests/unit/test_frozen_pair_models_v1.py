"""Synthetic preservation tests: no benchmark pairs, labels or evaluation entry."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from ipin_openppi.model_optimization.models import PairHead, save_state

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("freeze_pair_models_fixture", ROOT / "scripts/model/freeze_pair_models_v1.py")
freeze = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freeze)


def registry_fixture():
    return {"roles": {"best_performing_model": freeze.BEST, "original_confirmatory_baseline": freeze.BASELINE},
            "models": {name: {"seeds": list(freeze.SEEDS), "members": [{"seed": seed} for seed in freeze.SEEDS],
                               "status": "frozen", "member_weights": [1, 1, 1], "weight_divisor": 3,
                               "parameters_per_head": count,
                               "aggregation": "arithmetic_mean_of_three_FP32_raw_scores_in_FP64"}
                       for name, count in ((freeze.BASELINE, 1922), (freeze.BEST, 498053))},
            "claims": {"conclusive_primary_C3_superiority": False, "optimized_is_original_confirmatory_model": False}}


class PreservationFixtures(unittest.TestCase):
    def test_roles_and_prediction_unit_are_fixed(self):
        original = registry_fixture()
        freeze.validate_roles(original)
        for change in (lambda x: x["roles"].update(best_performing_model=freeze.BASELINE),
                       lambda x: x["models"][freeze.BEST].update(seeds=list(reversed(freeze.SEEDS))),
                       lambda x: x["models"][freeze.BEST].update(member_weights=[2, 1, 1]),
                       lambda x: x["models"][freeze.BEST].update(aggregation="mean_seed_metrics"),
                       lambda x: x["models"][freeze.BASELINE].update(status="retired"),
                       lambda x: x["claims"].update(conclusive_primary_C3_superiority=True),
                       lambda x: x["claims"].update(optimized_is_original_confirmatory_model=True)):
            with self.subTest(change=change):
                value = copy.deepcopy(original)
                change(value)
                with self.assertRaises(RuntimeError):
                    freeze.validate_roles(value)

    def test_state_census_and_invalid_state_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "head.npz"
            with path.open("xb") as handle:
                np.savez(handle, weight=np.zeros((1, 1921), np.float32), bias=np.zeros(1, np.float32))
            self.assertEqual(freeze.validate_state(path, False), 1922)
            model = PairHead(640, {"family": "residual_mlp", "width": 256, "dropout": .3})
            optimized = Path(directory) / "optimized.npz"
            save_state(optimized, model)
            self.assertEqual(freeze.validate_state(optimized, True), 498053)
            for index, state in enumerate((
                {"weight": np.zeros((1, 1921), np.float64), "bias": np.zeros(1, np.float32)},
                {"weight": np.zeros((1, 1920), np.float32), "bias": np.zeros(1, np.float32)},
                {"weight": np.zeros((1, 1921), np.float32), "bias": np.array([np.nan], np.float32)},
                {"unexpected": np.zeros(1, np.float32)},
            )):
                invalid = Path(directory) / f"invalid-{index}.npz"
                with invalid.open("xb") as handle:
                    np.savez(handle, **state)
                with self.assertRaises(RuntimeError):
                    freeze.validate_state(invalid, False)

    def test_exact_copy_exclusive_creation_and_hash_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bin"
            source.write_bytes(b"synthetic frozen model state")
            item = freeze.record(source, root)
            copied = freeze.copy_checked(root, root / "bundle", item, "heads/state.bin")
            self.assertEqual(copied["sha256"], item["sha256"])
            self.assertEqual(copied["source"], item)
            with self.assertRaises(FileExistsError):
                freeze.copy_checked(root, root / "bundle", item, "heads/state.bin")
            source.write_bytes(b"same path, different content")
            with self.assertRaises(RuntimeError):
                freeze.checked_path(root, item)

    def test_paths_cannot_escape_or_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.write_bytes(b"fixture")
            item = freeze.record(source, root)
            for path in ("../source", str(source)):
                with self.assertRaises(RuntimeError):
                    freeze.checked_path(root, {**item, "path": path})
            (root / "link").symlink_to(source)
            with self.assertRaises(RuntimeError):
                freeze.checked_path(root, {**item, "path": "link"})
            with self.assertRaises(RuntimeError):
                freeze.copy_checked(root, root / "bundle", item, "../escape")

    def test_existing_release_cannot_be_recreated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / freeze.PUBLIC).mkdir(parents=True)
            with self.assertRaises(FileExistsError):
                freeze.create(root)

    @unittest.skipUnless(torch.cuda.is_available(), "CUDA required for synthetic ensemble smoke test")
    def test_gpu_eval_raw_score_ensemble_and_symmetric_features(self):
        torch.manual_seed(54)
        torch.set_num_threads(2)
        a, b = torch.randn(8, 640, device="cuda"), torch.randn(8, 640, device="cuda")
        for family, width, dropout in (("linear", 0, 0.), ("residual_mlp", 256, .3)):
            scores = []
            for seed in freeze.SEEDS:
                torch.manual_seed(seed)
                model = PairHead(640, {"family": family, "width": width, "dropout": dropout}).cuda().eval()
                model.requires_grad_(False)
                with torch.inference_mode():
                    first = model(a, b)
                    torch.testing.assert_close(first, model(b, a), rtol=0, atol=0)
                    torch.testing.assert_close(first, model(a, b), rtol=0, atol=0)
                self.assertFalse(first.requires_grad)
                scores.append(first.cpu().numpy().astype(np.float64))
            ensemble = np.column_stack(scores).mean(1, dtype=np.float64)
            np.testing.assert_array_equal(ensemble, (scores[0] + scores[1] + scores[2]) / 3)
