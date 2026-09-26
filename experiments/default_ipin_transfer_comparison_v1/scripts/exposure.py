"""Exact expanded-corpus exposure; common cohorts for all four predictors."""
from collections import Counter
import numpy as np
from transfer_io import *

COMMON = 'no_exact_any_model_TRAIN_DEV_endpoint'
COHORTS = ('all', 'no_exact_TRAIN_DEV_endpoint', COMMON)


def audit(study, rows):
    output = OUT / study
    source = ROOT / 'benchmark' / study
    hashes = read(DATA / 'endpoints.json')
    meta = read(DATA / 'sequences.json')
    require(hashes == meta['sha256'], 'Training endpoint order changed')
    index = {h: i for i, h in enumerate(hashes)}
    n = len(hashes)
    checks = [('train_31k_P', 'training_31188.npz', 'p_a', 'p_b', None),
              ('train_U_pool', 'training_unlabeled.npz', 'u_a', 'u_b', None)]
    for part in ('reconciled', 'added'):
        for cell in ('C1', 'C2', 'C3'):
            for label, positive in (('P', True), ('U', False)):
                checks.append((f'dev_{part}_{cell}_{label}', f'development/{part}/{cell}.npz', 'a', 'b', positive))
    a = np.array([index.get(r['query_sequence_sha256'], -1) for r in rows], np.int64)
    b = np.array([index.get(r['partner_sequence_sha256'], -1) for r in rows], np.int64)
    codes = np.where((a >= 0) & (b >= 0), np.minimum(a, b) * n + np.maximum(a, b), -1)
    pair_flags, endpoint_sets, counts = {}, {}, {}
    for name, filename, akey, bkey, positive in checks:
        with np.load(DATA / filename, allow_pickle=False) as data:
            left, right = data[akey], data[bkey]
            if positive is not None:
                keep = data['positive'] == positive
                left, right = left[keep], right[keep]
            keys = np.unique(np.minimum(left, right).astype(np.int64) * n + np.maximum(left, right))
            endpoint_sets[name] = set(hashes[i] for i in np.unique(np.r_[left, right]))
        flags = np.isin(codes, keys)
        pair_flags[name] = flags
        counts[name] = {label: sum(bool(f) and r['label'] == label for f, r in zip(flags, rows, strict=True)) for label in ('P', 'U')}
    train = endpoint_sets['train_31k_P'] | endpoint_sets['train_U_pool']
    development = set().union(*(hs for key, hs in endpoint_sets.items() if key.startswith('dev_')))
    old = {r['sequence_sha256']: r for r in table(source / 'exact_endpoint_exposure.csv')}
    historical = {h for h, r in old.items() if r['exact_TRAIN_endpoint'] == 'True' or r['exact_DEV_endpoint'] == 'True'}
    common = historical | train | development
    all_hashes = set(old)
    require(all_hashes == {r[k] for r in rows for k in ('query_sequence_sha256', 'partner_sequence_sha256')}, 'Exposure universe mismatch')
    endpoints = []
    for h in sorted(all_hashes):
        endpoints.append({'sequence_sha256': h, 'historical_exact_TRAIN_endpoint': old[h]['exact_TRAIN_endpoint'],
            'historical_exact_DEV_endpoint': old[h]['exact_DEV_endpoint'],
            'exact_train_31k_P_endpoint': h in endpoint_sets['train_31k_P'],
            'exact_train_U_pool_endpoint': h in endpoint_sets['train_U_pool'],
            'exact_expanded_development_endpoint': h in development,
            'any_model_exact_TRAIN_DEV_endpoint': h in common,
            'newly_flagged_endpoint': h in common and h not in historical})
    pairs = []
    for i, row in enumerate(rows):
        hs = (row['query_sequence_sha256'], row['partner_sequence_sha256'])
        original = any(h in historical for h in hs)
        require(row['any_exact_TRAIN_DEV_endpoint'] == str(original), 'Historical exposure flag changed')
        row['any_model_exact_TRAIN_DEV_endpoint'] = any(h in common for h in hs)
        pairs.append({'row_index': i, 'pair_key': row['pair_key'], 'label': row['label'],
            **{key: bool(value[i]) for key, value in pair_flags.items()},
            'historical_exact_TRAIN_DEV_endpoint': original,
            'any_model_exact_TRAIN_DEV_endpoint': row['any_model_exact_TRAIN_DEV_endpoint'],
            'newly_flagged_endpoint_row': row['any_model_exact_TRAIN_DEV_endpoint'] and not original})
    write_csv(output / 'exact_endpoint_exposure.csv', endpoints)
    write_csv(output / 'exact_pair_exposure.csv', pairs)
    proteins = table(source / 'proteins.csv')
    species = {}
    for protein in proteins:
        taxid = protein['taxid']
        species.setdefault(taxid, set()).add(protein['sequence_sha256'])
    summary = {'at_utc': now(), 'method': 'Exact endpoint sequences and unordered exact-sequence pairs',
        'training_U_pool_membership_is_potential_exposure': True,
        'expanded_train_endpoints': len(train), 'expanded_development_endpoints': len(development),
        'expanded_training_P_endpoints': len(endpoint_sets['train_31k_P']),
        'source_pair_counts': counts, 'homology_audit_updated': False, 'ESM_pretraining_exposure_audited': False,
        'development_scope': 'All six evaluated expanded dev partitions; C3 was used for checkpoint selection',
        'exact_match_limit': 'Exact sequence identity; altered isoforms and sequence homology are not excluded',
        'endpoint_counts_by_taxid': [{'taxid': key, 'sequences': len(hs),
            'historical_exposed': len(hs & historical), 'common_exposed': len(hs & common),
            'newly_flagged': len((hs & common) - historical)} for key, hs in sorted(species.items())],
        'row_counts': {key: {label: sum(bool(r[key]) and r['label'] == label for r in pairs) for label in ('P', 'U')}
            for key in ('historical_exact_TRAIN_DEV_endpoint', 'any_model_exact_TRAIN_DEV_endpoint', 'newly_flagged_endpoint_row')}}
    write_json(output / 'EXPOSURE_AUDIT.json', summary)
    return summary


def included(row, cohort):
    if cohort == 'all':
        return True
    if cohort == 'no_exact_TRAIN_DEV_endpoint':
        return row['any_exact_TRAIN_DEV_endpoint'] == 'False'
    require(cohort == COMMON, 'Unknown cohort')
    return not row['any_model_exact_TRAIN_DEV_endpoint']

