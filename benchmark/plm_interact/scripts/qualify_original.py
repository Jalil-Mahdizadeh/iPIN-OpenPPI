"""Original-model fidelity, finite coverage, batching, guard and TRAIN timing."""
from pathlib import Path
import gc
import importlib.metadata
import platform
import re
import time
from unittest.mock import patch
import numpy as np
import torch
from transformers import AutoConfig, AutoModelForMaskedLM
from PLMinteract.inference.inference_PPI_singleGPU import PLMinteract
from common import cuda, now, read, write, sha, ORIGINAL_SHA
from benchmark_metrics import qualify
from frozen_scorer import Scorer
from native_model import ASSETS, learned_digest

def main():
    root = Path('/output'); device = cuda(); started = time.monotonic()
    meta = read('/sequences.json')
    assert sha('/sequences.json') == 'bc7a91661ea05cbfdcf3551b9a4d18c149ac077549ebbcf0be7e7ef5d94ace77'
    training_sha=sha('/training.npz')
    assert training_sha == '43ae252277820ffe527dad1ed4839d5673cff279b6c8c943ff4b5350a9283ca6'
    assert all(hashlib_sha(s) == h for s,h in zip(meta['sequence'],meta['sha256'],strict=True))
    fixture = root/'fixture'; fixture.mkdir(exist_ok=True)
    write(fixture/'sequences.json',meta['sequence']); write(fixture/'endpoints.json',meta['sha256'])
    scorer = Scorer(fixture, device, config={'maximum_tokens':1603,'batch_size':8})
    before = learned_digest(scorer.model)
    # Instantiate the actual published class without downloading redundant base
    # weights; strict released-state loading replaces every tensor before use.
    config = AutoConfig.from_pretrained(ASSETS/'esm2_650m',local_files_only=True)
    with patch.object(AutoModelForMaskedLM,'from_pretrained',side_effect=lambda *a,**k:AutoModelForMaskedLM.from_config(config)):
        reference = PLMinteract(str(ASSETS/'esm2_650m'),1,config,device,1280)
    reference.load_state_dict(torch.load(ASSETS/'humanV11/pytorch_model.bin',map_location='cpu',weights_only=True,mmap=True),strict=True)
    reference.to(device).eval().requires_grad_(False)
    text=Path('/opt/plm_interact/upstream/README.md').read_text()
    public=[re.search(r'protein'+str(i)+r'\s*=\s*"([A-Z]+)"',text).group(1) for i in (1,2)]
    features=scorer.tokenizer(public[0],public[1],padding=True,truncation='longest_first',max_length=1603,return_tensors='pt').to(device)
    with torch.inference_mode():
        expected=reference.forward_test(features); actual=scorer.model.forward_test(features)
    error=float(torch.max(torch.abs(expected-actual)))
    assert error == 0.0
    public_probability=float(actual.item())
    train=np.load('/training.npz',allow_pickle=False)
    generator=np.random.Generator(np.random.PCG64DXSM(20260916))
    chosen=generator.choice(len(train['u_a']),512,replace=False)
    a=train['u_a'][chosen];b=train['u_b'][chosen]
    assert all(meta['partition'][int(i)]=='train' for i in np.concatenate((a,b)))
    # Reference comparison includes the longest frozen TRAIN endpoints.
    train_ids=np.asarray([i for i,x in enumerate(meta['partition']) if x=='train'])
    longest=train_ids[np.argsort(np.asarray(meta['length'])[train_ids])[-8:]]
    qa=np.concatenate((a[:16],longest));qb=np.concatenate((b[:16],longest[::-1]))
    expected=[]
    with torch.inference_mode():
        for x,y in zip(qa,qb,strict=True):
            x,y=sorted((int(x),int(y)),key=lambda i:meta['sha256'][i])
            inputs=scorer.tokenizer(meta['sequence'][x],meta['sequence'][y],padding=True,truncation='longest_first',max_length=1603,return_tensors='pt').to(device)
            expected.append(float(reference.forward_test(inputs).item()))
    del reference;gc.collect();torch.cuda.empty_cache()
    timing=[];max_error=0.0
    for batch in (8,16,32):
        scorer.batch=batch
        values=scorer.scores(qa,qb)[:,0]
        batch_error=float(np.max(np.abs(values-np.asarray(expected))))
        symmetry=float(np.max(np.abs(values-scorer.scores(qb,qa)[:,0])))
        assert batch_error<=1e-5 and symmetry<=1e-5,(batch,batch_error,symmetry)
        max_error=max(max_error,batch_error)
        scorer.scores(a[:32],b[:32]);torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
        tick=time.monotonic();values=scorer.scores(a,b);torch.cuda.synchronize();elapsed=time.monotonic()-tick
        item={'batch_size':batch,'pairs':len(a),'seconds':elapsed,'pairs_per_second':len(a)/elapsed,
              'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'maximum_reference_error':batch_error,'symmetry_error':symmetry}
        timing.append(item);print({'TRAIN_ONLY_TIMING':item},flush=True)
    selected=max(timing,key=lambda x:x['pairs_per_second'])
    assert learned_digest(scorer.model)==before
    result={'passed':True,'at_utc':now(),'model':'danliu1226/PLM-interact-650M-humanV11',
            'checkpoint_sha256':ORIGINAL_SHA,'sequence_sha256':sha('/sequences.json'),
            'training_pilot_input_sha256':training_sha,
            'code_sha256':{name:sha(Path('/code')/name) for name in ('native_model.py','frozen_scorer.py','common.py','benchmark_metrics.py','gpu_guard.py','comparison.py','score_shard.py','qualify_original.py')},
            'gpu':torch.cuda.get_device_name(),'machine':platform.machine(),
            'versions':{x:importlib.metadata.version(x) for x in ('PLMinteract','transformers','tokenizers','torch','numpy')},
            'public_fixture_probability':public_probability,'public_fixture_native_error':error,
            'native_reference_pairs':len(qa),'reference_maximum_error':max_error,'tolerance':1e-5,
            'learned_state_sha256':before,'learned_state_unchanged':True,'timings':timing,'selected_timing':selected,
            'maximum_tokens':1603,'order':'ascending frozen sequence SHA256; no order averaging',
            'truncation':'native longest_first; retain every row; no full-sequence claim',
            'pilot_selection':'fixed-seed random TRAIN U pairs plus longest TRAIN endpoint fixtures; no test access',
            'original_test_rows':3019012,'ideal_four_gpu_scoring_hours':3019012/selected['pairs_per_second']/4/3600,
            'timing_caveat':'TRAIN-only length mixture; excludes queueing, setup and metrics; production rate may differ',
            'metric_qualification':qualify(device),'elapsed_seconds':time.monotonic()-started,
            'test_pairs_read':False,'test_truth_read':False,'training_performed':False}
    write(root/'QUALIFICATION.json',result,exclusive=True)
    print(result,flush=True)

def hashlib_sha(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()

if __name__=='__main__':main()
