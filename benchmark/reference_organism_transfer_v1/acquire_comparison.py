"""Archive the primary paper and its published comparison-data supplements."""
import hashlib
import json
import os
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
LOCAL = OUT / "local"
API = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4848758/"


def main():
    if not os.environ.get("APPTAINER_CONTAINER"):
        raise RuntimeError("Use the accepted data image")
    if (OUT / "COMPARISON_SOURCES.json").exists():
        raise RuntimeError("Refusing to overwrite source acquisition")
    LOCAL.mkdir(exist_ok=True)
    records = []
    for endpoint, name in (("fullTextXML", "PMC4848758.xml"),
                           ("supplementaryFiles", "PMC4848758_supplements.zip")):
        path = LOCAL / name
        if path.exists():
            raise RuntimeError(f"Refusing to replace {path}")
        url = API + endpoint
        with urllib.request.urlopen(url, timeout=45) as response:
            data = response.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024:
                raise RuntimeError("Unexpectedly large publication download")
            headers = {k: response.headers[k] for k in ("Content-Type", "Last-Modified", "ETag") if k in response.headers}
            final_url = response.url
        with path.open("xb") as handle:
            handle.write(data)
        if endpoint == "supplementaryFiles" and not zipfile.is_zipfile(path):
            raise RuntimeError("Supplement response is not a ZIP archive")
        records.append({"url": url, "resolved_url": final_url, "response_headers": headers,
                        "path": str(path.relative_to(ROOT)), "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
        print(f"Archived {name}: {len(data):,} bytes", flush=True)
    result = {"at_utc": datetime.now(timezone.utc).isoformat(), "pmid": "27107014",
              "pmcid": "PMC4848758", "sources": records,
              "source": "Europe PMC public article REST API",
              "api_documentation": "https://europepmc.org/RestfulWebService",
              "model_scores_read": False}
    with (OUT / "COMPARISON_SOURCES.json").open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
