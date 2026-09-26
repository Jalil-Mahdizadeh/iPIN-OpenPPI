"""Fixed TRAIN-only search; every saved prediction here is development-only."""
import argparse
import copy
from pathlib import Path
import time
import numpy as np
import torch
from torch.nn import functional as F
from common import arrays, concordance, cuda, now, read, record, sha, write
from data import ResidueCache, score_cached, validate_training
from model import PairModel


def orders(seed, epoch, n_positive, n_unlabeled):
    prng = np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, epoch, 0])))
    urng = np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, epoch, 1])))
    return np.resize(prng.permutation(n_positive), n_unlabeled), urng.permutation(n_unlabeled)


def training_step(model, optimizer, cache, train, p, u, config):
    device = cache.device
    a = np.concatenate((train['p_a'][p], train['u_a'][u]))
    b = np.concatenate((train['p_b'][p], train['u_b'][u]))
    ia = torch.as_tensor(a, device=device, dtype=torch.long)
    ib = torch.as_tensor(b, device=device, dtype=torch.long)
    optimizer.zero_grad(set_to_none=True)
    ta = tb = None
    if model.has_local:
        unique, inverse = torch.unique(torch.cat((ia, ib)), sorted=True, return_inverse=True)
        x, valid = cache.pack(unique, sample=config['training_residues'])
        tokens = model.encode(x, valid)
        ta, tb = tokens[inverse[:len(a)]], tokens[inverse[len(a):]]
    scores = model.score(cache.global_features[ia], cache.global_features[ib], ta, tb)
    weights = torch.as_tensor(train['normalized_u_weight'][u], device=device, dtype=torch.float64)
    loss = (F.softplus(scores[len(p):] - scores[:len(p)]).double() * weights).mean()
    if not bool(torch.isfinite(loss)):
        raise RuntimeError('Nonfinite training loss')
    loss.backward()
    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config['gradient_clip'], error_if_nonfinite=True)
    optimizer.step()
    return float(loss.detach()), float(norm)


def atomic_torch(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    torch.save(value, temporary)
    temporary.replace(path)


def save_resume(path, model, optimizer, epoch, step, loss_sum, protocol_hash, seed):
    atomic_torch(path, {'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                       'cpu_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state(),
                       'epoch': epoch, 'next_step': step, 'loss_sum': loss_sum,
                       'protocol_sha256': protocol_hash, 'recipe': model.recipe, 'seed': seed})


def verify_freeze():
    frozen = read('/output/TRAINING_FREEZE.json')
    if sha('/config.json') != frozen['config_sha256']:
        raise RuntimeError('Configuration changed after freeze')
    for item in frozen['code_files']:
        if sha(Path('/code') / item['path']) != item['sha256']:
            raise RuntimeError(f"Frozen code changed: {item['path']}")
    if sha('/output/data/DATA_MANIFEST.json') != frozen['data_manifest_sha256']:
        raise RuntimeError('Data manifest changed')
    for item in read('/output/data/DATA_MANIFEST.json')['files']:
        if sha(Path('/output/data') / item['path']) != item['sha256']:
            raise RuntimeError(f"Prepared input changed: {item['path']}")
    if sha('/cache/RESIDUE_CACHE_MANIFEST.json') != frozen['residue_manifest_sha256']:
        raise RuntimeError('Residue manifest changed')
    if not frozen['authorized_to_train']:
        raise RuntimeError('Training is not authorized')
    return frozen


def run_seed(recipe, seed, config, cache, train, dev):
    root = Path('/output/training') / recipe['name'] / f'seed_{seed}'
    root.mkdir(parents=True, exist_ok=True)
    protocol_hash = sha('/output/TRAINING_FREEZE.json')
    if (root / 'COMPLETE.json').exists():
        old = read(root / 'COMPLETE.json')
        if old['protocol_sha256'] != protocol_hash:
            raise RuntimeError('Completed seed belongs to another protocol')
        for item in old['files']:
            if sha(root / item['path']) != item['sha256']:
                raise RuntimeError('Completed seed artifact changed')
        print({'already_complete': str(root)}, flush=True)
        return
    cuda(seed)
    model = PairModel(recipe).to(cache.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config['learning_rate'],
                                  weight_decay=config['weight_decay'])
    resume_path = root / 'resume.pt'
    epoch_start, next_step, loss_sum = 1, 0, 0.
    if resume_path.exists():
        state = torch.load(resume_path, map_location=cache.device, weights_only=True)
        if state['protocol_sha256'] != protocol_hash or state['recipe'] != recipe or state['seed'] != seed:
            raise RuntimeError('Resume identity mismatch')
        model.load_state_dict(state['model'], strict=True)
        optimizer.load_state_dict(state['optimizer'])
        torch.set_rng_state(state['cpu_rng'].cpu())
        torch.cuda.set_rng_state(state['cuda_rng'].cpu())
        epoch_start, next_step, loss_sum = state['epoch'], state['next_step'], state['loss_sum']
        del state
    started = time.monotonic()

    def event(value):
        import json
        value = {'at_utc': now(), 'recipe': recipe['name'], 'seed': seed, **value}
        print(value, flush=True)
        with (root / 'events.jsonl').open('a') as handle:
            handle.write(json.dumps(value, allow_nan=False) + '\n')

    event({'event': 'start_or_resume', 'epoch': epoch_start, 'next_step': next_step,
           'parameters': sum(p.numel() for p in model.parameters()), 'gpu': torch.cuda.get_device_name(),
           'protocol_sha256': protocol_hash})
    batch = config['comparison_batch']
    allowed = np.flatnonzero(np.asarray(cache.meta['partition']) != 'test').tolist()
    for epoch in range(epoch_start, config['epochs'] + 1):
        model.train()
        epoch_started = time.monotonic()
        po, uo = orders(seed, epoch, len(train['p_a']), len(train['u_a']))
        for start in range(next_step, len(uo), batch):
            end = min(start + batch, len(uo))
            loss, norm = training_step(model, optimizer, cache, train, po[start:end], uo[start:end], config)
            loss_sum += loss * (end - start)
            if (start // batch + 1) % 500 == 0:
                event({'event': 'progress', 'epoch': epoch, 'comparisons_done': end,
                       'loss': loss, 'gradient_norm': norm, 'epoch_seconds': time.monotonic() - epoch_started})
            if (start // batch + 1) % config['checkpoint_steps'] == 0:
                save_resume(resume_path, model, optimizer, epoch, end, loss_sum, protocol_hash, seed)
        save_resume(resume_path, model, optimizer, epoch, len(uo), loss_sum, protocol_hash, seed)
        event({'event': 'epoch_training_complete', 'epoch': epoch,
               'weighted_loss': loss_sum / len(uo), 'seconds': time.monotonic() - epoch_started})
        if epoch in config['evaluation_epochs']:
            info_path = root / f'epoch_{epoch:02d}.json'
            if info_path.exists():
                for key in ('checkpoint', 'development_predictions'):
                    item = read(info_path)[key]
                    if sha(root / Path(item['path']).name) != item['sha256']:
                        raise RuntimeError('Existing development artifact changed')
            else:
                model.eval()
                tokens = cache.endpoint_tokens(model, allowed)
                predictions = score_cached(model, cache.global_features, tokens, dev['a'], dev['b'])
                metric = concordance(predictions, dev['positive'], dev['weight'])
                checkpoint = root / f'epoch_{epoch:02d}.pt'
                prediction_path = root / f'epoch_{epoch:02d}_C3_development.npy'
                atomic_torch(checkpoint, model.state_dict())
                temporary = prediction_path.with_suffix('.tmp')
                with temporary.open('wb') as handle:
                    np.save(handle, predictions, allow_pickle=False)
                temporary.replace(prediction_path)
                write(info_path, {'at_utc': now(), 'recipe': recipe['name'], 'seed': seed, 'epoch': epoch,
                      'C3_development_concordance': metric, 'checkpoint': record(checkpoint),
                      'development_predictions': record(prediction_path), 'protocol_sha256': protocol_hash,
                      'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
                del tokens, predictions
                event({'event': 'development', 'epoch': epoch, 'C3_concordance': metric})
        next_step, loss_sum = 0, 0.
        save_resume(resume_path, model, optimizer, epoch + 1, 0, 0., protocol_hash, seed)
    files = []
    for path in sorted(root.glob('epoch_*')):
        item = record(path); item['path'] = path.name; files.append(item)
    write(root / 'COMPLETE.json', {'at_utc': now(), 'recipe': recipe['name'], 'seed': seed,
          'protocol_sha256': protocol_hash, 'epochs': config['epochs'], 'files': files,
          'elapsed_this_process_seconds': time.monotonic() - started,
          'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
    event({'event': 'complete', 'elapsed_seconds': time.monotonic() - started})
    del optimizer, model
    torch.cuda.empty_cache()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--recipe', required=True)
    args = parser.parse_args()
    verify_freeze()
    config = read('/config.json')
    recipe = next(x for x in config['recipes'] if x['name'] == args.recipe)
    device = cuda()
    cache = ResidueCache(device=device, load_residues=recipe['local_branch'])
    train = arrays('/output/data/training.npz')
    dev = arrays('/output/data/development_00.npz')
    validate_training(train, cache.meta)
    train['normalized_u_weight'] = train['u_weight'] / train['u_weight'].mean()
    for seed in config['seeds']:
        run_seed(recipe, seed, config, cache, train, dev)


if __name__ == '__main__':
    main()
