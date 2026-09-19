"""Same-query PU ranking, with an optional bounded complete-list shortlist weight."""
from __future__ import annotations

import math
import time
import numpy as np
import torch
from torch.nn import functional as F

from common import (OUT, SPEC, assert_frozen, destination, environment, head, load_inputs,
                    lr_at, now, protocol, record, score, write_json, write_npy)


def oriented_csr(a, b, n):
    row = np.arange(len(a), dtype=np.int64)
    nonself = a != b
    q = np.r_[a, b[nonself]]
    partner = np.r_[b, a[nonself]]
    pair = np.r_[row, row[nonself]]
    order = np.argsort(q, kind='stable')
    counts = np.bincount(q, minlength=n)
    return np.r_[0, np.cumsum(counts)], partner[order], pair[order]


class QuerySampler:
    def __init__(self, train, n):
        self.train = train
        self.pp, self.p_partner, self.p_row = oriented_csr(train['p_a'], train['p_b'], n)
        self.up, self.u_partner, self.u_row = oriented_csr(train['u_a'], train['u_b'], n)
        pc, uc = np.diff(self.pp), np.diff(self.up)
        self.queries = np.flatnonzero((pc > 0) & (uc > 0))
        self.counts = (pc + uc)[self.queries]
        self.scale = self.counts / self.counts.mean()
        self.all_a = np.r_[train['p_a'], train['u_a']]
        self.all_b = np.r_[train['p_b'], train['u_b']]

    def draw(self, seed, epoch, count):
        # Same comparison samples in both ablations, independent of mining.
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, epoch, 1729])))
        qi = rng.integers(0, len(self.queries), size=count)
        q = self.queries[qi]
        pi = rng.integers(self.pp[q], self.pp[q + 1])
        ui = rng.integers(self.up[q], self.up[q + 1])
        return qi, q, pi, ui

    def shortlist_weights(self, pair_scores, cutoff=40, extra=2.0):
        weights = np.ones(len(self.u_partner), dtype=np.float32)
        top_mass, maxima = [], []
        offset = len(self.train['p_a'])
        for q in self.queries:
            ps = pair_scores[self.p_row[self.pp[q]:self.pp[q + 1]]]
            us = pair_scores[offset + self.u_row[self.up[q]:self.up[q + 1]]]
            credit = cutoff_credit(np.r_[ps, us], cutoff)[len(ps):]
            raw = 1 + extra * credit
            normalized = raw / raw.mean()
            weights[self.up[q]:self.up[q + 1]] = normalized
            assert np.isclose(normalized.mean(), 1.0, atol=1e-12)
            assert normalized.min() > 0 and normalized.max() <= 1 + extra + 1e-6
            top_mass.append(float(credit.sum()))
            maxima.append(float(normalized.max()))
        return weights, dict(mean_top_U_credit=float(np.mean(top_mass)),
                             max_normalized_weight=max(maxima),
                             min_normalized_weight=float(weights.min()))


def cutoff_credit(scores, cutoff):
    scores = np.asarray(scores)
    if not 1 <= cutoff <= len(scores):
        raise ValueError('Cutoff outside list')
    ordered = np.sort(-scores)
    lo = np.searchsorted(ordered, -scores, side='left')
    hi = np.searchsorted(ordered, -scores, side='right')
    return np.clip((cutoff - lo) / (hi - lo), 0.0, 1.0)


def train_all():
    freeze = assert_frozen()
    p = protocol()
    env = environment()
    x, ids, meta, data, dev = load_inputs()
    x = torch.from_numpy(x).cuda()
    sampler = QuerySampler(data, len(ids))
    steps = math.ceil(p['comparisons_per_epoch'] / p['batch_size'])
    total = steps * p['epochs']
    started = time.monotonic()
    records = []
    for variant in p['new_training_variants']:
        for seed in p['seeds']:
            run = f'checkpoints/{variant}/seed_{seed}'
            if (OUT / run).exists():
                raise FileExistsError(f'Will not overwrite or silently resume {run}')
            model = head.build(640, SPEC, seed).cuda()
            optimizer = torch.optim.AdamW(model.parameters(), lr=p['learning_rate'],
                                        weight_decay=p['weight_decay'], betas=tuple(p['betas']),
                                        eps=p['epsilon'], foreach=False, fused=False)
            for epoch in p['evaluation_epochs']:
                if time.monotonic() - started > p['GPU_runtime_limit_seconds']:
                    raise TimeoutError('Prospective GPU runtime budget exceeded; existing outputs retained')
                t0 = time.monotonic()
                info = dict(mean_top_U_credit=0.0, max_normalized_weight=1.0,
                            min_normalized_weight=1.0)
                if variant == 'shortlist_weighted' and epoch > p['shortlist_warmup_epochs']:
                    train_scores = score(model, x, sampler.all_a, sampler.all_b)
                    uw, info = sampler.shortlist_weights(train_scores, p['shortlist_rank_cutoff'],
                                                         p['shortlist_extra_weight'])
                else:
                    uw = np.ones(len(sampler.u_partner), dtype=np.float32)
                qi, q, pi, ui = sampler.draw(seed, epoch, p['comparisons_per_epoch'])
                q_tensor = torch.from_numpy(q).cuda()
                pp_tensor = torch.from_numpy(sampler.p_partner[pi]).cuda()
                up_tensor = torch.from_numpy(sampler.u_partner[ui]).cuda()
                wt = torch.from_numpy((sampler.scale[qi] * uw[ui]).astype(np.float32)).cuda()
                model.train()
                loss_sum = torch.zeros((), device='cuda', dtype=torch.float64)
                raw_sum = torch.zeros((), device='cuda', dtype=torch.float64)
                for bi, lo in enumerate(range(0, len(q), p['batch_size'])):
                    hi = min(lo + p['batch_size'], len(q))
                    lr = lr_at((epoch - 1) * steps + bi, total, p['learning_rate'])
                    for group in optimizer.param_groups:
                        group['lr'] = lr
                    optimizer.zero_grad(set_to_none=True)
                    # The positive and U share the query; independent dropout masks are retained.
                    ps = model(x[q_tensor[lo:hi]], x[pp_tensor[lo:hi]])
                    us = model(x[q_tensor[lo:hi]], x[up_tensor[lo:hi]])
                    raw = F.softplus(us - ps)
                    loss = (raw * wt[lo:hi]).mean()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), p['gradient_norm_cap'],
                                                   error_if_nonfinite=True)
                    optimizer.step()
                    loss_sum += loss.detach().double() * (hi - lo)
                    raw_sum += raw.detach().double().sum()
                torch.cuda.synchronize()
                fitting_seconds = time.monotonic() - t0
                predictions = score(model, x, dev['a'], dev['b'])
                reverse = score(model, x, dev['b'][:4096], dev['a'][:4096])
                # Same batch size for the symmetry check avoids batch-shape roundoff artifacts.
                forward = score(model, x, dev['a'][:4096], dev['b'][:4096])
                swap = float(np.max(np.abs(reverse - forward)))
                assert swap == 0.0
                checkpoint_path = destination(f'{run}/epoch_{epoch:02d}.npz')
                head.save_state(checkpoint_path, model)
                pred = write_npy(f'{run}/epoch_{epoch:02d}_C3_development.npy', predictions)
                rec = dict(variant=variant, seed=seed, epoch=epoch, at_utc=now(),
                           checkpoint=record(checkpoint_path), predictions=pred,
                           weighted_loss=float(loss_sum.cpu()) / len(q),
                           unweighted_sample_loss=float(raw_sum.cpu()) / len(q),
                           fitting_and_mining_seconds=fitting_seconds,
                           epoch_total_seconds=time.monotonic() - t0,
                           learning_rate_final=lr, swap_max_abs_error=swap,
                           input_freeze_sha256=freeze['freeze_identity'], **info)
                write_json(f'{run}/epoch_{epoch:02d}.json', rec)
                records.append(rec)
                print(f"{variant} seed={seed} epoch={epoch} loss={rec['weighted_loss']:.6f} "
                      f"seconds={rec['epoch_total_seconds']:.2f}", flush=True)
            del model, optimizer
    # Epoch 1 must be identical across matched variants, including scores and tensors.
    for seed in p['seeds']:
        a, b = [next(r for r in records if r['variant'] == v and r['seed'] == seed and r['epoch'] == 1)
                for v in p['new_training_variants']]
        assert a['predictions']['sha256'] == b['predictions']['sha256']
        with np.load(OUT / a['checkpoint']['path']) as ca, np.load(OUT / b['checkpoint']['path']) as cb:
            assert all(np.array_equal(ca[k], cb[k]) for k in ca.files)
    write_json('provenance/TRAINING_COMPLETE.json', dict(at_utc=now(), environment=env,
               records=records, elapsed_seconds=time.monotonic() - started,
               identical_epoch1_verified=True, input_freeze_identity=freeze['freeze_identity']))
