"""Freeze complete pair-identity-aligned predictions before opening test labels."""
import os
import numpy as np
from io_utils import ROOT,MODELS,arrays,atomic,now,read,record,sha,verify
from score import signature

def main():
    out=ROOT/'results';out.mkdir(exist_ok=True)
    freeze=out/'PREDICTION_FREEZE.json'
    if freeze.exists():
        frozen=read(freeze);assert frozen['signature']==signature()
        for item in frozen['files']:verify(ROOT/item['path'],item)
        return
    prepared=read(ROOT/'PREPARED.json')
    assert prepared['protocol_sha256']==sha(ROOT/'PROTOCOL.json')
    for item in prepared['files']:verify(ROOT/item['path'],item)
    protocol=read(ROOT/'PROTOCOL.json');n=protocol['unique_pairs'];predictions={};manifests=[]
    integration=read(ROOT/'qualification/INTEGRATION.json')
    assert integration['passed'] and integration['signature']==signature()
    for name in MODELS:
        seen=np.zeros(n,bool);probability=np.full(n,np.nan,np.float32);logit=probability.copy()
        for rank in range(protocol['scoring_workers']):
            path=ROOT/'shards'/name/f'rank-{rank:02d}'/'COMPLETE.json';completed=read(path)
            assert completed['signature']==signature() and completed['model']==name and completed['rank']==rank
            assert completed['learned_state_unchanged'] and not completed['test_truth_read']
            count=0
            for item in completed['files']:
                source=ROOT/item['path'];verify(source,item);part=arrays(source);index=part['index']
                assert np.all((index>=0)&(index<n)) and len(np.unique(index))==len(index) and not seen[index].any()
                assert np.isfinite(part['probability']).all() and np.isfinite(part['logit']).all()
                assert np.all((part['probability']>=0)&(part['probability']<=1))
                probability[index]=part['probability'];logit[index]=part['logit'];seen[index]=True;count+=len(index)
            assert count==completed['rows'];manifests.append(record(path))
        assert seen.all() and np.isfinite(probability).all() and np.isfinite(logit).all()
        fixture=integration['models'][name];ii=np.array(fixture['unique_pair_index'])
        assert np.max(np.abs(logit[ii]-fixture['native_logit']))<2e-4
        assert np.max(np.abs(probability[ii]-fixture['native_probability']))<1e-5
        predictions[name]=probability;predictions[name+'_logit']=logit
    target=out/'predictions';target.mkdir(exist_ok=True);files=[]
    for panel in protocol['panels']:
        cohort=panel['cohort'];cell=panel['cell'];index=arrays(ROOT/f'data/candidates/map_{cohort}_{cell}.npz')['index']
        assert len(index)==panel['rows']
        path=target/f'{cohort}_{cell}.npz';temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
        with temp.open('wb') as stream:np.savez(stream,**{k:v[index] for k,v in predictions.items()})
        temp.replace(path)
        files.append({**record(path),'cohort':cohort,'cell':cell,'rows':len(index),
                      'candidate_sha256':panel['candidate']['sha256']})
    atomic(freeze,{'at_utc':now(),'models':list(MODELS),'files':files,'shard_manifests':manifests,
        'signature':signature(),'complete_finite_candidate_coverage':True,'candidate_rows':n,
        'test_truth_read_during_scoring_or_assembly':False,'source_weights_unchanged':True,
        'embedding_qualification':record(ROOT/'qualification/EMBEDDING.json'),
        'scoring_qualification':record(ROOT/'qualification/SCORING.json'),
        'production_integration_qualification':record(ROOT/'qualification/INTEGRATION.json')})
    print({'prediction_freeze':str(freeze),'candidate_rows':n,'models':MODELS},flush=True)

if __name__=='__main__':main()
