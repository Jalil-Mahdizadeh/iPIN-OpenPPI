"""Build exact singleton caches and freeze this newly authorized test scorer.

Only public endpoint features and TRAIN pairs are mounted in this phase.
No test candidate pairs, test truth, or development labels are mounted.
"""
import hashlib
from pathlib import Path
import shutil
import time
import numpy as np
import torch
from common import SEEDS, UPSTREAM_COMMIT, SEQUENCES_SHA, DATA_SHA, cuda, now, read, record, sha, verify, write
from model import Tokens, endpoint_cache, fresh, learned_digest, scores
from frozen_scorer import Scorer, SCORERS
from benchmark_metrics import qualify


def main():
    started = time.monotonic(); root = Path('/output')
    selection = read(root / 'SELECTION.json')
    verify(root, selection['files'])
    for item in selection['code_files']:
        assert sha(Path('/code') / Path(item['path']).name) == item['sha256']
    assert sha('/data/sequences.json') == SEQUENCES_SHA
    assert sha('/data/training.npz') == DATA_SHA
    assert sha('/data/spm.model') == selection['tokenizer_sha256']
    device = cuda(); tokens = Tokens(); meta = tokens.meta
    assert len(meta['sequence']) == 17000 and len(set(meta['sha256'])) == 17000
    assert all(hashlib.sha256(s.encode()).hexdigest() == h for s, h in zip(meta['sequence'], meta['sha256'], strict=True))
    with np.load('/data/training.npz', allow_pickle=False) as train:
        a = train['u_a'][:32].copy(); b = train['u_b'][:32].copy()
    ids = np.flatnonzero(np.asarray(meta['partition']) == 'train')
    longest = ids[np.argsort(np.asarray(meta['length'])[ids])[-12:]]
    a = np.r_[a, longest]; b = np.r_[b, longest[::-1]]
    assert all(meta['partition'][int(i)] == 'train' for i in np.r_[a, b])
    bundle = root / 'scorer_bundle'; bundle.mkdir()
    (bundle / 'checkpoints').mkdir(); (bundle / 'code').mkdir()
    for item in selection['code_files']:
        shutil.copyfile(root / item['path'], bundle / 'code' / Path(item['path']).name)
    for name, key in (('endpoints.json', 'sha256'), ('components.json', 'component'), ('lengths.json', 'length')):
        write(bundle / name, meta[key], exclusive=True)
    shutil.copyfile(root / 'SELECTION.json', bundle / 'SELECTION.json')
    shutil.copyfile('/data/spm.model', bundle / 'spm.model')
    members, expected = [], []
    for member in selection['members']:
        tick = time.monotonic(); seed = member['seed']
        checkpoint = root / member['checkpoint']['path']
        state = torch.load(checkpoint, map_location='cpu', weights_only=True)
        assert state['seed'] == seed and state['epoch'] == 8
        assert state['next_comparison'] == member['comparisons_in_current_epoch']
        assert state['protocol_sha256'] == selection['training_protocol_sha256']
        assert all(torch.isfinite(v).all() for v in state['model'].values())
        assert {int(x['step']) for x in state['optimizer']['state'].values()} == {member['total_optimizer_updates']}
        model = fresh(seed, device).eval(); model.load_state_dict(state['model'], strict=True)
        before = learned_digest(model)
        assert before == member['learned_state_sha256']
        embeddings = torch.full((17000, 64), float('nan'), device=device)
        for partition in sorted(set(meta['partition'])):
            indices = np.flatnonzero(np.asarray(meta['partition']) == partition)
            values = endpoint_cache(model, tokens, indices, allowed_partition=partition)
            embeddings[indices] = values[indices]
            print({'seed': seed, 'cached_partition': partition, 'endpoints': len(indices),
                   'seconds': time.monotonic() - tick}, flush=True)
        assert torch.isfinite(embeddings).all() and (embeddings.std(1) > 0).all()
        with torch.inference_mode():
            native = np.asarray([float(model.class_head(embeddings[int(i):int(i)+1], embeddings[int(j):int(j)+1]).item())
                                 for i, j in zip(a, b, strict=True)])
        errors = []
        for batch in (1, 8, 8192):
            actual = scores(model, embeddings, a, b, batch=batch)
            errors.extend([float(np.max(np.abs(actual - native))),
                           float(np.max(np.abs(actual - scores(model, embeddings, b, a, batch=batch))))])
        assert max(errors) <= 1e-4
        assert learned_digest(model) == before
        with (bundle / f'embeddings_{seed}.npy').open('xb') as handle:
            np.save(handle, embeddings.cpu().numpy(), allow_pickle=False)
        shutil.copyfile(checkpoint, bundle / 'checkpoints' / checkpoint.name)
        members.append({**member, 'checkpoint_sha256': sha(checkpoint), 'native_head_max_error': max(errors),
                        'cache_seconds': time.monotonic() - tick, 'learned_state_unchanged': True})
        expected.append(native)
        del values, embeddings, model, state
        torch.cuda.empty_cache()
    config = {'members': members, 'training_protocol_sha256': selection['training_protocol_sha256']}
    wrapper = Scorer(bundle, device, config=config)
    expected = np.column_stack(expected)
    expected = np.column_stack([expected.mean(1, dtype=np.float64), expected])
    checks = []
    for batch in (1, 8, 8192):
        wrapper.batch = batch
        actual = wrapper.scores(a, b)
        error = float(np.max(np.abs(actual - expected)))
        reverse_error = float(np.max(np.abs(actual - wrapper.scores(b, a))))
        order_error = float(np.max(np.abs(actual[::-1] - wrapper.scores(a[::-1].copy(), b[::-1].copy()))))
        assert max(error, reverse_error, order_error) <= 1e-4
        assert np.array_equal(actual[:, 0], actual[:, 1:].mean(1, dtype=np.float64))
        checks.append({'batch': batch, 'native_error': error, 'reverse_error': reverse_error, 'order_error': order_error})
    wrapper.verify_state()
    qualification = {'at_utc': now(), 'passed': True, 'members': members, 'wrapper_checks': checks,
        'native_logit_tolerance': 1e-4, 'metric_qualification': qualify(device), 'gpu': torch.cuda.get_device_name(),
        'endpoints_per_seed': 17000, 'train_fixture_pairs': len(a), 'elapsed_seconds': time.monotonic()-started,
        'training_performed': False, 'test_pairs_read': False, 'test_truth_read': False,
        'cache_policy': 'Actual native singleton endpoints, one at a time, no cross-length batching'}
    write(root / 'QUALIFICATION.json', qualification, exclusive=True)
    shutil.copyfile(root / 'QUALIFICATION.json', bundle / 'QUALIFICATION.json')
    files = [record(p, bundle) for p in sorted(bundle.rglob('*')) if p.is_file()]
    freeze = {**config, 'at_utc': now(), 'execution_id': 'rapppid_recovery_test_v1', 'scorers': list(SCORERS),
        'model_revision': UPSTREAM_COMMIT, 'sif_sha256': selection['sif_sha256'],
        'tokenizer_sha256': selection['tokenizer_sha256'], 'selection_sha256': sha(root / 'SELECTION.json'),
        'original_results_sha256': selection['original_results_sha256'],
        'original_predictions_manifest_sha256': selection['original_predictions_manifest_sha256'],
        'workers': 1, 'maximum_residues': 1500, 'pair_batch_size': 8192, 'batch_tolerance': 1e-4,
        'score_definition': 'Individual native pre-sigmoid FP32 logits and FP64 mean of all three logits',
        'test_pairs_read': False, 'test_truth_read': False, 'training_performed': False,
        'training_resumed': False, 'completed_epoch8_claimed': False,
        'test_evaluation_authorized': True, 'primary_cell': 'C3_test', 'primary_scorer': SCORERS[0],
        'metric': 'Historical design-weighted P-versus-U concordance; 2000 paired component draws; exact-score half ties',
        'files': files}
    write(bundle / 'SCORER_FREEZE.json', freeze, exclusive=True)
    print({'qualification_passed': True, 'scorer_frozen': True, 'seconds': time.monotonic()-started}, flush=True)


if __name__ == '__main__':
    main()
