"""Selected three-seed PU-D-SCRIPT scorer; no training data or truth inputs."""
from pathlib import Path
import numpy as np
import torch
from common import SEEDS,read
from model import fresh,scores
from native_adapter import learned_digest

MEMBERS=tuple(f'dscript_seed_{seed}' for seed in SEEDS)
SCORERS=('dscript_retrained',)+MEMBERS
REFERENCES=('dscript_original','ipin_baseline','ipin_optimized')
ALL_SCORERS=SCORERS+REFERENCES


class Scorer:
    def __init__(self,bundle,device='cuda',config=None):
        root=Path(bundle);config=config or read(root/'SCORER_FREEZE.json')
        self.models=[];self.values=[];self.offsets=np.load(root/'features/offsets.npy',allow_pickle=False)
        for seed,name in zip(SEEDS,MEMBERS,strict=True):
            model=fresh(seed,device).eval()
            model.load_state_dict(torch.load(root/'weights'/f'{name}.pt',map_location=device,weights_only=True),strict=True)
            model.requires_grad_(False)
            assert learned_digest(model)==config['learned_state_sha256'][name]
            values=np.load(root/'features'/f'{name}.npy',mmap_mode='r',allow_pickle=False)
            features=torch.tensor(values,device=device,dtype=torch.float32)
            assert features.shape==(int(self.offsets[-1]),100) and torch.isfinite(features).all()
            self.models.append(model);self.values.append(features)

    def scores(self,a,b):
        a=np.asarray(a,np.int64);b=np.asarray(b,np.int64)
        assert a.shape==b.shape and a.ndim==1
        assert (a>=0).all() and (b>=0).all() and (a<len(self.offsets)-1).all() and (b<len(self.offsets)-1).all()
        members=np.column_stack([scores(model,values,self.offsets,a,b) for model,values in zip(self.models,self.values,strict=True)])
        result=np.column_stack([members.mean(axis=1,dtype=np.float64),members])
        if not np.isfinite(result).all():raise RuntimeError('Nonfinite selected model scores')
        return result
