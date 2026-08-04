# DEC-0016: Proposed disposition of the 2025 TF-isoform Y2H panel

**Date:** 2026-08-04

**Status:** Proposed; awaiting expert-group decision; not effective for
benchmark integration

**Proposal owner:** Codex under delegated project-execution authority

**Controlling authorization:** `DEC-0015`

## Proposed decision

Accept the bounded 2025 human TF-isoform Y2H/N2H semantics and contamination
audit as technically complete. Assign the source the disposition
**external-only diagnostic candidate** and retain every outcome in quarantine.

Do not authorize a benchmark, split, label, threshold, integration, or model
use. The source is not currently a protected benchmark candidate because no
positive-versus-negative matched isoform group is disjoint from current
future-training exposure at the exact-endpoint or UniRef90-endpoint level.

The existing authorization for the separate sequence-component audit remains
unchanged, but execution is operationally paused by the project owner until a
future explicit resume request.

## Evidence for technical acceptance

| Evidence | Result or SHA-256 |
|---|---|
| Scientific report | `docs/reports/m0/M0_TF_Isoform_2025_Y2H_Semantics_and_Contamination_Audit_Final_v1.md` |
| Production audit report | Pass; `9235569bd40adc4114c0b1f4387e57fb4fcabc823a28a3509676607ef809a281` |
| Independent validation | 26 pass, 0 warning, 0 fail; `af9297e54203b7486a883eaa555d006dfac57da232f475f165395cf888f42327` |
| Staging manifest | 18,476 rows; `49221d602c1f2d966c451985604538c045fa9ffa8744363c35824aade7a9bffc` |
| Canonical manifest | 14,529 rows; `c71de2354bacfdef43b35d7f0ecbe07851568ab4abeb6a23df7065f1d8c39b68` |
| Acquisition manifest | Five assets; `1c163f8cafaad152a49cc002af66a26a0779e9387a7cc9c3fca6bfaa56f60e96` |
| Raw verification | Five assets passed; `59c4536b3ed07f2c78349a7adbd52dce48c9ddd4e2b609d0a8440b6656ba9bf2` |
| Production implementation commit | `9de608ddc301d0af548d043c9fbd57b5c7e1b7f2` |

## Findings proposed for acceptance

- The 9,562 public Y2H rows crosswalk exactly to raw records with zero outcome
  disagreements.
- The source contains 2,563 positive and 5,739 explicit negative Y2H
  observations. All 1,260 blank public results resolve to technical states:
  1,065 sequence-confirmation failures, 157 mating/spotting failures, 31 assay
  measurement failures, and 7 autoactivation records. None is negative.
- The archived analytical filter reproduces a 3,593-attempt universe and a
  3,509-row evaluable subset containing 2,330 positive and 1,179 negative
  observations. This subset is conditioned on previous positives and is not
  prevalence-representative.
- All 693 exact clone sequences are preserved; 444 match frozen UniProt
  `2026_02`. The archive exposes no exact DB partner plasmid sequences. Of 753
  DB ORFs, 706 have a unique indirect frozen HuRI/hORFeome mapping, 46 are
  unmapped, and one is ambiguous.
- The reported 3,509 subset has 1,978 reference-usable pairs. Of these, 458
  overlap permitted positive/future-training pairs, 1,112 overlap at the
  UniRef90 pair level, and every one has exact and UniRef90 endpoint exposure.
- There are 848 fixed-partner positive-versus-negative evaluable isoform
  contrast groups, including 708 represented in the reported analysis. Only
  149 are completely mapped; 90 are exact-pair protected, 83 are UniRef90-pair
  protected, and zero are exact- or UniRef90-endpoint protected.
- The 765 N2H records remain continuous and separate. The 262 selected isoform
  validation rows have Spearman `rho = 0.1001` between Y2H state and continuous
  N2H score. No N2H threshold or binary relabelling is supported.
- Zenodo code/input assets are CC BY 4.0 with attribution. The article PDF is
  internal-audit-only and may not be redistributed.

## Proposed permitted role

The source may remain an immutable, external-only object for source-semantics
research and for designing a later diagnostic protocol. “Candidate” does not
mean eligible now. A future protocol would need a new decision and must define
a fixed training snapshot, exposure strata, exact assay estimand, technical
denominator, and claims that do not exceed Y2H observation recovery.

## Continuing prohibitions

- No Y2H or N2H outcome may enter training, tuning, calibration, thresholding,
  routing, selection, or pseudo-labelling.
- Do not merge this source with Negatome or relabel between Y2H and N2H.
- Do not create benchmark rows, split membership, C1/C2/C3 assignments, or
  benchmark metrics under this decision.
- Do not interpret an assay negative as universal nonbinding.
- Do not claim prevalence, orientation invariance, endogenous binding,
  family-generalizing performance, or experimental validation of the model.
- Do not change the primary PU-R design.

## Expert-group action required

Record one of: accept the proposed quarantine disposition; reject any future
diagnostic role while accepting the audit record; or request a specified
revision. Silence is not acceptance and this proposal authorizes no benchmark
integration.
