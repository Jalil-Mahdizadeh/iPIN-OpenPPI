"""Exact and sequence-relative exposure to actual human TRAIN/development.

Never opens human protected test pairs or truth. Protein-language-model
pretraining is outside this audit.
"""
from collections import defaultdict
import gzip
import subprocess
import numpy as np
from study_utils import *

FIELDS = 'query,target,fident,alnlen,qstart,qend,qlen,tstart,tend,tlen,evalue,bits,qcov,tcov'.split(',')

def human_data():
    folder = ROOT / 'benchmark/tuna/data'
    manifest = read(folder / 'DATA_MANIFEST.json')
    lookup = {Path(r['path']).name: r for r in manifest['outputs']}
    names = ('sequences.json', 'training.npz', 'development_00.npz', 'development_01.npz', 'development_02.npz')
    for name in names:
        if sha(folder / name) != lookup[name]['sha256']:
            raise RuntimeError('Frozen human training/development inputs changed')
    reference = read(folder / names[0])
    groups, train_ids, dev_ids = {}, set(), set()
    n = len(reference['sha256'])
    for name in names[1:]:
        with np.load(folder / name, allow_pickle=False) as d:
            if name == 'training.npz':
                records = [('TRAIN_' + s.upper(), d[s+'_a'], d[s+'_b']) for s in ('p', 'u')]
            else:
                records = [('DEV_' + label, d['a'][d['positive'] == v], d['b'][d['positive'] == v]) for label,v in [('P', True), ('U', False)]]
            for role, a, b in records:
                (train_ids if role.startswith('TRAIN') else dev_ids).update(map(int, np.unique(np.r_[a, b])))
                codes = np.minimum(a, b).astype(np.int64)*n + np.maximum(a, b)
                groups.setdefault(role, []).append(codes)
    groups = {role: np.unique(np.concatenate(values)) for role, values in groups.items()}
    return reference, train_ids, dev_ids, groups, [record(folder / name) for name in names]

def main():
    require_container()
    check_records(read(OUT / 'PANEL_SELECTION.json')['outputs'])
    rows = table(OUT / 'panels.csv')
    with gzip.open(OUT / 'selected_sequences.json.gz', 'rt') as f:
        seqs = json.load(f)
    ref, train, dev, groups, input_records = human_data()
    indices = {h: i for i,h in enumerate(ref['sha256'])}
    endpoint_rows = []
    for h in sorted(seqs):
        i = indices.get(h)
        endpoint_rows.append(dict(sequence_sha256=h, exact_TRAIN_endpoint=i in train,
            exact_DEV_endpoint=i in dev, human_catalogue_match=i is not None,
            matched_human_accessions=';'.join(ref['accessions'][i]) if i is not None else ''))
    write_csv(OUT / 'exact_endpoint_exposure.csv', endpoint_rows)
    n = len(indices)
    codes = np.array([min(indices[r['query_sequence_sha256']], indices[r['partner_sequence_sha256']])*n +
                      max(indices[r['query_sequence_sha256']], indices[r['partner_sequence_sha256']])
                      if r['query_sequence_sha256'] in indices and r['partner_sequence_sha256'] in indices else -1 for r in rows])
    flags = {role: np.isin(codes, values) for role,values in groups.items()}
    write_csv(OUT / 'exact_pair_exposure.csv', [dict(row_index=i, **{role: bool(values[i]) for role,values in flags.items()}) for i in range(len(rows))])
    binary = ROOT / 'artifacts/cache/tools/mmseqs2/18-8cc5c/mmseqs/bin/mmseqs'
    if sha(binary) != 'd5f6d96578e3dbcd1d8772bb575b112e9dd1dbf077d150914962a2356ae0d75d':
        raise RuntimeError('MMseqs2 executable changed')
    hom = LOCAL / 'homology'
    hom.mkdir()
    query, target, matches = hom/'query.fasta', hom/'train.fasta', hom/'matches.tsv'
    with query.open('x') as f:
        f.write(''.join(f'>{h}\n{seqs[h]}\n' for h in sorted(seqs)))
    with target.open('x') as f:
        f.write(''.join(f">{ref['sha256'][i]}\n{ref['sequence'][i]}\n" for i in sorted(train)))
    command = [str(binary), 'easy-search', str(query), str(target), str(matches), str(hom/'tmp'),
               '--threads', '8', '-s', '7.5', '-e', '0.001', '--max-seqs', str(len(train)),
               '--max-accept', str(len(train)), '--max-rejected', str(len(train)),
               '--alignment-mode', '3', '--format-output', ','.join(FIELDS)]
    write_json(OUT / 'HOMOLOGY_INPUT_FREEZE.json', dict(at_utc=now(), input_records=input_records,
        script=record(Path(__file__)), reference_endpoints=len(train), external_sequences=len(seqs),
        local_files=[record(query), record(target)], binary=record(binary), command=command,
        version=subprocess.check_output([str(binary), 'version'], text=True).strip(), protected_test_records_read=False))
    with (hom/'mmseqs.log').open('x') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    local, broad, hit_count = {}, {}, defaultdict(int)
    with matches.open() as f:
        for r in csv.DictReader(f, fieldnames=FIELDS, delimiter='\t'):
            h = r['query']
            hit_count[h] += 1
            local_key = lambda x: (float(x['bits']), float(x['fident']), x['target'])
            broad_key = lambda x: (float(x['fident']), float(x['bits']), x['target'])
            if h not in local or local_key(r) > local_key(local[h]):
                local[h] = r
            if float(r['qcov']) >= .8 and float(r['tcov']) >= .8:
                if h not in broad or broad_key(r) > broad_key(broad[h]):
                    broad[h] = r
    result = []
    for h in sorted(seqs):
        r = dict(sequence_sha256=h, reported_local_hits=hit_count[h])
        for scope, best in [('local', local.get(h)), ('both_coverage_80pct', broad.get(h))]:
            for k in FIELDS[1:]:
                r[scope+'_'+k] = best[k] if best else ''
        identity = float(broad[h]['fident']) if h in broad else None
        r['similarity_bin'] = ('no_qualifying_hit' if identity is None else 'below_30pct' if identity < .3 else
                               '30_to_50pct' if identity < .5 else '50_to_80pct' if identity < .8 else 'at_least_80pct')
        r['TRAIN_homolog_30pct_both80'] = identity is not None and identity >= .3
        result.append(r)
    write_csv(OUT / 'training_sequence_similarity.csv', result)
    write_json(OUT / 'EXPOSURE_AUDIT.json', dict(at_utc=now(), human_train_endpoints=len(train),
        human_development_endpoints=len(dev), external_sequences=len(seqs),
        exact_train_endpoints=sum(r['exact_TRAIN_endpoint'] for r in endpoint_rows),
        exact_development_endpoints=sum(r['exact_DEV_endpoint'] for r in endpoint_rows),
        exact_pair_counts={k: int(v.sum()) for k,v in flags.items()},
        similarity_bin_counts=dict(__import__('collections').Counter(r['similarity_bin'] for r in result)),
        raw_matches=record(matches), protected_test_pairs_or_truth_read=False,
        files=[record(OUT / p) for p in ['exact_endpoint_exposure.csv', 'exact_pair_exposure.csv', 'training_sequence_similarity.csv']],
        method='Exact sequence identity plus pinned local MMseqs2; not a pretraining or exhaustive homology audit'))

if __name__ == '__main__':
    main()
