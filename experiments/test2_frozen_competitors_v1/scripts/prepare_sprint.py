"""Construct unlabeled SPRINT routing inputs in the numerical data runtime."""
from pathlib import Path
import shutil
from study_io import CELLS, arrays, read, record, sha, write

out = Path("/output")
meta = read("/data/sequences.json")
assert read("/bundle/endpoints.json") == meta["sha256"][:17000]
assert not (out / "INPUTS.json").exists()
with (out / "proteins.fasta").open("x") as stream:
    for i, seq in enumerate(meta["sequence"]):
        stream.write(f">p{i:05d}\n{seq}\n")
shutil.copyfile("/bundle/train_positive.txt", out / "train_positive.txt")
assert sha(out / "train_positive.txt") == sha("/bundle/train_positive.txt")
assert len((out / "train_positive.txt").read_text().splitlines()) == 16799
(out / "empty.txt").touch(exist_ok=False)
parts = []
with (out / "pairs.txt").open("x") as stream:
    for cell in CELLS:
        for cohort in ("legacy", "added"):
            path = Path(f"/data/candidates/{cohort}_{cell}.npz")
            data = arrays(path)
            for a, b in zip(data["a"], data["b"], strict=True):
                stream.write(f"p{a:05d} p{b:05d}\n")
            parts.append({"cell": cell, "cohort": cohort, "rows": len(data["a"]), "candidate_sha256": sha(path)})
write(out / "INPUTS.json", {"sequence_sha256": sha("/data/sequences.json"),
    "bundle_sha256": sha("/bundle/SCORER_FREEZE.json"), "parts": parts, "sequences": len(meta["sequence"]),
    "test_truth_read": False, "routing_marker_is_not_ground_truth": True,
    "files": [record(out / name, out) for name in ("proteins.fasta", "train_positive.txt", "pairs.txt", "empty.txt")]})
print({"sprint_inputs_prepared": True, "candidate_rows": sum(x["rows"] for x in parts)}, flush=True)
