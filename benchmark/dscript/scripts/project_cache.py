"""Cache original per-residue learned projections; never fit or read pair labels."""
import hashlib
from pathlib import Path
import time
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from common import cuda, now, read, record, sha, write, ORIGINAL_SHA
from native_adapter import create, learned_digest

SEQUENCE_SHA='bc7a91661ea05cbfdcf3551b9a4d18c149ac077549ebbcf0be7e7ef5d94ace77'


def main():
    output=Path('/output'); root=output/'projection_cache'; root.mkdir(exist_ok=True)
    assert read(output/'ADAPTER_QUALIFICATION.json')['passed']
    assert read(output/'TILING_QUALIFICATION.json')['passed']
    if sha('/sequences.json')!=SEQUENCE_SHA:raise RuntimeError('Frozen sequence metadata changed')
    meta=read('/sequences.json'); lengths=np.asarray(meta['length'],np.int64)
    for h,s,n in zip(meta['sha256'],meta['sequence'],lengths):
        if hashlib.sha256(s.encode('ascii')).hexdigest()!=h or len(s)!=n:raise RuntimeError('Sequence identity failure')
    if (root/'CACHE.json').exists():
        manifest=read(root/'CACHE.json')
        for item in manifest['files']:
            if sha(root/Path(item['path']).name)!=item['sha256']:raise RuntimeError('Frozen projection cache changed')
        print('Complete projection cache verified',flush=True);return
    offsets=np.concatenate(([0],np.cumsum(lengths)))
    device=cuda(); model=create(device=device); initial=learned_digest(model)
    lm=get_pretrained('lm_v1').to(device).eval().requires_grad_(False)
    path=root/'projected.npy'; done_path=root/'completed.npy'
    identity={'sequence_sha256':SEQUENCE_SHA,'original_model_sha256':ORIGINAL_SHA,'shape':[int(offsets[-1]),100],'dtype':'float32'}
    if path.exists():
        assert read(root/'BUILD.json')==identity
        projected=np.lib.format.open_memmap(path,mode='r+')
        done=np.load(done_path,allow_pickle=False)
    else:
        write(root/'BUILD.json',identity,exclusive=True)
        projected=np.lib.format.open_memmap(path,mode='w+',dtype=np.float32,shape=(int(offsets[-1]),100))
        done=np.zeros(len(lengths),bool)
        with done_path.open('xb') as handle:np.save(handle,done,allow_pickle=False)
        with (root/'offsets.npy').open('xb') as handle:np.save(handle,offsets,allow_pickle=False)
        write(root/'endpoints.json',meta['sha256'],exclusive=True)
        write(root/'components.json',meta['component'],exclusive=True)
        write(root/'lengths.json',meta['length'],exclusive=True)
    alphabet=Uniprot21(); started=time.monotonic(); start_count=int(done.sum())
    with torch.inference_mode():
        for i,sequence in enumerate(meta['sequence']):
            if done[i]:continue
            x=torch.from_numpy(alphabet.encode(sequence.encode())).long()[None].to(device)
            values=model.embedding(lm.transform(x))[0].cpu().numpy()
            if values.shape!=(len(sequence),100) or not np.isfinite(values).all():raise RuntimeError('Invalid projected residues')
            projected[offsets[i]:offsets[i+1]]=values
            done[i]=True
            if (i+1)%250==0 or i+1==len(done):
                projected.flush()
                # Progress is committed only after the corresponding residue data flush.
                temporary=root/'completed-next.npy'
                with temporary.open('wb') as handle:np.save(handle,done,allow_pickle=False)
                temporary.replace(done_path)
                progress={'at_utc':now(),'completed':int(done.sum()),'total':len(done),
                          'seconds_this_run':time.monotonic()-started,'new_this_run':int(done.sum())-start_count}
                write(root/'PROGRESS.json',progress);print(progress,flush=True)
    assert done.all() and learned_digest(model)==initial
    projected.flush(); del projected
    names=['projected.npy','offsets.npy','endpoints.json','components.json','lengths.json']
    files=[]
    for name in names:
        item=record(root/name);item['path']=name;files.append(item)
    write(root/'CACHE.json',{'at_utc':now(),**identity,'files':files,'endpoints':len(lengths),'residues':int(offsets[-1]),
          'learned_state_sha256':initial,'no_training':True,'full_length':True,'projection_is_original_linear_relu_eval':True,
          'raw_6165_embeddings_persisted':False,'test_pairs_read':False,'test_truth_read':False},exclusive=True)


if __name__=='__main__':main()
