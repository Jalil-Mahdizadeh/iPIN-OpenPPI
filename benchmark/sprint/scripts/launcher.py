"""Host-side, allowlisted container launcher; no inherited repository mounts."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent.parent
RUN = ROOT/'runs/original-v1'
PRIVATE = ROOT/'private/original-v1'
RESULTS = ROOT/'results/original-v1'
LOGS = ROOT/'logs/original-v1'
SIF = ROOT.parent/'containers/images/sprint-native-arm64-v1.sif'
METRIC_SIF = REPO/'containers/images/ipin-model-arm64_0.1.0.sif'


def container(phase, output, binds, entry, *, native=False, frozen=False, threads=8):
    output = Path(output)
    assert ROOT in output.parents and not output.is_symlink()
    output.mkdir(parents=True, exist_ok=True); LOGS.mkdir(parents=True, exist_ok=True)
    bundle = RUN/'scorer_bundle'
    code = bundle/'code' if frozen else (RUN/'code' if (RUN/'INITIAL_FREEZE.json').exists() else ROOT/'scripts')
    command = ['apptainer', 'exec'] + ([] if native else ['--nv']) + [
        '--cleanenv', '--containall', '--no-home', '--no-mount', 'bind-paths,home,cwd,hostfs',
        '--pwd', '/output', '--bind', f'{code}:/code:ro', '--bind', f'{output}:/output:rw']
    if frozen: command += ['--bind', f'{bundle}:/bundle:ro']
    for source, target in binds:
        assert Path(source).exists(), source
        command += ['--bind', f'{source}:{target}:ro']
    command += [str(SIF if native else METRIC_SIF), 'env', 'PYTHONDONTWRITEBYTECODE=1', 'PYTHONUNBUFFERED=1',
        'UCX_VFS_ENABLE=n', 'NVIDIA_TF32_OVERRIDE=0', f'OMP_NUM_THREADS={threads}', 'OPENBLAS_NUM_THREADS=1',
        f'CUDA_VISIBLE_DEVICES={os.environ.get("CUDA_VISIBLE_DEVICES", "0")}',
        'XDG_CACHE_HOME=/output/.cache', 'MPLCONFIGDIR=/output/.cache/matplotlib', 'TMPDIR=/output',
        'python3' if native else 'python', '/code/gpu_guard.py', *entry]
    env = dict(os.environ)
    for key in ('APPTAINER_BIND', 'APPTAINER_BINDPATH', 'SINGULARITY_BIND', 'SINGULARITY_BINDPATH'):
        env.pop(key, None)
    env['APPTAINER_CACHEDIR'] = str(ROOT.parent/'containers/cache/apptainer')
    env['APPTAINER_TMPDIR'] = str(ROOT.parent/'containers/tmp/sprint-v1')
    print({'phase': phase, 'started_at_utc': datetime.now(timezone.utc).isoformat()}, flush=True)
    with (LOGS/(phase+'.log')).open('x') as log:
        subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    print({'phase': phase, 'completed_at_utc': datetime.now(timezone.utc).isoformat()}, flush=True)


if __name__ == '__main__':
    import sys
    mode = sys.argv[1]
    if mode == 'qualify':
        container('native-qualification', RUN/'qualification/native', [], ['/code/native.py', 'qualify'], native=True)
    elif mode == 'data':
        data = ROOT.parent/'rapppid/runs/retrained-v1/data'
        container('prepare-data', RUN/'data', [(data/name, '/data/'+name) for name in ('sequences.json', 'training.npz')], ['/code/prepare_data.py'])
    elif mode == 'pilot':
        container('pilot-hsp', RUN/'pilot', [(RUN/'data/pilot.fasta', '/data/pilot.fasta')], ['/code/native.py', 'pilot'], native=True)
    elif mode == 'metric':
        container('metric-qualification', RUN/'qualification/metric', [], ['/code/comparison.py', 'qualify'])
    else: raise ValueError(mode)
