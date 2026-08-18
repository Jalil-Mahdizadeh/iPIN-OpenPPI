# Model governance and baseline/training protocol v1

**Protocol ID:** `model_governance_and_baseline_training_protocol_v1`

**Configuration:** `configs/model_governance_and_baseline_training_protocol_v1.yaml`

**Authorization:** `DEC-0027`

**Frozen date:** 2026-08-18

**Execution state:** design accepted for validation only; no model execution

## 1. Purpose and authority boundary

This protocol freezes the first iPIN-OpenPPI modelling stage before any model
result exists. It is deliberately small, diagnostic, and sequence-only. It
preserves the accepted reference-sequence positive-unlabeled ranking (PU-R)
estimand and defines what a later, separately authorized implementation must do.

This document does not authorize model-weight acquisition, a model container,
embeddings, feature caches, baseline/model implementation, training,
development release, scoring, selection, or protected evaluation. Those actions
remain closed after protocol acceptance and require a new numbered decision.

The binding machine-readable detail is the configuration named above. If prose
and configuration disagree, execution must stop and return to governance; the
configuration may not be silently weakened to reconcile the mismatch.

## 2. Immutable scientific and custody boundary

The following parent state is read-only:

- 17,000 exact UniProt `2026_02` reference-sequence hashes;
- every accepted 40%/30%/20% similarity graph and component inventory;
- the 7,782-component `local_domain_union_30` split with
  11,900/2,550/2,550 training/development/protected-test endpoints;
- exact pair identity, C1/C2/C3 roles, quarantine, sampler, rational
  probabilities/weights, metrics, bootstrap, and claim rules;
- 16,799 public training positives and 2,000,000 frozen public training-U rows;
  and
- the encrypted development, protected-candidate, and protected-truth packages.

Only the public training package may support future fitting. Development stays
encrypted until every candidate training artifact is frozen and hashed and a
new decision authorizes release. Protected candidates and truth stay invisible
to model development and model selection. No private key may be read, hashed,
copied, mounted, or tested.

`Unlabeled` is an evidence state, not a negative class. A future loss may place
an unlabeled observation on the comparison side of a ranking contrast. That
operational contrast does not make the observation nonbinding, assay-negative,
pseudo-negative, or a probability target.

## 3. Frozen PLM candidates and provenance

Only two public checkpoints are admitted to the first stage.

| Role | Repository and immutable revision | Safetensors SHA-256 | Shape |
|---|---|---|---|
| Lightweight mandatory baseline | `facebook/esm2_t30_150M_UR50D` at `a695f6045e2e32885fa60af20c13cb35398ce30c` | `c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566` | 30 layers, 150M parameters, 640-dimensional residues |
| Primary frozen encoder | `facebook/esm2_t33_650M_UR50D` at `08e4846e537177426273712802403f7ba8261b6c` | `a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0` | 33 layers, 650M parameters, 1,280-dimensional residues |

Both repositories and the archived Meta ESM implementation declare the MIT
license. Only `model.safetensors` is permitted; pickle weights and remote code
are prohibited. The tokenizer, configuration, special-token map, vocabulary,
model card, and weights must come from the same immutable revision.

Primary provenance sources are the [Meta ESM repository](https://github.com/facebookresearch/esm),
the [150M model repository](https://huggingface.co/facebook/esm2_t30_150M_UR50D),
the [650M model repository](https://huggingface.co/facebook/esm2_t33_650M_UR50D),
and the [ESM-2 paper](https://www.science.org/doi/10.1126/science.ade2574).
Provider documentation describes masked-language-model pretraining on UR50/D;
a Meta maintainer identifies the underlying UniRef release as `2021_04` in
[the corpus record](https://github.com/facebookresearch/esm/discussions/667).

The available records do not provide the exact dynamic per-step sequence draw
log and this project has not audited exact or homologous membership for the
17,000 endpoints. Exact or family-level exposure is therefore unknown and
possible. Neither C3 nor any other axis is a PLM-exposure split. The project may
state that provider documentation describes sequence-only masked-language
pretraining; it may not claim that an endpoint, homolog, domain, or family was
unseen, that the checkpoint is temporally clean, or that a performance
difference is caused by pretraining exposure. The 150M/650M comparison is a
capacity/representation diagnostic, not an exposure experiment.

### 3.1 Future local custody

No model file is acquired by this protocol. A later acquisition must use the
exact revisions, stay inside
`artifacts/cache/models/model_governance_and_baseline_training_protocol_v1`,
reject links outside the project, and record bytes plus SHA-256 for every file.
After acquisition, both Hugging Face and Transformers offline modes are
mandatory. Embedding and training are no-network operations.

The future model image is named `ipin-model-arm64_0.1.0.sif`. Its recipe is
pinned to the accepted ARM64 NGC/PyTorch base and exact versions in the config,
including PyTorch `2.8.0a0+34c6371d24.nv25.08`, Transformers `4.55.2`,
Hugging Face Hub `0.34.4`, Tokenizers `0.21.4`, and Safetensors `0.6.2`.
The image does not yet exist. Its definition, dependency lock, SIF hash,
architecture/import checks, one-GPU embedding repeat, and checkpoint/restart
fixture must be independently accepted before scientific use.

## 4. Frozen embedding strategy

Both PLMs remain in evaluation mode with autograd disabled and all parameters
frozen. The exact uppercase frozen reference sequence is tokenized without
sequence replacement or truncation. BOS, EOS, and padding never enter pooling.
The final hidden layer is used: layer 30 for 150M and layer 33 for 650M.

For sequences of at most 1,022 residues, the complete sequence is one window.
Longer sequences use 1,022-residue windows with 128-residue overlap and stride
894. Starts are `0, 894, ...`; `length - 1022` is appended when it is not
already a start, guaranteeing complete C-terminal coverage. Each residue is
the arithmetic mean of its representations in all windows that cover it. The
protein vector is the arithmetic mean of those overlap-averaged residue
vectors. Forward, accumulation, and stored-vector dtype are FP32.

All 17,000 endpoint vectors may later be extracted label-blindly, but training
normalization uses only the 11,900 training-partition endpoints. Per-dimension
mean and standard deviation are computed there; standard deviations below
`1e-6` become `1e-6`. No held-out distribution statistic enters a trainable
head.

Embedding order is increasing `(sequence length, sequence SHA-256)`, with a
4,096-residue token budget per batch. Every vector is keyed by the checkpoint,
revision, tokenizer hashes, strategy, and sequence hash. Completeness,
uniqueness, finiteness, vector hashes, and a deterministic bottom-hash 1%
repeat with maximum absolute difference `1e-6` are hard gates.

No residue embedding is retained for interface prediction in this stage. The
only governed model input is the pooled protein vector.

## 5. Mandatory baseline ladder

All methods use identical frozen cell rows, weights, and tie rules. No held-out
label, held-out/full-graph degree, source, assay, publication, external panel,
or protected metadata may become a feature.

### 5.1 Frozen hash and graph/degree controls

The four definitions already frozen by `DEC-0024` remain exact:

1. normalized full-SHA-256 hash control using salt
   `ipin-openppi-pu-r-baseline-v1` and seed `20260803`;
2. endpoint degree sum, `log1p(d_a) + log1p(d_b)`;
3. preferential attachment, `log1p(d_a d_b)`; and
4. component degree-mass product, `log1p(D_ca D_cb)`.

All degrees are from the 16,799 training-positive graph. A held-out endpoint has
training degree zero. Component mass is the sum of training-positive endpoint
degrees in the frozen component. One additional C1 shortcut diagnostic is
`log1p(|N_train(a) intersect N_train(b)|)`.

### 5.2 Length and sequence-similarity controls

Two zero-parameter length scores are mandatory: log-length sum and negative
absolute log-length difference.

The deterministic sequence feature is the L2-normalized raw count of every
contiguous 3-mer over `ACDEFGHIKLMNPQRSTVWYX`; a noncanonical residue maps to
`X` for this feature only. The sequence itself is never changed. Two scores are
reported:

- cosine between the two endpoints' 3-mer vectors; and
- the exact training-interolog score

  `max_(u,v in P_train) max(min(sim(a,u),sim(b,v)), min(sim(a,v),sim(b,u)))`.

Approximate nearest-neighbor search is not permitted for this baseline.

### 5.3 Lightweight frozen-PLM pair baseline

The ESM-2 150M protein vectors feed one affine scalar head over the commutative
features `e_a + e_b`, `|e_a - e_b|`, `e_a * e_b`, and cosine. There is no
hidden layer. The frozen primary ranking loss fits only this head under the two
prespecified linear optimizer recipes.

The strongest simple sequence baseline set comprises both 3-mer controls, this
150M linear head, and the corresponding 650M linear ablation. The strongest is
chosen separately in each development cell on identical rows; test never
chooses a baseline.

## 6. Primary P-versus-U training objective

The primary future objective is design-weighted positive-versus-unlabeled
pairwise logistic ranking. It requires no class prior and produces no
probability.

Let `P` be the complete 16,799-row training-positive census and `U` the exact
2,000,000-row frozen public training-U sample. In each of five complete passes:

- every U row appears exactly once without replacement;
- P and U are independently ordered by full SHA-256 keys containing the public
  training salt, run seed, pass index, state, and pair ID;
- U row `i` is contrasted with positive
  `P[(i + pass_index - 1) mod 16,799]`, so every positive repeats either the
  floor or ceiling of `2,000,000 / 16,799` times; and
- each U observation retains its exact rational `N_h/m_h` design weight with
  no clipping or re-estimation.

For scores `s_p` and `s_u`, the comparison loss is

`softplus(-(s_p - s_u))`.

The optimized batch loss is the mean of that loss times `w_u / mean(w_U)`.
The complete-pass monitor is accumulated in FP64 as
`sum(w_u loss) / sum(w_u)`. Positive weights remain `1/1`.

BCE with U as zero, matched/random pseudo-negatives, nnPU or another
class-prior-dependent risk, calibration, source heads, and development or
protected supervision are excluded from the first stage.

## 7. Simple primary architecture and ablations

All pair heads are exactly swap-symmetric and have fewer than two million
trainable parameters; every ESM parameter remains frozen.

The primary head applies a shared `1280 -> 256` GELU projection. Partner B
gates A and A gates B through one shared affine-sigmoid map:

- `c_a = p_a * sigmoid(W_g p_b + b_g)`
- `c_b = p_b * sigmoid(W_g p_a + b_g)`.

The scalar head receives `c_a + c_b`, `|c_a - c_b|`, `c_a * c_b`, and cosine,
then applies `769 -> 128 -> 1` with exact GELU and recipe-controlled dropout.
Commutative construction—not orientation augmentation—is the symmetry proof.

Only three comparisons are scientifically necessary:

1. 150M linear: lightweight frozen-PLM baseline;
2. 650M linear: isolates encoder capacity;
3. 650M nonlinear without the partner gate: isolates nonlinear head capacity;
4. 650M partner-gated: the primary candidate.

No residue joint encoder, cross-attention, interface target, router, PLM
fine-tuning, LoRA, adapter, structure, teacher, or auxiliary head is present.

## 8. Optimization, search, checkpointing, and reproducibility

The three run seeds are `20260803`, `20260817`, and `20260831`. Python,
NumPy PCG64DXSM, Torch CPU, and every CUDA generator are seeded. Deterministic
algorithms are required; TF32 and cuDNN benchmarking are off, cuDNN
determinism is on, and `CUBLAS_WORKSPACE_CONFIG=:4096:8`.

Each batch has 4,096 P-U comparisons. AdamW uses betas `(0.9, 0.999)`, epsilon
`1e-8`, and global gradient clipping at 1.0. Five U passes give 489 steps per
pass and 2,445 steps total. A 123-step linear warmup precedes cosine decay to
10% of the initial learning rate.

Linear heads have two recipes: learning rates `3e-4` and `1e-3`, both with
weight decay `1e-4`. Nonlinear heads have exactly three recipes:

- `3e-4`, weight decay `1e-4`, dropout `0.1`;
- `1e-3`, weight decay `1e-4`, dropout `0.1`; and
- `1e-3`, weight decay `1e-5`, dropout `0`.

This is a complete, nonadaptive enumeration: 6 + 6 + 9 + 9 = 30 seed runs and
at most 300 million comparisons. Optuna, Bayesian optimization, adaptive
recipes, and extra seeds are prohibited. The first stage uses one GH200, at
most 100 GPU-hours and 100 GiB project storage; four-GPU and multi-node
training are not justified.

An atomic, hashed checkpoint is written after every complete U pass and holds
model/optimizer/scheduler state, all RNG states, data cursor and order digests,
pass/step, and every code/config/container/input/embedding hash. Five passes are
always attempted; there is no performance early stopping. The selected
training checkpoint is the lowest complete-pass monitor loss, with earliest
pass on an exact tie. Thus checkpoint choice is training-only and frozen before
development.

Nonfinite state, missing/duplicate U use, incomplete P coverage, hash drift, or
swap error above `1e-6` fails the run. One exact resume after infrastructure
failure is allowed. A second infrastructure failure or any numerical failure
marks the run failed; no replacement recipe or seed is invented.

## 9. Development release and model selection

After a separately authorized training stage, all successful runs are reduced
to their training-selected checkpoints. Each model-family/recipe candidate is
the arithmetic-mean score of its three run seeds; a seed may not be selected on
development. Model code, container, config, embeddings, inputs, checkpoints,
and ensemble definition enter one immutable training-artifact registry. The
registry SHA-256 and independent validation must precede a new development-
release decision.

Development may score only those pre-existing candidates. It may not create a
recipe, seed, architecture, embedding, feature, checkpoint, or retrained model.
All three seed runs must exist, all scores must be complete/unique/finite and
symmetric, and the within-candidate seed metric range must not exceed 0.02 in
any primary cell.

Model selection uses only HT P-versus-U concordance. Metrics are quantized to
0.001 with decimal `ROUND_HALF_UP` for selection, then compared in this exact
order: C3 development, C2 development, C1 development, lower architecture
complexity, candidate ID. C1/C2/C3 are never pooled. Novel-U and source-
exclusive diagnostics are report-only. No post-selection retraining is
permitted.

The selected scorer and all dependencies must be frozen and hashed before any
protected candidate access. Protected evaluation remains the existing
evaluator-only one-first procedure.

## 10. Metrics and reporting hierarchy

The only primary sampled-package metric is HT-weighted P-versus-U pairwise
concordance:

`sum_p,u w_u [I(s_p > s_u) + 0.5 I(s_p = s_u)] / (n_P sum_u w_u)`.

Reports lead with C3, then exclusive C2, then C1; development and protected
test remain separate. There is no pooled headline value. Every model comparison
is an absolute delta on identical rows with identical two-endpoint component-
bootstrap draws. The accepted 2,000-replicate PCG64DXSM, seed `20260803`,
percentile-95 interval remains unchanged.

Exact Recall@10/100/1000, enrichment at 0.0001/0.001/0.01, and positive rank
percentiles remain demoted until exact streaming full-candidate scoring is
separately authorized. Sampled AUROC/AUPRC and correlations with shortcuts are
diagnostic only. No result is biological classification performance,
precision, prevalence, false-positive rate, calibration, or probability.

## 11. Degree/hub analyses and C1 novel-U sensitivity

Training-positive degrees use the frozen bins `0`, `1`, `2`, `3-4`, `5-9`,
`10-19`, `20-49`, `50-99`, and `100+`. Pair strata sort the two bins. Nested
hub flags use the frozen top 1%, 5%, and 10% ranks: 119/595/1,190 endpoints,
with minimum degrees 41/14/7. A quantitative stratum needs 100 positives and 10
components; smaller strata are descriptive and never pooled to hide failure.
C2's held-out endpoint and both C3 endpoints have training degree zero.

The prespecified C1 novel-U sensitivity retains the original C1 positives and
only those frozen C1 U rows whose pair ID is absent from the frozen public
training-U pair IDs. It does not resample, add, relabel, or reweight a row. Its
metric uses the original rational weights normalized over retained rows:

`sum_p,u* w_u [I(s_p > s_u*) + 0.5 I(s_p = s_u*)] /
 (n_P sum_u* w_u)`.

This is a design-weighted Hájek ratio over the realized view, not a newly
sampled conditional candidate population. Counts removed/retained, weight
mass, nonempty strata, and uniqueness must be reported. Development use waits
for release; protected-test use is evaluator-only after prediction freeze.
The sensitivity cannot select or stop a model.

## 12. Complexity gate and model-level kill rules

The partner gate is retained only when its C3 development gain is at least
0.02 over the strongest simple sequence baseline with paired 95% interval
excluding zero, at least 0.01 over the 650M linear head with interval excluding
zero, and at least 0.005 over the matched nonlinear no-gate head with interval
excluding zero. Direction must also be positive on one supported named-source
development cell, stable across all seeds, and present outside hub strata.

Failure removes complexity in order: partner gate, nonlinear head, then 650M
scale. If no learned candidate beats deterministic controls, the learned model
line terminates. A residue/joint/routing architecture requires a later decision
and all existing blueprint oracle/efficiency gates; this protocol supplies no
interface justification.

The stage stops before protected evaluation if any of the following holds:

- integrity, custody, protected-boundary, or U-semantics violation;
- no learned candidate gains at least 0.02 on qualifying C3 over the strongest
  mandatory baseline with paired interval excluding zero;
- the best learned C3 lower confidence bound is not above 0.5;
- degree/graph/length explains C1 and there is no qualifying C2/C3 gain;
- interolog or a linear frozen-PLM head explains C3 and the complex incremental
  gain is below 0.01 or its interval includes zero;
- gain is absent outside top-10%-hub pairs;
- all candidates are unstable or fail numerically; or
- describing the gain requires an unsupported source, assay, temporal, family,
  PLM-exposure, probability, or calibration claim.

If C1 gain disappears or reverses in the novel-U view, the C1 gain claim is
withdrawn and only an independently passing C2/C3 gate can sustain the model.
If development was released before the registry hash, or any candidate was
trained/retrained after release, selection is invalid and the stage stops.

## 13. Exit condition

Protocol acceptance freezes rules only. The next possible action is a new
numbered proposal for model-container construction, checkpoint acquisition,
baseline/head implementation, and public-training-only execution under this
protocol. Silence, a code commit, available GPU time, or protocol acceptance
does not authorize that action.
