#!/usr/bin/env python3
"""Offline synthetic qualification only: no benchmark data or optimizer steps."""
import argparse
import copy
import csv
from datetime import datetime, timezone
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import random
import socket
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import dscript
import h5py
import numpy as np
from packaging.requirements import Requirement
import torch
from dscript.alphabets import Uniprot21
from dscript.language_model import lm_embed
from dscript.models.interaction import DSCRIPTModel
from dscript.pretrained import get_pretrained


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"started_utc": datetime.now(timezone.utc).isoformat(), "checks": {},
              "scope": "Synthetic inputs only; no iPIN data, no training, no optimizer steps",
              "limitations": []}
    failures = []

    def record(name, func):
        started = time.perf_counter()
        try:
            value = func()
            report["checks"][name] = {"passed": True, "details": value}
        except Exception:
            failures.append(name)
            report["checks"][name] = {"passed": False, "error": traceback.format_exc()}
        report["checks"][name]["seconds"] = time.perf_counter() - started
        (output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n")
        print(name, "PASS" if name not in failures else "FAIL", flush=True)

    def environment():
        assert platform.machine() == "aarch64"
        assert torch.cuda.is_available(), "GPU is required for this qualification"
        assert np.__version__ == "1.26.4"
        assert metadata.version("dscript") == "0.3.1"
        assert os.environ.get("DSCRIPT_TEST_OFFLINE") == "1"
        with socket.socket() as sock:
            try:
                sock.connect(("127.0.0.1", 9))
            except RuntimeError as exc:
                assert "forbids network" in str(exc)
            else:
                raise AssertionError("Python network guard did not activate")
        packages = {d.metadata["Name"]: d.version for d in metadata.distributions()}
        (output / "installed-packages.json").write_text(json.dumps(packages, indent=2, sort_keys=True) + "\n")
        for package in ("dscript", "biotite", "biotraj", "h5py", "loguru", "seaborn"):
            for requirement in metadata.requires(package) or []:
                req = Requirement(requirement)
                if req.marker is None or req.marker.evaluate({"extra": ""}):
                    assert req.specifier.contains(metadata.version(req.name), prereleases=True), (package, requirement)
        return {"architecture": platform.machine(), "python": sys.version,
                "torch": torch.__version__, "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(0), "numpy": np.__version__,
                "gpu_total_bytes": torch.cuda.get_device_properties(0).total_memory,
                "dscript_direct_and_added_dependency_requirements_satisfied": True,
                "python_tcp_networking_denied": True}

    record("environment", environment)
    if "environment" in failures:
        raise SystemExit(1)
    torch.set_num_threads(8)
    torch.manual_seed(20260912)
    np.random.seed(20260912)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.cuda.reset_peak_memory_stats()
    package_dir = Path(dscript.__file__).parent
    weights = Path("/opt/dscript/weights")

    def source_integrity():
        checked = 0
        with ZipFile("/opt/dscript/wheels/dscript-0.3.1-py3-none-any.whl") as archive:
            for name in archive.namelist():
                if name.startswith("dscript/") and name.endswith(".py"):
                    installed = package_dir.parent / name
                    assert installed.read_bytes() == archive.read(name), name
                    checked += 1
        return {"unmodified_upstream_python_files": checked}

    record("unmodified_upstream_source", source_integrity)
    native = get_pretrained("human_v1").cpu().eval()
    native.use_cuda = False
    hf = DSCRIPTModel.from_pretrained(str(weights / "human_v1_hf"), use_cuda=False,
                                     local_files_only=True).cpu().eval()
    lm = get_pretrained("lm_v1").cpu().eval()

    def checkpoint_identity():
        left, right = native.state_dict(), hf.state_dict()
        assert left.keys() == right.keys()
        assert all(torch.equal(left[k], right[k]) for k in left)
        assert native.do_pool == hf.do_pool is True
        assert native.do_w == hf.do_w is True
        assert native.do_sigmoid == hf.do_sigmoid is True
        assert native.pool_size == hf.pool_size == 9
        return {"legacy_and_hf_state_dicts_bitwise_identical": True,
                "state_dict_entries": len(left), "original_model": "human_v1",
                "language_model": "lm_v1", "embedding_dimension": 6165}

    record("original_checkpoint_identity", checkpoint_identity)
    rng = random.Random(20260912)
    sequences = {f"synthetic_{n}": "".join(rng.choices("ACDEFGHIKLMNPQRSTVWY", k=n))
                 for n in (32, 47, 101)}
    names = list(sequences)
    pairs = [(names[0], names[1]), (names[1], names[0]), (names[0], names[2]), (names[2], names[2])]
    (output / "synthetic.fasta").write_text("".join(f">{n}\n{s}\n" for n, s in sequences.items()))
    (output / "synthetic-pairs.tsv").write_text("".join(f"{a}\t{b}\n" for a, b in pairs))
    alphabet = Uniprot21()

    def encode(sequence, device):
        return torch.from_numpy(alphabet.encode(sequence.encode())).long().unsqueeze(0).to(device)

    cpu_embeddings = {}
    gpu_embeddings = {}
    cpu_scores = []
    gpu_scores = []
    lm_gpu = copy.deepcopy(lm).cuda().eval()
    native_gpu = copy.deepcopy(native).cuda().eval()
    native_gpu.use_cuda = True

    def embeddings():
        max_difference = 0.0
        with torch.no_grad():
            for name, sequence in sequences.items():
                cpu = lm.transform(encode(sequence, "cpu"))
                gpu = lm_gpu.transform(encode(sequence, "cuda"))
                assert list(cpu.shape) == [1, len(sequence), 6165]
                assert torch.isfinite(cpu).all() and torch.isfinite(gpu).all()
                torch.testing.assert_close(cpu, gpu.cpu(), rtol=3e-5, atol=3e-5)
                # Native convenience API randomizes an unused projection; transform must be unchanged.
                torch.testing.assert_close(cpu, lm_embed(sequence, use_cuda=False), rtol=0, atol=0)
                assert torch.equal(gpu, lm_gpu.transform(encode(sequence, "cuda")))
                max_difference = max(max_difference, (cpu - gpu.cpu()).abs().max().item())
                cpu_embeddings[name], gpu_embeddings[name] = cpu, gpu
        return {"lengths": [len(s) for s in sequences.values()], "dimension": 6165,
                "cpu_gpu_max_absolute_difference": max_difference,
                "gpu_repeat_bitwise_identical": True, "native_api_matches_direct_transform": True}

    record("bepler_berger_cpu_gpu_embeddings", embeddings)

    def predictions():
        with torch.no_grad():
            for a, b in pairs:
                score = native.predict(cpu_embeddings[a], cpu_embeddings[b])
                hf_score = hf.predict(cpu_embeddings[a], cpu_embeddings[b])
                gpu_score = native_gpu.predict(gpu_embeddings[a], gpu_embeddings[b])
                torch.testing.assert_close(score, hf_score, rtol=0, atol=0)
                torch.testing.assert_close(score, gpu_score.cpu(), rtol=3e-5, atol=1e-5)
                assert torch.isfinite(score) and 0 <= score.item() <= 1
                assert torch.equal(gpu_score, native_gpu.predict(gpu_embeddings[a], gpu_embeddings[b]))
                cpu_scores.append(score.item())
                gpu_scores.append(gpu_score.item())
        assert abs(gpu_scores[0] - gpu_scores[1]) < 1e-6
        with (output / "synthetic-scores.csv").open("x", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["protein_a", "protein_b", "original_cpu_score", "original_gpu_score"])
            writer.writerows((a, b, c, g) for (a, b), c, g in zip(pairs, cpu_scores, gpu_scores))
        return {"pairs": len(pairs), "cpu_gpu_max_absolute_score_difference":
                max(abs(c - g) for c, g in zip(cpu_scores, gpu_scores)),
                "reversed_pair_absolute_difference": abs(gpu_scores[0] - gpu_scores[1]),
                "legacy_hf_predictions_bitwise_identical": True, "gpu_repeat_bitwise_identical": True}

    record("original_checkpoint_cpu_gpu_inference", predictions)

    def cli():
        commands = [
            ["dscript", "embed", "--seqs", str(output / "synthetic.fasta"),
             "--outfile", str(output / "cli-embeddings.h5"), "--device", "0"],
            ["dscript", "predict_serial", "--pairs", str(output / "synthetic-pairs.tsv"),
             "--embeddings", str(output / "cli-embeddings.h5"), "--model", str(weights / "human_v1_hf"),
             "--outfile", str(output / "cli-predictions"), "--device", "0", "--load_proc", "1"],
        ]
        for index, command in enumerate(commands):
            with (output / f"cli-{index}.log").open("x") as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, cwd=output, timeout=240)
        with h5py.File(output / "cli-embeddings.h5", "r") as handle:
            assert set(handle) == set(sequences)
            for name in sequences:
                np.testing.assert_allclose(handle[name][:], gpu_embeddings[name].cpu().numpy(), rtol=3e-5, atol=3e-5)
        rows = list(csv.reader((output / "cli-predictions.tsv").open(), delimiter="\t"))
        assert len(rows) == len(pairs), "Native CLI can skip failed pairs; row count must be checked"
        for row, pair, expected in zip(rows, pairs, gpu_scores):
            assert tuple(row[:2]) == pair
            assert abs(float(row[2]) - expected) < 1e-5
        return {"offline_native_embed_and_predict_serial": True, "rows_expected": len(pairs), "rows_written": len(rows)}

    record("offline_native_cli", cli)

    def blocked_cli():
        # The newer blocked CLI canonicalizes/deduplicates pairs and excludes self-pairs.
        # Test its supported unique, non-self case separately from the row-preserving serial CLI.
        unique_pairs = [(names[0], names[1]), (names[0], names[2]), (names[1], names[2])]
        (output / "synthetic-unique-pairs.tsv").write_text("".join(f"{a}\t{b}\n" for a, b in unique_pairs))
        command = ["dscript", "predict", "--pairs", str(output / "synthetic-unique-pairs.tsv"),
                   "--embeddings", str(output / "cli-embeddings.h5"), "--model", str(weights / "human_v1_hf"),
                   "--outfile", str(output / "cli-blocked-predictions"), "--device", "0", "--load_proc", "1"]
        with (output / "cli-blocked.log").open("x") as log:
            # A separate process group makes timeout cleanup apply only to this test and its children.
            process = subprocess.Popen(command, cwd=output, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                returncode = process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                import signal
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=15)
                raise
        assert returncode == 0
        rows = list(csv.reader((output / "cli-blocked-predictions.tsv").open(), delimiter="\t"))
        assert len(rows) == len(unique_pairs)
        observed = {tuple(sorted(row[:2])): float(row[2]) for row in rows}
        assert set(observed) == {tuple(sorted(p)) for p in unique_pairs}
        with torch.no_grad():
            for a, b in unique_pairs:
                expected = native_gpu.predict(gpu_embeddings[a], gpu_embeddings[b]).item()
                assert abs(observed[tuple(sorted((a, b)))] - expected) < 1e-5
        return {"offline_single_gpu_blocked_predict": True, "unique_nonself_pairs": len(rows),
                "coverage_note": "Duplicates and self-pairs must use a row-aware adapter/serial path; blocked CLI not qualified for them"}

    record("offline_native_blocked_cli_unique_pairs", blocked_cli)

    def boundary():
        assert native.xx.numel() == 2000
        timings = {}
        with torch.no_grad():
            for length in (2000, 2001, 7570):
                sequence = "".join(rng.choices("ACDEFGHIKLMNPQRSTVWY", k=length))
                torch.cuda.synchronize()
                start = time.perf_counter()
                embedded = lm_gpu.transform(encode(sequence, "cuda"))
                torch.cuda.synchronize()
                timings[str(length)] = time.perf_counter() - start
                assert list(embedded.shape) == [1, length, 6165] and torch.isfinite(embedded).all()
                if length == 2000:
                    assert torch.isfinite(native_gpu.predict(embedded, gpu_embeddings[names[0]]))
                elif length == 2001:
                    try:
                        native_gpu.predict(embedded, gpu_embeddings[names[0]])
                    except RuntimeError as exc:
                        message = str(exc)
                        assert "2000" in message and "2001" in message
                    else:
                        raise AssertionError("Expected upstream 2,000-residue positional-array limit did not occur")
                del embedded
        report["limitations"].append({"type": "upstream_predictor_length_limit", "maximum_residues": 2000,
                                      "tested_failure_residues": 2001, "error": message,
                                      "action": "No patch, cropping, or excluded benchmark rows; resolve before full benchmarking"})
        return {"encoder_tested_lengths": [2000, 2001, 7570], "encoder_seconds": timings,
                "predictor_2000_by_32_passed": True, "predictor_2001_by_32_expected_failure": message}

    record("native_length_boundary_characterized", boundary)

    def upstream_tests():
        test_dir = package_dir / "tests"
        selected = [str(test_dir / f"test_{name}.py") for name in
                    ("alphabets", "models_contact", "models_embedding", "models_interaction")]
        selected += [str(test_dir / "test_pretrained.py") + "::TestModelBuilders::" + test
                     for test in ("test_build_lm_1", "test_build_human_1")]
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "--basetemp", str(output / "pytest-tmp"), "--junitxml", str(output / "upstream-tests.xml"), *selected]
        with (output / "upstream-tests.log").open("x") as log:
            result = subprocess.run(command, cwd=output, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        root = ET.parse(output / "upstream-tests.xml").getroot()
        suites = list(root.iter("testsuite"))
        counts = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
        report["upstream_test_counts"] = counts
        assert result.returncode == 0, f"Upstream tests failed: {counts}; see upstream-tests.log"
        return counts

    record("selected_upstream_unit_tests", upstream_tests)
    report["gpu_peak_allocated_bytes_main_process"] = torch.cuda.max_memory_allocated()
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    report["failed_checks"] = failures
    report["container_smoke_tests_passed"] = not failures
    report["full_benchmark_ready"] = False
    report["next_action"] = "Report to user and stop; resolve upstream length limit before benchmark work"
    (output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"container_smoke_tests_passed": not failures, "failed_checks": failures,
                      "limitations": report["limitations"]}), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
