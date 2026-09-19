"""Resumable native-head PU training; only TRAIN fitting and C3-DEV selection."""
import argparse
import json
import os
from pathlib import Path
import signal
import time
import numpy as np
import torch
from common import SEEDS,arrays,concordance,cuda,now,read,record,sha,write
from model import Residues,fresh,orders,project,scores,step
from native_adapter import learned_digest


def atomic_state(path, payload):
    temporary=path.with_suffix('.next.pt')
    torch.save(payload,temporary)
    os.replace(temporary,path)


def save_resume(path,model,optimizer,epoch,next_comparison,sums,protocol_sha):
    atomic_state(path,{'model':model.state_dict(),'optimizer':optimizer.state_dict(),
          'epoch':epoch,'next_comparison':next_comparison,'sums':sums,
          'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state(),
          'protocol_sha256':protocol_sha})


def load_resume(path,model,optimizer,protocol_sha,device):
    state=torch.load(path,map_location=device,weights_only=True)
    if state['protocol_sha256']!=protocol_sha:raise RuntimeError('Resume protocol changed')
    model.load_state_dict(state['model'],strict=True);optimizer.load_state_dict(state['optimizer'])
    torch.set_rng_state(state['cpu_rng'].cpu());torch.cuda.set_rng_state(state['cuda_rng'].cpu())
    return state['epoch'],state['next_comparison'],state['sums']


def development(root,epoch,model,cache,meta,dev,protocol_sha,event):
    model.eval();checkpoint=root/f'epoch_{epoch:02d}.pt';reservation=root/f'epoch_{epoch:02d}-RESERVATION.json'
    output=root/f'epoch_{epoch:02d}_C3_development.npy';info_path=root/f'epoch_{epoch:02d}.json'
    digest=learned_digest(model)
    if reservation.exists():
        old=read(reservation)
        assert old['learned_state_sha256']==digest and old['protocol_sha256']==protocol_sha
        assert sha(checkpoint)==old['checkpoint_sha256']
    else:
        atomic_state(checkpoint,model.state_dict())
        write(reservation,{'at_utc':now(),'epoch':epoch,'protocol_sha256':protocol_sha,
              'learned_state_sha256':digest,'checkpoint_sha256':sha(checkpoint),'test_pairs_read':False},exclusive=True)
    if info_path.exists():
        info=read(info_path);assert info['learned_state_sha256']==digest and sha(output)==info['development_predictions']['sha256']
        return
    indices=np.unique(np.concatenate([dev['a'],dev['b']]))
    assert all(meta['partition'][int(i)]=='development' for i in indices)
    values,offsets=project(model,cache,indices,meta['length'])
    temporary=root/f'epoch_{epoch:02d}_C3_development.next.npy'
    result=np.lib.format.open_memmap(temporary,mode='w+',dtype=np.float64,shape=(len(dev['a']),))
    for start in range(0,len(result),2048):
        end=min(start+2048,len(result))
        result[start:end]=scores(model,values,offsets,dev['a'][start:end],dev['b'][start:end])
        if start%102400==0:event({'event':'development_progress','epoch':epoch,'completed':end,'total':len(result)})
    assert np.isfinite(result).all()
    metric=concordance(result,dev['positive'],dev['weight'])
    result.flush();del result,values;temporary.replace(output)
    assert learned_digest(model)==digest
    write(info_path,{'at_utc':now(),'epoch':epoch,'protocol_sha256':protocol_sha,'learned_state_sha256':digest,
          'checkpoint':record(checkpoint),'development_predictions':record(output),'C3_development_concordance':metric,
          'test_pairs_read':False,'test_truth_read':False},exclusive=True)
    event({'event':'development_complete','epoch':epoch,'C3_development_concordance':metric})
    torch.cuda.empty_cache()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,choices=SEEDS,required=True)
    parser.add_argument('--through-epoch',type=int,choices=(2,4,6,8),required=True)
    args=parser.parse_args();protocol=read('/protocol.json');protocol_sha=sha('/protocol.json');root=Path('/output')
    for item in protocol['code_files']:
        assert sha(Path('/code')/item['path'])==item['sha256'],'Code changed after freeze'
    assert sha('/data/DATA_MANIFEST.json')==protocol['data_manifest_sha256']
    for item in read('/data/DATA_MANIFEST.json')['files']:assert sha(Path('/data')/item['path'])==item['sha256']
    assert sha('/cache/CACHE.json')==protocol['cache_manifest_sha256']
    for item in read('/cache/CACHE.json')['files']:assert (Path('/cache')/item['path']).stat().st_size==item['bytes']
    device=cuda(args.seed);model=fresh(args.seed,device)
    opt=torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=protocol['learning_rate'],weight_decay=0.)
    meta=read('/data/sequences.json');train=arrays('/data/training.npz');dev=arrays('/data/development_00.npz')
    train['normalized_u_weight']=train['u_weight']/train['u_weight'].mean()
    part=np.asarray(meta['partition'])
    for name in ('p_a','p_b','u_a','u_b'):assert (part[train[name]]=='train').all()
    assert (part[dev['a']]=='development').all() and (part[dev['b']]=='development').all()
    cache=Residues('/cache',device);resume=root/'resume.pt';epoch=1;done=0;sums={k:0. for k in ('loss','ranking_loss','contact_penalty')}
    if resume.exists():epoch,done,sums=load_resume(resume,model,opt,protocol_sha,device)
    if args.through_epoch>2:
        previous=root/f'STAGE_{args.through_epoch-2:02d}_COMPLETE.json'
        assert read(previous)['protocol_sha256']==protocol_sha
        if epoch<args.through_epoch-1:raise RuntimeError('Previous two-epoch stage is incomplete')
    stage=root/f'STAGE_{args.through_epoch:02d}_COMPLETE.json'
    if stage.exists():
        assert read(stage)['protocol_sha256']==protocol_sha
        print('Completed stage already recorded',flush=True);return
    stop_requested=[False]
    signal.signal(signal.SIGTERM,lambda *_:stop_requested.__setitem__(0,True))
    signal.signal(signal.SIGUSR1,lambda *_:stop_requested.__setitem__(0,True))
    started=time.monotonic();start_done=done
    def event(fields):
        item={'at_utc':now(),'seed':args.seed,**fields}
        print(item,flush=True)
        with (root/'events.jsonl').open('a') as handle:handle.write(json.dumps(item,allow_nan=False)+'\n')
        temporary=root/'PROGRESS.next.json';write(temporary,item);temporary.replace(root/'PROGRESS.json')
    event({'event':'start','epoch':epoch,'next_comparison':done,'through_epoch':args.through_epoch,
           'protocol_sha256':protocol_sha,'gpu':torch.cuda.get_device_name(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),
           'trainable_parameters':sum(p.numel() for p in model.parameters() if p.requires_grad)})
    for current in range(epoch,args.through_epoch+1):
        model.train();epoch_start=time.monotonic();comparison_start=done
        po,uo=orders(args.seed,current,len(train['p_a']),len(train['u_a']))
        if done==0:save_resume(resume,model,opt,current,0,sums,protocol_sha)
        for start in range(done,len(uo),protocol['comparison_batch']):
            end=min(start+protocol['comparison_batch'],len(uo))
            metrics=step(model,opt,cache,train,po[start:end],uo[start:end])
            for key in sums:sums[key]+=metrics[key]*(end-start)
            done=end
            if end%256==0 or end==len(uo):
                elapsed=time.monotonic()-epoch_start
                event({'event':'training_progress','epoch':current,'comparisons_done':end,'comparisons_total':len(uo),
                       'metrics':metrics,'running_means':{k:v/end for k,v in sums.items()},
                       'comparisons_per_second_this_epoch_process':(end-comparison_start)/max(elapsed,1e-9),
                       'epoch_seconds_this_process':elapsed,'peak_gpu_bytes':torch.cuda.max_memory_allocated()})
            if end%2048==0 or end==len(uo) or stop_requested[0]:
                save_resume(resume,model,opt,current,end,sums,protocol_sha)
            if stop_requested[0]:
                event({'event':'checkpointed_stop','epoch':current,'comparisons_done':end});raise SystemExit(75)
        event({'event':'epoch_complete','epoch':current,'running_means':{k:v/len(uo) for k,v in sums.items()}})
        if current in protocol['evaluation_epochs']:
            development(root,current,model,cache,meta,dev,protocol_sha,event)
        done=0;sums={k:0. for k in sums}
        save_resume(resume,model,opt,current+1,0,sums,protocol_sha)
    result={'at_utc':now(),'seed':args.seed,'through_epoch':args.through_epoch,'protocol_sha256':protocol_sha,
            'elapsed_this_process_seconds':time.monotonic()-started,'test_pairs_read':False,'test_truth_read':False,
            'all_training_rows_retained':True,'resume_checkpoint_sha256':sha(resume)}
    write(stage,result,exclusive=True)
    if args.through_epoch==protocol['epochs']:write(root/'COMPLETE.json',result,exclusive=True)
    event({'event':'stage_complete','through_epoch':args.through_epoch})


if __name__=='__main__':main()
