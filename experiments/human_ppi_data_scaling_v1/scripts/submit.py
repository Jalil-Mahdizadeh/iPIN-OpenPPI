"""Submit all registered fits and a dependent, fixed selection/evaluation job."""
from pathlib import Path
from datetime import datetime,timezone
import json
import os
import subprocess
from freeze_execution import ROOT,sha,verify

def main():
    verify()
    destination=ROOT/'runs/SUBMISSION.json'
    if destination.exists():raise RuntimeError('Study already submitted; refusing duplicate GPU work')
    p=json.loads((ROOT/'data/PROTOCOL.json').read_text())
    tasks=[{'budget':b,'seed':s} for b in p['positive_budgets'] for s in p['seeds']]
    env=dict(os.environ);env['HUMAN_PPI_STUDY_ROOT']=str(ROOT)
    for k in list(env):
        if k.startswith('SLURM_') and k not in ('SLURM_CLUSTER_NAME',):env.pop(k)
    common=['sbatch','--parsable','--export=ALL','--chdir='+str(ROOT)]
    value={'at_utc':datetime.now(timezone.utc).isoformat(),'execution_sha256':sha(ROOT/'audit/EXECUTION_FREEZE.json'),
           'tasks':tasks,'max_simultaneous_fits':4,'historical_artifacts_modified':False}
    training=subprocess.check_output(common+['--array=0-'+str(len(tasks)-1)+'%4',
        '--output='+str(ROOT/'logs/train-%A_%a.out'),'--error='+str(ROOT/'logs/train-%A_%a.err'),str(ROOT/'train.sbatch')],env=env,text=True).strip().split(';')[0]
    value['training_array_job_id']=training
    # Preserve the successful submission even if the dependent submission fails.
    with destination.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    final=subprocess.check_output(common+['--dependency=afterok:'+training,
        '--output='+str(ROOT/'logs/final-%j.out'),'--error='+str(ROOT/'logs/final-%j.err'),str(ROOT/'final.sbatch')],env=env,text=True).strip().split(';')[0]
    value['final_job_id']=final
    temp=destination.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(destination)
    print(json.dumps(value,indent=2))

if __name__=='__main__':main()
