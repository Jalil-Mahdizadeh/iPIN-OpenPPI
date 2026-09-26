# Frozen iPIN pair models v3

Date: 2026-09-26. Decision: [DEC-0056](../../governance/decisions/DEC-0056-designate-ipin-tuna-31k-primary-model.md).

**iPIN-TUnA-31k is the current primary/default iPIN predictor for human PPI
ranking.** Its registry ID is `ipin_tuna_31k_ensemble`; its completed experiment
result ID remains `selected_31k`. The catalogue contains four frozen models.

| Model | Registry ID | Current role |
|---|---|---|
| iPIN-TUnA-31k | `ipin_tuna_31k_ensemble` | Primary/default human PPI predictor |
| Original iPIN | `lightweight_esm2_150m_linear__linear_lr3e-4` | Historical confirmatory reference |
| Optimized pooled iPIN | `esm2_150m__residual_wide__epoch04_ensemble3` | Historical pooled-model reference |
| TUnA-retrained / PU-TUnA, 17k | `tuna_retrained_ensemble` | Historical three-seed epoch-4 reference |

The [v3 registry](../../artifacts/models/frozen_pair_models_v3/MODEL_REGISTRY.json)
sets both `primary_model` and `default_model` to `ipin_tuna_31k_ensemble`.
Aliases `iPIN-TUnA-31k`, `ipin-tuna-31k`, and `selected_31k` resolve to that entry.
The earlier `tuna-retrained` and `ipin_tuna_retrained` aliases retain their
17k model identity. The [v1](FROZEN_PAIR_MODELS_v1.md) and
[v2](FROZEN_PAIR_MODELS_v2.md) releases, definitions and results remain unchanged.

## Exact primary prediction unit

The primary model is the existing **31,188-positive, epoch-1 ensemble of seeds
20260803, 20260817 and 20260831**, with all three retained in that order.
The completed scaling study selected a common epoch and training budget using
the equal-weight mean of C3 development concordance on the reconciled legacy
and added cohorts. The selected development macro was 0.7789176315647479.
No selection, training, or benchmark scoring occurs during this registration.

The training expansion used qualified locally frozen human binary evidence
from IntAct, Lit-BM and additional HuRI views. The 31,188-P set contains the
original 16,799 P. All budgets in the new curve shared a newly sampled 2M-U
background excluding held-out candidates and expanded positive evidence.
Source composition, the reconciled U population and checkpoint selection also
changed relative to historical models; the comparison does not isolate data
volume or architecture causally. The endpoint universe contains 17,583
sequences, preserving the original 17,000 in the same order.

Architecture attribution remains **published Bernett TUnA with the iPIN
TRAIN-only PU adaptation**. The frozen ESM-2 150M encoder supplies full-context
layer-30 residue representations, followed by native full-length TUnA endpoint
encoders, a symmetric 64-dimensional maximum and 4,096 random Fourier features.
Encoder and upstream identities are inherited from the v2 card and recorded
explicitly in v3. The qualified container is `tuna-arm64-v1.sif`, SHA-256
`98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1`.

For each member, load the exact state, set `gp_layer.fitted = True` **before**
calling `eval()`, then retain `update_precision = False`. Use the preserved
SDPA implementation, FP32 parameters/operations, inference mode, no dropout,
no AMP and no TF32. The score is:

```text
member_score = logit / sqrt(1 + pi * saved_GP_variance / 8)
prediction = mean_FP64(member_score_20260803,
                       member_score_20260817,
                       member_score_20260831)
```

The exact saved precision and covariance remain unchanged. There is no sigmoid,
calibration, probability averaging, covariance refit or training normalizer.
This is a ranking score, not an interaction probability. The earlier scaling
report had a small GP reload-order drift; the
[replay audit](../../artifacts/models/frozen_pair_models_v3/evidence/scaling/covariance_replay.json)
and current test2 comparison use the saved covariance. Historical results remain
unchanged and the distinction is disclosed.

| Seed | Exact state SHA-256 |
|---|---|
| 20260803 | `f29ee395d747ff07cffba14d028430fa9c9ab1e7559a71b678b8541a22f7f979` |
| 20260817 | `7581d4f43354201914ba38924f58bd2e10b4babb9f56ccf6c104276190c97f59` |
| 20260831 | `707f56e0007e0af10d6949924d4c7afc096b9d87cf2375bb050dd12b9d11e66a` |

## Evidence for the designation

Test2's primary metric gives equal weight to design-weighted P/U concordance
in the reconciled legacy and added cohorts. C3 is primary. All 13 evaluated
predictors cover all 3,774,966 candidate rows.

| Registered predictor | C1 test2 macro | C2 test2 macro | C3 test2 macro |
|---|---:|---:|---:|
| **iPIN-TUnA-31k** | **0.886903** | **0.827113** | **0.786652** |
| Original iPIN | 0.744322 | 0.718876 | 0.726124 |
| Optimized pooled iPIN | 0.793734 | 0.750272 | 0.742563 |
| Historical PU-TUnA, 17k | 0.821205 | 0.772189 | 0.743871 |

iPIN-TUnA-31k has the highest macro point estimate among all 13 predictors in
C1, C2 and C3. Its paired C3 gain over the closest macro comparator, historical
17k PU-TUnA, is **+0.042781 [0.019768, 0.070150]**. All 12 paired C3 95%
intervals are positive; these use 2,000 common component-bootstrap draws and
are pointwise, without multiplicity correction. See the
[promotion report](../reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md),
[complete comparison](../../artifacts/models/frozen_pair_models_v3/evidence/test2/RESULTS.md),
and [paired intervals](../../artifacts/models/frozen_pair_models_v3/evidence/test2/paired_differences.csv).

The designation is scoped to these results. **PLM-interact scores higher on
added C3 alone: 0.767828 versus 0.740105.** The previous 17k TUnA scores higher
on reconciled legacy C1/C2. Removing all 91,781 C1 development-overlapping
candidates in the separate sensitivity view leaves the primary model first
at 0.887219. Test2, including its added cohort, is a disclosed historical
follow-up, not independent replication. The twelve-target panel is descriptive
and has training exposure; its results do not establish universal superiority.
Non-human evaluations of the earlier three models do not evaluate this model.

## Preservation and verification

`.private/frozen_pair_models_v3/bundle/` preserves byte-identical selected
states, their 17,583-by-64 feature matrices, sequence order, native code,
upstream licenses and selection/evaluation provenance. Files are mode 0400;
directories are 0500. The existing v1 encoder is referenced rather than copied.
The v3 verifier also verifies both prior releases and all recorded source copies.

Inside the pinned TUnA image with the repository mounted read-only at `/project`:

```sh
PYTHONPATH=/project/src:/opt/tuna/vendor PYTHONDONTWRITEBYTECODE=1 \
  python3 -B /project/scripts/model/freeze_pair_models_v3.py /project
```

`--create` constructs a new release once and refuses an existing release.
The [freeze audit](../../artifacts/validation/frozen_pair_models_v3/FREEZE_AUDIT.json)
and [unit evidence](../../artifacts/validation/frozen_pair_models_v3/UNIT_TESTS.xml)
record verification. Real-state CPU qualification compares native and cached
inference on synthetic residues, checks pair symmetry, and verifies all learned
parameters and GP buffers remain unchanged. It reads no benchmark pairs/truth.

The [artifact registry](../../artifacts/models/frozen_pair_models_v3/ARTIFACT_REGISTRY.json)
binds versioned release documents, code, tests and public aggregate evidence.
Living indexes point to this release separately. Model weights, sequence
identities, embeddings and pair-level predictions remain local; a Git checkout
is not a standalone arbitrary-sequence scoring service. U is unlabeled, and
direct binding, partner specificity, calibration and broad biological
generalization remain unresolved.
