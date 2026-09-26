# Releases

Release candidates and final releases are immutable, versioned packages. Public release requires expert-group approval, a passed release gate, license review, checksums, claim-ceiling review, and reproduction instructions.

No public release package is stored here. The current preserved predictors are
documented in the [four-model registry](../docs/models/FROZEN_PAIR_MODELS_v3.md),
with **iPIN-TUnA-31k** designated primary/default for human PPI ranking.
Its exact selected ensemble and the three historical reference models are
preserved locally; their weights remain local. The v3 release publishes
metadata, aggregate evidence and verification code. Public benchmark aggregates are indexed in
[benchmark/](../benchmark/README.md). A future approved package should create
its own versioned output directory and manifest.

The [X-PAIR test2 comparison](../docs/reports/m1/M1_XPAIR_Test2_Comparison_v1.md)
publishes a subsequent experiment's aggregate results and evaluation scripts
under `experiments/x_pair_test2_v1/`. It leaves the v3 registry, model card,
promotion report and release checksums unchanged; no new model release or
default-model change is made.
