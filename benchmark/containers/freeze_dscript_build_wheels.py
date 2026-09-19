#!/usr/bin/env python3
"""Validate resolved build wheels against PyPI and save a hashed offline lock."""
import hashlib
import json
from email.parser import BytesParser
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

root = Path(__file__).resolve().parent
records = []
for path in sorted((root / "cache/dscript-build-wheels").glob("*.whl")):
    with ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = BytesParser().parsebytes(archive.read(name))
    package, version = metadata["Name"], metadata["Version"]
    with urlopen(f"https://pypi.org/pypi/{package}/{version}/json", timeout=30) as response:
        release = json.load(response)
    artifact = next(a for a in release["urls"] if a["filename"] == path.name)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != artifact["digests"]["sha256"]:
        raise RuntimeError(f"Build wheel checksum mismatch: {path.name}")
    records.append({"package": package, "version": version, "filename": path.name,
                    "sha256": digest, "url": artifact["url"]})
manifest = root / "manifests/dscript-build-wheels.json"
if manifest.exists():
    if json.loads(manifest.read_text()) != records:
        raise RuntimeError("Build wheel set changed; use a new image version")
else:
    with manifest.open("x") as handle:
        json.dump(records, handle, indent=2)
        handle.write("\n")
lock = root / "manifests/dscript-build-requirements.lock"
content = "".join(f"{r['package']}=={r['version']} --hash=sha256:{r['sha256']}\n" for r in records)
if lock.exists():
    if lock.read_text() != content:
        raise RuntimeError("Existing build lock differs")
else:
    with lock.open("x") as handle:
        handle.write(content)
print(json.dumps({"verified_build_wheels": len(records)}))
