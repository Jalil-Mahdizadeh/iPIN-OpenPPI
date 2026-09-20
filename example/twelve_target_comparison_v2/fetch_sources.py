#!/usr/bin/env python3
"""Retrieve annotation sources only; never read model scores or features."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "twelve_target_comparison_v1"))
from build_panels import download


def main():
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Use the accepted data SIF")
    fields = "accession,gene_primary,length,cc_subcellular_location,ft_transmem,sequence,cc_subunit,protein_existence,xref_ensembl,ft_topo_dom,ft_signal,cc_tissue_specificity"
    url = "https://rest.uniprot.org/uniprotkb/stream?" + urlencode({
        "query": "reviewed:true AND organism_id:9606 AND existence:1", "format": "tsv", "fields": fields})
    jobs = [(url, "reviewed_human_annotations.tsv"),
            ("https://www.proteinatlas.org/download/tsv/subcellular_location.tsv.zip", "hpa_subcellular_location.tsv.zip"),
            ("https://www.proteinatlas.org/download/proteinatlas.tsv.zip", "hpa_proteinatlas.tsv.zip"),
            ("https://www.proteinatlas.org/humanproteome/subcellular/data", "hpa_subcellular_data.html")]
    for manifest in sorted(HERE.parent.glob("*/panel_manifest.json")):
        accession = json.loads(manifest.read_text())["target"]["accession"]
        jobs.append((f"https://rest.uniprot.org/uniprotkb/{accession}.json", f"uniprot_{accession}.json"))
    def fetch(job):
        body, meta = download(job[0], HERE / "sources" / job[1])
        print(job[1], len(body), meta["sha256"], flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, jobs))


if __name__ == "__main__":
    main()
