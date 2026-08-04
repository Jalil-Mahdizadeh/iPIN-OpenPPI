# iPIN-OpenPPI project status and restart checkpoint

**Checkpoint date:** 2026-08-04
**Execution environment:** NAISS Arrhenius; project computation must run through pinned ARM64 Apptainer images
**Scientific programme state:** Blueprint Amendment 001 accepted; negative-evidence discovery audit authorized

The authoritative gate is `governance/gates/gate_status_v10.yaml`.

## Completed and accepted

- Project/container initiation and single-/four-GPU qualification passed.
- Primary raw acquisition, evidence staging, and source reconciliation were
  independently validated and accepted through `DEC-0009`.
- The systematic-screen metadata audit passed 71 checks with zero failures and
  three expected blocker warnings. It established that current public HuRI data
  do not reconstruct a complete attempted/evaluable opportunity universe.
- The PU proposal consistency report passed 42 checks with zero failures and
  three expected warnings.
- The expert group explicitly accepted Blueprint Amendment 001 on 2026-08-04
  in `DEC-0011`. This satisfies ISSUE-0003 by estimand narrowing without
  claiming that the missing tested universe was recovered.
- Reference-sequence positive–unlabeled ranking with a non-probabilistic,
  symmetric compatibility/prioritization score is now the binding primary
  design.

## Current work unit

The active authorized work unit is `negative_evidence_discovery_audit_v1`.
Its controlling records are:

- accepted amendment:
  `docs/blueprints/iPIN_OpenPPI_Blueprint_Amendment_001_PU_Compatibility_Primary_Design_v1.md`;
- accepted policy: `configs/benchmark_estimand_policy_v1.yaml`;
- decision:
  `governance/decisions/DEC-0011-accept-blueprint-amendment-001-and-authorize-negative-evidence-audit.md`;
- source index: `data/source_manifests/PREACQUISITION_INDEX_v4.yaml`;
- source policy: `configs/source_policy_v2.yaml`; and
- license register: `governance/licenses/SOURCE_LICENSE_REGISTER_v4.md`.

The work unit acquires and versions all four Negatome 2.0 protein-pair datasets,
maps every record to frozen human UniProt `2026_02`, reconciles with all 939
frozen IntAct negative records and permitted current direct-positive evidence,
retains conditional provenance and isoform confidence, separates manual
experimental negatives from structural non-contact, tiers reliability, surveys
other systematic screens, evaluates PNU feasibility, validates the result, and
returns to governance.

After that return, `benchmark_eligibility_and_sequence_component_audit_v1` is
queued subject to the controlling gate.

## Active prohibitions

- No negative record is a universal nonbinding pair absent explicit evidence;
  no audited source currently provides such evidence.
- Do not merge manual experimental non-detections with PDB-derived non-contact.
- Do not infer missing constructs, orientation, conditions, or evaluability.
- Do not treat historical Negatome stringent membership as current
  conflict-free status.
- Do not redistribute raw or record-level Negatome data without permission.
- Do not materialize the candidate universe or construct evidence indicators,
  negative labels, pseudo-negatives, or splits.
- Do not construct structural training labels or implement, train, select, or
  release models.
- Do not imply experimental validation; the project has no laboratory work.

## Required execution discipline

- Keep raw, staged, canonical, derived, report, validation, and governance
  layers separate and immutable by version.
- Execute scientific software through the applicable pinned Apptainer SIF on
  Arrhenius.
- Record commands, manifests, checksums, container identity, validation results,
  and decisions before advancing a gate.
- Keep all user-authorized project materials within the organized repository
  tree and preserve raw-source redistribution boundaries.
