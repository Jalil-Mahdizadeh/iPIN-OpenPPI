# DEC-0030: Accept model runtime and custody for Stage 1

**Date:** 2026-08-19

**Status:** Accepted and effective for scientific Stage 1 use under the
unchanged `DEC-0028` protocol and bounded `DEC-0029` authorization

**Controlling records:** `DEC-0028`, `DEC-0029`, and gate v28

## Decision

Accept the exact-revision ESM-2 model custody and
`ipin-model-arm64_0.1.0.sif` as independently qualified. The separate runtime-
acceptance prerequisite in `DEC-0028` is satisfied. Scientific extraction of
the frozen pooled endpoint embeddings, implementation validation, and exact
public-training-only 30-run matrix may now proceed under `DEC-0029`.

This decision accepts a fixed runtime and custody snapshot. It changes no PLM,
revision, tokenizer, embedding rule, method, objective, recipe, seed, stopping
rule, budget, data row, metric, claim, or protected boundary.

## Accepted construction and evidence

The build producer was committed at
`ee14932567d7ef082eceb0a488c7bd508f391433`. Warning-free production
qualification ran at
`93ef7b7f328293b9b5d656f377f4dde008545f50`; production custody/build/runtime
evidence was frozen at
`b73df403958e0847bb799d4f90a548c99a4b3060`. The independently implemented
validator was committed at
`7fdeb9e2167cd1b5846e428d8414b29d6cd39eec` and passed 10 of 10 checks with
zero warnings and zero failures. Its evidence is committed at
`d76dca1daf9e8777984dfe7f9392fc5fda2efb07`.

Accept:

1. the 150M and 650M snapshots at exactly the two `DEC-0028` revisions, each
   with exactly six co-revision files, no symlink, no external cache link, no
   pickle weight, and the accepted Safetensors size and digest;
2. the 10,656,620,544-byte SIF with SHA-256
   `c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`,
   built offline from the accepted parent and three hash-locked added wheels;
3. exact ARM64/package imports, full checkpoint-key loading, pooler-free residue
   backbones, local-files-only operation, and remote-code prohibition;
4. production FP32/bfloat16 synthetic embedding fixtures, zero-difference
   deterministic repeat, and exact restart fixture; and
5. independent rehashing, config/label parsing, both-candidate one-GPU repeat,
   650M bfloat16, network-socket-blocked model use, exact restart, and sensitive-
   path exclusion.

The accepted evidence hashes are recorded in
`docs/reports/m1/M1_Model_Runtime_and_Custody_Qualification_Final_v1.md` and the
immutable qualification lock.

## Scientific-use boundary

The accepted runtime may process all 17,000 exact endpoint sequences only under
the label-blind, FP32, overlap-averaged pooling strategy frozen by `DEC-0028`.
It may train only the four frozen pair-head families against the exact public P
census and public U sample under the design-weighted ranking objective and
complete 30-run grid.

Every subsequent model load must remain offline, local-files-only,
Safetensors-only, and remote-code-disabled. A hash, package, file-set, key-set,
container, dtype, shape, or deterministic-fixture drift invalidates this
acceptance and stops scientific execution.

## Continuing hold

Development remains encrypted and unreleased. Protected candidates and truth
remain encrypted and evaluator-only. No private key, sealed identity,
development score, selection result, or protected result is authorized.

Frozen benchmark/protocol changes, negatives or pseudo-negatives, new or
resampled pair rows, adaptive or extra training runs, multi-GPU/multi-node
training, external panels, structures, residue/interface outputs, encoder
tuning, adapters, probability targets, and unsupported PLM-exposure claims
remain prohibited.

The next required governance return remains the complete, independently
validated training-artifact registry and an explicit numbered decision on
whether all prerequisites for a later development release have been satisfied.
