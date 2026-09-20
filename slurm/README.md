# Arrhenius Slurm jobs

Submit versioned job specifications from the project root. Scheduler stdout/stderr goes to `slurm/logs/`; scientific run outputs go to unique directories under `artifacts/runs/`.

This directory contains core platform, data, training, evaluation, and diagnostic
jobs. Published-method job specifications live with each method under
[benchmark/](../benchmark/README.md); example jobs live under
[example/](../example/six_target_comparison_v1/README.md).
Recorded job IDs in historical reports describe those executions and do not
indicate that a job is still running. Check the relevant completion report
before using any entry point; protected evaluations have single-use guards.
