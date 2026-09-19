"""Fresh native RAPPPID-mult; TRAIN-only weighted PU adaptation and token RNG."""
import copy
import hashlib
from pathlib import Path
import threading
import numpy as np
import sentencepiece as sp
import torch
from torch.nn import functional as F
from train import LSTMAWD
from data import RapppidDataset2
from ranger21 import Ranger21
from common import UPSTREAM_COMMIT, read, sha

CONFIG = {'num_codes': 250, 'embedding_size': 64, 'steps_per_epoch': 50000, 'num_epochs': 20,
          'lstm_dropout_rate': .3, 'classhead_dropout_rate': .2, 'rnn_num_layers': 2,
          'classhead_num_layers': 2, 'lr': .01, 'weight_decay': .0001, 'bi_reduce': 'last',
          'class_head_name': 'mult', 'variational_dropout': False, 'lr_scaling': False,
          'trunc_len': 1500, 'embedding_droprate': .3, 'frozen_epochs': 0, 'optimizer_type': 'ranger21'}


def fresh(seed, device='cuda'):
    manifest = read('/opt/rapppid/downloads.json')
    assert manifest['upstream_commit'] == UPSTREAM_COMMIT
    for item in manifest['files']:
        # Validate native source without loading any released learned weights.
        if item['path'].startswith('rapppid/'):
            assert sha(Path('/opt/rapppid/upstream') / item['path']) == item['sha256']
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    result = LSTMAWD(**CONFIG).to(device)
    assert sum(p.numel() for p in result.parameters()) == 188161
    assert all(p.requires_grad for p in result.parameters())
    return result


def optimizer(model):
    return Ranger21(model.parameters(), lr=CONFIG['lr'], weight_decay=CONFIG['weight_decay'],
                    num_batches_per_epoch=CONFIG['steps_per_epoch'], num_epochs=CONFIG['num_epochs'],
                    warmdown_start_pct=.72, logging_active=False)


def optimizer_auxiliary(opt):
    # Ranger21 does not put its warmup, lookahead-step and epoch counters into
    # Optimizer.state_dict(). Save all public instance configuration/counters,
    # in addition to the ordinary per-parameter moments and lookahead tensors.
    return copy.deepcopy({k: v for k, v in vars(opt).items()
                          if not k.startswith('_') and k not in ('state', 'param_groups', 'defaults')})


def restore_optimizer_auxiliary(opt, auxiliary):
    expected = set(optimizer_auxiliary(opt))
    if set(auxiliary) != expected:
        raise RuntimeError('Ranger21 auxiliary-state schema changed')
    for key, value in auxiliary.items():
        setattr(opt, key, value)


def learned_digest(model):
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode() + b'\0')
        digest.update(str(value.dtype).encode() + str(tuple(value.shape)).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def orders(seed, epoch, n_positive, n_unlabeled):
    p = np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, epoch, 0])))
    u = np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, epoch, 1])))
    return np.resize(p.permutation(n_positive), n_unlabeled), u.permutation(n_unlabeled)


class Tokens:
    def __init__(self, root='/data'):
        root = Path(root)
        self.meta = read(root / 'sequences.json')
        self.spp = sp.SentencePieceProcessor(model_file=str(root / 'spm.model'))
        assert self.spp.get_piece_size() == 250 and self.spp.pad_id() == 0

    def encode(self, index, sampling):
        value = np.asarray(RapppidDataset2.static_encode(1500, self.spp, self.meta['sequence'][int(index)],
                                                       sp=True, pad=True, sampling=sampling), np.int64)
        assert value.shape == (1500,) and ((value >= 0) & (value < 250)).all() and np.count_nonzero(value) > 0
        return value

    def pack(self, train, p, u, seed, epoch, start, device):
        # A deterministic per-step stream makes stochastic subword sampling
        # independent of process lifetime/prefetching and exactly resumable.
        token_seed = int(np.random.SeedSequence([seed, epoch, start, 2]).generate_state(1)[0] % (2**31 - 1))
        a = np.concatenate((train['p_a'][p], train['u_a'][u]))
        b = np.concatenate((train['p_b'][p], train['u_b'][u]))
        assert all(self.meta['partition'][int(i)] == 'train' for i in np.concatenate((a, b)))
        # SentencePiece's RNG is thread-local: resetting its global seed does
        # not reset an already initialized thread's generator. A fresh short-
        # lived tokenizer thread per step gives the native sampler its exact
        # seeded stream on both uninterrupted and resumed runs. CUDA stays on
        # the main thread; no persistent worker/prefetch RNG must be checkpointed.
        sp.set_random_generator_seed(token_seed)
        result, errors = [], []
        def tokenize():
            try:
                result.extend((np.stack([self.encode(i, True) for i in a]),
                               np.stack([self.encode(i, True) for i in b])))
            except BaseException as exc:
                errors.append(exc)
        worker = threading.Thread(target=tokenize)
        worker.start()
        worker.join()
        if errors:
            raise errors[0]
        x, y = result
        return torch.as_tensor(x, device=device), torch.as_tensor(y, device=device)


def ranking_loss(logits, weights):
    n = len(weights)
    assert logits.shape == (2 * n,)
    return (F.softplus(logits[n:] - logits[:n]).double() * weights).mean()


def step(model, opt, tokens, train, p, u, seed, epoch, start):
    model.train()
    opt.zero_grad(set_to_none=True)
    a, b = tokens.pack(train, p, u, seed, epoch, start, next(model.parameters()).device)
    # Actual native training calls: endpoint batches padded separately and the
    # unmodified MultClassHead uses batch-wide moments. DEV instead fixes native
    # singleton endpoints/head moments, as in the completed original evaluation.
    logits = model.class_head(model(a), model(b)).float().reshape(-1)
    weight = torch.as_tensor(train['normalized_u_weight'][u], device=logits.device, dtype=torch.float64)
    loss = ranking_loss(logits, weight)
    if not torch.isfinite(loss):
        raise RuntimeError('Nonfinite PU loss')
    loss.backward()
    grads = [p.grad for p in model.parameters() if p.grad is not None]
    if len(grads) != len(list(model.parameters())) or not torch.stack([g.isfinite().all() for g in grads]).all():
        raise RuntimeError('Missing or nonfinite native gradients')
    norm = torch.linalg.vector_norm(torch.stack([g.norm() for g in grads]))
    opt.step()
    if not torch.stack([p.isfinite().all() for p in model.parameters()]).all():
        raise RuntimeError('Nonfinite native parameters')
    return {'loss': float(loss.detach()), 'gradient_norm': float(norm.detach()),
            'learning_rate': float(opt.current_lr)}


@torch.inference_mode()
def singleton_head(model, a, b):
    a = (a - a.mean(1, keepdim=True)) / a.std(1, keepdim=True, correction=1)
    b = (b - b.mean(1, keepdim=True)) / b.std(1, keepdim=True, correction=1)
    return model.class_head.fc(model.class_head.nl(a * b)).float().reshape(-1)


@torch.inference_mode()
def endpoint_cache(model, tokens, indices, allowed_partition='development'):
    if model.training:
        raise RuntimeError('A changing training encoder cannot be cached')
    device = next(model.parameters()).device
    result = torch.full((17000, 64), float('nan'), device=device)
    for index in indices:
        assert tokens.meta['partition'][int(index)] == allowed_partition
        value = torch.as_tensor(tokens.encode(index, False)[None], device=device)
        result[int(index)] = model(value).reshape(64)
    assert torch.isfinite(result[indices]).all() and (result[indices].std(1) > 0).all()
    return result


@torch.inference_mode()
def scores(model, embeddings, a, b, batch=8192):
    result = np.empty(len(a), np.float64)
    for start in range(0, len(a), batch):
        ia = torch.as_tensor(a[start:start+batch], device=embeddings.device)
        ib = torch.as_tensor(b[start:start+batch], device=embeddings.device)
        result[start:start+len(ia)] = singleton_head(model, embeddings[ia], embeddings[ib]).cpu().numpy()
    assert np.isfinite(result).all()
    return result
