"""Independent artifact-level leakage, nesting and preservation checks."""
from pathlib import Path
import argparse
from collections import defaultdict
import numpy as np
from study import arrays, check, codes, now, read, save, sha, write

def main():
    p=argparse.ArgumentParser(); p.add_argument('--study',type=Path,required=True)
    p.add_argument('--repo',type=Path,required=True); args=p.parse_args(); root=args.study
    freeze=read(root/'audit/CORPUS_FREEZE.json')
    for item in freeze['data_files']+freeze['test_files']:
        check(sha(root/item['path'])==item['sha256'], 'Corpus checksum mismatch: '+item['path'])
    for item in read(root/'audit/PARENT_SNAPSHOT.json')['files']:
        check(sha(args.repo/item['path'])==item['sha256'], 'Historical parent changed')
    seq=read(root/'data/sequences.json'); n=len(seq['sha256']); part=np.array(seq['partition'])
    groups=defaultdict(set)
    for comp,fold in zip(seq['extended_component'],part,strict=True): groups[comp].add(fold)
    check(all(len(x)==1 for x in groups.values()), 'Accepted extended component crosses partitions')
    old=arrays(root/'data/legacy/training.npz'); controls=arrays(root/'data/training_16799.npz')
    check(np.array_equal(old['p_a'],controls['p_a']) and np.array_equal(old['p_b'],controls['p_b']), 'Control positives differ from parent')
    dev=[]; test=[]; overlap={}; panels={}
    for fold,directory,target in [('development',root/'data/development',dev),('test',root/'private/test',test)]:
        for cell in ['C1','C2','C3']:
            for cohort in ['reconciled','added']:
                a=arrays(directory/cohort/f'{cell}.npz'); k=codes(a['a'],a['b'],n)
                check(len(np.unique(k))==len(k) and (a['a']!=a['b']).all(), 'Duplicate/self panel pair')
                check(np.isfinite(a['weight']).all() and (a['weight']>0).all(), 'Invalid panel weight')
                if cell=='C3': check(np.all(part[a['a']]==fold) and np.all(part[a['b']]==fold), 'C3 endpoint error')
                if cell=='C2': check(np.all(((part[a['a']]=='train') & (part[a['b']]==fold)) | ((part[a['b']]=='train') & (part[a['a']]==fold))), 'C2 endpoint error')
                if cell=='C1': check(np.all(part[a['a']]=='train') and np.all(part[a['b']]=='train'), 'C1 endpoint error')
                target.append(k); panels[(fold,cell,cohort)]=(k,a['positive'])
                if fold=='test':
                    # No labels or weights in the scoring input.
                    cohort_name='legacy' if cohort=='reconciled' else cohort
                    save(root/f'private/candidates/{cohort_name}_{cell}.npz',a=a['a'],b=a['b'])
    dev_all=np.concatenate(dev); test_all=np.concatenate(test)
    for cell in ['C1','C2','C3']:
        dk,dp=panels[('development',cell,'reconciled')]; tk,tp=panels[('test',cell,'reconciled')]
        overlap[cell]={'legacy_candidate_overlap':len(np.intersect1d(dk,tk)),
                       'reconciled_positive_overlap':len(np.intersect1d(dk[dp],tk[tp]))}
    check(overlap['C2']['legacy_candidate_overlap']==overlap['C3']['legacy_candidate_overlap']==0, 'Unexpected C2/C3 old overlap')
    added=np.concatenate([v[0] for k,v in panels.items() if k[2]=='added'])
    oldkeys=np.concatenate([v[0] for k,v in panels.items() if k[2]=='reconciled'])
    check(len(np.unique(added))==len(added) and not len(np.intersect1d(added,oldkeys)), 'New holdout overlap')
    holdout=np.unique(np.r_[dev_all,test_all]); u=arrays(root/'data/training_unlabeled.npz')
    uk=codes(u['u_a'],u['u_b'],n)
    check(len(np.unique(uk))==len(uk) and not len(np.intersect1d(uk,holdout)), 'Training U overlaps holdout')
    prior=np.empty(0,np.int64)
    for budget in read(root/'data/PROTOCOL.json')['positive_budgets']:
        a=arrays(root/f'data/training_{budget}.npz'); pk=codes(a['p_a'],a['p_b'],n)
        check(len(pk)==budget and len(np.unique(pk))==budget, 'Training P census/duplicate error')
        check(np.all(np.isin(prior,pk)), 'Budget nesting failed')
        check(not len(np.intersect1d(pk,holdout)) and not len(np.intersect1d(pk,uk)), 'Training P overlaps holdout/U')
        check(np.all(part[a['p_a']]=='train') and np.all(part[a['p_b']]=='train'), 'Non-TRAIN P endpoint')
        prior=pk
    report={'at_utc':now(),'passed':True,'corpus_freeze_sha256':sha(root/'audit/CORPUS_FREEZE.json'),
      'parent_checksums_verified':True,'positive_nesting_verified':True,
      'all_training_pairs_disjoint_from_all_holdout_candidates':True,
      'all_added_holdout_candidates_disjoint':True,'accepted_component_partitions_disjoint':True,
      'inherited_legacy_overlap':overlap,
      'interpretation':'C1 legacy U sampling overlaps dev/test. Version-2 reconciliation can make shared rows P. Preserve requested old panels; disclose inherited overlap. C3 is unaffected; test-2 is historical follow-up.',
      'test_truth_read_by_curator_only':True}
    write(root/'audit/CORPUS_VALIDATION.json',report)
    print(report,flush=True)

if __name__=='__main__': main()
