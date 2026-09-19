#!/usr/bin/env python3
"""Fetch pinned original-model assets and ARM64 wheels into benchmark only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT.parent / 'plm_interact'
COMMIT = 'ab2ae6ae1aa81accf4c1f7f6f341164baf97809a'
MODEL = 'danliu1226/PLM-interact-650M-humanV11'
REVISION = 'e86e392dec13dd0c23252c94947b04a7a9821b0e'
BASE = 'facebook/esm2_t33_650M_UR50D'
BASE_REVISION = '08e4846e537177426273712802403f7ba8261b6c'
CHECKPOINT_SHA = '68c50e1dc84ee3cb6c08a7c83eefb382a29a3c1237fd577986854f746c63d665'
PACKAGES = {'PLMinteract':'0.1.1', 'transformers':'4.40.1', 'tokenizers':'0.19.1',
            'sentence-transformers':'2.7.0', 'datasets':'2.20.0', 'dill':'0.3.8',
            'multiprocess':'0.70.16', 'fsspec':'2024.5.0', 'pyarrow-hotfix':'0.7',
            'xxhash':'3.5.0', 'biopython':'1.85', 'seaborn':'0.13.2'}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'iPIN-PLM-interact-benchmark'}), timeout=90)

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(8<<20),b''): digest.update(block)
    return digest.hexdigest()

def fetch(url, path, expected=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if expected and sha(path) != expected: raise RuntimeError(f'Existing asset differs: {path}')
    else:
        temporary = path.with_name(path.name + '.partial')
        with get(url) as source, temporary.open('wb') as target:
            total = 0
            while block := source.read(8<<20):
                target.write(block); total += len(block)
                if total % (256<<20) == 0: print({'download':path.name,'bytes':total}, flush=True)
        if expected and sha(temporary) != expected: raise RuntimeError(f'Download hash differs: {path}')
        temporary.replace(path)
    record = {'path':str(path.relative_to(ROOT.parent)), 'url':url, 'bytes':path.stat().st_size, 'sha256':sha(path)}
    print({'download_verified':record['path'],'bytes':record['bytes']}, flush=True)
    return record

def wheel(item):
    name, version = item
    with get(f'https://pypi.org/pypi/{name}/{version}/json') as response: metadata=json.load(response)
    compatible=[]
    for asset in metadata['urls']:
        filename=asset['filename']
        if filename.endswith('none-any.whl') or (filename.endswith('.whl') and 'aarch64' in filename and 'manylinux' in filename and ('cp312' in filename or '-cp38-abi3-' in filename)):
            compatible.append(asset)
    if not compatible: raise RuntimeError(f'No ARM64/Python3.12 wheel for {name}=={version}')
    asset=sorted(compatible,key=lambda x:x['filename'])[0]
    return fetch(asset['url'],ROOT/'cache/plm-interact-wheels'/asset['filename'],asset['digests']['sha256'])

def main():
    records=[]
    with ThreadPoolExecutor(max_workers=4) as pool: records.extend(pool.map(wheel,PACKAGES.items()))
    for name in ('README.md','LICENSE','pyproject.toml','PLMinteract/train_mlm.py','PLMinteract/inference/inference_PPI_singleGPU.py'):
        records.append(fetch(f'https://raw.githubusercontent.com/liudan111/PLM-interact/{COMMIT}/{name}',CANDIDATE/'upstream'/name))
    for name in ('config.json','special_tokens_map.json','tokenizer_config.json','vocab.txt'):
        records.append(fetch(f'https://huggingface.co/{BASE}/resolve/{BASE_REVISION}/{name}',CANDIDATE/'assets/esm2_650m'/name))
    for name in ('README.md','config.json','special_tokens_map.json','tokenizer_config.json','vocab.txt'):
        records.append(fetch(f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}',CANDIDATE/'assets/humanV11'/name))
    records.append(fetch(f'https://huggingface.co/{MODEL}/resolve/{REVISION}/pytorch_model.bin?download=true',CANDIDATE/'assets/humanV11/pytorch_model.bin',CHECKPOINT_SHA))
    document={'at_utc':datetime.now(timezone.utc).isoformat(),'upstream_commit':COMMIT,'model':MODEL,'revision':REVISION,
              'base_model':BASE,'base_revision':BASE_REVISION,'checkpoint_sha256':CHECKPOINT_SHA,'packages':PACKAGES,'files':records,
              'retraining':False,'test_pairs_read':False,'test_truth_read':False}
    destination=ROOT/'manifests/plm-interact-downloads.json';destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        old=json.loads(destination.read_text())
        if old['files']!=document['files']:raise RuntimeError('Existing download manifest differs')
    else:destination.write_text(json.dumps(document,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
