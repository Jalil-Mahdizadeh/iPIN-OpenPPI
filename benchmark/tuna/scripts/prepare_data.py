#!/usr/bin/env python3
"""Copy and verify TRAIN/development and sequence-only inputs; never read test pairs/truth."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import shutil
import numpy as np
import pyarrow.parquet as pq
from common import arrays, now, read, record, sha, write

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    source=args.source; output=args.output
    output.mkdir(parents=True,exist_ok=True)
    if (output/'DATA_MANIFEST.json').exists():
        manifest=read(output/'DATA_MANIFEST.json')
        for item in manifest['outputs']:
            if sha(output/Path(item['path']).name)!=item['sha256']:
                raise RuntimeError('Prepared input changed')
        print('Existing prepared TRAIN/development data verified',flush=True)
        return
    seq_path=source/'data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/eligible_reference_sequences/part-00000.parquet'
    part_path=source/'data/canonical/final_benchmark_component_split_v1/endpoint_partition_assignments/part-00000.parquet'
    if sha(seq_path)!='4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e' or sha(part_path)!='66db8cd59e7cb8cf06ff3ad785448dfc7d5fdd24643811946246d129b0bd8a67':
        raise RuntimeError('Frozen sequence/partition checksum mismatch')
    previous=source/'.private/model_optimization_v1/bundle'
    freeze=read(previous/'SEARCH_FREEZE.json')
    records={x['path']:x for x in freeze['files']}
    inputs=[record(seq_path),record(part_path),record(previous/'SEARCH_FREEZE.json')]
    for name in ['endpoints.json','training.npz','development_00.npz','development_01.npz','development_02.npz']:
        relative='data/'+name
        if sha(previous/relative)!=records[relative]['sha256']:
            raise RuntimeError('Frozen train/dev array checksum mismatch')
        shutil.copyfile(previous/relative,output/name)
        inputs.append(record(previous/relative))
    order=read(output/'endpoints.json')
    seq=pq.read_table(seq_path).sort_by([('reference_sequence_sha256','ascending')])
    part=pq.read_table(part_path).sort_by([('reference_sequence_sha256','ascending')])
    if order!=seq['reference_sequence_sha256'].to_pylist() or order!=part['reference_sequence_sha256'].to_pylist():
        raise RuntimeError('Sequence-identity alignment failed')
    sequences=seq['sequence'].to_pylist()
    lengths=seq['sequence_length'].to_numpy()
    partitions=part['partition'].to_pylist()
    if Counter(partitions)!=Counter(train=11900,development=2550,test=2550):
        raise RuntimeError('Partition census mismatch')
    for h,s,n in zip(order,sequences,lengths,strict=True):
        if hashlib.sha256(s.encode('ascii')).hexdigest()!=h or len(s)!=n:
            raise RuntimeError('Sequence length/hash mismatch')
    write(output/'sequences.json',{'sha256':order,'sequence':sequences,'length':lengths.tolist(),
        'partition':partitions,'component':part['component_id'].to_pylist(),
        'accessions':seq['uniprot_accessions'].to_pylist()})
    train=arrays(output/'training.npz')
    if len(train['p_a'])!=16799 or len(train['u_a'])!=2000000:
        raise RuntimeError('Training row census mismatch')
    for name in ['p_a','p_b','u_a','u_b']:
        if any(partitions[i]!='train' for i in np.unique(train[name])):
            raise RuntimeError('Non-TRAIN pair endpoint in training')
    development=[]
    for i in range(3):
        data=arrays(output/f'development_{i:02d}.npz')
        if any(partitions[j]=='test' for j in np.unique(np.concatenate([data['a'],data['b']]))):
            raise RuntimeError('Test endpoint in development pairs')
        development.append({'cell':f'C{3-i}_development','positive_rows':int(data['positive'].sum()),'unlabeled_rows':int((~data['positive']).sum())})
    summary={'prepared_at_utc':now(),'sequence_rows':len(order),'total_residues':int(lengths.sum()),
        'max_length':int(lengths.max()),'mean_length':float(lengths.mean()),'raw_fp32_residue_bytes':int(lengths.sum())*640*4,
        'train_positive_rows':16799,'train_unlabeled_rows':2000000,'development':development,
        'test_pairs_read':False,'test_truth_read':False,'live_UniProt_access':False,
        'inputs':inputs,'outputs':[record(output/name) for name in ['endpoints.json','sequences.json','training.npz','development_00.npz','development_01.npz','development_02.npz']]}
    write(output/'DATA_MANIFEST.json',summary,exclusive=True)
    print({k:v for k,v in summary.items() if k not in ['inputs','outputs']},flush=True)

if __name__=='__main__':
    main()
