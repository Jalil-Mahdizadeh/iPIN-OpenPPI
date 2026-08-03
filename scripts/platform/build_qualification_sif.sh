#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "${script_dir:?}/../lib/project_paths.sh"

ipin_prepare_runtime_dirs

definition="${IPIN_PROJECT_ROOT}/containers/definitions/ipin-qual-arm64_0.1.0.def"
image="${IPIN_PROJECT_ROOT}/containers/images/ipin-qual-arm64_0.1.0.sif"
checksum="${IPIN_PROJECT_ROOT}/containers/locks/ipin-qual-arm64_0.1.0.sif.sha256"
inspection="${IPIN_PROJECT_ROOT}/containers/manifests/ipin-qual-arm64_0.1.0.inspect.json"
build_log="${IPIN_PROJECT_ROOT}/artifacts/reports/platform/ipin-qual-arm64_0.1.0.build.log"

for required_input in "${definition}"; do
    required_input="$(ipin_resolve_within_project "${required_input}")"
    if [[ ! -f "${required_input}" || -L "${required_input}" ]]; then
        echo "Required regular input is missing or is a symbolic link: ${required_input}" >&2
        exit 2
    fi
done

for new_output in "${image}" "${checksum}" "${inspection}" "${build_log}"; do
    ipin_require_new_path "${new_output}"
done

export APPTAINER_CACHEDIR="${IPIN_APPTAINER_CACHE}"
export APPTAINER_TMPDIR="${IPIN_APPTAINER_TMP}"

echo "Building ${image}"
apptainer build "${image}" "${definition}" 2>&1 | tee "${build_log}"
sha256sum "${image}" > "${checksum}"
apptainer inspect --json "${image}" > "${inspection}"

echo "Created immutable qualification image and provenance:"
echo "  image: ${image}"
echo "  checksum: ${checksum}"
echo "  inspection: ${inspection}"
echo "  build log: ${build_log}"

