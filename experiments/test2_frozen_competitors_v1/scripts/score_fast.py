"""Extend frozen sequence features and apply the previously selected fast scorers."""
import argparse
from pathlib import Path
import sys
import time
sys.path.insert(0, "/bundle/code")
if len(sys.argv) > 1 and sys.argv[1].startswith("rapppid"):
    sys.path.insert(1, "/opt/rapppid/runtime")
    sys.path.insert(2, "/opt/rapppid/upstream/rapppid")
import numpy as np
import torch
from study_io import CELLS, SEEDS, arrays, checked_bundle, configure_cuda, now, read, record, save, sha, verify, write

OUT = Path("/output")


def replay(callback, tag, names, tolerance):
    fixtures = arrays("/data/fixtures.npz")
    expected = arrays(f"/data/fixtures_{tag}.npz")
    actual = callback(fixtures["a"], fixtures["b"])
    errors = {name: float(np.max(np.abs(actual[name] - expected[name]))) for name in names}
    assert max(errors.values()) <= tolerance, (tag, errors)
    return errors


def scored_added(callback):
    files = []
    for cell in CELLS:
        panel = arrays(f"/data/candidates/added_{cell}.npz")
        values = callback(panel["a"], panel["b"])
        assert all(len(v) == len(panel["a"]) and np.isfinite(v).all() for v in values.values())
        path = OUT / f"added_{cell}.npz"
        save(path, **values)
        files.append(record(path, OUT))
        print({"cell": cell, "rows": len(panel["a"]), "models": list(values)}, flush=True)
    return files


def rapppid(method, meta, config, device):
    from frozen_scorer import Scorer
    scorer = Scorer("/bundle", device)
    if method == "rapppid_original":
        from native_model import encode, tokenizer, singleton_embedding, learned_digest
        initial = learned_digest(scorer.model)
        tokenizer_ = tokenizer()
        extended = torch.empty((len(meta["sha256"]), 64), dtype=torch.float32, device=device)
        extended[:17000] = scorer.embeddings
        for i in range(17000, len(meta["sha256"])):
            extended[i] = singleton_embedding(scorer.model, encode(tokenizer_, meta["sequence"][i]), device)[0]
        scorer.embeddings = extended
        scorer.lengths = np.asarray(meta["length"])
        names = config["scorers"]
        def callback(a, b):
            return {names[0]: scorer.scores(a, b)[:, 0]}
        errors = replay(callback, method, names, config["batch_tolerance"])
        files = scored_added(callback)
        assert initial == learned_digest(scorer.model)
        with (OUT / "endpoint_features.npy").open("xb") as stream:
            np.save(stream, extended.cpu().numpy(), allow_pickle=False)
    else:
        import sentencepiece as sp
        from data import RapppidDataset2
        from model import learned_digest, scores
        initial = [learned_digest(m) for m in scorer.models]
        spp = sp.SentencePieceProcessor(model_file="/bundle/spm.model")
        assert sha("/bundle/spm.model") == config["tokenizer_sha256"]
        tokens = [np.asarray(RapppidDataset2.static_encode(1500, spp, sequence, sp=True, pad=True, sampling=False), np.int64)
                  for sequence in meta["sequence"][17000:]]
        with torch.inference_mode():
            for j, model in enumerate(scorer.models):
                z = torch.empty((len(meta["sha256"]), 64), dtype=torch.float32, device=device)
                z[:17000] = scorer.embeddings[j]
                for k, value in enumerate(tokens):
                    assert value.shape == (1500,) and np.count_nonzero(value) > 0
                    z[17000 + k] = model(torch.as_tensor(value[None], device=device)).reshape(64)
                scorer.embeddings[j] = z
                with (OUT / f"endpoint_features_{SEEDS[j]}.npy").open("xb") as stream:
                    np.save(stream, z.cpu().numpy(), allow_pickle=False)
        names = config["scorers"]
        def callback(a, b):
            members = np.column_stack([scores(m, e, a, b) for m, e in zip(scorer.models, scorer.embeddings, strict=True)])
            values = np.column_stack([members.mean(1, dtype=np.float64), members])
            return {name: values[:, j] for j, name in enumerate(names)}
        errors = replay(callback, method, names, config["batch_tolerance"])
        files = scored_added(callback)
        assert initial == [learned_digest(m) for m in scorer.models]
    return files, {"archived_legacy_replay_max_errors": errors, "learned_parameters_unchanged": True,
                   "native_tokenizer_and_1500_residue_policy_preserved": True}


def load_residues(meta):
    import h5py
    manifest = read("/scaled/residue_cache/RESIDUE_CACHE_MANIFEST.json")
    assert manifest["sequences_sha256"] == sha("/data/sequences.json")
    handle = h5py.File("/scaled/residue_cache/residues.h5", "r")
    assert handle.attrs["complete"] and len(handle) == len(meta["sha256"])
    assert handle.attrs["sequence_manifest_sha256"] == manifest["sequences_sha256"]
    return handle


def encode_tuna_extension(model, handle, meta, old, device):
    from adapter import endpoint_features
    z = torch.empty((len(meta["sha256"]), 64), dtype=torch.float32, device=device)
    z[:17000] = torch.as_tensor(old, device=device)
    indices = sorted(range(17000, len(meta["sha256"])), key=lambda i: (meta["length"][i], i))
    with torch.inference_mode():
        start = 0
        while start < len(indices):
            width = meta["length"][indices[min(start + 16, len(indices)) - 1]]
            count = max(1, min(16, 16000000 // (width * width)))
            ids = indices[start:start+count]
            lengths = [meta["length"][i] for i in ids]
            x = torch.zeros((len(ids), max(lengths), 640), device=device)
            for j, i in enumerate(ids):
                x[j, :lengths[j]] = torch.from_numpy(handle[str(i)][:]).to(device)
            z[ids] = endpoint_features(model, x, lengths)
            start += len(ids)
    assert torch.isfinite(z).all()
    return z


def tuna(meta, config, device):
    from adapter import create, enable_sdpa, cached_scores
    from training import make_model
    panels = {(cohort, cell): arrays(f"/data/candidates/{cohort}_{cell}.npz") for cell in CELLS for cohort in ("legacy", "added")}
    results = {key: {} for key in panels}
    specifications = read("/scaled/SCORER_FREEZE.json")
    assert read("/scaled/SELECTION.json")["selected"]["budget"] == 31188
    qualifications = []
    fixtures = arrays("/data/fixtures.npz")
    expected = arrays("/data/fixtures_tuna.npz")
    for label, prefix in (("selected_31k", "scaled_31188"), ("tuna_retrained_ensemble", "baseline")):
        for seed in SEEDS:
            member = next(m for m in specifications["members"] if m["name"] == f"{prefix}_seed{seed}")
            for key in ("weights", "features"):
                verify(Path("/scaled") / member[key]["path"], member[key])
            model = make_model(seed, device)
            initial = torch.load(Path("/scaled") / member["weights"]["path"], map_location=device, weights_only=True)
            model.load_state_dict(initial, strict=True)
            model.gp_layer.fitted = True
            model.eval().requires_grad_(False)
            z = torch.from_numpy(np.load(Path("/scaled") / member["features"]["path"], allow_pickle=False)).to(device)
            assert z.shape == (len(meta["sha256"]), 64) and torch.isfinite(z).all()
            member_name = f"selected_31k_seed{seed}" if label == "selected_31k" else f"tuna_retrained_seed{seed}"
            if label == "tuna_retrained_ensemble":
                actual = cached_scores(model, z, fixtures["a"], fixtures["b"])
                error = float(np.max(np.abs(actual.astype(np.float64) - expected[member_name])))
                assert error <= 2e-5, error
                qualifications.append({"member": member_name, "legacy_replay_max_error": error})
            for panel, pairs in panels.items():
                results[panel][member_name] = cached_scores(model, z, pairs["a"], pairs["b"]).astype(np.float64)
            assert all(torch.equal(v, initial[k]) for k, v in model.state_dict().items())
            print({"scored_frozen_member": member_name, "rows": sum(len(p["a"]) for p in panels.values())}, flush=True)
            del model, z, initial
            torch.cuda.empty_cache()
        for result in results.values():
            keys = [f"selected_31k_seed{s}" if label == "selected_31k" else f"tuna_retrained_seed{s}" for s in SEEDS]
            result[label] = np.column_stack([result[k] for k in keys]).mean(1, dtype=np.float64)
    initial = torch.load("/bundle/weights/tuna_original.pt", map_location=device, weights_only=True)
    model = create(device=device)
    model.load_state_dict(initial, strict=True)
    model.gp_layer.fitted = True
    model.eval().requires_grad_(False)
    enable_sdpa(model)
    with load_residues(meta) as handle:
        z = encode_tuna_extension(model, handle, meta, np.load("/bundle/features/tuna_original.npy", allow_pickle=False), device)
    error = float(np.max(np.abs(cached_scores(model, z, fixtures["a"], fixtures["b"], probabilities=True).astype(np.float64) - expected["tuna_original"])))
    assert error <= 1e-5, error
    qualifications.append({"member": "tuna_original", "legacy_replay_max_error": error})
    for (cohort, cell), pairs in panels.items():
        if cohort == "legacy":
            results[cohort, cell]["tuna_original"] = arrays(f"/legacy/tuna/{cell}.npz")["tuna_original"]
        else:
            results[cohort, cell]["tuna_original"] = cached_scores(model, z, pairs["a"], pairs["b"], probabilities=True).astype(np.float64)
    assert all(torch.equal(v, initial[k]) for k, v in model.state_dict().items())
    with (OUT / "tuna_original_endpoint_features.npy").open("xb") as stream:
        np.save(stream, z.cpu().numpy(), allow_pickle=False)
    files = []
    for (cohort, cell), result in results.items():
        path = OUT / f"{cohort}_{cell}.npz"
        save(path, **result)
        files.append(record(path, OUT))
    return files, {"member_checks": qualifications, "exact_saved_covariance_preserved": True,
                   "parameters_and_buffers_unchanged": True, "selected_budget": 31188, "selected_epoch": 1}


def partner(meta, config, device):
    from frozen_scorer import Scorer
    from data import score_cached
    scorer = Scorer("/bundle", device)
    norm = arrays("/bundle/normalizer.npz")
    with load_residues(meta) as handle:
        means = np.stack([handle[str(i)][:].mean(0, dtype=np.float32) for i in range(17000, len(meta["sha256"]))])
        extra = ((means.astype(np.float64) - norm["mean"]) / norm["std"]).astype(np.float32)
        scorer.globals = torch.cat([scorer.globals, torch.from_numpy(extra).to(device)])
        members = []
        for member, model, old in scorer.members:
            initial = {k: v.detach().clone() for k, v in model.state_dict().items()}
            shape = (len(meta["sha256"]) - 17000, *old.shape[1:])
            additional = torch.zeros(shape, device=device)
            if model.has_local:
                ids = sorted(range(17000, len(meta["sha256"])), key=lambda i: meta["length"][i])
                begin = 0
                with torch.inference_mode():
                    while begin < len(ids):
                        end = begin + 1
                        while end < len(ids) and end - begin < 64 and (end + 1 - begin) * meta["length"][ids[end]] <= 32768:
                            end += 1
                        batch = ids[begin:end]
                        lengths = [meta["length"][i] for i in batch]
                        residues = torch.zeros((len(batch), max(lengths), 640), device=device)
                        valid = torch.arange(max(lengths), device=device)[None] < torch.tensor(lengths, device=device)[:, None]
                        for j, i in enumerate(batch):
                            residues[j, :lengths[j]] = torch.from_numpy(handle[str(i)][:]).to(device)
                        additional[np.array(batch) - 17000] = model.encode(residues, valid)
                        begin = end
            z = torch.cat([old, additional])
            assert torch.isfinite(z).all()
            assert all(torch.equal(v, initial[k]) for k, v in model.state_dict().items())
            members.append((member, model, z))
            with (OUT / (member["name"] + "_endpoint_features.npy")).open("xb") as stream:
                np.save(stream, z.cpu().numpy(), allow_pickle=False)
    def callback(a, b):
        result = {member["name"]: score_cached(model, scorer.globals, z, a, b).astype(np.float64) for member, model, z in members}
        for ensemble in config["ensembles"]:
            names = [member["name"] for member, _, _ in members if member["ensemble"] == ensemble]
            assert len(names) == 3
            result[ensemble] = np.column_stack([result[name] for name in names]).mean(1, dtype=np.float64)
        return result
    errors = replay(callback, "partner", config["scorers"], 2e-5)
    files = scored_added(callback)
    with (OUT / "global_standardized.npy").open("xb") as stream:
        np.save(stream, scorer.globals.cpu().numpy(), allow_pickle=False)
    return files, {"legacy_replay_max_errors": errors, "normalizer_refitted": False,
                   "selected_recipes_unchanged": config["ensembles"], "all_three_seeds_retained": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=("tuna", "rapppid_original", "rapppid_recovery", "partner"))
    args = parser.parse_args()
    started = time.monotonic()
    config = checked_bundle()
    if (OUT / "COMPLETE.json").exists():
        for item in read(OUT / "COMPLETE.json")["files"]:
            verify(OUT / item["path"], item)
        return
    meta = read("/data/sequences.json")
    assert meta["sha256"][:17000] == read("/bundle/endpoints.json")
    device = configure_cuda()
    if args.method.startswith("rapppid"):
        files, checks = rapppid(args.method, meta, config, device)
    else:
        files, checks = globals()[args.method](meta, config, device)
    write(OUT / "COMPLETE.json", {"method": args.method, "at_utc": now(), "files": files, "checks": checks,
          "elapsed_seconds": time.monotonic() - started, "test_truth_read": False, "training_performed": False,
          "bundle_sha256": sha("/bundle/SCORER_FREEZE.json"), "sequence_sha256": sha("/data/sequences.json"),
          "code_sha256": sha(__file__)})


if __name__ == "__main__":
    main()
