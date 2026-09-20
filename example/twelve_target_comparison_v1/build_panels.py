#!/usr/bin/env python3
"""Construct six new score-blind panels from retained public source snapshots.

Run inside the qualified data SIF. Only TRAIN/development arrays are opened.
The original six panel CSVs and manifests are never changed.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

import numpy as np

HERE = Path(__file__).resolve().parent
ACCESSION = r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})"
ALLOWED = frozenset("ACDEFGHIKLMNPQRSTVWYBXZUO")
COLUMNS = ("query_gene", "query_uniprot", "partner_gene", "partner_uniprot", "class")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def download(url, path):
    """Reuse only verified source bytes from this new run, never scored features."""
    metadata_path = path.with_name(path.name + ".metadata.json")
    if path.exists() and metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        if metadata["url"] != url or metadata["sha256"] != sha(path):
            raise RuntimeError(f"Source snapshot changed: {path}")
        return path.read_bytes(), metadata
    last_error = None
    for attempt in range(5):
        try:
            with urlopen(Request(url, headers={"User-Agent": "iPIN-OpenPPI-twelve-target/1.0"}), timeout=45) as response:
                body = response.read()
                headers = {k.lower(): v for k, v in response.headers.items()}
            path.write_bytes(body)
            metadata = {"url": url, "sha256": sha(path), "bytes": len(body),
                        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                        "headers": headers}
            write_json(metadata_path, metadata)
            return body, metadata
        except Exception as error:
            last_error = error
            if attempt < 4:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Source retrieval failed: {url}") from last_error


def location(text):
    return re.sub(r"\{[^}]*\}", "", text.split("Note=", 1)[0]).lower()


def matches_context(protein, compartment, transmembrane):
    tokens = ("cytoplasm", "cytosol") if compartment == "cytoplasm" else (compartment,)
    return protein["transmembrane"] == transmembrane and any(token in protein["location"] for token in tokens)


def selection_key(salt, target, anchor, stratum, accession):
    return hashlib.sha256("|".join((salt, target, anchor, stratum, accession)).encode()).hexdigest()


def read_pool(raw):
    rows = list(csv.DictReader(io.StringIO(raw.decode()), delimiter="\t"))
    proteins = {}
    for row in rows:
        sequence = row["Sequence"]
        genes = row["Gene Names (primary)"].split()
        if not genes or len(sequence) < 30 or set(sequence) - ALLOWED:
            continue
        proteins[row["Entry"]] = {
            "accession": row["Entry"], "gene": genes[0], "length": len(sequence),
            "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
            "transmembrane": bool(row["Transmembrane"]),
            "location": location(row["Subcellular location [CC]"]),
            "protein_existence": row["Protein existence"],
            "subunit": row["Subunit structure"],
        }
    return proteins, len(rows)


def intact_partners(accession, sources):
    partners, pages, matched, total = set(), [], 0, None
    offset = 0
    while total is None or offset < total:
        url = ("https://www.ebi.ac.uk/Tools/webservices/psicquic/intact/webservices/current/search/query/"
               + quote("id:" + accession + "*", safe="") + f"?format=tab25&firstResult={offset}&maxResults=2500")
        body, metadata = download(url, sources / f"intact_{accession}_{offset}.tsv")
        lines = [line.split("\t") for line in body.decode().splitlines() if line and not line.startswith("#")]
        reported = metadata["headers"].get("x-psicquic-count")
        if reported is None:
            raise RuntimeError("IntAct omitted its total-record count")
        if total is not None and total != int(reported):
            raise RuntimeError("IntAct record count changed across pages")
        total = int(reported)
        pages.append({**metadata, "rows": len(lines), "reported_total": total})
        for fields in lines:
            if len(fields) < 15:
                raise RuntimeError("Incomplete IntAct MITAB record")
            if "taxid:9606" not in fields[9] or "taxid:9606" not in fields[10]:
                continue
            sides = [set(re.findall(r"uniprotkb:(" + ACCESSION + r")(?:-\d+)?", "|".join(fields[i] for i in indices)))
                     for indices in ((0, 2, 4), (1, 3, 5))]
            if accession in sides[0]:
                partners.update(sides[1])
                matched += 1
            if accession in sides[1]:
                partners.update(sides[0])
                matched += 1
        offset += len(lines)
        if not lines and offset < total:
            raise RuntimeError("IntAct pagination ended early")
    return partners, {"query": "id:" + accession + "*", "records": total,
                      "matched_human_orientations": matched, "pages": pages,
                      "human_partner_accessions": sorted(partners)}


def prior_neighbors(root, target_records):
    folder = root / "benchmark/tuna/data"
    reference = json.loads((folder / "sequences.json").read_text())
    expected = json.loads((folder / "DATA_MANIFEST.json").read_text())
    inventory = {Path(item["path"]).name: item for item in expected["outputs"]}
    for name in ("sequences.json", "training.npz", "development_00.npz", "development_01.npz", "development_02.npz"):
        if sha(folder / name) != inventory[name]["sha256"]:
            raise RuntimeError(f"Frozen TRAIN/development source changed: {name}")
    accessions = reference["accessions"]
    digests = reference["sha256"]
    ids = {gene: {i for i, (accs, digest) in enumerate(zip(accessions, digests, strict=True))
                  if protein["accession"] in accs or protein["sequence_sha256"] == digest}
           for gene, protein in target_records.items()}
    neighbors = {gene: {key: set() for key in ("TRAIN_P", "TRAIN_U", "DEV_P", "DEV_U")} for gene in ids}
    records = []
    for name in ("training.npz", "development_00.npz", "development_01.npz", "development_02.npz"):
        path = folder / name
        records.append({"path": str(path.relative_to(root)), "sha256": sha(path)})
        with np.load(path, allow_pickle=False) as archive:
            groups = (("TRAIN_P", archive["p_a"], archive["p_b"]), ("TRAIN_U", archive["u_a"], archive["u_b"])) if name == "training.npz" else (
                ("DEV_P", archive["a"][archive["positive"]], archive["b"][archive["positive"]]),
                ("DEV_U", archive["a"][~archive["positive"]], archive["b"][~archive["positive"]]))
            for key, left, right in groups:
                for gene, indices in ids.items():
                    if indices:
                        neighbors[gene][key].update(right[np.isin(left, list(indices))].tolist())
                        neighbors[gene][key].update(left[np.isin(right, list(indices))].tolist())
    result = {}
    for gene, groups in neighbors.items():
        result[gene] = {key: {"accessions": sorted({a for i in indices for a in accessions[i]}),
                               "sequence_sha256": sorted({digests[i] for i in indices})}
                        for key, indices in groups.items()}
    return result, records, sha(folder / "sequences.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Run scientific preparation inside an accepted Apptainer SIF")
    root, out = args.root, args.output
    config = json.loads((HERE / "panel_config.json").read_text())
    sources = out / "sources"
    sources.mkdir(exist_ok=True)
    original = json.loads((root / "example/ERN1/panel_manifest.json").read_text())
    pool_raw, pool_meta = download(original["pool_source"]["url"], sources / "reviewed_human.tsv")
    proteins, source_count = read_pool(pool_raw)
    release = pool_meta["headers"].get("x-uniprot-release")
    if not release:
        raise RuntimeError("UniProt source release missing")
    print(f"UniProt {release}: {source_count} source rows, {len(proteins)} eligible", flush=True)
    all_specs = [p for t in config["new_targets"] for p in [t, *t["positives"]]]
    def fetch(spec):
        acc = spec["accession"]
        body, meta = download(f"https://rest.uniprot.org/uniprotkb/{acc}.json", sources / f"uniprot_{acc}.json")
        entry = json.loads(body)
        if meta["headers"].get("x-uniprot-release") != release:
            raise RuntimeError("UniProt release changed during panel preparation")
        protein = proteins[acc]
        if protein["gene"] != spec["gene"] or entry["primaryAccession"] != acc or entry["organism"]["taxonId"] != 9606:
            raise RuntimeError(f"Target/partner identity mismatch: {spec}")
        if hashlib.sha256(entry["sequence"]["value"].encode()).hexdigest() != protein["sequence_sha256"]:
            raise RuntimeError("Pool/entry sequence mismatch")
        if "compartment" in spec and not matches_context(protein, spec["compartment"], protein["transmembrane"]):
            go_locations = [v["value"][2:].lower() for ref in entry.get("uniProtKBCrossReferences", [])
                            if ref["database"] == "GO" for v in ref.get("properties", [])
                            if v.get("value", "").startswith("C:")]
            if spec["compartment"] not in go_locations:
                raise RuntimeError(f"Declared positive compartment lacks annotation: {spec['gene']}, {protein['location']}, GO={go_locations}")
            print(f"{spec['gene']} context supported by UniProt GO C:{spec['compartment']}; U filtering still uses location text", flush=True)
        return acc, (entry, meta)
    with ThreadPoolExecutor(max_workers=4) as executor:
        entries = dict(executor.map(fetch, all_specs))
    prior, prior_sources, sequence_source = prior_neighbors(root, {t["gene"]: proteins[t["accession"]] for t in config["new_targets"]})
    outcomes = []
    for target in config["new_targets"]:
        gene, acc = target["gene"], target["accession"]
        entry, target_meta = entries[acc]
        excluded, intact = intact_partners(acc, sources)
        synonyms = {gene, *[n["value"] for names in entry.get("genes", []) for n in names.get("synonyms", [])]}
        subunit = " ".join(text["value"] for c in entry.get("comments", []) if c["commentType"] == "SUBUNIT" for text in c.get("texts", []))
        pattern = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(s) for s in synonyms if len(s) >= 3) + r")(?![A-Za-z0-9])", re.I)
        mentioned = {a for a, protein in proteins.items() if re.search(r"(?<![A-Za-z0-9])" + re.escape(protein["gene"]) + r"(?![A-Za-z0-9])", subunit, re.I)}
        reciprocal = {a for a, protein in proteins.items() if pattern.search(protein["subunit"])}
        for comment in entry.get("comments", []):
            if comment["commentType"] == "INTERACTION":
                for interaction in comment.get("interactions", []):
                    for key in ("interactantOne", "interactantTwo"):
                        value = interaction.get(key, {}).get("uniProtKBAccession", "").split("-")[0]
                        if value:
                            excluded.add(value)
        excluded.update(mentioned | reciprocal | {acc} | {p["accession"] for p in target["positives"]})
        excluded_hashes = set()
        for group in prior[gene].values():
            excluded.update(group["accessions"])
            excluded_hashes.update(group["sequence_sha256"])
        excluded_hashes.update(proteins[a]["sequence_sha256"] for a in excluded if a in proteins)
        candidates, seen = {}, set()
        for a, protein in sorted(proteins.items()):
            digest = protein["sequence_sha256"]
            if a not in excluded and digest not in excluded_hashes and digest not in seen:
                candidates[a] = protein
                seen.add(digest)
        selected, used, blocks = {}, set(), []
        def available(positive, stratum):
            anchor = proteins[positive["accession"]]
            return [a for a, protein in candidates.items() if a not in used
                    and anchor["length"] / 2 <= protein["length"] <= anchor["length"] * 2
                    and (stratum == "background" or matches_context(protein, positive["compartment"], anchor["transmembrane"]))]
        order = sorted(target["positives"], key=lambda p: (len(available(p, "context")), p["accession"]))
        for stratum, positives in (("context", order), ("background", target["positives"])):
            for positive in positives:
                options = available(positive, stratum)
                if len(options) < 50:
                    raise RuntimeError(f"Insufficient {gene}/{positive['gene']}/{stratum}: {len(options)}; no widening permitted")
                options.sort(key=lambda a: selection_key(config["sampling_salt"], gene, positive["accession"], stratum, a))
                chosen = options[:50]
                used.update(chosen)
                selected[positive["accession"], stratum] = (chosen, len(options))
        rows, annotations = [], []
        def add(a, label, **extras):
            protein = proteins[a]
            rows.append(dict(zip(COLUMNS, (gene, acc, protein["gene"], a, label))))
            annotations.append({"row": len(rows), "class": label, "partner_gene": protein["gene"], "partner_uniprot": a,
                                "length": protein["length"], "sequence_sha256": protein["sequence_sha256"], **extras})
        for positive in target["positives"]:
            a = positive["accession"]
            exposure = {key: a in group["accessions"] or proteins[a]["sequence_sha256"] in group["sequence_sha256"] for key, group in prior[gene].items()}
            add(a, "P", homomeric=a == acc, prior_pair_exposure=exposure,
                evidence={"url": positive["url"], "note": positive["note"], "human_curated_record": f"https://www.uniprot.org/uniprotkb/{acc}/entry"})
        for positive in target["positives"]:
            for stratum in ("context", "background"):
                chosen, count = selected[positive["accession"], stratum]
                first = len(rows) + 1
                for a in chosen:
                    add(a, "U", anchor_positive_uniprot=positive["accession"], stratum=stratum)
                blocks.append({"first_data_row": first, "last_data_row": len(rows), "anchor_gene": positive["gene"],
                               "anchor_accession": positive["accession"], "stratum": stratum,
                               "compartment": positive["compartment"] if stratum == "context" else None,
                               "transmembrane": proteins[positive["accession"]]["transmembrane"] if stratum == "context" else None,
                               "length_ratio_limit": 2, "available_at_selection": count})
        folder = root / "example" / gene
        folder.mkdir(exist_ok=True)
        csv_path = folder / f"{gene.lower()}_ipin_panel.csv"
        with csv_path.open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        manifest = {"schema": "ipin_target_panel_v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                    "target": {k: v for k, v in proteins[acc].items() if k != "subunit"}, "process": target["process"],
                    "csv": csv_path.name, "csv_sha256": sha(csv_path), "P": 3, "U": 300,
                    "sampling_salt": config["sampling_salt"], "pool_source": {**pool_meta, "release": release,
                    "reviewed_human_rows": source_count, "eligible_rows": len(proteins)},
                    "target_uniprot_source": target_meta, "positive_uniprot_sources": {p["accession"]: entries[p["accession"]][1] for p in target["positives"]},
                    "intact_source": intact, "subunit_annotation_exclusions": sorted(mentioned | reciprocal),
                    "excluded_accessions": sorted(excluded), "excluded_sequence_sha256": sorted(excluded_hashes),
                    "training_development_sources": prior_sources, "frozen_sequence_source_sha256": sequence_source,
                    "prior_neighbors": prior[gene], "no_model_scores_used": True, "protected_test_truth_read": False,
                    "sampling_rule": {**original["sampling_rule"], "anchor_context_provenance": "Declared positive compartment checked against UniProt location or GO cellular-component annotation; U filtering uses subcellular-location text only"}, "U_blocks": blocks, "rows": annotations,
                    "configuration_sha256": sha(HERE / "panel_config.json"), "builder_sha256": sha(Path(__file__))}
        write_json(folder / "panel_manifest.json", manifest)
        outcomes.append({"target": gene, "P": 3, "U": 300, "csv_sha256": sha(csv_path),
                         "manifest_sha256": sha(folder / "panel_manifest.json"),
                         "positive_exposure": {r["partner_gene"]: r["prior_pair_exposure"] for r in annotations[:3]}})
        print(f"Prepared {gene}: 3 P + 300 U; positive exposure {outcomes[-1]['positive_exposure']}", flush=True)
    write_json(out / "PANEL_BUILD.json", {"passed": True, "at_utc": datetime.now(timezone.utc).isoformat(),
               "configuration_sha256": sha(HERE / "panel_config.json"), "builder_sha256": sha(Path(__file__)),
               "new_targets": outcomes, "uniprot_release": release, "protected_test_truth_read": False,
               "model_scores_read": False, "source_snapshots": "sources/ (retained locally; excluded from Git)"})


if __name__ == "__main__":
    main()
