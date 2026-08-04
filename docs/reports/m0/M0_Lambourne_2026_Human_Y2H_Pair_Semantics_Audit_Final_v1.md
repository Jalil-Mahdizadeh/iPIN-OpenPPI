# M0 Lambourne 2026 human Y2H-v1 pair-semantics audit

**Version:** 1.0

**Date:** 2026-08-04

**Status:** Final technical audit; independently validated; governance
disposition pending

**Execution owner:** Codex

**Platform:** NAISS Arrhenius through the pinned ARM64 Apptainer image

**Scientific scope:** Acquisition, source reconciliation, assay semantics,
frozen-reference mapping, evidence overlap, contamination, and aggregate
feasibility only. No training labels, benchmark split, model, or universal
nonbinding assertion was produced.

## Executive judgment

The bounded Lambourne et al. 2026 human Y2H-v1 audit is technically complete.
All 11 approved Nature, Zenodo, and IMEx assets were acquired and independently
reverified. Immutable staging and canonical artifacts were produced, and the
independent production validator passed all 15 checks with zero failures and
zero warnings.

Five conclusions control the governance decision.

1. **The exact claimed 4,100-pair original universe is not reconstructable
   from the public archived files.** The archived selection table has 4,133
   physical `Zhang_et_al` rows and 4,130 unique unordered ORF pairs. Three rows
   are duplicates, but this still leaves 30 more unique pairs than the paper's
   stated 4,100. No deterministic, source-supported rule identifies 30 pairs
   to remove. The discrepancy must remain explicit.
2. **The final 3,222-pair analysis subset is exactly reconstructable.** It is
   the zero-disagreement intersection of the 4,046 reported Zhang assay rows
   with the later Science Data S3 prediction list. It contains 376 positive
   Y2H observations, 2,300 assay-bounded negative observations, and 546
   technically unevaluable observations.
3. **Frozen-reference coverage is almost complete but not perfect.** Of the
   3,222 final pairs, 3,221 map both participants uniquely to human UniProt
   `2026_02`; one pair has one ambiguous participant (`P01562`). Exact assayed
   insert sequences and boundaries are not reported pair-by-pair, so these are
   reference-sequence mappings, not construct-sequence confirmations.
4. **Current evidence contamination is substantial.** Exactly 780 final pairs
   overlap a qualifying direct-positive record or a permitted HuRI-family pair
   view. They include 333 of the 376 reported Y2H positives, 332 reported Y2H
   negatives, and 115 technical observations. After exact-pair exclusion and
   removal of the one unusable mapping, 2,441 observations remain: 43 positive,
   1,967 negative, and 431 technical. Only 157 are UniRef90 endpoint-disjoint,
   and none of those is positive.
5. **A narrowly protected assay-specific diagnostic is conditionally
   feasible; a sequence-generalization or biological-probability benchmark is
   not.** The exact-pair-disjoint evaluable stratum has 43 positives and 1,967
   negatives, exceeding the prespecified descriptive size floor. It can at
   most test recovery of a Y2H-v1 observation within this selected panel. It
   cannot identify universal binding, biological interaction probability,
   proteome-wide prevalence, calibration, orientation invariance, or unseen-
   family generalization.

The recommended disposition is therefore technical acceptance plus continued
quarantine. The panel may remain a candidate for a future protected,
assay-specific, exact-pair-disjoint diagnostic, but no integration should occur
until the expert group explicitly approves a separate protocol and resolves or
waives the 4,100-universe discrepancy and the two IMEx/Data 22 discrepancies.

## 1. Authority and claim ceiling

`DEC-0013` authorized this audit and paused the sequence-component audit. The
authorization permitted source-faithful parsing, deterministic mapping,
evidence overlap, contamination analysis, and aggregate feasibility reporting.
It prohibited:

- using any Lambourne outcome as a training label;
- merging Lambourne observations with Negatome;
- constructing benchmark splits;
- training, tuning, selecting, or evaluating a model;
- treating technical failure or `NA` as negative;
- interpreting a Y2H negative as universal nonbinding; and
- integrating the panel before returning to governance.

All prohibitions remain satisfied. The canonical row-level guards contain zero
authorized labels, zero benchmark-integration flags, and zero universal-
nonbinding assertions.

## 2. Reproducibility and independent validation

The production audit ran from clean commit
`77cc6bd4d8a5876d7ed31618a9daa6936644ac88`. The final independent validator
ran from commit `eb33a297fc8ca3514e7ad013d019bb0bac7b89a0` after three validator-only
defects were corrected. The original failed validation output is retained under
`artifacts/validation/lambourne_y2h_audit_v1/attempts/` as engineering
provenance; it did not alter the production datasets.

All scientific execution used:

- image: `containers/images/ipin-data-arm64_0.1.2.sif`;
- image SHA-256:
  `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`;
- architecture: `aarch64`;
- Python `3.12.3`; and
- frozen human UniProt release `2026_02`.

The complete test suite passed 125 tests in the pinned image.

| Record | Result | SHA-256 |
|---|---:|---|
| Production audit report | Complete; governance pending | `361fe5bcc98e782b1cc36f3111f00865a5db9f025b01f0c1719b6a11eb60a836` |
| Independent validation report | 15 pass, 0 fail, 0 warning | `bd7812eede90f8cf0fac62a1690c8164115501476e7fa67b40470cf1673874d5` |
| Staging manifest | 183,965 rows across five tables | `4cb5608b5799a6baf4e2e05047d69a31f8a355827a58e88c3b42dd6d3b1b9911` |
| Canonical audit manifest | 25,864 rows across five tables | `3240c362fe05a7a68d579deccabdf8a608b43cbbf25ea0c7f703595698986d98` |
| Acquisition manifest | 11 assets; 30,682,106,573 bytes | `7dc05ebe9a4173636b7cbdf02eaa631603be33688a75c972a4bbce97bb9444d2` |
| Independent raw verification | All 11 assets passed | `6c1024a6ad6879cbbff80dd02c8789a070b7ca99c98c232b4b3ad284eddf6cd7` |

The validator independently re-read the raw ZIP, Supplementary Data 22, and
all immutable Parquet outputs. It recomputed the source counts and raw/paper
crosswalk; verified file hashes, schemas, sidecars, table sets, and read-only
permissions; and independently recomputed all positive, negative, exact-pair,
UniRef90/50 pair, and endpoint overlays. It reported zero mismatched rows.

## 3. Acquisition, versioning, and license boundary

The article version of record is dated 2026-06-03 and identified by DOI
`10.1038/s41467-026-70942-x`. The archived code/input record is Zenodo record
`19118078`, version `v2.1`, version DOI `10.5281/zenodo.19118078`. IMEx study
`IM-30553` was frozen as provider preview snapshot `2026-08-04` because it was
curated but not yet integrated into IntAct services.

| Source asset | Bytes | SHA-256 |
|---|---:|---|
| Article methods supplement | 2,556,881 | `2fd7839258de28afeedcc4e2a02ebc5162c471ba3c021e993ef69b38a87cbc78` |
| Supplementary Data 22 | 264,313 | `d02ad6b31e6c80e758211cf6cb303982e6f29ad6d8fc86f671ce6a183493d43d` |
| Article source-data workbook | 5,988,321 | `dfc2053f69f9ccf3bac5951d54b3e57b7a721542a39f407c6511b6ea2e6caa8b` |
| Zenodo code archive v1.1 | 37,940,047 | `bd8608e18f384b93c633d6a5b17fc6832b2e202dc217c01b736d0fd3b9c00591` |
| Zenodo input archive v2.1 | 29,980,820,672 | `69a9d32219ebaa45170df0e986f0b2a87cb095d790d115b55651d5c14ffede8c` |
| IMEx HTML preview | 372,970,181 | `c1168fc6aa0bb138d5fb290e53e11e06ebafc1f15514fc63c09f7dc1029b915c` |
| IMEx PSI-MI XML 3 expanded | 242,545,085 | `c157a5855f4697f32d35c2f152d13da8a1fd75a2f996d489abf16cf22e47d3e1` |
| IMEx MITAB 2.7 | 25,178,098 | `f46ef395382df436f7473191fbee2a5d05a1e9aa4f2a8fbedb98e0a513ae4674` |
| IMEx MI-JSON | 13,819,166 | `a0b6554fae5722041d5a62c1f66568193695c4ad7e665132d664efbeb2b70e72` |

The Zenodo MD5 values for both archives were independently reproduced as well
as the project SHA-256 values. The code ZIP has 126 members. The input TAR has
160,370 members and was streamed without extraction; neither archive contains
an accepted unsafe path, symbolic link, or special-file escape. Sixteen bounded
members were selected for semantics. The three source tables duplicated between
the code and input packages are byte-identical. The article source-data workbook
contains 57 sheets.

The license determination in `SOURCE_LICENSE_REGISTER_v6.md` is:

| Material | Determination | Redistribution boundary |
|---|---|---|
| Nature article and included supplements/source data | CC BY 4.0 unless a separate third-party credit line applies | Attribution and credit-line review required |
| Zenodo record 19118078 v2.1, code v1.1, and input archive v2.1 | MIT | Preserve MIT notice, attribution, version DOI, and checksums |
| IMEx preview exports | IntAct data terms: CC BY 4.0 | Attribution required; identify as dated preview, not Release 252 |

Raw payloads remain outside Git. Any future public record-level derived release
requires a separate governance review. This is a conservative project
compliance determination, not legal advice.

## 4. Original selected-pair universe

The archived selection table contains 4,600 physical rows across three source
strata.

| Source stratum | Physical rows | Unique unordered ORF pairs |
|---|---:|---:|
| `Zhang_et_al` prediction pairs | 4,133 | 4,130 |
| `RRS_UniProt` | 242 | 242 |
| `Lit-BM-24` | 225 | 225 |
| **Global total** | **4,600** | **4,585** |

Twelve unordered pairs occur in more than one source stratum, so the
per-stratum unique counts are not additive. This cross-stratum overlap does not
change the 4,130 unique count within `Zhang_et_al`.

The paper describes 4,100 originally selected prediction pairs. The public
`Zhang_et_al` file instead has 4,133 rows, including three duplicate pair rows,
and therefore 4,130 unique unordered pairs. Deduplication does not resolve the
remaining +30 discrepancy. No hidden or alternate exact 4,100-pair selection
file was found among the 160,370 archived input members, and no source field
provides a defensible removal rule.

Every publicly listed Zhang pair is nevertheless accounted for:

| Public reconstruction state | Unique pairs | Selection rows | Paper assay rows | Final rows |
|---|---:|---:|---:|---:|
| Tested and retained in final analysis | 3,222 | 3,225 | 3,222 | 3,222 |
| Tested but excluded by later prediction-list intersection | 824 | 824 | 824 | 0 |
| No reported assay record | 84 | 84 | 0 | 0 |
| **Total** | **4,130** | **4,133** | **4,046** | **3,222** |

The three duplicate physical rows fall within final-analysis pairs. This audit
does not invent a unique-pair multiplier or silently count them twice.

The correct finding is therefore not “the exact 4,100 were reconstructed.” It
is: **the paper's 4,100 claim is recorded, the complete public archived
candidate universe is 4,130 unique pairs, and the +30 discrepancy is open.**
`ISSUE-0007` tracks the gap.

## 5. Exact final-analysis subset and outcome semantics

The final flag in Supplementary Data 22 is exactly reproduced by membership in
the later Science Data S3 pair list: 0 disagreements across the 4,046 Zhang
assay rows. The final subset is therefore exactly 3,222 pairs.

| Reported state | Count | Audit interpretation |
|---|---:|---|
| Positive | 376 | Y2H-v1 signal observed and positive-colony sequence confirmation passed |
| Negative | 2,300 | No Y2H-v1 interaction-selective signal after an evaluable attempt and SC-LW sequence confirmation |
| Failed sequence confirmation | 478 | Technically unevaluable; not negative |
| Autoactivator | 41 | Technically unevaluable bait autoactivation state; not negative |
| Test failed | 27 | Technically unevaluable assay failure; not negative |
| **Total** | **3,222** | **2,676 evaluable; 546 technically unevaluable** |

The conditional positive fraction among evaluable final attempts is
`376 / 2,676 = 14.05%`; the conditional negative fraction is `85.95%`. The
workflow recovery fraction retaining technical states in the denominator is
`376 / 3,222 = 11.67%`. The technical/unevaluable fraction is `16.95%`.
These are descriptive rates for this selected workflow, not estimates of human
PPI prevalence, assay sensitivity, or biological binding probability.

Across all 4,046 reported Zhang assay pairs, there are 402 positives, 2,916
negatives, 630 failed sequence confirmations, 59 autoactivators, and 39 failed
tests. The 824 later-filtered rows include all five outcomes, showing that the
final subset must be interpreted through its later prediction-list membership,
not as the complete originally selected panel.

The independently parsed 4,499-row raw assay table and 4,775-row Supplementary
Data 22 table have zero outcome-crosswalk disagreements. All 2,300 final
negatives have the required SC-LW confirmation flag; all 376 final positives
have the required 3AT confirmation flag. The raw flags remain separate fields.

## 6. Construct, orientation, assay, and condition provenance

The assay is the study's pairwise human Y2H version 1 (`MI:0397`, two hybrid
array). The source reports one selected orientation per pair.

| Role | Reported construct and host context |
|---|---|
| AD/prey | `pDEST-AD-CYH2`; N-terminal Gal4 activation domain residues 768–881; GGSNQ linker; truncated ADH1 promoter; CEN low-copy origin; TRP1; yeast strain Y8800 (MATa) |
| DB/bait | `pDEST-DB`; N-terminal Gal4 DNA-binding domain residues 1–147; SRSNQ linker; truncated ADH1 promoter; CEN low-copy origin; LEU2; yeast strain Y8930 (MATalpha) |

Diploids were selected on SC-LW. Interaction-selective growth used
SC-LW-His with 1 mM 3-amino-1,2,4-triazole. Bait autoactivation was assessed
against AD-null. Negative-colony sequence confirmation was sampled from SC-LW;
positive-colony confirmation was sampled from interaction-selective medium.
The paper reports 90% positive-sample and 83% SC-LW-sample confirmation
coverage at the workflow level.

Every canonical row preserves AD/prey and DB/bait orientation, CCSB ORF clone
IDs, source UniProt accessions, raw sequence-confirmation flags, construct
metadata, assay identifier, and experimental conditions. Exact assayed insert
sequences, clone-specific variants, and insert boundaries are not provided
pair-by-pair. Consequently, reference mappings must not be described as exact
construct mappings, and a single-orientation negative must not be generalized
to the reverse orientation or another assay condition.

## 7. Frozen human UniProt 2026_02 mapping

### All 4,046 reported Zhang assay pairs

| Participant mapping state | Participant rows |
|---|---:|
| Exact primary canonical | 8,084 |
| Exact isoform | 4 |
| Ambiguous frozen accession | 3 |
| Not in frozen human reference | 1 |
| **Total** | **8,092** |

### Final 3,222 pairs

| Participant mapping state | Participant rows | Distinct source accessions |
|---|---:|---:|
| Exact primary canonical | 6,439 | 3,171 |
| Exact isoform | 4 | 1 |
| Ambiguous frozen accession | 1 | 1 |
| **Total** | **6,444** | **3,173** |

Exactly 3,221 final pairs map both participants uniquely; one maps only one
participant uniquely. The sole ambiguous final accession is `P01562`, which is
a frozen secondary accession with two current human candidates
(`A0A087WWS6` and `P0DY56`). The audit retains both candidates and confidence D
rather than selecting one. Isoform identity is preserved, and no canonical
sequence is substituted for an explicitly reported isoform.

## 8. Overlap with current permitted evidence

The final 3,222 pairs were checked against the already validated frozen HuRI,
IntAct Release 252, permitted HuRI-family pair views, all 939 frozen IntAct
negative records, and the canonical Negatome audit. Counts below are pair counts
and are non-exclusive unless stated otherwise.

| Evidence overlay | Final pairs |
|---|---:|
| HuRI positive record | 464 |
| Permitted HuRI/HI-II-14/Lit-BM/Test-space pair view | 689 |
| IntAct positive record, including broader physical/association semantics | 991 |
| Any qualifying direct-positive record | 614 |
| Broader non-direct IntAct positive record | 912 |
| **Union used for exact future-training pair contamination: qualifying direct or permitted pair view** | **780** |
| Frozen IntAct explicit negative, among all 939 records | 0 |
| Negatome parent record | 18 |

The exact 780-pair contamination union contains 333 positives, 332 negatives,
and 115 technical observations. The near-equal positive/negative count inside
this overlap is a warning against treating current-database agreement as an
outcome relabeling rule. A positive record under another construct, method,
orientation, or context can coexist with a Y2H-v1 negative.

The IntAct-positive overlay includes 501 final Y2H-v1 negatives. These are
source/assay disagreements to preserve, not errors to vote away. Exact overlap
with the 939 frozen IntAct negatives is zero. Negatome overlaps 18 final pairs:
one Y2H positive, 15 Y2H negatives, and two technical observations. Lambourne
was not merged with either negative source.

## 9. IMEx/IntAct study IM-30553 semantics

The dated IMEx preview contains 9,595 unique interaction elements, 19,190
participants, and 4,520 feature elements. MITAB and XML counts agree. It spans
six detection-method strata:

| Detection method | Preview records |
|---|---:|
| MI:0397 two hybrid array | 4,909 |
| MI:1356 validated two hybrid | 1,970 |
| MI:1112 two hybrid prey pooling | 1,970 |
| MI:0231 MAPPIT | 389 |
| MI:2170 bimolecular luminescence complementation | 207 |
| MI:1203 split luciferase complementation | 150 |

The preview is a whole-paper, multi-assay and multi-species representation, not
a table of the human panel's attempted opportunities. All 9,595 MITAB negative
flags are missing. Missing does not mean negative. The preview therefore cannot
recover the 2,300 assay negatives or 546 technical states and cannot serve as a
negative denominator.

Exact reported-UniProt-pair reconciliation links 407 preview records to 404
distinct Zhang panel pairs. It captures all 402 positive Zhang pairs across the
4,046 tested rows and 378 distinct final-analysis pairs. It also contains three
preview records for two source-discordant final pairs:

- Data 22 reports `P24941`–`P61024` as failed sequence confirmation, while two
  MI:0397 human/human, yeast-host preview interaction records match the pair;
- Data 22 reports `Q99471`–`Q9UHV9` as negative, while one MI:0397 human/human,
  yeast-host preview interaction record matches the pair.

The audit preserves both representations and does not relabel either pair.
`ISSUE-0008` requests source clarification before any benchmark integration.
The IMEx preview remains separate from frozen IntAct Release 252 under
`ISSUE-0006`.

## 10. Pair and sequence-family contamination

Contamination is measured only against the frozen, currently permitted
positive/direct evidence that could enter future training. Lambourne outcomes
themselves were never added to that evidence.

| Final-pair audit stratum | Pairs | Positive | Negative | Technical |
|---|---:|---:|---:|---:|
| Exact sequence-pair overlap | 780 | 333 | 332 | 115 |
| Exact sequence-pair disjoint and reference-usable | 2,441 | 43 | 1,967 | 431 |
| UniRef90 pair overlap | 786 | 333 | 337 | 116 |
| UniRef90 pair disjoint and reference-usable | 2,435 | 43 | 1,962 | 430 |
| UniRef50 pair overlap | 795 | 333 | 342 | 120 |
| UniRef50 pair disjoint and reference-usable | 2,426 | 43 | 1,957 | 426 |

One final pair is absent from these complements because it lacks a usable
two-participant mapping.

Participant leakage is much more severe than pair leakage:

| Endpoint-disjoint stratum | Pairs | Positive | Negative | Technical |
|---|---:|---:|---:|---:|
| Exact sequence endpoint-disjoint | 159 | 0 | 133 | 26 |
| UniRef90 endpoint-disjoint | 157 | 0 | 131 | 26 |
| UniRef50 endpoint-disjoint | 154 | 0 | 129 | 25 |

There is no positive support for an unseen-sequence or unseen-family benchmark.
The panel can only be considered for a largely seen-protein, assay-transfer
diagnostic after exact-pair protection. Calling it a sequence-generalization
benchmark would be unsupported.

## 11. Protected external-benchmark feasibility

After exact-pair decontamination, the reference-usable evaluable stratum has:

- 2,010 pairs;
- 43 positive Y2H-v1 observations;
- 1,967 negative Y2H-v1 observations; and
- a conditional positive fraction of 2.14%.

This exceeds the prespecified descriptive floor of 40 positives and 100
negatives. It is therefore **numerically sufficient for a protected,
assay-specific, exact-pair-disjoint diagnostic**. This statement is deliberately
narrow. It does not authorize a benchmark and does not establish that the
diagnostic will be stable, representative, calibrated, or biologically
generalizable.

Before any future integration, a separate expert-approved protocol would need
to freeze at least:

1. whether the estimand is explicitly the public 3,222-pair later-filtered
   subset, despite failure to reconstruct the claimed 4,100 universe;
2. exact handling of the two IMEx/Data 22 discrepancies;
3. exclusion of technical observations from evaluable performance denominators
   while retaining them in workflow accounting;
4. exact pair/family leakage rules against the eventual training snapshot;
5. metric choice suitable for the severe 43:1,967 imbalance;
6. a permanent external-only role for Lambourne outcomes; and
7. wording limited to Y2H-v1 observation recovery in this selected panel.

No such protocol or split was constructed in this work package.

## 12. Identifiable and non-identifiable claims

| Claim | Identifiable? | Boundary |
|---|---|---|
| Final source counts and five outcome states | Yes | Exact for the frozen Supplementary Data 22 representation |
| Y2H-v1 signal fraction | Yes, conditionally | Among attempted and technically evaluable pairs in the frozen selected subset |
| Workflow recovery fraction | Yes, conditionally | Among all 3,222 final attempts with technical states retained |
| Mapping, current-evidence overlap, and contamination | Yes | Relative to frozen UniProt `2026_02` and the stated evidence snapshot |
| Assay-specific discrimination | Potentially | Only after a separately governed, protected, provenance-matched protocol |
| Exact original 4,100 public pair universe | No | Public archive yields 4,130 unique pairs and supplies no removal rule |
| Universal nonbinding | No | A single Y2H orientation/condition cannot establish it |
| Biological interaction probability | No | Selection, assay sensitivity, construct effects, and technical missingness are not separated |
| Calibrated unconditional probability | No | Sampling probabilities and a universal gold standard are unavailable |
| Proteome-wide prevalence | No | The pairs are model-selected, not a probability sample of human pairs |
| Orientation-invariant binding | No | One bait/prey orientation is reported per selected pair |
| Unseen-sequence/family generalization | No | UniRef90 endpoint-disjoint stratum contains zero positives |
| Causal superiority of an AI architecture | No | Candidate selection and later filtering are not randomized model comparisons |

The defensible language is “Y2H-v1 positive/negative observation under the
reported construct, orientation, selection, and confirmation workflow.” The
word “nonbinding” is not defensible for the 2,300 negatives without additional,
explicit evidence supporting that stronger claim.

## 13. Governance return and recommendation

The technical audit can be accepted as complete. The scientific recommendation
is to keep the panel quarantined and external-only. A later governance decision
may authorize design of a protected exact-pair-disjoint assay diagnostic, but
immediate benchmark integration is not recommended because:

- the original 4,100 universe is unresolved;
- two IMEx/Data 22 outcome discrepancies are unresolved;
- 333 of 376 final positives overlap current permitted training evidence;
- only 43 exact-pair-disjoint positives remain;
- no UniRef90 endpoint-disjoint positives remain; and
- all negative meanings are assay- and condition-specific.

The decision proposal is
`governance/decisions/DEC-0014-propose-lambourne-panel-disposition.md`. Until the
expert group records an explicit disposition, the previously paused sequence-
component audit remains paused and no benchmark or model work is authorized.

## 14. Artifact map

| Layer | Location |
|---|---|
| Source policy | `configs/source_policy_v3.yaml` |
| License register | `governance/licenses/SOURCE_LICENSE_REGISTER_v6.md` |
| Preacquisition manifest | `data/source_manifests/PREACQUISITION_lambourne_human_y2h_v1.yaml` |
| Acquisition manifest | `data/source_manifests/acquisitions/lambourne-y2h-v1-20260804T114500Z/ACQUISITION_MANIFEST.json` |
| Raw verification | `artifacts/validation/source_acquisition/raw_verification_lambourne_y2h_v1.json` |
| Audit configuration | `configs/lambourne_y2h_audit_v1.yaml` |
| Canonical schema | `schemas/canonical/lambourne_y2h_audit_v1.yaml` |
| Immutable staging | `data/staging/lambourne_y2h_audit_v1/` |
| Immutable canonical audit | `data/canonical/lambourne_y2h_audit_v1/` |
| Aggregate audit report | `artifacts/validation/lambourne_y2h_audit_v1/AUDIT_REPORT.json` |
| Independent validation report | `artifacts/validation/lambourne_y2h_audit_v1/VALIDATION_REPORT.json` |
| Audit implementation | `src/ipin_openppi/lambourne_audit/` |
| Independent validator | `src/ipin_openppi/validation/lambourne.py` |
