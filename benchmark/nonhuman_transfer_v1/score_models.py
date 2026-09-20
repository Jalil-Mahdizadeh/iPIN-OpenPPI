"""Apply three unchanged frozen ensembles to the prospective external panel."""
from __future__ import annotations
import argparse
import gzip
import importlib.util
import math
import sys
import time
from study_utils import *

SEEDS = (20260803, 20260817, 20260831)
TUNA_SHA = '98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1'

def inputs(*unused):
    freeze = read(OUT / 'INPUT_FREEZE.json')
    check_records(freeze['files'])
    rows = table(OUT / 'panels.csv')
    with gzip.open(OUT / 'selected_sequences.json.gz', 'rt') as f:
        seqs = json.load(f)
    order = sorted(seqs, key=lambda h: (len(seqs[h]), h))
    return rows, None, order, [seqs[h] for h in order]

def parent():
    path = ROOT / 'example/twelve_target_comparison_v2/run_comparison.py'
    spec = importlib.util.spec_from_file_location('qualified_example_scoring', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.inputs = inputs
    sys.path.insert(0, str(ROOT / 'example'))
    return module

def tuna():
    import h5py
    import numpy as np
    import torch
    started = time.monotonic()
    runner = parent()
    device = runner.configure_gpu()
    rows, _, order, sequences = inputs()
    registry = runner.catalogue(ROOT)
    bundle = ROOT / registry['model_bundles']['tuna_retrained_ensemble']
    scripts = bundle / 'code'
    os.environ['TUNA_UPSTREAM_DIR'] = str(bundle / 'upstream/TUnA/results/bernett/TUnA')
    sys.path.insert(0, str(scripts))
    import adapter
    import esm_cache
    if sha(ROOT / 'benchmark/containers/images/tuna-arm64-v1.sif') != TUNA_SHA:
        raise RuntimeError('TUnA runtime changed')
    verified = []
    for item in registry['bundle_files']:
        if item['path'].startswith('features/'):
            continue
        p = bundle / item['path']
        if sha(p) != item['sha256'] or p.stat().st_size != item['bytes']:
            raise RuntimeError(f'Frozen bundle changed: {p}')
        verified.append(record(p))
    encoder_dir = ROOT / '.private/frozen_pair_models_v1/bundle/encoder'
    encoder, alphabet, ignored = esm_cache.load_encoder(encoder_dir, device)
    fixtures = sorted({len(order) // 4, len(order) // 2, int(.9 * len(order))})
    esm_qualification = esm_cache.qualify(encoder, alphabet, encoder_dir,
        [sequences[i] for i in fixtures], OUT / 'TUNA_ESM_QUALIFICATION.json')
    lengths = np.array([len(s) for s in sequences], np.int64)
    offsets = np.r_[0, np.cumsum(lengths)]
    needed = int(offsets[-1]) * 640 * 4
    if needed > torch.cuda.mem_get_info()[0] - (12 << 30):
        raise RuntimeError('Residue cache needs more GPU memory than available; use a documented streaming execution')
    values = torch.empty((int(offsets[-1]), 640), dtype=torch.float32, device=device)
    print(f'TUnA: {len(order):,} fresh sequences; {needed / 2**30:.1f} GiB residues', flush=True)
    with h5py.File(LOCAL / 'tuna_residues.h5', 'x') as f:
        f.attrs['selected_sequences_sha256'] = sha(OUT / 'selected_sequences.json.gz')
        for start in range(0, len(order), 4):
            batch = esm_cache.embed(encoder, alphabet, sequences[start:start + 4])
            for i, value in enumerate(batch, start):
                if value.shape != (lengths[i], 640) or value.dtype != torch.float32 or not torch.isfinite(value).all():
                    raise RuntimeError('Invalid fresh embedding')
                values[offsets[i]:offsets[i+1]] = value
                f.create_dataset(order[i], data=value.cpu().numpy())
            if start % 1000 == 0:
                print(f'TUnA ESM {start}/{len(order)}; {time.monotonic()-started:.1f}s', flush=True)
        f.attrs['complete'] = True
    del encoder, batch
    torch.cuda.empty_cache()
    index = {h: i for i, h in enumerate(order)}
    a = np.array([index[r['query_sequence_sha256']] for r in rows])
    b = np.array([index[r['partner_sequence_sha256']] for r in rows])
    fixtures = sorted({next(i for i, r in enumerate(rows) if r['species'] == s['id']) for s in CONFIG['species']
                       if any(r['species'] == s['id'] for r in rows)} | {int(np.argmax(lengths[a] + lengths[b]))})
    predictions, qualifications = {}, []
    for seed in SEEDS:
        member = f'tuna_retrained_seed{seed}'
        path = bundle / 'weights' / (member + '.pt')
        initial = torch.load(path, map_location='cpu', weights_only=True)
        model = adapter.create(checkpoint=path, device=device)
        model.gp_layer.fitted = True
        model.eval()
        for p in model.parameters():
            p.requires_grad_(False)
        adapter.enable_sdpa(model)
        z = torch.empty((len(order), 64), dtype=torch.float32, device=device)
        with torch.inference_mode():
            start = 0
            while start < len(order):
                longest = lengths[min(start+16, len(order))-1]
                count = max(1, min(16, 16000000 // int(longest*longest)))
                ids = list(range(start, min(start+count, len(order))))
                width = int(lengths[ids].max())
                x = torch.zeros((len(ids), width, 640), dtype=torch.float32, device=device)
                for j, i in enumerate(ids):
                    x[j, :lengths[i]] = values[offsets[i]:offsets[i+1]]
                z[ids] = adapter.endpoint_features(model, x, lengths[ids].tolist())
                start += len(ids)
        if not torch.isfinite(z).all():
            raise RuntimeError('Nonfinite endpoint representation')
        with (LOCAL / (member + '_features.npy')).open('xb') as f:
            np.save(f, z.cpu().numpy(), allow_pickle=False)
        score = adapter.cached_scores(model, z, a, b, probabilities=False)
        reverse = adapter.cached_scores(model, z, b, a, probabilities=False)
        if not np.array_equal(score, reverse):
            raise RuntimeError('Pair-order asymmetry')
        oracle = adapter.create(checkpoint=path, device=device)
        oracle.gp_layer.fitted = True
        oracle.eval()
        reference = []
        with torch.inference_mode():
            for i in fixtures:
                left, right = values[offsets[a[i]]:offsets[a[i]+1]], values[offsets[b[i]]:offsets[b[i]+1]]
                packed = adapter.native.test_pack([left], [right], [0], 512, 640, device)
                logit, variance = oracle.forward(packed[0], packed[1], packed[3], packed[4], packed[5], packed[6], True, False)
                reference.append(float((logit.reshape(-1) / torch.sqrt(1+math.pi*variance/8)).reshape(())))
        error = float(np.max(np.abs(score[fixtures].astype(np.float64)-reference)))
        if error > 1e-5:
            raise RuntimeError(f'Native qualification failed: {error}')
        for key, value in model.state_dict().items():
            if not torch.equal(value.detach().cpu(), initial[key]):
                raise RuntimeError(f'Parameter/buffer changed: {key}')
        qualifications.append(dict(seed=seed, native_max_absolute_error=error, tolerance=1e-5,
            fixture_rows=fixtures, pair_order_symmetry_passed=True, parameters_and_buffers_unchanged=True))
        predictions[member] = score.astype(np.float64)
        print(f'{member}: {len(rows):,} pairs; native maximum error {error:.3g}', flush=True)
        del model, oracle, z, initial
        torch.cuda.empty_cache()
    predictions['tuna_retrained'] = np.column_stack(list(predictions.values())).mean(axis=1, dtype=np.float64)
    write_csv(OUT / 'tuna_scores.csv', [dict(row_index=i, **{k+'_score': float(v[i]) for k,v in predictions.items()}) for i in range(len(rows))])
    write_json(OUT / 'sequence_order.json', order)
    write_json(OUT / 'TUNA_RUN.json', dict(at_utc=now(), elapsed_seconds=time.monotonic()-started,
        device=torch.cuda.get_device_name(), torch=torch.__version__, SIF_sha256=TUNA_SHA,
        fresh_sequences=len(order), total_residues=int(offsets[-1]), selected_epoch=4, seeds=list(SEEDS),
        GP_covariance_refitted=False, preexisting_feature_cache_reads=0, native_qualification=qualifications,
        esm_qualification=esm_qualification, ignored_unused_encoder_keys=ignored, verified_model_inputs=verified,
        output=record(OUT / 'tuna_scores.csv'), residues=record(LOCAL / 'tuna_residues.h5'), script=record(Path(__file__))))

def main():
    require_container()
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['freeze', 'ipin', 'tuna'])
    phase = parser.parse_args().phase
    if phase == 'freeze':
        catalogue = ROOT / 'artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json'
        if sha(catalogue) != CONFIG['model_registry_sha256']:
            raise RuntimeError('Model registry changed')
        selection = read(OUT / 'PANEL_SELECTION.json')
        check_records(selection['outputs'])
        names = ['config.json', 'PROTOCOL.md', 'study_utils.py', 'acquire.py', 'parse_sources.py',
                 'build_panels.py', 'score_models.py', 'audit_exposure.py', 'analyze.py', 'validate.py',
                 'panels.csv', 'proteins.csv', 'targets.csv', 'selected_sequences.json.gz',
                 'selected_evidence.json.gz', 'PANEL_SELECTION.json', 'SOURCES.json', 'SOURCE_PARSING_v2.json',
                 'PRE_SCORING_EVIDENCE_ADJUSTMENT.md', 'PANEL_VALIDATION.json']
        records = [record(OUT / p) for p in names]
        records += [record(catalogue), record(ROOT / 'example/twelve_target_comparison_v2/run_comparison.py'),
                    record(ROOT / 'example/twelve_target_comparison_v1/metrics.py'), record(ROOT / 'example/score_frozen_models.py')]
        write_json(OUT / 'INPUT_FREEZE.json', dict(at_utc=now(), no_model_inference_yet=True, files=records,
            pairs=selection['pairs'], P=selection['P'], U=selection['U'], unique_sequences=selection['unique_sequences']))
    elif phase == 'ipin':
        parent().ipin(ROOT, OUT)
    else:
        tuna()

if __name__ == '__main__':
    main()
