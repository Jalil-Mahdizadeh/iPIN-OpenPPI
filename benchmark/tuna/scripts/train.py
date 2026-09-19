#!/usr/bin/env python3
"""One prospectively frozen PU-TUnA seed; TRAIN-only fitting, C3-dev snapshots."""
from __future__ import annotations
import argparse
import json
import os
import time
from pathlib import Path
import numpy as np
import torch
from adapter import cached_scores
from common import SEEDS, arrays, concordance, cuda, now, read, record, sha, write
from residues import Residues
from training import fitted_features, make_model, optimizer, step, training_orders

def save_resume(path,model,inner,opt,epoch,next_step,epoch_loss,protocol_sha):
    payload={'model':model.state_dict(),'optimizer':inner.state_dict(),
        'lookahead':[opt.state[p]['cached_params'] for group in inner.param_groups for p in group['params']],
        'lookahead_step':opt.step_counter,'epoch':epoch,'next_step':next_step,'epoch_loss':epoch_loss,
        'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state(),
        'protocol_sha256':protocol_sha}
    temporary=path.with_suffix('.tmp')
    torch.save(payload,temporary)
    os.replace(temporary,path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,choices=SEEDS,required=True)
    p.add_argument('--data',type=Path,default=Path('/data'))
    p.add_argument('--cache',type=Path,default=Path('/output/residue_cache/residues.h5'))
    p.add_argument('--protocol',type=Path,default=Path('/output/TRAINING_FREEZE.json'))
    p.add_argument('--output',type=Path,default=Path('/output/training'))
    p.add_argument('--resume',action='store_true')
    args=p.parse_args()
    protocol=read(args.protocol); protocol_sha=sha(args.protocol)
    if not protocol['authorized_to_train'] or not read(Path('/output/QUALIFICATION.json'))['passed']:
        raise RuntimeError('Missing qualified/frozen training protocol')
    for item in protocol['training_code']:
        if sha(Path('/code')/item['name'])!=item['sha256']:
            raise RuntimeError('Training code changed after freeze')
    if sha(args.data/'DATA_MANIFEST.json')!=protocol['data_manifest_sha256']:
        raise RuntimeError('Training data freeze mismatch')
    if sha(Path('/output/residue_cache/RESIDUE_CACHE_MANIFEST.json'))!=protocol['residue_manifest_sha256']:
        raise RuntimeError('Residue extraction freeze mismatch')
    root=args.output/f'seed_{args.seed}'
    root.mkdir(parents=True,exist_ok=args.resume)
    if (root/'COMPLETE.json').exists():
        raise RuntimeError('This seed is already complete; no overwrite')
    device=cuda(args.seed); started=time.monotonic()
    train=arrays(args.data/'training.npz'); development=arrays(args.data/'development_00.npz')
    train['normalized_u_weight']=train['u_weight']/np.mean(train['u_weight'])
    cache=Residues(args.data,args.cache,device)
    model=make_model(args.seed,device); inner,opt=optimizer(model)
    epoch_start=1; next_step=0; epoch_loss=0.
    resume_path=root/'resume.pt'
    if args.resume and resume_path.exists():
        state=torch.load(resume_path,map_location=device,weights_only=True)
        if state['protocol_sha256']!=protocol_sha:
            raise RuntimeError('Resume protocol mismatch')
        model.load_state_dict(state['model'],strict=True); inner.load_state_dict(state['optimizer'])
        params=[p for group in inner.param_groups for p in group['params']]
        for parameter,cached in zip(params,state['lookahead'],strict=True):
            opt.state[parameter]['cached_params'].copy_(cached)
        opt.step_counter=state['lookahead_step']
        epoch_start=state['epoch']; next_step=state['next_step']; epoch_loss=state['epoch_loss']
        torch.set_rng_state(state['cpu_rng'].cpu()); torch.cuda.set_rng_state(state['cuda_rng'].cpu())
        del state
    batch=protocol['comparison_batch']; epochs=protocol['epochs']
    def event(data):
        value={'at_utc':now(),'seed':args.seed,**data}
        print(value,flush=True)
        with (root/'events.jsonl').open('a') as f:
            f.write(json.dumps(value,allow_nan=False)+'\n')
    event({'event':'start','resume':args.resume,'protocol_sha256':protocol_sha,
        'gpu':torch.cuda.get_device_name(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),
        'trainable_parameters':sum(x.numel() for x in model.parameters() if x.requires_grad)})
    for epoch in range(epoch_start,epochs+1):
        epoch_started=time.monotonic(); model.train()
        lr=1e-4*(.93**((epoch-1)//2))
        for group in inner.param_groups:
            group['lr']=lr
        po,uo=training_orders(args.seed,epoch,len(train['p_a']),len(train['u_a']))
        for start in range(next_step,len(uo),batch):
            end=min(start+batch,len(uo))
            loss=step(model,opt,cache,train,po[start:end],uo[start:end])
            epoch_loss+=loss*(end-start)
            if (start//batch)%1000==0:
                event({'event':'progress','epoch':epoch,'comparisons_done':end,'loss':loss,
                    'epoch_seconds':time.monotonic()-epoch_started})
            if (start//batch+1)%10000==0:
                save_resume(resume_path,model,inner,opt,epoch,end,epoch_loss,protocol_sha)
        event({'event':'epoch','epoch':epoch,'weighted_loss':epoch_loss/len(uo),
            'epoch_seconds':time.monotonic()-epoch_started,'lr':lr})
        if epoch in protocol['evaluation_epochs']:
            z=fitted_features(model,cache,train,args.seed)
            scores=cached_scores(model,z,development['a'],development['b'])
            metric=concordance(scores,development['positive'],development['weight'])
            checkpoint=root/f'epoch_{epoch:02d}.pt'
            prediction=root/f'epoch_{epoch:02d}_C3_development.npy'
            if checkpoint.exists() or prediction.exists():
                raise RuntimeError('Existing evaluated checkpoint: audit interruption before resuming')
            torch.save(model.state_dict(),checkpoint)
            with prediction.open('xb') as f:
                np.save(f,scores,allow_pickle=False)
            write(root/f'epoch_{epoch:02d}.json',{'seed':args.seed,'epoch':epoch,'at_utc':now(),
                'C3_development_concordance':metric,'checkpoint':record(checkpoint),
                'development_predictions':record(prediction),'protocol_sha256':protocol_sha},exclusive=True)
            event({'event':'development','epoch':epoch,'C3_concordance':metric})
            del z,scores
        next_step=0; epoch_loss=0.
        save_resume(resume_path,model,inner,opt,epoch+1,0,0.,protocol_sha)
    write(root/'COMPLETE.json',{'completed_at_utc':now(),'seed':args.seed,'protocol_sha256':protocol_sha,
        'elapsed_this_process_seconds':time.monotonic()-started,'epochs':epochs,
        'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'test_pairs_read':False,'test_truth_read':False},exclusive=True)

if __name__=='__main__':
    main()
