# Protected final test v1: execution record

This records the authorized one-time workflow. **Do not rerun it on this split.**
The original package-scoped ledger is now consumed. Nothing here authorizes
key release, retraining, an alternate ledger, a new split, or another attempt.
The aggregate results are the reusable research artifact; protected rows are not.

## Frozen inputs and numerical implementation

`SCORER_FREEZE.json` contains all bundle file hashes, source/dependency
provenance, upstream input hashes, exact three checkpoints, embedding-identity
permutation, the original package/certificate/ciphertext hashes, prior-study
closure checks, and the fixed scorer/cell census.

Model image: `ipin-model-arm64_0.1.0.sif`, SHA-256
`c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`.
Public-only preparation and scientific tests ran in that pinned ARM64 image.
Ten synthetic tests ran again under the same restrictions as protected scoring.
Two separate aggregate-publication fixtures ran in the pinned ARM64 data image.

The frozen execution bundle is stored locally under
`artifacts/runs/protected_final_test_v1/frozen_bundle/`, read-only. It is a
checksum-bound snapshot, not a claim that the root worktree was clean or
committed. Existing uncommitted DEC-0050 research work was preserved.

No new training, ESM inference, normalization fit, checkpoint selection or
protected-label-dependent code change occurred. Only the development-selected
150M model was tested, not a new sweep of 650M or later diagnostic heads.
The CPU implementation replays the frozen head exactly on 128 public training
pairs. This is a CPU replay check, not a claim of bit-identical CPU/GPU arithmetic
on every possible pair.

## Historical sequence

1. Confirmed no prior ledger/completion; checked key paths/modes without reading
   key contents. Verified immutable image and public-input hashes.
2. Tried the usual no-network namespace launch. The host sets
   `user.max_net_namespaces=0` and disables Apptainer PID virtualization.
   No privileged host settings were changed.
3. Qualified CPU execution with hidden proc/sys/checkout/home mounts,
   no inherited descriptors above stderr, no_new_privs and inherited seccomp
   restrictions. Actual INET/INET6/UNIX socket creation, io_uring, pidfd and
   child-process enforcement were checked. GPU initialization fails with the
   restricted mounts, so the final scientific execution is entirely CPU.
4. Ran `prepare_protected_final_test_v1.py` in the pinned model image. It checks
   public inputs, derives immutable public-training features and pickle-free
   head parameters, checks synthetic tests, and freezes the bundle. It never
   opens keys or protected packages.
5. Ran the frozen `run_protected_final_test_v1.sh` stages separately:
   `preflight`, `open`, `score`, `freeze-predictions`, `reserve`, `evaluate`.
   Candidate key, scorer, ledger operator and truth key have separate mounts.
   The ledger operator's escrow-key paths were additionally verified as masked
   devices, not readable keys.
6. `open` persisted only the exact four-column label-free projection and removed
   unprojected plaintext. `score` emitted 135 private two-column Parquet files.
   `freeze-predictions` independently checked every token and score after the
   scorer exited. Fixed 128-row-per-cell swap checks had error zero.
7. The existing package ledger was exclusively created at 09:00:54 UTC,
   after prediction validation at 09:00:08 UTC and before truth-key delivery.
   The truth process rechecks frozen artifacts and computes all cells and paired
   2,000-component-draw intervals in one invocation. No metric-driven resubmission.

All key material, candidate/truth rows, row predictions, and actual evaluator
logs remain under account-private local custody. A UCX startup message precedes
the final JSON in the private guard-probe log; its final attestation and exit
status were checked explicitly. The scored session and prediction manifests
are private; public records expose only integrity hashes and aggregate counts.

The public aggregate publisher is separate from numerical evaluation: it
cannot score, fit or decrypt, strictly checks allowed fields and comparison
coverage, copies completed results byte-for-byte, and creates an aggregate-only
receipt and separate completion record with exclusive writes. Synthetic
publication tests do not use the real test result.

Implementation/reference checks are same-author checks, not external
preregistration or independent scientific replication. A final artifact registry
records the completed public result/report/receipt and code closure.
