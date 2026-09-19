#!/usr/bin/env python3
"""Download exact PyPI artifacts and verify their registry-provided SHA-256."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

root = Path(__file__).resolve().parent
dest = root / 'cache/tuna-wheels'
dest.mkdir(parents=True, exist_ok=True)
records = []
for package, version, kind in [('fair-esm','2.0.0','any'), ('uncertainty-calibration','0.1.4','sdist'), ('h5py','3.14.0','arm')]:
    with urlopen(f'https://pypi.org/pypi/{package}/{version}/json', timeout=30) as response:
        metadata = json.load(response)
    choices = [u for u in metadata['urls'] if
               (kind == 'any' and u['filename'].endswith('py3-none-any.whl')) or
               (kind == 'sdist' and u['packagetype'] == 'sdist') or
               (kind == 'arm' and 'cp312-cp312' in u['filename'] and 'aarch64' in u['filename'] and 'manylinux' in u['filename'])]
    if len(choices) != 1:
        raise RuntimeError(f'Expected one platform artifact for {package}: {[x["filename"] for x in choices]}')
    item = choices[0]
    target = dest / item['filename']
    if not target.exists():
        with urlopen(item['url'], timeout=60) as source, target.open('xb') as output:
            for block in iter(lambda: source.read(8 << 20), b''):
                output.write(block)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if digest != item['digests']['sha256']:
        raise RuntimeError(f'Package checksum mismatch: {package}')
    records.append({'package':package,'version':version,'filename':target.name,'sha256':digest,'url':item['url']})
manifest = root / 'manifests/tuna-pypi-artifacts.json'
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps(records, indent=2)+'\n')
print(json.dumps({'verified_dependencies':len(records)}))
