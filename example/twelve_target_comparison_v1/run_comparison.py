#!/usr/bin/env python3
"""Fresh-sequence, fresh-embedding comparison; never load an existing feature cache.

Phases: prepare (network), ipin (iPIN SIF/GPU), tuna (TUnA SIF/GPU), summarize.
Every output is exclusive-create. Frozen inputs and model parameters are read-only.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

CONFIG = json.loads(Path(__file__).with_name("panel_config.json").read_text())
TARGETS = tuple(CONFIG["original_targets"]) + tuple(t["gene"] for t in CONFIG["new_targets"])
INPUT_COLUMNS = ("query_gene", "query_uniprot", "partner_gene", "partner_uniprot", "class")
MODELS = ("ipin_baseline", "ipin_optimized", "tuna_retrained")
SEEDS = (20260803, 20260817, 20260831)
IPIN_SIF_SHA = "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"
TUNA_SIF_SHA = "98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def write_csv(path, rows, columns=None):
    columns = list(columns or rows[0])
    with Path(path).open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def record(path):
    path = Path(path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}



def catalogue(root):
    """Bind every invocation to the preserved three-model catalogue."""
    path = root / "artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json"
    if sha(path) != "faf2d585dbfee34ca3fe19487bc7a821f744014cdcdb94e95e4b657097110878":
        raise RuntimeError("Frozen three-model registry changed")
    registry = read(path)
    if sha(root / registry["bundle_path"] / "MODEL_REGISTRY.json") != sha(path):
        raise RuntimeError("Public/private catalogue mismatch")
    return registry


def load_panels(root):
    rows, files, expected = [], [], {}
    for gene in TARGETS:
        folder = root / "example" / gene
        path = folder / f"{gene.lower()}_ipin_panel.csv"
        manifest_path = folder / "panel_manifest.json"
        manifest = read(manifest_path)
        if sha(path) != manifest["csv_sha256"]:
            raise RuntimeError(f"Panel checksum mismatch: {gene}")
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames) != INPUT_COLUMNS:
                raise RuntimeError("Unexpected input schema")
            panel = list(reader)
        if len(panel) != len(manifest["rows"]):
            raise RuntimeError("Panel/manifest length mismatch")
        q = manifest["target"]
        for i, (row, annotation) in enumerate(zip(panel, manifest["rows"], strict=True), 1):
            if row["query_gene"] != gene or row["query_uniprot"] != q["accession"]:
                raise RuntimeError("Unexpected target identity")
            for key in ("partner_gene", "partner_uniprot", "class"):
                if row[key] != annotation[key]:
                    raise RuntimeError("Row/manifest mismatch")
            for acc, digest, length in (
                (q["accession"], q["sequence_sha256"], q["length"]),
                (row["partner_uniprot"], annotation["sequence_sha256"], annotation["length"]),
            ):
                value = {"sequence_sha256": digest, "sequence_length": length}
                if acc in expected and expected[acc] != value:
                    raise RuntimeError("Conflicting sequence identities across targets")
                expected[acc] = value
            exposure = annotation.get("prior_pair_exposure", {})
            rows.append({**row, "panel_row": i,
                         "query_sequence_sha256": q["sequence_sha256"],
                         "query_sequence_length": q["length"],
                         "partner_sequence_sha256": annotation["sequence_sha256"],
                         "partner_sequence_length": annotation["length"],
                         "U_stratum": annotation.get("stratum", ""),
                         "anchor_positive_uniprot": annotation.get("anchor_positive_uniprot", ""),
                         "development_exposed_positive": bool(exposure.get("DEV_P", False)),
                         "training_exposed_positive": bool(exposure.get("TRAIN_P", False)),
                         "prior_train_development_pair": any(exposure.values()),
                         "target_cohort": "original_six" if gene in CONFIG["original_targets"] else "additional_six",
                         "homomeric": row["query_uniprot"] == row["partner_uniprot"]})
        for f in (path, manifest_path):
            files.append({"path": str(f.relative_to(root)), "sha256": sha(f)})
    if len(rows) != 3737 or sum(r["class"] == "P" for r in rows) != 37:
        raise RuntimeError("Unexpected panel census")
    return rows, files, expected


def helper(root):
    sys.path.insert(0, str(root / "example"))
    import score_ire1_ipin_panel2
    return score_ire1_ipin_panel2


def prepare(root, out):
    catalogue(root)
    started = time.monotonic()
    rows, files, expected = load_panels(root)
    original = {}
    for path in sorted((root / "example").rglob("*")):
        if path.is_file() and "twelve_target_comparison_v1" not in path.relative_to(root).parts:
            original[str(path.relative_to(root))] = sha(path)
    api = helper(root)
    accessions = sorted(expected)
    chunks = [accessions[i:i + 40] for i in range(0, len(accessions), 40)]
    print(f"Fetching fresh UniProt sequences for {len(accessions)} accessions ({len(chunks)} requests)", flush=True)
    parts = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(api.fetch_uniprot, chunk) for chunk in chunks]
        for future in as_completed(jobs):
            parts.append(future.result())
            print(f"UniProt requests complete: {len(parts)}/{len(chunks)}", flush=True)
    releases = {(p["uniprot_release"], p["uniprot_release_date"], p["uniprot_api_deployment_date"]) for p in parts}
    if len(releases) != 1:
        raise RuntimeError("UniProt release changed during retrieval")
    records = {a: r for p in parts for a, r in p["records"].items()}
    if set(records) != set(accessions):
        raise RuntimeError("Incomplete sequence snapshot")
    for acc, values in expected.items():
        for key, value in values.items():
            if records[acc][key] != value:
                raise RuntimeError(f"Sequence differs from the curated panel: {acc}, {key}")
    body = {k: v for k, v in parts[0].items() if k not in ("snapshot_sha256", "records")}
    body.update(retrieved_at_utc=now(), records={a: records[a] for a in accessions})
    snapshot = {**body, "snapshot_sha256": api.sha256_bytes(api.canonical_json(body))}
    write_json(out / "uniprot_sequences.json", snapshot)
    write_json(out / "pairs.json", rows)
    unique = {r["sequence_sha256"]: r["sequence"] for r in records.values()}
    plan = {"at_utc": now(), "input_files": files, "original_file_hashes": original,
            "pairs": len(rows), "P": 37, "U": 3700, "accessions": len(accessions),
            "unique_sequences": len(unique), "total_residues": sum(map(len, unique.values())),
            "maximum_sequence_length": max(map(len, unique.values())),
            "sequence_snapshot": record(out / "uniprot_sequences.json"),
            "pair_manifest_sha256": sha(out / "pairs.json"),
            "preexisting_embedding_or_feature_cache_reuse": False,
            "all_embeddings_recomputed": True,
            "metrics_prespecified": "P-versus-U concordance; AP and macro MAP; expected first-positive rank and reciprocal rank/MRR; recovered-positive counts, recall, known-positive precision, EF, NDCG and target success at K=5,10,20; equal-target averages; all/context/background U and exposure/homomer subsets; original/additional/all-target cohorts.",
            "metric_protocol_sha256": sha(out / "METRICS.md"),
            "implementation_files": [{"path": str(Path(__file__).with_name(name).relative_to(root)),
                                      "sha256": sha(Path(__file__).with_name(name))}
                                     for name in ("build_panels.py", "metrics.py", "run_comparison.py", "analysis_outputs.py")],
            "panel_configuration_sha256": sha(out / "panel_config.json"),
            "model_registry": record(root / "artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json"),
            "unlabeled_is_not_negative": True, "no_training_or_model_selection": True,
            "script_sha256": sha(Path(__file__)), "elapsed_seconds": time.monotonic() - started}
    write_json(out / "INPUT_FREEZE.json", plan)
    print({k: plan[k] for k in ("pairs", "accessions", "unique_sequences", "total_residues", "maximum_sequence_length", "elapsed_seconds")}, flush=True)


def inputs(root, out):
    plan = read(out / "INPUT_FREEZE.json")
    for item in plan["input_files"]:
        if sha(root / item["path"]) != item["sha256"]:
            raise RuntimeError("Input panel changed")
    if sha(out / "pairs.json") != plan["pair_manifest_sha256"]:
        raise RuntimeError("Pair order changed")
    if sha(out / "uniprot_sequences.json") != plan["sequence_snapshot"]["sha256"]:
        raise RuntimeError("Sequence snapshot changed")
    for item in plan["implementation_files"]:
        if sha(root / item["path"]) != item["sha256"]:
            raise RuntimeError("Scoring/metric implementation changed after input freeze")
    if sha(out / "METRICS.md") != plan["metric_protocol_sha256"] or sha(out / "panel_config.json") != plan["panel_configuration_sha256"]:
        raise RuntimeError("Panel or metric protocol changed after input freeze")
    catalogue(root)
    rows = read(out / "pairs.json")
    accessions = {r[k] for r in rows for k in ("query_uniprot", "partner_uniprot")}
    snapshot = helper(root).read_snapshot(out / "uniprot_sequences.json", accessions)
    unique = {r["sequence_sha256"]: r["sequence"] for r in snapshot["records"].values()}
    order = sorted(unique, key=lambda h: (len(unique[h]), h))
    return rows, snapshot, order, [unique[h] for h in order]


def configure_gpu():
    import torch
    torch.set_num_threads(8)
    torch.manual_seed(20260803)
    torch.cuda.manual_seed_all(20260803)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("One allocated GPU is required")
    return torch.device("cuda")


def ipin(root, out):
    import numpy as np
    import torch
    started = time.monotonic()
    configure_gpu()
    rows, snapshot, order, sequences = inputs(root, out)
    sys.path.insert(0, str(root / "src"))
    from ipin_openppi.stage1 import embeddings
    import score_frozen_models as frozen
    bundle = root / ".private/frozen_pair_models_v1/bundle"
    registry = frozen.load_registry(root, bundle)
    verified = []
    for item in registry["bundle_files"]:
        if item["path"].startswith("encoder/") or item["path"] == "code/embeddings.py":
            path = frozen.checked_file(bundle, item)
            verified.append(record(path))
            if item["path"] == "code/embeddings.py" and sha(path) != sha(Path(embeddings.__file__)):
                raise RuntimeError("Embedding implementation differs from frozen source")
    image = root / "containers/images/ipin-model-arm64_0.1.0.sif"
    if sha(image) != IPIN_SIF_SHA:
        raise RuntimeError("iPIN SIF checksum mismatch")
    seq_records = [embeddings.SequenceRecord(h, s, len(s)) for h, s in zip(order, sequences, strict=True)]
    print(f"Fresh iPIN ESM extraction: {len(seq_records)} sequences", flush=True)
    raw, extraction = embeddings.extract_matrix(candidate_id="esm2_150m", records=seq_records, model_root=bundle / "encoder")
    normalizer_path = frozen.checked_file(bundle, registry["shared_inputs"]["training_normalization.npz"])
    with np.load(normalizer_path, allow_pickle=False) as normalizer:
        mean, std = normalizer["mean"], normalizer["standard_deviation"]
        if mean.shape != (640,) or std.shape != (640,) or mean.dtype != np.float64 or std.dtype != np.float64 or not np.isfinite(mean).all() or not np.isfinite(std).all() or np.any(std < 1e-6):
            raise RuntimeError("Invalid frozen normalizer")
        standardized = ((raw.astype(np.float64) - mean) / std).astype(np.float32)
    with (out / "ipin_fresh_embeddings.npz").open("xb") as handle:
        np.savez(handle, raw=raw, standardized=standardized, sequence_sha256=np.asarray(order))
    index = {h: i for i, h in enumerate(order)}
    a = [index[r["query_sequence_sha256"]] for r in rows]
    b = [index[r["partner_sequence_sha256"]] for r in rows]
    left, right = torch.from_numpy(standardized[a].copy()), torch.from_numpy(standardized[b].copy())
    features = frozen.pair_features(left, right)
    outputs = {}
    for name, model_id in (("ipin_baseline", frozen.BASELINE_MODEL), ("ipin_optimized", frozen.BEST_MODEL)):
        score = frozen.ensemble_scores(features, bundle, registry, model_id)
        reversed_score = frozen.ensemble_scores(frozen.pair_features(right, left), bundle, registry, model_id)
        if not np.array_equal(score, reversed_score):
            raise RuntimeError("iPIN pair-order symmetry failed")
        outputs[name + "_score"] = score
        for member in registry["models"][model_id]["members"]:
            verified.append(record(frozen.checked_file(bundle, member["state"])))
    scored = [{"row_index": i, **{k: float(v[i]) for k, v in outputs.items()}} for i in range(len(rows))]
    write_csv(out / "ipin_scores.csv", scored)
    write_json(out / "IPIN_RUN.json", {"at_utc": now(), "elapsed_seconds": time.monotonic() - started,
        "device": torch.cuda.get_device_name(), "torch": torch.__version__, "SIF_sha256": IPIN_SIF_SHA,
        "freshly_embedded_sequences": len(order), "preexisting_feature_cache_reads": 0,
        "extraction": extraction, "embedding_artifact": record(out / "ipin_fresh_embeddings.npz"),
        "score_artifact": record(out / "ipin_scores.csv"), "model_registry": record(bundle / "MODEL_REGISTRY.json"),
        "normalizer": record(normalizer_path), "verified_model_inputs": verified,
        "pair_order_symmetry_passed": True, "script_sha256": sha(Path(__file__))})
    print("Both frozen iPIN ensembles completed", flush=True)


def tuna(root, out):
    import h5py
    import numpy as np
    import torch
    started = time.monotonic()
    device = configure_gpu()
    rows, snapshot, order, sequences = inputs(root, out)
    registry = catalogue(root)
    bundle = root / registry["model_bundles"]["tuna_retrained_ensemble"]
    scripts = bundle / "code"
    os.environ["TUNA_UPSTREAM_DIR"] = str(bundle / "upstream/TUnA/results/bernett/TUnA")
    sys.path.insert(0, str(scripts))
    import adapter
    import esm_cache
    freeze = read(bundle / "provenance/SCORER_FREEZE.json")
    if freeze["selected_epoch"] != 4 or freeze["sif_sha256"] != TUNA_SIF_SHA:
        raise RuntimeError("Frozen TUnA selection changed")
    if sha(root / "benchmark/containers/images/tuna-arm64-v1.sif") != TUNA_SIF_SHA:
        raise RuntimeError("TUnA SIF checksum mismatch")
    verified = []
    for item in registry["bundle_files"]:
        # Intentionally NEVER open the pre-existing features/ arrays.
        if item["path"].startswith("features/"):
            continue
        path = bundle / item["path"]
        if sha(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise RuntimeError(f"Frozen TUnA file changed: {path}")
        verified.append(record(path))
    recipe = read(bundle / "provenance/TRAINING_FREEZE.json")
    for item in recipe["training_code"]:
        if item["name"] in ("adapter.py", "common.py") and sha(scripts / item["name"]) != item["sha256"]:
            raise RuntimeError("TUnA adapter differs from frozen training code")
    encoder_dir = root / ".private/frozen_pair_models_v1/bundle/encoder"
    encoder, alphabet, ignored = esm_cache.load_encoder(encoder_dir, device)
    fixture_indices = sorted(set([len(order) // 4, len(order) // 2, int(.9 * len(order))]))
    qualification = esm_cache.qualify(encoder, alphabet, encoder_dir,
                                    [sequences[i] for i in fixture_indices], out / "TUNA_ESM_QUALIFICATION.json")
    lengths = np.asarray([len(s) for s in sequences], np.int64)
    offsets = np.concatenate(([0], np.cumsum(lengths)))
    values = torch.empty((int(offsets[-1]), 640), dtype=torch.float32, device=device)
    print(f"Fresh full-context TUnA ESM extraction: {len(order)} sequences, {offsets[-1]} residues", flush=True)
    with h5py.File(out / "tuna_fresh_residues.h5", "x") as fresh:
        fresh.attrs["sequence_snapshot_sha256"] = sha(out / "uniprot_sequences.json")
        fresh.attrs["encoder_sha256"] = esm_cache.ENCODER_SHA
        fresh.attrs["preexisting_cache_reused"] = False
        for start in range(0, len(order), 4):
            batch = esm_cache.embed(encoder, alphabet, sequences[start:start + 4])
            for i, value in enumerate(batch, start):
                if value.shape != (lengths[i], 640) or value.dtype != torch.float32 or not torch.isfinite(value).all():
                    raise RuntimeError("Invalid fresh TUnA embedding")
                values[offsets[i]:offsets[i + 1]] = value
                fresh.create_dataset(order[i], data=value.cpu().numpy(), dtype="float32")
            if start % 100 == 0 or start + 4 >= len(order):
                print(f"TUnA ESM: {min(start + 4,len(order))}/{len(order)} sequences; {time.monotonic()-started:.1f}s", flush=True)
        fresh.attrs["complete"] = True
    del encoder, batch
    torch.cuda.empty_cache()
    index = {h: i for i, h in enumerate(order)}
    a = np.asarray([index[r["query_sequence_sha256"]] for r in rows], np.int64)
    b = np.asarray([index[r["partner_sequence_sha256"]] for r in rows], np.int64)
    # Twelve first nominated pairs (including ERN1 self-pair) plus the longest pair.
    fixture_rows = [next(i for i, r in enumerate(rows) if r["query_gene"] == g) for g in TARGETS]
    fixture_rows.append(int(np.argmax(lengths[a] + lengths[b])))
    fixture_rows = sorted(set(fixture_rows))
    members = [f"tuna_retrained_seed{s}" for s in SEEDS]
    scores, qualifications = {}, []
    for member in members:
        path = bundle / "weights" / f"{member}.pt"
        initial = torch.load(path, map_location="cpu", weights_only=True)
        model = adapter.create(checkpoint=path, device=device)
        model.gp_layer.fitted = True  # Preserve the already frozen covariance; never refit.
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        adapter.enable_sdpa(model)
        z = torch.empty((len(order), 64), dtype=torch.float32, device=device)
        with torch.inference_mode():
            start = 0
            while start < len(order):
                longest = lengths[min(start + 16, len(order)) - 1]
                count = max(1, min(16, 16000000 // int(longest * longest)))
                ids = list(range(start, min(start + count, len(order))))
                width = int(lengths[ids].max())
                x = torch.zeros((len(ids), width, 640), dtype=torch.float32, device=device)
                for j, i in enumerate(ids):
                    x[j, :lengths[i]] = values[offsets[i]:offsets[i + 1]]
                z[ids] = adapter.endpoint_features(model, x, lengths[ids].tolist())
                start += len(ids)
        if not torch.isfinite(z).all():
            raise RuntimeError("Nonfinite TUnA endpoint features")
        with (out / f"{member}_fresh_endpoint_features.npy").open("xb") as handle:
            np.save(handle, z.cpu().numpy(), allow_pickle=False)
        score = adapter.cached_scores(model, z, a, b, probabilities=False)
        reverse = adapter.cached_scores(model, z, b, a, probabilities=False)
        if not np.array_equal(score, reverse):
            raise RuntimeError("TUnA pair-order symmetry failed")
        # Native, unaccelerated pairwise forward is an independent oracle for
        # the within-run endpoint factorization. No old feature cache is read.
        oracle = adapter.create(checkpoint=path, device=device)
        oracle.gp_layer.fitted = True
        oracle.eval()
        reference = []
        with torch.inference_mode():
            for i in fixture_rows:
                left = values[offsets[a[i]]:offsets[a[i] + 1]]
                right = values[offsets[b[i]]:offsets[b[i] + 1]]
                packed = adapter.native.test_pack([left], [right], [0], 512, 640, device)
                logit, variance = oracle.forward(packed[0], packed[1], packed[3], packed[4], packed[5], packed[6], True, False)
                value = logit.reshape(-1) / torch.sqrt(1 + math.pi / 8 * variance)
                reference.append(float(value.reshape(())))
        error = float(np.max(np.abs(score[fixture_rows].astype(np.float64) - reference)))
        if error > 1e-5:
            raise RuntimeError(f"Native TUnA qualification failed: {member}, error {error}")
        for key, value in model.state_dict().items():
            if not torch.equal(value.detach().cpu(), initial[key]):
                raise RuntimeError(f"Frozen TUnA parameter/buffer changed: {member} {key}")
        qualifications.append({"member": member, "native_max_absolute_error": error,
                               "tolerance": 1e-5, "fixture_rows_zero_based": fixture_rows,
                               "pair_order_symmetry_passed": True, "all_parameters_and_buffers_unchanged": True})
        scores[member] = score.astype(np.float64)
        print(f"{member}: all {len(rows)} pairs scored; native agreement error {error:.3g}", flush=True)
        del model, oracle, z, initial
        torch.cuda.empty_cache()
    scores["tuna_retrained"] = np.column_stack([scores[m] for m in members]).mean(1, dtype=np.float64)
    write_csv(out / "tuna_scores.csv", [{"row_index": i, **{k + "_score": float(v[i]) for k, v in scores.items()}} for i in range(len(rows))])
    write_json(out / "sequence_order.json", order)
    write_json(out / "TUNA_RUN.json", {"at_utc": now(), "elapsed_seconds": time.monotonic() - started,
        "device": torch.cuda.get_device_name(), "torch": torch.__version__, "SIF_sha256": TUNA_SIF_SHA,
        "selected_epoch": 4, "seeds": list(SEEDS), "freshly_embedded_sequences": len(order),
        "freshly_computed_endpoint_representations_per_member": len(order), "preexisting_feature_cache_reads": 0,
        "GP_covariance_refitted": False, "native_qualification": qualifications,
        "esm_qualification": qualification, "ignored_unused_encoder_keys": ignored,
        "verified_model_inputs": verified, "scorer_freeze": record(bundle / "provenance/SCORER_FREEZE.json"),
        "esm_cache_code": record(scripts / "esm_cache.py"), "adapter_code": record(scripts / "adapter.py"),
        "score_artifact": record(out / "tuna_scores.csv"), "fresh_residues": record(out / "tuna_fresh_residues.h5"),
        "script_sha256": sha(Path(__file__))})


class Tee:
    def __init__(self, console, log):
        self.console, self.log = console, log
    def write(self, text):
        self.console.write(text)
        self.log.write(text)
        self.log.flush()
        return len(text)
    def flush(self):
        self.console.flush()
        self.log.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "ipin", "tuna", "summarize"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Run inside a qualified Apptainer SIF")
    root, out = args.root.resolve(), args.output.resolve()
    if not out.is_dir():
        raise RuntimeError("Output directory must already exist")
    with (out / f"{args.phase}.log").open("x") as log:
        stdout, stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = Tee(stdout, log), Tee(stderr, log)
        try:
            print(f"{now()} starting {args.phase}; pre-existing embeddings are prohibited", flush=True)
            if args.phase == "summarize":
                from analysis_outputs import summarize
                summarize(root, out)
            else:
                globals()[args.phase](root, out)
            print(f"{now()} completed {args.phase}", flush=True)
        except BaseException:
            traceback.print_exc()
            raise
        finally:
            sys.stdout, sys.stderr = stdout, stderr


if __name__ == "__main__":
    main()
