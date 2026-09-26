"""Append sequence-only D-SCRIPT projections for the 583 additional endpoints."""
import argparse
from pathlib import Path
import time
import sys
sys.path.insert(0, "/bundle/code")
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from native_adapter import create, learned_digest
from study_io import SEEDS, checked_bundle, configure_cuda, now, read, record, sha, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=("dscript_original", "dscript_retrained"))
    method = parser.parse_args().method
    out = Path("/output")
    started = time.monotonic()
    config = checked_bundle()
    meta = read("/data/sequences.json")
    assert read("/bundle/endpoints.json") == meta["sha256"][:17000]
    if (out / "COMPLETE.json").exists():
        for item in read(out / "COMPLETE.json")["files"]:
            assert sha(out / item["path"]) == item["sha256"]
        print("Completed feature extension verified", flush=True)
        return
    device = configure_cuda()
    models = {}
    if method == "dscript_original":
        models["dscript_original"] = create(device=device, max_length=max(meta["length"]), tile_area=config["tile_area"])
    else:
        from model import fresh
        for seed in SEEDS:
            name = f"dscript_seed_{seed}"
            model = fresh(seed, device)
            model.load_state_dict(torch.load(Path("/bundle/weights") / (name + ".pt"), map_location=device, weights_only=True), strict=True)
            model.eval().requires_grad_(False)
            models[name] = model
    initial = {name: learned_digest(model) for name, model in models.items()}
    expected = {"dscript_original": config["learned_state_sha256"]} if method == "dscript_original" else config["learned_state_sha256"]
    assert initial == expected
    lengths = np.array(meta["length"][17000:], np.int64)
    offsets = np.r_[0, np.cumsum(lengths)]
    lm = get_pretrained("lm_v1").to(device).eval().requires_grad_(False)
    alphabet = Uniprot21()
    values = {name: np.lib.format.open_memmap(out / (name + ".npy"), mode="w+", dtype=np.float32,
              shape=(int(offsets[-1]), 100)) for name in models}
    old_offsets = np.load("/bundle/features/offsets.npy", allow_pickle=False)
    errors = {name: 0. for name in models}
    with torch.inference_mode():
        for i in (0, 8000, 16999):
            x = torch.from_numpy(alphabet.encode(meta["sequence"][i].encode())).long()[None].to(device)
            raw = lm.transform(x)
            for name, model in models.items():
                filename = "projected.npy" if method == "dscript_original" else name + ".npy"
                historical = np.load(Path("/bundle/features") / filename, mmap_mode="r", allow_pickle=False)
                reference = historical[old_offsets[i]:old_offsets[i+1]]
                actual = model.embedding(raw)[0].cpu().numpy()
                errors[name] = max(errors[name], float(np.max(np.abs(actual - reference))))
        assert max(errors.values()) <= 2e-4, errors
        for j, sequence in enumerate(meta["sequence"][17000:]):
            x = torch.from_numpy(alphabet.encode(sequence.encode())).long()[None].to(device)
            raw = lm.transform(x)
            assert raw.shape == (1, len(sequence), 6165) and torch.isfinite(raw).all()
            for name, model in models.items():
                z = model.embedding(raw)[0].cpu().numpy()
                assert z.shape == (len(sequence), 100) and np.isfinite(z).all()
                values[name][offsets[j]:offsets[j+1]] = z
            if (j + 1) % 50 == 0 or j + 1 == len(lengths):
                print({"method": method, "new_endpoints": j + 1, "total": len(lengths), "seconds": time.monotonic() - started}, flush=True)
    for value in values.values():
        value.flush()
    assert initial == {name: learned_digest(model) for name, model in models.items()}
    files = [record(out / (name + ".npy"), out) for name in models]
    write(out / "COMPLETE.json", {"at_utc": now(), "method": method, "files": files,
        "bundle_sha256": sha("/bundle/SCORER_FREEZE.json"), "sequence_sha256": sha("/data/sequences.json"),
        "old_sequence_endpoints_unchanged": 17000, "new_sequence_endpoints": len(lengths),
        "native_projection_replay_errors": errors, "projection_tolerance": 2e-4,
        "learned_parameters_unchanged": True, "test_pairs_or_truth_read": False,
        "elapsed_seconds": time.monotonic() - started, "code_sha256": sha(__file__)})


if __name__ == "__main__":
    main()
