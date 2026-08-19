# RESUME-004: Post-Stage 1 public-training-freeze phase checkpoint

**Checkpoint date:** 2026-08-19

**Scientific phase boundary:** `DEC-0031` accepts and freezes the complete,
independently validated Stage 1 public-training execution and determines that
the frozen prerequisites for a later development release are satisfied;
development remains encrypted and unreleased, protected packages remain
evaluator-only, and no next executable work package is active

**Use:** this is the self-contained restart record for a fresh Codex thread.
Read it before proposing or performing any next phase. Chat history is not an
authority source.

## 1. Exact repository anchor and handoff invariant

The accepted scientific state immediately before this documentation checkpoint
was authored is:

| Field | Frozen value |
|---|---|
| Branch | `main` |
| Accepted-state commit | `fc3b8b3d89a14449a5c42da00ac54add1d1710a8` |
| Commit subject | `Accept and freeze Stage 1 public training` |
| Commit date | 2026-08-19 |
| Worktree before checkpoint authoring | clean; `git status --short` emitted no paths |
| Prior resume checkpoint commit | `f573ea411233f42d8f3d9a30e640baa2eef10363` |
| Final accepted-anchor local/remote relation | freshly fetched `main` and `origin/main` were `0 0` divergent; `HEAD`, `main`, and `origin/main` were identical |

This file is necessarily committed after the accepted-state anchor. Resolve
the commit containing this checkpoint with:

```bash
git log -1 --format='%H %s' -- governance/checkpoints/RESUME-004-post-stage-1-public-training-freeze.md
```

At a completed handoff, that commit must be reachable from `HEAD`, the branch
must be `main`, the worktree must be clean, and local `main` must equal freshly
fetched `origin/main`. If any condition fails, stop before development-related
work and reconcile non-destructively.

## 2. Current authority

The authoritative records are:

- acceptance decision:
  `governance/decisions/DEC-0031-accept-stage-1-public-training-and-development-release-readiness.md`;
- ledger: `governance/gates/gate_status_v30.yaml`;
- scientific status: `governance/PROJECT_STATUS_v30.md`;
- Stage 1 final report:
  `docs/reports/m1/M1_Stage_1_Public_Training_Execution_Final_v1.md`;
- binding configuration:
  `configs/model_governance_and_baseline_training_protocol_v1.yaml`; and
- binding protocol:
  `docs/protocols/MODEL_GOVERNANCE_AND_BASELINE_TRAINING_PROTOCOL_v1.md`.

Their frozen hashes are:

| Artifact | SHA-256 |
|---|---|
| `DEC-0028` protocol acceptance | `cab395f3be486a19fca4f5444627fe7bdce2b35e2da89e2b87f646639912d894` |
| `DEC-0029` Stage 1 authorization | `0779fda66831e6ad80d2839555652a179a943bc18a0228d1dc39ea4c6c1aef76` |
| `DEC-0030` runtime acceptance | `1508aa2d9a925f1e7ee49c7082830a47f9c49b9451285b596b6d306f6fd92a51` |
| `DEC-0031` Stage 1 acceptance | `8bd585d5944072e37f21cc17386e84209ce8e27c24b3c690536405fe1c3cde0f` |
| gate v30 | `651f48f928a92c1c40abbd1f7dc49c3d9e569138196752ec8556af3cc1a97029` |
| project status v30 | `5d8acc40b7405c17a330cace65aeb467f555058ddca53c6afc5ab2973f4ab1f4` |
| Stage 1 final report | `6bc9804e1b8d99fd113dafa9bc0314b08524b2ee4c5308eb2db909eef0804803` |
| model protocol config v1 | `3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5` |
| binding model protocol v1 | `5daf5809b864de75f236ca3552369f943300bdbc86557a3a99277665faeda851` |

`DEC-0031` closes the `DEC-0029` execution package. It accepts the training
freeze and a prerequisite-satisfaction determination only. It does not release
or authorize decryption of development.

## 3. Immutable parent benchmark and sealed boundary

`DEC-0022`, `DEC-0024`, `DEC-0026`, and `DEC-0028` remain binding. Do not
reopen or alter:

- the 17,000 exact UniProt `2026_02` reference-sequence hashes;
- the frozen sequence-similarity and leakage graphs;
- the 7,782-component `local_domain_union_30` hard rule;
- the 11,900/2,550/2,550 training/development/protected endpoint split;
- pair identities, C1/C2/C3 assignments, source cells, sampling strata,
  design weights, metrics, degree/hub definitions, or claim semantics;
- the 16,799 public training-P rows and 2,000,000 public training-U rows; or
- any encrypted development, protected-candidate, or protected-truth package.

Direct boundary hashes remain:

| Artifact | SHA-256 |
|---|---|
| training P Parquet | `4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499` |
| training U Parquet | `d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7` |
| training strata Parquet | `b8e4247ce934d837477513b322af008413ac8d61fa95ccedd16fe2712c1d6427` |
| encrypted development | `bbbd07472da621a34f45e95ab4b51c799fa0fc967d94de2aa3578e0cda0c1d41` |
| encrypted protected candidates | `5ac1c30dbda85f6274f60febb2f4b01feda34c43bf87f4bbb690abe6c639ff63` |
| encrypted protected truth | `69824547667861694aff88a0f6e43526d4f3aa27f930d4a4ff44c924d29aa1e9` |

U is an unlabeled evidence state, never a biological or assay-negative class.
The frozen training-U sample is not the full candidate universe or a prevalence
denominator.

## 4. Accepted runtime, PLMs, and embeddings

The exact accepted model image is
`containers/images/ipin-model-arm64_0.1.0.sif`, 10,656,620,544 bytes, SHA-256
`c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`.
It ran offline on one NVIDIA GH200 120 GB GPU on Arrhenius node `n180`.

Exactly two frozen encoders exist:

| Role | Immutable revision | Safetensors SHA-256 | Output shape |
|---|---|---|---|
| lightweight baseline | `facebook/esm2_t30_150M_UR50D@a695f6045e2e32885fa60af20c13cb35398ce30c` | `c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566` | `17000 x 640` FP32 |
| primary frozen encoder | `facebook/esm2_t33_650M_UR50D@08e4846e537177426273712802403f7ba8261b6c` | `a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0` | `17000 x 1280` FP32 |

Both complete embedding caches use the frozen final-residue-layer,
special-token-excluded, overlap-averaged pooling rule without truncation.
Normalization statistics use only the 11,900 training endpoints. The frozen
bottom-hash repeat set contains 170 endpoints per encoder and has maximum
absolute difference `0.0`; no residue representation was retained.

Runtime and embedding evidence:

| Artifact | SHA-256 |
|---|---|
| model custody manifest | `a32399a1bdff8b56ff15509ec922e58f78a0e0bf6b860093db2f4952f48bbffe` |
| runtime production qualification | `a96ceb38d5beca8e3c3d640f99341111ed477e9a39e61494e42555c3d17020ec` |
| independent runtime validation | `17321ee58881ba7f2a170b64ebf8411989aa1bfde18c889527bb7ee0ad2bb2ac` |
| implementation audit | `082d166573b3e521b8a579c1f4b5fd8b4ca798678f75b334fcf13cde68df5145` |
| embedding registry | `429e9b3c40827ea5a7513b3599a95d201cdc5eea1e0f99f8c384050cbfcbaed1` |
| embedding production audit | `992faf2029a2e2c0288dfc3b4216a7de75e0b04eea4e54f80560c0313055a79a` |
| independent pretraining validation | `0cd6b9985eb33ddec1948cb22a14bda08c16990d6d2c4d46924952a18e1fd8de` |

Provider metadata supports only the frozen exposure claim ceiling. Exact or
homologous pretraining exposure is unknown and possible. C3 is not PLM-unseen,
family-unseen, temporally clean, or an exposure experiment.

## 5. Frozen methods and training objective

The mandatory deterministic scorers are salted full-SHA-256, training-positive
degree sum, preferential attachment, frozen-component degree-mass product,
training-positive common neighbors, both sequence-length controls, exact
contiguous 3-mer cosine, and exact orientation-invariant training-interolog
3-mer score. Graph features use only public training positives.

The four trainable families and exact matrix census are:

| Family | Parameters | Recipes | Seeds | Runs |
|---|---:|---:|---:|---:|
| lightweight ESM-2 150M affine | 1,922 | 2 | 3 | 6 |
| ESM-2 650M affine ablation | 3,842 | 2 | 3 | 6 |
| ESM-2 650M nonlinear no-gate ablation | 426,625 | 3 | 3 | 9 |
| ESM-2 650M partner-gated primary | 492,417 | 3 | 3 | 9 |

The sole accepted objective was design-weighted P-versus-U pairwise logistic
ranking. Each of five passes used every frozen U row exactly once and the
complete P census through the frozen cyclic rule. Per pass, 919 P observations
occurred 120 times and 15,880 occurred 119 times. Exact rational U weights had
FP64 sum `10902230.000000007` and mean `5.451115000000004`; they were not
clipped or re-estimated.

Seeds are exactly `20260803`, `20260817`, and `20260831`. There was no
performance early stopping. The selected checkpoint is the complete pass with
minimum weighted training monitor and the earliest pass on an exact tie.

## 6. Frozen execution result and registry

The exact result census is:

| Quantity | Frozen value |
|---|---:|
| complete / failed runs | 30 / 0 |
| infrastructure resumes | 0 |
| complete-pass checkpoints | 150 |
| selected checkpoints | 30 |
| selected pass | pass 5 for every run |
| three-seed ensemble definitions | 10 |
| optimizer steps | 73,350 |
| P-versus-U comparisons | 300,000,000 |
| registry artifacts | 647 |
| registered unique bytes | 15,124,997,716 |
| final governed storage bytes | 14,959,953,220 |
| conservative total GPU-hours | 0.45626144182586964 |

All configs, orders, logs, states, pass metrics, checkpoints, selected
checkpoints, sidecars, code/input/runtime dependencies, and ensemble
definitions were frozen before any development access.

Training preparation and final evidence hashes are:

| Artifact | SHA-256 |
|---|---|
| preparation registry | `8d15f244f390d7069a4ecd7453622a425a465dcf1ec9d32087e4d557fbb84f4e` |
| preparation audit | `849f09fdf3f32f6572ffdc097de21fa8a56da29a2494b949386df7871f37631f` |
| independent preparation validation | `a08a62513ef60feff5f3737dbab308c553f24a3f98b562edc8514ba5bd9d70f8` |
| complete training-artifact registry | `11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318` |
| training production audit | `fb15f7462f61597928be68e3f2963505a10318c2696f6575d0354b73a0cb7040` |
| independent final validation | `b7178f659bd03b0b779d0de015cdb8b33af41e4ee7729fb2cb8d461a0e727a88` |

The preparation registry was frozen at commit
`8d026f6b18c4770bd820654ca95f5dfaf7465f33`. The complete training registry
was frozen at `a46639245fc34d9b53063ec46370a6139a2bd021`. Final independent-validation
evidence was frozen at `1003d3e4a0270047d904f06e9acb025bce78cd94`.

## 7. Training-monitor diagnostics

The following are selected-checkpoint training-objective means and ranges over
the three frozen seeds. They are not held-out results and may not select a
candidate or support a generalization or biological claim.

| Candidate | Mean | Range |
|---|---:|---:|
| 650M affine, lr `1e-3` | 0.263228133598 | 0.000494538236 |
| 650M affine, lr `3e-4` | 0.281662857639 | 0.001013004947 |
| 650M no-gate, conservative | 0.016341940400 | 0.000517906952 |
| 650M no-gate, default | 0.005007561962 | 0.000166975093 |
| 650M no-gate, no dropout | 0.003498074303 | 0.000133869945 |
| 650M partner-gated, conservative | 0.012928620223 | 0.000878122141 |
| 650M partner-gated, default | 0.003806196051 | 0.000109098062 |
| 650M partner-gated, no dropout | 0.003065420798 | 0.000152459634 |
| 150M affine, lr `1e-3` | 0.327930147225 | 0.000424617224 |
| 150M affine, lr `3e-4` | 0.344916648255 | 0.000236227125 |

## 8. Independent validation

The production completed-training audit passed 12 checks with zero warnings
and zero failures. The independently implemented final validator, committed
only after the complete registry freeze, passed 14 checks with zero warnings
and zero failures. It does not import production Stage 1 modules.

It independently rehashed all 647 artifacts; reconstructed all 30 P/U orders,
exact rational weights, and positive coverage; inspected all 150 checkpoints;
verified RNG/order/cursor/weight state and finiteness; checked 30-run and
300-million-comparison completeness; and clean-room scored all 30 selected
checkpoints in both partner orientations. Swap maximum absolute difference was
`0.0`. It confirmed offline one-GPU logs, zero resumes, 10 exact ensembles, and
absence of development, protected, private-key, temporary, or sensitive-path
leakage.

## 9. Scientific interpretation and current hold

The frozen prerequisites for a later development release are satisfied. No
development release or access is authorized. No C1, C2, or C3 concordance,
bootstrap interval, degree/hub stratum, C1 novel-U sensitivity, supported-source
direction, development selection, or protected metric exists at this boundary.

The complexity and kill criteria remain pending. Training loss cannot justify
the partner gate, nonlinear head, or 650M scale. A future authorized development
stage must apply the existing C3-first hierarchy and shortcut rules. Graph,
degree, or length explanation triggers the shortcut stop; interolog or
frozen-PLM-linear explanation rejects complexity; failure of every learned
candidate to clear the qualifying C3 gate stops the programme before protected
test.

No new training, adaptive run, checkpoint change, feature change, architecture
change, or post-release retraining is permitted.

## 10. Verification record

The repository-wide suite passed 260 of 260 tests in the checksum-pinned data
SIF with `PYTHONPATH=src`. The eight Stage 1 modules were repeated in the
accepted model SIF and passed 39 of 39 tests. Repository-wide compile checks,
all ten Stage 1 evidence sidecars, YAML parsing, staged-diff checks, and an
independent gate-to-registry/no-release consistency check passed.

The required graphify refresh completed with 2,793 nodes, 6,796 edges, and 209
communities. Its transient pre-overwrite snapshot matched the corresponding
accepted Git blobs before being moved out of the worktree.

No development or protected package was opened. No private key was accessed.
No negative, pseudo-negative, external panel, residue/interface output,
additional training run, SLURM job, multi-GPU task, or post-freeze model artifact
was created.

## 11. Next-phase gate

There is no active executable work package. Before any development-related
implementation, release, decryption, or scoring, a new numbered governance
decision must define and authorize the bounded package. At minimum it must:

1. preserve the exact frozen scorer candidates, checkpoints, ensemble
   definitions, benchmark, metrics, hierarchy, and selection cascade;
2. authorize only the development package, never protected candidates or truth;
3. specify and independently validate release custody, scorer/evaluator code,
   data visibility, prediction hashes, and output schema before scores are used;
4. prohibit training, checkpoint choice, candidate change, adaptive search,
   negatives, pseudo-negatives, and external or structural evidence;
5. report C3, then C2, then C1, plus frozen uncertainty, degree/hub, source,
   seed-stability, and C1 novel-U diagnostics;
6. apply the frozen decimal-`0.001` `ROUND_HALF_UP` selection and all complexity
   and model-level kill criteria exactly; and
7. freeze the final scorer or stop decision and return to governance before any
   protected-test action.

Prerequisite satisfaction is not implied authorization. Do not decrypt
development merely because `DEC-0031` records readiness.

## 12. Exact fresh-thread preflight

From the repository root, first run read-only Git checks:

```bash
git fetch origin main
git status --short
git branch --show-current
git rev-parse HEAD main origin/main
git rev-list --left-right --count main...origin/main
git merge-base --is-ancestor fc3b8b3d89a14449a5c42da00ac54add1d1710a8 HEAD
git log -1 --format='%H %s' -- governance/checkpoints/RESUME-004-post-stage-1-public-training-freeze.md
git log --oneline -8
```

Require a clean worktree, branch `main`, zero divergence, equality of `HEAD`,
local `main`, and `origin/main`, and successful ancestry of the accepted-state
anchor.

Verify accepted governance and runtime hashes:

```bash
sha256sum governance/decisions/DEC-0031-accept-stage-1-public-training-and-development-release-readiness.md
sha256sum governance/gates/gate_status_v30.yaml
sha256sum governance/PROJECT_STATUS_v30.md
sha256sum docs/reports/m1/M1_Stage_1_Public_Training_Execution_Final_v1.md
sha256sum configs/model_governance_and_baseline_training_protocol_v1.yaml
sha256sum docs/protocols/MODEL_GOVERNANCE_AND_BASELINE_TRAINING_PROTOCOL_v1.md
sha256sum containers/images/ipin-model-arm64_0.1.0.sif
```

Verify every Stage 1 evidence sidecar without regenerating evidence:

```bash
(cd artifacts/validation/model_execution/stage1_model_execution_v1 && \
  sha256sum -c STAGE1_IMPLEMENTATION_AUDIT_REPORT.json.sha256 \
    EMBEDDING_ARTIFACT_REGISTRY.json.sha256 \
    EMBEDDING_PRODUCTION_AUDIT_REPORT.json.sha256 \
    INDEPENDENT_PRETRAINING_VALIDATION_REPORT.json.sha256 \
    TRAINING_PREPARATION_REGISTRY.json.sha256 \
    TRAINING_PREPARATION_AUDIT_REPORT.json.sha256 \
    INDEPENDENT_TRAINING_PREPARATION_VALIDATION_REPORT.json.sha256 \
    TRAINING_ARTIFACT_REGISTRY.json.sha256 \
    TRAINING_PRODUCTION_AUDIT_REPORT.json.sha256 \
    INDEPENDENT_TRAINING_ARTIFACT_VALIDATION_REPORT.json.sha256)
```

Verify public and sealed ciphertext hashes without opening sealed content:

```bash
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/positive_pairs/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/unlabeled_pairs/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/sampling_strata/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/development_release.cms
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_candidates.cms
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms
```

The model SIF, development ciphertext, protected-candidate ciphertext, and
protected-truth ciphertext must match the hashes in sections 3 and 4. Do not
read a private key or decrypt a package during preflight.

The complete read-only unit check is:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python -m pytest -q tests/unit
```

Do not rerun any production audit, registry producer, embedding job, training
orchestrator, evaluator, release command, download, or SLURM command as
preflight.

## 13. Fail-closed escalation

Stop and require explicit governance escalation if any recorded commit, hash,
count, model revision, container, checkpoint, registry entry, ciphertext,
protected boundary, authority state, or test result differs; if a development
or protected identity appears; if a private key is needed; or if proposed work
would modify the frozen protocol or scorer set.

Do not repair a mismatch by regenerating accepted artifacts, changing hashes,
opening packages, replacing checkpoints, running an extra seed or recipe,
creating a negative/pseudo-negative, changing U semantics, or silently
broadening authority.
