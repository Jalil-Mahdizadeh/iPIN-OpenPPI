"""Audit committed score prefixes without opening test labels or changing jobs."""
from array import array
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def read(path):return json.loads(path.read_text())

def main():
    job=read(ROOT/'runs/original-v1/JOB.json');job_id=job['job_id']
    state=subprocess.run(['squeue','-h','-j',job_id,'-o','%T|%N|%M|%L'],capture_output=True,text=True,check=True).stdout.strip()
    assert state.startswith('RUNNING|'),state
    current=datetime.now(timezone.utc);ranks=[];uuids=[]
    for rank in range(4):
        directory=ROOT/'private/original-v1/shards'/f'rank-{rank:02d}'
        progress=read(directory/'C1_test-PROGRESS.json');done=progress['completed'];assert done>0
        age=(current-datetime.fromisoformat(progress['at_utc'])).total_seconds();assert age<180
        with (directory/'C1_test.npy').open('rb') as f:
            assert f.read(6)==b'\x93NUMPY';version=tuple(f.read(2));width=2 if version==(1,0) else 4
            header=ast.literal_eval(f.read(int.from_bytes(f.read(width),'little')).decode())
            assert header['descr']=='<f8' and header['shape']==(progress['total'],)
            values=array('d');values.frombytes(f.read(done*8))
        if sys.byteorder!='little':values.byteswap()
        assert len(values)==done and all(math.isfinite(x) and 0<=x<=1 for x in values)
        log=(ROOT/'logs'/f'original-score-{job_id}-rank-{rank}.log').read_text()
        assert not re.search(r'Traceback|RuntimeError|out of memory|nonfinite|FATAL',log,re.I)
        uuid=re.search(r'uuid=(GPU-[a-zA-Z0-9-]+)',log).group(1);uuids.append(uuid)
        ranks.append({'rank':rank,'gpu_uuid':uuid,'cell':'C1_test','committed_pairs':done,'prefix_scores_independently_finite':True,
                      'progress_age_seconds':age,'pairs_per_second':progress['pairs_per_second_this_run']})
    assert len(set(uuids))==4
    private=ROOT/'private/original-v1'
    assert not read(private/'session/SESSION.json')['truth_accessed']
    assert not (private/'evaluation/EVALUATION_RESERVATION.json').exists()
    sources=[]
    for p in sorted((ROOT/'scripts').glob('*.py'))+sorted(ROOT.glob('*.sh'))+sorted(ROOT.glob('*.sbatch')):
        sources.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    result={'passed':True,'at_utc':current.isoformat(),'job_id':job_id,'slurm_state':state,'ranks':ranks,
            'total_committed_pairs':sum(x['committed_pairs'] for x in ranks),'test_truth_accessed':False,
            'training_performed':False,'dscript_jobs_modified':False,'outside_scope_audit':read(ROOT/'provenance/repository-sif-audit.json'),
            'scorer_freeze_sha256':hashlib.sha256((ROOT/'runs/original-v1/scorer_bundle/SCORER_FREEZE.json').read_bytes()).hexdigest(),
            'execution_sources':sources}
    destination=ROOT/'provenance/STARTUP_HEALTH.json'
    with destination.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({k:result[k] for k in ('passed','at_utc','job_id','slurm_state','total_committed_pairs','ranks')},sort_keys=True))

if __name__=='__main__':main()
