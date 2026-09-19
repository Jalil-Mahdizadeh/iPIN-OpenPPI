#!/usr/bin/env python3
"""Numerical qualification against the actual upstream batch-one predictor."""
from __future__ import annotations
import argparse
import platform
import time
from pathlib import Path
import numpy as np
import torch
from adapter import cached_scores, endpoint_features, enable_sdpa, load_original, native_scores
from common import concordance, cuda, now, record, write

def pad(proteins,device):
    lengths=[len(x) for x in proteins]
    output=torch.zeros(len(proteins),max(lengths),640,device=device)
    for i,x in enumerate(proteins):
        output[i,:len(x)]=x.to(device)
    return output,lengths

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--checkpoint',type=Path,default=Path('/weights/bernett_original.pt'))
    p.add_argument('--output',type=Path,default=Path('/output/QUALIFICATION.json'))
    args=p.parse_args()
    device=cuda(); started=time.monotonic()
    model=load_original(args.checkpoint,device)
    lengths=[7,31,137,513,1025]
    proteins=[torch.randn(n,640,device=device)*.25 for n in lengths]
    a=np.array([0,1,2,3,4,0,4,2]); b=np.array([1,2,3,4,0,0,4,1])
    reference=native_scores(model,[proteins[i] for i in a],[proteins[i] for i in b]).cpu().numpy()
    swapped=native_scores(model,[proteins[i] for i in b],[proteins[i] for i in a]).cpu().numpy()
    x,lens=pad(proteins,device)
    with torch.inference_mode():
        z=endpoint_features(model,x,lens)
        factored=cached_scores(model,z,a,b,probabilities=True,batch_size=3)
        singles=torch.cat([endpoint_features(model,p[None],[len(p)]) for p in proteins])
        sing_scores=cached_scores(model,singles,a,b,probabilities=True,batch_size=1)
    enable_sdpa(model)
    with torch.inference_mode():
        fast_z=endpoint_features(model,x,lens)
        fast_scores=cached_scores(model,fast_z,a,b,probabilities=True,batch_size=5)
    accelerated_native=native_scores(model,[proteins[i] for i in a],[proteins[i] for i in b]).cpu().numpy()
    errors={'native_order':float(np.max(np.abs(reference-swapped))),
        'native_vs_factored_probability':float(np.max(np.abs(reference-factored))),
        'factored_batch_padding_probability':float(np.max(np.abs(factored-sing_scores))),
        'native_vs_sdpa_factored_probability':float(np.max(np.abs(reference-fast_scores))),
        'native_vs_sdpa_native_probability':float(np.max(np.abs(reference-accelerated_native))),
        'sdpa_endpoint_feature':float((z-fast_z).abs().max())}
    expected=(2*1+3*.5+5*0+2*1+3*1+5*.5)/20
    actual=concordance([2,3,1,2,3],[True,True,False,False,False],[1,1,2,3,5])
    # Brute-force definition, including weighted ties.
    brute=sum(w*((ps>us)+.5*(ps==us)) for ps in [2,3] for us,w in [(1,2),(2,3),(3,5)])/20
    errors['weighted_concordance']=abs(actual-brute)
    inaccessible={str(x):not x.exists() for x in [Path('/source'),Path('/repo'),Path('/nobackup/proj/disk/theo-storage/personal/jalil/iPIN-OpenPPI/.private')]}
    passed=all(v<=1e-5 for k,v in errors.items() if k!='sdpa_endpoint_feature') and errors['sdpa_endpoint_feature']<=1e-4 and all(inaccessible.values())
    result={'at_utc':now(),'passed':passed,'elapsed_seconds':time.monotonic()-started,
        'errors':errors,'probability_absolute_tolerance':1e-5,'feature_absolute_tolerance':1e-4,
        'fixture':'fixed seeded synthetic residue matrices; no test interactions or labels',
        'fixture_lengths':lengths,'pair_count':len(a),'checkpoint':record(args.checkpoint),
        'native_inference_batch_size':1,'cuda':torch.version.cuda,'torch':torch.__version__,
        'gpu':torch.cuda.get_device_name(),'architecture':platform.machine(),
        'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'precision':'FP32, TF32 disabled',
        'inaccessible_host_paths':inaccessible,'network_isolation':'not claimed; no runtime network downloads',
        'pid_namespace_isolation':'not claimed; HPC configuration disables PID virtualization',
        'formula_note':'Cached inference preserves this pinned implementation: block-diagonal attention masks, first-column pooling, AB/BA elementwise max. Training is not factorized.',
        'native_batch_note':'Released batch-one test predictor is the oracle; upstream mean-field broadcasting for B>1 is not used.'}
    write(args.output,result)
    print(result,flush=True)
    if not passed:
        raise RuntimeError('TUnA qualification failed; do not score protected test')

if __name__=='__main__':
    main()
