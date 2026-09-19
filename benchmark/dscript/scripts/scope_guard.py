#!/usr/bin/env python3
"""Audit this build without changing the earlier TUnA scope audit."""
import argparse
import importlib.util
import json
from pathlib import Path

CANDIDATE = Path(__file__).resolve().parents[1]
BENCHMARK = CANDIDATE.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["record", "verify"])
    parser.add_argument("--snapshot", type=Path, help="Per-run snapshot inside benchmark/dscript/")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("benchmark_scope", BENCHMARK / "workspace_guard.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    current = guard.snapshot()
    before = (args.snapshot or CANDIDATE / "provenance/repository-before-sif.json").resolve()
    if CANDIDATE not in before.parents:
        raise ValueError("Scope-audit outputs must remain inside benchmark/dscript/")
    before.parent.mkdir(parents=True, exist_ok=True)
    if args.mode == "record":
        with before.open("x") as handle:
            json.dump(current, handle, indent=2, sort_keys=True)
        print(json.dumps({"outside_benchmark_files_recorded": len(current)}))
        return
    previous = json.loads(before.read_text())
    report = {
        "files_checked": len(previous),
        "coverage": "Git-tracked and non-ignored untracked files outside benchmark/",
        "added": sorted(current.keys() - previous.keys()),
        "removed": sorted(previous.keys() - current.keys()),
        "changed": sorted(k for k in current.keys() & previous.keys() if current[k] != previous[k]),
    }
    report["passed"] = not any(report[k] for k in ("added", "removed", "changed"))
    audit = before.parent / ("scope-audit.json" if args.snapshot else "repository-sif-audit.json")
    audit.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
