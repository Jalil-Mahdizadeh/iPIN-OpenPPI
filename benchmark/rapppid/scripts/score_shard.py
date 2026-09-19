"""Resumable original-model probability scoring; no truth or reference inputs."""
import argparse
from pathlib import Path
import signal
import time
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from common import CELLS,cuda,now,read,write,sha
from comparison import session_check,cell_path,COLUMNS,relative_record
from frozen_scorer import Scorer,SCORERS
from native_model import learned_digest

def work(rank,workers):
    session_check();root=Path('/output');device=cuda()
    frozen=read('/bundle/SCORER_FREEZE.json')
    assert workers==frozen['workers'] and 0<=rank<workers
    identity={'scorer_freeze_sha256':sha('/bundle/SCORER_FREEZE.json'),'session_sha256':sha('/session/SESSION.json'),'rank':rank,'workers':workers}
    if (root/'IDENTITY.json').exists():assert read(root/'IDENTITY.json')==identity
    else:write(root/'IDENTITY.json',identity,exclusive=True)
    if (root/'COMPLETE.json').exists():
        previous=read(root/'COMPLETE.json')
        for item in previous['files']:assert sha(root/item['path'])==item['sha256']
        print('Complete shard verified',flush=True);return
    scorer=Scorer('/bundle',device);ids=pa.array(read('/bundle/endpoints.json'))
    assert learned_digest(scorer.model)==frozen['learned_state_sha256']
    files=[];started=time.monotonic();total_done=0;stop_requested=[False]
    signal.signal(signal.SIGTERM,lambda *_:stop_requested.__setitem__(0,True))
    signal.signal(signal.SIGUSR1,lambda *_:stop_requested.__setitem__(0,True))
    for cell in CELLS:
        rows=pq.read_table(cell_path('/session',cell));left=len(rows)*rank//workers;right=len(rows)*(rank+1)//workers
        subset=rows.slice(left,right-left)
        a=pc.index_in(subset[COLUMNS[1]],value_set=ids).to_numpy();b=pc.index_in(subset[COLUMNS[2]],value_set=ids).to_numpy()
        truncated=int(np.sum((scorer.lengths[a]>frozen['maximum_residues']) | (scorer.lengths[b]>frozen['maximum_residues'])))
        path=root/f'{cell}.npy';progress=root/f'{cell}-PROGRESS.json'
        if path.exists():
            old=read(progress)
            assert all(old[k]==v for k,v in identity.items())
            assert (old['cell'],old['left'],old['right'],old['total'])==(cell,left,right,len(subset))
            values=np.lib.format.open_memmap(path,mode='r+');done=old['completed']
            assert values.shape==(len(subset),) and 0<=done<=len(subset) and np.isfinite(values[:done]).all()
        else:
            values=np.lib.format.open_memmap(path,mode='w+',dtype=np.float64,shape=(len(subset),));values[:]=np.nan;values.flush();done=0
            write(progress,{**identity,'cell':cell,'completed':0,'total':len(subset),'left':left,'right':right})
        while done<len(subset):
            end=min(done+32768,len(subset));values[done:end]=scorer.scores(a[done:end],b[done:end])[:,0];values.flush()
            total_done+=end-done;done=end
            info={**identity,'at_utc':now(),'cell':cell,'completed':done,'total':len(subset),'left':left,'right':right,
                  'pairs_with_native_truncation_in_shard_cell':truncated,'this_run_pairs':total_done,
                  'elapsed_seconds':time.monotonic()-started,'pairs_per_second_this_run':total_done/(time.monotonic()-started)}
            temporary=progress.with_suffix('.next.json');write(temporary,info);temporary.replace(progress)
            if done%131072==0 or done==len(subset):print(info,flush=True)
            if stop_requested[0]:print({'checkpointed_stop':info},flush=True);raise SystemExit(75)
        if not np.isfinite(values).all():raise RuntimeError('Missing/nonfinite shard scores')
        error=float(np.max(np.abs(scorer.scores(b[:17],a[:17])[:,0]-values[:17])))
        if error>frozen['batch_tolerance']:raise RuntimeError('Canonical order/batching check failed')
        files.append({**relative_record(path,root),'cell':cell,'left':left,'right':right,'rows':len(subset),
                      'canonical_order_error':error,'pairs_with_native_truncation':truncated})
    assert learned_digest(scorer.model)==frozen['learned_state_sha256']
    write(root/'COMPLETE.json',{**identity,'files':files,'at_utc':now(),'truth_accessed':False,'training_performed':False,
                              'elapsed_seconds':time.monotonic()-started},exclusive=True)

def merge(workers):
    session_check();output=Path('/output');files=[];shards=[];coverage={}
    for rank in range(workers):
        directory=Path('/shards')/f'rank-{rank:02d}';item=read(directory/'COMPLETE.json')
        assert item['rank']==rank and item['workers']==workers and not item['truth_accessed'] and not item['training_performed']
        assert item['scorer_freeze_sha256']==sha('/bundle/SCORER_FREEZE.json') and item['session_sha256']==sha('/session/SESSION.json')
        for artifact in item['files']:assert sha(directory/artifact['path'])==artifact['sha256']
        shards.append((directory,item))
    for cell in CELLS:
        rows=pq.read_table(cell_path('/session',cell));values=np.full(len(rows),np.nan);seen=np.zeros(len(rows),bool);truncated=0
        for directory,item in shards:
            part=next(x for x in item['files'] if x['cell']==cell);left,right=part['left'],part['right']
            assert 0<=left<right<=len(rows) and not seen[left:right].any()
            score=np.load(directory/part['path'],allow_pickle=False);assert score.shape==(right-left,)
            values[left:right]=score;seen[left:right]=True;truncated+=part['pairs_with_native_truncation']
        if not seen.all() or not np.isfinite(values).all() or (values<0).any() or (values>1).any():raise RuntimeError('Incomplete/nonfinite coverage')
        path=cell_path(output,cell)
        if path.exists():raise RuntimeError('Refusing to overwrite merged predictions')
        pq.write_table(pa.table({'candidate_token':rows['candidate_token'],SCORERS[0]:values}),path,compression='zstd')
        files.append({**relative_record(path,output),'cell':cell,'rows':len(rows)})
        coverage[cell]={'pairs_scored':len(rows),'pairs_with_native_truncation':truncated,'fraction_with_native_truncation':truncated/len(rows)}
    write(output/'PREDICTIONS.json',{'at_utc':now(),'files':files,'truth_accessed':False,
          'scorer_freeze_sha256':sha('/bundle/SCORER_FREEZE.json'),'session_sha256':sha('/session/SESSION.json'),
          'workers':workers,'complete_unique_finite_coverage':True,'training_performed':False,'coverage':coverage},exclusive=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['work','merge']);parser.add_argument('--rank',type=int);parser.add_argument('--workers',type=int,default=1)
    args=parser.parse_args()
    if args.mode=='work':work(args.rank,args.workers)
    else:merge(args.workers)
