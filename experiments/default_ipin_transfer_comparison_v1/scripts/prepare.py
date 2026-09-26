"""Bind both historical panels, the registered default, and this experiment."""
from pathlib import Path
import subprocess
from transfer_io import *


def main():
    require(not (OUT / 'INPUT_FREEZE.json').exists(), 'Already frozen')
    registry = read(REGISTRY)
    require(registry['default_model'] == registry['primary_model'] == 'ipin_tuna_31k_ensemble', 'Unexpected default')
    model = registry['models'][registry['default_model']]
    require(model['training_positive_pairs'] == 31188 and model['selected_epoch'] == 1, 'Unexpected model selection')
    records = {}

    def add(path, expected=None):
        item = record(path)
        key = (item['scope'], item['path'])
        if key in records:
            item = records[key]
        else:
            records[key] = item
        if expected:
            require(item['sha256'] == expected['sha256'], 'Historical checksum mismatch: ' + str(path))
            require('bytes' not in expected or item['bytes'] == expected['bytes'], 'Historical size mismatch: ' + str(path))
        return item

    panels = {}
    for study in STUDIES:
        folder = ROOT / 'benchmark' / study
        manifest = read(folder / 'FINAL_MANIFEST.json')
        for item in manifest.get('outputs', manifest.get('files')):
            add(ROOT / item['path'], item)
        # Also bind public files added after the historical final manifest.
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.stat().st_size < (1 << 30):
                add(path)
        previous = read(folder / 'TUNA_RUN.json')
        require(previous['esm_qualification']['passed'], 'Historical encoder qualification failed')
        require(previous['esm_qualification']['encoder_sha256'] == model['encoder_weights_sha256'], 'Encoder mismatch')
        print('Verifying full residue cache:', study, flush=True)
        add(ROOT / previous['residues']['path'], previous['residues'])
        rows = table(folder / 'panels.csv')
        panels[study] = {'pairs': len(rows), 'P': sum(r['label'] == 'P' for r in rows),
                         'U': sum(r['label'] == 'U' for r in rows),
                         'targets': len({r['target_id'] for r in rows}),
                         'sequences': previous['fresh_sequences'], 'residues': previous['total_residues']}
        (OUT / study).mkdir()
        print('Verified historical panel:', panels[study], flush=True)
    add(REGISTRY)
    for item in registry['bundle_files']:
        add(BUNDLE / item['path'], item)
    add(BUNDLE / 'MODEL_REGISTRY.json', {'sha256': sha(REGISTRY)})
    print('Verifying pinned runtime', flush=True)
    add(ROOT / model['runtime']['path'], model['runtime'])
    add(ROOT / 'benchmark/tuna/scripts/gpu_guard.py')
    add(ROOT / 'example/twelve_target_comparison_v1/metrics.py')
    execution_path = ROOT / 'experiments/human_ppi_data_scaling_v1/audit/EXECUTION_FREEZE.json'
    add(execution_path, registry['provenance']['execution_freeze'])
    execution = read(execution_path)
    wanted = {'sequences.json', 'endpoints.json', 'training_16799.npz', 'training_31188.npz', 'training_unlabeled.npz'}
    wanted.update(f'development/{cohort}/C{k}.npz' for cohort in ('reconciled', 'added') for k in (1, 2, 3))
    for item in execution['data_files']:
        if item['name'] in wanted:
            add(DATA / item['name'], item)
    for path in sorted((OUT / 'scripts').glob('*.py')):
        add(path)
    for name in ('run.sh', 'PROTOCOL.md'):
        add(OUT / name)
    status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT, text=True)
    # Preserve the existing dirty graph and all tracked content byte-for-byte.
    changed = subprocess.check_output(['git', 'diff', '--name-only', '-z'], cwd=ROOT).decode().split('\0')
    before = [record(ROOT / name) for name in changed if name and (ROOT / name).is_file()]
    write_json(OUT / 'INPUT_FREEZE.json', {'at_utc': now(), 'default_model': registry['default_model'],
        'registry_sha256': sha(REGISTRY), 'model': model, 'panels': panels,
        'inputs': list(records.values()), 'tracked_status_before': status, 'dirty_tracked_before': before,
        'git_head_before': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'new_model_inference_yet': False, 'historical_scores_known': True,
        'fitting_or_selection': False, 'historical_inputs_read_only': True})
    print('Input freeze complete:', len(records), 'checksummed files', flush=True)


if __name__ == '__main__':
    main()

