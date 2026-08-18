# RESUME-003: Post-model-governance-protocol-freeze phase checkpoint

**Checkpoint date:** 2026-08-18

**Scientific phase boundary:** `DEC-0028` accepts and freezes the independently
validated model-governance and baseline/training protocol; no model acquisition,
implementation, embedding, training, development release, or protected
evaluation is authorized or has begun

**Use:** this is the self-contained restart record for a fresh Codex thread.
Read it before proposing or performing any next phase. Chat history is not an
authority source.

## 1. Exact repository anchor and handoff invariant

The accepted scientific state immediately before this documentation checkpoint
was authored is:

| Field | Frozen value |
|---|---|
| Branch | `main` |
| Accepted-state commit | `142b571bbb60b1f6f484a2dd00854cea8d43c5ed` |
| Commit subject | `Accept and freeze model governance protocol` |
| Commit date | 2026-08-18 |
| Worktree before checkpoint authoring | clean; `git status --short` emitted no paths |
| Resume source verified at phase start | `55be4cd4f43659acf32423580b94732aa7e38041` |
| Phase-start local/remote relation | freshly fetched `main` and `origin/main` were `0 0` divergent at the resume source |

This file is necessarily committed after the accepted-state anchor. Resolve
the commit containing this checkpoint with:

```bash
git log -1 --format='%H %s' -- governance/checkpoints/RESUME-003-post-model-governance-protocol-freeze.md
```

At a completed handoff, that commit must be reachable from `HEAD`, the branch
must be `main`, the worktree must be clean, and local `main` must equal freshly
fetched `origin/main`. If any condition fails, stop before model-related work
and reconcile non-destructively.

## 2. Current authority

The authoritative records are:

- acceptance decision:
  `governance/decisions/DEC-0028-accept-model-governance-and-baseline-training-protocol.md`;
- ledger: `governance/gates/gate_status_v27.yaml`;
- scientific status: `governance/PROJECT_STATUS_v27.md`;
- binding machine configuration:
  `configs/model_governance_and_baseline_training_protocol_v1.yaml`;
- binding scientific protocol:
  `docs/protocols/MODEL_GOVERNANCE_AND_BASELINE_TRAINING_PROTOCOL_v1.md`;
  and
- expert-facing report:
  `docs/reports/m1/M1_Model_Governance_and_Baseline_Training_Protocol_Final_v1.md`.

Their frozen hashes are:

| Artifact | SHA-256 |
|---|---|
| `DEC-0028` | `cab395f3be486a19fca4f5444627fe7bdce2b35e2da89e2b87f646639912d894` |
| gate v27 | `3c03fdb0442631fa4e55409221995e2c8ca0d1588f2e9f0814babe9a67966063` |
| project status v27 | `da0e29be5a6160dda3c213d982326bd0c8f7fab28268c65fd9168403bd20d7e0` |
| model protocol config v1 | `3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5` |
| binding model protocol v1 | `5daf5809b864de75f236ca3552369f943300bdbc86557a3a99277665faeda851` |
| M1 model protocol report v1 | `3e79d50f9a2d9543cd12dc06131f9a2c870b2d8f2044ebe45c899fa25071e2a3` |
| production audit | `62ca0deea443951925351edaf2b2f397b0490308193e9b2fdfd0759d9cda89b4` |
| independent validation | `e5af1b7a30af7ed971a099f71c01518ba54ad9419fa63e5a0bc4ba4fa77a61ea` |

`DEC-0028` accepts a protocol only. It authorizes no executable next work
package. A new numbered governance decision is mandatory before any checkpoint
or tokenizer download, cache population, model-image build, baseline/model
implementation, embedding extraction, training, or checkpointing.

## 3. Immutable parent benchmark

`DEC-0022`, `DEC-0024`, and `DEC-0026` remain binding. Do not reopen or alter:

- the 17,000 exact UniProt `2026_02` reference-sequence hashes;
- any frozen 40%/30%/20% full-length, sensitivity, local, or domain graph;
- the 7,782-component `local_domain_union_30` hard rule;
- the 11,900/2,550/2,550 training/development/protected endpoint split;
- exact pair identity, C1/C2/C3 assignment, source-cell, quarantine,
  information-visibility, sampling, probability, weight, metric, uncertainty,
  degree/hub, or claim semantics;
- the 16,799 public training-P rows, 2,000,000 public training-U rows, and
  36 public training sampling strata; or
- the encrypted development, protected-candidate, and protected-truth packages
  or their custody/evaluator procedure.

Key direct artifact hashes remain:

| Artifact | SHA-256 |
|---|---|
| training P Parquet | `4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499` |
| training U Parquet | `d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7` |
| training strata Parquet | `b8e4247ce934d837477513b322af008413ac8d61fa95ccedd16fe2712c1d6427` |
| encrypted development | `bbbd07472da621a34f45e95ab4b51c799fa0fc967d94de2aa3578e0cda0c1d41` |
| encrypted protected candidates | `5ac1c30dbda85f6274f60febb2f4b01feda34c43bf87f4bbb690abe6c639ff63` |
| encrypted protected truth | `69824547667861694aff88a0f6e43526d4f3aa27f930d4a4ff44c924d29aa1e9` |

Unlabeled is an evidence state, not a biological or assay-negative class. The
frozen public training-U sample is not the full candidate universe and is not a
prevalence denominator.

## 4. Accepted PLM candidates and claim ceiling

Exactly two ESM-2 checkpoints are permitted in the first possible stage:

| Role | Repository revision | `model.safetensors` SHA-256 | Shape |
|---|---|---|---|
| lightweight mandatory baseline | `facebook/esm2_t30_150M_UR50D@a695f6045e2e32885fa60af20c13cb35398ce30c` | `c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566` | 30 layers; 640 hidden |
| primary frozen encoder | `facebook/esm2_t33_650M_UR50D@08e4846e537177426273712802403f7ba8261b6c` | `a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0` | 33 layers; 1,280 hidden |

Only safetensors is permitted; pickle weights and remote code are prohibited.
Tokenizer, config, vocabulary, special-token map, model card, and weights must
come from the same immutable revision. A later authorized acquisition must stay
inside the configured project-local cache, reject symlink escape, record bytes
and SHA-256 per file, and run embedding/training offline.

Provider records describe sequence-only masked-language-model pretraining on
UR50/D associated with UniRef `2021_04`, but no exact dynamic draw log is
available and benchmark endpoints/homologs have not been exposure-audited.
Exact or homologous exposure is unknown and possible. Never call C3 PLM-unseen,
family-unseen, temporally clean, or an exposure experiment. A 150M/650M
difference is a capacity/representation diagnostic only.

The future image recipe is pinned as `ipin-model-arm64_0.1.0.sif`, but the image
does not exist and is not authorized. It must derive from the accepted ARM64
NGC/PyTorch parent and exact runtime versions in the config. Its build,
dependency lock, SIF hash, imports, deterministic embedding repeat, and exact
checkpoint/restart fixture require independent qualification before use.

## 5. Accepted embedding strategy

Both encoders stay frozen, in evaluation mode, with autograd disabled. Use the
final residue layer, exclude special tokens, and keep forward, accumulation,
and stored outputs FP32.

Exact frozen sequences are never truncated or replaced. Lengths above 1,022
use windows of 1,022 residues with 128 overlap and 894 stride; append
`length - 1022` when not already a start. Average each residue across every
covering window before globally averaging residues.

All 17,000 endpoint vectors may be extracted label-blindly only after later
authorization. Trainable-head normalization uses only the 11,900 training
endpoints. Complete/unique/finite vector and manifest checks plus a deterministic
1% repeat extraction at maximum absolute difference `1e-6` are hard gates.
No residue embedding or interface output is retained in stage one.

## 6. Mandatory baseline ladder

Every method must use the same governed rows, design weights, and tie rule.
The mandatory ladder is:

1. normalized deterministic full-SHA-256 score using the accepted public salt
   and seed;
2. training-positive endpoint-degree sum;
3. training-positive preferential attachment;
4. frozen-component training-degree-mass product;
5. training-positive common-neighbor count;
6. sequence log-length sum and negative absolute log-length difference;
7. exact within-pair contiguous 3-mer cosine over
   `ACDEFGHIKLMNPQRSTVWYX`;
8. exact best orientation-invariant training-interolog 3-mer score;
9. frozen ESM-2 150M commutative-feature one-affine-scalar head; and
10. the corresponding frozen ESM-2 650M affine-head ablation.

All graph features use only the 16,799 training positives; held-out endpoint
training degree is zero. Approximate interolog search, held-out/full-graph
degree, source/assay/publication features, protected metadata, and external
panels are prohibited.

## 7. Primary training objective

The only accepted objective is design-weighted positive-versus-unlabeled
pairwise logistic ranking. For each of five complete passes:

- use all 2,000,000 frozen public U rows exactly once without replacement;
- independently order P and U by the configured full-SHA-256 keys;
- contrast U position `i` with
  `positive_order[(i + pass_index - 1) mod 16799]`;
- use the complete 16,799-P census, where 919 positives repeat 120 times and
  the other 15,880 repeat 119 times; and
- retain each U row's exact rational `N_h/m_h` design weight without clipping
  or re-estimation.

The per-comparison loss is `softplus(-(score_positive-score_unlabeled))`.
The batch objective normalizes U weights by their all-U mean; the complete-pass
monitor is an FP64 weighted mean. This operational comparison does not label U
as zero or nonbinding. BCE, pseudo-negatives, class-prior risks such as nnPU,
calibration, source heads, and held-out supervision are excluded.

## 8. Architecture, optimization, and stopping

The primary head uses the frozen 650M pooled vector, shared `1280 -> 256` exact
GELU projection, one shared affine-sigmoid partner gate applied symmetrically,
commutative sum/absolute-difference/product/cosine features, and a
`769 -> 128 -> 1` scalar head. Trainable parameters must be below 2,000,000.

The only scientific ablations are the 650M affine head and a 650M nonlinear
no-gate head. Along with the 150M affine baseline, there are four trainable
families, three fixed seeds (`20260803`, `20260817`, `20260831`), two linear
recipes, three nonlinear recipes, exactly 30 runs, five passes, and a ceiling
of 300,000,000 comparisons.

Use one NVIDIA GH200 120GB, at most 100 GPU-hours and 100 GiB. Four-GPU or
multi-node training is prohibited in stage one. Deterministic algorithms,
disabled TF32, fixed cuBLAS workspace, PCG64DXSM, complete-pass checkpoints,
and exact RNG/order/data-cursor hashes are binding.

There is no performance early stopping. Select the complete pass with minimum
design-weighted training monitor loss and the earliest pass on an exact tie.
One exact infrastructure resume is allowed; a repeat infrastructure failure or
any numerical/integrity/symmetry failure closes the run without recipe/seed
replacement.

## 9. Development release and model selection

Development is encrypted and unreleased. Before any release, all prespecified
runs must complete or fail closed; selected run checkpoints and three-seed
ensemble definitions must be frozen; code, config, container, input,
embedding, checkpoint, and ordering hashes must enter a complete training-
artifact registry; that registry must pass independent validation; and a new
numbered decision must authorize release.

Development receives only already-frozen scorer candidates. New training,
checkpoint choice, architecture, recipe, seed, feature, or embedding changes
are prohibited after release. Select the arithmetic three-seed ensemble by
decimal-`0.001` `ROUND_HALF_UP` C3 concordance, then C2, then C1, then lower
complexity, then lexicographic candidate ID. No cell pooling, individual-seed
selection, post-selection retraining, or novel-U/source diagnostic selection
is permitted.

Protected candidates and truth remain invisible to development. After final
scorer freeze, protected evaluation remains the existing no-network,
prediction-hash-before-truth, exclusive one-first evaluator procedure. Only
aggregate receipts may leave it.

## 10. Metrics, stratification, complexity, and kill rules

The primary metric remains Horvitz-Thompson positive-versus-U pairwise
concordance with half credit for exact ties. Report separately in order C3,
C2, C1 for development and, only later, protected test. Use the existing
two-endpoint-component pigeonhole bootstrap with 2,000 replicates and the
frozen seed. Never publish a pooled headline metric.

Degree bins and nested top-1%, top-5%, and top-10% hubs use only the training-
positive graph. Quantitative strata require at least 100 positives and 10
participating components. The C1 novel-U sensitivity retains only already-
frozen C1 U pair IDs absent from public training U, keeps original rational
weights, creates/resamples nothing, and is report-only.

The partner gate requires a C3 gain of at least 0.02 over the strongest simple
sequence baseline with paired interval excluding zero, at least 0.01 over the
650M linear ablation, at least 0.005 over the no-gate head, supported-source
direction, non-hub-only gain, and stable eligible seeds. Failure removes the
gate, nonlinear head, or 650M scale in the frozen fallback order.

Stop before protected test if no learned candidate clears the qualifying C3
gate. Treat graph/degree/length explanation as a shortcut stop and interolog or
frozen-PLM-linear explanation as rejection of complexity. Integrity leakage,
U-as-negative use, premature development release, and post-release retraining
invalidate the stage. A residue/joint/routing model needs accepted simple-stage
results, an unresolved non-shortcut error, separate oracle/interface evidence,
a compute case, and a new numbered decision.

## 11. Validation and execution record

Production audit:

- clean implementation commit:
  `547592d64aced7a1ab91ee4a320c643bf8c36bad`;
- report SHA-256:
  `62ca0deea443951925351edaf2b2f397b0490308193e9b2fdfd0759d9cda89b4`;
- result: 24 pass, 0 warning, 0 fail.

Independent validation:

- clean evidence commit:
  `9d7159b80e35416cbe0aa219066eab09817c3a49`;
- report SHA-256:
  `e5af1b7a30af7ed971a099f71c01518ba54ad9419fa63e5a0bc4ba4fa77a61ea`;
- result: 20 pass, 0 warning, 0 fail;
- validation-evidence commit:
  `d2e68c71786ac63864965924aea08fd9ad12cd79`.

The checkpoint-prescribed eight-module preflight passed 26 tests. The final
ten-module suite added 27 model-governance tests and passed 53 tests total in
the checksum-pinned data SIF. Compile checks and gate/report hash consistency
checks passed.

The required incremental graphify refresh completed with 2,424 nodes, 5,960
edges, and 179 communities. Each file in the tool's transient pre-overwrite
snapshot matched the corresponding accepted-state Git blob exactly, so the
prior curated graph remains recoverable from commit `142b571` without a
duplicate dated directory.

No GPU or SLURM job was launched. No model/tokenizer file was acquired; no
cache or model image exists from this phase; no model framework was imported by
the independent validator; no embedding, feature, checkpoint, prediction, or
metric was created; no development/protected identity was accessed; no sealed
package was opened; and no private key was read.

## 12. Next-phase gate

There is no active next work package. If the project owner asks to proceed,
first create a new numbered decision defining a bounded implementation and
public-training package under the accepted protocol. At minimum it must:

1. authorize only the exact two model revisions and local offline acquisition;
2. build and independently qualify the exact model SIF before scientific use;
3. implement and test embeddings, every mandatory baseline, the three 650M
   heads, the pairwise objective, determinism, symmetry, checkpoint/restart,
   and artifact registries before launching the finite training matrix;
4. preserve development encryption and all protected boundaries;
5. emit no negative/pseudo-negative, residue/interface, external-panel, or
   full-universe artifact; and
6. return with clean production and independent validation evidence before any
   development-release request.

Do not interpret `DEC-0028` as authorization to start a job. The current gate's
`next_authorized_work_package` is null.

## 13. Exact fresh-thread preflight

From the repository root, first run read-only Git checks:

```bash
git fetch origin main
git status --short
git branch --show-current
git rev-parse HEAD main origin/main
git rev-list --left-right --count main...origin/main
git log -1 --format='%H %s' -- governance/checkpoints/RESUME-003-post-model-governance-protocol-freeze.md
git log --oneline -6
```

Require a clean worktree, branch `main`, zero divergence, and equality of
`HEAD`, local `main`, and `origin/main`. Confirm the accepted-state anchor above
is an ancestor of `HEAD`.

Verify immutable reports and direct hashes without opening sealed content:

```bash
(cd artifacts/validation/model_governance/model_governance_and_baseline_training_protocol_v1 && sha256sum -c AUDIT_REPORT.json.sha256 && sha256sum -c VALIDATION_REPORT.json.sha256)
sha256sum configs/model_governance_and_baseline_training_protocol_v1.yaml
sha256sum docs/protocols/MODEL_GOVERNANCE_AND_BASELINE_TRAINING_PROTOCOL_v1.md
sha256sum docs/reports/m1/M1_Model_Governance_and_Baseline_Training_Protocol_Final_v1.md
sha256sum governance/decisions/DEC-0028-accept-model-governance-and-baseline-training-protocol.md
sha256sum governance/gates/gate_status_v27.yaml
sha256sum governance/PROJECT_STATUS_v27.md
sha256sum containers/images/ipin-data-arm64_0.1.2.sif
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/positive_pairs/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/unlabeled_pairs/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/sampling_strata/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/development_release.cms
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_candidates.cms
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms
```

The data SIF must hash to
`72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`.
Compare every other result to the tables above or `RESUME-002`. Do not use a
private key or decrypt any package.

Run the lightweight fail-closed tests in the pinned container:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python -m pytest -q \
  tests/unit/test_sequence_component_safety.py \
  tests/unit/test_pre_split_safety.py \
  tests/unit/test_component_split_safety.py \
  tests/unit/test_pair_protocol_safety.py \
  tests/unit/test_pair_protocol_semantics.py \
  tests/unit/test_pair_protocol_validation.py \
  tests/unit/test_pair_artifacts_safety.py \
  tests/unit/test_pair_artifacts_semantics.py \
  tests/unit/test_model_governance_protocol_safety.py \
  tests/unit/test_model_governance_validation.py
```

For a codebase question, follow `AGENTS.md` and begin with a scoped
`graphify query`. Do not run the production audit again because its output is
immutable, and do not invoke any construction, evaluator, release, download,
model, embedding, training, or SLURM command as preflight.

## 14. Fail-closed escalation

Stop and require explicit governance escalation if any recorded commit, hash,
count, path, role, model revision, protocol rule, report sidecar, protected
boundary, or authority state differs; if a sealed or private identity appears;
if a model/cache artifact exists without an authorization record; or if the
requested next work would weaken the accepted simple-stage or claim ceiling.

Do not repair a mismatch by regenerating frozen artifacts, changing hashes,
opening packages, substituting a newer model revision, creating negative or
pseudo-negative data, or silently broadening authority.
