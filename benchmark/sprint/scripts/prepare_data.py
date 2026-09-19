"""Prepare TRAIN-only graph and frozen sequence features, without test pairs."""
import hashlib
from pathlib import Path
import numpy as np
from common import now, read, record, sha, write
from policy import SEQUENCES_SHA, TRAINING_SHA

assert sha('/data/sequences.json') == SEQUENCES_SHA
assert sha('/data/training.npz') == TRAINING_SHA
meta = read('/data/sequences.json'); output = Path('/output')
ids = meta['sha256']; seqs = meta['sequence']; n = len(ids)
assert n == 17000 and len(set(ids)) == n and all(len(v) == n for v in meta.values())
for i, seq in enumerate(seqs):
    assert hashlib.sha256(seq.encode()).hexdigest() == ids[i]
    assert len(seq) == meta['length'][i] and len(seq) >= 20
    assert set(seq) <= set('ARNDCQEGHILKMFPSTWYVBZXUO')
with np.load('/data/training.npz', allow_pickle=False) as data:
    a, b = data['p_a'].copy(), data['p_b'].copy()
assert len(a) == len(b) == 16799 and (a != b).all()
assert min(a.min(), b.min()) >= 0 and max(a.max(), b.max()) < n
assert all(meta['partition'][int(x)] == 'train' for x in np.concatenate([a, b]))
assert len({tuple(sorted((int(x), int(y)))) for x, y in zip(a, b)}) == len(a)
with (output/'proteins.fasta').open('x') as f:
    for i, seq in enumerate(seqs): f.write(f'>p{i:05d}\n{seq}\n')
with (output/'train_positive.txt').open('x') as f:
    for x, y in zip(a, b): f.write(f'p{x:05d} p{y:05d}\n')
write(output/'endpoints.json', ids, exclusive=True)
write(output/'components.json', meta['component'], exclusive=True)
# Timing-only pilot, fixed first 512 TRAIN sequences in SHA order. Never used
# as the production HSP cache, nor for selecting algorithm parameters.
pilot = [i for i, part in enumerate(meta['partition']) if part == 'train'][:512]
with (output/'pilot.fasta').open('x') as f:
    for i in pilot: f.write(f'>p{i:05d}\n{seqs[i]}\n')
files = []
for path in sorted(output.iterdir()):
    if path.is_file():
        item = record(path); item['path'] = path.name; files.append(item)
write(output/'DATA_FREEZE.json', {'at_utc': now(), 'sequences_source_sha256': SEQUENCES_SHA,
    'training_source_sha256': TRAINING_SHA, 'files': files, 'proteins': n,
    'residues': sum(map(len, seqs)), 'max_length': max(map(len, seqs)), 'min_length': min(map(len, seqs)),
    'train_positive_pairs': len(a), 'pilot_proteins': len(pilot), 'pilot_residues': sum(len(seqs[i]) for i in pilot),
    'full_length_sequences': True, 'no_external_interactions': True,
    'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
print({'prepared': True, 'proteins': n, 'train_positive_pairs': len(a)}, flush=True)
