"""Exercise real scorer serialization and candidate/reference identity failures."""
from pathlib import Path
import tempfile
import numpy as np
import pyarrow as pa
import torch
from common import cuda, now, read, record, write
from comparison import prediction_values, verify
from data import ResidueCache
from frozen_scorer import Scorer
from model import PairModel
from selection import choose_promotions
from train import orders


def rejects(fn):
    try:
        fn()
    except RuntimeError:
        return
    raise AssertionError('Expected rejection did not occur')


def main():
    device = cuda(718)
    config = read('/config.json')
    tokens = pa.array(['c', 'a', 'b'])
    reference = pa.table({'candidate_token': ['a', 'b', 'c'], 'score': [1., 2., 3.]})
    assert np.array_equal(prediction_values(tokens, reference), [3., 1., 2.])
    tuna = pa.table({'candidate_token': ['a', 'b', 'c'], 'unused': [-1., -2., -3.],
                     'tuna_retrained_ensemble': [1., 2., 3.]})
    assert np.array_equal(prediction_values(tokens, tuna, 'tuna_retrained_ensemble'), [3., 1., 2.])
    rejects(lambda: prediction_values(tokens, pa.table({'candidate_token': ['a', 'a', 'b'], 'score': [1., 2., 3.]})))
    rejects(lambda: prediction_values(tokens, pa.table({'candidate_token': ['a', 'b', 'x'], 'score': [1., 2., 3.]})))
    rejects(lambda: prediction_values(tokens, pa.table({'candidate_token': ['a', 'b', 'c'], 'score': [1., 2., float('nan')]})))
    best = [{'recipe': x, 'C3_development_concordance': .81 + i * .001} for i, x in enumerate(config['recipes'])]
    promoted, selected = choose_promotions(best, config)
    assert [x['recipe']['name'] for x in promoted] == ['cross_attention_wide', 'cross_attention']
    assert selected[-1]['recipe']['name'] == 'mean_pool'
    for x in best:
        x['C3_development_concordance'] = config['promotion_reference_C3_development']
    assert choose_promotions(best, config) == ([], [])
    p, u = orders(1, 2, 3, 17)
    assert sorted(u.tolist()) == list(range(17))
    counts = np.bincount(p); assert counts.max() - counts.min() == 1
    assert all(np.array_equal(x, y) for x, y in zip((p, u), orders(1, 2, 3, 17)))
    cache = ResidueCache.__new__(ResidueCache)
    cache.device = device
    cache.lengths = torch.tensor([3, 7, 900], device=device)
    cache.offsets = torch.tensor([0, 3, 10, 910], device=device)
    cache.values = torch.arange(910, device=device, dtype=torch.float32)[:, None].expand(-1, 640)
    sampled, valid = cache.pack([2, 0, 1], sample=64)
    assert torch.equal(sampled[1, :3, 0], torch.arange(3, device=device, dtype=torch.float32))
    assert torch.equal(sampled[2, :7, 0], torch.arange(3, 10, device=device, dtype=torch.float32))
    long_positions = sampled[0, :, 0] - 10
    assert bool((long_positions[1:] > long_positions[:-1]).all())
    assert float(long_positions.min()) >= 0 and float(long_positions.max()) < 900
    assert valid.sum(1).tolist() == [64, 3, 7]
    with tempfile.TemporaryDirectory(prefix='pipeline-', dir='/output/.tmp') as directory:
        root = Path(directory); (root / 'weights').mkdir(); (root / 'features').mkdir()
        globals_ = np.random.default_rng(21).standard_normal((17000, 640)).astype(np.float32)
        np.save(root / 'global_standardized.npy', globals_, allow_pickle=False)
        specification = {'scorers': [], 'ensembles': [], 'members': []}
        oracle = {}
        a, b = np.array([0, 1, 4, 2]), np.array([3, 4, 2, 1])
        gpu_globals = torch.as_tensor(globals_, device=device)
        for recipe in (config['recipes'][0], config['recipes'][2]):
            ensemble = recipe['name'] + '_ensemble'
            specification['ensembles'].append(ensemble); specification['scorers'].append(ensemble)
            for seed in config['seeds']:
                cuda(seed); model = PairModel(recipe).to(device)
                if model.has_local:
                    torch.nn.init.normal_(model.local_head[-1].weight, std=.02)
                model.eval()
                name = recipe['name'] + f'_seed{seed}'
                shape = (17000, recipe['tokens'], recipe['dimension']) if model.has_local else (17000, 1, 1)
                latent = np.zeros(shape, np.float32)
                latent[:5] = np.random.default_rng(seed).standard_normal(latent[:5].shape).astype(np.float32)
                np.save(root / 'features' / f'{name}.npy', latent, allow_pickle=False)
                torch.save(model.state_dict(), root / 'weights' / f'{name}.pt')
                with torch.inference_mode():
                    oracle[name] = model.score(gpu_globals[a], gpu_globals[b],
                        torch.as_tensor(latent[a], device=device), torch.as_tensor(latent[b], device=device)).cpu().numpy()
                specification['scorers'].append(name)
                specification['members'].append({'name': name, 'ensemble': ensemble, 'recipe': recipe,
                    'checkpoint': f'weights/{name}.pt', 'features': f'features/{name}.npy'})
                del model
        scorer = Scorer(root, device, specification)
        values = scorer.scores(a, b)
        error = max(float(np.max(np.abs(values[:, specification['scorers'].index(name)] - expected))) for name, expected in oracle.items())
        symmetry = float(np.max(np.abs(values - scorer.scores(b, a))))
        assert error < 2e-5 and symmetry < 2e-5
        for ensemble in specification['ensembles']:
            columns = [specification['scorers'].index(x['name']) for x in specification['members'] if x['ensemble'] == ensemble]
            assert np.array_equal(values[:, specification['scorers'].index(ensemble)], values[:, columns].mean(1))
        path = root / 'fixture.txt'; path.write_text('original')
        item = record(path); item['path'] = path.name
        verify(root, [item]); path.write_text('changed')
        rejects(lambda: verify(root, [item]))
        rejects(lambda: verify(root, [{'path': '../escape', 'bytes': 1, 'sha256': '0' * 64}]))
        rejects(lambda: scorer.scores([-1], [0]))
        rejects(lambda: scorer.scores([0], [17000]))
    result = {'at_utc': now(), 'passed': True, 'frozen_roundtrip_max_error': error,
              'frozen_swap_error': symmetry, 'dynamic_multimodel_ensembles': True,
              'reference_token_permutation_and_TUnA_column': True,
              'duplicate_missing_nonfinite_reference_rejected': True,
              'tampered_artifact_and_path_traversal_rejected': True,
              'strict_development_promotion_and_no_promotion': True,
              'stratified_sampling_and_short_sequence_padding': True,
              'balanced_P_and_complete_U_training_orders': True,
              'test_pairs_read': False, 'test_truth_read': False}
    write('/output/PIPELINE_QUALIFICATION.json', result, exclusive=True)
    print(result, flush=True)


if __name__ == '__main__':
    main()
