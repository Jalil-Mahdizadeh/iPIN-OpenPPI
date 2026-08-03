#!/usr/bin/env bash
set -euo pipefail

ipin_lib_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
IPIN_PROJECT_ROOT="$(cd -- "${ipin_lib_dir:?}/../.." && pwd -P)"

if [[ ! -f "${IPIN_PROJECT_ROOT:?}/governance/START_MANIFEST_v1.yaml" ]]; then
    echo "Project-root validation failed: start manifest is missing." >&2
    exit 2
fi

export IPIN_PROJECT_ROOT
export IPIN_APPTAINER_CACHE="${IPIN_PROJECT_ROOT}/containers/cache"
export IPIN_APPTAINER_TMP="${IPIN_PROJECT_ROOT}/containers/tmp"
export IPIN_RUNTIME_CACHE="${IPIN_PROJECT_ROOT}/artifacts/cache"
export IPIN_RUNTIME_TMP="${IPIN_PROJECT_ROOT}/artifacts/tmp"

ipin_resolve_within_project() {
    local candidate="${1:?path argument required}"
    local resolved
    resolved="$(realpath -m -- "${candidate}")"
    if [[ "${resolved}" != "${IPIN_PROJECT_ROOT}" && "${resolved}" != "${IPIN_PROJECT_ROOT}/"* ]]; then
        echo "Refusing path outside project root: ${resolved}" >&2
        return 2
    fi
    printf '%s\n' "${resolved}"
}

ipin_require_new_path() {
    local resolved
    resolved="$(ipin_resolve_within_project "${1:?path argument required}")"
    if [[ -e "${resolved}" || -L "${resolved}" ]]; then
        echo "Refusing to overwrite existing path: ${resolved}" >&2
        return 2
    fi
}

ipin_prepare_runtime_dirs() {
    local relative_dir
    local resolved_dir
    local runtime_dirs=(
        containers/cache
        containers/tmp
        containers/images
        containers/manifests
        artifacts/cache/xdg
        artifacts/cache/huggingface
        artifacts/cache/torch
        artifacts/tmp/runtime
        artifacts/runs/platform
        artifacts/reports/platform
        slurm/logs
    )
    for relative_dir in "${runtime_dirs[@]}"; do
        resolved_dir="$(ipin_resolve_within_project "${IPIN_PROJECT_ROOT}/${relative_dir}")"
        mkdir -p -- "${resolved_dir:?}"
    done
}

