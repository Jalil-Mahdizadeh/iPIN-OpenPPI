#!/usr/bin/env bash
set -euo pipefail
umask 077
rapppid_root=${RAPPPID_BENCHMARK_ROOT:?Use submit_retrained.sh}
bench_root=$(dirname -- "$rapppid_root")
case ${SLURM_PROCID:?Must launch through srun} in
  0) rapppid_seed=20260803 ;;
  1) rapppid_seed=20260817 ;;
  2) rapppid_seed=20260831 ;;
  *) exit 1 ;;
esac
output="$rapppid_root/runs/retrained-v1/training/seed_$rapppid_seed"
mkdir -p "$output/tmp"
mapfile -t rapppid_gpu_uuids < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
[[ ${#rapppid_gpu_uuids[@]} -eq 1 ]]
printf 'GPU_BINDING rank=%s seed=%s uuid=%s visible=%s\n' \
  "$SLURM_PROCID" "$rapppid_seed" "${rapppid_gpu_uuids[0]}" "${CUDA_VISIBLE_DEVICES:?}"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/rapppid-v1"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$rapppid_root/runs/retrained-v1/code:/code:ro" \
  --bind "$rapppid_root/runs/retrained-v1/data:/data:ro" \
  --bind "$rapppid_root/runs/retrained-v1/TRAINING_FREEZE.json:/protocol.json:ro" \
  --bind "$output:/output:rw" --pwd /output \
  "$bench_root/containers/images/rapppid-native-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES" SLURM_JOB_ID="$SLURM_JOB_ID" \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output/tmp \
  python /code/gpu_guard.py /code/train_worker.py --seed "$rapppid_seed" --through-epoch "$1"
