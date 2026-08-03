# M0 systematic-screen metadata audit and benchmark/estimand proposal

**Version:** 1.0
**Date:** 2026-08-03
**Status:** Final audit report; benchmark policy proposed for expert-group approval
**Execution owner:** Codex
**Platform:** NAISS Arrhenius through pinned ARM64 Apptainer
**Scientific scope:** Metadata and semantics only; no labels, splits, structural mappings, or models were constructed

## Executive conclusion

The project remains feasible, but the originally intended primary calibrated HuRI assay endpoint is not feasible from the currently public evidence.

The public HuRI release provides extensive positive-interaction evidence, gene-level Space III membership, positive detection histories, and selected reference, retest, orthogonal-validation, literature, and structural-sensitivity panels. It does not provide the complete pair-level log needed to know which opportunities were selected, attempted, technically evaluable, excluded, failed, or negative across the nine screens. Therefore:

- absence from a HuRI positive list is not an experimental negative;
- the 3,038 selected Table 15 pairs not detected in assay versions 1–3 are not universal negatives;
- selected Y2H, MAPPIT, and GPCA control-panel non-detections are conditional panel outcomes, not population negatives;
- the 939 explicit IntAct negative records do not define the HuRI systematic universe; and
- neither a natural-prevalence AUPRC nor a calibrated assay-positive probability can be defended as the current primary endpoint.

The recommended path is Resolution Path 3 of ISSUE-0003: adopt a reference-sequence positive–unlabeled (PU) ranking design as the definitive proposed primary design, retain the released HuRI positives as observed positive evidence, treat all other eligible pairs as unlabeled, and make a symmetric compatibility/prioritization score—not a probability—the primary model output.

This is a scientifically meaningful narrowing, not a substitute negative-label construction. It preserves a viable evidence-aware sequence-ranking project while removing claims that the public data cannot identify.

The proposal is not yet effective. Expert-group approval of the accompanying blueprint amendment is required before even the candidate-eligibility and sequence-component audit begins. Label construction, split construction, structural mapping, and model training remain prohibited.

## 1. Audit authority and reproducibility

The audit ran only through:

- `containers/images/ipin-data-arm64_0.1.2.sif`;
- SIF SHA-256 `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`;
- architecture `aarch64`; and
- implementation commit `7af9473c876e53b777cf6ee829bbcbdf85c49fe4`.

The production audit began from a clean Git worktree. Its independent validator recomputed the scientific counts directly from immutable staged Parquet, rather than trusting the audit report.

| Record | Status | SHA-256 |
|---|---:|---|
| `artifacts/validation/benchmark_design/systematic_screen_metadata_v1/AUDIT_REPORT.json` | Complete | `db75b0cb2863cc1b44e45759e924bfc4b00d379fa291873e7e3e10e99748fc5e` |
| `artifacts/validation/benchmark_design/systematic_screen_metadata_v1/VALIDATION_REPORT.json` | Pass: 71 pass, 0 fail, 3 expected warnings | `2ca92051172b7a7a512072f3ed6212ac8caed5891870abcea7c6e5929cd56a01` |
| `configs/systematic_screen_metadata_audit_v1.yaml` | Frozen audit contract | `baedc6cdd96d89790497293650421db4c385fb5747c3a456b27712096e55af5b` |

The three validation warnings are substantive scientific blockers, not integrity failures:

1. the HuRI attempted/evaluable universe remains unresolved;
2. strict construct-confidence A/B coverage remains zero; and
3. the reviewed authors' code repository has no license file and was not ingested.

## 2. Question tested

The audit asked whether the frozen public sources can reconstruct, at pair and assay-opportunity level:

1. search-space membership;
2. screen and run;
3. ordered bait and prey constructs;
4. selection;
5. attempted status;
6. technical evaluability;
7. technical failure or exclusion reason;
8. observed outcome;
9. first-pass candidate status;
10. complete pairwise retest status;
11. prescreen autoactivator exclusion; and
12. sampling probability for released controls.

A calibrated binary assay endpoint requires these processes to be distinguished. A positive-only list is insufficient because a missing pair can mean not in space, unavailable clone, removed bait, not selected, not attempted, invalid, autoactivating, failed, below a candidate threshold, negative on retest, or simply not released.

## 3. Sources inspected

The audit verified immutable hashes and read-only status for:

- HuRI and HI-II-14 pair and PSI-MITAB releases;
- the published test-space pair list;
- all 29 scientific supplementary tables;
- the 32-page supplementary methods;
- the 3-page supplementary-table guide;
- the accepted staging and reconciliation manifests and validators;
- the frozen source-policy and schema contracts; and
- the relevant HuRI, supplementary, fusion-interference, and IntAct staged Parquet.

A public-availability review also examined the [Nature article](https://www.nature.com/articles/s41586-020-2188-x), [Interactome Atlas downloads](https://www.interactome-atlas.org/download), [FAQ](https://www.interactome-atlas.org/faq/), [About page](https://www.interactome-atlas.org/about/), and the [authors' HuRI paper repository](https://github.com/CCSB-DFCI/HuRI_paper) at commit `16c57919f4e0c3d1a78edf90c105ed42d3022f8f`.

The authors' repository republishes Tables 1–28 and selected derived validation files. Its README states that parts of the analysis depend on internal databases and are not fully reproducible outside the originating environment. No alternate scientific branch, tag, or public file containing the complete selected/attempted/evaluable opportunity log was found. The repository has no license file, so its files were used only as availability metadata and were not ingested.

## 4. Audited evidence

### 4.1 Main systematic-source representations

| Evidence object | Audited count | Interpretation |
|---|---:|---|
| HuRI/HI-II-14 evidence rows | 220,934 | All are positive |
| Positive evidence rows | 220,934 | 171,545 HuRI plus 49,389 HI-II-14 |
| Negative evidence rows | 0 | No primary negative opportunity records |
| HuRI pair-view rows | 52,548 | Released positive pair view; includes 480 self-pairs before primary heteromeric filtering |
| HI-II-14 pair-view rows | 13,633 | Released positive pair view |
| Test-space pair-view rows | 1,159 | Released positive pair view |
| Lit-BM pair-view rows | 13,441 | Literature benchmark pair view |
| Space III genes | 17,408 | Gene membership, not pair-opportunity membership |
| Unordered Space III gene pairs excluding self | 151,510,528 | Candidate upper universe only; not a claim that all were attempted |

Every main HuRI evidence row has a positive observation. Selection, attempt, evaluability, and passed technical state can be logically inferred for a released positive, but the search-space state remains unknown at the evidence-record level. The inverse implication is invalid: a pair without a released positive cannot be assigned any one of those states.

The 21-row difference between the 52,548 HuRI portal pair view and 52,569 Supplementary Table 9 rows is a representation difference that must remain explicit. It does not supply missing negative opportunities.

### 4.2 Positive detection metadata

| Positive-only table | Audited count | What it establishes |
|---|---:|---|
| Table 7 positive pairs | 1,214 | Test-space positives with 3,099 screen-detection mentions |
| Table 9 HuRI positive pairs | 52,569 | Released HuRI positives |
| Table 9 screen-detection mentions | 77,653 | Positive detections across screens |
| Table 9 assay-version detection mentions | 55,534 | Positive detections across assay versions |
| Minimum/maximum detected screens for a Table 9 pair | 1 / 9 | Multiplicity among detected positives |

Table 9 enumerates detections for positive pairs. It does not enumerate the failed or negative opportunity denominator. Detection multiplicity is useful as evidence strength and assay-sensitivity metadata, but cannot recover the complete screen universe.

### 4.3 Selected conditional panels

| Table | Rows | Source outcomes | Admissible interpretation |
|---|---:|---|---|
| 5, Y2H reference controls | 1,044 | 791 `0`, 70 `1`, 142 autoactivating, 41 invalid | Orientation/assay-version reference diagnostic; all 522 pair-assay groups have two orientations |
| 6, MAPPIT selected panels | 2,839 | 2,196 `0`, 150 `1`, 493 blank/unresolved | Orthogonal recovery diagnostic |
| 8, MAPPIT/GPCA selected panels | 8,239 | 8,239 numeric scores | Quantitative selected-panel diagnostic; publication table has no binary result field |
| 12, Y2H literature recovery | 2,391 | 2,017 `0`, 83 `1`, 29 autoactivating, 262 invalid | Literature recovery diagnostic |
| 13, MAPPIT literature recovery | 1,433 | 1,272 `0`, 85 `1`, 76 blank/unresolved | Literature recovery diagnostic |
| 15, fusion-interference subset | 3,738 | 3,038 never detected in versions 1–3 | Technical sensitivity diagnostic only |
| 16, selected MAPPIT panel | 6,447 | 4,344 `0`, 1,138 `1`, 965 blank/unresolved | Recovery by Y2H detection history |

A source value of `0` in a selected assay panel is a conditional non-detection for that construct, orientation, assay, batch, and sampling design. It is not proof of biological incompatibility. `AA`, `NA`, blanks, invalid records, and technical failures are separate states and may never be merged into the negative category.

Table 15 is especially important: 3,038 structurally selected pairs were not detected in any of the three Y2H assay versions, while 700 had at least one detection. This measures assay/version sensitivity in a selected subset. Treating the 3,038 as biological negatives would directly contradict the reason the panel was assembled.

### 4.4 IntAct explicit negatives

The staged IntAct evidence contains 939 source-asserted negative rows. Their search-space state is not applicable, selection state is unknown, and technical evaluability and technical state are unknown. These records may eventually support source-scoped qualitative or conditional diagnostics after a dedicated construct/evaluability/sampling audit. They do not define the systematic HuRI denominator and are not eligible as primary binary negatives.

## 5. Completeness result

None of the 12 required universe fields is complete at pair-opportunity level.

| Requirement class | Public state |
|---|---|
| Pair-level search-space membership | Positive-only or gene-level only |
| Screen/run and ordered constructs for every opportunity | Positive-only |
| Selection and attempted state for every opportunity | Positive-only |
| Evaluability and technical exclusion reason | Unavailable |
| Outcome for every evaluable opportunity | Positive-only |
| First-pass and full retest logs | Unavailable |
| Prescreen autoactivator exclusion log | Unavailable |
| Control sampling probability | Partial |

The complete attempted/evaluable universe is therefore not reconstructable from the public release. ISSUE-0003 cannot close under Resolution Path 1. Resolution Path 2 would require new investigator-provided data and compatible reproducibility terms; no such data are presently available. Resolution Path 3 is the only currently executable scientific design.

## 6. Feasibility assessment

| Proposed product | Feasibility now | Judgment |
|---|---|---|
| Provenance-preserving evidence warehouse | Feasible and already validated | Strong |
| Reference-sequence PU ranking benchmark | Feasible subject to post-approval eligibility and minimum-size audit | Recommended primary |
| Conditional Y2H/MAPPIT/GPCA recovery diagnostics | Feasible with exact panel semantics | Recommended secondary |
| Symmetric sequence compatibility/prioritization score | Feasible as a score | Recommended model output |
| Calibrated HuRI assay-positive probability | Not feasible from current public data | Defer |
| Binary positive/negative HuRI benchmark | Not feasible | Prohibit |
| Absolute latent binding probability | Not identifiable | Prohibit |
| Strict construct benchmark | Not feasible; A/B coverage is 0% | Defer |
| Structure-derived labels or interface benchmark | Not feasible under unresolved SIFTS/UniProt alignment | Defer |
| Proteome hypothesis catalogue | Potentially feasible after ranking, uncertainty, and retrieval gates | Computational hypotheses only |
| Experimental validation | Impossible within project scope | No claim permitted |

The project is worth continuing because the reference-sequence evidence coverage, positive evidence volume, orthogonal panels, and prospective leakage controls support a substantial ranking and generalization programme. Its success claim must be narrower than the original minimum programme: it can demonstrate recovery, ranking, transfer, robustness, and computational prioritization, but not calibrated biological or assay probability from the current HuRI release.

## 7. Proposed primary design

### 7.1 Population and units

The proposed population is the set of unordered heteromeric human pairs for which both Space III participants map to distinct usable frozen reference-sequence hashes.

The exact eligible count is deliberately not asserted in this proposal. It will be computed only after approval by a dedicated eligibility audit. The 151,510,528 unordered gene-pair count is an upper candidate count before sequence mapping, exclusions, and deduplication. It is not an attempted universe.

Two units remain separate:

- the biological ranking unit is an unordered reference-sequence pair; and
- the evidence unit retains source, construct, orientation, assay version, batch, repeat, technical state, and outcome.

### 7.2 Observed and latent variables

Let:

- \(X_{AB}\) be the frozen sequence pair and permitted pre-cutoff metadata;
- \(R_{AB}=1\) mean that the pair has qualifying released positive evidence by the relevant frozen information cutoff;
- \(R_{AB}=0\) mean unlabeled, not negative; and
- \(Y_{AB}\) denote latent direct compatibility in an incompletely specified biochemical context.

Selection into \(R=1\) is feature-dependent and unknown. A selected-completely-at-random or constant-labeling-propensity assumption is not authorized. \(Y\), assay sensitivity, assay specificity, and the class prior are not jointly identified from the public release.

### 7.3 Primary estimand

For a symmetric score \(f\), the primary observed-evidence estimand is:

\[
\theta(f)=P[f(X^{R=1})>f(X^{R=0})]+\tfrac{1}{2}P[f(X^{R=1})=f(X^{R=0})],
\]

where the probability is taken under the frozen held-out-positive and deterministic unlabeled sampling distributions.

This estimand measures ranking recovery of released positive evidence. It is sensitive to biological signal, assayability, source selection, and other feature-dependent release processes. It must not be described as biological AUROC, binding probability, assay probability, or causal correction of selection bias.

The paired query-retrieval estimand is the rank of each held-out released-positive partner within the eligible partner universe. Since hidden positives can remain among candidates, retrieval precision and false-positive rate are not biologically identified.

### 7.4 Required output semantics

The primary model output is a swap-symmetric sequence compatibility/prioritization score satisfying \(f(A,B)=f(B,A)\).

An optional observed-release propensity may be computed only as a diagnostic within its explicit artificial sampling design. It is not a biological probability and is not a headline output.

The original conditional assay-positive endpoint remains defined but inactive. It can reactivate only after an official pair-level opportunity log passes the future tested-universe gate.

## 8. Proposed benchmark tiers

1. **PU-R: reference-sequence positive–unlabeled ranking.** Proposed primary tier. Uses held-out released positives and deterministic unlabeled candidates. No negative or probability claim.
2. **CP-D: conditional-panel diagnostics.** Uses Tables 5, 6, 8, 12, 13, 15, and 16 for assay/version, orientation, technical-state, literature-recovery, and orthogonal-recovery diagnostics. Protected diagnostic records are not training data.
3. **TU-C: tested-universe calibrated assay endpoint.** Inactive. Requires an official or investigator-provided opportunity log with at least 90% auditable pair-level coverage of search-space, selection, attempt, evaluability, technical state, and outcome, with characterized residual missingness.
4. **SC-S: strict construct and structural benchmark.** Inactive. Requires at least 80% construct confidence A/B in the relevant strict evidence, resolved SIFTS/UniProt alignment, proven residue-interval validity, and zero unresolved structure-derived labels.

The inactive tiers may not be simulated by silently upgrading reference mappings, selected controls, non-detections, or absent pairs.

## 9. Sampling and prevalence

The eligible unlabeled pool contains candidate pairs without visible qualifying positive evidence at the axis-specific cutoff.

Sampling must be deterministic uniform hash sampling without replacement within each split and stratum, using SHA-256 and a committed public salt. Every sampled candidate records its inclusion probability and sampling weight. Full-candidate evaluation is preferred when computationally feasible.

For held-out-source and temporal tests, held-out labels are invisible to candidate exclusion. Otherwise the benchmark would leak the answer by removing the held-out positive from the unlabeled pool.

Random-negative and matched-negative BCE models remain allowed only as shortcut-diagnostic baselines. Their sampled unlabeled pairs are pseudo-negatives for optimization, not scientific negatives.

The true positive class prior is not identified. No single prevalence estimate will be reported as fact. Before model results, a sensitivity grid will be frozen from the exact observed-positive fraction through plausible higher values up to 0.05; every grid result must be reported.

## 10. Splits and leakage controls

No split has been constructed.

If approved, frozen reference-sequence hashes will be connected when an alignment meets both the identity threshold and at least 80% coverage of each sequence. Deterministic connected components will be constructed at:

- 30% identity as the primary threshold;
- 40% identity as a less stringent leakage sensitivity; and
- 20% identity as a more stringent sensitivity.

Tool version, commands, parameters, databases, and hashes must be frozen. Entire components—not accessions—are the partitioning unit. The proposed target fractions are 70% train, 15% development, and 15% protected test with seed `20260803`.

C1, exclusive C2, and C3 retain the blueprint definitions. Reverse pairs, all evidence for a pair within an axis, close homologues, construct variants, and applicable publication/assay groups must remain co-located.

The complete information cutoff covers source releases, publications, sequences, structures, PLMs, teacher models, predicted sources, and candidate-generation rules. Test labels, held-out sources, and post-cutoff evidence may not influence training, candidate exclusion, graph degree, split balancing, or hyperparameter choice.

## 11. Metrics and uncertainty

Primary metrics are:

- positive–unlabeled pairwise concordance;
- held-out released-positive Recall@10, Recall@100, and Recall@1000;
- released-positive enrichment at frozen candidate fractions; and
- positive rank percentile.

Every result reports C1/C2/C3 separately, identity threshold, surviving positives, eligible candidates, proteins, independent sequence components, source/assay strata, nearest-training similarity, sampling fraction, and inclusion weights.

Sampled positive-versus-unlabeled AUPRC/AUROC, release-propensity log loss, and graph metrics are diagnostic only. Biological precision, biological false-positive rate, calibrated binding probability, calibrated assay probability, and proteome-wide precision are prohibited interpretations.

Brier skill, calibration slope/intercept, adaptive calibration error, natural-prevalence assay AUPRC, and recall at fixed biological precision are deferred to TU-C.

Confidence intervals use 2,000 paired clustered bootstrap replicates at the sequence-component level with seed `20260803`, with source/publication, assay/batch, and query-protein sensitivity resampling. Repeated records and proteins are not independent trials.

A headline axis requires at least 500 held-out released-positive pairs and 50 independent sequence components. A quantitative control-panel stratum requires at least 100 evaluable records and 10 components. Smaller results are descriptive and may not be pooled to hide failure.

## 12. Effect on novelty

PU learning itself is established methodology and is not a novelty claim. This audit does not make the sequence backbone, joint encoder, cross-attention, or PU loss novel.

The potentially distinctive contribution remains the integration of:

- explicit selection, evaluability, technical-state, and assay-observation semantics;
- construct/orientation-aware evidence records;
- symmetric biological scoring with separate asymmetric assay diagnostics;
- a unified C1/C2/C3, homology, time, source, assay, and exposure-control ladder; and
- uncertainty- and provenance-aware hypothesis prioritization.

Any “first” or “unique” wording remains prohibited pending a formal scoping review and empirical success.

## 13. Residual risks

The PU-R design does not solve all scientific problems.

- Released positives are selected non-randomly; models can learn assayability, clone availability, study selection, or source visibility.
- Hidden positives contaminate the unlabeled pool.
- The class prior is unknown.
- Reference sequences are not exact assayed constructs.
- PLM exposure can inflate apparent generalization.
- Later evidence can share sequence families, interfaces, or source history with training.
- No laboratory experiment can resolve or confirm predictions.
- A successful ranking score can still fail to transfer outside its frozen evidence process.

These risks are managed by claim limits, source/assay/temporal holdouts, strict clustering, sensitivity analyses, shortcut baselines, clustered uncertainty, and protected tests—not claimed away.

## 14. Blueprint amendment required

If approved, the amendment will:

- replace the current primary calibrated HuRI endpoint with PU-R ranking;
- defer assay calibration and natural-prevalence AUPRC to TU-C;
- remove a calibrated assay predictor from the minimum-success definition while the tested-universe gate is closed;
- reinterpret random/matched-negative BCE as pseudo-negative diagnostics;
- keep the compatibility score explicitly non-probabilistic;
- keep the strict construct and structural tiers inactive;
- preserve the no-laboratory claim ceiling and Arrhenius/Apptainer requirement; and
- require an eligibility and sequence-component audit before evidence indicators or splits.

The original Version 3 blueprint remains authoritative until the expert group approves the proposed amendment.

## 15. Requested expert-group decision

The recommended decision is to approve the PU-R amendment and authorize only the next label-free eligibility/sequence-component audit.

Approval would not authorize:

- positive/unlabeled indicator construction;
- pseudo-negative sampling;
- split construction;
- structural mapping;
- model implementation; or
- model training.

Those activities require the post-approval eligibility audit and a subsequent gate confirmation.

If the expert group does not approve the amendment, the model programme should pause. The project can still release the validated evidence warehouse and this source-audit result, but it cannot honestly proceed with the original calibrated primary endpoint.

## 16. First action after approval

The first action will be `benchmark_eligibility_and_sequence_component_audit_v1`:

1. freeze the eligibility schema and source hashes;
2. enumerate reference-sequence-eligible Space III proteins and compute the
   candidate count without materializing candidate-pair rows;
3. quantify every mapping exclusion without imputation;
4. construct and independently validate 40%, 30%, and 20% sequence components;
5. report only aggregate positive-mapping and component-size distributions to
   assess whether a later split is likely to meet minimum sizes, without
   emitting pair-level evidence indicators or C1/C2/C3 assignments; and
6. return to the gate before materializing candidate pairs or constructing
   evidence indicators, sampled unlabeled sets, or splits.

## 17. Current authorization state

At report close:

| Activity | Authorized |
|---|---:|
| Metadata audit acceptance | Yes |
| Benchmark/estimand policy proposal | Yes |
| Expert review of amendment | Yes |
| Candidate eligibility construction | No |
| Positive/unlabeled indicator construction | No |
| Binary label construction | No |
| Split construction | No |
| Structural mapping | No |
| Model implementation | No |
| Model training | No |
