"""Runtime estimate from uniformly sampled TRAIN rows, no validation tuning."""
import time
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from common import arrays,cuda,read,write,now
from model import fresh,step
from pilot import Fixtures


def main():
    device=cuda();meta=read('/data/sequences.json');train=arrays('/data/training.npz')
    train['normalized_u_weight']=train['u_weight']/train['u_weight'].mean()
    rng=np.random.default_rng(172912)
    p=rng.integers(len(train['p_a']),size=64);u=rng.integers(len(train['u_a']),size=64)
    ids=np.unique(np.concatenate([train['p_a'][p],train['p_b'][p],train['u_a'][u],train['u_b'][u]]))
    assert all(meta['partition'][int(i)]=='train' for i in ids)
    lm=get_pretrained('lm_v1').to(device).eval().requires_grad_(False);alphabet=Uniprot21();raw={}
    with torch.inference_mode():
        for i in ids:
            raw[int(i)]=lm.transform(torch.from_numpy(alphabet.encode(meta['sequence'][int(i)].encode())).long()[None].to(device))[0].cpu().numpy()
    del lm;torch.cuda.empty_cache();cache=Fixtures(raw,device)
    model=fresh(337,device).train();opt=torch.optim.Adam([x for x in model.parameters() if x.requires_grad],lr=1e-3)
    step(model,opt,cache,train,p[:16],u[:16]);torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
    started=time.monotonic();losses=[]
    for repeat in range(4):
        for start in range(0,64,16):losses.append(step(model,opt,cache,train,p[start:start+16],u[start:start+16]))
    torch.cuda.synchronize();elapsed=time.monotonic()-started;rate=256/elapsed
    result={'at_utc':now(),'passed':True,'comparison_batch':16,'uniformly_sampled_TRAIN_comparisons':64,'timed_comparisons':256,
            'seconds':elapsed,'comparisons_per_second':rate,'estimated_8_epoch_training_hours':16_000_000/rate/3600,
            'estimated_2_epoch_training_hours':4_000_000/rate/3600,'peak_gpu_bytes':torch.cuda.max_memory_allocated(),
            'first_metrics':losses[0],'last_metrics':losses[-1],
            'caveat':'Small warm-memory TRAIN-only pilot; excludes full file-cache I/O, development scoring and contention; not a guaranteed wall time.',
            'formal_training_performed':False,'test_pairs_read':False,'test_truth_read':False,'pilot_discarded':True}
    write('/output/REPRESENTATIVE_PILOT.json',result,exclusive=True);print(result,flush=True)


if __name__=='__main__':main()
