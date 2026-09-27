"""Candidate-only scoring; freeze all sixteen controls before truth access."""
from pathlib import Path
import hashlib
import time
import numpy as np
from scipy import sparse
import torch
from control_io import (
    ROOT, OUT, KERNELS, MODELS, arrays, check_pairs, cuda, manifest_files, now,
    panel_names, phase_guard, protocol, read, record, save, sha, verify, write,
)
from control_math import neighbor_max_cuda, transfer_cuda, unit
from ipin_openppi.homology_source.semantics import exhaustive_transfer_numpy


def hash_control(hashes, a, b):
    output = np.empty(len(a), np.float64)
    for i, (aa, bb) in enumerate(zip(a, b, strict=True)):
        left, right = sorted((hashes[aa], hashes[bb]))
        pair = "pair:" + hashlib.sha256(f"{left}|{right}".encode()).hexdigest()
        output[i] = int.from_bytes(hashlib.sha256(
            f"ipin-openppi-pu-r-baseline-v1:20260803:baseline:{pair}".encode()).digest(), "big") / (2**256-1)
    return output


def selected_reference(panels, values, device):
    from adapter import cached_scores
    from training import make_model
    frozen = read("/selected/SCORER_FREEZE.json")
    old_freeze = read("/reference_predictions/FREEZE.json")
    inputs = read(ROOT / "INPUT_FREEZE.json")
    records = {}
    for item in old_freeze["files"]:
        cohort, cell = item["cohort"], item["cell"]
        p = Path("/reference_predictions") / Path(item["path"]).name
        verify(p, item)
        candidate_parent = next(x for x in inputs["parents"]
                                if x["path"].endswith(f"/private/candidates/{cohort}_{cell}.npz"))
        if candidate_parent["sha256"] != item["candidate_sha256"]:
            raise RuntimeError("reference prediction/candidate identity mismatch")
        name = f"test_{cohort}_{cell}"
        with np.load(p, allow_pickle=False) as z:
            values[name]["selected_31k"] = z["selected_31k"].copy()
        records[name] = item
    development = {name: [] for fold, cell, cohort, name in panel_names() if fold == "development"}
    checks = []
    for seed in protocol()["reference"]["seeds"]:
        member = next(x for x in frozen["members"] if x["name"] == f"scaled_31188_seed{seed}")
        for k in ("features", "weights"):
            verify(Path("/selected") / member[k]["path"], member[k])
        initial = torch.load(Path("/selected") / member["weights"]["path"], map_location=device, weights_only=True)
        model = make_model(seed, device)
        model.load_state_dict(initial, strict=True)
        model.gp_layer.fitted = True
        model.eval().requires_grad_(False)
        z = torch.from_numpy(np.load(Path("/selected") / member["features"]["path"], allow_pickle=False)).to(device)
        for name in development:
            data = panels[name]
            development[name].append(cached_scores(model, z, data["a"], data["b"]).astype(np.float64))
        maximum = 0.
        for fold, cell, cohort, name in panel_names():
            if fold != "test":
                continue
            data = panels[name]
            ids = np.unique(np.linspace(0, len(data["a"])-1, 128, dtype=np.int64))
            actual = cached_scores(model, z, data["a"][ids], data["b"][ids]).astype(np.float64)
            with np.load(Path("/reference_predictions") / f"{cohort}_{cell}.npz", allow_pickle=False) as old:
                expected = old[f"selected_31k_seed{seed}"][ids]
            error = float(np.max(np.abs(actual-expected)))
            maximum = max(maximum, error)
            if error > 2e-5:
                raise RuntimeError("current TUnA state replay failed")
        if not all(torch.equal(v, initial[k]) for k, v in model.state_dict().items()):
            raise RuntimeError("reference model mutated during inference")
        checks.append({"seed": seed, "test_fixture_max_error": maximum, "covariance_preserved": True})
        print({"reference_seed_scored": seed, "test_replay_error": maximum}, flush=True)
        del model, z, initial
        torch.cuda.empty_cache()
    for name, members in development.items():
        values[name]["selected_31k"] = np.mean(members, axis=0)
    return {"reference_test_predictions": records, "member_checks": checks}


def main():
    phase_guard()
    if Path("/truth").exists() or Path("/devtruth").exists() or (OUT / "PREDICTION_FREEZE.json").exists():
        raise RuntimeError("evaluation truth visible or predictions already frozen")
    device = cuda()
    started = time.monotonic()
    meta = read("/sequences/sequences.json")
    n = len(meta["sha256"])
    inputs = read(ROOT / "INPUT_FREEZE.json")
    for item in inputs["files"]:
        if item["path"].startswith("data/candidates/"):
            verify(Path("/candidates") / Path(item["path"]).name, item)
    manifest_files("/features/FEATURES.json", "/features")
    manifest_files("/features/ALIGNMENT.json", "/features")
    manifest_files("/training/TRAINING.json", "/training")
    if read("/features/FEATURES.json")["sequence_manifest_sha256"] != sha("/sequences/sequences.json"):
        raise RuntimeError("endpoint feature identity changed")
    panels = {name: arrays(Path("/candidates")/(name+".npz")) for _, _, _, name in panel_names()}
    for rows in panels.values():
        if set(rows) != {"a", "b"}:
            raise RuntimeError("candidate scoring received labels/weights")
        check_pairs(rows["a"], rows["b"], n)
    values = {name: {} for name in panels}
    kmer = sparse.load_npz("/features/kmer.npz")
    adjacency = sparse.load_npz("/features/adjacency.npz")
    graph = arrays("/features/graph.npz")
    degree, mass, exposed = graph["degree"], graph["component_mass"], graph["exposed"]
    raw_unit = unit(np.load("/features/raw_pooled.npy", allow_pickle=False))
    aac = np.load("/features/aac_unit.npy", allow_pickle=False)
    unary = arrays("/training/unary_scores.npz")
    loglength = np.log1p(np.asarray(meta["length"], np.float64))
    for name, data in panels.items():
        a, b = data["a"], data["b"]
        v = values[name]
        v["deterministic_hash"] = hash_control(meta["sha256"], a, b)
        v["training_degree_sum"] = np.log1p(degree[a]) + np.log1p(degree[b])
        v["preferential_attachment"] = np.log1p(degree[a]*degree[b])
        v["component_degree_mass_product"] = np.log1p(mass[a]*mass[b])
        v["sequence_length_sum"] = loglength[a]+loglength[b]
        v["sequence_length_ratio"] = -np.abs(loglength[a]-loglength[b])
        for key in ("training_common_neighbors", "within_pair_3mer_cosine", "pooled_150m_cosine", "aac_cosine"):
            v[key] = np.empty(len(a), np.float64)
        for start in range(0, len(a), 8192):
            stop = min(start+8192, len(a))
            aa, bb = a[start:stop], b[start:stop]
            v["training_common_neighbors"][start:stop] = np.log1p(
                np.asarray(adjacency[aa].multiply(adjacency[bb]).sum(1)).ravel())
            v["within_pair_3mer_cosine"][start:stop] = np.asarray(kmer[aa].multiply(kmer[bb]).sum(1)).ravel()
            v["pooled_150m_cosine"][start:stop] = np.einsum("ij,ij->i", raw_unit[aa], raw_unit[bb])
            v["aac_cosine"][start:stop] = np.einsum("ij,ij->i", aac[aa], aac[bb])
        for key in ("endpoint_linear", "endpoint_mlp64"):
            v[key] = unary[key][a]+unary[key][b]
        if name.endswith("C3") and any(np.any(v[key]) for key in (
                "training_degree_sum", "preferential_attachment", "component_degree_mass_product",
                "training_common_neighbors")):
            raise RuntimeError("C3 train-only topology control is not constant")
        print({"direct_controls_scored": name, "rows": len(a)}, flush=True)
    transfer_checks = {}
    for kernel, label in KERNELS.items():
        if kernel == "kmer":
            similarity = (kmer @ kmer[exposed].T).toarray()
        elif kernel == "pooled":
            similarity = np.maximum(raw_unit @ raw_unit[exposed].T, 0.)
        else:
            full = np.load(f"/features/similarity_{kernel}.npy", mmap_mode="r", allow_pickle=False)
            similarity = np.asarray(full[:, exposed])
            del full
        tensor = torch.as_tensor(similarity, dtype=torch.float64, device=device)
        neighbor = neighbor_max_cuda(tensor, graph["edge_a"], graph["edge_b"])
        maximum_oracle, maximum_swap = 0., 0.
        for name, data in panels.items():
            a, b = data["a"], data["b"]
            result = transfer_cuda(tensor, neighbor, a, b)
            fixture = np.unique(np.linspace(0, len(a)-1, 31, dtype=np.int64))
            # Independent direct evaluation of every fitting edge in both
            # orientations, with global query rows and compact target columns.
            oracle = np.array([np.maximum(
                np.minimum(similarity[x, graph["edge_a"]], similarity[y, graph["edge_b"]]),
                np.minimum(similarity[x, graph["edge_b"]], similarity[y, graph["edge_a"]])).max()
                for x, y in zip(a[fixture], b[fixture], strict=True)])
            reverse = transfer_cuda(tensor, neighbor, b[fixture], a[fixture])
            err = float(np.max(np.abs(result[fixture]-oracle)))
            swap = float(np.max(np.abs(result[fixture]-reverse)))
            maximum_oracle, maximum_swap = max(maximum_oracle, err), max(maximum_swap, swap)
            if err > 1e-12 or swap > 1e-12:
                raise RuntimeError("exact transfer or symmetry oracle failed")
            values[name][label] = result
        transfer_checks[label] = {"max_full_edge_oracle_error": maximum_oracle,
                                  "max_swap_error": maximum_swap, "training_edges": 31188}
        print({"transfer_control_scored": label, **transfer_checks[label]}, flush=True)
        del tensor, neighbor, similarity
        torch.cuda.empty_cache()
    reference = selected_reference(panels, values, device)
    files = []
    for fold, cell, cohort, name in panel_names():
        scores = values[name]
        if set(scores) != set(MODELS) or any(len(v) != len(panels[name]["a"]) or not np.isfinite(v).all()
                                           for v in scores.values()):
            raise RuntimeError("incomplete/nonfinite prediction coverage")
        path = OUT / (name+".npz")
        save(path, **{key: scores[key] for key in MODELS})
        files.append({**record(path, OUT), "partition": fold, "cell": cell, "cohort": cohort,
                      "rows": len(panels[name]["a"]), "candidate_sha256": sha(Path("/candidates")/(name+".npz"))})
    write(OUT / "PREDICTION_FREEZE.json", {
        "at_utc": now(), "models": list(MODELS), "files": files,
        "implementation_freeze_sha256": sha(ROOT / "IMPLEMENTATION_FREEZE.json"),
        "protocol_sha256": sha(ROOT / "PROTOCOL.json"),
        "input_freeze_sha256": sha(ROOT / "INPUT_FREEZE.json"),
        "feature_freeze_sha256": sha("/features/FEATURES.json"),
        "alignment_freeze_sha256": sha("/features/ALIGNMENT.json"),
        "training_freeze_sha256": sha("/training/TRAINING.json"),
        "complete_finite_identity_aligned_coverage": True,
        "evaluation_truth_mounted": False, "transfer_qualification": transfer_checks,
        "reference_replay": reference, "elapsed_seconds": time.monotonic()-started,
    })
    print({"prediction_freeze_complete": True, "models": len(MODELS), "panels": len(files)}, flush=True)


if __name__ == "__main__":
    main()
