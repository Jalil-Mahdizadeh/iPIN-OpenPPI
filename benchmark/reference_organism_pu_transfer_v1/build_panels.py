"""Retain all 1,555 P and assign 100 globally distinct metadata-matched U each."""
from collections import Counter, defaultdict
import shutil
import numpy as np
from study_utils import *


def main():
    require_container()
    require(not (OUT / 'PANEL_SELECTION.json').exists(), 'Panel already built')
    LOCAL.mkdir(exist_ok=True)
    source_path = ROOT / 'benchmark/host_pathogen_transfer_v1/SOURCE_PARSING_v2.json'
    require(sha(source_path) == CONFIG['source_manifest_sha256'], 'Source manifest changed')
    source = read(source_path)
    check_records([source['parsed_source']] + source['sources'])
    parent_manifest = read(PARENT / 'FINAL_MANIFEST.json')
    wanted = {'published_pairs.csv', 'published_proteins.csv', 'published_sequences.json.gz',
              'published_evidence.json.gz', 'assay_comparison.csv', 'SOURCE_PREPARATION.json'}
    parent_records = [r for r in parent_manifest['files'] if Path(r['path']).name in wanted]
    require(len(parent_records) == len(wanted), 'Parent provenance incomplete')
    check_records(parent_records)
    require(sha(PARENT / 'published_pairs.csv') == CONFIG['published_pairs_sha256'], 'P set changed')
    positives = table(PARENT / 'published_pairs.csv')
    require(len(positives) == CONFIG['expected_P'], 'Unexpected P count')
    require(all(r['label'] == 'P' and int(r['reference_taxid']) == 559292 and int(r['human_taxid']) == 9606 for r in positives), 'Unexpected P labels/taxids')
    source_data = load_gzip(ROOT / source['parsed_source']['path'])
    original = load_gzip(PARENT / 'published_sequences.json.gz')
    targets = {r['reference_sequence_sha256'] for r in positives}
    humans = {v['sequence_sha256']: v for v in source_data['proteins'].values() if v['taxid'] == 9606}
    # Exclude sequence-equivalent reference records regardless of source taxid label.
    exclusions = defaultdict(set)
    for r in source_data['exclusions']:
        if r['pathogen'] in targets:
            exclusions[r['pathogen']].add(r['human'])
    for r in positives:
        exclusions[r['reference_sequence_sha256']].add(r['human_sequence_sha256'])
    by_target = defaultdict(list)
    for r in positives:
        by_target[r['reference_sequence_sha256']].append(r)
    human_order = sorted(humans)
    human_index = {h:i for i,h in enumerate(human_order)}
    lengths = np.array([humans[h]['length'] for h in human_order])
    bins = np.array([degree_bin(humans[h]['association_degree']) for h in human_order])
    sequences = {h: original['559292:' + h]['sequence'] for h in targets}
    allocations, tier_counts, target_rows = {}, Counter(), []
    for ordinal, q in enumerate(sorted(targets), 1):
        ps = sorted(by_target[q], key=lambda r: keyed('P_order', r['pair_id']))
        allowed = np.array([h not in exclusions[q] and h != q for h in human_order])
        require(int(allowed.sum()) >= len(ps)*CONFIG['U_per_P'], 'Not enough globally distinct U for a target')
        used = ~allowed.copy()
        orders, tiers, positions = {}, {}, {}
        for p in ps:
            pid = p['pair_id']
            anchor = human_index[p['human_sequence_sha256']]
            length_match = (lengths >= .5*lengths[anchor]) & (lengths <= 2*lengths[anchor])
            degree_match = bins == bins[anchor]
            tier = np.where(length_match & degree_match, 0, np.where(length_match, 1, np.where(degree_match, 2, 3))).astype(np.int8)
            rng = np.random.Generator(np.random.PCG64(int(keyed('U_order', pid), 16)))
            order = rng.permutation(len(human_order))
            order = order[allowed[order]]
            orders[pid] = np.concatenate([order[tier[order] == t] for t in range(4)])
            tiers[pid], positions[pid], allocations[pid] = tier, 0, []
        for _ in range(CONFIG['U_per_P']):
            for p in ps:
                pid = p['pair_id']
                order, position = orders[pid], positions[pid]
                while position < len(order) and used[order[position]]:
                    position += 1
                require(position < len(order), 'Allocation exhausted candidate pool')
                i = int(order[position])
                used[i], positions[pid] = True, position + 1
                tier = int(tiers[pid][i])
                allocations[pid].append((human_order[i], tier))
                tier_counts[tier] += 1
        target_rows.append({'target_id': q, 'P': len(ps), 'U': len(ps)*CONFIG['U_per_P'],
                            'eligible_U': int(allowed.sum()), 'source_excluded_humans': len(exclusions[q] & set(humans))})
        if ordinal % 100 == 0:
            print(f'Allocated {ordinal}/{len(targets)} reference targets', flush=True)
    panels, assignment_rows = [], []
    for p in positives:
        q, pid = p['reference_sequence_sha256'], p['pair_id']
        nominated = [(p['human_sequence_sha256'], 'P', '')] + [(h, 'U', t) for h,t in allocations[pid]]
        for h, label, tier in nominated:
            sequences[h] = humans[h]['sequence']
            panels.append({'row_index': len(panels), 'panel_id': pid, 'positive_pair_id': pid,
                'species': 'human_s288c_reference', 'target_id': q, 'query_taxid': 559292, 'partner_taxid': 9606,
                'query_sequence_sha256': q, 'partner_sequence_sha256': h,
                'query_sequence_length': len(sequences[q]), 'partner_sequence_length': humans[h]['length'],
                'pair_key': '|'.join(sorted((q,h))), 'label': label,
                'stratum': 'matched' if label == 'U' else '', 'matched_tier': tier,
                'matched_anchor_sequence_sha256': p['human_sequence_sha256'] if label == 'U' else ''})
        assignment_rows.append({'positive_pair_id':pid, 'target_id':q, 'P':1, 'U':len(allocations[pid])})
    require(len(panels) == CONFIG['expected_P']*(1+CONFIG['U_per_P']), 'Unexpected panel size')
    require(len({r['pair_key'] for r in panels}) == len(panels), 'Repeated sequence pair')
    for name in ('published_pairs.csv','published_evidence.json.gz'):
        require(not (OUT / name).exists(), 'Refusing to overwrite source copy')
        shutil.copyfile(PARENT / name, OUT / name)
    write_csv(OUT / 'panels.csv', panels)
    write_csv(OUT / 'positive_assignments.csv', assignment_rows)
    write_csv(OUT / 'targets.csv', target_rows)
    write_csv(OUT / 'eligible_human_pool.csv', [{'sequence_sha256':h, 'taxid':9606,
        'length':v['length'], 'source_accessions':';'.join(sorted(v['aliases'])),
        'association_degree':v['association_degree']} for h,v in sorted(humans.items())])
    write_csv(OUT / 'excluded_pairs.csv', [{'reference_sequence_sha256':q,'human_sequence_sha256':h}
        for q in sorted(exclusions) for h in sorted(exclusions[q]) if h in humans])
    parent_proteins = {r['sequence_sha256']:r for r in table(PARENT / 'published_proteins.csv') if r['taxid'] == '559292'}
    protein_rows = []
    for h,s in sorted(sequences.items()):
        require(hashlib.sha256(s.encode()).hexdigest() == h, 'Sequence digest mismatch')
        require(CONFIG['minimum_sequence_length'] <= len(s) <= CONFIG['maximum_sequence_length'] and set(s) <= set('ACDEFGHIKLMNPQRSTVWY'), 'Sequence outside eligibility')
        is_reference = h in targets
        protein_rows.append({'sequence_sha256':h,'taxid':559292 if is_reference else 9606,
            'length':len(s), 'source_accessions':parent_proteins[h]['source_accessions'] if is_reference else ';'.join(sorted(humans[h]['aliases'])),
            'association_degree':len(exclusions[h]) if is_reference else humans[h]['association_degree']})
    write_csv(OUT / 'proteins.csv', protein_rows)
    write_gzip(OUT / 'selected_sequences.json.gz', sequences)
    prior_unconfirmed = {r['pair_id'] for r in table(PARENT / 'assay_comparison.csv') if r['confirmed'] == 'False'}
    require(prior_unconfirmed <= {r['pair_id'] for r in positives}, 'An original P was lost')
    outputs = ['published_pairs.csv','published_evidence.json.gz','panels.csv','positive_assignments.csv',
               'targets.csv','eligible_human_pool.csv','excluded_pairs.csv','proteins.csv','selected_sequences.json.gz']
    inputs = [record(source_path), source['parsed_source'], *source['sources'], *parent_records,
              record(OUT/'config.json'), record(OUT/'PROTOCOL.md'), record(Path(__file__)), record(OUT/'study_utils.py')]
    write_json(OUT / 'PANEL_SELECTION.json', {'at_utc':now(),'P':len(positives),
        'U':sum(r['label']=='U' for r in panels),'pairs':len(panels), 'panels':len(positives),
        'reference_targets':len(targets),'eligible_human_sequences':len(humans),
        'selected_human_sequences':len(set(sequences)-targets),'unique_sequences':len(sequences),
        'total_residues':sum(map(len,sequences.values())), 'U_per_P':CONFIG['U_per_P'],
        'globally_distinct_U':True,'reused_U_pairs':0,'P_U_overlap':0,
        'original_P_all_preserved':True,'original_assay_unconfirmed_retained_as_P':len(prior_unconfirmed),
        'matched_tier_counts':dict(tier_counts),'inputs':inputs,'outputs':[record(OUT/n) for n in outputs],
        'selection_uses_model_scores':False,'prior_P_model_scores_seen_before_this_design':True,
        'new_U_model_scores_seen':False,'U_is_unreported_in_declared_source_not_verified_negative':True,
        'numpy':np.__version__, 'random_generator':'PCG64; SHA256 seed per P; round-robin allocation'})
    print(f'Built {len(positives):,} P + {len(panels)-len(positives):,} globally distinct U', flush=True)


if __name__ == '__main__':
    main()
