"""Run original-only benchmark on the already allocated interactive GPU."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def now():return datetime.now(timezone.utc).isoformat()


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'Use an allocated HPC GPU, not a login node'
    assert (ROOT/'private/original-v1/session/SESSION.json').is_file()
    subprocess.run(['python3','-B',str(ROOT/'scripts/host_guard.py')],check=True)
    started=time.monotonic()
    source_paths=sorted((ROOT/'scripts').glob('*.py'))+sorted(ROOT.glob('*.sh'))
    files=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in source_paths]
    run={'at_utc':now(),'execution_mode':'existing interactive Slurm GPU allocation',
         'slurm_job_id':os.environ['SLURM_JOB_ID'],'node':socket.gethostname(),'gpus':1,
         'new_jobs_submitted':False,'training_performed':False,'dscript_jobs_modified':False,
         'release':'1690837077.519848_red-dreamy','files':files}
    with (ROOT/'runs/original-v1/RUN.json').open('x') as f:json.dump(run,f,indent=2);f.write('\n')
    env=dict(os.environ);env['RAPPPID_BENCHMARK_ROOT']=str(ROOT)
    for script,log in [('score_original_worker.sh','original-score-rank-0.log'),('finish_original.sh','original-finish.log')]:
        print({'phase':script,'started_at_utc':now()},flush=True)
        with (ROOT/'logs'/log).open('x') as handle:
            subprocess.run(['bash',str(ROOT/script)],env=env,stdout=handle,stderr=subprocess.STDOUT,check=True)
    result=json.loads((ROOT/'results/original-v1/RESULTS.json').read_text())
    assert result['historical_reference_points_reproduced'] and result['historical_component_draws_reproduced']
    assert sum(x['pairs_scored'] for x in result['coverage'].values())==3019012
    completed={**run,'completed_at_utc':now(),'elapsed_seconds':time.monotonic()-started,'status':'completed',
               'result_sha256':hashlib.sha256((ROOT/'results/original-v1/RESULTS.json').read_bytes()).hexdigest()}
    with (ROOT/'runs/original-v1/RUN_COMPLETE.json').open('x') as f:json.dump(completed,f,indent=2);f.write('\n')
    print({k:completed[k] for k in ('status','completed_at_utc','elapsed_seconds','slurm_job_id','node')},flush=True)


if __name__=='__main__':main()
