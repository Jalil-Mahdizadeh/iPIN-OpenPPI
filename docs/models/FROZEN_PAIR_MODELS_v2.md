# Frozen iPIN pair models v2

Date: 2026-09-20. Decision:
[DEC-0055](../../governance/decisions/DEC-0055-freeze-tuna-retrained-as-third-ipin-model.md).

The iPIN catalogue now contains **three frozen models**. Model 3 is the existing
development-selected TUnA-retrained ensemble, also called **PU-TUnA**. Its
published TUnA architecture and the iPIN TRAIN-only PU adaptation retain their
attribution. Registration adds preservation and a project model role; it does
not change weights, checkpoint selection, predictions, or benchmark results.

| Model | Exact registry ID | Role | C1 test | C2 test | C3 test (primary) |
|---|---|---|---:|---:|---:|
| 1. Original iPIN | `lightweight_esm2_150m_linear__linear_lr3e-4` | Original confirmatory affine ensemble | 0.843493 | 0.805299 | 0.789249 |
| 2. Optimized pooled iPIN | `esm2_150m__residual_wide__epoch04_ensemble3` | Development-selected residual-MLP ensemble | 0.916037 | 0.851301 | 0.807948 |
| 3. TUnA-retrained | `tuna_retrained_ensemble` | Three-seed epoch-4 PU-TUnA ensemble | 0.948619 | 0.880401 | 0.815875 |

The third model's aliases are `tuna-retrained` and `ipin_tuna_retrained`.
`tuna_retrained_ensemble` remains its unchanged benchmark result identifier.
The authors' original released `tuna_original` predictor remains a published
comparator and is not one of these three registered iPIN models.

TUnA-retrained has the highest C3 point estimate of these three, but its paired
gain over optimized pooled iPIN is **+0.007927 [−0.028978, +0.038272]**.
This interval includes zero; primary C3 superiority is not established.
The [original TUnA result record](../../benchmark/tuna/results/RESULTS.md),
[full scores](../../benchmark/tuna/results/scores.csv), and
[paired contrasts](../../benchmark/tuna/results/paired_differences.csv) remain
unchanged. This registration follows the completed benchmark and descriptive
examples; it is not a new prospective selection or independent replication.

## Unchanged models 1 and 2

The [v1 cards](FROZEN_PAIR_MODELS_v1.md), v1 registry, release closure, and private
bundle remain immutable. The v2 catalogue copies both exact model definitions
and resolves their state paths through `.private/frozen_pair_models_v1/bundle/`.
The v1 "best-performing" designation remains historically scoped to those two
pooled iPIN models.

Their frozen ESM-2 encoder, windowed residue-mean pooling, TRAIN-only
standardization, symmetric 1,921-dimensional pair features, head states, seed
order, and equal FP64 mean of FP32 raw scores are unchanged. The v1 verifier is
also run as part of v2 verification.

## Exact TUnA-retrained prediction definition

The preserved predictor is the **epoch-4 ensemble of seeds 20260803, 20260817,
and 20260831**, in that order, with equal weights. The completed training
schedule ran eight epochs; C3 development alone selected epoch 4 over epoch 8.
Its C3 development concordance is 0.8044558035378994. All three seeds are
retained. No selection is performed during this registration.

The encoder is `facebook/esm2_t30_150M_UR50D`, revision
`a695f6045e2e32885fa60af20c13cb35398ce30c`, with weight SHA-256
`c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566`.
The unchanged encoder files are preserved in the v1 bundle and explicitly
referenced by the v2 registry.

TUnA uses **full-context final-layer residue representations**, followed by its
full-length native endpoint encoders. It does not use the other models'
windowed pooled vectors or training normalizer. The qualified implementation
forms a symmetric 64-dimensional elementwise maximum of endpoint features,
followed by 4,096 random Fourier features and the GP output layer. Architecture
and runtime identities are recorded in the machine-readable registry. Preserve
the exact upstream TUnA and GP implementations: their tensor shapes alone are
not a complete model definition.

For member `s`, retain its trained precision and covariance and calculate:

```text
adjusted_logit_s = logit_s / sqrt(1 + pi * frozen_GP_variance_s / 8)
prediction = mean_FP64(adjusted_logit_20260803,
                       adjusted_logit_20260817,
                       adjusted_logit_20260831)
```

Member operations and parameters are FP32; cast member outputs to FP64 before
averaging. Use evaluation/inference mode, disable dropout, AMP, and TF32, set
`gp_layer.fitted = True`, and keep `update_precision = False`. Do not refit GP
covariance, apply a sigmoid or calibration, average probabilities, or change
member weights. These are ranking scores, not interaction probabilities.

The exact runtime-state files are:

| Seed | State SHA-256 |
|---|---|
| 20260803 | `c96b6cd4dcde5edc766d1028d8f22a410a072b1376d26cb392f09c3801793ebd` |
| 20260817 | `f1444b8d43efcf4d76a73a6f4a0419d395651b493f5e21dc8ab1dd002a7e0c02` |
| 20260831 | `45aae93319be687cec386d7875a78d4a4b5068a635874abe67b6d9ab1a23727c` |

These are byte-identical copies of the completed benchmark's scorer states.
The original training checkpoint archives have different serialization hashes;
every state tensor is checked for exact equality with its selected training
checkpoint, including GP and spectral-normalization buffers.

## Preservation and verification

The [v2 registry](../../artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json)
is the current three-model catalogue. Its `model_bundles` mapping identifies
the correct base directory for each model's relative state paths. Its
[artifact registry](../../artifacts/models/frozen_pair_models_v2/ARTIFACT_REGISTRY.json)
binds this versioned card, decision/status/gate, preservation code, tests, and
audit. Living navigation indexes are updated separately.

The new `.private/frozen_pair_models_v2/bundle/` holds the three TUnA runtime
states, their 17,000 × 64 endpoint feature matrices, endpoint/component identity
manifests, inference source snapshots, pinned upstream sources/licenses, and
closed selection/evaluation provenance. It references the preserved v1 encoder
instead of duplicating it. Files are mode 0400 and directories 0500. Public and
private registry copies are byte-identical; SHA-256 checks detect content drift.
This is local preservation, not hardware WORM storage or an off-site backup.

The qualified runtime is `benchmark/containers/images/tuna-arm64-v1.sif`, SHA-256
`98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1`.
Inside that image, with the repository mounted read-only at `/project`, verify:

```sh
PYTHONPATH=/project/src:/opt/tuna/vendor PYTHONDONTWRITEBYTECODE=1 \
  python -B /project/scripts/model/freeze_pair_models_v2.py /project
```

Verification checks all three model identities, v1 preservation, the TUnA source
freeze and runtime, byte-identical bundle contents, read-only permissions,
checkpoint/feature membership, and closed evaluation records. It neither opens
pair data nor runs a spent evaluation operator. `--create` constructs the new
release once and refuses an existing release.

The [freeze audit](../../artifacts/validation/frozen_pair_models_v2/FREEZE_AUDIT.json)
and [unit-test evidence](../../artifacts/validation/frozen_pair_models_v2/UNIT_TESTS.xml)
record validation. Additional CPU qualification uses the actual preserved heads
with synthetic residue inputs to compare native pairwise and factorized scoring,
check order symmetry, and confirm that all parameters and buffers stay unchanged.
Historical GPU qualifications remain part of the original TUnA evidence; the
preservation step does not repeat encoder or benchmark inference.

Weights, endpoint identities, and private feature matrices remain outside Git.
A fresh checkout contains public metadata, code, and aggregate results, not a
standalone arbitrary-sequence scoring service or every execution dependency.
The source snapshots preserve the original pipeline context; the historical
minimal scorer also contains the original-TUnA comparison branch, which is not
added to the three-model catalogue.

## Claim boundaries

These are positive-versus-unlabeled ranking results on previously examined
panels. Unlabeled pairs are not verified negatives. C3 concerns interaction-
training-naïve endpoints under the frozen split, not absence from sequence
pretraining or all homology. Direct binding, genuine partner specificity, and
shortcut-free generalization remain unresolved. The separate six-target
application is descriptive and does not select or modify this ensemble.

No training, GP refitting, encoder inference, benchmark scoring, truth access,
metric recomputation, or ledger reset is performed for this freeze. Any later
change to a frozen predictor requires a new version and authorization.
