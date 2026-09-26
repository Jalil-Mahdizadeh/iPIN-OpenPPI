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
[benchmark/](../benchmark/README.md), while the twelve-target application is under
[example/](../example/twelve_target_comparison_v2/README.md). Its local scripts
add annotated low-plausibility U, score all three frozen iPIN models and original
TUnA, compare five candidate sets, independently validate results, and render
reports/figures. Run scientific entry
points inside their qualified ARM64 SIF and use a new run directory. Completed
single-use evaluations are not general-purpose rerun commands.

Current model-preservation entry points are
`model/freeze_pair_models_v3.py` for the [four-model catalogue and primary iPIN-TUnA-31k](../docs/models/FROZEN_PAIR_MODELS_v3.md),
`model/freeze_pair_models_v2.py` for the historical three-model release (both
use the pinned TUnA SIF), and `model/freeze_pair_models_v1.py` for the original
two-model release (pinned core model SIF). Each defaults to read-only verification;
`--create` refuses an existing release. The v3 verifier checks v2 and v1 custody,
selected-state identities, aggregate provenance and private bundle checksums.
Creation uses synthetic residues for real-state qualification; it performs no
training, encoder inference, benchmark scoring, truth access or metric recomputation.
Some subdirectory READMEs belong to historical checksum-bound releases and
retain their phase-specific instructions.
