#!/usr/bin/env bash
set -euo pipefail
umask 077
dscript_root=${DSCRIPT_BENCHMARK_ROOT:?Use submit_retrained.sh}
bench_root=$(dirname -- "$dscript_root")
case ${SLURM_PROCID:?Must run through srun} in
  0) dscript_seed=20260803 ;;
  1) dscript_seed=20260817 ;;
  2) dscript_seed=20260831 ;;
  *) exit 1 ;;
esac
output="$dscript_root/runs/retrained-v1/training/seed_$dscript_seed"
mkdir -p "$output/tmp"
mapfile -t dscript_gpu_uuids < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
[[ ${#dscript_gpu_uuids[@]} -eq 1 ]]
printf 'GPU_BINDING rank=%s seed=%s uuid=%s visible=%s\n' \
  "$SLURM_PROCID" "$dscript_seed" "${dscript_gpu_uuids[0]}" "${CUDA_VISIBLE_DEVICES:?}"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/dscript-v1"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$dscript_root/runs/retrained-v1/code:/code:ro" \
  --bind "$dscript_root/runs/retrained-v1/data:/data:ro" \
  --bind "$dscript_root/runs/retrained-v1/residue_cache:/cache:ro" \
  --bind "$dscript_root/runs/retrained-v1/TRAINING_FREEZE.json:/protocol.json:ro" \
  --bind "$output:/output:rw" --pwd /output \
  "$bench_root/containers/images/dscript-native-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES" SLURM_JOB_ID="$SLURM_JOB_ID" \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output/tmp \
  python /code/gpu_guard.py /code/train.py --seed "$dscript_seed" --through-epoch "$1"
