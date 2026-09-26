"""Paired component bootstrap of the prespecified two-cohort PU objective."""
import numpy as np
import torch
from benchmark_metrics import component_counts
from common import concordance, cuda
from study import check, now, write

def macro_bootstrap(scores,positive,weights,cohort,component_a,component_b,cell,
                    replicates=2000,device='cuda',batch=8):
    a,b,counts,metadata=component_counts(component_a,component_b,cell,replicates)
    counts=torch.as_tensor(counts,device=device,dtype=torch.float64)
    points=np.empty((scores.shape[1],2)); draws=np.full((scores.shape[1],2,replicates),np.nan)
    for j in range(scores.shape[1]):
        for c in (0,1):
            pmask=positive & (cohort==c); umask=(~positive) & (cohort==c)
            use=cohort==c
            points[j,c]=concordance(scores[use,j],positive[use],weights[use])
            p=scores[pmask,j]; u=scores[umask,j]; order=np.argsort(u,kind='stable')
            left=torch.as_tensor(np.searchsorted(u[order],p,'left'),device=device)
            right=torch.as_tensor(np.searchsorted(u[order],p,'right'),device=device)
            pa=torch.as_tensor(a[pmask],device=device); pb=torch.as_tensor(b[pmask],device=device)
            ua=torch.as_tensor(a[umask][order],device=device); ub=torch.as_tensor(b[umask][order],device=device)
            w=torch.as_tensor(weights[umask][order],device=device)
            for start in range(0,replicates,batch):
                count=counts[start:start+batch]
                pw=torch.where(pa==pb,count[:,pa],count[:,pa]*count[:,pb])
                uw=torch.where(ua==ub,count[:,ua],count[:,ua]*count[:,ub])*w
                prefix=torch.cat([torch.zeros(len(count),1,device=device,dtype=torch.float64),torch.cumsum(uw,1)],1)
                den=pw.sum(1)*prefix[:,-1]
                result=(pw*(prefix[:,left]+prefix[:,right])*.5).sum(1)/den
                result[den<=0]=float('nan')
                draws[j,c,start:start+len(count)]=result.cpu().numpy()
    return points.mean(1),draws.mean(1),metadata

def qualify_macro(device):
    # Independent brute-force pair comparison with the SAME component draw shared
    # by both cohorts. Covers ties, unequal weights and shared components.
    rng=np.random.default_rng(924)
    n=61; scores=rng.integers(0,7,(n,3)).astype(float)
    positive=np.arange(n)%4==0; cohort=np.arange(n)%2
    positive[1::8]=True  # positive support in each cohort
    weights=rng.integers(1,6,n).astype(float)/3
    ca=[f'c{x}' for x in rng.integers(0,8,n)]; cb=[f'c{x}' for x in rng.integers(0,8,n)]
    point,draw,meta=macro_bootstrap(scores,positive,weights,cohort,ca,cb,'macro_fixture',37,device,3)
    a,b,count,_=component_counts(ca,cb,'macro_fixture',37)
    expected=np.full_like(draw,np.nan)
    for j in range(3):
        for k,c in enumerate(count):
            mult=np.where(a==b,c[a],c[a]*c[b]); parts=[]
            for group in (0,1):
                pp=np.flatnonzero(positive & (cohort==group)); uu=np.flatnonzero(~positive & (cohort==group))
                den=mult[pp].sum()*(mult[uu]*weights[uu]).sum()
                value=sum(mult[p]*mult[u]*weights[u]*((scores[p,j]>scores[u,j])+.5*(scores[p,j]==scores[u,j])) for p in pp for u in uu)
                parts.append(value/den if den else np.nan)
            expected[j,k]=np.mean(parts)
    err=float(np.nanmax(np.abs(draw-expected)))
    check(np.array_equal(np.isnan(draw),np.isnan(expected)) and err<1e-12, 'Macro bootstrap oracle failed')
    return {'passed':True,'max_absolute_error':err,'tolerance':1e-12,'replicates':37,'cohorts':2}

if __name__=='__main__':
    result=qualify_macro(cuda())
    write('/output/MACRO_METRIC_QUALIFICATION.json',{'at_utc':now(),**result})
    print(result,flush=True)
