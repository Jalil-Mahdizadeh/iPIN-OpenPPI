"""Close the public final-test record; no scoring, decryption or row access."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import yaml


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main(root):
    result_root = root / "artifacts/results/protected_final_test_v1"
    validation = root / "artifacts/validation/protected_final_test_v1"
    result_path = result_root / "FINAL_TEST_RESULTS.json"
    result = read(result_path)
    receipt_path = root / "artifacts/validation/protected_evaluation_receipts/protected_final_test_v1.json"
    receipt = read(receipt_path)
    custody = root / ".private/pair_level_pu_r_benchmark_artifacts_v1"
    ledger, completion = custody / "protected_evaluation_ledger.json", custody / "protected_evaluation_completion.json"
    complete = read(completion)
    assert complete["status"] == "completed"
    assert complete["ledger_sha256"] == sha(ledger) == receipt["ledger_sha256"] == result["ledger_sha256"]
    assert complete["receipt_sha256"] == sha(receipt_path)
    assert complete["results_sha256"] == sha(result_path) == receipt["results_sha256"]
    for path in (result_path, receipt_path):
        assert path.with_suffix(".json.sha256").read_text().split() == [sha(path), path.name]
    freeze = read(validation / "SCORER_FREEZE.json")
    assert sha(validation / "SCORER_FREEZE.json") == result["scorer_freeze_sha256"]
    checked_frozen = 0
    bundle = root / "artifacts/runs/protected_final_test_v1/frozen_bundle"
    for base, records in ((root, freeze["source_inputs"]), (root, freeze["preparation_source_closure"]), (bundle, freeze["files"])):
        for item in records:
            path = base / item["path"]
            assert path.stat().st_size == item["bytes"] and sha(path) == item["sha256"]
            checked_frozen += 1
    earlier = []
    for study in ("within_anchor_partner_specificity_v1", "homology_source_challenge_v1", "external_bioplex_challenge_v1", "composition_order_challenge_v1", "direct_binary_feasibility_v1"):
        registry = root / f"artifacts/results/{study}/ARTIFACT_REGISTRY.json"
        entries = read(registry)["artifacts"]
        for item in entries:
            path = root / item["path"]
            assert sha(path) == item["sha256"] and path.stat().st_size == item["bytes"]
        earlier.append({"study": study, "registered_files_unchanged": len(entries), "registry_sha256": sha(registry)})
    private_run = root / ".private/protected_final_test_v1"
    assert not list((private_run / "session").glob("candidate-decrypt-*"))
    assert not list((private_run / "evaluation").glob("truth-decrypt-*"))
    assert sha(private_run / "freeze/PREDICTION_FREEZE.json") == result["prediction_freeze_sha256"]
    assert all(values["finite_bootstrap_draws"] == 2000 for data in result["cells"].values() for values in data["metrics"].values())
    assert all(values["finite_paired_draws"] == 2000 for data in result["cells"].values() for values in data["model_minus_controls"].values())
    # Exact graph-null expectation in C3, allowing harmless FP64 summation error.
    for scorer in ("training_degree_sum", "preferential_attachment", "component_degree_mass_product", "training_common_neighbors"):
        assert abs(result["cells"]["C3_test"]["metrics"][scorer]["ht_P_vs_U_concordance"] - .5) < 1e-12
    gates = yaml.safe_load((root / "governance/gates/gate_status_v51.yaml").read_text())
    final_gate = gates["gates"]["final_protected_evaluation"]
    for cell in ("C3", "C2", "C1"):
        assert final_gate[f"{cell}_concordance"] == result["cells"][f"{cell}_test"]["metrics"][result["model"]]["ht_P_vs_U_concordance"]
    assert final_gate["C3_all_11_prespecified_paired_lower_bounds_positive"] == result["cells"]["C3_test"]["above_every_control_with_positive_paired_lower_bound"]
    links = 0
    for relative in ("README.md", "docs/reports/README.md", "docs/reports/m1/M1_Protected_Final_Test_v1.md", "docs/protocols/PROTECTED_FINAL_TEST_v1.md"):
        path = root / relative
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" not in target and not target.startswith("#"):
                assert (path.parent / target.split("#")[0]).resolve().exists()
                links += 1
    audit = {"execution_id": "protected_final_test_v1", "status": "pass", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
             "result_sha256": sha(result_path), "receipt_sha256": sha(receipt_path), "completion_sha256": sha(completion),
             "frozen_source_and_bundle_records_reverified": checked_frozen, "earlier_closures": earlier,
             "local_document_links_resolved": links, "all_bootstrap_draws_finite": True,
             "C3_graph_controls_at_chance_within_1e_12": True, "gate_metrics_match_results": True,
             "temporary_candidate_and_truth_plaintext_absent": True, "prediction_freeze_unchanged": True,
             "new_decryption_scoring_fitting_or_protected_row_access": False,
             "same_author_not_independent_replication": True, "validator_sha256": sha(Path(__file__))}
    write(validation / "COMPLETED_AUDIT.json", audit)
    paths = [Path(__file__).resolve()]
    paths += [root / f"scripts/benchmark/{name}" for name in ("prepare_protected_final_test_v1.py", "protected_final_core_v1.py", "protected_final_guard_v1.py", "publish_protected_final_test_v1.py", "run_protected_final_test_v1.sh")]
    paths += [root / f"tests/unit/{name}" for name in ("test_protected_final_test_v1.py", "test_protected_final_publication_v1.py")]
    paths += [root / name for name in ("docs/protocols/PROTECTED_FINAL_TEST_v1.md", "docs/reports/m1/M1_Protected_Final_Test_v1.md", "governance/PROJECT_STATUS_v51.md", "governance/gates/gate_status_v51.yaml", "governance/decisions/DEC-0051-authorize-one-final-protected-evaluation.md")]
    paths += list(validation.glob("*.json")) + list(validation.glob("*.md")) + [result_path, result_path.with_suffix(".json.sha256"), receipt_path, receipt_path.with_suffix(".json.sha256")]
    records = [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(set(paths))]
    write(result_root / "ARTIFACT_REGISTRY.json", {"execution_id": "protected_final_test_v1", "status": "complete_frozen",
          "created_at_utc": datetime.now(timezone.utc).isoformat(), "artifacts": records, "protected_test_attempt_consumed": True,
          "public_pair_identity_or_row_scores": False, "new_fits_or_embeddings": False, "post_test_tuning": False,
          "commit_or_push_performed": False, "same_author_not_independent_replication": True})
    print(json.dumps({"completed_audit": "pass", "registered_files": len(records), "prior_files_unchanged": sum(x["registered_files_unchanged"] for x in earlier), "links_resolved": links}))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(strict=True))
