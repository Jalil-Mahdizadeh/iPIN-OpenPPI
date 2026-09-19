"""Submit the authorized one-time HSP -> C1/C2/C3 test workflow."""
import json
import os
import subprocess
from launcher import ROOT, RUN, LOGS
from pipeline import now, rec, write, check_initial

os.umask(0o077)
assert not (RUN/'SUBMISSION.json').exists()
check_initial()
env = {k: v for k, v in os.environ.items() if not k.startswith(('SLURM_', 'SBATCH_', 'SRUN_'))}
env['SPRINT_BENCHMARK_ROOT'] = str(ROOT)
env.pop('CUDA_VISIBLE_DEVICES', None)
items = []
for phase in ('hsp', 'evaluate'):
    command = ['sbatch', '--parsable', '--chdir', str(ROOT), '--export', 'ALL',
        '--output', str(LOGS/(phase+'-%j.out')), '--error', str(LOGS/(phase+'-%j.err'))]
    if items: command += ['--dependency', 'afterok:'+items[0]['job_id'], '--kill-on-invalid-dep=yes']
    script = ROOT/(phase+'.sbatch'); command += [str(script)]
    job = subprocess.check_output(command, env=env, text=True).strip().split(';')[0]
    assert job.isdigit()
    item = {'phase': phase, 'job_id': job, 'script': rec(script, ROOT), 'at_utc': now()}
    items.append(item)
    write(RUN/(phase.upper()+'_JOB.json'), item)
    print(json.dumps(item), flush=True)
write(RUN/'SUBMISSION.json', {'at_utc': now(), 'jobs': items, 'no_other_jobs_modified': True})
