# Model registry

Current catalogue: [Frozen pair models v2](FROZEN_PAIR_MODELS_v2.md),
authorized by [DEC-0055](../../governance/decisions/DEC-0055-freeze-tuna-retrained-as-third-ipin-model.md).

- Original confirmatory baseline:
  `lightweight_esm2_150m_linear__linear_lr3e-4`.
- Optimized pooled residual-MLP ensemble:
  `esm2_150m__residual_wide__epoch04_ensemble3`.
- Third frozen iPIN model, TUnA-retrained (PU-TUnA):
  `tuna_retrained_ensemble`, aliases `tuna-retrained` and `ipin_tuna_retrained`.

All three retain their exact three-seed prediction definitions. The first two
average raw member scores; TUnA-retrained averages mean-field-adjusted logits
and retains its trained GP covariance. TUnA-retrained has the highest observed
C3 point score, but its paired difference from optimized pooled iPIN includes
zero. Registration is not a statistically conclusive superiority claim.

Exact hashes, model roles and preserved inputs are in the
[machine-readable registry](../../artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json).
Private model weights remain local and are not distributed in this Git repository.

The [v1 registry and cards](FROZEN_PAIR_MODELS_v1.md) remain unchanged historical
records for the first two models. Published-model comparisons are indexed in
[benchmark/](../../benchmark/README.md); the original TUnA predictor remains a
separate comparator.

External transfer: [six non-human organisms](../../benchmark/nonhuman_transfer_v1/REPORT.md).
The three unchanged ensembles score 61,385 rows for 300 targets, with
species-specific retrieval and exact/related human-training exposure audits.
This evaluation does not retrain, promote, or alter a model; the versioned
cards and registry remain immutable. Non-human taxids do not establish absence
from sequence pretraining or absence of homologous human training proteins.

Current biological application: [expanded twelve-target comparison](../../example/twelve_target_comparison_v2/REPORT.md)
and [panel index](../../example/INDEX.md). All three unchanged models and original
published TUnA score 5,587 pairs with fresh embeddings. Five candidate sets compare
context, background and biologically selected low-plausibility U, with all prior
retrieval metrics, exposure checks and evidence-tier sensitivities. Original TUnA
is a comparator; the registry still has three iPIN models. Versioned model cards
and their checksum-bound freeze records remain unchanged.

The [original TUnA example audit](../../example/original_tuna_investigation_v1/REPORT.md)
verifies the authors' checkpoint directly and finds a plausible transfer route
through analogous training pairs for EGFR. Its net lead is sensitive to EGFR;
the registered predictors and all completed benchmark records remain unchanged.
