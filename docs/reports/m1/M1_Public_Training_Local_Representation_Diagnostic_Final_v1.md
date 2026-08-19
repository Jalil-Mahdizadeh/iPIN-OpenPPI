# M1 public-training local-representation diagnostic: final report

**Date:** 2026-08-19
**Protocol:** `public_training_local_representation_diagnostic_v1_revision_2`
**Data boundary:** public training only
**Disposition:** no incremental coarse local-representation signal; do not run conditional Phase B

## Question and frozen design

This diagnostic tested the prospective hypothesis that global mean pooling hides
local protein information needed for partner specificity. It did not reuse
development labels and did not access protected-test candidates or truth.

The frozen Phase A design divided each endpoint into exhaustive contiguous
segments, retained frozen ESM-2 150M segment means, and compared two local
pairwise cosine oracles with a matched global cosine reconstructed from the
same encoder forward pass. The primary local score was the mean of the top four
segment-pair cosines. Evaluation used the nested whole-component public-training
C3 cell, original positive and unlabeled observations, frozen PU-R design
weights, Horvitz--Thompson positive-versus-unlabeled concordance, and a paired
200-draw component bootstrap. No negative or pseudo-negative was constructed.

The preregistered point trigger required both:

1. primary local top-four concordance at least `0.51`; and
2. primary local minus matched-global concordance at least `0.01`.

Only passage of both conditions could authorize conditional Phase B.

## Extraction and evaluation census

- public-training endpoints: `11,900`
- exhaustive segments: `56,304`
- held-out whole components: `1,366`
- nested C3 positives: `650`
- nested C3 unlabeled observations: `86,450`
- retained embedding dtype: FP32
- cosine normalization and reductions: FP64 on the retained FP32 vectors
- extraction elapsed time: `149.65228069300065` seconds on one GH200

## Phase A results

| Prespecified scorer | HT concordance | Descriptive paired-component 95% interval |
|---|---:|---:|
| sequence-length ratio | 0.572742 | [0.525077, 0.621777] |
| matched global pooled ESM cosine | 0.568759 | [0.511487, 0.627676] |
| within-pair 3-mer cosine | 0.563776 | [0.499476, 0.623285] |
| local maximum segment cosine | 0.561705 | [0.499935, 0.630201] |
| **local top-four segment cosine (primary)** | **0.553171** | **[0.487950, 0.625206]** |
| exact nested-training interolog 3-mer | 0.518071 | [0.450685, 0.583462] |
| deterministic hash control | 0.493506 | [0.459842, 0.534805] |

The primary score exceeded its absolute `0.51` condition, but its increment over
the matched global score was `-0.015587991105247556`, not at least `+0.01`.
The descriptive paired-bootstrap interval for that delta was
`[-0.042924265306829947, 0.0067081094539078205]`. The trigger therefore failed.
The conditional learned Phase B model was not run, exactly as preregistered.

Additional point comparisons are diagnostic rather than new criteria:

- local maximum minus matched global: `-0.007053675700960683`
- local top-four minus within-pair 3-mer: `-0.010604902386338925`
- local top-four minus length ratio: `-0.01957142282234122`

## Scientific interpretation

The prespecified coarse local oracle did not show incremental public-training
C3 signal over a matched global representation. Both local summaries also
trailed simple length and 3-mer controls at the point-estimate level. These
results do not support the proposed global-pooling bottleneck as an immediate
explanation for the stopped partner-gated model, and they do not justify
escalating this branch to a learned conditional model.

This is deliberately narrower than claiming that every residue-, domain-, or
token-aware architecture must fail. A genuinely learned token-token model could
encode interactions that max/top-four segment cosine cannot. It would,
however, be a new speculative programme and would require a fresh prospective
rationale, budget, protocol, and numbered authorization. Neither already spent
development information nor sealed protected material may be used to design it.

## Validation and information-flow controls

Production validation passed all `7/7` checks. A standalone validator written
after the production evidence commit imported no production implementation and
passed all `13/13` checks. It independently reconstructed the component split,
cell census, all `609,700` score values, all point metrics, `1,400` bootstrap
values and intervals, the trigger, and the mandatory Phase B stop. Maximum
disagreement was exactly `0.0` for scores, point estimates, bootstrap values,
and intervals. The validator rehashed `43,650,560` retained embedding values.
The checkpoint-prescribed complete unit suite passed `301/301` tests in the
qualified data container.

The two fail-closed numerical incidents occurred before the affected artifacts
were written. DEC-0042 widened only an FP32 regrouping audit tolerance; DEC-0043
made the scorer implement the frozen ordinary-cosine reference with FP64
reductions. Neither changed data, retained embeddings, scores, metrics,
thresholds, or scientific semantics.

Development was not decrypted or accessed. Protected candidates and truth were
not decrypted or accessed; their ciphertexts were hash-checked only. No
external panel, residue/interface label, negative, pseudo-negative, training,
checkpoint selection, or adaptive scorer change entered this diagnostic.

## Frozen evidence identifiers

- embedding manifest SHA-256: `3f8d644eb42e3a740e62d1de440ec627d25ef47b3970fd358578970430810146`
- Phase A results SHA-256: `becf069b9bae635af2554ba89849e659967baa6b073acb1346d0ebdac2a79544`
- raw score matrix SHA-256: `462d3c45296298e84bf1747bcce3050a8fd20e8837c48bf78dd425a513caf7ca`
- production registry SHA-256: `52aa06c0785e23e65c68899124634bd891ef963b45749b2f76be538537a8bebd`
- production validation SHA-256: `6956289ce1a4aef4d5d342b2d04bac043cf0af417a4b008916b46e898babfb39`
- independent validation SHA-256: `7ac2e2bf4b54c8001c238d233121c88ba40f9c5e0240282ca7c81b53da7a68fe`

DEC-0044 accepts this evidence and stops this architecture branch without
altering any parent benchmark or model-governance conclusion.
