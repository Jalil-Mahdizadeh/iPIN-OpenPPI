# M1 development release and evaluation final report v1

**Date:** 2026-08-19

**Scope:** one-time development-only release, frozen-scorer evaluation, and
independent completed-evaluation validation under the accepted model protocol

**Controlling authority:** `DEC-0028`, `DEC-0032`, `DEC-0033`, and
`DEC-0038`; binding protocol SHA-256
`5daf5809b864de75f236ca3552369f943300bdbc86557a3a99277665faeda851`;
execution configuration SHA-256
`d74c683bbeb57e8b455efc789f487ca20df7a128ab0ec27b317dc602eda3e57d`

## Result and disposition

The development-only stage is complete and independently validated. The exact
frozen disposition is **stop the complex-model claim and stop before protected
evaluation**. No candidate advances to protected evaluation, and this report
does not authorize any protected action.

The partner-gated line does not demonstrate genuine transferable sequence
signal. Its best C3 ensemble has PU-R concordance `0.49134652604741336` with
percentile-95 interval `[0.4622492977197828, 0.5372847754287488]`. It is worse
than the preregistered within-pair 3-mer comparator and does not establish the
required improvement over either the 650M linear or matched no-gate model.
Simple sequence, interolog, length, and graph-degree controls explain the
apparent performance structure. The simple controls remain frozen explanatory
baselines only; none is advanced as a protected-evaluation model.

All values below are display-formatted from the immutable aggregate JSON.
Selection and kill decisions used the full, unrounded values in
`SELECTION_AND_KILL_TRACE.json`, not the displayed precision.

## Release, scoring, and information boundary

The development ciphertext was decrypted exactly once after both final
prerelease qualifications passed 14 of 14 checks. Its ciphertext SHA-256 is
`bbbd07472da621a34f45e95ab4b51c799fa0fc967d94de2aa3578e0cda0c1d41`;
the deterministic plaintext archive and released package manifest have
SHA-256 values
`c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122`
and
`3f58403138b878d912789f529dc1f8ec7d1db7356d6ccc4c3b88cfcb2f6554fa`.
Plaintext row identities, score matrices, and release keys remain Git-ignored
under `.private/`.

Exactly nine cells were scored with 49 columns: nine mandatory deterministic
controls, all 30 frozen selected checkpoints, and all ten frozen arithmetic
three-seed ensembles. The score census is 9,026,108 rows: 26,108 P and
9,000,000 U observations. No scorer, checkpoint, ensemble, row, weight,
threshold, or training state changed.

| Cell | P rows | U rows |
|---|---:|---:|
| C3 development | 2,265 | 1,000,000 |
| HI-II-14-exclusive C3 | 312 | 1,000,000 |
| HuRI-exclusive C3 | 1,677 | 1,000,000 |
| C2 development | 11,327 | 1,000,000 |
| HI-II-14-exclusive C2 | 1,601 | 1,000,000 |
| HuRI-exclusive C2 | 4,751 | 1,000,000 |
| C1 development | 3,259 | 1,000,000 |
| HI-II-14-exclusive C1 | 305 | 1,000,000 |
| HuRI-exclusive C1 | 611 | 1,000,000 |

Scoring used one NVIDIA GH200 120 GB on node `n180`, took
`342.7965478779515` elapsed seconds, and recorded conservative use of
`0.09522126329943098` GPU-hours. The accepted container, pooled embeddings,
public-training graph, 30 checkpoint hashes, and ten ensemble definitions were
used without modification. There was no retraining, tuning, second development
decryption, or protected access.

The protected-candidate and protected-truth ciphertexts remain sealed and
unchanged at SHA-256
`5ac1c30dbda85f6274f60febb2f4b01feda34c43bf87f4bbb690abe6c639ff63`
and
`69824547667861694aff88a0f6e43526d4f3aa27f930d4a4ff44c924d29aa1e9`.
Neither protected private key, candidate plaintext, nor truth plaintext was
resolved, statted, read, copied, mounted, decrypted, or scored.

## Metric semantics

The primary metric is the frozen design-weighted positive-versus-U HT
concordance with half credit for ties. U remains unlabeled and was never used
as a negative biological class. Percentile-95 intervals use the exact paired
two-endpoint-component pigeonhole bootstrap with 2,000 deterministic
PCG64DXSM replicates rooted at seed `20260803`.

Diagnostic sampled P-versus-U AUROC is numerically identical to concordance in
these records and has no biological-classification meaning. Diagnostic sampled
AUPRC is reported separately. Cells are never pooled. Reporting is C3 first,
then C2, then C1.

## C3 development — primary claim cell

| Frozen control or ensemble | PU-R concordance | Percentile-95 CI | Diagnostic AUPRC |
|---|---:|---:|---:|
| Deterministic hash | 0.494233 | [0.473022, 0.521978] | 0.000676663 |
| Training degree sum | 0.500000 | [0.500000, 0.500000] | 0.000696928 |
| Preferential attachment | 0.500000 | [0.500000, 0.500000] | 0.000696928 |
| Component degree-mass product | 0.500000 | [0.500000, 0.500000] | 0.000696928 |
| Training common neighbors | 0.500000 | [0.500000, 0.500000] | 0.000696928 |
| Sequence length sum | 0.520454 | [0.418265, 0.577579] | 0.000663410 |
| Sequence length ratio | 0.660880 | [0.566995, 0.742350] | 0.001171894 |
| Within-pair 3-mer cosine | 0.644683 | [0.498094, 0.726463] | 0.001521380 |
| Exact training interolog 3-mer | 0.635701 | [0.525749, 0.754754] | 0.001210776 |
| 150M linear, lr 1e-3 | 0.485996 | [0.426575, 0.548083] | 0.000668221 |
| 150M linear, lr 3e-4 | 0.491608 | [0.434282, 0.552575] | 0.000681192 |
| 650M linear, lr 1e-3 | 0.485029 | [0.436781, 0.548374] | 0.000684054 |
| 650M linear, lr 3e-4 | 0.485140 | [0.434499, 0.552563] | 0.000696509 |
| 650M no-gate, conservative | 0.469102 | [0.432855, 0.534395] | 0.001092468 |
| 650M no-gate, default | 0.476761 | [0.443674, 0.532839] | 0.000701721 |
| 650M no-gate, no dropout | 0.476429 | [0.445365, 0.524802] | 0.000688354 |
| 650M partner-gated, conservative | 0.487780 | [0.450603, 0.539054] | 0.000673627 |
| 650M partner-gated, default | 0.487181 | [0.455412, 0.536845] | 0.000685212 |
| 650M partner-gated, no dropout | 0.491347 | [0.462249, 0.537285] | 0.000691295 |

The best complex candidate under the frozen trace is the no-dropout
partner-gated ensemble. Its exact C3 comparisons are:

| Comparator | Exact delta | Paired percentile-95 interval | Frozen requirement | Result |
|---|---:|---:|---|---|
| Within-pair 3-mer | -0.15333611147533133 | [-0.2459824782324954, 0.019318960348454824] | at least 0.02 and interval positive | fail |
| 650M linear, lr 3e-4 | 0.006206836644593983 | [-0.043158071185191056, 0.050104062093720605] | at least 0.01 and interval positive | fail |
| Matched no-gate, no dropout | 0.014917351434742432 | [-0.0017786841786421868, 0.03245385852354833] | at least 0.005 and interval positive | fail: interval includes zero |

The sequence-length ratio exceeds every learned ensemble in C3, and both the
within-pair and exact-interolog controls substantially exceed the best complex
ensemble. The exact interolog interval excludes `0.5`; the best complex lower
bound does not exceed `0.5`.

## C2 development

| Frozen control or ensemble | PU-R concordance | Percentile-95 CI | Diagnostic AUPRC |
|---|---:|---:|---:|
| Deterministic hash | 0.497992 | [0.487134, 0.506688] | 0.000949196 |
| Training degree sum | 0.839263 | [0.822793, 0.853079] | 0.007638683 |
| Preferential attachment | 0.500000 | [0.500000, 0.500000] | 0.000950152 |
| Component degree-mass product | 0.500000 | [0.500000, 0.500000] | 0.000950152 |
| Training common neighbors | 0.500000 | [0.500000, 0.500000] | 0.000950152 |
| Sequence length sum | 0.495916 | [0.436638, 0.537880] | 0.000917079 |
| Sequence length ratio | 0.561149 | [0.534885, 0.581808] | 0.001111203 |
| Within-pair 3-mer cosine | 0.548960 | [0.493610, 0.590925] | 0.001165410 |
| Exact training interolog 3-mer | 0.608146 | [0.543587, 0.655489] | 0.002538838 |
| 150M linear, lr 1e-3 | 0.495536 | [0.471931, 0.520898] | 0.000965378 |
| 150M linear, lr 3e-4 | 0.497756 | [0.472847, 0.523091] | 0.000974229 |
| 650M linear, lr 1e-3 | 0.492801 | [0.466203, 0.517202] | 0.000934040 |
| 650M linear, lr 3e-4 | 0.491769 | [0.465625, 0.516926] | 0.000935254 |
| 650M no-gate, conservative | 0.487217 | [0.464148, 0.509725] | 0.000918799 |
| 650M no-gate, default | 0.488791 | [0.467200, 0.508954] | 0.000918982 |
| 650M no-gate, no dropout | 0.486918 | [0.467120, 0.505625] | 0.000913122 |
| 650M partner-gated, conservative | 0.488120 | [0.466639, 0.508156] | 0.000919659 |
| 650M partner-gated, default | 0.492451 | [0.474180, 0.512512] | 0.000927236 |
| 650M partner-gated, no dropout | 0.493875 | [0.475762, 0.512467] | 0.000927771 |

The large degree-sum result and the interolog result are simple-control
explanations. Every PLM ensemble is near chance and has an interval spanning
`0.5`.

## C1 development

| Frozen control or ensemble | PU-R concordance | Percentile-95 CI | Diagnostic AUPRC |
|---|---:|---:|---:|
| Deterministic hash | 0.493247 | [0.476159, 0.509491] | 0.000295143 |
| Training degree sum | 0.906789 | [0.894429, 0.916155] | 0.007531662 |
| Preferential attachment | 0.906942 | [0.894732, 0.916496] | 0.007509734 |
| Component degree-mass product | 0.695019 | [0.642473, 0.823300] | 0.000503857 |
| Training common neighbors | 0.681018 | [0.659085, 0.704781] | 0.004748357 |
| Sequence length sum | 0.459942 | [0.422035, 0.495463] | 0.000274252 |
| Sequence length ratio | 0.552608 | [0.529896, 0.582128] | 0.000350926 |
| Within-pair 3-mer cosine | 0.517473 | [0.487786, 0.558624] | 0.000746803 |
| Exact training interolog 3-mer | 0.620921 | [0.576136, 0.654349] | 0.005450754 |
| 150M linear, lr 1e-3 | 0.491911 | [0.471748, 0.514315] | 0.000290330 |
| 150M linear, lr 3e-4 | 0.492810 | [0.472614, 0.515583] | 0.000290571 |
| 650M linear, lr 1e-3 | 0.494195 | [0.473371, 0.518268] | 0.000293815 |
| 650M linear, lr 3e-4 | 0.489964 | [0.469408, 0.513965] | 0.000288686 |
| 650M no-gate, conservative | 0.498770 | [0.475766, 0.523471] | 0.000301228 |
| 650M no-gate, default | 0.492919 | [0.471488, 0.517116] | 0.000293841 |
| 650M no-gate, no dropout | 0.495702 | [0.474000, 0.520157] | 0.000296495 |
| 650M partner-gated, conservative | 0.491405 | [0.469710, 0.515311] | 0.000292881 |
| 650M partner-gated, default | 0.492174 | [0.470566, 0.516201] | 0.000294006 |
| 650M partner-gated, no dropout | 0.491014 | [0.469290, 0.516020] | 0.000292161 |

C1 is dominated by training-graph degree and preferential attachment. It does
not support a transferable-sequence or biological-probability claim.

## Source-exclusive diagnostics

Source-exclusive cells are report-only and do not select a candidate. The
table gives PU-R concordance; the complete 49-scorer records are frozen in
`SOURCE_EXCLUSIVE_METRICS.json`.

| Frozen control or ensemble | C3 HI | C3 HuRI | C2 HI | C2 HuRI | C1 HI | C1 HuRI |
|---|---:|---:|---:|---:|---:|---:|
| Within-pair 3-mer | 0.580560 | 0.652732 | 0.595068 | 0.549207 | 0.577864 | 0.530138 |
| Exact interolog 3-mer | 0.635615 | 0.627836 | 0.682195 | 0.613668 | 0.697160 | 0.641911 |
| 150M linear, lr 3e-4 | 0.459611 | 0.498279 | 0.497732 | 0.493646 | 0.526329 | 0.476849 |
| 650M linear, lr 3e-4 | 0.431546 | 0.497255 | 0.479259 | 0.492598 | 0.513533 | 0.481895 |
| 650M no-gate, no dropout | 0.406222 | 0.493544 | 0.468207 | 0.490005 | 0.525180 | 0.470296 |
| 650M partner-gated, no dropout | 0.402991 | 0.512089 | 0.474889 | 0.494906 | 0.514163 | 0.474419 |
| Preferential attachment | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 0.915761 | 0.899964 |

Against the frozen strongest-simple comparator, the partner-gated no-dropout
C3 deltas are `-0.23262459775331246` in HI-II-14 and
`-0.1406427868176625` in HuRI. The required positive direction is absent in
both supported named-source cells.

## Degree and hub stratification

The `100`-positive/`10`-component support floor was applied exactly. Unsupported
strata remain descriptive only. C3 has only the degree-pair `0|0` quantitative
stratum and no top-10%-hub P rows, so its non-hub view is identical to the
primary view.

| Cell | Quantitative degree strata | Descriptive strata | Top-10% hub P | Non-hub P | Non-hub preferential | Non-hub interolog | Non-hub 150M linear | Non-hub partner-gated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C3 | 1 | 0 | 0 | 2,265 | 0.500000 | 0.635701 | 0.491608 | 0.491347 |
| C2 | 8 | 0 | 8,937 | 2,390 | 0.500000 | 0.598619 | 0.494318 | 0.493413 |
| C1 | 9 | 27 | 3,063 | 196 | 0.730789 | 0.653349 | 0.454604 | 0.475215 |

The exact best-complex C3 gain outside top-10%-hub pairs is
`-0.15333611147533133`; the prespecified non-hub requirement therefore fails.

## Prespecified C1 novel-U sensitivity

The report-only C1 novel-U view retained the original frozen rows and weights,
removed only C1 U pair IDs present in public training U, and did not affect
selection or stopping. It contains 3,259 P rows and 817,183 retained U rows;
182,817 U rows were removed. Retained U pair IDs are unique, 36 strata remain
nonempty, and the FP64 weight sum is `8909119.603382831`.

| Frozen control or ensemble | Primary C1 | Novel-U C1 |
|---|---:|---:|
| Preferential attachment | 0.906942 | 0.906918 |
| Exact interolog 3-mer | 0.620921 | 0.620817 |
| Within-pair 3-mer | 0.517473 | 0.517508 |
| 150M linear, lr 3e-4 | 0.492810 | 0.492843 |
| 650M linear, lr 3e-4 | 0.489964 | 0.490171 |
| 650M no-gate, no dropout | 0.495702 | 0.495745 |
| 650M partner-gated, no dropout | 0.491014 | 0.491020 |

The best-complex gain over the strongest simple control is
`-0.12215151286601061` in primary C1 and `-0.12203007817426298` in novel-U
C1. The sensitivity result does not change the interpretation.

## Three-seed stability and frozen selection

All 30 individual selected checkpoints were evaluated. The table gives the
exact within-candidate concordance range across seeds `20260803`, `20260817`,
and `20260831`. The frozen eligibility ceiling is `0.02` in every primary cell.

| Candidate ensemble | C3 range | C2 range | C1 range | Seed-stable eligible |
|---|---:|---:|---:|---|
| 150M linear, lr 1e-3 | 0.001767915 | 0.001863241 | 0.000539444 | yes |
| 150M linear, lr 3e-4 | 0.002544906 | 0.002732665 | 0.001636264 | yes |
| 650M linear, lr 1e-3 | 0.000875463 | 0.000860146 | 0.000731823 | yes |
| 650M linear, lr 3e-4 | 0.001755576 | 0.002047102 | 0.000941083 | yes |
| 650M no-gate, conservative | 0.030779810 | 0.019672096 | 0.006291735 | no |
| 650M no-gate, default | 0.018517039 | 0.013533791 | 0.007765331 | yes |
| 650M no-gate, no dropout | 0.009589322 | 0.009947734 | 0.009418790 | yes |
| 650M partner-gated, conservative | 0.011412701 | 0.003352716 | 0.003760952 | yes |
| 650M partner-gated, default | 0.007731214 | 0.005149834 | 0.007861325 | yes |
| 650M partner-gated, no dropout | 0.005808897 | 0.010662473 | 0.009329673 | yes |

The exact decimal-`0.001` `ROUND_HALF_UP` cascade ordered by C3, C2, C1,
lower frozen complexity, and candidate ID selects
`lightweight_esm2_150m_linear__linear_lr3e-4`. This mechanical candidate
selection does not override the model-level kill rules and does not authorize
protected advancement. Individual seeds, source-exclusive cells, and novel-U
results had no selection role.

## Complexity and model-level kill rules

The partner-gated no-dropout model meets only the raw `0.005` delta magnitude
against its matched no-gate model and the seed-range condition. Its paired
interval includes zero, and every other required partner-gate condition fails:
the `0.02` simple-sequence gain, positive simple-sequence interval, `0.01`
650M-linear gain, positive 650M-linear interval, positive no-gate interval,
positive named-source direction, and positive non-hub direction.

The following frozen model-level kill criteria fire:

- the best complex C3 lower confidence bound is not above `0.5`;
- no complex candidate has C3 gain at least `0.02` with a positive paired
  interval;
- the complex result is explained by the interolog or frozen-PLM-linear
  comparisons;
- gain is absent outside top-10%-hub pairs; and
- simple graph shortcuts explain C1 without a qualifying learned C2 or C3
  gain.

Integrity/custody violation, post-release training, use of U as a negative or
probability target, and protected-boundary violation are all false. The stop is
scientific, not an execution-integrity failure. The partner gate is rejected;
the nonlinear head and 650M scale have no justified retained claim; no learned
line advances.

## Production and independent validation

The corrected completed-evaluation production audit passed 9 of 9 checks. It
verified every registered byte and hash, all nine score matrices and 49-column
schemas, every ensemble column, all `9 x 49` point-metric records, every
supported stratum and hub view, all correlations, all three `19 x 2,000`
bootstrap result matrices, the C1 novel-U view, and the exact
selection/complexity/kill trace.

The clean-room validator was committed only after production results and
evidence were frozen. It is standalone and imports no production
`ipin_openppi` development-evaluation module. It passed 16 of 16 checks and:

- rehashed 57 registered private/public files totaling 3,959,706,937 bytes;
- recomputed all nine deterministic scorers on all rows: 81,234,972 values,
  maximum absolute difference `0.0`;
- independently scored all 30 checkpoints on all rows: 270,783,240 values,
  maximum absolute difference `0.0` and swap difference `0.0`;
- checked every value in all ten arithmetic ensemble columns;
- independently recomputed all `9 x 49` point metrics, degree/hub strata,
  diagnostic correlations, all `3 x 19 x 2,000` component bootstraps, C1
  novel-U, seed stability, selection, complexity, and kill results; and
- confirmed one-time development release, no training/checkpoint change, no
  public pair identities, and no protected key, candidate, or truth access.

Three fail-closed implementation/audit incidents were governed without changing
scientific semantics: `ISSUE-0009` corrected only nullable concat schema,
`ISSUE-0010` corrected the source-cell degree metadata guard while retaining
pooled public-training graph features, and `ISSUE-0011` corrected only the
completed auditor's score-row census. Their failed evidence is preserved, and
each correction was separately authorized, regression-tested, requalified,
and independently validated before execution resumed.

Production result evidence was frozen at commit
`c7ef1736bce641f21297b66d1ac086f825c6a108`; independent validator source was
then frozen at `3a88c737af1bd66a1684c7f66144d89d20035eb1`; passing independent evidence
was frozen at `3e8674944367456a516b91dbb846befaffe1daca`.

## Frozen evidence

| Artifact | SHA-256 |
|---|---|
| Development scoring manifest | `c82be153593ad46101f1ce49e1c79d341da535c71b34ded748c63e478b10dc99` |
| Development results manifest | `e6b5455e3c1e0346b5b9c9a358db7abc628732b57bab2ec778992d2fbe9c8299` |
| Primary metrics | `feb81ccd88cd58e0c4cbe81abce1d9006bf787df5ed927f3a5ba1beee5442e8f` |
| Source-exclusive metrics | `6e5246861f843358afac2f60eb8f73a51d41b586dff272f556734da9a7ddfd4f` |
| Degree/hub diagnostics | `25ea592ae495e69bf688101444e6c671574553af26c5e1e35edbfb802cc81455` |
| C1 novel-U sensitivity | `a557d53e1a25d5bb21550a687131250fb7a4ed201985a935d05c2a03528dad90` |
| Diagnostic correlations | `c1a44d2719163034c7254f30cf1eb1ae2fbdc7953d188eb75ebcb5036c3d9f07` |
| Bootstrap registry | `c38ddd0d673c246511dabb1137d14be8936a89c95a4e97006f57e0f81e311be9` |
| Selection and kill trace | `ac583545f2dd3c8305dc477cb2d414e75a31800afcb29ddaedc6276cab165c45` |
| Completed-evaluation registry | `42aa8b19c4c5cfaf36bfbe1bd19bdf74e7de81df27cccb793809a5ec80d0e189` |
| Production completed audit | `1724a645e39ec232827aa8d1a8b6142fd257ec9404f133e985f2330e15e073ba` |
| Independent completed validation | `0d3bc35047bd8971177dbe148d1f5a4bbe515ba6d396552e6f3f3cf49f11039e` |

## Final boundary

The development work package is closed. The accepted disposition is the third
preregistered outcome: stop the complex-model claim and stop before protected
evaluation. No protected candidate, truth, or private key may be accessed; no
protected prediction or metric may be generated; and no development result may
be used for retraining, tuning, checkpoint change, threshold change, or a new
architecture. Any new scientific phase requires a separate prospective
protocol and numbered governance authorization and cannot reinterpret this
frozen development evaluation.
