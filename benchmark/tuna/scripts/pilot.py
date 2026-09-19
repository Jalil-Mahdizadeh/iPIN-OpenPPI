#!/usr/bin/env python3
"""Short disposable TRAIN-only throughput/gradient pilot, never a final fit."""
import argparse
import time
from pathlib import Path
import numpy as np
import torch
from common import arrays, cuda, now, write
from residues import Residues
from training import curvature_test, make_model, optimizer, step

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,default=Path('/data'))
    p.add_argument('--cache',type=Path,default=Path('/output/residue_cache/residues.h5'))
    p.add_argument('--output',type=Path,default=Path('/output/PILOT.json'))
    args=p.parse_args()
    device=cuda(); train=arrays(args.data/'training.npz')
    train['normalized_u_weight']=train['u_weight']/np.mean(train['u_weight'])
    cache=Residues(args.data,args.cache,device)
    curvature_error=curvature_test(device)
    rng=np.random.default_rng(90210); results=[]
    for batch in (16,32,64):
        model=make_model(90210,device); model.train(); inner,opt=optimizer(model)
        torch.cuda.reset_peak_memory_stats()
        losses=[]
        for i in range(16):
            positives=rng.integers(len(train['p_a']),size=batch)
            unlabeled=rng.integers(len(train['u_a']),size=batch)
            if i==4:
                torch.cuda.synchronize(); started=time.monotonic()
            losses.append(step(model,opt,cache,train,positives,unlabeled))
        torch.cuda.synchronize(); elapsed=time.monotonic()-started
        results.append({'comparison_batch':batch,'timed_steps':12,'seconds':elapsed,
            'comparisons_per_second':batch*12/elapsed,'projected_full_U_epoch_hours':2000000/(batch*12/elapsed)/3600,
            'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'losses':losses})
        del model,opt,inner
        torch.cuda.empty_cache()
        print(results[-1],flush=True)
    write(args.output,{'at_utc':now(),'purpose':'disposable TRAIN-only throughput pilot; not a selected model',
        'test_accessed':False,'gpu':torch.cuda.get_device_name(),'pu_hessian_max_absolute_error':curvature_error,
        'trials':results})

if __name__=='__main__':
    main()
