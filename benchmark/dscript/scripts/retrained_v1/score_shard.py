"""Resumable four-GPU scoring of the selected three-seed ensemble."""
import argparse
from pathlib import Path
import time
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from common import CELLS,cuda,now,read,write,sha
from comparison import session_check,cell_path,COLUMNS,relative_record
from frozen_scorer import Scorer,SCORERS,MEMBERS
from native_adapter import learned_digest


def work(rank,workers):
    session_check();root=Path('/output');device=cuda();freeze=read('/bundle/SCORER_FREEZE.json')
    assert workers==freeze['workers'] and 0<=rank<workers
    identity={'scorer_freeze_sha256':sha('/bundle/SCORER_FREEZE.json'),'session_sha256':sha('/session/SESSION.json'),
              'rank':rank,'workers':workers}
    if (root/'IDENTITY.json').exists():assert read(root/'IDENTITY.json')==identity
    else:write(root/'IDENTITY.json',identity,exclusive=True)
    if (root/'COMPLETE.json').exists():
        for item in read(root/'COMPLETE.json')['files']:assert sha(root/item['path'])==item['sha256']
        print('Completed shard verified',flush=True);return
    scorer=Scorer('/bundle',device);ids=pa.array(read('/bundle/endpoints.json'));files=[];started=time.monotonic();new=0
    for cell in CELLS:
        rows=pq.read_table(cell_path('/session',cell));left=len(rows)*rank//workers;right=len(rows)*(rank+1)//workers
        subset=rows.slice(left,right-left)
        ia=pc.index_in(subset[COLUMNS[1]],value_set=ids);ib=pc.index_in(subset[COLUMNS[2]],value_set=ids)
        assert not ia.null_count and not ib.null_count
        a,b=ia.to_numpy(),ib.to_numpy();path=root/f'{cell}.npy';progress=root/f'{cell}-PROGRESS.json'
        if path.exists():
            values=np.lib.format.open_memmap(path,mode='r+');done=read(progress)['completed']
            assert values.shape==(len(subset),len(SCORERS)) and np.isfinite(values[:done]).all()
        else:
            values=np.lib.format.open_memmap(path,mode='w+',dtype=np.float64,shape=(len(subset),len(SCORERS)))
            values[:]=np.nan;values.flush();done=0
            write(progress,{**identity,'cell':cell,'completed':0,'total':len(subset),'left':left,'right':right})
        while done<len(subset):
            stop=min(done+2048,len(subset));values[done:stop]=scorer.scores(a[done:stop],b[done:stop]);values.flush()
            new+=stop-done;done=stop
            info={**identity,'at_utc':now(),'cell':cell,'completed':done,'total':len(subset),'left':left,'right':right,
                  'pairs_per_second_this_run':new/(time.monotonic()-started)}
            temporary=progress.with_suffix('.next.json');write(temporary,info);temporary.replace(progress)
            if done%10240==0 or done==len(subset):print(info,flush=True)
        assert np.isfinite(values).all() and np.array_equal(values[:,0],values[:,1:].mean(1,dtype=np.float64))
        error=float(np.max(np.abs(scorer.scores(b[:17],a[:17])-values[:17])))
        if error>freeze['logit_tolerance']:raise RuntimeError('Exchange-symmetry qualification failed')
        files.append({**relative_record(path,root),'cell':cell,'left':left,'right':right,'rows':len(subset),'symmetry_error':error})
    for name,model in zip(MEMBERS,scorer.models,strict=True):assert learned_digest(model)==freeze['learned_state_sha256'][name]
    write(root/'COMPLETE.json',{**identity,'files':files,'at_utc':now(),'truth_accessed':False,'training_performed':False},exclusive=True)


def merge(workers):
    session_check();output=Path('/output');files=[];shards=[]
    for rank in range(workers):
        directory=Path('/shards')/f'rank-{rank:02d}';item=read(directory/'COMPLETE.json')
        assert item['rank']==rank and item['workers']==workers and not item['truth_accessed']
        assert item['scorer_freeze_sha256']==sha('/bundle/SCORER_FREEZE.json') and item['session_sha256']==sha('/session/SESSION.json')
        for artifact in item['files']:assert sha(directory/artifact['path'])==artifact['sha256']
        shards.append((directory,item))
    for cell in CELLS:
        rows=pq.read_table(cell_path('/session',cell));values=np.full((len(rows),len(SCORERS)),np.nan);seen=np.zeros(len(rows),bool)
        for directory,item in shards:
            part=next(x for x in item['files'] if x['cell']==cell);left,right=part['left'],part['right']
            assert 0<=left<right<=len(rows) and not seen[left:right].any()
            scores=np.load(directory/part['path'],allow_pickle=False);assert scores.shape==(right-left,len(SCORERS))
            values[left:right]=scores;seen[left:right]=True
        assert seen.all() and np.isfinite(values).all() and np.array_equal(values[:,0],values[:,1:].mean(1,dtype=np.float64))
        path=cell_path(output,cell)
        if path.exists():raise RuntimeError('Refusing to overwrite merged predictions')
        pq.write_table(pa.table({'candidate_token':rows['candidate_token'],**{name:values[:,j] for j,name in enumerate(SCORERS)}}),path,compression='zstd')
        files.append({**relative_record(path,output),'cell':cell,'rows':len(rows)})
    write(output/'PREDICTIONS.json',{'at_utc':now(),'files':files,'truth_accessed':False,
          'scorer_freeze_sha256':sha('/bundle/SCORER_FREEZE.json'),'session_sha256':sha('/session/SESSION.json'),
          'workers':workers,'complete_unique_finite_coverage':True,'training_performed':False},exclusive=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['work','merge']);parser.add_argument('--rank',type=int);parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if args.mode=='work':work(args.rank,args.workers)
    else:merge(args.workers)
