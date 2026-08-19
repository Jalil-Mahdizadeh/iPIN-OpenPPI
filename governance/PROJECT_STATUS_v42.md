# iPIN-OpenPPI project status: FP64 local scoring retry authorized

The local FP32 embedding snapshot passed. The first Phase A scoring attempt
then failed before artifact output because its GPU cosine arithmetic was FP32
while the exact CPU reference promoted retained FP32 vectors to FP64.

DEC-0043 authorizes FP64 cosine reductions on the unchanged vectors. No formula,
scorer, metric, trigger, or data boundary changes. The retry must meet the
original `2e-6` CPU/GPU parity check. Development and protected material remain
outside scope.

The authoritative ledger is `governance/gates/gate_status_v42.yaml`.
