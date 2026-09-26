"""Independent full-forward checks of production indexing on real test identities."""
import numpy as np
import torch
from io_utils import ROOT,MODELS,arrays,atomic,cuda,now,read,record,sha,verify
from embedding import feature_path
from native import load_model,projected_forward,clear_attention
from score import signature,padded,batches
from xpair.utils.embedding_menager import pad_and_mask_emb_batch

@torch.inference_mode()
def main():
    device=cuda();meta=read(ROOT/'data/sequences.json');lengths=np.array(meta['length']);n=len(lengths)
    pair=arrays(ROOT/'data/unique_pairs.npz');a=pair['a'];b=pair['b']
    selected=np.unique(np.r_[np.linspace(0,len(a)-1,48,dtype=np.int64),
                             np.argsort(lengths[a]*lengths[b])[-4:]])
    ids=np.unique(np.r_[a[selected],b[selected]])
    features={int(i):torch.load(feature_path(i),map_location=device,weights_only=True) for i in ids}
    alignments=[]
    for panel in read(ROOT/'PROTOCOL.json')['panels']:
        tag=f"{panel['cohort']}_{panel['cell']}"
        source=arrays(ROOT/f'data/candidates/{tag}.npz');index=arrays(ROOT/f'data/candidates/map_{tag}.npz')['index']
        assert np.array_equal(np.minimum(source['a'],source['b']),a[index])
        assert np.array_equal(np.maximum(source['a'],source['b']),b[index])
        alignments.append({'panel':tag,'rows':len(index),'passed':True})
    output={}
    for name in MODELS:
        model,info=load_model(name,device)
        pieces=[];offsets=np.zeros(n,np.int64);position=0
        # Reverse feature storage order deliberately: gather must follow offsets.
        for i in ids[::-1]:
            projected=model.embedding_projection(features[int(i)])
            offsets[i]=position;position+=len(projected);pieces.append(projected)
        table=torch.cat(pieces);offsets=torch.tensor(offsets,device=device);glengths=torch.tensor(lengths,device=device)
        native=[];production=[];native_prob=[];production_prob=[];order=[]
        for rows,la,lb in batches(selected,a,b,lengths):
            raw1,mask1=pad_and_mask_emb_batch([features[int(i)] for i in a[rows]])
            raw2,mask2=pad_and_mask_emb_batch([features[int(i)] for i in b[rows]])
            reference=model({'input1':(raw1,mask1),'input2':(raw2,mask2)},task='interaction')[0];clear_attention(model)
            x1,m1=padded(table,offsets,glengths,a[rows],la);x2,m2=padded(table,offsets,glengths,b[rows],lb)
            assert torch.equal(m1,mask1) and torch.equal(m2,mask2)
            actual=projected_forward(model,x1,x2,m1,m2)
            native.append(reference.cpu().numpy());production.append(actual.cpu().numpy())
            native_prob.append(reference.sigmoid().cpu().numpy());production_prob.append(actual.sigmoid().cpu().numpy());order.extend(rows.tolist())
        expected=np.concatenate(native);actual=np.concatenate(production)
        ep=np.concatenate(native_prob);ap=np.concatenate(production_prob)
        error=float(np.max(np.abs(expected-actual)));prob_error=float(np.max(np.abs(ep-ap)))
        assert error<2e-4 and prob_error<1e-5
        output[name]={'max_abs_logit_error':error,'max_abs_probability_error':prob_error,
                      'unique_pair_index':order,'native_logit':expected.tolist(),'native_probability':ep.tolist()}
        print({'model':name,'native_forward_integration_error':error,'probability_error':prob_error},flush=True)
        del model,table,pieces;torch.cuda.empty_cache()
    atomic(ROOT/'qualification/INTEGRATION.json',{'at_utc':now(),'passed':True,'signature':signature(),
           'identity_alignment':alignments,'models':output,'script':record(ROOT/'scripts/integration.py')})

if __name__=='__main__':main()
