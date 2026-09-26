"""Synthetic/TRAIN-only numerical checks and discarded runtime pilots."""
import argparse
import copy
from pathlib import Path
import time
import numpy as np
import torch
from torch.nn import functional as F
from benchmark_metrics import qualify as qualify_metrics
from common import arrays, cuda, now, read, write
from data import ResidueCache, score_cached, train_standardization, validate_training
from model import PairModel
from train import training_step


def synthetic(config, device):
    rows = []
    for recipe in config['recipes']:
        cuda(631)
        model = PairModel(recipe).to(device)
        if model.has_local:
            torch.nn.init.normal_(model.local_head[-1].weight, std=.02)
        model.eval()
        x = torch.randn(4, 13, 640, device=device)
        valid = torch.arange(13, device=device)[None, :] < torch.tensor([3, 8, 13, 5], device=device)[:, None]
        global_ = torch.randn(4, 640, device=device)
        with torch.inference_mode():
            tokens = model.encode(x, valid)
            modified = x.clone(); modified[~valid] = 10000
            padding_error = float((tokens - model.encode(modified, valid)).abs().max())
            a, b = [0, 1, 2], [3, 2, 0]
            direct = model.score(global_[a], global_[b], tokens[a], tokens[b])
            reverse = model.score(global_[b], global_[a], tokens[b], tokens[a])
            symmetry_error = float((direct - reverse).abs().max())
            individual = torch.cat([model.score(global_[a[i:i+1]], global_[b[i:i+1]],
                                   tokens[a[i:i+1]], tokens[b[i:i+1]]) for i in range(3)])
            batching_error = float((direct - individual).abs().max())
            partner_effect = None
            if recipe['cross_layers']:
                old = model.condition(tokens[:1], tokens[1:2])[0]
                changed = model.condition(tokens[:1], tokens[2:3])[0]
                partner_effect = float((old - changed).abs().max())
                if partner_effect < 1e-5:
                    raise RuntimeError('Cross-attention does not depend on partner')
        if padding_error > 1e-5 or symmetry_error > 1e-5 or batching_error > 1e-5:
            raise RuntimeError('Padding/symmetry/batching qualification failed')
        model.train()
        xa = x[:2].clone().requires_grad_(); xb = x[2:].clone().requires_grad_()
        score = model.score(global_[:2], global_[2:], model.encode(xa, valid[:2]), model.encode(xb, valid[2:]))
        score.sum().backward()
        if model.has_local and (xa.grad is None or xb.grad is None or not bool(torch.isfinite(xa.grad).all())
                                or not bool(torch.isfinite(xb.grad).all()) or float(xa.grad.abs().sum()) == 0
                                or float(xb.grad.abs().sum()) == 0):
            raise RuntimeError('Missing/nonfinite gradients to one protein')
        rows.append({'recipe': recipe['name'], 'padding_error': padding_error, 'symmetry_error': symmetry_error,
                     'batching_error': batching_error, 'partner_conditioning_effect': partner_effect})
        del model
    # Independent PU derivative: positive scores must be pushed up relative to U.
    scores = torch.tensor([1., 2., .5, 3.], device=device, dtype=torch.float64, requires_grad=True)
    weights = torch.tensor([.5, 1.5], device=device, dtype=torch.float64)
    loss = (F.softplus(scores[2:] - scores[:2]) * weights).mean()
    gradient = torch.autograd.grad(loss, scores)[0]
    expected = weights * torch.sigmoid(scores[2:] - scores[:2]) / 2
    assert torch.allclose(gradient, torch.cat((-expected, expected)), atol=1e-14, rtol=0)
    # Adversarial held-out changes cannot alter fitted normalizer parameters.
    means = np.arange(32, dtype=np.float32).reshape(8, 4)
    partitions = ['train'] * 5 + ['development', 'test', 'test']
    first = train_standardization(means, partitions)
    means[5:] = 1e8
    second = train_standardization(means, partitions)
    assert all(np.array_equal(a, b) for a, b in zip(first, second))
    metric = qualify_metrics(device)
    return {'at_utc': now(), 'passed': True, 'models': rows, 'metric': metric,
            'TRAIN_only_normalization': True, 'PU_gradient_oracle': True,
            'test_pairs_read': False, 'test_truth_read': False}


def real(config, device):
    cache = ResidueCache(device=device)
    train = arrays('/output/data/training.npz')
    validate_training(train, cache.meta)
    train['normalized_u_weight'] = train['u_weight'] / train['u_weight'].mean()
    permitted = np.flatnonzero(np.asarray(cache.meta['partition']) == 'train')
    ordered = sorted(permitted.tolist(), key=lambda i: cache.meta['length'][i])
    selected = [ordered[0], ordered[len(ordered) // 2], ordered[-1]]
    records = []
    for recipe in config['recipes']:
        cuda(9161)
        model = PairModel(recipe).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=config['learning_rate'], weight_decay=config['weight_decay'])
        p = np.resize(np.arange(len(train['p_a'])), config['comparison_batch'])
        u = np.arange(config['comparison_batch'])
        model.train()
        training_step(model, optimizer, cache, train, p, u, config)
        # Save/restore all state and compare one resumed stochastic step.
        checkpoint = copy.deepcopy(model.state_dict())
        optimizer_checkpoint = copy.deepcopy(optimizer.state_dict())
        cpu_rng, cuda_rng = torch.get_rng_state(), torch.cuda.get_rng_state()
        training_step(model, optimizer, cache, train, p, u, config)
        after = copy.deepcopy(model.state_dict())
        model.load_state_dict(checkpoint); optimizer.load_state_dict(optimizer_checkpoint)
        torch.set_rng_state(cpu_rng); torch.cuda.set_rng_state(cuda_rng)
        training_step(model, optimizer, cache, train, p, u, config)
        resume_error = max(float((after[k] - value).abs().max()) for k, value in model.state_dict().items())
        if resume_error > 1e-7:
            raise RuntimeError(f'Resume-state recovery error: {resume_error}')
        del checkpoint, optimizer_checkpoint, after
        torch.cuda.synchronize(); start = time.monotonic()
        for _ in range(10):
            loss, norm = training_step(model, optimizer, cache, train, p, u, config)
        torch.cuda.synchronize(); train_seconds = (time.monotonic() - start) / 10
        model.eval()
        tokens = cache.endpoint_tokens(model, selected)
        x, valid = cache.pack(selected)
        with torch.inference_mode():
            direct_tokens = model.encode(x, valid)
            token_error = float((direct_tokens - tokens[selected]).abs().max())
            a, b = np.asarray(selected), np.asarray(selected[::-1])
            direct = model.score(cache.global_features[a], cache.global_features[b], direct_tokens,
                                 direct_tokens.flip(0)).cpu().numpy()
        cached = score_cached(model, cache.global_features, tokens, a, b)
        score_error = float(np.max(np.abs(direct - cached)))
        if token_error > 2e-5 or score_error > 2e-5:
            raise RuntimeError('Full-length direct/cached scoring mismatch')
        a = np.resize(a, 4096); b = np.resize(b, 4096)
        score_cached(model, cache.global_features, tokens, a, b)
        torch.cuda.synchronize(); start = time.monotonic()
        score_cached(model, cache.global_features, tokens, a, b)
        torch.cuda.synchronize(); seconds = time.monotonic() - start
        value = {'recipe': recipe['name'], 'parameters': sum(p.numel() for p in model.parameters()),
                 'seconds_per_training_batch': train_seconds,
                 'estimated_training_seconds_per_epoch_excluding_dev': train_seconds * int(np.ceil(2000000 / config['comparison_batch'])),
                 'head_seconds_per_4096_pairs': seconds, 'resume_maximum_absolute_error': resume_error,
                 'full_length_token_error': token_error, 'cached_score_error': score_error,
                 'fixture_lengths': [cache.meta['length'][i] for i in selected], 'final_pilot_loss': loss,
                 'final_pilot_gradient_norm': norm}
        records.append(value); print(value, flush=True)
        del optimizer, model, tokens, direct_tokens, x
        torch.cuda.empty_cache()
    return {'at_utc': now(), 'passed': True, 'recipes': records, 'pilot_fits_discarded': True,
            'fixtures': 'TRAIN endpoints/pairs only', 'test_pairs_read': False, 'test_truth_read': False,
            'device': torch.cuda.get_device_name(), 'torch': torch.__version__, 'cuda': torch.version.cuda}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--real', action='store_true')
    args = parser.parse_args(); config = read('/config.json'); device = cuda()
    result = real(config, device) if args.real else synthetic(config, device)
    name = 'REAL_QUALIFICATION.json' if args.real else 'QUALIFICATION.json'
    write(Path('/output') / name, result, exclusive=True)
    print(result, flush=True)
