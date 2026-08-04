# DEC-0014: Proposed disposition of the Lambourne human Y2H-v1 panel

**Date:** 2026-08-04

**Status:** Proposed; awaiting expert-group decision; not effective

**Proposal owner:** Codex under delegated project-execution authority

**Controlling authorization:** `DEC-0013`

## Proposed decision

Accept the bounded Lambourne human Y2H-v1 pair-semantics audit as technically
complete, while retaining the complete panel and all outcomes in a quarantined,
external-only audit role.

Do **not** authorize benchmark integration at this decision. Instead, retain
the exact-pair-disjoint, reference-usable evaluable stratum as a candidate for
a future protected assay-specific diagnostic. Any such integration would
require a new expert-approved protocol after resolution or explicit waiver of
`ISSUE-0007` and `ISSUE-0008`.

If the expert group accepts this proposal, it may separately authorize
resumption of the paused
`benchmark_eligibility_and_sequence_component_audit_v1` at its prior checkpoint.
Acceptance must not be read as authorization to use Lambourne outcomes, build a
benchmark split, or begin model work.

## Evidence proposed for technical acceptance

| Evidence | Result or SHA-256 |
|---|---|
| Scientific report | `docs/reports/m0/M0_Lambourne_2026_Human_Y2H_Pair_Semantics_Audit_Final_v1.md` |
| Production audit report | `361fe5bcc98e782b1cc36f3111f00865a5db9f025b01f0c1719b6a11eb60a836` |
| Independent validation report | Pass: 15/15, SHA-256 `bd7812eede90f8cf0fac62a1690c8164115501476e7fa67b40470cf1673874d5` |
| Staging manifest | `4cb5608b5799a6baf4e2e05047d69a31f8a355827a58e88c3b42dd6d3b1b9911` |
| Canonical audit manifest | `3240c362fe05a7a68d579deccabdf8a608b43cbbf25ea0c7f703595698986d98` |
| Acquisition manifest | `7dc05ebe9a4173636b7cbdf02eaa631603be33688a75c972a4bbce97bb9444d2` |
| Raw verification report | `6c1024a6ad6879cbbff80dd02c8789a070b7ca99c98c232b4b3ad284eddf6cd7` |
| Production implementation commit | `77cc6bd4d8a5876d7ed31618a9daa6936644ac88` |
| Final validator commit | `eb33a297fc8ca3514e7ad013d019bb0bac7b89a0` |

## Findings proposed for acceptance

- The paper's exact 4,100-pair claim is not publicly reconstructable. The
  archived Zhang selection contains 4,133 rows and 4,130 unique unordered ORF
  pairs; no source-supported rule identifies 30 exclusions.
- The 3,222 final-analysis subset is exactly reproduced with zero membership
  disagreements against later Science Data S3.
- Final outcomes are 376 positive, 2,300 assay-negative, 478 failed sequence
  confirmation, 41 autoactivator, and 27 test failed. The last three states are
  technically unevaluable and are not negative.
- Exactly 3,221 final pairs have two unique frozen human UniProt `2026_02`
  mappings. One pair contains the ambiguous accession `P01562`.
- Current permitted direct/pair-view evidence overlaps 780 final pairs. Frozen
  IntAct negative overlap is zero; Negatome overlap is 18. No source was merged
  or used to relabel another source.
- IMEx preview `IM-30553` is a dated, mixed-assay provider representation, not
  IntAct Release 252 and not an attempted-negative ledger. It matches all 402
  positive Zhang assay pairs plus two source-discordant pairs tracked in
  `ISSUE-0008`.
- Exact-pair decontamination leaves 2,010 evaluable pairs: 43 positive and 1,967
  negative. This is numerically adequate only for a protected assay-specific
  diagnostic.
- The UniRef90 endpoint-disjoint stratum has 157 pairs and zero positives.
  Sequence-family or unseen-protein generalization is not supported.

## Proposed scientific disposition

1. Preserve the 3,222 final panel as an immutable external audit source.
2. Preserve the full 4,046 tested Zhang rows and 4,130 public candidate pairs
   for denominator/provenance accounting.
3. Do not use Lambourne outcomes in training, tuning, model selection, router
   selection, calibration fitting, or threshold selection.
4. Do not merge the observations with Negatome or IntAct negatives.
5. Do not describe negative observations as nonbinding outside the reported
   Y2H-v1 construct, orientation, and condition.
6. Do not claim sequence-family generalization from this panel.
7. Require a separate benchmark protocol and new decision before any metric,
   split, row eligibility set, or integration is constructed.

## Conditions for any later benchmark protocol

A future proposal must explicitly address:

- whether the estimand is the public 3,222 later-filtered subset despite the
  unresolved 4,100 claim;
- disposition of the two IMEx/Data 22 discrepancies;
- a newly frozen training-evidence snapshot and exact pair/family overlap audit;
- external-only outcome isolation from every training and selection path;
- technical-state denominator rules;
- imbalance-aware descriptive metrics; and
- claim text limited to Y2H-v1 assay-observation recovery.

## Continuing prohibitions

This proposal does not authorize labels, candidates, evidence indicators,
benchmark rows, C1/C2/C3 assignments, splits, model implementation, training,
selection, calibration, release, universal-nonbinding claims, or experimental-
validation claims.

## Expert-group action required

The expert group should record one of the following in a new effective decision:

- accept the recommended technical-acceptance-and-quarantine disposition;
- reject all future benchmark use while accepting the audit record; or
- request a specified revision or additional source clarification.

Silence or absence of comments is not treated as acceptance of this proposal.
