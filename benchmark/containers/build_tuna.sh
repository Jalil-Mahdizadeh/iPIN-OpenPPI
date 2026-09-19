#!/usr/bin/env bash
set -euo pipefail
umask 077
bench_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
repo_root=$(dirname -- "$bench_root")
bench_parent="$repo_root/containers/images/ipin-model-arm64_0.1.0.sif"
bench_output="$bench_root/containers/images/tuna-arm64-v1.sif"
test ! -e "$bench_output"
test "$(sha256sum "$bench_parent" | cut -d ' ' -f1)" = c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91
mkdir -p "$bench_root/containers/cache/tuna-wheels" "$bench_root/containers/tmp/tuna-v1" "$bench_root/containers/manifests"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/tuna-v1"
export TMPDIR="$bench_root/.tmp"
python3 "$bench_root/containers/fetch_tuna_dependencies.py"
env -u APPTAINER_BIND -u APPTAINER_BINDPATH \
  apptainer exec --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$bench_root:/benchmark:rw" --pwd /benchmark "$bench_parent" \
  env PIP_CACHE_DIR=/benchmark/.cache/pip TMPDIR=/benchmark/.tmp \
  python -m pip wheel --no-index --no-deps --no-build-isolation \
  --wheel-dir /benchmark/containers/cache/tuna-wheels \
  /benchmark/containers/cache/tuna-wheels/uncertainty-calibration-0.1.4.tar.gz
sha256sum "$bench_root"/containers/cache/tuna-wheels/*.whl > "$bench_root/containers/manifests/tuna-wheel-sha256.txt"
cd "$repo_root"
apptainer build --fakeroot --mksquashfs-args '-processors 8' "$bench_output" "$bench_root/containers/tuna-arm64-v1.def"
sha256sum "$bench_output" > "$bench_root/containers/manifests/tuna-sif-sha256.txt"
apptainer inspect --json "$bench_output" > "$bench_root/containers/manifests/tuna-inspect.json"
