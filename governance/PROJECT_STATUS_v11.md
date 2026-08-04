# iPIN-OpenPPI project status and restart checkpoint

**Checkpoint date:** 2026-08-04

**Execution environment:** NAISS Arrhenius; project computation must run through
pinned ARM64 Apptainer images

**Scientific programme state:** Negative-evidence audit accepted; eligibility
and sequence-component audit authorized but not started

The authoritative gate is `governance/gates/gate_status_v11.yaml`.

## Completed and accepted

- Project/container initiation and single-/four-GPU qualification passed.
- Primary raw acquisition, evidence staging, and source reconciliation passed
  their independent validators and were accepted through `DEC-0009`.
- The systematic-screen metadata audit established that the current public
  HuRI release does not reconstruct a complete pair-level
  selected/attempted/evaluable universe.
- Blueprint Amendment 001 is accepted. The binding primary design is
  reference-sequence positive–unlabeled ranking with a non-probabilistic,
  symmetric compatibility/prioritization score.
- All four complete Negatome 2.0 pair datasets were acquired, versioned, and
  independently hash-verified under the internal-only redistribution boundary.
- `negative_evidence_discovery_audit_v1` completed through clean implementation
  commit `30220bd5e0fec5f6c259ba369f14b62a71530f3f`.
- Its production audit report SHA-256 is
  `ccefebc920ec5c3d1a04d271babbdee044608662ef88d87615a274d82f6e6315`.
- Its independent validation passed 43 checks with 0 failures and 0 warnings;
  validation SHA-256 is
  `e3b7b8da6fbb9d6361278e9d89ab1cdd070c087279a8a821dc852cfd5f4fc155`.
- The audit subgate is accepted in `DEC-0012`.

## Binding negative-evidence conclusions

- The 12,720 physical Negatome rows represent 6,568 parent observations after
  stringent membership is represented without double-counting.
- Exactly 1,630 parent observations have two unique frozen human mappings:
  1,408 manual experimental-negative and 222 structure-derived non-contact.
- All 939 IntAct negative records were enumerated; 453 have usable frozen human
  reference pairs.
- Exact Negatome–IntAct negative overlap is zero under the prespecified ordered,
  unordered, and frozen sequence-pair routes. This is not evidence of universal
  nonbinding or biological independence.
- Current permitted positive evidence conflicts with 237 fully mapped
  Negatome parent records. Historical stringent status is not current
  conflict-free status.
- Reliability tiers are ME-1 1,216; ME-2 192; SN-1 154; SN-2 68; and MX 4,938.
  Manual and structural families remain separate.
- A conservative manual diagnostic candidate contains 1,188 records, 1,163
  unique sequence pairs, and 315 publications. It is protected diagnostic
  evidence only; it has no authorized training-label role.
- Population-calibrated P+N+U remains unidentified. PU-R remains primary.
- No source supports a universal nonbinding class.

## Exact restart point

The next authorized unit is
`benchmark_eligibility_and_sequence_component_audit_v1`, and it has **not**
started. Its permitted outputs are limited to:

1. frozen Space III reference-sequence eligibility and exclusion accounting;
2. aggregate candidate count without materializing pair rows;
3. deterministic 40%/30%/20% sequence-component construction and aggregate
   size/connectivity feasibility; and
4. aggregate qualifying-positive mapping and minimum-size feasibility.

It must run through the pinned Apptainer image and return to governance. It may
not emit pair-level positive/unlabeled indicators, candidate-pair tables,
pseudo-negatives, labels, C1/C2/C3 assignments, splits, or models.

The Lambourne 2026 human Y2H panel is registered only as the highest-priority
future negative-evidence follow-up candidate. It is not authorized for
acquisition. A new source policy, preacquisition manifest, asset-level license
review, and pair-level semantics audit are required first.

## Active prohibitions

- No negative record is a universal nonbinding pair.
- Do not merge manual experimental non-detections with PDB-derived non-contact.
- Do not infer missing constructs, orientation, species, conditions, or
  evaluability.
- Do not treat historical stringent membership as current conflict clearance.
- Do not redistribute raw or record-level Negatome data without permission.
- Do not use the conditional diagnostic candidate as training negatives.
- Do not materialize the candidate universe or construct evidence indicators,
  negative labels, pseudo-negatives, or splits.
- Do not construct structural training labels or implement, train, select, or
  release models.
- Do not imply experimental validation; the project has no laboratory work.

## Required execution discipline

- Keep raw, staging, canonical, derived, report, validation, and governance
  layers separate and immutable by version.
- Execute scientific software through the applicable pinned Apptainer SIF on
  Arrhenius.
- Begin production work units from a clean tracked Git state and record the
  implementation commit in each manifest.
- Record commands, manifests, checksums, container identity, validation results,
  and decisions before advancing a gate.
- Keep all project materials in the organized repository tree and respect
  source-specific release boundaries.
