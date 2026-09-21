"""Report the completed P-versus-unlabeled evaluation and exact requested counts."""
import numpy as np
from study_utils import *


def main():
    require_container()
    require(not (OUT/'FINAL_MANIFEST.json').exists(),'Already finalized')
    validation=read(OUT/'RESULT_VALIDATION.json')
    require(validation['status']=='passed','Independent result validation required')
    verify(validation['analysis'])
    check_records(read(OUT/'INPUT_FREEZE.json')['files'])
    analysis=read(OUT/'ANALYSIS.json')
    check_records(analysis['outputs']+analysis['model_outputs'])
    selection=read(OUT/'PANEL_SELECTION.json')
    metrics=table(OUT/'metrics.csv')
    def row(model,key='P_vs_U_concordance',cohort='all',aggregation='equal_positive'):
        return next(r for r in metrics if (r['cohort'],r['aggregation'],r['model'],r['metric'])==(cohort,aggregation,model,key))
    def estimate(r):
        return f"{float(r['estimate']):.6f} [{float(r['ci_low']):.6f}, {float(r['ci_high']):.6f}]"
    lines=['# All 1,555 P versus 155,500 globally distinct U','',
        '**Completed P-versus-unlabeled evaluation.** Every original published P is retained, with exactly 100 assigned U per P.','',
        '## Dataset','',
        '| Quantity | Count |','|---|---:|',
        '| Published P pairs | 1,555 |','| Globally distinct U pairs | 155,500 |',
        '| Total scored pairs | 157,055 |','| Panels (one P plus 100 U) | 1,555 |',
        '| S288C proteins | 545 |',f"| Human proteins used | {selection['selected_human_sequences']:,} |",
        f"| Eligible archived human sequence pool | {selection['eligible_human_sequences']:,} |",
        '| Repeated U pairs | 0 |','| P/U overlap | 0 |',
        '| Reported source pairs retained in U | 0 |','',
        'All 39 published positives that failed secondary-assay confirmation remain P. U contains pairs unreported in the declared source snapshot; it may include real interactions and is not a verified-negative label.','',
        f"Matching tiers: {selection['matched_tier_counts'].get('0',0):,} U meet both source-degree-bin and length criteria; {selection['matched_tier_counts'].get('1',0):,} use length only. Degree-only and unmatched tiers have {selection['matched_tier_counts'].get('2',0):,} and {selection['matched_tier_counts'].get('3',0):,} entries. All fallbacks are retained and disclosed.",'',
        '## Primary result: equal weight for every P','',
        'Concordance is the fraction of each P\'s 100 U scores below its P score, with half credit for ties, averaged over all 1,555 P. Chance is 0.5. The brackets are exploratory 95% target-bootstrap intervals.','',
        '| Model | P-vs-U concordance [95% interval] | Mean AP | Mean recall@10 |',
        '|---|---:|---:|---:|']
    for m in MODELS:
        lines.append(f"| {NAMES[m]} | {estimate(row(m))} | {float(row(m,'average_precision')['estimate']):.6f} | {float(row(m,'recall_at_10')['estimate']):.6f} |")
    lines += ['', 'Recall@10 measures recovery of the one known P in each 101-pair panel. Its random-order reference is 10/101 = 0.099010; random expected P rank is 51. These are retrieval of reported positives, not biological accuracy or precision.','',
        '## Equal-target summary','',
        'Average per-P results within each yeast target, then give all 545 targets equal weight. This reports the target weighting used in the earlier nonhuman study; the panels and U ratio still differ.','',
        '| Model | Equal-target P-vs-U concordance [95% interval] |','|---|---:|']
    for m in MODELS:
        lines.append(f"| {NAMES[m]} | {estimate(row(m,aggregation='equal_yeast_target'))} |")
    lines += ['', '![P-versus-U concordance](pu_concordance.png)','',
        '## Training/development exposure sensitivity','',
        'The primary result above retains all 1,555 P. This separate sensitivity removes pairs containing either exact TRAIN/development endpoint. It can change both the P count and the U count per panel.','',
        '| Model | Retained P panels | Retained U | Concordance [95% interval] |','|---|---:|---:|---:|']
    for m in MODELS:
        r=row(m,cohort='no_exact_TRAIN_DEV_endpoint')
        lines.append(f"| {NAMES[m]} | {int(r['P']):,} | {int(r['U']):,} | {estimate(r)} |")
    exposure=read(OUT/'EXPOSURE_SUMMARY.json')
    lines += ['', '| Organism | Proteins | Exact TRAIN | Exact development | Either |','|---|---:|---:|---:|---:|']
    for r in exposure['organisms']:
        lines.append(f"| {'S288C' if r['taxid']==559292 else 'Human'} | {r['proteins']:,} | {r['exact_TRAIN']:,} | {r['exact_development']:,} | {r['either_exact_TRAIN_or_development']:,} |")
    lines += ['',f"Exact pair exposure counts: {exposure['exact_pair_counts']}. Protected human test pairs/truth were not opened. ESM pretraining exposure was not audited.",'',
        '## Paired model comparisons','',
        '| Model B minus model A | Concordance difference [95% interval] |','|---|---:|']
    differences=[r for r in table(OUT/'paired_differences.csv') if r['cohort']=='all' and r['aggregation']=='equal_positive' and r['metric']=='P_vs_U_concordance']
    for r in differences:
        lines.append(f"| {NAMES[r['model_b']]} minus {NAMES[r['model_a']]} | {float(r['difference_b_minus_a']):.6f} [{float(r['ci_low']):.6f}, {float(r['ci_high']):.6f}] |")
    lines += ['', '## Interpretation and limits','',
        '- This is the requested P-versus-unlabeled comparison. The earlier 36-versus-39 secondary-assay analysis is a different historical endpoint and is not used as P/U truth here.',
        '- All P come from one published human–yeast study. The comparison tests ranking against this archived U sampling design; it does not establish replication across studies or human-pathogen performance.',
        '- Human proteins/isoforms come from an archived evidence universe, with reference-sequence projection and length limits. U can contain unreported true interactions. Matching does not equalize all study or biological biases.',
        '- The 10,000 paired bootstrap draws resample whole yeast targets. Shared human partners, homologous targets and the one source publication leave residual dependence; intervals are exploratory.',
        '- This follow-up was designed after the previous positive scores were inspected. U selection used no model scores. Every model, normalizer and preprocessing definition was frozen; no retraining, calibration or outcome-based model selection occurred.',
        '- Source-degree control and every per-P and per-target result are supplied so the aggregate does not hide weighting or metadata effects.','',
        '## Validation and files','',
        f"Independent validation passed: {validation['validated_per_positive_model_rows']:,} per-positive/model rows, {validation['validated_bootstrap_series']} bootstrap series with 10,000 draws each, maximum metric difference {validation['maximum_metric_error']:.3g}.",
        'All original P, exactly 100 U per P, global uniqueness, source exclusions, sequence identities and model qualifications passed.','',
        '- [All panels](panels.csv), [positive assignments](positive_assignments.csv), and [panel validation](PANEL_VALIDATION.json)',
        '- [All model scores](all_model_scores.csv), [per-P metrics](per_positive_metrics.csv), [per-target metrics](per_target_metrics.csv), and [summary metrics](metrics.csv)',
        '- [Degree control](degree_control_summary.csv), [paired differences](paired_differences.csv), and [exposure summary](EXPOSURE_SUMMARY.json)',
        '- [Protocol](PROTOCOL.md), [input freeze](INPUT_FREEZE.json), [independent result validation](RESULT_VALIDATION.json), and [reproduction](REPRODUCE.md)',
        '- [PDF figure](pu_concordance.pdf), [SVG figure](pu_concordance.svg), and [final checksums](FINAL_MANIFEST.json)','',
        'Source attribution: EMBL-EBI IntAct/IMEx release 252 and Zhong et al. (2016), PMID 27107014, under CC BY 4.0.','']
    with (OUT/'REPORT.md').open('x') as f:
        f.write('\n'.join(lines))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4.2),sharex=True)
    colors=('#496B8B','#CE883F','#507A60')
    for ax,aggregation,title in zip(axes,('equal_positive','equal_yeast_target'),('Equal weight per P','Equal weight per yeast target')):
        for i,m in enumerate(MODELS):
            r=row(m,aggregation=aggregation)
            v,lo,hi=map(float,(r['estimate'],r['ci_low'],r['ci_high']))
            ax.errorbar(v,2-i,xerr=np.array([[v-lo],[hi-v]]),fmt='o',capsize=4,color=colors[i],markersize=7)
            ax.text(v,2-i+.16,f'{v:.3f}',ha='center',fontsize=10)
        ax.axvline(.5,color='0.55',linestyle='--',linewidth=1)
        ax.set_xlim(0,1)
        ax.set_ylim(-.5,2.6)
        ax.set_yticks([2,1,0],[NAMES[m] for m in MODELS])
        ax.set_xlabel('P-vs-U concordance (95% interval)')
        ax.set_title(title)
        ax.grid(axis='x',alpha=.15)
    fig.suptitle('1,555 published P; 100 globally distinct U per P')
    fig.tight_layout()
    for suffix in ('png','pdf','svg'):
        fig.savefig(OUT/('pu_concordance.'+suffix),dpi=180,bbox_inches='tight')
    plt.close(fig)
    ipin,tuna=read(OUT/'IPIN_RUN.json'),read(OUT/'TUNA_RUN.json')
    files=[p for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='FINAL_MANIFEST.json' and p.suffix!='.npz']
    write_json(OUT/'FINAL_MANIFEST.json',{'at_utc':now(),'status':'complete_P_vs_U_evaluation',
        'study_id':CONFIG['study_id'],'P':1555,'U':155500,'globally_distinct_U':155500,'U_per_P':100,
        'total_pairs':157055,'all_original_P_preserved':True,'models':list(MODELS),'validation_status':'passed',
        'files':[record(p) for p in files],
        'local_features':[ipin['embedding_artifact'],tuna['residues'],analysis['bootstrap_samples']]})
    print('Finalized P-vs-U evaluation with all 1,555 P and 155,500 distinct U',flush=True)


if __name__=='__main__':
    main()
