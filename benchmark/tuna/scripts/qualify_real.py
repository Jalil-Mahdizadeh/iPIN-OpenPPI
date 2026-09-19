#!/usr/bin/env python3
"""TRAIN-only real-residue fidelity, GP-curvature, and tiny-fit tests."""
import time
from pathlib import Path
import numpy as np
import torch
from adapter import cached_scores, create, enable_sdpa, load_original, native_scores
from common import arrays, cuda, now, write
from residues import Residues
from training import curvature_test, make_model, optimizer, step

def main():
    device=cuda(); started=time.monotonic()
    cache=Residues(Path('/data'),Path('/output/residue_cache/residues.h5'),device)
    permitted=[i for i,p in enumerate(cache.meta['partition']) if p=='train']
    ordered=sorted(permitted,key=lambda i:cache.meta['length'][i])
    indices=[ordered[0],ordered[len(ordered)//2],ordered[int(.9*len(ordered))],ordered[-1]]
    proteins=[cache.values[cache.offsets[i]:cache.offsets[i+1]] for i in indices]
    aa=[0,1,2,3]; bb=[1,2,3,0]
    model=load_original('/weights/bernett_original.pt',device)
    reference=native_scores(model,[proteins[i] for i in aa],[proteins[i] for i in bb]).cpu().numpy()
    enable_sdpa(model)
    z=cache.features(model,indices)
    a=np.array(indices); b=np.roll(a,-1)
    cached=cached_scores(model,z,a,b,probabilities=True)
    error=float(np.max(np.abs(reference-cached)))
    del model,z
    torch.cuda.empty_cache()
    train=arrays('/data/training.npz')
    train['normalized_u_weight']=train['u_weight']/np.mean(train['u_weight'])
    model=make_model(90211,device); inner,opt=optimizer(model); model.train()
    positives=np.arange(16); unlabeled=np.arange(16)
    losses=[]
    for i in range(160):
        losses.append(step(model,opt,cache,train,positives,unlabeled))
    reduction=float(np.mean(losses[:20])-np.mean(losses[-20:]))
    curvature=curvature_test(device)
    passed=error<=1e-5 and reduction>0 and curvature<=1e-10
    result={'at_utc':now(),'passed':passed,'elapsed_seconds':time.monotonic()-started,
        'real_fixture_lengths':[len(x) for x in proteins],
        'native_batch_one_vs_cached_max_probability_error':error,
        'tiny_fit_early_loss':float(np.mean(losses[:20])),
        'tiny_fit_late_loss':float(np.mean(losses[-20:])),
        'tiny_fit_loss_reduction':reduction,'tiny_fit_steps':len(losses),
        'PU_Hessian_autograd_error':curvature,'test_pairs_read':False,'test_truth_read':False}
    write('/output/REAL_QUALIFICATION.json',result)
    print(result,flush=True)
    if not passed:
        raise RuntimeError('Real-data qualification failed')

if __name__=='__main__':
    main()
