#!/usr/bin/env python3
"""Independently reconcile every evidence tier with the downloaded source tables."""
from collections import defaultdict
import csv
import io
from pathlib import Path
import re
import zipfile

from run_comparison import now, record, write_json

HERE = Path(__file__).resolve().parent


def zipped(path):
    with zipfile.ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".tsv"))
        return list(csv.DictReader(io.StringIO(archive.read(name).decode()), delimiter="\t"))


def main():
    sources = HERE / "sources"
    locations = {r["Gene"]: r for r in zipped(sources / "hpa_subcellular_location.tsv.zip")}
    mapping = defaultdict(set)
    for row in zipped(sources / "hpa_proteinatlas.tsv.zip"):
        for acc in re.split(r"[;, ]+", row["Uniprot"]):
            if acc:
                mapping[acc].add(row["Ensembl"])
    with (sources / "reviewed_human_annotations.tsv").open() as stream:
        proteins = {r["Entry"]: r for r in csv.DictReader(stream, delimiter="\t")}
    permitted = {"nuclear": {"Nucleoplasm", "Nuclear bodies", "Nuclear speckles", "Nucleoli", "Nucleoli rim", "Nucleoli fibrillar center", "Mitotic chromosome", "Kinetochore"},
                 "mitochondrial_matrix": {"Mitochondria"}, "mitochondrial": {"Mitochondria"}, "peroxisomal": {"Peroxisomes"},
                 "secreted": {"Endoplasmic reticulum", "Golgi apparatus", "Vesicles"},
                 "secretory_lumen": {"Endoplasmic reticulum", "Golgi apparatus", "Vesicles", "Lysosomes"}}
    with (HERE / "low_plausibility_annotations.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        source, accession = proteins[row["partner_uniprot"]], row["partner_uniprot"]
        identifiers = mapping[accession]
        hpa = locations.get(next(iter(identifiers)), {}) if len(identifiers) == 1 else {}
        if hpa and hpa["Gene name"] != source["Gene Names (primary)"].split()[0]:
            hpa = {}
        assert row["HPA_Ensembl"] == hpa.get("Gene", "")
        assert row["HPA_gene"] == hpa.get("Gene name", "")
        assert row["HPA_reliability"] == hpa.get("Reliability", "")
        high = {v for key in ("Enhanced", "Supported") for v in hpa.get(key, "").split(";") if v}
        all_locations = high | {v for key in ("Approved", "Uncertain") for v in hpa.get(key, "").split(";") if v}
        allowed = permitted[row["localization_class"]]
        assert not all_locations - allowed
        assert row["hpa_high_confidence_locations"] == ";".join(sorted(high))
        assert row["hpa_all_locations"] == ";".join(sorted(all_locations))
        assert row["uniprot_location"] == source["Subcellular location [CC]"]
        experimental = "ECO:0000269" in source["Subcellular location [CC]"].split("Note=", 1)[0]
        support = bool(high & allowed)
        assert row["uniprot_experimental_location"] == str(experimental)
        assert row["hpa_supported_location"] == str(support)
        quality = 0 if experimental and support else 1 if experimental else 2 if support else 3
        assert int(row["annotation_quality"]) == quality
        if row["evidence_tier"].startswith("B_"):
            assert row["target"] == "EGFR" and quality == 0
        elif row["target"] == "EGFR":
            assert row["localization_class"] == "peroxisomal"
        if row["target"] in ("ERN1", "EGFR", "TNFRSF1A"):
            assert row["localization_class"] not in ("secreted", "secretory_lumen")
        if row["target"] in ("TP53", "BRCA1"):
            assert not row["localization_class"].startswith("mitochondrial")
    write_json(HERE / "EVIDENCE_VALIDATION.json", {"at_utc": now(), "passed": True,
               "annotations_independently_reconciled": len(rows), "HPA_identifier_gene_location_and_quality_checked": True,
               "UniProt_experimental_evidence_codes_checked": True, "membrane_and_secondary_location_exceptions_checked": True,
               "validator": record(Path(__file__))})
    print(f"Reconciled {len(rows)} annotation rows with UniProt and HPA source records", flush=True)


if __name__ == "__main__":
    main()
