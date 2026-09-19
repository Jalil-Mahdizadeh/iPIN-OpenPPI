#!/usr/bin/env bash
set -euo pipefail
umask 077
bench_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
repo_root=$(dirname -- "$bench_root")
rapppid_parent="$repo_root/containers/images/ipin-model-arm64_0.1.0.sif"
rapppid_output="$bench_root/containers/images/rapppid-native-arm64-v1.sif"
test ! -e "$rapppid_output"
mkdir -p "$bench_root/containers/"{tmp/rapppid-v1,manifests,logs,images}
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/rapppid-v1"
export TMPDIR="$bench_root/containers/tmp/rapppid-v1"
export PYTHONDONTWRITEBYTECODE=1
unset APPTAINER_BIND APPTAINER_BINDPATH SINGULARITY_BIND SINGULARITY_BINDPATH
exec > >(tee -a "$bench_root/containers/logs/rapppid-native-v1-build.log") 2>&1
date -u
python3 -B "$bench_root/containers/fetch_rapppid.py"
test -d "$bench_root/rapppid/runtime/pytorch_lightning"
test "$(sha256sum "$rapppid_parent" | cut -d ' ' -f1)" = c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91
cd "$repo_root"
apptainer build --fakeroot --mksquashfs-args '-processors 8' "$rapppid_output" "$bench_root/containers/rapppid-native-arm64-v1.def"
sha256sum "$rapppid_output" > "$bench_root/containers/manifests/rapppid-sif.sha256"
apptainer inspect --json "$rapppid_output" > "$bench_root/containers/manifests/rapppid-inspect.json"
date -u
echo 'Image built; native GPU/cache/metric qualification required before test access.'
