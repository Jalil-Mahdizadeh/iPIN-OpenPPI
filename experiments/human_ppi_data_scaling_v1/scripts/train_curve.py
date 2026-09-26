"""Unchanged native PU-TUnA recipe across prospectively fixed positive budgets."""
import argparse
import json
import os
from pathlib import Path
import time
import numpy as np
import torch
from adapter import cached_scores
from common import concordance, cuda
from residues import Residues
from training import fitted_features, make_model, optimizer, step, training_orders
from train import save_resume
from study import arrays, check, now, read, record, save, sha, write

def restore(path,model,inner,opt,identity,device):
    state=torch.load(path,map_location=device,weights_only=True)
    check(state['protocol_sha256']==identity, 'Resume execution mismatch')
    model.load_state_dict(state['model'],strict=True); inner.load_state_dict(state['optimizer'])
    parameters=[p for group in inner.param_groups for p in group['params']]
    for p,v in zip(parameters,state['lookahead'],strict=True): opt.state[p]['cached_params'].copy_(v)
    opt.step_counter=state['lookahead_step']
    torch.set_rng_state(state['cpu_rng'].cpu()); torch.cuda.set_rng_state(state['cuda_rng'].cpu())
    return state['epoch'],state['next_step'],state['epoch_loss']

def verify_execution():
    frozen=read('/freeze/EXECUTION_FREEZE.json')
    for group,directory in [('study_code','/code'),('native_code','/native')]:
        for item in frozen[group]: check(sha(Path(directory)/item['name'])==item['sha256'], 'Frozen code changed: '+item['name'])
    for item in frozen['data_files']: check(sha(Path('/data')/item['name'])==item['sha256'], 'Frozen data changed: '+item['name'])
    check(sha('/output/residue_cache/RESIDUE_CACHE_MANIFEST.json')==frozen['residue_manifest_sha256'], 'Residue freeze mismatch')
    check(sha('/output/QUALIFICATION.json')==frozen['qualification_sha256'] and read('/output/QUALIFICATION.json')['passed'], 'Qualification missing')
    check(not Path('/truth').exists() and not Path('/candidates').exists() and not Path('/nobackup').exists(), 'Excess fitting visibility')
    return sha('/freeze/EXECUTION_FREEZE.json')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--budget',type=int,required=True); p.add_argument('--seed',type=int,required=True)
    p.add_argument('--resume',action='store_true'); args=p.parse_args()
    identity=verify_execution(); protocol=read('/data/PROTOCOL.json')
    check(args.budget in protocol['positive_budgets'] and args.seed in protocol['seeds'], 'Unregistered fit')
    check(not Path('/output/PREDICTION_FREEZE.json').exists(), 'No fitting after final prediction freeze')
    root=Path(f'/output/training/budget_{args.budget}/seed_{args.seed}')
    root.mkdir(parents=True,exist_ok=args.resume)
    check(not (root/'COMPLETE.json').exists(), 'Fit already complete')
    device=cuda(args.seed); started=time.monotonic()
    train={**arrays(f'/data/training_{args.budget}.npz'),**arrays('/data/training_unlabeled.npz')}
    train['normalized_u_weight']=train['u_weight']/train['u_weight'].mean()
    legacy=arrays('/data/legacy/development_00.npz')
    reconciled=arrays('/data/development/reconciled/C3.npz'); added=arrays('/data/development/added/C3.npz')
    print({'stage':'loading_frozen_residue_cache','budget':args.budget,'seed':args.seed},flush=True)
    cache=Residues('/data','/output/residue_cache/residues.h5',device)
    model=make_model(args.seed,device); inner,opt=optimizer(model)
    epoch_start,next_step,epoch_loss=1,0,0.
    resume=root/'resume.pt'
    if args.resume and resume.exists(): epoch_start,next_step,epoch_loss=restore(resume,model,inner,opt,identity,device)
    def event(**value):
        data={'at_utc':now(),'budget':args.budget,'seed':args.seed,**value}
        print(data,flush=True)
        with (root/'events.jsonl').open('a') as f: f.write(json.dumps(data,allow_nan=False)+'\n')
    event(event='start',execution_sha256=identity,gpu=torch.cuda.get_device_name(),slurm_job_id=os.environ.get('SLURM_JOB_ID'))
    batch=protocol['comparison_batch']
    for epoch in range(epoch_start,protocol['epochs']+1):
        t=time.monotonic(); model.train(); lr=1e-4*.93**((epoch-1)//2)
        for group in inner.param_groups: group['lr']=lr
        po,uo=training_orders(args.seed,epoch,len(train['p_a']),len(train['u_a']))
        for start in range(next_step,len(uo),batch):
            stop=min(start+batch,len(uo)); loss=step(model,opt,cache,train,po[start:stop],uo[start:stop])
            epoch_loss+=loss*(stop-start)
            if start//batch%1000==0: event(event='progress',epoch=epoch,comparisons=stop,loss=loss,epoch_seconds=time.monotonic()-t)
            if (start//batch+1)%5000==0: save_resume(resume,model,inner,opt,epoch,stop,epoch_loss,identity)
        event(event='epoch',epoch=epoch,loss=epoch_loss/len(uo),seconds=time.monotonic()-t,lr=lr)
        if epoch in protocol['evaluation_epochs']:
            z=fitted_features(model,cache,train,args.seed)
            old_score=cached_scores(model,z,legacy['a'],legacy['b'])
            new_score=cached_scores(model,z,added['a'],added['b'])
            metrics={
              'dev_1':concordance(old_score,legacy['positive'],legacy['weight']),
              'dev_1_reconciled':concordance(old_score,reconciled['positive'],reconciled['weight']),
              'dev_added':concordance(new_score,added['positive'],added['weight'])}
            metrics['dev_2_macro']=.5*(metrics['dev_1_reconciled']+metrics['dev_added'])
            checkpoint=root/f'epoch_{epoch:02d}.pt'; prediction=root/f'epoch_{epoch:02d}_C3.npz'
            check(not checkpoint.exists() and not prediction.exists(), 'Interrupted checkpoint requires review; refusing overwrite')
            torch.save(model.state_dict(),checkpoint); save(prediction,legacy=old_score,added=new_score)
            write(root/f'epoch_{epoch:02d}.json',{'at_utc':now(),'budget':args.budget,'seed':args.seed,'epoch':epoch,
                'metrics':metrics,'checkpoint':record(checkpoint),'prediction':record(prediction),'execution_sha256':identity})
            event(event='development',epoch=epoch,**metrics)
            del z,old_score,new_score
        next_step,epoch_loss=0,0.
        save_resume(resume,model,inner,opt,epoch+1,0,0.,identity)
    write(root/'COMPLETE.json',{'at_utc':now(),'budget':args.budget,'seed':args.seed,'execution_sha256':identity,
       'epochs':protocol['epochs'],'elapsed_this_process_seconds':time.monotonic()-started,
       'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'test_pairs_read':False,'test_truth_read':False})

if __name__=='__main__': main()
