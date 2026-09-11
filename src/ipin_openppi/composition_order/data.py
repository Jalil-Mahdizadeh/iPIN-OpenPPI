"""Fail-closed, append-only registration for a diagnostic of existing evidence."""

import os
from pathlib import Path
import platform

import numpy as np
import yaml

from ipin_openppi.external_bioplex import data as bio
from ipin_openppi.homology_source import data as hio
from ipin_openppi.partner_specificity import data as pio
from ipin_openppi.stage1.support import atomic_npz, atomic_numpy, sha256_file

ID = 'composition_order_challenge_v1'
CONFIG = Path('configs') / f'{ID}.yaml'
RUN, RESULT, VALID = [Path('artifacts') / p / ID for p in ('runs', 'results', 'validation')]
read_json, write_json, artifact, verify_records, now, load = (
    bio.read_json, bio.write_json, bio.artifact, bio.verify_records, bio.now, bio.load)


def config(root):
    c = yaml.safe_load((root / CONFIG).read_text())
    if (c['protocol_id'] != ID or c['cells'] != ['293T', 'HCT116'] or c['folds'] != [0, 1, 2]
            or any(c[k] is not False for k in ('protected_access', 'development_access',
                                             'new_source_acquisition', 'fresh_validation'))
            or c['new_fits'] != 0 or c['new_embeddings'] != 0
            or c['shuffle']['replicates_per_endpoint'] != 64
            or c['shuffle']['alphabet'] != 'ACDEFGHIKLMNPQRSTVWYX'
            or not c['shuffle']['mean_vectors_are_not_renormalized']
            or c['matching']['tiers'] != ['composition_length', 'also_direct_similarity']
            or c['bootstrap']['source'] != str(bio.RUN / 'component_multipliers.npy')):
        raise RuntimeError('diagnostic boundary drift')
    return c


def runtime():
    if not os.environ.get('APPTAINER_CONTAINER') or platform.machine() != 'aarch64':
        raise RuntimeError('scientific phases require the pinned ARM64 Apptainer runtime')


def save_npz(path, **arrays):
    if path.exists():
        raise RuntimeError('refusing to replace generated artifact')
    atomic_npz(path, **arrays)


def save_numpy(path, array):
    if path.exists():
        raise RuntimeError('refusing to replace generated artifact')
    atomic_numpy(path, array)


def prior_closures(root):
    records = []
    for directory in (pio.RESULTS, hio.RESULT, bio.RESULT):
        path = root / directory / 'ARTIFACT_REGISTRY.json'
        verify_records(root, read_json(path)['artifacts'])
        records.append(artifact(root, path))
    return records


def register(root):
    runtime()
    cfg = config(root)
    if (root / RESULT).exists() or (root / RUN).exists():
        raise RuntimeError('diagnostic namespace already exists')
    for file, key in [('EXECUTION_FREEZE.json', 'parent_execution_freeze_sha256'), ('RESULTS.json', 'parent_results_sha256')]:
        if sha256_file(root / bio.RESULT / file) != cfg[key]:
            raise RuntimeError('parent identity mismatch')
    bio.verify_freeze(root)
    closures = prior_closures(root)
    image = Path(cfg['runtime']['data_image'])
    if sha256_file(root / image) != cfg['runtime']['data_image_sha256']:
        raise RuntimeError('runtime identity mismatch')
    paths = [CONFIG, Path(cfg['authority']), Path(cfg['protocol']), image,
             pio.GENERATED / 'public_arrays.npz', pio.GENERATED / 'endpoint_metadata.json',
             bio.RESULT / 'EXECUTION_FREEZE.json', bio.RESULT / 'RESULTS.json',
             bio.RUN / 'component_multipliers.npy']
    for cell in cfg['cells']:
        paths.append(bio.RUN / f'bootstrap_{cell}.npz')
        for f in cfg['folds']:
            paths += [bio.RUN / f'panel_{cell}_{f}.npz', bio.RUN / f'scores_{cell}_{f}.npz']
    records = [artifact(root, root / p) for p in paths] + closures
    write_json(root / RESULT / 'PREREGISTRATION.json', {
        'created_utc': now(), 'config': cfg, 'artifacts': records,
        'parent_results_seen': True, 'fresh_validation': False, 'external_registration': False,
        'new_features_match_counts_or_scores_computed': False, 'new_fits': 0, 'protected_access': False})
    return {'registered': True, 'reused_artifact_records': len(records)}


def verify_registration(root):
    runtime()
    reg = read_json(root / RESULT / 'PREREGISTRATION.json')
    verify_records(root, reg['artifacts'])
    if config(root) != reg['config']:
        raise RuntimeError('registered configuration drift')
    return reg['config']


def freeze(root):
    verify_registration(root)
    if (root / RESULT / 'EXECUTION_FREEZE.json').exists() or (root / RUN).exists():
        raise RuntimeError('freeze must precede new diagnostic computation')
    xml = root / VALID / 'unit_tests_pre_execution.xml'
    passed = bio.passed_tests(xml)
    if not any('test_composition_order' in cls for cls, _ in passed):
        raise RuntimeError('dedicated tests missing')
    paths = sorted((root / 'src/ipin_openppi').rglob('*.py'))
    paths += sorted((root / 'tests/unit').glob('*.py'))
    paths += [root / 'scripts/model/run_composition_order_challenge_v1.py', xml,
              root / RESULT / 'PREREGISTRATION.json']
    write_json(root / RESULT / 'EXECUTION_FREEZE.json', {
        'created_utc': now(), 'artifacts': [artifact(root, p) for p in paths],
        'tests_passed': len(passed), 'diagnostic_outcomes_seen': False})
    return {'execution_frozen': True, 'CPU_tests': len(passed)}


def verify_freeze(root):
    cfg = verify_registration(root)
    verify_records(root, read_json(root / RESULT / 'EXECUTION_FREEZE.json')['artifacts'])
    return cfg
