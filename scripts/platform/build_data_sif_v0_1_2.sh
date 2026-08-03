#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
DEFINITION="${PROJECT_ROOT}/containers/definitions/ipin-data-arm64_0.1.2.def"
QUAL_SIF="${PROJECT_ROOT}/containers/images/ipin-qual-arm64_0.1.0.sif"
OUTPUT_SIF="${PROJECT_ROOT}/containers/images/ipin-data-arm64_0.1.2.sif"
BUILD_CACHE="${PROJECT_ROOT}/containers/cache/apptainer-data-build"
BUILD_TMP="${PROJECT_ROOT}/containers/tmp/ipin-data-arm64_0.1.2"
EXPECTED_QUAL_SHA="9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5"

[[ "${OUTPUT_SIF}" == "${PROJECT_ROOT}/containers/images/ipin-data-arm64_0.1.2.sif" ]] || exit 1
[[ "${BUILD_CACHE}" == "${PROJECT_ROOT}/containers/cache/apptainer-data-build" ]] || exit 1
[[ "${BUILD_TMP}" == "${PROJECT_ROOT}/containers/tmp/ipin-data-arm64_0.1.2" ]] || exit 1
[[ -f "${DEFINITION}" ]] || { echo "Missing definition: ${DEFINITION}" >&2; exit 1; }
[[ -f "${QUAL_SIF}" ]] || { echo "Missing qualification SIF: ${QUAL_SIF}" >&2; exit 1; }
[[ ! -e "${OUTPUT_SIF}" ]] || { echo "Refusing to overwrite: ${OUTPUT_SIF}" >&2; exit 1; }

OBSERVED_QUAL_SHA=$(sha256sum "${QUAL_SIF}" | awk '{print $1}')
[[ "${OBSERVED_QUAL_SHA}" == "${EXPECTED_QUAL_SHA}" ]] || {
    echo "Qualification SIF checksum mismatch" >&2
    exit 1
}

for wheel in \
    duckdb-1.5.5-cp312-cp312-manylinux_2_26_aarch64.manylinux_2_28_aarch64.whl \
    et_xmlfile-2.0.0-py3-none-any.whl \
    openpyxl-3.1.5-py2.py3-none-any.whl \
    pypdf-6.14.2-py3-none-any.whl \
    xlrd-2.0.2-py2.py3-none-any.whl
do
    [[ -f "${PROJECT_ROOT}/containers/cache/data-wheels/${wheel}" ]] || {
        echo "Missing locked wheel: ${wheel}" >&2
        exit 1
    }
done

mkdir -p -- "${BUILD_CACHE}" "${BUILD_TMP}" "$(dirname -- "${OUTPUT_SIF}")"
export APPTAINER_CACHEDIR="${BUILD_CACHE}"
export APPTAINER_TMPDIR="${BUILD_TMP}"

cd -- "${PROJECT_ROOT}"
apptainer build --fakeroot "${OUTPUT_SIF}" "${DEFINITION}"
sha256sum "${OUTPUT_SIF}"
