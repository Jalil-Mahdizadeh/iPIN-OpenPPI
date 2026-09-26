#!/usr/bin/env bash
set -euo pipefail
MANUSCRIPT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPOSITORY_ROOT=$(dirname "$MANUSCRIPT_ROOT")
export APPTAINER_CACHEDIR="$MANUSCRIPT_ROOT/cache"
export APPTAINER_TMPDIR="$MANUSCRIPT_ROOT/tmp"
exec apptainer exec --cleanenv --containall --bind "$REPOSITORY_ROOT:$REPOSITORY_ROOT:ro" --bind "$MANUSCRIPT_ROOT:$MANUSCRIPT_ROOT:rw" --pwd "$REPOSITORY_ROOT" --env PYTHONDONTWRITEBYTECODE=1,MPLCONFIGDIR="$MANUSCRIPT_ROOT/cache/matplotlib",TMPDIR="$MANUSCRIPT_ROOT/tmp" "$REPOSITORY_ROOT/containers/images/ipin-model-arm64_0.1.0.sif" "$@"
