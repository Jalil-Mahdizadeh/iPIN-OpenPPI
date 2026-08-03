#!/usr/bin/env bash
#SBATCH --job-name=ipin-qual-1gpu
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gpus=1
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=slurm/logs/%x-%j.out
#SBATCH --error=slurm/logs/%x-%j.err

set -euo pipefail
project_root="$(cd -- "${SLURM_SUBMIT_DIR:?}" && pwd -P)"
expected_manifest="${project_root}/governance/START_MANIFEST_v1.yaml"
if [[ ! -f "${expected_manifest}" ]]; then
    echo "Submit this job from the iPIN-OpenPPI project root." >&2
    exit 2
fi

"${project_root}/scripts/platform/run_single_gpu_qualification.sh"

