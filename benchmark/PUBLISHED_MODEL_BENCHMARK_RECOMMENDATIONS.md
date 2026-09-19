# Published PPI models for an iPIN-OpenPPI manuscript benchmark

Prepared: 12 September 2026. Revised to include the requested original-versus-retrained comparison and authorize starting TUnA. This document is the plan; actual execution status/results belong in each candidate's report.

Scope: a new comparison on the existing iPIN-OpenPPI dataset, preserving its positive–unlabeled (PU) interpretation and generalization philosophy. Implementation starts with TUnA. All new files, scripts, model/data downloads, configurations, logs, results, and containers must remain under `benchmark/`. Existing repository inputs, frozen models, historical protocols, and ledgers remain read-only.

Hardware and execution assumptions incorporate your clarification: the current Arrhenius session exposes one GPU; additional jobs can be submitted to separate nodes with four GPUs per node. **GPU evaluation is allowed for the proposed benchmark.** The historical CPU-only evaluation restriction is not a requirement of this proposal. Existing historical protocol files remain unchanged.

## 0. Binding comparison and workspace requirements

For every candidate, compare **the authors' original released model** and **a separately identified model retrained on iPIN TRAIN** with both frozen iPIN models on the identical C1, C2, and C3 test panels. “Original” means the published/released weights and predictor, not a fresh model trained using the original objective. Pin the original checkpoint before examining its test performance. Do not silently choose among authors' checkpoints by test score.

| Required predictor row | C1 test | C2 test | C3 test |
| --- | --- | --- | --- |
| Candidate: authors' original released predictor | Required | Required | Required |
| Candidate: retrained on iPIN TRAIN, development-selected | Required | Required | Required |
| Frozen iPIN baseline ensemble | Required | Required | Required |
| Frozen optimized iPIN ensemble | Required | Required | Required |

Report paired differences for both candidate versions against both iPIN references, original-versus-retrained differences, coverage, and the same design-weighted PU metric. C3 remains the prespecified primary inference; C1/C2 are mandatory reported comparisons, not optional omissions. The three requested cells contain 3,019,012 rows in total. The six historical source-exclusive cells are optional additional diagnostics for this new study, not prerequisites for completing the requested C1/C2/C3 comparison.

The original model may have seen overlapping human interactions through external training; disclose/audit that exposure without excluding it from the requested descriptive comparison. Retrained results have a different evidence role. Keep original-checkpoint evaluation separate from the optional native-objective-versus-PU-objective retraining sensitivity in Section 6. Original single-checkpoint models stay single-checkpoint models; do not invent an authors' ensemble. Report retrained members as well as their predefined ensemble.

Each candidate has its own directory: `tuna/`, `dscript/`, `plm_interact/`, `rapppid/`, `sprint/`, `topsy_turvy/`, `tt3d/`, `ppitrans/`, `pipr/`, `pplm/`, and `mint/`. New per-candidate SIF images and build files go in **`benchmark/containers/`**. This is the containers folder for the new work, keeping the repository's existing `containers/` untouched. Reuse an existing read-only SIF only when documented dependency and numerical checks establish that it is sufficient; otherwise build a dedicated candidate image. Keep caches and temporary job/build outputs inside `benchmark/` as well.

If an original checkpoint is unavailable, report the missing original result explicitly. For a nonparametric algorithm such as SPRINT, explain that neural-checkpoint retraining is not applicable rather than fabricating two learned models. Start TUnA first; other candidate directories are organizational preparation, not authorization to run every model simultaneously.

Execution update: TUnA has a dedicated ARM64 SIF, a verified full-length residue cache, qualified GPU inference/evaluation, and three-seed retraining in progress. The final comparison is queued after successful training. See [TUnA startup report](tuna/REPORT.md). Other candidate folders are prepared; their candidate-specific images and runs remain pending, to be qualified as each candidate is started.

## 1. Recommendation in brief

Yes: retraining selected published models would materially strengthen the manuscript. The useful question is whether more elaborate sequence-interaction models improve ranking under the same evidence, split, and sampling rules—not whether their published scores exceed ours on unrelated datasets.

My recommended order is:

1. **TUnA:** first priority. Its published ESM-2 150M residue representation makes it a particularly informative comparison with the current pooled ESM-2 150M models.
2. **D-SCRIPT:** an established, structurally motivated residue-pair model, representing a different way to combine sequences.
3. **PLM-interact:** the important recent joint-sequence alternative. Pilot the supported 35M configuration, then include the paper's 650M configuration if measured training and full-panel inference costs are acceptable.
4. **RAPPPID:** a useful complementary model trained without a pretrained protein language model. It helps separate the benefit of the benchmark/training formulation from reliance on large pretrained representations.
5. **SPRINT:** a published sequence-similarity control. It is not a deep-learning retraining experiment, but a strong inexpensive reference is scientifically valuable.

The model descriptions and primary sources are in Section 4. Keep both existing frozen iPIN models and the existing shortcut controls in the comparison. Do not replace the original baseline with a newly tuned version under the same name.

For a constrained first release, use TUnA, D-SCRIPT, RAPPPID, and SPRINT. For the preferred manuscript package, add PLM-interact, ideally 650M as well as the smaller feasibility variant. Treat PPLM and MINT as an optional, separately labeled interaction-pretraining track until their exposure to this benchmark's interactions and protein components has been audited.

The strongest manuscript story could be any of the following:

- A compact pooled model remains competitive after sophisticated models receive fair retraining and tuning.
- Residue-level or joint-sequence modeling provides a reproducible gain under the same PU evaluation.
- Performance differences shrink or change substantially under controlled splits, sampling, and training objectives.

All three are useful outcomes. A large list of models is less valuable than a small, defensible comparison that explains why the results differ.

## 2. What “the same philosophy” should mean here

The following are facts from the current repository, not assumptions imported from other PPI benchmarks. Sources: [frozen model definition](../docs/models/FROZEN_PAIR_MODELS_v1.md), [optimization protocol](../docs/protocols/MODEL_OPTIMIZATION_v1.md), [original evaluation protocol](../docs/protocols/PROTECTED_FINAL_TEST_v1.md), and [disclosed follow-up protocol](../docs/protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md).

| Dimension | Current benchmark and recommended treatment |
| --- | --- |
| Target | Rank released-positive pairs above sampled unlabeled alternatives. U does not mean experimentally established noninteraction. |
| Training data | 16,799 positive pairs and 2,000,000 sampled U pairs in the existing optimization protocol. Preserve the original sampling/design weights. |
| Generalization | C3 is primary; both endpoints are interaction-training-naïve under the frozen split. C2 and C1 remain secondary. Keep the actual component assignments; do not rebuild a superficially similar split. |
| Primary test panel | C3 has 2,379 positives and 1,000,000 sampled U pairs. |
| Other panels | C2 has 13,446 positives; C1 has 3,187. Preserve the six source-exclusive HI-II-14/HuRI cells as separate diagnostics. All nine cells together contain 9,028,821 candidate rows. |
| Estimand | Tie-aware, design-weighted P-versus-U concordance; not biological precision or calibrated binding probability. |
| Uncertainty | The existing 2,000-draw paired, two-endpoint component bootstrap, with the same weights and draws across models. |
| Inputs | Frozen sequence identities and release snapshot. Normalization and other fitted preprocessing use training data only. |
| Prediction unit | A prospectively defined predictor, including preprocessing, checkpoint, score transformation, order handling, and ensemble. |

These invariants do not imply identical architectures, identical optimizers, or forcing every published model to consume pooled vectors. Those choices would often remove the feature that makes the comparator interesting.

### The two existing reference models

| Frozen reference | Exact ID | C3 test concordance |
| --- | --- | ---: |
| Optimized residual-head ensemble | `esm2_150m__residual_wide__epoch04_ensemble3` | 0.807948 |
| Original affine-head ensemble | `lightweight_esm2_150m_linear__linear_lr3e-4` | 0.789249 |

Their observed difference is +0.018699, with paired 95% interval [−0.001358, +0.050000]. Thus the current primary C3 result does not establish superiority of the optimized model over the original baseline. This is context for planning, not a prediction of how published comparators will perform. Both use frozen ESM-2 150M, training-standardized pooled representations, symmetric pair features, and three-member raw-score ensembles. [Frozen model definition](../docs/models/FROZEN_PAIR_MODELS_v1.md).

Do not refresh benchmark sequences from today's UniProt records. The recent `example/` panel is an application to user-selected pairs, not a replacement training/evaluation dataset. Preserve the benchmark's existing accession/isoform mapping and sequence hashes; new UniProt releases would define a separate experiment.

## 3. Why the comparison needs more than retraining a classifier

Published PPI performance can depend heavily on the way pairs, proteins, and sequence similarities are distributed between training and test. Bernett and colleagues demonstrated substantial effects from leakage, similarity, and degree-related information. Their results motivate retaining simple controls and auditing the split—not assuming a more sophisticated model must generalize better. [Bernett et al., 2024](https://doi.org/10.1093/bib/bbae076).

There are at least four distinct exposure questions:

1. Did the same unordered pair occur in supervised interaction training?
2. Did either endpoint, or a related component, occur in interaction training?
3. Did the underlying encoder see the endpoint sequence during pretraining?
4. Did a supposedly general pretrained encoder learn from known interacting pairs, complexes, or interaction-derived features?

The current C3 split addresses a defined interaction-training generalization problem; it does not establish absence from PLM pretraining. A 2026 study specifically reports downstream PPI score inflation from pretrained-language-model exposure, using strict versus non-strict pretraining comparisons. Consequently, matched-encoder experiments and a non-PLM comparator are especially helpful. This does not make all sequence pretraining equivalent to direct exposure to the test interaction labels. [Szymborski and Emad, 2026](https://www.nature.com/articles/s42256-025-01176-7).

For each comparator, publish an exposure record: base encoder and revision, sequence-pretraining source, any structure supervision, any interaction-pair pretraining, and downstream interaction-training sources. Label unavailable overlap information as unknown, not clean.

Retraining a head cannot erase interaction information already present in an interaction-pretrained encoder. Conversely, retraining every foundation model from random initialization would be a different and much larger project. The practical solution is separate comparison tracks and appropriately bounded claims.

## 4. Candidate models and priorities

Feasibility ratings below are engineering judgments for this dataset and hardware, not measured runtimes or rankings of expected accuracy.

| Model and publication | What it contributes | Proposed role | Main feasibility issue |
| --- | --- | --- | --- |
| **TUnA**, Briefings in Bioinformatics, 2024 | ESM-2 150M residue embeddings, intra-/interprotein transformers, spectral normalization and a last-layer GP. [Paper](https://doi.org/10.1093/bib/bbae359); [official code](https://github.com/Wang-lab-UCSD/TUnA). | Highest-priority sophisticated comparator; strong matched-encoder opportunity. | Medium: length handling, residue storage, and defining GP behavior after PU adaptation. |
| **D-SCRIPT**, Cell Systems, 2021 | Residue-pair/contact-map-inspired sequence scoring using Bepler–Berger embeddings. [Paper](https://doi.org/10.1016/j.cels.2021.08.010); [official code](https://github.com/samsledje/D-SCRIPT). | Core, established alternative to pooled pair features. | Medium: large residue embeddings and pairwise contact computations. |
| **PLM-interact**, Nature Communications, 2025 | Jointly encodes the two sequences with an adapted ESM-2 model; trains interaction classification with masked-language modeling. Paper results emphasize 650M; a 35M variant is also provided. [Paper](https://www.nature.com/articles/s41467-025-64512-w); [official code](https://github.com/liudan111/PLM-interact). | Preferred recent comparator, conditional on throughput/coverage pilot. | High: per-pair encoder execution, finetuning, and long combined sequences. |
| **RAPPPID**, Bioinformatics, 2022 | Regularized twin AWD-LSTM sequence model, designed with unseen-protein generalization in mind. [Paper](https://doi.org/10.1093/bioinformatics/btac429); [official code](https://github.com/jszym/rapppid). | Core complementary non-PLM model. | Medium: older software stack and from-scratch training on relatively few distinct positives. |
| **SPRINT**, BMC Bioinformatics, 2017 | Sequence-substring similarity combined with the training interaction graph. [Paper](https://doi.org/10.1186/s12859-017-1871-x); [official code](https://github.com/lucian-ilie/SPRINT). | Recommended published non-neural control. | Low–medium: exact-sequence similarity preprocessing and ARM64 compilation. |
| **Topsy-Turvy**, Bioinformatics, 2022 | Adds training-network information to D-SCRIPT-style learning. [Paper](https://doi.org/10.1093/bioinformatics/btac258); [implementation](https://github.com/samsledje/D-SCRIPT). | Useful extension after D-SCRIPT, not essential to the first package. | Medium: graph-derived supervision must use only TRAIN edges and remain a declared auxiliary objective. |
| **TT3D**, Bioinformatics, 2023 | Adds structure-derived Foldseek 3Di input to Topsy-Turvy. [Paper](https://doi.org/10.1093/bioinformatics/btad663); [implementation](https://github.com/samsledje/D-SCRIPT). | Optional sequence-plus-structure track. | Medium–high: structure/version coverage, mapping, confidence, and preprocessing. Not the same input-information budget. |
| **PPITrans**, 2024 | Transformer-based PPI predictor with a ProtT5-embedding configuration. [Official paper/code repository](https://github.com/LtECoD/PPITrans). | Reserve comparator if another frozen-embedding transformer is needed. | Medium: another encoder/cache and adapter; lower incremental value after TUnA. |
| **PIPR**, ISMB/Bioinformatics, 2019 | Siamese residual recurrent-convolutional sequence model. [Official paper/code repository](https://github.com/muhaochen/seq_ppi). | Historical supplement or reviewer-requested addition. | Medium–high integration effort for a legacy stack; RAPPPID is my first choice for this broad comparison role. |

### Recent interaction-pretrained models: important, but a separate question

**PPLM / PPLM-PPI**, Nature Communications, March 2026, is a genuine recent candidate. Its encoder was initialized from ESM-2 650M and trained on more than 3.3 million sequence pairs derived from PDB complexes and STRING. Rebuilding this stage after benchmark-aware filtering is substantially more work than fitting a new PPI head; the paper describes four A100 GPUs and 50,000 training steps. Recommendation: initially consider a clearly marked external-interaction-pretraining comparison, with an overlap audit. Do not call a reset-head experiment TRAIN-only. [Paper](https://www.nature.com/articles/s41467-026-70457-5); [author-hosted paper](https://zhanggroup.org/papers/2026_4.pdf).

**MINT**, Nature Communications, January 2026, learns interaction-aware representations from a reported 96 million STRING PPIs. Its official repository provides a binary-PPI head and finetuning tools. It is relevant to the modern-model landscape, but shares the interaction-pretraining concern. Recommendation: optional external-pretraining track, not a prerequisite for a clean first manuscript benchmark. [Paper](https://www.nature.com/articles/s41467-025-67971-3); [official code](https://github.com/VarunUllanat/mint).

Structural-complex predictors and paired-MSA/contact methods should not be added simply because they are sophisticated. They consume different information and address different tasks. They may support a small mechanistic follow-up, but their feasibility and interpretation should not delay the primary pair-ranking comparison.

## 5. Model-specific adaptation and reproducibility traps

### TUnA

The published input is an `L × 640` ESM-2 150M residue matrix, not the current `640`-dimensional pooled vector. Its GP produces a mean and variance used in a mean-field score adjustment. Keep the complete prediction definition explicit; removing this adjustment is an ablation, not automatically the original TUnA predictor. [Methods](https://escholarship.org/content/qt9q42r5vh/qt9q42r5vh.pdf).

The manuscript repository now links to a refactored TUnA-R implementation but distinguishes that from the exact manuscript code. The original Bernett configuration includes length-limited input paths and a 512-length configuration setting. Audit the actual preprocessing, padding, and cropping behavior before adopting either implementation. Pin a commit and establish numerical agreement on public fixtures if using the refactor. [Repository](https://github.com/Wang-lab-UCSD/TUnA); [configuration](https://github.com/Wang-lab-UCSD/TUnA/blob/main/results/bernett/TUnA/config.yaml).

For TUnA-PU, explicitly define training-only GP covariance construction, including how weighted/cycled examples contribute. The original binary-logistic covariance calculation is not automatically a valid uncertainty model for a PU-ranking loss. Report its uncertainty output as exploratory unless separately validated for the intended target. Never update covariance on development/test candidates during scoring. [Implementation](https://github.com/Wang-lab-UCSD/TUnA/blob/main/results/bernett/TUnA/model.py).

### D-SCRIPT

The upstream training code defaults to 6,165-dimensional residue embeddings projected to 100 dimensions. Its loss combines binary cross-entropy with a contact-map magnitude penalty; Topsy-Turvy optionally adds graph-derived supervision. There is more to preserve than the final classifier. [Training implementation](https://github.com/samsledje/D-SCRIPT/blob/main/dscript/commands/train.py).

For D-SCRIPT-PU, replace the supervised classification term with the common ranking term and retain a documented, development-selected contact regularizer. Reassess its coefficient because the loss scale changes. A separate ESM-2-input version is useful for a representation-matched ablation, but label it as a modified D-SCRIPT variant. Also record the native encoder's structure-informed pretraining; sequence-only inference does not imply sequence-only pretraining. [Official embedding documentation](https://d-script.readthedocs.io/en/main/api.html).

Some upstream versions call the validation argument `--test`. That name is not permission to expose this benchmark's final test during training. Use released development data only. Do not accidentally select a pretrained human/Topsy-Turvy checkpoint via a default model name. [Training code](https://github.com/samsledje/D-SCRIPT/blob/main/dscript/commands/train.py); [usage documentation](https://d-script.readthedocs.io/en/main/usage.html).

### PLM-interact

Start from the general ESM-2 checkpoint, with fresh interaction-specific parameters—not the authors' human-PPI-trained checkpoint. Unlike fixed independent-protein embeddings, pair-conditioned representations cannot generally be cached once per protein. The paper also reports restricting part of its training data by combined sequence length; reproducing that filtering silently would violate the intended common-data comparison. [Paper](https://www.nature.com/articles/s41467-025-64512-w).

Inspect the executable objective rather than copying an ambiguous “1:10” description: the supplied training command sets `weight_loss_mlm=1` and `weight_loss_class=10`, and the classification implementation additionally uses positive-class weight 10. Neither that class weight nor that loss balance should be blindly transplanted to this weighted PU dataset. [Training command](https://github.com/liudan111/PLM-interact/blob/main/PLMinteract/script/slurm.sh); [loss implementation](https://github.com/liudan111/PLM-interact/blob/main/PLMinteract/train_mlm.py).

Pilot supported 35M first; do not imply its result represents the paper's 650M model. A 150M implementation would be an additional adaptation, not the default published configuration. Preserve/document MLM as an auxiliary objective in the faithful variant; a PU-only or parameter-efficient finetuning variant needs its own name and comparison row.

### RAPPPID

For the retrained RAPPPID row, train the sequence encoder and pair head from newly initialized parameters. Fit its SentencePiece tokenizer using only permitted training sequences for the strict no-external-pretraining comparator. Retain the method's regularization rather than replacing its recurrent encoder with a generic small network. Its independent endpoint encoder offers a useful inference optimization: after training is frozen, cache per-protein representations and then score pairs with the head. Verify this is algebraically equivalent to the unmodified inference path. The original-checkpoint row retains the authors' own tokenizer and trained parameters. [Paper](https://doi.org/10.1093/bioinformatics/btac429).

The official environment includes older PyTorch Lightning/dependency pins. An ARM64-compatible port needs qualification, not an assumption that the existing model SIF can run it unchanged. [Repository](https://github.com/jszym/rapppid); [requirements](https://github.com/jszym/rapppid/blob/main/requirements.txt).

### SPRINT

Supply only the original TRAIN-positive graph. Recompute similarities for the frozen sequence snapshot rather than using a downloaded precomputed human proteome with different sequence identities. Its C++/OpenMP implementation is a CPU-appropriate control even though GPU evaluation is allowed for other models. Benchmark preprocessing separately from pair scoring. Its `test_negative` input naming does not change U into a biological negative. [Official code and interface](https://github.com/lucian-ilie/SPRINT).

## 6. Separate original predictors from retraining-objective experiments

### Required original-predictor track

Evaluate each pinned authors' original predictor without interaction retraining on iPIN, using the frozen sequence snapshot and full C1/C2/C3 candidates. Record any necessary runtime/long-sequence adaptation, retain its native score definition where possible, and qualify equivalence to upstream code. If equivalence cannot be established, label the adaptation instead of claiming an exact reproduction. This original-predictor row is mandatory when an original model is available, independently of the three retraining/information tracks below.

### Track A — common-data, common-PU-objective comparison

This should be the main analysis: native published architectures where possible, trained with the original TRAIN pairs and the common weighted ranking target. Use names such as `TUnA-PU` and `D-SCRIPT-PU`, so adaptation is visible.

The existing optimization loss is:

```text
loss = mean[(w_U / mean_training_w_U) × softplus(s_U − s_P)]
```

Here a training-positive pair is paired with a training-U pair; these are two separate pair-scoring inputs. Preserve the original positive cycling/permutation and U-weight conventions for the directly matched training schedule. Auxiliary terms must be declared separately. This is a surrogate for the observed P-versus-U ranking problem; it does not, by itself, identify the latent positive–negative risk or the true prevalence of binding.

Default to the full frozen training-U set. If joint-encoder compute requires fewer optimization steps, state the exact exposure budget. If a smaller U sample becomes necessary, define a separate, predeclared reduced-budget experiment, account for the additional sampling probabilities, and train matched reference models on that same regime. Do not silently train one comparator on easy or fewer U pairs and call it the identical experiment. Existing frozen reference rows remain unchanged.

### Track B — native-objective sensitivity

For the principal sophisticated models, also test the original supervised objective on the same permitted training data, preserving necessary architecture-specific auxiliary losses. U may be encoded as zero for this computational surrogate, but is still scientifically unlabeled.

Document changes required by the dataset's class ratio/design: sampling, positive-class weighting, loss normalization, and auxiliary coefficients. Distinguish a class-weight-adapted native-objective implementation from an exact original-recipe run. Select hyperparameters/checkpoints on the same weighted C3 development metric, not on a competing test-driven objective.

This answers an important reviewer question: does the outcome reflect the architecture, or our change to its training objective? The strongest compact design is a two-column native-objective versus PU-objective comparison for TUnA and D-SCRIPT, extended to PLM-interact when feasible. Run both objectives regardless of which appears favorable during early development; do not add a fidelity check only after a comparator loses.

### Track C — extra information and external pretraining

Keep interaction-pretrained PPLM/MINT and structure-input TT3D results in a separately labeled panel. Audit exact-pair, endpoint/component, and source overlap where provenance permits. An unauditable checkpoint can still be discussed as an off-the-shelf system, but not as clean evidence of the same interaction-training generalization.

Native-backbone comparison measures complete systems. A smaller matched-backbone analysis—especially TUnA versus the current ESM-2 150M models—more directly examines the value of residue-level interaction modeling. Neither should be mislabeled as a pure architecture experiment if the optimizer, preprocessing, or data exposure also differs.

## 7. Training selection, scoring, and statistics

### Fair development effort

- Use a small, prospectively declared search per family, beginning with the published configuration and a few justified alternatives. Allocate comparable tuning opportunity, and record total trials and compute; equal learning rates or equal epoch counts are not inherently fair across these models.
- Keep optimizer and regularization choices appropriate to each model. Do not impose the old two-GPU-hour small-head search cap on end-to-end PLM finetuning; it was a budget for a different experiment.
- A practical design is one-seed screening followed by the same three fixed seeds, `20260803`, `20260817`, and `20260831`, for the selected recipe of each included family. Predeclare checkpoint-evaluation occasions and tie-breaking rules.
- Select each family's recipe/checkpoint on released development data. Include all planned successfully qualified comparators in the report, not just models that beat an internal baseline in development. Report failed/incomplete training explicitly.
- Do not refit on development after selection when claiming the same original training protocol. Any train-plus-development refit would require its own comparison and version.

### Define a symmetric ensemble score

For models without guaranteed exchange symmetry, a straightforward final predictor is:

```text
member_score(A, B) = [raw_score(A, B) + raw_score(B, A)] / 2
ensemble_score(A, B) = mean(member_score over the three fixed seeds)
```

Use the native symmetric path directly when it has been verified. Order averaging is an explicit adaptation and can double pair-dependent inference cost; train with a declared order policy too. Pre-sigmoid scores are usually preferable where available. For a GP-adjusted predictor, specify whether the raw score is the adjusted or unadjusted logit; those are different predictors. Do not invert saturated probabilities to manufacture logits.

Average predictions, not per-seed concordances. Do not drop an unfavorable seed or tune ensemble weights on test. Individual members are stability diagnostics; there is no requirement that every member separately outperform its counterpart for the fixed ensemble to be evaluated.

### Preserve the metric and paired uncertainty

For one cell, the target is the weighted proportion of P–U comparisons in which the positive scores higher, with half credit for exact ties:

```text
C_PU = sum[p in P, u in U] w_u × (I[s_p > s_u] + 0.5 I[s_p = s_u])
       / (|P| × sum[u in U] w_u)
```

Use sorting/cumulative-weight implementations; do not materialize the enormous P-by-U comparison matrix. Reuse the validated metric implementation where possible. Keep the 2,000 shared `local_domain_union_30` component-bootstrap draws: multiply distinct-endpoint-component multiplicities, but apply a same-component multiplicity once. Resample both P and U contributions, retain rational design weights, report finite draws, and suppress inferential conclusions below the existing 1,900-finite-draw requirement. [Existing evaluation definition](../docs/protocols/PROTECTED_FINAL_TEST_v1.md).

Report each score and paired difference against the frozen optimized reference, with the original baseline retained for context. These intervals condition on fitted predictors; they are not estimates of uncertainty over all possible retraining runs. Three seeds do not fix that distinction.

My suggested single primary contrast is **optimized iPIN minus TUnA-PU on C3**, declared before new development runs because of the matched encoder and scientific relevance. Other published models, native-objective comparisons, C2/C1, and source cells can be planned secondary analyses. If claiming superiority across a family of comparisons, specify an appropriate family-level testing strategy in advance. Marginal intervals must not be presented as simultaneous evidence that a selected best-looking result is significant. Nonsignificance does not establish equivalence; an equivalence claim would need a justified, prespecified margin and suitable inference.

Do not substitute accuracy, F1, ordinary negative-label AUPRC, or a favorable source cell for the primary PU result. Optional P-versus-U retrieval summaries must be explicitly defined for their sampled/weighted population; they are not biological precision. A million sampled U rows do not establish exact top-K recall over the entire proteome-wide universe.

## 8. Feasibility on Arrhenius: memory is only half the question

### Available execution modes

A read-only check in this session reported `aarch64` and a GH200 device named `NVIDIA GH200 120GB`, with 97,871 MiB reported total memory. That is an observation of this session, not a guaranteed future free-memory allocation. Your four-GPU-node clarification means the plan is not restricted to serial work on this device.

Use the current single GPU for import checks, numerical fixtures, embedding pilots, and representative forward/backward timing. Use scheduled four-GPU nodes for:

- Three independent final seeds in parallel, when each fits on one GPU; the fourth can process another scheduled independent task.
- Distributed data-parallel training of one expensive joint model where throughput benefits justify it; this does not automatically solve a single-example memory problem.
- Deterministic candidate sharding during frozen inference, merging by candidate identity with exact coverage checks.

Prefer independent-seed parallelism first when practical: it avoids some distributed-training complexity. Measure DDP scaling separately before assuming a fourfold improvement. Queue time, shared I/O, memory bandwidth, synchronization, and node allocation granularity affect elapsed time and charged resources.

### Residue caches versus pooled caches

The existing 17,000-by-640 FP32 pooled matrix is approximately 43.5 MB of raw array data. It cannot be expanded back into residue embeddings. Residue storage scales as:

```text
raw_cache_bytes = sum(sequence_lengths) × embedding_dimension × bytes_per_value
```

For illustration only, assuming 17,000 proteins averaging 500 residues:

| Representation | Raw FP32 storage, decimal GB |
| --- | ---: |
| 640-dimensional residues | 21.76 |
| 1,280-dimensional residues | 43.52 |
| 6,165-dimensional residues | 209.61 |

These are arithmetic examples, not measured sequence statistics or full working-set estimates. Measure actual total residues, longest proteins, pair-length distributions, cache overhead, and loader throughput before reserving storage. FP16/BF16 storage can reduce cache size but changes numerical behavior; qualify it rather than silently changing a frozen representation.

### The million-U inference bill

One complete nine-cell pass contains 9,028,821 candidate rows. Three seeds imply 27,086,463 member-pair evaluations before order averaging. If both orders are required, this becomes 54,172,926. These counts assume no cross-cell duplicate reuse and no additional window combinations.

Let `q` be measured one-GPU throughput in individual member-pair evaluations per second, including representative sequence lengths and data loading. Then:

```text
aggregate_GPU_hours ≈ number_of_member_pair_evaluations / (q × 3600)
ideal_four_GPU_wall_hours ≈ aggregate_GPU_hours / 4
```

| Hypothetical q | C3 only, 3 seeds, one order: GPU-hours | All 9 cells, 3 seeds, one order: GPU-hours | All 9 cells, 3 seeds, both orders: GPU-hours | Ideal 4-GPU wall hours for last column |
| ---: | ---: | ---: | ---: | ---: |
| 10/s | 83.53 | 752.40 | 1,504.80 | 376.20 |
| 100/s | 8.35 | 75.24 | 150.48 | 37.62 |
| 1,000/s | 0.84 | 7.52 | 15.05 | 3.76 |

These are planning scenarios, not performance estimates for a named model. They exclude training, development scoring, embedding generation, bootstrap/validation, and scheduler overhead. Per-protein caching can dramatically change the work for independently encoded models; joint encoders retain substantial per-pair work. Actual multi-GPU utilization can be lower than the ideal column.

Training also scales with the ranking formulation. One epoch over 2,000,000 U comparisons requires approximately 4,000,000 pair-score evaluations, plus backward computation. Eight epochs and three seeds imply 96,000,000 training pair-score evaluations before extra MLM passes, order augmentation, or repeated development evaluation. An epoch schedule sensible for tiny frozen heads is not automatically sensible for an end-to-end 650M pair encoder.

### Long proteins and coverage

Never let an upstream loader silently exclude, clip, or mis-pad long proteins. Before formal fitting, define maximum supported length, residue-window extraction, pair-window aggregation, padding masks, and treatment of nonstandard residues. Windowing a pair encoder is a modified predictor, not guaranteed equivalent to a full-context model.

Preferred outcome: every main-table model returns finite scores for the complete original candidate panel under a predeclared policy. If a model genuinely cannot do so, report failure/coverage and place any restricted evaluation in a separate shared-eligibility analysis: all compared models must be evaluated on exactly that same prespecified subset, with its weights and changed estimand stated. Do not compare a model's short-protein subset score with another model's full-panel score, and never fill failed predictions with zero.

## 9. GPU evaluation policy for this new benchmark

Your clarification removes CPU-only scoring as a proposed benchmark requirement. GPU inference is allowed on the current allocation and on submitted Arrhenius jobs. CPU remains useful for controls, validation, or metric calculation when that is more efficient; no model must be ported to CPU merely to enter the new comparison.

The protection that matters scientifically is separation of model development, candidate-only scoring, and truth-based evaluation—not the processor type:

1. Freeze model weights, code, tokenizer, preprocessing, score/order rules, numerical settings, and image checksums before final candidate scoring.
2. Provide the GPU scorer only the permitted candidate projection and frozen sequence/features; no interaction truth, truth keys, or training-time access to final-test packages.
3. Disable training behavior and all test-dependent state updates, including batch-normalization statistics or GP covariance fitting. No online sequence/model downloads during final scoring.
4. Shard candidates deterministically across devices if desired. Validate unique identities, row completeness, finite scores, order handling, and stable results across batch/shard assignments before freezing predictions.
5. Perform the planned bundled metric comparison after all model predictions are frozen. Keep keys, candidate-level outputs, and private logs out of publication artifacts.

CUDA may need device mounts and runtime facilities disallowed by the old CPU guard. Qualify a GPU-compatible launcher explicitly; do not relabel the old seccomp setup as GPU-qualified without testing it. Preserve least-privilege mounts, restricted network access, and scorer/truth separation as far as the approved HPC execution environment supports them, documenting actual guarantees.

For new models, BF16 training/inference or other acceleration can be considered after public/development-fixture qualification. Declare precision, TF32 settings, deterministic-kernel policy, and justified numerical tolerances before final scoring. The two existing frozen references retain their original prediction definitions and cached predictions; permission to use a GPU does not authorize changing those reference scores.

This report records the proposed GPU-enabled procedure and your instruction. It does not modify, reset, or reuse historical one-shot ledgers or rewrite the original CPU-only protocols. Future execution should have a separately versioned benchmark record linking to that historical evidence.

## 10. Reusing the existing test: valid follow-up, clear disclosure

It is reasonable to compare these new development-selected models on the same existing test. A new independent dataset is not a prerequisite for doing this work. The existing test has already been examined, however, so this comparison must be described as a disclosed follow-up—not an untouched confirmation or independent replication. The repository already makes this distinction in its [follow-up protocol](../docs/protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md).

Before new fitting, document the candidate families, tuning budgets, score definitions, primary contrast, planned secondary analyses, and stopping rules. Before final test scoring, freeze the selected implementation/checkpoints for every included model. Report all planned outcomes, including negative, null, incomplete, and resource-limited results. Do not respond to a test loss by changing length rules, seeds, objectives, or comparators and retesting silently.

Possible manuscript wording, adjusted to what is actually executed:

> We evaluated authors' released predictors and separately retrained published sequence-based interaction architectures using the fixed iPIN-OpenPPI TRAIN partition, with development-only selection. Both versions were compared with the frozen baseline and optimized iPIN ensembles on the identical C1, C2, and C3 test panels. Our primary comparison used design-weighted positive-versus-unlabeled concordance on C3. These panels had previously been evaluated for iPIN; the new results therefore constitute a disclosed benchmark follow-up. Predictors were frozen before their test evaluation, and external training exposure of released checkpoints was reported. Unlabeled pairs were not interpreted as verified noninteractions.

An additional independent or temporal dataset could strengthen a later generalization claim, but should be presented as an optional extension with its own feasibility and exposure audit, not as a reason to postpone this comparison.

## 11. High-value scientific questions beyond a leaderboard

### A. Does residue-level modeling add useful information?

The most incisive starting comparison is current pooled ESM-2 150M scoring versus TUnA's residue-level use of the same encoder family. Align the exact encoder revision and extraction policy where possible; document remaining differences. A matched-representation D-SCRIPT adaptation is a secondary extension. This is more informative than attributing every difference between a 150M pooled model and a finetuned 650M model to architecture alone.

### B. Does the objective matter as much as the architecture?

The native-objective/PU-objective comparison in Section 6 can reveal whether methods transfer well when optimized for this dataset's scientific target. Keep the data, development selection metric, and inference coverage controlled. Avoid claiming a causal architecture advantage from this mixed set of changes.

### C. Is the score partner-specific, or largely endpoint propensity?

Retain existing degree, length, amino-acid-composition, similarity, and training-interolog controls. A training-only additive endpoint model, `s(A,B)=g(A)+g(B)`, is an especially useful additional diagnostic: it can rank pairs while lacking learned compatibility between the particular partners.

An exploratory score-only quartet diagnostic can examine `s(A,B)+s(C,D)−s(A,D)−s(C,B)`, which cancels a purely additive endpoint score. Nonzero values demonstrate nonadditive scoring, not correct biological specificity. Within-anchor ranking also needs anchor-matched alternatives, adequate positive evidence, and a separately defined estimand. Previously examined anchor/BioPlex analyses must not be presented as fresh independent validation.

### D. Where do gains occur?

Prespecify descriptive breakdowns by C3/C2/C1, source cell, sequence-length regime, and permitted training-similarity measures. Keep cell scores separate. The existing source-exclusive diagnostics are not equivalent to retraining with an entire evidence source purged. A high C1 score cannot establish unseen-protein performance, and a high aggregate concordance cannot establish direct binding or interface accuracy.

### E. What is the accuracy–cost tradeoff?

Report concordance against measured training GPU-hours, end-to-end scoring cost, memory, and sequence coverage. Include frozen-encoder parameters and embedding cost, not only trainable head parameters. A compact model can be practically attractive without a formal superiority claim; “equivalent” still requires the relevant statistical design.

Recent PRING work evaluates PPI prediction beyond isolated pairs, including network-level properties. It is useful manuscript context and potential future work, but importing its network metrics would change the present scientific target and does not convert U into verified negatives. Do not expand into whole-network reconstruction just to add another benchmark name. [PRING, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/86a4ea51ccac6c830230f281a23e74c8-Abstract-Datasets_and_Benchmarks_Track.html).

## 12. A staged implementation plan

The user has authorized starting TUnA. Other candidates remain planned. Actual run and qualification records live in the candidate directories; the recommendations below do not assert that any experiment has completed.

| Stage | Work and deliverable | Decision before proceeding |
| --- | --- | --- |
| 1. Data/interface audit | Resolve frozen train/development inputs; document native architecture/objective, encoder provenance, licenses, length behavior, and expected pair counts. | No test access; reject adapters that change labels, identities, or splits silently. |
| 2. Single-GPU qualification | Build separate compatible images; verify imports, public-fixture scores, finite gradients, tiny-training-set learning, padding/order correctness, and memory behavior. | A runnable implementation is not yet a faithful or scientifically eligible comparator. |
| 3. Throughput pilot | Time length-stratified TRAIN/development batches, full epoch projections, embedding I/O, repeated development scoring, and frozen inference. Test four-GPU scaling where appropriate. | Freeze realistic tuning/training/inference budgets and the included model/track list. |
| 4. Development-only training | Run declared searches, then final three-seed recipes; retain all attempt records and resource accounting. | Freeze each family's complete predictor using development selection only. |
| 5. GPU-enabled final comparison | Candidate-only scoring, identity/coverage audits, prediction freeze, one planned bundled metric report. | No tuning or retries motivated by test performance. |
| 6. Manuscript integration | Primary C3 paired comparison, secondary cells, objective sensitivity, cost/coverage table, and exposure/limitations statement. | Claims match the actual evidence, including failed and inconclusive comparisons. |

Planning allowance: a few engineering days for the adapter/runtime audit and roughly two to four weeks of elapsed project time for a focused core study is a reasonable initial scheduling assumption, not a delivery promise. Queue delays, dependency repairs, and measured pair-encoder throughput can dominate. Begin with a small bounded pilot allocation per model; derive production requests from its measured costs instead of declaring an unsupported universal GPU-hour estimate. Four-GPU nodes improve throughput opportunities but do not eliminate the millions-of-pairs workload.

### Suggested packages

- **Core:** both frozen iPIN references, existing controls, SPRINT, TUnA-PU, D-SCRIPT-PU, RAPPPID-PU; native-objective sensitivity for TUnA and D-SCRIPT.
- **Preferred:** core plus PLM-interact-PU 650M if it passes coverage/cost qualification, with the supported 35M variant as an explicit size/cost comparison and a native-objective check. Do not report a 35M-only result as a complete reproduction of the 650M paper.
- **Extended:** selected Topsy-Turvy/TT3D or PPLM/MINT analyses, only when they answer a specific remaining question. Keep additional-information tracks visibly separate.

Do not make inclusion depend on beating our model. Feasibility exclusions should be based on declared operational criteria before final evaluation and documented transparently.

## 13. What the manuscript and reproducibility package should contain

For each model/variant, preserve: publication and upstream commit; adapter diff; code/weight license; container digest; base-checkpoint revision; preprocessing and sequence checksums; split/sampler/weight definition; native versus adapted loss; hyperparameter trials; training exposure; seed/checkpoint selection; precision and score transformation; order/ensemble rule; length coverage; training/inference hardware and resource use; and failure status.

Upstream repositories currently identify MIT licensing for D-SCRIPT, TUnA, and PLM-interact, AGPL-3.0 for RAPPPID, and GPL-3.0 for SPRINT. PPLM's README specifies PolyForm Noncommercial. Check the exact chosen code, pretrained weights, and data licenses separately before redistribution; a public GitHub repository alone is not a complete redistribution decision. [D-SCRIPT](https://github.com/samsledje/D-SCRIPT); [TUnA license](https://github.com/Wang-lab-UCSD/TUnA/blob/main/LICENSE); [PLM-interact license](https://github.com/liudan111/PLM-interact/blob/main/LICENSE); [RAPPPID](https://github.com/jszym/rapppid); [SPRINT](https://github.com/lucian-ilie/SPRINT); [PPLM](https://github.com/junliu621/PPLM).

The main results table should include: model/variant, input/pretraining track, C3 concordance with interval, paired difference versus optimized iPIN with interval, secondary C2/C1 scores, sequence/pair coverage, and measured compute. Put full source-cell results, member diagnostics, tuning history, and numerical qualification in supplementary material. Do not combine incompatible full-panel and length-restricted scores into one ranked column.

Two particularly useful figures would be a C3 paired-difference forest plot and a concordance-versus-scoring-cost plot. Keep source and C1/C2 results visually secondary. These answer the scientific and practical questions more directly than a heatmap of incomparable published metrics.

### Final recommendation

Start execution with TUnA first, as requested; D-SCRIPT, RAPPPID, SPRINT, and an early PLM-interact throughput/length pilot are subsequent priorities. Use the available four-GPU nodes for seed parallelism and frozen inference as appropriate. Preserve the current PU estimand and split, allow GPU evaluation, and make every training-objective or input-information change visible. That is a feasible path to a stronger manuscript without turning the comparison into an open-ended foundation-model training project.
