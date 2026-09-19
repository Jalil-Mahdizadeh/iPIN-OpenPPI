"""Choose one shared epoch using C3-DEV, then freeze a sequence-only scorer."""
from pathlib import Path
import shutil
import numpy as np
import torch
from common import SEEDS,arrays,concordance,cuda,read,write,record,sha,now
from model import Residues,fresh,contact_logit
from frozen_scorer import MEMBERS,SCORERS,Scorer
from native_adapter import learned_digest
from benchmark_metrics import qualify


def main():
    output=Path('/output');recipe=read('/protocol.json');protocol_sha=sha('/protocol.json')
    for item in recipe['code_files']:assert sha(Path('/code')/item['path'])==item['sha256']
    assert sha('/data/DATA_MANIFEST.json')==recipe['data_manifest_sha256']
    data=arrays('/data/development_00.npz');meta=read('/data/sequences.json');candidates=[]
    for epoch in recipe['evaluation_epochs']:
        vectors=[];members=[]
        for seed in SEEDS:
            root=Path('/training')/f'seed_{seed}'
            assert read(root/'COMPLETE.json')['protocol_sha256']==protocol_sha
            info=read(root/f'epoch_{epoch:02d}.json');assert info['protocol_sha256']==protocol_sha
            for key in ('checkpoint','development_predictions'):
                assert sha(root/Path(info[key]['path']).name)==info[key]['sha256']
            vectors.append(np.load(root/f'epoch_{epoch:02d}_C3_development.npy',allow_pickle=False));members.append(info)
        mean=np.column_stack(vectors).mean(1,dtype=np.float64)
        candidates.append({'epoch':epoch,'C3_development_concordance':concordance(mean,data['positive'],data['weight']),'members':members})
    selected=sorted(candidates,key=lambda x:(-x['C3_development_concordance'],x['epoch']))[0]
    bundle=output/'scorer_bundle';bundle.mkdir(exist_ok=False)
    for name in ('weights','features','code','provenance'):(bundle/name).mkdir()
    write(bundle/'SELECTION.json',{'at_utc':now(),'training_freeze_sha256':protocol_sha,'selected_epoch':selected['epoch'],
          'candidates':candidates,'all_three_seeds_retained':True,'test_pairs_read':False,'test_truth_read':False},exclusive=True)
    device=cuda();cache=Residues('/cache',device);digests={};references=[]
    train_ids=np.flatnonzero(np.asarray(meta['partition'])=='train');a=train_ids[:16];b=train_ids[16:32]
    offsets=np.concatenate(([0],np.cumsum(meta['length'],dtype=np.int64)))
    with (bundle/'features/offsets.npy').open('xb') as handle:np.save(handle,offsets,allow_pickle=False)
    for seed,name in zip(SEEDS,MEMBERS,strict=True):
        checkpoint=Path('/training')/f'seed_{seed}'/f'epoch_{selected["epoch"]:02d}.pt'
        model=fresh(seed,device).eval();model.load_state_dict(torch.load(checkpoint,map_location=device,weights_only=True),strict=True)
        model.requires_grad_(False);digests[name]=learned_digest(model)
        shutil.copyfile(checkpoint,bundle/'weights'/f'{name}.pt')
        projected=np.lib.format.open_memmap(bundle/'features'/f'{name}.npy',mode='w+',dtype=np.float32,shape=(int(offsets[-1]),100))
        with torch.inference_mode():
            for i in range(len(meta['length'])):
                projected[offsets[i]:offsets[i+1]]=model.embedding(cache.full(i))[0].cpu().numpy()
                if (i+1)%1000==0:print({'member':name,'projected':i+1,'total':17000},flush=True)
            references.append(np.asarray([float(contact_logit(model,cache.full(x),cache.full(y))[1]) for x,y in zip(a,b,strict=True)]))
        projected.flush();del projected,model;torch.cuda.empty_cache()
    for name,key in [('endpoints.json','sha256'),('components.json','component'),('lengths.json','length')]:
        write(bundle/name,meta[key],exclusive=True)
    scorer=Scorer(bundle,device,config={'learned_state_sha256':digests})
    actual=scorer.scores(a,b);errors=[float(np.max(np.abs(actual[:,j+1]-reference))) for j,reference in enumerate(references)]
    assert max(errors)<=recipe['logit_tolerance'] and np.array_equal(actual[:,0],actual[:,1:].mean(1,dtype=np.float64))
    write(bundle/'provenance/FROZEN_SCORER_QUALIFICATION.json',{'passed':True,'fixture_pairs':16,'maximum_errors':errors,
          'tolerance':recipe['logit_tolerance'],'fixtures':'Fixed TRAIN endpoints; raw versus projected-cache scoring',
          'test_pairs_read':False,'test_truth_read':False,'metric_qualification':qualify(device)},exclusive=True)
    for name in ('common.py','model.py','native_adapter.py','frozen_scorer.py','comparison.py','score_shard.py','benchmark_metrics.py','gpu_guard.py'):
        shutil.copyfile(Path('/code')/name,bundle/'code'/name)
    shutil.copyfile('/protocol.json',bundle/'provenance/TRAINING_FREEZE.json')
    files=[]
    for path in sorted(bundle.rglob('*')):
        if path.is_file():item=record(path);item['path']=str(path.relative_to(bundle));files.append(item)
    write(bundle/'SCORER_FREEZE.json',{'at_utc':now(),'execution_id':'dscript_retrained_benchmark_v1','scorers':list(SCORERS),
          'files':files,'training_freeze_sha256':protocol_sha,'selected_epoch':selected['epoch'],'learned_state_sha256':digests,
          'workers':4,'maximum_length':7570,'tile_area':1_000_000,'logit_tolerance':recipe['logit_tolerance'],
          'score':'Three-seed arithmetic mean of native pre-sigmoid logits; not calibrated interaction probability',
          'test_pairs_read':False,'test_truth_read':False,'original_predictions_manifest_sha256':recipe['original_predictions_manifest_sha256'],
          'original_results_sha256':recipe['original_results_sha256'],'sif_sha256':recipe['sif_sha256']},exclusive=True)
    print({'selected_epoch':selected['epoch'],'C3_development_concordance':selected['C3_development_concordance'],
           'scorer_freeze_sha256':sha(bundle/'SCORER_FREEZE.json')},flush=True)


if __name__=='__main__':main()
