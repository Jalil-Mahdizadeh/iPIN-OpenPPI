"""Immutable registration and bounded published-source acquisition."""

import csv
import os
from pathlib import Path
import platform
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np
import yaml

from ipin_openppi.homology_source import data as hio
from ipin_openppi.partner_specificity import data as pio
from ipin_openppi.stage1.support import sha256_file

ID = 'external_bioplex_challenge_v1'
CONFIG = Path('configs') / f'{ID}.yaml'
RUN = Path('artifacts/runs') / ID
RESULT = Path('artifacts/results') / ID
VALID = Path('artifacts/validation') / ID
RAW = Path('data/raw/bioplex') / ID
read_json, write_json, artifact, verify_records, now = (
    pio.read_json, pio.write_json, pio.artifact, pio.verify_records, pio.now)


def load(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def config(root):
    cfg = yaml.safe_load((root / CONFIG).read_text())
    if (cfg['protocol_id'] != ID or cfg['protected_access'] is not False
            or cfg['development_access'] is not False or cfg['new_fits'] != 0
            or cfg['model_arm'] != 'purged20' or cfg['cells'] != ['293T', 'HCT116']
            or cfg['models'] != ['endpoint_linear', 'pair_linear']
            or cfg['seeds'] != [20260911, 20260912, 20260913]):
        raise RuntimeError('external challenge boundary drift')
    return cfg


def register(root):
    cfg = config(root)
    if (root / RESULT).exists() or (root / RUN).exists() or (root / RAW).exists():
        raise RuntimeError('registered namespace cannot be overwritten')
    if sha256_file(root / hio.RESULT / 'EXECUTION_FREEZE.json') != cfg['parent_execution_freeze_sha256']:
        raise RuntimeError('parent freeze mismatch')
    hio.verify_freeze(root)
    registry = read_json(root / hio.RESULT / 'ARTIFACT_REGISTRY.json')
    verify_records(root, registry['artifacts'])
    verify_records(root, read_json(root / hio.RESULT / 'TRAINING_COMPLETE.json')['artifacts'])
    paths = [CONFIG, Path(cfg['authority']), Path(cfg['protocol']),
             hio.RESULT / 'ARTIFACT_REGISTRY.json', hio.RESULT / 'EXECUTION_FREEZE.json',
             pio.GENERATED / 'public_arrays.npz', pio.GENERATED / 'endpoint_metadata.json',
             pio.GENERATED / 'raw_public_embeddings.npy', hio.RUN / 'purge_edges.npy',
             Path(pio.config(root)['inputs']['endpoints']['path'])]
    for fold in range(3):
        paths += [hio.RUN / f'plan_purged20_{fold}.npz', hio.RUN / f'normalization_purged20_{fold}.npz']
        paths += [hio.RUN / f'purged20_f{fold}_{m}_s{s}.pt' for m in cfg['models'] for s in cfg['seeds']]
    paths += [hio.similarity_path(root, k).relative_to(root) for k in ('kmer', 'plm', 'local', 'coverage')]
    for key in ('data_image', 'model_image'):
        p = Path(cfg['runtime'][key])
        if sha256_file(root / p) != cfg['runtime'][key + '_sha256']:
            raise RuntimeError('container identity mismatch')
        paths.append(p)
    records = [artifact(root, root / p) for p in paths]
    out = {'created_utc': now(), 'config': cfg, 'artifacts': records,
           'checkpoints_locked_before_external_acquisition': True, 'new_fits': 0,
           'external_interaction_rows_acquired': False, 'prior_internal_outcomes_informed_design': True,
           'external_registration': False, 'protected_access': False}
    write_json(root / RESULT / 'PREREGISTRATION.json', out)
    return {'registered': True, 'locked_checkpoints': 18, 'artifacts': len(records)}


def verify_registration(root):
    reg = read_json(root / RESULT / 'PREREGISTRATION.json')
    verify_records(root, reg['artifacts'])
    if config(root) != reg['config']:
        raise RuntimeError('registered scientific configuration changed')
    return reg['config']


def allowed_url(url, cfg):
    permitted = {cfg['source']['page']} | {
        cfg['source']['origin'] + '/data/' + v for v in cfg['source']['files'].values()}
    if url not in permitted or urllib.parse.urlsplit(url).scheme != 'https':
        raise RuntimeError('URL outside exact published-source allowlist')


class AllowlistedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, cfg):
        self.cfg = cfg

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl, self.cfg)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def acquire(root):
    cfg = verify_registration(root)
    if not os.environ.get('APPTAINER_CONTAINER') or platform.machine() != 'aarch64':
        raise RuntimeError('scientific downloads require the ARM64 Apptainer runtime')
    if (root / RESULT / 'ACQUISITION.json').exists() or (root / RAW).exists():
        raise RuntimeError('existing raw snapshot cannot be overwritten')
    raw = root / RAW
    raw.mkdir(parents=True)
    opener = urllib.request.build_opener(AllowlistedRedirect(cfg))
    assets = [('release_page', 'interactions.html', cfg['source']['page'])] + [
        (k, v, cfg['source']['origin'] + '/data/' + v) for k, v in cfg['source']['files'].items()]
    records, responses = [], []
    for key, filename, url in assets:
        allowed_url(url, cfg)
        path = raw / filename
        partial = path.with_suffix(path.suffix + '.partial')
        started = now()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'iPIN-OpenPPI research/DEC-0048'})
            with opener.open(req, timeout=45) as response, partial.open('xb') as handle:
                allowed_url(response.geturl(), cfg)
                size = 0
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > cfg['source']['maximum_file_bytes']:
                        raise RuntimeError('source file exceeds registered size ceiling')
                    handle.write(block)
                if not size or (response.headers.get('Content-Length') and size != int(response.headers['Content-Length'])):
                    raise RuntimeError('incomplete source download')
                header_record = {k: response.headers.get(k) for k in (
                    'Content-Type', 'Content-Length', 'ETag', 'Last-Modified', 'Content-Disposition')}
                info = {'key': key, 'url': url, 'final_url': response.geturl(), 'http_status': response.status,
                        'started_utc': started, 'completed_utc': now(), 'headers': header_record,
                        'tls_verification': True, 'provider_checksum': 'not_published_on_release_page'}
                handle.flush()
                os.fsync(handle.fileno())
            os.link(partial, path)  # atomic, refuses replacement even under a race
            partial.unlink()
            path.chmod(0o444)
            records.append(artifact(root, path))
            info['artifact'] = records[-1]
            responses.append(info)
            print({'acquired': key, 'bytes': size}, flush=True)
        except Exception as exc:
            write_json(root / RESULT / 'ACQUISITION_FAILURE.json', {
                'created_utc': now(), 'asset': key, 'error': str(exc), 'completed': responses,
                'partial_path': str(partial.relative_to(root)), 'new_scores': False})
            raise
    out = {'created_utc': now(), 'artifacts': records, 'responses': responses,
           'raw_redistribution': False, 'model_results_seen': False}
    write_json(root / RESULT / 'ACQUISITION.json', out)
    return {'acquired_files': len(records)}


def tsv(path):
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise RuntimeError('invalid TSV header')
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise RuntimeError('ragged TSV row')
            yield row


def passed_tests(path):
    cases = list(ET.parse(path).getroot().iter('testcase'))
    if not cases or any(c.find('failure') is not None or c.find('error') is not None for c in cases):
        raise RuntimeError('unit evidence is empty or failed')
    return {(c.get('classname'), c.get('name')) for c in cases if c.find('skipped') is None}


def freeze(root):
    verify_registration(root)
    if (root / RESULT / 'EXECUTION_FREEZE.json').exists():
        raise RuntimeError('execution already frozen')
    prepared = read_json(root / RESULT / 'FEASIBILITY.json')
    verify_records(root, prepared['artifacts'])
    passed = passed_tests(root / VALID / 'unit_tests_pre_execution.xml')
    passed |= passed_tests(root / VALID / 'gpu_control_pre_execution.xml')
    if not any('external_bioplex' in c for c, _ in passed):
        raise RuntimeError('missing dedicated tests')
    paths = sorted((root / 'src/ipin_openppi/external_bioplex').glob('*.py'))
    paths += [root / p for p in ('scripts/model/run_external_bioplex_challenge_v1.py',
        'tests/unit/test_external_bioplex.py', str(RESULT / 'ACQUISITION.json'),
        str(RESULT / 'FEASIBILITY.json'), str(VALID / 'unit_tests_pre_execution.xml'),
        str(VALID / 'gpu_control_pre_execution.xml'))]
    write_json(root / RESULT / 'EXECUTION_FREEZE.json', {
        'created_utc': now(), 'artifacts': [artifact(root, p) for p in paths],
        'tested_distinct_cases': len(passed), 'new_fits': 0, 'external_scores_seen': False})
    return {'frozen': True, 'tests': len(passed)}


def verify_freeze(root):
    cfg = verify_registration(root)
    for name in ('EXECUTION_FREEZE.json', 'ACQUISITION.json', 'FEASIBILITY.json'):
        verify_records(root, read_json(root / RESULT / name)['artifacts'])
    return cfg
