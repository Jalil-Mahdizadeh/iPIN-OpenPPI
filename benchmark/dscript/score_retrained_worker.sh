#!/usr/bin/env bash
set -euo pipefail
umask 077
dscript_root=${DSCRIPT_BENCHMARK_ROOT:?Use submit_retrained.sh}
bench_root=$(dirname -- "$dscript_root")
rank=${SLURM_PROCID:?Must run with srun}
[[ "$rank" =~ ^[0-3]$ ]]
printf -v rank_name 'rank-%02d' "$rank"
output="$dscript_root/private/retrained-v1/shards/$rank_name"
mkdir -p "$output/tmp"
mapfile -t dscript_gpu_uuids < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
[[ ${#dscript_gpu_uuids[@]} -eq 1 ]]
printf 'GPU_BINDING rank=%s uuid=%s visible=%s\n' "$rank" "${dscript_gpu_uuids[0]}" "${CUDA_VISIBLE_DEVICES:?}"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/dscript-v1"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$dscript_root/runs/retrained-v1/scorer_bundle:/bundle:ro" \
  --bind "$dscript_root/runs/retrained-v1/scorer_bundle/code:/code:ro" \
  --bind "$dscript_root/private/retrained-v1/session:/session:ro" \
  --bind "$output:/output:rw" --pwd /output \
  "$bench_root/containers/images/dscript-native-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES" \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output/tmp \
  python /code/gpu_guard.py /code/score_shard.py work --rank "$rank" --workers 4
