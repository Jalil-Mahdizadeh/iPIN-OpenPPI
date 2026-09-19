#!/usr/bin/env python3
"""Fetch verified native D-SCRIPT artifacts, entirely inside benchmark/."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

CONTAINERS = Path(__file__).resolve().parent
CANDIDATE = CONTAINERS.parent / "dscript"
HF_REVISION = "907ea0b745b1a555b19f2b3e73f2d98963caf365"
MODEL_HASHES = {
    "lm_v1": "b91f32fcd7d68460ca3c3e3bd2396c1f5826a333ad4ad4962b7f4ab3a410b17c",
    "human_v1": "9fc07ac14bb218a8b65288a9114b0c934e8f9c426a53274b0119ea2336b2a32a",
}
HF_HASHES = {
    "config.json": "bba3058e2231703dfaae25d8195e14993b8d8f064e8de79d52371465bd79e5b5",
    "model.safetensors": "9933c0628a86ea574ce5bb5af33995b7f00e0be1a63ab626caf0bad245e25378",
    "README.md": "45bc25cecc3b749773abd8d41fd811581d5325e32a3ab4c1232a74bfad6d5bb8",
}
PACKAGES = [
    ("dscript", "0.3.1", "any", "c1182f68da2af165dffeae3da062745d8bfd88a19a10cb011f9fdcdd1a2b320b"),
    ("h5py", "3.14.0", "arm", "554ef0ced3571366d4d383427c00c966c360e178b5fb5ee5bb31a435c424db0c"),
    ("loguru", "0.7.3", "any", "31a33c10c8e1e10422bfd431aeb5d351c7cf7fa671e3c4df004162264b28220c"),
    ("seaborn", "0.13.2", "any", "636f8336facf092165e27924f223d3c62ca560b1f2bb5dff7ab7fad265361987"),
    ("packaging", "24.2", "any", "09abb1bccd265c01f4a3aa3f7a7db064b36514d2cba19a2f694fe6150451a759"),
    ("biotite", "1.2.0", "sdist", "8b36dd708a976db10f629ffc8f81a236a74268a4e65e1f576610331d67dab392"),
    ("biotraj", "1.2.2", "sdist", "4bcba92101ed50f369cc1487fb5dfcfe1d8402ad47adaa9232b080553271663a"),
]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url, target, expected=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    final_url = url
    if not target.exists():
        partial = target.with_name(target.name + ".part")
        with urlopen(url, timeout=60) as source, partial.open("xb") as output:
            final_url = source.url
            for block in iter(lambda: source.read(8 << 20), b""):
                output.write(block)
        digest = sha256(partial)
        if expected and digest != expected:
            raise RuntimeError(f"Checksum mismatch: {partial}")
        partial.rename(target)
    digest = sha256(target)
    if expected and digest != expected:
        raise RuntimeError(f"Checksum mismatch: {target}")
    print(f"Verified {target.name}: {digest}", flush=True)
    return {"path": str(target.relative_to(CONTAINERS.parent)), "url": url,
            "resolved_url": final_url, "bytes": target.stat().st_size, "sha256": digest}


def package(spec):
    name, version, kind, expected = spec
    with urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=30) as response:
        metadata = json.load(response)
    choices = [a for a in metadata["urls"] if
               (kind == "any" and a["filename"].endswith("py3-none-any.whl")) or
               (kind == "sdist" and a["packagetype"] == "sdist") or
               (kind == "arm" and "cp312-cp312" in a["filename"] and
                "manylinux" in a["filename"] and "aarch64" in a["filename"])]
    if len(choices) != 1 or choices[0]["digests"]["sha256"] != expected:
        raise RuntimeError(f"Unexpected PyPI artifact: {name} {version}")
    artifact = choices[0]
    record = download(artifact["url"], CONTAINERS / "cache/dscript-wheels" / artifact["filename"], expected)
    record.update(package=name, version=version, verification="Pinned PyPI SHA-256")
    return record


def main():
    manifest = CONTAINERS / "manifests/dscript-downloads.json"
    old = json.loads(manifest.read_text()) if manifest.exists() else {"artifacts": []}
    hashes = {a["path"]: a["sha256"] for a in old["artifacts"]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        records = list(pool.map(package, PACKAGES))
    for name in ("lm_v1", "human_v1"):
        target = CANDIDATE / f"weights/dscript_{name}.pt"
        url = f"https://cb.csail.mit.edu/cb/dscript/data/models/dscript_{name}.pt"
        record = download(url, target, MODEL_HASHES[name])
        record["verification"] = "Official HTTPS download; locally recorded SHA-256 (no upstream checksum supplied)"
        records.append(record)
    for name in ("config.json", "model.safetensors", "README.md"):
        target = CANDIDATE / "weights/human_v1_hf" / name
        url = f"https://huggingface.co/samsl/dscript_human_v1/resolve/{HF_REVISION}/{name}"
        record = download(url, target, HF_HASHES[name])
        record["verification"] = f"Official Hugging Face revision {HF_REVISION}; locally recorded SHA-256"
        records.append(record)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    content = {"dscript_version": "0.3.1", "release_tag_commit": "0b3f7363b7d62fb99f5c8bfc6780833f088b8d84",
               "hf_revision": HF_REVISION, "artifacts": records}
    # Preserve first-download URLs/provenance and prevent silent replacement.
    if manifest.exists():
        if {a["path"]: a["sha256"] for a in records} != hashes:
            raise RuntimeError("Artifacts differ from the existing download manifest")
    else:
        with manifest.open("x") as handle:
            json.dump(content, handle, indent=2)
            handle.write("\n")


if __name__ == "__main__":
    main()
