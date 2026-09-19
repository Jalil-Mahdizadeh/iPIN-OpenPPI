"""TRAIN-only weighted P-vs-U loss and its RFF-weight curvature.

This is explicitly a PU-adapted TUnA, not the authors' native BCE recipe.
The inference architecture, frozen ESM encoder, spectral normalization,
dropout, 512-residue training crops and native Adam/Lookahead are retained.
"""
import numpy as np
import torch
from torch.nn import functional as F
from adapter import create, enable_sdpa, native, rff

def make_model(seed,device):
    model=create(seed=seed,device=device,fresh_initialize=True)
    enable_sdpa(model)
    return model

def optimizer(model):
    weight=[]; bias=[]
    for name,p in model.named_parameters():
        (bias if 'bias' in name else weight).append(p)
    inner=torch.optim.Adam([{'params':weight,'weight_decay':1e-5},{'params':bias,'weight_decay':0}],lr=1e-4)
    return inner,native.Lookahead(inner,alpha=.8,k=5)

def pair_logits(model,cache,a,b):
    x,lx=cache.pack(a); y,ly=cache.pack(b)
    return model.forward(x,y,lx,ly,512,512,False,True).reshape(-1)

def step(model,opt,cache,train,p,u):
    a=np.concatenate([train['p_a'][p],train['u_a'][u]])
    b=np.concatenate([train['p_b'][p],train['u_b'][u]])
    opt.zero_grad()
    scores=pair_logits(model,cache,a,b)
    weights=torch.as_tensor(train['normalized_u_weight'][u],device=model.device,dtype=torch.float64)
    loss=(F.softplus(scores[len(p):]-scores[:len(p)]).double()*weights).mean()
    if not torch.isfinite(loss):
        raise RuntimeError('Nonfinite training loss')
    loss.backward()
    if not all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters()):
        raise RuntimeError('Nonfinite training gradient')
    opt.step()
    return float(loss.detach())

def fitted_features(model,cache,train,seed,batch_size=4096):
    """Fit a pairwise-Laplace RFF covariance using TRAIN comparisons only.

    H = I + sum w * sigmoid(delta)*(1-sigmoid(delta)) * dphi dphi^T.
    This matches the declared summed weighted ranking loss curvature, not
    binary-negative uncertainty. Its mean-field score is a ranking score,
    NOT a calibrated probability of physical interaction.
    """
    model.gp_layer.fitted=True  # Don't invoke native binary-likelihood pinv.
    model.eval()
    permitted=[i for i,part in enumerate(cache.meta['partition']) if part!='test']
    z=cache.features(model,permitted)
    if not torch.isfinite(z[permitted]).all():
        raise RuntimeError('Incomplete endpoint feature cache')
    gp=model.gp_layer
    precision=torch.zeros_like(gp.precision,dtype=torch.float64)
    rng=np.random.Generator(np.random.PCG64DXSM(seed+900000))
    positives=rng.integers(len(train['p_a']),size=len(train['u_a']))
    with torch.inference_mode():
        for start in range(0,len(positives),batch_size):
            end=min(start+batch_size,len(positives)); p=positives[start:end]
            pu=rff(model,torch.maximum(z[train['u_a'][start:end]],z[train['u_b'][start:end]]))
            pp=rff(model,torch.maximum(z[train['p_a'][p]],z[train['p_b'][p]]))
            difference=pu-pp
            prob=torch.sigmoid((difference@gp.output_weights).reshape(-1))
            w=torch.as_tensor(train['normalized_u_weight'][start:end],device=model.device)
            adjusted=difference.double()*torch.sqrt(w*prob.double()*(1-prob.double()))[:,None]
            precision.addmm_(adjusted.T,adjusted)
        matrix=precision+torch.eye(gp.RFFs,device=model.device,dtype=torch.float64)*gp.ridge_penalty
        covariance=torch.cholesky_inverse(torch.linalg.cholesky(matrix))
        gp.precision.copy_(precision.float())
        gp.covariance.copy_(covariance.float())
        gp.fitted=True
    return z

def training_orders(seed,epoch,n_positive,n_unlabeled):
    # Same independent streams and balanced positive cycling as frozen iPIN.
    p_rng=np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed,epoch,0])))
    u_rng=np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed,epoch,1])))
    return np.resize(p_rng.permutation(n_positive),n_unlabeled),u_rng.permutation(n_unlabeled)

def curvature_test(device):
    """Independent autograd Hessian check of the PU covariance expression."""
    generator=torch.Generator(device=device).manual_seed(611)
    difference=torch.randn(7,5,generator=generator,device=device,dtype=torch.float64)
    weights=torch.arange(1,8,device=device,dtype=torch.float64)/4
    beta=torch.randn(5,generator=generator,device=device,dtype=torch.float64,requires_grad=True)
    hessian=torch.autograd.functional.hessian(lambda b:(F.softplus(difference@b)*weights).sum(),beta)
    p=torch.sigmoid(difference@beta)
    explicit=difference.T@(difference*(weights*p*(1-p))[:,None])
    error=float((hessian-explicit).abs().max().detach())
    if error>1e-10:
        raise RuntimeError('PU curvature qualification failed')
    return error
