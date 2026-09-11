# Project status v53 — ensemble tested; primary incremental gain inconclusive

Date: 2026-09-11. Decision: [DEC-0053](decisions/DEC-0053-authorize-fixed-ensemble-followup.md).
Previous immutable status: [v52](PROJECT_STATUS_v52.md).

The user-authorized fixed-ensemble follow-up is complete. C3 test concordance
increased from **0.789249 to 0.807948**, gain **0.018699**, paired 95% interval
**[−0.001358, 0.050000]**. The development and test gains agree in direction and
point magnitude, but the primary interval includes zero: no conclusive primary
C3 improvement claim. This does not establish equivalence or absence of benefit.

Secondary C2 increased **0.805299 → 0.851301**, gain 0.046002
[0.031561, 0.061559]; C1 increased **0.843493 → 0.916037**, gain 0.072544
[0.063093, 0.081869]. All nine cell point gains are positive. Both source-specific
C3 intervals overlap zero; all source-specific C2/C1 intervals are positive.
Secondary findings do not replace the primary comparison.

The evaluated predictor is the exact existing three-seed residual-MLP ensemble
at epoch 4, with equal raw-score averaging. No new fitting or tuning. Individual
C3 candidate seeds all increased on test, but the model-level comparison remains
ensemble-versus-ensemble. DEC-0053 is explicitly post-development and pre-follow-up
test; DEC-0052's failed individual-seed gate remains unchanged, not relabeled.

The original baseline remains an immutable reference. The optimized ensemble
is now a higher-scoring tested predictor, not merely a development candidate,
but is not a conclusively superior C3 replacement. Unqualified statements that
network shortcuts dominate this optimized model are unsupported: its C2/C1
point scores exceed the historical highlighted network controls, although
paired optimized-versus-network comparisons were not part of this follow-up.
Shortcut exploitation, genuine partner specificity and direct binding remain
unresolved. BioPlex remains secondary cross-assay evidence, outside this study.

Exactly one bundled follow-up evaluated eight scorers on nine cells and
9,028,821 candidate rows, with 2,000 finite paired component draws throughout.
Baseline predictions were byte-identical and all original baseline metrics and
bootstrap metadata reproduced exactly. The separate follow-up authorization is
consumed; original spent custody and all 179 earlier registered files remain
unchanged. This is reuse of a previously examined panel, not an unseen test or
independent replication. Unlabeled pairs are not negatives or binding labels.

The actual GH200 GPU exactly replayed development predictions before access;
protected CPU inference passed its numerical and isolation qualifications.
The full runtime-partitioned regression passed 492 CPU tests and 12 GPU tests;
initial environment-only failures and the lossless guard-log normalization are
preserved. No scientific code or checkpoint was adjusted after scorer freeze.

See the [concise report](../docs/reports/m1/M1_Model_Optimization_Followup_v1.md),
[protocol](../docs/protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md), and
[gate record](gates/gate_status_v53.yaml). Preserve both models and publish the
complete comparison. No additional experiment, new test, refit or evaluation is
authorized automatically. The user authorized repository updates, commit and push.
