"""Exploratory C3 cohort intervals after observing opposite cohort rankings."""
from pathlib import Path
import numpy as np
from io_utils import ROOT,MODELS,arrays,atomic,cuda,now,read,record,sha,verify
from benchmark_metrics import bootstrap

def main():
    device=cuda();out=ROOT/'results';freeze=read(out/'PREDICTION_FREEZE.json')
    for item in freeze['files']:verify(ROOT/item['path'],item)
    meta=read(ROOT/'data/sequences.json');components=np.array(meta['extended_component'])
    flags=arrays(ROOT/'exposure/unique_pairs.npz')['normalized'];names=['selected_31k']+list(MODELS)
    output={}
    for cohort,truth_dir in [('legacy','reconciled'),('added','added')]:
        truth=arrays(Path('/truth')/truth_dir/'C3.npz');candidate=arrays(ROOT/f'data/candidates/{cohort}_C3.npz')
        assert np.array_equal(truth['a'],candidate['a']) and np.array_equal(truth['b'],candidate['b'])
        old=arrays(Path('/reference/results/predictions')/f'{cohort}_C3.npz')
        new=arrays(out/f'predictions/{cohort}_C3.npz');index=arrays(ROOT/f'data/candidates/map_{cohort}_C3.npz')['index']
        scores=np.column_stack([old['selected_31k']]+[new[m] for m in MODELS])
        for tag,keep in [('full',np.ones(len(index),bool)),('no_XPAIR_pair_exposure',flags[index]==0)]:
            key=f'C3_{cohort}_{tag}_exploratory'
            points,draws,metadata=bootstrap(scores[keep],truth['positive'][keep],truth['weight'][keep],
                components[truth['a'][keep]].tolist(),components[truth['b'][keep]].tolist(),key,2000,device)
            values={name:{'PU_concordance':float(points[j]),'ci95':np.quantile(draws[j],[.025,.975]).tolist()}
                    for j,name in enumerate(names)}
            contrasts={name:{'XPAIR_minus_selected_31k':float(points[j]-points[0]),
                'paired_ci95':np.quantile(draws[j]-draws[0],[.025,.975]).tolist()} for j,name in enumerate(names) if j}
            output[key]={'models':values,'contrasts':contrasts,'bootstrap':metadata,
                         'P':int(truth['positive'][keep].sum()),'U':int((~truth['positive'][keep]).sum())}
            with (out/f'bootstrap_{key}.npz').open('wb') as stream:np.savez(stream,points=points,draws=draws)
            print({'panel':key,'contrasts':contrasts},flush=True)
    atomic(out/'C3_COHORT_EXPLORATORY.json',{'at_utc':now(),'exploratory_after_primary_results':True,
           'reason':'Investigate opposite rankings in legacy and added C3; no model selection or score changes',
           'panels':output,'prediction_freeze_sha256':sha(out/'PREDICTION_FREEZE.json'),
           'script':record(ROOT/'scripts/cohort_detail.py'),
           'intervals':'Pointwise paired component bootstrap, 2000 draws; not multiplicity-adjusted'})

if __name__=='__main__':main()
