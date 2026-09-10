# iPIN-OpenPPI status: development identity correction complete

Date: 2026-09-10

Supersedes `governance/PROJECT_STATUS_v44.md` under the bounded user authority
recorded in DEC-0045. This records execution results, not an external expert
review or authorization for another phase.

ISSUE-0014 is resolved. The scorer now joins frozen embedding rows to protein
identities explicitly. Existing checkpoints were reevaluated on all original
development rows, weights, scorer definitions, metrics and scientific rules.
All 329 unit tests, nine production audit checks and 17 standalone independent
validation checks pass. The standalone implementation keeps embedding rows
in storage order and translates pair coordinates; all 270,783,240 learned
scores agree exactly with production.

The original near-chance learned-model scores were invalidated by the identity
mismatch. Corrected C3 positive-versus-U concordance is 0.784142 for the
selected 150M affine ensemble (95% component-bootstrap interval
[0.742820, 0.852716]) and 0.759554 for the best C3 partner-gated ensemble.
There is useful development ranking signal, but all gated configurations fail
the original seed-stability and incremental-benefit criteria. The unchanged
disposition remains `stop_complex_model_claim_and_stop_before_protected_evaluation`.
This does not support a general claim that frozen sequence representations
contain no useful signal; nor does it establish biological accuracy,
probability calibration, novel architecture benefit or protected performance.

The separate coarse-local diagnostic remains a negative result for that
heuristic. Original inputs, models and v1 evidence are preserved. Protected
candidates and truth remain sealed; no decryption, training or architecture
change was performed. No additional work package or protected evaluation is
authorized by this checkpoint.

Report:
`docs/reports/m1/M1_Research_Reassessment_and_Embedding_Identity_Findings_2026-09-10.md`.
Current ledger: `governance/gates/gate_status_v45.yaml`.
Independent evidence:
`artifacts/validation/development_evaluation/development_embedding_identity_correction_v2/INDEPENDENT_VALIDATION_ARTIFACT_REGISTRY.json`.

Recommended next research question, not an authorized execution: does the
simple model capture partner-specific compatibility beyond endpoint/assay
propensity in a prospectively defined within-anchor retrieval comparison?
