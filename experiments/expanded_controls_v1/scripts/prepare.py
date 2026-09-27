"""Validate frozen parents and emit separate training/candidate-only inputs."""
from pathlib import Path
import hashlib
import numpy as np
from control_io import CELLS, COHORTS, arrays, check_pairs, now, read, record, save, sha, verify, write

REPO = Path("/repo")
STUDY = REPO / "experiments/human_ppi_data_scaling_v1"
OUT = Path("/output")


def main():
    if (OUT / "INPUT_FREEZE.json").exists():
        raise RuntimeError("preparation already complete")
    protocol = read(OUT / "PROTOCOL.json")
    inputs = {}

    def keep(path, expected=None):
        path = Path(path)
        item = record(path, REPO)
        if expected is not None:
            if item["sha256"] != expected["sha256"]:
                raise RuntimeError(f"parent hash mismatch: {path}")
            if "bytes" in expected and item["bytes"] != expected["bytes"]:
                raise RuntimeError(f"parent size mismatch: {path}")
        inputs[item["path"]] = item
        return item

    for name in ("CORPUS_FREEZE.json", "CANDIDATE_FREEZE.json", "CORPUS_VALIDATION.json",
                 "EXECUTION_FREEZE.json", "SCORER_REPLAY_REVIEW.json"):
        keep(STUDY / "audit" / name)
    execution = read(STUDY / "audit/EXECUTION_FREEZE.json")
    expected_data = {x["name"]: x for x in execution["data_files"]}

    def data(name):
        path = STUDY / "data" / name
        keep(path, expected_data[name])
        return path

    meta_path = data("sequences.json")
    meta = read(meta_path)
    n = len(meta["sha256"])
    if n != 17583 or len(set(meta["sha256"])) != n:
        raise RuntimeError("endpoint universe drift")
    if not all(len(v) == n for v in meta.values()):
        raise RuntimeError("endpoint metadata length mismatch")
    for h, seq, length in zip(meta["sha256"], meta["sequence"], meta["length"], strict=True):
        if hashlib.sha256(seq.encode("ascii")).hexdigest() != h or len(seq) != length:
            raise RuntimeError("sequence identity or length mismatch")
    partition = np.asarray(meta["partition"])
    component = np.asarray(meta["extended_component"])
    groups = {}
    for c, part in zip(component, partition, strict=True):
        groups.setdefault(c, set()).add(part)
    if any(len(v) != 1 for v in groups.values()):
        raise RuntimeError("extended component crosses a partition")
    p = arrays(data("training_31188.npz"))
    u = arrays(data("training_unlabeled.npz"))
    pkeys = check_pairs(p["p_a"], p["p_b"], n)
    ukeys = check_pairs(u["u_a"], u["u_b"], n)
    if len(pkeys) != 31188 or len(ukeys) != 2000000 or np.intersect1d(pkeys, ukeys).size:
        raise RuntimeError("training P/U census or disjointness failure")
    for values, prefix in ((p, "p"), (u, "u")):
        if not np.all((partition[values[prefix+"_a"]] == "train") &
                      (partition[values[prefix+"_b"]] == "train")):
            raise RuntimeError("training endpoint outside train partition")
    if not np.isfinite(u["u_weight"]).all() or np.any(u["u_weight"] <= 0):
        raise RuntimeError("invalid training design weights")
    # Canonical unordered-pair order, frozen before the fixed fitting permutations.
    po, uo = np.argsort(pkeys, kind="stable"), np.argsort(ukeys, kind="stable")
    save(OUT / "data/train/positive.npz",
         p_a=np.minimum(p["p_a"], p["p_b"])[po], p_b=np.maximum(p["p_a"], p["p_b"])[po])
    save(OUT / "data/train/unlabeled.npz",
         u_a=np.minimum(u["u_a"], u["u_b"])[uo], u_b=np.maximum(u["u_a"], u["u_b"])[uo],
         u_weight=u["u_weight"][uo])
    (OUT / "data").mkdir(exist_ok=True)
    with (OUT / "data/sequences.json").open("xb") as stream:
        stream.write(meta_path.read_bytes())
    candidates = read(STUDY / "audit/CANDIDATE_FREEZE.json")
    candidate_expected = {x["name"]: x for x in candidates["files"]}
    files, census = [], {}
    for fold in ("development", "test"):
        for cell in CELLS:
            for cohort in COHORTS:
                name = f"{fold}_{cohort}_{cell}"
                if fold == "test":
                    source = STUDY / "private/candidates" / f"{cohort}_{cell}.npz"
                    keep(source, candidate_expected[source.name])
                else:
                    source = data(f"development/{'reconciled' if cohort == 'legacy' else 'added'}/{cell}.npz")
                rows = arrays(source)
                if fold == "test" and set(rows) != {"a", "b"}:
                    raise RuntimeError("test candidate input contains forbidden columns")
                a, b = rows["a"], rows["b"]
                keys = check_pairs(a, b, n)
                if np.intersect1d(keys, pkeys, assume_unique=True).size or np.intersect1d(keys, ukeys, assume_unique=True).size:
                    raise RuntimeError("held-out candidate entered training")
                pa, pb = partition[a], partition[b]
                expected = ((pa == "train") & (pb == "train") if cell == "C1" else
                            ((pa == "train") & (pb == fold)) | ((pb == "train") & (pa == fold)) if cell == "C2" else
                            (pa == fold) & (pb == fold))
                if not expected.all():
                    raise RuntimeError(f"partition exposure violation: {name}")
                target = OUT / "data/candidates" / (name + ".npz")
                save(target, a=a, b=b)
                files.append(record(target, OUT))
                census[name] = {"rows": len(a), "endpoints": len(np.unique(np.r_[a, b])),
                                "candidate_identity_sha256": hashlib.sha256(keys.tobytes()).hexdigest()}
    # Test-truth files are checked only as opaque bytes; no labels are deserialized.
    corpus = read(STUDY / "audit/CORPUS_FREEZE.json")
    for item in corpus["test_files"]:
        if "/reconciled/" in item["path"] or "/added/" in item["path"]:
            keep(STUDY / item["path"], item)
    raw_dir = REPO / "artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/esm2_150m"
    emb = read(raw_dir / "EMBEDDING_MANIFEST.json")
    keep(raw_dir / "EMBEDDING_MANIFEST.json")
    keep(REPO / emb["matrix_path"], {"sha256": emb["matrix_sha256"], "bytes": emb["matrix_bytes"]})
    keep(REPO / emb["normalization"]["normalizer_path"], {"sha256": emb["normalization"]["normalizer_sha256"]})
    pooled = read(STUDY / "runs/POOLED_FEATURE_MANIFEST.json")
    keep(STUDY / "runs/POOLED_FEATURE_MANIFEST.json")
    keep(STUDY / "runs/pooled_features.npy", pooled["features"])
    for name in ("SCORER_FREEZE.json", "SELECTION.json"):
        keep(STUDY / "runs" / name)
    selected = read(STUDY / "runs/SELECTION.json")["selected"]
    if selected["budget"] != 31188 or selected["epoch"] != 1:
        raise RuntimeError("reference model selection drift")
    for item in read(STUDY / "runs/SCORER_FREEZE.json")["members"]:
        if item["name"].startswith("scaled_31188_"):
            for k in ("features", "weights"):
                keep(STUDY / "runs" / item[k]["path"], item[k])
    old_test = REPO / "experiments/test2_frozen_competitors_v1/results"
    for name in ("RESULTS.json", "PREDICTION_FREEZE.json"):
        keep(old_test / name)
    for item in read(old_test / "PREDICTION_FREEZE.json")["files"]:
        keep(old_test / item["path"], item)
    for cell in CELLS:
        keep(old_test / f"bootstrap_{cell}_test_2_macro.npz")
    keep(old_test / "bootstrap_C1_test_2_macro_no_dev_overlap.npz")
    keep(REPO / protocol["alignment"]["binary"], {"sha256": protocol["alignment"]["sha256"]})
    for name in ("ipin-data-arm64_0.1.2.sif",):
        keep(REPO / "containers/images" / name)
    keep(REPO / "benchmark/containers/images/tuna-arm64-v1.sif", execution["container"])
    for path in (OUT / "data/train").glob("*.npz"):
        files.append(record(path, OUT))
    files.append(record(OUT / "data/sequences.json", OUT))
    write(OUT / "INPUT_FREEZE.json", {
        "at_utc": now(), "protocol_sha256": sha(OUT / "PROTOCOL.json"),
        "parents": list(inputs.values()), "files": files, "candidates": census,
        "endpoints": n, "training_P": len(pkeys), "training_U": len(ukeys),
        "training_exposed_endpoints": int(len(np.unique(np.r_[p["p_a"], p["p_b"]]))),
        "training_candidate_overlap": 0, "training_P_U_overlap": 0,
        "component_partition_overlap": 0, "test_truth_deserialized": False,
        "preparation_code": record(Path("/code/prepare.py")),
    })
    print({"prepared": True, "candidates": census, "parent_files": len(inputs)}, flush=True)


if __name__ == "__main__":
    main()
