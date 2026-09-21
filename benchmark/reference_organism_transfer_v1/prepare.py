#!/usr/bin/env python3
"""Prepare one published human/S288C reference dataset without model scoring."""

import csv
import gzip
import hashlib
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
HUMAN = 9606
YEAST = 559292
K12 = 83333
PMID = "27107014"
NAMES = {K12: "Escherichia coli K-12", YEAST: "Saccharomyces cerevisiae S288C"}
OUTPUTS = (
    "TAXON_ELIGIBILITY.csv", "published_pairs.csv", "published_proteins.csv",
    "published_sequences.json.gz", "published_evidence.json.gz",
    "SOURCE_PREPARATION.json", "SOURCE_REVIEW.md",
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def record(path):
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": sha(path)}


def verify(item):
    path = ROOT / item["path"]
    require(sha(path) == item["sha256"], f"Input checksum mismatch: {item['path']}")
    if "bytes" in item:
        require(path.stat().st_size == item["bytes"], f"Input size mismatch: {path}")
    return path


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_gzip(path, value):
    body = (json.dumps(value, sort_keys=True) + "\n").encode()
    with path.open("xb") as handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as zipped:
            zipped.write(body)


def write_csv(path, rows):
    require(bool(rows), f"Empty table: {path.name}")
    with path.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def cv_id(element, child):
    return next((ref.get("id") for ref in element.findall(f"./{{*}}{child}/{{*}}xref/*")
                 if ref.get("db") == "psi-mi" and ref.get("refType") == "identity"), None)


def interactor_profile(element):
    organism = element.find("./{*}organism")
    if organism is None:
        return None
    taxid = int(organism.get("ncbiTaxId"))
    if taxid not in (HUMAN, YEAST):
        return None
    sequence = "".join(element.findtext("./{*}sequence", "").split()).upper()
    accession = next((r.get("id") for r in element.findall("./{*}xref/*")
                      if r.get("db", "").lower() in ("uniprotkb", "uniprot")
                      and r.get("refType") == "identity"), None)
    return {"taxid": taxid, "accession": accession,
            "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
            "molecule_type": cv_id(element, "interactorType")}


def experiment_profile(element):
    return {
        "pmids": {r.get("id") for r in element.findall("./{*}bibref/{*}xref/*")
                  if r.get("db") == "pubmed" and re.fullmatch(r"[1-9][0-9]*", r.get("id", ""))},
        "method": cv_id(element, "interactionDetectionMethod"),
        "host_taxids": {int(h.get("ncbiTaxId")) for h in
                        element.findall("./{*}hostOrganismList/{*}hostOrganism")},
    }


def validate_original_xml(archive_path, expected, allowed_tags):
    """Read XML directly, independently of the source-cache parser."""
    found = set()
    methods = Counter()
    members = sorted({key[0] for key in expected})
    with zipfile.ZipFile(archive_path) as archive:
        for member in members:
            entry = 0
            stack, proteins, experiments = [], {}, {}
            with archive.open(member) as handle:
                for event, element in ET.iterparse(handle, events=("start", "end")):
                    tag = element.tag.rsplit("}", 1)[-1]
                    if event == "start":
                        stack.append(tag)
                        if tag == "entry":
                            entry += 1
                            proteins, experiments = {}, {}
                        continue
                    parent = stack[-2] if len(stack) > 1 else None
                    if tag == "interactor":
                        proteins[element.get("id")] = interactor_profile(element)
                        if parent == "interactorList":
                            element.clear()
                    elif tag == "experimentDescription":
                        experiments[element.get("id")] = experiment_profile(element)
                        if parent == "experimentList" and "interaction" not in stack:
                            element.clear()
                    elif tag == "interaction":
                        identity = next((r.get("id") for r in element.findall("./{*}xref/*")
                                         if r.get("db") == "intact" and r.get("refType") == "identity"),
                                        element.get("id"))
                        key = (member, entry, identity)
                        if key in expected:
                            require(key not in found, f"Repeated XML evidence identity: {key}")
                            pair, evidence = expected[key]
                            participants = element.findall("./{*}participantList/{*}participant")
                            require(len(participants) == 2, f"Nonbinary record: {key}")
                            resolved = []
                            for participant in participants:
                                inline = participant.find("./{*}interactor")
                                ref = participant.findtext("./{*}interactorRef")
                                if inline is not None:
                                    ref = inline.get("id")
                                resolved.append(proteins.get(ref))
                            require(all(resolved), f"Unresolved/other organism: {key}")
                            by_taxid = {p["taxid"]: p for p in resolved}
                            require(set(by_taxid) == {HUMAN, YEAST}, f"Incorrect participant taxa: {key}")
                            for taxid, digest, accession in (
                                (HUMAN, pair["human"], evidence["human_accession"]),
                                (YEAST, pair["pathogen"], evidence["pathogen_accession"]),
                            ):
                                profile = by_taxid[taxid]
                                require(profile["sequence_sha256"] == digest and
                                        profile["accession"] == accession and
                                        profile["molecule_type"] == "MI:0326", f"Endpoint mismatch: {key}")
                            for flag in ("negative", "modelled", "intramolecular"):
                                require(element.findtext(f"./{{*}}{flag}", "false").strip().lower()
                                        not in ("true", "1"), f"Disallowed {flag}: {key}")
                            refs = [r.text for r in element.findall("./{*}experimentList/{*}experimentRef")]
                            refs.extend(e.get("id") for e in element.findall("./{*}experimentList/{*}experimentDescription"))
                            require(bool(refs) and all(r in experiments for r in refs), f"Missing experiment: {key}")
                            exp = [experiments[r] for r in refs]
                            require(PMID in set().union(*(e["pmids"] for e in exp)), f"Publication mismatch: {key}")
                            method_ids = {e["method"] for e in exp}
                            require(method_ids == set(evidence["detection_method_ids"]), f"Method mismatch: {key}")
                            require(set().union(*(e["host_taxids"] for e in exp)) ==
                                    {int(t) for t in evidence["experimental_host_taxids"]}, f"Assay-host mismatch: {key}")
                            require(cv_id(element, "interactionType") == evidence["interaction_type"], f"Type mismatch: {key}")
                            features = [f for p in participants for f in p.findall("./{*}featureList/{*}feature")]
                            feature_ids = {cv_id(f, "featureType") for f in features}
                            require(feature_ids <= allowed_tags and len(features) == evidence["participant_feature_count"]
                                    and feature_ids == set(evidence["feature_type_ids"]), f"Feature mismatch: {key}")
                            found.add(key)
                            methods.update(method_ids)
                        element.clear()
                    elif tag == "entry":
                        element.clear()
                    stack.pop()
            print(f"Validated {member}: {len(found):,}/{len(expected):,} selected records", flush=True)
    require(found == set(expected), "Selected evidence missing from original XML")
    return {"all_selected_records_verified": True, "evidence_records": len(found),
            "members": members, "detection_method_record_counts": dict(methods)}


def review_negative_members(archive_path):
    counts = Counter()
    with zipfile.ZipFile(archive_path) as archive:
        members = sorted(m for m in archive.namelist() if m.endswith("_negative.xml"))
        for member in members:
            with archive.open(member) as handle:
                root = ET.parse(handle).getroot()
            for entry in root.findall("./{*}entry"):
                proteins = {p.get("id"): p for p in entry.findall(".//{*}interactor")}
                for interaction in entry.findall("./{*}interactionList/{*}interaction"):
                    counts["interactions_reviewed"] += 1
                    participants = interaction.findall("./{*}participantList/{*}participant")
                    if len(participants) != 2:
                        continue
                    taxids = []
                    for participant in participants:
                        protein = participant.find("./{*}interactor")
                        if protein is None:
                            protein = proteins.get(participant.findtext("./{*}interactorRef"))
                        organism = protein.find("./{*}organism") if protein is not None else None
                        if organism is not None:
                            taxids.append(int(organism.get("ncbiTaxId")))
                    if sorted(taxids) in ([HUMAN, K12], [HUMAN, YEAST]):
                        counts["reference_human_candidate_records"] += 1
    return {"members_reviewed": len(members), "interactions_reviewed": counts["interactions_reviewed"],
            "reference_human_candidate_records": counts["reference_human_candidate_records"],
            "scope": "Explicit negative archive members; not an exhaustive search of published comparison data"}


def main():
    require(bool(os.environ.get("APPTAINER_CONTAINER") or os.environ.get("SINGULARITY_CONTAINER")),
            "Run inside the accepted Apptainer data image")
    require(not any((OUT / name).exists() for name in OUTPUTS), "Refusing to replace prepared outputs")
    config = read_json(OUT / "config.json")
    require(config["reviewed_reference_taxids"] == [K12, YEAST] and
            config["primary_reference_taxid"] == YEAST and config["human_taxid"] == HUMAN and
            config["primary_pubmed_id"] == PMID and not config["other_taxids_eligible"] and
            config["published_pairs_only"] and not config["model_scoring_enabled"], "Scope configuration changed")
    source_manifest_path = verify(config["source_manifest"])
    taxonomy_path = verify(config["taxonomy"])
    source = read_json(source_manifest_path)
    parsed_path = verify(source["parsed_source"])
    archive_item = next(r for r in source["sources"] if r["path"] ==
                        "data/raw/intact/2026-01-09/psi30/species/human.zip")
    archive_path = verify(archive_item)
    with taxonomy_path.open(newline="") as handle:
        taxonomy = {int(r["taxid"]): r for r in csv.DictReader(handle)}
    for taxid, name in NAMES.items():
        require(taxonomy[taxid]["ncbi_scientific_name"] == name and taxonomy[taxid]["ncbi_rank"] == "strain",
                "Reference taxonomy identity changed")
    with gzip.open(parsed_path, "rt") as handle:
        parsed = json.load(handle)
    reviewed = [p for p in parsed["positives"] if p["pathogen_taxid"] in NAMES]
    primary = []
    for pair in reviewed:
        if pair["pathogen_taxid"] != YEAST:
            continue
        evidence = [e for e in pair["evidence"] if f"pubmed:{PMID}" in e["publication_ids"]]
        if evidence:
            primary.append({**pair, "evidence": evidence})
    require(bool(primary), "No primary published pairs")
    require(len({(p['pathogen'], p['human']) for p in primary}) == len(primary), "Duplicate primary pair")
    expected = {}
    for pair in primary:
        for evidence in pair["evidence"]:
            require(evidence["archive"] == archive_item["path"] and evidence["pathogen_taxid"] == YEAST,
                    "Evidence source or participant taxid mismatch")
            key = (evidence["member"], evidence["entry"], evidence["interaction_id"])
            require(key not in expected, "Duplicate cached evidence identity")
            expected[key] = (pair, evidence)
    xml_validation = validate_original_xml(archive_path, expected, set(source["allowed_tag_feature_types"]))
    negative_review = review_negative_members(archive_path)
    eligibility = []
    for taxid, name in NAMES.items():
        rows = [r for r in reviewed if r["pathogen_taxid"] == taxid]
        require(len(rows) == int(taxonomy[taxid]["eligible_positive_pairs"]), "Feasibility count mismatch")
        eligibility.append({"taxid": taxid, "reference_name": name, "eligible_reference_label": True,
                            "selected_for_primary_dataset": taxid == YEAST,
                            "available_positive_pairs": len(rows),
                            "available_nonhuman_proteins": len({r["pathogen"] for r in rows}),
                            "primary_pubmed_id": PMID if taxid == YEAST else "",
                            "decision": "published_single_study_pilot" if taxid == YEAST else "insufficient_coverage_for_primary_comparison",
                            "classification_reference": config["reference_classification_sources"][str(taxid)]})
    pair_rows, evidence_rows = [], []
    proteins, aliases = {}, defaultdict(set)
    legacy_aliases = Counter()
    for pair in sorted(primary, key=lambda p: (p["pathogen"], p["human"])):
        pair_id = hashlib.sha256(f"{YEAST}:{pair['pathogen']}:{HUMAN}:{pair['human']}".encode()).hexdigest()
        for taxid, digest in ((YEAST, pair["pathogen"]), (HUMAN, pair["human"])):
            key = f"{taxid}:{digest}"
            protein = parsed["proteins"][key]
            sequence = protein["sequence"]
            require(protein["taxid"] == taxid and protein["sequence_sha256"] == digest and
                    hashlib.sha256(sequence.encode()).hexdigest() == digest and 50 <= len(sequence) <= 2000 and
                    set(sequence) <= set("ACDEFGHIKLMNPQRSTVWY"), "Invalid primary reference sequence")
            proteins[key] = {"taxid": taxid, "sequence_sha256": digest, "sequence": sequence}
        require(pair["pathogen"] != pair["human"], "Identical-sequence endpoints")
        for evidence in pair["evidence"]:
            aliases[f"{YEAST}:{pair['pathogen']}"].add(evidence["pathogen_accession"])
            aliases[f"{HUMAN}:{pair['human']}"].add(evidence["human_accession"])
            legacy_aliases.update(p for p in evidence["publication_ids"] if not re.fullmatch(r"pubmed:[1-9][0-9]*", p))
            renamed = {k.replace("pathogen_", "reference_"): v for k, v in evidence.items()}
            evidence_rows.append({"pair_id": pair_id, **renamed, "verified_pubmed_id": PMID})
        pair_rows.append({"pair_id": pair_id, "reference_taxid": YEAST, "human_taxid": HUMAN,
                          "reference_sequence_sha256": pair["pathogen"], "human_sequence_sha256": pair["human"],
                          "label": "P", "pubmed_id": PMID, "evidence_records": len(pair["evidence"])})
    protein_rows = [{"protein_key": key, "taxid": value["taxid"],
                     "sequence_sha256": value["sequence_sha256"], "length": len(value["sequence"]),
                     "source_accessions": ";".join(sorted(aliases[key]))} for key, value in sorted(proteins.items())]
    inputs = [config["source_manifest"], config["taxonomy"], source["parsed_source"], archive_item]
    for item in inputs:
        verify(item)
    coverage = {"primary_pairs": len(pair_rows), "primary_evidence_records": len(evidence_rows),
                "reference_proteins": sum(p["taxid"] == YEAST for p in protein_rows),
                "human_proteins": sum(p["taxid"] == HUMAN for p in protein_rows), "primary_publications": 1}
    write_csv(OUT / "TAXON_ELIGIBILITY.csv", eligibility)
    write_csv(OUT / "published_pairs.csv", pair_rows)
    write_csv(OUT / "published_proteins.csv", protein_rows)
    write_gzip(OUT / "published_sequences.json.gz", proteins)
    write_gzip(OUT / "published_evidence.json.gz", evidence_rows)
    review = f"""# Published reference-organism source review

The primary dataset contains {coverage['primary_pairs']:,} published positive pairs,
{coverage['reference_proteins']:,} S288C proteins, {coverage['human_proteins']:,} human proteins,
and {coverage['primary_evidence_records']:,} original evidence records from
[PMID {PMID}](https://pubmed.ncbi.nlm.nih.gov/{PMID}/).
Every selected record was checked against the original XML for participant
identity, reference sequence, publication, method, assay host, and features.

K-12 is an eligible reference label but has only four available positive pairs
across three nonhuman proteins. It is not part of this primary pilot.

The explicit negative-member review covered {negative_review['members_reviewed']} archive
members and {negative_review['interactions_reviewed']} interaction records. It found
{negative_review['reference_human_candidate_records']} exact reference/human binary candidates.
This is not an exhaustive audit of all published comparison data.

Source preparation is complete. Ranking evaluation is not ready: an appropriate
published comparison set, TRAIN/development exposure audit, and inference input
freeze remain required. No scores were read or generated, and no missing pair
was assigned a negative label. All retained pairs come from a single study.
See [PROTOCOL.md](PROTOCOL.md) for scope and interpretation.
"""
    with (OUT / "SOURCE_REVIEW.md").open("x") as handle:
        handle.write(review)
    write_json(OUT / "SOURCE_PREPARATION.json", {
        "schema_version": 1, "at_utc": datetime.now(timezone.utc).isoformat(),
        "study_id": config["study_id"], "status": "published_positive_source_prepared",
        "inputs": inputs, "code": record(Path(__file__)), "config": record(OUT / "config.json"),
        "protocol": record(OUT / "PROTOCOL.md"), "coverage": coverage,
        "scope": {"reviewed_reference_taxids": [K12, YEAST], "primary_reference_taxid": YEAST,
                  "human_taxid": HUMAN, "other_taxids_eligible": False, "primary_pubmed_id": PMID},
        "original_xml_validation": xml_validation, "negative_member_review": negative_review,
        "nonnumeric_publication_alias_record_counts": dict(legacy_aliases),
        "source_field_renames": {"pathogen_*": "reference_*"},
        "sequence_identity_interpretation": "Archived reference taxonomy; experimental culture/construct authenticity not independently established",
        "runtime_container": os.environ.get("APPTAINER_CONTAINER", os.environ.get("SINGULARITY_CONTAINER")),
        "runtime_qualification": record(ROOT / "containers/manifests/ipin-data-arm64_0.1.2.qualification.json"),
        "runtime_image_lock": record(ROOT / "containers/locks/ipin-data-arm64_0.1.2.sif.sha256"),
        "ranking_evaluation_ready": False,
        "remaining_gates": ["published_comparison_set_and_assay_interpretation", "training_and_development_exposure_audit", "inference_input_and_model_freeze"],
        "model_scores_read": False, "model_inference_run": False, "protected_test_records_read": False,
        "outputs": [record(OUT / name) for name in OUTPUTS if name != "SOURCE_PREPARATION.json"],
    })
    print(json.dumps({"coverage": coverage, "negative_member_review": negative_review, "ranking_evaluation_ready": False}, sort_keys=True))


if __name__ == "__main__":
    main()
