# RESUME-005: Post-development-evaluation stop checkpoint

**Checkpoint date:** 2026-08-19

**Scientific phase boundary:** `DEC-0039` accepts the complete,
independently validated development-only evaluation, stops the complex-model
claim under the frozen `DEC-0028` criteria, and requires the programme to stop
before protected evaluation; both protected packages and keys remain sealed
and no executable model work package is active

**Use:** this is the self-contained restart record for a fresh Codex thread.
Read it before proposing or performing any further scientific work. Chat
history is not an authority source.

## 1. Exact repository anchor and handoff invariant

The accepted scientific state immediately before this documentation checkpoint
was authored is:

| Field | Frozen value |
|---|---|
| Branch | `main` |
| Accepted-state commit | `011181a1be5f0b65830599fdd5be037512d3c308` |
| Commit subject | `Accept development evaluation and stop complex claim` |
| Commit date | 2026-08-19T14:16:35+02:00 |
| Worktree before checkpoint authoring | clean; `git status --short` emitted no paths |
| Prior resume checkpoint commit | `dc6dbb2cf938bcc19c1b1dd423af92a0ed94b067` |
| Accepted-anchor local/remote relation | `HEAD`, `main`, and `origin/main` identical; `main...origin/main` was `0 0` divergent |

This file is necessarily committed after the accepted-state anchor. Resolve
the commit containing this checkpoint with:

```bash
git log -1 --format='%H %s' -- governance/checkpoints/RESUME-005-post-development-evaluation-stop.md
```

At a completed handoff, that commit must be reachable from `HEAD`, the branch
must be `main`, the worktree must be clean, and local `main` must equal freshly
fetched `origin/main`. If any condition fails, stop and reconcile
non-destructively before scientific work.

## 2. Current authority

The authoritative records are:

- acceptance and stop decision:
  `governance/decisions/DEC-0039-accept-development-evaluation-and-stop-complex-model-claim.md`;
- ledger: `governance/gates/gate_status_v38.yaml`;
- scientific status: `governance/PROJECT_STATUS_v38.md`;
- final development report:
  `docs/reports/m1/M1_Development_Release_and_Evaluation_Final_v1.md`;
- binding model protocol:
  `docs/protocols/MODEL_GOVERNANCE_AND_BASELINE_TRAINING_PROTOCOL_v1.md`;
  and
- development execution configuration:
  `configs/development_release_and_evaluation_execution_v1.yaml`.

Their frozen hashes are:

| Artifact | SHA-256 |
|---|---|
| `DEC-0028` model-protocol acceptance | `cab395f3be486a19fca4f5444627fe7bdce2b35e2da89e2b87f646639912d894` |
| `DEC-0032` development authorization | `58076de374cb4f15856cff75dc9737e2d8e032415f6c0bb0aaf64079a5161ab3` |
| `DEC-0038` completed-audit correction authorization | `0f60a38e8cb53454e81200d540879e5a0b577ad303162c174b2eebdc328824fc` |
| `DEC-0039` development acceptance and stop | `b5f9dd5041022321fdaeb77a3d623a480a6a250a2f5d61f1193930805b664bb5` |
| gate v38 | `6bfd775a087ed114ac24351c2c6b8f7f2411a69ea8bde012fc3d8ad75cee0ae5` |
| project status v38 | `c1330372998c1c2ac828903d216ae6211233ec29ea8b00f39b161c2ad35961bf` |
| development final report | `ecefd3679291fe84e258cc15be9a9336b7a4f64f39bd7a3470722ad2537bec76` |
| binding model protocol | `5daf5809b864de75f236ca3552369f943300bdbc86557a3a99277665faeda851` |
| model protocol config | `3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5` |
| development execution config | `d74c683bbeb57e8b455efc789f487ca20df7a128ab0ec27b317dc602eda3e57d` |

`DEC-0039` closes the `DEC-0032` work package. It does not authorize a
protected stage. The third preregistered disposition is final for this claim:
**stop the complex-model claim and stop before protected evaluation**.

## 3. Immutable parent benchmark, model, and training state

`DEC-0022`, `DEC-0024`, `DEC-0026`, `DEC-0028`, and `DEC-0031` remain
binding. Do not reopen or change:

- the 17,000 exact UniProt `2026_02` endpoint sequences or hashes;
- sequence-similarity/leakage graphs, 7,782 components, or the
  `local_domain_union_30` hard rule;
- the 11,900/2,550/2,550 endpoint split;
- P/U identities or semantics, C1/C2/C3 definitions, source cells, sampling
  strata, design weights, bootstrap, degree/hub rules, or claim hierarchy;
- the 16,799 public training-P and 2,000,000 public training-U observations;
- either ESM-2 revision, the 17,000-endpoint pooled embeddings, normalization,
  model architecture, objective, run recipe, seeds, checkpoints, or ensemble
  definitions; or
- any development or protected score, result, prediction, or identity.

U is unlabeled evidence, never a biological or assay-negative class. No
probability, prevalence, calibration, or biological-classification claim is
supported.

The complete Stage 1 registry remains frozen at SHA-256
`11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318`.
It contains the 30 selected checkpoints and ten exact three-seed ensemble
definitions used here. There was no post-release training or checkpoint
change.

## 4. One-time development release and exact scorer census

The final prerelease production and independent validators each passed 14 of
14 checks before decryption. Development was decrypted exactly once. The
custody hashes are:

| Artifact | SHA-256 |
|---|---|
| development ciphertext | `bbbd07472da621a34f45e95ab4b51c799fa0fc967d94de2aa3578e0cda0c1d41` |
| deterministic development archive | `c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122` |
| released development manifest | `3f58403138b878d912789f529dc1f8ec7d1db7356d6ccc4c3b88cfcb2f6554fa` |
| final prerelease production audit | `778b8d68ff102aad005286bc5ab85691e949742c69f116c9027492523d823fd7` |
| final prerelease independent validation | `77ed919c4812453fab85de94a7ce0c52838bb3b7e921db6ca99a045e305ae686` |

Exactly nine cells were scored with 49 scorers: nine mandatory deterministic
controls, all 30 frozen checkpoints, and all ten arithmetic three-seed
ensembles. The exact census is:

| Quantity | Frozen value |
|---|---:|
| cells | 9 |
| primary / source-exclusive cells | 3 / 6 |
| score rows | 9,026,108 |
| P rows | 26,108 |
| U rows | 9,000,000 |
| deterministic controls | 9 |
| selected checkpoints | 30 |
| three-seed ensembles | 10 |
| conservative scoring GPU-hours | 0.09522126329943098 |

All score matrices and release plaintext remain Git-ignored under `.private/`.
Public results contain aggregates only and no pair identity.

## 5. C3-first primary result

The key C3 development results are:

| Frozen scorer | PU-R concordance | Percentile-95 interval |
|---|---:|---:|
| sequence-length ratio control | 0.6608800512102514 | [0.5669951093863831, 0.742349922980613] |
| within-pair 3-mer cosine | 0.6446826375227447 | [0.49809389706477586, 0.7264625851079812] |
| exact training interolog 3-mer | 0.635701358715407 | [0.5257493426482096, 0.754754284382531] |
| selected 150M linear lr-3e-4 | 0.49160758476715566 | [0.43428163991755836, 0.552575197069042] |
| 650M linear lr-3e-4 | 0.4851396894028194 | [0.43449932709449524, 0.5525625635742079] |
| matched no-gate no-dropout | 0.4764291746126709 | [0.4453647624700922, 0.5248018495112559] |
| best complex: partner-gated no-dropout | 0.49134652604741336 | [0.4622492977197828, 0.5372847754287488] |

The exact best-complex comparisons are:

| Comparator | Delta | Paired percentile-95 interval | Result |
|---|---:|---:|---|
| within-pair 3-mer | -0.15333611147533133 | [-0.2459824782324954, 0.019318960348454824] | fail 0.02 and positive-interval rules |
| 650M linear | 0.006206836644593983 | [-0.043158071185191056, 0.050104062093720605] | fail 0.01 and positive-interval rules |
| matched no-gate | 0.014917351434742432 | [-0.0017786841786421868, 0.03245385852354833] | magnitude passes 0.005; interval rule fails |

The best complex lower interval bound is below `0.5`. Simple length,
within-pair sequence, and interolog controls all exceed every learned
ensemble. The partner-gated line does not demonstrate genuine transferable
sequence signal.

## 6. C2 and C1 results

The main C2 and C1 findings are:

| Scorer | C2 PU-R | C2 interval | C1 PU-R | C1 interval |
|---|---:|---:|---:|---:|
| training degree sum | 0.8392632813073615 | [0.8227927097712394, 0.8530794888619072] | 0.9067887878636159 | [0.8944285725001593, 0.9161548102221595] |
| preferential attachment | 0.49999999999151445 | [0.4999999999999904, 0.5000000000000006] | 0.9069423975969924 | [0.89473182781589, 0.9164960880271142] |
| exact interolog 3-mer | 0.6081455864100263 | [0.5435872837841499, 0.6554891193539972] | 0.6209214147156702 | [0.5761362640876896, 0.6543486893446728] |
| within-pair 3-mer | 0.5489599244142936 | [0.49361028728967254, 0.590925219103257] | 0.5174725822527396 | [0.4877858875744042, 0.5586238088839771] |
| selected 150M linear | 0.4977559017089412 | [0.4728472842006161, 0.523091315231223] | 0.4928097327485993 | [0.47261377022728324, 0.5155827343989765] |
| best complex | 0.4938754154112627 | [0.4757619726761884, 0.5124670690144871] | 0.49101376569134214 | [0.46928987251319204, 0.516019978996213] |

C2 is strongly explained by public-training degree and interolog controls. C1
is dominated by degree/preferential-attachment shortcuts. Learned PLM
ensembles are near chance in both cells.

The complete primary record reports every one of the 49 scorers in C3, C2, and
C1, with diagnostic sampled AUROC/AUPRC. Diagnostic AUROC is numerically equal
to concordance here and has no biological-classification interpretation.

## 7. Source, degree/hub, seed, and novel-U diagnostics

The partner-gated no-dropout C3 deltas against the frozen strongest-simple
comparator are `-0.23262459775331246` in HI-II-14-exclusive and
`-0.1406427868176625` in HuRI-exclusive. Positive named-source direction is
absent.

Supported degree/hub summaries are:

| Cell | Quantitative / descriptive degree strata | Top-10% hub / non-hub P | Non-hub interolog | Non-hub selected 150M | Non-hub best complex |
|---|---:|---:|---:|---:|---:|
| C3 | 1 / 0 | 0 / 2,265 | 0.635701358715407 | 0.49160758476715566 | 0.49134652604741336 |
| C2 | 8 / 0 | 8,937 / 2,390 | 0.5986191961663149 | 0.4943181107072152 | 0.49341319215963264 |
| C1 | 9 / 27 | 3,063 / 196 | 0.653349411029331 | 0.45460363074121873 | 0.47521515746272947 |

C3 contains no top-10%-hub P pair, so its non-hub delta is the primary delta:
`-0.15333611147533133`. The required positive non-hub direction fails.

The ten three-seed ensembles were evaluated together with all 30 individual
checkpoints. Nine ensembles meet the `<=0.02` range condition in every primary
cell. The no-gate conservative ensemble is ineligible because its C3 range is
`0.030779809712848716`. Seed stability alone does not establish efficacy or
override a kill criterion.

The C1 novel-U sensitivity retains 817,183 U rows, removes 182,817, retains all
3,259 P rows, has 36 nonempty strata, unique retained pair IDs, and FP64 U
weight sum `8909119.603382831`. The best-complex deficit versus the strongest
simple control is `-0.12215151286601061` in primary C1 and
`-0.12203007817426298` in novel-U C1. It had no selection or stopping role and
does not change the interpretation.

## 8. Frozen selection, complexity, and kill result

The exact selection order is C3, C2, C1, lower frozen complexity, then
lexicographically ascending candidate ID. Metrics are quantized only for
selection to decimal `0.001` with `ROUND_HALF_UP`. The mechanical selected
candidate is:

`lightweight_esm2_150m_linear__linear_lr3e-4`.

That selection does not imply advancement. The best complex candidate is
`esm2_650m_partner_gated_primary__nonlinear_no_dropout`, and it fails the
partner-gate requirements. The following frozen model-level kill criteria are
true:

- best-complex C3 lower bound not above `0.5`;
- no complex C3 gain of at least `0.02` with positive paired interval;
- interolog or frozen-PLM-linear explanation of complex C3;
- absence of gain outside top-10%-hub pairs; and
- shortcut explanation of C1 without qualifying learned C2/C3 gain.

The integrity/custody, protected-boundary, post-release-training, and
U-as-negative flags are false. This is a scientific stop, not an execution
failure. Partner gating, nonlinear-head advantage, and 650M-scale advantage are
not retained claims. No learned model or simple baseline advances to protected
evaluation.

## 9. Independent validation and governed incidents

The corrected production completed-evaluation audit passed 9 of 9 checks. The
standalone clean-room validator was committed only after production evidence,
imports no production development-evaluation module, and passed 16 of 16
checks. It independently:

- rehashed 57 registered files totaling 3,959,706,937 bytes;
- recomputed all nine deterministic scorers over all rows: 81,234,972 values,
  maximum absolute difference `0.0`;
- rescored all 30 checkpoints over all rows: 270,783,240 values, maximum
  absolute difference `0.0`, swap maximum difference `0.0`;
- verified every value of all ten ensembles;
- recomputed every `9 x 49` point metric, supported degree/hub view,
  correlation, all `3 x 19 x 2,000` bootstrap results, C1 novel-U result,
  seed range, selection, complexity rule, and kill flag; and
- confirmed one-time development release, no training/checkpoint change, no
  public pair identity, and no protected key/candidate/truth access.

Evidence order is fixed:

| Event | Commit |
|---|---|
| production results and completed audit frozen | `c7ef1736bce641f21297b66d1ac086f825c6a108` |
| standalone independent validator source frozen | `3a88c737af1bd66a1684c7f66144d89d20035eb1` |
| passing independent evidence frozen | `3e8674944367456a516b91dbb846befaffe1daca` |
| development results accepted and stopped | `011181a1be5f0b65830599fdd5be037512d3c308` |

`ISSUE-0009`, `ISSUE-0010`, and `ISSUE-0011` are closed for this work package.
Each incident failed closed, preserved failed evidence, received a narrow
numbered authorization, added a regression, and passed production and
independent requalification. No benchmark semantic, score, metric, bootstrap
draw, threshold, candidate, or final scientific result changed.

## 10. Frozen development result evidence

| Artifact | SHA-256 |
|---|---|
| scoring-run manifest | `c82be153593ad46101f1ce49e1c79d341da535c71b34ded748c63e478b10dc99` |
| results manifest | `e6b5455e3c1e0346b5b9c9a358db7abc628732b57bab2ec778992d2fbe9c8299` |
| primary metrics | `feb81ccd88cd58e0c4cbe81abce1d9006bf787df5ed927f3a5ba1beee5442e8f` |
| source-exclusive metrics | `6e5246861f843358afac2f60eb8f73a51d41b586dff272f556734da9a7ddfd4f` |
| degree/hub diagnostics | `25ea592ae495e69bf688101444e6c671574553af26c5e1e35edbfb802cc81455` |
| C1 novel-U sensitivity | `a557d53e1a25d5bb21550a687131250fb7a4ed201985a935d05c2a03528dad90` |
| diagnostic correlations | `c1a44d2719163034c7254f30cf1eb1ae2fbdc7953d188eb75ebcb5036c3d9f07` |
| bootstrap registry | `c38ddd0d673c246511dabb1137d14be8936a89c95a4e97006f57e0f81e311be9` |
| selection and kill trace | `ac583545f2dd3c8305dc477cb2d414e75a31800afcb29ddaedc6276cab165c45` |
| completed-evaluation registry | `42aa8b19c4c5cfaf36bfbe1bd19bdf74e7de81df27cccb793809a5ec80d0e189` |
| production completed audit | `1724a645e39ec232827aa8d1a8b6142fd257ec9404f133e985f2330e15e073ba` |
| independent completed validation | `0d3bc35047bd8971177dbe148d1f5a4bbe515ba6d396552e6f3f3cf49f11039e` |

Implementation custody hashes are:

| Artifact | SHA-256 |
|---|---|
| scoring runner | `3adc6b763a1b5862bfc63f68c2f89b3ad734316b0651d550cbd45ac66391c782` |
| evaluator runner | `f9dfe6a5baa2096794fb9fefcc2ed16229246f1385c601836e76c8896eee9a2e` |
| completed-audit runner | `18cb40412176bdc412d224f6b5f91ca1a25281aabea3672cf2dccfbee399afd1` |
| independent completed validator | `cd50d8a54fbdd7f0aeefeadb9219cdf47dcf24cbedef98276ec86851fe6555fa` |
| scoring module | `874b84270be2fe47211a3936907762ebb6442052eb6928adbdcda50ace60ca5f` |
| evaluation module | `df8b4949c3e94120a816ea981ad99dd4138826cd896e33153980ea4763fec38f` |
| completed-audit module | `9ba24d9d1ce7cc1eab9a8c62c1407306a77020c3c579aa119a71b62e9fb8c035` |
| frozen semantics module | `5e63276dbb769659dcb3ca636f0022c485a05bd82f5fc6855ee6aa5b2ee7bd00` |

## 11. Verification record

The repository-wide suite passed 295 of 295 tests in the checksum-pinned data
SIF with `PYTHONPATH=src`. YAML parsing, Git diff checks, ciphertext rehashing,
aggregate table-to-JSON checks, and production/independent evidence hashes
passed.

The required graphify refresh completed with 3,194 nodes, 7,662 edges, and 238
communities. The transient pre-overwrite graph snapshot matched the recorded
pre-refresh hashes before being moved out of the worktree.

No negative, pseudo-negative, external panel, structure, residue/interface
output, new model, additional run, SLURM job, multi-GPU task, protected
prediction, or protected metric was created.

## 12. Current closed boundary

Protected candidates and truth remain encrypted at:

| Package | Ciphertext SHA-256 |
|---|---|
| protected candidates | `5ac1c30dbda85f6274f60febb2f4b01feda34c43bf87f4bbb690abe6c639ff63` |
| protected truth | `69824547667861694aff88a0f6e43526d4f3aa27f930d4a4ff44c924d29aa1e9` |

Do not resolve, stat, read, hash, copy, mount, decrypt, or use either protected
private key. Do not access protected plaintext, create predictions, or compute
protected metrics. Protected evaluation is explicitly prohibited by the
accepted kill result.

There is no active next executable work package. Any future scientific phase
requires a prospective protocol and new numbered governance authorization. It
cannot be treated as continuation of the stopped complex-model claim, cannot
retrain on development, and cannot modify or reinterpret frozen development or
protected evidence.

## 13. Exact fresh-thread preflight

From the repository root, first run read-only Git checks:

```bash
git fetch origin main
git status --short
git branch --show-current
git rev-parse HEAD main origin/main
git rev-list --left-right --count main...origin/main
git merge-base --is-ancestor 011181a1be5f0b65830599fdd5be037512d3c308 HEAD
git log -1 --format='%H %s' -- governance/checkpoints/RESUME-005-post-development-evaluation-stop.md
git log --oneline -10
```

Require a clean worktree, branch `main`, zero divergence, equality of `HEAD`,
local `main`, and `origin/main`, and ancestry of the accepted-state anchor.

Verify current governance and protocol hashes:

```bash
sha256sum governance/decisions/DEC-0039-accept-development-evaluation-and-stop-complex-model-claim.md
sha256sum governance/gates/gate_status_v38.yaml
sha256sum governance/PROJECT_STATUS_v38.md
sha256sum docs/reports/m1/M1_Development_Release_and_Evaluation_Final_v1.md
sha256sum configs/development_release_and_evaluation_execution_v1.yaml
sha256sum docs/protocols/MODEL_GOVERNANCE_AND_BASELINE_TRAINING_PROTOCOL_v1.md
```

Verify frozen public aggregate and validation evidence without regenerating it:

```bash
sha256sum artifacts/results/development_evaluation/development_release_and_evaluation_v1/DEVELOPMENT_RESULTS_MANIFEST.json
sha256sum artifacts/results/development_evaluation/development_release_and_evaluation_v1/PRIMARY_METRICS.json
sha256sum artifacts/results/development_evaluation/development_release_and_evaluation_v1/SOURCE_EXCLUSIVE_METRICS.json
sha256sum artifacts/results/development_evaluation/development_release_and_evaluation_v1/DEGREE_HUB_DIAGNOSTICS.json
sha256sum artifacts/results/development_evaluation/development_release_and_evaluation_v1/C1_NOVEL_U_SENSITIVITY.json
sha256sum artifacts/results/development_evaluation/development_release_and_evaluation_v1/BOOTSTRAP_REGISTRY.json
sha256sum artifacts/results/development_evaluation/development_release_and_evaluation_v1/SELECTION_AND_KILL_TRACE.json
sha256sum artifacts/validation/development_evaluation/development_release_and_evaluation_v1/DEVELOPMENT_EVALUATION_REGISTRY.json
sha256sum artifacts/validation/development_evaluation/development_release_and_evaluation_v1/COMPLETED_EVALUATION_PRODUCTION_AUDIT_REPORT.json
sha256sum artifacts/validation/development_evaluation/development_release_and_evaluation_v1/INDEPENDENT_COMPLETED_EVALUATION_VALIDATION_REPORT.json
```

Verify sealed ciphertext bytes only:

```bash
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/development_release.cms
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_candidates.cms
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms
```

Do not inspect or hash a private key, decrypt a package, or open protected
content during preflight.

The complete read-only unit check is:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python -m pytest -q tests/unit
```

For codebase questions, use the repository graph first as required by
`AGENTS.md`; do not regenerate scientific evidence merely to inspect it.

## 14. Fail-closed escalation

Stop and require a new numbered governance decision if any accepted commit,
hash, count, score, interval, candidate, selection, kill flag, ciphertext,
protected boundary, authority state, or test result differs; if a private key
or protected identity appears; or if proposed work would retrain, tune,
re-score, change a threshold, reinterpret U, or modify the frozen benchmark.

Do not repair a mismatch by regenerating accepted evidence, changing hashes,
opening packages, replacing checkpoints, running an extra seed, creating a
negative or pseudo-negative, integrating an external panel, or silently
broadening authority.
