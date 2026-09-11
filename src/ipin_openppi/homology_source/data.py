"""Allowlisted public provenance projection, homology search and phase freezes."""

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from scipy import sparse
import yaml

from ipin_openppi.partner_specificity import data as parent
from ipin_openppi.partner_specificity.semantics import build_queries
from ipin_openppi.stage1.baselines import kmer3_csr
from ipin_openppi.stage1.support import atomic_numpy, atomic_npz, sha256_file
from .semantics import alignment_scores, alignment_values, fit_rows, panel_mask, purged_fit_mask

ID = 'homology_source_challenge_v1'
CONFIG = Path('configs') / (ID + '.yaml')
RUN = Path('artifacts/runs') / ID
RESULT = Path('artifacts/results') / ID
VALID = Path('artifacts/validation') / ID
SOURCE_ROOT = Path('data/canonical/primary_reconciliation_v1/huri_evidence_gene_pair_projections')
read_json, write_json, artifact, verify_records, now = (
    parent.read_json, parent.write_json, parent.artifact, parent.verify_records, parent.now)


def config(root):
    cfg = yaml.safe_load((root / CONFIG).read_text())
    if cfg['protocol_id'] != ID or cfg['protected_access'] is not False:
        raise RuntimeError('protocol boundary drift')
    if cfg['source_projection']['root'] != str(SOURCE_ROOT) or set(cfg['source_projection']['parts']) != {
        'part-00000.parquet', 'part-00001.parquet', 'part-00002.parquet'}:
        raise RuntimeError('source allowlist drift')
    if cfg['arms'] != ['union', 'purged20', 'hi_to_huri', 'huri_to_hi']:
        raise RuntimeError('arm drift')
    return cfg


def parent_data(root):
    with np.load(root / parent.GENERATED / 'public_arrays.npz', allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def kmer_similarity(sequences):
    # Sparse dot products can sum thousands of terms: accumulate in FP64.
    kmer = kmer3_csr(sequences)
    return (kmer @ kmer.T).toarray().astype(np.float32)


def similarity_path(root, name):
    if name == 'kmer' and (root / RESULT / 'PRE_EXECUTION_PRECISION_CORRECTION.json').exists():
        return root / RUN / 'similarity_kmer_fp64_accumulated.npy'
    return root / RUN / f'similarity_{name}.npy'


def correct_precision(root):
    verify_registration(root)
    if (root / RESULT / 'EXECUTION_FREEZE.json').exists() or (root / RESULT / 'TRAINING_COMPLETE.json').exists():
        raise RuntimeError('precision correction only allowed before execution freeze')
    if (root / RESULT / 'PRE_EXECUTION_PRECISION_CORRECTION.json').exists():
        raise RuntimeError('precision correction already complete')
    meta = read_json(root / parent.GENERATED / 'endpoint_metadata.json')
    path = root / RUN / 'similarity_kmer_fp64_accumulated.npy'
    if path.exists():
        raise RuntimeError('refusing corrected similarity overwrite')
    atomic_numpy(path, kmer_similarity(meta['sequences']))
    out = {'created_utc': now(), 'reason': 'FP32_sparse_accumulation_exceeded_frozen_2e-6_tolerance',
           'correction': 'FP64_sparse_accumulation_then_FP32_storage', 'tolerance_changed': False,
           'scientific_design_changed': False, 'new_fits_or_scores_exist': False,
           'original_artifact_preserved': artifact(root, root / RUN / 'similarity_kmer.npy'),
           'artifacts': [artifact(root, path), artifact(root, root / VALID / 'pre_execution_precision_failure.txt')]}
    write_json(root / RESULT / 'PRE_EXECUTION_PRECISION_CORRECTION.json', out)
    return out


def verify_parent(root, cfg):
    for path, expected in ((parent.CONFIG, cfg['parent_config_sha256']),
                           (parent.RESULTS / 'EXECUTION_FREEZE.json', cfg['parent_execution_freeze_sha256'])):
        if sha256_file(root / path) != expected:
            raise RuntimeError('parent identity drift')
    parent.verify_freeze(root)
    for name in ('TRAINING_COMPLETE.json', 'SCORING_COMPLETE.json'):
        verify_records(root, read_json(root / parent.RESULTS / name)['artifacts'])


def register(root):
    cfg = config(root)
    if (root / RESULT).exists() or (root / RUN).exists():
        raise RuntimeError('study already registered; refusing overwrite')
    verify_parent(root, cfg)
    records = [artifact(root, root / p) for p in (CONFIG, Path(cfg['authority']), Path(cfg['protocol']))]
    for name, expected in cfg['source_projection']['parts'].items():
        rec = artifact(root, root / SOURCE_ROOT / name)
        if rec['sha256'] != expected:
            raise RuntimeError('source archive drift')
        records.append(rec)
    for path, expected in [(cfg['mmseqs']['binary'], cfg['mmseqs']['sha256'])] + [
        (cfg['runtime'][k], cfg['runtime'][k + '_sha256']) for k in ('data_image', 'model_image')]:
        rec = artifact(root, root / path)
        if rec['sha256'] != expected:
            raise RuntimeError('runtime identity drift')
        records.append(rec)
    for p in (parent.CONFIG, parent.RESULTS / 'EXECUTION_FREEZE.json',
              parent.RESULTS / 'FEASIBILITY.json', parent.RESULTS / 'SCORING_COMPLETE.json'):
        records.append(artifact(root, root / p))
    out = {'created_utc': now(), 'config': cfg, 'artifacts': records,
           'prior_results_informed_question': True, 'new_source_counts_or_scores_seen': False,
           'external_registry': False, 'protected_access': False}
    write_json(root / RESULT / 'PREREGISTRATION.json', out)
    return {'registered': True, 'config_sha256': sha256_file(root / CONFIG)}


def verify_registration(root):
    reg = read_json(root / RESULT / 'PREREGISTRATION.json')
    verify_records(root, reg['artifacts'])
    if config(root) != reg['config']:
        raise RuntimeError('frozen config drift')
    return reg['config']


def project_sources(connection, public_pairs, gene_mapping, files):
    """Only public-positive indices and source bits leave the SQL query."""
    connection.register('allowed_pairs', public_pairs)
    connection.register('public_genes', gene_mapping)
    return connection.execute('''
        SELECT p.positive_index, bit_or(CASE e.source_dataset
               WHEN 'HI-II-14' THEN 1 WHEN 'HuRI' THEN 2 ELSE 0 END) AS source_bit
        FROM read_parquet(?) e
        JOIN public_genes a ON e.gene_a=a.gene
        JOIN public_genes b ON e.gene_b=b.gene
        JOIN allowed_pairs p ON p.a=least(a.endpoint,b.endpoint)
                             AND p.b=greatest(a.endpoint,b.endpoint)
        WHERE e.unique_gene_pair AND NOT e.label_authorized
        GROUP BY p.positive_index ORDER BY p.positive_index
    ''', [files]).fetchall()


def annotate(root):
    import duckdb
    cfg = verify_registration(root)
    if (root / RESULT / 'SOURCE_PROJECTION.json').exists():
        raise RuntimeError('source projection already complete')
    data = parent_data(root)
    meta = read_json(root / parent.GENERATED / 'endpoint_metadata.json')
    lookup = {e: i for i, e in enumerate(meta['endpoints'])}
    endpoint_path = parent.config(root)['inputs']['endpoints']['path']
    table = pq.read_table(root / endpoint_path, columns=['reference_sequence_sha256', 'space_iii_gene_ids']).to_pylist()
    genes = [(gene, lookup[r['reference_sequence_sha256']]) for r in table
             if r['reference_sequence_sha256'] in lookup for gene in r['space_iii_gene_ids']]
    if len({g for g, _ in genes}) != len(genes):
        raise RuntimeError('ambiguous public gene map')
    mapping = pa.table({'gene': [g for g, _ in genes], 'endpoint': [e for _, e in genes]})
    allowed = pa.table({'positive_index': np.arange(len(data['p_a'])),
                        'a': np.minimum(data['p_a'], data['p_b']), 'b': np.maximum(data['p_a'], data['p_b'])})
    files = [str(root / SOURCE_ROOT / name) for name in sorted(cfg['source_projection']['parts'])]
    with duckdb.connect(':memory:') as conn:
        conn.execute('SET threads=8')
        rows = project_sources(conn, allowed, mapping, files)
    if [r[0] for r in rows] != list(range(len(data['p_a']))) or any(r[1] not in (1, 2, 3) for r in rows):
        raise RuntimeError('incomplete or invalid public-positive source projection')
    bits = np.array([r[1] for r in rows], dtype=np.uint8)
    path = root / RUN / 'public_positive_source_bits.npy'
    atomic_numpy(path, bits)
    out = {'created_utc': now(), 'emitted_public_P': len(bits), 'additional_pair_rows_emitted': 0,
           'counts': {str(k): int((bits == k).sum()) for k in (1, 2, 3)},
           'source_meaning': {'1': 'HI-II-14_only', '2': 'HuRI_only', '3': 'both'},
           'complete_assay_opportunity_metadata': False, 'protected_artifacts_read': False,
           'artifacts': [artifact(root, path)]}
    write_json(root / RESULT / 'SOURCE_PROJECTION.json', out)
    return out


def search(root):
    cfg = verify_registration(root)
    if (root / RUN / 'mmseqs').exists():
        raise RuntimeError('existing search workspace requires explicit operational review')
    work = root / RUN / 'mmseqs'
    work.mkdir(parents=True)
    meta = read_json(root / parent.GENERATED / 'endpoint_metadata.json')
    fasta = work / 'public.fasta'
    with fasta.open('x') as handle:
        for i, seq in enumerate(meta['sequences']):
            handle.write(f'>{i}\n{seq}\n')
    binary = str(root / cfg['mmseqs']['binary'])
    version = subprocess.check_output([binary, 'version'], text=True).strip()
    if version != cfg['mmseqs']['version']:
        raise RuntimeError('MMseqs version mismatch')
    db, result, tmp, tsv = (str(work / n) for n in ('db', 'result', 'tmp', 'alignments.tsv'))
    commands = [[binary, 'createdb', str(fasta), db, '--shuffle', '0', '--createdb-mode', '0'],
                [binary, 'search', db, db, result, tmp, *cfg['mmseqs']['search_parameters']],
                [binary, 'convertalis', db, db, result, tsv, '--format-output', cfg['mmseqs']['fields'], '--threads', '8']]
    for i, command in enumerate(commands):
        print(f'MMseqs phase {i}: {command[1]}', flush=True)
        with (work / f'command_{i}.log').open('x') as handle:
            subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, check=True)
    out = {'created_utc': now(), 'public_sequences': len(meta['sequences']), 'version': version,
           'commands': commands, 'artifacts': [artifact(root, Path(tsv)), artifact(root, fasta)] + [
               artifact(root, work / f'command_{i}.log') for i in range(3)]}
    write_json(root / RESULT / 'SEARCH_COMPLETE.json', out)
    return {'search_complete': True}


def prepare(root):
    cfg = verify_registration(root)
    if (root / RESULT / 'FEASIBILITY.json').exists():
        raise RuntimeError('already prepared')
    for name in ('SOURCE_PROJECTION.json', 'SEARCH_COMPLETE.json'):
        verify_records(root, read_json(root / RESULT / name)['artifacts'])
    data = parent_data(root)
    source = np.load(root / RUN / 'public_positive_source_bits.npy', allow_pickle=False)
    n = len(data['fold'])
    local, coverage = np.zeros((n, n), np.float32), np.zeros((n, n), np.float32)
    purge_edges, self_seen = set(), set()
    rows, qualifying = 0, 0
    with (root / RUN / 'mmseqs/alignments.tsv').open() as handle:
        for line in handle:
            values = alignment_values(line.rstrip().split('\t'), data['length'])
            a, b, loc, cov, purge = alignment_scores(values)
            rows += 1
            if a == b:
                self_seen.add(a)
            if loc:
                qualifying += 1
                local[a, b] = local[b, a] = max(float(local[a, b]), loc)
                coverage[a, b] = coverage[b, a] = max(float(coverage[a, b]), cov)
                if purge and a != b:
                    purge_edges.add(tuple(sorted((a, b))))
    # Very short proteins may have no >=40-span self hit; require all eligible lengths.
    if not set(np.flatnonzero(data['length'] >= 40)).issubset(self_seen):
        raise RuntimeError('missing eligible self alignments')
    edges = np.array(sorted(purge_edges), dtype=np.int64).reshape(-1, 2)
    paths = []
    for name, matrix in (('local', local), ('coverage', coverage)):
        p = root / RUN / f'similarity_{name}.npy'
        atomic_numpy(p, matrix)
        paths.append(p)
    p = root / RUN / 'purge_edges.npy'
    atomic_numpy(p, edges)
    paths.append(p)
    meta = read_json(root / parent.GENERATED / 'endpoint_metadata.json')
    km = kmer_similarity(meta['sequences'])
    raw = np.load(root / parent.GENERATED / 'raw_public_embeddings.npy', allow_pickle=False).astype(np.float64)
    unit = raw / np.linalg.norm(raw, axis=1)[:, None]
    plm = np.maximum(unit @ unit.T, 0).astype(np.float32)
    for name, matrix in (('kmer', km), ('plm', plm)):
        p = root / RUN / f'similarity_{name}.npy'
        atomic_numpy(p, matrix)
        paths.append(p)
    census = []
    for arm in cfg['arms']:
        for fold in range(3):
            fit = data['fold'] != fold
            if arm == 'purged20':
                fit = purged_fit_mask(data['fold'], data['component'], fold, edges[:, 0], edges[:, 1])
            visible = {'hi_to_huri': 1, 'huri_to_hi': 2}.get(arm, 0)
            target = {'hi_to_huri': 2, 'huri_to_hi': 1}.get(arm, 0)
            plan = fit_rows(data, source, fit, visible)
            with np.load(root / parent.GENERATED / f'evaluation_fold_{fold}.npz', allow_pickle=False) as z:
                ev = {k: z[k] for k in z.files}
            include = panel_mask(ev, source, target)
            # Keep parent coordinates: all excluded target/source P are absent, not relabeled as U.
            query = build_queries(ev['a'][include], ev['b'][include], ev['positive'][include])
            qkeep = np.all(include[ev['quartet_rows']], axis=1)
            quartet_components = np.unique(data['component'][ev['quartet_endpoints'][qkeep]])
            anchors = np.array([q.anchor for q in query], dtype=np.int64)
            cross = np.sum(((data['fold'][edges[:, 0]] == fold) & fit[edges[:, 1]]) |
                           ((data['fold'][edges[:, 1]] == fold) & fit[edges[:, 0]]))
            no_hit_endpoint = ~np.any(local[:, data['fold'] != fold] > 0, axis=1)
            plan.update(evaluation_mask=include, quartet_mask=qkeep,
                        no_hit_pair=no_hit_endpoint[ev['a']] & no_hit_endpoint[ev['b']])
            p = root / RUN / f'plan_{arm}_{fold}.npz'
            atomic_npz(p, **plan)
            paths.append(p)
            mins = cfg['feasibility']
            record = {'arm': arm, 'fold': fold, 'fit_endpoints': int(fit.sum()),
                      'removed_fit_endpoints': int((data['fold'] != fold).sum() - fit.sum()),
                      'fit_P': len(plan['p_rows']), 'fit_U': len(plan['u_a']),
                      'target_only_P_hidden_as_U': len(plan['hidden_p_rows']),
                      'evaluation_P': int((include & ev['positive']).sum()),
                      'evaluation_U': int((include & ~ev['positive']).sum()),
                      'anchors': len(anchors), 'anchor_components': len(np.unique(data['component'][anchors])),
                      'quartets': int(qkeep.sum()), 'quartet_components': len(quartet_components),
                      'direct_remote_cross_edges': int(cross)}
            record['anchor_feasible'] = all(record[k] >= mins[m] for k, m in (
                ('fit_P', 'minimum_fit_P'), ('fit_U', 'minimum_fit_U'),
                ('anchors', 'minimum_anchors'), ('anchor_components', 'minimum_anchor_components')))
            record['quartet_feasible'] = record['quartets'] >= mins['minimum_quartets'] and len(quartet_components) >= mins['minimum_quartet_components']
            census.append(record)
            print(json.dumps(record), flush=True)
    out = {'created_utc': now(), 'alignments': rows, 'qualifying_alignment_rows': qualifying,
           'undirected_remote_edges': len(edges), 'folds': census,
           'feasible_arms': [a for a in cfg['arms'] if all(r['anchor_feasible'] for r in census if r['arm'] == a)],
           'quartet_feasible_arms': [a for a in cfg['arms'] if all(r['quartet_feasible'] for r in census if r['arm'] == a)],
           'artifacts': [artifact(root, p) for p in paths]}
    write_json(root / RESULT / 'FEASIBILITY.json', out)
    return out


def freeze(root):
    cfg = verify_registration(root)
    verify_parent(root, cfg)
    feasible = read_json(root / RESULT / 'FEASIBILITY.json')
    verify_records(root, feasible['artifacts'])
    tests = root / VALID / 'unit_tests_final_pre_execution.xml'
    tree = ET.parse(tests)
    suites = list(tree.getroot().iter('testsuite'))
    if not suites or sum(int(s.get('tests', 0)) for s in suites) < 358 or any(
        int(s.get(k, 0)) for s in suites for k in ('errors', 'failures')):
        raise RuntimeError('passing complete unit suite required before execution freeze')
    paths = sorted((root / 'src/ipin_openppi/homology_source').glob('*.py')) + [
        root / 'scripts/model/run_homology_source_challenge_v1.py',
        root / 'tests/unit/test_homology_source.py', tests]
    paths += [root / RESULT / name for name in (
        'PREREGISTRATION.json', 'SOURCE_PROJECTION.json', 'SEARCH_COMPLETE.json', 'FEASIBILITY.json')]
    correction = root / RESULT / 'PRE_EXECUTION_PRECISION_CORRECTION.json'
    if correction.exists():
        verify_records(root, read_json(correction)['artifacts'])
        paths.append(correction)
        paths.extend(root / a['path'] for a in read_json(correction)['artifacts'])
    gpu_tests = root / VALID / 'gpu_control_pre_execution.xml'
    gpu_suites = list(ET.parse(gpu_tests).getroot().iter('testsuite'))
    if not gpu_suites or any(int(s.get(k, 0)) for s in gpu_suites for k in ('errors', 'failures', 'skipped')):
        raise RuntimeError('passing GPU control test required')
    paths.append(gpu_tests)
    reference = root / VALID / 'label_free_reference_pre_execution.json'
    if read_json(reference).get('passed') is not True:
        raise RuntimeError('label-free reference matrices must pass before execution freeze')
    paths.append(reference)
    out = {'created_utc': now(), 'before_any_new_fits_or_scores': True,
           'feasible_arms': feasible['feasible_arms'], 'artifacts': [artifact(root, p) for p in paths]}
    write_json(root / RESULT / 'EXECUTION_FREEZE.json', out)
    return {'execution_frozen': True, 'arms': out['feasible_arms']}


def verify_freeze(root):
    cfg = verify_registration(root)
    verify_records(root, read_json(root / RESULT / 'EXECUTION_FREEZE.json')['artifacts'])
    verify_records(root, read_json(root / RESULT / 'FEASIBILITY.json')['artifacts'])
    verify_parent(root, cfg)
    return cfg
