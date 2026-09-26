"""Real-data finite-gradient, optimizer/RNG resume and independent metric checks."""
from pathlib import Path
import numpy as np
import torch
from common import cuda
from residues import Residues
from training import make_model, optimizer, step, curvature_test
from train import save_resume
from train_curve import restore
from benchmark_metrics import qualify
from study import arrays, check, now, read, sha, write

def main():
    check(not Path('/output/QUALIFICATION.json').exists(), 'Qualification already completed')
    check(not Path('/truth').exists() and not Path('/candidates').exists(), 'Qualification sees test data')
    device=cuda(20260925)
    cache=Residues('/data','/output/residue_cache/residues.h5',device)
    budget=max(read('/data/PROTOCOL.json')['positive_budgets'])
    train={**arrays(f'/data/training_{budget}.npz'),**arrays('/data/training_unlabeled.npz')}
    train['normalized_u_weight']=train['u_weight']/train['u_weight'].mean()
    model=make_model(20260925,device); inner,opt=optimizer(model); model.train()
    # Include new positive endpoints in a real 64-comparison batch.
    pi=np.arange(len(train['p_a'])-64,len(train['p_a'])); ui=np.arange(64)
    first=step(model,opt,cache,train,pi,ui)
    path=Path('/output/.tmp/qualification_resume.pt')
    save_resume(path,model,inner,opt,1,64,first*64,'qualification')
    expected=step(model,opt,cache,train,pi,ui+64)
    expected_state={k:v.detach().clone() for k,v in model.state_dict().items()}
    other=make_model(20260925,device); other_inner,other_opt=optimizer(other); other.train()
    restore(path,other,other_inner,other_opt,'qualification',device)
    observed=step(other,other_opt,cache,train,pi,ui+64)
    error=max(float((v-expected_state[k]).abs().max()) for k,v in other.state_dict().items())
    check(error<=2e-6 and abs(expected-observed)<=1e-8, 'Optimizer/RNG resume does not reproduce update')
    path.unlink()
    curvature=curvature_test(device); metric=qualify(device)
    write('/output/QUALIFICATION.json',{'at_utc':now(),'passed':True,'device':torch.cuda.get_device_name(),
      'real_comparison_batch':64,'first_loss':first,'resume_loss_absolute_error':abs(expected-observed),
      'resume_state_max_absolute_error':error,'curvature_max_absolute_error':curvature,'metric_oracle':metric,
      'sequence_count':len(cache.meta['sha256']),'peak_gpu_bytes':torch.cuda.max_memory_allocated(),
      'residue_manifest_sha256':sha('/output/residue_cache/RESIDUE_CACHE_MANIFEST.json'),
      'test_pairs_read':False,'test_truth_read':False})
    print(read('/output/QUALIFICATION.json'),flush=True)

if __name__=='__main__': main()
