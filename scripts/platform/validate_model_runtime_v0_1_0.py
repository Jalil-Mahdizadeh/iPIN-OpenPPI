#!/usr/bin/env python3
"""Independent validation of the DEC-0029 model runtime and model custody."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import random
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any


PROTOCOL_SHA256 = "3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5"
SIF_SHA256 = "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"
SIF_BYTES = 10_656_620_544
PARENT_SIF_SHA256 = "9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5"
EXPECTED_FILES = {
    "README.md",
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer_config.json",
    "vocab.txt",
}
CANDIDATES = {
    "esm2_150m": {
        "revision": "a695f6045e2e32885fa60af20c13cb35398ce30c",
        "weight_sha256": "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566",
        "weight_bytes": 595_257_706,
        "hidden_size": 640,
        "layers": 30,
    },
    "esm2_650m": {
        "revision": "08e4846e537177426273712802403f7ba8261b6c",
        "weight_sha256": "a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0",
        "weight_bytes": 2_609_506_392,
        "hidden_size": 1280,
        "layers": 33,
    },
}
FORBIDDEN_PATH_FRAGMENTS = (
    "/sealed/",
    "development_release.cms",
    "protected_candidates.cms",
    "protected_truth.cms",
    "/.private/",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def inside_fixture(args: argparse.Namespace) -> int:
    import numpy as np
    import torch
    from transformers import EsmForMaskedLM, EsmTokenizer

    assert platform.machine() == "aarch64"
    assert torch.__version__ == "2.8.0a0+34c6371d24.nv25.08"
    expected_versions = {
        "huggingface-hub": "0.34.4",
        "numpy": "1.26.4",
        "pyarrow": "19.0.1",
        "safetensors": "0.6.2",
        "scikit-learn": "1.6.1",
        "tokenizers": "0.21.4",
        "transformers": "4.55.2",
    }
    assert {name: importlib.metadata.version(name) for name in expected_versions} == expected_versions
    assert torch.cuda.is_available() and torch.cuda.device_count() == 1
    assert os.environ.get("HF_HUB_OFFLINE") == "1"
    assert os.environ.get("TRANSFORMERS_OFFLINE") == "1"

    seed = 20260831
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    random.seed(seed)
    np.random.default_rng(np.random.PCG64DXSM(seed))
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False

    original_socket = socket.socket

    def blocked_socket(*unused_args: Any, **unused_kwargs: Any) -> Any:
        raise RuntimeError("network socket prohibited during model use")

    socket.socket = blocked_socket
    results: dict[str, Any] = {}
    sequence = "MKTAYIAKQRQISFVKSHFSRQDILDLWIYHTQGYFP"
    try:
        for candidate_id, expected in CANDIDATES.items():
            model_root = args.model_cache / candidate_id
            tokenizer = EsmTokenizer.from_pretrained(
                model_root, local_files_only=True, trust_remote_code=False
            )
            checkpoint_model, loading = EsmForMaskedLM.from_pretrained(
                model_root,
                local_files_only=True,
                output_loading_info=True,
                trust_remote_code=False,
                use_safetensors=True,
                torch_dtype=torch.float32,
            )
            assert loading["missing_keys"] == []
            assert loading["unexpected_keys"] == []
            assert loading["mismatched_keys"] == []
            assert checkpoint_model.esm.pooler is None
            assert checkpoint_model.config.hidden_size == expected["hidden_size"]
            assert checkpoint_model.config.num_hidden_layers == expected["layers"]
            backbone = checkpoint_model.esm.cuda().eval()
            for parameter in backbone.parameters():
                parameter.requires_grad_(False)
            assert all(not parameter.requires_grad for parameter in backbone.parameters())
            encoded = tokenizer(sequence, return_tensors="pt", add_special_tokens=True)
            encoded = {key: value.cuda() for key, value in encoded.items()}
            with torch.inference_mode():
                first = backbone(**encoded).last_hidden_state[0, 1 : 1 + len(sequence)].float().mean(0)
                second = backbone(**encoded).last_hidden_state[0, 1 : 1 + len(sequence)].float().mean(0)
            difference = float(torch.max(torch.abs(first - second)).cpu())
            assert first.shape == (expected["hidden_size"],)
            assert torch.isfinite(first).all()
            assert difference <= 1e-6
            result = {
                "deterministic_repeat_max_absolute_difference": difference,
                "finite": True,
                "hidden_size": expected["hidden_size"],
                "loading_keys_exact": True,
                "pooler_instantiated": False,
            }
            if candidate_id == "esm2_650m":
                backbone.to(dtype=torch.bfloat16)
                with torch.inference_mode():
                    bf16 = backbone(**encoded).last_hidden_state[0, 1 : 1 + len(sequence)].float().mean(0)
                assert bf16.shape == (1280,) and torch.isfinite(bf16).all()
                result["bfloat16_finite"] = True
            results[candidate_id] = result
            del first, second, backbone, checkpoint_model, tokenizer, encoded
            torch.cuda.empty_cache()
    finally:
        socket.socket = original_socket

    torch.manual_seed(seed)
    parameter = torch.nn.Parameter(torch.tensor([0.75, -0.25], device="cuda"))
    optimizer = torch.optim.AdamW([parameter], lr=1e-3, weight_decay=1e-4)

    def train_step() -> tuple[float, torch.Tensor]:
        optimizer.zero_grad(set_to_none=True)
        loss = ((parameter * torch.tensor([1.25, -0.5], device="cuda")).sum() - 0.2).square()
        loss.backward()
        optimizer.step()
        return float(loss.detach().cpu()), parameter.detach().cpu().clone()

    train_step()
    buffer = io.BytesIO()
    torch.save(
        {
            "parameter": parameter.detach().cpu(),
            "optimizer": optimizer.state_dict(),
            "cpu_rng": torch.get_rng_state(),
            "cuda_rng": torch.cuda.get_rng_state_all(),
        },
        buffer,
    )
    expected_loss, expected_parameter = train_step()
    buffer.seek(0)
    restored = torch.load(buffer, map_location="cuda", weights_only=False)
    with torch.no_grad():
        parameter.copy_(restored["parameter"].cuda())
    optimizer.load_state_dict(restored["optimizer"])
    torch.set_rng_state(restored["cpu_rng"].cpu())
    torch.cuda.set_rng_state_all([state.cpu() for state in restored["cuda_rng"]])
    observed_loss, observed_parameter = train_step()
    restart_exact = expected_loss == observed_loss and torch.equal(expected_parameter, observed_parameter)
    assert restart_exact

    print(
        json.dumps(
            {
                "architecture": platform.machine(),
                "candidates": results,
                "checkpoint_restart_exact": restart_exact,
                "gpu_count": torch.cuda.device_count(),
                "gpu_name": torch.cuda.get_device_name(0),
                "network_socket_blocked_during_load_and_forward": True,
                "versions": expected_versions,
            },
            sort_keys=True,
        )
    )
    return 0


def check_record(checks: list[dict[str, str]], check_id: str, detail: str) -> None:
    checks.append({"check_id": check_id, "detail": detail, "status": "pass"})


def host_validation(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve(strict=True)
    sif = project_root / "containers/images/ipin-model-arm64_0.1.0.sif"
    evidence_root = project_root / "artifacts/validation/model_execution/stage1_model_execution_v1"
    custody_path = evidence_root / "MODEL_CUSTODY_MANIFEST.json"
    qualification_path = evidence_root / "MODEL_RUNTIME_QUALIFICATION_REPORT.json"
    checks: list[dict[str, str]] = []

    assert sif.stat().st_size == SIF_BYTES and sha256_file(sif) == SIF_SHA256
    check_record(checks, "sif_identity", f"{SIF_BYTES} bytes; SHA-256 {SIF_SHA256}")

    inspection = json.loads(
        subprocess.check_output(["apptainer", "inspect", "--json", str(sif)], text=True)
    )
    labels = inspection["data"]["attributes"]["labels"]
    assert "aarch64" in labels["ipin.architecture"]
    assert PARENT_SIF_SHA256 in labels["ipin.model.image.parent.sif.sha256"]
    assert PROTOCOL_SHA256 in labels["ipin.model.image.protocol.configuration.sha256"]
    check_record(checks, "sif_labels", "architecture, parent, protocol, offline model role exact")

    custody = json.loads(custody_path.read_text(encoding="utf-8"))
    assert custody["protocol_configuration_sha256"] == PROTOCOL_SHA256
    assert custody["pickle_weights_present"] is False and custody["symlinks_present"] is False
    assert {entry["candidate_id"] for entry in custody["candidates"]} == set(CANDIDATES)
    for candidate in custody["candidates"]:
        candidate_id = candidate["candidate_id"]
        expected = CANDIDATES[candidate_id]
        assert candidate["repository_revision"] == expected["revision"]
        file_records = {record["filename"]: record for record in candidate["files"]}
        assert set(file_records) == EXPECTED_FILES
        candidate_root = project_root / Path(next(iter(file_records.values()))["path"]).parent
        assert not candidate_root.is_symlink()
        assert {path.name for path in candidate_root.iterdir()} == EXPECTED_FILES
        for filename, record in file_records.items():
            path = project_root / record["path"]
            assert path.is_file() and not path.is_symlink()
            assert path.stat().st_size == record["bytes"]
            assert sha256_file(path) == record["sha256"]
            assert all(fragment not in str(path) for fragment in FORBIDDEN_PATH_FRAGMENTS)
        weight = file_records["model.safetensors"]
        assert weight["bytes"] == expected["weight_bytes"]
        assert weight["sha256"] == expected["weight_sha256"]
        config = json.loads((candidate_root / "config.json").read_text(encoding="utf-8"))
        assert config["architectures"] == ["EsmForMaskedLM"]
        assert config["hidden_size"] == expected["hidden_size"]
        assert config["num_hidden_layers"] == expected["layers"]
    check_record(checks, "model_custody", "two exact revisions; six files each; link-free; all bytes and SHA-256 recomputed")
    check_record(checks, "checkpoint_shapes", "150M 30x640 and 650M 33x1280 configs independently parsed")

    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    assert qualification["status"] == "pass"
    assert qualification["synthetic_fixture_only"] is True
    assert qualification["container_sha256"] == SIF_SHA256
    assert qualification["model_loading_info"]["missing_keys"] == []
    assert qualification["model_loading_info"]["unexpected_keys"] == []
    assert qualification["model_loading_info"]["mismatched_keys"] == []
    assert qualification["checkpoint_restart_fixture"]["exact"] is True
    check_record(checks, "production_qualification", "production report passes with exact keys and exact restart")

    command = [
        "apptainer",
        "exec",
        "--nv",
        "--cleanenv",
        "--containall",
        "--bind",
        f"{project_root}:{project_root}",
        "--pwd",
        str(project_root),
        str(sif),
        "python",
        str(project_root / "scripts/platform/validate_model_runtime_v0_1_0.py"),
        "--inside-fixture",
        "--model-cache",
        str(project_root / "artifacts/cache/models/model_governance_and_baseline_training_protocol_v1"),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    fixture = json.loads(completed.stdout.strip().splitlines()[-1])
    assert fixture["gpu_count"] == 1
    assert fixture["checkpoint_restart_exact"] is True
    assert fixture["network_socket_blocked_during_load_and_forward"] is True
    assert set(fixture["candidates"]) == set(CANDIDATES)
    assert fixture["candidates"]["esm2_650m"]["bfloat16_finite"] is True
    check_record(checks, "independent_gpu_fixture", "both checkpoints exact-load and repeat on one GPU; 650M bfloat16 finite")
    check_record(checks, "independent_offline_fixture", "all model loads/forwards succeeded with Python network sockets blocked")
    check_record(checks, "independent_restart_fixture", "separately implemented optimizer checkpoint restart is bit-exact")

    serialized_evidence = custody_path.read_text(encoding="utf-8") + qualification_path.read_text(encoding="utf-8")
    assert all(fragment not in serialized_evidence for fragment in FORBIDDEN_PATH_FRAGMENTS)
    check_record(checks, "sensitive_path_exclusion", "no sealed, private-key, development, or protected path in runtime evidence")

    producer_commit = subprocess.check_output(
        ["git", "rev-parse", args.evidence_commit], cwd=project_root, text=True
    ).strip()
    assert producer_commit == args.evidence_commit
    check_record(checks, "clean_evidence_anchor", f"production evidence commit {producer_commit}")

    payload = {
        "checks": checks,
        "evidence_commit": producer_commit,
        "fixture": fixture,
        "protocol_configuration_sha256": PROTOCOL_SHA256,
        "schema_version": 1,
        "status": "pass",
        "summary": {"fail": 0, "pass": len(checks), "warning": 0},
        "validator_independence": "does_not_import_production_acquisition_or_qualification_modules",
    }
    output = args.output if args.output.is_absolute() else project_root / args.output
    atomic_json(output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--evidence-commit", default="b73df403958e0847bb799d4f90a548c99a4b3060")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/validation/model_execution/stage1_model_execution_v1/INDEPENDENT_MODEL_RUNTIME_VALIDATION_REPORT.json"),
    )
    parser.add_argument("--inside-fixture", action="store_true")
    parser.add_argument("--model-cache", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.inside_fixture:
        if args.model_cache is None:
            raise SystemExit("--model-cache is required for --inside-fixture")
        return inside_fixture(args)
    return host_validation(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"INDEPENDENT VALIDATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
