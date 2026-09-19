#!/usr/bin/env bash
set -euo pipefail
umask 077
bench_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
repo_root=$(dirname -- "$bench_root")
plm_parent="$repo_root/containers/images/ipin-model-arm64_0.1.0.sif"
plm_output="$bench_root/containers/images/plm-interact-native-arm64-v1.sif"
test ! -e "$plm_output"
mkdir -p "$bench_root/containers/"{cache/plm-interact-wheels,tmp/plm-interact-v1,manifests,logs,images}
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/plm-interact-v1"
export TMPDIR="$bench_root/containers/tmp/plm-interact-v1"
export PYTHONDONTWRITEBYTECODE=1
unset APPTAINER_BIND APPTAINER_BINDPATH SINGULARITY_BIND SINGULARITY_BINDPATH
exec > >(tee -a "$bench_root/containers/logs/plm-interact-native-v1-build.log") 2>&1
date -u
python3 -B "$bench_root/containers/fetch_plm_interact.py"
test "$(sha256sum "$plm_parent" | cut -d ' ' -f1)" = c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91
cd "$repo_root"
apptainer build --fakeroot --mksquashfs-args '-processors 8' "$plm_output" "$bench_root/containers/plm-interact-native-arm64-v1.def"
sha256sum "$plm_output" > "$bench_root/containers/manifests/plm-interact-sif.sha256"
apptainer inspect --json "$plm_output" > "$bench_root/containers/manifests/plm-interact-inspect.json"
date -u
echo 'Image built; model and scoring qualification still required before test access.'
