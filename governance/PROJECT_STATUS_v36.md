# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Scientific programme state:** `ISSUE-0010` is exactly corrected and
independently requalified; `DEC-0037` authorizes resume from four complete
manifested development cells and the existing one-time release

The authoritative gate is `governance/gates/gate_status_v36.yaml`.

## Accepted requalification

The production and clean-room validators each passed 14/14 checks. Their
SHA-256 digests are
`778b8d68ff102aad005286bc5ab85691e949742c69f116c9027492523d823fd7`
and
`77ed919c4812453fab85de94a7ce0c52838bb3b7e921db6ca99a045e305ae686`.
The four completed cell manifests and every registered constituent hash/byte
count were rechecked; the custody report has SHA-256
`7f36b15e90a01cfba7896ab11ba389aa706a9a7ceda5c4a416501a4c747b49d5`.

## Active exact resume

The empty failed source-cell directory may be preserved under its unique
private incident name. The frozen scorer may then run once with `--resume`,
skipping the four complete cells and scoring the remaining five. It must
produce exactly one complete nine-cell run manifest before evaluation.

Development was decrypted exactly once and cannot be decrypted again.
Protected candidates, truth, and keys remain sealed. All pair artifacts,
weights, models, checkpoints, metrics, complexity thresholds, and kill rules
remain frozen.
