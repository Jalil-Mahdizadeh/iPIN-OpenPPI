"""Verify all original source inputs after completion; write only in this experiment."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    out = Path(__file__).resolve().parents[1]
    repo = out.parents[1]
    frozen = json.loads((out / "INPUT_FREEZE.json").read_text())
    assert (out / "results/COMPLETE.json").exists()
    for item in frozen["files"]:
        path = repo / item["path"]
        assert path.stat().st_size == item["bytes"] and sha(path) == item["sha256"], str(path)
    with (out / "PRESERVATION.json").open("x") as stream:
        json.dump({"at_utc": datetime.now(timezone.utc).isoformat(), "passed": True,
            "original_inputs_verified_unchanged": len(frozen["files"]),
            "all_new_artifacts_confined_to": str(out.relative_to(repo)),
            "results_sha256": sha(out / "results/RESULTS.json"),
            "input_freeze_sha256": sha(out / "INPUT_FREEZE.json")}, stream, indent=2)
    print("All frozen source inputs preserved", flush=True)


if __name__ == "__main__":
    main()
