"""Verify the training-only execution freeze without opening test data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'runs/retrained-v1'
SHELL_FILES = ('run_retrained_setup.sh', 'run_retrained_worker.sh',
               'report_retrained_development.sh', 'retrained_train.sbatch', 'submit_retrained.sh')
ORIGINAL_RECORDS = ('runs/original-v1/scorer_bundle/SCORER_FREEZE.json',
                    'runs/original-v1/RUN_COMPLETE.json',
                    'private/original-v1/predictions/PREDICTIONS.json',
                    'results/original-v1/RESULTS.json')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def record(path, root):
    return {'path': str(path.relative_to(root)), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def verify(root, records):
    for item in records:
        relative = Path(item['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        path = root / relative
        assert path.is_file() and not path.is_symlink(), path
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('record', 'verify'))
    args = parser.parse_args()
    target = RUN / 'EXECUTION_CODE_FREEZE.json'
    protocol = read(RUN / 'TRAINING_FREEZE.json')
    assert protocol['epochs'] == 20 and protocol['evaluation_epochs'] == [4, 8, 12, 16, 20]
    assert not protocol['test_evaluation_authorized'] and not protocol['test_evaluation_scheduled']
    if args.mode == 'record':
        paths = sorted((ROOT / 'scripts/retrained_v1').glob('*.py')) + [ROOT / p for p in SHELL_FILES]
        value = {'at_utc': datetime.now(timezone.utc).isoformat(),
                 'training_freeze_sha256': sha(RUN / 'TRAINING_FREEZE.json'),
                 'files': [record(p, ROOT) for p in paths],
                 'original_read_only_records': [record(ROOT / p, ROOT) for p in ORIGINAL_RECORDS]}
        with target.open('x') as handle:
            json.dump(value, handle, indent=2)
            handle.write('\n')
    value = read(target)
    assert value['training_freeze_sha256'] == sha(RUN / 'TRAINING_FREEZE.json')
    verify(ROOT, value['files'])
    verify(ROOT, value['original_read_only_records'])
    verify(RUN / 'code', protocol['code_files'])
    assert sha(RUN / 'data/DATA_MANIFEST.json') == protocol['data_manifest_sha256']
    verify(RUN / 'data', read(RUN / 'data/DATA_MANIFEST.json')['files'])
    assert sha(RUN / 'QUALIFICATION.json') == protocol['qualification_sha256']
    assert sha(RUN / 'data/spm.model') == protocol['tokenizer_sha256']
    assert sha(ROOT.parent / 'containers/images/rapppid-native-arm64-v1.sif') == protocol['sif_sha256']
    print(json.dumps({'at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True, 'mode': args.mode,
                      'training_freeze_sha256': value['training_freeze_sha256'],
                      'execution_freeze_sha256': sha(target), 'test_evaluation_scheduled': False}), flush=True)


if __name__ == '__main__':
    main()
