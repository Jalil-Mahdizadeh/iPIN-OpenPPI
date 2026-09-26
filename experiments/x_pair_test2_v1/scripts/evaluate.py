"""The unchanged test2 metric, paired contrasts, and disclosed exposure sensitivity."""
import argparse
import csv
import os
import time
from pathlib import Path
import numpy as np
from io_utils import ROOT,MODELS,CELLS,COHORTS,arrays,atomic,cuda,now,read,record,sha,verify
from common import concordance
from macro_metrics import macro_bootstrap,qualify_macro

OUT=ROOT/'results'
REF=Path('/reference/results')
FOCUS=('selected_31k',)+MODELS
LABELS={'selected_31k':'iPIN-TUnA-31k','multitask_xfair':'X-PAIR default multitask',
        'interaction_xfair':'X-PAIR interaction only','ipin_baseline':'Original iPIN',
        'ipin_optimized':'Optimized iPIN','tuna_retrained_ensemble':'PU-TUnA 17k',
        'tuna_original':'Original TUnA','dscript_original':'Original D-SCRIPT','dscript_retrained':'PU-D-SCRIPT',
        'plm_interact_original_650m_humanv11':'PLM-interact 650M humanV11',
        'rapppid_original_released_mult':'Original RAPPPID','rapppid_recovery_mean_logit':'PU-RAPPPID recovery',
        'sprint_native_train_positive_graph':'SPRINT 17k','cross_attention_ensemble':'Cross-attention ensemble',
        'mean_pool_ensemble':'Mean-pooling ensemble'}

def csv_write(path,rows):
    with Path(path).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)

def quantiles(values):
    valid=values[np.isfinite(values)];assert len(valid)>1900
    return np.quantile(valid,[.025,.975]).tolist()

def summarize(names,points,draws):
    scores={name:{'PU_concordance':float(points[j]),'ci95':quantiles(draws[j])} for j,name in enumerate(names)}
    contrasts=[]
    for new in MODELS:
        j=names.index(new)
        for old in names:
            if old in MODELS:continue
            k=names.index(old)
            contrasts.append({'model':new,'reference':old,'difference':float(points[j]-points[k]),
                              'ci95':quantiles(draws[j]-draws[k])})
    return scores,contrasts

def pair_codes(a,b,n):return np.minimum(a,b).astype(np.int64)*n+np.maximum(a,b)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--qualify',action='store_true');args=parser.parse_args()
    device=cuda();q=qualify_macro(device)
    atomic(ROOT/'qualification/METRIC.json',{'at_utc':now(),**q})
    if args.qualify:print(q,flush=True);return
    started=time.monotonic();freeze=read(OUT/'PREDICTION_FREEZE.json')
    assert freeze['complete_finite_candidate_coverage'] and not freeze['test_truth_read_during_scoring_or_assembly']
    for item in freeze['files']:verify(ROOT/item['path'],item)
    # All prediction files are frozen and checked before labels are opened here.
    for item in read(ROOT/'INPUT_FREEZE.json')['files']:
        path=item['path']
        if '/private/test/' in path:verify(Path('/truth')/path.split('/private/test/')[1],item)
        elif 'test2_frozen_competitors_v1/results/' in path:verify(REF/path.split('/results/')[1],item)
    assert sha('/studydata/sequences.json')==sha(ROOT/'data/sequences.json')
    metadata=read(ROOT/'data/sequences.json');components=np.array(metadata['extended_component']);lengths=np.array(metadata['length'])
    n=len(lengths);prior=read(REF/'RESULTS.json');old_names=prior['primary_models']
    exposure=arrays(ROOT/'exposure/unique_pairs.npz');endpoint_seen=arrays(ROOT/'exposure/endpoints.npz')['normalized']
    audit=read(ROOT/'exposure/AUDIT.json')
    for item in audit['files']:verify(ROOT/item['path'],item)
    results={};cohort_rows=[];exposure_rows=[];replay=[]
    for cell in CELLS:
        targets=[];scores=[];rawlogits=[];flags=[];groups=[]
        for c,cohort in enumerate(COHORTS):
            data=arrays(Path('/truth')/('reconciled' if cohort=='legacy' else 'added')/f'{cell}.npz')
            candidate=arrays(ROOT/f'data/candidates/{cohort}_{cell}.npz')
            assert np.array_equal(data['a'],candidate['a']) and np.array_equal(data['b'],candidate['b'])
            fresh=arrays(OUT/f'predictions/{cohort}_{cell}.npz');old=arrays(REF/f'predictions/{cohort}_{cell}.npz')
            index=arrays(ROOT/f'data/candidates/map_{cohort}_{cell}.npz')['index'];flag=exposure['normalized'][index]
            targets.append(data);scores.append(np.column_stack([old['selected_31k']]+[fresh[m] for m in MODELS]))
            rawlogits.append(np.column_stack([fresh[m+'_logit'] for m in MODELS]));flags.append(flag)
            groups.append(np.full(len(index),c,int))
            length_ok=(lengths[data['a']]>=50)&(lengths[data['a']]<=2000)&(lengths[data['b']]>=50)&(lengths[data['b']]<=2000)
            for name,value in [(m,old[m]) for m in old_names]+[(m,fresh[m]) for m in MODELS]:
                cohort_rows.append({'cell':cell,'cohort':cohort,'model':name,'P':int(data['positive'].sum()),
                    'U':int((~data['positive']).sum()),'PU_concordance':concordance(value,data['positive'],data['weight'])})
            exposure_rows.append({'cell':cell,'cohort':cohort,'P':int(data['positive'].sum()),'U':int((~data['positive']).sum()),
                'exposed_P':int(((flag!=0)&data['positive']).sum()),'exposed_U':int(((flag!=0)&~data['positive']).sum()),
                'exposed_to_interaction_training_P':int(((flag&1)!=0).sum()),
                'exposed_to_interaction_training_U':int(((flag&2)!=0).sum()),
                'benchmark_P_in_XPAIR_positive_train':int((((flag&1)!=0)&data['positive']).sum()),
                'benchmark_P_in_XPAIR_negative_train':int((((flag&2)!=0)&data['positive']).sum()),
                'benchmark_U_in_XPAIR_positive_train':int((((flag&1)!=0)&~data['positive']).sum()),
                'benchmark_U_in_XPAIR_negative_train':int((((flag&2)!=0)&~data['positive']).sum()),
                'both_endpoints_seen_in_XPAIR_train_or_val':int(((endpoint_seen[data['a']]!=0)&(endpoint_seen[data['b']]!=0)).sum()),
                'outside_checkpoint_training_length_range':int((~length_ok).sum())})
        data={key:np.r_[targets[0][key],targets[1][key]] for key in ('a','b','positive','weight')}
        score=np.concatenate(scores);rawlogit=np.concatenate(rawlogits);flag=np.concatenate(flags);group=np.concatenate(groups)
        views=[('test_2_macro',np.ones(len(group),bool)),('test_2_macro_no_XPAIR_pair_exposure',flag==0)]
        if cell=='C1':
            old_dev=arrays('/studydata/legacy/development_02.npz');new_dev=arrays('/studydata/development/added/C1.npz')
            dev_codes=np.r_[pair_codes(old_dev['a'],old_dev['b'],n),pair_codes(new_dev['a'],new_dev['b'],n)]
            no_dev=~np.isin(pair_codes(data['a'],data['b'],n),dev_codes)
            views += [('test_2_macro_no_dev_overlap',no_dev),
                      ('test_2_macro_no_dev_or_XPAIR_pair_exposure',no_dev&(flag==0))]
        for view,keep in views:
            target=OUT/f'{cell}_{view}.json';bootstrap=OUT/f'bootstrap_{cell}_{view}.npz'
            if target.exists():
                report=read(target)
                assert report['prediction_freeze_sha256']==sha(OUT/'PREDICTION_FREEZE.json')
                verify(bootstrap,report['bootstrap_file'])
            else:
                points,draws,bmeta=macro_bootstrap(score[keep],data['positive'][keep],data['weight'][keep],group[keep],
                    components[data['a'][keep]].tolist(),components[data['b'][keep]].tolist(),cell+'_'+view,
                    replicates=2000,device=device)
                names=list(FOCUS);replayed=None
                if view in ('test_2_macro','test_2_macro_no_dev_overlap'):
                    old=arrays(REF/f'bootstrap_{cell}_{view}.npz');old_report=prior['test'][cell+':'+view]
                    j=old_names.index('selected_31k')
                    assert abs(points[0]-old['points'][j])<1e-12
                    error=float(np.nanmax(np.abs(draws[0]-old['draws'][j])))
                    assert error<1e-12 and np.array_equal(np.isnan(draws[0]),np.isnan(old['draws'][j]))
                    assert bmeta==old_report['bootstrap']
                    replayed={'cell':cell,'view':view,'max_selected_31k_draw_error':error,'passed':True}
                    names=old_names+list(MODELS)
                    points=np.r_[old['points'],points[1:]];draws=np.concatenate([old['draws'],draws[1:]])
                models,differences=summarize(names,points,draws)
                temp=bootstrap.with_name(bootstrap.name+f'.{os.getpid()}.tmp')
                with temp.open('wb') as stream:np.savez(stream,points=points,draws=draws)
                temp.replace(bootstrap)
                logit_checks={m:float(np.mean([concordance(rawlogit[keep&(group==c),j],data['positive'][keep&(group==c)],
                             data['weight'][keep&(group==c)]) for c in (0,1)])) for j,m in enumerate(MODELS)}
                report={'cell':cell,'view':view,'model_order':names,'models':models,'paired_differences':differences,
                    'bootstrap':bmeta,'bootstrap_file':record(bootstrap),'reference_replay':replayed,
                    'prediction_freeze_sha256':sha(OUT/'PREDICTION_FREEZE.json'),
                    'excluded_candidate_rows':int((~keep).sum()),
                    'cohort_counts':[{'cohort':COHORTS[c],'P':int((keep&(group==c)&data['positive']).sum()),
                                     'U':int((keep&(group==c)&~data['positive']).sum())} for c in (0,1)],
                    'raw_logit_macro_diagnostic_only':logit_checks}
                atomic(target,report)
            if report['reference_replay']:replay.append(report['reference_replay'])
            results[cell+':'+view]=report
            print({'evaluated':cell+':'+view,'points':{m:report['models'][m]['PU_concordance'] for m in FOCUS}},flush=True)
    result={'at_utc':now(),'primary_cell':'C3','primary_XPAIR':'multitask_xfair','test':results,
        'metric':'Equal-cohort macro of design-weighted P/U concordance','bootstrap_replicates':2000,
        'test2_is_fresh_independent':False,'checkpoint_selection':False,'U_is_confirmed_negative':False,
        'cohort_points':cohort_rows,'exposure':exposure_rows,'reference_replay':replay,
        'intervals':'Pointwise 95% paired component bootstrap; not multiplicity-adjusted',
        'prediction_freeze_sha256':sha(OUT/'PREDICTION_FREEZE.json')}
    atomic(OUT/'RESULTS.json',result)
    rows=[];contrasts=[]
    for panel,report in results.items():
        for model,value in report['models'].items():
            rows.append({'panel':panel,'model':model,'PU_concordance':value['PU_concordance'],
                         'ci95_low':value['ci95'][0],'ci95_high':value['ci95'][1]})
        for value in report['paired_differences']:
            contrasts.append({'panel':panel,'model':value['model'],'reference':value['reference'],
                              'difference':value['difference'],'ci95_low':value['ci95'][0],'ci95_high':value['ci95'][1]})
    csv_write(OUT/'scores.csv',rows);csv_write(OUT/'paired_differences.csv',contrasts)
    csv_write(OUT/'cohort_scores.csv',cohort_rows);csv_write(OUT/'exposure.csv',exposure_rows)
    write_report(result,old_names);plot(result,old_names)
    atomic(OUT/'COMPLETE.json',{'at_utc':now(),'elapsed_s':time.monotonic()-started,
        'results':record(OUT/'RESULTS.json'),'candidate_rows':freeze['candidate_rows'],'models_added':list(MODELS),
        'all_previous_reference_replays_passed':all(x['passed'] for x in replay)})

def write_report(result,old_names):
    test=result['test'];lines=['# Released X-PAIR on unchanged test-2','',
        f"Completed {result['at_utc']}. Both released X-PAIR checkpoints cover all 3,774,966 candidate pairs.",'',
        'The primary predictor is the authors’ default multitask X-fair checkpoint. The interaction-only X-fair checkpoint is a prespecified secondary result. Neither is retrained, selected, calibrated, or threshold-tuned on test-2.',
        '', 'The metric is the existing equal-cohort macro of design-weighted P-versus-U concordance. C3 is primary. U pairs are unlabeled; test-2 is a previously examined historical benchmark.', '',
        '| Model | C1 | C2 | C3 |','|---|---:|---:|---:|']
    for model in ['selected_31k']+list(MODELS)+[m for m in old_names if m!='selected_31k']:
        lines.append('| '+LABELS[model]+' | '+' | '.join(f"{test[c+':test_2_macro']['models'][model]['PU_concordance']:.6f}" for c in CELLS)+' |')
    lines += ['', '## Paired comparison with iPIN-TUnA-31k','',
        'Positive differences favor X-PAIR. Intervals are pointwise, not adjusted for multiple comparisons.','',
        '| Cell | X-PAIR | Difference | Paired 95% interval |','|---|---|---:|---:|']
    for c in CELLS:
        for row in test[c+':test_2_macro']['paired_differences']:
            if row['reference']=='selected_31k':
                lo,hi=row['ci95'];lines.append(f"| {c} | {LABELS[row['model']]} | {row['difference']:+.6f} | [{lo:+.6f}, {hi:+.6f}] |")
    lines += ['', '## Released training and validation exposure','',
        'We matched unordered pairs by full sequence identity and by Ankh-normalized identity (UZOBJ→X). The union includes interaction and interface training and validation. Both-endpoint exposure is recorded separately. C1/C2/C3 retain their original definitions relative to iPIN training; they do not establish unseen-protein status for X-PAIR.','',
        '| Cell / cohort | P | Exposed P | U | Exposed U |','|---|---:|---:|---:|---:|']
    for r in result['exposure']:lines.append(f"| {r['cell']} / {r['cohort']} | {r['P']:,} | {r['exposed_P']:,} | {r['U']:,} | {r['exposed_U']:,} |")
    lines += ['', 'Exact pair exclusion is a sensitivity analysis, not a leakage-free or homology-disjoint benchmark. Structural chains, fragments, homologs, sequence variants and PLM pretraining exposure are not eliminated by exact matching. The full original test-2 panels above are retained.', '',
        '| Cell, exposed pairs excluded | iPIN-TUnA-31k | X-PAIR default | X-PAIR interaction |','|---|---:|---:|---:|']
    for c in CELLS:
        r=test[c+':test_2_macro_no_XPAIR_pair_exposure']
        lines.append('| '+c+' | '+' | '.join(f"{r['models'][m]['PU_concordance']:.6f}" for m in FOCUS)+' |')
    lines += ['', 'The separate C1 development-overlap sensitivity and its intersection with X-PAIR pair exclusion are in `scores.csv`, with paired intervals in `paired_differences.csv`. Legacy and added cohorts are reported separately in `cohort_scores.csv`.', '',
        '## Inference and validation','',
        'Ankh-large features use the pinned released model, full protein sequences, FP32 and the authors’ residue normalization/tokenization. All 7,320 test endpoints are retained, including 100 longer than the checkpoint training maximum of 2,000 residues; the longest is 7,570. This uses the upstream-supported all-length policy. The native default auto policy would filter these proteins.', '',
        'The complete released model state loads strictly. Only the independent 1536→128 linear projection is cached per protein. The original cross-attention, rotary positions, masking, pooling and interaction head run unchanged. Scores are native FP32 sigmoid probabilities; raw logits are also retained as a diagnostic. No attention approximation, truncation, symmetrization, or score calibration is applied.', '',
        'Inference qualification compares the upstream embedding generator and complete forward function against this runner, including long sequences, heterogeneous padding, swapped proteins, and batches. Embeddings matched exactly; score differences were below the recorded tolerances. Model state is checked unchanged after every scoring shard. Existing iPIN bootstrap points and paired draws are replayed within 1e-12 before reusing all 13 reference predictors.', '',
        'The isolated ARM64 runtime uses the existing CUDA/PyTorch 2.8 container with Lightning 2.5.1, TorchMetrics 1.7.1 and Transformers 4.50.3 installed only in this experiment. It uses NumPy 1.26 and FP32 with TF32 disabled. Qualification establishes numerical agreement with the unchanged upstream functions in this runtime; it is not a claim of bitwise agreement across all software/hardware versions.', '',
        'This comparison concerns released predictors with different training corpora and endpoint exposure. It does not isolate architecture, prove calibration, establish confirmed negative pairs, or compare structural interface accuracy. All original input data, model weights and previous result files are preserved; `PRESERVATION.json` records the final hash verification.', '',
        'Sources: [released X-PAIR repository](https://gitlab.lcqb.upmc.fr/srescalli/X-PAIR), commit `897646a4a768acd488f4163ff07dd5a1183d52b1`; [released X-fair data](https://doi.org/10.5281/zenodo.21457017); [Ankh-large](https://huggingface.co/ElnaggarLab/ankh-large), revision `74b371dbfa3ee0a05d32ae74df0c2e0b82d6b9a6`.','']
    (OUT/'RESULTS.md').write_text('\n'.join(lines))

def plot(result,old_names):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names=['selected_31k']+list(MODELS)+[m for m in old_names if m!='selected_31k']
    fig,ax=plt.subplots(figsize=(10,7),layout='constrained')
    for i,name in enumerate(names):
        r=result['test']['C3:test_2_macro']['models'][name]
        color='#00876c' if name=='selected_31k' else '#d95f02' if name in MODELS else '#607d8b'
        ax.plot(r['ci95'],[i,i],color=color,linewidth=2);ax.plot(r['PU_concordance'],i,'o',color=color)
    ax.set(yticks=range(len(names)),yticklabels=[LABELS[n] for n in names],
           xlabel='C3 test-2 macro P/U concordance (pointwise 95% interval)',title='Released X-PAIR and frozen competitors')
    ax.invert_yaxis();ax.spines[['top','right']].set_visible(False)
    for ext in ('png','pdf'):fig.savefig(OUT/f'C3_comparison.{ext}',dpi=180)
    plt.close(fig)

if __name__=='__main__':main()
