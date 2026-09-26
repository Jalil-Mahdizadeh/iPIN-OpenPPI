"""Exact registered default scoring on the two unchanged transfer panels."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import sys
import time
import h5py
import numpy as np
import torch

# The guard's script directory precedes PYTHONPATH; choose the immutable bundle.
sys.path.insert(0, '/code')
from transfer_io import *
sys.path.insert(0, str(BUNDLE / 'code'))
import adapter
from common import cuda


def score(study, freeze, device):
    start = time.monotonic()
    source = ROOT / 'benchmark' / study
    output = OUT / study
    require(not (output / 'SCORING_RUN.json').exists(), 'Scores already complete')
    rows = table(source / 'panels.csv')
    with gzip.open(source / 'selected_sequences.json.gz', 'rt') as stream:
        sequences = json.load(stream)
    for key, sequence in sequences.items():
        require(hashlib.sha256(sequence.encode()).hexdigest() == key, 'Sequence identity mismatch')
        require(50 <= len(sequence) <= 2000 and set(sequence) <= set('ACDEFGHIKLMNPQRSTVWY'), 'Unexpected sequence scope')
    order = read(source / 'sequence_order.json')
    require(order == sorted(sequences, key=lambda h: (len(sequences[h]), h)), 'Endpoint order changed')
    index = {h: i for i, h in enumerate(order)}
    lengths = np.array([len(sequences[h]) for h in order], np.int64)
    offsets = np.r_[0, np.cumsum(lengths)]
    a = np.array([index[r['query_sequence_sha256']] for r in rows], np.int64)
    b = np.array([index[r['partner_sequence_sha256']] for r in rows], np.int64)
    for i, row in enumerate(rows):
        require(int(row['row_index']) == i, 'Pair order changed')
        for side in ('query', 'partner'):
            require(int(row[side + '_sequence_length']) == len(sequences[row[side + '_sequence_sha256']]), 'Pair/sequence mismatch')
    if study == STUDIES[0]:
        allowed = {s['id']: str(s['taxid']) for s in read(source / 'config.json')['species']}
        require(all(r['species'] in allowed and r['taxid'] == allowed[r['species']] for r in rows), 'Unexpected species')
    else:
        require(all(r['query_taxid'] == '559292' and r['partner_taxid'] == '9606' for r in rows), 'Unexpected reference organisms')
    require(int(offsets[-1]) * 640 * 4 < torch.cuda.mem_get_info()[0] - (12 << 30), 'Insufficient GPU residue memory')
    values = torch.empty((int(offsets[-1]), 640), dtype=torch.float32, device=device)
    with h5py.File(source / 'local/tuna_residues.h5', 'r') as cache:
        require(bool(cache.attrs['complete']), 'Incomplete cache')
        require(cache.attrs['selected_sequences_sha256'] == sha(source / 'selected_sequences.json.gz'), 'Wrong cache snapshot')
        require(set(cache) == set(order), 'Cache endpoint mismatch')
        for i, h in enumerate(order):
            x = cache[h][:]
            require(x.dtype == np.float32 and x.shape == (lengths[i], 640) and np.isfinite(x).all(), 'Invalid residues')
            values[offsets[i]:offsets[i+1]] = torch.from_numpy(x).to(device)
    print(f'{study}: loaded {len(order):,} verified sequences / {offsets[-1]:,} residues', flush=True)
    # Fixed fixtures: each species, length quantiles, and longest total pair.
    fixtures = {next(i for i, r in enumerate(rows) if r['species'] == s) for s in sorted({r['species'] for r in rows})}
    total_length = lengths[a] + lengths[b]
    ranked = np.argsort(total_length, kind='stable')
    fixtures.update(int(ranked[int(q * (len(rows)-1))]) for q in (0, .25, .5, .75, .9, 1))
    fixtures = sorted(fixtures)
    scores, qualifications = {}, []
    for member in freeze['model']['members']:
        member_start = time.monotonic()
        seed = member['seed']
        checkpoint = BUNDLE / member['state']['path']
        require(sha(checkpoint) == member['state']['sha256'], 'Checkpoint changed')
        initial = torch.load(checkpoint, map_location='cpu', weights_only=True)
        model = adapter.create(seed=seed, checkpoint=checkpoint, device=device)
        model.gp_layer.fitted = True  # MUST precede eval; never refit covariance.
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        adapter.enable_sdpa(model)
        require(torch.equal(model.gp_layer.covariance.cpu(), initial['gp_layer.covariance']), 'Saved covariance changed')
        z = torch.empty((len(order), 64), dtype=torch.float32, device=device)
        with torch.inference_mode():
            begin, next_report = 0, 5000
            while begin < len(order):
                longest = lengths[min(begin + 16, len(order))-1]
                count = max(1, min(16, 16000000 // int(longest * longest)))
                ids = list(range(begin, min(begin + count, len(order))))
                x = torch.zeros((len(ids), int(lengths[ids].max()), 640), dtype=torch.float32, device=device)
                for j, i in enumerate(ids):
                    x[j, :lengths[i]] = values[offsets[i]:offsets[i+1]]
                z[ids] = adapter.endpoint_features(model, x, lengths[ids].tolist())
                begin += len(ids)
                if begin >= next_report or begin == len(order):
                    print(f'{study} seed {seed}: {begin}/{len(order)} endpoints; {time.monotonic()-member_start:.1f}s', flush=True)
                    next_report += 5000
        require(bool(torch.isfinite(z).all()), 'Nonfinite endpoint features')
        prediction = adapter.cached_scores(model, z, a, b, probabilities=False)
        reverse = adapter.cached_scores(model, z, b, a, probabilities=False)
        require(np.array_equal(prediction, reverse), 'Pair-order asymmetry')
        oracle = adapter.create(seed=seed, checkpoint=checkpoint, device=device)
        oracle.gp_layer.fitted = True
        oracle.eval()
        reference = []
        with torch.inference_mode():
            for i in fixtures:
                left, right = values[offsets[a[i]]:offsets[a[i]+1]], values[offsets[b[i]]:offsets[b[i]+1]]
                packed = adapter.native.test_pack([left], [right], [0], 512, 640, device)
                logit, variance = oracle.forward(packed[0], packed[1], packed[3], packed[4], packed[5], packed[6], True, False)
                reference.append(float((logit.reshape(-1) / torch.sqrt(1 + math.pi / 8 * variance)).reshape(())))
        error = float(np.max(np.abs(prediction[fixtures].astype(np.float64) - reference)))
        require(error <= 1e-5, f'Native qualification failed: {seed}: {error}')
        for instance in (model, oracle):
            for key, value in instance.state_dict().items():
                require(torch.equal(value.detach().cpu(), initial[key]), 'Model state changed: ' + key)
        with (output / f'{NEW}_seed{seed}_endpoint_features.npy').open('xb') as stream:
            np.save(stream, z.cpu().numpy(), allow_pickle=False)
        scores[f'{NEW}_seed{seed}'] = prediction.astype(np.float64)
        qualifications.append({'seed': seed, 'native_max_absolute_error': error, 'native_tolerance': 1e-5,
            'fixture_rows_zero_based': fixtures, 'pair_order_symmetry_passed': True,
            'parameters_and_buffers_unchanged': True, 'saved_GP_covariance_preserved': True,
            'checkpoint': member['state'], 'elapsed_seconds': time.monotonic()-member_start})
        print(f'{study} seed {seed}: {len(rows):,} pairs complete; native error {error:.3g}', flush=True)
        del model, oracle, z, initial
        torch.cuda.empty_cache()
    scores[NEW] = np.column_stack(list(scores.values())).mean(axis=1, dtype=np.float64)
    identity = ('row_index', 'target_id', 'query_sequence_sha256', 'partner_sequence_sha256', 'pair_key')
    write_csv(output / 'default_model_scores.csv', [{**{key: row[key] for key in identity},
        **{key + '_score': float(value[i]) for key, value in scores.items()}} for i, row in enumerate(rows)])
    write_json(output / 'sequence_order.json', order)
    artifacts = [record(output / 'default_model_scores.csv'), record(output / 'sequence_order.json')]
    artifacts += [record(path) for path in sorted(output.glob('*endpoint_features.npy'))]
    write_json(output / 'SCORING_RUN.json', {'at_utc': now(), 'study': study, 'pairs': len(rows),
        'sequences': len(order), 'residues': int(offsets[-1]), 'gpu': torch.cuda.get_device_name(),
        'torch': torch.__version__, 'cuda': torch.version.cuda, 'elapsed_seconds': time.monotonic()-start,
        'default_model': freeze['default_model'], 'registry_sha256': freeze['registry_sha256'],
        'input_freeze_sha256': sha(OUT / 'INPUT_FREEZE.json'), 'precision': freeze['model']['precision'],
        'learned_features_recomputed': True, 'verified_historical_ESM_cache_reused': True,
        'training_or_selection': False, 'GP_covariance_refitted': False, 'GP_fitted_set_before_eval': True,
        'qualifications': qualifications, 'outputs': artifacts})
    del values
    torch.cuda.empty_cache()


def main():
    freeze = read(OUT / 'INPUT_FREEZE.json')
    verify_small_inputs(freeze)
    device = cuda(freeze['model']['seeds'][0])
    for study in STUDIES:
        score(study, freeze, device)
    write_json(OUT / 'PREDICTION_FREEZE.json', {'at_utc': now(),
        'runs': [record(OUT / study / 'SCORING_RUN.json') for study in STUDIES],
        'input_freeze': record(OUT / 'INPUT_FREEZE.json'), 'complete': True})


if __name__ == '__main__':
    main()

