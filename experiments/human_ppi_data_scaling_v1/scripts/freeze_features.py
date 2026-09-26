"""Freeze selected weights and full-length endpoint features before test scoring."""
from pathlib import Path
import shutil
import numpy as np
import torch
from common import cuda
from residues import Residues
from training import make_model
from study import SEEDS, check, now, read, record, sha, write

def main():
    selection=read('/output/SELECTION.json')
    check(not Path('/output/SCORER_FREEZE.json').exists(), 'Scorers already frozen')
    device=cuda(); cache=Residues('/data','/output/residue_cache/residues.h5',device)
    root=Path('/output/frozen'); root.mkdir(exist_ok=True)
    members=[]
    def store_member(name,source,seed,old=False):
        dest=root/(name+'.pt'); feature=root/(name+'.npy')
        check(not dest.exists() and not feature.exists(), 'Frozen member already exists')
        model=make_model(seed,device)
        model.load_state_dict(torch.load(source,map_location=device,weights_only=True),strict=True)
        model.eval(); model.gp_layer.fitted=True
        if old:
            z=cache.features(model,indices=range(17000,len(cache.meta['sha256'])))
            parent=np.load(f'/old_models/features/tuna_retrained_seed{seed}.npy',allow_pickle=False)
            z[:17000]=torch.as_tensor(parent,device=device)
        else:
            z=cache.features(model)
        values=z.cpu().numpy()
        check(np.isfinite(values).all(), 'Incomplete frozen features')
        shutil.copyfile(source,dest)
        with feature.open('xb') as f: np.save(f,values,allow_pickle=False)
        members.append({'name':name,'seed':seed,'weights':record(dest,Path('/output')),'features':record(feature,Path('/output'))})
        print({'frozen_member':name},flush=True)
        del model,z
    for chosen in selection['best_per_budget']:
        for member in chosen['members']:
            source=Path('/output')/member['checkpoint']['path']
            check(sha(source)==member['checkpoint']['sha256'], 'Selected state changed')
            store_member(f"scaled_{chosen['budget']}_seed{member['seed']}",source,member['seed'])
    registry=read('/old_models/MODEL_REGISTRY.json')
    for item in registry['bundle_files']:
        if item['path'].startswith(('weights/','features/')):
            check(sha(Path('/old_models')/item['path'])==item['sha256'], 'Frozen baseline changed')
    # The source registry is also preserved in the execution freeze; each exact
    # baseline state and vector gets a fresh content record in the scorer freeze.
    for seed in SEEDS:
        store_member(f'baseline_seed{seed}',Path(f'/old_models/weights/tuna_retrained_seed{seed}.pt'),seed,old=True)
    write('/output/SCORER_FREEZE.json',{'at_utc':now(),'selection_sha256':sha('/output/SELECTION.json'),
      'execution_sha256':selection['execution_sha256'],'members':members,
      'baseline_registry_sha256':sha('/old_models/MODEL_REGISTRY.json'),
      'pooled_feature_manifest_sha256':sha('/output/POOLED_FEATURE_MANIFEST.json'),
      'test_pairs_read':False,'test_truth_read':False})

if __name__=='__main__': main()
