"""Read-back check of stored native residues against fresh TRAIN-sequence encoding."""
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from common import cuda,read,write,now
from model import Residues


def main():
    device=cuda();meta=read('/data/sequences.json');cache=Residues('/output/residue_cache',device)
    ids=np.flatnonzero(np.asarray(meta['partition'])=='train')
    chosen=ids[np.linspace(0,len(ids)-1,6,dtype=int)]
    lm=get_pretrained('lm_v1').to(device).eval().requires_grad_(False);alphabet=Uniprot21();errors=[]
    with torch.inference_mode():
        for i in chosen:
            seq=meta['sequence'][int(i)]
            fresh=lm.transform(torch.from_numpy(alphabet.encode(seq.encode())).long()[None].to(device))
            saved=cache.full(i);assert saved.shape==fresh.shape
            errors.append(float((fresh-saved).abs().max()))
            torch.manual_seed(222)
            crop=cache.crop(i)
            torch.manual_seed(222);n=min(len(seq),512);start=int(torch.randint(len(seq)-n+1,()).item())
            assert crop.shape==(1,n,6165) and torch.equal(crop,saved[:,start:start+n])
    assert max(errors)<=1e-6
    result={'at_utc':now(),'passed':True,'TRAIN_sequences':6,'native_embedding_max_errors':errors,
            'maximum_absolute_error':max(errors),'crop_width_and_offsets_exact':True,
            'test_pairs_read':False,'test_truth_read':False,'training_performed':False}
    write('/output/CACHE_QUALIFICATION.json',result,exclusive=True);print(result,flush=True)


if __name__=='__main__':main()
