"""Read-only preflight: reject scorer/image drift before scheduling or opening."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BENCH=ROOT.parent

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()

def main():
    bundle=ROOT/'runs/original-v1/scorer_bundle'
    manifest=json.loads((bundle/'SCORER_FREEZE.json').read_text())
    assert manifest['original_model']=='danliu1226/PLM-interact-650M-humanV11'
    assert not manifest['training_performed'] and not manifest['test_pairs_read'] and not manifest['test_truth_read']
    assert manifest['maximum_tokens']==1603 and manifest['workers']==4
    for item in manifest['files']:
        relative=Path(item['path']);assert not relative.is_absolute() and '..' not in relative.parts
        p=bundle/relative
        assert not p.is_symlink() and p.is_file() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256']
    assert sha(BENCH/'containers/images/plm-interact-native-arm64-v1.sif')==manifest['sif_sha256']
    print('Frozen original PLM-interact code, sequences and image verified',flush=True)

if __name__=='__main__':main()
