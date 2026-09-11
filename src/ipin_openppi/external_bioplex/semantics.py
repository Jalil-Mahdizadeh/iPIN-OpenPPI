"""Directed external-panel semantics, independent of model fitting."""

from collections import Counter, defaultdict
import hashlib

import numpy as np

from ipin_openppi.partner_specificity.semantics import Query


def accession_lookup(records, public_ids):
    """Exact accessions only; detect ambiguity before the public projection."""
    candidates = defaultdict(set)
    for record in records:
        for accession in record['uniprot_accessions']:
            candidates[accession].add(record['reference_sequence_sha256'])
    index = {sha: i for i, sha in enumerate(public_ids)}
    return {acc: index[next(iter(ids))] for acc, ids in candidates.items()
            if len(ids) == 1 and next(iter(ids)) in index}


def project_source(network, directed_rows, bait_rows, accessions):
    """Validate source-local inventories before the exact public projection."""
    gene_accessions, network_pairs = defaultdict(set), set()
    counts = Counter()
    for row in network:
        if not {'GeneA', 'GeneB', 'UniprotA', 'UniprotB'} <= row.keys():
            raise ValueError('network schema mismatch')
        counts['network_rows'] += 1
        for side in ('A', 'B'):
            gene_accessions[row['Gene' + side]].add(row['Uniprot' + side])
        network_pairs.add(tuple(sorted((row['GeneA'], row['GeneB']))))
    mapping = {}
    for gene, acc in gene_accessions.items():
        targets = {accessions.get(a) for a in acc}
        if None not in targets and len(targets) == 1:
            mapping[gene] = next(iter(targets))
        else:
            counts['genes_unmapped_or_ambiguous'] += 1
    baits = set()
    for row in bait_rows:
        if 'GeneID' not in row:
            raise ValueError('bait schema mismatch')
        baits.add(row['GeneID'])
        counts['bait_rows'] += 1
    raw_directed, preys, output = set(), set(), set()
    for row in directed_rows:
        if not {'Bait GeneID', 'Prey GeneID'} <= row.keys():
            raise ValueError('directed schema mismatch')
        a, b = row['Bait GeneID'], row['Prey GeneID']
        if a not in baits or tuple(sorted((a, b))) not in network_pairs:
            raise ValueError('directed edge inconsistent with published network/baits')
        counts['directed_rows'] += 1
        raw_directed.add((a, b))
        preys.add(b)
        if a in mapping and b in mapping:
            output.add((mapping[a], mapping[b]))
        else:
            counts['directed_rows_unmapped'] += 1
    counts.update(network_unique_pairs=len(network_pairs), directed_unique_gene_edges=len(raw_directed),
                  mapped_genes=len(mapping), mapped_directed_reference_edges=len(output),
                  source_unique_baits=len(baits), source_unique_preys=len(preys))
    return (np.array(sorted(output), dtype=np.int64).reshape(-1, 2),
            np.array(sorted({mapping[g] for g in baits if g in mapping}), dtype=np.int64),
            np.array(sorted({mapping[g] for g in preys if g in mapping}), dtype=np.int64), dict(counts))


def directed_queries(a, b, positive):
    if a.shape != b.shape or a.shape != positive.shape or positive.dtype != bool:
        raise ValueError('aligned directed panel arrays required')
    if np.any(a == b) or len(set(zip(a.tolist(), b.tolist()))) != len(a):
        raise ValueError('self or duplicate directed pair')
    order = np.argsort(a, kind='stable')
    boundaries = np.r_[0, 1 + np.flatnonzero(np.diff(a[order])), len(order)]
    out = []
    for start, stop in zip(boundaries[:-1], boundaries[1:]):
        rows = order[start:stop]
        if not len(rows):
            continue
        p, u = rows[positive[rows]], rows[~positive[rows]]
        if len(p) and len(u):
            out.append(Query(int(a[rows[0]]), p, b[p], u, b[u]))
    return out


def make_panel(data, directed, baits, preys, fold):
    """Restrict source-local evidence and orient existing U, never invent U."""
    old_p = {tuple(sorted(p)) for p in zip(data['p_a'], data['p_b'])}
    all_p = {tuple(sorted(p)) for p in directed if p[0] != p[1]}
    positives, counts = [], Counter()
    for a, b in sorted(set(directed)):
        if a == b:
            counts['self'] += 1
        elif a not in baits or b not in preys:
            raise ValueError('directed positive outside source bait/prey inventory')
        elif data['fold'][a] != fold or data['fold'][b] != fold:
            counts['outside_fold'] += 1
        elif tuple(sorted((a, b))) in old_p:
            counts['previously_released_P'] += 1
        else:
            positives.append((a, b))
    rows = [(a, b, True, 1, 1, -1) for a, b in positives]
    for i in np.flatnonzero((data['fold'][data['u_a']] == fold) & (data['fold'][data['u_b']] == fold)):
        a, b = int(data['u_a'][i]), int(data['u_b'][i])
        if tuple(sorted((a, b))) in all_p:
            counts['sampled_U_now_source_P'] += 1
            continue
        for x, y in ((a, b), (b, a)):
            if x in baits and y in preys:
                rows.append((x, y, False, int(data['u_num'][i]), int(data['u_den'][i]), int(i)))
    rows.sort(key=lambda r: (r[0], r[1]))
    matrix = np.array(rows, dtype=np.int64).reshape(-1, 6)
    out = {k: matrix[:, i] for i, k in enumerate(('a', 'b', 'positive', 'num', 'den', 'parent_u_row'))}
    out['positive'] = out['positive'].astype(bool)
    directed_queries(out['a'], out['b'], out['positive'])  # duplicate/orientation checks
    return out, dict(counts)


def select_directed_quartets(a, b, positive, *, salt, maximum, edge_cap, endpoint_cap):
    lookup = {(int(a[i]), int(b[i])): int(i) for i in np.flatnonzero(~positive)}
    candidates = []
    p_rows = np.flatnonzero(positive)
    n = max(int(a.max(initial=0)), int(b.max(initial=0))) + 1
    urows = np.flatnonzero(~positive)
    ucodes = a[urows] * n + b[urows]
    order = np.argsort(ucodes)
    ucodes = ucodes[order]
    for j, first in enumerate(p_rows[:-1]):
        aa, bb = int(a[first]), int(b[first])
        second = p_rows[j + 1:]
        distinct = (a[second] != aa) & (a[second] != bb) & (b[second] != aa) & (b[second] != bb)
        second = second[distinct]
        good = np.ones(len(second), dtype=bool)
        for codes in (aa * n + b[second], a[second] * n + bb):
            positions = np.searchsorted(ucodes, codes)
            found = positions < len(ucodes)
            valid = np.flatnonzero(found)
            found[valid] = ucodes[positions[valid]] == codes[valid]
            good &= found
        for other in second[good]:
            cc, dd = int(a[other]), int(b[other])
            endpoints = (aa, bb, cc, dd)
            key = hashlib.sha256(f'{salt}:{aa}:{bb}:{cc}:{dd}'.encode()).digest()
            candidates.append((key, endpoints, (int(first), int(other), lookup[(aa, dd)], lookup[(cc, bb)])))
    candidates.sort()
    edge_uses, endpoint_uses = Counter(), Counter()
    selected, endpoints = [], []
    for _, ends, rows in candidates:
        if len(selected) >= maximum:
            break
        if any(edge_uses[e] >= edge_cap for e in rows[:2]) or any(endpoint_uses[e] >= endpoint_cap for e in ends):
            continue
        selected.append(rows)
        endpoints.append(ends)
        edge_uses.update(rows[:2])
        endpoint_uses.update(ends)
    return (np.array(selected, dtype=np.int64).reshape(-1, 4),
            np.array(endpoints, dtype=np.int64).reshape(-1, 4), len(candidates))


def positive_interval(info, threshold=0):
    return info['ci95'] is not None and info['ci95'][0] > threshold


def classify(anchor_feasible, quartet_feasible, macro, deltas, folds, seed_names, quartet, controls, margin):
    anchor = bool(anchor_feasible and macro['pair_linear'] - max(macro[c] for c in controls) >= margin
                  and all(positive_interval(deltas[c]) for c in controls)
                  and all(f['macro']['pair_linear'] > f['macro']['endpoint_linear'] for f in folds)
                  and all(macro[f'pair_linear__{s}'] > macro[f'endpoint_linear__{s}'] for s in seed_names))
    swap = bool(quartet_feasible and positive_interval(quartet['interval'], .5)
                and all(positive_interval(quartet['deltas'][c]) for c in controls if c != 'endpoint_linear'))
    return {'anchor_signal_survives': anchor, 'swap_signal_survives': swap,
            'anchor_status': 'infeasible' if not anchor_feasible else 'pass' if anchor else 'does_not_pass',
            'swap_status': 'inconclusive_insufficient_support' if not quartet_feasible else 'pass' if swap else 'does_not_pass'}
