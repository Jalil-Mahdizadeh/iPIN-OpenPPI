"""Paths, integrity checks and qualified implementation loading for this study."""
import csv
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from prepare import OUT, ROOT, record, require, sha, verify, write_csv, write_json

LOCAL = OUT / "local"
MODELS = ("ipin_baseline", "ipin_optimized", "tuna_retrained")
MODEL_NAMES = {"ipin_baseline": "Baseline iPIN", "ipin_optimized": "Optimized iPIN", "tuna_retrained": "TUnA retrained"}
REGISTRY_SHA = "faf2d585dbfee34ca3fe19487bc7a821f744014cdcdb94e95e4b657097110878"


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def table(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def boolean(value):
    require(str(value).lower() in {"true", "false"}, "Invalid Boolean field")
    return str(value).lower() == "true"


def container():
    require(bool(os.environ.get("APPTAINER_CONTAINER")), "Use a pinned accepted Apptainer image")


def qualified_module(name):
    folder = ROOT / "benchmark/nonhuman_transfer_v1"
    sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location("qualified_reference_" + name, folder / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT, module.LOCAL = OUT, LOCAL
    module.CONFIG = {"species": [{"id": "human_yeast_reference"}], "model_registry_sha256": REGISTRY_SHA}
    return module


def check_selection():
    validation = read(OUT / "COMPARISON_VALIDATION.json")
    require(validation["status"] == "passed", "Comparison validation missing")
    verify(validation["selection"])
    selection = read(OUT / "PANEL_SELECTION.json")
    for item in selection["outputs"]:
        verify(item)
    rows = table(OUT / "panels.csv")
    require(all(r["query_taxid"] == "559292" and r["partner_taxid"] == "9606" and r["label"] == "P"
                for r in rows), "Only published human/S288C pairs are eligible")
    return rows
