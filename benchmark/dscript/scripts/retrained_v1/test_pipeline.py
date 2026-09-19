"""Synthetic scorer, manifest, metric, worst-crop and resume qualification."""
from pathlib import Path
import tempfile
import time
import numpy as np
import pyarrow as pa
import torch
from common import SEEDS,cuda,now,write
from comparison import prediction_values,token_for,verify
from benchmark_metrics import qualify
from frozen_scorer import MEMBERS,Scorer
from model import fresh,contact_logit,step
from native_adapter import learned_digest
from pilot import Fixtures
from train import save_resume,load_resume


def main():
    device=cuda();root=Path('/output/tmp');root.mkdir(exist_ok=True);errors=[]
    with tempfile.TemporaryDirectory(prefix='pipeline-fixture-',dir=root) as directory:
        bundle=Path(directory);(bundle/'weights').mkdir();(bundle/'features').mkdir()
        lengths=np.arange(32,40,dtype=np.int64);offsets=np.concatenate(([0],np.cumsum(lengths)))
        raw={i:np.random.default_rng(193+i).normal(0,.1,size=(n,6165)).astype(np.float32) for i,n in enumerate(lengths)}
        a=np.arange(8);b=np.roll(a,1);refs=[];digests={}
        for seed,name in zip(SEEDS,MEMBERS,strict=True):
            model=fresh(seed,device).eval();features=[];reference=[]
            with torch.inference_mode():
                for i in range(8):features.append(model.embedding(torch.from_numpy(raw[i]).to(device)[None])[0].cpu().numpy())
                for x,y in zip(a,b,strict=True):reference.append(float(contact_logit(model,torch.from_numpy(raw[x]).to(device)[None],torch.from_numpy(raw[y]).to(device)[None])[1]))
            refs.append(reference);digests[name]=learned_digest(model)
            with (bundle/'features'/f'{name}.npy').open('xb') as handle:np.save(handle,np.concatenate(features),allow_pickle=False)
            torch.save(model.state_dict(),bundle/'weights'/f'{name}.pt')
        with (bundle/'features/offsets.npy').open('xb') as handle:np.save(handle,offsets,allow_pickle=False)
        scorer=Scorer(bundle,device,config={'learned_state_sha256':digests});values=scorer.scores(a,b)
        errors.extend(float(np.max(np.abs(values[:,j+1]-reference))) for j,reference in enumerate(refs))
        errors.append(float(np.max(np.abs(values-scorer.scores(b,a)))))
        errors.append(float(np.max(np.abs(values-np.concatenate([scorer.scores(a[i:i+1],b[i:i+1]) for i in range(8)])))))
        assert max(errors)<=1e-4 and np.array_equal(values[:,0],values[:,1:].mean(1,dtype=np.float64))
        del scorer,model;torch.cuda.empty_cache()
        train={'p_a':a,'p_b':b,'u_a':np.roll(a,2),'u_b':np.roll(a,3),'normalized_u_weight':np.linspace(.5,1.5,8)}
        cache=Fixtures(raw,device);model=fresh(881,device).train()
        opt=torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=1e-3)
        idx=np.arange(4);step(model,opt,cache,train,idx,idx)
        checkpoint=bundle/'resume.pt';save_resume(checkpoint,model,opt,1,4,{'loss':1.,'ranking_loss':2.,'contact_penalty':3.},'fixture')
        expected=step(model,opt,cache,train,idx,idx);expected_state={k:v.detach().clone() for k,v in model.state_dict().items()}
        resumed=fresh(999,device).train();resumed_opt=torch.optim.Adam([p for p in resumed.parameters() if p.requires_grad],lr=1e-3)
        assert load_resume(checkpoint,resumed,resumed_opt,'fixture',device)[:2]==(1,4)
        observed=step(resumed,resumed_opt,cache,train,idx,idx)
        assert expected==observed and all(torch.equal(expected_state[k],v) for k,v in resumed.state_dict().items())
        del model,resumed,opt,resumed_opt,expected_state;torch.cuda.empty_cache()
        # Worst declared crop size, including backward/optimizer with batch 16.
        worst={i:np.random.default_rng(i+515).normal(0,.1,size=(512,6165)).astype(np.float32) for i in range(8)}
        cache=Fixtures(worst,device);model=fresh(668,device).train()
        opt=torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=1e-3)
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();started=time.monotonic()
        metrics=step(model,opt,cache,train,np.tile(a,2),np.tile(a,2));torch.cuda.synchronize()
        worst_probe={'comparison_batch':16,'endpoint_crop_length':512,'seconds':time.monotonic()-started,
                     'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'metrics':metrics}
        assert worst_probe['peak_gpu_bytes']<torch.cuda.get_device_properties(device).total_memory*.8
    tokens=pa.array(['a','b','c']);ordered=[1.,2.,3.]
    for col in ('score','dscript_original'):
        table=pa.table({'candidate_token':['c','a','b'],col:[3.,1.,2.]})
        assert np.array_equal(prediction_values(tokens,table),ordered)
    bad=[pa.table({'candidate_token':['a','a','c'],'score':[1.,2.,3.]}),
         pa.table({'candidate_token':['a','b','d'],'score':[1.,2.,3.]}),
         pa.table({'candidate_token':['a','b','c'],'score':[1.,float('nan'),3.]})]
    for table in bad:
        try:prediction_values(tokens,table)
        except RuntimeError:pass
        else:raise AssertionError('Invalid reference accepted')
    try:verify('/output',[{'path':'../outside','bytes':0,'sha256':'invalid'}])
    except RuntimeError:pass
    else:raise AssertionError('Unsafe manifest accepted')
    assert token_for('C1_test','pair:dummy')!=token_for('C3_test','pair:dummy')
    result={'at_utc':now(),'passed':True,'scorer_errors':errors,'logit_tolerance':1e-4,
            'resume_next_step_model_and_metrics_bit_identical':True,'bad_reference_inputs_rejected':len(bad),
            'original_reference_column_supported':True,'metric':qualify(device),'worst_crop_probe':worst_probe,
            'test_pairs_read':False,'test_truth_read':False,'formal_training_performed':False}
    write('/output/PIPELINE_QUALIFICATION.json',result,exclusive=True);print(result,flush=True)


if __name__=='__main__':main()
