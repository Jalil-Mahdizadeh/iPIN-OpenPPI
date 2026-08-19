# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Execution environment:** NAISS Arrhenius node `n180`; accepted
`ipin-model-arm64_0.1.0.sif`; one NVIDIA GH200 120 GB

**Scientific programme state:** `DEC-0030` accepts the exact model runtime and
custody snapshot; the frozen Stage 1 embedding, implementation-validation, and
public-training work may proceed under `DEC-0029`

The authoritative gate is `governance/gates/gate_status_v29.yaml`.

## Accepted runtime and custody

Both frozen ESM-2 revisions are present inside link-free, project-local custody
with exactly the six required files. Both Safetensors weights match the frozen
size and SHA-256. No pickle weight or remote code is admitted.

The accepted ARM64 model SIF is 10,656,620,544 bytes with SHA-256
`c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`.
It layers only the three missing hash-pinned model packages on the previously
accepted parent. Production synthetic qualification passed. A separately
implemented validator then passed 10 of 10 checks with zero warnings and zero
failures, including exact rehashes, both checkpoint loads, deterministic
zero-difference repeats, bfloat16 execution, offline socket-blocked use, exact
restart, and sensitive-path exclusion.

No scientific endpoint, pair, development candidate, protected candidate or
truth was processed before `DEC-0030`.

## Active execution boundary

The next work is exact implementation and validation of the frozen methods,
two complete 17,000-endpoint embedding caches with one-percent repeats, and the
complete 30-run public-training-only matrix. All use is one-GPU, offline,
Safetensors-only, fixed-seed, fixed-recipe, fixed-pass, and bounded by 100 GPU-
hours, 100 GiB, and 300 million comparisons.

The benchmark, component split, C1/C2/C3 definitions, P/U rows and weights,
PU-R objective, metrics, and claim semantics remain unchanged. U remains
unlabeled. No negative or pseudo-negative is created.

## Continuing hold and return

Development and protected packages remain encrypted and inaccessible. The
stage must freeze all run configurations, checkpoints, orders, logs, metrics,
hashes, failures, selected training checkpoints, and three-seed ensembles in
one complete registry. Independent validation of the full training stage and a
new numbered readiness decision must precede any later development release.
