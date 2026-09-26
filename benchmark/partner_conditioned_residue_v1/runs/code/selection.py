"""Select on C3 development, then freeze complete sequence-only scorers."""
from pathlib import Path
import shutil
import time
import numpy as np
import torch
from common import arrays, concordance, cuda, now, read, record, sha, write
from data import ResidueCache, score_cached
from frozen_scorer import Scorer
from model import PairModel
from train import verify_freeze


def choose_promotions(best, config):
    promising = [x for x in best if x['recipe']['local_branch'] and
                 x['C3_development_concordance'] > config['promotion_reference_C3_development']]
    promising.sort(key=lambda x: (-x['C3_development_concordance'], x['recipe']['name']))
    promising = promising[:config['maximum_promoted_advanced_models']]
    selected = promising + [x for x in best if x['recipe']['name'] == 'mean_pool'] if promising else []
    return promising, selected


def checked_member(root, recipe, seed, epoch, protocol_hash):
    folder = root / 'training' / recipe['name'] / f'seed_{seed}'
    complete = read(folder / 'COMPLETE.json')
    if complete['protocol_sha256'] != protocol_hash:
        raise RuntimeError('Incomplete/changed training protocol')
    info = read(folder / f'epoch_{epoch:02d}.json')
    if info['protocol_sha256'] != protocol_hash or info['seed'] != seed or info['recipe'] != recipe['name']:
        raise RuntimeError('Member identity changed')
    for key in ('checkpoint', 'development_predictions'):
        path = folder / Path(info[key]['path']).name
        if sha(path) != info[key]['sha256']:
            raise RuntimeError('Selected member artifact changed')
    return info, folder


def main():
    verify_freeze()
    root = Path('/output')
    config = read('/config.json')
    protocol_hash = sha(root / 'TRAINING_FREEZE.json')
    dev = arrays(root / 'data/development_00.npz')
    candidates, best = [], []
    for recipe in config['recipes']:
        recipe_results = []
        for epoch in config['evaluation_epochs']:
            predictions, members = [], []
            for seed in config['seeds']:
                info, folder = checked_member(root, recipe, seed, epoch, protocol_hash)
                predictions.append(np.load(folder / Path(info['development_predictions']['path']).name, allow_pickle=False))
                members.append(info)
            values = np.stack(predictions, axis=1).mean(axis=1, dtype=np.float64)
            metric = concordance(values, dev['positive'], dev['weight'])
            result = {'recipe': recipe, 'epoch': epoch, 'C3_development_concordance': metric,
                      'members': members, 'all_three_seeds_retained': True}
            recipe_results.append(result)
            candidates.append(result)
        best.append(sorted(recipe_results, key=lambda x: (-x['C3_development_concordance'], x['epoch']))[0])
    promising, selected = choose_promotions(best, config)
    selection = {'at_utc': now(), 'study_id': config['study_id'], 'training_freeze_sha256': protocol_hash,
                 'all_candidates': candidates, 'best_per_recipe': best, 'selected': selected,
                 'promotion_reference_C3_development': config['promotion_reference_C3_development'],
                 'primary_candidate': promising[0]['recipe']['name'] + '_ensemble' if promising else None,
                 'test_pairs_read': False, 'test_truth_read': False}
    write(root / 'SELECTION.json', selection, exclusive=True)
    lines = ['# Development comparison', '', 'All values are full C3-development weighted P-versus-U concordance.', '',
             '| Recipe | Selected epoch | Three-seed ensemble | Promoted |', '|---|---:|---:|---|']
    selected_names = {x['recipe']['name'] for x in selected}
    for x in best:
        lines.append(f"| {x['recipe']['name']} | {x['epoch']} | {x['C3_development_concordance']:.6f} | {x['recipe']['name'] in selected_names} |")
    lines += ['', f"Promotion reference: frozen PU-TUnA C3 development = {config['promotion_reference_C3_development']:.12f}.",
              '', 'All three seeds were retained. Selection used development only. Development gains are post-selection and exploratory.']
    (root / 'DEVELOPMENT.md').write_text('\n'.join(lines) + '\n')
    if not selected:
        write(root / 'NO_PROMOTION.json', {'at_utc': now(), 'reason': 'No advanced ensemble exceeded frozen PU-TUnA on C3 development.',
              'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
        print({'selected': [], 'test_disposition': 'skip_no_promising_candidate'}, flush=True)
        return
    device = cuda()
    cache = ResidueCache(device=device)
    bundle = root / 'scorer_bundle'
    bundle.mkdir(exist_ok=False)
    for folder in ('code', 'weights', 'features', 'provenance'):
        (bundle / folder).mkdir()
    for name in ('common.py', 'model.py', 'data.py', 'frozen_scorer.py', 'comparison.py', 'benchmark_metrics.py', 'gpu_guard.py'):
        shutil.copyfile(Path('/code') / name, bundle / 'code' / name)
    for name in ('TRAINING_FREEZE.json', 'SELECTION.json', 'QUALIFICATION.json', 'REAL_QUALIFICATION.json', 'PIPELINE_QUALIFICATION.json'):
        shutil.copyfile(root / name, bundle / 'provenance' / name)
    for name in ('global_standardized.npy', 'normalizer.npz'):
        shutil.copyfile(root / 'data' / name, bundle / name)
    write(bundle / 'endpoints.json', cache.meta['sha256'], exclusive=True)
    write(bundle / 'components.json', cache.meta['component'], exclusive=True)
    specification = {'study_id': config['study_id'], 'at_utc': now(), 'members': [], 'ensembles': [], 'scorers': [],
                     'primary_candidate': selection['primary_candidate'], 'test_pairs_read': False, 'test_truth_read': False,
                     'training_freeze_sha256': protocol_hash, 'selection_sha256': sha(root / 'SELECTION.json')}
    train = arrays(root / 'data/training.npz')
    a, b = train['p_a'][:97], train['p_b'][:97]
    reference = {}
    for candidate in selected:
        recipe, epoch = candidate['recipe'], candidate['epoch']
        ensemble = recipe['name'] + '_ensemble'
        specification['ensembles'].append(ensemble)
        specification['scorers'].append(ensemble)
        for seed in config['seeds']:
            info, folder = checked_member(root, recipe, seed, epoch, protocol_hash)
            name = recipe['name'] + f'_seed{seed}'
            checkpoint = bundle / 'weights' / f'{name}.pt'
            shutil.copyfile(folder / Path(info['checkpoint']['path']).name, checkpoint)
            model = PairModel(recipe).to(device)
            model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True), strict=True)
            model.eval()
            tokens = cache.endpoint_tokens(model, list(range(17000)))
            feature_path = bundle / 'features' / f'{name}.npy'
            np.save(feature_path, tokens.cpu().numpy(), allow_pickle=False)
            reference[name] = score_cached(model, cache.global_features, tokens, a, b)
            specification['scorers'].append(name)
            specification['members'].append({'name': name, 'ensemble': ensemble, 'recipe': recipe, 'seed': seed,
                                             'epoch': epoch, 'checkpoint': str(checkpoint.relative_to(bundle)),
                                             'features': str(feature_path.relative_to(bundle))})
            print({'frozen_member': name, 'epoch': epoch, 'all_endpoints': 17000}, flush=True)
            del model, tokens
            torch.cuda.empty_cache()
    del cache
    torch.cuda.empty_cache()
    scorer = Scorer(bundle, device, specification)
    values = scorer.scores(a, b)
    errors = {name: float(np.max(np.abs(values[:, specification['scorers'].index(name)] - expected)))
              for name, expected in reference.items()}
    swap_error = float(np.max(np.abs(values - scorer.scores(b, a))))
    if max(errors.values()) > 2e-5 or swap_error > 2e-5:
        raise RuntimeError('Frozen scorer reload/symmetry qualification failed')
    qa, qb = np.resize(a, 4096), np.resize(b, 4096)
    scorer.scores(qa, qb)
    torch.cuda.synchronize(); start = time.monotonic()
    scorer.scores(qa, qb)
    torch.cuda.synchronize(); seconds = time.monotonic() - start
    write(bundle / 'FROZEN_SCORER_QUALIFICATION.json', {'at_utc': now(), 'passed': True,
          'reload_errors': errors, 'swap_error': swap_error, 'tolerance': 2e-5,
          'head_only_seconds_per_4096_pairs_all_selected_models': seconds,
          'fixtures': '97 fixed TRAIN positives, repeated for throughput; encoding excluded'}, exclusive=True)
    files = []
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            item = record(path); item['path'] = str(path.relative_to(bundle)); files.append(item)
    specification['files'] = files
    write(bundle / 'SCORER_FREEZE.json', specification, exclusive=True)
    print({'selected_ensembles': specification['ensembles'], 'primary_candidate': specification['primary_candidate'],
           'scorer_freeze_sha256': sha(bundle / 'SCORER_FREEZE.json')}, flush=True)


if __name__ == '__main__':
    main()
