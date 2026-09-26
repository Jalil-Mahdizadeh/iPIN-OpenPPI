"""Tables and exportable figures for the two unchanged transfer panels."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from transfer_io import *
from exposure import COMMON

SPECIES = ('mouse', 'fly', 'worm', 'yeast', 'arabidopsis', 'ecoli', 'equal_species')
SPECIES_LABELS = dict(zip(SPECIES, ('Mouse', 'Fly', 'Worm', 'Budding yeast', 'Arabidopsis', 'E. coli K-12', 'Equal-species mean')))


def pick(rows, **criteria):
    selected = [r for r in rows if all(r[k] == v for k, v in criteria.items())]
    require(len(selected) == 1, f'Ambiguous summary: {criteria}: {len(selected)}')
    return selected[0]


def interval(row, signed=False):
    return f"[{row['ci_low']:+.4f}, {row['ci_high']:+.4f}]" if signed else f"[{row['ci_low']:.4f}, {row['ci_high']:.4f}]"


def target_changes(rows, scope_keys):
    groups = {}
    for row in rows:
        key = tuple(row[k] for k in scope_keys)
        groups.setdefault(key, {}).setdefault(row['target_id'], {})[row['model']] = row
    result = []
    for key, targets in sorted(groups.items()):
        for baseline in OLD:
            for metric in ('P_vs_U_concordance', 'average_precision', 'recall_at_10'):
                delta = [v[NEW][metric] - v[baseline][metric] for v in targets.values()
                         if NEW in v and baseline in v and metric in v[NEW] and metric in v[baseline]
                         and v[NEW][metric] != '' and v[baseline][metric] != '']
                values = np.asarray(delta)
                result.append({**dict(zip(scope_keys, key)), 'reference_model': baseline, 'model': NEW,
                    'metric': metric, 'targets': len(values), 'wins': int((values > 0).sum()),
                    'ties': int((values == 0).sum()), 'losses': int((values < 0).sum())})
    return result


def render(nh, pu, nh_exposure, pu_exposure):
    macro, nh_intervals, nh_differences, nh_targets = nh
    pu_intervals, pu_differences, pu_targets = pu
    win_nh = target_changes(nh_targets, ('species', 'subset', 'candidate_set'))
    win_pu = target_changes(pu_targets, ('cohort',))
    write_csv(OUT / STUDIES[0] / 'target_win_tie_loss.csv', win_nh)
    write_csv(OUT / STUDIES[1] / 'target_win_tie_loss.csv', win_pu)
    primary = []
    for sp in SPECIES:
        for model in MODELS:
            row = pick(nh_intervals, species=sp, subset='all', candidate_set='matched', model=model, metric='P_vs_U_concordance')
            primary.append({'study': STUDIES[0], 'group': sp, 'aggregation': 'equal_species' if sp == 'equal_species' else 'equal_target',
                'model': model, 'estimate': row['estimate'], 'ci_low': row['ci_low'], 'ci_high': row['ci_high'], 'targets': row['targets']})
    for aggregation in ('equal_positive', 'equal_yeast_target'):
        for model in MODELS:
            row = pick(pu_intervals, cohort='all', aggregation=aggregation, model=model, metric='P_vs_U_concordance')
            primary.append({'study': STUDIES[1], 'group': 'human_s288c_reference', 'aggregation': aggregation,
                'model': model, 'estimate': row['estimate'], 'ci_low': row['ci_low'], 'ci_high': row['ci_high'], 'targets': row['targets']})
    write_csv(OUT / 'primary_comparison.csv', primary)
    contrasts = [{'study': STUDIES[0], **r} for r in nh_differences if r['subset'] == 'all'
        and r['candidate_set'] == 'matched' and r['metric'] == 'P_vs_U_concordance' and r['model_b'] == NEW]
    contrasts += [{'study': STUDIES[1], **r} for r in pu_differences if r['cohort'] == 'all'
        and r['metric'] == 'P_vs_U_concordance' and r['model_b'] == NEW]
    write_csv(OUT / 'primary_paired_differences.csv', contrasts)

    def nh_value(model, species='equal_species', subset='all', candidate='matched'):
        return pick(macro, species=species, subset=subset, candidate_set=candidate, model=model)

    def pu_value(model, metric='P_vs_U_concordance', cohort='all', aggregation='equal_positive'):
        return pick(pu_intervals, cohort=cohort, aggregation=aggregation, model=model, metric=metric)

    old, new = nh_value('tuna_retrained'), nh_value(NEW)
    old_pu, new_pu = pu_value('tuna_retrained'), pu_value(NEW)
    nh_delta = pick(nh_differences, species='equal_species', subset='all', candidate_set='matched',
                    metric='P_vs_U_concordance', model_a='tuna_retrained', model_b=NEW)
    pu_delta = pick(pu_differences, cohort='all', aggregation='equal_positive', metric='P_vs_U_concordance',
                    model_a='tuna_retrained', model_b=NEW)
    lines = ['# Default iPIN transfer comparison', '', f'Completed {now()}.', '',
        '**iPIN-TUnA-31k was applied to every historical pair in both studies: 218,440 pairs in total.** '
        'The frozen default is the three-seed, epoch-1 ensemble trained with 31,188 P. '
        'All prior models use their archived scores, with exact historical metric and bootstrap reproduction.', '',
        f"Six-species matched-U concordance changed from **{old['P_vs_U_concordance']:.4f} to {new['P_vs_U_concordance']:.4f}** "
        f"against the previous TUnA, a difference of {nh_delta['difference_b_minus_a']:+.4f} "
        f"(paired 95% interval {interval(nh_delta, True)}).", '',
        f"Human–laboratory-yeast equal-P concordance changed from **{old_pu['estimate']:.4f} to {new_pu['estimate']:.4f}**, "
        f"a difference of {pu_delta['difference_b_minus_a']:+.4f} (paired 95% interval {interval(pu_delta, True)}).", '',
        'These are two separate estimands. The six-species result gives equal weight to targets within species and '
        'then to species. The reference-organism result gives equal weight to each published P and its assigned 100 U. '
        'Their raw metric values should not be compared as a controlled species effect.', '',
        '## Six-species primary comparison', '',
        'All 61,385 rows are preserved: 1,385 P and 60,000 U across 300 targets. The table uses the original '
        '100 matched U per target. Background U and combined 200-U results are also supplied.', '',
        '| Organism | Original iPIN | Optimized iPIN | Previous TUnA (17k) | Default 31k | Difference vs 17k [95% interval] |',
        '|---|---:|---:|---:|---:|---|']
    for sp in SPECIES:
        values = [nh_value(m, sp)['P_vs_U_concordance'] for m in MODELS]
        delta = pick(nh_differences, species=sp, subset='all', candidate_set='matched', metric='P_vs_U_concordance', model_a='tuna_retrained', model_b=NEW)
        lines.append('| ' + SPECIES_LABELS[sp] + ' | ' + ' | '.join(f'{v:.4f}' for v in values)
            + f" | {delta['difference_b_minus_a']:+.4f} {interval(delta, True)} |")
    species_wins = sum(nh_value(NEW, sp)['P_vs_U_concordance'] > nh_value('tuna_retrained', sp)['P_vs_U_concordance'] for sp in SPECIES[:-1])
    lines += ['', f'The default has a higher matched-U concordance point estimate in {species_wins}/6 species.', '',
        '| Equal-species matched-U metric | Original iPIN | Optimized iPIN | Previous TUnA | Default 31k |',
        '|---|---:|---:|---:|---:|']
    for key, label in (('average_precision', 'MAP'), ('reciprocal_rank', 'MRR'), ('recall_at_10', 'Recall@10'),
                       ('known_positive_precision_at_10', 'Known-positive precision@10'), ('NDCG_at_10', 'NDCG@10')):
        lines.append('| ' + label + ' | ' + ' | '.join(f'{nh_value(m)[key]:.4f}' for m in MODELS) + ' |')
    lines += ['', '| Candidate set, equal-species concordance | Original iPIN | Optimized iPIN | Previous TUnA | Default 31k |',
        '|---|---:|---:|---:|---:|']
    for candidate in ('background', 'matched', 'all_U'):
        lines.append('| ' + candidate + ' | ' + ' | '.join(f"{nh_value(m, candidate=candidate)['P_vs_U_concordance']:.4f}" for m in MODELS) + ' |')
    lines += ['', '## Human–laboratory-yeast reference panel', '',
        'All 1,555 published P, all 155,500 globally distinct U, and all 545 yeast targets are retained. '
        'Each P has exactly 100 assigned U, with no new filtering in the primary analysis.', '',
        '| Model | Equal-P concordance [95% interval] | Mean AP | Recall@10 | Equal-target concordance |',
        '|---|---:|---:|---:|---:|']
    for model in MODELS:
        v = pu_value(model)
        lines.append(f"| {LABELS[model]} | {v['estimate']:.4f} {interval(v)} | "
            f"{pu_value(model, 'average_precision')['estimate']:.4f} | {pu_value(model, 'recall_at_10')['estimate']:.4f} | "
            f"{pu_value(model, aggregation='equal_yeast_target')['estimate']:.4f} |")
    lines += ['', 'Random-order concordance is 0.5; random recall@10 in these 101-pair panels is 10/101 (0.0990).', '',
        '## Paired differences against each previous model', '',
        '| Study primary summary | Reference | Default minus reference | Paired 95% interval |', '|---|---|---:|---|']
    for name, records, cond in (
        ('Six species, matched U', nh_differences, {'species': 'equal_species', 'subset': 'all', 'candidate_set': 'matched'}),
        ('Human–yeast, equal P', pu_differences, {'cohort': 'all', 'aggregation': 'equal_positive'})):
        for baseline in OLD:
            delta = pick(records, **cond, metric='P_vs_U_concordance', model_a=baseline, model_b=NEW)
            lines.append(f"| {name} | {LABELS[baseline]} | {delta['difference_b_minus_a']:+.4f} | {interval(delta, True)} |")
    lines += ['', '## Exact training/development exposure', '',
        'The complete primary panels above stay unchanged. The original exposure sensitivity is reproduced exactly. '
        'A new common sensitivity excludes the union of historical and expanded-corpus exact TRAIN/development endpoints '
        'from every model. It includes the 31k positives, the U sampling pool, and all six evaluated expanded development '
        'partitions. Membership in the U pool is potential sampling exposure. Different cohorts have different denominators.', '',
        '| Common expanded-exposure sensitivity | Targets | P | U | Previous TUnA | Default 31k | Paired difference [95% interval] |',
        '|---|---:|---:|---:|---:|---:|---|']
    n_old, n_new = nh_value('tuna_retrained', subset=COMMON), nh_value(NEW, subset=COMMON)
    n_delta = pick(nh_differences, species='equal_species', subset=COMMON, candidate_set='matched', metric='P_vs_U_concordance', model_a='tuna_retrained', model_b=NEW)
    lines.append(f"| Six species, matched U | {n_new['targets']} | {n_new['total_P']} | {n_new['total_U']} | "
        f"{n_old['P_vs_U_concordance']:.4f} | {n_new['P_vs_U_concordance']:.4f} | "
        f"{n_delta['difference_b_minus_a']:+.4f} {interval(n_delta, True)} |")
    p_old, p_new = pu_value('tuna_retrained', cohort=COMMON), pu_value(NEW, cohort=COMMON)
    p_delta = pick(pu_differences, cohort=COMMON, aggregation='equal_positive', metric='P_vs_U_concordance', model_a='tuna_retrained', model_b=NEW)
    lines.append(f"| Human–yeast, equal P | {p_new['targets']} | {p_new['P']} | {p_new['U']} | "
        f"{p_old['estimate']:.4f} | {p_new['estimate']:.4f} | {p_delta['difference_b_minus_a']:+.4f} {interval(p_delta, True)} |")
    lines += ['', '| Audit | Study | P rows | U rows |', '|---|---|---:|---:|']
    for study, exposure in zip(STUDIES, (nh_exposure, pu_exposure)):
        for key, count in exposure['row_counts'].items():
            lines.append(f"| {key} | {study} | {count['P']} | {count['U']} |")
    lines += ['', 'Exposure audit files contain every exact pair flag and endpoint count. This is an exact-sequence '
        'sensitivity, not proof of protein-family independence. Historical homology annotations retained in the score '
        'tables refer to the original training corpus; no expanded homology or ESM pretraining audit is claimed.', '',
        '## Validation and limitations', '',
        '- Historical pair metadata, sequence snapshots, labels, candidate strata and three archived score columns are unchanged.',
        '- Historical metrics and original 10,000-draw bootstrap intervals were reproduced to tolerance 2e-12.',
        '- All six new member runs passed native-pair agreement (tolerance 1e-5), exact pair-order symmetry, finite-output checks, and unchanged saved model state.',
        '- Independent sorted-rank, sklearn AP, combinatorial rank/MRR and fractional-recall checks passed. The ensemble mean is exact.',
        '- The expanded model changes both its training corpus and selected epoch relative to the old 17k model; this comparison alone does not attribute changes solely to training-set size.',
        '- The intervals are paired target-bootstrap, exploratory and pointwise. Related targets, repeated partners and publication concentration are not fully represented. The human–yeast panel comes from one source publication.',
        '- U is unreported in the archived source, not a verified negative. Retrieval metrics do not identify biological specificity, binding probabilities or prospective assay precision.',
        '- These existing panels have been examined previously. No threshold, checkpoint, species-specific model or calibration was selected from this run.', '',
        '![Fixed-panel comparison](comparison.png)', '',
        '## Outputs', '',
        '- [Primary comparison](primary_comparison.csv), [paired differences](primary_paired_differences.csv), [PDF figure](comparison.pdf).',
        '- Each study subfolder contains every member/ensemble prediction, combined historical scores, per-target/per-P metrics, coverage, paired intervals, target wins, exposure audit, and scoring qualification.',
        '- [Metric validation](METRIC_VALIDATION.json), [input freeze](INPUT_FREEZE.json), [prediction freeze](PREDICTION_FREEZE.json).',
        '- [Protocol](PROTOCOL.md), [reproduction instructions](README.md), and final `PRESERVATION.json`.', '',
        'The two original `benchmark/` directories and all original model/data/results files were treated as read-only. '
        'All new artifacts are under `experiments/default_ipin_transfer_comparison_v1/`.', '']
    with (OUT / 'REPORT.md').open('x') as stream:
        stream.write('\n'.join(lines))
    colors = ('#7a8190', '#2b72a4', '#dd9d26', '#00876c')
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.3), constrained_layout=True)
    for m_index, (model, color) in enumerate(zip(MODELS, colors)):
        points = [pick(nh_intervals, species=sp, subset='all', candidate_set='matched', model=model, metric='P_vs_U_concordance') for sp in SPECIES]
        y = np.arange(len(SPECIES)) + (m_index-1.5)*.16
        x = np.array([r['estimate'] for r in points])
        error = np.array([[r['estimate']-r['ci_low'] for r in points], [r['ci_high']-r['estimate'] for r in points]])
        axes[0].errorbar(x, y, xerr=error, fmt='o', color=color, markersize=4, capsize=2, label=LABELS[model])
        vals = [pu_value(model, aggregation=a) for a in ('equal_positive', 'equal_yeast_target')]
        axes[1].errorbar([r['estimate'] for r in vals], np.arange(2)+(m_index-1.5)*.14,
            xerr=np.array([[r['estimate']-r['ci_low'] for r in vals], [r['ci_high']-r['estimate'] for r in vals]]),
            fmt='o', color=color, capsize=3, label=LABELS[model])
    axes[0].set(yticks=np.arange(len(SPECIES)), yticklabels=[SPECIES_LABELS[s] for s in SPECIES],
                title='Six species: matched U per target', xlabel='PU concordance (paired target-bootstrap 95% intervals)')
    axes[0].invert_yaxis()
    axes[1].set(yticks=[0, 1], yticklabels=['Equal P (primary)', 'Equal yeast target'],
                title='Human–laboratory-yeast: 100 U per P', xlabel='PU concordance', ylim=(1.5, -.5))
    for ax in axes:
        ax.axvline(.5, color='0.6', linestyle='--', linewidth=.8)
        ax.spines[['top', 'right']].set_visible(False)
    axes[1].legend(loc='lower right', fontsize=9)
    fig.savefig(OUT / 'comparison.png', dpi=180)
    fig.savefig(OUT / 'comparison.pdf')
    plt.close(fig)

