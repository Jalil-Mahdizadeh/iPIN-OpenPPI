# ISSUE-0014: Development scoring uses the wrong protein embedding identities

Opened: 2026-09-10

Status: confirmed; correction authorized by DEC-0045.

ESM matrices and training indices use `(sequence_length, sequence_sha256)`
order. Development pair indices use SHA-only order, but the scorer indexes the
original matrices without aligning them. The independent v1 validator repeats
this error. Frozen manifests and a read-only container diagnostic confirm
16,999 mismatched indices among 17,000 endpoints for both encoders.

All learned-model development columns and dependent conclusions are affected.
The original artifacts remain immutable incident evidence. Deterministic
controls and the separate local-representation diagnostic do not share this
specific mismatch. Corrected development performance is pending.

The complete finding and scientific assessment are recorded in
`docs/reports/m1/M1_Research_Reassessment_and_Embedding_Identity_Findings_2026-09-10.md`.

Correction requirements: explicit identity joins using frozen embedding
manifests, permutation-invariance and missing/duplicate identity rejection,
public-training score agreement, complete versioned development rescoring,
original metrics/thresholds, and a separate independent implementation that
checks protein identity in addition to arithmetic and file integrity.
