"""Frozen GP scoring only: no sequence encoder, train inputs, or truth access."""
from pathlib import Path
import math
import numpy as np
import torch
from common import SEEDS

MEMBERS=('tuna_original',)+tuple(f'tuna_retrained_seed{s}' for s in SEEDS)
SCORERS=('tuna_original','tuna_retrained_ensemble')+MEMBERS[1:]
REFERENCES=('ipin_baseline','ipin_optimized')
ALL_SCORERS=SCORERS+REFERENCES

class Scorer:
    def __init__(self,bundle,device='cuda'):
        self.device=device; self.members=[]
        for name in MEMBERS:
            path=Path(bundle)
            state=torch.load(path/'weights'/f'{name}.pt',map_location=device,weights_only=True)
            z=torch.from_numpy(np.load(path/'features'/f'{name}.npy',allow_pickle=False)).to(device)
            if z.ndim!=2 or z.shape[1]!=64 or not torch.isfinite(z).all():
                raise RuntimeError('Invalid frozen endpoint features')
            self.members.append((name,z,state['gp_layer.weight_mat'],state['gp_layer.output_weights'],state['gp_layer.covariance']))

    def scores(self,a,b,batch_size=1024):
        a=np.asarray(a,np.int64); b=np.asarray(b,np.int64)
        if a.shape!=b.shape or a.ndim!=1 or (a<0).any() or (b<0).any():
            raise RuntimeError('Invalid score indices')
        result=np.empty((len(a),len(SCORERS)),np.float64)
        with torch.inference_mode():
            for index,(name,z,w,beta,covariance) in enumerate(self.members):
                column=0 if index==0 else index+1
                for start in range(0,len(a),batch_size):
                    stop=min(start+batch_size,len(a))
                    f=torch.maximum(z[a[start:stop]],z[b[start:stop]])
                    phase=f@w
                    phi=math.sqrt(2/2048)*torch.cat([torch.cos(phase),torch.sin(phase)],dim=1)
                    logits=(phi@beta).reshape(-1)
                    variance=(phi*(covariance@phi.T).T).sum(1)
                    score=logits/torch.sqrt(1+math.pi/8*variance)
                    if name=='tuna_original':
                        score=torch.sigmoid(score)
                    result[start:stop,column]=score.cpu().numpy()
            result[:,1]=result[:,2:].mean(1,dtype=np.float64)
        if not np.isfinite(result).all():
            raise RuntimeError('Nonfinite frozen TUnA scores')
        return result
