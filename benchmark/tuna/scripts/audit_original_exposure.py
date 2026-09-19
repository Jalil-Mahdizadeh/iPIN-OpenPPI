#!/usr/bin/env python3
"""Aggregate exact-sequence exposure audit of the documented authors' inputs.

This does not inspect iPIN test pairs/truth, alter checkpoints, or select
between checkpoints. Published input files do not cryptographically prove
the complete training history of the downloaded checkpoint.
"""
import csv
import hashlib
from pathlib import Path
from common import now, read, record, write

def main():
    source=Path('/upstream/data'); fasta=source/'raw/bernett/human_swissprot_oneliner.fasta'
    sequences={}; accession=None
    for line in fasta.read_text().splitlines():
        if line.startswith('>'):
            accession=line[1:].split()[0]; sequences[accession]=''
        elif line.strip():
            sequences[accession]+=line.strip()
    hashes={k:hashlib.sha256(v.encode('ascii')).hexdigest() for k,v in sequences.items()}
    reference=read('/data/sequences.json'); report={}; sources=[record(fasta)]
    for dataset,meaning in [('Intra1','documented_training'),('Intra0','documented_validation')]:
        path=source/'processed/bernett'/f'{dataset}_interaction_1500_or_less.tsv'
        rows=list(csv.reader(path.open(),delimiter='\t'))
        endpoints={x for row in rows for x in row[:2]}
        missing=endpoints-set(hashes)
        exposed={hashes[x] for x in endpoints if x in hashes}
        overlaps={}
        for part in ('train','development','test'):
            eligible={h for h,p in zip(reference['sha256'],reference['partition']) if p==part}
            overlaps[part]={'iPIN_endpoints':len(eligible),'exact_sequence_matches':len(eligible&exposed)}
        report[meaning]={'public_pairs':len(rows),'public_positive_pairs':sum(row[2]=='1' for row in rows),
            'public_negative_labeled_pairs':sum(row[2]=='0' for row in rows),'public_endpoints':len(endpoints),
            'missing_fasta_endpoints':len(missing),'exact_sequence_overlap_by_iPIN_partition':overlaps}
        sources.append(record(path))
    result={'at_utc':now(),'audit':report,'sources':sources,'test_pairs_read':False,'test_truth_read':False,
        'scope':'Exact sequence identity of endpoints only; no similarity/component or protected exact-pair audit',
        'interpretation':'Any exact test-endpoint match disproves an unseen-endpoint guarantee for the original external model. It is retained in the requested descriptive comparison. Absence of an exact match does not establish absence of homologous or PLM-pretraining exposure.',
        'checkpoint_history_caveat':'Based on the training/validation files named by the pinned public Bernett configuration, not an independently authenticated complete checkpoint training log.'}
    write('/output/ORIGINAL_EXPOSURE_AUDIT.json',result); print(result,flush=True)

if __name__=='__main__':
    main()
