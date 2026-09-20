"""Render the completed external comparison and close its public artifacts."""
from __future__ import annotations
from collections import defaultdict
import subprocess
import numpy as np
from study_utils import *

LABELS={'ipin_baseline':'Original affine iPIN','ipin_optimized':'Optimized iPIN','tuna_retrained':'TUnA-retrained'}
SHORT={'mouse':'Mouse','fly':'Fly','worm':'Worm','yeast':'Budding yeast','arabidopsis':'Arabidopsis','ecoli':'E. coli K-12','equal_species':'Equal-species mean'}

def render():
    require_container()
    check_records(read(OUT/'INPUT_FREEZE.json')['files'])
    assert read(OUT/'INDEPENDENT_VALIDATION.json')['passed']
    macro=table(OUT/'macro_metrics.csv'); coverage=table(OUT/'panel_coverage.csv')
    contrasts=table(OUT/'paired_differences.csv'); intervals=table(OUT/'metric_intervals.csv')
    exposure=read(OUT/'EXPOSURE_AUDIT.json'); selection=read(OUT/'PANEL_SELECTION.json')
    similarity=table(OUT/'pair_homology_summary.csv')
    def metric(species,model,key='P_vs_U_concordance',candidate='matched',subset='all'):
        return float(next(r[key] for r in macro if (r['species'],r['model'],r['candidate_set'],r['subset'])==(species,model,candidate,subset)))
    def bound(species,model,key):
        r=next(r for r in intervals if (r['species'],r['model'],r['candidate_set'],r['subset'],r['metric'])==(species,model,'matched','all',key))
        return float(r['ci_low']),float(r['ci_high'])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'svg.fonttype':'none','pdf.fonttype':42})
    names=[s['id'] for s in CONFIG['species']]
    fig,axes=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
    keys=['P_vs_U_concordance','average_precision','recall_at_10','NDCG_at_10']
    titles=['P-versus-U concordance','Mean average precision','Mean recall at 10','Mean NDCG at 10']
    colors=['#52687d','#16837b','#c46a30']
    for ax,key,title in zip(axes.ravel(),keys,titles):
        for j,m in enumerate(MODELS):
            values=np.array([metric(s,m,key) for s in names]); ci=np.array([bound(s,m,key) for s in names])
            x=np.arange(len(names))+(j-1)*.23
            ax.errorbar(x,values,yerr=np.maximum(0,np.vstack((values-ci[:,0],ci[:,1]-values))),
                        fmt='o',capsize=3,color=colors[j],label=LABELS[m],markersize=6)
        if key=='P_vs_U_concordance':ax.axhline(.5,ls='--',lw=1,color='#888888')
        ax.set_xticks(np.arange(len(names)),[SHORT[s] for s in names],rotation=18,ha='right')
        ax.set_title(title);ax.set_ylim(0,1);ax.grid(axis='y',alpha=.2)
        ax.spines[['top','right']].set_visible(False)
    axes[0,0].legend(loc='lower left',fontsize=9)
    fig.suptitle('Frozen human-trained iPIN models: retrieval within six non-human species\n100 length/degree-matched U per target; exploratory paired target-bootstrap intervals',fontsize=13)
    for ext in ('png','pdf','svg'):
        fig.savefig(OUT/f'nonhuman_transfer.{ext}',dpi=180)
    plt.close(fig)
    all_mean={m:metric('equal_species',m) for m in MODELS}
    leader=max(all_mean,key=all_mean.get)
    target_metrics=table(OUT/'per_target_metrics.csv')
    random_reference=[]
    for s in names:
        for candidate in ('background','matched','all_U'):
            rr=[r for r in target_metrics if (r['species'],r['model'],r['subset'],r['candidate_set'])==(s,MODELS[0],'all',candidate)]
            random_reference.append(dict(species=s,candidate_set=candidate,targets=len(rr),
                expected_P_vs_U_concordance=.5,
                expected_recall_at_10=float(np.mean([10/int(r['panel_size']) for r in rr]))))
    write_csv(OUT/'random_ranking_reference.csv',random_reference)
    random_ecoli=next(r['expected_recall_at_10'] for r in random_reference if r['species']=='ecoli' and r['candidate_set']=='matched')
    overall_difference=next(r for r in contrasts if (r['species'],r['subset'],r['candidate_set'],r['metric'],r['model_a'],r['model_b'])==('equal_species','all','matched','P_vs_U_concordance','ipin_optimized','tuna_retrained'))
    lines=['# Frozen iPIN transfer to six non-human organisms','',
        f'Completed {now()[:10]}. All three unchanged frozen iPIN ensembles scored **{selection["pairs"]:,} rows: {selection["P"]:,} P and {selection["U"]:,} U**, across 300 targets in six organisms. There are {selection["unique_sequences"]:,} distinct sequences and {selection["total_residues"]:,} residues. Every species contributes 50 targets.', '',
        f'**{LABELS[leader]} has the highest equal-species point estimate on the primary matched-U comparison ({all_mean[leader]:.4f}).** Its gain over optimized iPIN is {float(overall_difference["difference_b_minus_a"]):+.4f}, with exploratory paired 95% interval [{float(overall_difference["ci_low"]):+.4f}, {float(overall_difference["ci_high"]):+.4f}]. The interval includes zero. The species-specific estimates and early retrieval below matter for screening; this is an external descriptive comparison, not a universal winner designation.', '',
        'Transfer is uneven. Mouse and Arabidopsis have the strongest observed concordance, while E. coli K-12 is weakest. The model with the highest concordance is not always the one recovering most P at a small screening budget: affine iPIN leads mouse concordance, but TUnA-retrained leads its MAP and recall@10; optimized iPIN leads yeast concordance, but TUnA-retrained has higher recall@10.', '',
        f'For E. coli, TUnA-retrained mean recall@10 is {100*metric("ecoli","tuna_retrained","recall_at_10"):.2f}%, versus {100*metric("ecoli","ipin_optimized","recall_at_10"):.2f}% for optimized iPIN and {100*random_ecoli:.2f}% expected from random ordering of these candidate lists. These are point comparisons, not a tested claim of below-random performance. The [analytical random-order reference](random_ranking_reference.csv) is 10/list-size, averaged over targets; it was added during reporting and does not change any prespecified metric. E. coli is also strongly dominated by one source publication, as quantified below. Its modest PU signal is insufficient on its own to justify a general bacterial-screening recommendation.', '',
        '## Primary comparison: P versus 100 matched U per target','',
        'Scores are ranked separately within each target. The table gives equal-target PU concordance; 0.5 is random ranking of the observed P/U labels. The models retain their human TRAIN normalizers, checkpoints, and inference definitions. U is unreported in the declared source snapshot, not experimentally verified noninteraction.','',
        '| Organism | Original affine iPIN | Optimized iPIN | TUnA-retrained |',
        '|---|---:|---:|---:|']
    for s in names+['equal_species']:
        lines.append('| '+SHORT[s]+' | '+' | '.join(f'{metric(s,m):.4f}' for m in MODELS)+' |')
    lines += ['', '![Species-specific retrieval results](nonhuman_transfer.png)','',
        'Intervals in the figure resample targets 10,000 times with the same draw used for all models. They are exploratory and conditional on these fixed panels. Related targets, shared partners, reversed pairs, and shared studies create dependence that these intervals do not fully capture. Intervals are pointwise, without a multiplicity correction.','',
        '### Paired primary differences: TUnA-retrained minus optimized iPIN','',
        '| Organism | Difference | Paired 95% interval |','|---|---:|---|']
    for s in names+['equal_species']:
        r=next(r for r in contrasts if (r['species'],r['subset'],r['candidate_set'],r['metric'],r['model_a'],r['model_b'])==(s,'all','matched','P_vs_U_concordance','ipin_optimized','tuna_retrained'))
        lines.append(f'| {SHORT[s]} | {float(r["difference_b_minus_a"]):+.4f} | [{float(r["ci_low"]):+.4f}, {float(r["ci_high"]):+.4f}] |')
    lines += ['', '## All requested retrieval measures','',
        '[Per-target metrics](per_target_metrics.csv), [macro metrics](macro_metrics.csv), [positive ranks](positive_ranks.csv), [metric intervals](metric_intervals.csv), and [paired model differences](paired_differences.csv) contain concordance, AP/MAP, expected first-positive rank, MRR, recovered P, recall, known-positive precision, enrichment, NDCG and target success at K=5,10,20. All three candidate sets are reported: background, matched, and their union. The same P and frozen predictions are used across sets. Counts are **100+100 U per target**, not per positive.', '',
        '| Matched-U equal-species metric | Original affine iPIN | Optimized iPIN | TUnA-retrained |',
        '|---|---:|---:|---:|']
    for key,label in [('average_precision','MAP'),('reciprocal_rank','MRR'),('recall_at_10','Recall@10'),('known_positive_precision_at_10','Known-positive precision@10'),('NDCG_at_10','NDCG@10')]:
        lines.append('| '+label+' | '+' | '.join(f'{metric("equal_species",m,key):.4f}' for m in MODELS)+' |')
    lines += ['', '| Candidate set: equal-species PU concordance | Original affine iPIN | Optimized iPIN | TUnA-retrained |','|---|---:|---:|---:|']
    for candidate in ('background','matched','all_U'):
        lines.append('| '+candidate+' | '+' | '.join(f'{metric("equal_species",m,candidate=candidate):.4f}' for m in MODELS)+' |')
    lines += ['', 'Known-positive precision is recovery of documented P in the selected list. It is not biological precision or prospective assay hit rate. Additional U changes candidate prevalence and difficulty, so AP/precision values depend on the declared candidate design. [Degree-only controls](degree_control_metrics.csv) use evaluation-source association degree and are diagnostic of ascertainment cues, not independent deployment models.', '',
        '## Training exposure and sequence similarity','',
        f'The audit used **{exposure["human_train_endpoints"]:,} actual human TRAIN pair endpoints** and {exposure["human_development_endpoints"]:,} endpoints appearing in development pairs. Among the external sequences, {exposure["exact_train_endpoints"]:,} exactly match a TRAIN endpoint and {exposure["exact_development_endpoints"]:,} exactly match a development endpoint (these counts can overlap). Taxonomic difference alone is therefore insufficient to establish sequence novelty.', '',
        'Exact sequence and pair flags are in [endpoint exposure](exact_endpoint_exposure.csv) and [pair exposure](exact_pair_exposure.csv). None of the selected P pairs occurs exactly in the checked human TRAIN/development pairs; two mouse U rows match previously sampled human U pairs. The `no_exact_TRAIN_DEV_endpoint` sensitivity removes a pair whenever either endpoint is an exact match to an actual TRAIN/development pair endpoint. It uses the same frozen scores and does not relabel removed P as U. Coverage is explicit in [analysis coverage](analysis_coverage.csv).','',
        '| Matched U after excluding exact TRAIN/development endpoint matches | Original affine iPIN | Optimized iPIN | TUnA-retrained |','|---|---:|---:|---:|']
    for s in names+['equal_species']:
        lines.append('| '+SHORT[s]+' | '+' | '.join(f'{metric(s,m,subset="no_exact_TRAIN_DEV_endpoint"):.4f}' for m in MODELS)+' |')
    lines += ['', 'Pinned MMseqs2 searched the external sequences against actual TRAIN endpoints at sensitivity 7.5 and E<=0.001. [Sequence matches](training_sequence_similarity.csv) retain the highest-bit local match and maximum-identity match covering at least 80% of both sequences. [Target-similarity metrics](target_similarity_metrics.csv) preserve retrieval lists and group targets by similarity; [pair-homology summaries](pair_homology_summary.csv) compare P and U within the same target and 0/1/2-endpoint homology category. Those conditional subsets have different denominators and are not interchangeable with the full panel.', '',
        'No qualifying hit does not rule out remote homology or a shared domain. These are human PPI-supervision exposure checks; neither absence from ESM pretraining nor complete sequence naivety is established. The frozen normalizer and encoder remain unchanged.', '',
        '## Source, sampling, and coverage','',
        'The data are original XML records from archived IntAct release 252 (2026-01-09), attributed to [IntAct/IMEx](https://www.ebi.ac.uk/intact/about) and the source publications retained in `selected_evidence.json.gz`. Data are CC BY 4.0. [Sources](SOURCES.json), [revised evidence audit](SOURCE_PARSING_v2.json), and [source feasibility](source_feasibility_v2.csv) record the audit. Positives require direct-interaction annotation or a binary two-hybrid method, exactly two protein participants of the specified taxid, no negative/modelled/expansion/intramolecular flag, and no recorded non-tag features.', '',
        'The initial stricter rules left little usable fly and worm coverage because they excluded all tags and all MI:0915 two-hybrid evidence. The [prescoring adjustment](PRE_SCORING_EVIDENCE_ADJUSTMENT.md) documents the methodological revision based only on source metadata. Both initial and revised counts remain public. No model predictions informed it.', '',
        'Targets were selected uniformly by fixed seeded hash from those with at least two eligible positive partners. Up to ten P per target were selected the same way. U excludes every reported co-participant pair in these species archives, including complexes and negative records. All 30,000 matched U satisfy the same source-association-degree bin and the 0.5–2 length ratio; no fallback tier was used.', '',
        '| Organism | P rows | Unique P pairs | Unique sequences | P-supporting studies | Largest study fraction |','|---|---:|---:|---:|---:|---:|']
    for r in coverage:
        lines.append(f'| {SHORT[r["species"]]} | {r["P_rows"]} | {r["unique_P_pairs"]} | {r["unique_sequences"]} | {r["P_publications"]} | {100*float(r["largest_publication_fraction"]):.1f}% |')
    lines += ['', 'Study fractions count unique selected P pairs supported by a publication; multiple studies can support a pair. [Full study coverage](study_coverage.csv) and [panel coverage](panel_coverage.csv) show reuse and ascertainment concentration. Eligibility and assay/study composition differ across organisms, so differences cannot be attributed solely to evolutionary distance.', '',
        'The candidate universe is the archived species evidence universe, not the whole proteome. Only standard-amino-acid sequences of 50–2,000 residues are included. Yeast is specifically the S288C taxid 559292 and E. coli is K-12 taxid 83333. No sequence is truncated. Sequence and assay annotations do not authenticate every experimental construct as native full length; the task is reference-sequence partner prioritization.', '',
        '## Integrity and interpretation','',
        '[Input freeze](INPUT_FREEZE.json) preceded model inference. The [independent panel audit](PANEL_VALIDATION.json) re-parsed original XML without the production parser and checked that no selected U was a reported co-participant pair. [Independent metric validation](INDEPENDENT_VALIDATION.json) checks every reported target row with sklearn ROC/AP/NDCG and separate combinatorial cutoff/rank oracles. [iPIN execution](IPIN_RUN.json) and [TUnA execution](TUNA_RUN.json) record fresh representations, exact model inputs, symmetry, native qualification and unchanged parameters/buffers.', '',
        'No model was retrained, recalibrated, selected, or promoted. No original TUnA comparator was added; this study evaluates the three registered iPIN ensembles only. Human protected test pair identities and truth were not opened. The human C3 benchmark and this panel differ in sampling and evidence, so their numerical difference is not a controlled species-transfer effect. These results support choosing candidates for prospective assays within the examined scope; they do not establish binding probabilities, verified negatives, or performance on all non-human proteins.', '',
        'See [reproduction and file guide](README.md) and the final checksum manifest.']
    with (OUT/'REPORT.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    write_json(OUT/'SUMMARY.json',dict(at_utc=now(),primary='equal-target PU concordance for matched U within species',
        overall_equal_species=all_mean,highest_overall_point_model=leader,selection=selection,
        conclusions_are_descriptive=True,no_frozen_model_changed=True))

def finalize():
    require_container()
    check_records(read(OUT/'INPUT_FREEZE.json')['files'])
    check_records(read(OUT/'EXPOSURE_AUDIT.json')['files'])
    for name in ('IPIN_RUN.json','TUNA_RUN.json'):
        check_records(read(OUT/name)['verified_model_inputs'])
    assert read(OUT/'INDEPENDENT_VALIDATION.json')['passed']
    runtimes=[]
    expected={'containers/images/ipin-data-arm64_0.1.2.sif':'72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629',
              'containers/images/ipin-model-arm64_0.1.0.sif':'c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91',
              'benchmark/containers/images/tuna-arm64-v1.sif':'98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1'}
    for path,wanted in expected.items():
        r=record(ROOT/path);assert r['sha256']==wanted;runtimes.append(r)
    write_json(OUT/'RUNTIMES.json',dict(at_utc=now(),runtimes=runtimes))
    files=[record(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='FINAL_MANIFEST.json' and p.suffix!='.log' and not p.name.startswith('.') and p.suffix not in ('.npz','.npy','.h5')]
    write_json(OUT/'FINAL_MANIFEST.json',dict(at_utc=now(),complete=True,outputs=files,
        git_parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        frozen_registry_sha256=CONFIG['model_registry_sha256'],all_three_models_unchanged=True,
        human_protected_test_pairs_or_truth_read=False,large_local_assets_excluded_from_git=True))
    print('Closed public artifacts:',len(files),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('phase',choices=('render','finalize'))
    globals()[p.parse_args().phase]()
