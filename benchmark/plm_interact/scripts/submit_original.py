"""Submit only the original-checkpoint scoring/evaluation job, once."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    subprocess.run(['python3','-B',str(ROOT/'scripts/host_guard.py')],check=True)
    assert (ROOT/'private/original-v1/session/SESSION.json').is_file()
    output=ROOT/'runs/original-v1/JOB.json'
    with output.open('x') as record:
        env=dict(os.environ);env['PLM_INTERACT_BENCHMARK_ROOT']=str(ROOT)
        result=subprocess.run(['sbatch','--parsable','--chdir='+str(ROOT),
                               '--output='+str(ROOT/'logs/original-job-%j.stdout.log'),
                               '--error='+str(ROOT/'logs/original-job-%j.stderr.log'),str(ROOT/'original.sbatch')],
                              env=env,capture_output=True,text=True,check=True)
        value={'job_id':result.stdout.strip().split(';')[0],'at_utc':datetime.now(timezone.utc).isoformat(),
               'gpus':4,'walltime':'72:00:00','checkpoint':'PLM-interact-650M-humanV11','training':False,
               'dscript_jobs_modified':False,'slurm_response':result.stdout.strip()}
        json.dump(value,record,indent=2);record.write('\n')
    print(json.dumps(value),flush=True)

if __name__=='__main__':main()
