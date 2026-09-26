"""Reuse all 17k frozen residue arrays, encode only admitted new human sequences."""
from pathlib import Path
import shutil
import time
import h5py
import numpy as np
import torch
from common import cuda
from esm_cache import load_encoder, qualify, embed
from study import arrays, check, now, read, record, sha, write

def main():
    started=time.monotonic(); out=Path('/output/residue_cache'); out.mkdir(exist_ok=True)
    if (out/'RESIDUE_CACHE_MANIFEST.json').exists():
        frozen=read(out/'RESIDUE_CACHE_MANIFEST.json')
        check(sha(out/'residues.h5')==frozen['cache']['sha256'], 'Completed cache changed')
    else:
        old=read('/old_data/sequences.json'); new=read('/data/sequences.json')
        check(new['sha256'][:17000]==old['sha256'] and new['sequence'][:17000]==old['sequence'], 'Cache prefix mismatch')
        parent=read('/old_cache/RESIDUE_CACHE_MANIFEST.json')
        check(sha('/old_cache/residues.h5')==parent['cache']['sha256'], 'Parent cache changed')
        target=out/'residues.h5'
        if not target.exists():
            shutil.copyfile('/old_cache/residues.h5',target)
        identity=sha('/data/sequences.json')
        with h5py.File(target,'r+') as f:
            check(f.attrs['sequence_manifest_sha256'] in (sha('/old_data/sequences.json'),identity), 'Cache identity mismatch')
            f.attrs['sequence_manifest_sha256']=identity; f.attrs['complete']=False
        device=cuda(); model,alphabet,ignored=load_encoder('/encoder',device)
        train=sorted([s for s,part in zip(new['sequence'],new['partition']) if part=='train'],key=len)
        fixtures=[train[len(train)//4],train[len(train)//2],train[int(.9*len(train))]]
        qualification=qualify(model,alphabet,'/encoder',fixtures,out/'ESM_QUALIFICATION.json')
        with h5py.File(target,'r+') as f:
            pending=sorted([i for i in range(17000,len(new['sha256'])) if str(i) not in f],key=lambda i:new['length'][i])
            for start in range(0,len(pending),4):
                indices=pending[start:start+4]
                values=embed(model,alphabet,[new['sequence'][i] for i in indices])
                for i,value in zip(indices,values,strict=True):
                    a=value.cpu().numpy()
                    check(a.shape==(new['length'][i],640) and np.isfinite(a).all(), 'Invalid new embedding')
                    f.create_dataset(str(i),data=a,dtype='float32')
                if start%100==0:
                    f.flush(); print({'new_embeddings_completed':start+len(indices),'new_total':len(pending)},flush=True)
            check(len(f)==len(new['sha256']), 'Incomplete cache')
            f.attrs['complete']=True
        del model; torch.cuda.empty_cache()
        write(out/'RESIDUE_CACHE_MANIFEST.json',{'at_utc':now(),'cache':record(target),
          'parent_cache_sha256':parent['cache']['sha256'],'sequences_sha256':identity,
          'old_embeddings_reused':17000,'new_embeddings':len(new['sha256'])-17000,
          'qualification':qualification,'precision':'full-context FP32; no truncation; frozen ESM layer30',
          'elapsed_seconds':time.monotonic()-started,'test_pairs_or_truth_read':False})
    # The two older iPIN models use a DIFFERENT, windowed mean representation.
    # Retain their 17k vectors and TRAIN normalizer exactly, then extend with their
    # original extraction implementation, rather than substituting TUnA vectors.
    destination=Path('/output/pooled_features.npy')
    if not destination.exists():
        from ipin_openppi.stage1.embeddings import SequenceRecord, extract_matrix
        meta=read('/data/sequences.json'); old=np.load('/pooled/features/standardized.npy',allow_pickle=False)
        norm=arrays('/pooled/features/training_normalization.npz')
        fixtures=[i for i,p in enumerate(meta['partition'][:17000]) if p=='train']
        fixtures=sorted(fixtures,key=lambda i:meta['length'][i])
        fixtures=[fixtures[len(fixtures)//2],fixtures[int(.95*len(fixtures))],fixtures[-1]]
        selected=fixtures+list(range(17000,len(meta['sha256'])))
        records=[SequenceRecord(meta['sha256'][i],meta['sequence'][i],meta['length'][i]) for i in selected]
        matrix,details=extract_matrix(candidate_id='esm2_150m',records=records,model_root=Path('/encoder'))
        standardized=((matrix.astype(np.float64)-norm['mean'])/norm['standard_deviation']).astype(np.float32)
        error=float(np.abs(standardized[:3]-old[fixtures]).max())
        check(error<2e-4, 'Frozen pooled embedding reproduction failed')
        with destination.open('xb') as f:
            np.save(f,np.concatenate([old,standardized[3:]],axis=0),allow_pickle=False)
        write('/output/POOLED_FEATURE_MANIFEST.json',{'at_utc':now(),'features':record(destination),
          'old_vectors_reused':17000,'normalizer_sha256':sha('/pooled/features/training_normalization.npz'),
          'original_extractor_sha256':sha('/library/ipin_openppi/stage1/embeddings.py'),
          'fixture_max_absolute_error':error,'tolerance':2e-4,'details':details,
          'test_pairs_or_truth_read':False})

if __name__=='__main__': main()
