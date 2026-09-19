#!/usr/bin/env bash
set -euo pipefail
umask 077
bench_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
repo_root=$(dirname -- "$bench_root")
sprint_output="$bench_root/containers/images/sprint-native-arm64-v1.sif"
test ! -e "$sprint_output"
mkdir -p "$bench_root/containers/"{tmp/sprint-v1,manifests,logs,images,cache/apptainer}
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/sprint-v1"
export TMPDIR="$bench_root/containers/tmp/sprint-v1"
export PYTHONDONTWRITEBYTECODE=1
unset APPTAINER_BIND APPTAINER_BINDPATH SINGULARITY_BIND SINGULARITY_BINDPATH
exec > >(tee -a "$bench_root/containers/logs/sprint-native-v1-build.log") 2>&1
date -u
python3 -B "$bench_root/containers/sprint_source_manifest.py"
cd "$repo_root"
apptainer build --fakeroot --mksquashfs-args '-processors 8' "$sprint_output" "$bench_root/containers/sprint-native-arm64-v1.def"
sha256sum "$sprint_output" > "$bench_root/containers/manifests/sprint-sif.sha256"
apptainer inspect --json "$sprint_output" > "$bench_root/containers/manifests/sprint-inspect.json"
date -u
echo 'Image built; native numerical qualification required before test scoring.'
