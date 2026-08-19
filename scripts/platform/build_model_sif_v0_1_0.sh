#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
DEFINITION="${PROJECT_ROOT}/containers/definitions/ipin-model-arm64_0.1.0.def"
QUAL_SIF="${PROJECT_ROOT}/containers/images/ipin-qual-arm64_0.1.0.sif"
OUTPUT_SIF="${PROJECT_ROOT}/containers/images/ipin-model-arm64_0.1.0.sif"
BUILD_CACHE="${PROJECT_ROOT}/containers/cache/apptainer-model-build"
BUILD_TMP="${PROJECT_ROOT}/containers/tmp/ipin-model-arm64_0.1.0"
WHEEL_DIR="${PROJECT_ROOT}/containers/cache/model-wheels"
EXPECTED_QUAL_SHA="9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5"

[[ "${OUTPUT_SIF}" == "${PROJECT_ROOT}/containers/images/ipin-model-arm64_0.1.0.sif" ]] || exit 1
[[ "${BUILD_CACHE}" == "${PROJECT_ROOT}/containers/cache/apptainer-model-build" ]] || exit 1
[[ "${BUILD_TMP}" == "${PROJECT_ROOT}/containers/tmp/ipin-model-arm64_0.1.0" ]] || exit 1
[[ -f "${DEFINITION}" ]] || { echo "Missing definition: ${DEFINITION}" >&2; exit 1; }
[[ -f "${QUAL_SIF}" ]] || { echo "Missing qualification SIF: ${QUAL_SIF}" >&2; exit 1; }
[[ ! -e "${OUTPUT_SIF}" ]] || { echo "Refusing to overwrite: ${OUTPUT_SIF}" >&2; exit 1; }
[[ "$(sha256sum "${QUAL_SIF}" | awk '{print $1}')" == "${EXPECTED_QUAL_SHA}" ]] || {
    echo "Qualification SIF checksum mismatch" >&2
    exit 1
}

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

mkdir -p -- "${BUILD_CACHE}" "${BUILD_TMP}" "$(dirname -- "${OUTPUT_SIF}")"
export APPTAINER_CACHEDIR="${BUILD_CACHE}"
export APPTAINER_TMPDIR="${BUILD_TMP}"

cd -- "${PROJECT_ROOT}"
apptainer build --fakeroot "${OUTPUT_SIF}" "${DEFINITION}"
sha256sum "${OUTPUT_SIF}"
