# One-time protected final test v1

Authority: DEC-0051, 2026-09-11. Status: prospective local execution freeze;
candidate and truth packages remain sealed until all pre-access checks pass.

## Fixed scientific question

Does the existing development-selected scorer rank held-out released-positive
pairs above unlabeled alternatives in the frozen reference-sequence benchmark?
This is not a new model-development or negative-label study.

The sole primary model is `lightweight_esm2_150m_linear__linear_lr3e-4`, the
selection recorded by the identity-corrected development analysis. Average the
raw scores of seeds 20260803, 20260817, 20260831, each original pass-05 checkpoint
(step 2445). Report the three members descriptively; never choose a seed on test.
No 650M/architecture sweep or later within-anchor refit is substituted.

Use the original frozen 150M standardized pooled vectors with the corrected
sequence-SHA-to-manifest-row join. Standardization remains training-only. The
previously permitted label-blind 17,000-vector extraction is not access to test
interaction labels. No new embedding inference, normalization fit or optimizer.
Extract only the hash-verified head's exact FP32 weights and biases into a
pickle-free input bundle. Qualify CPU algebra against the frozen scorer on
public training pairs before candidate access. FP32 head outputs are promoted
to FP64, then averaged in FP64. Swap tolerance is 1e-6.

Fixed controls: original nine deterministic controls (hash, degree sum,
preferential attachment, component mass product, common neighbors, length sum,
length ratio, within-pair 3-mer cosine, exact training-interolog 3-mer), plus raw
pooled-150M cosine and 21-letter amino-acid-count cosine. All features use public
sequences and the original public training graph only. 3-mer/interolog and
added cosine arithmetic are FP64. Baselines remain controls, not test-selected
replacement models.

## Estimand and uncertainty

Primary cell: C3_test; C2_test and C1_test secondary. Report all six frozen
HI-II-14/HuRI source-exclusive test cells as separate descriptive diagnostics.
These are not jointly source-purged/homology-purged training experiments.
Never pool cells. Preserve all original rows and rational U weights. C3 has
2,379 released positives; C2 13,446; C1 3,187. Each cell has one million sampled U
rows. Expected total across all nine cells is 9,028,821 candidate rows.

Primary metric is original HT-weighted P-versus-U pairwise concordance with
exact 0.5 tie credit. Compute the frozen 2,000-draw two-endpoint
local_domain_union_30 component pigeonhole bootstrap, base seed 20260803,
cell seed from the first eight big-endian bytes of
SHA256(`20260803:bootstrap:{cell_id}`), PCG64DXSM, sorted participating
components. Draw the same number with replacement; distinct-component pair
multiplier is the product, same-component multiplier is one multiplicity.
Positive weight is one; retain rational U design weights. Use identical draws
for all scorers. Report percentile 95% intervals, finite draw counts and paired
model-minus-control differences. Zero-mass draws are invalid, not imputed.
If fewer than 1,900 draws are finite, suppress inferential conclusions.

Every comparison is reported; no claim based on a best-on-test comparator.
C3 model versus all eleven controls is one intersection-union superiority
claim: require every paired 95% lower bound above zero. Individual intervals
are marginal, not simultaneous; secondary/source claims are descriptive.
No equivalence claim from nonsignificance. Retain the original seed-range
diagnostic (0.02), not a post-test selection rule.

## Execution and custody

Preserve the binding protected procedure v1 except that a single versioned
comparison harness consumes a fixed bundle of separate two-column Parquet
predictions in one attempt. Each file has exactly candidate_token and score;
per-cell partitioning is private routing, not an extra scorer feature.

Before candidate access, hash the protocol, DEC-0051, source, synthetic tests,
public inputs, derived features and immutable model SIF into SCORER_FREEZE.json.
The frozen execution bundle is a checksum-bound read-only snapshot, not the
dirty editable checkout. Existing uncommitted research records are preserved.
Snapshotting does not imply a clean root worktree or external preregistration.

On this host user.max_net_namespaces=0 and Apptainer PID virtualization is
disabled. Qualify a restriction-only CPU launcher before access: no elevated
privileges, no host configuration changes, no proc/sys/home/cwd/hostfs or
administrator bind-path mounts; no GPU/RDMA devices; allowlisted read-only
bundle and role-specific mounts only. Close inherited descriptors above stderr;
stdin is /dev/null, stdout/stderr are private local files. Set no_new_privs and
native-ABI seccomp denial of sockets, network I/O, io_uring, cross-process access,
mount/namespace changes and SysV shared memory. Verify actual socket failure,
alternative-channel failure and child inheritance before protected reads.
This is syscall and mount isolation, not a claimed network/PID namespace.
Only then set the isolation attestation flag. CPU compatibility and metric
tests must run under exactly these restrictions. Fail closed on guard failure.

The opener gets only the candidate key; unprojected plaintext is temporary and
deleted before session persistence. The scorer gets no keys/truth and only the
four-column projection and frozen public-derived features. After scoring exits,
the validator verifies every token, finite score, exact coverage, symmetry
audit, bundle hashes and session sidecar, then freezes every prediction hash.
Exclusively reserve the original package-scoped
`.private/pair_level_pu_r_benchmark_artifacts_v1/protected_evaluation_ledger.json`
before mounting the truth key into the metric process. No new namespace,
deletion, reset or per-baseline repeated truth call. Reservation irrevocably
consumes the attempt on success or failure. Truth plaintext is temporary.
Write a separate completion record only on success.

Release only allowlisted aggregate metrics, integrity hashes and receipts.
Protected identities, scores, membership, row errors and logs remain private.
Failure after reservation is reported without repairing/retrying on this split.
Numerical/reference checks are same-author checks, not independent replication.

## Interpretation and stopping

Unlabeled is not experimentally nonbinding. Concordance is not classification
accuracy, biological precision, prevalence or a calibrated interaction
probability. Sampled U is not the full universe: no exact Recall@K or full-rank
claims. No family-unseen, PLM-unseen or exhaustive-homology claim; the fixed
30% local-domain split is not the stronger later 20% purge. Final test results
do not retrospectively make the spent external/within-anchor diagnostics fresh.
Report positive, null and adverse findings; stop without tuning or retesting.
