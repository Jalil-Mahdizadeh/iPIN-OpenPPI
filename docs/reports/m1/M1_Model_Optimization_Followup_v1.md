# Fixed-ensemble test follow-up v1

2026-09-11 · [DEC-0053](../../../governance/decisions/DEC-0053-authorize-fixed-ensemble-followup.md)
· [Protocol](../../protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md)
· [Full results](../../../artifacts/results/model_optimization_followup_v1/FOLLOWUP_TEST_RESULTS.json)

## Outcome

The frozen residual-MLP ensemble scored higher than the original linear ensemble
on every test cell. **Primary C3 increased from 0.789249 to 0.807948**, gain
**0.018699**, but its paired 95% interval **[−0.001358, 0.050000] includes zero**.
The point improvement is consistent with development (+0.015277); the primary
incremental benefit is not conclusive at the prespecified interval criterion.
This is not evidence of no benefit or equivalence. C2/C1 improvements are larger
and their paired intervals exclude zero, but those comparisons are secondary.

All values below are design-weighted positive-versus-unlabeled concordance,
not binary binding accuracy. C3 has neither endpoint exposed to interaction
training, C2 has one, and C1 has both, under the frozen component-based split.

| Test cell | Original baseline ensemble | Optimized ensemble | Gain | Paired 95% interval |
|---|---:|---:|---:|---|
| **C3 (primary)** | 0.789249 | **0.807948** | +0.018699 | [−0.001358, +0.050000] |
| C2 | 0.805299 | 0.851301 | +0.046002 | [+0.031561, +0.061559] |
| C1 | 0.843493 | 0.916037 | +0.072544 | [+0.063093, +0.081869] |

The optimized C3 model's own 95% interval is [0.740480, 0.852013]. The comparison
uses the **paired difference interval**, not overlap between separate intervals.

## Source and seed diagnostics

| Source-exclusive test cell | Baseline | Optimized | Gain | Paired 95% interval |
|---|---:|---:|---:|---|
| HI-II-14 C3 | 0.710625 | 0.750070 | +0.039445 | [−0.003849, +0.099104] |
| HuRI C3 | 0.794629 | 0.810999 | +0.016370 | [−0.003650, +0.047627] |
| HI-II-14 C2 | 0.800239 | 0.844007 | +0.043768 | [+0.023387, +0.074022] |
| HuRI C2 | 0.808502 | 0.853384 | +0.044882 | [+0.028629, +0.062273] |
| HI-II-14 C1 | 0.841249 | 0.919746 | +0.078497 | [+0.049782, +0.108311] |
| HuRI C1 | 0.840972 | 0.914208 | +0.073236 | [+0.058178, +0.094889] |

Both C3 source intervals also include zero; all C2/C1 source intervals are
positive. These cells overlap the corresponding overall analyses and are
descriptive, not independent replications or substitute primary endpoints.

The three candidate C3 seed scores were **0.801813, 0.792924, 0.795379**, versus
their original counterparts **0.790177, 0.787532, 0.786298**. Each increased here,
and their averaged-score ensemble reached **0.807948**, above every member.
These seed diagnostics are not promotion vetoes or evidence about the variability
of independently retrained whole ensembles. Complete member results for all
nine cells are retained in the machine-readable result.

## Scientific reading

The experiment supports continued interest in small heads over frozen PLM
representations. The C3 development gain transferred in direction and point
magnitude, while its test uncertainty remains substantial. The larger C2/C1
gains show that the revised head/training recipe particularly benefits settings
with prior interaction exposure; this does not establish partner-specific or
direct-binding generalization.

Do **not** carry forward an unqualified claim that network shortcuts dominate
the optimized model. The historical C2 degree-sum score (0.810652) and C1
preferential-attachment score (0.912831) are below its new point estimates.
However, this frozen follow-up compared against the original PLM ensemble,
**not those network controls in paired inference**. It neither proves superiority
over all shortcuts nor rules out learning protein-level interaction propensity.

Architecture and training recipe changed together. The near-tied plain MLP on
development was not tested, so there is no demonstrated residual-architecture
mechanism. Retain the original baseline and this higher-scoring tested ensemble;
do not label the latter a conclusively superior C3 replacement. BioPlex remains
unchanged, secondary cross-assay evidence, outside this comparison.

## Execution, amendment and verification

The predictor was exactly the existing 150M residual-MLP ensemble, width 256,
epoch 4, seeds 20260803/20260817/20260831; 498,053 parameters per head. Raw FP32
scores were averaged equally in FP64. No fitting, checkpoint substitution,
seed selection, ensemble-weight search, encoder inference or test tuning.

DEC-0053 is explicitly **post-development, pre-follow-up-test**. It accepts the
ensemble as the prediction unit while preserving DEC-0052's failed original
individual-seed gate byte-for-byte. The original test had already been examined;
this is a disclosed follow-up on the existing panel, not a new unseen holdout,
independent replication or independent preregistration.

The scorer was frozen at **12:17:58 UTC**, predictions at **12:25:22**, the
separate one-attempt ledger reserved at **12:26:26**, and evaluation entered at
**12:26:39**. Results completed at **12:34:50**. One bundled truth evaluation
covered **9,028,821 candidate rows**, eight scorers and nine cells. All 2,000
paired component-bootstrap draws were finite for every comparison. Original
baseline point estimates, intervals and draw metadata replayed **exactly**.
Baseline prediction files were imported byte-for-byte only after candidate
predictions were fixed. Original custody records were never reset or rewritten.

Pre-access replay on the actual **GH200 GPU** exactly matched all cached C3
development scores. CPU replay differed by at most **9.36e-6** in member raw
scores and **1.04e-8** in concordance, within the frozen numerical tolerances.
Inference swap errors were zero across all nine test cells. Protected scoring
retained the unchanged offline CPU seccomp/mount guard.

Verification: 19 synthetic checks before access and again inside the guard;
**492 CPU tests** across the pinned model/data images and **12 GPU tests** passed,
covering all 494 repository cases across runtimes (GPU tests include repeated
CPU-capable cases). Initial broad-test environment failures and their corrected
runtime/scratch routing are retained, with no dependency or scientific changes.
The known UCX startup prefix was preserved as raw stdout and its unchanged JSON
attestation extracted for closure; the frozen guard/scorer were not edited.
The closure checks all **179 historical registered files**, 72 frozen prediction
files and the stored bootstrap summaries. These are same-author implementation
checks, not external scientific replication.

See the [validation records](../../../artifacts/validation/model_optimization_followup_v1/)
and [follow-up receipt](../../../artifacts/validation/protected_evaluation_receipts/model_optimization_followup_v1.json).
Model states, pair identities, predictions and bootstrap arrays remain private.
The code knowledge graph was refreshed using AST-only extraction; artifact JSON
files without code nodes are not a substitute for their scientific registries.
No further fitting, test evaluation or external-panel experiment is queued.
