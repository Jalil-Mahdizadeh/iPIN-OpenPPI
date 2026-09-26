"""Qualified native X-PAIR scoring with cached independent linear projections."""
import argparse
import os
import time
import numpy as np
import torch
from io_utils import ROOT,MODELS,arrays,atomic,cuda,now,read,record,sha,verify
from native import load_model,projected_forward,clear_attention
from embedding import feature_path
from xpair.utils.embedding_menager import pad_and_mask_emb_batch

LIMIT=8_000_000
MAX_BATCH=64
CHUNK=8192

def signature():
    return {name:sha(ROOT/name) for name in ('PROTOCOL.json','sources/XPAIR_FREEZE.json',
        'sources/ANKH_FREEZE.json','runtime/requirements.freeze.txt','scripts/native.py','scripts/score.py')}

@torch.inference_mode()
def qualify(device):
    embedding=read(ROOT/'qualification/EMBEDDING.json');assert embedding['passed']
    features={x['id']:torch.load(feature_path(x['id']),map_location=device,weights_only=True) for x in embedding['cases']}
    ids=sorted(features,key=lambda i:len(features[i]))
    pairs=[(ids[0],ids[1]),(ids[0],ids[-1]),(ids[-1],ids[2]),
           (ids[2],ids[3]),(ids[-1],ids[-2]),(ids[3],ids[4]),(ids[-1],ids[-1])]
    output={};started=time.monotonic()
    for name in MODELS:
        model,info=load_model(name,device);before={k:v.clone() for k,v in model.state_dict().items()}
        cached={i:model.embedding_projection(f) for i,f in features.items()}
        reference=[];fast=[];reverse=[]
        for a,b in pairs:
            m1=torch.ones(1,len(features[a]),dtype=torch.bool,device=device)
            m2=torch.ones(1,len(features[b]),dtype=torch.bool,device=device)
            batch={'input1':(features[a][None],m1),'input2':(features[b][None],m2)}
            reference.append(model(batch,task='interaction')[0]);clear_attention(model)
            fast.append(projected_forward(model,cached[a][None],cached[b][None],m1,m2))
            reverse.append(projected_forward(model,cached[b][None],cached[a][None],m2,m1))
        reference=torch.cat(reference);fast=torch.cat(fast);reverse=torch.cat(reverse)
        # Heterogeneous padding, repeats, order, and the actual production batch size.
        short=pairs[0:1]+pairs[3:4]+pairs[5:6]
        pp=[short[i%len(short)] for i in range(MAX_BATCH)]
        x1,m1=pad_and_mask_emb_batch([features[a] for a,b in pp])
        x2,m2=pad_and_mask_emb_batch([features[b] for a,b in pp])
        raw=model({'input1':(x1,m1),'input2':(x2,m2)},task='interaction')[0];clear_attention(model)
        z1,_=pad_and_mask_emb_batch([cached[a] for a,b in pp])
        z2,_=pad_and_mask_emb_batch([cached[b] for a,b in pp])
        result=projected_forward(model,z1,z2,m1,m2)
        scalar=torch.stack([reference[pairs.index(p)] for p in pp])
        errors={'cache_logits':float((reference-fast).abs().max()),
                'swap_logits':float((reference-reverse).abs().max()),
                'padded_cache_logits':float((raw-result).abs().max()),
                'batch_singleton_logits':float((scalar-result).abs().max()),
                'padded_probability':float((raw.sigmoid()-result.sigmoid()).abs().max())}
        assert max(errors.values())<2e-4,errors
        assert errors['padded_probability']<1e-5
        assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items())
        output[name]={'model':info,'errors':errors,'pairs':[list(p) for p in pairs],
                      'batch_size':MAX_BATCH,'state_unchanged':True}
        print({'qualified':name,'errors':errors},flush=True)
        del model,cached,before,x1,x2,z1,z2
        torch.cuda.empty_cache()
    atomic(ROOT/'qualification/SCORING.json',{'at_utc':now(),'passed':True,'models':output,
        'signature':signature(),'elapsed_s':time.monotonic()-started,
        'logit_tolerance':2e-4,'probability_tolerance':1e-5,
        'reference':'Unmodified upstream XPairModel.forward with original 1536-dimensional embeddings'})

@torch.inference_mode()
def cache(model,ids,lengths,device):
    segments=[];offsets=np.zeros(len(lengths),np.int64);position=0
    provenance=read(ROOT/'qualification/EMBEDDING.json')['provenance']
    for k,i in enumerate(ids):
        path=feature_path(i);item=read(path.with_suffix('.json'));verify(path,item['file'])
        assert all(item[key]==value for key,value in provenance.items())
        feature=torch.load(path,map_location=device,weights_only=True)
        assert feature.shape==(lengths[i],1536) and feature.dtype==torch.float32
        offsets[i]=position;position+=len(feature)
        segments.append(model.embedding_projection(feature))
        if k%1000==0:print({'projection_cache':k,'total':len(ids)},flush=True)
    table=torch.cat(segments);del segments
    return table,torch.tensor(offsets,device=device),torch.tensor(lengths,device=device)

def padded(table,offsets,lengths,ids,maxlen):
    index=torch.as_tensor(ids,device=table.device)
    positions=torch.arange(maxlen,device=table.device)[None,:]
    mask=positions<lengths[index,None]
    gather=torch.where(mask,offsets[index,None]+positions,0)
    return table[gather]*mask[:,:,None],mask

def batches(indices,a,b,lengths):
    start=0
    while start<len(indices):
        end=start;la=lb=0
        while end<len(indices) and end-start<MAX_BATCH:
            k=indices[end];nexta=max(la,int(lengths[a[k]]));nextb=max(lb,int(lengths[b[k]]))
            if end>start and nexta*nextb*(end-start+1)>LIMIT:break
            la=nexta;lb=nextb;end+=1
        yield indices[start:end],la,lb
        start=end

@torch.inference_mode()
def score(args,device):
    qualification=read(ROOT/'qualification/SCORING.json')
    assert qualification['passed'] and qualification['signature']==signature()
    for rank in range(8):assert (ROOT/'features'/f'COMPLETE-{rank:02d}.json').exists()
    meta=read(ROOT/'data/sequences.json');lengths=np.array(meta['length'])
    ids=arrays(ROOT/'data/endpoint_ids.npz')['ids']
    pairs=arrays(ROOT/'data/unique_pairs.npz');a=pairs['a'];b=pairs['b']
    # Length buckets are identity-only and reduce padding. Every row is assigned once.
    order=np.lexsort((lengths[b]//64,lengths[a]//64))
    order=order[args.rank::8]
    if args.pilot:order=order[:args.pilot]
    for name in MODELS:
        out=ROOT/('pilot' if args.pilot else 'shards')/name/f'rank-{args.rank:02d}'
        out.mkdir(parents=True,exist_ok=True)
        if (out/'COMPLETE.json').exists():
            completed=read(out/'COMPLETE.json');assert completed['signature']==signature()
            for item in completed['files']:verify(ROOT/item['path'],item)
            continue
        model,info=load_model(name,device);before={k:v.clone() for k,v in model.state_dict().items()}
        table,offsets,glengths=cache(model,ids,lengths,device)
        files=[];started=time.monotonic();computed=0
        for start in range(0,len(order),CHUNK):
            index=order[start:start+CHUNK];path=out/f'chunk-{start:08d}.npz';side=path.with_suffix('.json')
            if side.exists():
                previous=read(side);verify(path,previous['file']);assert previous['signature']==signature()
                saved=arrays(path);assert np.array_equal(saved['index'],index)
                assert np.isfinite(saved['logit']).all() and np.isfinite(saved['probability']).all()
            else:
                logit=[];probability=[]
                for rows,la,lb in batches(index,a,b,lengths):
                    x1,m1=padded(table,offsets,glengths,a[rows],la)
                    x2,m2=padded(table,offsets,glengths,b[rows],lb)
                    value=projected_forward(model,x1,x2,m1,m2)
                    logit.append(value.cpu().numpy());probability.append(value.sigmoid().cpu().numpy())
                values=np.concatenate(logit);probs=np.concatenate(probability)
                assert np.isfinite(values).all() and np.isfinite(probs).all()
                temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
                with temp.open('xb') as stream:np.savez(stream,index=index,logit=values,probability=probs)
                temp.replace(path)
                atomic(side,{'at_utc':now(),'file':record(path),'signature':signature()})
                computed+=len(index)
            files.append(record(path))
            elapsed=time.monotonic()-started
            print({'model':name,'rank':args.rank,'finished':start+len(index),'total':len(order),
                   'elapsed_s':round(elapsed,2),'computed_pairs_per_s':round(computed/max(elapsed,.001),2)},flush=True)
        assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items())
        atomic(out/'COMPLETE.json',{'at_utc':now(),'model':name,'rank':args.rank,'workers':8,
              'rows':len(order),'files':files,'signature':signature(),'learned_state_unchanged':True,
              'test_truth_read':False,'elapsed_s':time.monotonic()-started,'checkpoint':info})
        del model,table,before;torch.cuda.empty_cache()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--qualify',action='store_true')
    parser.add_argument('--rank',type=int,default=0);parser.add_argument('--pilot',type=int,default=0)
    args=parser.parse_args();assert 0<=args.rank<8
    device=cuda()
    if args.qualify:qualify(device)
    else:score(args,device)

if __name__=='__main__':main()
