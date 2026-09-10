# ISSUE-0014: Development scoring uses the wrong protein embedding identities

Opened: 2026-09-10

Status: resolved on 2026-09-10 under DEC-0045. Corrected evaluation passed
production audit (9/9) and standalone independent validation (17/17).

ESM matrices and training indices use `(sequence_length, sequence_sha256)`
order. Development pair indices use SHA-only order, but the scorer indexes the
original matrices without aligning them. The independent v1 validator repeats
this error. Frozen manifests and a read-only container diagnostic confirm
16,999 mismatched indices among 17,000 endpoints for both encoders.

All learned-model development columns and dependent conclusions are affected.
The original artifacts remain immutable incident evidence. Deterministic
controls and the separate local-representation diagnostic do not share this
specific mismatch. The corrected selected 150M affine ensemble has C3
positive-versus-U concordance 0.784142, versus the invalid original 0.491608.
The partner-gated complexity claim still fails the unchanged scientific rules.

The complete finding and scientific assessment are recorded in
`docs/reports/m1/M1_Research_Reassessment_and_Embedding_Identity_Findings_2026-09-10.md`.

Correction requirements: explicit identity joins using frozen embedding
manifests, permutation-invariance and missing/duplicate identity rejection,
public-training score agreement, complete versioned development rescoring,
original metrics/thresholds, and a separate independent implementation that
checks protein identity in addition to arithmetic and file integrity.

All correction requirements above are complete. The 329-test unit suite
passes, and the independent storage-coordinate implementation exactly
reproduced all 270,783,240 learned scores. Evidence is recorded in
`artifacts/validation/development_evaluation/development_embedding_identity_correction_v2/INDEPENDENT_VALIDATION_ARTIFACT_REGISTRY.json`.
No checkpoint, scientific rule, original evidence or protected seal changed.
