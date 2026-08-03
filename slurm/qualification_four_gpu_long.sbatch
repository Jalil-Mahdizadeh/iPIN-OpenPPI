#!/usr/bin/env bash
#SBATCH --job-name=ipin-qual-4gpu-long
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
#SBATCH --gpus=4
#SBATCH --mem=400G
#SBATCH --time=00:15:00
#SBATCH --exclusive
#SBATCH --output=slurm/logs/%x-%j.out
#SBATCH --error=slurm/logs/%x-%j.err

set -euo pipefail
project_root="$(cd -- "${SLURM_SUBMIT_DIR:?}" && pwd -P)"
if [[ ! -f "${project_root}/governance/START_MANIFEST_v1.yaml" ]]; then
    echo "Submit this job from the iPIN-OpenPPI project root." >&2
    exit 2
fi

"${project_root}/scripts/platform/run_four_gpu_qualification_long.sh"
