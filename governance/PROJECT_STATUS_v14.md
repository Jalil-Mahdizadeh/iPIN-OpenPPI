# iPIN-OpenPPI project status and restart checkpoint

**Checkpoint date:** 2026-08-04

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** Bounded 2025 TF-isoform Y2H semantics and
contamination audit authorized; sequence-component audit paused and unstarted

The authoritative gate is `governance/gates/gate_status_v14.yaml`.

## Accepted baseline

Work accepted through `DEC-0012` remains binding. The 2026 Lambourne panel
audit is complete and validated but remains quarantined with no benchmark or
training role. PU-R remains the unchanged primary design.

## Active work package

`DEC-0015` authorizes only the bounded audit of the Lambourne et al. 2025
TFIso1.0 pairwise Y2H dataset and separate N2H validation observations. The
active source index is `PREACQUISITION_INDEX_v6.yaml`; five minimal assets are
authorized. The two Zenodo deposits are CC BY 4.0. The public article PDF is
internal-audit-only and may not enter Git.

The audit must independently reconstruct technical states, investigate all
1,260 blank result cells without treating unresolved cells as negatives,
preserve exact clones and AD→DB orientation, reconstruct selection/filtering,
map to UniProt 2026_02, quantify all requested contamination views and matched
isoform contrasts, retain Y2H/N2H separation, and return a three-way
disposition with independent validation.

## Exact restart point

Freeze and validate the source-policy, license, and preacquisition package;
then acquire and checksum the five assets through the pinned container. Build
immutable staging/canonical audit artifacts and return the report, validator,
governance decision, gate ledger, and project status. Commit and push that
completed package, then resume
`benchmark_eligibility_and_sequence_component_audit_v1` under its original
scope.

## Binding prohibitions

- No TF-isoform outcomes may be used for training, tuning, calibration,
  thresholding, selection, or routing.
- Do not merge with Negatome or change PU-R.
- Do not construct a benchmark, rows, or splits.
- Do not turn blanks, unknowns, autoactivation, mating/expression failures, or
  any other technical state into negatives.
- Do not collapse exact constructs, AD→DB orientation, or Y2H/N2H assays.
- Do not infer universal nonbinding or imply experimental validation by this
  computational project.
