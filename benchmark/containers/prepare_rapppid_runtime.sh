#!/usr/bin/env bash
set -euo pipefail
umask 077
bench_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
repo_root=$(dirname -- "$bench_root")
mkdir -p "$bench_root/rapppid/runtime" "$bench_root/containers/tmp/rapppid-v1" "$bench_root/containers/logs"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/rapppid-v1"
python3 -B "$bench_root/containers/fetch_rapppid_runtime.py"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs --pwd /runtime \
  --bind "$bench_root/rapppid/runtime:/runtime:rw" \
  --bind "$bench_root/containers/cache/rapppid-wheels:/wheels:ro" \
  --bind "$bench_root/containers/tmp/rapppid-v1:/work:rw" \
  "$repo_root/containers/images/ipin-model-arm64_0.1.0.sif" \
  env TMPDIR=/work PIP_CACHE_DIR=/work/pip-cache PYTHONDONTWRITEBYTECODE=1 \
  python -m pip install --no-index --find-links=/wheels --no-deps --no-build-isolation --target=/runtime \
  pytorch-lightning==1.3.8 torchmetrics==0.4.1 pyDeprecate==0.3.0 sentencepiece==0.2.1 \
  tables==3.10.2 blosc2==2.7.1 ranger21==0.1.0 passlib==1.7.4 fire==0.5.0 future==0.18.3 \
  numexpr==2.11.0 ndindex==1.10.0 msgpack==1.1.1 py-cpuinfo==9.0.0 termcolor==2.2.0
