"""Preserve UCX-prefixed probe stdout and expose its unchanged JSON attestation.

Logging-only adapter, added after scorer freeze. It cannot change the frozen
scorer, predictions, guard, decision or evaluation. The original final-test
qualification documents the same UCX startup message with /proc hidden.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone


def parse(payload):
    lines = payload.decode().splitlines()
    records = [line for line in lines if line.startswith("{")]
    noise = [line for line in lines if line and not line.startswith("{")]
    pattern = r"\[\d+\.\d+\] \[[^\]\s]+\]\s+sys\.c:\d+\s+UCX\s+ERROR failed to get boot id"
    if len(records) != 1 or any(re.fullmatch(pattern, line) is None for line in noise):
        raise RuntimeError("Unexpected guard stdout; refuse normalization")
    attestation = json.loads(records[0])
    for key in ("child_inherits_filter", "cpu_only", "network_syscall_filter_enforced", "no_inherited_descriptors_above_stderr", "proc_sys_hidden"):
        if attestation.get(key) is not True:
            raise RuntimeError("Guard did not affirm its qualification")
    return (records[0] + "\n").encode(), len(noise)


def normalize(private, validation):
    source = private / "preflight/GUARD.json"
    raw = private / "preflight/GUARD.stdout.log"
    report_path = validation / "GUARD_LOG_NORMALIZATION.json"
    payload = source.read_bytes()
    canonical, warnings = parse(payload)
    if raw.exists() or report_path.exists():
        raise RuntimeError("Refuse raw-log or normalization-record overwrite")
    source.rename(raw)
    with source.open("xb") as stream:
        stream.write(canonical)
        stream.flush()
        os.fsync(stream.fileno())
    report = {"at_utc": datetime.now(timezone.utc).isoformat(), "logging_only": True,
        "raw_stdout_preserved": True, "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "attestation_sha256": hashlib.sha256(canonical).hexdigest(), "recognized_UCX_startup_lines": warnings,
        "attestation_values_changed": False, "scorer_guard_or_protocol_changed": False,
        "introduced_after_scorer_freeze_before_truth_access": True,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "note": "The same UCX startup text was documented in protected_final_test_v1/PREACCESS_QUALIFICATION.json. Raw stdout is retained; only its one JSON line is exposed to the closure reader."}
    with report_path.open("x") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"guard_attestation_normalized": True, "raw_stdout_preserved": True, "values_changed": False}))


if __name__ == "__main__":
    normalize(Path(sys.argv[1]), Path(sys.argv[2]))
