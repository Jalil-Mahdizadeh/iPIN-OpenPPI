"""Deterministically select the external panels without loading model scores."""
from collections import Counter, defaultdict
import gzip
from study_utils import *

def main():
    require_container()
    audit = read(OUT / 'SOURCE_PARSING_v2.json')
    check_records([s['parsed_source'] for s in audit['summaries']])
    rows, target_rows, protein_rows, evidence, sequence_values, summaries = [], [], {}, {}, {}, []
    for species in CONFIG['species']:
        with gzip.open(LOCAL / (species['id'] + '_parsed_v2.json.gz'), 'rt') as f:
            data = json.load(f)
        proteins = data['proteins']
        exclusion, partners, by_pair = defaultdict(set), defaultdict(set), {}
        for a, b in data['exclusions']:
            exclusion[a].add(b)
            exclusion[b].add(a)
        for p in data['positives']:
            a, b = p['a'], p['b']
            partners[a].add(b)
            partners[b].add(a)
            by_pair[tuple(sorted((a, b)))] = p['evidence']
        candidates = sorted((q for q in proteins if len(partners[q]) >= CONFIG['minimum_positive_partners']),
                            key=lambda q: keyed('target', species['id'], q))
        selected, tier_counts, not_enough = [], Counter(), 0
        for q in candidates:
            available = set(proteins) - exclusion[q] - {q}
            if len(available) < CONFIG['background_U_per_target'] + CONFIG['matched_U_per_target']:
                not_enough += 1
                continue
            positives = sorted(partners[q], key=lambda p: keyed('P', species['id'], q, p))[:CONFIG['maximum_positive_partners']]
            background = sorted(available, key=lambda p: keyed('background', species['id'], q, p))[:CONFIG['background_U_per_target']]
            available.difference_update(background)
            orders = {}
            for anchor in positives:
                length = proteins[anchor]['length']
                dbin = degree_bin(proteins[anchor]['association_degree'])
                def tier(p):
                    l = .5 <= proteins[p]['length'] / length <= 2
                    d = degree_bin(proteins[p]['association_degree']) == dbin
                    return 0 if l and d else 1 if l else 2 if d else 3
                orders[anchor] = sorted(((tier(p), keyed('matched', species['id'], q, anchor, p), p) for p in available), reverse=True)
            matched, used = [], set()
            for j in range(CONFIG['matched_U_per_target']):
                anchor = positives[j % len(positives)]
                while orders[anchor][-1][2] in used:
                    orders[anchor].pop()
                tier, _, p = orders[anchor].pop()
                used.add(p)
                matched.append((p, anchor, tier))
                tier_counts[tier] += 1
            target_id = species['id'] + ':' + proteins[q]['accession']
            target_rows.append(dict(species=species['id'], taxid=species['taxid'], target_id=target_id,
                target_accession=proteins[q]['accession'], target_sequence_sha256=q,
                eligible_P=len(partners[q]), selected_P=len(positives), background_U=len(background),
                matched_U=len(matched), available_U=len(available) + len(background)))
            nominated = [(p, 'P', '', '', '') for p in positives]
            nominated += [(p, 'U', 'background', '', '') for p in background]
            nominated += [(p, 'U', 'matched', anchor, tier) for p, anchor, tier in matched]
            for p, label, stratum, anchor, tier in nominated:
                pair_key = '|'.join(sorted((q, p)))
                evidence_key = species['id'] + ':' + pair_key
                if label == 'P':
                    evidence[evidence_key] = by_pair[tuple(sorted((q, p)))]
                rows.append(dict(row_index=len(rows), species=species['id'], taxid=species['taxid'],
                    target_id=target_id, query_uniprot=proteins[q]['accession'], partner_uniprot=proteins[p]['accession'],
                    query_sequence_sha256=q, partner_sequence_sha256=p, query_sequence_length=proteins[q]['length'],
                    partner_sequence_length=proteins[p]['length'], label=label, stratum=stratum,
                    matched_anchor_sequence_sha256=anchor, matched_tier=tier, pair_key=pair_key,
                    evidence_key=evidence_key if label == 'P' else ''))
                for h in (q, p):
                    v = proteins[h]
                    protein_rows[species['id'], h] = dict(species=species['id'], taxid=species['taxid'],
                        accession=v['accession'], aliases=';'.join(v['aliases']), name=v['name'],
                        sequence_sha256=h, length=v['length'], association_degree=v['association_degree'],
                        eligible_positive_degree=v['eligible_positive_degree'])
                    if h in sequence_values and sequence_values[h] != v['sequence']:
                        raise RuntimeError('Sequence hash collision')
                    sequence_values[h] = v['sequence']
            selected.append(q)
            if len(selected) == CONFIG['targets_per_species']:
                break
        summaries.append(dict(species=species['id'], eligible_targets=len(candidates),
            selected_targets=len(selected), insufficient_candidate_pool_skips=not_enough,
            matched_tier_counts=dict(tier_counts)))
        print(summaries[-1], flush=True)
    if not rows:
        raise RuntimeError('No feasible panels; inspect source evidence before changing any rule')
    write_csv(OUT / 'panels.csv', rows)
    write_csv(OUT / 'targets.csv', target_rows)
    write_csv(OUT / 'proteins.csv', [protein_rows[k] for k in sorted(protein_rows)])
    for name, value in (('selected_evidence.json.gz', evidence), ('selected_sequences.json.gz', sequence_values)):
        with gzip.open(OUT / name, 'xt') as f:
            json.dump(value, f, sort_keys=True)
    write_json(OUT / 'PANEL_SELECTION.json', dict(at_utc=now(), species=summaries,
        pairs=len(rows), P=sum(r['label'] == 'P' for r in rows), U=sum(r['label'] == 'U' for r in rows),
        unique_sequences=len(sequence_values), total_residues=sum(map(len, sequence_values.values())),
        max_length=max(map(len, sequence_values.values())), model_scores_read=False,
        inputs=[record(OUT / 'PROTOCOL.md'), record(OUT / 'config.json'), record(OUT / 'SOURCE_PARSING_v2.json')],
        outputs=[record(OUT / p) for p in ('panels.csv', 'targets.csv', 'proteins.csv',
                 'selected_evidence.json.gz', 'selected_sequences.json.gz')],
        script=record(Path(__file__))))

if __name__ == '__main__':
    main()
