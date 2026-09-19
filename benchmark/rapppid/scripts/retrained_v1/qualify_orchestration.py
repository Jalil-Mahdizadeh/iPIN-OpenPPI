"""Exercise retained checkpoints and full-size reports using TRAIN-only fixtures.

The synthetic panel is deliberately stored outside formal training/results.
Its repeated TRAIN pairs are NOT the real C3-development panel or a performance
estimate. This tests I/O, checkpoint identity, RNG preservation and idempotence.
"""
from pathlib import Path
import shutil
import numpy as np
import torch
from common import SEEDS, arrays, cuda, now, record, sha, write
from model import Tokens, fresh, learned_digest, optimizer, step
from pipeline import evaluate_development


def main():
    root = Path('/output/orchestration-qualification')
    root.mkdir(exist_ok=False)
    data, code = root / 'data', root / 'code'
    data.mkdir()
    code.mkdir()
    train = arrays('/output/data/training.npz')
    train['normalized_u_weight'] = train['u_weight'] / train['u_weight'].mean()
    dev = {'a': np.r_[np.resize(train['p_a'][:8], 2265), np.resize(train['u_a'][:8], 1000000)],
           'b': np.r_[np.resize(train['p_b'][:8], 2265), np.resize(train['u_b'][:8], 1000000)],
           'positive': np.r_[np.ones(2265, bool), np.zeros(1000000, bool)],
           'weight': np.r_[np.ones(2265), np.resize(train['u_weight'][:8], 1000000)]}
    np.savez(data / 'development_00.npz', **dev)
    files = [record(data / 'development_00.npz', data)]
    write(data / 'DATA_MANIFEST.json', {'synthetic_TRAIN_fixture_only': True, 'files': files}, exclusive=True)
    for path in sorted(Path('/code').glob('*.py')):
        shutil.copyfile(path, code / path.name)
    protocol = {'synthetic_TRAIN_fixture_only': True, 'code_files': [record(p, code) for p in sorted(code.glob('*.py'))],
                'data_manifest_sha256': sha(data / 'DATA_MANIFEST.json')}
    write(root / 'protocol.json', protocol, exclusive=True)
    tokens = Tokens('/output/data')
    used = np.unique(np.r_[dev['a'], dev['b']])
    assert all(tokens.meta['partition'][int(i)] == 'train' for i in used)
    device = cuda()
    for seed in SEEDS:
        model = fresh(seed, device)
        opt = optimizer(model)
        p, u = np.arange(40), np.arange(40)
        metrics = step(model, opt, tokens, train, p, u, seed, 1, 0)
        # In-memory role override ONLY for the synthetic I/O harness. No actual
        # sequence metadata, partition, tokenizer or training input is changed.
        for index in used:
            tokens.meta['partition'][int(index)] = 'development'
        output = root / 'training' / f'seed_{seed}'
        output.mkdir(parents=True)
        before = learned_digest(model)
        cpu_rng, gpu_rng = torch.get_rng_state(), torch.cuda.get_rng_state()
        for epoch in (4, 8):
            for repeat in range(2):
                evaluate_development(output, epoch, model, opt, tokens, dev, sha(root / 'protocol.json'),
                                     seed, {'loss': metrics['loss'] * 2000000}, lambda event: None)
                assert learned_digest(model) == before
                assert torch.equal(cpu_rng, torch.get_rng_state())
                assert torch.equal(gpu_rng, torch.cuda.get_rng_state())
        for index in used:
            tokens.meta['partition'][int(index)] = 'train'
        del model, opt
        torch.cuda.empty_cache()
    (root / 'results/tmp').mkdir(parents=True)
    write(root / 'PIPELINE_QUALIFICATION.json', {
        'at_utc': now(), 'passed': True, 'synthetic_TRAIN_fixture_only': True,
        'rows_per_fixture': 1002265, 'independent_models': 3, 'retention_epochs_exercised': [4, 8],
        'repeat_calls_verified': True, 'model_and_RNG_unchanged_by_reporting': True,
        'real_development_outcomes_used': False, 'test_pairs_read': False, 'test_truth_read': False,
        'formal_training_performed': False, 'fixture_weights_not_used_in_formal_training': True,
    }, exclusive=True)
    print('Synthetic TRAIN-only full-size checkpoint/report fixtures passed; ready for actual reporting entrypoint.', flush=True)


if __name__ == '__main__':
    main()
