"""Queue only the frozen training, selection and test stages, with afterok gates."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/retrained-v1'


def main():
    target=RUN/'JOBS.json'
    if target.exists():raise RuntimeError('Jobs already recorded; inspect before resubmitting')
    cache=(RUN/'CACHE_JOB.txt').read_text().strip();assert cache.isdigit()
    assert (RUN/'TRAINING_FREEZE.json').is_file() and (RUN/'EXECUTION_CODE_FREEZE.json').is_file()
    os.environ['DSCRIPT_BENCHMARK_ROOT']=str(ROOT)
    value={'submitted_at_utc':datetime.now(timezone.utc).isoformat(),'cache_job':cache,'status':'submitting','jobs':[]}
    with target.open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n')
    def persist():
        temporary=target.with_suffix('.next.json')
        with temporary.open('w') as handle:json.dump(value,handle,indent=2);handle.write('\n')
        temporary.replace(target)
    previous=cache
    definitions=[(f'epochs-{end-1}-{end}','retrained_train.sbatch',[str(end)],'72:00:00',end) for end in (2,4,6,8)]
    definitions.extend([('selection','retrained_prepare.sbatch',[],'24:00:00',None),('C123-test','retrained_test.sbatch',[],'24:00:00',None)])
    try:
        for label,script,args,wall,epoch in definitions:
            command=['sbatch','--parsable',f'--dependency=afterok:{previous}',f'--chdir={ROOT}',
                     f'--job-name=dscript-{label}',f'--output={ROOT}/logs/retrained-{label}-%j.stdout.log',
                     f'--error={ROOT}/logs/retrained-{label}-%j.stderr.log',str(ROOT/script),*args]
            job=subprocess.check_output(command,text=True).strip();assert job.isdigit(),job
            value['jobs'].append({'stage':label,'job_id':job,'dependency_afterok':previous,'walltime':wall,'through_epoch':epoch})
            persist();print(value['jobs'][-1],flush=True);previous=job
    except Exception:
        value['status']='partial_submission_requires_audit';persist();raise
    value['status']='submitted';persist()
    print('Frozen training and evaluation chain submitted; no further benchmarks queued.',flush=True)


if __name__=='__main__':main()
