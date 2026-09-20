"""Metadata feasibility and full evidence projection from original IntAct XML.

No predictor, human pair file, or embeddings are opened. Original n-ary records
are expanded only into an exclusion set, never into positive labels.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import gzip
from itertools import combinations
import sys
import xml.etree.ElementTree as ET
import zipfile
from study_utils import *

sys.path.insert(0, str(ROOT / 'src'))
from ipin_openppi.ingestion import intact as xml

AMINO = set('ACDEFGHIKLMNPQRSTVWY')
OBO = ROOT / 'data/raw/intact/2026-01-09/cv/intact.obo'

def descendants(root):
    parents = defaultdict(set)
    term = None
    for line in OBO.read_text().splitlines():
        if line == '[Term]':
            term = None
        elif line.startswith('id: '):
            term = line[4:].strip()
        elif line.startswith('is_a: ') and term:
            parents[term].add(line[6:].split()[0])
    result = {root}
    while True:
        new = {t for t, ps in parents.items() if ps & result} - result
        if not new:
            return result
        result.update(new)

TAGS, TWO_HYBRID = descendants('MI:0507'), descendants('MI:0018')

def protein(p, species):
    if not p or p['taxid'] != species['taxid'] or p['molecule_type_ac'] != 'MI:0326':
        return None
    if (p['primary_db'] or '').lower() not in ('uniprotkb', 'uniprot'):
        return None
    seq = p['sequence'] or ''
    if not seq:
        return None
    return dict(accession=p['primary_id'], sequence=seq,
                sequence_sha256=hashlib.sha256(seq.encode()).hexdigest(),
                length=len(seq), taxid=p['taxid'], name=p['names']['short'] or p['names']['full'] or '')

def parse_species(species):
    out = LOCAL / (species['id'] + '_parsed_v2.json.gz')
    if out.exists():
        raise RuntimeError('Refusing to replace parsed source')
    seen = defaultdict(dict)
    excluded = set()
    positive = defaultdict(list)
    counter, methods, feature_types, type_counts = Counter(), Counter(), Counter(), Counter()
    archive = LOCAL / species['archive']
    def register(p):
        v = protein(p, species)
        if v:
            seen[v['accession']][v['sequence_sha256']] = v
        return v
    with zipfile.ZipFile(archive) as z:
        for member in sorted(z.namelist()):
            if not member.endswith('.xml'):
                continue
            stack, interactors, experiments = [], {}, {}
            entry = 0
            with z.open(member) as f:
                for event, e in ET.iterparse(f, events=('start', 'end')):
                    tag = xml._local(e.tag)
                    if event == 'start':
                        stack.append(tag)
                        if tag == 'entry':
                            entry += 1
                            interactors, experiments = {}, {}
                        continue
                    parent = stack[-2] if len(stack) > 1 else None
                    if tag == 'interactor':
                        p = xml._parse_interactor(e)
                        interactors[p['source_interactor_id']] = p
                        register(p)
                        if parent == 'interactorList':
                            e.clear()
                    elif tag == 'experimentDescription':
                        v = xml._parse_experiment(e)
                        experiments[v['source_experiment_id']] = v
                        if parent == 'experimentList':
                            e.clear()
                    elif tag == 'interaction':
                        v = xml._parse_interaction(e, interactors)
                        counter['source_interactions'] += 1
                        type_counts[v['interaction_type_ac'] or 'missing'] += 1
                        pp = [register(p['interactor']) for p in v['participants']]
                        good = [p for p in pp if p]
                        for a, b in combinations(good, 2):
                            if a['sequence_sha256'] != b['sequence_sha256']:
                                excluded.add(tuple(sorted((a['sequence_sha256'], b['sequence_sha256']))))
                        reasons = []
                        if len(pp) != 2:
                            reasons.append('not_binary')
                        elif not all(pp):
                            reasons.append('wrong_species_type_or_identity')
                        exp = [experiments[x] for x in v['experiment_refs'] if x in experiments]
                        binary_two_hybrid = (v['interaction_type_ac'] in ('MI:0407', 'MI:0915', 'MI:0914')
                            and any(x['detection_method_ac'] in TWO_HYBRID for x in exp))
                        if v['interaction_type_ac'] != 'MI:0407' and not binary_two_hybrid:
                            reasons.append('not_direct_or_binary_two_hybrid')
                        if v['negative'] or member.endswith('_negative.xml'):
                            reasons.append('negative_record')
                        if (v['modelled'] or '').lower() == 'true':
                            reasons.append('modelled')
                        if (v['intramolecular'] or '').lower() == 'true':
                            reasons.append('intramolecular')
                        if v['expansion_method_ac'] or v['expansion_method_name']:
                            reasons.append('expanded')
                        features = [f for p in v['participants'] for f in p['features']]
                        feature_types.update((f['type_name'] or f['type_ac'] or 'unknown') for f in features)
                        if any(f['type_ac'] not in TAGS for f in features):
                            reasons.append('recorded_non_tag_features')
                        if len(good) == 2 and good[0]['sequence_sha256'] == good[1]['sequence_sha256']:
                            reasons.append('identical_sequence_pair')
                        pubs = sorted({p for x in exp for p in x['publication_ids'] if p.startswith('pubmed:')})
                        if not pubs:
                            reasons.append('no_pubmed_provenance')
                        counter.update('excluded_' + r for r in reasons)
                        if not reasons:
                            pair = tuple(sorted(p['sequence_sha256'] for p in good))
                            ac = next((x['id'] for x in v['xrefs'] if x['db'] == 'intact' and x['ref_type'] == 'identity'), v['local_id'])
                            method_ids = sorted({x['detection_method_ac'] or '' for x in exp})
                            method_names = sorted({x['detection_method_name'] or '' for x in exp})
                            methods.update(method_names)
                            positive[pair].append(dict(archive=species['archive'], member=member, entry=entry,
                                interaction_id=ac, participant_accessions=[p['accession'] for p in good],
                                publication_ids=pubs, detection_method_ids=method_ids, detection_method_names=method_names,
                                negative_flag=v['negative'], participant_feature_count=len(features),
                                feature_type_ids=sorted({f['type_ac'] for f in features}), non_tag_feature_count=0,
                                interaction_type=v['interaction_type_ac'], binary_two_hybrid=binary_two_hybrid))
                            counter['eligible_direct_records_before_sequence_filter'] += 1
                        e.clear()
                    elif tag == 'entry':
                        e.clear()
                    stack.pop()
            print(f"Parsed {species['id']} {member}; {counter['source_interactions']:,} source interactions", flush=True)
    conflicted = [a for a, values in seen.items() if len(values) != 1]
    proteins = {}
    for a, values in sorted(seen.items()):
        if len(values) != 1:
            continue
        p = next(iter(values.values()))
        if not CONFIG['minimum_sequence_length'] <= p['length'] <= CONFIG['maximum_sequence_length']:
            counter['accessions_excluded_by_length'] += 1
            continue
        if not set(p['sequence']) <= AMINO:
            counter['accessions_excluded_by_alphabet'] += 1
            continue
        h = p['sequence_sha256']
        if h not in proteins:
            proteins[h] = {**p, 'aliases': []}
        proteins[h]['aliases'].append(a)
    valid_accessions = {a for p in proteins.values() for a in p['aliases']}
    positives = []
    for pair, evidence in sorted(positive.items()):
        allowed = [r for r in evidence if set(r['participant_accessions']) <= valid_accessions]
        if set(pair) <= proteins.keys() and allowed:
            positives.append(dict(a=pair[0], b=pair[1], evidence=allowed))
    exclusions = [p for p in sorted(excluded) if set(p) <= proteins.keys()]
    degree, pdegree = Counter(), Counter()
    for a, b in exclusions:
        degree.update((a, b))
    for p in positives:
        pdegree.update((p['a'], p['b']))
    for h, p in proteins.items():
        p['association_degree'] = degree[h]
        p['eligible_positive_degree'] = pdegree[h]
    targets = [h for h in proteins if pdegree[h] >= CONFIG['minimum_positive_partners']]
    summary = dict(species=species['id'], name=species['name'], taxid=species['taxid'],
        source_archive=record(archive), counts=dict(counter), interaction_types=dict(type_counts),
        feature_types=dict(feature_types), eligible_detection_methods=dict(methods),
        sequence_conflict_accessions=conflicted, source_accessions=len(seen),
        eligible_unique_sequences=len(proteins), positive_pairs=len(positives),
        exclusion_pairs=len(exclusions), targets_with_at_least_two_P=len(targets))
    with gzip.open(out, 'xt') as f:
        json.dump(dict(species=species, proteins=proteins, positives=positives,
                       exclusions=exclusions, summary=summary), f, sort_keys=True)
    summary['parsed_source'] = record(out)
    write_json(OUT / (species['id'] + '_SOURCE_AUDIT_v2.json'), summary)
    return summary

def main():
    require_container()
    sources = read(OUT / 'SOURCES.json')
    check_records([s['artifact'] for s in sources['sources']])
    summaries = [parse_species(s) for s in CONFIG['species']]
    write_csv(OUT / 'source_feasibility_v2.csv', [{k: s[k] for k in ('species', 'taxid', 'source_accessions',
        'eligible_unique_sequences', 'positive_pairs', 'exclusion_pairs', 'targets_with_at_least_two_P')} for s in summaries])
    write_json(OUT / 'SOURCE_PARSING_v2.json', dict(at_utc=now(), summaries=summaries,
        parser=record(Path(__file__)), original_parser=record(Path(xml.__file__)),
        vocabulary=record(OBO), allowed_tag_feature_types=sorted(TAGS), two_hybrid_methods=sorted(TWO_HYBRID),
        protected_test_records_read=False, model_scores_read=False))

if __name__ == '__main__':
    main()
