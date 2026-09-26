"""Preserve historical estimands and reproduce old metrics before comparing."""
from collections import defaultdict
from itertools import combinations, product
import math
import sys
sys.path.insert(0, '/code')
import numpy as np
from sklearn.metrics import average_precision_score
from transfer_io import *
from exposure import COHORTS, COMMON, audit, included

METRIC = metrics_module()
PRIMARY = ('P_vs_U_concordance', 'average_precision', 'reciprocal_rank', 'recall_at_10', 'NDCG_at_10')
PU_METRICS = ('P_vs_U_concordance', 'average_precision', 'reciprocal_rank', 'first_positive_rank_expected',
              'recall_at_5', 'recall_at_10', 'recall_at_20', 'NDCG_at_10')
SETS = ('background', 'matched', 'all_U')
ORACLE = {'evaluations': 0, 'maximum_concordance_error': 0., 'maximum_AP_error': 0.,
          'maximum_expected_first_rank_error': 0., 'maximum_MRR_error': 0., 'maximum_recall_error': 0.}


def evaluate(scores, positive, cutoffs):
    scores = np.asarray(scores, np.float64)
    result = METRIC.evaluate(scores, positive, cutoffs)
    # Separate ranking/AP oracles, including tie behavior.
    u = np.sort(scores[~positive])
    ps = scores[positive]
    concordance = np.mean((np.searchsorted(u, ps, side='left') + np.searchsorted(u, ps, side='right')) / (2 * len(u)))
    ap = average_precision_score(positive, scores)
    best = ps.max()
    above, width, hits = int((scores > best).sum()), int((scores == best).sum()), int((ps == best).sum())
    first = above + (width + 1) / (hits + 1)
    reciprocal = sum(math.comb(width-j, hits-1) / math.comb(width, hits) / (above+j) for j in range(1, width-hits+2))
    errors = {'maximum_concordance_error': abs(result['P_vs_U_concordance'] - concordance),
              'maximum_AP_error': abs(result['average_precision'] - ap),
              'maximum_expected_first_rank_error': abs(result['first_positive_rank_expected'] - first),
              'maximum_MRR_error': abs(result['reciprocal_rank'] - reciprocal)}
    recalls = []
    for k in cutoffs:
        credit = [min(1., max(0., (k - int((scores > p).sum())) / int((scores == p).sum()))) for p in ps]
        recalls.append(abs(result[f'recall_at_{k}'] - np.mean(credit)))
    errors['maximum_recall_error'] = max(recalls, default=0.)
    for key, error in errors.items():
        require(error <= 2e-12, f'Independent metric failure: {key}: {error}')
        ORACLE[key] = max(ORACLE[key], float(error))
    ORACLE['evaluations'] += 1
    return result


def check_historical(study, filename, calculated, keys):
    archived = table(ROOT / 'benchmark' / study / filename)
    lookup = {tuple(str(row[k]) for k in keys): row for row in calculated}
    maximum = 0.
    for old in archived:
        key = tuple(old[k] for k in keys)
        require(key in lookup, f'Missing historical row: {filename}: {key}')
        current = lookup[key]
        for field, value in old.items():
            require(field in current, f'Missing historical field: {filename}: {field}')
            if value == '' and current[field] == '':
                continue
            if isinstance(current[field], (int, float, np.integer, np.floating)) and not isinstance(current[field], bool):
                error = abs(float(value) - float(current[field]))
                require(error <= 2e-12, f'Historical mismatch: {filename}, {key}, {field}: {value} vs {current[field]}')
                maximum = max(maximum, error)
            else:
                require(value == str(current[field]), f'Historical metadata mismatch: {filename}, {field}')
    return {'file': filename, 'rows': len(archived), 'maximum_absolute_error': maximum, 'passed': True}


def load(study):
    source, output = ROOT / 'benchmark' / study, OUT / study
    for item in read(output / 'SCORING_RUN.json')['outputs']:
        verify(item)
    panels = table(source / 'panels.csv')
    rows = table(source / 'all_model_scores.csv')
    fresh = table(output / 'default_model_scores.csv')
    old_ipin, old_tuna = table(source / 'ipin_scores.csv'), table(source / 'tuna_scores.csv')
    require(len(panels) == len(rows) == len(fresh) == len(old_ipin) == len(old_tuna), 'Incomplete score tables')
    seeds = read(OUT / 'INPUT_FREEZE.json')['model']['seeds']
    for i, (panel, row, new, old_a, old_b) in enumerate(zip(panels, rows, fresh, old_ipin, old_tuna, strict=True)):
        require(all(row[k] == v for k, v in panel.items()), 'Historical panel metadata changed')
        require(all(int(x['row_index']) == i for x in (row, new, old_a, old_b)), 'Score order mismatch')
        require(all(new[k] == row[k] for k in ('target_id', 'query_sequence_sha256', 'partner_sequence_sha256', 'pair_key')), 'New score identity mismatch')
        for model in OLD:
            key = model + '_score'
            require(row[key] == (old_b if model == 'tuna_retrained' else old_a)[key], 'Archived score mismatch')
            row[key] = float(row[key])
        for key, value in new.items():
            if key.endswith('_score'):
                row[key] = float(value)
        expected = np.mean([row[f'{NEW}_seed{seed}_score'] for seed in seeds], dtype=np.float64)
        require(row[NEW + '_score'] == expected, 'Incorrect three-member mean')
        require(all(np.isfinite(row[m + '_score']) for m in MODELS), 'Nonfinite prediction')
    exposure = audit(study, rows)
    write_csv(output / 'all_model_scores.csv', rows)
    return rows, exposure


def nonhuman(rows):
    study = STUDIES[0]
    output = OUT / study
    config = read(ROOT / 'benchmark' / study / 'config.json')
    species = [s['id'] for s in config['species']]
    groups = defaultdict(list)
    for row in rows:
        groups[row['target_id']].append(row)
    evaluated, ranks, coverage = [], [], []
    for target, panel in groups.items():
        for cohort, candidate in product(COHORTS, SETS):
            selected = [r for r in panel if included(r, cohort) and (r['label'] == 'P' or candidate == 'all_U' or r['stratum'] == candidate)]
            positive = np.array([r['label'] == 'P' for r in selected], bool)
            valid = bool(positive.any() and (~positive).any() and len(selected) >= 20)
            base = {'species': panel[0]['species'], 'target_id': target, 'subset': cohort, 'candidate_set': candidate}
            coverage.append({**base, 'P': int(positive.sum()), 'U': int((~positive).sum()), 'evaluable': valid})
            if not valid:
                continue
            for model in MODELS:
                scores = np.array([r[model + '_score'] for r in selected])
                evaluated.append({**base, 'model': model, 'target_similarity_bin': panel[0]['target_similarity_bin'],
                    **evaluate(scores, positive, (5, 10, 20))})
                if cohort == 'all':
                    for i in np.flatnonzero(positive):
                        ranks.append({'species': panel[0]['species'], 'target_id': target,
                            'partner_uniprot': selected[i]['partner_uniprot'], 'model': model, 'candidate_set': candidate,
                            **METRIC.positive_ranks(scores[i], scores, (5, 10, 20))})
    metric_keys = list(METRIC.evaluate(np.array([1., 0.]), np.array([True, False]), ()))
    metric_keys += [f'{stem}_at_{k}' for k in (5, 10, 20) for stem in
        ('recovered_P', 'recall', 'known_positive_precision', 'EF', 'NDCG', 'target_success')]
    grouped = defaultdict(list)
    for row in evaluated:
        grouped[row['species'], row['subset'], row['candidate_set'], row['model']].append(row)
    macro = []
    for (sp, cohort, candidate, model), group in sorted(grouped.items()):
        macro.append({'species': sp, 'subset': cohort, 'candidate_set': candidate, 'model': model,
            'targets': len(group), **{key: float(np.mean([r[key] for r in group])) for key in metric_keys},
            'total_P': sum(r['P'] for r in group), 'total_U': sum(r['U'] for r in group)})
    species_macro = list(macro)
    for cohort, candidate, model in product(COHORTS, SETS, MODELS):
        group = [r for r in species_macro if (r['subset'], r['candidate_set'], r['model']) == (cohort, candidate, model)]
        if group:
            macro.append({'species': 'equal_species', 'subset': cohort, 'candidate_set': candidate, 'model': model,
                'targets': sum(r['targets'] for r in group), **{key: float(np.mean([r[key] for r in group])) for key in metric_keys},
                'total_P': sum(r['total_P'] for r in group), 'total_U': sum(r['total_U'] for r in group)})
    intervals, contrasts, draw_store = [], [], {}
    rng = np.random.default_rng(config['seed'])
    # Exactly preserve the two original cohorts' RNG call order.
    plans = [(sp, cohort, candidate) for sp in species for cohort in COHORTS[:2] for candidate in SETS]
    plans += [(sp, COMMON, candidate) for sp in species for candidate in SETS]
    for sp, cohort, candidate in plans:
        available = {m: {r['target_id']: r for r in grouped.get((sp, cohort, candidate, m), [])} for m in MODELS}
        targets = sorted(set.intersection(*(set(v) for v in available.values())))
        if not targets:
            continue
        sample = rng.integers(0, len(targets), size=(config['bootstrap_draws'], len(targets)))
        for key in PRIMARY:
            points, draws = {}, {}
            for model in MODELS:
                values = np.array([available[model][t][key] for t in targets])
                points[model] = float(values.mean())
                draws[model] = values[sample].mean(axis=1)
                draw_store[sp, cohort, candidate, key, model] = draws[model]
                low, high = np.quantile(draws[model], [.025, .975])
                intervals.append({'species': sp, 'subset': cohort, 'candidate_set': candidate, 'metric': key,
                    'model': model, 'targets': len(targets), 'estimate': points[model], 'ci_low': float(low), 'ci_high': float(high)})
            for left, right in combinations(MODELS, 2):
                low, high = np.quantile(draws[right] - draws[left], [.025, .975])
                contrasts.append({'species': sp, 'subset': cohort, 'candidate_set': candidate, 'metric': key,
                    'model_a': left, 'model_b': right, 'targets': len(targets),
                    'difference_b_minus_a': points[right]-points[left], 'ci_low': float(low), 'ci_high': float(high)})
    for cohort, candidate, key in product(COHORTS, SETS, PRIMARY):
        names = [sp for sp in species if (sp, cohort, candidate, key, OLD[0]) in draw_store]
        if not names:
            continue
        draws = {m: np.mean([draw_store[sp, cohort, candidate, key, m] for sp in names], axis=0) for m in MODELS}
        values = {r['model']: r for r in macro if (r['species'], r['subset'], r['candidate_set']) == ('equal_species', cohort, candidate)}
        for model in MODELS:
            low, high = np.quantile(draws[model], [.025, .975])
            intervals.append({'species': 'equal_species', 'subset': cohort, 'candidate_set': candidate, 'metric': key,
                'model': model, 'targets': values[model]['targets'], 'estimate': values[model][key], 'ci_low': float(low), 'ci_high': float(high)})
        for left, right in combinations(MODELS, 2):
            low, high = np.quantile(draws[right]-draws[left], [.025, .975])
            contrasts.append({'species': 'equal_species', 'subset': cohort, 'candidate_set': candidate, 'metric': key,
                'model_a': left, 'model_b': right, 'targets': values[left]['targets'],
                'difference_b_minus_a': values[right][key]-values[left][key], 'ci_low': float(low), 'ci_high': float(high)})
    outputs = {'per_target_metrics.csv': (evaluated, ('species', 'target_id', 'subset', 'candidate_set', 'model')),
        'macro_metrics.csv': (macro, ('species', 'subset', 'candidate_set', 'model')),
        'positive_ranks.csv': (ranks, ('species', 'target_id', 'partner_uniprot', 'model', 'candidate_set')),
        'analysis_coverage.csv': (coverage, ('species', 'target_id', 'subset', 'candidate_set')),
        'metric_intervals.csv': (intervals, ('species', 'subset', 'candidate_set', 'metric', 'model')),
        'paired_differences.csv': (contrasts, ('species', 'subset', 'candidate_set', 'metric', 'model_a', 'model_b'))}
    checks = []
    for filename, (data, keys) in outputs.items():
        checks.append(check_historical(study, filename, data, keys))
        write_csv(output / filename, data)
    write_json(output / 'HISTORICAL_REPLAY.json', checks)
    print('Nonhuman metrics and original bootstrap intervals reproduced', flush=True)
    return macro, intervals, contrasts, evaluated


def reference(rows):
    study = STUDIES[1]
    output = OUT / study
    config = read(ROOT / 'benchmark' / study / 'config.json')
    groups = defaultdict(list)
    for row in rows:
        groups[row['panel_id']].append(row)
    require(len(groups) == 1555 and all(len(rr) == 101 and sum(r['label'] == 'P' for r in rr) == 1 for rr in groups.values()), 'PU panels changed')
    require(len({r['pair_key'] for r in rows}) == len(rows), 'PU pairs repeated')
    evaluated, coverage, ranks = [], [], []
    for panel_id, full in groups.items():
        for cohort in COHORTS:
            selected = [r for r in full if included(r, cohort)]
            positive = np.array([r['label'] == 'P' for r in selected], bool)
            valid = bool(positive.any() and (~positive).any())
            base = {'cohort': cohort, 'panel_id': panel_id, 'target_id': full[0]['target_id']}
            coverage.append({**base, 'P': int(positive.sum()), 'U': int((~positive).sum()), 'evaluable': valid})
            if not valid:
                continue
            cutoffs = tuple(k for k in (5, 10, 20) if k <= len(selected))
            for model in MODELS:
                scores = np.array([r[model + '_score'] for r in selected])
                evaluated.append({**base, 'model': model, **evaluate(scores, positive, cutoffs)})
                if cohort == 'all':
                    ranks.append({**base, 'model': model, **METRIC.positive_ranks(scores[positive][0], scores, cutoffs)})
    by_target = defaultdict(list)
    for row in evaluated:
        by_target[row['cohort'], row['model'], row['target_id']].append(row)
    target_rows = []
    for (cohort, model, target), group in sorted(by_target.items()):
        target_rows.append({'cohort': cohort, 'model': model, 'target_id': target, 'panels': len(group),
            'P': sum(r['P'] for r in group), 'U': sum(r['U'] for r in group),
            **{key: float(np.mean([r[key] for r in group if key in r])) if any(key in r for r in group) else '' for key in PU_METRICS}})
    intervals, contrasts = [], []
    for cohort, key in product(COHORTS, PU_METRICS):
        selected = {m: [r for r in evaluated if r['cohort'] == cohort and r['model'] == m and key in r] for m in MODELS}
        require(all(selected.values()), 'No evaluable PU panels')
        targets = sorted({r['target_id'] for r in selected[OLD[0]]})
        count = np.array([sum(r['target_id'] == t for r in selected[OLD[0]]) for t in targets], np.float64)
        sample = np.random.default_rng(config['seed']).integers(0, len(targets), size=(config['bootstrap_draws'], len(targets)))
        sampled_counts = count[sample].sum(axis=1)
        for aggregation in ('equal_positive', 'equal_yeast_target'):
            points, draws = {}, {}
            for model in MODELS:
                sums = np.array([sum(r[key] for r in selected[model] if r['target_id'] == t) for t in targets])
                if aggregation == 'equal_positive':
                    points[model] = float(sums.sum() / count.sum())
                    draws[model] = sums[sample].sum(axis=1) / sampled_counts
                else:
                    points[model] = float((sums/count).mean())
                    draws[model] = (sums/count)[sample].mean(axis=1)
                low, high = np.quantile(draws[model], [.025, .975])
                intervals.append({'cohort': cohort, 'aggregation': aggregation, 'model': model, 'metric': key,
                    'estimate': points[model], 'ci_low': float(low), 'ci_high': float(high), 'targets': len(targets),
                    'panels': int(count.sum()), 'P': sum(r['P'] for r in selected[model]), 'U': sum(r['U'] for r in selected[model])})
            for left, right in combinations(MODELS, 2):
                low, high = np.quantile(draws[right]-draws[left], [.025, .975])
                contrasts.append({'cohort': cohort, 'aggregation': aggregation, 'metric': key, 'model_a': left,
                    'model_b': right, 'difference_b_minus_a': points[right]-points[left],
                    'ci_low': float(low), 'ci_high': float(high), 'targets': len(targets), 'panels': int(count.sum())})
    outputs = {'per_positive_metrics.csv': (evaluated, ('cohort', 'panel_id', 'target_id', 'model')),
        'analysis_coverage.csv': (coverage, ('cohort', 'panel_id', 'target_id')),
        'per_target_metrics.csv': (target_rows, ('cohort', 'model', 'target_id')),
        'metrics.csv': (intervals, ('cohort', 'aggregation', 'model', 'metric')),
        'paired_differences.csv': (contrasts, ('cohort', 'aggregation', 'metric', 'model_a', 'model_b'))}
    checks = []
    for filename, (data, keys) in outputs.items():
        checks.append(check_historical(study, filename, data, keys))
        write_csv(output / filename, data)
    write_csv(output / 'positive_ranks.csv', ranks)
    write_json(output / 'HISTORICAL_REPLAY.json', checks)
    print('Reference PU metrics and original bootstrap intervals reproduced', flush=True)
    return intervals, contrasts, target_rows


def main():
    verify_small_inputs(read(OUT / 'INPUT_FREEZE.json'))
    require(read(OUT / 'PREDICTION_FREEZE.json')['complete'], 'Freeze all predictions before comparison')
    for item in read(OUT / 'PREDICTION_FREEZE.json')['runs']:
        verify(item)
    # Exercise adversarial ties before evaluating real scores.
    for scores in ([1., 1., 1., 1.], [0., 1., 1., 0.], [2., 0., 1., 2.]):
        evaluate(np.array(scores), np.array([True, False, True, False]), (1, 2, 3))
    rows, nonhuman_exposure = load(STUDIES[0])
    nh = nonhuman(rows)
    del rows
    rows, reference_exposure = load(STUDIES[1])
    pu = reference(rows)
    del rows
    write_json(OUT / 'METRIC_VALIDATION.json', {'at_utc': now(), 'passed': True, **ORACLE,
        'independent_oracles': 'Sorted-U search, sklearn threshold AP, combinatorial first-P rank/MRR, fractional per-P recall',
        'pair_metadata_identical': True, 'archived_scores_identical': True, 'three_seed_mean_exact': True,
        'historical_metric_and_bootstrap_replay_passed': True})
    from report import render
    render(nh, pu, nonhuman_exposure, reference_exposure)
    write_json(OUT / 'ANALYSIS_COMPLETE.json', {'at_utc': now(), 'status': 'complete',
        'prediction_freeze': record(OUT / 'PREDICTION_FREEZE.json'), 'validation': record(OUT / 'METRIC_VALIDATION.json'),
        'outputs': [record(p) for p in sorted(OUT.rglob('*')) if p.is_file()
            and not any(part in ('.cache', 'tmp') for part in p.relative_to(OUT).parts) and p.suffix in ('.csv', '.json', '.md', '.pdf', '.png')
            and p.name not in ('INPUT_FREEZE.json', 'ANALYSIS_COMPLETE.json')]})
    print('Both transfer comparisons complete', flush=True)


if __name__ == '__main__':
    main()

