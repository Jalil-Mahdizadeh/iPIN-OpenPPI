"""TRAIN-only forward/backward, native fidelity and resource qualification."""
import copy
from pathlib import Path
import time
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from common import arrays,cuda,read,write,now
from model import fresh,contact_logit,step


class Fixtures:
    def __init__(self,values,device):self.values=values;self.device=device
    def crop(self,index):
        v=self.values[int(index)];size=min(len(v),512)
        start=int(torch.randint(len(v)-size+1,()).item())
        return torch.from_numpy(v[start:start+size].copy()).to(self.device)[None]


def main():
    device=cuda();meta=read('/data/sequences.json');train=arrays('/data/training.npz')
    train['normalized_u_weight']=train['u_weight']/train['u_weight'].mean()
    # Separate fixed TRAIN fixtures, never checkpointed for formal training.
    p=np.arange(64);u=np.arange(64)
    ids=np.unique(np.concatenate([train['p_a'][p],train['p_b'][p],train['u_a'][u],train['u_b'][u]]))
    assert all(meta['partition'][int(i)]=='train' for i in ids)
    lm=get_pretrained('lm_v1').to(device).eval().requires_grad_(False);alphabet=Uniprot21();raw={}
    with torch.inference_mode():
        for i in ids:
            seq=meta['sequence'][int(i)]
            raw[int(i)]=lm.transform(torch.from_numpy(alphabet.encode(seq.encode())).long()[None].to(device))[0].cpu().numpy()
    del lm;torch.cuda.empty_cache();cache=Fixtures(raw,device)
    model=fresh(771,device);model.eval();native=copy.deepcopy(model);native.do_sigmoid=True
    a,b=cache.crop(train['p_a'][0]),cache.crop(train['p_b'][0])
    with torch.inference_mode():
        _,logit=contact_logit(model,a,b)
        error=float((torch.sigmoid(logit)-native.predict(a,b)).abs().max())
    assert error<=1e-6
    # Training path must match unmodified native modules, including gradients.
    left=copy.deepcopy(model).train();right=copy.deepcopy(model).train()
    right.__class__=type(native).__mro__[1]  # Native DSCRIPTModel, no adapter.
    torch.manual_seed(882);torch.cuda.manual_seed_all(882)
    c1,r1=left.map_predict(a,b);loss1=r1+c1.mean();loss1.backward()
    torch.manual_seed(882);torch.cuda.manual_seed_all(882)
    c2,r2=right.map_predict(a,b);loss2=r2+c2.mean();loss2.backward()
    grad_error=max(float((x.grad-y.grad).abs().max()) for x,y in zip(left.parameters(),right.parameters(),strict=True) if x.grad is not None)
    assert float((c1-c2).abs().max())<=1e-6 and abs(float(r1-r2))<=1e-6 and grad_error<=1e-6
    del left,right,native,model,c1,c2,loss1,loss2,r1,r2
    trials=[]
    for batch in (4,8,16):
        model=fresh(991,device).train();opt=torch.optim.Adam([x for x in model.parameters() if x.requires_grad],lr=1e-3)
        torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats()
        step(model,opt,cache,train,p[:batch],u[:batch])
        torch.cuda.synchronize();started=time.monotonic();losses=[]
        for k in range(8):
            start=(k*batch)%(64-batch+1)
            losses.append(step(model,opt,cache,train,p[start:start+batch],u[start:start+batch]))
        torch.cuda.synchronize();elapsed=time.monotonic()-started
        trial={'comparison_batch':batch,'comparisons':8*batch,'seconds':elapsed,
               'comparisons_per_second':8*batch/elapsed,'estimated_8_epoch_training_hours':16_000_000/(8*batch/elapsed)/3600,
               'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'initial':losses[0],'last':losses[-1]}
        trials.append(trial);print(trial,flush=True)
        del model,opt;torch.cuda.empty_cache()
    # Deliberately overfit tiny fixed TRAIN examples to check that learning works.
    model=fresh(441,device).train();opt=torch.optim.Adam([x for x in model.parameters() if x.requires_grad],lr=1e-3)
    learning=[]
    for k in range(32):learning.append(step(model,opt,cache,train,p[:4],u[:4])['ranking_loss'])
    assert np.isfinite(learning).all() and np.mean(learning[-8:])<np.mean(learning[:8])
    result={'at_utc':now(),'passed':True,'trials':trials,'native_probability_max_error':error,'native_gradient_max_error':grad_error,
            'tiny_TRAIN_learning_first8_mean':float(np.mean(learning[:8])),'tiny_TRAIN_learning_last8_mean':float(np.mean(learning[-8:])),
            'formal_training_performed':False,'test_pairs_read':False,'test_truth_read':False,'pilots_discarded':True}
    write('/output/PILOT.json',result,exclusive=True);print(result,flush=True)


if __name__=='__main__':main()
