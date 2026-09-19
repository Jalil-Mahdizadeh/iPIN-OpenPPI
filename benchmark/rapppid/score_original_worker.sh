#!/usr/bin/env bash
set -euo pipefail
umask 077
rapppid_root=${RAPPPID_BENCHMARK_ROOT:?Set by run_original.py}
bench_root=$(dirname -- "$rapppid_root")
output="$rapppid_root/private/original-v1/shards/rank-00"
mkdir -p "$output/tmp"
mapfile -t rapppid_gpu_uuids < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
[[ ${#rapppid_gpu_uuids[@]} -eq 1 ]]
printf 'GPU_BINDING rank=0 uuid=%s CUDA_VISIBLE_DEVICES=%s\n' "${rapppid_gpu_uuids[0]}" "${CUDA_VISIBLE_DEVICES:-0}"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/rapppid-v1"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$rapppid_root/runs/original-v1/scorer_bundle:/bundle:ro" \
  --bind "$rapppid_root/runs/original-v1/scorer_bundle/code:/code:ro" \
  --bind "$rapppid_root/private/original-v1/session:/session:ro" \
  --bind "$output:/output:rw" --pwd /output \
  "$bench_root/containers/images/rapppid-native-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output/tmp \
  python /code/gpu_guard.py /code/score_shard.py work --rank 0 --workers 1
