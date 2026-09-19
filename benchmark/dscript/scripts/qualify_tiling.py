"""Compare full contact maps, not just final low-probability scores."""
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from common import cuda, now, read, write
from native_adapter import create, learned_digest


def main():
    device=cuda(20260913); meta=read('/sequences.json')
    indices=[i for i,p in enumerate(meta['partition']) if p=='train' and 100<=meta['length'][i]<=1800][:24]
    lm=get_pretrained('lm_v1').to(device).eval().requires_grad_(False)
    model=create(device=device); before=learned_digest(model); alphabet=Uniprot21(); residues=[]
    results=[]
    with torch.inference_mode():
        for i in indices:
            x=torch.from_numpy(alphabet.encode(meta['sequence'][i].encode())).long()[None].to(device)
            residues.append(model.embedding(lm.transform(x)))
        for a,b in zip(residues[:12],residues[12:]):
            model.tile_area=None
            full=model.cpred(a,b); score=model.predict(a,b)
            model.tile_area=25_000
            tiled=model.cpred(a,b); tiled_score=model.predict(a,b); swapped=model.predict(b,a)
            error=(full-tiled).abs().max().item()
            torch.testing.assert_close(full,tiled,atol=1e-6,rtol=1e-5)
            assert abs(score.item()-tiled_score.item())<=1e-5
            assert abs(tiled_score.item()-swapped.item())<=1e-5
            results.append({'n':a.shape[1],'m':b.shape[1],'contact_map_max_absolute_error':error,
                            'score_absolute_error':abs(score.item()-tiled_score.item()),
                            'symmetry_absolute_error':abs(tiled_score.item()-swapped.item()),
                            'native_score':score.item(),'contact_map_range':[full.min().item(),full.max().item()]})
    assert learned_digest(model)==before
    write('/output/TILING_QUALIFICATION.json',{'at_utc':now(),'passed':True,'fixtures':'12 fixed short TRAIN-sequence pairs, no pair labels',
          'results':results,'learned_state_unchanged':True,'test_pairs_read':False,'test_truth_read':False},exclusive=True)
    print({'passed':True,'cases':len(results),'maximum_contact_map_error':max(x['contact_map_max_absolute_error'] for x in results),
           'maximum_score_error':max(x['score_absolute_error'] for x in results)},flush=True)


if __name__=='__main__':main()
