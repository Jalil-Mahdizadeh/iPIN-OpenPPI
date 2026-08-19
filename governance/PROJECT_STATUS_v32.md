# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Execution environment:** NAISS Arrhenius node `n180`; accepted ARM64 model
container; at most one NVIDIA GH200 120 GB

**Scientific programme state:** the `DEC-0032` development-only implementation
has passed production and clean-room independent pre-release qualification;
`DEC-0033` activates exactly one development decryption and frozen evaluation

The authoritative gate is `governance/gates/gate_status_v32.yaml`.

## Accepted pre-release qualification

Production code was frozen at
`21aa040484eec533a8f519f1e70c11a817317ba7`. The no-key production audit
passed 12/12 checks and has SHA-256
`609de99b92e4b4be56a98b61823618056be1cb8bf156cbe51c273f505a0c7ad9`.
The independently implemented validator imports no production development
module, passed 12/12 checks, and has SHA-256
`146d06a689b6ccb473b663db50675b1fc660a9fd11921e6965c9b6007ce50395`.

Neither qualification accessed the development private key or plaintext. No
protected private key, candidate, truth, or score was accessed. The exact
9-control, 30-checkpoint, and 10-ensemble census, score-only model algebra,
metrics, bootstrap, diagnostics, selection, complexity, and kill rules are
qualified without changing the frozen protocol.

## Active development-only execution

One decryption of the development ciphertext at SHA-256
`bbbd07472da621a34f45e95ab4b51c799fa0fc967d94de2aa3578e0cda0c1d41`
is active. The deterministic archive must hash to
`c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122`.
The resolver may inspect only the development key; a pre-existing private
release target prevents a second decryption.

The active work is scoring the nine development primary/source cells with all
49 frozen scorers and calculating C3, then C2, then C1 HT metrics, paired
2,000-draw component-bootstrap intervals, degree/hub views, supported source
cells, seed ranges, C1 novel-U, diagnostics, exact model selection, and every
complexity/kill rule. No training or checkpoint mutation is allowed.

## Required return

Freeze all score/log/metric/registry evidence, then independently validate the
completed evaluation. Governance must record whether to advance a completely
frozen eligible scorer toward a separately authorized protected evaluation,
retain only a simpler baseline, or stop the complex-model claim. Protected
evaluation does not follow automatically.

## Continuing boundary

Protected candidates, protected truth, and their keys remain sealed. Benchmark
changes, negatives or pseudo-negatives, retraining, tuning, adaptive criteria,
new architectures or ablations, external panels, structure/residue/interface
work, multi-GPU execution, and probability/prevalence/calibration or
unsupported transfer/exposure claims remain prohibited.
