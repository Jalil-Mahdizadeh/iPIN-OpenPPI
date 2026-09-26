"""Verify all frozen inputs remained unchanged; inventory outputs without mutation."""
from pathlib import Path
import subprocess
from panel_io import now, read, sha, write_json


def main():
    out = Path(__file__).resolve().parents[1]
    root = out.parents[1]
    freeze = read(out / "INPUT_FREEZE.json")
    for record in freeze["inputs"]:
        path = root / record["path"]
        assert path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], path
    current = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=no"], cwd=root, text=True)
    assert current == freeze["tracked_status_before"], "Tracked working-tree status changed"
    for name in ("SCORING_RUN.json", "VALIDATION.json", "REPORT.md", "comparison.png", "comparison.pdf", "all_twelve_targets_scores.csv"):
        assert (out / "output" / name).is_file()
    assert read(out / "output/VALIDATION.json")["passed"]
    files = [{"path": str(p.relative_to(out)), "bytes": p.stat().st_size, "sha256": sha(p)}
             for p in sorted(out.rglob("*")) if p.is_file() and ".cache" not in p.parts]
    write_json(out / "PRESERVATION.json", {"at_utc": now(), "passed": True,
        "all_frozen_inputs_unchanged": True, "inputs_verified": len(freeze["inputs"]),
        "tracked_working_tree_status_unchanged": True, "files": files})
    print(f"All {len(freeze['inputs'])} frozen inputs unchanged; output inventory complete", flush=True)


if __name__ == "__main__":
    main()
