"""Post-run integrity audit; reads manifests/aggregates, never decrypts truth."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FREEZE_SHA = '4ceaf28210f74b4f8519d2e8b9453376ce08edf27dcf79ef5ef12fbb8fc0ee86'
CELLS = {'C1_test': 1003187, 'C2_test': 1013446, 'C3_test': 1002379}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def checked(root, manifest):
    for item in manifest['files']:
        relative = Path(item['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        path = root / relative
        assert not path.is_symlink() and path.stat().st_size == item['bytes']
        assert sha(path) == item['sha256'], path


def main():
    bundle = ROOT / 'runs/original-v1/scorer_bundle'
    private = ROOT / 'private/original-v1'
    published = ROOT / 'results/original-v1'
    freeze = read(bundle / 'SCORER_FREEZE.json')
    assert sha(bundle / 'SCORER_FREEZE.json') == FREEZE_SHA
    assert freeze['original_model'] == 'human_v1' and not freeze['training_performed']
    checked(bundle, freeze)
    assert sha(ROOT.parent / 'containers/images/dscript-native-arm64-v1.sif') == freeze['sif_sha256']
    session = read(private / 'session/SESSION.json')
    prediction = read(private / 'predictions/PREDICTIONS.json')
    references = read(private / 'references/REFERENCES.json')
    pf = read(private / 'freeze/PREDICTION_FREEZE.json')
    reservation = read(private / 'evaluation/EVALUATION_RESERVATION.json')
    result = read(published / 'RESULTS.json')
    for folder, manifest in [('session', session), ('predictions', prediction), ('references', references)]:
        checked(private / folder, manifest)
    assert references['byte_identical_to_historical_predictions']
    assert prediction['complete_unique_finite_coverage'] and not prediction['training_performed']
    assert {x['cell']: x['rows'] for x in prediction['files']} == CELLS
    assert pf['complete_unique_finite_coverage'] and pf['rows'] == sum(CELLS.values())
    assert not any(x['truth_accessed'] for x in (session, prediction, pf))
    assert reservation['prediction_freeze_sha256'] == sha(private / 'freeze/PREDICTION_FREEZE.json')
    assert result['prediction_freeze_sha256'] == reservation['prediction_freeze_sha256']
    assert sha(published / 'RESULTS.json') == sha(private / 'evaluation/RESULTS.json')
    assert result['historical_reference_points_reproduced'] and result['historical_component_draws_reproduced']
    assert result['no_test_tuning'] and result['temporary_decrypted_truth_removed']
    assert not list((private / 'evaluation').glob('truth-*'))
    times = [x['at_utc'] for x in (freeze, session, prediction, references, pf, reservation, result)]
    assert [datetime.fromisoformat(x) for x in times] == sorted(datetime.fromisoformat(x) for x in times)
    symmetry = {}
    for rank in range(4):
        root = private / 'shards' / f'rank-{rank:02d}'
        item = read(root / 'COMPLETE.json')
        checked(root, item)
        assert not item['truth_accessed'] and not item['training_performed']
        assert item['scorer_freeze_sha256'] == FREEZE_SHA
        symmetry[str(rank)] = max(x['symmetry_error'] for x in item['files'])
        assert symmetry[str(rank)] <= 1e-5
    for cell, count in CELLS.items():
        item = result['cells'][cell]
        assert item['positive_pairs'] + item['unlabeled_pairs'] == count
        assert set(item['metrics']) == {'dscript_original', 'ipin_baseline', 'ipin_optimized'}
        assert all(x['finite_bootstrap_draws'] == 2000 for x in item['metrics'].values())
        assert all(x['finite_paired_draws'] == 2000 for x in result['differences'][cell])
    with (published / 'scores.csv').open() as handle:
        assert len(list(csv.DictReader(handle))) == 9
    with (published / 'paired_differences.csv').open() as handle:
        assert len(list(csv.DictReader(handle))) == 6
    job = (ROOT / 'runs/original-v1/JOB.txt').read_text().strip()
    assert job.isdigit()
    accounting = subprocess.check_output(
        ['sacct', '-X', '-j', job, '--noheader', '--parsable2', '--format=JobID,State,ExitCode,Elapsed,NodeList'],
        text=True).strip()
    fields = accounting.split('|')
    assert fields[:3] == [job, 'COMPLETED', '0:0'], accounting
    uuids = []
    for rank in range(4):
        log = (ROOT / f'logs/original-score-{job}-rank-{rank}.log').read_text()
        match = re.search(rf'GPU_BINDING rank={rank} uuid=(GPU-\S+)', log)
        assert match
        uuids.append(match.group(1))
    assert len(set(uuids)) == 4
    scope = read(ROOT / 'provenance/original-evaluation-v1/scope-audit.json')
    assert scope['passed']
    report = {'at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
              'scorer_freeze_sha256': FREEZE_SHA, 'rows': CELLS, 'total_rows': sum(CELLS.values()),
              'stage_timestamps_in_order': times, 'slurm_accounting': accounting,
              'gpu_uuids_by_rank': uuids, 'maximum_symmetry_error_by_rank': symmetry,
              'all_2000_paired_draws_finite': True, 'historical_references_reproduced': True,
              'frozen_files_and_image_verified': True, 'temporary_truth_absent': True,
              'scope_audit_passed': True, 'training_performed': False,
              'result_sha256': sha(published / 'RESULTS.json')}
    target = ROOT / 'provenance/original-evaluation-v1/COMPLETION_AUDIT.json'
    with target.open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
