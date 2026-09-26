"""Evaluate frozen predictions; report historical and expanded panels separately."""
from pathlib import Path
import csv
import numpy as np
from benchmark_metrics import bootstrap
from common import concordance, cuda
from macro_metrics import macro_bootstrap
from study import arrays, check, codes, now, read, record, sha, write

SCORERS=['selected','fresh_control','ipin_tuna_frozen','ipin_optimized','ipin_original']
HISTORICAL={
 'C1':[.9486194208587495,.9160374988139083,.8434933190102009],
 'C2':[.8804013010037104,.85130120194772,.8052990558636478],
 'C3':[.8158745071491785,.8079478806256634,.7892487658713853]}

def summary(points,draws,metadata):
    estimates={}; differences={}
    for i,name in enumerate(SCORERS):
        finite=draws[i,np.isfinite(draws[i])]
        estimates[name]={'PU_concordance':float(points[i]),'component_bootstrap_ci95':np.quantile(finite,[.025,.975]).tolist(),
                         'finite_replicates':len(finite)}
        if i:
            d=draws[0]-draws[i]; d=d[np.isfinite(d)]
            differences[name]={'selected_minus_reference':float(points[0]-points[i]),'paired_ci95':np.quantile(d,[.025,.975]).tolist(),
                               'finite_replicates':len(d)}
    return {'models':estimates,'paired_differences':differences,'bootstrap':metadata}

def main():
    frozen=read('/output/PREDICTION_FREEZE.json')
    check(frozen['complete_finite_candidate_coverage'] and not frozen['test_truth_read'], 'Invalid prediction freeze')
    check(frozen['selection_sha256']==sha('/output/SELECTION.json') and frozen['scorer_freeze_sha256']==sha('/output/SCORER_FREEZE.json'), 'Selection/scorer changed')
    for item in frozen['files']:
        check(sha(Path('/output')/item['prediction']['path'])==item['prediction']['sha256'], 'Prediction changed after freeze')
    for item in read('/freeze/CORPUS_FREEZE.json')['test_files']:
        local=Path('/truth')/Path(item['path']).relative_to('private/test')
        check(sha(local)==item['sha256'], 'Frozen test state changed')
    out=Path('/output/results'); out.mkdir(exist_ok=True)
    write(out/'EVALUATION_RESERVATION.json',{'at_utc':now(),'prediction_freeze_sha256':sha('/output/PREDICTION_FREEZE.json'),
       'historical_ledgers_modified':False,'no_test_guided_refitting':True})
    device=cuda(); meta=read('/data/sequences.json'); selection=read('/output/SELECTION.json')
    old_components=np.array(meta['component']); expanded_components=np.array(meta['extended_component'])
    results={}; development={}
    for cell in ('C1','C2','C3'):
        predictions={cohort:arrays(f'/output/predictions/test_{cohort}_{cell}.npz') for cohort in ('legacy','added')}
        old=arrays(f'/truth/legacy/{cell}.npz'); reconciled=arrays(f'/truth/reconciled/{cell}.npz'); added=arrays(f'/truth/added/{cell}.npz')
        sm_old=np.column_stack([predictions['legacy'][x] for x in SCORERS]); sm_added=np.column_stack([predictions['added'][x] for x in SCORERS])
        for view,data,scores,comp in [('test_1',old,sm_old,old_components),('test_1_reconciled',reconciled,sm_old,expanded_components),('test_added',added,sm_added,expanded_components)]:
            check(len(scores)==len(data['a']), 'Prediction/test row mismatch')
            points,draws,metadata=bootstrap(scores,data['positive'],data['weight'],comp[data['a']].tolist(),comp[data['b']].tolist(),
                                           cell+'_test' if view=='test_1' else cell+'_'+view,device=device)
            if view=='test_1':
                check(np.max(np.abs(points[2:]-HISTORICAL[cell]))<=1e-6, 'Frozen baseline does not reproduce historical panel')
            results[cell+':'+view]=summary(points,draws,metadata)
            with (out/f'bootstrap_{cell}_{view}.npz').open('xb') as f: np.savez(f,points=points,draws=draws)
            print({'evaluated':cell+':'+view,'points':points.tolist()},flush=True)
        merged={key:np.r_[reconciled[key],added[key]] for key in ('a','b','positive','weight')}
        scores=np.concatenate([sm_old,sm_added]); cohort=np.r_[np.zeros(len(sm_old),int),np.ones(len(sm_added),int)]
        points,draws,metadata=macro_bootstrap(scores,merged['positive'],merged['weight'],cohort,
           expanded_components[merged['a']].tolist(),expanded_components[merged['b']].tolist(),cell+'_test_2_macro',device=device)
        results[cell+':test_2_macro']=summary(points,draws,metadata)
        with (out/f'bootstrap_{cell}_test_2_macro.npz').open('xb') as f: np.savez(f,points=points,draws=draws)
        if cell=='C1':
            # Prespecified sensitivity view: remove every development candidate
            # identity from the retained C1 test cohort, without altering v1/v2.
            # This prevents the inherited shared-U/promoted-P rows from silently
            # driving an apparent C1 gain. C3 selection is unaffected.
            d_old=arrays('/data/legacy/development_02.npz')
            d_added=arrays('/data/development/added/C1.npz'); n=len(meta['sha256'])
            dev_codes=np.r_[codes(d_old['a'],d_old['b'],n),codes(d_added['a'],d_added['b'],n)]
            keep=~np.isin(codes(merged['a'],merged['b'],n),dev_codes)
            points,draws,metadata=macro_bootstrap(scores[keep],merged['positive'][keep],merged['weight'][keep],cohort[keep],
              expanded_components[merged['a'][keep]].tolist(),expanded_components[merged['b'][keep]].tolist(),
              'C1_test_2_macro_no_dev_overlap',device=device)
            report=summary(points,draws,metadata)
            report['excluded_shared_candidates']=int((~keep).sum())
            results['C1:test_2_macro_no_dev_overlap']=report
            with (out/'bootstrap_C1_test_2_macro_no_dev_overlap.npz').open('xb') as f: np.savez(f,points=points,draws=draws)
        d1=arrays(f'/data/legacy/development_{3-int(cell[1]):02d}.npz')
        dr=arrays(f'/data/development/reconciled/{cell}.npz'); da=arrays(f'/data/development/added/{cell}.npz')
        s1=arrays(f'/output/predictions/development_legacy_{cell}.npz'); sa=arrays(f'/output/predictions/development_added_{cell}.npz')
        development[cell]={}
        for name in s1:
            v={'dev_1':concordance(s1[name],d1['positive'],d1['weight']),
               'dev_1_reconciled':concordance(s1[name],dr['positive'],dr['weight']),
               'dev_added':concordance(sa[name],da['positive'],da['weight'])}
            v['dev_2_macro']=.5*(v['dev_1_reconciled']+v['dev_added']); development[cell][name]=v
    result={'at_utc':now(),'selected_budget':selection['selected']['budget'],'selected_epoch':selection['selected']['epoch'],
       'selection_sha256':sha('/output/SELECTION.json'),'prediction_freeze_sha256':sha('/output/PREDICTION_FREEZE.json'),
       'test':results,'development':development,'learning_curve':selection['best_per_budget'],
       'metric':'weighted P-vs-U concordance; test-2 macro gives equal weight to reconciled-old and added cohorts',
       'U_is_confirmed_negative':False,'test_2_is_fresh_independent':False,
       'inherited_overlap':read('/freeze/CORPUS_VALIDATION.json')['inherited_legacy_overlap'],
       'limitations':['The corpus expansion changes source composition and protein coverage as well as size.',
                     'Fresh 17k control and all larger budgets share regenerated, positive-reconciled U.',
                     'Original C1 dev/test U identities overlap; reconciliation promotes 57 shared pairs to P.',
                     'An additional C1 test-2 view excludes every development candidate identity; the complete requested panels remain reported.',
                     'Homology separation uses the declared heuristic graph, not an exhaustive homology guarantee.',
                     'One nested corpus ordering; three fitting seeds do not measure alternative dataset-sampling uncertainty.']}
    write(out/'RESULTS.json',result)
    with (out/'metrics.csv').open('x',newline='') as f:
        w=csv.writer(f);w.writerow(['panel','model','PU_concordance','ci95_low','ci95_high'])
        for panel,data in results.items():
            for model,value in data['models'].items():w.writerow([panel,model,value['PU_concordance'],*value['component_bootstrap_ci95']])
    lines=['# Human PPI data scaling results','',f"Selected {result['selected_budget']:,} positives, epoch {result['selected_epoch']}, using the frozen C3-dev-2 macro objective.",'',
      'All numbers below are P-versus-unlabeled concordance. Test-2 is a disclosed historical follow-up, not independent replication.','',
      '| Panel | Selected | Fresh 17k control | Frozen PU-TUnA | Optimized iPIN | Original iPIN |',
      '|---|---:|---:|---:|---:|---:|']
    for panel,data in results.items(): lines.append('| '+panel+' | '+' | '.join(f"{data['models'][x]['PU_concordance']:.6f}" for x in SCORERS)+' |')
    lines+=['','Paired component-bootstrap intervals and differences are in `RESULTS.json`; point estimates and intervals are in `metrics.csv`.','',
      'Training sizes and epoch curves are in `../SELECTION.json`. Legacy panels retain their original labels; reconciled panels explicitly incorporate new positive evidence.','']
    lines.extend('- '+x for x in result['limitations'])
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    rows=selection['best_per_budget']; x=[r['budget'] for r in rows]
    for key,label in [('dev_1','Original dev-1'),('dev_1_reconciled','Reconciled original'),('dev_added','Added only'),('dev_2_macro','Dev-2 macro')]:
        axes[0].plot(x,[r['metrics'][key] for r in rows],'o-',label=label)
    axes[0].set(xlabel='Training positive pairs',ylabel='C3 P–U concordance',title='Best common epoch per budget')
    axes[0].legend(fontsize=8)
    for budget in x:
        rows=[r for r in selection['all_epoch_points'] if r['budget']==budget]
        axes[1].plot([r['epoch'] for r in rows],[r['metrics']['dev_2_macro'] for r in rows],'o-',label=f'{budget:,} P')
    axes[1].set(xlabel='Epoch',ylabel='C3 dev-2 macro concordance',title='Three-seed ensemble learning curves')
    axes[1].legend(fontsize=8)
    for suffix in ('png','pdf','svg'):fig.savefig(out/('learning_curves.'+suffix),dpi=180)
    write(out/'COMPLETE.json',{'at_utc':now(),'results':record(out/'RESULTS.json'),
        'historical_artifacts_modified':False,'selected_on_development_only':True})

if __name__=='__main__': main()
