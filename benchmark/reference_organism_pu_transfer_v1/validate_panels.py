"""Independently check labels, sequences, source exclusions and global uniqueness."""
from collections import Counter, defaultdict
from study_utils import *


def main():
    require_container()
    selection = read(OUT/'PANEL_SELECTION.json')
    check_records(selection['inputs']+selection['outputs'])
    require(sha(OUT/'published_pairs.csv') == CONFIG['published_pairs_sha256'], 'P copy differs')
    original = table(PARENT/'published_pairs.csv')
    expected = {r['pair_id']:(r['reference_sequence_sha256'],r['human_sequence_sha256']) for r in original}
    rows = table(OUT/'panels.csv')
    seqs = load_gzip(OUT/'selected_sequences.json.gz')
    raw = load_gzip(ROOT/'benchmark/host_pathogen_transfer_v1/local/source_parsed_v2.json.gz')
    query_hashes = {q for q,h in expected.values()}
    human_pool = {v['sequence_sha256']:v for v in raw['proteins'].values() if v['taxid']==9606}
    forbidden = {(r['pathogen'],r['human']) for r in raw['exclusions'] if r['pathogen'] in query_hashes}
    forbidden |= set(expected.values())
    forbidden |= {(h,h) for h in query_hashes}
    seen, groups, labels = set(), defaultdict(list), Counter()
    for i,r in enumerate(rows):
        require(int(r['row_index']) == i, 'Row index misaligned')
        require(r['panel_id'] in expected and r['positive_pair_id']==r['panel_id'], 'Unknown P anchor')
        q,h = r['query_sequence_sha256'],r['partner_sequence_sha256']
        require(q == expected[r['panel_id']][0] and h in human_pool, 'Endpoint outside source scope')
        require(r['query_taxid']=='559292' and r['partner_taxid']=='9606', 'Unexpected taxid')
        key=tuple(sorted((q,h)))
        require(key not in seen, 'Repeated complete pair')
        seen.add(key)
        require(r['pair_key']=='|'.join(key), 'Pair key mismatch')
        require(q in seqs and h in seqs and seqs[h]==human_pool[h]['sequence'], 'Missing or changed sequence')
        if r['label']=='P':
            require((q,h)==expected[r['panel_id']], 'A P was changed')
        else:
            require(r['label']=='U' and (q,h) not in forbidden, 'U overlaps reported evidence')
            anchor = human_pool[expected[r['panel_id']][1]]
            candidate = human_pool[h]
            length = .5 <= candidate['length']/anchor['length'] <= 2
            cuts = (3,10,30)
            same_bin = sum(candidate['association_degree']>=c for c in cuts)==sum(anchor['association_degree']>=c for c in cuts)
            tier = 0 if length and same_bin else 1 if length else 2 if same_bin else 3
            require(int(r['matched_tier'])==tier, 'Wrong matching tier')
            require(r['matched_anchor_sequence_sha256']==expected[r['panel_id']][1], 'Wrong matching anchor')
        labels[r['label']]+=1
        groups[r['panel_id']].append(r)
    require(set(groups)==set(expected), 'Missing or extra positive panel')
    for pid,rr in groups.items():
        require(Counter(r['label'] for r in rr)=={'P':1,'U':100}, 'Wrong per-P ratio')
    require(labels=={'P':1555,'U':155500} and len(rows)==157055, 'Wrong requested totals')
    require({r[k] for r in rows for k in ('query_sequence_sha256','partner_sequence_sha256')}==set(seqs), 'Sequence set does not match panels')
    for h,s in seqs.items():
        require(hashlib.sha256(s.encode()).hexdigest()==h and 50<=len(s)<=2000 and set(s)<=set('ACDEFGHIKLMNPQRSTVWY'), 'Invalid sequence')
    parent_sequences = load_gzip(PARENT/'published_sequences.json.gz')
    require(all(seqs[q]==parent_sequences['559292:'+q]['sequence'] for q in query_hashes), 'Reference sequence changed')
    failed_second = {r['pair_id'] for r in table(PARENT/'assay_comparison.csv') if r['confirmed']=='False'}
    require(len(failed_second)==39 and failed_second<=set(groups), 'Previously reported P relabeled or omitted')
    write_json(OUT/'PANEL_VALIDATION.json', {'at_utc':now(),'status':'passed','selection':record(OUT/'PANEL_SELECTION.json'),
        'P':1555,'U':155500,'total_pairs':157055,'per_P_U':100,'unique_P':1555,'unique_U':155500,
        'P_U_overlap':0,'reported_pairs_in_U':0,'reused_U_pairs':0,'all_original_P_retained':True,
        'all_39_assay_unconfirmed_remain_P':True,'sequence_hashes_and_taxids_verified':True,
        'protected_test_records_read':False,'validator':record(Path(__file__))})
    print('Independent panel validation passed: 1,555 P; 155,500 distinct U; exactly 100 U per P',flush=True)


if __name__=='__main__':
    main()
