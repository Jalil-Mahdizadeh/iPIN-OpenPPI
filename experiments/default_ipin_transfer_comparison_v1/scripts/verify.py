"""Final byte preservation and completed-artifact verification; no science fitting."""
import subprocess
from transfer_io import *


def main():
    freeze = read(OUT / 'INPUT_FREEZE.json')
    require(read(OUT / 'ANALYSIS_COMPLETE.json')['status'] == 'complete', 'Analysis incomplete')
    require(read(OUT / 'METRIC_VALIDATION.json')['passed'], 'Metric checks failed')
    for item in freeze['inputs']:
        if item['bytes'] >= (1 << 30):
            print('Rechecking unchanged large input:', item['path'], flush=True)
        verify(item)
    for item in freeze['dirty_tracked_before']:
        verify(item)
    status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT, text=True)
    require(status == freeze['tracked_status_before'], 'Tracked workspace status changed')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    require(head == freeze['git_head_before'], 'Git HEAD changed')
    for item in read(OUT / 'ANALYSIS_COMPLETE.json')['outputs']:
        verify(item)
    score_rows = 0
    for study in STUDIES:
        run = read(OUT / study / 'SCORING_RUN.json')
        for item in run['outputs']:
            verify(item)
        require(run['pairs'] == freeze['panels'][study]['pairs'], 'Prediction coverage mismatch')
        require(len(run['qualifications']) == 3 and not run['GP_covariance_refitted'], 'Scoring qualification incomplete')
        for q in run['qualifications']:
            require(q['native_max_absolute_error'] <= q['native_tolerance'] and q['pair_order_symmetry_passed']
                    and q['parameters_and_buffers_unchanged'] and q['saved_GP_covariance_preserved'], 'Scoring qualification failed')
        require(all(r['passed'] for r in read(OUT / study / 'HISTORICAL_REPLAY.json')), 'Historical replay failed')
        score_rows += run['pairs']
    write_json(OUT / 'PRESERVATION.json', {'at_utc': now(), 'status': 'passed',
        'input_files_rechecked': len(freeze['inputs']), 'all_input_bytes_unchanged': True,
        'preexisting_dirty_tracked_files_unchanged': True, 'tracked_status_unchanged': True, 'git_HEAD_unchanged': True,
        'new_predictions': score_rows, 'studies_complete': list(STUDIES),
        'scope': 'All new scripts, scores, learned features, metrics, reports, logs and runtime caches are inside this experiment',
        'input_freeze_sha256': sha(OUT / 'INPUT_FREEZE.json'), 'analysis_complete_sha256': sha(OUT / 'ANALYSIS_COMPLETE.json')})
    write_json(OUT / 'FINAL_MANIFEST.json', {'at_utc': now(), 'status': 'complete', 'files': [record(p)
        for p in sorted(OUT.rglob('*')) if p.is_file()
        and not any(part in ('.cache', 'tmp') for part in p.relative_to(OUT).parts)
        and p.name not in ('FINAL_MANIFEST.json', 'verify.log')]})
    print(f'COMPLETE: {score_rows:,} new predictions; all {len(freeze["inputs"])} frozen inputs unchanged', flush=True)


if __name__ == '__main__':
    main()

