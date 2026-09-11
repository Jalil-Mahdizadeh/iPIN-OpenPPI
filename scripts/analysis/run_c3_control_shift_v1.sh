#!/usr/bin/env bash
# Reproduce aggregate diagnostics with no test-pair/truth/key mount.
set -euo pipefail
if [[ $# -ne 2 || ( "$1" != "first" && "$1" != "supplement" ) ]]; then
    echo "Usage: bash scripts/analysis/run_c3_control_shift_v1.sh first|supplement NEW_OUTPUT_DIRECTORY" >&2
    exit 2
fi
task_stage=$1
task_repo=$(git rev-parse --show-toplevel)
task_output=$(realpath -m -- "$2")
cd "$task_repo"
sha256sum -c containers/locks/ipin-model-arm64_0.1.0.sif.sha256
mkdir -p "$task_output"
task_mounts=(
    --bind "$task_repo/src:/project/src:ro"
    --bind "$task_repo/scripts:/project/scripts:ro"
    --bind "$task_repo/docs/protocols:/project/docs/protocols:ro"
    --bind "$task_repo/artifacts/results:/project/artifacts/results:ro"
    --bind "$task_repo/artifacts/validation:/project/artifacts/validation:ro"
    --bind "$task_repo/data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/eligible_reference_sequences:/project/data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/eligible_reference_sequences:ro"
    --bind "$task_repo/data/canonical/final_benchmark_component_split_v1/endpoint_partition_assignments:/project/data/canonical/final_benchmark_component_split_v1/endpoint_partition_assignments:ro"
    --bind "$task_repo/.private/model_optimization_v1/bundle/data:/development:ro"
    --bind "$task_repo/.private/development_embedding_identity_correction_v2/evaluation/scores/C3_development:/scores:ro"
    --bind "$task_output:/output:rw"
)
if [[ "$task_stage" == "first" ]]; then
    task_mounts+=(--bind "$task_repo/artifacts/runs/protected_final_test_v1/frozen_bundle/features:/frozen/features:ro")
    task_args=(/project/scripts/analysis/c3_control_shift_v1.py --output /output/RESULTS.json)
else
    task_args=(/project/scripts/analysis/c3_control_shift_components_v1.py
        --first /project/artifacts/results/c3_control_shift_investigation_v1/RESULTS.json
        --output /output/COMPONENT_SUPPLEMENT.json)
fi
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
    apptainer exec --nv --cleanenv --containall --no-home \
    --no-mount bind-paths,home,cwd,hostfs "${task_mounts[@]}" --pwd /project \
    "$task_repo/containers/images/ipin-model-arm64_0.1.0.sif" \
    env PYTHONPATH=/project/src PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    CUBLAS_WORKSPACE_CONFIG=:4096:8 python "${task_args[@]}"
