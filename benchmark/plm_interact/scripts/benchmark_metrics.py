"""The historical weighted PU metric and paired component draws, on GPU.

CPU oracle below is deliberately small and independent of the GPU reduction.
Draw order, exact-score ties and same-component multiplicities are preserved.
"""
import hashlib
import numpy as np
import torch
from common import concordance

def component_counts(component_a,component_b,cell,replicates=2000):
    components=sorted(set(component_a)|set(component_b))
    index={x:i for i,x in enumerate(components)}
    a=np.asarray([index[x] for x in component_a],np.int64)
    b=np.asarray([index[x] for x in component_b],np.int64)
    seed=int.from_bytes(hashlib.sha256(f'20260803:bootstrap:{cell}'.encode()).digest()[:8],'big')
    generator=np.random.Generator(np.random.PCG64DXSM(seed))
    draws=generator.integers(0,len(components),(replicates,len(components)),dtype=np.int64)
    counts=np.zeros((replicates,len(components)),np.int32)
    np.add.at(counts,(np.arange(replicates)[:,None],draws),1)
    return a,b,counts,{'seed':seed,'replicates':replicates,'participating_components':len(components),
        'multiplicities_sha256':hashlib.sha256(counts.astype('<i4').tobytes()).hexdigest()}

def bootstrap(scores,positive,weights,component_a,component_b,cell,replicates=2000,device='cuda',batch=16):
    scores=np.asarray(scores,np.float64); mask=np.asarray(positive,bool); weights=np.asarray(weights,np.float64)
    if scores.ndim!=2 or len(mask)!=len(scores) or len(weights)!=len(scores):
        raise RuntimeError('Invalid metric shapes')
    a,b,counts,metadata=component_counts(component_a,component_b,cell,replicates)
    counts=torch.as_tensor(counts,device=device,dtype=torch.float64)
    pa=torch.as_tensor(a[mask],device=device); pb=torch.as_tensor(b[mask],device=device)
    result=np.full((scores.shape[1],replicates),np.nan,np.float64)
    points=[]
    for column in range(scores.shape[1]):
        points.append(concordance(scores[:,column],mask,weights))
        p=scores[mask,column]; u=scores[~mask,column]
        order=np.argsort(u,kind='mergesort')
        left=torch.as_tensor(np.searchsorted(u[order],p,'left'),device=device)
        right=torch.as_tensor(np.searchsorted(u[order],p,'right'),device=device)
        ua=torch.as_tensor(a[~mask][order],device=device); ub=torch.as_tensor(b[~mask][order],device=device)
        design=torch.as_tensor(weights[~mask][order],device=device)
        for start in range(0,replicates,batch):
            count=counts[start:start+batch]
            pm=torch.where(pa==pb,count[:,pa],count[:,pa]*count[:,pb])
            um=torch.where(ua==ub,count[:,ua],count[:,ua]*count[:,ub])
            prefix=torch.cat([torch.zeros(len(count),1,device=device,dtype=torch.float64),
                torch.cumsum(um*design,dim=1)],dim=1)
            denominator=pm.sum(1)*prefix[:,-1]
            value=(pm*(prefix[:,left]+prefix[:,right])*.5).sum(1)/denominator
            value[denominator<=0]=float('nan')
            result[column,start:start+len(count)]=value.cpu().numpy()
    return np.asarray(points),result,metadata

def qualify(device='cuda'):
    rng=np.random.default_rng(771)
    n=71; scores=rng.integers(0,7,size=(n,4)).astype(np.float64)
    mask=np.arange(n)<17; weights=rng.integers(1,30,size=n).astype(np.float64)/7
    ca=[f'c{x}' for x in rng.integers(0,9,n)]; cb=[f'c{x}' for x in rng.integers(0,9,n)]
    points,draws,meta=bootstrap(scores,mask,weights,ca,cb,'C3_test',replicates=41,device=device,batch=3)
    a,b,counts,_=component_counts(ca,cb,'C3_test',41)
    reference=np.full_like(draws,np.nan)
    for j in range(scores.shape[1]):
        for k,count in enumerate(counts):
            mult=np.where(a==b,count[a],count[a]*count[b])
            totalp=mult[mask].sum(); totalu=(weights[~mask]*mult[~mask]).sum()
            if totalp and totalu:
                total=0.
                for i in np.flatnonzero(mask):
                    for q in np.flatnonzero(~mask):
                        total+=mult[i]*mult[q]*weights[q]*((scores[i,j]>scores[q,j])+.5*(scores[i,j]==scores[q,j]))
                reference[j,k]=total/(totalp*totalu)
    error=float(np.nanmax(np.abs(draws-reference)))
    if not np.array_equal(np.isnan(draws),np.isnan(reference)) or error>1e-12:
        raise RuntimeError('GPU/independent brute-force bootstrap qualification failed')
    return {'passed':True,'maximum_absolute_error':error,'tolerance':1e-12,'rows':n,
        'replicates':41,'scorers':4,'covers_ties_unequal_weights_same_components':True,'draws':meta}
