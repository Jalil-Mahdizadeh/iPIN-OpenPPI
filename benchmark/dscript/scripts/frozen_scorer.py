"""One frozen original predictor; no training interfaces or truth inputs."""
from pathlib import Path
import numpy as np
import torch
from common import read
from native_adapter import create, learned_digest

SCORERS=('dscript_original',)
REFERENCES=('ipin_baseline','ipin_optimized')
ALL_SCORERS=SCORERS+REFERENCES


class Scorer:
    def __init__(self,bundle,device='cuda',config=None):
        root=Path(bundle); config=config or read(root/'SCORER_FREEZE.json')
        self.device=device
        self.offsets=np.load(root/'features/offsets.npy',allow_pickle=False)
        values=np.load(root/'features/projected.npy',mmap_mode='r',allow_pickle=False)
        self.features=torch.tensor(values,device=device,dtype=torch.float32)
        if self.features.shape!=(int(self.offsets[-1]),100) or not torch.isfinite(self.features).all():
            raise RuntimeError('Invalid frozen projected residues')
        self.model=create(device=device,max_length=config['maximum_length'],tile_area=config['tile_area'])
        if learned_digest(self.model)!=config['learned_state_sha256']:
            raise RuntimeError('Learned original weights changed')

    def scores(self,a,b,batch_size=512):
        a=np.asarray(a,np.int64);b=np.asarray(b,np.int64)
        if a.shape!=b.shape or a.ndim!=1 or (a<0).any() or (b<0).any() or (a>=len(self.offsets)-1).any() or (b>=len(self.offsets)-1).any():
            raise RuntimeError('Invalid endpoint indices')
        result=np.empty((len(a),1),np.float64)
        with torch.inference_mode():
            for start in range(0,len(a),batch_size):
                stop=min(start+batch_size,len(a))
                pending=torch.empty(stop-start,device=self.device,dtype=torch.float32)
                for j,(x,y) in enumerate(zip(a[start:stop],b[start:stop])):
                    p=self.features[self.offsets[x]:self.offsets[x+1]][None]
                    q=self.features[self.offsets[y]:self.offsets[y+1]][None]
                    pending[j]=self.model.predict(p,q)
                result[start:stop,0]=pending.cpu().numpy()
        if not np.isfinite(result).all() or (result<0).any() or (result>1).any():
            raise RuntimeError('Nonfinite or out-of-range original D-SCRIPT scores')
        return result
