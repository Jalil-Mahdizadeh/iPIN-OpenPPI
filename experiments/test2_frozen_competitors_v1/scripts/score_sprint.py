"""Standard-library-only native SPRINT; frozen graph, expanded sequence features."""
from pathlib import Path
import json
import sys
import time
sys.path.insert(0, "/bundle/code")
from native import canonical, run, sha, write
from policy import HSP_ARGS, PREDICT_ARGS


def read(path):
    return json.loads(Path(path).read_text())


def main():
    started = time.monotonic()
    out = Path("/output")
    config = read("/bundle/SCORER_FREEZE.json")
    for item in config["files"]:
        assert sha(Path("/bundle") / item["path"]) == item["sha256"]
    inputs = read(out / "INPUTS.json")
    assert inputs["bundle_sha256"] == sha("/bundle/SCORER_FREEZE.json")
    assert inputs["sequence_sha256"] == sha("/data/sequences.json")
    for item in inputs["files"]:
        assert sha(out / item["path"]) == item["sha256"]
    if (out / "COMPLETE.json").exists():
        assert read(out / "COMPLETE.json")["scores_sha256"] == sha(out / "scores.txt")
        return
    if not (out / "HSP_COMPLETE.json").exists():
        print({"phase": "native_hsp", "proteins": 17583, "threads": 64}, flush=True)
        elapsed = run("native-hsp", ["/opt/sprint/bin/compute_HSPs", "-p", str(out / "proteins.fasta"),
                      "-h", str(out / "raw.hsp"), *HSP_ARGS], threads=64)
        census = canonical(out / "raw.hsp", out / "canonical.hsp", out / "proteins.fasta")
        assert census["proteins_with_full_self_hsp"] == 17583
        write(out / "HSP_COMPLETE.json", {"elapsed_seconds": elapsed, "input_sha256": sha(out / "INPUTS.json"), **census})
    hsp = read(out / "HSP_COMPLETE.json")
    assert hsp["input_sha256"] == sha(out / "INPUTS.json")
    assert sha(out / "canonical.hsp") == hsp["canonical_sha256"]
    print({"phase": "native_serial_predict", "rows": sum(x["rows"] for x in inputs["parts"])}, flush=True)
    elapsed = run("native-predict", ["/opt/sprint/bin/predict_interactions", "-p", str(out / "proteins.fasta"),
                  "-h", str(out / "canonical.hsp"), "-tr", str(out / "train_positive.txt"),
                  "-pos", str(out / "pairs.txt"), "-neg", str(out / "empty.txt"),
                  "-o", str(out / "scores.txt"), *PREDICT_ARGS], threads=1)
    write(out / "COMPLETE.json", {"input_sha256": sha(out / "INPUTS.json"), "scores_sha256": sha(out / "scores.txt"),
        "prediction_seconds": elapsed, "elapsed_seconds": time.monotonic() - started,
        "unchanged_native_algorithm": True, "unchanged_training_graph_positive_pairs": 16799,
        "sequence_only_transductive_corpus_size": 17583, "legacy_scores_recomputed": True,
        "test_truth_read": False, "new_training_or_selection": False, "code_sha256": sha(__file__)})


if __name__ == "__main__":
    main()
