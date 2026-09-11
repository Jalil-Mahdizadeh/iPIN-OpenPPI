"""Close this follow-up without decryption, scoring, fitting or new truth access."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model_optimization_followup_core_v1 as core
import publish_model_optimization_followup_v1 as publisher
from prepare_model_optimization_followup_v1 import historical_check, SOURCES


def audit(project):
    private = project / ".private" / core.EXECUTION
    bundle = private / "bundle"
    validation = project / "artifacts/validation" / core.EXECUTION
    results = project / "artifacts/results" / core.EXECUTION
    custody = project / ".private" / core.PACKAGE / "followup_evaluations" / core.EXECUTION
    frozen = core.verify_bundle(bundle)
    core.verify_records(project, frozen["source_inputs"])
    core.verify_records(project, frozen["input_records"])
    historical = historical_check(project)
    result_path = results / "FOLLOWUP_TEST_RESULTS.json"
    result = core.read(result_path)
    publisher.validate(result)
    receipt_path = project / "artifacts/validation/protected_evaluation_receipts" / f"{core.EXECUTION}.json"
    receipt, completion, ledger = [core.read(p) for p in (receipt_path, custody / "completion.json", custody / "ledger.json")]
    prediction = core.read(private / "freeze/PREDICTION_FREEZE.json")
    if (result["ledger_sha256"] != core.sha(custody / "ledger.json")
            or completion["ledger_sha256"] != result["ledger_sha256"]
            or receipt["ledger_sha256"] != result["ledger_sha256"]
            or completion["receipt_sha256"] != core.sha(receipt_path)
            or completion["results_sha256"] != core.sha(result_path)
            or receipt["results_sha256"] != core.sha(result_path)
            or core.sha(private / "evaluation/FOLLOWUP_TEST_RESULTS.json") != core.sha(result_path)
            or result["scorer_freeze_sha256"] != core.sha(bundle / "SCORER_FREEZE.json")
            or core.sha(validation / "SCORER_FREEZE.json") != result["scorer_freeze_sha256"]
            or result["prediction_freeze_sha256"] != core.sha(private / "freeze/PREDICTION_FREEZE.json")
            or result["acceptance_sha256"] != core.sha(validation / "ENSEMBLE_ACCEPTANCE.json")):
        raise RuntimeError("Follow-up publication/custody lineage mismatch")
    for path in (result_path, receipt_path):
        if path.with_suffix(".json.sha256").read_text().split() != [core.sha(path), path.name]:
            raise RuntimeError("Published checksum sidecar drift")
    core.verify_records(private / "predictions", prediction["files"])
    for part, digest in prediction["prediction_manifest_sha256"].items():
        if core.sha(private / "predictions" / part / "PREDICTIONS.json") != digest:
            raise RuntimeError("Prediction manifest drift after evaluation")
    session = core.read(private / "session/SCORING_SESSION.json")
    candidate = core.read(private / "predictions/candidate/PREDICTIONS.json")
    baseline = core.read(private / "predictions/baseline/PREDICTIONS.json")
    attempt = core.read(private / "evaluation/EVALUATION_ATTEMPT.json")
    timeline = {
        "scorer_frozen": frozen["frozen_at_utc"], "candidate_session": session["created_at_utc"],
        "candidate_predictions_completed": candidate["generated_at_utc"],
        "baseline_import_completed": baseline["imported_at_utc"],
        "predictions_frozen": prediction["validated_at_utc"], "followup_reserved": ledger["reserved_at_utc"],
        "evaluation_entered": attempt["entered_at_utc"], "results_generated": result["generated_at_utc"],
        "aggregate_published": receipt["published_at_utc"]}
    moments = [datetime.fromisoformat(x) for x in timeline.values()]
    if moments != sorted(moments) or any(a >= b for a, b in zip(moments, moments[1:])):
        raise RuntimeError("Freeze/access/ledger timing order violated")
    originals = core.read(project / ".private/protected_final_test_v1/freeze/PREDICTION_FREEZE.json")
    original_files = {(r["cell_id"], r["scorer_id"]): r for r in originals["files"]}
    for rec in baseline["files"]:
        old_name = core.ORIGINAL_SCORERS[core.BASELINE_SCORERS.index(rec["scorer_id"])]
        old = original_files[(rec["cell_id"], old_name)]
        if (rec["sha256"], rec["bytes"]) != (old["sha256"], old["bytes"]):
            raise RuntimeError("Imported baseline not byte-identical to original")
        core.verify_records(project / ".private/protected_final_test_v1/predictions", [old])
    array_manifest = core.read(private / "evaluation/PRIVATE_BOOTSTRAP_MANIFEST.json")
    core.verify_records(private / "evaluation", array_manifest["files"])
    if array_manifest["scorers"] != list(core.SCORERS) or len(array_manifest["files"]) != 9:
        raise RuntimeError("Stored bootstrap census mismatch")
    for index, cell in enumerate(core.CELLS):
        with np.load(private / f"evaluation/bootstrap-cell-{index:02d}.npz", allow_pickle=False) as values:
            if values["points"].shape != (8,) or values["draws"].shape != (8, 2000):
                raise RuntimeError("Stored bootstrap dimensions mismatch")
            replay = core.summarize(values["points"], values["draws"])
        if any(replay[key] != result["cells"][cell][key] for key in replay):
            raise RuntimeError("Published summary differs from stored bootstrap arithmetic")
    if list((private / "session").glob("candidate-decrypt-*")) or list((private / "evaluation").glob("truth-decrypt-*")):
        raise RuntimeError("Temporary decryption workspace remains")
    guard = core.read(private / "preflight/GUARD.json")
    qualification = core.read(private / "preflight/SCORER_QUALIFICATION.json")
    if (not guard["network_syscall_filter_enforced"] or not guard["child_inherits_filter"]
            or not guard["proc_sys_hidden"] or not qualification["passed"]):
        raise RuntimeError("Restricted pre-access qualification incomplete")
    for name, payload in (("PROTECTED_GUARD.json", guard), ("PROTECTED_SCORER_QUALIFICATION.json", qualification)):
        core.write_new(validation / name, payload)
    tests = []
    for name in ("test_protected_final_test_v1.py", "test_model_optimization_followup_v1.py", "test_model_optimization_followup_publication_v1.py"):
        path = private / "preflight" / f"{name}.stderr.log"
        output = path.read_text()
        if not output.rstrip().endswith("OK"):
            raise RuntimeError("Protected synthetic test did not pass")
        tests.append({"test": name, "passed": True, "console": output, "log_sha256": core.sha(path)})
    core.write_new(validation / "PROTECTED_SYNTHETIC_TESTS.json", {"passed": True, "suites": tests})
    gates = yaml.safe_load((project / "governance/gates/gate_status_v53.yaml").read_text())
    for cell in ("C3_test", "C2_test", "C1_test"):
        if gates["followup_test"]["overall_cells"][cell] != {
            "baseline_concordance": result["cells"][cell]["metrics"][core.BASELINE]["ht_P_vs_U_concordance"],
            "candidate_concordance": result["cells"][cell]["metrics"][core.MODEL]["ht_P_vs_U_concordance"],
            **result["cells"][cell]["ensemble_minus_baseline"]}:
            raise RuntimeError("Current gate values differ from published result")
    links = 0
    report_paths = ("README.md", "docs/reports/README.md", "docs/reports/m1/M1_Model_Optimization_Followup_v1.md",
                    "docs/protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md", "governance/PROJECT_STATUS_v53.md")
    for relative in report_paths:
        path = project / relative
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" not in target and not target.startswith("#"):
                if not (path.parent / target.split("#")[0]).resolve().exists():
                    raise RuntimeError(f"Unresolved local document link in {relative}")
                links += 1
    audit_record = {"execution_id": core.EXECUTION, "passed": True, "at_utc": core.now(),
        "historical_integrity": historical, "scorer_source_and_input_records_verified": True,
        "prediction_files_verified": len(prediction["files"]), "baseline_files_byte_identical": len(baseline["files"]),
        "stored_bootstrap_groups_rechecked": 9, "stored_bootstrap_scorers_per_group": 8,
        "stored_bootstrap_replicates": 2000, "publication_byte_identical": True,
        "all_draws_finite": all(x["finite_bootstrap_draws"] == 2000 for c in result["cells"].values() for x in c["metrics"].values()),
        "original_baseline_replay_max_abs": max(c["original_baseline_replay_max_abs"] for c in result["cells"].values()),
        "timeline": timeline, "freeze_before_candidate_access_and_truth_reservation": True,
        "temporary_candidate_and_truth_plaintext_absent": True, "local_document_links_resolved": links,
        "new_decryption_scoring_fitting_or_protected_row_inspection": False,
        "same_author_not_independent_replication": True, "validator_sha256": core.sha(Path(__file__))}
    core.write_new(validation / "COMPLETED_AUDIT.json", audit_record)
    paths = [project / p for p in SOURCES]
    paths += [project / p for p in ("docs/reports/m1/M1_Model_Optimization_Followup_v1.md",
        "governance/PROJECT_STATUS_v53.md", "governance/gates/gate_status_v53.yaml")]
    paths += list(validation.glob("*.json")) + [result_path, result_path.with_suffix(".json.sha256"), receipt_path, receipt_path.with_suffix(".json.sha256")]
    records = [core.record(p, project) for p in sorted(set(paths))]
    core.write_new(results / "ARTIFACT_REGISTRY.json", {"execution_id": core.EXECUTION,
        "status": "complete_frozen", "created_at_utc": core.now(), "artifacts": records,
        "historical_registered_files_unchanged": 179, "original_gate_and_test_records_unchanged": True,
        "protected_pair_identity_or_row_scores_public": False, "one_followup_attempt_consumed": True,
        "new_fit_or_test_tuning": False, "same_author_not_independent_replication": True})
    print(json.dumps({"completed_audit": "pass", "registered_files": len(records),
        "historical_files_unchanged": 179, "prediction_files_verified": len(prediction["files"]),
        "baseline_replay_max_abs": audit_record["original_baseline_replay_max_abs"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    audit(parser.parse_args().project.resolve(strict=True))
