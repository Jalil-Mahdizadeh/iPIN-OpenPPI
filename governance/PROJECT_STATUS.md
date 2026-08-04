# iPIN-OpenPPI historical restart checkpoint

**Checkpoint date:** 2026-08-03
**Execution environment:** NAISS Arrhenius; project computation must run through pinned ARM64 Apptainer images
**Scientific programme state:** Systematic-screen audit validated; PU benchmark amendment proposed and awaiting expert-group approval

> **Superseded on 2026-08-04.** The current restart checkpoint is
> `governance/PROJECT_STATUS_v12.md`; the current authoritative gate is
> `governance/gates/gate_status_v12.yaml`. The text below is retained only as
> immutable evidence of the pre-acceptance pause.

This file is the durable restart checkpoint. The authoritative gate details remain in
`governance/gates/gate_status_v9.yaml` and its cited decisions and evidence.

## Completed and accepted

- Project/container initiation and single-/four-GPU qualification passed.
- Primary raw acquisition was accepted with documented source-representation warnings.
- Primary evidence staging was accepted after independent validation.
- Primary source reconciliation was accepted in `DEC-0009` after independent validation:
  5 canonical tables, 46 Parquet files, 4,297,000 rows, 152 validation passes,
  0 failures, and 4 documented warnings.
- The production reconciliation manifest SHA-256 is
  `6408c6be771ac6a957e443d8c848b66789ca47230ae372b7ec3f3390ab7a6932`.
- The accepted reconciliation implementation commit is
  `d66d990a16592eb469f1b58643d982cb936c9083`; the acceptance/report commit is
  `ae0f72be7bbb19f623c131c1b03a93affe83e406`.
- The systematic-screen audit completed from clean commit
  `7af9473c876e53b777cf6ee829bbcbdf85c49fe4`.
- Its immutable audit SHA-256 is
  `db75b0cb2863cc1b44e45759e924bfc4b00d379fa291873e7e3e10e99748fc5e`.
- Its independent validation passed 71 checks, failed 0, and recorded 3 expected
  blockers; validation SHA-256 is
  `2ca92051172b7a7a512072f3ed6212ac8caed5891870abcea7c6e5929cd56a01`.
- The audit established that current public HuRI data do not reconstruct the
  complete selected/attempted/evaluable universe. The original calibrated
  primary assay endpoint is therefore infeasible from current public data.
- The non-effective PU proposal package was frozen at clean commit
  `b030c5a593de9f9bbba3a1ece3f122ab47a624dd`.
- Its production consistency report passed 42 checks, failed 0, and recorded 3
  expected warnings. The report is
  `artifacts/validation/benchmark_design/benchmark_estimand_policy_proposal_v1/VALIDATION_REPORT.json`
  with SHA-256
  `9abbf55e8050e700ae885c6c1143633bae3d9b66e942c690ae59931ba79a3e87`.
- That pass certifies proposal consistency only; the amendment remains
  unapproved and ineffective.

## Exact pause point

The metadata audit and independent validation are complete. A fully specified
reference-sequence positive–unlabeled ranking policy and Blueprint Amendment 001
have been prepared, but they are proposals rather than active policy.

The project is paused at a mandatory human-governance boundary:

- proposed policy:
  `configs/benchmark_estimand_policy_proposal_v1.yaml`;
- proposed amendment:
  `docs/blueprints/iPIN_OpenPPI_Blueprint_Amendment_001_PU_Compatibility_Primary_Design_PROPOSAL_v1.md`;
- expert report:
  `docs/reports/m0/M0_Systematic_Screen_Metadata_Audit_and_Benchmark_Estimand_Proposal_v1.md`; and
- proposed decision:
  `governance/decisions/DEC-0010-propose-pu-compatibility-primary-design.md`.

The next required event is expert-group acceptance, rejection, or requested
revision of Blueprint Amendment 001. No absence of extra comments is treated as
approval.

If the expert group accepts the amendment, the next authorized technical unit
will be only `benchmark_eligibility_and_sequence_component_audit_v1`: freeze
eligible Space III reference sequences, quantify mapping exclusions, compute
the candidate count without materializing pair rows, construct and validate
40%/30%/20% sequence components, and report only aggregate positive-mapping
and component-size feasibility. It must not emit pair-level evidence
indicators or C1/C2/C3 assignments, and it must return to the gate before any
candidate pairs, pseudo-negatives, splits, structures, or models are
constructed.

## Active prohibitions

Until the benchmark/estimand policy is approved and the governing blockers are
resolved or formally amended:

- do not construct the candidate universe before amendment approval;
- do not construct positive/unlabeled indicators or binary labels;
- do not convert unreported or technically failed opportunities into negatives;
- do not construct pseudo-negative samples;
- do not construct or freeze data splits;
- do not perform structural mapping that assumes unresolved release alignment;
- do not implement, train, or select models; and
- do not weaken the strict construct or leakage criteria silently.

## Required execution discipline

- Keep raw, staged, canonical, and derived layers separate and immutable by version.
- Execute project software through the applicable pinned Apptainer SIF on Arrhenius.
- Record commands, manifests, checksums, container identity, validation results, and
  decisions before advancing a gate.
- Preserve computational-only claims: the programme has no laboratory-validation
  capability and must not imply experimental confirmation.
