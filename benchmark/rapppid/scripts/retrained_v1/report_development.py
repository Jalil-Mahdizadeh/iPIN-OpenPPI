"""Report all three seeds and their mean-logit C3-DEV score; select nothing."""
import argparse
import csv
from pathlib import Path
import numpy as np
from common import SEEDS, EVALUATION_EPOCHS, arrays, atomic_json, concordance, now, read, record, sha, verify, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--through-epoch', type=int, choices=EVALUATION_EPOCHS, required=True)
    args = parser.parse_args()
    root = Path('/output')
    protocol = read('/protocol.json')
    verify('/code', protocol['code_files'])
    assert sha('/data/DATA_MANIFEST.json') == protocol['data_manifest_sha256']
    verify('/data', read('/data/DATA_MANIFEST.json')['files'])
    dev = arrays('/data/development_00.npz')
    results = []
    for epoch in EVALUATION_EPOCHS:
        if epoch > args.through_epoch:
            continue
        means, members, references = [], {}, []
        for seed in SEEDS:
            directory = Path('/training') / f'seed_{seed}'
            info = read(directory / f'epoch_{epoch:02d}.json')
            assert info['protocol_sha256'] == sha('/protocol.json') and info['epoch'] == epoch and info['seed'] == seed
            assert info['rows'] == 1002265 and not info['test_pairs_read'] and not info['test_truth_read']
            verify(directory, [info['checkpoint'], info['development_predictions']])
            values = np.load(directory / info['development_predictions']['path'], allow_pickle=False)
            assert values.shape == (1002265,) and values.dtype == np.float64 and np.isfinite(values).all()
            value = concordance(values, dev['positive'], dev['weight'])
            assert value == info['C3_development_concordance']
            members[str(seed)] = value
            means.append(values)
            references.append({'seed': seed, 'report_sha256': sha(directory / f'epoch_{epoch:02d}.json'),
                               'checkpoint_sha256': info['checkpoint']['sha256'],
                               'prediction_sha256': info['development_predictions']['sha256']})
        ensemble = np.stack(means).mean(0, dtype=np.float64)
        point = concordance(ensemble, dev['positive'], dev['weight'])
        path = root / f'epoch_{epoch:02d}_ensemble_C3_development.npy'
        if path.exists():
            assert np.array_equal(np.load(path, allow_pickle=False), ensemble)
        else:
            with path.open('xb') as handle:
                np.save(handle, ensemble, allow_pickle=False)
        item = {'epoch': epoch, 'member_concordance': members, 'ensemble_concordance': point,
                'members': references, 'ensemble_predictions': record(path, root), 'rows': len(ensemble)}
        info_path = root / f'epoch_{epoch:02d}.json'
        if info_path.exists():
            assert read(info_path) == item
        else:
            write(info_path, item, exclusive=True)
        results.append(item)
    value = {'at_utc': now(), 'through_epoch': args.through_epoch, 'epochs': results,
             'metric': 'Full C3-DEV design-weighted P-versus-U concordance with exact-score half ties',
             'ensemble': 'Arithmetic mean of all three native logits in FP64',
             'protocol_sha256': sha('/protocol.json'), 'test_pairs_read': False, 'test_truth_read': False,
             'checkpoint_selected': False, 'test_evaluation_scheduled': False,
             'next_decision': 'User chooses a retained epoch after reviewing development results'}
    atomic_json(root / 'DEVELOPMENT_RESULTS.json', value)
    temporary = root / 'development_scores.next.csv'
    with temporary.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['epoch', 'model', 'C3_development_weighted_P_vs_U_concordance', 'positive_pairs', 'unlabeled_pairs'])
        for item in results:
            for seed in SEEDS:
                writer.writerow([item['epoch'], f'seed_{seed}', item['member_concordance'][str(seed)], 2265, 1000000])
            writer.writerow([item['epoch'], 'three_seed_mean_logit', item['ensemble_concordance'], 2265, 1000000])
    temporary.replace(root / 'development_scores.csv')
    lines = ['# RAPPPID retraining: C3-development checkpoints', '',
             'All rows retained: 2,265 observed positives and 1,000,000 unlabeled pairs. No test evaluation or automatic epoch selection.', '',
             '| Epoch | Seed 20260803 | Seed 20260817 | Seed 20260831 | Mean-logit ensemble |',
             '|---|---:|---:|---:|---:|']
    for item in results:
        values = [item['member_concordance'][str(s)] for s in SEEDS] + [item['ensemble_concordance']]
        lines.append(f"| {item['epoch']} | " + ' | '.join(f'{v:.6f}' for v in values) + ' |')
    lines.extend(['', 'Scores are ranking metrics, not calibrated interaction probabilities. Training uses native padded batches; development uses the declared native singleton inference policy.',
                  '', 'Every listed epoch and all three seed checkpoints remain available. The user will decide which epoch proceeds to a separately authorized test evaluation.'])
    temporary = root / 'DEVELOPMENT_RESULTS.next.md'
    temporary.write_text('\n'.join(lines) + '\n')
    temporary.replace(root / 'DEVELOPMENT_RESULTS.md')
    print({'through_epoch': args.through_epoch, 'ensemble_C3_development': results[-1]['ensemble_concordance'],
           'checkpoint_selected': False, 'test_evaluation_scheduled': False}, flush=True)


if __name__ == '__main__':
    main()
