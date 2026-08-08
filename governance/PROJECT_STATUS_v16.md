# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-08

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** TF-isoform audit and `DEC-0016` disposition
technically accepted; external panel quarantined; previously authorized
sequence-component audit resumed from its unstarted checkpoint

The authoritative gate is `governance/gates/gate_status_v16.yaml`.

## Minimal governance disposition

`DEC-0017` accepts the completed 2025 TF-isoform Y2H/N2H audit and the
disposition proposed by `DEC-0016` as technically complete. This is a technical
acceptance of the immutable audit record and an acceptance of quarantine, not
authorization for integration or downstream construction.

The panel remains an **external-only diagnostic candidate**. It is unsuitable
for training negatives, universal-nonbinding claims, prevalence estimation,
calibration, or unseen-endpoint/family benchmarking. Its Y2H and N2H outcomes
have no training, tuning, thresholding, selection, routing, pseudo-labelling,
or benchmark role.

The audit, source acquisition, reconstruction, immutable Parquet artifacts,
validation, report, and disposition analysis are closed. Do not reopen,
recompute, or extend them.

## Immutable evidence accepted without recomputation

- production audit report SHA-256:
  `9235569bd40adc4114c0b1f4387e57fb4fcabc823a28a3509676607ef809a281`;
- independent validation SHA-256:
  `af9297e54203b7486a883eaa555d006dfac57da232f475f165395cf888f42327`;
- staging manifest SHA-256:
  `49221d602c1f2d966c451985604538c045fa9ffa8744363c35824aade7a9bffc`;
- canonical manifest SHA-256:
  `c71de2354bacfdef43b35d7f0ecbe07851568ab4abeb6a23df7065f1d8c39b68`;
- acquisition manifest SHA-256:
  `1c163f8cafaad152a49cc002af66a26a0779e9387a7cc9c3fca6bfaa56f60e96`;
- independent raw-verification SHA-256:
  `59c4536b3ed07f2c78349a7adbd52dce48c9ddd4e2b609d0a8440b6656ba9bf2`.

## Resumed work package

Resume only `benchmark_eligibility_and_sequence_component_audit_v1` from
`governance/checkpoints/RESUME-001-post-tf-isoform-audit.md`. The accepted
primary design remains reference-sequence positive-unlabeled ranking (PU-R).

The authorized unit is limited to freezing eligibility and tool semantics;
enumerating usable Space III reference sequences and every exclusion without
imputation; calculating the unordered candidate count algebraically without
pair materialization; constructing deterministic 40%, 30%, and 20% identity
components under bidirectional coverage; reporting aggregate positive mapping
coverage, exclusions, component sizes, and later-gate feasibility; and
independently validating the consequential counts and components.

## Binding prohibitions

- Do not materialize candidate-pair rows or call the algebraic universe tested.
- Do not construct positive/unlabeled or negative labels, pseudo-negatives,
  C1/C2/C3 assignments, partitions, or train/dev/test splits.
- Do not use external-panel outcomes or Negatome/IntAct-negative outcomes as
  training labels or merge external panels with Negatome.
- Do not construct structural mappings or structure-derived training labels.
- Do not implement, train, tune, calibrate, threshold, select, or route models.
- Do not change the accepted primary PU-R design.
- Do not infer universal nonbinding or claim experimental validation.
