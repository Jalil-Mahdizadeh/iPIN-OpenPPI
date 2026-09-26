"""Pure-standard-library execution freeze and verification for host/SLURM launch."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import ast
import subprocess

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def entries(root,paths):return [{'name':str(p.relative_to(root)),'sha256':sha(p)} for p in sorted(paths)]
def check(condition,message):
    if not condition:raise RuntimeError(message)
def verify():
    value=read(ROOT/'audit/EXECUTION_FREEZE.json')
    for key,base in [('study_code',ROOT/'scripts'),('native_code',REPO/'benchmark/tuna/scripts'),
                     ('upstream_code',REPO/'benchmark/tuna/upstream/TUnA'),('launch_files',ROOT),('data_files',ROOT/'data')]:
        for item in value[key]:check(sha(base/item['name'])==item['sha256'],'Frozen execution changed: '+str(base/item['name']))
    check(sha(REPO/value['container']['path'])==value['container']['sha256'],'Container changed')
    for item in value['required_manifests']:
        check(sha(ROOT/item['path'])==item['sha256'],'Required manifest changed: '+item['path'])
    return value
def freeze():
    check(not (ROOT/'audit/EXECUTION_FREEZE.json').exists(),'Execution already frozen')
    for path in (ROOT/'scripts').glob('*.py'):ast.parse(path.read_text(),filename=str(path))
    for path in [*ROOT.glob('*.sh'),*ROOT.glob('*.sbatch')]:subprocess.run(['bash','-n',str(path)],check=True)
    for path in [ROOT/'audit/CORPUS_VALIDATION.json',ROOT/'runs/QUALIFICATION.json',ROOT/'runs/MACRO_METRIC_QUALIFICATION.json']:
        check(read(path)['passed'],'Qualification failed: '+str(path))
    cache=read(ROOT/'runs/residue_cache/RESIDUE_CACHE_MANIFEST.json')
    check(sha(ROOT/'runs/residue_cache/residues.h5')==cache['cache']['sha256'],'Cache changed after qualification')
    for item in read(ROOT/'audit/PARENT_SNAPSHOT.json')['files']:
        check(sha(REPO/item['path'])==item['sha256'],'Historical parent changed')
    candidates=entries(ROOT/'private/candidates',(ROOT/'private/candidates').glob('*.npz'))
    with (ROOT/'audit/CANDIDATE_FREEZE.json').open('x') as f:
        json.dump({'files':candidates,'labels_in_candidates':False},f,indent=2);f.write('\n')
    manifests=['audit/CORPUS_FREEZE.json','audit/CORPUS_VALIDATION.json','audit/CANDIDATE_FREEZE.json',
      'runs/QUALIFICATION.json','runs/MACRO_METRIC_QUALIFICATION.json','runs/POOLED_FEATURE_MANIFEST.json',
      'runs/residue_cache/RESIDUE_CACHE_MANIFEST.json']
    image='benchmark/containers/images/tuna-arm64-v1.sif'; image_sha=sha(REPO/image)
    check(image_sha=='98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1','Unqualified runtime')
    value={'at_utc':datetime.now(timezone.utc).isoformat(),'authorized_to_train':True,
      'study_code':entries(ROOT/'scripts',(ROOT/'scripts').glob('*.py')),
      'native_code':entries(REPO/'benchmark/tuna/scripts',(REPO/'benchmark/tuna/scripts').glob('*.py')),
      'upstream_code':entries(REPO/'benchmark/tuna/upstream/TUnA',(REPO/'benchmark/tuna/upstream/TUnA').rglob('*.py')),
      'launch_files':entries(ROOT,[*ROOT.glob('*.sh'),*ROOT.glob('*.sbatch')]),
      'data_files':entries(ROOT/'data',[p for p in (ROOT/'data').rglob('*') if p.is_file()]),
      'required_manifests':[{'path':s,'sha256':sha(ROOT/s)} for s in manifests],
      'residue_manifest_sha256':sha(ROOT/'runs/residue_cache/RESIDUE_CACHE_MANIFEST.json'),
      'qualification_sha256':sha(ROOT/'runs/QUALIFICATION.json'),
      'container':{'path':image,'sha256':image_sha},
      'historical_files_modified':False,'test_truth_mounted_in_training':False,
      'protocol_sha256':sha(ROOT/'data/PROTOCOL.json')}
    with (ROOT/'audit/EXECUTION_FREEZE.json').open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    verify();print('Execution frozen and verified',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','verify']);args=p.parse_args()
    if args.action=='freeze':freeze()
    else:verify();print('Execution verified',flush=True)
