"""Reproduce the separate preparation export audit without running inference."""
import argparse
import csv
import gzip
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def check(value, message):
    if not value:
        raise RuntimeError(message)


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            value.update(block)
    return value.hexdigest()


def table(name):
    with (OUT / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def compressed(path):
    with gzip.open(path, "rt") as handle:
        return json.load(handle)


def main(verify_only):
    check(bool(os.environ.get("APPTAINER_CONTAINER")), "Use the accepted data image")
    manifest = json.loads((OUT / "SOURCE_PREPARATION.json").read_text())
    records = manifest["inputs"] + manifest["outputs"] + [manifest[k] for k in
              ("code", "config", "protocol", "runtime_qualification", "runtime_image_lock")]
    for item in records:
        path = ROOT / item["path"]
        check(digest(path) == item["sha256"], "Checksum mismatch: " + item["path"])
        if "bytes" in item:
            check(path.stat().st_size == item["bytes"], "Artifact size mismatch")
    pairs, proteins = table("published_pairs.csv"), table("published_proteins.csv")
    eligibility = table("TAXON_ELIGIBILITY.csv")
    sequences = compressed(OUT / "published_sequences.json.gz")
    evidence = compressed(OUT / "published_evidence.json.gz")
    check({int(r["taxid"]) for r in eligibility} == {83333, 559292}, "Eligibility scope differs")
    check({int(r["taxid"]) for r in eligibility if r["selected_for_primary_dataset"] == "True"} == {559292},
          "Primary eligibility differs")
    check({r["taxid"] for r in sequences.values()} == {9606, 559292}, "Unexpected sequence taxon")
    check(len(proteins) == len(sequences) and {p["protein_key"] for p in proteins} == set(sequences), "Endpoint table differs")
    for protein in proteins:
        item = sequences[protein["protein_key"]]
        sequence = item["sequence"]
        check(hashlib.sha256(sequence.encode()).hexdigest() == protein["sequence_sha256"] == item["sequence_sha256"], "Sequence digest differs")
        check(int(protein["taxid"]) == item["taxid"] and len(sequence) == int(protein["length"]), "Sequence metadata differs")
        check(50 <= len(sequence) <= 2000 and set(sequence) <= set("ACDEFGHIKLMNPQRSTVWY"), "Invalid sequence")
    by_pair = {p["pair_id"]: p for p in pairs}
    check(len(by_pair) == len(pairs), "Repeated pair ID")
    used = set()
    for pair in pairs:
        check(pair["reference_taxid"] == "559292" and pair["human_taxid"] == "9606" and
              pair["label"] == "P" and pair["pubmed_id"] == "27107014", "Pair scope differs")
        text = f"559292:{pair['reference_sequence_sha256']}:9606:{pair['human_sequence_sha256']}"
        check(hashlib.sha256(text.encode()).hexdigest() == pair["pair_id"], "Pair identity differs")
        used.update((f"559292:{pair['reference_sequence_sha256']}", f"9606:{pair['human_sequence_sha256']}"))
    check(used == set(sequences), "Missing or unused exported endpoint")
    counts, locators = Counter(), set()
    for item in evidence:
        check(item["pair_id"] in by_pair and item["reference_taxid"] == 559292 and
              item["verified_pubmed_id"] == "27107014" and "pubmed:27107014" in item["publication_ids"], "Evidence scope differs")
        counts[item["pair_id"]] += 1
        locators.add((item["archive"], item["member"], item["entry"], item["interaction_id"]))
    check(len(locators) == len(evidence), "Repeated evidence")
    check(all(counts[p["pair_id"]] == int(p["evidence_records"]) for p in pairs), "Evidence counts differ")
    source_record = next(r for r in manifest["inputs"] if r["path"].endswith("source_parsed_v2.json.gz"))
    source = compressed(ROOT / source_record["path"])
    expected_pairs, expected_evidence = set(), set()
    for pair in source["positives"]:
        if pair["pathogen_taxid"] != 559292:
            continue
        records_for_pair = [e for e in pair["evidence"] if "pubmed:27107014" in e["publication_ids"]]
        if records_for_pair:
            expected_pairs.add((pair["pathogen"], pair["human"]))
            expected_evidence.update((e["archive"], e["member"], e["entry"], e["interaction_id"]) for e in records_for_pair)
    check(expected_pairs == {(p["reference_sequence_sha256"], p["human_sequence_sha256"]) for p in pairs}, "Restricted source pair set differs")
    check(expected_evidence == locators, "Restricted source evidence set differs")
    check(manifest["original_xml_validation"]["all_selected_records_verified"], "Original XML validation missing")
    result = {"schema_version": 1, "at_utc": datetime.now(timezone.utc).isoformat(), "status": "passed",
              "preparation_manifest": {"path": str((OUT / "SOURCE_PREPARATION.json").relative_to(ROOT)),
                                       "sha256": digest(OUT / "SOURCE_PREPARATION.json")},
              "checked_artifact_records": len(records), "pair_set_recomputed_from_pinned_input": True,
              "evidence_set_recomputed_from_pinned_input": True, "only_primary_endpoint_sequences_exported": True,
              "all_exported_sequence_digests_verified": True, "scope_and_publication_verified": True,
              "unique_pairs": len(pairs), "unique_proteins": len(sequences), "evidence_records": len(evidence),
              "ranking_evaluation_ready": False, "model_inference_run": False}
    if not verify_only:
        with (OUT / "VALIDATION.json").open("x") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    main(parser.parse_args().verify_only)
