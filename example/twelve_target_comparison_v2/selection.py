"""Score-independent localization evidence and conservative candidate classes."""
from __future__ import annotations

import csv
import hashlib
import io
import re
import zipfile
from collections import defaultdict

ALLOWED = frozenset("ACDEFGHIKLMNPQRSTVWYBXZUO")
HPA_NUCLEAR = {"Nucleoplasm", "Nuclear bodies", "Nuclear speckles", "Nucleoli", "Nucleoli rim",
               "Nucleoli fibrillar center", "Mitotic chromosome", "Kinetochore"}
HPA_ALLOWED = {
    "nuclear": HPA_NUCLEAR,
    "mitochondrial_matrix": {"Mitochondria"},
    "mitochondrial": {"Mitochondria"},
    "peroxisomal": {"Peroxisomes"},
    "secreted": {"Endoplasmic reticulum", "Golgi apparatus", "Vesicles"},
    "secretory_lumen": {"Endoplasmic reticulum", "Golgi apparatus", "Vesicles", "Lysosomes"},
}
# These are encounter screens, not assertions of experimentally absent binding.
# Both faces and trafficking of type-I membrane receptors count as accessible.
STRICT_CLASSES = {
    "ERN1": {"nuclear", "mitochondrial_matrix", "peroxisomal"},
    "TP53": {"secreted", "secretory_lumen", "peroxisomal"},
    "EGFR": {"peroxisomal"},
    "BCL2": {"secreted", "secretory_lumen", "mitochondrial_matrix", "peroxisomal"},
    "KEAP1": {"secreted", "secretory_lumen", "mitochondrial_matrix", "peroxisomal"},
    "BRCA1": {"secreted", "secretory_lumen", "peroxisomal"},
    "KRAS": {"secreted", "secretory_lumen", "mitochondrial_matrix", "peroxisomal"},
    "CDK2": {"secreted", "secretory_lumen", "mitochondrial_matrix", "peroxisomal"},
    "HIF1A": {"secreted", "secretory_lumen", "mitochondrial_matrix", "peroxisomal"},
    "CTNNB1": {"secreted", "secretory_lumen", "mitochondrial_matrix", "peroxisomal"},
    "TNFRSF1A": {"nuclear", "mitochondrial_matrix", "peroxisomal"},
    "BECN1": {"secreted", "secretory_lumen", "mitochondrial_matrix", "peroxisomal"},
}


def unzip_table(path):
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith(".tsv")]
        if len(names) != 1:
            raise RuntimeError("Ambiguous HPA archive")
        return list(csv.DictReader(io.StringIO(archive.read(names[0]).decode()), delimiter="\t"))


def sources(folder):
    hpa_rows = {r["Gene"]: r for r in unzip_table(folder / "hpa_subcellular_location.tsv.zip")}
    mappings = defaultdict(set)
    for row in unzip_table(folder / "hpa_proteinatlas.tsv.zip"):
        for acc in re.split(r"[;, ]+", row["Uniprot"]):
            if acc:
                mappings[acc].add(row["Ensembl"])
    proteins = {}
    with (folder / "reviewed_human_annotations.tsv").open() as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            sequence, genes = row["Sequence"], row["Gene Names (primary)"].split()
            if not genes or len(sequence) < 30 or set(sequence) - ALLOWED:
                continue
            acc = row["Entry"]
            genes_mapped = mappings.get(acc, set())
            hpa = hpa_rows.get(next(iter(genes_mapped)), {}) if len(genes_mapped) == 1 else {}
            if hpa and hpa["Gene name"] != genes[0]:
                # A changed gene name or ambiguous mapping must not silently join.
                hpa = {}
            proteins[acc] = {
                "accession": acc, "gene": genes[0], "length": len(sequence),
                "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
                "transmembrane": bool(row["Transmembrane"]),
                "location_raw": row["Subcellular location [CC]"],
                "location": re.sub(r"\{[^}]*\}", "", row["Subcellular location [CC]"]).lower(),
                "subunit": row["Subunit structure"], "signal_peptide": row["Signal peptide"],
                "topological_domain": row["Topological domain"], "hpa": hpa,
                "hpa_mapping_ensembl": ";".join(sorted(genes_mapped)),
            }
    return proteins


def candidate_evidence(protein):
    """Require affirmative annotation, reject alternative intracellular sites."""
    if protein["transmembrane"]:
        return None
    text = protein["location"]
    annotation = text.split("note=", 1)[0]
    # Search notes too for explicitly stated alternative locations, isoforms,
    # stress release or cleavage products; do not use a missing annotation.
    forbidden = ("cytoplasm", "cytosol", "cell membrane", "nucleus membrane", "nuclear membrane",
                 "cell junction", "synapse", "outer membrane", "intermembrane", "exosome")
    if any(term in text for term in forbidden):
        return None
    nuclear = any(t in text for t in ("nucleus", "nuclear", "chromosome", "nucleol"))
    mitochondrial = "mitochond" in text
    peroxisomal = "peroxisom" in text
    secretory = any(t in text for t in ("secreted", "extracellular", "endoplasmic", "golgi", "lysosom", "vesicle", "endosom"))
    categories = []
    if "mitochondrion matrix" in annotation and not (nuclear or peroxisomal or secretory):
        categories.append("mitochondrial_matrix")
    elif "mitochondrion" in annotation and not (nuclear or peroxisomal or secretory) and "membrane" not in annotation:
        categories.append("mitochondrial")
    if "peroxisome" in annotation and not (nuclear or mitochondrial or secretory) and "membrane" not in annotation:
        categories.append("peroxisomal")
    if nuclear and not (mitochondrial or peroxisomal or secretory):
        categories.append("nuclear")
    if protein["signal_peptide"] and not (nuclear or mitochondrial or peroxisomal):
        if "secreted" in annotation and "membrane" not in annotation:
            categories.append("secreted")
        elif any(t in annotation for t in ("endoplasmic reticulum lumen", "golgi apparatus lumen", "lysosome lumen")):
            categories.append("secretory_lumen")
    if len(categories) != 1:
        return None
    category = categories[0]
    hpa = protein["hpa"]
    observed = {v for key in ("Enhanced", "Supported", "Approved", "Uncertain") for v in hpa.get(key, "").split(";") if v}
    high = {v for key in ("Enhanced", "Supported") for v in hpa.get(key, "").split(";") if v}
    if observed - HPA_ALLOWED[category]:
        return None
    experimental = "ECO:0000269" in protein["location_raw"].split("Note=", 1)[0]
    hpa_supported = bool(high & HPA_ALLOWED[category])
    # Reviewed-only annotation is a disclosed fallback, never experimental evidence.
    quality = 0 if experimental and hpa_supported else 1 if experimental else 2 if hpa_supported else 3
    return {"localization_class": category, "annotation_quality": quality,
            "uniprot_experimental_location": experimental, "hpa_supported_location": hpa_supported,
            "hpa_all_locations": ";".join(sorted(observed)),
            "hpa_high_confidence_locations": ";".join(sorted(high))}


def pair_evidence(target, protein, allow_secondary_overlap):
    evidence = candidate_evidence(protein)
    if evidence is None:
        return None
    category = evidence["localization_class"]
    if category in STRICT_CLASSES[target]:
        tier = "A_compartment_separation"
        rationale = f"Mature {category} protein; target policy excludes this compartment/side."
    elif (allow_secondary_overlap and target == "EGFR" and category in {"mitochondrial_matrix", "mitochondrial", "nuclear"}
          and evidence["hpa_supported_location"] and evidence["uniprot_experimental_location"]):
        tier = "B_secondary_location_overlap"
        rationale = (f"Restricted {category} UniProt annotation with experimental evidence and concordant HPA staining; "
                     "differs from dominant surface/Golgi EGFR location, but documented mitochondrial/nuclear EGFR "
                     "prevents a strict separation claim. This is only a weaker localization-prior candidate.")
    else:
        return None
    return {**evidence, "evidence_tier": tier, "reason": rationale}
