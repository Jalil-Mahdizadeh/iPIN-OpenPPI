"""Frozen small-head fitting, one-shot scoring, and paired specificity readout."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time

import numpy as np

from ipin_openppi.stage1.baselines import kmer3_csr
from ipin_openppi.stage1.support import atomic_npz, atomic_numpy, sha256_file
from .data import (
    GENERATED, RESULTS, VALIDATION, artifact, config, freeze, now, prepare, read_json,
    verify_freeze, verify_records, write_json,
)
from .semantics import (
    anchor_points, bootstrap_anchor_totals, build_queries, cell_masks, interval,
    normalize, pair_codes, panel_recall, quartet_bootstrap_totals, quartet_credit,
)


def gpu_runtime(cfg):
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("one qualified CUDA device required")
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("deterministic CUBLAS workspace required")
    torch.set_num_threads(cfg["runtime"]["cpu_threads"])
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    return torch


def array_digest(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def train(root):
    cfg = config(root)
    verify_freeze(root)
    if (root / RESULTS / "TRAINING_COMPLETE.json").exists():
        raise RuntimeError("training already complete")
    torch = gpu_runtime(cfg)
    from .models import make_model
    data = np.load(root / GENERATED / "public_arrays.npz", allow_pickle=False)
    raw = np.load(root / GENERATED / "raw_public_embeddings.npy", allow_pickle=False)
    recipe = cfg["training"]
    started = time.monotonic()
    records, runs = [], []
    for fold in range(cfg["split"]["folds"]):
        embeddings, mean, std = normalize(raw, data["fold"] != fold)
        norm_path = root / GENERATED / f"normalization_fold_{fold}.npz"
        if norm_path.exists():
            raise RuntimeError("existing fit artifacts require infrastructure review")
        atomic_npz(norm_path, mean=mean, std=std, fit_endpoints=np.flatnonzero(data["fold"] != fold))
        records.append(artifact(root, norm_path))
        matrix = torch.from_numpy(embeddings).cuda()
        arrays = {}
        for state in ("p", "u"):
            fit, _, evaluate = cell_masks(data[f"{state}_a"], data[f"{state}_b"], data["fold"], fold)
            if np.any(fit & evaluate):
                raise RuntimeError("fit/evaluation overlap")
            for side in ("a", "b"):
                arrays[f"{state}_{side}"] = torch.from_numpy(data[f"{state}_{side}"][fit]).cuda()
            if state == "u":
                weight = data["u_num"][fit].astype(np.float64) / data["u_den"][fit]
        weights = torch.from_numpy(weight).cuda()
        mean_weight = float(weight.mean())
        n_p, n_u = len(arrays["p_a"]), len(arrays["u_a"])
        batch = recipe["comparisons_per_batch"]
        steps = math.ceil(n_u / batch) * recipe["complete_passes"]
        warmup = max(1, math.ceil(steps * recipe["warmup_fraction"]))
        for name in cfg["models"]:
            for seed in recipe["seeds"]:
                run_id = f"fit_f{fold}_{name}_s{seed}"
                path = root / GENERATED / f"{run_id}.pt"
                if path.exists():
                    raise RuntimeError("existing fit requires explicit infrastructure review")
                model = make_model(name, seed).cuda()
                optimizer = torch.optim.AdamW(model.parameters(), lr=recipe["learning_rate"],
                    betas=tuple(recipe["betas"]), eps=recipe["epsilon"],
                    weight_decay=recipe["weight_decay"], foreach=False, fused=False)
                run_started, step, monitors = time.monotonic(), 0, []
                for pass_index in range(1, recipe["complete_passes"] + 1):
                    rng = np.random.Generator(np.random.PCG64DXSM(seed + pass_index))
                    po, uo = rng.permutation(n_p), rng.permutation(n_u)
                    positive_cycle = po[(np.arange(n_u) + pass_index - 1) % n_p]
                    order_hash = {"p": array_digest(po), "u": array_digest(uo)}
                    numerator = torch.zeros((), dtype=torch.float64, device="cuda")
                    denominator = torch.zeros_like(numerator)
                    for start in range(0, n_u, batch):
                        if time.monotonic() - started > cfg["runtime"]["gpu_hours_ceiling"] * 3600:
                            raise RuntimeError("frozen GPU-time ceiling exceeded")
                        stop = min(n_u, start + batch)
                        ip = torch.from_numpy(positive_cycle[start:stop]).cuda()
                        iu = torch.from_numpy(uo[start:stop]).cuda()
                        optimizer.zero_grad(set_to_none=True)
                        sp = model(matrix[arrays["p_a"][ip]], matrix[arrays["p_b"][ip]])
                        su = model(matrix[arrays["u_a"][iu]], matrix[arrays["u_b"][iu]])
                        per = torch.nn.functional.softplus(-(sp - su))
                        loss = ((weights[iu] / mean_weight) * per.double()).mean()
                        if not torch.isfinite(loss):
                            raise FloatingPointError("nonfinite training loss")
                        loss.backward()
                        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), recipe["gradient_clip_norm"])
                        if not torch.isfinite(norm):
                            raise FloatingPointError("nonfinite training gradient")
                        step += 1
                        if step <= warmup:
                            fraction = step / warmup
                        else:
                            floor = recipe["final_learning_rate_fraction"]
                            fraction = floor + (1 - floor) * .5 * (1 + math.cos(math.pi * (step - warmup) / (steps - warmup)))
                        for group in optimizer.param_groups:
                            group["lr"] = recipe["learning_rate"] * fraction
                        optimizer.step()
                        numerator += torch.sum(weights[iu] * per.detach().double())
                        denominator += weights[iu].sum()
                    monitor = {"pass": pass_index, "U_comparisons": n_u, "training_loss": float((numerator / denominator).cpu()),
                               "order_hashes": order_hash, "step": step}
                    monitors.append(monitor)
                if step != steps or not all(torch.isfinite(p).all() for p in model.parameters()):
                    raise RuntimeError("incomplete or nonfinite fit")
                checkpoint = {"state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                              "fold": fold, "model": name, "seed": seed,
                              "execution_freeze_sha256": sha256_file(root / RESULTS / "EXECUTION_FREEZE.json")}
                with path.open("xb") as handle:
                    torch.save(checkpoint, handle)
                record = {"run_id": run_id, "fold": fold, "model": name, "seed": seed,
                          "fit_P": n_p, "fit_U": n_u, "monitors": monitors,
                          "parameters": sum(p.numel() for p in model.parameters()),
                          "elapsed_seconds": time.monotonic() - run_started, "checkpoint": artifact(root, path)}
                write_json(path.with_suffix(".json"), record)
                records.extend((record["checkpoint"], artifact(root, path.with_suffix(".json"))))
                runs.append(record)
                print(json.dumps({k: record[k] for k in ("run_id", "parameters", "elapsed_seconds")}), flush=True)
    result = {"created_utc": now(), "runs": runs, "artifacts": records,
              "elapsed_seconds": time.monotonic() - started, "holdout_scoring_performed": False,
              "torch_version": torch.__version__, "gpu": torch.cuda.get_device_name(0)}
    write_json(root / RESULTS / "TRAINING_COMPLETE.json", result)
    return result


def score(root):
    cfg = config(root)
    verify_freeze(root)
    training = read_json(root / RESULTS / "TRAINING_COMPLETE.json")
    if len(training["runs"]) != 27:
        raise RuntimeError("all 27 fits must finish before any heldout scores")
    verify_records(root, training["artifacts"])
    if (root / RESULTS / "SCORING_COMPLETE.json").exists():
        raise RuntimeError("scoring already complete")
    torch = gpu_runtime(cfg)
    from .models import make_model
    data = np.load(root / GENERATED / "public_arrays.npz", allow_pickle=False)
    raw = np.load(root / GENERATED / "raw_public_embeddings.npy", allow_pickle=False)
    metadata = read_json(root / GENERATED / "endpoint_metadata.json")
    kmer = kmer3_csr(metadata["sequences"])
    raw_unit = raw.astype(np.float64) / np.linalg.norm(raw.astype(np.float64), axis=1)[:, None]
    records = []
    for fold in range(cfg["split"]["folds"]):
        ev = np.load(root / GENERATED / f"evaluation_fold_{fold}.npz", allow_pickle=False)
        a, b = ev["a"], ev["b"]
        normalized, _, _ = normalize(raw, data["fold"] != fold)
        matrix = torch.from_numpy(normalized).cuda()
        columns, values, endpoint_values = [], [], {}
        for name in cfg["models"]:
            for seed in cfg["training"]["seeds"]:
                path = root / GENERATED / f"fit_f{fold}_{name}_s{seed}.pt"
                checkpoint = torch.load(path, map_location="cpu", weights_only=True)
                if (checkpoint["model"], checkpoint["fold"], checkpoint["seed"]) != (name, fold, seed):
                    raise RuntimeError("checkpoint identity mismatch")
                model = make_model(name, seed).cuda().eval()
                model.load_state_dict(checkpoint["state_dict"], strict=True)
                column = f"{name}__{seed}"
                with torch.inference_mode():
                    if name.startswith("endpoint_"):
                        # Sum endpoint scores in float64; preserve exact additive null algebra.
                        unary = model.unary(matrix).squeeze(-1).double().cpu().numpy()
                        endpoint_values[column] = unary
                        value = unary[a] + unary[b]
                    else:
                        value = np.empty(len(a), dtype=np.float64)
                        for start in range(0, len(a), 8192):
                            stop = min(len(a), start + 8192)
                            left, right = torch.from_numpy(a[start:stop]).cuda(), torch.from_numpy(b[start:stop]).cuda()
                            value[start:stop] = model(matrix[left], matrix[right]).double().cpu().numpy()
                        reverse = model(matrix[torch.from_numpy(b[:1024]).cuda()], matrix[torch.from_numpy(a[:1024]).cuda()]).double().cpu().numpy()
                        if not np.allclose(reverse, value[:len(reverse)], atol=1e-5, rtol=0):
                            raise RuntimeError("pair symmetry check failed")
                columns.append(column)
                values.append(value)
        for name in cfg["models"]:
            indices = [columns.index(f"{name}__{s}") for s in cfg["training"]["seeds"]]
            columns.append(name)
            values.append(np.mean([values[i] for i in indices], axis=0))
        lengths = np.log1p(data["length"])
        columns.append("length_ratio")
        values.append(-np.abs(lengths[a] - lengths[b]))
        columns.append("kmer3_cosine")
        values.append(np.asarray(kmer[a].multiply(kmer[b]).sum(axis=1)).ravel())
        columns.append("pooled_cosine")
        values.append(np.einsum("ij,ij->i", raw_unit[a], raw_unit[b]))
        scores = np.column_stack(values)
        if not np.isfinite(scores).all():
            raise RuntimeError("nonfinite score")
        for column in columns:
            if column.startswith("endpoint_"):
                _, delta = quartet_credit(scores[:, columns.index(column)], ev["quartet_rows"])
                if np.max(np.abs(delta), initial=0) > 1e-6:
                    raise RuntimeError("additive quartet cancellation failed")
        unary = np.mean([endpoint_values[f"endpoint_mlp64__{s}"] for s in cfg["training"]["seeds"]], axis=0)
        boundaries = np.quantile(unary[data["fold"] != fold], [.2, .4, .6, .8])
        bins = np.searchsorted(boundaries, unary, side="right")
        path = root / GENERATED / f"scores_fold_{fold}.npz"
        if path.exists():
            raise RuntimeError("refusing to overwrite scores")
        atomic_npz(path, scores=scores, columns=np.array(columns), propensity_bins=bins,
                   propensity_boundaries=boundaries, **endpoint_values)
        records.append(artifact(root, path))
        print(f"scored fold {fold}: {len(a)} rows, {len(columns)} columns", flush=True)
    result = {"created_utc": now(), "artifacts": records, "training_complete_sha256": sha256_file(root / RESULTS / "TRAINING_COMPLETE.json")}
    write_json(root / RESULTS / "SCORING_COMPLETE.json", result)
    return result


def safe_ratio(a, b):
    return np.divide(a, b, out=np.full_like(a, np.nan, dtype=np.float64), where=b > 0)


def decide(primary_delta, primary_interval, fold_deltas, seed_deltas, controls, propensity_delta, quartet, cfg):
    d = cfg["decision"]
    checks = {
        "practical_primary_gain": primary_delta >= d["minimum_primary_delta"],
        "positive_primary_lower_bound": primary_interval[0] > d["paired_95_lower_must_exceed"],
        "each_fold_positive": all(x > 0 for x in fold_deltas),
        "each_seed_positive": all(x > 0 for x in seed_deltas),
        "all_frozen_controls_beaten": all(x > 0 for x in controls.values()),
        "propensity_sensitivity_positive": bool(propensity_delta > 0),
        "quartet_above_chance": quartet["ci95"][0] > d["require_quartet_95_lower_above"],
        "quartet_beats_length_and_kmer": all(x > 0 for x in quartet["control_deltas"].values()),
    }
    if all(checks.values()):
        disposition = "useful_internal_partner_specific_signal_not_external_confirmation"
    elif primary_interval[1] < d["tight_negative_if_primary_95_upper_below"]:
        disposition = "useful_incremental_gain_excluded_under_frozen_recipe"
    else:
        disposition = "inconclusive_or_mixed_internal_evidence"
    return {"checks": checks, "disposition": disposition, "protected_evaluation_authorized": False}


def evaluate(root):
    cfg = config(root)
    verify_freeze(root)
    verification = read_json(root / RESULTS / "SCORING_COMPLETE.json")
    verify_records(root, verification["artifacts"])
    if (root / RESULTS / "RESULTS.json").exists():
        raise RuntimeError("readout already exists")
    data = np.load(root / GENERATED / "public_arrays.npz", allow_pickle=False)
    component = data["component"]
    bcfg = cfg["evaluation"]["bootstrap"]
    rng = np.random.Generator(np.random.PCG64DXSM(bcfg["seed"]))
    draws = rng.poisson(1, size=(bcfg["replicates"], int(component.max()) + 1)).astype(np.int16)
    draw_path = root / GENERATED / "component_multipliers.npy"
    atomic_numpy(draw_path, draws)
    anchor_results, quartet_results, propensity_results = {}, {}, {}
    bootstrap, quartet_bootstrap, fold_results, fold_deltas = {}, {}, [], []
    for fold in range(cfg["split"]["folds"]):
        ev = np.load(root / GENERATED / f"evaluation_fold_{fold}.npz", allow_pickle=False)
        scored = np.load(root / GENERATED / f"scores_fold_{fold}.npz", allow_pickle=False)
        columns = list(scored["columns"])
        weights = ev["num"].astype(np.float64) / ev["den"]
        queries = build_queries(ev["a"], ev["b"], ev["positive"])
        points = {}
        per_anchor = {}
        for i, name in enumerate(columns):
            scores = scored["scores"][:, i]
            points[name] = anchor_points(scores, queries, weights)
            per_anchor[name] = points[name]
            anchor_results.setdefault(name, []).append(points[name])
            credit, _ = quartet_credit(scores, ev["quartet_rows"], cfg["quartets"]["tie_absolute_tolerance"])
            quartet_results.setdefault(name, []).append(credit)
            if name in cfg["models"] + cfg["evaluation"]["secondary_comparators"]:
                # All non-seed columns share the same frozen draws.
                qt, qm = quartet_bootstrap_totals(credit, ev["quartet_endpoints"], component, draws)
                quartet_bootstrap.setdefault(name, []).append((qt, qm))
            if name in ("pair_linear", "endpoint_mlp64"):
                sensitivity = anchor_points(scores, queries, weights, scored["propensity_bins"])
                propensity_results.setdefault(name, []).append(sensitivity)
                print(f"bootstrap fold {fold}, {name}: {len(queries)} anchors", flush=True)
                total, mass = bootstrap_anchor_totals(scores, queries, weights, component, draws)
                bootstrap.setdefault(name, []).append((total, mass))
        fold_delta = float(np.mean(points["pair_linear"] - points["endpoint_mlp64"]))
        fold_deltas.append(fold_delta)
        tie_keys = pair_codes(ev["a"], ev["b"], len(component))
        recalls = {name: {str(k): float(panel_recall(scored["scores"][:, columns.index(name)], queries, k, tie_keys).mean())
                          for k in cfg["evaluation"]["recall_at"]} for name in cfg["models"]}
        fold_results.append({"fold": fold, "anchors": len(queries), "macro": {n: float(v.mean()) for n, v in points.items()},
                             "primary_delta": fold_delta, "panel_recall": recalls})
        path = root / GENERATED / f"anchor_metrics_fold_{fold}.npz"
        atomic_npz(path, anchors=np.array([q.anchor for q in queries]), **per_anchor)
    macro = {name: float(np.concatenate(values).mean()) for name, values in anchor_results.items()}
    def combine(items):
        return safe_ratio(sum(x[0] for x in items), sum(x[1] for x in items))
    boot = {name: combine(values) for name, values in bootstrap.items()}
    quartet_boot = {name: combine(values) for name, values in quartet_bootstrap.items()}
    delta = macro["pair_linear"] - macro["endpoint_mlp64"]
    delta_draws = boot["pair_linear"] - boot["endpoint_mlp64"]
    seed_deltas = [macro[f"pair_linear__{s}"] - macro[f"endpoint_mlp64__{s}"] for s in cfg["training"]["seeds"]]
    controls = {n: macro["pair_linear"] - macro[n] for n in cfg["evaluation"]["secondary_comparators"]}
    prop_pair, prop_null = [np.concatenate(propensity_results[n]) for n in ("pair_linear", "endpoint_mlp64")]
    eligible = np.isfinite(prop_pair) & np.isfinite(prop_null)
    propensity_delta = float((prop_pair[eligible] - prop_null[eligible]).mean()) if eligible.any() else float("nan")
    quartet_means = {n: float(np.concatenate(v).mean()) for n, v in quartet_results.items()}
    quartet = {"point": quartet_means["pair_linear"], "ci95": interval(quartet_boot["pair_linear"]),
               "all_points": quartet_means,
               "control_deltas": {n: quartet_means["pair_linear"] - quartet_means[n] for n in ("length_ratio", "kmer3_cosine")},
               "paired_control_ci95": {n: interval(quartet_boot["pair_linear"] - quartet_boot[n]) for n in ("length_ratio", "kmer3_cosine")}}
    result = {"created_utc": now(), "metric": cfg["evaluation"]["primary"], "macro_concordance": macro,
              "primary_delta": delta, "primary_delta_ci95": interval(delta_draws),
              "model_ci95": {n: interval(v) for n, v in boot.items()},
              "valid_primary_replicates": int(np.isfinite(delta_draws).sum()),
              "folds": fold_results, "seed_deltas": seed_deltas, "control_deltas": controls,
              "propensity_sensitivity": {"eligible_anchors": int(eligible.sum()), "delta": propensity_delta if np.isfinite(propensity_delta) else None},
              "quartets": quartet, "source_sensitivity": "not_available_in_public_training_package",
              "inference_limit": "conditional_on_fitted_models_fixed_folds_and_released_panel_not_physical_specificity"}
    result["decision"] = decide(delta, result["primary_delta_ci95"], fold_deltas, seed_deltas, controls, propensity_delta, quartet, cfg)
    boot_path = root / GENERATED / "bootstrap_metrics.npz"
    atomic_npz(boot_path, primary_delta=delta_draws, **{f"anchor_{n}": v for n, v in boot.items()},
               **{f"quartet_{n}": v for n, v in quartet_boot.items()})
    result["bootstrap_artifacts"] = [artifact(root, draw_path), artifact(root, boot_path)]
    write_json(root / RESULTS / "RESULTS.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "freeze", "train", "score", "evaluate", "validate"))
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--resume-preparation", action="store_true",
                        help="retry input preparation only, preserving the original preregistration; no generated arrays may exist")
    args = parser.parse_args(argv)
    root = args.project_root.resolve(strict=True)
    if args.resume_preparation and args.action != "prepare":
        parser.error("--resume-preparation applies only to input preparation")
    if args.action == "prepare":
        result = prepare(root, resume_preparation=args.resume_preparation)
    elif args.action == "validate":
        from .validation import validate
        result = validate(root)
    else:
        result = globals()[args.action](root)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0
