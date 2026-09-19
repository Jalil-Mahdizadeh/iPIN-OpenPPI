#!/usr/bin/env python3
"""Development-only ensemble selection, then immutable sequence-only scorer bundle."""
from pathlib import Path
import shutil
import numpy as np
import torch
from adapter import cached_scores, create, enable_sdpa, load_original
from benchmark_metrics import qualify as qualify_metrics
from common import SEEDS, arrays, concordance, cuda, now, read, record, sha, write
from frozen_scorer import MEMBERS, SCORERS, Scorer
from residues import Residues

CODE=('common.py','frozen_scorer.py','benchmark_metrics.py','comparison.py','gpu_guard.py')

def main():
    output=Path('/output'); frozen=output/'TRAINING_FREEZE.json'; recipe=read(frozen)
    device=cuda()
    if not read(output/'GUARDED_QUALIFICATION.json')['passed'] or not read(output/'GPU_GUARD.json')['gpu_forward_backward_passed']:
        raise RuntimeError('Qualified GPU execution required before scorer freeze')
    data=arrays('/data/development_00.npz')
    candidates=[]
    for epoch in recipe['evaluation_epochs']:
        scores=[]; records=[]
        for seed in SEEDS:
            root=output/'training'/f'seed_{seed}'
            if read(root/'COMPLETE.json')['protocol_sha256']!=sha(frozen):
                raise RuntimeError('Missing complete frozen training seed')
            info=read(root/f'epoch_{epoch:02d}.json')
            for kind in ('checkpoint','development_predictions'):
                path=root/Path(info[kind]['path']).name
                if sha(path)!=info[kind]['sha256']:
                    raise RuntimeError('Development/checkpoint identity changed')
            scores.append(np.load(root/f'epoch_{epoch:02d}_C3_development.npy',allow_pickle=False))
            records.append(info)
        ensemble=np.column_stack(scores).mean(1,dtype=np.float64)
        candidates.append({'epoch':epoch,'C3_development_concordance':concordance(ensemble,data['positive'],data['weight']),'members':records})
    candidates.sort(key=lambda x:(-x['C3_development_concordance'],x['epoch']))
    selected=candidates[0]
    bundle=output/'scorer_bundle'
    bundle.mkdir(exist_ok=False)
    for folder in ('weights','features','code','provenance'):
        (bundle/folder).mkdir()
    selection={'at_utc':now(),'training_freeze_sha256':sha(frozen),'selected_epoch':selected['epoch'],
        'candidates':candidates,'test_pairs_read':False,'test_truth_read':False,'all_three_seeds_retained':True}
    write(bundle/'SELECTION.json',selection,exclusive=True)
    cache=Residues('/data',output/'residue_cache/residues.h5',device)
    model_references=[]
    for index,name in enumerate(MEMBERS):
        if index==0:
            model=load_original('/weights/bernett_original.pt',device)
        else:
            checkpoint=output/'training'/f'seed_{SEEDS[index-1]}'/f'epoch_{selected["epoch"]:02d}.pt'
            model=create(seed=SEEDS[index-1],checkpoint=checkpoint,device=device)
            model.gp_layer.fitted=True  # Retain the frozen PU covariance, do not refit it.
            model.eval()
        enable_sdpa(model)
        z=cache.features(model)
        with (bundle/'features'/f'{name}.npy').open('xb') as f:
            np.save(f,z.cpu().numpy(),allow_pickle=False)
        torch.save(model.state_dict(),bundle/'weights'/f'{name}.pt')
        # Test the minimal frozen scorer against the qualified adapter before
        # any final-test candidate is opened. Fixed TRAIN fixtures only.
        permitted=np.flatnonzero(np.asarray(cache.meta['partition'])=='train')
        a=permitted[:97]; b=permitted[97:194]
        model_references.append(cached_scores(model,z,a,b,probabilities=(index==0)))
        del model,z
        torch.cuda.empty_cache()
    scorer=Scorer(bundle,device)
    minimal=scorer.scores(a,b)
    columns=[0,2,3,4]
    errors=[float(np.max(np.abs(minimal[:,j]-reference))) for j,reference in zip(columns,model_references)]
    if max(errors)>1e-5 or not np.array_equal(minimal[:,1],minimal[:,2:].mean(1,dtype=np.float64)):
        raise RuntimeError('Minimal frozen scorer qualification failed')
    write(bundle/'FROZEN_SCORER_QUALIFICATION.json',{'passed':True,'errors':errors,'absolute_tolerance':1e-5,
        'fixtures':'97 fixed TRAIN pairs','bootstrap':qualify_metrics(device)},exclusive=True)
    write(bundle/'endpoints.json',cache.meta['sha256'],exclusive=True)
    write(bundle/'components.json',cache.meta['component'],exclusive=True)
    for name in CODE:
        shutil.copyfile(Path('/code')/name,bundle/'code'/name)
    for name in ['TRAINING_FREEZE.json','QUALIFICATION.json','REAL_QUALIFICATION.json','GPU_GUARD.json','GUARDED_QUALIFICATION.json','PILOT.json']:
        shutil.copyfile(output/name,bundle/'provenance'/name)
    files=[]
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            item=record(path); item['path']=str(path.relative_to(bundle)); files.append(item)
    write(bundle/'SCORER_FREEZE.json',{'at_utc':now(),'execution_id':'tuna_pu_benchmark_v1',
        'sif_sha256':'98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1',
        'training_freeze_sha256':sha(frozen),'selected_epoch':selected['epoch'],'scorers':list(SCORERS),
        'files':files,'test_pairs_read':False,'test_truth_read':False,
        'original_runtime_state_note':'Released state loaded without training; native eval recomputes GP covariance from its released precision. All trained parameters remain the authors weights.',
        'original_checkpoint_sha256':recipe['original_checkpoint']['sha256']},exclusive=True)
    print({'selected_epoch':selected['epoch'],'C3_development_concordance':selected['C3_development_concordance'],
        'scorer_freeze_sha256':sha(bundle/'SCORER_FREEZE.json')},flush=True)

if __name__=='__main__':
    main()
