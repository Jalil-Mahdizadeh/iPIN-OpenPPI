"""Audit documented public human training endpoints, not protected test labels."""
import csv
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

COMMIT='0b3f7363b7d62fb99f5c8bfc6780833f088b8d84'
ROOT=Path(__file__).resolve().parents[1]


def main():
    destination=ROOT/'upstream/original-exposure';destination.mkdir(parents=True,exist_ok=True)
    records=[]
    for relative in ('data/seqs/human.fasta','data/pairs/human_train.tsv'):
        url=f'https://raw.githubusercontent.com/samsledje/D-SCRIPT/{COMMIT}/{relative}'
        path=destination/Path(relative).name
        if not path.exists():
            partial=path.with_suffix(path.suffix+'.part')
            with urlopen(url,timeout=60) as source,partial.open('xb') as out:
                for block in iter(lambda:source.read(8<<20),b''):out.write(block)
            partial.rename(path)
        content=path.read_bytes()
        if content.startswith(b'version https://git-lfs'):raise RuntimeError('Unexpected Git LFS pointer instead of data')
        records.append({'path':str(path.relative_to(ROOT)),'url':url,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)})
    hashes={};name=None;sequence=[]
    with (destination/'human.fasta').open() as handle:
        for line in handle:
            if line.startswith('>'):
                if name is not None:hashes[name]=hashlib.sha256(''.join(sequence).encode()).hexdigest()
                name=line[1:].split()[0];sequence=[]
            else:sequence.append(line.strip())
    if name is not None:hashes[name]=hashlib.sha256(''.join(sequence).encode()).hexdigest()
    endpoints=set();pairs=0;positives=0
    with (destination/'human_train.tsv').open() as handle:
        for row in csv.reader(handle,delimiter='\t'):
            if len(row)<3:raise RuntimeError('Unexpected public pair schema')
            endpoints.update(row[:2]);pairs+=1;positives+=row[2]=='1'
    exposed={hashes[x] for x in endpoints if x in hashes}
    reference=json.loads((ROOT.parent/'tuna/data/sequences.json').read_text())
    overlap={}
    for part in ('train','development','test'):
        eligible={h for h,p in zip(reference['sha256'],reference['partition']) if p==part}
        overlap[part]={'iPIN_endpoints':len(eligible),'exact_sequence_matches':len(eligible&exposed)}
    result={'commit':COMMIT,'sources':records,'public_pairs':pairs,'public_positive_pairs':positives,
            'public_negative_labeled_pairs':pairs-positives,'public_pair_endpoints':len(endpoints),
            'missing_public_fasta_endpoints':len(endpoints-set(hashes)),
            'exact_sequence_overlap_by_iPIN_partition':overlap,'test_pairs_read':False,'test_truth_read':False,
            'caveat':'Audit of the public human-training files linked by official documentation, not independent authentication of the complete human_v1 checkpoint training history. Exact-sequence overlap is not a complete homology or interaction-pair audit. No test rows are excluded on this basis.'}
    output=ROOT/'provenance/original-evaluation-v1/ORIGINAL_EXPOSURE_AUDIT.json'
    with output.open('x') as handle:json.dump(result,handle,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
