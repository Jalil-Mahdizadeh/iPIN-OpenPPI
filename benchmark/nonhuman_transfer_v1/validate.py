"""Independent panel/evidence and scientific metric oracles for this study.

The XML oracle does not import the production IntAct parser. The metric oracle
uses sklearn and separate fractional-cutoff/rank calculations.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import gzip
import math
import xml.etree.ElementTree as ET
import zipfile
import numpy as np
from study_utils import *

def children(e,name):
    return [x for x in e if x.tag.rsplit('}',1)[-1]==name] if e is not None else []

def child(e,name):
    return next(iter(children(e,name)),None)

def value(e,name):
    x=child(e,name)
    return (x.text or '').strip() if x is not None else ''

def cv(e):
    refs=child(e,'xref')
    for r in list(refs) if refs is not None else []:
        if r.get('db')=='psi-mi':
            return r.get('id')
    return None

def protein(e):
    if e is None:
        return None
    organism=child(e,'organism'); seq=value(e,'sequence')
    refs=child(e,'xref'); acc=None
    for r in list(refs) if refs is not None else []:
        if r.tag.rsplit('}',1)[-1]=='primaryRef' and r.get('db','').lower() in ('uniprotkb','uniprot'):
            acc=r.get('id')
    return dict(taxid=int(organism.get('ncbiTaxId')) if organism is not None else None,
        sequence_sha256=hashlib.sha256(seq.encode()).hexdigest() if seq else None,
        accession=acc,molecule_type=cv(child(e,'interactorType')))

def panel_validation():
    selection=read(OUT/'PANEL_SELECTION.json')
    check_records(selection['outputs'])
    rows=table(OUT/'panels.csv')
    with gzip.open(OUT/'selected_sequences.json.gz','rt') as f:
        sequences=json.load(f)
    with gzip.open(OUT/'selected_evidence.json.gz','rt') as f:
        evidence=json.load(f)
    for h,s in sequences.items():
        assert hashlib.sha256(s.encode()).hexdigest()==h
        assert CONFIG['minimum_sequence_length']<=len(s)<=CONFIG['maximum_sequence_length']
        assert set(s)<=set('ACDEFGHIKLMNPQRSTVWY')
    groups=defaultdict(list)
    positives,unlabeled=defaultdict(set),defaultdict(set)
    for i,r in enumerate(rows):
        assert int(r['row_index'])==i
        assert r['query_sequence_sha256']!=r['partner_sequence_sha256']
        assert int(r['query_sequence_length'])==len(sequences[r['query_sequence_sha256']])
        assert int(r['partner_sequence_length'])==len(sequences[r['partner_sequence_sha256']])
        assert r['pair_key']=='|'.join(sorted((r['query_sequence_sha256'],r['partner_sequence_sha256'])))
        groups[r['target_id']].append(r)
        (positives if r['label']=='P' else unlabeled)[r['species']].add(r['pair_key'])
    for t,rr in groups.items():
        assert len({r['partner_sequence_sha256'] for r in rr})==len(rr)
        assert 2<=sum(r['label']=='P' for r in rr)<=CONFIG['maximum_positive_partners']
        assert sum(r['stratum']=='background' for r in rr)==CONFIG['background_U_per_target']
        assert sum(r['stratum']=='matched' for r in rr)==CONFIG['matched_U_per_target']
    parsing=read(OUT/'SOURCE_PARSING_v2.json')
    tags=set(parsing['allowed_tag_feature_types']); hybrid=set(parsing['two_hybrid_methods'])
    requested={}
    for key, records in evidence.items():
        for r in records:
            source=(r['archive'],r['member'],r['entry'],r['interaction_id'])
            requested[source]=(key,r)
    found=set(); checked_records=0; forbidden_u=0
    for species in CONFIG['species']:
        assert not (positives[species['id']] & unlabeled[species['id']])
        with gzip.open(LOCAL/(species['id']+'_parsed_v2.json.gz'),'rt') as f:
            parsed=json.load(f)
        excluded={'|'.join(p) for p in parsed['exclusions']}
        assert not (excluded & unlabeled[species['id']])
        meta=parsed['proteins']
        for rr in groups.values():
            if rr[0]['species']!=species['id']:
                continue
            pset={r['partner_sequence_sha256'] for r in rr if r['label']=='P'}
            for r in rr:
                assert int(r['taxid'])==species['taxid']
                assert meta[r['query_sequence_sha256']]['taxid']==species['taxid']
                assert meta[r['partner_sequence_sha256']]['taxid']==species['taxid']
                if r['stratum']=='matched':
                    a=r['matched_anchor_sequence_sha256']; p=r['partner_sequence_sha256']
                    assert a in pset
                    length_ok=.5<=meta[p]['length']/meta[a]['length']<=2
                    def dbin(x): return sum(x>k for k in (2,9,29))
                    degree_ok=dbin(meta[p]['association_degree'])==dbin(meta[a]['association_degree'])
                    expected=0 if length_ok and degree_ok else 1 if length_ok else 2 if degree_ok else 3
                    assert int(r['matched_tier'])==expected
        with zipfile.ZipFile(LOCAL/species['archive']) as z:
            for member in sorted(z.namelist()):
                if not member.endswith('.xml'):
                    continue
                stack=[]; interactors={}; experiments={}; entry=0
                with z.open(member) as f:
                    for event,e in ET.iterparse(f,events=('start','end')):
                        name=e.tag.rsplit('}',1)[-1]
                        if event=='start':
                            stack.append(name)
                            if name=='entry':
                                entry+=1; interactors={}; experiments={}
                            continue
                        parent=stack[-2] if len(stack)>1 else None
                        if name=='interactor':
                            interactors[e.get('id')]=protein(e)
                            if parent=='interactorList': e.clear()
                        elif name=='experimentDescription':
                            experiments[e.get('id')]=cv(child(e,'interactionDetectionMethod'))
                            # Keep embedded descriptions intact until interaction
                            # validation; this oracle is separate from production.
                            if parent=='experimentList' and 'interaction' not in stack: e.clear()
                        elif name=='interaction':
                            pp=children(child(e,'participantList'),'participant')
                            proteins=[]
                            for p in pp:
                                ref=value(p,'interactorRef')
                                proteins.append(interactors.get(ref) if ref else protein(child(p,'interactor')))
                            usable=[p for p in proteins if p and p['accession'] and p['sequence_sha256'] and
                                    p['molecule_type']=='MI:0326' and p['taxid']==species['taxid']]
                            # All reported co-participant sequence pairs are
                            # independently checked against the selected U set.
                            for i,a in enumerate(usable):
                                for b in usable[i+1:]:
                                    pair='|'.join(sorted((a['sequence_sha256'],b['sequence_sha256'])))
                                    if pair in unlabeled[species['id']]: forbidden_u+=1
                            refs=child(e,'xref'); ac=e.get('id')
                            for x in list(refs) if refs is not None else []:
                                if x.get('db')=='intact' and x.get('refType')=='identity': ac=x.get('id'); break
                            source=(species['archive'],member,entry,ac)
                            if source in requested:
                                key, provenance=requested[source]
                                assert len(pp)==len(usable)==2
                                assert '|'.join(sorted(p['sequence_sha256'] for p in usable))==key.split(':',1)[1]
                                assert value(e,'negative').lower()!='true'
                                assert not member.endswith('_negative.xml')
                                assert value(e,'modelled').lower()!='true'
                                assert value(e,'intraMolecular').lower()!='true'
                                assert child(e,'expansionMethod') is None
                                method_ids=[]
                                for x in children(e,'experimentList'):
                                    for y in x:
                                        if y.tag.rsplit('}',1)[-1]=='experimentRef': method_ids.append(experiments.get((y.text or '').strip()))
                                        elif y.tag.rsplit('}',1)[-1]=='experimentDescription': method_ids.append(experiments.get(y.get('id')))
                                itype=cv(child(e,'interactionType'))
                                assert itype=='MI:0407' or (itype in ('MI:0915','MI:0914') and bool(set(method_ids)&hybrid))
                                for p in pp:
                                    for feature in children(child(p,'featureList'),'feature'):
                                        assert cv(child(feature,'featureType')) in tags
                                assert provenance['publication_ids']
                                found.add(source); checked_records+=1
                            e.clear()
                        elif name=='entry': e.clear()
                        stack.pop()
        print('Independent XML/panel validation:',species['id'],flush=True)
    assert found==set(requested), (len(found),len(requested))
    assert forbidden_u==0
    output=dict(at_utc=now(),passed=True,targets=len(groups),rows=len(rows),sequences=len(sequences),
        independently_checked_original_XML_evidence_records=checked_records,
        selected_U_found_in_original_XML_co_participant_records=forbidden_u,
        labels_taxids_sequence_hashes_deduplication_matching_tiers_checked=True,
        validator=record(Path(__file__)),panel_selection=record(OUT/'PANEL_SELECTION.json'))
    write_json(OUT/'PANEL_VALIDATION.json',output)

def metric_validation():
    from sklearn.metrics import roc_auc_score, average_precision_score, ndcg_score
    check_records(read(OUT/'INPUT_FREEZE.json')['files'])
    rows=table(OUT/'all_model_scores.csv'); reported=table(OUT/'per_target_metrics.csv')
    groups=defaultdict(list)
    for r in rows:
        for m in MODELS: assert math.isfinite(float(r[m+'_score']))
        groups[r['target_id']].append(r)
    errors=defaultdict(float)
    for r in reported:
        selected=[v for v in groups[r['target_id']] if
                  (r['subset']=='all' or v['any_exact_TRAIN_DEV_endpoint']=='False') and
                  (v['label']=='P' or r['candidate_set']=='all_U' or v['stratum']==r['candidate_set'])]
        score=np.array([float(v[r['model']+'_score']) for v in selected])
        truth=np.array([v['label']=='P' for v in selected])
        expected={'P_vs_U_concordance':roc_auc_score(truth,score),'average_precision':average_precision_score(truth,score)}
        for k in CONFIG['cutoffs']:
            expected[f'NDCG_at_{k}']=ndcg_score(truth.astype(int)[None,:],score[None,:],k=k,ignore_ties=False)
            recovered=0.
            for s in score[truth]:
                above=int((score>s).sum()); tied=int((score==s).sum())
                recovered+=max(0,min(tied,k-above))/tied
            expected[f'recovered_P_at_{k}']=recovered
            expected[f'recall_at_{k}']=recovered/truth.sum()
            expected[f'known_positive_precision_at_{k}']=recovered/k
            expected[f'EF_at_{k}']=(recovered/k)/truth.mean()
        best=score[truth].max(); above=int((score>best).sum()); tied=int((score==best).sum()); hits=int((truth&(score==best)).sum())
        expected['first_positive_rank_expected']=above+(tied+1)/(hits+1)
        denom=math.comb(tied,hits)
        expected['reciprocal_rank']=sum(math.comb(tied-j,hits-1)/denom/(above+j) for j in range(1,tied-hits+2))
        for k in CONFIG['cutoffs']:
            available=min(tied,max(0,k-above))
            expected[f'target_success_at_{k}']=1-(math.comb(tied-available,hits)/denom if tied-available>=hits else 0)
        for k,v in expected.items():
            err=abs(v-float(r[k])); errors[k]=max(errors[k],err)
            assert err<1e-10,(r['target_id'],r['model'],k,err)
        assert int(r['P'])==int(truth.sum()) and int(r['U'])==int((~truth).sum())
    # Macro means are checked from independent target grouping.
    macro=table(OUT/'macro_metrics.csv')
    for r in macro:
        rr=[v for v in reported if all(v[k]==r[k] for k in ('subset','candidate_set','model')) and
            (r['species']=='equal_species' or v['species']==r['species'])]
        for metric in errors:
            by_species=defaultdict(list)
            for v in rr: by_species[v['species']].append(float(v[metric]))
            expected=np.mean([np.mean(v) for v in by_species.values()])
            assert abs(float(r[metric])-expected)<1e-10
    ranks=table(OUT/'positive_ranks.csv')
    assert len(ranks)==sum(v['label']=='P' for v in rows)*len(MODELS)*3
    write_json(OUT/'INDEPENDENT_VALIDATION.json',dict(at_utc=now(),passed=True,
        metric_rows_checked=len(reported),macro_rows_checked=len(macro),rank_rows=len(ranks),
        maximum_absolute_errors=dict(errors),validator=record(Path(__file__)),
        metric_oracles='sklearn ROC AUC, AP, tie-aware NDCG; independent combinatorial rank/cutoff oracles',
        panel_validation=record(OUT/'PANEL_VALIDATION.json'),frozen_inputs_unchanged=True))
    print('Independent metrics passed:',len(reported),'target rows and',len(macro),'macro rows',flush=True)

if __name__=='__main__':
    require_container()
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=('panels','metrics'))
    globals()['panel_validation' if p.parse_args().phase=='panels' else 'metric_validation']()
