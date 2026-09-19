#!/usr/bin/env python3
"""Host-side code freeze/verification; only benchmark files are written."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'runs/EXECUTION_CODE_FREEZE.json'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):
            h.update(block)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['record','verify']); mode=parser.parse_args().mode
    if mode=='record':
        for name in ['QUALIFICATION.json','REAL_QUALIFICATION.json','GUARDED_QUALIFICATION.json','METRIC_QUALIFICATION.json','PIPELINE_QUALIFICATION.json']:
            if not json.loads((ROOT/'runs'/name).read_text())['passed']:
                raise RuntimeError('Qualification failed or missing')
        paths=sorted(list((ROOT/'scripts').glob('*.py'))+list(ROOT.glob('*.sh'))+list(ROOT.glob('*.sbatch')))
        payload={'at_utc':datetime.now(timezone.utc).isoformat(),'test_pairs_read':False,'test_truth_read':False,
            'files':[{'path':str(p.relative_to(ROOT)),'sha256':digest(p)} for p in paths],
            'training_freeze_sha256':digest(ROOT/'runs/TRAINING_FREEZE.json')}
        with TARGET.open('x') as f:
            json.dump(payload,f,sort_keys=True,indent=2); f.write('\n')
    else:
        payload=json.loads(TARGET.read_text())
        if any(digest(ROOT/item['path'])!=item['sha256'] for item in payload['files']):
            raise RuntimeError('Code changed after execution freeze: final test is blocked')
        if digest(ROOT/'runs/TRAINING_FREEZE.json')!=payload['training_freeze_sha256']:
            raise RuntimeError('Training recipe changed')
    print({'mode':mode,'passed':True,'files':len(payload['files']),'execution_freeze_sha256':digest(TARGET)})

if __name__=='__main__':
    main()
