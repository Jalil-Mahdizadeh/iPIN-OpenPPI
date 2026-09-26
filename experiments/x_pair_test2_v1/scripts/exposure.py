"""Identity-only exact/encoder-normalized overlap audit of released X-fair data."""
from pathlib import Path
import csv
import hashlib
import re
import numpy as np
from Bio import SeqIO
from io_utils import ROOT,arrays,atomic,now,read,record,save

def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def normalized(s):return re.sub(r'[UZOBJ]','X',s.upper())

def main():
    meta=read(ROOT/'data/sequences.json');n=len(meta['sequence'])
    target=arrays(ROOT/'data/unique_pairs.npz');codes=target['a']*n+target['b']
    endpoints=arrays(ROOT/'data/endpoint_ids.npz')['ids']
    root=ROOT/'sources/datasets/xpair_datasets/X-fair'
    tables={kind:{} for kind in ('exact','normalized')}
    for i in endpoints:
        for kind,seq in [('exact',meta['sequence'][i]),('normalized',normalized(meta['sequence'][i]))]:
            tables[kind].setdefault(digest(seq),[]).append(int(i))
    flags={kind:np.zeros(len(codes),np.uint8) for kind in tables}
    seen={kind:np.zeros(n,np.uint8) for kind in tables}
    rows=[];sources=[]
    bit_labels={1:'interaction_train_P',2:'interaction_train_U',4:'interaction_val_P',
                8:'interaction_val_U',16:'interface_train',32:'interface_val'}
    for task in ('interaction','interface'):
        fasta=root/task/'sequences.fasta';sources.append(record(fasta))
        maps={kind:{} for kind in tables}
        for item in SeqIO.parse(str(fasta),'fasta'):
            seq=str(item.seq)
            for kind,value in [('exact',seq),('normalized',normalized(seq))]:
                match=tables[kind].get(digest(value))
                if match:maps[kind][item.id]=match
        for split in ('train','val'):
            path=root/task/f'{task}_{split}.tsv';sources.append(record(path))
            found={kind:{} for kind in maps};total=0
            with path.open() as stream:
                for row in csv.DictReader(stream,delimiter='\t'):
                    total+=1
                    if task=='interaction':bit=(1 if float(row['interaction_labels'])==1 else 2)*(1 if split=='train' else 4)
                    else:bit=16 if split=='train' else 32
                    for kind,mapping in maps.items():
                        aa=mapping.get(row['id1'],[]);bb=mapping.get(row['id2'],[])
                        for a in aa:seen[kind][a]|=bit
                        for b in bb:seen[kind][b]|=bit
                        for a in aa:
                            for b in bb:
                                code=min(a,b)*n+max(a,b)
                                found[kind][code]=found[kind].get(code,0)|bit
            summary={'task':task,'split':split,'source_rows':total}
            for kind,matched in found.items():
                keys=np.fromiter(matched,dtype=np.int64);values=np.fromiter(matched.values(),dtype=np.uint8)
                index=np.searchsorted(codes,keys);valid=index<len(codes)
                valid[valid]&=codes[index[valid]]==keys[valid]
                flags[kind][index[valid]]|=values[valid]
                summary[kind+'_test_pairs']=int(valid.sum())
            rows.append(summary);print(summary,flush=True)
    out=ROOT/'exposure';out.mkdir(exist_ok=True)
    save(out/'unique_pairs.npz',**flags)
    save(out/'endpoints.npz',**seen)
    atomic(out/'AUDIT.json',{'at_utc':now(),'rows':rows,'sources':sources,'bit_labels':bit_labels,
          'files':[record(out/'unique_pairs.npz'),record(out/'endpoints.npz')],
          'primary_mask':'normalized flags == 0: excludes any exact or Ankh-normalized pair in either task train/val',
          'interaction_only_mask':'normalized flags & 15 == 0',
          'caveat':'Exact sequence matching cannot exclude homologous pairs, fragments, sequence variants, or pretraining exposure. Endpoint exposure is recorded separately; test2 C1/C2/C3 definitions remain relative to iPIN training.',
          'test_labels_read':False})

if __name__=='__main__':main()
