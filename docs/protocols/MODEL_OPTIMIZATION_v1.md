# Model optimization v1 and conditional follow-up amendment

Prospective local protocol, 2026-09-11; authority DEC-0052. Freeze this file,
the exact configuration, implementation, tests, and input hashes before formal
training. Record UTC freeze and first-fit times. Do not edit frozen scientific
rules after looking at search results; implementation failures must be exposed.

## Question and scope

Can a different small, swap-symmetric head or optimization recipe improve C3
positive-versus-unlabeled (PU) concordance over the original frozen 150M affine
three-seed ensemble? C3 is primary. C2/C1 and named-source results are descriptive
only, reported for the final winner if a follow-up test occurs. Neither these
diagnostics nor prior test/BioPlex results may determine recipes, promotion,
epoch, seeds, gate, or stopping. The development interval is a stability screen
after selection, **not a multiplicity-adjusted confirmatory significance test**.

Keep the existing train/development/test partition and all sampling weights.
Unlabeled means untested/unknown, never a negative or direct-binding label.
Preserve training-only normalization and use manifest-identity joins, not
positional assumptions, for existing frozen ESM-2 150M (640 dimensions) and
650M (1280 dimensions) vectors. Access to existing endpoint embeddings does
not constitute access to test-pair membership or outcomes. The optimization
container receives only allowlisted code/configuration and prepared training
and released-development arrays; no test package, keys, predictions, or ledger.

## Fixed search and compute

`configs/model_optimization_v1.json` enumerates twelve recipes crossed with two
encoders: 24 total, four families. No added recipes or encoder fine-tuning.
All use commutative sum, absolute difference, product and exact cosine features.
Linear is affine; MLP uses feature LayerNorm, one GELU hidden layer and dropout;
residual MLP adds an independent affine branch; bilinear adds a learned shared
rank-32/128 projection product with signed output weights to an affine branch.
All models start from newly seeded parameters, not test-informed checkpoints.

Use CUDA on the pinned ARM64 model SIF; fail if unavailable. FP32 parameters
and activations, no AMP or TF32, deterministic PyTorch algorithms, Xavier
linear initialization, zero biases, AdamW (0.9, 0.999), epsilon 1e-8,
gradient-norm clipping 1.0. Batch size 8192 comparisons. Every epoch visits all
2,000,000 training U pairs once, in a PCG64DXSM permutation keyed by seed and
epoch; a separately permuted set of 16,799 P pairs cycles across comparisons.
No row resampling, new labels, or training on development. Optimize
`mean((w_U / mean_training_w_U) * softplus(-(s_P - s_U)))` with FP64 weighted
reduction. Linear 5% warm-up then cosine learning-rate decay to 10% of peak;
each stage has its own declared horizon. This differs from the original
five-pass schedule and is therefore an architecture **and training-recipe**
comparison, not a pure architecture ablation.

Stage 1: every recipe, seed 20260803, three epochs; score full C3 development
only at epoch 3. Promote the four largest concordances; exact ties prefer fewer
parameters, then lexical recipe ID. No family quota. Stage 2: each promoted
recipe trained anew for eight epochs using seeds 20260803, 20260817, 20260831.
Evaluate only epochs 4 and 8. For each recipe/epoch, average its three raw FP32
scores in FP64; choose the largest ensemble concordance over these eight
groups. Exact ties prefer fewer parameters, earlier epoch, lexical recipe ID.
Do not choose a single best seed or search ensemble weights.

Cap total GPU-using optimization/evaluation process wall time at 7200 seconds
(two allocated GPU-hours), including baseline replay and development bootstrap.
Stop fitting by 6300 seconds to reserve 900 seconds for closure. The process
checks its deadline between batches and bootstrap chunks. If the fixed matrix
is incomplete, any numerical/validation failure occurs, or the deadline is
exceeded, publish incomplete status and **do not retest**. Do not select the
best available partial run or launch another search automatically. Synthetic
CPU correctness tests and documentation do not consume the search budget.

## Frozen baseline and development gate

The comparator is the original `lightweight_esm2_150m_linear__linear_lr3e-4`,
pass 05, steps 2445, seeds above; corrected development ensemble C3 is about
0.784142. Verify checkpoint and corrected development-cache hashes, replay its
GPU predictions within 1e-5 maximum score error and 1e-7 concordance error, and
use the original cached scores for exact paired comparisons. Refitted linear
recipes receive the same search procedure as other families. No baseline
checkpoint is overwritten. No new arbitrary minimum effect size.

For the one selected group, require **all**:

1. Complete valid search and finite predictions; validated input identity and
   exact swap symmetry in inference (absolute tolerance 1e-6).
2. Ensemble C3 concordance greater than the original baseline.
3. Each of its three seed concordances exceeds the corresponding original
   baseline seed, and maximum minus minimum candidate seed concordance <=0.02.
4. Lower endpoint of the paired 95% percentile interval for ensemble-minus-
   baseline C3 concordance is strictly positive, using 2000 fixed shared
   component bootstrap draws and exact design-weighted tie handling.

Use the original `20260803:bootstrap:C3_development` PCG64DXSM component-draw
rule, sampling the union of components with replacement. A pair within one
component gets that multiplicity once, otherwise the product of both endpoint
component multiplicities. Both P and U weights are affected; invalid draws
fail the gate. Report point gain, interval, every seed's performance and gain,
all attempts, total time and promotion/selection tables. If the highest-scoring
group fails, do not fall back to another group or retune.

## Conditional follow-up on the existing test

This amends the one-shot restriction **prospectively**; no new test set is
required by this authorization. Preserve all six completed study registries
(148 registered files), especially the original final-test protocol, scorer
freeze, result, receipt, private ledger and completion record. Verify their
checksums before and after. Public original result SHA-256:
`6cc8c3ba61039501b3e1b09dfcee442de8f4dfcd0c717a466b15f9e77ef3a02e`.
Original spent-ledger SHA-256:
`e23a6a8980d3e9d148a40be8e9b3d1316ff1c2c6ed8f7f03ab2bd899b777914f`.

Only a passing gate authorizes freezing exactly the selected recipe/epoch's
three checkpoint states, preprocessing, source code, and input manifests for
one additional evaluation. The follow-up namespace is
`model_optimization_followup_v1`; its exclusive, irrevocable reservation must
link to DEC-0052, the search freeze, selected-model freeze, passing gate and
the original spent ledger. The original ledger is never rewritten.

Retain staged candidate/scorer/truth access, token-identity validation, fixed
predictions before truth access, inherited offline seccomp guard, read-only
allowlisted mounts and account-private row outputs. Qualify the new model
scorer on synthetic/public or development data before accessing test pairs.
The strict original CPU isolation guard may be used for protected scoring;
GPU optimization is mandatory. Score the selected three-seed ensemble and its
three members. Compare to the original fixed baseline predictions, with
provenance/identity checked after model freezing, in the same paired bootstrap;
no selection among controls or substitution of baseline refits. Report all
nine original C3/C2/C1 and source-exclusive cells, primary paired C3 gain and
uncertainty, seed results, and failures. This is one bundled truth evaluation,
not repeated attempts by scorer or cell. Reserve before truth decryption;
failure after reservation consumes the authorization.

Disclose that the baseline test results were already known before this search.
The follow-up is not an untouched test, an independent replication, calibrated
binding prediction, or proof of partner-specific/direct-binding generalization.
No further tuning or evaluations follow this result without new user authority.
BioPlex remains frozen, secondary cross-assay evidence, not an optimization
target, selection criterion, or decisive binary-validation failure.
