# iPIN-OpenPPI project status and restart checkpoint

**Checkpoint date:** 2026-08-04

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** Lambourne human Y2H pair-semantics audit
complete and independently validated; expert-group disposition pending;
sequence-component audit paused and unstarted

The authoritative gate is `governance/gates/gate_status_v13.yaml`.

## Completed work package

The `DEC-0013` Lambourne audit has completed. All 11 approved Nature, Zenodo,
and IMEx assets were acquired and reverified. Immutable staging and canonical
artifacts were produced. The independent validator passed 15 checks with zero
failures or warnings. The expert-facing interpretation is
`docs/reports/m0/M0_Lambourne_2026_Human_Y2H_Pair_Semantics_Audit_Final_v1.md`.

The final 3,222-pair subset is exactly reconstructed as 376 positive, 2,300
assay-negative, and 546 technically unevaluable observations. The exact
original 4,100-pair claim is not publicly reconstructable: the archived
selection file contains 4,130 unique Zhang pairs. This remains open as
`ISSUE-0007`.

Frozen mapping resolves both participants uniquely for 3,221 final pairs.
Current permitted direct/pair-view evidence overlaps 780 final pairs. Exact-
pair exclusion leaves 43 positive and 1,967 negative evaluable observations.
The UniRef90 endpoint-disjoint stratum contains zero positives, so the panel
cannot support unseen-family generalization.

IMEx preview `IM-30553` remains a dated, non-integrated provider snapshot. It
does not encode attempted negative/technical states and contains two pair-level
discrepancies with Data 22, tracked in `ISSUE-0008`.

## Governance return

`governance/decisions/DEC-0014-propose-lambourne-panel-disposition.md` is a
proposal only. It recommends technical acceptance, continued quarantine, and
no immediate benchmark integration. It does not become effective without an
explicit expert-group decision.

## Exact restart point

Wait for the expert group to disposition `DEC-0014`. Do not resume the paused
sequence-component audit and do not begin benchmark integration while the
proposal is pending.

If the expert group explicitly accepts the recommended disposition and
authorizes resumption, continue
`benchmark_eligibility_and_sequence_component_audit_v1` from its prior
unstarted checkpoint under its original scope. That resumption still does not
authorize candidate pairs, labels, splits, models, or use of Lambourne outcomes.

If the expert group requests clarification, address only the specified source,
estimand, or governance question and issue a versioned replacement proposal.

## Binding prohibitions

- Do not use Lambourne outcomes as training, tuning, calibration, selection, or
  routing labels.
- Do not merge Lambourne with Negatome or IntAct negatives.
- Do not construct benchmark rows or splits without a new effective decision.
- Do not treat `NA`, failed sequence confirmation, autoactivation, test failure,
  absence, or unreported pairs as negative.
- Do not infer universal nonbinding or biological interaction probability.
- Do not claim unseen-sequence/family generalization from this panel.
- Do not present IM-30553 preview exports as IntAct Release 252.
- Do not imply laboratory or experimental validation by this computational
  project.

## Durable artifacts

- Production audit:
  `artifacts/validation/lambourne_y2h_audit_v1/AUDIT_REPORT.json`
- Independent validation:
  `artifacts/validation/lambourne_y2h_audit_v1/VALIDATION_REPORT.json`
- Staging: `data/staging/lambourne_y2h_audit_v1/`
- Canonical audit: `data/canonical/lambourne_y2h_audit_v1/`
- Source acquisition:
  `data/source_manifests/acquisitions/lambourne-y2h-v1-20260804T114500Z/`
