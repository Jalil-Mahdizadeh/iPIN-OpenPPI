#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
QUAL_SIF="${PROJECT_ROOT}/containers/images/ipin-qual-arm64_0.1.0.sif"
LOCK_FILE="${PROJECT_ROOT}/containers/locks/ipin-data-arm64_0.1.2.requirements.lock"
WHEEL_DIR="${PROJECT_ROOT}/containers/cache/data-wheels"
PIP_CACHE="${PROJECT_ROOT}/containers/cache/pip-download"

[[ -f "${QUAL_SIF}" ]] || { echo "Missing qualification SIF: ${QUAL_SIF}" >&2; exit 1; }
[[ -f "${LOCK_FILE}" ]] || { echo "Missing requirements lock: ${LOCK_FILE}" >&2; exit 1; }
[[ "${WHEEL_DIR}" == "${PROJECT_ROOT}/containers/cache/data-wheels" ]] || exit 1
mkdir -p -- "${WHEEL_DIR}" "${PIP_CACHE}"

if find "${WHEEL_DIR}" -mindepth 1 -print -quit | grep -q .; then
    echo "Wheel directory is not empty; refusing to mix snapshots: ${WHEEL_DIR}" >&2
    exit 1
fi

apptainer exec --cleanenv \
    --env "PIP_CACHE_DIR=${PIP_CACHE}" \
    "${QUAL_SIF}" \
    python -m pip download \
        --only-binary=:all: \
        --require-hashes \
        --dest "${WHEEL_DIR}" \
        --requirement "${LOCK_FILE}"
