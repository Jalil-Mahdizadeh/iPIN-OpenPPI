"""One GPU-only, bounded train/development search. No test access or retry."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
import torch
from torch.nn import functional as F

from .common import SEEDS, read, recipes, sha, verify, write_new
from .metrics import bootstrap, gate, point
from .models import build, load_state, save_state


class Deadline:
    def __init__(self, seconds: float):
        self.start = time.monotonic()
        self.seconds = seconds

    def elapsed(self) -> float:
        return time.monotonic() - self.start

    def check(self, limit=None) -> None:
        if self.elapsed() >= (self.seconds if limit is None else limit):
            raise TimeoutError("Prospective GPU budget exhausted; no retest authorized")


def arrays(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as values:
        return {k: values[k].copy() for k in values.files}


def configure_cuda() -> dict:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required: CPU fallback is prohibited")
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("Missing deterministic CUDA workspace configuration")
    torch.set_num_threads(8)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    probe = torch.randn((256, 256), device="cuda")
    product = probe @ probe.T
    torch.cuda.synchronize()
    if not bool(torch.isfinite(product).all()):
        raise RuntimeError("CUDA qualification failed")
    return {"torch": torch.__version__, "cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(0), "probe_device": str(product.device),
            "deterministic_algorithms": True, "tf32": False, "amp": False}


@torch.inference_mode()
def score(model, embedding, a, b, *, deadline=None, batch_size=16384):
    model.eval()
    output = np.empty(a.numel(), dtype=np.float32)
    for start in range(0, a.numel(), batch_size):
        if deadline is not None:
            deadline.check()
        stop = min(start + batch_size, a.numel())
        values = model(embedding[a[start:stop]], embedding[b[start:stop]])
        output[start:stop] = values.cpu().numpy()
    if not np.isfinite(output).all():
        raise RuntimeError("Non-finite model score")
    return output


def lr_at(step: int, total: int, peak: float) -> float:
    warmup = max(1, math.ceil(.05 * total))
    if step < warmup:
        return peak * (step + 1) / warmup
    fraction = (step - warmup) / max(total - warmup - 1, 1)
    return peak * (.1 + .9 * .5 * (1 + math.cos(math.pi * fraction)))


def training_orders(seed: int, epoch: int, n_positive: int, n_unlabeled: int):
    # Separate streams; identical comparison order for every architecture.
    p_rng = np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, epoch, 0])))
    u_rng = np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, epoch, 1])))
    p = np.resize(p_rng.permutation(n_positive), n_unlabeled)
    u = u_rng.permutation(n_unlabeled)
    return p, u


def train_one(spec, seed, epochs, evaluation_epochs, stage, *, config, training, data,
              embedding, a, b, output, deadline, emit):
    run_id = f"stage{stage}__{spec['id']}__seed{seed}"
    root = output / run_id
    root.mkdir(exist_ok=False)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    model = build(embedding.shape[1], spec, seed).cuda()
    params = sum(p.numel() for p in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=spec["lr"], weight_decay=spec["weight_decay"],
                                 betas=(.9, .999), eps=1e-8, foreach=False, fused=False)
    n_u, n_p = training["u_a"].numel(), training["p_a"].numel()
    steps = math.ceil(n_u / config["batch_size"])
    weight = training["u_weight"] / training["u_weight"].mean()
    step = 0
    results = []
    for epoch in range(1, epochs + 1):
        deadline.check(config["search_seconds"])
        started = time.monotonic()
        p_order, u_order = training_orders(seed, epoch, n_p, n_u)
        p_order = torch.as_tensor(p_order, device="cuda")
        u_order = torch.as_tensor(u_order, device="cuda")
        model.train()
        loss_sum = torch.zeros((), device="cuda", dtype=torch.float64)
        for start in range(0, n_u, config["batch_size"]):
            deadline.check(config["search_seconds"])
            stop = min(start + config["batch_size"], n_u)
            pi, ui = p_order[start:stop], u_order[start:stop]
            optimizer.param_groups[0]["lr"] = lr_at(step, epochs * steps, spec["lr"])
            optimizer.zero_grad(set_to_none=True)
            pscore = model(embedding[training["p_a"][pi]], embedding[training["p_b"][pi]])
            uscore = model(embedding[training["u_a"][ui]], embedding[training["u_b"][ui]])
            loss = (F.softplus(-(pscore - uscore)).double() * weight[ui]).mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            loss_sum += loss.detach() * (stop - start)
            step += 1
        mean_loss = float((loss_sum / n_u).item())
        if not math.isfinite(mean_loss):
            raise RuntimeError("Non-finite training objective")
        event = {"event": "epoch", "run_id": run_id, "epoch": epoch, "loss": mean_loss,
                 "epoch_seconds": time.monotonic() - started, "elapsed_seconds": deadline.elapsed()}
        emit(event)
        if epoch in evaluation_epochs:
            predictions = score(model, embedding, a, b, deadline=deadline)
            swapped = score(model, embedding, b[:256], a[:256], deadline=deadline)
            # Match batch dimensions for symmetry qualification: GEMM kernels
            # can change with batch size; mathematical swapping is checked here.
            forward_fixture = score(model, embedding, a[:256], b[:256], deadline=deadline)
            swap_error = float(np.max(np.abs(forward_fixture - swapped)))
            if swap_error > 1e-6:
                raise RuntimeError("Swap symmetry failed")
            checkpoint = root / f"epoch_{epoch:02d}.npz"
            prediction_path = root / f"epoch_{epoch:02d}_development.npy"
            save_state(checkpoint, model)
            np.save(prediction_path, predictions, allow_pickle=False)
            item = {"run_id": run_id, "recipe_id": spec["id"], "seed": seed, "stage": stage,
                    "epoch": epoch, "concordance": point(predictions.astype(np.float64), data),
                    "parameters": params, "checkpoint": str(checkpoint.relative_to(output)),
                    "checkpoint_sha256": sha(checkpoint), "predictions": str(prediction_path.relative_to(output)),
                    "prediction_sha256": sha(prediction_path), "swap_max_abs_error": swap_error}
            write_new(root / f"epoch_{epoch:02d}.json", item)
            results.append(item)
            emit({"event": "development", **item})
    del model, optimizer
    return results


def run(bundle: Path, output: Path):
    os.umask(0o077)
    clock = Deadline(7200)
    output.mkdir(parents=True, exist_ok=True)
    # An exclusive marker prevents an accidental second search in this namespace.
    write_new(output / "START.json", {"started_at_utc": datetime.now(timezone.utc).isoformat(),
                                      "search_freeze_sha256": sha(bundle / "SEARCH_FREEZE.json")})
    log = (output / "events.jsonl").open("x")

    def emit(event):
        import json
        value = json.dumps(event, sort_keys=True, allow_nan=False)
        log.write(value + "\n")
        log.flush()
        print(value, flush=True)

    results = []
    try:
        frozen = read(bundle / "SEARCH_FREEZE.json")
        clock.start -= frozen.get("prior_prefit_gpu_seconds_charged", 0)
        verify(bundle, frozen["files"])
        config = frozen["configuration"]
        specs = recipes(config)
        if specs != frozen["recipes"] or config["total_gpu_seconds"] != 7200:
            raise RuntimeError("Search freeze/configuration drift")
        runtime = configure_cuda()
        fixture_result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(bundle / "tests/test_model_optimization_v1.py")],
            check=False, capture_output=True, text=True)
        (output / "GPU_FIXTURE_TESTS.txt").write_text(fixture_result.stdout + fixture_result.stderr)
        fixture_result.check_returncode()
        if Path("/nobackup").exists() or Path("/home/jalil").exists():
            raise RuntimeError("Unexpected host checkout/home visibility in optimization container")
        data = arrays(bundle / "data/development_00.npz")
        training = {k: torch.from_numpy(v).cuda() for k, v in arrays(bundle / "data/training.npz").items()}
        embeddings = {encoder: torch.from_numpy(np.load(bundle / f"data/{encoder}.npy", allow_pickle=False)).cuda()
                      for encoder in config["encoders"]}
        a = torch.as_tensor(data["a"], dtype=torch.int64, device="cuda")
        b = torch.as_tensor(data["b"], dtype=torch.int64, device="cuda")
        if a.numel() != 1002265 or int(data["positive"].sum()) != 2265:
            raise RuntimeError("Primary development census drift")
        replay = np.empty_like(data["baseline"])
        for j, seed in enumerate(SEEDS):
            model = build(640, {"family": "linear", "width": 0, "dropout": 0.}, seed).cuda()
            load_state(bundle / f"data/baseline_{seed}.npz", model)
            replay[:, j] = score(model, embeddings["esm2_150m"], a, b, deadline=clock)
        max_error = float(np.max(np.abs(replay - data["baseline"])))
        point_error = abs(point(replay.mean(1), data) - point(data["baseline"].mean(1), data))
        if max_error > 1e-5 or point_error > 1e-7:
            raise RuntimeError(f"Original baseline GPU replay failed: max_score_error={max_error}, point_error={point_error}")
        qualification = {"runtime": runtime, "baseline_replay_max_score_error": max_error,
                         "baseline_replay_concordance_error": point_error,
                         "baseline_concordance": point(data["baseline"].mean(1), data),
                         "training_positive_rows": training["p_a"].numel(), "training_unlabeled_rows": training["u_a"].numel(),
                         "passed": True, "protected_inputs_mounted": False}
        write_new(output / "QUALIFICATION.json", qualification)
        emit({"event": "qualification", **qualification})
        write_new(output / "FIRST_FIT.json", {"at_utc": datetime.now(timezone.utc).isoformat(),
                                              "search_freeze_sha256": sha(bundle / "SEARCH_FREEZE.json")})
        common = dict(config=config, training=training, data=data, a=a, b=b, output=output,
                      deadline=clock, emit=emit)
        for spec in specs:
            results += train_one(spec, SEEDS[0], config["stage1_epochs"], [config["stage1_epochs"]], 1,
                                 embedding=embeddings[spec["encoder"]], **common)
        promoted = sorted(results, key=lambda r: (-r["concordance"], r["parameters"], r["recipe_id"]))[:config["promoted_recipes"]]
        write_new(output / "PROMOTION.json", {"selected": promoted, "all_stage1": results.copy()})
        emit({"event": "promotion", "recipe_ids": [r["recipe_id"] for r in promoted]})
        spec_by_id = {r["id"]: r for r in specs}
        for item in promoted:
            spec = spec_by_id[item["recipe_id"]]
            for seed in SEEDS:
                results += train_one(spec, seed, config["stage2_epochs"], config["stage2_evaluation_epochs"], 2,
                                     embedding=embeddings[spec["encoder"]], **common)
        groups = []
        for item in promoted:
            for epoch in config["stage2_evaluation_epochs"]:
                members = sorted([r for r in results if r["stage"] == 2 and r["recipe_id"] == item["recipe_id"] and r["epoch"] == epoch], key=lambda r: r["seed"])
                if [r["seed"] for r in members] != list(SEEDS):
                    raise RuntimeError("Incomplete three-seed group")
                predictions = np.column_stack([np.load(output / r["predictions"], allow_pickle=False).astype(np.float64) for r in members])
                groups.append({"recipe_id": item["recipe_id"], "epoch": epoch, "parameters": item["parameters"],
                               "concordance": point(predictions.mean(1), data), "members": members})
        groups.sort(key=lambda r: (-r["concordance"], r["parameters"], r["epoch"], r["recipe_id"]))
        selected = groups[0]
        write_new(output / "SELECTION.json", {"selected": selected, "all_groups": groups,
                                              "selected_before_gate": True, "selection_uses_only_C3_development": True})
        emit({"event": "selection", "recipe_id": selected["recipe_id"], "epoch": selected["epoch"], "concordance": selected["concordance"]})
        predictions = np.column_stack([np.load(output / r["predictions"], allow_pickle=False).astype(np.float64) for r in selected["members"]])
        draws = bootstrap(np.column_stack((data["baseline"].mean(1), predictions.mean(1))), data,
                          cell="C3_development", replicates=config["bootstrap_replicates"], deadline_check=clock.check)
        np.save(output / "paired_development_bootstrap.npy", draws, allow_pickle=False)
        development_gate = gate(predictions, data, draws, seed_range_limit=config["seed_range_limit"])
        development_gate.update({"complete_search": True, "search_freeze_sha256": sha(bundle / "SEARCH_FREEZE.json"),
                                 "selection_sha256": sha(output / "SELECTION.json"),
                                 "computed_at_utc": datetime.now(timezone.utc).isoformat()})
        clock.check()
        write_new(output / "DEVELOPMENT_GATE.json", development_gate)
        emit({"event": "gate", **development_gate})
        completed = {"status": "complete", "study_id": "model_optimization_v1", "selected": selected,
                     "development_gate": development_gate, "stage1_runs": 24, "stage2_runs": 12,
                     "total_epochs": 168, "elapsed_gpu_process_seconds": clock.elapsed(),
                     "runtime": runtime, "test_accessed": False, "followup_authorized": development_gate["passed"],
                     "all_evaluations": results, "all_ensemble_groups": groups}
        write_new(output / "RESULTS.json", completed)
    except Exception as exc:
        # Full errors stay private. Incomplete searches cannot authorize a test.
        (output / "ERROR.txt").write_text(traceback.format_exc())
        write_new(output / "RESULTS.json", {"status": "incomplete", "error_type": type(exc).__name__,
                                            "elapsed_gpu_process_seconds": clock.elapsed(), "all_evaluations": results,
                                            "test_accessed": False, "followup_authorized": False})
        emit({"event": "incomplete", "error_type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.bundle, args.output)
