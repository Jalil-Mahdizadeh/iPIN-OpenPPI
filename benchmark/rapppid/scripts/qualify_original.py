"""Public/TRAIN-only reference checks, endpoint-cache qualification and timing."""
from collections import defaultdict
import hashlib
import importlib.metadata
from pathlib import Path
import re
import shutil
import time
import numpy as np
import torch
from pytorch_lightning.callbacks import ModelCheckpoint
import infer as author_infer
from common import cuda, now, read, write, sha, ORIGINAL_SHA
from native_model import (UPSTREAM, CHECKPOINT, MAX_RESIDUES, load_model, tokenizer, encode,
                          learned_digest, native_probability, singleton_embedding, independent_head)
from benchmark_metrics import qualify
from frozen_scorer import Scorer

CODE = ('common.py','native_model.py','frozen_scorer.py','benchmark_metrics.py','gpu_guard.py',
        'comparison.py','score_shard.py','qualify_original.py')


def main():
    output = Path('/output'); device = cuda(); started = time.monotonic()
    assert sha('/sequences.json') == 'bc7a91661ea05cbfdcf3551b9a4d18c149ac077549ebbcf0be7e7ef5d94ace77'
    assert sha('/training.npz') == '43ae252277820ffe527dad1ed4839d5673cff279b6c8c943ff4b5350a9283ca6'
    meta = read('/sequences.json')
    assert len(meta['sequence']) == 17000
    assert all(hashlib.sha256(s.encode()).hexdigest() == h for s,h in zip(meta['sequence'],meta['sha256'],strict=True))
    model = load_model(device); spp = tokenizer(); before = learned_digest(model)
    # Load once through the actual public inference loader as an independent
    # check of constructor/hyperparameters and strict manual-state loading.
    with torch.serialization.safe_globals([ModelCheckpoint]):
        reference = author_infer.load_chkpt(str(CHECKPOINT)).eval().requires_grad_(False).to(device)
    assert learned_digest(reference) == before
    public = re.findall(r"'([A-Z]{30,})'", (UPSTREAM/'docs/infer.md').read_text())
    assert len(public) == 2
    public_tokens = [encode(spp, s) for s in public]
    for s,t in zip(public,public_tokens,strict=True):
        assert np.array_equal(t, author_infer.encode_seq(spp,s[:MAX_RESIDUES],MAX_RESIDUES).numpy())
    with torch.inference_mode():
        # Public example's two-sequence encoder call is also reproduced exactly;
        # production deliberately fixes separate singleton endpoint semantics.
        batch = author_infer.process_seqs(spp, public, MAX_RESIDUES).to(device)
        expected_embeddings = reference(batch)
        actual_embeddings = model(batch)
        public_reference = author_infer.predict(reference,expected_embeddings[0:1],expected_embeddings[1:2])
        public_actual = author_infer.predict(model,actual_embeddings[0:1],actual_embeddings[1:2])
    public_error = float(torch.max(torch.abs(public_reference-public_actual)))
    assert public_error <= 1e-6
    train = np.load('/training.npz', allow_pickle=False)
    generator = np.random.Generator(np.random.PCG64DXSM(20260917))
    chosen = generator.choice(len(train['u_a']),4096,replace=False)
    a = train['u_a'][chosen]; b = train['u_b'][chosen]
    assert all(meta['partition'][int(i)] == 'train' for i in np.concatenate((a,b)))
    train_ids = np.asarray([i for i,p in enumerate(meta['partition']) if p == 'train'])
    longest = train_ids[np.argsort(np.asarray(meta['length'])[train_ids])[-12:]]
    qa = np.concatenate((a[:32],longest)); qb = np.concatenate((b[:32],longest[::-1]))
    fixture_ids = sorted(set(qa.tolist()+qb.tolist()))
    fixture_tokens = {i:encode(spp,meta['sequence'][i]) for i in fixture_ids}
    expected=[]; singleton={}
    with torch.inference_mode():
        for i in fixture_ids:
            native = author_infer.process_seqs(spp,[meta['sequence'][i][:MAX_RESIDUES]],MAX_RESIDUES).to(device)
            assert np.array_equal(native.cpu().numpy()[0],fixture_tokens[i])
            singleton[i] = author_infer.get_embeddings(reference,native).reshape(1,64)
        for x,y in zip(qa,qb,strict=True):
            expected.append(float(author_infer.predict(reference,singleton[int(x)],singleton[int(y)]).item()))
    expected=np.asarray(expected); cache_errors=[]
    # Test batching with identical native effective lengths, including longest
    # TRAIN proteins. Unequal-length padding would not preserve this encoder.
    with torch.inference_mode():
        for batch_size in (1,8,32):
            maximum=0.0
            for i in fixture_ids:
                values=np.repeat(fixture_tokens[i][None,:],batch_size,axis=0)
                actual=model(torch.as_tensor(values,device=device)).reshape(batch_size,64)
                maximum=max(maximum,float(torch.max(torch.abs(actual-singleton[i]))))
            assert maximum <= 1e-5, (batch_size,maximum)
            cache_errors.append({'batch_size':batch_size,'maximum_embedding_error':maximum})
    # Record, without using outcomes for model choices, why ordinary batching
    # cannot be substituted for the frozen singleton predictor.
    with torch.inference_mode():
        sa=torch.cat([singleton[int(i)] for i in qa]);sb=torch.cat([singleton[int(i)] for i in qb])
        native_batched=torch.sigmoid(reference.class_head(sa,sb)).reshape(-1).cpu().numpy()
        corrected=independent_head(model,sa,sb).cpu().numpy()
    direct_batch_difference=float(np.max(np.abs(native_batched-expected)))
    head_error=float(np.max(np.abs(corrected-expected)))
    assert head_error <= 1e-5
    print({'reference_pairs':len(qa),'public_native_error':public_error,'head_error':head_error,
           'unqualified_cross_pair_batch_difference':direct_batch_difference},flush=True)
    # All frozen sequences are public candidate features, not test pair labels.
    # Build the cache only after singleton/batch reference checks above pass.
    cache=output/'endpoint_cache';cache.mkdir(exist_ok=False)
    tokens=np.stack([encode(spp,s) for s in meta['sequence']])
    effective=np.count_nonzero(tokens,axis=1)
    groups=defaultdict(list)
    for index,length in enumerate(effective.tolist()):groups[length].append(index)
    values=np.full((len(tokens),64),np.nan,np.float32);done=0;cache_start=time.monotonic()
    with torch.inference_mode():
        for length,indices in sorted(groups.items()):
            for offset in range(0,len(indices),32):
                ids=np.asarray(indices[offset:offset+32],np.int64)
                result=model(torch.as_tensor(tokens[ids],device=device)).reshape(len(ids),64)
                values[ids]=result.cpu().numpy();done+=len(ids)
            if done % 100 < len(indices) or done == len(tokens):
                progress={'at_utc':now(),'completed':done,'total':len(tokens),'elapsed_seconds':time.monotonic()-cache_start}
                write(cache/'PROGRESS.json',progress);print({'endpoint_cache':progress},flush=True)
    torch.cuda.synchronize();cache_seconds=time.monotonic()-cache_start
    assert np.isfinite(values).all() and (values.std(axis=1,ddof=1)>0).all()
    np.save(cache/'embeddings.npy',values,allow_pickle=False)
    embedding_error=max(float(np.max(np.abs(values[i]-singleton[i].cpu().numpy()[0]))) for i in fixture_ids)
    assert embedding_error <= 1e-5
    embeddings=torch.as_tensor(values,device=device)
    with torch.inference_mode():
        actual=independent_head(model,embeddings[qa],embeddings[qb]).cpu().numpy()
        reverse=independent_head(model,embeddings[qb],embeddings[qa]).cpu().numpy()
    score_error=float(np.max(np.abs(actual-expected))); reversal_error=float(np.max(np.abs(actual-reverse)))
    assert score_error <= 1e-5 and reversal_error == 0.0
    fixture=output/'fixture';fixture.mkdir(exist_ok=False)
    shutil.copyfile(cache/'embeddings.npy',fixture/'embeddings.npy')
    write(fixture/'lengths.json',meta['length'])
    wrapper=Scorer(fixture,device,config={'pair_batch_size':8192})
    wrapper_errors=[]
    for batch_size in (1,8,8192):
        wrapper.batch=batch_size
        got=wrapper.scores(qa,qb)[:,0]
        error=float(np.max(np.abs(got-expected)))
        reverse_error=float(np.max(np.abs(got-wrapper.scores(qb,qa)[:,0])))
        permutation=np.arange(len(qa))[::-1]
        permuted_error=float(np.max(np.abs(got[permutation]-wrapper.scores(qa[permutation],qb[permutation])[:,0])))
        assert error<=1e-5 and reverse_error==0.0 and permuted_error<=1e-5
        wrapper_errors.append({'batch_size':batch_size,'maximum_native_error':error,'reversal_error':reverse_error,'permutation_error':permuted_error})
    timings=[]
    with torch.inference_mode():
        # Fixed TRAIN-U pairs, repeated to make the small native head timing
        # useful. No optimization step or biological outcome is evaluated.
        ia=np.tile(a,32);ib=np.tile(b,32)
        for batch_size in (1024,8192,32768):
            torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();tick=time.monotonic()
            for start in range(0,len(ia),batch_size):
                predictions=independent_head(model,embeddings[ia[start:start+batch_size]],embeddings[ib[start:start+batch_size]])
                assert torch.isfinite(predictions).all()
            torch.cuda.synchronize();elapsed=time.monotonic()-tick
            timings.append({'batch_size':batch_size,'pairs':len(ia),'seconds':elapsed,
                            'pairs_per_second':len(ia)/elapsed,'peak_gpu_bytes':torch.cuda.max_memory_allocated()})
    assert learned_digest(model)==before and learned_digest(reference)==before
    coverage={'sequences':len(tokens),'sequences_with_prefix_truncation':int(np.sum(np.asarray(meta['length'])>MAX_RESIDUES)),
              'maximum_effective_tokens':int(effective.max()),'minimum_effective_tokens':int(effective.min()),
              'all_embeddings_finite':True,'elapsed_seconds':cache_seconds,'embedding_sha256':sha(cache/'embeddings.npy'),
              'cache_semantics':'Exact-effective-length batches of at most32; native singleton endpoints, no cross-length padding',
              'learned_state_sha256':before,'sequence_sha256':sha('/sequences.json'),'training_performed':False}
    write(cache/'CACHE.json',coverage,exclusive=True)
    result={'passed':True,'at_utc':now(),'release':'1690837077.519848_red-dreamy','checkpoint_sha256':ORIGINAL_SHA,
            'sequence_sha256':sha('/sequences.json'),'training_pilot_input_sha256':sha('/training.npz'),
            'code_sha256':{name:sha(Path('/code')/name) for name in CODE},
            'gpu':torch.cuda.get_device_name(),'versions':{n:importlib.metadata.version(n) for n in ('torch','numpy','pytorch-lightning','torchmetrics','sentencepiece','tables')},
            'public_example_native_error':public_error,'public_example_probability':float(public_actual.item()),
            'reference_pairs':len(qa),'maximum_embedding_error':embedding_error,'maximum_score_error':score_error,
            'head_vectorization_error':head_error,'reversal_error':reversal_error,'tolerance':1e-5,
            'unqualified_native_multi_pair_head_difference':direct_batch_difference,'cache_batch_checks':cache_errors,
            'wrapper_checks':wrapper_errors,
            'learned_state_sha256':before,'learned_state_unchanged':True,'cache':coverage,'timings':timings,
            'pair_batch_size':8192,'maximum_residues':MAX_RESIDUES,'metric_qualification':qualify(device),
            'elapsed_seconds':time.monotonic()-started,'test_pairs_read':False,'test_truth_read':False,'training_performed':False}
    write(output/'QUALIFICATION.json',result,exclusive=True);print(result,flush=True)


if __name__=='__main__':
    main()
