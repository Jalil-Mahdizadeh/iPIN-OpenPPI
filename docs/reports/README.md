# Project reports

Human-readable M0 platform, evidence, benchmark, modelling, gate, and release reports are stored here. Machine-readable run records remain under `artifacts/runs/`.

The current model disposition is [Frozen pair models v1](../models/FROZEN_PAIR_MODELS_v1.md),
authorized by [DEC-0054](../../governance/decisions/DEC-0054-freeze-and-designate-both-models.md).
Both exact ensembles are preserved: the optimized residual-MLP ensemble is the
**best-performing model by observed benchmark score**; the affine ensemble is
the **original confirmatory baseline**. No new experiment or evaluation was
performed for this designation. See [status v54](../../governance/PROJECT_STATUS_v54.md)
and the [public model registry](../../artifacts/models/frozen_pair_models_v1/MODEL_REGISTRY.json).

The latest completed study is
[Fixed-ensemble test follow-up](m1/M1_Model_Optimization_Followup_v1.md), authorized
by [DEC-0053](../../governance/decisions/DEC-0053-authorize-fixed-ensemble-followup.md).
The frozen optimized ensemble increased primary C3 test concordance from
**0.789249 to 0.807948**, paired gain **0.018699 [−0.001358, 0.050000]**:
positive point improvement, but not conclusive at the 95% interval criterion.
Secondary C2/C1 gains are larger with positive paired intervals. All nine cells
and all member results are reported. See [status v53](../../governance/PROJECT_STATUS_v53.md)
and the [follow-up protocol](../protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md).
This is one disclosed comparison on the existing, previously examined test;
no new test set, refitting, seed selection or test tuning. Original records remain
immutable and no further evaluation is queued.

The preceding completed study is
[Development-only model optimization](m1/M1_Model_Optimization_v1.md), authorized by
[DEC-0052](../../governance/decisions/DEC-0052-development-only-optimization-and-conditional-followup.md).
Its [prospective protocol](../protocols/MODEL_OPTIMIZATION_v1.md) fixes 24 recipes,
two GPU-hours, a three-seed stability/paired-interval improvement gate, and one
conditional follow-up on the existing (already examined) test. The selected
residual-MLP ensemble improved C3 development from 0.784142 to 0.799419, paired
gain interval [0.002942, 0.034460], but failed individual-seed stability. No
follow-up occurred under that original gate. Its unchanged
[status v52](../../governance/PROJECT_STATUS_v52.md) records that historical stop;
DEC-0053 later accepted the ensemble as the prediction unit in an explicit
post-development, pre-follow-up-test amendment rather than rewriting the gate.

The original completed evaluation report is
[One-time protected final test](m1/M1_Protected_Final_Test_v1.md)
(DEC-0051, 2026-09-11). The final test is complete: primary C3 concordance is
0.789 [0.708, 0.846], above all eleven prespecified controls with positive
paired intervals. C2/C1 do not establish improvement over strong degree
controls. These are PU ranking results, not direct-binding accuracy. See
[status v51](../../governance/PROJECT_STATUS_v51.md) and
[gate ledger v51](../../governance/gates/gate_status_v51.yaml).

The historical research-disposition report is
[Direct-binary feasibility and project disposition](m1/M1_Direct_Binary_Feasibility_and_Project_Disposition_v1.md)
(DEC-0050, 2026-09-11): its model-development stop is narrowly superseded by DEC-0052.
SAVEXIS is a conditional candidate for a separate extracellular study, not an
evaluation-ready rescue. No model experiment was run. See
[status v50](../../governance/PROJECT_STATUS_v50.md) and
[gate ledger v50](../../governance/gates/gate_status_v50.yaml).

The preceding frozen research reports are:

- [Composition/order challenge](m1/M1_Composition_Order_Challenge_v1.md).
- [External BioPlex challenge](m1/M1_External_BioPlex_Challenge_v1.md).
- [Homology/interolog and source challenge](m1/M1_Homology_and_Source_Challenge_v1.md).
- [Within-anchor partner specificity](m1/M1_Within_Anchor_Partner_Specificity_Diagnostic_v1.md).
- [Research reassessment and embedding-identity correction](m1/M1_Research_Reassessment_and_Embedding_Identity_Findings_2026-09-10.md).

BioPlex AP-MS is retained as secondary cross-assay association evidence, not a
valid decisive direct-binary panel, an optimization target, or a selection gate
for the primary PU benchmark. The historical reports and null results are not
rewritten or removed. Partner-specific and direct-binding claims remain open.

The historical model-governance report is
`docs/reports/m1/M1_Model_Governance_and_Baseline_Training_Protocol_Final_v1.md`.
It freezes the deliberately simple first-stage model design but contains no
model experiment or result. The accepted pair-package report remains
`docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Artifacts_Final_v1.md`.
The accepted frozen protocol report remains
`docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Protocol_Final_v1.md`, and the
sealed custody procedure is
`docs/reports/m0/PROTECTED_TEST_EVALUATION_PROCEDURE_v1.md`.
The accepted frozen component-split report remains
`docs/reports/m0/M0_Final_Benchmark_Component_Split_Final_v1.md`.
The external-panel audit reports remain quarantined from the primary design.
The previously accepted negative-evidence report remains
`docs/reports/m0/M0_Negative_Evidence_Discovery_Audit_Final_v1.md`.
