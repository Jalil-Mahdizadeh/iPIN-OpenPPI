"""Synthetic-only final-test harness checks; never load protected data."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import subprocess
import tarfile

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import torch


if Path("/bundle/code/protected_final_core_v1.py").exists():
    CORE = Path("/bundle/code/protected_final_core_v1.py")
else:
    CORE = Path(__file__).resolve().parents[2] / "scripts/benchmark/protected_final_core_v1.py"
spec = importlib.util.spec_from_file_location("protected_final_core", CORE)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class FinalTestFixtures(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2)

    def test_token_is_symmetric_and_cell_specific(self):
        pair = core.pair_identifier("a", "b")
        self.assertEqual(pair, core.pair_identifier("b", "a"))
        self.assertNotEqual(core.token_for("C1_test", pair), core.token_for("C3_test", pair))
        with self.assertRaises(RuntimeError):
            core.pair_identifier("a", "a")

    def test_prediction_order_independent(self):
        table = pa.table({"candidate_token": ["b", "a"], "score": [2., 1.]})
        np.testing.assert_array_equal(core.validate_predictions(pa.array(["a", "b"]), table), [1., 2.])

    def test_bad_predictions_rejected(self):
        for tokens, scores in ((["a", "a"], [1., 2.]), (["a", "c"], [1., 2.]),
                               (["a", "b"], [1., np.nan]), (["a", None], [1., 2.]),
                               (["a"], [1.])):
            with self.subTest(tokens=tokens, scores=scores), self.assertRaises(RuntimeError):
                core.validate_predictions(pa.array(["a", "b"]), pa.table({"candidate_token": tokens, "score": scores}))
        with self.assertRaises(RuntimeError):
            core.validate_predictions(pa.array(["a"]), pa.table({"candidate_token": ["a"], "score": [1.], "label": [1]}))

    def test_ledger_exclusive_and_persistent_after_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            core.write_new(path, {"consumed": True})
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                core.write_new(path, {"consumed": False})
            self.assertEqual(original, path.read_bytes())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_manifest_hash_and_path_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core.write_new(root / "input.json", {"value": 1})
            rec = core.record(root / "input.json", root)
            core.verify_records(root, [rec])
            with self.assertRaises(RuntimeError):
                core.verify_records(root, [{**rec, "sha256": "0" * 64}])
            with self.assertRaises(RuntimeError):
                core.verify_records(root, [{**rec, "path": "../input.json"}])

    def test_head_math_and_swap(self):
        rng = np.random.default_rng(17)
        z = rng.normal(size=(12, 4)).astype(np.float32)
        params = [(rng.normal(size=(1, 13)).astype(np.float32), rng.normal(size=1).astype(np.float32)) for _ in range(3)]
        a, b = np.array([1, 4, 8]), np.array([6, 3, 2])
        observed = core.head_scores(z, params, a, b)
        np.testing.assert_array_equal(observed, core.head_scores(z, params, b, a))
        x, y = z[a], z[b]
        cosine = (x * y).sum(axis=1) / (np.linalg.norm(x, axis=1) * np.linalg.norm(y, axis=1))
        features = np.column_stack((x + y, np.abs(x - y), x * y, cosine))
        expected = np.column_stack([(features @ w.T + bias).ravel() for w, bias in params])
        np.testing.assert_allclose(observed, expected, rtol=2e-6, atol=2e-6)

    def test_interolog_matches_explicit_edges_fp64(self):
        rng = np.random.default_rng(5)
        sim = rng.random((8, 4))
        edges = [(0, 1), (1, 2), (2, 3)]
        neighbor = np.zeros_like(sim)
        for endpoint in range(4):
            adjacent = [v if u == endpoint else u for u, v in edges if endpoint in (u, v)]
            neighbor[:, endpoint] = sim[:, adjacent].max(axis=1)
        a, b = np.array([0, 3, 6]), np.array([7, 1, 4])
        expected = [max(max(min(sim[x, u], sim[y, v]), min(sim[x, v], sim[y, u])) for u, v in edges) for x, y in zip(a, b)]
        np.testing.assert_array_equal(core.interolog(sim, neighbor, a, b), expected)
        np.testing.assert_array_equal(core.interolog(sim, neighbor, a, b), core.interolog(sim, neighbor, b, a))

    def test_bootstrap_matches_bruteforce_paired_reference(self):
        scores = np.array([[.2, .5], [.7, .5], [.2, .5], [.4, .5], [.9, .5], [.7, .5]])
        positive = np.array([1, 1, 0, 0, 0, 0], bool)
        weights = np.array([1., 1., 2/3, 3/2, 7., 5.])
        ca, cb = ["a", "c", "a", "b", "c", "a"], ["a", "a", "c", "b", "a", "b"]
        points, draws, metadata = core.bootstrap_metrics(scores, positive, weights, ca, cb, "fixture", replicates=53, workers=1)
        rng = np.random.Generator(np.random.PCG64DXSM(metadata["seed"]))
        sampled = rng.integers(0, 3, (53, 3), dtype=np.int64)
        reference = np.full((2, 53), np.nan)
        component = {x: i for i, x in enumerate(sorted(set(ca + cb)))}
        for r, sample in enumerate(sampled):
            counts = np.bincount(sample, minlength=3)
            mult = np.array([counts[component[x]] if x == y else counts[component[x]] * counts[component[y]] for x, y in zip(ca, cb)])
            for col in range(2):
                numerator, mass = 0., 0.
                for p in (0, 1):
                    for u in (2, 3, 4, 5):
                        w = mult[p] * mult[u] * weights[u]
                        mass += w
                        numerator += w * ((scores[p, col] > scores[u, col]) + .5 * (scores[p, col] == scores[u, col]))
                if mass:
                    reference[col, r] = numerator / mass
        np.testing.assert_allclose(draws, reference, rtol=1e-14, atol=1e-14, equal_nan=True)
        expected_point = sum(weights[u] * ((scores[p, 0] > scores[u, 0]) + .5 * (scores[p, 0] == scores[u, 0])) for p in (0, 1) for u in (2, 3, 4, 5)) / (2 * weights[2:].sum())
        self.assertAlmostEqual(points[0], expected_point)
        self.assertEqual(points[1], .5)
        self.assertTrue(np.isnan(draws).any())
        self.assertTrue(np.all(draws[1, np.isfinite(draws[1])] == .5))

    def test_real_cms_decryption_hash_and_link_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key, cert, cipher = root / "key.pem", root / "cert.pem", root / "cipher.cms"
            subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key),
                            "-out", str(cert), "-days", "1", "-subj", "/CN=synthetic-only"], check=True, capture_output=True)
            core.write_new(root / "fixture.json", {"synthetic": True})
            archive = root / "fixture.tar"
            with tarfile.open(archive, "w") as handle:
                handle.add(root / "fixture.json", arcname="fixture.json")
            subprocess.run(["openssl", "cms", "-encrypt", "-binary", "-aes-256-cbc", "-outform", "DER",
                            "-in", str(archive), "-out", str(cipher), str(cert)], check=True, capture_output=True)
            entry = {"ciphertext_sha256": core.sha(cipher), "certificate_sha256": core.sha(cert), "plaintext_archive_sha256": core.sha(archive)}
            manifest = {"sealed_packages": {"fixture": entry}}
            out = root / "out"
            out.mkdir()
            core.decrypt("fixture", manifest, out, cipher=cipher, cert=cert, key=key)
            self.assertEqual(core.read(out / "plain/fixture.json"), {"synthetic": True})
            manifest["sealed_packages"]["fixture"]["plaintext_archive_sha256"] = "0" * 64
            with self.assertRaises(RuntimeError):
                core.decrypt("fixture", manifest, out, cipher=cipher, cert=cert, key=key)
            with tarfile.open(archive, "w") as handle:
                info = tarfile.TarInfo("bad-link")
                info.type, info.linkname = tarfile.SYMTYPE, "/etc/passwd"
                handle.addfile(info)
            subprocess.run(["openssl", "cms", "-encrypt", "-binary", "-aes-256-cbc", "-outform", "DER",
                            "-in", str(archive), "-out", str(cipher), str(cert)], check=True, capture_output=True)
            entry.update(ciphertext_sha256=core.sha(cipher), plaintext_archive_sha256=core.sha(archive))
            with self.assertRaises(RuntimeError):
                core.decrypt("fixture", manifest, out, cipher=cipher, cert=cert, key=key)

    def test_synthetic_end_to_end_and_one_first_gate(self):
        cell = "C3_test"
        with tempfile.TemporaryDirectory() as directory, patch.object(core, "CELLS", (cell,)), patch.object(core, "P_COUNTS", {cell: 1}), patch.object(core, "U_ROWS", 2):
            root = Path(directory)
            bundle, session, predictions, freeze, output = [root / name for name in ("bundle", "session", "predictions", "freeze", "output")]
            for folder in (bundle, session, predictions, freeze, output):
                folder.mkdir()
            core.write_new(bundle / "SCORER_FREEZE.json", {"model": core.MODEL, "scorers": list(core.SCORERS), "cells": [cell], "files": [],
                           "sealed_packages": {"protected_candidates": {"plaintext_archive_sha256": "fixture"}}})
            core.write_new(bundle / "features/endpoints.json", ["a", "b", "c"])
            core.write_new(bundle / "features/components.json", ["ca", "cb", "cc"])
            left, right = ["a", "a", "b"], ["b", "c", "c"]
            pairs = [core.pair_identifier(a, b) for a, b in zip(left, right)]
            tokens = [core.token_for(cell, p) for p in pairs]
            candidates = pa.table({"candidate_token": tokens, "endpoint_a_sha256": left, "endpoint_b_sha256": right, "cell_id": [cell] * 3})

            def fixture_decrypt(role, manifest, target):
                if role == "protected_candidates":
                    folder = target / "plain/protected_candidates"
                    folder.mkdir(parents=True)
                    pq.write_table(candidates.append_column("forbidden_metadata", pa.array(["P", "U", "U"])), folder / "part-00000.parquet")
                else:
                    folder = target / "plain/protected_positive_truth"
                    folder.mkdir(parents=True)
                    pq.write_table(pa.table({"candidate_token": tokens[:1], "state": ["released_positive"], "cell_id": [cell]}), folder / "part-00000.parquet")
                    folder = target / "plain/unlabeled_pairs"
                    folder.mkdir(parents=True)
                    pq.write_table(pa.table({"pair_id": pairs[1:], "state": ["unlabeled"] * 2, "cell_id": [cell] * 2,
                                           "sampling_weight_numerator": [3, 2], "sampling_weight_denominator": [2, 1]}), folder / "part-00000.parquet")

            with patch.object(core, "decrypt", fixture_decrypt):
                core.open_candidates(bundle, session)
                projected = pq.read_table(core.cell_path(session / "candidates", cell))
                self.assertEqual(projected.column_names, list(core.COLUMNS))
                self.assertFalse(list(session.glob("candidate-decrypt-*")))
                fake = SimpleNamespace(score=lambda rows, swap=False: np.ones((rows.num_rows, len(core.SCORERS))))
                with patch.object(core, "Scorer", return_value=fake):
                    core.score_all(bundle, session, predictions)
                core.freeze_predictions(bundle, session, predictions, freeze)
                ledger = root / "custody/protected_evaluation_ledger.json"
                core.reserve_attempt(bundle, freeze, ledger)
                with self.assertRaises(FileExistsError):
                    core.reserve_attempt(bundle, freeze, ledger)
                original_read, original_sha = core.read, core.sha
                def mapped_read(path):
                    return original_read(ledger if path == Path("/ledger.json") else path)
                def mapped_sha(path):
                    return original_sha(ledger if path == Path("/ledger.json") else path)
                with patch.object(core, "read", mapped_read), patch.object(core, "sha", mapped_sha):
                    core.evaluate(bundle, session, predictions, freeze, output)
                result = core.read(output / "FINAL_TEST_RESULTS.json")
                self.assertEqual(result["cells"][cell]["metrics"][core.MODEL]["ht_P_vs_U_concordance"], .5)
                self.assertFalse(list(output.glob("truth-decrypt-*")))
                self.assertTrue(core.read(ledger)["truth_access_attempt_irrevocably_consumed"])


if __name__ == "__main__":
    unittest.main(argv=[__file__], verbosity=2)
