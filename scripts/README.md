# Executable entry points

Core scripts are grouped by the work they execute:

| Directory | Purpose |
|---|---|
| `data/` | Acquisition, staging, reconciliation, source audits, and data validation |
| `benchmark/` | Benchmark construction, development release, protected evaluation, and publication |
| `model/` | Runtime qualification, model custody, embedding preparation, and training |
| `analysis/` | Bounded analyses of existing evidence and model results |
| `platform/` | Arrhenius, container, and hardware qualification |
| `lib/` | Shared shell/runtime helpers |

Reusable scientific logic generally lives under [src/](../src/README.md).
Some frozen evaluation entry points also contain protocol-specific scoring and
publication logic; preserve their registered identities when inspecting them.
Core scheduler declarations live under [slurm/](../slurm/README.md).

Published-model runners and scheduler files live with each method under
[benchmark/](../benchmark/README.md), while the six-target application is under
[example/](../example/six_target_comparison_v1/README.md). Run scientific entry
points inside their qualified ARM64 SIF and use a new run directory. Completed
single-use evaluations are not general-purpose rerun commands.
