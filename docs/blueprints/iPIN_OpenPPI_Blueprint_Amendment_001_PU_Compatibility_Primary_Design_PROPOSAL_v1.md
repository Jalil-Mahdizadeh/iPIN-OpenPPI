# Blueprint Amendment 001: PU compatibility as the primary design

**Version:** 1.0 proposal
**Date:** 2026-08-03
**Status:** Proposed for expert-group approval; not effective
**Parent document:** `docs/blueprints/iPIN_OpenPPI_Final_Computational_Blueprint_and_Workflow_v3.md`
**Machine-readable policy:** `configs/benchmark_estimand_policy_proposal_v1.yaml`
**Evidence report:** `docs/reports/m0/M0_Systematic_Screen_Metadata_Audit_and_Benchmark_Estimand_Proposal_v1.md`

## 1. Approval boundary

This amendment changes a frozen primary target and therefore cannot be activated by the execution owner alone.

Until the expert group explicitly accepts it:

- Version 3 remains authoritative;
- this document is a review proposal only;
- ISSUE-0003 remains open;
- no candidate universe, evidence indicator, pseudo-negative sample, split, structural mapping, or model may be constructed; and
- no training or model-selection run may start.

If accepted, the amendment authorizes only the label-free eligibility and sequence-component audit in Section 16. A further gate is required before positive/unlabeled indicators, candidate samples, or splits are built.

## 2. Reason for amendment

Version 3 defined the primary calibrated endpoint as the probability of an observed positive in a defined systematic binary assay/search space conditional on an evaluable test.

The validated public-source audit found:

- 220,934 HuRI/HI-II-14 evidence rows, all positive;
- zero primary HuRI negative evidence rows;
- 52,548 HuRI pair-view rows and 52,569 positive Table 9 rows;
- positive detection histories but no complete failed-opportunity denominator;
- no pair-level log of all selections, attempts, evaluability states, technical exclusions, and outcomes;
- selected control and validation panels whose non-detections are conditional, not population negatives;
- 939 IntAct source negatives outside a systematic HuRI universe; and
- zero construct-confidence A/B rows in the accepted reconciliation.

The independent audit gate passed 71 checks with zero failures and three expected blocker warnings. The complete public attempted/evaluable universe is not reconstructable. Consequently, the original endpoint and its natural-prevalence calibration metrics are not identified.

## 3. Amendment decision proposed

Replace the current active primary endpoint with a reference-sequence positive–unlabeled ranking estimand.

The primary model output becomes a symmetric sequence compatibility/prioritization score. It is evaluated by recovery and ranking of held-out released positive evidence among a frozen candidate/unlabeled universe.

The following remain defined but inactive:

- calibrated assay-positive probability;
- binary positive/negative HuRI benchmarking;
- absolute latent compatibility probability;
- strict construct benchmarking;
- structure-derived labels; and
- interface-supervised modeling.

They reactivate only through the future gates in Sections 13 and 14.

## 4. Locked scope after approval

| Decision | Amended choice |
|---|---|
| Species | Human |
| Interaction type | Direct, binary, heteromeric physical compatibility |
| Input | Two frozen reference amino-acid sequences |
| Biological unit | Unordered pair of distinct frozen reference-sequence hashes |
| Evidence unit | Source record with construct, orientation, assay/version, batch, repeat, technical state, and outcome |
| Candidate population | Reference-sequence-eligible pairs from frozen HuRI Space III membership |
| Positive state | Qualifying released direct-positive evidence visible by the axis-specific cutoff |
| Other eligible pairs | Unlabeled; never negative by absence |
| Primary output | Symmetric compatibility/prioritization score |
| Active calibration claim | None |
| Wet-lab validation | Unavailable |
| Execution | Arrhenius only through accepted ARM64 Apptainer SIFs |

Homomers, unary/n-ary records, nonprotein molecules, ambiguous reference mappings, and pairs outside the frozen candidate population remain excluded from the primary task.

## 5. Variables and estimands

Let \(X_{AB}\) be permitted frozen features for pair A–B.

Let \(R_{AB}=1\) indicate qualifying released positive evidence by the applicable information cutoff. Let \(R_{AB}=0\) mean unlabeled.

Let \(Y_{AB}\) represent latent direct compatibility in a relevant biochemical context. \(Y\) is not observed and is not identified as a probability from the current data.

The primary estimand for symmetric score \(f\) is:

\[
\theta(f)=P[f(X^{R=1})>f(X^{R=0})]+\tfrac{1}{2}P[f(X^{R=1})=f(X^{R=0})],
\]

under the frozen held-out-positive and deterministic unlabeled sampling distributions.

The query-retrieval estimand is the rank of a held-out released-positive partner within the relevant eligible partner universe.

Neither estimand identifies biological precision, specificity, false-positive rate, universal binding probability, or calibrated assay-positive probability. Feature-dependent release and selection remain part of what can influence the observed estimand.

A selected-completely-at-random or constant-labeling-propensity assumption is prohibited unless a later, independently validated analysis justifies it in a specifically bounded subset.

## 6. Output semantics

### 6.1 Active output

The active biological output is a score satisfying exact swap symmetry:

\[
f(A,B)=f(B,A).
\]

Permitted wording is “sequence compatibility score”, “prioritization score”, or “released-evidence recovery score” with the declared evidence and candidate domain.

The score must not be called a probability.

### 6.2 Diagnostic output

A model may estimate propensity for \(R=1\) within an explicitly defined sampled dataset as a diagnostic. That value is conditional on the artificial sampling and source-release process and is not a headline output.

### 6.3 Inactive output

An orientation- or assay-specific probability is inactive while the tested-universe gate is closed. Selected control-panel outcomes do not reactivate it.

## 7. Evidence-state rules

The following rules are binding:

- released qualifying positives may become positive evidence indicators only after construction is authorized;
- unreported eligible pairs are unlabeled;
- explicit source negatives remain conditional on their exact assay, construct, orientation, batch, technical state, and sampling design;
- technical failure, invalid, autoactivating, blank, ambiguous, outside-space, and untested states remain distinct;
- conflicts retain all source records;
- random reference controls remain sampled controls; and
- no state is promoted to universal noninteraction.

Table 15 non-detection is a sensitivity diagnostic. It is not a negative label.

The 939 IntAct negatives are excluded from the primary negative role. A future source-scoped diagnostic requires its own construct, evaluability, and sampling audit.

## 8. Benchmark ladder

### 8.1 PU-R: primary reference-sequence PU ranking

PU-R is the proposed primary tier. It uses held-out released positives and eligible unlabeled candidates. It supports ranking, recovery, transfer, and uncertainty claims, not calibration or biological classification claims.

### 8.2 CP-D: conditional-panel diagnostics

Tables 5, 6, 8, 12, 13, 15, and 16 form protected secondary panels for:

- Y2H orientation and assay-version sensitivity;
- technical-state frequencies;
- literature-pair recovery;
- MAPPIT/GPCA orthogonal recovery;
- score stratification; and
- sensitivity versus Y2H detection history.

Protected records may not be reused for training. Panel `0` values remain conditional non-detections.

### 8.3 TU-C: future calibrated tested-universe tier

TU-C is inactive. It may activate only under Section 13.

### 8.4 SC-S: future strict construct/structural tier

SC-S is inactive. It may activate only under Section 14.

## 9. Candidate sampling and prevalence

The exact eligible population is frozen before evidence indicators or splits.

The unlabeled pool contains eligible pairs without visible qualifying positive evidence at the axis-specific cutoff. Held-out source and future temporal labels must be invisible to construction and candidate exclusion.

When full-candidate evaluation is not feasible, candidates are sampled uniformly without replacement by deterministic SHA-256 hash within split and stratum. The public salt is `ipin-openppi-benchmark-v1`. Inclusion probability and sampling weight are mandatory fields.

Random-negative and matched-negative BCE remain in the baseline ladder only as pseudo-negative shortcut diagnostics. Their optimization targets are not scientific negative labels.

The positive class prior is unknown. No point prevalence is identified. Before model results, sensitivity values will be frozen on a log-spaced grid from the observed released-positive fraction to 0.05. Results at every grid value are reported.

## 10. Sequence components and partition design

No partition is created by this amendment.

After the eligibility audit is authorized, frozen sequences are connected when an alignment:

- meets the relevant identity threshold; and
- covers at least 80% of each sequence.

Deterministic connected components are constructed at 30% identity for the primary analysis and at 40% and 20% for sensitivity analyses. Tool version, full commands, parameters, alignment database, and hashes are frozen.

Entire components are the assignment units. Proposed target fractions are:

- train: 70%;
- development: 15%; and
- protected test: 15%.

The deterministic seed is `20260803`.

Partition optimization may use component size and pre-model source/assay/time counts. It may not use any model output, performance result, or protected-test statistic.

C1, exclusive C2, and C3 retain their Version 3 definitions. Reverse pairs, pair-level evidence groups, close homologues, construct variants, and applicable source/study/batch groups remain co-located.

The 30% C3 result is a combined headline stress test only if it retains at least 500 held-out released-positive pairs, 50 independent sequence components, and meaningful evidence diversity. Otherwise it is demoted before modeling and the separate prespecified axes remain primary.

## 11. Temporal, source, assay, species, and interface axes

Required active axes are:

- C1, exclusive C2, and C3;
- 30% primary and 40%/20% sequence sensitivity;
- complete-information-cutoff temporal evaluation;
- held-out source;
- held-out assay version; and
- human primary evaluation.

A complete information cutoff freezes database releases, publications, sequences, structures, PLMs and documented corpora, teachers, predicted sources, and candidate-generation rules.

Yeast/E. coli transfer stays inactive until a separate source-eligibility policy passes.

The structural-interface axis stays inactive because ISSUE-0005 remains open and strict construct A/B coverage is zero. “Interface unknown” may be reported as metadata; it is not a constructed structural class.

## 12. Metrics, uncertainty, and minimum sizes

### 12.1 Primary metrics

- positive–unlabeled pairwise concordance;
- held-out positive Recall@10, Recall@100, and Recall@1000;
- released-positive enrichment at frozen candidate fractions; and
- positive rank percentile.

Every result reports C1/C2/C3 separately, identity threshold, surviving positive pairs, eligible candidates, proteins, components, source/assay strata, nearest-training similarity, inclusion fractions, and weights.

### 12.2 Diagnostic metrics

Sampled positive-versus-unlabeled AUPRC/AUROC, release-propensity log loss, and graph metrics are diagnostic only and must name the artificial sampling prevalence.

### 12.3 Deferred metrics

The following are suspended until TU-C:

- natural-prevalence assay AUPRC;
- Brier skill;
- calibration slope and intercept;
- adaptive calibration error;
- log loss as a biological/assay probability score; and
- recall at fixed biological precision.

### 12.4 Prohibited interpretations

No PU-R metric may be called biological precision, biological specificity, false-positive rate, calibrated binding probability, calibrated assay probability, or proteome-wide precision.

### 12.5 Uncertainty

Use 2,000 paired clustered-bootstrap replicates at the sequence-component level with seed `20260803`. Source/publication, assay/batch, and query-protein resampling are required sensitivity analyses. Repeated proteins and evidence records are not independent trials.

### 12.6 Minimum sizes

A headline axis requires at least:

- 500 held-out released-positive pairs; and
- 50 independent sequence components.

A quantitative CP-D stratum requires at least 100 evaluable records and 10 components. Smaller analyses are descriptive and cannot be pooled to hide a failed threshold.

## 13. Future tested-universe activation gate

TU-C activates only if an official or investigator-provided reproducible source records, for at least 90% of the declared candidate opportunities:

- pair-level search-space membership;
- screen and run;
- ordered bait/prey constructs and orientation;
- selection and attempted state;
- technical evaluability;
- failure or exclusion reason; and
- observed outcome.

The remaining missingness must be characterized, source terms must permit reproducible project use, and an independent validator must pass.

Before this gate, binary negative labels and calibrated assay-endpoint claims are prohibited.

## 14. Future strict construct and structure gate

SC-S activates only if:

- at least 80% of the relevant strict evidence has construct confidence A or B;
- SIFTS and UniProt releases are aligned or a restricted exact-sequence subset is approved;
- every retained sequence and residue interval is proven valid;
- all descending or otherwise anomalous intervals are explained or excluded; and
- there are zero unresolved mappings in structure-derived labels.

Before this gate, strict construct labels, structure-derived labels, and interface-supervised training are prohibited.

## 15. Amended programme gates

### 15.1 Reference-evidence gate

The PU-R evidence branch passes only after the post-approval eligibility audit demonstrates:

- frozen provenance and license coverage meet Version 3 requirements;
- at least 90% of qualifying released-positive pairs have usable frozen reference-sequence mappings, or a further expert decision narrows the population;
- all missing, conflicting, and excluded mappings are reported;
- no technical or absent state is encoded as negative; and
- the exact candidate-universe semantics are independently validated.

The strict construct branch may remain blocked without blocking a reference-sequence-only PU-R pilot. It stays visibly inactive and cannot support strict-construct or structural claims.

### 15.2 Benchmark gate

The Version 3 leakage, temporal, reporting, minimum-size, protected-test, and baseline requirements remain. “Label” is replaced by “positive/unlabeled evidence indicator” where appropriate, without changing the prohibition on hidden-test inspection.

### 15.3 PU statistical gate

A final sequence model passes the PU statistical gate only if:

- on the qualifying 30% C3 axis, or C2 if C3 fails the prespecified minimum size, pairwise concordance improves by at least 0.02 absolute over the strongest applicable simple sequence baseline;
- the paired component-clustered 95% interval for that improvement excludes zero;
- improvement direction is consistent on at least one independent held-out source, assay, or temporal axis;
- ranking under every approved class-prior sensitivity value has Spearman correlation of at least 0.90 with the primary ranking;
- gain is not explained by protein degree, source identity, sequence length, or other shortcut-only controls; and
- the protected test is evaluated once after model freeze.

If neither C3 nor C2 meets the minimum size, the PU statistical gate cannot pass without another pre-result amendment.

Calibration criteria do not apply to PU-R.

### 15.4 Routing, retrieval, uncertainty, and computational-validation gates

Existing architecture-efficiency thresholds remain.

Retrieval recall thresholds remain Recall@1000 ≥ 95% and Recall@100 ≥ 80% for held-out released positives. They do not imply biological precision.

The uncertainty and computational-validation gates remain, with “precision” interpreted only as released-evidence recovery unless TU-C has activated. Any catalogue remains a computational hypothesis catalogue.

## 16. First post-approval work unit

Approval authorizes only `benchmark_eligibility_and_sequence_component_audit_v1`:

1. freeze eligibility fields, source versions, and hashes;
2. enumerate usable reference-sequence Space III proteins;
3. report every mapping exclusion and ambiguity;
4. compute the exact unordered candidate count without materializing candidate
   pair rows or calling the count tested;
5. construct deterministic 40%, 30%, and 20% sequence components;
6. report aggregate eligible-positive mapping and component-size distributions
   sufficient to assess whether a later split is likely to meet minimum sizes,
   without emitting pair-level evidence indicators or C1/C2/C3 assignments;
7. independently validate the artifact; and
8. return to governance.

This unit must not materialize the candidate-pair universe, construct \(R\),
pseudo-negatives, split assignments, structural mappings, models, or training
data.

## 17. Minimum successful programme after amendment

While TU-C and SC-S are inactive, the minimum successful programme becomes:

- a versioned evidence ontology and source system;
- a provenance-preserving evidence warehouse or reproducible manifests;
- a validated reference-sequence PU benchmark with immutable C1/C2/C3, homology, source, assay, and temporal axes;
- contamination and public-PLM exposure audits;
- complete simple and PU baseline ladders;
- a validated non-probabilistic symmetric compatibility/prioritization score;
- clustered uncertainty and shortcut audits;
- reproducible Arrhenius/Apptainer execution; and
- if retrieval gates pass, a computational hypothesis catalogue with required warnings.

A calibrated assay-specific predictor is not part of minimum success while TU-C is closed.

## 18. Publication and novelty wording

PU learning is not novel. The backbone, joint encoder, cross-attention, and local routing are not novel merely because this amendment uses them.

Permitted contribution wording remains focused on integrated evidence-generation semantics, provenance, conditional outcomes, leakage controls, and uncertainty-aware ranking.

Paper 1 becomes an evidence and positive–unlabeled benchmark paper. Paper 2 remains conditional on model, routing, retrieval, and computational-validation gates.

Every catalogue must state:

> These pairs are computationally prioritized hypotheses. They have not been experimentally tested or validated by the iPIN-OpenPPI project. Scores are conditional on the frozen evidence, candidate universe, sampling design, and model assumptions.

## 19. Unchanged binding decisions

This amendment does not change:

- computational-only scope;
- no experimental-validation claim;
- human direct heteromeric primary scope;
- evidence-record-first warehouse design;
- exact source and construct provenance;
- C1/C2/C3 definitions;
- temporal and PLM-exposure controls;
- protected final evaluation;
- Codex as execution owner;
- human approval of target, split, claim, release, and external communication changes;
- Arrhenius-only production execution;
- immutable ARM64 Apptainer images; or
- the prohibition on silent target, threshold, split, or claim changes.

## 20. Approval record required

Activation requires an accepted revision of `governance/decisions/DEC-0010-propose-pu-compatibility-primary-design.md` or a superseding accepted decision, followed by a gate record that explicitly authorizes Section 16.

Silence, absence of extra comments, code commit, audit acceptance, or continuation of metadata work does not itself activate this amendment.
