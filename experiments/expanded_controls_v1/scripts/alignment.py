"""Frozen all-sequence homology search and symmetric kernel construction."""
from pathlib import Path
import subprocess
import numpy as np
from control_io import ROOT, OUT, now, read, record, save_array, sha, write
from ipin_openppi.homology_source.semantics import alignment_scores, alignment_values


def main():
    cfg = read(ROOT / "PROTOCOL.json")["alignment"]
    if Path("/truth").exists() or (OUT / "ALIGNMENT.json").exists():
        raise RuntimeError("truth visibility or existing alignment freeze")
    meta = read("/sequences/sequences.json")
    n = len(meta["sha256"])
    binary = "/mmseqs/mmseqs"
    if sha(binary) != cfg["sha256"]:
        raise RuntimeError("alignment binary changed")
    version = subprocess.check_output([binary, "version"], text=True).strip()
    if version != cfg["version"]:
        raise RuntimeError("alignment version changed")
    work = Path("/work/alignment")
    work.mkdir()
    fasta = work / "sequences.fasta"
    with fasta.open("x") as f:
        for i, seq in enumerate(meta["sequence"]):
            f.write(f">{i}\n{seq}\n")
    db, result, tmp, tsv = (str(work / x) for x in ("db", "result", "tmp", "alignments.tsv"))
    commands = [
        [binary, "createdb", str(fasta), db, "--shuffle", "0", "--createdb-mode", "0"],
        [binary, "search", db, db, result, tmp, "--threads", str(cfg["threads"]), *cfg["parameters"]],
        [binary, "convertalis", db, db, result, tsv, "--format-output", cfg["fields"],
         "--threads", str(cfg["threads"])],
    ]
    for i, command in enumerate(commands):
        print({"alignment_stage": command[1]}, flush=True)
        with (work / f"command_{i}.log").open("x") as f:
            subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, check=True)
    local, coverage = np.zeros((n, n), np.float64), np.zeros((n, n), np.float64)
    rows, qualified, self_seen, purge = 0, 0, set(), set()
    with Path(tsv).open() as f:
        for line in f:
            values = alignment_values(line.rstrip().split("\t"), meta["length"])
            a, b, loc, cov, is_purge = alignment_scores(values)
            rows += 1
            if a == b:
                self_seen.add(a)
            if loc > 0:
                qualified += 1
                local[a, b] = local[b, a] = max(local[a, b], loc)
                coverage[a, b] = coverage[b, a] = max(coverage[a, b], cov)
            if is_purge and a != b:
                purge.add((min(a, b), max(a, b)))
    # Short proteins can fail the declared min-span filter, including self hits.
    eligible_self = sum(length >= 40 for length in meta["length"])
    missing_long = [i for i, length in enumerate(meta["length"]) if length >= 40 and i not in self_seen]
    if missing_long:
        raise RuntimeError("long sequence missing self alignment")
    save_array(OUT / "similarity_local.npy", local)
    save_array(OUT / "similarity_coverage.npy", coverage)
    cross_train = sum((meta["partition"][a] == "train") != (meta["partition"][b] == "train")
                      for a, b in purge)
    write(OUT / "ALIGNMENT.json", {
        "at_utc": now(), "version": version, "sequence_manifest_sha256": sha("/sequences/sequences.json"),
        "protocol_sha256": sha(ROOT / "PROTOCOL.json"), "sequences": n,
        "reported_alignments": rows, "qualified_alignments": qualified,
        "self_alignments": len(self_seen), "eligible_self_min40": eligible_self,
        "detected_purge_rule_edges": len(purge), "train_to_heldout_purge_rule_edges": cross_train,
        "commands": commands, "search_artifacts": [record(Path(tsv)), record(fasta)],
        "files": [record(OUT / name, OUT) for name in ("similarity_local.npy", "similarity_coverage.npy")],
        "evaluation_pairs_or_truth_mounted": False,
        "code": [record(Path("/code") / name) for name in ("alignment.py", "control_io.py")],
    })
    print({"alignment_complete": True, "alignments": rows, "qualified": qualified}, flush=True)


if __name__ == "__main__":
    main()
