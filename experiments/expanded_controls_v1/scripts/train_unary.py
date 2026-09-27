"""Fit six fixed endpoint-only controls using train2 pairs exclusively."""
from pathlib import Path
import hashlib
import math
import time
import numpy as np
import torch
from control_io import ROOT, OUT, arrays, cuda, manifest_files, now, phase_guard, protocol, read, record, save, sha, verify, write
from ipin_openppi.partner_specificity.models import make_model


def main():
    phase_guard()
    if Path("/truth").exists() or Path("/candidates").exists() or (OUT / "TRAINING.json").exists():
        raise RuntimeError("forbidden evaluation access or existing completed training")
    cfg = protocol()["endpoint_training"]
    meta = read("/sequences/sequences.json")
    features = read("/features/FEATURES.json")
    if features["sequence_manifest_sha256"] != sha("/sequences/sequences.json"):
        raise RuntimeError("feature identity mismatch")
    manifest_files("/features/FEATURES.json", "/features")
    for item in read(ROOT / "INPUT_FREEZE.json")["files"]:
        if item["path"].startswith("data/train/"):
            verify(Path("/train") / Path(item["path"]).name, item)
    raw = np.load("/features/standardized_train2.npy", allow_pickle=False)
    p, u = arrays("/train/positive.npz"), arrays("/train/unlabeled.npz")
    if len(p["p_a"]) != cfg["positive_budget"] or len(u["u_a"]) != cfg["unlabeled_rows"]:
        raise RuntimeError("fitting population drift")
    part = np.asarray(meta["partition"])
    if any(np.any(part[x] != "train") for x in (p["p_a"], p["p_b"], u["u_a"], u["u_b"])):
        raise RuntimeError("held-out endpoint entered fitting")
    device = cuda()
    matrix = torch.as_tensor(raw, device=device)
    pairs = {k: torch.as_tensor(v, device=device) for k, v in {**p, **u}.items() if k != "u_weight"}
    weights = torch.as_tensor(u["u_weight"], device=device)
    mean_weight = float(u["u_weight"].mean())
    n_p, n_u = len(p["p_a"]), len(u["u_a"])
    batch = cfg["comparisons_per_batch"]
    steps = math.ceil(n_u/batch) * cfg["complete_passes"]
    warmup = max(1, math.ceil(steps*cfg["warmup_fraction"]))
    files, runs, endpoint_scores = [], [], {}
    started = time.monotonic()
    for name in cfg["models"]:
        for seed in cfg["seeds"]:
            run_id = f"{name}_seed{seed}"
            path = OUT / (run_id + ".pt")
            metadata = OUT / (run_id + ".json")
            if path.exists() or metadata.exists():
                raise RuntimeError("existing fit requires an explicit infrastructure audit")
            model = make_model(name, seed).to(device)
            optimizer = torch.optim.AdamW(
                model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"],
                betas=tuple(cfg["betas"]), eps=cfg["epsilon"], foreach=False, fused=False)
            step, monitors = 0, []
            run_start = time.monotonic()
            for epoch in range(1, cfg["complete_passes"]+1):
                rng = np.random.Generator(np.random.PCG64DXSM(seed+epoch))
                po, uo = rng.permutation(n_p), rng.permutation(n_u)
                cycle = po[(np.arange(n_u)+epoch-1) % n_p]
                numerator = torch.zeros((), dtype=torch.float64, device=device)
                denominator = torch.zeros_like(numerator)
                for start in range(0, n_u, batch):
                    stop = min(start+batch, n_u)
                    ip = torch.as_tensor(cycle[start:stop], device=device)
                    iu = torch.as_tensor(uo[start:stop], device=device)
                    optimizer.zero_grad(set_to_none=True)
                    sp = model(matrix[pairs["p_a"][ip]], matrix[pairs["p_b"][ip]])
                    su = model(matrix[pairs["u_a"][iu]], matrix[pairs["u_b"][iu]])
                    per = torch.nn.functional.softplus(su-sp)
                    loss = ((weights[iu]/mean_weight) * per.double()).mean()
                    if not torch.isfinite(loss):
                        raise FloatingPointError("nonfinite unary loss")
                    loss.backward()
                    grad = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg["gradient_clip_norm"])
                    if not torch.isfinite(grad):
                        raise FloatingPointError("nonfinite unary gradient")
                    step += 1
                    fraction = step/warmup if step <= warmup else (
                        cfg["final_learning_rate_fraction"] +
                        (1-cfg["final_learning_rate_fraction"])*.5*(1+math.cos(math.pi*(step-warmup)/(steps-warmup))))
                    for group in optimizer.param_groups:
                        group["lr"] = cfg["learning_rate"]*fraction
                    optimizer.step()
                    numerator += (weights[iu]*per.detach().double()).sum()
                    denominator += weights[iu].sum()
                monitor = {
                    "pass": epoch, "U_comparisons": n_u,
                    "training_loss": float((numerator/denominator).cpu()),
                    "P_order_sha256": hashlib.sha256(po.tobytes()).hexdigest(),
                    "U_order_sha256": hashlib.sha256(uo.tobytes()).hexdigest(),
                }
                monitors.append(monitor)
                print({"run": run_id, **monitor}, flush=True)
            if step != steps or not all(torch.isfinite(t).all() for t in model.parameters()):
                raise RuntimeError("incomplete or nonfinite unary fit")
            model.eval()
            with torch.inference_mode():
                endpoint_scores[run_id] = model.unary(matrix).reshape(-1).double().cpu().numpy()
            with path.open("xb") as stream:
                torch.save({"model": name, "seed": seed, "passes": cfg["complete_passes"],
                            "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                            "implementation_freeze_sha256": sha(ROOT / "IMPLEMENTATION_FREEZE.json")}, stream)
            result = {"run": run_id, "model": name, "seed": seed, "fit_P": n_p, "fit_U": n_u,
                      "complete_passes": cfg["complete_passes"], "steps": step, "monitors": monitors,
                      "parameters": sum(p.numel() for p in model.parameters()),
                      "elapsed_seconds": time.monotonic()-run_start, "checkpoint": record(path, OUT)}
            write(metadata, result)
            files.extend([record(path, OUT), record(metadata, OUT)])
            runs.append(result)
    for name in cfg["models"]:
        endpoint_scores[name] = np.mean([endpoint_scores[f"{name}_seed{s}"] for s in cfg["seeds"]], axis=0)
    save(OUT / "unary_scores.npz", **endpoint_scores)
    files.append(record(OUT / "unary_scores.npz", OUT))
    write(OUT / "TRAINING.json", {
        "at_utc": now(), "files": files, "runs": runs,
        "implementation_freeze_sha256": sha(ROOT / "IMPLEMENTATION_FREEZE.json"),
        "input_freeze_sha256": sha(ROOT / "INPUT_FREEZE.json"),
        "feature_freeze_sha256": sha("/features/FEATURES.json"),
        "development_or_test_pairs_mounted": False, "development_or_test_selection": False,
        "elapsed_seconds": time.monotonic()-started, "torch_version": torch.__version__,
        "gpu": torch.cuda.get_device_name(0),
    })
    print({"unary_training_complete": True, "fits": len(runs)}, flush=True)


if __name__ == "__main__":
    main()
