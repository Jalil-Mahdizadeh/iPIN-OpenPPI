"""Freeze model, cache, code and scoring policy before opening test candidates."""
from pathlib import Path
import shutil
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from benchmark_metrics import qualify
from common import ORIGINAL_SHA,SIF_SHA,now,read,write,record,sha,cuda
from frozen_scorer import Scorer

CODE=('common.py','native_adapter.py','frozen_scorer.py','comparison.py','benchmark_metrics.py','gpu_guard.py','score_shard.py')


def main():
    root=Path('/output');cache=root/'projection_cache';bundle=root/'scorer_bundle'
    for name in ('ADAPTER_QUALIFICATION.json','TILING_QUALIFICATION.json'):
        assert read(root/name)['passed']
    manifest=read(cache/'CACHE.json')
    for item in manifest['files']:
        assert sha(cache/item['path'])==item['sha256']
    bundle.mkdir(exist_ok=False)
    for name in ('code','features','provenance'):(bundle/name).mkdir()
    for name in ('projected.npy','offsets.npy'):
        # Immutable independent copy, not a writable link to a live build cache.
        shutil.copyfile(cache/name,bundle/'features'/name)
    for name in ('endpoints.json','components.json','lengths.json'):
        shutil.copyfile(cache/name,bundle/name)
    for name in CODE:shutil.copyfile(Path('/code')/name,bundle/'code'/name)
    for name in ('ADAPTER_QUALIFICATION.json','TILING_QUALIFICATION.json'):
        shutil.copyfile(root/name,bundle/'provenance'/name)
    device=cuda();meta=read('/sequences.json')
    config={'maximum_length':7570,'tile_area':1_000_000,'learned_state_sha256':manifest['learned_state_sha256']}
    scorer=Scorer(bundle,device,config=config)
    permitted=[i for i,p in enumerate(meta['partition']) if p=='train' and meta['length'][i]<=2000]
    selected=np.asarray(permitted)[np.linspace(0,len(permitted)-1,32,dtype=int)]
    a,b=selected[:16],selected[16:]
    actual=scorer.scores(a,b)[:,0]
    original=get_pretrained('human_v1').to(device).eval().requires_grad_(False)
    lm=get_pretrained('lm_v1').to(device).eval().requires_grad_(False);alphabet=Uniprot21();errors=[]
    with torch.inference_mode():
        for j,(x,y) in enumerate(zip(a,b)):
            p=lm.transform(torch.from_numpy(alphabet.encode(meta['sequence'][x].encode())).long()[None].to(device))
            q=lm.transform(torch.from_numpy(alphabet.encode(meta['sequence'][y].encode())).long()[None].to(device))
            expected=original.predict(p,q).item();error=abs(expected-actual[j]);errors.append(error)
            if error>1e-5:raise RuntimeError('Frozen cache/scorer differs from native end-to-end model')
    write(bundle/'provenance/FROZEN_SCORER_QUALIFICATION.json',{'passed':True,'TRAIN_sequence_fixture_pairs':16,
          'maximum_absolute_score_error':max(errors),'test_pairs_read':False,'test_truth_read':False},exclusive=True)
    del scorer,lm,original;torch.cuda.empty_cache()
    write(bundle/'provenance/METRIC_QUALIFICATION.json',qualify(device),exclusive=True)
    files=[]
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            item=record(path);item['path']=str(path.relative_to(bundle));files.append(item)
    write(bundle/'SCORER_FREEZE.json',{'at_utc':now(),'execution_id':'dscript_original_benchmark_v1',
          'scorers':['dscript_original'],'original_model':'human_v1','original_checkpoint_sha256':ORIGINAL_SHA,
          'sif_sha256':SIF_SHA,'learned_state_sha256':manifest['learned_state_sha256'],
          'sequence_metadata_sha256':manifest['sequence_sha256'],'maximum_length':7570,'tile_area':1_000_000,
          'score_definition':'native generalized-sigmoid probability; no score inversion, calibration, ensembling or refitting',
          'residue_policy':'all residues; extend nonlearned xx; 3-residue convolution halo for contact tiling',
          'precision':'FP32; TF32 disabled; original 100-D projection cached in FP32',
          'workers':4,'test_pairs_read':False,'test_truth_read':False,'training_performed':False,
          'metric':'design-weighted P-versus-U concordance with exact-score half ties',
          'primary_cell':'C3_test','paired_component_bootstrap_replicates':2000,
          'prior_test_exposure':'These panels were previously examined for iPIN/TUnA; descriptive follow-up, not new untouched holdout',
          'files':files},exclusive=True)
    print({'frozen':True,'scorer_freeze_sha256':sha(bundle/'SCORER_FREEZE.json')},flush=True)


if __name__=='__main__':main()
