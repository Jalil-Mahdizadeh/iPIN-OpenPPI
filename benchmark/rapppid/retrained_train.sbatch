#!/usr/bin/env bash
#SBATCH --job-name=rapppid-pu-20ep
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=3
#SBATCH --gpus=3
#SBATCH --gpus-per-node=3
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=96G
#SBATCH --time=2-00:00:00
#SBATCH --signal=USR1@180
#SBATCH --requeue
set -euo pipefail
umask 077
rapppid_root=${RAPPPID_BENCHMARK_ROOT:?Use submit_retrained.sh}
python3 -B "$rapppid_root/scripts/retrained_v1/host_guard.py" verify
for through_epoch in 4 8 12 16 20; do
  srun --ntasks=3 --gpus=3 --gpus-per-node=3 --gpus-per-task=1 --cpus-per-task=72 \
    --gpu-bind=single:1 --cpu-bind=none --kill-on-bad-exit=1 \
    --output="$rapppid_root/logs/retrained-train-%j-epoch$through_epoch-rank-%t.log" \
    bash "$rapppid_root/run_retrained_worker.sh" "$through_epoch"
  srun --ntasks=1 --gpus=1 --gpus-per-node=1 --gpus-per-task=1 --cpus-per-task=72 \
    --gpu-bind=single:1 --cpu-bind=none --kill-on-bad-exit=1 \
    --output="$rapppid_root/logs/retrained-development-%j-epoch$through_epoch.log" \
    bash "$rapppid_root/report_retrained_development.sh" "$through_epoch"
done
echo 'All20epochs and five C3-development reports complete. Awaiting user epoch choice; no test evaluation scheduled.'
