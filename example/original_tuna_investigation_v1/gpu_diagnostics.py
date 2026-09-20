"""Frozen TUnA query replacement, score decomposition, and authors-checkpoint oracle."""
from __future__ import annotations

import math
import os
import sys
import time

import h5py
import numpy as np
import torch

from investigate import ROOT, OUT, PARENT, check_inputs, read, record, table, write_csv, write_json

sys.path.insert(0, str(ROOT / "benchmark/tuna/scripts"))
import adapter


def score_components(model, z, left, right):
    output = np.empty((len(left), 4), dtype=np.float64)
    with torch.inference_mode():
        for start in range(0, len(left), 2048):
            stop = min(start + 2048, len(left))
            a = torch.as_tensor(left[start:stop], device=z.device)
            b = torch.as_tensor(right[start:stop], device=z.device)
            features = torch.maximum(z[a], z[b])
            logits, var = model.gp_layer(features, update_precision=False, get_var=True)
            raw = logits.reshape(-1)
            adjusted = raw / torch.sqrt(1 + math.pi / 8 * var)
            output[start:stop] = torch.stack([raw, var, adjusted, torch.sigmoid(adjusted)], 1).cpu().numpy()
    assert np.isfinite(output).all() and (output[:, 1] >= 0).all()
    return output


def main():
    assert os.environ.get("APPTAINER_CONTAINER"), "Run in the pinned TUnA SIF"
    check_inputs()
    torch.set_num_threads(8)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    assert torch.cuda.is_available() and torch.cuda.device_count() == 1
    start = time.monotonic()
    rows = table(PARENT / "all_twelve_targets_scores.csv")
    order = read(PARENT / "sequence_order.json")
    idx = {h: i for i, h in enumerate(order)}
    left = np.array([idx[r["query_sequence_sha256"]] for r in rows])
    right = np.array([idx[r["partner_sequence_sha256"]] for r in rows])
    genes = list(dict.fromkeys(r["query_gene"] for r in rows))
    query_indices = [left[next(i for i, r in enumerate(rows) if r["query_gene"] == gene)] for gene in genes]
    outputs, qualifications, components = {}, [], None
    seed_members = [f"tuna_retrained_seed{s}" for s in (20260803, 20260817, 20260831)]
    original_path = ROOT / "benchmark/tuna/runs/scorer_bundle/weights/tuna_original.pt"
    for member in ["tuna_original"] + seed_members:
        checkpoint = original_path if member == "tuna_original" else ROOT / f".private/frozen_pair_models_v2/bundle/weights/{member}.pt"
        initial = torch.load(checkpoint, map_location="cpu", weights_only=True)
        model = adapter.create(checkpoint=checkpoint, device="cuda")
        model.gp_layer.fitted = True
        model.eval()
        for p in model.parameters():
            p.requires_grad_(False)
        z = torch.as_tensor(np.load(PARENT / f"{member}_fresh_endpoint_features.npy", allow_pickle=False), device="cuda")
        actual_components = score_components(model, z, left, right)
        actual = actual_components[:, 3 if member == "tuna_original" else 2]
        reference = np.array([float(r[member + "_score"]) for r in rows])
        error = float(np.max(np.abs(actual - reference)))
        assert error < 1e-5, (member, error)
        values = []
        for gene, query_index in zip(genes, query_indices, strict=True):
            values.append(adapter.cached_scores(model, z, np.full(len(rows), query_index), right,
                                                probabilities=member == "tuna_original"))
        outputs[member] = np.asarray(values, np.float64)
        assert all(torch.equal(v.cpu(), initial[k]) for k, v in model.state_dict().items())
        qualifications.append(dict(member=member, checkpoint=record(checkpoint), all_saved_pair_scores_max_absolute_error=error,
                                   all_parameters_and_buffers_unchanged=True))
        if member == "tuna_original":
            components = actual_components
        print(f"{member}: 12 replacement queries scored; actual-query error {error:.3g}", flush=True)
        del model, z, initial
        torch.cuda.empty_cache()
    outputs["tuna_retrained"] = np.mean([outputs[m] for m in seed_members], axis=0, dtype=np.float64)
    np.savez_compressed(OUT / "query_swap_scores.npz", query_genes=np.array(genes),
                        **{k: outputs[k] for k in ("tuna_original", "tuna_retrained")})
    write_csv("original_score_components.csv", [dict(row_index=i, query_gene=r["query_gene"], partner_uniprot=r["partner_uniprot"],
                                                    raw_logit=float(components[i, 0]), variance=float(components[i, 1]),
                                                    adjusted_logit=float(components[i, 2]), probability=float(components[i, 3]))
                                               for i, r in enumerate(rows)])
    authors_path = ROOT / "benchmark/tuna/weights/bernett_original.pt"
    authors = torch.load(authors_path, map_location="cpu", weights_only=True)
    runtime = torch.load(original_path, map_location="cpu", weights_only=True)
    assert authors.keys() == runtime.keys()
    differing = [k for k in authors if not torch.equal(authors[k], runtime[k])]
    assert set(differing) <= {"gp_layer.covariance"}, differing
    # Deliberately do not set fitted=True: native eval must recompute covariance
    # from the authors' released precision matrix, as its own code specifies.
    oracle = adapter.create(checkpoint=authors_path, device="cuda")
    oracle.eval()
    covariance_error = float(torch.max(torch.abs(oracle.gp_layer.covariance.cpu() - runtime["gp_layer.covariance"])))
    for parameter in oracle.parameters():
        parameter.requires_grad_(False)
    fixture_ids = {i for i, r in enumerate(rows) if r["class"] == "P"}
    for gene in genes:
        candidates = [i for i, r in enumerate(rows) if r["query_gene"] == gene and r["class"] == "U"]
        fixture_ids.add(max(candidates, key=lambda i: float(rows[i]["tuna_original_score"])))
    fixture_ids.add(max(range(len(rows)), key=lambda i: int(rows[i]["query_sequence_length"]) + int(rows[i]["partner_sequence_length"])))
    fixture_rows = []
    with h5py.File(PARENT / "tuna_fresh_residues.h5", "r") as residues, torch.inference_mode():
        for i in sorted(fixture_ids):
            r = rows[i]
            a = torch.as_tensor(residues[r["query_sequence_sha256"]][:], device="cuda")
            b = torch.as_tensor(residues[r["partner_sequence_sha256"]][:], device="cuda")
            native = float(adapter.native_scores(oracle, [a], [b])[0])
            saved = float(r["tuna_original_score"])
            fixture_rows.append(dict(row_index=i, query_gene=r["query_gene"], partner_gene=r["partner_gene"],
                                     partner_uniprot=r["partner_uniprot"], **{"class": r["class"]},
                                     native_authors_checkpoint_probability=native, saved_probability=saved,
                                     absolute_error=abs(native - saved)))
    error = max(r["absolute_error"] for r in fixture_rows)
    assert error < 1e-5, error
    assert all(torch.equal(v.cpu(), authors[k]) for k, v in oracle.state_dict().items() if k != "gp_layer.covariance")
    write_csv("authors_checkpoint_native_predictions.csv", fixture_rows)
    check_inputs()
    write_json("GPU_DIAGNOSTICS.json", dict(
        device=torch.cuda.get_device_name(), torch=torch.__version__, elapsed_seconds=time.monotonic() - start,
        precision="FP32; TF32 disabled; no autocast", reused_parent_residue_and_endpoint_arrays=True,
        runtime_checkpoint_covariance_refitted=False, author_covariance_native_eval_recomputation_in_memory=True,
        original_vs_runtime_differing_state_keys=differing, authors_checkpoint=record(authors_path),
        native_recomputed_vs_frozen_covariance_max_absolute_error=covariance_error,
        native_unaccelerated_batch_one_fixture_count=len(fixture_rows), native_fixture_max_absolute_error=error,
        native_agreement_tolerance=1e-5, all_37_positives_checked=True,
        original_probability_zero_count=int((components[:, 3] == 0).sum()),
        original_probability_one_count=int((components[:, 3] == 1).sum()),
        qualifications=qualifications, swap_cache=record(OUT / "query_swap_scores.npz"),
        pretrained_checkpoint_files_unchanged=True, model_training_or_selection=False,
        protected_test_records_read=False, passed=True))
    print(f"Authors native oracle: {len(fixture_rows)} pairs, max error {error:.3g}", flush=True)


if __name__ == "__main__":
    main()
