"""Candidate-only final scoring. Development diagnostics cannot change selection."""
from pathlib import Path
import sys
import numpy as np
import torch
from adapter import cached_scores
from common import cuda
from training import make_model
from study import SEEDS, arrays, check, now, read, record, save, sha, write

class Scores:
    def __init__(self,device):
        self.device=device; self.members={}
        frozen=read('/output/SCORER_FREEZE.json')
        for member in frozen['members']:
            for key in ('weights','features'):
                check(sha(Path('/output')/member[key]['path'])==member[key]['sha256'],'Frozen scoring artifact changed')
            model=make_model(member['seed'],device)
            model.load_state_dict(torch.load(Path('/output')/member['weights']['path'],map_location=device,weights_only=True),strict=True)
            model.eval(); model.gp_layer.fitted=True
            z=torch.from_numpy(np.load(Path('/output')/member['features']['path'],allow_pickle=False)).to(device)
            self.members[member['name']]=(model,z)
        sys.path.insert(0,'/pooled/code')
        from optimization_models_v1 import PairHead, load_state
        registry=read('/pooled/MODEL_REGISTRY.json')
        for item in registry['bundle_files']:
            if item['path'].startswith('heads/'):
                check(sha(Path('/pooled')/item['path'])==item['sha256'],'Frozen pooled head changed')
        self.z=torch.as_tensor(np.load('/output/pooled_features.npy',allow_pickle=False),device=device)
        self.optimized=[]; self.affine=[]
        for seed in SEEDS:
            model=PairHead(640,registry['optimized_recipe'])
            load_state(Path(f'/pooled/heads/optimized/{seed}.npz'),model)
            self.optimized.append(model.to(device).eval())
            a=arrays(f'/pooled/heads/affine/{seed}.npz')
            self.affine.append((torch.as_tensor(a['weight'],device=device),torch.as_tensor(a['bias'],device=device)))
    def tuna(self,prefix,a,b):
        result=[]
        for seed in SEEDS:
            model,z=self.members[prefix+f'_seed{seed}']
            result.append(cached_scores(model,z,a,b).astype(np.float64))
        return np.mean(result,axis=0)
    def pooled(self,a,b):
        from optimization_models_v1 import features
        original=np.empty((len(a),3),np.float64); optimized=np.empty_like(original)
        with torch.inference_mode():
            for start in range(0,len(a),8192):
                stop=min(start+8192,len(a)); x=self.z[a[start:stop]]; y=self.z[b[start:stop]]
                f=features(x,y)
                for j,(weight,bias) in enumerate(self.affine):
                    original[start:stop,j]=torch.nn.functional.linear(f,weight,bias).reshape(-1).cpu().numpy()
                    optimized[start:stop,j]=self.optimized[j](x,y).cpu().numpy()
        return {'ipin_original':original.mean(1),'ipin_optimized':optimized.mean(1)}
    def all(self,a,b,selected,control,extra=()):
        values={f'budget_{budget}':self.tuna(f'scaled_{budget}',a,b) for budget in sorted(set([selected,control,*extra]))}
        values.update(selected=values[f'budget_{selected}'],fresh_control=values[f'budget_{control}'],
                      ipin_tuna_frozen=self.tuna('baseline',a,b))
        values.update(self.pooled(a,b))
        check(all(len(v)==len(a) and np.isfinite(v).all() for v in values.values()), 'Invalid prediction coverage')
        return values

def main():
    check(not Path('/truth').exists() and not Path('/output/PREDICTION_FREEZE.json').exists(),'Unexpected truth visibility or existing prediction freeze')
    selection=read('/output/SELECTION.json'); frozen=read('/output/SCORER_FREEZE.json')
    for item in read('/freeze/CANDIDATE_FREEZE.json')['files']:
        check(sha(Path('/candidates')/item['name'])==item['sha256'], 'Frozen candidate input changed')
    check(sha('/output/SELECTION.json')==frozen['selection_sha256'], 'Selection changed')
    selected=selection['selected']['budget']; control=selection['fresh_control']['budget']
    device=cuda(); scorer=Scores(device); out=Path('/output/predictions'); files=[]
    for fold in ('development','test'):
        for cell in ('C1','C2','C3'):
            for cohort in ('legacy','added'):
                if fold=='test': path=Path(f'/candidates/{cohort}_{cell}.npz')
                elif cohort=='legacy': path=Path(f'/data/legacy/development_{3-int(cell[1]):02d}.npz')
                else: path=Path(f'/data/development/added/{cell}.npz')
                data=arrays(path)
                if fold=='test': check(set(data)=={'a','b'}, 'Test scoring received labels or weights')
                values=scorer.all(data['a'],data['b'],selected,control,
                  extra=[x['budget'] for x in selection['best_per_budget']] if fold=='development' else ())
                dest=out/f'{fold}_{cohort}_{cell}.npz'; save(dest,**values)
                files.append({'input_sha256':sha(path),'fold':fold,'cell':cell,'cohort':cohort,
                              'rows':len(data['a']),'prediction':record(dest,Path('/output'))})
                print({'scored':dest.name,'rows':len(data['a'])},flush=True)
    write('/output/PREDICTION_FREEZE.json',{'at_utc':now(),'scorer_freeze_sha256':sha('/output/SCORER_FREEZE.json'),
      'selection_sha256':sha('/output/SELECTION.json'),'files':files,
      'complete_finite_candidate_coverage':True,'test_truth_read':False,
      'no_test_guided_refitting':True,'test_2_fresh_independent_claim':False})

if __name__=='__main__': main()
