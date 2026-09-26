"""Submit one four-GPU training job and its dependent comparison once."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/freeze.py'), 'verify'], check=True)
    target = ROOT / 'runs/JOBS.json'
    value = {'submitted_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'submitting', 'jobs': []}
    with target.open('x') as handle:
        json.dump(value, handle, indent=2); handle.write('\n')
    env = os.environ.copy(); env['RESIDUE_STUDY_ROOT'] = str(ROOT)
    def persist():
        tmp = target.with_suffix('.tmp')
        tmp.write_text(json.dumps(value, indent=2) + '\n'); tmp.replace(target)
    previous = None
    try:
        for stage, script in [('training', 'train.sbatch'), ('selection_and_C123_comparison', 'final.sbatch')]:
            cmd = ['sbatch', '--parsable', f'--chdir={ROOT}', f'--output={ROOT}/logs/{stage}-%j.stdout.log',
                   f'--error={ROOT}/logs/{stage}-%j.stderr.log']
            if previous:
                cmd += [f'--dependency=afterok:{previous}']
            cmd += [str(ROOT / script)]
            job = subprocess.check_output(cmd, env=env, text=True).strip().split(';')[0]
            if not job.isdigit():
                raise RuntimeError(f'Unexpected SLURM response: {job}')
            value['jobs'].append({'stage': stage, 'job_id': job, 'dependency_afterok': previous})
            persist(); previous = job
            print(value['jobs'][-1], flush=True)
    except Exception:
        value['status'] = 'partial_submission_requires_review'; persist(); raise
    value['status'] = 'submitted'; persist()
    subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/publish_status.py'), 'submitted'], check=True)


if __name__ == '__main__':
    main()
