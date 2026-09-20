# Project status v55 — TUnA-retrained is the third frozen iPIN model

Date: 2026-09-20. Decision:
[DEC-0055](decisions/DEC-0055-freeze-tuna-retrained-as-third-ipin-model.md).
Previous immutable model status: [v54](PROJECT_STATUS_v54.md).

The current catalogue contains three frozen prediction units:

1. `lightweight_esm2_150m_linear__linear_lr3e-4`: original confirmatory affine
   ensemble, retained unchanged.
2. `esm2_150m__residual_wide__epoch04_ensemble3`: optimized pooled residual-MLP
   ensemble, retained unchanged.
3. `tuna_retrained_ensemble`: TUnA-retrained (PU-TUnA), the fixed three-seed
   epoch-4 predictor selected in the completed TUnA benchmark.

The third model retains its published TUnA architecture attribution, full-context
residue pipeline, trained GP state, and equal FP64 mean of FP32 mean-field-adjusted
logits. It uses neither the pooled-model standardizer nor a sigmoid output.
Its C3 development concordance is 0.804456; C1/C2/C3 test concordances are
0.948619 / 0.880401 / 0.815875. Its primary C3 advantage over optimized pooled
iPIN remains inconclusive: +0.007927 [−0.028978, +0.038272].

The [v2 registry and cards](../docs/models/FROZEN_PAIR_MODELS_v2.md) add exact
identity and read-only preservation for model 3. Models 1 and 2 resolve to their
unchanged v1 bundle; the original v1 registry and release closure are verified.
The new bundle preserves byte-identical selected TUnA runtime states, endpoint
features, inference sources, upstream code, and provenance. Synthetic residue
fixtures validate native/factorized scoring and unchanged checkpoint tensors.

This is a post-result preservation decision. No training, covariance refit,
encoder inference, benchmark scoring, truth access, metric recomputation, or new
evaluation occurs. Existing result records, failed gates, amendments, and spent
ledgers remain intact. PU ranking does not establish binding probabilities,
direct binding, universal superiority, or independent replication.

Public metadata and validation evidence are under
`artifacts/models/frozen_pair_models_v2/` and
`artifacts/validation/frozen_pair_models_v2/`; weights remain local under
`.private/frozen_pair_models_v2/bundle/`.
