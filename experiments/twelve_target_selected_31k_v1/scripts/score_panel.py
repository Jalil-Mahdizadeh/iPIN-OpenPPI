"""Score the unchanged historical panel with the frozen selected 31k ensemble."""
from pathlib import Path
import hashlib
import math
import time
import h5py
import numpy as np
import torch
import adapter
from common import cuda
from training import make_model
from panel_io import now, read, sha, verify_mounted, write_csv, write_json

OUT = Path("/output")
PANEL = Path("/panel")


def main():
    started = time.monotonic()
    freeze = read("/freeze/INPUT_FREEZE.json")
    verify_mounted(freeze, {"panel", "model", "native", "upstream", "code"})
    device = cuda(freeze["seeds"][0])
    rows = read(PANEL / "pairs.json")
    order = read(PANEL / "sequence_order.json")
    snapshot = read(PANEL / "uniprot_sequences.json")["records"]
    assert len(rows) == 5587 and sum(r["class"] == "P" for r in rows) == 37
    sequences = {}
    for value in snapshot.values():
        assert value["taxon_id"] == 9606
        assert hashlib.sha256(value["sequence"].encode()).hexdigest() == value["sequence_sha256"]
        sequences[value["sequence_sha256"]] = value["sequence"]
    assert len(order) == 4012 and set(order) == set(sequences)
    assert order == sorted(order, key=lambda h: (len(sequences[h]), h))
    index = {h: i for i, h in enumerate(order)}
    lengths = np.array([len(sequences[h]) for h in order], np.int64)
    offsets = np.r_[0, np.cumsum(lengths)]
    a = np.array([index[r["query_sequence_sha256"]] for r in rows], np.int64)
    b = np.array([index[r["partner_sequence_sha256"]] for r in rows], np.int64)
    for r in rows:
        for prefix in ("query", "partner"):
            record = snapshot[r[prefix + "_uniprot"]]
            assert record["sequence_sha256"] == r[prefix + "_sequence_sha256"]
            assert record["sequence_length"] == r[prefix + "_sequence_length"]
    values = torch.empty((int(offsets[-1]), 640), dtype=torch.float32, device=device)
    with h5py.File(PANEL / "tuna_fresh_residues.h5", "r") as cache:
        assert bool(cache.attrs["complete"])
        assert cache.attrs["sequence_snapshot_sha256"] == sha(PANEL / "uniprot_sequences.json")
        assert cache.attrs["encoder_sha256"] == read(PANEL / "TUNA_RUN.json")["esm_qualification"]["encoder_sha256"]
        assert set(cache.keys()) == set(order)
        for i, h in enumerate(order):
            v = cache[h][:]
            assert v.dtype == np.float32 and v.shape == (lengths[i], 640)
            assert np.isfinite(v).all()
            values[offsets[i]:offsets[i+1]] = torch.from_numpy(v).to(device)
    print(f"Verified panel cache: {len(order)} proteins, {offsets[-1]:,} residues; {torch.cuda.get_device_name()}", flush=True)
    targets = list(dict.fromkeys(r["query_gene"] for r in rows))
    fixtures = sorted(set([next(i for i, r in enumerate(rows) if r["query_gene"] == t) for t in targets]
                          + [int(np.argmax(lengths[a] + lengths[b]))]))
    scores, qualifications = {}, []
    for seed in freeze["seeds"]:
        start = time.monotonic()
        name = f"tuna_selected_31k_seed{seed}"
        checkpoint = Path(f"/model/frozen/scaled_31188_seed{seed}.pt")
        initial = torch.load(checkpoint, map_location="cpu", weights_only=True)
        model = make_model(seed, device)
        model.load_state_dict(initial, strict=True)
        # fitted is not serialized: set BEFORE eval() to preserve saved covariance.
        model.gp_layer.fitted = True
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        assert torch.equal(model.gp_layer.covariance.cpu(), initial["gp_layer.covariance"])
        z = torch.empty((len(order), 64), dtype=torch.float32, device=device)
        with torch.inference_mode():
            begin = 0
            next_report = 1000
            while begin < len(order):
                longest = lengths[min(begin + 16, len(order)) - 1]
                count = max(1, min(16, 16000000 // int(longest * longest)))
                ids = list(range(begin, min(begin + count, len(order))))
                width = int(lengths[ids].max())
                x = torch.zeros((len(ids), width, 640), dtype=torch.float32, device=device)
                for j, i in enumerate(ids):
                    x[j, :lengths[i]] = values[offsets[i]:offsets[i+1]]
                z[ids] = adapter.endpoint_features(model, x, lengths[ids].tolist())
                begin += len(ids)
                if begin >= next_report or begin == len(order):
                    print(f"Seed {seed}: {begin}/{len(order)} learned endpoint features; {time.monotonic()-start:.1f}s", flush=True)
                    next_report += 1000
        assert torch.isfinite(z).all()
        score = adapter.cached_scores(model, z, a, b, probabilities=False)
        reverse = adapter.cached_scores(model, z, b, a, probabilities=False)
        assert np.array_equal(score, reverse)
        oracle = adapter.create(seed=seed, checkpoint=checkpoint, device=device)
        oracle.gp_layer.fitted = True
        oracle.eval()
        reference = []
        with torch.inference_mode():
            for i in fixtures:
                left = values[offsets[a[i]]:offsets[a[i]+1]]
                right = values[offsets[b[i]]:offsets[b[i]+1]]
                packed = adapter.native.test_pack([left], [right], [0], 512, 640, device)
                logit, variance = oracle.forward(packed[0], packed[1], packed[3], packed[4], packed[5], packed[6], True, False)
                reference.append(float((logit.reshape(-1) / torch.sqrt(1 + math.pi / 8 * variance)).reshape(())))
        error = float(np.max(np.abs(score[fixtures].astype(np.float64) - reference)))
        assert error <= 1e-5, (seed, error)
        for instance in (model, oracle):
            for key, value in instance.state_dict().items():
                assert torch.equal(value.detach().cpu(), initial[key]), (seed, key)
        with (OUT / f"{name}_endpoint_features.npy").open("xb") as stream:
            np.save(stream, z.cpu().numpy(), allow_pickle=False)
        scores[name] = score.astype(np.float64)
        qualifications.append({"seed": seed, "checkpoint_sha256": sha(checkpoint),
            "native_max_absolute_error": error, "native_tolerance": 1e-5,
            "fixture_rows_zero_based": fixtures, "pair_order_symmetry_passed": True,
            "parameters_and_buffers_unchanged": True, "saved_GP_covariance_preserved": True,
            "elapsed_seconds": time.monotonic() - start})
        print(f"Seed {seed}: all {len(rows)} scores complete; native error {error:.3g}", flush=True)
        del model, oracle, z, initial
        torch.cuda.empty_cache()
    scores["tuna_selected_31k"] = np.column_stack(list(scores.values())).mean(1, dtype=np.float64)
    write_csv(OUT / "selected_31k_scores.csv", [{"row_index": i, **{k + "_score": float(v[i]) for k, v in scores.items()}} for i in range(len(rows))])
    write_json(OUT / "sequence_order.json", order)
    write_json(OUT / "SCORING_RUN.json", {"completed_at_utc": now(), "elapsed_seconds": time.monotonic() - started,
        "pairs": len(rows), "unique_sequences": len(order), "gpu": torch.cuda.get_device_name(),
        "torch": torch.__version__, "cuda": torch.version.cuda, "precision": "FP32; TF32 disabled; no autocast",
        "budget": 31188, "epoch": 1, "seeds": freeze["seeds"], "training_or_reselection": False,
        "reused_verified_ESM_residues": True, "recomputed_endpoint_features_per_seed": len(order),
        "GP_covariance_refitted": False, "GP_fitted_flag_set_before_eval": True,
        "qualifications": qualifications, "score_sha256": sha(OUT / "selected_31k_scores.csv"),
        "input_freeze_sha256": sha("/freeze/INPUT_FREEZE.json")})


if __name__ == "__main__":
    main()
