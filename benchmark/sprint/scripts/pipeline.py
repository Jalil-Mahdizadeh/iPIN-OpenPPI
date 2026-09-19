"""Single-use SPRINT pipeline: sequence HSPs, label-free scoring, frozen evaluation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
from launcher import ROOT, REPO, RUN, PRIVATE, RESULTS, LOGS, SIF, METRIC_SIF, container
from policy import POLICY, REVISION, SCORERS, SPRINT_SIF_SHA, MODEL_SIF_SHA, HSP_THREADS


def now(): return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''): digest.update(block)
    return digest.hexdigest()


def read(path): return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as f: json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)


def rec(path, root):
    path = Path(path)
    return {'path': str(path.relative_to(root)), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as a, target.open('xb') as b: shutil.copyfileobj(a, b)
    assert sha(source) == sha(target)


def verify(root, items):
    for item in items:
        relative = Path(item['path']); assert not relative.is_absolute() and '..' not in relative.parts
        path = root/relative
        assert not path.is_symlink() and path.is_file() and path.stat().st_size == item['bytes']
        assert sha(path) == item['sha256'], str(path)


def prepare():
    assert os.environ.get('SLURM_JOB_ID'), 'An allocation is required'
    assert sha(SIF) == SPRINT_SIF_SHA and sha(METRIC_SIF) == MODEL_SIF_SHA
    native = read(RUN/'qualification/native/NATIVE_QUALIFICATION.json')
    metric = read(RUN/'qualification/metric/METRIC_QUALIFICATION.json')
    data = read(RUN/'data/DATA_FREEZE.json'); pilot = read(RUN/'pilot/HSP_COMPLETE.json')
    assert native['passed'] and metric['passed'] and pilot['passed'] and pilot['pilot']
    assert not data['test_pairs_read'] and not data['test_truth_read']
    verify(RUN/'data', data['files'])
    (RUN/'code').mkdir()
    for path in sorted((ROOT/'scripts').glob('*.py')): copy(path, RUN/'code'/path.name)
    for name in ('gpu_guard.py', 'benchmark_metrics.py'):
        assert sha(RUN/'code'/name) == sha(ROOT.parent/'rapppid/scripts'/name)
    files = [rec(p, RUN) for p in sorted((RUN/'code').glob('*.py'))]
    for relative in ('data/DATA_FREEZE.json', 'qualification/native/NATIVE_QUALIFICATION.json',
                     'qualification/metric/METRIC_QUALIFICATION.json', 'pilot/HSP_COMPLETE.json'):
        files.append(rec(RUN/relative, RUN))
    write(RUN/'INITIAL_FREEZE.json', {'at_utc': now(), 'policy': POLICY, 'files': files,
        'sif_sha256': SPRINT_SIF_SHA, 'metric_sif_sha256': MODEL_SIF_SHA,
        'test_pairs_read': False, 'test_truth_read': False,
        'new_artifacts_confined_to_benchmark': True, 'prepared_on': socket.gethostname(),
        'preparation_slurm_job': os.environ['SLURM_JOB_ID']})
    print({'prepared': True, 'initial_freeze_sha256': sha(RUN/'INITIAL_FREEZE.json')}, flush=True)


def check_initial():
    initial = read(RUN/'INITIAL_FREEZE.json'); verify(RUN, initial['files'])
    assert initial['policy'] == POLICY and not initial['test_pairs_read'] and not initial['test_truth_read']
    assert sha(SIF) == initial['sif_sha256'] == SPRINT_SIF_SHA
    assert sha(METRIC_SIF) == initial['metric_sif_sha256'] == MODEL_SIF_SHA
    verify(RUN/'data', read(RUN/'data/DATA_FREEZE.json')['files'])
    for path in sorted((RUN/'code').glob('*.py')): assert sha(path) == sha(ROOT/'scripts'/path.name)


def hsp():
    check_initial()
    assert len(os.sched_getaffinity(0)) >= HSP_THREADS
    container('full-hsp', RUN/'hsp', [(RUN/'data/proteins.fasta', '/data/proteins.fasta')],
              ['/code/native.py', 'hsp'], native=True, threads=HSP_THREADS)
    status = read(RUN/'hsp/HSP_COMPLETE.json')
    assert status['passed'] and not status['pilot'] and status['proteins_with_full_self_hsp'] == 17000
    assert status['input_fasta_sha256'] == sha(RUN/'data/proteins.fasta')
    assert status['canonical_sha256'] == sha(RUN/'hsp/canonical.hsp')
    print({'hsp_complete': True, 'elapsed_seconds': status['elapsed_seconds']}, flush=True)


def freeze_bundle():
    check_initial(); hsp = read(RUN/'hsp/HSP_COMPLETE.json')
    assert hsp['passed'] and not hsp['pilot'] and hsp['proteins_with_full_self_hsp'] == 17000
    assert hsp['input_fasta_sha256'] == sha(RUN/'data/proteins.fasta')
    assert hsp['canonical_sha256'] == sha(RUN/'hsp/canonical.hsp')
    bundle = RUN/'scorer_bundle'; bundle.mkdir()
    for name in ('proteins.fasta', 'train_positive.txt', 'endpoints.json', 'components.json', 'DATA_FREEZE.json'):
        copy(RUN/'data'/name, bundle/name)
    for name in ('canonical.hsp', 'HSP_COMPLETE.json'): copy(RUN/'hsp'/name, bundle/name)
    for path in sorted((RUN/'code').glob('*.py')): copy(path, bundle/'code'/path.name)
    copy(RUN/'INITIAL_FREEZE.json', bundle/'INITIAL_FREEZE.json')
    copy(RUN/'qualification/native/NATIVE_QUALIFICATION.json', bundle/'NATIVE_QUALIFICATION.json')
    copy(RUN/'qualification/metric/METRIC_QUALIFICATION.json', bundle/'METRIC_QUALIFICATION.json')
    files = [rec(p, bundle) for p in sorted(bundle.rglob('*')) if p.is_file()]
    write(bundle/'SCORER_FREEZE.json', {'at_utc': now(), 'files': files, 'scorers': list(SCORERS),
        'policy': POLICY, 'model_revision': REVISION, 'sif_sha256': SPRINT_SIF_SHA,
        'metric_sif_sha256': MODEL_SIF_SHA, 'test_pairs_read': False, 'test_truth_read': False,
        'initial_freeze_sha256': sha(RUN/'INITIAL_FREEZE.json')})


def evaluate():
    started = time.monotonic(); freeze_bundle()
    PRIVATE.mkdir(parents=True, mode=0o700, exist_ok=False)
    container('open', PRIVATE/'session', [(REPO/'.private/model_optimization_followup_v1/session', '/previous_session')],
        ['/code/comparison.py', 'open'], frozen=True)
    session = (PRIVATE/'session', '/session'); predictions = (PRIVATE/'predictions', '/predictions')
    references = (PRIVATE/'references', '/references'); freeze = (PRIVATE/'freeze', '/freeze')
    native_input = (PRIVATE/'native_input', '/native_input'); native_scores = (PRIVATE/'native_scores', '/native_scores')
    container('native-input', PRIVATE/'native_input', [session], ['/code/score_adapter.py', 'prepare'], frozen=True)
    container('native-score', PRIVATE/'native_scores', [native_input], ['/code/native.py', 'predict'], native=True, frozen=True, threads=1)
    container('collect', PRIVATE/'predictions', [session, native_input, native_scores], ['/code/score_adapter.py', 'collect'], frozen=True)
    container('references', PRIVATE/'references', [session, predictions,
        (REPO/'.private/protected_final_test_v1/predictions/lightweight_esm2_150m_linear__linear_lr3e-4', '/original_baseline'),
        (REPO/'.private/protected_final_test_v1/freeze/PREDICTION_FREEZE.json', '/baseline_freeze.json'),
        (REPO/'.private/model_optimization_followup_v1/predictions/candidate/esm2_150m__residual_wide__epoch04_ensemble3', '/original_optimized'),
        (REPO/'.private/model_optimization_followup_v1/freeze/PREDICTION_FREEZE.json', '/optimized_freeze.json')], ['/code/comparison.py', 'references'], frozen=True)
    container('freeze', PRIVATE/'freeze', [session, predictions, references], ['/code/comparison.py', 'freeze'], frozen=True)
    container('evaluate', PRIVATE/'evaluation', [session, predictions, references, freeze,
        (REPO/'.private/model_optimization_followup_v1/bundle/SCORER_FREEZE.json', '/historical_scorer_freeze.json'),
        (REPO/'.private/model_optimization_followup_v1/evaluation/FOLLOWUP_TEST_RESULTS.json', '/historical_results.json'),
        (REPO/'data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms', '/cipher.cms'),
        (REPO/'governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem', '/certificate.pem'),
        (REPO/'.private/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_private.pem', '/key.pem')],
        ['/code/comparison.py', 'evaluate'], frozen=True)
    container('publish', RESULTS, [(PRIVATE/'evaluation/RESULTS.json', '/aggregate/RESULTS.json')],
        ['/code/comparison.py', 'publish'], frozen=True)
    result = read(RESULTS/'RESULTS.json')
    assert result['historical_reference_points_reproduced'] and result['historical_component_draws_reproduced']
    assert result['temporary_decrypted_truth_removed'] and not list((PRIVATE/'evaluation').glob('truth-*'))
    assert sum(item['pairs_scored'] for item in result['coverage'].values()) == 3019012
    subprocess.run(['python3', '-B', str(ROOT/'scripts/scope_guard.py'), 'verify'], check=True)
    write(RUN/'RUN_COMPLETE.json', {'at_utc': now(), 'status': 'completed',
        'evaluation_pipeline_seconds': time.monotonic()-started,
        'hsp_seconds': read(RUN/'hsp/HSP_COMPLETE.json')['elapsed_seconds'],
        'result': rec(RESULTS/'RESULTS.json', ROOT), 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
        'node': socket.gethostname(), 'existing_repository_artifacts_not_modified': True})
    print({'completed': True, 'results': str(RESULTS)}, flush=True)


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'hsp', 'evaluate'])
    {'prepare': prepare, 'hsp': hsp, 'evaluate': evaluate}[parser.parse_args().phase]()
