"""Atomic recovery and immutable four-epoch checkpoints; C3-DEV only."""
import copy
from pathlib import Path
import numpy as np
import torch
from common import concordance, now, read, record, sha, write
from model import endpoint_cache, learned_digest, optimizer_auxiliary, restore_optimizer_auxiliary, scores


def atomic_state(path, value):
    path = Path(path)
    temporary = path.with_suffix('.next.pt')
    torch.save(value, temporary)
    temporary.replace(path)


def recovery_payload(model, opt, epoch, done, sums, protocol_sha, seed):
    return {'model': model.state_dict(), 'optimizer': opt.state_dict(),
            'ranger21_auxiliary': optimizer_auxiliary(opt), 'epoch': epoch,
            'next_comparison': done, 'sums': dict(sums), 'seed': seed,
            'cpu_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state(),
            'protocol_sha256': protocol_sha}


def save_resume(path, model, opt, epoch, done, sums, protocol_sha, seed):
    atomic_state(path, recovery_payload(model, opt, epoch, done, sums, protocol_sha, seed))


def load_resume(path, model, opt, protocol_sha, seed, device):
    state = torch.load(path, map_location=device, weights_only=True)
    if state['protocol_sha256'] != protocol_sha or state['seed'] != seed:
        raise RuntimeError('Recovery identity changed')
    model.load_state_dict(state['model'], strict=True)
    opt.load_state_dict(state['optimizer'])
    restore_optimizer_auxiliary(opt, state['ranger21_auxiliary'])
    torch.set_rng_state(state['cpu_rng'].cpu())
    torch.cuda.set_rng_state(state['cuda_rng'].cpu())
    return state['epoch'], state['next_comparison'], state['sums']


def evaluate_development(root, epoch, model, opt, tokens, dev, protocol_sha, seed, sums, event):
    if len(dev['a']) != 1002265 or int(dev['positive'].sum()) != 2265:
        raise RuntimeError('Full C3-DEV panel required')
    model.eval()
    before = learned_digest(model)
    checkpoint = root / f'epoch_{epoch:02d}.pt'
    output = root / f'epoch_{epoch:02d}_C3_development.npy'
    reservation = root / f'epoch_{epoch:02d}-RESERVATION.json'
    report = root / f'epoch_{epoch:02d}.json'
    if checkpoint.exists():
        saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
        assert saved['protocol_sha256'] == protocol_sha and saved['seed'] == seed and saved['epoch'] == epoch
        assert all(torch.equal(v.detach().cpu(), saved['model'][k]) for k, v in model.state_dict().items())
    else:
        # Retain optimizer, tokenizer-step position and RNG too, not just weights.
        atomic_state(checkpoint, recovery_payload(model, opt, epoch, 2000000, sums, protocol_sha, seed))
    if reservation.exists():
        saved = read(reservation)
        assert saved['learned_state_sha256'] == before and saved['checkpoint_sha256'] == sha(checkpoint)
        assert saved['protocol_sha256'] == protocol_sha
    else:
        write(reservation, {'at_utc': now(), 'epoch': epoch, 'seed': seed, 'protocol_sha256': protocol_sha,
              'checkpoint_sha256': sha(checkpoint), 'learned_state_sha256': before,
              'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
    if report.exists():
        saved = read(report)
        assert saved['learned_state_sha256'] == before and sha(output) == saved['development_predictions']['sha256']
        assert saved['checkpoint']['sha256'] == sha(checkpoint)
        return
    cpu_rng, gpu_rng = torch.get_rng_state(), torch.cuda.get_rng_state()
    indices = np.unique(np.concatenate((dev['a'], dev['b'])))
    embeddings = endpoint_cache(model, tokens, indices)
    # Per-checkpoint native-head fidelity on features only. No outcome-based
    # change to architecture, batching, scoring direction or length policy.
    fixture_a, fixture_b = dev['a'][:32], dev['b'][:32]
    with torch.inference_mode():
        native = np.asarray([float(model.class_head(embeddings[int(a):int(a)+1],
                            embeddings[int(b):int(b)+1]).item()) for a, b in zip(fixture_a, fixture_b, strict=True)])
    actual = scores(model, embeddings, fixture_a, fixture_b)
    reversal = scores(model, embeddings, fixture_b, fixture_a)
    error = float(np.max(np.abs(native - actual)))
    reverse_error = float(np.max(np.abs(actual - reversal)))
    if error > 1e-4 or reverse_error > 1e-4:
        raise RuntimeError('Checkpoint singleton-head qualification failed')
    values = scores(model, embeddings, dev['a'], dev['b'])
    metric = concordance(values, dev['positive'], dev['weight'])
    temporary = output.with_suffix('.next.npy')
    with temporary.open('wb') as handle:
        np.save(handle, values, allow_pickle=False)
    temporary.replace(output)
    assert learned_digest(model) == before
    torch.set_rng_state(cpu_rng)
    torch.cuda.set_rng_state(gpu_rng)
    write(report, {'at_utc': now(), 'seed': seed, 'epoch': epoch, 'protocol_sha256': protocol_sha,
          'checkpoint': record(checkpoint, root), 'learned_state_sha256': before,
          'development_predictions': record(output, root), 'C3_development_concordance': metric,
          'rows': len(values), 'positive_rows': int(dev['positive'].sum()),
          'all_rows_scored_finitely': True, 'singleton_head_error': error, 'reversal_error': reverse_error,
          'score_type': 'native pre-sigmoid logit; not a calibrated probability',
          'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
    event({'event': 'development_complete', 'epoch': epoch, 'C3_development_concordance': metric,
           'rows': len(values), 'checkpoint_sha256': sha(checkpoint)})


def nested_equal(a, b):
    """Exact recovery check including Ranger21's state outside state_dict()."""
    if torch.is_tensor(a):
        return torch.is_tensor(b) and torch.equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(nested_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return isinstance(b, type(a)) and len(a) == len(b) and all(nested_equal(x, y) for x, y in zip(a, b))
    return a == b
