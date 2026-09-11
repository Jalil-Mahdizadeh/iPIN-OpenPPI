"""Same-author reference audit, independent of production models/metric code.

Reconstruct source memberships by filtered streaming (not production SQL),
normalization and score algebra in NumPy, point metrics by direct comparisons,
and 16 complete component bootstrap replicates by direct weighted comparisons.
Verify every control-similarity entry and deterministic samples of exhaustive
interaction transfer. This is numerical validation, not external replication.
"""

from collections import Counter
import hashlib
import json

import numpy as np
import pyarrow.parquet as pq
from scipy import sparse

from ipin_openppi.partner_specificity import data as parent
from ipin_openppi.partner_specificity.validation import reference_scores
from ipin_openppi.stage1.support import sha256_file
from . import data as io


def load(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def reference_source_bits(root, data, meta):
    index = {e: i for i, e in enumerate(meta['endpoints'])}
    genes = {}
    source_endpoint_path = parent.config(root)['inputs']['endpoints']['path']
    for r in pq.read_table(root / source_endpoint_path, columns=['reference_sequence_sha256', 'space_iii_gene_ids']).to_pylist():
        if r['reference_sequence_sha256'] in index:
            for g in r['space_iii_gene_ids']:
                if g in genes:
                    raise RuntimeError('ambiguous reference gene map')
                genes[g] = index[r['reference_sequence_sha256']]
    lookup = {tuple(sorted((a, b))): i for i, (a, b) in enumerate(zip(data['p_a'], data['p_b']))}
    bits = np.zeros(len(lookup), dtype=np.uint8)
    for name in ('part-00000.parquet', 'part-00001.parquet', 'part-00002.parquet'):
        parquet = pq.ParquetFile(root / io.SOURCE_ROOT / name)
        for batch in parquet.iter_batches(columns=['gene_a', 'gene_b', 'unique_gene_pair', 'label_authorized', 'source_dataset']):
            for r in batch.to_pylist():
                # Discard non-allowlisted identities before using their source field.
                a, b = genes.get(r['gene_a']), genes.get(r['gene_b'])
                if a is None or b is None or (min(a, b), max(a, b)) not in lookup:
                    continue
                if not r['unique_gene_pair'] or r['label_authorized']:
                    continue
                bits[lookup[(min(a, b), max(a, b))]] |= {'HI-II-14': 1, 'HuRI': 2}[r['source_dataset']]
    return bits


def reference_similarities(root, data, meta):
    """Full alignment and dense similarity audit, without production parsers."""
    n = len(meta['endpoints'])
    loc, cov = np.zeros((n, n), np.float32), np.zeros((n, n), np.float32)
    edges = set()
    with (root / io.RUN / 'mmseqs/alignments.tsv').open() as handle:
        for line in handle:
            f = line.split()
            a, b, mismatch, columns, qs, qe, qlen, ts, te, tlen = map(int, f[:10])
            assert qlen == data['length'][a] and tlen == data['length'][b]
            qspan, tspan = qe - qs + 1, te - ts + 1
            # Gaps occupy columns but consume only one residue, mismatches two.
            gaps = 2 * columns - qspan - tspan
            identities = columns - gaps - mismatch
            if identities * 5 < columns or min(qspan, tspan) < 40 or float(f[10]) > 1e-3:
                continue
            identity = identities / columns
            local = identity * min(qspan, tspan, 80) / 80
            coverage = identity * np.sqrt(qspan * tspan / (qlen * tlen))
            for x, y in ((a, b), (b, a)):
                loc[x, y] = max(float(loc[x, y]), local)
                cov[x, y] = max(float(cov[x, y]), coverage)
            if a != b and qspan >= 80 and tspan >= 80 and 5 * qspan >= qlen and 5 * tspan >= tlen:
                edges.add(tuple(sorted((a, b))))
    for key, value in (('local', loc), ('coverage', cov)):
        stored = np.load(root / io.RUN / f'similarity_{key}.npy', mmap_mode='r', allow_pickle=False)
        np.testing.assert_allclose(stored, value, rtol=0, atol=1e-7)
    np.testing.assert_array_equal(np.load(root / io.RUN / 'purge_edges.npy', allow_pickle=False), np.array(sorted(edges)).reshape(-1, 2))
    # Independent 3-mer encoding/counting; U and all other nonalphabet residues map to X.
    alphabet = 'ACDEFGHIKLMNPQRSTVWYX'
    rows, cols, vals = [], [], []
    for i, sequence in enumerate(meta['sequences']):
        mapped = ''.join(c if c in alphabet else 'X' for c in sequence)
        counts = Counter(mapped[j:j + 3] for j in range(len(mapped) - 2))
        norm = np.sqrt(sum(v * v for v in counts.values()))
        for word, value in counts.items():
            c = sum(alphabet.index(ch) * 21 ** (2 - k) for k, ch in enumerate(word))
            rows.append(i)
            cols.append(c)
            vals.append(value / norm)
    kmer = sparse.csr_matrix((vals, (rows, cols)), shape=(n, 21**3), dtype=np.float64)
    raw = np.load(root / parent.GENERATED / 'raw_public_embeddings.npy', allow_pickle=False).astype(np.float64)
    unit = raw / np.sqrt(np.sum(raw ** 2, axis=1))[:, None]
    kstored = np.load(io.similarity_path(root, 'kmer'), mmap_mode='r', allow_pickle=False)
    pstored = np.load(root / io.RUN / 'similarity_plm.npy', mmap_mode='r', allow_pickle=False)
    maximum = 0.
    for start in range(0, n, 128):
        expected = (kmer[start:start + 128] @ kmer.T).toarray()
        diff = float(np.max(np.abs(kstored[start:start + 128] - expected)))
        maximum = max(maximum, diff)
        np.testing.assert_allclose(kstored[start:start + 128], expected, rtol=0, atol=2e-6)
        expected = np.maximum(unit[start:start + 128] @ unit.T, 0)
        np.testing.assert_allclose(pstored[start:start + 128], expected, rtol=0, atol=1e-7)
    return np.array(sorted(edges)).reshape(-1, 2), maximum


def direct_queries(a, b, positive):
    panels = {}
    for row, (x, y, p) in enumerate(zip(a, b, positive)):
        for anchor, partner in ((x, y), (y, x)):
            panels.setdefault(int(anchor), [[], [], [], []])
            panels[int(anchor)][0 if p else 2].append(row)
            panels[int(anchor)][1 if p else 3].append(partner)
    return [(a, *[np.array(x, dtype=np.int64) for x in panels[a]]) for a in sorted(panels)
            if panels[a][0] and panels[a][2]]


def direct_metrics(values, queries, weight, component, draws=None):
    points, total, mass = [], None, None
    if draws is not None:
        total, mass = np.zeros(len(draws)), np.zeros(len(draws))
    for anchor, pi, pp, ui, up in queries:
        credit = (values[pi, None] > values[ui]).astype(float) + .5 * (values[pi, None] == values[ui])
        points.append(float((credit * weight[ui]).sum() / (len(pi) * weight[ui].sum())))
        if draws is not None:
            for r, draw in enumerate(draws):
                pm = np.array([1 if component[p] == component[anchor] else draw[component[p]] for p in pp])
                um = weight[ui] * np.array([1 if component[u] == component[anchor] else draw[component[u]] for u in up])
                denom = pm.sum() * um.sum()
                if denom > 0:
                    total[r] += draw[component[anchor]] * (credit * pm[:, None] * um).sum() / denom
                    mass[r] += draw[component[anchor]]
    return np.array(points), total, mass


def check_interval(values, result):
    valid = np.isfinite(values)
    assert result['valid_replicates'] == int(valid.sum())
    if valid.mean() < .95:
        assert result['ci95'] is None
    else:
        np.testing.assert_allclose(result['ci95'], np.percentile(values[valid], [2.5, 97.5]), atol=1e-12, rtol=0)


def validate(root):
    import torch
    cfg = io.verify_freeze(root)
    report = io.read_json(root / io.RESULT / 'RESULTS.json')
    for payload in (report, io.read_json(root / io.RESULT / 'TRAINING_COMPLETE.json'),
                    io.read_json(root / io.RESULT / 'SCORING_COMPLETE.json')):
        io.verify_records(root, payload['artifacts'])
    data = io.parent_data(root)
    meta = io.read_json(root / parent.GENERATED / 'endpoint_metadata.json')
    source = reference_source_bits(root, data, meta)
    np.testing.assert_array_equal(source, np.load(root / io.RUN / 'public_positive_source_bits.npy', allow_pickle=False))
    assert len(source) == 16799 and np.isin(source, [1, 2, 3]).all()
    print('reference source projection passed', flush=True)
    edges, kdiff = reference_similarities(root, data, meta)
    print('all four full similarity matrices passed', flush=True)
    draws = np.load(root / io.RUN / 'component_multipliers.npy', allow_pickle=False)
    expected = np.random.Generator(np.random.PCG64DXSM(20260915)).poisson(1, (2000, int(data['component'].max()) + 1))
    np.testing.assert_array_equal(draws, expected)
    raw = np.load(root / parent.GENERATED / 'raw_public_embeddings.npy', allow_pickle=False)
    learned_count, control_count, max_diff = 0, 0, 0.
    seeds = parent.config(root)['training']['seeds']
    for run in io.read_json(root / io.RESULT / 'TRAINING_COMPLETE.json')['runs']:
        plan = load(root / io.RUN / f"plan_{run['arm']}_{run['fold']}.npz")
        assert run['fit_P'] == len(plan['p_rows']) and run['fit_U'] == len(plan['u_a'])
        assert len(run['monitors']) == 5
        for pass_index, monitor in enumerate(run['monitors'], 1):
            rng = np.random.Generator(np.random.PCG64DXSM(run['seed'] + pass_index))
            po, uo = rng.permutation(run['fit_P']), rng.permutation(run['fit_U'])
            assert monitor['order_hashes'] == {k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in [('p', po), ('u', uo)]}
            assert monitor['U_comparisons'] == run['fit_U'] and monitor['pass'] == pass_index
            assert monitor['steps'] == int(np.ceil(run['fit_U'] / 4096)) * pass_index
            assert np.isfinite(monitor['training_loss'])
    for arm, result in report['arms'].items():
        point_lists, quartet_lists, reference_boot = {}, {}, {}
        qtotals, qmasses = {}, {}
        for fold in range(3):
            print(f'reference {arm}/{fold}', flush=True)
            ev = load(root / parent.GENERATED / f'evaluation_fold_{fold}.npz')
            plan = load(root / io.RUN / f'plan_{arm}_{fold}.npz')
            scored = load(root / io.RUN / f'scores_{arm}_{fold}.npz')
            names = scored['columns'].tolist()
            fit = data['fold'] != fold
            if arm == 'purged20':
                banned = set()
                for a, b in edges:
                    if data['fold'][a] == fold:
                        banned.add(data['component'][b])
                    if data['fold'][b] == fold:
                        banned.add(data['component'][a])
                fit &= np.array([c not in banned for c in data['component']])
            np.testing.assert_array_equal(fit, plan['fit_endpoints'])
            visible = {'hi_to_huri': 1, 'huri_to_hi': 2}.get(arm, 0)
            eligible = fit[data['p_a']] & fit[data['p_b']]
            pfit = np.flatnonzero(eligible & (((source & visible) > 0) if visible else True))
            hidden = np.flatnonzero(eligible & ((source & visible) == 0)) if visible else np.array([], int)
            np.testing.assert_array_equal(plan['p_rows'], pfit)
            np.testing.assert_array_equal(plan['hidden_p_rows'], hidden)
            ufit = fit[data['u_a']] & fit[data['u_b']]
            ua, ub = np.r_[data['u_a'][ufit], data['p_a'][hidden]], np.r_[data['u_b'][ufit], data['p_b'][hidden]]
            order = np.argsort(np.minimum(ua, ub) * len(fit) + np.maximum(ua, ub))
            for name, expected in [('a', ua), ('b', ub), ('num', np.r_[data['u_num'][ufit], np.ones(len(hidden), int)]),
                                   ('den', np.r_[data['u_den'][ufit], np.ones(len(hidden), int)])]:
                np.testing.assert_array_equal(plan['u_' + name], expected[order])
            assert not np.any((data['fold'][data['p_a'][pfit]] == fold) | (data['fold'][data['p_b'][pfit]] == fold))
            mean, std = raw[fit].astype(np.float64).mean(0), np.maximum(raw[fit].astype(np.float64).std(0), 1e-6)
            normpath = root / (parent.GENERATED / f'normalization_fold_{fold}.npz' if arm == 'union' else io.RUN / f'normalization_{arm}_{fold}.npz')
            norm = load(normpath)
            np.testing.assert_array_equal(mean, norm['mean'])
            np.testing.assert_array_equal(std, norm['std'])
            x = ((raw.astype(np.float64) - mean) / std).astype(np.float32)
            expected_freeze = sha256_file(root / (parent.RESULTS if arm == 'union' else io.RESULT) / 'EXECUTION_FREEZE.json')
            for name in cfg['models']:
                for seed in seeds:
                    path = root / (parent.GENERATED / f'fit_f{fold}_{name}_s{seed}.pt' if arm == 'union' else io.RUN / f'{arm}_f{fold}_{name}_s{seed}.pt')
                    ckpt = torch.load(path, map_location='cpu', weights_only=True)
                    assert ckpt['execution_freeze_sha256'] == expected_freeze
                    assert ckpt['model'] == name and ckpt['fold'] == fold and ckpt['seed'] == seed
                    reference = reference_scores(ckpt['state_dict'], name, x, ev['a'], ev['b'])
                    values = scored['scores'][:, names.index(f'{name}__{seed}')]
                    max_diff = max(max_diff, float(np.abs(reference - values).max()))
                    np.testing.assert_allclose(values, reference, atol=cfg['runtime']['forward_absolute_tolerance'], rtol=0)
                    learned_count += len(values)
                ensemble = np.mean([scored['scores'][:, names.index(f'{name}__{seed}')] for seed in seeds], axis=0)
                np.testing.assert_array_equal(ensemble, scored['scores'][:, names.index(name)])
            sample = np.unique(np.r_[np.linspace(0, int(ev['positive'].sum()) - 1, 256, dtype=int),
                                     np.linspace(int(ev['positive'].sum()), len(ev['a']) - 1, 256, dtype=int)])
            for name in cfg['controls']:
                sim = np.load(io.similarity_path(root, name[10:]), mmap_mode='r', allow_pickle=False)
                # Enumerate every directed training-edge orientation independently.
                left = np.r_[data['p_a'][pfit], data['p_b'][pfit]]
                right = np.r_[data['p_b'][pfit], data['p_a'][pfit]]
                expected = np.array([np.fmin(sim[ev['a'][r], left], sim[ev['b'][r], right]).max() for r in sample])
                np.testing.assert_array_equal(expected, scored['scores'][sample, names.index(name)])
                control_count += len(sample)
            target = {'hi_to_huri': 2, 'huri_to_hi': 1}.get(arm, 0)
            keep = np.array([not pos or not target or source[parent_row] == target for pos, parent_row in zip(ev['positive'], ev['parent_row'])])
            np.testing.assert_array_equal(keep, plan['evaluation_mask'])
            qmask = np.array([all(keep[r] for r in row) for row in ev['quartet_rows']])
            np.testing.assert_array_equal(qmask, plan['quartet_mask'])
            queries = direct_queries(ev['a'][keep], ev['b'][keep], ev['positive'][keep])
            w = ev['num'].astype(np.float64) / ev['den']
            saved_points = load(root / io.RUN / f'points_{arm}_{fold}.npz')
            np.testing.assert_array_equal(saved_points['anchors'], [q[0] for q in queries])
            # All quartet replicates (simple multiplicative weights) are cheap.
            qweights = np.array([np.prod(draws[:, sorted(set(data['component'][ep]))].astype(np.float64), axis=1)
                                for ep in ev['quartet_endpoints'][qmask]]).reshape(-1, len(draws)).T
            for i, name in enumerate(names):
                bootstrap = draws[:16] if name in cfg['models'] + cfg['controls'] else None
                pts, total, mass = direct_metrics(scored['scores'][keep, i], queries, w[keep], data['component'], bootstrap)
                np.testing.assert_allclose(pts, saved_points[name], atol=1e-10, rtol=0)
                np.testing.assert_allclose(pts.mean(), result['folds'][fold]['macro'][name], atol=1e-10, rtol=0)
                point_lists.setdefault(name, []).append(pts)
                qrows = ev['quartet_rows'][qmask]
                contrast = scored['scores'][qrows, i] @ np.array([1., 1., -1., -1.])
                credit = (contrast > 1e-6).astype(float) + .5 * (abs(contrast) <= 1e-6)
                quartet_lists.setdefault(name, []).append(credit)
                if bootstrap is not None:
                    reference_boot.setdefault(name, []).append((total, mass))
                    qtotals.setdefault(name, []).append(qweights @ credit)
                    qmasses.setdefault(name, []).append(qweights.sum(axis=1))
        saved_boot = load(root / io.RUN / f'bootstrap_{arm}.npz')
        for name, values in point_lists.items():
            np.testing.assert_allclose(np.concatenate(values).mean(), result['macro'][name], atol=1e-10, rtol=0)
            qvalue = np.concatenate(quartet_lists[name])
            if len(qvalue):
                np.testing.assert_allclose(qvalue.mean(), result['quartet']['points'][name], atol=1e-10, rtol=0)
        for name, items in reference_boot.items():
            total, mass = sum(t for t, m in items), sum(m for t, m in items)
            expected = np.divide(total, mass, out=np.full_like(total, np.nan), where=mass > 0)
            np.testing.assert_allclose(expected, saved_boot['anchor_' + name][:16], atol=1e-10, rtol=0)
            qt, qm = sum(qtotals[name]), sum(qmasses[name])
            expected = np.divide(qt, qm, out=np.full_like(qt, np.nan), where=qm > 0)
            np.testing.assert_allclose(expected, saved_boot['quartet_' + name], atol=1e-10, rtol=0)
            check_interval(saved_boot['anchor_' + name], result['model_intervals'][name])
        for name, delta in result['deltas'].items():
            check_interval(saved_boot['anchor_pair_linear'] - saved_boot['anchor_' + name], delta)
            np.testing.assert_allclose(delta['point'], result['macro']['pair_linear'] - result['macro'][name], atol=1e-12, rtol=0)
        for name, delta in result['quartet']['deltas'].items():
            check_interval(saved_boot['quartet_pair_linear'] - saved_boot['quartet_' + name], delta)
        check_interval(saved_boot['quartet_pair_linear'], result['quartet']['pair_interval'])
        check_interval(saved_boot['anchor_pair_linear'] - np.maximum.reduce([saved_boot['anchor_' + n] for n in result['deltas']]),
                       result['descriptive_minimum_margin_interval'])
    out = {'created_utc': io.now(), 'passed': True, 'source_projection_rows_checked': len(source),
           'similarity_entries_checked': 4 * len(meta['endpoints']) ** 2,
           'maximum_kmer_similarity_difference': kdiff, 'all_learned_score_values_checked': learned_count,
           'maximum_forward_difference': max_diff, 'exhaustive_transfer_sample_values_checked': control_count,
           'all_anchor_and_quartet_points_checked': True, 'direct_anchor_bootstrap_replicates_checked_per_arm': 16,
           'all_training_row_orders_and_complete_passes_checked': True,
           'all_quartet_bootstrap_replicates_checked': 2000, 'all_reported_primary_intervals_checked': True,
           'scope': 'same_author_numerical_reference_not_external_scientific_validation'}
    io.write_json(root / io.VALID / 'REFERENCE_VALIDATION.json', out)
    return out
