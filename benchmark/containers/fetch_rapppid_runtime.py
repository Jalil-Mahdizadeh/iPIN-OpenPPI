"""Pin and verify Python runtime artifacts; no dependencies installed on host."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parent
PACKAGES = {'pytorch-lightning':'1.3.8', 'torchmetrics':'0.4.1', 'pyDeprecate':'0.3.0',
            'sentencepiece':'0.2.1', 'tables':'3.10.2', 'blosc2':'2.7.1',
            'ranger21':'0.1.0', 'passlib':'1.7.4', 'fire':'0.5.0', 'future':'0.18.3',
            'numexpr':'2.11.0', 'ndindex':'1.10.0', 'msgpack':'1.1.1',
            'py-cpuinfo':'9.0.0', 'termcolor':'2.2.0'}


def fetch(item):
    name, version = item
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json', timeout=60) as response:
        metadata = json.load(response)
    compatible = []
    for asset in metadata['urls']:
        filename = asset['filename']
        if filename.endswith('none-any.whl') or (filename.endswith('.whl') and 'aarch64' in filename and 'manylinux' in filename
                and ('cp312' in filename or re.search(r'-cp3(?:8|9|10|11)-abi3-', filename))):
            compatible.append(asset)
    if not compatible:
        compatible = [x for x in metadata['urls'] if x['packagetype'] == 'sdist']
    assert compatible, (name, version)
    asset = sorted(compatible, key=lambda x:x['filename'])[0]
    path = ROOT / 'cache/rapppid-wheels' / asset['filename']
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        content = path.read_bytes()
    else:
        with urllib.request.urlopen(asset['url'], timeout=90) as response:
            content = response.read()
        assert hashlib.sha256(content).hexdigest() == asset['digests']['sha256']
        with path.open('xb') as handle:
            handle.write(content)
    assert hashlib.sha256(content).hexdigest() == asset['digests']['sha256']
    print('verified runtime', asset['filename'], flush=True)
    return {'package': name, 'version': version, 'filename': asset['filename'], 'url': asset['url'],
            'bytes': len(content), 'sha256': asset['digests']['sha256']}


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(fetch, PACKAGES.items()))
    document = {'packages': PACKAGES, 'artifacts': files, 'platform':'aarch64 CPython3.12',
                'torch_numpy_cuda':'Unchanged immutable iPIN ARM64 parent',
                'compatibility_note':'Native Lightning1.3.8 and metrics0.4.1; ARM64-compatible SentencePiece/PyTables; numerical qualification required'}
    destination = ROOT / 'manifests/rapppid-runtime-downloads.json'
    if destination.exists():
        assert json.loads(destination.read_text()) == document
    else:
        with destination.open('x') as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write('\n')


if __name__ == '__main__':
    main()
