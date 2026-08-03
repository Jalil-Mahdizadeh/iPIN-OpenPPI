#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "${script_dir:?}/../lib/project_paths.sh"
ipin_prepare_runtime_dirs

image="${IPIN_PROJECT_ROOT}/containers/images/ipin-qual-arm64_0.1.0.sif"
checksum_file="${IPIN_PROJECT_ROOT}/containers/locks/ipin-qual-arm64_0.1.0.sif.sha256"
qualification_script="${IPIN_PROJECT_ROOT}/scripts/platform/qualify_torch_gpu.py"
comparison_script="${IPIN_PROJECT_ROOT}/scripts/platform/compare_qualification_runs.py"

for required_input in "${image}" "${checksum_file}" "${qualification_script}" "${comparison_script}"; do
    required_input="$(ipin_resolve_within_project "${required_input}")"
    if [[ ! -f "${required_input}" || -L "${required_input}" ]]; then
        echo "Required regular input is missing or is a symbolic link: ${required_input}" >&2
        exit 2
    fi
done

image_sha256="$(awk 'NR == 1 {print $1}' "${checksum_file}")"
if [[ ! "${image_sha256}" =~ ^[0-9a-f]{64}$ ]]; then
    echo "Invalid SIF checksum in ${checksum_file}" >&2
    exit 2
fi

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
    echo "This qualification must run inside a Slurm allocation." >&2
    exit 2
fi

run_timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
run_id="platform-single-gpu-${SLURM_JOB_ID}-${run_timestamp}"
run_dir="${IPIN_PROJECT_ROOT}/artifacts/runs/platform/${run_id}"
ipin_require_new_path "${run_dir}"
mkdir -p -- "${run_dir:?}"

export APPTAINER_CACHEDIR="${IPIN_APPTAINER_CACHE}"
export APPTAINER_TMPDIR="${IPIN_APPTAINER_TMP}"
export APPTAINERENV_CUBLAS_WORKSPACE_CONFIG=:4096:8
export APPTAINERENV_PYTHONHASHSEED=0
export APPTAINERENV_PYTHONNOUSERSITE=1
export APPTAINERENV_XDG_CACHE_HOME="${IPIN_RUNTIME_CACHE}/xdg"
export APPTAINERENV_HF_HOME="${IPIN_RUNTIME_CACHE}/huggingface"
export APPTAINERENV_TORCH_HOME="${IPIN_RUNTIME_CACHE}/torch"
export APPTAINERENV_TMPDIR="${IPIN_RUNTIME_TMP}/runtime"
export APPTAINERENV_SLURM_JOB_ID="${SLURM_JOB_ID}"

uname -a > "${run_dir}/host_uname.txt"
nvidia-smi -q > "${run_dir}/host_nvidia_smi.txt"
scontrol show job "${SLURM_JOB_ID}" > "${run_dir}/slurm_job.txt"
apptainer inspect --json "${image}" > "${run_dir}/container_inspect.json"
sha256sum "${image}" > "${run_dir}/container.sha256"

for repeat in 1 2; do
    output="${run_dir}/repeat_${repeat}.json"
    log="${run_dir}/repeat_${repeat}.log"
    apptainer exec --nv --cleanenv --no-home \
        --bind "${IPIN_PROJECT_ROOT}:${IPIN_PROJECT_ROOT}" \
        --pwd "${IPIN_PROJECT_ROOT}" \
        "${image}" \
        python "${qualification_script}" \
        --output "${output}" \
        --run-label "repeat_${repeat}" \
        --project-root "${IPIN_PROJECT_ROOT}" \
        --image-sha256 "${image_sha256}" 2>&1 | tee "${log}"
done

apptainer exec --cleanenv --no-home \
    --bind "${IPIN_PROJECT_ROOT}:${IPIN_PROJECT_ROOT}" \
    --pwd "${IPIN_PROJECT_ROOT}" \
    "${image}" \
    python "${comparison_script}" \
    --left "${run_dir}/repeat_1.json" \
    --right "${run_dir}/repeat_2.json" \
    --output "${run_dir}/comparison.json" \
    --tolerance 1.0e-6 2>&1 | tee "${run_dir}/comparison.log"

echo "Single-GPU qualification completed: ${run_dir}"

