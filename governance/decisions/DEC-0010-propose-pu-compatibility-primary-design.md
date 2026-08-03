# DEC-0010: Propose PU compatibility as the primary benchmark design

**Date:** 2026-08-03
**Status:** Proposed for expert-group approval; not accepted
**Proposal owner:** Codex
**Approval owner:** iPIN-OpenPPI expert group
**Gate effect now:** Systematic-screen metadata audit accepted; no benchmark construction authority
**Gate effect if approved:** Authorize only the reference-sequence eligibility and sequence-component audit

## Proposed decision

Approve Blueprint Amendment 001 and adopt Resolution Path 3 of ISSUE-0003 as the definitive primary design for the current public-data project:

- use a reference-sequence positive–unlabeled ranking estimand;
- treat released qualifying HuRI positives as observed positive evidence;
- treat other eligible pairs as unlabeled rather than negative;
- make the symmetric sequence compatibility/prioritization score the active primary output;
- use selected Y2H/MAPPIT/GPCA panels only as conditional diagnostics;
- defer calibrated assay probability until a complete tested-universe gate passes; and
- defer strict construct and structural tiers until ISSUE-0005 and construct-coverage gates pass.

## Evidence

The production systematic-screen audit was generated from clean implementation commit `7af9473c876e53b777cf6ee829bbcbdf85c49fe4` inside the pinned Arrhenius Apptainer image.

- Audit: `artifacts/validation/benchmark_design/systematic_screen_metadata_v1/AUDIT_REPORT.json`
- Audit SHA-256: `db75b0cb2863cc1b44e45759e924bfc4b00d379fa291873e7e3e10e99748fc5e`
- Independent validation: `artifacts/validation/benchmark_design/systematic_screen_metadata_v1/VALIDATION_REPORT.json`
- Validation SHA-256: `2ca92051172b7a7a512072f3ed6212ac8caed5891870abcea7c6e5929cd56a01`
- Validation result: 71 pass, 0 fail, 3 expected blocker warnings

The audit established:

1. all 220,934 HuRI/HI-II-14 evidence rows are positive;
2. the primary HuRI release contains zero negative evidence rows;
3. positive detection histories do not enumerate failed or negative opportunities;
4. the complete selected/attempted/evaluable opportunity universe is absent;
5. selected-panel non-detections are conditional outcomes, not universal negatives;
6. 939 IntAct source negatives do not define the HuRI systematic universe;
7. strict construct-confidence A/B coverage is zero; and
8. the SIFTS/UniProt release-alignment blocker remains open.

## Scientific reasoning

The original calibrated endpoint requires a declared denominator of selected, attempted, technically evaluable assay opportunities. Without that denominator, absence from the positive release conflates biological and technical states with selection and reporting.

Constructing binary negatives would create unsupported labels, distort prevalence, invalidate natural-prevalence AUPRC, and make calibration uninterpretable.

A PU ranking estimand is the strongest defensible alternative. It directly measures recovery of held-out released evidence while keeping the non-random release process explicit. It does not identify absolute direct-binding probability or biological precision.

PU methodology itself is not novel. The potential contribution lies in integrating selection/evaluability semantics, construct and orientation provenance, conditional control panels, strict leakage axes, dependence-aware uncertainty, and non-probabilistic hypothesis prioritization.

## Alternatives considered

### A. Treat all unreported Space III pairs as negatives

Rejected. Public records do not show that every pair was selected, attempted, evaluable, and negative.

### B. Treat selected control-panel `0` values as general negatives

Rejected. These values are conditional on selected panels, constructs, orientations, assay versions, batches, and control sampling. Invalid and autoactivating states are separate.

### C. Use 939 IntAct negatives as the primary negative class

Rejected. They are heterogeneous source records without a systematic HuRI denominator or complete evaluability metadata.

### D. Reconstruct the screen universe as a Cartesian product

Rejected. Clone availability differs by assay version; autoactivating baits were removed; screen/run thresholds selected candidates; and only selected candidates were pairwise retested.

### E. Stop the entire project

Not recommended. The validated evidence warehouse, reference-sequence mappings, positive evidence scale, orthogonal panels, and leakage-controlled ranking design support a meaningful computational programme with narrower claims.

### F. Wait indefinitely for investigator data

Not recommended as the active plan. An official opportunity log would be valuable and could reactivate the tested-universe tier, but the current project must have an executable public-data design.

## Proposed activation sequence

If the expert group accepts this decision:

1. mark Blueprint Amendment 001 effective;
2. update ISSUE-0003 to “resolved by approved estimand narrowing” without claiming the tested universe was recovered;
3. authorize `benchmark_eligibility_and_sequence_component_audit_v1` only;
4. freeze eligible reference sequences and 40%/30%/20% components without
   materializing candidate-pair rows;
5. independently validate exclusions plus aggregate positive-mapping and
   component-size feasibility without constructing C1/C2/C3 assignments; and
6. return to governance before constructing candidate pairs, positive/unlabeled
   indicators, or splits.

## Explicit non-authorizations

This proposal and its current review state do not authorize:

- candidate-universe construction;
- positive/unlabeled evidence-indicator construction;
- pseudo-negative sampling;
- binary label construction;
- split construction;
- structural mapping;
- model implementation;
- model training;
- model selection; or
- a public probability or experimental-validation claim.

## Approval requested

The expert group should record either:

- **Accepted:** Blueprint Amendment 001 becomes effective and the eligibility/component audit is authorized; or
- **Rejected/Revision required:** the model programme pauses at the current validated evidence state until a scientifically valid target is approved.

No response, no extra comments, or continued repository work is not equivalent to acceptance.
