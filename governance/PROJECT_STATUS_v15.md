# iPIN-OpenPPI project status and restart checkpoint

**Checkpoint date:** 2026-08-04

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** 2025 TF-isoform Y2H audit complete and
validated; returned to governance; sequence-component audit paused and not
started at the project owner's explicit checkpoint

The authoritative gate is `governance/gates/gate_status_v15.yaml`.

## Completed in this work package

`DEC-0015` has been executed within scope. Exactly five governed source assets
were acquired and verified. Production ran from clean commit
`9de608ddc301d0af548d043c9fbd57b5c7e1b7f2` in the pinned data image. The
immutable audit passed and its independent validator passed 26 checks with no
warning or failure.

The expert report is
`docs/reports/m0/M0_TF_Isoform_2025_Y2H_Semantics_and_Contamination_Audit_Final_v1.md`.
The proposed disposition is in
`governance/decisions/DEC-0016-propose-tf-isoform-y2h-disposition.md`.

## Scientific result

The source is an **external-only diagnostic candidate**, not a current
benchmark. The public 9,562-row Y2H table contains 2,563 positive and 5,739
explicit negative assay observations. All 1,260 blanks resolve to technical
states and none is negative. The archived filters reproduce 3,593 attempts and
3,509 evaluable rows (2,330 positive, 1,179 negative), but the selection is
positive-conditioned and not prevalence-representative.

There are 848 fixed-partner positive-versus-negative evaluable isoform
contrast groups. Only 149 have all evaluable pairs mapped; 83 are protected at
the UniRef90 pair-signature level, but zero are protected at the exact-endpoint
or UniRef90-endpoint level. Therefore the panel cannot currently support an
unseen-protein or family-generalizing protected benchmark.

N2H remains a separate continuous assay. No threshold or binary label was
constructed. The study outcomes remain quarantined and have no training,
tuning, selection, calibration, routing, or benchmark role.

## Immutable production evidence

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

## Exact operational pause point

Do not resume `benchmark_eligibility_and_sequence_component_audit_v1` in the
current session. The project owner explicitly requested a pause after the
completed audit is committed and pushed because of the weekly Codex usage
limit. The sequence-component audit remains previously authorized but has not
started.

When the project owner asks to resume after the usage limit refreshes, first
read this status, the authoritative gate, and the dedicated post-push resume
checkpoint. Verify that local `main` equals `origin/main`, the worktree is
clean, the pinned SIF hash is unchanged, and the production validation report
still passes its checksum. Then resume only the previously authorized
sequence-component audit scope; do not repeat this TF-isoform audit.

## Binding prohibitions at pause

- No Lambourne 2025 or 2026 external-panel outcomes may be used for training,
  tuning, calibration, thresholding, selection, routing, or pseudo-labelling.
- Do not merge external-panel outcomes with Negatome or change PU-R.
- Do not construct benchmark rows, C1/C2/C3 assignments, or splits.
- Do not turn blank, unknown, autoactivation, mating/expression failure, or
  another technical state into a negative.
- Do not collapse exact constructs, orientation, or Y2H/N2H assay identity.
- Do not infer universal nonbinding or claim experimental validation.
