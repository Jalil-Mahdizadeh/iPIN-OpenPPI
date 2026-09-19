#!/usr/bin/env python3
"""Single-use, benchmark-local evaluation; never submit or restart training.

The host freezes source/checkpoint choices, then runs isolated container phases
with candidate data and truth mounted separately. All existing inputs are RO.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent.parent
RUN = ROOT / 'runs/recovery-test-v1'
PRIVATE = ROOT / 'private/recovery-test-v1'
RESULTS = ROOT / 'results/retrained-v1/recovery-test-v1'
LOGS = ROOT / 'logs/recovery-test-v1'
SIF = ROOT.parent / 'containers/images/rapppid-native-arm64-v1.sif'
PREVIOUS = ROOT / 'results/retrained-v1/recovery-c3-dev-2578434-v2'
SIF_SHA = 'e853a89768c5351927f90fd0ccfb2ad899a15a6fc239a9014726af0c34442d48'
PROTOCOL_SHA = '4d7a912c278faa79477e8e65869963d4d984ec3059ff482ac4deafe04b3ee16e'
CHECKPOINTS = {
    20260803: ('f332c9fbd42e9d3146ca7c54743acca66ab0fa5e6d583e89aca2ae41e4135c30', 1502840),
    20260817: ('2ea98f070c5f5f712c6c4dc31c2a8f7f2389f0329a5a73a4548bdde487a49060', 1577920),
    20260831: ('ac0facd77f4bbb70fe25f144556d90cdf28e4151b324c41aae6a5c0efd0a4ef8', 1556480),
}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8 << 20), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')


def record(path, root=RUN):
    path = Path(path)
    return {'path': str(path.relative_to(root)), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def copy(source, target):
    with Path(source).open('rb') as reader, Path(target).open('xb') as writer:
        shutil.copyfileobj(reader, writer)
    assert sha(source) == sha(target)


def prepare():
    assert os.environ.get('SLURM_JOB_ID'), 'An allocated GPU is required'
    assert sha(SIF) == SIF_SHA
    protocol_path = ROOT / 'runs/retrained-v1/TRAINING_FREEZE.json'
    assert sha(protocol_path) == PROTOCOL_SHA
    protocol = read(protocol_path)
    latest = read(PREVIOUS / 'RESULTS.json')
    previous_freeze = read(PREVIOUS / 'EVALUATION_FREEZE.json')
    assert latest['passed'] and latest['freeze_sha256'] == sha(PREVIOUS / 'EVALUATION_FREEZE.json')
    assert latest['training_protocol_sha256'] == PROTOCOL_SHA
    assert latest['training_checkpoints_unchanged'] and not latest['training_resumed']
    assert not latest['test_pairs_read'] and not latest['test_truth_read']
    RUN.mkdir(); (RUN / 'code').mkdir(); (RUN / 'checkpoints').mkdir()
    PRIVATE.mkdir(mode=0o700); LOGS.mkdir(); RESULTS.mkdir()
    members = []
    for seed, (digest, position) in CHECKPOINTS.items():
        old = next(m for m in latest['members'] if m['seed'] == seed)
        frozen = next(m for m in previous_freeze['members'] if m['seed'] == seed)
        source = PREVIOUS / frozen['checkpoint']['path']
        training = ROOT / f'runs/retrained-v1/training/seed_{seed}/resume.pt'
        assert sha(source) == sha(training) == digest == old['checkpoint']['sha256']
        assert old['epoch_in_progress'] == 8 and old['comparisons_in_current_epoch'] == position
        target = RUN / 'checkpoints' / f'seed_{seed}.pt'; copy(source, target)
        members.append({'seed': seed, 'source_path': str(source.relative_to(ROOT)),
            'training_source_path': str(training.relative_to(ROOT)), 'checkpoint': record(target),
            'completed_epochs': 7, 'epoch_in_progress': 8, 'comparisons_in_current_epoch': position,
            'current_epoch_fraction': position / 2000000, 'total_optimizer_updates': 350000 + position // 40,
            'learned_state_sha256': old['learned_state_sha256']})
    for path in sorted(Path(__file__).parent.glob('*.py')):
        copy(path, RUN / 'code' / path.name)
    # The actual native helper and historical metric implementation are copied
    # without changes; only test orchestration/common panel constants are new.
    assert sha(RUN / 'code/model.py') == sha(ROOT / 'runs/retrained-v1/code/model.py')
    assert sha(RUN / 'code/benchmark_metrics.py') == sha(ROOT / 'scripts/benchmark_metrics.py')
    copy(protocol_path, RUN / 'TRAINING_FREEZE.json')
    copy(PREVIOUS / 'RESULTS.json', RUN / 'LATEST_DEVELOPMENT_RESULTS.json')
    copy(PREVIOUS / 'EVALUATION_FREEZE.json', RUN / 'LATEST_DEVELOPMENT_FREEZE.json')
    files = [record(p) for p in sorted(RUN.rglob('*')) if p.is_file()]
    selection = {'at_utc': now(), 'execution_id': 'rapppid_recovery_test_v1',
        'authorization': 'User declines restarting training and requests the latest saved checkpoints on C1/C2/C3 test',
        'selection_basis': 'Exactly the three latest saved states evaluated in recovery-c3-dev-2578434-v2; no further search',
        'members': members, 'training_protocol_sha256': PROTOCOL_SHA, 'sif_sha256': SIF_SHA,
        'tokenizer_sha256': protocol['tokenizer_sha256'], 'latest_development_results_sha256': sha(PREVIOUS / 'RESULTS.json'),
        'original_results_sha256': sha(ROOT / 'results/original-v1/RESULTS.json'),
        'original_predictions_manifest_sha256': sha(ROOT / 'private/original-v1/predictions/PREDICTIONS.json'),
        'files': files, 'code_files': [f for f in files if f['path'].startswith('code/')],
        'ensemble': 'FP64 arithmetic mean of all three native pre-sigmoid logits',
        'primary_cell': 'C3_test', 'secondary_cells': ['C1_test', 'C2_test'],
        'primary_comparison': 'Recovery ensemble versus optimized iPIN; original RAPPPID and baseline iPIN are additional references',
        'inference': 'Unchanged native singleton endpoint/head policy; deterministic TRAIN-fitted tokenizer; first1500 residues; FP32/noAMP/noTF32',
        'metric': 'Historical design-weighted P-versus-U concordance, exact half ties, 2000 paired two-endpoint component bootstrap draws',
        'native_logit_tolerance': 1e-4, 'full_panel_independent_metric_tolerance': 1e-9,
        'test_evaluation_authorized': True, 'test_pairs_read': False, 'test_truth_read': False,
        'test_previously_examined': True, 'selection_after_additional_development_look': True,
        'training_resumed': False, 'training_repair_applied': False, 'completed_epoch8_claimed': False,
        'planned20epochs_completed': False, 'new_slurm_jobs_submitted': False,
        'slurm_job_id': os.environ['SLURM_JOB_ID'], 'node': socket.gethostname()}
    write(RUN / 'SELECTION.json', selection)
    print({'selected': True, 'three_mid_epoch8_checkpoints': True, 'training_resumed': False}, flush=True)


def container(phase, output, binds, entry, *, qualified=True):
    output = Path(output)
    assert ROOT in output.parents and not output.is_symlink()
    if not output.exists():
        output.mkdir()
    bundle = RUN / 'scorer_bundle'
    code = bundle / 'code' if qualified else RUN / 'code'
    command = ['apptainer', 'exec', '--nv', '--cleanenv', '--containall', '--no-home',
               '--no-mount', 'bind-paths,home,cwd,hostfs', '--pwd', '/output',
               '--bind', f'{code}:/code:ro', '--bind', f'{output}:/output:rw']
    if qualified:
        command += ['--bind', f'{bundle}:/bundle:ro']
    for source, target in binds:
        assert Path(source).exists(), source
        command += ['--bind', f'{source}:{target}:ro']
    command += [str(SIF), 'env', 'UCX_VFS_ENABLE=n', 'PYTHONUNBUFFERED=1', 'PYTHONDONTWRITEBYTECODE=1',
                'NVIDIA_TF32_OVERRIDE=0', 'OMP_NUM_THREADS=8', 'OPENBLAS_NUM_THREADS=1',
                f'CUDA_VISIBLE_DEVICES={os.environ.get("CUDA_VISIBLE_DEVICES", "0")}',
                f'SLURM_JOB_ID={os.environ["SLURM_JOB_ID"]}', 'XDG_CACHE_HOME=/output/.cache',
                'MPLCONFIGDIR=/output/.cache/matplotlib', 'TMPDIR=/output',
                'python', '/code/gpu_guard.py', *entry]
    env = dict(os.environ)
    for key in ('APPTAINER_BIND', 'APPTAINER_BINDPATH', 'SINGULARITY_BIND', 'SINGULARITY_BINDPATH'):
        env.pop(key, None)
    env['APPTAINER_CACHEDIR'] = str(ROOT.parent / 'containers/cache/apptainer')
    env['APPTAINER_TMPDIR'] = str(ROOT.parent / 'containers/tmp/rapppid-v1')
    print({'phase': phase, 'started_at_utc': now()}, flush=True)
    with (LOGS / f'{phase}.log').open('x') as log:
        subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    print({'phase': phase, 'completed_at_utc': now()}, flush=True)


def main():
    os.umask(0o077); started = time.monotonic()
    prepare()
    data = ROOT / 'runs/retrained-v1/data'
    container('qualify-freeze', RUN, [(data / name, f'/data/{name}') for name in ('sequences.json', 'spm.model', 'training.npz')],
              ['/code/qualify_freeze.py'], qualified=False)
    container('open', PRIVATE / 'session', [(REPO / '.private/model_optimization_followup_v1/session', '/previous_session')],
              ['/code/comparison.py', 'open'])
    session = (PRIVATE / 'session', '/session'); predictions = (PRIVATE / 'predictions', '/predictions')
    references = (PRIVATE / 'references', '/references'); freeze = (PRIVATE / 'freeze', '/freeze')
    container('score', PRIVATE / 'predictions', [session], ['/code/score.py'])
    container('references', PRIVATE / 'references', [session, predictions,
        (REPO / '.private/protected_final_test_v1/predictions/lightweight_esm2_150m_linear__linear_lr3e-4', '/original_baseline'),
        (REPO / '.private/protected_final_test_v1/freeze/PREDICTION_FREEZE.json', '/baseline_freeze.json'),
        (REPO / '.private/model_optimization_followup_v1/predictions/candidate/esm2_150m__residual_wide__epoch04_ensemble3', '/original_optimized'),
        (REPO / '.private/model_optimization_followup_v1/freeze/PREDICTION_FREEZE.json', '/optimized_freeze.json'),
        (ROOT / 'private/original-v1/predictions', '/original_rapppid'),
        (ROOT / 'private/original-v1/predictions/PREDICTIONS.json', '/rapppid_predictions.json')], ['/code/comparison.py', 'references'])
    container('freeze', PRIVATE / 'freeze', [session, predictions, references], ['/code/comparison.py', 'freeze'])
    container('evaluate', PRIVATE / 'evaluation', [session, predictions, references, freeze,
        (REPO / '.private/model_optimization_followup_v1/bundle/SCORER_FREEZE.json', '/historical_scorer_freeze.json'),
        (REPO / '.private/model_optimization_followup_v1/evaluation/FOLLOWUP_TEST_RESULTS.json', '/historical_results.json'),
        (ROOT / 'results/original-v1/RESULTS.json', '/original_results.json'),
        (REPO / 'data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms', '/cipher.cms'),
        (REPO / 'governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem', '/certificate.pem'),
        (REPO / '.private/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_private.pem', '/key.pem')],
        ['/code/comparison.py', 'evaluate'])
    container('publish', RESULTS, [(PRIVATE / 'evaluation/RESULTS.json', '/aggregate/RESULTS.json')], ['/code/comparison.py', 'publish'])
    result = read(RESULTS / 'RESULTS.json')
    assert result['historical_reference_points_reproduced'] and result['original_reference_points_reproduced']
    assert result['historical_component_draws_reproduced'] and result['temporary_decrypted_truth_removed']
    assert sum(x['pairs_scored'] for x in result['coverage'].values()) == 3019012
    assert not list((PRIVATE / 'evaluation').glob('truth-*'))
    for member in read(RUN / 'SELECTION.json')['members']:
        for key in ('source_path', 'training_source_path'):
            assert sha(ROOT / member[key]) == member['checkpoint']['sha256']
    subprocess.run(['python3', '-B', str(ROOT / 'scripts/retrained_v1/host_guard.py'), 'verify'], check=True)
    write(RUN / 'RUN_COMPLETE.json', {'at_utc': now(), 'status': 'completed', 'elapsed_seconds': time.monotonic()-started,
        'result': record(RESULTS / 'RESULTS.json', ROOT), 'selection_sha256': sha(RUN / 'SELECTION.json'),
        'training_resumed': False, 'source_checkpoints_unchanged': True,
        'new_jobs_submitted': False, 'slurm_job_id': os.environ['SLURM_JOB_ID'], 'node': socket.gethostname()})
    print({'completed': True, 'elapsed_seconds': time.monotonic()-started, 'result': str(RESULTS)}, flush=True)


if __name__ == '__main__':
    main()
