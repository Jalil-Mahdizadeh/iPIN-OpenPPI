# Fixed-ensemble follow-up on the existing test v1

2026-09-11. Authority: [DEC-0053](../../governance/decisions/DEC-0053-authorize-fixed-ensemble-followup.md),
following DEC-0052. Execution namespace: `model_optimization_followup_v1`.
Freeze this document, decision, code, tests and inputs before follow-up test-pair
access. This amendment occurs **after development selection and before the
follow-up test**. It does not retroactively change the search's frozen gate.

## Fixed predictor and acceptance

Only `esm2_150m__residual_wide`, epoch 4 of its completed eight-epoch schedule.
Frozen ESM-2 150M, 640-dimensional training-standardized endpoint vectors;
commutative sum, absolute difference, product and exact cosine; LayerNorm,
width-256 GELU MLP, training dropout 0.3 (disabled for inference), plus affine
branch. There are 498,053 parameters per head. No encoder inference or fitting.

Use exactly these existing state-only NPZ checkpoint hashes in this order:

| Seed | SHA-256 |
|---|---|
| 20260803 | `f46452e84cb30df1c785a6af982f83d37ba892855b5af0a848aac4610890cabc` |
| 20260817 | `08a67b0309a2d3d2928c9f188f73180a4e917f457a087ea1206c85bbae828463` |
| 20260831 | `2f5fbe82194f88b8afb6ce90c8db1b1b2ed87cd1d03484ffec0375e2774c17f1` |

Evaluate each head in FP32 without AMP/TF32; convert the three raw scores to
FP64 and take their equal arithmetic mean. No sigmoid averaging, rank averaging,
calibration, reweighting, member removal or refitting. Epoch, preprocessing and
model source remain identical to the completed search.

Search-freeze SHA-256:
`c321841b6d79f4ca4256f14f9f7463a5bf3b5dc0085cfa554a1dc3ba4c906f67`.
Selection SHA-256:
`3a4fe7e5a960a6798638ca84cf2433b2fa195c3dfeccd680986ee15ef0ea2ce6`.
Require the valid complete-search record, positive ensemble gain, and positive
paired 95% lower bound already recorded. Create `ENSEMBLE_ACCEPTANCE.json`;
leave `model_optimization_v1/DEVELOPMENT_GATE.json` unchanged and failed.
Individual seeds remain reported diagnostics, not test-promotion conditions.

## Qualification before access

Verify all 179 registered historical files and the original custody records.
Use only the exact manifest-aligned 150M matrix and endpoint ordering from the
search; verify identity against the original protected scorer's public feature
bundle. Verify every selected checkpoint and cached development prediction.

In the pinned ARM64 model SIF, replay all three checkpoints on the full C3
development panel on the actual GPU and the CPU inference path. Require maximum
raw-score difference from the frozen GPU cache <=1e-5 and concordance difference
<=1e-7 for each member and the ensemble. This is a numerical qualification,
not another optimization run. Qualify exact inference swap symmetry (<=1e-6),
raw-score ensemble arithmetic, state loading and deterministic repeat scoring.
Freeze a fixed 128-row public-training fixture and its GPU reference scores for
another check inside the protected CPU guard. Run synthetic metric, prediction,
custody, publication and end-to-end tests before accessing real candidates.

## Staged execution and baseline

Keep the original protected CPU seccomp launcher unchanged. Disable host
proc/sys/home/cwd/hostfs/admin binds; use allowlisted read-only input mounts,
no network, no inherited extra file descriptors, and private output directories.
GPU is used for pre-access numerical qualification; protected scoring/metrics
remain CPU-only to preserve the already-qualified isolation boundary.

1. Freeze the exact model, implementation, amendment, qualification and input
   manifests into an immutable scorer bundle. No test pair rows or truth inside.
2. Decrypt/project the same sealed candidate package to token, endpoint A/B
   sequence hashes and cell only. Validate all nine cell counts and unique tokens.
3. Score the candidate ensemble and its three members with no truth, key or
   baseline-prediction mounts. Freeze the candidate prediction manifest.
4. Import only the original baseline ensemble and its three member predictions,
   byte-for-byte, through read-only mounts. Verify their original prediction
   freeze, per-file hashes, token identities and exact ensemble arithmetic. No
   baseline refits or control selection. These four imported scorers plus four
   candidate scorers are the complete eight-scorer census.
5. Validate and hash every prediction for every cell. Record a new prediction
   freeze. Atomically reserve a separate ledger under
   `.private/pair_level_pu_r_benchmark_artifacts_v1/followup_evaluations/model_optimization_followup_v1/`.
   Bind the original ledger read-only and link its SHA-256, DEC-0053, acceptance,
   search, selection and scorer/prediction freezes. Never alter original custody.
6. Make one bundled truth evaluation. Mark evaluation entry exclusively before
   decryption, prohibit reentry even after failure, and report all nine cells.
   A post-reservation failure consumes this authorization; do not retry.
7. Publish only strictly allowlisted aggregates and a separate follow-up receipt
   and completion record; verify the entire historical closure again.

## Metrics and interpretation

The sole primary comparison is candidate **ensemble minus original baseline
ensemble C3_test** design-weighted P-versus-U concordance. C2/C1, HI-II-14 and
HuRI source-exclusive cells, and individual seeds are descriptive; they cannot
change the predictor, acceptance, primary conclusion or stopping.

Use the original frozen `protected_final_core_v1.bootstrap_metrics` unchanged:
exact tie handling, original U rational sampling weights and 2,000 paired
sequence-component resamples. Draw seed is SHA-256-derived from
`20260803:bootstrap:{cell}` with PCG64DXSM. A within-component pair uses its
multiplicity once; other pairs use the product of endpoint multiplicities.
Resample both P and U contributions. Report each concordance and percentile
95% interval, paired ensemble difference and its 95% interval, finite draws,
component count/draw hash, and member concordances. Store draws privately for
arithmetic verification without another truth access. Reproduce original
baseline point/interval and draw-multiplicity hash within 1e-12 numerically.

A positive gain with paired lower bound >0 and at least 1,900 finite paired
draws supports an improvement for this fixed predictor on this reused benchmark.
If uncertainty overlaps zero, report an inconclusive improvement; if the point
falls or interval is negative, report that honestly. Do not replace a failed or
inconclusive comparison with another recipe, member, source cell or metric.
All intervals are conditional on fitted predictors, not training-seed resampling.
The development interval was post-selection; the amendment is not independent
preregistration. Disclose prior baseline test access. No new unseen-test,
independent-replication, pure-architecture-causality, calibration, biological
precision, partner-specific/direct-binding or universal-nonbinding claims.

No further model changes or test evaluations follow automatically. Keep all
historical studies, including BioPlex, intact; BioPlex is secondary cross-assay
evidence and is not a binary-binding gate. Commit only code, docs and approved
aggregates/provenance, never checkpoints, candidate tokens, pairs, truth or keys.
