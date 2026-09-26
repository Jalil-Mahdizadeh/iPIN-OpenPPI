"""Freeze source-supported human pair evidence before split construction/model use."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from study import check, digest, now, read, record, write

Y2H = ['MI:0018', 'MI:0397', 'MI:0398', 'MI:0399', 'MI:1112', 'MI:1356']

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    root, out = args.repo, args.output
    (out / 'private').mkdir(parents=True, exist_ok=True)
    (out / 'work').mkdir(parents=True, exist_ok=True)
    check(not (out / 'audit/SOURCE_AUDIT.json').exists(), 'Source audit already frozen')
    c = duckdb.connect()
    c.execute('set threads=8')
    paths = {
        'e': 'data/staging/primary_sources_v1/intact_imex/evidence_records',
        'm': 'data/canonical/primary_reconciliation_v1/participant_sequence_mappings',
        's': 'data/canonical/primary_reconciliation_v1/evidence_mapping_summaries',
        'f': 'data/staging/primary_sources_v1/intact_imex/participant_features',
        'mu': 'data/staging/primary_sources_v1/intact_imex/mutations',
        'q': 'data/staging/primary_sources_v1/uniprot/protein_sequences',
        'ids': 'data/staging/primary_sources_v1/uniprot/identifier_mappings',
        'pv': 'data/staging/primary_sources_v1/huri/source_pair_views',
    }
    inputs = []
    for name, path in paths.items():
        files = sorted((root / path).glob('*.parquet'))
        check(bool(files), 'Missing source ' + path)
        inputs.extend(record(f, root) for f in files)
        c.execute(f"create view {name} as select * from read_parquet('{root / path}/*.parquet')")
    # Do not equate annotation absence with verified wild type. Explicit mutations,
    # sequence changes and state-changing features are excluded; uncertainty stays.
    c.execute("""create temp table excluded_evidence as
      select distinct evidence_id from f where
        regexp_matches(lower(coalesce(feature_type_name,'')),
          'mutation|deletion|insertion|variant|phosphorylat|acetylat|methylat|ubiquitinyl|glycosyl')
        or nullif(original_sequence,'') is not null
        or nullif(resulting_sequence,'') is not null
      union select e.evidence_id from e join mu on e.source_record_id=mu.interaction_ac""")
    c.execute("""create temp table eligible_mapping as
      select evidence_id, count(*) n,
        min(mapped_sequence_sha256) a, max(mapped_sequence_sha256) b,
        bool_and(taxid=9606 and reference_sequence_usable and canonical_projection_usable
          and mapped_sequence_sha256=canonical_projection_sequence_sha256
          and coalesce(sequence_change_feature_count,0)=0) exact_canonical
      from m where source_key='intact_imex' group by evidence_id""")
    methods = ','.join("'" + x + "'" for x in Y2H)
    common = """s.binary_two_human_proteins and s.reference_pair_usable
      and s.canonical_pair_usable and s.observation_state='positive'
      and not s.original_nary and not e.is_expanded_projection
      and coalesce(e.negative_flag,false)=false and em.n=2 and em.exact_canonical
      and em.a<>em.b and not exists(select 1 from excluded_evidence x where x.evidence_id=e.evidence_id)"""
    # Quantitative fragment screens are kept out until their positive calls are
    # independently reconciled. Neither affinity measurements nor database presence
    # alone establish a primary full-reference interaction label.
    evidence = c.sql(f"""select e.evidence_id, em.a, em.b, e.source_release,
      e.publication_ids, e.detection_method_ac method_ac, e.detection_method_name method_name,
      e.interaction_semantics, e.raw_file_path, e.raw_file_sha256, e.raw_locator,
      e.source_record_id, e.license_id, e.attribution,
      case when e.detection_method_ac in ({methods}) then 'binary_two_hybrid'
        else 'curated_direct_binary' end tier
      from e join s using(evidence_id) join eligible_mapping em using(evidence_id)
      where {common}
      and (e.detection_method_ac in ({methods}) or s.interaction_semantics='direct_binary')
      and e.detection_method_ac not in ('MI:2437')
      and not list_contains(e.publication_ids,'pubmed:36115835')
      order by e.evidence_id""").to_arrow_table()
    evidence_path = out / 'private/intact_qualified_evidence.parquet'
    pq.write_table(evidence, evidence_path, compression='zstd')
    # Match the old reference projection rule: one canonical sequence hash per
    # versionless Ensembl gene. Never collapse distinct isoforms by gene name.
    c.execute("""create temp table gene_map as select ids.identifier_versionless gene,
      min(q.sequence_sha256) h from ids join q using(uniprot_accession)
      where ids.database='Ensembl' and q.canonical and q.taxid=9606
      group by gene having count(distinct q.sequence_sha256)=1""")
    views = c.sql("""select pv.pair_view_id evidence_id, pv.source_dataset,
       least(ga.h,gb.h) a, greatest(ga.h,gb.h) b,
       pv.raw_file_path,pv.raw_file_sha256,pv.raw_locator
       from pv join gene_map ga on ga.gene=pv.member_a join gene_map gb on gb.gene=pv.member_b
       where pv.source_dataset in ('HI-II-14','HuRI','Lit-BM','Test_space_screens-19')
       and ga.h<>gb.h order by pv.pair_view_id""").to_arrow_table()
    pq.write_table(views, out / 'private/huri_qualified_views.parquet', compression='zstd')
    old = read(root / 'benchmark/tuna/data/sequences.json')
    seqs = {h: {'hash': h, 'sequence': s, 'length': len(s), 'partition': part,
                'component': comp, 'accessions': acc, 'original': True}
            for h, s, part, comp, acc in zip(old['sha256'], old['sequence'], old['partition'],
                                            old['component'], old['accessions'], strict=True)}
    qualified = defaultdict(lambda: {'sources': set(), 'tiers': set(), 'publications': set(), 'records': 0})
    for row in evidence.to_pylist():
        x = qualified[(row['a'], row['b'])]
        x['sources'].add('IntAct'); x['tiers'].add(row['tier'])
        x['publications'].update(p for p in row['publication_ids'] if p.startswith('pubmed:'))
        x['records'] += 1
    for row in views.to_pylist():
        x = qualified[(row['a'], row['b'])]
        x['sources'].add(row['source_dataset']); x['tiers'].add('released_' + row['source_dataset'])
        x['records'] += 1
    needed = set(h for pair in qualified for h in pair) - set(seqs)
    new = c.sql('select * from q where canonical and taxid=9606').to_arrow_table().to_pylist()
    invalid = Counter()
    for row in new:
        h, sequence = row['sequence_sha256'], row['sequence']
        if h not in needed:
            continue
        if not sequence or set(sequence) - set('ACDEFGHIKLMNPQRSTUVWY'):
            invalid['invalid_amino_acids'] += 1
            continue
        check(digest(sequence) == h, 'Source sequence hash mismatch')
        # Same upper length as the already qualified full-context GPU path. Longer
        # new proteins are recorded as deferred, never truncated or silently dropped.
        if len(sequence) > max(old['length']):
            invalid['beyond_qualified_full_context_length'] += 1
            continue
        if h in seqs:
            if row['uniprot_accession'] not in seqs[h]['accessions']:
                seqs[h]['accessions'].append(row['uniprot_accession'])
        else:
            seqs[h] = {'hash': h, 'sequence': sequence, 'length': len(sequence),
                       'accessions': [row['uniprot_accession']], 'original': False}
    pair_rows = []
    for (a,b), x in sorted(qualified.items()):
        if a not in seqs or b not in seqs:
            invalid['pair_with_ineligible_new_endpoint'] += 1
            continue
        pair_rows.append({'a': a, 'b': b, **{k: sorted(v) if isinstance(v,set) else v for k,v in x.items()}})
    pq.write_table(pa.Table.from_pylist(pair_rows), out / 'private/qualified_pairs.parquet', compression='zstd')
    # Existing indexes are unchanged; new hashes appended in deterministic order.
    order = list(old['sha256']) + sorted(set(seqs) - set(old['sha256']))
    write(out / 'private/sequence_candidates.json', [seqs[h] for h in order])
    for name, selected in [('all', order), ('new', order[len(old['sha256']):])]:
        with (out / f'work/{name}.fasta').open('x') as f:
            for h in selected:
                f.write('>' + h + '\n' + seqs[h]['sequence'] + '\n')
    hist = Counter('|'.join(x['sources']) for x in pair_rows)
    audit = {'at_utc': now(), 'scope': 'human-human reference-sequence binary PPI',
        'intact_qualified_evidence_rows': len(evidence), 'huri_view_rows': len(views),
        'qualified_unique_pairs_before_split': len(pair_rows),
        'original_endpoints': len(old['sha256']), 'new_candidate_endpoints': len(order)-len(old['sha256']),
        'source_membership_counts': dict(hist), 'deferred_or_ineligible': dict(invalid),
        'exact_construct_sequences_claimed': False,
        'reference_projection': 'IntAct mapped hash must equal canonical hash; unique canonical gene map for HuRI views',
        'binary_two_hybrid_methods': Y2H,
        'excluded': ['nonhuman participants', 'complex expansion', 'ambiguous/isoform projection',
                     'explicit mutant or modified evidence', 'holdup/PMID36115835 pending positive-call audit'],
        'legacy_policies_unchanged': True, 'inputs': inputs,
        'outputs': [record(f, out) for f in sorted((out/'private').iterdir()) if f.is_file()]}
    write(out / 'audit/SOURCE_AUDIT.json', audit)
    print({k:v for k,v in audit.items() if k not in ('inputs','outputs')}, flush=True)

if __name__ == '__main__':
    main()
