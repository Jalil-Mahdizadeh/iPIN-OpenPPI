"""Host-side execution registration after all pre-execution qualifications."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def record(path, base):
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return {"path": str(p.relative_to(base)), "bytes": p.stat().st_size, "sha256": h.hexdigest()}


def main():
    target = ROOT/"IMPLEMENTATION_FREEZE.json"
    if target.exists():
        raise RuntimeError("implementation already frozen")
    for file in ("INPUT_FREEZE.json", "features/FEATURES.json", "features/ALIGNMENT.json",
                 "validation/QUALIFICATION_FINAL.json"):
        if not (ROOT/file).exists():
            raise RuntimeError(f"required pre-execution evidence missing: {file}")
    initial = json.loads((ROOT/"INPUT_FREEZE.json").read_text())["protocol_sha256"]
    correction = json.loads((ROOT/"PRE_EXECUTION_CLARIFICATION.json").read_text())
    protocol = record(ROOT/"PROTOCOL.json", ROOT)
    if correction["initial_protocol_sha256"] != initial or correction["clarified_protocol_sha256"] != protocol["sha256"]:
        raise RuntimeError("protocol clarification lineage mismatch")
    library = REPO/"src"
    files = [
        "ipin_openppi/__init__.py",
        "ipin_openppi/stage1/__init__.py", "ipin_openppi/stage1/baselines.py",
        "ipin_openppi/stage1/constants.py", "ipin_openppi/stage1/embeddings.py",
        "ipin_openppi/stage1/models.py", "ipin_openppi/stage1/support.py",
        "ipin_openppi/partner_specificity/__init__.py",
        "ipin_openppi/partner_specificity/models.py", "ipin_openppi/partner_specificity/semantics.py",
        "ipin_openppi/homology_source/__init__.py", "ipin_openppi/homology_source/semantics.py",
    ]
    native = REPO/"benchmark/tuna/scripts"
    upstream = REPO/"benchmark/tuna/upstream/TUnA"
    code = sorted((ROOT/"scripts").glob("*.py")) + sorted((ROOT/"tests").glob("*.py")) + [ROOT/"run.sh"]
    value = {
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": protocol["sha256"],
        "input_freeze_sha256": record(ROOT/"INPUT_FREEZE.json", ROOT)["sha256"],
        "pre_execution_clarification": record(ROOT/"PRE_EXECUTION_CLARIFICATION.json", ROOT),
        "qualification": record(ROOT/"validation/QUALIFICATION_FINAL.json", ROOT),
        "preprocessing": [record(ROOT/p, ROOT) for p in ("features/FEATURES.json", "features/ALIGNMENT.json")],
        "code": [record(p, ROOT) for p in code],
        "libraries": [record(library/p, library) for p in files],
        "native": [record(p, native) for p in sorted(native.glob("*.py"))],
        "upstream": [record(p, upstream) for p in sorted((upstream/"results/bernett/TUnA").rglob("*.py"))],
        "metric_reference": record(REPO/"experiments/human_ppi_data_scaling_v1/scripts/macro_metrics.py", REPO),
        "control_fitting_started": False, "candidate_scoring_started": False,
        "test_truth_deserialized": False,
    }
    with target.open("x") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Implementation frozen after independent qualifications.")


if __name__ == "__main__":
    main()
