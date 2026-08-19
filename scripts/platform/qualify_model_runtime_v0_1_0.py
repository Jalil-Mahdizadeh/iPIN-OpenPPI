#!/usr/bin/env python3
"""Synthetic-only production qualification for ipin-model-arm64_0.1.0."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import torch
from transformers import EsmModel, EsmTokenizer


EXPECTED_VERSIONS = {
    "huggingface-hub": "0.34.4",
    "numpy": "1.26.4",
    "pyarrow": "19.0.1",
    "safetensors": "0.6.2",
    "scikit-learn": "1.6.1",
    "tokenizers": "0.21.4",
    "transformers": "4.55.2",
}
EXPECTED_TORCH = "2.8.0a0+34c6371d24.nv25.08"
EXPECTED_CHECKPOINT_SHA256 = "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566"
SYNTHETIC_SEQUENCE = "ACDEFGHIKLMNPQRSTVWY" * 4


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


def configure_determinism(seed: int) -> None:
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def pooled_synthetic_embedding(
    model: EsmModel, tokenizer: EsmTokenizer, dtype: torch.dtype
) -> torch.Tensor:
    encoded = tokenizer(SYNTHETIC_SEQUENCE, return_tensors="pt", add_special_tokens=True)
    encoded = {key: value.cuda(non_blocking=False) for key, value in encoded.items()}
    model.to(device="cuda", dtype=dtype)
    model.eval()
    with torch.inference_mode():
        hidden = model(**encoded).last_hidden_state[0, 1 : 1 + len(SYNTHETIC_SEQUENCE)]
        return hidden.float().mean(dim=0).cpu()


def checkpoint_restart_fixture() -> dict[str, Any]:
    seed = 20260803
    configure_determinism(seed)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    initial_weight = torch.randn((4, 8), generator=generator)
    initial_bias = torch.randn((4,), generator=generator)
    x = torch.arange(24, dtype=torch.float32, device="cuda").reshape(3, 8) / 23.0
    target = torch.arange(12, dtype=torch.float32, device="cuda").reshape(3, 4) / 11.0

    def make_state() -> tuple[torch.nn.Module, torch.optim.Optimizer, Any]:
        module = torch.nn.Linear(8, 4, device="cuda")
        with torch.no_grad():
            module.weight.copy_(initial_weight.cuda())
            module.bias.copy_(initial_bias.cuda())
        optimizer = torch.optim.AdamW(module.parameters(), lr=1e-3, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: 1.0 - 0.1 * step)
        return module, optimizer, scheduler

    def step(module: torch.nn.Module, optimizer: torch.optim.Optimizer, scheduler: Any) -> float:
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.mse_loss(module(x), target)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(module.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        return float(loss.detach().cpu())

    module_a, optimizer_a, scheduler_a = make_state()
    step(module_a, optimizer_a, scheduler_a)
    state = {
        "model": module_a.state_dict(),
        "optimizer": optimizer_a.state_dict(),
        "scheduler": scheduler_a.state_dict(),
        "torch_cpu_rng": torch.get_rng_state(),
        "torch_cuda_rng": torch.cuda.get_rng_state_all(),
    }
    with tempfile.TemporaryDirectory(prefix="ipin-runtime-qualification-") as directory:
        checkpoint = Path(directory) / "restart.pt"
        torch.save(state, checkpoint)
        reference_loss = step(module_a, optimizer_a, scheduler_a)
        reference_state = {key: value.detach().cpu().clone() for key, value in module_a.state_dict().items()}

        module_b, optimizer_b, scheduler_b = make_state()
        loaded = torch.load(checkpoint, map_location="cuda", weights_only=False)
        module_b.load_state_dict(loaded["model"])
        optimizer_b.load_state_dict(loaded["optimizer"])
        scheduler_b.load_state_dict(loaded["scheduler"])
        torch.set_rng_state(loaded["torch_cpu_rng"].cpu())
        torch.cuda.set_rng_state_all([state.cpu() for state in loaded["torch_cuda_rng"]])
        resumed_loss = step(module_b, optimizer_b, scheduler_b)
        resumed_state = {key: value.detach().cpu() for key, value in module_b.state_dict().items()}

    exact = reference_loss == resumed_loss and all(
        torch.equal(reference_state[key], resumed_state[key]) for key in reference_state
    )
    return {
        "exact": exact,
        "reference_loss": reference_loss,
        "resumed_loss": resumed_loss,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--container-sha256", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert platform.machine() == "aarch64"
    assert torch.__version__ == EXPECTED_TORCH
    versions = {name: importlib.metadata.version(name) for name in EXPECTED_VERSIONS}
    assert versions == EXPECTED_VERSIONS
    assert os.environ.get("HF_HUB_OFFLINE") == "1"
    assert os.environ.get("TRANSFORMERS_OFFLINE") == "1"
    assert torch.cuda.is_available() and torch.cuda.device_count() == 1
    checkpoint = args.model_dir / "model.safetensors"
    assert checkpoint.is_file() and not checkpoint.is_symlink()
    assert sha256_file(checkpoint) == EXPECTED_CHECKPOINT_SHA256

    configure_determinism(20260803)
    tokenizer = EsmTokenizer.from_pretrained(
        args.model_dir, local_files_only=True, trust_remote_code=False
    )
    model, loading_info = EsmModel.from_pretrained(
        args.model_dir,
        add_pooling_layer=False,
        local_files_only=True,
        output_loading_info=True,
        trust_remote_code=False,
        use_safetensors=True,
        torch_dtype=torch.float32,
    )
    assert loading_info["missing_keys"] == []
    assert loading_info["unexpected_keys"] == []
    assert loading_info["mismatched_keys"] == []
    first = pooled_synthetic_embedding(model, tokenizer, torch.float32)
    second = pooled_synthetic_embedding(model, tokenizer, torch.float32)
    repeat_max_abs = float(torch.max(torch.abs(first - second)))
    bf16 = pooled_synthetic_embedding(model, tokenizer, torch.bfloat16)
    restart = checkpoint_restart_fixture()
    assert first.shape == second.shape == bf16.shape == (640,)
    assert torch.isfinite(first).all() and torch.isfinite(bf16).all()
    assert repeat_max_abs <= 1e-6
    assert restart["exact"] is True

    project_root = Path.cwd()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    payload = {
        "architecture": platform.machine(),
        "bfloat16_embedding_fixture": {"finite": True, "shape": [640]},
        "checkpoint_restart_fixture": restart,
        "code_commit": commit,
        "container_sha256": args.container_sha256,
        "cuda": torch.version.cuda,
        "cudnn": str(torch.backends.cudnn.version()),
        "fp32_embedding_fixture": {
            "deterministic_repeat_max_absolute_difference": repeat_max_abs,
            "finite": True,
            "shape": [640],
        },
        "gpu_count": torch.cuda.device_count(),
        "gpu_name": torch.cuda.get_device_name(0),
        "model_checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "model_loading_info": {
            "mismatched_keys": loading_info["mismatched_keys"],
            "missing_keys": loading_info["missing_keys"],
            "pooler_instantiated": False,
            "unexpected_keys": loading_info["unexpected_keys"],
        },
        "network_mode": {
            "hf_hub_offline": os.environ["HF_HUB_OFFLINE"],
            "local_files_only": True,
            "transformers_offline": os.environ["TRANSFORMERS_OFFLINE"],
        },
        "numpy_generator_required_for_scientific_runs": "PCG64DXSM",
        "protocol_configuration_sha256": "3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5",
        "schema_version": 1,
        "status": "pass",
        "synthetic_fixture_only": True,
        "torch": torch.__version__,
        "versions": versions,
    }
    atomic_json(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
