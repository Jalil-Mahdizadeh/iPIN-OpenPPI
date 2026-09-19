"""User-requested C3-DEV evaluation of the failed run's latest saved states.

Never train, repair, select an epoch, or open test pairs/truth. Reuse the frozen
native singleton scorer; keep partial-epoch results separate from scheduled DEV.
"""
import argparse
import csv
import os
from pathlib import Path
import shutil
import sys
import time

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

sys.path.insert(0, '/frozen_code')
from common import SEEDS, arrays, concordance, cuda, now, read, record, sha, verify, write
from model import Tokens, endpoint_cache, fresh, learned_digest, scores

ROOT = Path('/output')
EXPECTED_POSITIONS = {20260803: 1502840, 20260817: 1577920, 20260831: 1556480}


def check_inputs():
    protocol = read('/protocol.json')
    verify('/frozen_code', protocol['code_files'])
    assert sha('/data/DATA_MANIFEST.json') == protocol['data_manifest_sha256']
    verify('/data', read('/data/DATA_MANIFEST.json')['files'])
    assert not protocol['test_evaluation_scheduled']
    return protocol


def copy_exclusive(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Path(source).open('rb') as reader, destination.open('xb') as writer:
        shutil.copyfileobj(reader, writer)
    assert sha(source) == sha(destination)


def snapshot():
    protocol = check_inputs()
    freeze = ROOT / 'EVALUATION_FREEZE.json'
    if freeze.exists():
        raise RuntimeError('This evaluation has already been frozen; do not overwrite it')
    members = []
    for seed in SEEDS:
        source = Path('/training') / f'seed_{seed}' / 'resume.pt'
        target = ROOT / 'checkpoints' / f'seed_{seed}.pt'
        copy_exclusive(source, target)
        state = torch.load(target, map_location='cpu', weights_only=True)
        assert state['seed'] == seed and state['protocol_sha256'] == sha('/protocol.json')
        assert state['epoch'] == 8 and state['next_comparison'] == EXPECTED_POSITIONS[seed]
        assert all(torch.isfinite(value).all() for value in state['model'].values())
        assert all(torch.isfinite(value).all() for item in state['optimizer']['state'].values()
                   for value in item.values() if torch.is_tensor(value))
        updates = 7 * 50000 + state['next_comparison'] // 40
        assert {int(item['step']) for item in state['optimizer']['state'].values()} == {updates}
        members.append({'seed': seed, 'epoch_in_progress': 8, 'completed_epochs': 7,
                        'comparisons_in_current_epoch': state['next_comparison'],
                        'current_epoch_fraction': state['next_comparison'] / 2000000,
                        'total_optimizer_updates': updates, 'source_path': str(source),
                        'source_sha256': sha(source), 'checkpoint': record(target, ROOT)})
    old = read('/previous/DEVELOPMENT_RESULTS.json')
    assert old['protocol_sha256'] == sha('/protocol.json') and old['through_epoch'] == 4
    assert len(old['epochs']) == 1 and old['epochs'][0]['epoch'] == 4
    copy_exclusive('/previous/DEVELOPMENT_RESULTS.json', ROOT / 'epoch4_reference.json')
    files = []
    for source in sorted(Path('/code').iterdir()):
        if source.suffix in ('.py', '.sh'):
            target = ROOT / 'code' / source.name
            copy_exclusive(source, target)
            files.append(record(target, ROOT))
    value = {'at_utc': now(), 'execution_id': 'rapppid_recovery_c3_dev_2578434',
             'authorization': 'User requested C3-development results for the latest checkpoints after the training failure',
             'source_training_job': '2578434', 'training_protocol_sha256': sha('/protocol.json'),
             'sif_sha256': protocol['sif_sha256'], 'data_manifest_sha256': protocol['data_manifest_sha256'],
             'members': members, 'wrapper_files': files, 'epoch4_reference': record(ROOT / 'epoch4_reference.json', ROOT),
             'inference': 'Unchanged frozen native singleton endpoints/head; deterministic TRAIN-fitted tokenizer; first 1500 residues',
             'metric': 'Full C3-development design-weighted P-versus-U concordance with exact-score half ties',
             'ensemble': 'FP64 arithmetic mean of all three saved-state logits; checkpoints have unequal training exposure',
             'ad_hoc_development_look': True, 'completed_epoch8_claimed': False,
             'training_resumed': False, 'numerical_training_repair_applied': False,
             'checkpoint_selection_performed': False, 'test_pairs_read': False, 'test_truth_read': False}
    write(freeze, value, exclusive=True)
    print({'snapshots_frozen': True, 'members': members}, flush=True)


def metric_checked(values, dev):
    point = concordance(values, dev['positive'], dev['weight'])
    # Independent weighted-ranking implementation; P has uniform weight. This
    # equality check does not relabel U as verified biological negatives.
    check = float(roc_auc_score(dev['positive'], values,
                               sample_weight=np.where(dev['positive'], 1., dev['weight'])))
    assert abs(point - check) <= 1e-12, (point, check)
    return point, abs(point - check)


def save_predictions(path, values):
    assert values.shape == (1002265,) and values.dtype == np.float64 and np.isfinite(values).all()
    with path.open('xb') as handle:
        np.save(handle, values, allow_pickle=False)
    return record(path, ROOT)


def evaluate():
    started = time.monotonic()
    check_inputs()
    freeze = read(ROOT / 'EVALUATION_FREEZE.json')
    assert freeze['training_protocol_sha256'] == sha('/protocol.json')
    verify(ROOT, freeze['wrapper_files'] + [freeze['epoch4_reference']])
    for item in freeze['wrapper_files']:
        assert sha(Path('/code') / Path(item['path']).name) == item['sha256']
    verify(ROOT, [member['checkpoint'] for member in freeze['members']])
    # A single-use reservation prevents an accidental duplicate/overwriting run.
    write(ROOT / 'EVALUATION_STARTED.json', {'at_utc': now(), 'freeze_sha256': sha(ROOT / 'EVALUATION_FREEZE.json')}, exclusive=True)
    device = cuda()
    dev = arrays('/data/development_00.npz')
    assert len(dev['a']) == 1002265 and int(dev['positive'].sum()) == 2265
    tokens = Tokens()
    ids = np.unique(np.r_[dev['a'], dev['b']])
    assert len(ids) == 2550 and all(tokens.meta['partition'][int(i)] == 'development' for i in ids)
    old = read(ROOT / 'epoch4_reference.json')['epochs'][0]
    verify('/previous', [old['ensemble_predictions']])
    old_ensemble = np.load(Path('/previous') / old['ensemble_predictions']['path'], allow_pickle=False)
    assert abs(metric_checked(old_ensemble, dev)[0] - old['ensemble_concordance']) <= 1e-12
    rows, predictions = [], []
    for member in freeze['members']:
        tick = time.monotonic()
        seed = member['seed']
        state = torch.load(ROOT / member['checkpoint']['path'], map_location='cpu', weights_only=True)
        model = fresh(seed, device).eval()
        model.load_state_dict(state['model'], strict=True)
        before = learned_digest(model)
        embeddings = endpoint_cache(model, tokens, ids)
        a, b = dev['a'][:32], dev['b'][:32]
        with torch.inference_mode():
            native = np.asarray([float(model.class_head(embeddings[int(i):int(i)+1], embeddings[int(j):int(j)+1]).item())
                                 for i, j in zip(a, b, strict=True)])
        errors = []
        for batch in (1, 8, 8192):
            actual = scores(model, embeddings, a, b, batch=batch)
            errors.append(float(np.max(np.abs(actual - native))))
            errors.append(float(np.max(np.abs(actual - scores(model, embeddings, b, a, batch=batch)))))
        assert max(errors) <= 1e-4
        values = scores(model, embeddings, dev['a'], dev['b'])
        point, metric_error = metric_checked(values, dev)
        assert learned_digest(model) == before
        assert sha(member['source_path']) == member['source_sha256']
        previous_directory = Path('/training') / f'seed_{seed}'
        previous = read(previous_directory / 'epoch_04.json')
        verify(previous_directory, [previous['checkpoint'], previous['development_predictions']])
        previous_values = np.load(previous_directory / previous['development_predictions']['path'], allow_pickle=False)
        previous_point = metric_checked(previous_values, dev)[0]
        assert abs(previous_point - old['member_concordance'][str(seed)]) <= 1e-12
        row = {**member, 'model': f'seed_{seed}', 'C3_development_concordance': point,
               'epoch4_concordance': previous_point, 'difference_from_epoch4': point - previous_point,
               'native_head_and_reversal_max_error': max(errors), 'independent_metric_error': metric_error,
               'learned_state_sha256': before, 'all_rows_finite': True,
               'predictions': save_predictions(ROOT / f'seed_{seed}_C3_development.npy', values),
               'evaluation_seconds': time.monotonic() - tick}
        write(ROOT / f'seed_{seed}.json', row, exclusive=True)
        rows.append(row)
        predictions.append(values)
        print({'seed': seed, 'epoch8_fraction': member['current_epoch_fraction'], 'C3_development': point}, flush=True)
        del state, model, embeddings
        torch.cuda.empty_cache()
    ensemble = np.stack(predictions).mean(0, dtype=np.float64)
    point, metric_error = metric_checked(ensemble, dev)
    ensemble_row = {'model': 'three_seed_mean_logit', 'C3_development_concordance': point,
                    'epoch4_concordance': old['ensemble_concordance'],
                    'difference_from_epoch4': point - old['ensemble_concordance'],
                    'independent_metric_error': metric_error, 'all_rows_finite': True,
                    'predictions': save_predictions(ROOT / 'ensemble_C3_development.npy', ensemble)}
    for member in freeze['members']:
        assert sha(member['source_path']) == member['source_sha256']
    result = {'at_utc': now(), 'passed': True, 'members': rows, 'ensemble': ensemble_row,
              'metric': freeze['metric'], 'positive_pairs': 2265, 'unlabeled_pairs': 1000000,
              'total_pairs': 1002265, 'total_evaluation_seconds': time.monotonic() - started,
              'freeze_sha256': sha(ROOT / 'EVALUATION_FREEZE.json'),
              'training_protocol_sha256': freeze['training_protocol_sha256'],
              'gpu': torch.cuda.get_device_name(), 'evaluation_slurm_allocation': os.environ.get('SLURM_JOB_ID'),
              'caveat': 'User-requested extra development look at unequal mid-epoch-8 recovery states; not a completed epoch-8 comparison',
              'training_resumed': False, 'checkpoint_selection_performed': False,
              'training_checkpoints_unchanged': True, 'test_pairs_read': False, 'test_truth_read': False}
    write(ROOT / 'RESULTS.json', result, exclusive=True)
    with (ROOT / 'scores.csv').open('x', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['model', 'epoch_in_progress', 'fraction_of_epoch_completed', 'optimizer_updates',
                         'C3_development_weighted_P_vs_U_concordance', 'epoch4_concordance', 'difference_from_epoch4',
                         'positive_pairs', 'unlabeled_pairs'])
        for row in rows + [ensemble_row]:
            writer.writerow([row['model'], row.get('epoch_in_progress', 'mixed_mid_epoch_8'),
                             row.get('current_epoch_fraction', ''), row.get('total_optimizer_updates', ''),
                             row['C3_development_concordance'], row['epoch4_concordance'], row['difference_from_epoch4'], 2265, 1000000])
    lines = ['# RAPPPID latest recovery checkpoints: C3 development', '',
             'Full panel: 2,265 observed positives + 1,000,000 unlabeled pairs. Higher weighted P-versus-U concordance is better.', '',
             '| Model | Saved position | C3-dev | Epoch 4 | Change |', '|---|---|---:|---:|---:|']
    for row in rows + [ensemble_row]:
        position = f"7 full epochs + {row['current_epoch_fraction']:.3%} of epoch 8" if 'seed' in row else 'Mean logits of the three unequal-position snapshots'
        lines.append(f"| {row['model']} | {position} | {row['C3_development_concordance']:.6f} | {row['epoch4_concordance']:.6f} | {row['difference_from_epoch4']:+.6f} |")
    lines.extend(['', 'These are the latest valid saved recovery states from failed job 2578434, not completed epoch-8 checkpoints. This is an additional user-requested development look, separate from the scheduled epoch 4/8/12/16/20 comparisons.',
                  '', 'The original frozen singleton scorer, deterministic TRAIN-fitted tokenizer, 1,500-residue prefix policy and full-panel weighted metric were reused. All rows scored finitely; native-head/reversal checks and an independent weighted-ranking metric check passed.',
                  '', 'Training checkpoints, frozen code, previous development reports and test artifacts were not modified. No training, numerical repair, checkpoint selection or test evaluation was performed.',
                  '', f"Evaluation time: {result['total_evaluation_seconds']:.2f} seconds, excluding snapshot creation, image verification and container startup. Allocation: {result['evaluation_slurm_allocation']} on {result['gpu']}.",
                  '', 'Files: `scores.csv`, `RESULTS.json`, per-seed/ensemble NPY predictions, `EVALUATION_FREEZE.json`, copied checkpoint snapshots and wrapper code. NPY rows follow the unchanged `development_00.npz` order.'])
    with (ROOT / 'RESULTS.md').open('x') as handle:
        handle.write('\n'.join(lines) + '\n')
    print({'ensemble_C3_development': point, 'change_from_epoch4': ensemble_row['difference_from_epoch4'],
           'seconds': result['total_evaluation_seconds'], 'training_resumed': False, 'test_evaluated': False}, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('snapshot', 'evaluate'))
    mode = parser.parse_args().mode
    snapshot() if mode == 'snapshot' else evaluate()
