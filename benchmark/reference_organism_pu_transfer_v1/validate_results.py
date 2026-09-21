"""Independent one-P rank oracle and all paired target-bootstrap intervals."""
from collections import defaultdict
import math
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
from study_utils import *

KEYS=('P_vs_U_concordance','average_precision','reciprocal_rank','first_positive_rank_expected',
      'recall_at_5','recall_at_10','recall_at_20','NDCG_at_10')


def main():
    require_container()
    check_records(read(OUT/'INPUT_FREEZE.json')['files'])
    validation=read(OUT/'PANEL_VALIDATION.json')
    require(validation['status']=='passed','Panel validation missing')
    verify(validation['selection'])
    analysis=read(OUT/'ANALYSIS.json')
    check_records(analysis['outputs']+analysis['model_outputs'])
    verify(analysis['bootstrap_samples'])
    rows=table(OUT/'panels.csv')
    score_tables={m:table(OUT/('tuna_scores.csv' if m=='tuna_retrained' else 'ipin_scores.csv')) for m in MODELS}
    require(all(len(rr)==len(rows) for rr in score_tables.values()),'Incomplete model scores')
    exposure={r['sequence_sha256']:r for r in table(OUT/'exact_endpoint_exposure.csv')}
    groups=defaultdict(list)
    for i,r in enumerate(rows):
        require(int(r['row_index'])==i,'Changed panel row order')
        for m,rr in score_tables.items():
            require(int(rr[i]['row_index'])==i and math.isfinite(float(rr[i][m+'_score'])),'Invalid score alignment/value')
        groups[r['panel_id']].append(i)
    measured={(r['cohort'],r['model'],r['panel_id']):r for r in table(OUT/'per_positive_metrics.csv')}
    oracle={}
    maximum=0.
    checks=0
    def check(a,b,message):
        nonlocal maximum,checks
        error=abs(float(a)-float(b))
        maximum=max(maximum,error)
        checks+=1
        require(error<1e-12,message)
    for cohort in ('all','no_exact_TRAIN_DEV_endpoint'):
        for pid,indices in groups.items():
            selected=[i for i in indices if cohort=='all' or not any(
                exposure[rows[i][field]][flag]=='True'
                for field in ('query_sequence_sha256','partner_sequence_sha256')
                for flag in ('exact_TRAIN_endpoint','exact_DEV_endpoint'))]
            ps=[i for i in selected if rows[i]['label']=='P']
            us=[i for i in selected if rows[i]['label']=='U']
            if not ps or not us:
                require(all((cohort,m,pid) not in measured for m in MODELS),'Unevaluable panel reported')
                continue
            require(len(ps)==1,'Expected exactly one P')
            for m in MODELS:
                score=lambda i: float(score_tables[m][i][m+'_score'])
                p=score(ps[0])
                u=[score(i) for i in us]
                wins=sum(p>s for s in u)
                ties=sum(p==s for s in u)
                losses=len(u)-wins-ties
                ranks=list(range(losses+1,losses+ties+2))
                values={'P_vs_U_concordance':(wins+.5*ties)/len(u),
                    'average_precision':1/max(ranks),
                    'reciprocal_rank':sum(1/r for r in ranks)/len(ranks),
                    'first_positive_rank_expected':sum(ranks)/len(ranks)}
                for k in (5,10,20):
                    if k<=1+len(u):
                        values['recall_at_'+str(k)]=sum(r<=k for r in ranks)/len(ranks)
                if len(u)+1>=10:
                    values['NDCG_at_10']=sum(1/math.log2(r+1) if r<=10 else 0 for r in ranks)/len(ranks)
                truth=[1]+[0]*len(u)
                check(values['P_vs_U_concordance'],roc_auc_score(truth,[p]+u),'Concordance/library mismatch')
                check(values['average_precision'],average_precision_score(truth,[p]+u),'AP/library mismatch')
                r=measured[cohort,m,pid]
                require(int(r['P'])==1 and int(r['U'])==len(u),'Wrong evaluated label counts')
                for k,v in values.items():
                    check(r[k],v,'Per-positive metric mismatch: '+k)
                oracle[cohort,m,pid]={'target':rows[ps[0]]['target_id'],'U':len(u),**values}
    require(set(oracle)==set(measured),'Different evaluated panel set')
    saved=table(OUT/'metrics.csv')
    lookup={(r['cohort'],r['aggregation'],r['model'],r['metric']):r for r in saved}
    boot=np.load(LOCAL/'bootstrap_draws.npz',allow_pickle=False)
    oracle_draws={}
    for cohort in ('all','no_exact_TRAIN_DEV_endpoint'):
        for k in KEYS:
            values={m:[v for (c,mm,pid),v in oracle.items() if c==cohort and mm==m and k in v] for m in MODELS}
            targets=sorted({v['target'] for v in values[MODELS[0]]})
            index={t:i for i,t in enumerate(targets)}
            counts=np.zeros(len(targets),dtype=np.int64)
            for v in values[MODELS[0]]:
                counts[index[v['target']]]+=1
            # Multinomial multiplicities reconstructed from the documented index draws.
            draw=np.random.default_rng(CONFIG['seed']).integers(0,len(targets),size=(CONFIG['bootstrap_draws'],len(targets)))
            weights=np.zeros((len(draw),len(targets)),dtype=np.int32)
            np.add.at(weights,(np.arange(len(draw))[:,None],draw),1)
            for m in MODELS:
                sums=np.zeros(len(targets),dtype=np.float64)
                for v in values[m]:
                    sums[index[v['target']]]+=v[k]
                for aggregation in ('equal_positive','equal_yeast_target'):
                    if aggregation=='equal_positive':
                        point=sum(v[k] for v in values[m])/len(values[m])
                        distribution=(weights@sums)/(weights@counts)
                    else:
                        means=sums/counts
                        point=sum(means)/len(means)
                        distribution=(weights@means)/len(targets)
                    key=(cohort,aggregation,m,k)
                    reported=lookup[key]
                    check(reported['estimate'],point,'Macro estimate mismatch')
                    lo,hi=np.quantile(distribution,[.025,.975])
                    check(reported['ci_low'],lo,'Interval low mismatch')
                    check(reported['ci_high'],hi,'Interval high mismatch')
                    stored=boot['__'.join(key)]
                    require(stored.shape==distribution.shape,'Bootstrap draw count mismatch')
                    check(float(np.max(np.abs(stored-distribution))),0,'Bootstrap sample mismatch')
                    require(int(reported['panels'])==len(values[m]) and int(reported['targets'])==len(targets),'Macro cohort counts mismatch')
                    oracle_draws[key]=distribution
    for r in table(OUT/'paired_differences.csv'):
        a=(r['cohort'],r['aggregation'],r['model_a'],r['metric'])
        b=(r['cohort'],r['aggregation'],r['model_b'],r['metric'])
        check(r['difference_b_minus_a'],float(lookup[b]['estimate'])-float(lookup[a]['estimate']),'Paired point mismatch')
        lo,hi=np.quantile(oracle_draws[b]-oracle_draws[a],[.025,.975])
        check(r['ci_low'],lo,'Paired interval low mismatch')
        check(r['ci_high'],hi,'Paired interval high mismatch')
    ipin,tuna=read(OUT/'IPIN_RUN.json'),read(OUT/'TUNA_RUN.json')
    require(ipin['pair_order_symmetry_passed'],'iPIN symmetry failed')
    require(len(tuna['native_qualification'])==3 and all(
        r['parameters_and_buffers_unchanged'] and r['pair_order_symmetry_passed'] and r['native_max_absolute_error']<=r['tolerance']
        for r in tuna['native_qualification']),'TUnA qualification failed')
    check_records(ipin['verified_model_inputs']+tuna['verified_model_inputs'])
    write_json(OUT/'RESULT_VALIDATION.json',{'at_utc':now(),'status':'passed','analysis':record(OUT/'ANALYSIS.json'),
        'panel_validation':record(OUT/'PANEL_VALIDATION.json'),'scalar_metric_checks':checks,
        'maximum_metric_error':maximum,'validated_per_positive_model_rows':len(oracle),
        'validated_bootstrap_series':len(oracle_draws),'draws_per_series':CONFIG['bootstrap_draws'],
        'independent_oracles':['sklearn AUROC/AP','explicit possible ranks','multinomial target-weight bootstrap'],
        'all_original_P_retained':True,'U_per_P':100,'unique_U':155500,'model_identity_and_symmetry_passed':True,
        'validator':record(Path(__file__))})
    print('Independent result validation passed; maximum metric error',maximum,flush=True)


if __name__=='__main__':
    main()
