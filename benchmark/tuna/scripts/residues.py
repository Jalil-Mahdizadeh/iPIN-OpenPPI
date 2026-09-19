"""Full residue cache on the allocated GPU, plus native-policy training crops."""
from pathlib import Path
import h5py
import numpy as np
import torch
from adapter import endpoint_features
from common import read, sha

class Residues:
    def __init__(self,data,cache,device):
        self.meta=read(Path(data)/'sequences.json')
        lengths=np.asarray(self.meta['length'],np.int64)
        offsets=np.concatenate(([0],np.cumsum(lengths)))
        self.device=device
        self.lengths=torch.as_tensor(lengths,device=device)
        self.offsets=torch.as_tensor(offsets,device=device)
        self.values=torch.empty((int(offsets[-1]),640),device=device)
        with h5py.File(cache,'r') as f:
            if not f.attrs.get('complete',False) or f.attrs['sequence_manifest_sha256']!=sha(Path(data)/'sequences.json'):
                raise RuntimeError('Residue cache is not complete or not aligned')
            for i in range(len(lengths)):
                x=f[str(i)][:]
                if x.shape!=(lengths[i],640) or not np.isfinite(x).all():
                    raise RuntimeError('Invalid cached embedding')
                self.values[offsets[i]:offsets[i+1]]=torch.from_numpy(x).to(device)

    def pack(self,indices,width=512,random_crop=True):
        indices=torch.as_tensor(indices,device=self.device)
        lengths=self.lengths[indices]
        n=len(indices)
        if width is None:
            width=int(lengths.max())
        if random_crop:
            starts=(torch.rand(n,device=self.device)*(lengths-width+1).clamp(min=1)).long()
        else:
            if bool((lengths>width).any()):
                raise RuntimeError('Evaluation must not truncate residues')
            starts=torch.zeros(n,dtype=torch.long,device=self.device)
        local=torch.arange(width,device=self.device)[None,:]
        valid=local<lengths[:,None]
        positions=self.offsets[indices,None]+starts[:,None]+local
        positions=torch.minimum(positions,(self.offsets[indices+1]-1)[:,None])
        x=self.values[positions]*valid[:,:,None]
        return x,lengths.clamp(max=width).tolist()

    def features(self,model,indices=None,batch_size=16):
        if model.training:
            raise RuntimeError('Features require eval mode')
        indices=list(range(len(self.meta['length']))) if indices is None else list(map(int,indices))
        order=sorted(indices,key=lambda i:self.meta['length'][i])
        out=torch.full((len(self.meta['length']),64),float('nan'),device=self.device)
        # Limit squared length padding cost for the longest proteins.
        with torch.inference_mode():
            start=0
            while start<len(order):
                length=self.meta['length'][order[min(start+batch_size,len(order))-1]]
                batch=max(1,min(batch_size,16000000//(length*length)))
                subset=order[start:start+batch]
                x,lens=self.pack(subset,width=None,random_crop=False)
                out[subset]=endpoint_features(model,x,lens)
                start+=len(subset)
        return out
