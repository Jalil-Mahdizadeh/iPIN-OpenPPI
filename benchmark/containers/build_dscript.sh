#!/usr/bin/env bash
set -euo pipefail
umask 077
bench_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
repo_root=$(dirname -- "$bench_root")
dscript_parent="$repo_root/containers/images/ipin-model-arm64_0.1.0.sif"
dscript_output="$bench_root/containers/images/dscript-native-arm64-v1.sif"
test ! -e "$dscript_output"
test "$(sha256sum "$dscript_parent" | cut -d ' ' -f1)" = c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91
mkdir -p "$bench_root/containers/"{cache/dscript-wheels,cache/dscript-build-wheels,tmp/dscript-v1,manifests,logs,images}
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/dscript-v1"
export TMPDIR="$bench_root/containers/tmp/dscript-v1"
export PYTHONDONTWRITEBYTECODE=1
unset APPTAINER_BIND APPTAINER_BINDPATH SINGULARITY_BIND SINGULARITY_BINDPATH
exec > >(tee -a "$bench_root/containers/logs/dscript-native-v1-build.log") 2>&1
date -u
python3 -B "$bench_root/containers/fetch_dscript_dependencies.py"
dscript_exec=(apptainer exec --cleanenv --containall --no-home --no-mount "bind-paths,home,cwd,hostfs"
  --bind "$bench_root/containers:/work:rw" --bind /etc/resolv.conf:/etc/resolv.conf:ro --pwd /work "$dscript_parent"
  env PIP_CACHE_DIR=/work/cache/dscript-pip TMPDIR=/work/tmp/dscript-v1 PYTHONDONTWRITEBYTECODE=1)
if [[ ! -f "$bench_root/containers/manifests/dscript-build-requirements.lock" ]]; then
  "${dscript_exec[@]}" python -m pip download --index-url https://pypi.org/simple --only-binary=:all: \
    --dest /work/cache/dscript-build-wheels numpy==2.0.2 hatch==1.14.0 hatchling==1.27.0 \
    hatch-vcs==0.4.0 hatch-cython==0.5.0 setuptools-scm==8.2.0 setuptools==79.0.1 wheel==0.45.1 Cython==3.1.2
fi
python3 -B "$bench_root/containers/freeze_dscript_build_wheels.py"
# NumPy 2 is confined to this throwaway compiler environment. Runtime stays on 1.26.4.
"${dscript_exec[@]}" python -m venv /work/tmp/dscript-v1/build-venv
"${dscript_exec[@]}" /work/tmp/dscript-v1/build-venv/bin/python -m pip install \
  --no-index --find-links=/work/cache/dscript-build-wheels --require-hashes \
  -r /work/manifests/dscript-build-requirements.lock
"${dscript_exec[@]}" /work/tmp/dscript-v1/build-venv/bin/python -m pip wheel \
  --no-index --no-deps --no-build-isolation --wheel-dir /work/cache/dscript-wheels \
  /work/cache/dscript-wheels/biotraj-1.2.2.tar.gz /work/cache/dscript-wheels/biotite-1.2.0.tar.gz
sha256sum "$bench_root"/containers/cache/dscript-wheels/*.whl > "$bench_root/containers/manifests/dscript-runtime-wheels.sha256"
cd "$repo_root"
apptainer build --fakeroot --mksquashfs-args '-processors 8' "$dscript_output" "$bench_root/containers/dscript-native-arm64-v1.def"
sha256sum "$dscript_output" > "$bench_root/containers/manifests/dscript-sif.sha256"
apptainer inspect --json "$dscript_output" > "$bench_root/containers/manifests/dscript-inspect.json"
date -u
echo 'SIF built. Run benchmark/dscript/test_container.sh before any benchmark work.'
