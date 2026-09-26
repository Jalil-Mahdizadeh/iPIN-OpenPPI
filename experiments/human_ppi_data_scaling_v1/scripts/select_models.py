"""Choose epochs and corpus size exclusively from the frozen C3 development rule."""
from pathlib import Path
import numpy as np
from common import concordance
from train_curve import verify_execution
from study import arrays, check, now, read, record, sha, write

def main():
    identity=verify_execution(); p=read('/data/PROTOCOL.json')
    check(not Path('/output/SELECTION.json').exists(), 'Selection already frozen')
    legacy=arrays('/data/legacy/development_00.npz')
    reconciled=arrays('/data/development/reconciled/C3.npz'); added=arrays('/data/development/added/C3.npz')
    curve=[]; chosen=[]
    for budget in p['positive_budgets']:
        candidates=[]
        for seed in p['seeds']:
            complete=read(f'/output/training/budget_{budget}/seed_{seed}/COMPLETE.json')
            check(complete['execution_sha256']==identity, 'Fit execution mismatch')
        for epoch in p['evaluation_epochs']:
            old=[]; new=[]; members=[]; seed_metrics=[]
            for seed in p['seeds']:
                root=Path(f'/output/training/budget_{budget}/seed_{seed}')
                meta=read(root/f'epoch_{epoch:02d}.json')
                checkpoint=root/f'epoch_{epoch:02d}.pt'; prediction=root/f'epoch_{epoch:02d}_C3.npz'
                check(sha(checkpoint)==meta['checkpoint']['sha256'] and sha(prediction)==meta['prediction']['sha256'], 'Checkpoint/prediction changed')
                a=arrays(prediction); old.append(a['legacy'].astype(np.float64)); new.append(a['added'].astype(np.float64))
                members.append({'seed':seed,'checkpoint':record(checkpoint,Path('/output'))})
                seed_metrics.append(meta['metrics'])
            s1=np.mean(old,axis=0); sa=np.mean(new,axis=0)
            metrics={'dev_1':concordance(s1,legacy['positive'],legacy['weight']),
                     'dev_1_reconciled':concordance(s1,reconciled['positive'],reconciled['weight']),
                     'dev_added':concordance(sa,added['positive'],added['weight'])}
            metrics['dev_2_macro']=.5*(metrics['dev_1_reconciled']+metrics['dev_added'])
            row={'budget':budget,'epoch':epoch,'metrics':metrics,'seed_metrics':seed_metrics,'members':members}
            candidates.append(row); curve.append(row)
        chosen.append(sorted(candidates,key=lambda x:(-x['metrics']['dev_2_macro'],x['epoch']))[0])
    best=sorted(chosen,key=lambda x:(-x['metrics']['dev_2_macro'],x['budget'],x['epoch']))[0]
    write('/output/SELECTION.json',{'at_utc':now(),'execution_sha256':identity,
       'selection_rule':p['selection'],'tie_break':p['tie_break'],'all_epoch_points':curve,
       'best_per_budget':chosen,'selected':best,'fresh_control':next(x for x in chosen if x['budget']==16799),
       'test_pairs_read':False,'test_truth_read':False})
    print({'selected_budget':best['budget'],'selected_epoch':best['epoch'],'metrics':best['metrics']},flush=True)

if __name__=='__main__': main()
