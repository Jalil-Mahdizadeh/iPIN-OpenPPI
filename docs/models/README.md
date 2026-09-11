# Model registry

Current release: [Frozen pair models v1](FROZEN_PAIR_MODELS_v1.md),
authorized by [DEC-0054](../../governance/decisions/DEC-0054-freeze-and-designate-both-models.md).

- Best-performing model by observed benchmark score:
  `esm2_150m__residual_wide__epoch04_ensemble3`.
- Original confirmatory baseline:
  `lightweight_esm2_150m_linear__linear_lr3e-4`.

Both are frozen three-seed ensembles. Their prediction is the equal mean of
raw member scores. The optimized C3 test point is higher, but its paired gain
interval includes zero; the best-performing designation is not a statistically
conclusive superiority claim.

Exact hashes, model roles and preserved inputs are in the
[machine-readable registry](../../artifacts/models/frozen_pair_models_v1/MODEL_REGISTRY.json).
Private model weights remain local and are not distributed in this Git repository.
