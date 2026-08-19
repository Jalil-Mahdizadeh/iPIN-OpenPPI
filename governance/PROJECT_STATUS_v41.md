# iPIN-OpenPPI project status: FP32 audit correction authorized

The first local-embedding forward pass failed before writing artifacts because
an implementation-only reconstruction check used an overly tight `2e-6`
tolerance. The exact observed FP32 reduction-order difference was
`1.52587890625e-05`.

DEC-0042 authorizes a `1e-4` audit tolerance and an exact rerun. No scientific
formula, score, metric, trigger, or boundary changes. Development and protected
packages remain outside scope.

The authoritative ledger is `governance/gates/gate_status_v41.yaml`.
