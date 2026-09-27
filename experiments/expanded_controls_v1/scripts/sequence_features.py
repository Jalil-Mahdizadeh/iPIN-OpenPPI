"""Identity-joined original raw pooled vectors and sequence-only extension."""
from pathlib import Path
import numpy as np
from scipy import sparse
from control_io import ROOT, OUT, arrays, now, read, record, save, save_array, sha, verify, write
from control_math import composition, graph
from ipin_openppi.partner_specificity.semantics import embedding_indices, normalize
from ipin_openppi.stage1.baselines import kmer3_csr


def main():
    if Path("/truth").exists() or (OUT / "FEATURES.json").exists():
        raise RuntimeError("truth visibility or existing feature freeze")
    frozen = read(ROOT / "INPUT_FREEZE.json")
    meta = read("/sequences/sequences.json")
    n = len(meta["sha256"])
    manifest = read("/raw/EMBEDDING_MANIFEST.json")
    if sha("/raw/pooled_embeddings.f32.npy") != manifest["matrix_sha256"]:
        raise RuntimeError("raw embedding parent changed")
    raw_parent = np.load("/raw/pooled_embeddings.f32.npy", allow_pickle=False)
    indices = embedding_indices(manifest["vectors"], meta["sha256"][:17000], len(raw_parent))
    raw = np.empty((n, 640), np.float32)
    raw[:17000] = raw_parent[indices]
    # Match the established sequence-only extension's extraction order, including
    # its three fixed public-training fixtures, to remove batching ambiguity.
    train = sorted([i for i, p in enumerate(meta["partition"][:17000]) if p == "train"],
                   key=lambda i: meta["length"][i])
    fixture = [train[len(train)//2], train[int(.95*len(train))], train[-1]]
    selected = fixture + list(range(17000, n))
    from ipin_openppi.stage1.embeddings import SequenceRecord, extract_matrix
    records = [SequenceRecord(meta["sha256"][i], meta["sequence"][i], meta["length"][i]) for i in selected]
    matrix, details = extract_matrix(candidate_id="esm2_150m", records=records, model_root=Path("/encoder"))
    fixture_error = float(np.max(np.abs(matrix[:3] - raw[fixture])))
    if fixture_error > 2e-5:
        raise RuntimeError(f"raw embedding replay failed: {fixture_error}")
    raw[17000:] = matrix[3:]
    # Reproducing the established standardized vectors verifies the entire
    # sequence identity join, including all 583 newly extracted endpoints.
    norm = arrays("/raw/training_normalization.npz")
    standardized_old = ((raw.astype(np.float64) - norm["mean"]) / norm["standard_deviation"]).astype(np.float32)
    archived = np.load("/pooled/pooled_features.npy", allow_pickle=False)
    reproduction_error = float(np.max(np.abs(standardized_old - archived)))
    if reproduction_error > 2e-5:
        raise RuntimeError(f"extended embedding identity/reproduction failed: {reproduction_error}")
    save_array(OUT / "raw_pooled.npy", raw)
    fit = np.asarray(meta["partition"]) == "train"
    z, mean, std = normalize(raw, fit)
    save_array(OUT / "standardized_train2.npy", z)
    save(OUT / "train2_normalization.npz", mean=mean, std=std, fit_endpoints=np.flatnonzero(fit))
    kmer = kmer3_csr(meta["sequence"])
    sparse.save_npz(OUT / "kmer.npz", kmer)
    save_array(OUT / "aac_unit.npy", composition(meta["sequence"]))
    p = arrays("/train/positive.npz")
    adjacency, degree, mass = graph(n, p["p_a"], p["p_b"], meta["extended_component"])
    sparse.save_npz(OUT / "adjacency.npz", adjacency)
    exposed = np.flatnonzero(degree > 0)
    index = np.full(n, -1, np.int64)
    index[exposed] = np.arange(len(exposed))
    save(OUT / "graph.npz", degree=degree, component_mass=mass, exposed=exposed,
         edge_a=index[p["p_a"]], edge_b=index[p["p_b"]])
    if np.any(degree[~fit]) or np.any(mass[~fit]):
        raise RuntimeError("train-only graph assigned held-out topology mass")
    write(OUT / "ROW_MANIFEST.json", {
        "sequence_manifest_sha256": sha("/sequences/sequences.json"),
        "vectors": [{"row_index": i, "sequence_sha256": h} for i, h in enumerate(meta["sha256"])],
        "parent_manifest_sha256": sha("/raw/EMBEDDING_MANIFEST.json"),
    })
    files = [record(OUT / p, OUT) for p in
             ("raw_pooled.npy", "standardized_train2.npy", "train2_normalization.npz",
              "kmer.npz", "aac_unit.npy", "adjacency.npz", "graph.npz", "ROW_MANIFEST.json")]
    write(OUT / "FEATURES.json", {
        "at_utc": now(), "files": files, "input_freeze_sha256": sha(ROOT / "INPUT_FREEZE.json"),
        "protocol_sha256": sha(ROOT / "PROTOCOL.json"),
        "sequence_manifest_sha256": sha("/sequences/sequences.json"),
        "identity_join": "Explicit original embedding manifest sequence_sha256 -> row_index; new vectors in declared frozen sequence order.",
        "raw_fixture_max_error": fixture_error, "extended_standardized_replay_max_error": reproduction_error,
        "training_normalizer_endpoints": int(fit.sum()), "training_exposed_endpoints": len(exposed),
        "heldout_degree_and_component_mass_zero": True, "windowed_extraction": details,
        "evaluation_pairs_or_truth_mounted": False,
        "code": [record(Path("/code") / name) for name in ("sequence_features.py", "control_io.py", "control_math.py")],
    })
    print({"features_complete": True, "raw_fixture_error": fixture_error,
           "identity_replay_error": reproduction_error, "training_exposed": len(exposed)}, flush=True)


if __name__ == "__main__":
    main()
