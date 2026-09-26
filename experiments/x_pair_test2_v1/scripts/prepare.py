"""Freeze sources and identity-only test candidates before any predictions."""
from pathlib import Path
import shutil
import subprocess
import numpy as np
from io_utils import ROOT, MODELS, CELLS, COHORTS, arrays, atomic, now, read, record, save, sha, verify

REPO=Path('/repo')
BASE=REPO/'experiments/test2_frozen_competitors_v1'

def main():
    if (ROOT/'PREPARED.json').exists():
        print('Preparation already complete');return
    upstream=ROOT/'sources/X-PAIR'
    commit=subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
    assert commit=='897646a4a768acd488f4163ff07dd5a1183d52b1'
    originals={x['path']:x for x in read(BASE/'INPUT_FREEZE.json')['files']}
    for p in [BASE/'INPUT_FREEZE.json', BASE/'PROTOCOL.json', BASE/'results/PREDICTION_FREEZE.json',
              BASE/'results/RESULTS.json', BASE/'results/scores.csv', BASE/'results/paired_differences.csv',
              BASE/'results/cohort_scores.csv', BASE/'scripts/evaluate.py']:
        originals[str(p.relative_to(REPO))]=record(p,REPO)
    for p in (BASE/'results/predictions').glob('*.npz'):
        originals[str(p.relative_to(REPO))]=record(p,REPO)
    for p in (BASE/'results').glob('bootstrap_*.npz'):
        originals[str(p.relative_to(REPO))]=record(p,REPO)
    for p in (REPO/'experiments/human_ppi_data_scaling_v1/scripts').glob('*.py'):
        originals[str(p.relative_to(REPO))]=record(p,REPO)
    for i,item in enumerate(originals.values()):
        verify(REPO/item['path'],item)
        if i%50==0:print({'verified_originals':i,'total':len(originals)},flush=True)
    atomic(ROOT/'INPUT_FREEZE.json',{'at_utc':now(),'files':list(originals.values()),'all_originals_verified':True})
    source_files=[record(p) for p in sorted(upstream.rglob('*')) if p.is_file() and '.git' not in p.parts]
    atomic(ROOT/'sources/XPAIR_FREEZE.json',{'commit':commit,'files':source_files,
            'models':{m:record(upstream/'pretrained_models'/f'{m}.ckpt') for m in MODELS},
            'primary':'multitask_xfair','selection':'Released default; interaction-only counterpart is prespecified secondary'})
    for name in ('sequences.json','endpoints.json'):
        shutil.copyfile(BASE/'data'/name,ROOT/'data'/name)
    sequences=read(ROOT/'data/sequences.json');n=len(sequences['sha256'])
    panels=[];all_codes=[]
    (ROOT/'data/candidates').mkdir(exist_ok=True)
    for cell in CELLS:
        for cohort in COHORTS:
            name=f'{cohort}_{cell}.npz';source=BASE/'data/candidates'/name
            shutil.copyfile(source,ROOT/'data/candidates'/name)
            values=arrays(source)
            assert set(values)=={'a','b'}
            assert np.all(values['a']!=values['b'])
            codes=np.minimum(values['a'],values['b']).astype(np.int64)*n+np.maximum(values['a'],values['b'])
            assert len(np.unique(codes))==len(codes)
            all_codes.append(codes)
            panels.append({'cohort':cohort,'cell':cell,'rows':len(codes),'candidate':record(ROOT/'data/candidates'/name)})
    unique=np.unique(np.concatenate(all_codes))
    a=unique//n;b=unique%n
    save(ROOT/'data/unique_pairs.npz',a=a,b=b)
    for panel,codes in zip(panels,all_codes):
        mapping=np.searchsorted(unique,codes)
        assert np.array_equal(unique[mapping],codes)
        save(ROOT/'data/candidates'/f"map_{panel['cohort']}_{panel['cell']}.npz",index=mapping)
    endpoints=np.unique(np.r_[a,b]);length=np.array(sequences['length'])
    save(ROOT/'data/endpoint_ids.npz',ids=endpoints)
    # Length-balanced deterministic embedding work; no labels or scores involved.
    loads=np.zeros(8,dtype=np.int64);assignment=np.full(n,-1,dtype=np.int16)
    for i in endpoints[np.argsort(-length[endpoints],kind='stable')]:
        rank=int(np.argmin(loads));assignment[i]=rank;loads[rank]+=int(length[i])**2
    save(ROOT/'data/embedding_assignment.npz',rank=assignment)
    protocol={'at_utc':now(),'models':list(MODELS),'primary_model':'multitask_xfair',
        'no_training_or_model_selection':True,'native_score':'FP32 sigmoid of native interaction logit; logits also retained',
        'precision':'FP32, TF32 disabled; compared with the unchanged upstream forward function',
        'length_policy':'Upstream --seq_len all; full context; no sequence truncation',
        'metric':'0.5 design-weighted P/U concordance on reconciled legacy + 0.5 on added cohort',
        'primary_cell':'C3','cells':list(CELLS),'bootstrap_replicates':2000,
        'bootstrap':'Inherited component identities and deterministic draws; paired to selected 31k',
        'candidate_rows':sum(p['rows'] for p in panels),'unique_pairs':len(unique),'test_endpoints':len(endpoints),
        'endpoint_residues':int(length[endpoints].sum()),'minimum_length':int(length[endpoints].min()),
        'maximum_length':int(length[endpoints].max()),'endpoints_above_training_maximum_2000':int((length[endpoints]>2000).sum()),
        'panels':panels,'U_is_confirmed_negative':False,'test2_is_fresh_independent':False,
        'test_labels_mounted_for_scoring':False,'exposure':'Audit exact unordered sequence pairs in released interaction/interface train and validation; secondary exclusion views',
        'other_released_checkpoints':'Not selected or evaluated; no picking checkpoints using test2',
        'embedding_workers':8,'scoring_workers':8}
    atomic(ROOT/'PROTOCOL.json',protocol)
    atomic(ROOT/'PREPARED.json',{'at_utc':now(),'protocol_sha256':sha(ROOT/'PROTOCOL.json'),
        'inputs_sha256':sha(ROOT/'INPUT_FREEZE.json'),'source_sha256':sha(ROOT/'sources/XPAIR_FREEZE.json'),
        'files':[record(p) for p in sorted((ROOT/'data').rglob('*')) if p.is_file()]})
    print({k:v for k,v in protocol.items() if k not in ('panels',)},flush=True)

if __name__=='__main__':main()
