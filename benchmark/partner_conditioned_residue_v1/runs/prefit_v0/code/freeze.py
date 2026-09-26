"""Host-side prospective execution snapshot and immutable-input verification."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SIF_SHA = '98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['record', 'verify'])
    args = parser.parse_args()
    run = ROOT / 'runs'; target = run / 'TRAINING_FREEZE.json'
    if args.mode == 'record':
        if target.exists() or (run / 'code').exists():
            raise RuntimeError('Execution snapshot already exists')
        for name in ('QUALIFICATION.json', 'REAL_QUALIFICATION.json', 'PIPELINE_QUALIFICATION.json'):
            if not read(run / name)['passed']:
                raise RuntimeError('Qualification did not pass')
        config = read(ROOT / 'config.json')
        previous = read(ROOT.parent / 'tuna/runs/scorer_bundle/SELECTION.json')
        reference = next(x['C3_development_concordance'] for x in previous['candidates'] if x['epoch'] == previous['selected_epoch'])
        if config['promotion_reference_C3_development'] != reference:
            raise RuntimeError('PU-TUnA development reference drift')
        image = ROOT.parent / 'containers/images/tuna-arm64-v1.sif'
        if sha(image) != SIF_SHA:
            raise RuntimeError('Pinned runtime image drift')
        (run / 'code').mkdir()
        for source in sorted((ROOT / 'scripts').glob('*.py')):
            shutil.copyfile(source, run / 'code' / source.name)
        code_files = [{'path': p.name, 'sha256': sha(p)} for p in sorted((run / 'code').glob('*.py'))]
        paths = sorted((ROOT / 'scripts').glob('*.py')) + sorted(ROOT.glob('*.sh')) + sorted(ROOT.glob('*.sbatch'))
        paths += [ROOT / 'config.json', ROOT / 'PROTOCOL.md']
        project = ROOT.parent.parent
        reference_paths = {
            'baseline_freeze.json': project / '.private/protected_final_test_v1/freeze/PREDICTION_FREEZE.json',
            'optimized_freeze.json': project / '.private/model_optimization_followup_v1/freeze/PREDICTION_FREEZE.json',
            'tuna_predictions_manifest.json': ROOT.parent / 'tuna/private/predictions/PREDICTIONS.json',
            'historical_results.json': project / '.private/model_optimization_followup_v1/evaluation/FOLLOWUP_TEST_RESULTS.json',
            'historical_tuna_results.json': ROOT.parent / 'tuna/results/RESULTS.json',
            'historical_scorer_freeze.json': project / '.private/model_optimization_followup_v1/bundle/SCORER_FREEZE.json'}
        value = {'at_utc': datetime.now(timezone.utc).isoformat(), 'study_id': config['study_id'],
                 'authorized_to_train': True,
                 'authorization': 'User requested new models, development-selected C1/C2/C3 comparison, and interactive or SLURM GPU execution on 2026-09-24.',
                 'configuration': config, 'config_sha256': sha(ROOT / 'config.json'),
                 'data_manifest_sha256': sha(run / 'data/DATA_MANIFEST.json'),
                 'residue_manifest_sha256': sha(ROOT.parent / 'tuna/runs/residue_cache/RESIDUE_CACHE_MANIFEST.json'),
                 'runtime_sif_sha256': SIF_SHA,
                 'PU_TUnA_development_selection_sha256': sha(ROOT.parent / 'tuna/runs/scorer_bundle/SELECTION.json'),
                 'code_files': code_files,
                 'reference_input_hashes': {name: sha(path) for name, path in reference_paths.items()},
                 'host_files': [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p)} for p in paths],
                 'qualification_files': [{'path': name, 'sha256': sha(run / name)} for name in
                      ('QUALIFICATION.json', 'REAL_QUALIFICATION.json', 'PIPELINE_QUALIFICATION.json')],
                 'formal_training_started': False, 'test_pairs_read': False, 'test_truth_read': False,
                 'preparation': read(run / 'data/DATA_MANIFEST.json'),
                 'test_panels_previously_examined': True}
        with target.open('x') as handle:
            json.dump(value, handle, indent=2, sort_keys=True); handle.write('\n')
        for path in (run / 'code').glob('*.py'):
            path.chmod(0o444)
        target.chmod(0o444)
    value = read(target)
    for item in value['host_files']:
        if sha(ROOT / item['path']) != item['sha256']:
            raise RuntimeError(f"Frozen host code/configuration changed: {item['path']}")
    for item in value['code_files']:
        if sha(run / 'code' / item['path']) != item['sha256']:
            raise RuntimeError(f"Frozen worker code changed: {item['path']}")
    print(json.dumps({'passed': True, 'mode': args.mode, 'training_freeze_sha256': sha(target)}))


if __name__ == '__main__':
    main()
