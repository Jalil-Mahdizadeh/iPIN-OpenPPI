"""Read-only launch verification; record only this candidate's execution freeze."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/retrained-v1'
SHELL_FILES=('run_retrained_setup.sh','retrained_cache.sbatch','retrained_train.sbatch','run_retrained_worker.sh',
             'retrained_prepare.sbatch','prepare_retrained_test.sh','retrained_test.sbatch','score_retrained_worker.sh',
             'finish_retrained.sh','submit_retrained.sh')


def read(path):return json.loads(path.read_text())


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(8<<20),b''):digest.update(block)
    return digest.hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('record','verify'));parser.add_argument('--cache',action='store_true')
    args=parser.parse_args();target=RUN/'EXECUTION_CODE_FREEZE.json';protocol=read(RUN/'TRAINING_FREEZE.json')
    if args.mode=='record':
        paths=sorted((ROOT/'scripts/retrained_v1').glob('*.py'))+[ROOT/name for name in SHELL_FILES]
        value={'at_utc':datetime.now(timezone.utc).isoformat(),'training_freeze_sha256':sha(RUN/'TRAINING_FREEZE.json'),
               'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in paths]}
        with target.open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n')
    value=read(target);assert value['training_freeze_sha256']==sha(RUN/'TRAINING_FREEZE.json')
    for item in value['files']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    for item in protocol['code_files']:assert sha(RUN/'code'/item['path'])==item['sha256']
    assert sha(RUN/'data/DATA_MANIFEST.json')==protocol['data_manifest_sha256']
    for item in read(RUN/'data/DATA_MANIFEST.json')['files']:assert sha(RUN/'data'/item['path'])==item['sha256']
    assert sha(ROOT.parent/'containers/images/dscript-native-arm64-v1.sif')==protocol['sif_sha256']
    assert sha(ROOT/'private/original-v1/predictions/PREDICTIONS.json')==protocol['original_predictions_manifest_sha256']
    assert sha(ROOT/'results/original-v1/RESULTS.json')==protocol['original_results_sha256']
    assert sha(RUN/'residue_cache/CACHE.json')==protocol['cache_manifest_sha256']
    if args.cache:
        print('Verifying full native residue cache before workers launch...',flush=True)
        for item in read(RUN/'residue_cache/CACHE.json')['files']:
            path=RUN/'residue_cache'/item['path'];assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256']
    print(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'mode':args.mode,'cache_bytes_verified':args.cache,
                      'training_freeze_sha256':value['training_freeze_sha256'],'execution_freeze_sha256':sha(target)}),flush=True)


if __name__=='__main__':main()
