"""Order-free controls and matched within-bait estimands; no fitting."""

import hashlib

import numpy as np

from ipin_openppi.external_bioplex.semantics import directed_queries

ALPHABET = 'ACDEFGHIKLMNPQRSTVWYX'


def encode(sequence):
    if not sequence:
        raise ValueError('empty sequence')
    lookup = {v: i for i, v in enumerate(ALPHABET)}
    return np.array([lookup.get(v, 20) for v in sequence], dtype=np.int64)


def frequencies(sequences):
    return np.stack([np.bincount(encode(s), minlength=21) / len(s) for s in sequences])


def unit_triplets(residues):
    codes = (residues[:-2] * 21 + residues[1:-1]) * 21 + residues[2:]
    counts = np.bincount(codes, minlength=21**3).astype(np.float64)
    norm = np.sqrt(np.dot(counts, counts))
    return counts / norm if norm else counts


def shuffle_means(sequence, endpoint, salt, replicates):
    if replicates < 2 or replicates % 2:
        raise ValueError('positive even replicate count required')
    original = np.sort(encode(sequence))
    halves = np.zeros((2, 21**3), dtype=np.float64)
    for r in range(replicates):
        seed = int.from_bytes(hashlib.sha256(f'{salt}:{endpoint}:{r}'.encode()).digest()[:16], 'big')
        residues = np.random.Generator(np.random.PCG64DXSM(seed)).permutation(original)
        halves[r // (replicates // 2)] += unit_triplets(residues)
    return halves / (replicates // 2)


def row_dot(vectors, a, b, batch=512):
    out = np.empty(len(a), dtype=np.float64)
    for start in range(0, len(a), batch):
        stop = start + batch
        out[start:stop] = np.einsum('ij,ij->i', vectors[a[start:stop]], vectors[b[start:stop]])
    return out


def build_matches(ev, freq, lengths, old_scores, cfg):
    """Enumerate all caliper-eligible U, never consulting a learned score."""
    output = {tier: {'p': [], 'offsets': [0], 'u': [], 'balance': []} for tier in cfg['tiers']}
    eps = cfg['caliper_roundoff_tolerance']
    for q in directed_queries(ev['a'], ev['b'], ev['positive']):
        for p in q.positive:
            b, c = ev['b'][p], q.unlabeled_partner
            length_ratio = np.maximum(lengths[b], lengths[c]) / np.minimum(lengths[b], lengths[c])
            tv = np.abs(freq[b] - freq[c]).sum(axis=1) / 2
            kdiff = np.abs(old_scores['kmer3_cosine'][p] - old_scores['kmer3_cosine'][q.unlabeled])
            pdiff = np.abs(old_scores['pooled_cosine'][p] - old_scores['pooled_cosine'][q.unlabeled])
            basic = (length_ratio <= cfg['maximum_partner_length_ratio'] + eps) & (
                tv <= cfg['maximum_partner_composition_total_variation'] + eps)
            strict = basic & (kdiff <= cfg['maximum_kmer3_score_difference'] + eps) & (
                pdiff <= cfg['maximum_pooled_score_difference'] + eps)
            for tier, mask in zip(cfg['tiers'], (basic, strict), strict=True):
                if mask.sum() < cfg['minimum_U_per_positive']:
                    continue
                out = output[tier]
                out['p'].append(p)
                out['u'].extend(q.unlabeled[mask].tolist())
                out['offsets'].append(len(out['u']))
                out['balance'].append(np.column_stack([v[mask] for v in (length_ratio, tv, kdiff, pdiff)]))
    for out in output.values():
        for k in ('p', 'u', 'offsets'):
            out[k] = np.array(out[k], dtype=np.int64)
        out['balance'] = np.concatenate(out['balance']) if out['balance'] else np.empty((0, 4))
    return output


def matched_metrics(scores, ev, matched, component, draws):
    """P-specific U ratio -> P-partner-weighted bait ratio -> bait macro."""
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 2 or not np.isfinite(scores).all():
        raise ValueError('finite score matrix required')
    count, columns = len(draws), scores.shape[1]
    total, mass, points = np.zeros((count, columns)), np.zeros(count), []
    p, offsets, u = (matched[k] for k in ('p', 'offsets', 'u'))
    if len(offsets) != len(p) + 1 or offsets[0] != 0 or offsets[-1] != len(u):
        raise ValueError('invalid match offsets')
    if len(p) and (np.any(np.diff(offsets) <= 0) or not ev['positive'][p].all() or ev['positive'][u].any()):
        raise ValueError('nonempty P-versus-U match groups required')
    anchors = ev['a'][p]
    if np.any(np.diff(anchors) < 0):
        raise ValueError('matches must be grouped by ascending anchor')
    for anchor in np.unique(anchors):
        ac = component[anchor]
        numerator, denominator = np.zeros((count, columns)), np.zeros(count)
        point = []
        for i in np.flatnonzero(anchors == anchor):
            positive = p[i]
            unlabeled = u[offsets[i]:offsets[i + 1]]
            if np.any(ev['a'][unlabeled] != anchor):
                raise ValueError('match crosses bait')
            credit = (scores[positive] > scores[unlabeled]).astype(np.float64) + .5 * (scores[positive] == scores[unlabeled])
            weight = ev['num'][unlabeled].astype(np.float64) / ev['den'][unlabeled]
            if not np.isfinite(weight).all() or np.any(weight <= 0):
                raise ValueError('positive finite U weights required')
            point.append(weight @ credit / weight.sum())
            uc = component[ev['b'][unlabeled]]
            um = draws[:, uc].astype(np.float64)
            um[:, uc == ac] = 1
            um *= weight
            den = um.sum(axis=1)
            pc = component[ev['b'][positive]]
            pm = np.ones(count) if pc == ac else draws[:, pc].astype(np.float64)
            pm *= den > 0
            ratio = np.divide(um @ credit, den[:, None], out=np.zeros((count, columns)), where=den[:, None] > 0)
            numerator += pm[:, None] * ratio
            denominator += pm
        values = np.divide(numerator, denominator[:, None], out=np.zeros_like(numerator), where=denominator[:, None] > 0)
        am = draws[:, ac] * (denominator > 0)
        total += am[:, None] * values
        mass += am
        points.append(np.mean(point, axis=0))
    return np.array(points).reshape(-1, columns), total, mass


def lower_above(record, value):
    return record.get('ci95') is not None and record['ci95'][0] > value


def diagnostic_flags(cells, cfg):
    stable = all(c['half_macro_difference'] <= cfg['shuffle']['maximum_half_macro_difference'] for c in cells.values())
    flags = {'shuffle_half_stability': stable,
        'order_free_recovery_supported': stable and all(lower_above(c['anchor']['shuffle_kmer3'], .5) for c in cells.values()),
        'material_native_order_increment_supported': stable and all(
            c['anchor_deltas']['kmer3_minus_shuffle']['point'] >= cfg['decision']['minimum_order_increment']
            and lower_above(c['anchor_deltas']['kmer3_minus_shuffle'], 0) for c in cells.values()),
        'matched_incremental_ranking_supported': {}}
    for tier in cfg['matching']['tiers']:
        supported = True
        for c in cells.values():
            m = c['matched'][tier]
            controls = cfg['decision']['matched_controls']
            if not m['adequate_support']:
                supported = False
                continue
            supported &= lower_above(m['scores']['pair_linear'], .5)
            supported &= all(m['deltas'][k]['point'] >= cfg['decision']['minimum_matched_pair_margin'] for k in controls)
            supported &= all(lower_above(m['deltas'][k], 0) for k in controls)
        flags['matched_incremental_ranking_supported'][tier] = bool(supported)
    return flags
