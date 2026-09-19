#!/usr/bin/env python3
"""Synthetic/private-free tests of the minimal final scorer and identity checks."""
from pathlib import Path
import tempfile
import numpy as np
import pyarrow as pa
import torch
from adapter import cached_scores, create, load_original
from benchmark_metrics import qualify
from common import SEEDS, cuda, now, write
from comparison import prediction_values, token_for, verify
from frozen_scorer import MEMBERS, Scorer

def main():
    device=cuda(); root=Path('/output/.tmp'); root.mkdir(exist_ok=True)
    errors=[]
    with tempfile.TemporaryDirectory(prefix='pipeline-fixture-',dir=root) as directory:
        bundle=Path(directory); (bundle/'weights').mkdir(); (bundle/'features').mkdir()
        a=np.arange(17); b=np.roll(a,1); references=[]
        for i,name in enumerate(MEMBERS):
            model=load_original('/weights/bernett_original.pt',device) if i==0 else create(seed=SEEDS[i-1],device=device,fresh_initialize=True)
            if i:
                model.gp_layer.fitted=True; model.eval()
            z=torch.randn(17,64,device=device)*.2
            references.append(cached_scores(model,z,a,b,probabilities=(i==0)))
            torch.save(model.state_dict(),bundle/'weights'/f'{name}.pt')
            np.save(bundle/'features'/f'{name}.npy',z.cpu().numpy(),allow_pickle=False)
            del model,z
        scorer=Scorer(bundle,device)
        values=scorer.scores(a,b,batch_size=7)
        for j,reference in zip([0,2,3,4],references):
            errors.append(float(np.max(np.abs(values[:,j]-reference))))
        errors.append(float(np.max(np.abs(values-scorer.scores(b,a,batch_size=7)))))
        errors.append(float(np.max(np.abs(values-scorer.scores(a,b,batch_size=1)))))
        if max(errors)>1e-5 or not np.array_equal(values[:,1],values[:,2:].mean(1,dtype=np.float64)):
            raise RuntimeError('Minimal final scorer fixture failed')
    tokens=pa.array(['a','b','c'])
    correct=pa.table({'candidate_token':['c','a','b'],'score':[3.,1.,2.]})
    if not np.array_equal(prediction_values(tokens,correct),[1.,2.,3.]):
        raise RuntimeError('Reference identity join failed')
    rejected=0
    for broken in [pa.table({'candidate_token':['a','a','c'],'score':[1.,2.,3.]}),
                   pa.table({'candidate_token':['a','b','d'],'score':[1.,2.,3.]}),
                   pa.table({'candidate_token':['a','b','c'],'score':[1.,float('nan'),3.]})]:
        try:
            prediction_values(tokens,broken)
        except RuntimeError:
            rejected+=1
    if rejected!=3:
        raise RuntimeError('Malformed predictions not rejected')
    try:
        verify('/output',[{'path':'../outside','sha256':'invalid','bytes':0}])
    except RuntimeError:
        pass
    else:
        raise RuntimeError('Unsafe manifest path accepted')
    if token_for('C1_test','pair:dummy')==token_for('C3_test','pair:dummy'):
        raise RuntimeError('Tokens are not cell-specific')
    result={'at_utc':now(),'passed':True,'minimal_scorer_max_absolute_errors':errors,
        'absolute_tolerance':1e-5,'bad_reference_inputs_rejected':rejected,'metric':qualify(device),
        'test_pairs_read':False,'test_truth_read':False}
    write('/output/PIPELINE_QUALIFICATION.json',result); print(result,flush=True)

if __name__=='__main__':
    main()
