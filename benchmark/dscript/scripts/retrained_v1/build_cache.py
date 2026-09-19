"""Resumable full-length FP32 native LM cache, without a fixed PPI projection."""
from pathlib import Path
import time
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from common import cuda,read,write,sha,record,now


def main():
    output=Path('/output'); root=output/'residue_cache';root.mkdir(exist_ok=True)
    meta=read('/data/sequences.json');seqsha=sha('/data/sequences.json')
    assert seqsha=='bc7a91661ea05cbfdcf3551b9a4d18c149ac077549ebbcf0be7e7ef5d94ace77'
    if (root/'CACHE.json').exists():
        for item in read(root/'CACHE.json')['files']:assert sha(root/item['path'])==item['sha256']
        print('Completed native LM cache verified',flush=True);return
    offsets=np.concatenate(([0],np.cumsum(meta['length'],dtype=np.int64)))
    shape=(int(offsets[-1]),6165)
    if (root/'BUILD.json').exists():
        assert read(root/'BUILD.json')=={'sequence_sha256':seqsha,'shape':list(shape),'dtype':'float32'}
        values=np.lib.format.open_memmap(root/'residues.npy',mode='r+')
        done=np.load(root/'completed.npy',allow_pickle=False)
    else:
        write(root/'BUILD.json',{'sequence_sha256':seqsha,'shape':list(shape),'dtype':'float32'},exclusive=True)
        values=np.lib.format.open_memmap(root/'residues.npy',mode='w+',dtype=np.float32,shape=shape)
        done=np.zeros(len(meta['length']),bool)
        for name,array in [('offsets.npy',offsets),('completed.npy',done)]:
            with (root/name).open('xb') as handle:np.save(handle,array,allow_pickle=False)
    device=cuda();lm=get_pretrained('lm_v1').to(device).eval().requires_grad_(False);alphabet=Uniprot21()
    started=time.monotonic();initial=int(done.sum())
    with torch.inference_mode():
        for i,seq in enumerate(meta['sequence']):
            if done[i]:continue
            encoded=torch.from_numpy(alphabet.encode(seq.encode())).long()[None].to(device)
            features=lm.transform(encoded)[0].cpu().numpy()
            assert features.shape==(len(seq),6165) and np.isfinite(features).all()
            values[offsets[i]:offsets[i+1]]=features;done[i]=True
            if (i+1)%100==0 or done.all():
                values.flush()
                temporary=root/'completed-next.npy'
                with temporary.open('wb') as handle:np.save(handle,done,allow_pickle=False)
                temporary.replace(root/'completed.npy')
                progress={'at_utc':now(),'completed':int(done.sum()),'total':len(done),'new_this_run':int(done.sum())-initial,
                          'seconds_this_run':time.monotonic()-started}
                write(root/'PROGRESS.json',progress);print(progress,flush=True)
    values.flush();del values
    files=[]
    for name in ('residues.npy','offsets.npy'):
        item=record(root/name);item['path']=name;files.append(item)
    write(root/'CACHE.json',{'at_utc':now(),'files':files,'sequence_sha256':seqsha,'shape':list(shape),
          'dtype':'float32','full_length':True,'encoder':'native Bepler-Berger lm_v1; frozen',
          'encoder_sha256':'b91f32fcd7d68460ca3c3e3bd2396c1f5826a333ad4ad4962b7f4ab3a410b17c',
          'no_PPI_projection_applied':True,'training_performed':False,'test_pairs_read':False,'test_truth_read':False},exclusive=True)
    print({'cache_complete':True,'payload_bytes':int(offsets[-1])*6165*4},flush=True)


if __name__=='__main__':main()
