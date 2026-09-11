"""Separate NumPy/source arithmetic audit; same author, not external review."""

from collections import defaultdict, Counter
import csv
import hashlib
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from ipin_openppi.homology_source import data as hio
from ipin_openppi.homology_source.validation import check_interval, direct_metrics
from ipin_openppi.partner_specificity import data as pio
from ipin_openppi.partner_specificity.validation import reference_scores
from ipin_openppi.stage1.support import sha256_file
from . import data as io


def reference_source(root, cfg, cell, metadata):
    """An independent accession-to-sequence and source-direction reconstruction."""
    ids = {v: i for i, v in enumerate(metadata['endpoints'])}
    all_accessions = defaultdict(set)
    endpoint_path = root / pio.config(root)['inputs']['endpoints']['path']
    for batch in pq.ParquetFile(endpoint_path).iter_batches(columns=['reference_sequence_sha256', 'uniprot_accessions']):
        for row in batch.to_pylist():
            for acc in row['uniprot_accessions']:
                all_accessions[acc].add(row['reference_sequence_sha256'])
    genes = defaultdict(set)
    missing = set()
    network_edges = set()
    def rows(key):
        with (root / io.RAW / cfg['source']['files'][key + '_' + cell]).open(newline='') as handle:
            yield from csv.DictReader(handle, delimiter='\t')
    for row in rows('network'):
        network_edges.add(frozenset((row['GeneA'], row['GeneB'])))
        for side in 'AB':
            gene, accession = row['Gene' + side], row['Uniprot' + side]
            possibilities = all_accessions.get(accession, set())
            if len(possibilities) != 1 or next(iter(possibilities)) not in ids:
                missing.add(gene)
            else:
                genes[gene].add(ids[next(iter(possibilities))])
    gene_map = {g: list(values)[0] for g, values in genes.items() if len(values) == 1 and g not in missing}
    bait_genes = {r['GeneID'] for r in rows('baits')}
    preys, mapped = set(), set()
    for row in rows('directed'):
        a, b = row['Bait GeneID'], row['Prey GeneID']
        assert a in bait_genes and frozenset((a, b)) in network_edges
        preys.add(b)
        if a in gene_map and b in gene_map:
            mapped.add((gene_map[a], gene_map[b]))
    return mapped, {gene_map[g] for g in bait_genes if g in gene_map}, {gene_map[g] for g in preys if g in gene_map}


def reference_panel(data, directed, baits, preys, fold):
    old = {frozenset((int(a), int(b))) for a, b in zip(data['p_a'], data['p_b'])}
    detected = {frozenset(p) for p in directed}
    rows = {}
    for a, b in directed:
        if a != b and data['fold'][a] == fold == data['fold'][b] and frozenset((a, b)) not in old:
            assert a in baits and b in preys
            rows[(a, b)] = (1, 1, 1, -1)
    for i, (a, b, num, den) in enumerate(zip(data['u_a'], data['u_b'], data['u_num'], data['u_den'])):
        if data['fold'][a] != fold or data['fold'][b] != fold or frozenset((a, b)) in detected:
            continue
        if a in baits and b in preys:
            assert (a, b) not in rows
            rows[(a, b)] = (0, num, den, i)
        if b in baits and a in preys:
            assert (b, a) not in rows
            rows[(b, a)] = (0, num, den, i)
    return np.array([(*key, *value) for key, value in sorted(rows.items())], dtype=np.int64).reshape(-1, 6)


def reference_queries(ev):
    grouped = defaultdict(lambda: [[], [], [], []])
    for row, (a, b, positive) in enumerate(zip(ev['a'], ev['b'], ev['positive'])):
        offset = 0 if positive else 2
        grouped[int(a)][offset].append(row)
        grouped[int(a)][offset + 1].append(int(b))
    return [(a, *[np.array(v, dtype=np.int64) for v in grouped[a]]) for a in sorted(grouped)
            if grouped[a][0] and grouped[a][2]]


def reference_quartet_selection(ev, cfg, cell, fold):
    """Brute force directed alternative lookup, without production searchsorted."""
    positive = np.flatnonzero(ev['positive']).tolist()
    unlabeled = {(int(ev['a'][i]), int(ev['b'][i])): i for i in np.flatnonzero(~ev['positive'])}
    possibilities = []
    salt = f"{cfg['quartets']['salt']}:{cell}:{fold}"
    for index, i in enumerate(positive):
        a, b = int(ev['a'][i]), int(ev['b'][i])
        for j in positive[index + 1:]:
            c, d = int(ev['a'][j]), int(ev['b'][j])
            if len({a, b, c, d}) != 4 or (a, d) not in unlabeled or (c, b) not in unlabeled:
                continue
            ends = (a, b, c, d)
            rank = hashlib.sha256((salt + ':' + ':'.join(str(v) for v in ends)).encode()).digest()
            possibilities.append((rank, ends, (i, j, unlabeled[(a, d)], unlabeled[(c, b)])))
    uses, nodes, selected, endpoints = Counter(), Counter(), [], []
    q = cfg['quartets']
    for _, ends, rows in sorted(possibilities):
        if len(selected) == q['maximum_per_fold']:
            break
        if max(uses[rows[0]], uses[rows[1]]) >= q['positive_edge_cap'] or max(nodes[x] for x in ends) >= q['endpoint_cap']:
            continue
        selected.append(rows)
        endpoints.append(ends)
        uses[rows[0]] += 1
        uses[rows[1]] += 1
        nodes.update(ends)
    np.testing.assert_array_equal(ev['quartet_rows'], np.array(selected, dtype=np.int64).reshape(-1, 4))
    np.testing.assert_array_equal(ev['quartet_endpoints'], np.array(endpoints, dtype=np.int64).reshape(-1, 4))
    return len(possibilities)


def validate(root):
    import torch
    cfg = io.verify_freeze(root)
    for name in ('SCORING_COMPLETE.json', 'RESULTS.json'):
        io.verify_records(root, io.read_json(root / io.RESULT / name)['artifacts'])
    if (root / io.VALID / 'REFERENCE_VALIDATION.json').exists():
        raise RuntimeError('numerical validation already recorded')
    result = io.read_json(root / io.RESULT / 'RESULTS.json')
    feasible = io.read_json(root / io.RESULT / 'FEASIBILITY.json')
    data = hio.parent_data(root)
    meta = io.read_json(root / pio.GENERATED / 'endpoint_metadata.json')
    raw = np.load(root / pio.GENERATED / 'raw_public_embeddings.npy', allow_pickle=False).astype(np.float64)
    draws = np.random.Generator(np.random.PCG64DXSM(20260917)).poisson(
        1, (2000, int(data['component'].max()) + 1)).astype(np.int16)
    np.testing.assert_array_equal(draws, np.load(root / io.RUN / 'component_multipliers.npy', allow_pickle=False))
    learned, transfer, panel_rows, max_error = 0, 0, 0, 0.
    for cell in cfg['cells']:
        directed, baits, preys = reference_source(root, cfg, cell, meta)
        source = io.load(root / io.RUN / f'source_{cell}.npz')
        np.testing.assert_array_equal(source['directed'], sorted(directed))
        np.testing.assert_array_equal(source['baits'], sorted(baits))
        np.testing.assert_array_equal(source['preys'], sorted(preys))
        all_points, all_credits, ref_totals, ref_qtotals = {}, {}, {}, {}
        for fold in range(3):
            ev = io.load(root / io.RUN / f'panel_{cell}_{fold}.npz')
            expected = reference_panel(data, directed, baits, preys, fold)
            actual = np.column_stack([ev[k] for k in ('a', 'b', 'positive', 'num', 'den', 'parent_u_row')])
            np.testing.assert_array_equal(actual, expected)
            candidates = reference_quartet_selection(ev, cfg, cell, fold)
            assert candidates == feasible['cells'][cell]['folds'][fold]['candidate_quartets']
            panel_rows += len(actual)
            if not feasible['cells'][cell]['anchor_feasible']:
                continue
            stored = io.load(root / io.RUN / f'scores_{cell}_{fold}.npz')
            names, scores = stored['columns'].tolist(), stored['scores']
            plan = io.load(root / hio.RUN / f'plan_purged20_{fold}.npz')
            fit = plan['fit_endpoints']
            mu = raw[fit].mean(axis=0)
            sigma = np.maximum(np.sqrt(np.mean((raw[fit] - mu) ** 2, axis=0)), 1e-6)
            norm = io.load(root / hio.RUN / f'normalization_purged20_{fold}.npz')
            np.testing.assert_allclose(norm['mean'], mu, atol=1e-12, rtol=0)
            np.testing.assert_allclose(norm['std'], sigma, atol=1e-12, rtol=0)
            x = ((raw - mu) / sigma).astype(np.float32)
            for name in cfg['models']:
                ensemble = []
                for seed in cfg['seeds']:
                    state = torch.load(root / hio.RUN / f'purged20_f{fold}_{name}_s{seed}.pt', map_location='cpu', weights_only=True)['state_dict']
                    ref = reference_scores(state, name, x, ev['a'], ev['b'])
                    observed = scores[:, names.index(f'{name}__{seed}')]
                    max_error = max(max_error, float(np.max(np.abs(ref - observed))))
                    np.testing.assert_allclose(observed, ref, atol=cfg['runtime']['forward_absolute_tolerance'], rtol=0)
                    ensemble.append(observed)
                    learned += len(ref)
                np.testing.assert_array_equal(scores[:, names.index(name)], np.mean(ensemble, axis=0))
            sampled = np.unique(np.linspace(0, len(scores) - 1, min(1024, len(scores)), dtype=int))
            pa, pb = data['p_a'][plan['p_rows']], data['p_b'][plan['p_rows']]
            for name in ('kmer', 'plm', 'local', 'coverage'):
                sim = np.load(hio.similarity_path(root, name), mmap_mode='r', allow_pickle=False)
                for row in sampled:
                    a, b = ev['a'][row], ev['b'][row]
                    possibilities = np.r_[np.minimum(sim[a, pa], sim[b, pb]), np.minimum(sim[a, pb], sim[b, pa])]
                    assert abs(scores[row, names.index('interolog_' + name)] - float(max(possibilities))) <= 2e-6
                transfer += len(sampled)
                if name == 'kmer':
                    np.testing.assert_array_equal(scores[:, names.index('kmer3_cosine')], sim[ev['a'], ev['b']])
            for start in range(0, len(scores), 4096):
                a, b = ev['a'][start:start + 4096], ev['b'][start:start + 4096]
                expected = np.einsum('ij,ij->i', raw[a], raw[b]) / (np.linalg.norm(raw[a], axis=1) * np.linalg.norm(raw[b], axis=1))
                np.testing.assert_allclose(scores[start:start + 4096, names.index('pooled_cosine')], expected, atol=1e-12, rtol=0)
            length = data['length'].astype(float)
            expected = np.exp(-np.abs(np.log(length[ev['a']]) - np.log(length[ev['b']])) )
            np.testing.assert_allclose(scores[:, names.index('length_ratio')], expected, atol=1e-12, rtol=0)
            queries = reference_queries(ev)
            weight = ev['num'].astype(float) / ev['den']
            for j, name in enumerate(names):
                point, total, mass = direct_metrics(scores[:, j], queries, weight, data['component'], draws[:16] if '__' not in name else None)
                np.testing.assert_allclose(point.mean(), result['cells'][cell]['folds'][fold]['macro'][name], atol=1e-12, rtol=0)
                all_points.setdefault(name, []).append(point)
                qr = ev['quartet_rows']
                delta = (scores[qr[:, 0], j] - scores[qr[:, 2], j]) + (scores[qr[:, 1], j] - scores[qr[:, 3], j])
                credit = np.where(np.abs(delta) <= 1e-6, .5, (delta > 0).astype(float))
                all_credits.setdefault(name, []).append(credit)
                if '__' not in name:
                    ref_totals[name] = ref_totals.get(name, 0) + np.stack((total, mass))
                    qt, qm = np.zeros(2000), np.zeros(2000)
                    for value, ends in zip(credit, ev['quartet_endpoints']):
                        unique = set(int(data['component'][e]) for e in ends)
                        product = np.ones(2000)
                        for c in unique:
                            product *= draws[:, c]
                        qt += value * product
                        qm += product
                    ref_qtotals[name] = ref_qtotals.get(name, 0) + np.stack((qt, qm))
            print({'validated': cell, 'fold': fold, 'learned_values_so_far': learned}, flush=True)
        if not feasible['cells'][cell]['anchor_feasible']:
            assert result['cells'][cell]['anchor_status'] == 'infeasible'
            continue
        outcome = result['cells'][cell]
        boot = io.load(root / io.RUN / f'bootstrap_{cell}.npz')
        ab, qb = {}, {}
        for name, blocks in all_points.items():
            np.testing.assert_allclose(np.concatenate(blocks).mean(), outcome['macro'][name], atol=1e-12, rtol=0)
            allq = np.concatenate(all_credits[name])
            if len(allq):
                np.testing.assert_allclose(allq.mean(), outcome['quartet']['preference'][name], atol=1e-12, rtol=0)
            if '__' not in name:
                np.testing.assert_allclose(boot['anchor_' + name][:, :16], ref_totals[name], atol=1e-8, rtol=0)
                np.testing.assert_allclose(boot['quartet_' + name], ref_qtotals[name], atol=1e-8, rtol=0)
                for prefix, dest in (('anchor_', ab), ('quartet_', qb)):
                    num, den = boot[prefix + name]
                    dest[name] = np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0)
        for c in cfg['controls']:
            np.testing.assert_allclose(outcome['deltas'][c]['point'], outcome['macro']['pair_linear'] - outcome['macro'][c], atol=1e-12, rtol=0)
            check_interval(ab['pair_linear'] - ab[c], outcome['deltas'][c])
            check_interval(qb['pair_linear'] - qb[c], outcome['quartet']['deltas'][c])
            if outcome['quartet']['count']:
                np.testing.assert_allclose(outcome['quartet']['deltas'][c]['point'], outcome['quartet']['preference']['pair_linear'] - outcome['quartet']['preference'][c], atol=1e-12, rtol=0)
        check_interval(qb['pair_linear'], outcome['quartet']['interval'])
        passes = outcome['macro']['pair_linear'] >= max(outcome['macro'][c] for c in cfg['controls']) + .02
        passes &= all(outcome['deltas'][c]['ci95'] is not None and outcome['deltas'][c]['ci95'][0] > 0 for c in cfg['controls'])
        passes &= all(f['macro']['pair_linear'] > f['macro']['endpoint_linear'] for f in outcome['folds'])
        passes &= all(outcome['macro'][f'pair_linear__{s}'] > outcome['macro'][f'endpoint_linear__{s}'] for s in cfg['seeds'])
        assert outcome['anchor_signal_survives'] == bool(passes)
        qinterval = outcome['quartet']['interval']['ci95']
        qpass = feasible['cells'][cell]['quartet_feasible'] and qinterval is not None and qinterval[0] > .5
        qpass &= all(outcome['quartet']['deltas'][c]['ci95'] is not None and outcome['quartet']['deltas'][c]['ci95'][0] > 0
                     for c in cfg['controls'] if c != 'endpoint_linear')
        assert outcome['swap_signal_survives'] == bool(qpass)
    assert result['all_external_challenges_pass'] == all(c['anchor_signal_survives'] and c['swap_signal_survives'] for c in result['cells'].values())
    out = {'created_utc': io.now(), 'passed': True, 'learned_values_checked': learned,
           'maximum_forward_absolute_error': max_error, 'sampled_exhaustive_transfer_values_checked': transfer,
           'directed_panel_rows_independently_reconstructed': panel_rows,
           'all_source_mappings_and_quartet_selection_checked': True,
           'all_point_estimates_and_decision_arithmetic_checked': True,
           'independent_anchor_bootstrap_replicates_per_cell': 16,
           'independent_quartet_bootstrap_replicates_per_cell': 2000,
           'same_author_numerical_audit_not_external_review': True}
    io.write_json(root / io.VALID / 'REFERENCE_VALIDATION.json', out)
    return out


def close(root):
    io.verify_freeze(root)
    if (root / io.RESULT / 'ARTIFACT_REGISTRY.json').exists():
        raise RuntimeError('closure already recorded')
    assert io.read_json(root / io.VALID / 'REFERENCE_VALIDATION.json')['passed'] is True
    for name in ('SCORING_COMPLETE.json', 'RESULTS.json'):
        io.verify_records(root, io.read_json(root / io.RESULT / name)['artifacts'])
    for prior in (hio.RESULT, pio.RESULTS):
        io.verify_records(root, io.read_json(root / prior / 'ARTIFACT_REGISTRY.json')['artifacts'])
    before = io.passed_tests(root / io.VALID / 'unit_tests_pre_execution.xml') | io.passed_tests(root / io.VALID / 'gpu_control_pre_execution.xml')
    after = io.passed_tests(root / io.VALID / 'unit_tests_post_execution.xml') | io.passed_tests(root / io.VALID / 'gpu_control_post_execution.xml')
    assert before == after
    paths = [root / p for p in (io.CONFIG,
        'docs/protocols/EXTERNAL_BIOPLEX_CHALLENGE_v1.md',
        'governance/decisions/DEC-0048-authorize-locked-external-bioplex-challenge.md',
        'docs/reports/m1/M1_External_BioPlex_Challenge_v1.md',
        'governance/PROJECT_STATUS_v48.md', 'governance/gates/gate_status_v48.yaml',
        'scripts/model/run_external_bioplex_challenge_v1.py', 'tests/unit/test_external_bioplex.py')]
    paths += sorted((root / 'src/ipin_openppi/external_bioplex').glob('*.py'))
    paths += sorted((root / io.RESULT).glob('*.json'))
    paths += sorted(p for p in (root / io.VALID).iterdir() if p.is_file())
    out = {'created_utc': io.now(), 'protocol_id': io.ID, 'execution_complete': True,
           'numerical_validation_passed': True, 'distinct_tests': len(after),
           'prior_two_study_closures_unchanged': True, 'protected_access': False,
           'publication_authorized_by_user': True, 'new_fits': 0,
           'raw_and_large_arrays_remain_local': True,
           'artifacts': [io.artifact(root, p) for p in paths]}
    io.write_json(root / io.RESULT / 'ARTIFACT_REGISTRY.json', out)
    return {'closure_artifacts': len(paths), 'tests': len(after), 'prior_closures_unchanged': True}
