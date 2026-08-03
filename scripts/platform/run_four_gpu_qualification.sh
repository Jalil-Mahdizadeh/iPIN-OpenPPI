#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "${script_dir:?}/../lib/project_paths.sh"
ipin_prepare_runtime_dirs

image="${IPIN_PROJECT_ROOT}/containers/images/ipin-qual-arm64_0.1.0.sif"
checksum_file="${IPIN_PROJECT_ROOT}/containers/locks/ipin-qual-arm64_0.1.0.sif.sha256"
fixture_script="${IPIN_PROJECT_ROOT}/scripts/platform/distributed_scaling_fixture.py"
comparison_script="${IPIN_PROJECT_ROOT}/scripts/platform/compare_scaling_runs.py"

for required_input in "${image}" "${checksum_file}" "${fixture_script}" "${comparison_script}"; do
    required_input="$(ipin_resolve_within_project "${required_input}")"
    if [[ ! -f "${required_input}" || -L "${required_input}" ]]; then
        echo "Required regular input is missing or is a symbolic link: ${required_input}" >&2
        exit 2
    fi
done

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
    echo "This qualification must run inside a Slurm allocation." >&2
    exit 2
fi
if [[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]; then
    echo "CUDA_VISIBLE_DEVICES is missing from the Slurm allocation." >&2
    exit 2
fi
IFS=',' read -r -a visible_devices <<< "${CUDA_VISIBLE_DEVICES}"
if [[ "${#visible_devices[@]}" -ne 4 ]]; then
    echo "Expected exactly four allocated GPUs, observed: ${CUDA_VISIBLE_DEVICES}" >&2
    exit 2
fi

image_sha256="$(awk 'NR == 1 {print $1}' "${checksum_file}")"
if [[ ! "${image_sha256}" =~ ^[0-9a-f]{64}$ ]]; then
    echo "Invalid SIF checksum in ${checksum_file}" >&2
    exit 2
fi

run_timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
run_id="platform-four-gpu-${SLURM_JOB_ID}-${run_timestamp}"
run_dir="${IPIN_PROJECT_ROOT}/artifacts/runs/platform/${run_id}"
ipin_require_new_path "${run_dir}"
mkdir -p -- "${run_dir:?}"

export APPTAINER_CACHEDIR="${IPIN_APPTAINER_CACHE}"
export APPTAINER_TMPDIR="${IPIN_APPTAINER_TMP}"
export APPTAINERENV_PYTHONHASHSEED=0
export APPTAINERENV_PYTHONNOUSERSITE=1
export APPTAINERENV_XDG_CACHE_HOME="${IPIN_RUNTIME_CACHE}/xdg"
export APPTAINERENV_HF_HOME="${IPIN_RUNTIME_CACHE}/huggingface"
export APPTAINERENV_TORCH_HOME="${IPIN_RUNTIME_CACHE}/torch"
export APPTAINERENV_TMPDIR="${IPIN_RUNTIME_TMP}/runtime"
export APPTAINERENV_SLURM_JOB_ID="${SLURM_JOB_ID}"
export APPTAINERENV_OMP_NUM_THREADS=8

uname -a > "${run_dir}/host_uname.txt"
nvidia-smi -q > "${run_dir}/host_nvidia_smi.txt"
scontrol show job "${SLURM_JOB_ID}" > "${run_dir}/slurm_job.txt"
apptainer inspect --json "${image}" > "${run_dir}/container_inspect.json"
sha256sum "${image}" > "${run_dir}/container.sha256"

export APPTAINERENV_CUDA_VISIBLE_DEVICES="${visible_devices[0]}"
apptainer exec --nv --cleanenv --no-home \
    --bind "${IPIN_PROJECT_ROOT}:${IPIN_PROJECT_ROOT}" \
    --pwd "${IPIN_PROJECT_ROOT}" \
    "${image}" \
    torchrun --standalone --nproc-per-node=1 "${fixture_script}" \
    --output "${run_dir}/single_gpu.json" \
    --project-root "${IPIN_PROJECT_ROOT}" \
    --run-label single_gpu_baseline \
    --image-sha256 "${image_sha256}" 2>&1 | tee "${run_dir}/single_gpu.log"

export APPTAINERENV_CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}"
apptainer exec --nv --cleanenv --no-home \
    --bind "${IPIN_PROJECT_ROOT}:${IPIN_PROJECT_ROOT}" \
    --pwd "${IPIN_PROJECT_ROOT}" \
    "${image}" \
    torchrun --standalone --nproc-per-node=4 "${fixture_script}" \
    --output "${run_dir}/four_gpu.json" \
    --project-root "${IPIN_PROJECT_ROOT}" \
    --run-label four_gpu_ddp \
    --image-sha256 "${image_sha256}" 2>&1 | tee "${run_dir}/four_gpu.log"

apptainer exec --cleanenv --no-home \
    --bind "${IPIN_PROJECT_ROOT}:${IPIN_PROJECT_ROOT}" \
    --pwd "${IPIN_PROJECT_ROOT}" \
    "${image}" \
    python "${comparison_script}" \
    --single "${run_dir}/single_gpu.json" \
    --four "${run_dir}/four_gpu.json" \
    --output "${run_dir}/scaling_comparison.json" \
    --minimum-efficiency 0.70 2>&1 | tee "${run_dir}/scaling_comparison.log"

echo "Four-GPU qualification completed: ${run_dir}"

