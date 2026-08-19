# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Scientific programme state:** development was released exactly once and
verified; scoring is paused before its first row because `ISSUE-0009` exposed a
nullability-only Arrow concatenation defect

The authoritative gate is `governance/gates/gate_status_v33.yaml`.

## Released development state

The authorized release produced a deterministic archive at SHA-256
`c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122`.
Its development manifest has SHA-256
`3f58403138b878d912789f529dc1f8ec7d1db7356d6ccc4c3b88cfcb2f6554fa`
and registers 13 tables / 9,044,323 rows. A second decryption is prohibited.

## Scoring incident

The first `C3_development` loader call stopped before scoring because filtered P
and U Arrow fields had identical names/types but different nullable metadata.
The private failed-attempt tree is preserved and contains no files. No score,
metric, bootstrap, selection result, or model/checkpoint mutation occurred.

`DEC-0034` authorizes only
`pa.concat_tables(tables, promote_options="permissive")` plus a preservation
fixture. The change may not cast or alter any row, value, type, order, state,
weight, or count.

## Next gate

Freeze the correction, repeat production validation, then implement and run a
new clean-room validator. A numbered acceptance is required before scoring can
resume from the existing released package.

Protected candidates, protected truth, and protected keys remain fully sealed.
All training, tuning, scorer/protocol change, benchmark modification, negative
construction, external-panel, and structure/residue/interface prohibitions
continue unchanged.
