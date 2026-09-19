"""PU-D-SCRIPT: fresh native PPI layers, fixed native LM inputs."""
import json
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from native_adapter import LengthSafeOriginal


def fresh(seed, device='cuda'):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    config = json.loads(Path('/opt/dscript/weights/human_v1_hf/config.json').read_text())
    config['use_cuda'] = str(device).startswith('cuda')
    model = LengthSafeOriginal(**config).to(device)
    model.extend_positions(7570)
    model.tile_area = 1_000_000
    # Keep the native fixed generalized-sigmoid slope in the state dictionary,
    # but expose its stable pre-sigmoid logit for the PU ranking objective.
    model.do_sigmoid = False
    return model


def contact_logit(model, x, y):
    if model.training and max(x.shape[1], y.shape[1]) > 512:
        raise RuntimeError('Training requires the declared <=512-residue crops')
    contact, raw = model.map_predict(x, y)
    return contact, model.activation.k * (raw - model.activation.x0)


def orders(seed, epoch, n_positive, n_unlabeled):
    p = np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, epoch, 0])))
    u = np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, epoch, 1])))
    return np.resize(p.permutation(n_positive), n_unlabeled), u.permutation(n_unlabeled)


def step(model, optimizer, cache, train, p, u):
    optimizer.zero_grad(set_to_none=True)
    rankings, contacts = [], []
    for pi, ui in zip(p, u, strict=True):
        cm_p, sp = contact_logit(model, cache.crop(train['p_a'][pi]), cache.crop(train['p_b'][pi]))
        cm_u, su = contact_logit(model, cache.crop(train['u_a'][ui]), cache.crop(train['u_b'][ui]))
        rankings.append(F.softplus(su - sp).reshape(()))
        contacts.append((cm_p.mean() + cm_u.mean()) * 0.5)
    weight = torch.as_tensor(train['normalized_u_weight'][u], device=rankings[0].device, dtype=torch.float64)
    ranking = (torch.stack(rankings).double() * weight).mean()
    contact = (torch.stack(contacts).double() * weight).mean()
    # Retain the published 0.35/0.65 interaction/contact regularization mixture,
    # replacing binary-negative BCE by the matched weighted P-vs-U objective.
    loss = 0.35 * ranking + 0.65 * contact
    if not torch.isfinite(loss):
        raise RuntimeError('Nonfinite training loss')
    loss.backward()
    gradients = [p.grad for p in model.parameters() if p.grad is not None]
    if not gradients or not torch.stack([g.isfinite().all() for g in gradients]).all():
        raise RuntimeError('Missing/nonfinite training gradient')
    norm = torch.linalg.vector_norm(torch.stack([g.norm() for g in gradients]))
    optimizer.step()
    model.clip()  # Native symmetry and theta/lambda/gamma constraints.
    if not torch.stack([p.isfinite().all() for p in model.parameters()]).all():
        raise RuntimeError('Nonfinite model parameter')
    return {'loss':float(loss.detach()), 'ranking_loss':float(ranking.detach()),
            'contact_penalty':float(contact.detach()), 'gradient_norm':float(norm.detach())}


class Residues:
    def __init__(self, root, device='cuda'):
        root = Path(root)
        self.offsets = np.load(root/'offsets.npy', allow_pickle=False)
        self.values = np.load(root/'residues.npy', mmap_mode='r', allow_pickle=False)
        self.device = device
        if self.values.shape != (int(self.offsets[-1]), 6165):
            raise RuntimeError('Invalid native LM cache shape')

    def crop(self, index):
        index = int(index)
        start, stop = map(int, self.offsets[index:index+2])
        size = min(stop-start, 512)
        offset = int(torch.randint(stop-start-size+1, ()).item())
        # Inputs are copied, never modified through a read-only memmap.
        return torch.from_numpy(self.values[start+offset:start+offset+size].copy()).to(self.device)[None]

    def full(self, index):
        start, stop = map(int, self.offsets[int(index):int(index)+2])
        return torch.from_numpy(self.values[start:stop].copy()).to(self.device)[None]


def project(model, cache, indices, lengths, device='cuda'):
    if model.training:
        raise RuntimeError('Projection caches require evaluation mode')
    offsets = np.concatenate(([0], np.cumsum(lengths, dtype=np.int64)))
    values = torch.full((int(offsets[-1]), 100), float('nan'), device=device)
    with torch.inference_mode():
        for i in indices:
            values[offsets[i]:offsets[i+1]] = model.embedding(cache.full(i))[0]
    return values, offsets


def scores(model, values, offsets, a, b, block=512):
    if model.training:
        raise RuntimeError('Scoring requires eval mode')
    output = np.empty(len(a), np.float64)
    with torch.inference_mode():
        for start in range(0, len(a), block):
            end = min(start+block, len(a))
            pending = torch.empty(end-start, device=values.device)
            for j, (x,y) in enumerate(zip(a[start:end],b[start:end],strict=True)):
                p = values[offsets[x]:offsets[x+1]][None]
                q = values[offsets[y]:offsets[y+1]][None]
                _, logit = contact_logit(model,p,q)
                pending[j] = logit
            output[start:end] = pending.cpu().numpy()
    if not np.isfinite(output).all():
        raise RuntimeError('Nonfinite retrained scores')
    return output
