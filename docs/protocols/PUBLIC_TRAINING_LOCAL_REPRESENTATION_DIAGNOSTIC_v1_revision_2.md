# Public-training local-representation diagnostic protocol v1, revision 2

This pre-execution clarification inherits every rule in
`PUBLIC_TRAINING_LOCAL_REPRESENTATION_DIAGNOSTIC_v1` except one optional,
underspecified diagnostic. No local embedding or model score existed when this
revision was frozen.

`local_bidirectional_best_match_cosine` is removed. It has no replacement.
Phase A retains the exact hash, length-ratio, 3-mer, nested interolog, matched
global cosine, local maximum cosine, and primary local top-four cosine scores.
Conditional Phase B, if mechanically triggered, uses matched global cosine
alone versus matched global plus local maximum and local top-four cosine.

For exactness, a segment vector is the raw FP32 arithmetic mean of its frozen
contextual residue vectors. Segment cosine independently L2-normalizes each
segment and rejects zero norms. The matched global vector is the residue-count-
weighted mean of raw segment vectors. Local maximum is the maximum of every
valid segment-pair cosine. Local top-four is the arithmetic mean of the largest
`min(4, number of valid segment pairs)` values.

The executable delta is
`configs/public_training_local_representation_diagnostic_v1_revision_2.yaml`.
All primary thresholds, cells, metrics, split rules, data boundaries, and
prohibitions remain unchanged.

