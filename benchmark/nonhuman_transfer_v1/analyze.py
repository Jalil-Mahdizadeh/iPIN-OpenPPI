"""Prespecified target-level PU retrieval and paired descriptive comparisons."""
from __future__ import annotations
from collections import Counter, defaultdict
import gzip
import importlib.util
import itertools
import numpy as np
from study_utils import *

def load_metrics():
    path = ROOT / 'example/twelve_target_comparison_v1/metrics.py'
    spec = importlib.util.spec_from_file_location('known_positive_metrics', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

SETS = ('background', 'matched', 'all_U')
PRIMARY = ('P_vs_U_concordance', 'average_precision', 'reciprocal_rank', 'recall_at_10', 'NDCG_at_10')

def main():
    require_container()
    check_records(read(OUT / 'INPUT_FREEZE.json')['files'])
    metrics = load_metrics()
    rows, ipin, tuna = [table(OUT/p) for p in ('panels.csv', 'ipin_scores.csv', 'tuna_scores.csv')]
    if len(rows) != len(ipin) or len(rows) != len(tuna):
        raise RuntimeError('Incomplete scores')
    exact = {r['sequence_sha256']: r for r in table(OUT/'exact_endpoint_exposure.csv')}
    similarity = {r['sequence_sha256']: r for r in table(OUT/'training_sequence_similarity.csv')}
    degree = {(r['species'], r['sequence_sha256']): int(r['association_degree']) for r in table(OUT/'proteins.csv')}
    groups = defaultdict(list)
    for i, (r,a,b) in enumerate(zip(rows, ipin, tuna, strict=True)):
        if int(r['row_index']) != i or int(a['row_index']) != i or int(b['row_index']) != i:
            raise RuntimeError('Score order changed')
        for m in MODELS:
            r[m+'_score'] = float((b if m == 'tuna_retrained' else a)[m+'_score'])
        endpoints = (r['query_sequence_sha256'], r['partner_sequence_sha256'])
        r['any_exact_TRAIN_DEV_endpoint'] = any(exact[h][k] == 'True' for h in endpoints for k in ('exact_TRAIN_endpoint', 'exact_DEV_endpoint'))
        r['target_similarity_bin'] = similarity[endpoints[0]]['similarity_bin']
        count = sum(similarity[h]['TRAIN_homolog_30pct_both80'] == 'True' for h in endpoints)
        r['homologous_endpoint_count'] = count
        groups[r['target_id']].append(r)
    write_csv(OUT/'all_model_scores.csv', rows)
    per_target, ranks, coverage, pair_strata, controls = [], [], [], [], []
    for target, panel in groups.items():
        species = panel[0]['species']
        for subset in ('all', 'no_exact_TRAIN_DEV_endpoint'):
            cohort = [r for r in panel if subset == 'all' or not r['any_exact_TRAIN_DEV_endpoint']]
            for candidate in SETS:
                selected = [r for r in cohort if r['label'] == 'P' or candidate == 'all_U' or r['stratum'] == candidate]
                positive = np.array([r['label'] == 'P' for r in selected], dtype=bool)
                valid = bool(positive.any() and (~positive).any() and len(selected) >= max(CONFIG['cutoffs']))
                coverage.append(dict(species=species, target_id=target, subset=subset, candidate_set=candidate,
                    P=int(positive.sum()), U=int((~positive).sum()), evaluable=valid))
                if not valid:
                    continue
                for model in MODELS:
                    score = np.array([r[model+'_score'] for r in selected])
                    result = metrics.evaluate(score, positive, tuple(CONFIG['cutoffs']))
                    per_target.append(dict(species=species, target_id=target, subset=subset, candidate_set=candidate,
                        model=model, target_similarity_bin=panel[0]['target_similarity_bin'], **result))
                    if subset == 'all':
                        for i in np.flatnonzero(positive):
                            r = selected[i]
                            ranks.append(dict(species=species, target_id=target, partner_uniprot=r['partner_uniprot'],
                                model=model, candidate_set=candidate, **metrics.positive_ranks(score[i],score,tuple(CONFIG['cutoffs']))))
                        # Conditional concordance, requiring P and U in the same
                        # both-endpoint homology stratum for the same target.
                        for hcount in range(3):
                            mask = np.array([r['homologous_endpoint_count'] == hcount for r in selected])
                            p, u = score[mask & positive], score[mask & ~positive]
                            if len(p) and len(u):
                                concordance = float(((p[:,None]>u).astype(float)+.5*(p[:,None]==u)).mean())
                                pair_strata.append(dict(species=species, target_id=target, candidate_set=candidate,
                                    model=model, homologous_endpoint_count=hcount, P=len(p), U=len(u),
                                    P_vs_U_concordance=concordance))
                if subset == 'all':
                    score = [degree[species,r['partner_sequence_sha256']] for r in selected]
                    controls.append(dict(species=species, target_id=target, candidate_set=candidate,
                        control='source_association_degree', **metrics.evaluate(score,positive,tuple(CONFIG['cutoffs']))))
    write_csv(OUT/'per_target_metrics.csv',per_target)
    write_csv(OUT/'positive_ranks.csv',ranks)
    write_csv(OUT/'analysis_coverage.csv',coverage)
    write_csv(OUT/'pair_homology_concordance.csv',pair_strata,
        ['species','target_id','candidate_set','model','homologous_endpoint_count','P','U','P_vs_U_concordance'])
    homology_groups=defaultdict(list)
    for r in pair_strata:
        homology_groups[r['species'],r['candidate_set'],r['model'],r['homologous_endpoint_count']].append(r)
    write_csv(OUT/'pair_homology_summary.csv', [dict(species=s,candidate_set=c,model=m,
        homologous_endpoint_count=h,targets=len(v),total_P=sum(x['P'] for x in v),total_U=sum(x['U'] for x in v),
        P_vs_U_concordance=float(np.mean([x['P_vs_U_concordance'] for x in v])))
        for (s,c,m,h),v in sorted(homology_groups.items())],
        ['species','candidate_set','model','homologous_endpoint_count','targets','total_P','total_U','P_vs_U_concordance'])
    write_csv(OUT/'degree_control_metrics.csv',controls)
    metric_keys = [k for k in per_target[0] if k not in ('species','target_id','subset','candidate_set','model','target_similarity_bin')]
    macro_groups = defaultdict(list)
    for r in per_target:
        macro_groups[r['species'],r['subset'],r['candidate_set'],r['model']].append(r)
    macro = []
    for (species,subset,candidate,model), values in sorted(macro_groups.items()):
        macro.append(dict(species=species, subset=subset, candidate_set=candidate, model=model,
            targets=len(values), **{k:float(np.mean([r[k] for r in values])) for k in metric_keys},
            total_P=sum(r['P'] for r in values),total_U=sum(r['U'] for r in values)))
    species_macro = list(macro)
    for subset,candidate,model in itertools.product(('all','no_exact_TRAIN_DEV_endpoint'),SETS,MODELS):
        values = [r for r in species_macro if (r['subset'],r['candidate_set'],r['model']) == (subset,candidate,model)]
        macro.append(dict(species='equal_species',subset=subset,candidate_set=candidate,model=model,
            targets=sum(r['targets'] for r in values),**{k:float(np.mean([r[k] for r in values])) for k in metric_keys},
            total_P=sum(r['total_P'] for r in values),total_U=sum(r['total_U'] for r in values)))
    write_csv(OUT/'macro_metrics.csv',macro)
    similarity_rows = []
    sim_groups = defaultdict(list)
    for r in per_target:
        if r['subset'] == 'all':
            sim_groups[r['species'],r['candidate_set'],r['model'],r['target_similarity_bin']].append(r)
    for (species,candidate,model,sim), values in sorted(sim_groups.items()):
        similarity_rows.append(dict(species=species,candidate_set=candidate,model=model,target_similarity_bin=sim,
            targets=len(values),**{k:float(np.mean([r[k] for r in values])) for k in PRIMARY}))
    write_csv(OUT/'target_similarity_metrics.csv',similarity_rows)
    # Target resampling is paired across models and metrics, conditional on the
    # selected fixed panels. It does not remove shared-partner/study dependence.
    contrasts, intervals, draw_store = [], [], {}
    rng = np.random.default_rng(CONFIG['seed'])
    for species in [s['id'] for s in CONFIG['species']]:
        for subset,candidate in itertools.product(('all','no_exact_TRAIN_DEV_endpoint'),SETS):
            available = {m:{r['target_id']:r for r in macro_groups.get((species,subset,candidate,m),[])} for m in MODELS}
            targets = sorted(set.intersection(*(set(v) for v in available.values())))
            if not targets:
                continue
            sample = rng.integers(0,len(targets),size=(CONFIG['bootstrap_draws'],len(targets)))
            for key in PRIMARY:
                draws, points = {}, {}
                for m in MODELS:
                    values = np.array([available[m][t][key] for t in targets])
                    points[m] = float(values.mean())
                    draws[m] = values[sample].mean(axis=1)
                    draw_store[species,subset,candidate,key,m] = draws[m]
                    lo,hi = np.quantile(draws[m],[.025,.975])
                    intervals.append(dict(species=species,subset=subset,candidate_set=candidate,metric=key,model=m,
                        targets=len(targets),estimate=points[m],ci_low=float(lo),ci_high=float(hi)))
                for a,b in itertools.combinations(MODELS,2):
                    lo,hi = np.quantile(draws[b]-draws[a],[.025,.975])
                    contrasts.append(dict(species=species,subset=subset,candidate_set=candidate,metric=key,
                        model_a=a,model_b=b,targets=len(targets),difference_b_minus_a=points[b]-points[a],
                        ci_low=float(lo),ci_high=float(hi)))
    for subset,candidate,key in itertools.product(('all','no_exact_TRAIN_DEV_endpoint'),SETS,PRIMARY):
        names = [s['id'] for s in CONFIG['species'] if (s['id'],subset,candidate,key,MODELS[0]) in draw_store]
        ds = {m:np.mean([draw_store[s,subset,candidate,key,m] for s in names],axis=0) for m in MODELS}
        point = {m:next(r[key] for r in macro if (r['species'],r['subset'],r['candidate_set'],r['model']) == ('equal_species',subset,candidate,m)) for m in MODELS}
        nt = sum(r['targets'] for r in species_macro if (r['subset'],r['candidate_set'],r['model']) == (subset,candidate,MODELS[0]))
        for m in MODELS:
            lo,hi = np.quantile(ds[m],[.025,.975])
            intervals.append(dict(species='equal_species',subset=subset,candidate_set=candidate,metric=key,model=m,
                targets=nt,estimate=point[m],ci_low=float(lo),ci_high=float(hi)))
        for a,b in itertools.combinations(MODELS,2):
            lo,hi = np.quantile(ds[b]-ds[a],[.025,.975])
            contrasts.append(dict(species='equal_species',subset=subset,candidate_set=candidate,metric=key,
                model_a=a,model_b=b,targets=nt,difference_b_minus_a=point[b]-point[a],ci_low=float(lo),ci_high=float(hi)))
    write_csv(OUT/'paired_differences.csv',contrasts)
    write_csv(OUT/'metric_intervals.csv',intervals)
    with gzip.open(OUT/'selected_evidence.json.gz','rt') as f:
        evidence=json.load(f)
    studies=defaultdict(set)
    for r in rows:
        if r['label']=='P':
            for ev in evidence[r['evidence_key']]:
                for pub in ev['publication_ids']:
                    studies[r['species'],pub].add(r['pair_key'])
    study_rows=[dict(species=s,publication_id=p,unique_selected_P_pairs=len(v)) for (s,p),v in sorted(studies.items())]
    write_csv(OUT/'study_coverage.csv',study_rows)
    census=[]
    for spec in CONFIG['species']:
        s=spec['id']; rr=[r for r in rows if r['species']==s]
        if not rr:
            continue
        pos={r['pair_key'] for r in rr if r['label']=='P'}
        counts=Counter(r['pair_key'] for r in rr)
        ss=[v for (species,_),v in studies.items() if species==s]
        census.append(dict(species=s,targets=len({r['target_id'] for r in rr}),P_rows=sum(r['label']=='P' for r in rr),
            U_rows=sum(r['label']=='U' for r in rr),unique_pairs=len(counts),unique_P_pairs=len(pos),
            repeated_undirected_pairs=sum(v>1 for v in counts.values()),
            unique_sequences=len({r[k] for r in rr for k in ('query_sequence_sha256','partner_sequence_sha256')}),
            P_publications=len(ss),largest_publication_P_pairs=max(map(len,ss)),
            largest_publication_fraction=max(map(len,ss))/len(pos)))
    write_csv(OUT/'panel_coverage.csv',census)
    write_json(OUT/'ANALYSIS.json',dict(at_utc=now(),per_target_metric_rows=len(per_target),
        macro_metric_rows=len(macro),paired_contrasts=len(contrasts),bootstrap_draws=CONFIG['bootstrap_draws'],
        seed=CONFIG['seed'],U_is_unlabeled=True,thresholds_fitted=False,
        uncertainty='Exploratory paired target bootstrap; fixed panels; residual homology, study and reused-partner dependencies',
        script=record(Path(__file__))))
    print('Analysis complete:',len(rows),'score rows;',len(per_target),'target metric rows',flush=True)

if __name__=='__main__':
    main()
