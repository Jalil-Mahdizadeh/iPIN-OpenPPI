"""Per-positive PU concordance, retrieval, target bootstrap and exposure sensitivity."""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
import numpy as np
from study_utils import *

METRICS=('P_vs_U_concordance','average_precision','reciprocal_rank','first_positive_rank_expected',
         'recall_at_5','recall_at_10','recall_at_20','NDCG_at_10')
COHORTS=('all','no_exact_TRAIN_DEV_endpoint')
AGGREGATIONS=('equal_positive','equal_yeast_target')


def selftest():
    from sklearn.metrics import roc_auc_score,average_precision_score
    metric=metric_module()
    rng=np.random.default_rng(CONFIG['seed'])
    cases=[np.r_[1.,np.zeros(100)],np.r_[0.,np.ones(100)],np.ones(101)]
    cases += [rng.integers(-3,4,101).astype(float) for _ in range(200)]
    truth=np.r_[True,np.zeros(100,dtype=bool)]
    maximum=0.
    for scores in cases:
        actual=metric.evaluate(scores,truth,tuple(CONFIG['cutoffs']))
        expected={'P_vs_U_concordance':roc_auc_score(truth,scores),
                  'average_precision':average_precision_score(truth,scores)}
        greater=sum(float(s)>float(scores[0]) for s in scores[1:])
        equal=sum(float(s)==float(scores[0]) for s in scores[1:])
        positions=list(range(greater+1,greater+equal+2))
        expected['reciprocal_rank']=sum(1/r for r in positions)/len(positions)
        expected['first_positive_rank_expected']=sum(positions)/len(positions)
        for k in CONFIG['cutoffs']:
            expected['recall_at_'+str(k)]=sum(r<=k for r in positions)/len(positions)
        for k,value in expected.items():
            error=abs(actual[k]-value)
            maximum=max(maximum,error)
            require(error<1e-12,'Metric self-test failed: '+k)
    write_json(OUT/'METRIC_SELFTEST.json',{'status':'passed','at_utc':now(),'cases':len(cases),
        'maximum_error':maximum,'oracle':'sklearn AUROC/AP and enumerated possible P ranks',
        'implementation':record(ROOT/'example/twelve_target_comparison_v1/metrics.py')})
    print('Metric self-test passed:',len(cases),'cases',flush=True)


def analyze():
    check_records(read(OUT/'INPUT_FREEZE.json')['files'])
    metric=metric_module()
    rows,ipin,tuna=[table(OUT/n) for n in ('panels.csv','ipin_scores.csv','tuna_scores.csv')]
    require(len(rows)==len(ipin)==len(tuna)==157055,'Incomplete scores')
    exact={r['sequence_sha256']:r for r in table(OUT/'exact_endpoint_exposure.csv')}
    proteins={r['sequence_sha256']:r for r in table(OUT/'proteins.csv')}
    groups=defaultdict(list)
    for i,(r,a,b) in enumerate(zip(rows,ipin,tuna,strict=True)):
        require(int(r['row_index'])==int(a['row_index'])==int(b['row_index'])==i,'Score row order changed')
        for m in MODELS:
            value=float((b if m=='tuna_retrained' else a)[m+'_score'])
            require(np.isfinite(value),'Nonfinite model score')
            r[m+'_score']=value
        endpoints=(r['query_sequence_sha256'],r['partner_sequence_sha256'])
        r['any_exact_TRAIN_DEV_endpoint']=any(exact[h][k]=='True' for h in endpoints for k in ('exact_TRAIN_endpoint','exact_DEV_endpoint'))
        groups[r['panel_id']].append(r)
    write_csv(OUT/'all_model_scores.csv',rows)
    del ipin,tuna
    evaluated,coverage,controls=[],[],[]
    for pid,full in groups.items():
        for cohort in COHORTS:
            selected=[r for r in full if cohort=='all' or not r['any_exact_TRAIN_DEV_endpoint']]
            positive=np.array([r['label']=='P' for r in selected],dtype=bool)
            valid=bool(positive.any() and (~positive).any())
            coverage.append({'cohort':cohort,'panel_id':pid,'target_id':full[0]['target_id'],
                'P':int(positive.sum()),'U':int((~positive).sum()),'evaluable':valid})
            if not valid:
                continue
            cutoffs=tuple(k for k in CONFIG['cutoffs'] if k<=len(selected))
            for m in MODELS:
                score=np.array([r[m+'_score'] for r in selected])
                result=metric.evaluate(score,positive,cutoffs)
                evaluated.append({'cohort':cohort,'panel_id':pid,'target_id':full[0]['target_id'],'model':m,**result})
            if cohort=='all':
                score=np.array([int(proteins[r['partner_sequence_sha256']]['association_degree']) for r in selected])
                controls.append({'panel_id':pid,'target_id':full[0]['target_id'],
                    'control':'source_association_degree',**metric.evaluate(score,positive,cutoffs)})
    write_csv(OUT/'per_positive_metrics.csv',evaluated)
    write_csv(OUT/'analysis_coverage.csv',coverage)
    write_csv(OUT/'degree_control_metrics.csv',controls)
    target_rows=[]
    by_target=defaultdict(list)
    for r in evaluated:
        by_target[r['cohort'],r['model'],r['target_id']].append(r)
    for (cohort,model,target),rr in sorted(by_target.items()):
        target_rows.append({'cohort':cohort,'model':model,'target_id':target,'panels':len(rr),
            'P':sum(r['P'] for r in rr),'U':sum(r['U'] for r in rr),
            **{k:float(np.mean([r[k] for r in rr if k in r])) if any(k in r for r in rr) else '' for k in METRICS}})
    write_csv(OUT/'per_target_metrics.csv',target_rows)
    intervals,contrasts,draw_arrays=[],[],{}
    for cohort in COHORTS:
        for key in METRICS:
            selected={m:[r for r in evaluated if r['cohort']==cohort and r['model']==m and key in r] for m in MODELS}
            require(all(selected.values()),'No evaluable panels for metric')
            targets=sorted({r['target_id'] for r in selected[MODELS[0]]})
            count=np.array([sum(r['target_id']==t for r in selected[MODELS[0]]) for t in targets],dtype=np.float64)
            sample=np.random.default_rng(CONFIG['seed']).integers(0,len(targets),size=(CONFIG['bootstrap_draws'],len(targets)))
            sampled_counts=count[sample].sum(axis=1)
            for aggregation in AGGREGATIONS:
                points,draws={},{}
                for m in MODELS:
                    sums=np.array([sum(r[key] for r in selected[m] if r['target_id']==t) for t in targets])
                    if aggregation=='equal_positive':
                        points[m]=float(sums.sum()/count.sum())
                        draws[m]=sums[sample].sum(axis=1)/sampled_counts
                    else:
                        means=sums/count
                        points[m]=float(means.mean())
                        draws[m]=means[sample].mean(axis=1)
                    lo,hi=np.quantile(draws[m],[.025,.975])
                    intervals.append({'cohort':cohort,'aggregation':aggregation,'model':m,'metric':key,
                        'estimate':points[m],'ci_low':float(lo),'ci_high':float(hi),'targets':len(targets),
                        'panels':int(count.sum()),'P':sum(r['P'] for r in selected[m]),'U':sum(r['U'] for r in selected[m])})
                    draw_arrays['__'.join((cohort,aggregation,m,key))]=draws[m]
                for a,b in combinations(MODELS,2):
                    lo,hi=np.quantile(draws[b]-draws[a],[.025,.975])
                    contrasts.append({'cohort':cohort,'aggregation':aggregation,'metric':key,
                        'model_a':a,'model_b':b,'difference_b_minus_a':points[b]-points[a],
                        'ci_low':float(lo),'ci_high':float(hi),'targets':len(targets),'panels':int(count.sum())})
    write_csv(OUT/'metrics.csv',intervals)
    write_csv(OUT/'paired_differences.csv',contrasts)
    with (LOCAL/'bootstrap_draws.npz').open('xb') as f:
        np.savez_compressed(f,**draw_arrays)
    control_summary=[]
    for aggregation in AGGREGATIONS:
        rr=controls if aggregation=='equal_positive' else [
            {k:float(np.mean([r[k] for r in controls if r['target_id']==t])) for k in METRICS}
            for t in sorted({r['target_id'] for r in controls})]
        control_summary.append({'aggregation':aggregation,**{k:float(np.mean([r[k] for r in rr])) for k in METRICS}})
    write_csv(OUT/'degree_control_summary.csv',control_summary)
    exposure_summary=[]
    for taxid in ('559292','9606'):
        hs=[h for h,r in proteins.items() if r['taxid']==taxid]
        exposure_summary.append({'taxid':int(taxid),'proteins':len(hs),
            'exact_TRAIN':sum(exact[h]['exact_TRAIN_endpoint']=='True' for h in hs),
            'exact_development':sum(exact[h]['exact_DEV_endpoint']=='True' for h in hs),
            'either_exact_TRAIN_or_development':sum(exact[h]['exact_TRAIN_endpoint']=='True' or exact[h]['exact_DEV_endpoint']=='True' for h in hs)})
    write_json(OUT/'EXPOSURE_SUMMARY.json',{'organisms':exposure_summary,
        'exact_pair_counts':read(OUT/'EXPOSURE_AUDIT.json')['exact_pair_counts'],
        'protein_language_model_pretraining_audited':False})
    output_names=('all_model_scores.csv','per_positive_metrics.csv','analysis_coverage.csv','degree_control_metrics.csv',
                  'per_target_metrics.csv','metrics.csv','paired_differences.csv','degree_control_summary.csv','EXPOSURE_SUMMARY.json')
    write_json(OUT/'ANALYSIS.json',{'at_utc':now(),'P':1555,'U':155500,'pairs':157055,'P_per_panel':1,'U_per_panel':100,
        'primary_metric':'P_vs_U_concordance','primary_aggregation':'equal_positive','secondary_aggregation':'equal_yeast_target',
        'U_is_unlabeled':True,'biological_negative_claim':False,'per_positive_metric_rows':len(evaluated),
        'bootstrap_draws':CONFIG['bootstrap_draws'],'bootstrap_seed':CONFIG['seed'],'bootstrap_unit':'yeast target',
        'bootstrap_samples':record(LOCAL/'bootstrap_draws.npz'),'metrics':intervals,'paired_differences':contrasts,
        'selection':record(OUT/'PANEL_SELECTION.json'),'input_freeze':record(OUT/'INPUT_FREEZE.json'),
        'outputs':[record(OUT/n) for n in output_names],
        'model_outputs':[record(OUT/n) for n in ('ipin_scores.csv','tuna_scores.csv','IPIN_RUN.json','TUNA_RUN.json')],
        'uncertainty':'Exploratory paired target bootstrap, conditional on fixed panels and one source study; shared human partners remain dependent.'})
    print('PU analysis complete: 1,555 P versus 155,500 globally distinct U',flush=True)


if __name__=='__main__':
    require_container()
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('selftest','analyze'))
    phase=parser.parse_args().phase
    selftest() if phase=='selftest' else analyze()
