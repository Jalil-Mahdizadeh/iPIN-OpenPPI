"""Submit one three-seed, 20-epoch TRAIN/C3-development job; never a test job."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'runs/retrained-v1'


def main():
    target = RUN / 'JOBS.json'
    assert (RUN / 'TRAINING_FREEZE.json').is_file() and (RUN / 'EXECUTION_CODE_FREEZE.json').is_file()
    os.environ['RAPPPID_BENCHMARK_ROOT'] = str(ROOT)
    command = ['sbatch', '--parsable', f'--chdir={ROOT}',
               f'--output={ROOT}/logs/retrained-%j.stdout.log',
               f'--error={ROOT}/logs/retrained-%j.stderr.log', str(ROOT / 'retrained_train.sbatch')]
    value = {'submitted_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'submitting',
             'command': command, 'jobs': [], 'epochs': 20, 'evaluation_epochs': [4, 8, 12, 16, 20],
             'seeds': [20260803, 20260817, 20260831], 'checkpoint_selected': False,
             'test_evaluation_authorized': False, 'test_evaluation_scheduled': False}
    # Reserve before contacting Slurm. An ambiguous submission must be audited,
    # not silently retried and duplicated.
    with target.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')

    def persist():
        temporary = target.with_suffix('.next.json')
        with temporary.open('w') as handle:
            json.dump(value, handle, indent=2)
            handle.write('\n')
        temporary.replace(target)

    try:
        response = subprocess.check_output(command, text=True).strip()
        value['raw_sbatch_response'] = response
        job = response.split(';', 1)[0]
        assert job.isdigit(), response
        value['jobs'].append({'stage': 'epochs-1-20-and-C3-development', 'job_id': job,
                              'walltime': '48:00:00', 'nodes': 1, 'gpus': 3,
                              'cpus_per_task': 72, 'memory': '96G', 'through_epoch': 20})
        value['status'] = 'submitted'
        persist()
    except Exception:
        value['status'] = 'submission_requires_audit_before_retry'
        persist()
        raise
    print(json.dumps(value, indent=2), flush=True)
    print('Only TRAIN and C3 development queued. The user will choose an epoch before any test evaluation.', flush=True)


if __name__ == '__main__':
    main()
