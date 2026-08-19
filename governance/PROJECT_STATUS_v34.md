# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Execution environment:** NAISS Arrhenius node `n180`; accepted ARM64 model
container; at most one NVIDIA GH200 120 GB

**Scientific programme state:** the sole nullability-metadata loader correction
has passed repeated production and independent qualification; `DEC-0035`
resumes frozen scoring from the existing one-time development release

The authoritative gate is `governance/gates/gate_status_v34.yaml`.

## Accepted requalification

The correction is frozen at
`90ed5007d1deed7f50bab0f2901bf5780a1ab034`. The repeated no-key production
audit passed 13/13 checks at SHA-256
`963b3a9d0e567bc0dd4d1850bd9d8a9382579f46ce9f4643297923f5ccb4962e`.
The new clean-room validator imports no production development module,
re-executed the full frozen prerelease reconstruction, independently tested the
Arrow/AST correction, and passed 13/13 checks at SHA-256
`aaeab6728463f188eb8d81c355a333071f695b5d7278e38c1440aed6a810e5d8`.

Neither qualification accessed development plaintext or a development private
key. No protected private key, candidate, truth, or score was accessed. The
correction preserves exact rows, values, logical types, order, states, rational
weights, and all scientific rules.

## Active development scoring

Development was decrypted exactly once. Its archive SHA-256 is
`c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122`
and its manifest SHA-256 is
`3f58403138b878d912789f529dc1f8ec7d1db7356d6ccc4c3b88cfcb2f6554fa`.
No second decryption is authorized.

The active work is to score all nine development cells with the exact nine
controls, 30 frozen checkpoints, and ten three-seed ensembles, then calculate
the frozen C3-first metrics, intervals, strata, source cells, seed stability,
C1 novel-U sensitivity, selection, complexity, and kill-rule disposition.

## Required return

Freeze score/log/metric/registry evidence and independently validate the
completed evaluation. Governance must then choose: advance a completely frozen
eligible scorer toward separately authorized protected evaluation, retain only
a simpler eligible baseline, or stop the complex-model claim. Protected access
does not follow automatically.

Protected candidates, protected truth, and their keys remain fully sealed.
Training, tuning, checkpoint/scorer/protocol change, negative construction,
external panels, and structure/residue/interface work remain prohibited.
