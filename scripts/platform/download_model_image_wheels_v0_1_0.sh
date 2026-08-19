#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
QUAL_SIF="${PROJECT_ROOT}/containers/images/ipin-qual-arm64_0.1.0.sif"
LOCK_FILE="${PROJECT_ROOT}/containers/locks/ipin-model-arm64_0.1.0.requirements.lock"
WHEEL_DIR="${PROJECT_ROOT}/containers/cache/model-wheels"
PIP_CACHE="${PROJECT_ROOT}/containers/cache/pip-model-download"
EXPECTED_QUAL_SHA="9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5"

[[ -f "${QUAL_SIF}" ]] || { echo "Missing qualification SIF: ${QUAL_SIF}" >&2; exit 1; }
[[ -f "${LOCK_FILE}" ]] || { echo "Missing requirements lock: ${LOCK_FILE}" >&2; exit 1; }
[[ "$(sha256sum "${QUAL_SIF}" | awk '{print $1}')" == "${EXPECTED_QUAL_SHA}" ]] || {
    echo "Qualification SIF checksum mismatch" >&2
    exit 1
}
[[ "${WHEEL_DIR}" == "${PROJECT_ROOT}/containers/cache/model-wheels" ]] || exit 1
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
        --no-deps \
        --dest "${WHEEL_DIR}" \
        transformers==4.55.2 \
        huggingface-hub==0.34.4 \
        tokenizers==0.21.4

declare -A EXPECTED_WHEELS=(
    [huggingface_hub-0.34.4-py3-none-any.whl]=9b365d781739c93ff90c359844221beef048403f1bc1f1c123c191257c3c890a
    [tokenizers-0.21.4-cp39-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl]=39b376f5a1aee67b4d29032ee85511bbd1b99007ec735f7f35c8a2eb104eade5
    [transformers-4.55.2-py3-none-any.whl]=097e3c2e2c0c9681db3da9d748d8f9d6a724c644514673d0030e8c5a1109f1f1
)
for wheel in "${!EXPECTED_WHEELS[@]}"; do
    path="${WHEEL_DIR}/${wheel}"
    [[ -f "${path}" && ! -L "${path}" ]] || { echo "Missing regular wheel: ${path}" >&2; exit 1; }
    [[ "$(sha256sum "${path}" | awk '{print $1}')" == "${EXPECTED_WHEELS[${wheel}]}" ]] || {
        echo "Wheel checksum mismatch: ${wheel}" >&2
        exit 1
    }
done
sha256sum "${WHEEL_DIR}"/*
