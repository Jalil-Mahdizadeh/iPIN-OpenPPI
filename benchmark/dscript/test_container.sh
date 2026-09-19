#!/usr/bin/env bash
set -euo pipefail
umask 077
dscript_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bench_root=$(dirname -- "$dscript_root")
dscript_image="$bench_root/containers/images/dscript-native-arm64-v1.sif"
test -f "$dscript_image"
sha256sum --check "$bench_root/containers/manifests/dscript-sif.sha256"
mkdir -p "$dscript_root/qualification"
dscript_run=$(mktemp -d "$dscript_root/qualification/sif-test-XXXXXXXX")
mkdir -p "$dscript_run"/{tmp,cache,mpl}
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/dscript-v1"
unset APPTAINER_BIND APPTAINER_BINDPATH SINGULARITY_BIND SINGULARITY_BINDPATH
echo "Qualification output: $dscript_run"
python3 -B "$dscript_root/scripts/scope_guard.py" record --snapshot "$dscript_run/scope-before.json"
# Only test scripts are mounted read-only and this new output directory read-write.
# No root-repository data, checkpoints, training splits, or test labels are mounted.
apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$dscript_root/scripts:/qualification-scripts:ro" \
  --bind "$dscript_root/tests/offline_guard:/offline-guard:ro" \
  --bind "$dscript_run:/output:rw" --pwd /output "$dscript_image" \
  env PYTHONPATH=/offline-guard DSCRIPT_TEST_OFFLINE=1 TMPDIR=/output/tmp \
  XDG_CACHE_HOME=/output/cache MPLCONFIGDIR=/output/mpl HF_HOME=/output/cache/huggingface \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONHASHSEED=20260912 NVIDIA_TF32_OVERRIDE=0 \
  python -B /qualification-scripts/qualify_native.py --output /output 2>&1 | tee "$dscript_run/test.log"
python3 -B "$dscript_root/scripts/scope_guard.py" verify --snapshot "$dscript_run/scope-before.json"
echo "Test report: $dscript_run/qualification.json"
