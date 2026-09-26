"""Full-length FP32 Ankh features; no pair labels are available here."""
import argparse
import os
import time
import numpy as np
import torch
from io_utils import ROOT, arrays, atomic, cuda, now, read, record, sha, verify
from native import encode,load_encoder

def feature_path(i):return ROOT/'features'/f'{i:05d}.pt'

def put_feature(i,feature,sequence_sha,provenance):
    path=feature_path(i);path.parent.mkdir(exist_ok=True)
    temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    torch.save(feature,temp);temp.replace(path)
    atomic(path.with_suffix('.json'),{'id':int(i),'sequence_sha256':sequence_sha,
           'length':feature.shape[0],'dimension':1536,'dtype':'float32',
           'file':record(path),**provenance})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--rank',type=int,required=True)
    parser.add_argument('--qualify',action='store_true');args=parser.parse_args()
    device=cuda();meta=read(ROOT/'data/sequences.json')
    ids=arrays(ROOT/'data/endpoint_ids.npz')['ids']
    provenance={'encoder_freeze_sha256':sha(ROOT/'sources/ANKH_FREEZE.json'),
                'runtime_sha256':sha(ROOT/'runtime/requirements.freeze.txt'),
                'encoder_script_sha256':sha(ROOT/'scripts/native.py')}
    lengths=np.array(meta['length'])
    if args.qualify:
        ids=ids[np.argsort(lengths[ids],kind='stable')]
        ids=np.unique(ids[np.array([0,1,len(ids)//4,len(ids)//2,3*len(ids)//4,len(ids)-1])])
    else:
        qualification=read(ROOT/'qualification/EMBEDDING.json')
        assert qualification['passed'] and qualification['provenance']==provenance
        assignment=arrays(ROOT/'data/embedding_assignment.npz')['rank']
        ids=ids[assignment[ids]==args.rank]
        ids=ids[np.argsort(-lengths[ids],kind='stable')]
    for item in read(ROOT/'sources/ANKH_FREEZE.json')['files']:
        verify(ROOT/item['path'],item)
    model,tokenizer=load_encoder(device)
    started=time.monotonic();files=[]
    if args.qualify:
        from unittest.mock import patch
        from xpair.utils.embedding_menager import generate_embeddings_with_ankh
        gold=ROOT/'qualification/native_embeddings';gold.mkdir(parents=True,exist_ok=True)
        def encoder_alias(name,*a,**k):
            assert name=='ElnaggarLab/ankh-large';return model
        def tokenizer_alias(name,*a,**k):
            assert name=='ElnaggarLab/ankh-large';return tokenizer
        with patch('transformers.T5EncoderModel.from_pretrained',side_effect=encoder_alias),\
             patch('transformers.AutoTokenizer.from_pretrained',side_effect=tokenizer_alias):
            generate_embeddings_with_ankh([(str(i),meta['sequence'][i]) for i in ids],output_dir=str(gold))
        errors=[]
    for j,i in enumerate(ids):
        path=feature_path(i);side=path.with_suffix('.json')
        if not args.qualify and side.exists():
            item=read(side);verify(path,item['file'])
            assert item['sequence_sha256']==meta['sha256'][i]
            assert all(item[k]==v for k,v in provenance.items())
        else:
            feature=encode(model,tokenizer,meta['sequence'][i],device)
            if args.qualify:
                expected=torch.load(gold/f'{i}.pt',map_location='cpu',weights_only=True)
                error=float((expected-feature).abs().max());assert error==0
                errors.append({'id':int(i),'length':len(feature),'max_abs_error':error})
            put_feature(i,feature,meta['sha256'][i],provenance)
        files.append(record(side))
        if j%25==0:print({'rank':args.rank,'finished':j+1,'total':len(ids),
                          'elapsed_s':round(time.monotonic()-started,2),'last_length':int(lengths[i])},flush=True)
    if args.qualify:
        output=ROOT/'qualification/EMBEDDING.json'
        result={'passed':True,'reference':'Unmodified upstream generate_embeddings_with_ankh; only public model path redirected to its pinned local files',
                'cases':errors,'provenance':provenance}
    else:
        output=ROOT/'features'/f'COMPLETE-{args.rank:02d}.json'
        result={'rank':args.rank,'ids':ids.tolist(),'files':files,'provenance':provenance}
    atomic(output,{'at_utc':now(),'elapsed_s':time.monotonic()-started,**result})
    print({'complete':str(output),'elapsed_s':time.monotonic()-started},flush=True)

if __name__=='__main__':main()
