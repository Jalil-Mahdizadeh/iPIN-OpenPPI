# Public-training local-representation diagnostic protocol v1

## Question and scope

This prospective diagnostic asks one narrow question: did the stopped pooled
model line discard transferable PPI-ranking information by reducing each
protein to one whole-sequence mean before the two partners interacted?

It is a new public-training-only study, not an amendment or reinterpretation of
`DEC-0028` or its development result. Development is treated as spent and the
protected packages remain sealed. The parent benchmark, P/U meaning, endpoint
sequences, leakage components, pair rows, and design weights are read-only.
U remains unlabeled evidence. No negative, pseudo-negative, interface label,
structure feature, probability, or prevalence claim is created.

The executable source of truth is
`configs/public_training_local_representation_diagnostic_v1.yaml`.

## Prospective nested component test

Only endpoints already assigned to the frozen public training partition enter
this study. Whole frozen leakage components are ordered by
`SHA256("ipin-openppi-local-representation-diagnostic-v1:" + component_id)`.
Components are assigned to the nested holdout in that order until 2,380 of the
11,900 endpoints are held out. This label-independent rule yields 1,366 held-
out components and the following public row census:

| Nested cell | P | U |
|---|---:|---:|
| C1: neither component held out | 11,051 | 1,254,297 |
| C2: exactly one held out | 5,098 | 659,253 |
| C3: both held out | 650 | 86,450 |

C3 is the only primary oracle cell. It tests transfer to endpoints from whole
components unavailable to any conditional fitting step.

## Frozen local representation

The exact already-custodied ESM-2 150M revision and qualified FP32 offline
runtime are reused with a frozen encoder. Long-sequence contextualization and
overlap averaging are identical to the accepted embedding strategy. Instead
of discarding the residue axis immediately, every protein is divided into
`min(32, max(1, ceil(length / 128)))` contiguous, exhaustive bins. Each bin is
the arithmetic mean of its contextual residue vectors. Segment-length-weighted
pooling must reconstruct the matched whole-protein mean, so global versus local
comparisons use the same forward pass and differ only in when the partners
interact.

This is coarse local representation learning, not residue/interface
prediction. No residue target or interface claim is permitted.

## Phase A: label-free late-interaction oracle

The primary local score is the mean of the four largest cosine similarities
between the two proteins' segment vectors (or all segment pairs when fewer than
four exist). The matched comparator is cosine similarity between the two
reconstructed global means. Maximum segment cosine and bidirectional best-
match cosine are secondary diagnostics. Frozen hash, length-ratio, within-pair
3-mer, and nested-C1 exact interolog controls remain visible.

The metric is exact Horvitz--Thompson P-versus-U concordance with original U
design weights and half credit for ties. A 200-replicate paired two-endpoint
component bootstrap is descriptive. To keep this diagnostic fast and
screening-oriented, the conditional learned phase triggers on point estimates:
the primary local score must exceed `0.51` and beat its matched global control
by at least `0.01`.

## Conditional Phase B: low-capacity feature test

Only if both Phase A trigger conditions pass, two linear ranking scores are fit
on nested C1 with the frozen design-weighted P-versus-U logistic objective. The
matched global score receives only pooled cosine. The local score receives
pooled cosine plus the three frozen local summaries. There is one seed, one
optimizer recipe, three complete passes, final-pass selection, and no search.
An incremental local-model C3 point gain of at least `0.01` is the permissive
signal criterion.

Passing this diagnostic would justify a separately governed confirmatory
token/domain-aware study. It would not revive the stopped development claim or
authorize any development or protected access. Failure ends this architecture
branch without such escalation.

