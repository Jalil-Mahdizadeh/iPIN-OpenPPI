# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-18

**Execution environment:** NAISS Arrhenius; static governance validation used
the checksum-pinned ARM64 data SIF; no model SIF exists or is authorized

**Scientific programme state:** the pair-level PU-R benchmark remains accepted
and immutable; `DEC-0028` accepts and freezes the independently validated model-
governance and baseline/training protocol; no executable model stage is
authorized

The authoritative gate is `governance/gates/gate_status_v27.yaml`.

## Accepted model protocol

`DEC-0028` accepts `model_governance_and_baseline_training_protocol_v1`.
Production static audit ran from clean commit
`547592d64aced7a1ab91ee4a320c643bf8c36bad` and passed 24 checks. Independent
validation ran from clean evidence commit
`9d7159b80e35416cbe0aa219066eab09817c3a49` and passed 20 checks. Both had zero
warnings and zero failures.

The accepted evidence hashes are:

- configuration: `3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5`;
- binding protocol: `5daf5809b864de75f236ca3552369f943300bdbc86557a3a99277665faeda851`;
- scientific report: `3e79d50f9a2d9543cd12dc06131f9a2c870b2d8f2044ebe45c899fa25071e2a3`;
- production audit: `62ca0deea443951925351edaf2b2f397b0490308193e9b2fdfd0759d9cda89b4`;
  and
- independent validation:
  `e5af1b7a30af7ed971a099f71c01518ba54ad9419fa63e5a0bc4ba4fa77a61ea`.

## Frozen first-stage design

The first possible future modelling stage is deliberately simple and
diagnostic:

- exact frozen ESM-2 150M and 650M candidates with offline hash-pinned custody
  and conservative, unknown-and-possible pretraining-exposure boundaries;
- complete FP32 final-layer pooled embeddings with overlap-safe long-sequence
  coverage and training-only normalization;
- deterministic hash, graph/degree, component, common-neighbor, length, exact
  3-mer, exact training-interolog, and lightweight frozen-PLM controls;
- a design-weighted P-versus-U pairwise logistic ranking objective using all
  16,799 public training positives and every one of the 2,000,000 frozen public
  training-U observations once per pass without assigning a negative class;
- one swap-symmetric pooled 650M partner-gated head and only linear and no-gate
  650M ablations;
- three seeds, 30 finite runs, five complete passes, a 300,000,000-comparison
  ceiling, one-GH200 execution, fixed checkpoint/restart and stopping rules,
  100 GPU-hours, and 100 GiB;
- complete training-artifact freeze and independent validation before any
  development release, then nonadaptive C3/C2/C1 selection with no retraining;
- separate Horvitz-Thompson C3/C2/C1 reporting, the frozen component bootstrap,
  training-only degree/hub diagnostics, and the view-only C1 novel-U analysis;
  and
- explicit complexity thresholds and kill rules when shortcut or simple
  sequence baselines explain apparent gain.

Residue/interface prediction, structural inputs, routing, retrieval, custom
pretraining, encoder tuning/adapters, external panels, calibration, and
probability targets are excluded.

## Immutable benchmark boundary

The 17,000 exact reference sequences, all 40%/30%/20% leakage graphs, the 7,782
`local_domain_union_30` components, 11,900/2,550/2,550 split, exact pair IDs,
C1/C2/C3 roles, sampler, rational weights, metrics, bootstrap, public training
tables, and encrypted development/protected packages are unchanged.

Unlabeled remains an evidence state, not a negative. Development is encrypted.
Protected candidates and truth remain separately encrypted and evaluator-only.
No private key or sealed identity was accessed during this phase.

## Execution record

The `RESUME-002` preflight matched local `main`, freshly fetched `origin/main`,
and the recorded checkpoint commit at
`55be4cd4f43659acf32423580b94732aa7e38041`; all prescribed hashes matched and
26 checkpoint safety tests passed. The final relevant suite, including 27 new
model-governance tests, passed 53 tests inside the pinned data SIF.

No GPU or SLURM job was started. No checkpoint or tokenizer was downloaded, no
cache populated, no model runtime built, no embedding extracted, and no model
or baseline implemented, trained, scored, selected, or evaluated.

## Binding hold

No next work package is authorized. Model files, a model SIF, implementation,
embeddings, and training require a new numbered authorization tied exactly to
the accepted protocol and a new independent validation return.

Development release additionally requires the complete prespecified training
matrix to be closed, selected checkpoints and ensembles frozen, a complete
training-artifact registry hash independently validated, and another numbered
decision. Protected evaluation remains later, one-first, evaluator-only, and
post-selection.

Frozen benchmark modification, new pairs or samples, negative or pseudo-
negative construction, full-universe materialization, development/protected
access, external-panel integration, residue/interface work, and unsupported
probability, prevalence, biological-precision, unseen-family, or PLM-unseen
claims remain prohibited.
