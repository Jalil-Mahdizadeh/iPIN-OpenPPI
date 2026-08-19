# DEC-0029: Authorize Stage 1 executable model work

**Date:** 2026-08-19

**Status:** Accepted and effective for the bounded Stage 1 work package, with
scientific embedding and training conditional on separate acceptance of the
new model runtime before its scientific use

**Decision basis:** Explicit project-owner instruction supplied in the active
session after successful execution of the `RESUME-003` preflight

**Controlling records:** `RESUME-003`, `DEC-0028`, and
`model_governance_and_baseline_training_protocol_v1`

## Decision

Authorize the bounded, public-training-only execution of the complete frozen
`DEC-0028` Stage 1 model protocol. This authorization changes execution state;
it does not amend a scientific definition, candidate, recipe, seed, budget,
metric, data artifact, or claim boundary.

The binding configuration is
`configs/model_governance_and_baseline_training_protocol_v1.yaml`, SHA-256
`3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5`.
If any executable requirement cannot be implemented exactly, execution must
fail closed and return to governance. The frozen configuration may not be
changed to accommodate software, hardware, time, or an observed result.

## Successful authorization preflight

Execution was authorized only after the exact `RESUME-003` preflight completed
on branch `main` at
`f573ea411233f42d8f3d9a30e640baa2eef10363`, with local and freshly fetched
`origin/main` identical and zero divergence. The accepted-state anchor
`142b571bbb60b1f6f484a2dd00854cea8d43c5ed` is an ancestor of that commit.

Both immutable model-protocol sidecars validated. The protocol configuration,
binding protocol, scientific report, `DEC-0028`, gate v27, status v27, and data
SIF matched their recorded hashes. The public training P, U, and sampling-
strata Parquets matched the frozen digests, as did the three sealed ciphertexts
when hashed without opening them. The exact ten-module pinned-container suite
passed 53 of 53 tests. No private key was inspected and no sealed package was
opened.

The assigned interactive node was `n180` with one visible NVIDIA GH200 120 GB
GPU. Direct execution there is permitted. A SLURM allocation is also permitted
only if exactly one GH200 GPU is used by a Stage 1 process. Multi-GPU and
multi-node model execution remain prohibited.

## Authorized work

The work package shall:

1. acquire only the two accepted ESM-2 repositories at their exact frozen
   revisions, retain only the required co-revision files and safetensors
   weights in the project-local cache, verify the two frozen weight digests and
   sizes, reject links outside the project, hash every retained file, and make
   all later model use offline;
2. construct `ipin-model-arm64_0.1.0.sif` from the accepted qualified parent
   with exactly the dependency versions in the binding configuration, freeze
   its definition, resolved hash lock, SIF digest, inspection metadata, build
   provenance, and qualification evidence;
3. independently validate CPU imports and ARM64 identity, one-GPU FP32 and
   bfloat16 fixtures, deterministic embedding repeat, exact checkpoint/restart,
   and offline operation, then return through a new numbered decision that
   accepts or rejects the runtime before any scientific embedding or training;
4. implement the deterministic hash, training-positive graph/degree,
   component-mass, common-neighbor, length, exact 3-mer, exact training-
   interolog, 150M linear, 650M linear, 650M nonlinear-no-gate, and 650M
   partner-gated methods exactly as frozen, with unit and mutation tests;
5. after runtime acceptance, extract the prescribed label-blind pooled FP32
   embeddings for all 17,000 exact frozen endpoint sequences for both accepted
   candidates, compute normalization only from the 11,900 training endpoints,
   complete the deterministic bottom-hash one-percent repeats, and freeze every
   vector and manifest hash;
6. independently validate model/revision/tokenizer/runtime binding, endpoint
   completeness and uniqueness, long-sequence window coverage, vector shape,
   dtype and finiteness, training-only normalization, repeat tolerance, public-
   only visibility, and absence of sensitive inputs before training;
7. execute the complete nonadaptive 30-run matrix, using exactly the three
   seeds, five complete U passes, optimizer recipes, deterministic order,
   weighted P-versus-U logistic ranking objective, checkpointing, one-resume
   infrastructure rule, numerical-failure closure, 300,000,000-comparison
   ceiling, 100-GPU-hour ceiling, and 100-GiB project-storage ceiling;
8. freeze the selected training checkpoint for each successful run, all
   complete-pass checkpoints, configurations, orders, logs, metrics, failure
   dispositions, three-seed ensemble definitions, code/container/input/
   embedding hashes, and one complete training-artifact registry plus its
   SHA-256 before any development release or access; and
9. independently validate data visibility, exact objective weights and order,
   method symmetry and formulas, run-budget completeness, checkpoint selection,
   artifact custody and hashes, reproducibility controls, comparison/GPU/storage
   accounting, and the absence of leakage, then return to governance with a
   numbered results decision, gate, status, report, and restart checkpoint.

The separately accepted runtime is a hard prerequisite to item 5 and all later
scientific execution. Runtime qualification fixtures may use only synthetic
sequences and synthetic state; they may not use benchmark labels, pair rows,
development material, or protected material.

## Frozen scientific and data boundary

Only the already-public training P census, frozen public training-U sample,
sampling-strata table, and immutable public/reference endpoint metadata needed
by the frozen methods may enter fitting. Every U observation remains unlabeled;
its use on the comparison side of the ranking loss creates neither a negative
label nor a pseudo-negative artifact.

The 17,000 exact sequences, all sequence-similarity graphs, 7,782 components,
11,900/2,550/2,550 split, C1/C2/C3 definitions, pair identities, weights,
sampler, metrics, bootstrap, pair packages, and sealed package ciphertexts are
read-only. Endpoint sequences from all three partitions may be embedded only
through the frozen label-blind strategy; held-out labels, degrees, graph edges,
source fields, candidate identities, and distribution statistics may not enter
a trainable head.

## Evidence and commit discipline

Large model files, the SIF, embeddings, checkpoints, and logs remain generated
project-local artifacts. They shall not be treated as self-authenticating:
tracked manifests and registries must name each governed artifact by exact
path, bytes, SHA-256, producer commit, frozen inputs, container, code version,
and disposition. Atomic outputs must be verified before registration.

Consequential production validation and independently implemented validation
must be separated by clean commits. The independent validators may share only
frozen schemas and evidence, not production implementation logic. Any mismatch,
missing artifact, ambiguous run disposition, budget overrun, visibility breach,
or hash drift is a failure, not a warning that can be waived in place.

## Continuing prohibitions

This decision does not authorize:

- modifying `DEC-0028` or any frozen benchmark/protocol/artifact semantics;
- creating, relabeling, resampling, or interpreting negatives or pseudo-
  negatives, or using BCE/class-prior/calibration objectives;
- decrypting, mounting, inspecting, reconstructing, probing, scoring, or
  otherwise accessing the development or protected packages or any private
  key;
- development scoring, model selection, protected scoring, or any prediction
  keyed to unreleased candidate identity;
- adding a checkpoint, PLM, recipe, seed, architecture, training pass, adaptive
  search, replacement run, or comparison beyond the accepted 30-run matrix;
- multi-GPU or multi-node training, full-universe pair materialization, new
  candidate/sample rows, or external diagnostic-panel integration;
- encoder tuning, LoRA, adapters, custom pretraining, routing, retrieval,
  structure, residue/interface features or targets, or other complex model
  work; or
- probability, calibration, prevalence, biological precision, nonbinding,
  unseen-family, PLM-unseen, temporal-cleanliness, or causal pretraining-
  exposure claims.

## Return and next decision boundary

No development release follows automatically from a completed run. The stage
must first return with every prespecified run complete or failed closed, all
selected checkpoints and ensemble definitions frozen, a complete registry hash,
and passing independent validation. A numbered governance decision shall then
state explicitly whether every frozen prerequisite for a later development
release has been satisfied. Development remains encrypted unless a separately
effective release decision later changes that state.
