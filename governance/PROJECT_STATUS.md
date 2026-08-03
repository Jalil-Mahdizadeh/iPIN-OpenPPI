# iPIN-OpenPPI project status and restart checkpoint

**Checkpoint date:** 2026-08-03
**Execution environment:** NAISS Arrhenius; project computation must run through pinned ARM64 Apptainer images
**Scientific programme state:** Primary-source reconciliation accepted; benchmark and estimand design authorized

This file is the durable restart checkpoint. The authoritative gate details remain in
`governance/gates/gate_status_v8.yaml` and its cited decisions and evidence.

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

## Exact pause point

The next authorized unit is **benchmark and estimand design without label or split
construction**. Work had just started on the governing-document audit; no new data
transformation, labels, splits, benchmark manifests, model code, or training run was
started for this unit.

Resume in this order:

1. Audit the acquired and staged systematic-screen metadata, with special attention
   to HuRI selection, attempted-pair membership, orientation, evaluability, technical
   state, and explicit negative/control semantics.
2. Resolve or formally disposition
   `governance/issues/ISSUE-0003-huri-attempted-pair-universe.md`. Do not infer that a
   pair absent from HuRI positive lists is negative. If no auditable pair-level screen
   log exists, make the PU/latent-observation fallback the proposed primary design.
3. Account explicitly for
   `governance/issues/ISSUE-0005-sifts-uniprot-release-alignment.md` and the observed
   zero strict construct-A/B coverage when defining admissible benchmark tiers.
4. Draft a benchmark/estimand policy proposal defining the target population,
   observation unit, estimands, admissible evidence states, unknown and technical-
   failure handling, prevalence treatment, C1/C2/C3 and sequence-cluster axes,
   temporal/assay/source/interface tests, leakage controls, metrics, uncertainty, and
   minimum-size rules.
5. Validate the proposal against the final blueprint, open issues, accepted source
   artifacts, and gate thresholds. Then prepare a decision record and the next gate
   update for approval before constructing labels or splits.

## Active prohibitions

Until the benchmark/estimand policy is approved and the governing blockers are
resolved or formally amended:

- do not construct binary labels;
- do not convert unreported or technically failed opportunities into negatives;
- do not construct or freeze data splits;
- do not perform structural mapping that assumes unresolved release alignment;
- do not train or select models; and
- do not weaken the strict construct or leakage criteria silently.

## Required execution discipline

- Keep raw, staged, canonical, and derived layers separate and immutable by version.
- Execute project software through the applicable pinned Apptainer SIF on Arrhenius.
- Record commands, manifests, checksums, container identity, validation results, and
  decisions before advancing a gate.
- Preserve computational-only claims: the programme has no laboratory-validation
  capability and must not imply experimental confirmation.
