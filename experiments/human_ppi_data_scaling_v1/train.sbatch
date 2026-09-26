#!/usr/bin/env bash
#SBATCH --job-name=human-ppi-scale
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=64G
#SBATCH --time=20:00:00
set -euo pipefail
umask 077
unset SLURM_CPU_BIND SLURM_CPU_BIND_LIST SLURM_CPU_BIND_TYPE SLURM_CPU_BIND_VERBOSE
study_root=${HUMAN_PPI_STUDY_ROOT:?Must be submitted with scripts/submit.py}
read -r study_budget study_seed < <(python3 - "$study_root/data/PROTOCOL.json" "$SLURM_ARRAY_TASK_ID" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); tasks=[(b,s) for b in p['positive_budgets'] for s in p['seeds']]
print(*tasks[int(sys.argv[2])])
PY
)
exec srun --cpu-bind=none --nodes=1 --ntasks=1 --gpus=1 --gpus-per-task=1 --cpus-per-task=18 \
  bash "$study_root/run_gpu.sh" train --budget "$study_budget" --seed "$study_seed" --resume
