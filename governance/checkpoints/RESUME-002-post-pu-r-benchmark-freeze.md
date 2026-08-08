# RESUME-002: Post-PU-R-benchmark-freeze phase checkpoint

**Checkpoint date:** 2026-08-09

**Scientific phase boundary:** accepted `DEC-0026`; endpoint/component split,
pair-level PU-R protocol, and pair-level benchmark artifacts are frozen; no
model work has begun

**Use:** this is the self-contained restart record for a fresh Codex thread.
Read it before proposing or performing any next phase. Chat history is not an
authority source.

## 1. Exact repository anchor and handoff invariant

The accepted scientific state immediately before this documentation-only
checkpoint was authored is:

| Field | Frozen value |
|---|---|
| Branch | `main` |
| Accepted-state commit | `c340d7b7ef8723b3dcc16382f5a5f29a0da3082a` |
| Commit subject | `Accept and freeze pair-level PU-R artifacts` |
| Commit date | 2026-08-08 |
| Worktree before checkpoint authoring | clean; `git status --short` emitted no paths |
| Remote check | `git fetch origin main` completed on 2026-08-09 |
| Local/remote relation | `git rev-list --left-right --count main...origin/main` returned `0 0` |
| Local `main` equals `origin/main` | yes, at the accepted-state anchor |

This file is necessarily committed *after* the accepted-state anchor. A file
cannot contain the SHA of the commit that contains the file without changing
that commit. Therefore, after checkout, resolve the documentation commit with:

```bash
git log -1 --format='%H %s' -- governance/checkpoints/RESUME-002-post-pu-r-benchmark-freeze.md
```

At the completed handoff, that commit must be reachable from `HEAD`, the branch
must be `main`, the worktree must be clean, and local `main` must equal the
freshly fetched `origin/main`. If any condition fails, stop before scientific
or model work and reconcile non-destructively.

## 2. Current authority: what controls the project

The authoritative current ledger is
`governance/gates/gate_status_v25.yaml`; the authoritative scientific status is
`governance/PROJECT_STATUS_v25.md`; and the latest accepted decision is
`governance/decisions/DEC-0026-accept-pair-level-pu-r-benchmark-artifacts.md`.
`DEC-0026` accepts the package, but authorizes no next work package.

The binding scientific design remains:

- `docs/blueprints/iPIN_OpenPPI_Blueprint_Amendment_001_PU_Compatibility_Primary_Design_v1.md`;
- `configs/benchmark_estimand_policy_v1.yaml` (`accepted_effective`);
- `governance/decisions/DEC-0011-accept-blueprint-amendment-001-and-authorize-negative-evidence-audit.md`;
- the frozen split accepted by `DEC-0022`;
- the pair protocol accepted by `DEC-0024`; and
- the pair package accepted by `DEC-0026`.

The earlier accepted foundation remains intact: `DEC-0001` through `DEC-0009`
cover initiation, repository/platform qualification, source manifests, raw
acquisition, evidence staging, and primary-source reconciliation. Do not
replace their manifests with current online data or silently remap their
frozen identifiers.

### 2.1 Binding decision chain and hashes

| Decision | Role | SHA-256 |
|---|---|---|
| `governance/decisions/DEC-0011-accept-blueprint-amendment-001-and-authorize-negative-evidence-audit.md` | accepts primary PU-R design | `0de5233f4f5cb34a76212ffca844455d49043f68dd42cef6803dca0eec16a013` |
| `governance/decisions/DEC-0012-accept-negative-evidence-discovery-audit.md` | accepts bounded negative-evidence audit | `7c7212c572c293e809caf4132470e683cd35e45f86b37441a62a8f7d258ba304` |
| `governance/decisions/DEC-0013-authorize-lambourne-y2h-semantics-audit.md` | authorizes Lambourne audit | `8447363fd4c21c44d85d9d1fb590d9a9521264a63ab71bd2ac36b84407400971` |
| `governance/decisions/DEC-0014-propose-lambourne-panel-disposition.md` | proposed external-only disposition; not an acceptance event | `da2487573b7323014e19c0b68520f3bc7ef5f5989ffbe17671ed37625ab5f8c0` |
| `governance/decisions/DEC-0015-authorize-tf-isoform-y2h-audit.md` | authorizes TF-isoform audit | `8c7535d810a3593ecbca8a832a94200dac5f655b84f926bad76fca20ec1cf381` |
| `governance/decisions/DEC-0016-propose-tf-isoform-y2h-disposition.md` | proposed TF-isoform disposition | `314a2bd317b815c64a82bed729aa0b7ecdb416f7e5ebb072cbef7b5b6a13bfc8` |
| `governance/decisions/DEC-0017-accept-tf-isoform-y2h-disposition.md` | accepts TF-isoform technical disposition | `178488341ed3eeeaef4ab68904f4f46e9654c20dcae14bddd5fdd3986966760c` |
| `governance/decisions/DEC-0018-accept-benchmark-eligibility-and-sequence-component-audit.md` | accepts endpoint/component audit | `c8c0ac28c46518ce32e1590403549a1fc9bd40b9c92c3dac50f7aaca67b6e170` |
| `governance/decisions/DEC-0019-authorize-pre-split-feasibility-and-leakage-stress-test.md` | authorizes leakage stress-test | `d193cdcba066e792f7219e7ba1be0a83302d63703551d79b5854cb4fb4438668` |
| `governance/decisions/DEC-0020-accept-pre-split-feasibility-and-leakage-stress-test.md` | accepts leakage stress-test | `301d187f39ddbc8f78c05beea6d3b0cffc119d20c5c4443fba4c2625f7144c51` |
| `governance/decisions/DEC-0021-authorize-final-benchmark-component-split.md` | preregisters and authorizes split | `f5c7e2e1817070be4d035230c246a25c0a014fbdb4018bf7add309f743877323` |
| `governance/decisions/DEC-0022-accept-final-benchmark-component-split.md` | accepts/freeze split skeleton | `29aedd8bc0e3c47f2cab457a13d1d33a2cdca6f0c0e50a24884cff2ab7e67d33` |
| `governance/decisions/DEC-0023-authorize-pair-level-pu-r-benchmark-protocol-freeze.md` | authorizes protocol design | `49800af09d13c430cfb5420bc9da7954ad3e39437b23042872e2537ae81c2177` |
| `governance/decisions/DEC-0024-accept-pair-level-pu-r-benchmark-protocol.md` | accepts/freezes protocol | `289f0af04146ed163190682fa91c0079d559e85e391d46d8cd03313b6ab3dd4c` |
| `governance/decisions/DEC-0025-authorize-pair-level-pu-r-benchmark-artifact-construction.md` | authorizes exact construction only | `eb2d37211ec9560272780b48faf16ce19e85bb75fe3d0ada3a55dbea9138e800` |
| `governance/decisions/DEC-0026-accept-pair-level-pu-r-benchmark-artifacts.md` | accepts/freezes pair package | `1ebe76faeb2059fee648b217b355aa04186453cec192a4f6711838ddad535925` |

Current state-file hashes are:

| File | SHA-256 |
|---|---|
| `governance/gates/gate_status_v25.yaml` | `8371af1172ab10ae10b0cff28aa081fe7677166a58d90eb8554b00cc55861457` |
| `governance/PROJECT_STATUS_v25.md` | `907e584ccb1221046c395878be1c1d56e08d962097d345ca2027d6c2cba0b892` |
| accepted blueprint amendment | `0fb1cc3a02f6a526c195e12e0623f3c69c7513080c5a486be9ea41f71972c40a` |
| `configs/benchmark_estimand_policy_v1.yaml` | `3340b6b9e4130d8011b43ccf92556d59f9278a89a05b08b4c6581ec8b311164d` |

## 3. Scientific state and conclusions already established

1. Public systematic-screen evidence does not reconstruct the complete
   selected/attempted/evaluable opportunity universe. Absence from a released
   positive list is not an experimental negative. Prevalence and a calibrated
   assay-positive or biological-binding probability are not identified.
2. The primary design is therefore frozen as **reference-sequence
   positive-unlabeled ranking (PU-R)**. The model output, if later authorized,
   is a symmetric nonprobabilistic compatibility/prioritization score.
3. Negatome and frozen IntAct-negative records are conditional, heterogeneous
   evidence. They do not form a universal negative class and have no training
   role. Negatome can support only a separately governed protected conditional
   diagnostic; structure-derived non-contact remains a separate evidence
   family.
4. Lambourne 2026 and the 2025 TF-isoform panel are external-only and unused by
   the primary benchmark. `DEC-0017` technically accepts the TF-isoform audit
   and `DEC-0016` disposition. The TF panel is unsuitable for training
   negatives or any training role, universal-nonbinding claims, prevalence,
   calibration, or unseen-endpoint/family benchmarking.
5. The frozen endpoint universe contains 17,000 distinct exact UniProt
   `2026_02` reference-sequence hashes. The algebraic unordered non-self space
   is 144,491,500 pairs. It was never materialized and is not a tested universe
   or prevalence denominator.
6. The original full-length MMseqs2 components contain 12,467/11,311/10,497
   components at 40%/30%/20% exact identity with at least 80% coverage of both
   endpoints. The independent 30% sensitivity challenge found 106 additional
   qualifying edges, 42 crossing original components.
7. Substantial local/domain similarity escapes that full-length rule. At 30%,
   `local_domain_union` has 176,264 edges, 7,782 components, and a largest
   component of 1,624. This operational graph is stricter but is not a
   biological-family ontology or proof of exhaustive nonhomology.
8. A valid final endpoint split was selected under the primary 30%
   `local_domain_union` rule. The prespecified `sensitive_fl80_union` fallback
   was not evaluated because 2,653 of 4,096 primary candidates passed all
   frozen gates.
9. The exact pair protocol and artifacts are complete, independently
   validated, accepted, and immutable. No model, embedding, prediction,
   protected metric, structural label, negative, or pseudo-negative has been
   produced.

## 4. Frozen endpoint universe, leakage rule, and partition skeleton

Endpoint identity is the full SHA-256 of the exact frozen reference sequence.
Sequence replacement, remapping, endpoint addition/removal, component
reconstruction, or partition reassignment is prohibited without a new
versioned governance action.

| Partition | Endpoints | `local_domain_union_30` components | Singletons | Largest component | Internal released-positive pairs |
|---|---:|---:|---:|---:|---:|
| Training | 11,900 | 5,427 | 3,992 | 1,624 | 23,823 |
| Development | 2,550 | 1,071 | 796 | 643 | 2,265 |
| Protected test | 2,550 | 1,284 | 931 | 111 | 2,379 |
| **Total** | **17,000** | **7,782** | **5,719** | — | — |

The selected split has zero cross-partition edges and zero split components
under both independently reconstructed 30% graphs:

| Verification graph | Edges | Components | Largest | Cross-partition edges | Split components |
|---|---:|---:|---:|---:|---:|
| `local_domain_union` | 176,264 | 7,782 | 1,624 | 0 | 0 |
| `sensitive_fl80_union` | 63,180 | 11,292 | 362 | 0 | 0 |

The selected candidate index was 1,064 under seed `20260803`, public salt
`ipin-openppi-final-benchmark-component-split-v1`, preregistered component
ordering/allocation, quantized lexicographic objective, conjunctive acceptance
floors, and lowest-index final tie-break. No result-dependent split choice was
made.

The released-positive source union contains 58,049 exact sequence pairs:
7,504 `HI-II-14_only`, 45,696 `HuRI_only`, and 4,849 supported by both. These
are evidence-source composition counts, not biological prevalence.

## 5. Exact pair unit and C1/C2/C3 semantics

A benchmark pair is an unordered pair of distinct frozen sequence hashes,
sorted ascending. Its ID is
`pair:{SHA256(endpoint_a_sha256 + "|" + endpoint_b_sha256)}`. Reverse
orientations and all evidence records for the same exact pair co-locate in one
role.

- **Training positive:** both endpoints are in the training partition and the
  label-blind C1 role hash assigns the released-positive pair to training.
- **C1 development/test:** both endpoints are in the training partition and
  exposed by at least one interaction-supervised training positive; the pair
  itself is withheld from training and its label-blind hash assigns it to the
  named cell.
- **Exclusive C2 development/test:** exactly one endpoint is an exposed
  training endpoint and the other endpoint is in the named held-out partition.
- **C3 development/test:** both exact endpoints are in the same named held-out
  partition, both are absent from interaction-supervised training, and their
  components are disjoint from training under frozen
  `local_domain_union_30`.

C1 hashing uses salt `ipin-openppi-pair-level-pu-r-protocol-v1`, seed
`20260803`, payload
`{salt}:{seed}:primary:C1:{pair_id}`, the first eight SHA-256 bytes as an
unsigned big-endian integer modulo 10,000, and buckets 0–6,999 training,
7,000–8,499 development, and 8,500–9,999 test. It uses no source, assay,
degree, study, protected label, or model result.

Quarantine is terminal: development-test cross-partition positives, C1
exposure failures, C2 exposure failures, same-sequence/self pairs, ambiguous
projections, and out-of-cutoff evidence are never reassigned.

| Primary role | Pairs |
|---|---:|
| Training | 16,799 |
| C1 development / test | 3,259 / 3,187 |
| C2 development / test | 11,327 / 13,446 |
| C3 development / test | 2,265 / 2,379 |
| Quarantine | 5,387 |
| **Released-positive union** | **58,049** |

The interaction-supervised training graph exposes 4,675 of 11,900 training
endpoints; 7,225 have degree zero. Training-positive degree has median 0, q90
7, q95 14, q99 41, and maximum 279. Protected/development positives never
enter degree strata or model features.

**C3 is not a biological novelty claim.** It does not establish unseen gene,
isoform, homolog, domain, domain architecture, biological family, PLM-unseen
protein, nonhomology, or exhaustive absence of local similarity.

## 6. Information cutoffs and visibility

| Layer | Frozen cutoff / rule |
|---|---|
| Positive evidence | published-2020 HI-II-14/HuRI release union; acquisition `primary-raw-v1-20260803T135432Z`, parsed/reconciled 2026-08-03 |
| Sequences | UniProt human release `2026_02`; exact sequence SHA-256 identity |
| Partitions | `final_benchmark_component_split_v1`, frozen 2026-08-08 under 30% `local_domain_union` |
| External evidence | structures, panels, teacher predictions, text-mined/post-cutoff PPI evidence absent; separate authority required |
| PLM provenance | not yet frozen; no PLM-unseen claim is available |

Interaction-supervised training sees only the 16,799 training positives and
the frozen public training U sample. It must not see withheld C1 identities,
development/test positive evidence, development/test endpoints as interaction
supervision, source/assay/publication labels as model features, or protected
graph degree.

Development remains encrypted. A future numbered decision may release it only
after a training-artifact SHA-256 is frozen. Protected test is invisible to
training, tuning, stopping, architecture choice, and model selection. It is a
one-first evaluator-only operation after the scoring artifact and predictions
are frozen and hashed.

## 7. PU-R candidate and unlabeled-sampling protocol

The persisted pair-state vocabulary is exactly `released_positive` and
`unlabeled`. **Unlabeled pairs are not negatives.** Missing released-positive
evidence is not a nonbinding label, pseudo-negative label, assay-negative
observation, or probability target.

Candidate universes are handled algebraically or by streaming. Self-pairs and
reverse duplicates are excluded. The full 144,491,500-pair space remains
unmaterialized.

The frozen sampler is deterministic stratified bottom-SHA-256 sampling without
replacement:

- public salt: `ipin-openppi-benchmark-v1`;
- seed: `20260803`;
- payload:
  `{public_salt}:{deterministic_seed}:unlabeled:{cell_id}:{stratum_id}:{pair_id}`;
- order: full unsigned 256-bit digest ascending, then pair ID ascending;
- degree basis: interaction-supervised training-positive degree only;
- bins: `0`, `1`, `2`, `3-4`, `5-9`, `10-19`, `20-49`, `50-99`, `100+`;
- allocation: one row per nonempty stratum, then exact Hamilton proportional
  apportionment; fractional ties by ascending stratum ID;
- U inclusion probability in stratum h: reduced rational `m_h/N_h`;
- U design weight: reduced rational `N_h/m_h`; and
- positive census probability and weight: `1/1`.

| Primary cell | Positive pairs | U population | Frozen U rows | Nonempty strata |
|---|---:|---:|---:|---:|
| Training | 16,799 | 10,902,230 | 2,000,000 | 36 |
| C1 development | 3,259 | 10,902,230 | 1,000,000 | 36 |
| C1 test | 3,187 | 10,902,230 | 1,000,000 | 36 |
| C2 development | 11,327 | 11,909,923 | 1,000,000 | 8 |
| C2 test | 13,446 | 11,907,804 | 1,000,000 | 8 |
| C3 development | 2,265 | 3,247,710 | 1,000,000 | 1 |
| C3 test | 2,379 | 3,247,596 | 1,000,000 | 1 |

All 12 source-exclusive development/test cells inherit a 1,000,000-row cap and
use cell ID `source_exclusive:{target_source}:{primary_cell}`. Their positive
counts are:

| Target source | C1 dev/test | C2 dev/test | C3 dev/test | Visible training pairs/endpoints |
|---|---:|---:|---:|---:|
| HI-II-14, HuRI visible | 305 / 280 | 1,601 / 1,488 | 312 / 269 | 14,829 / 4,320 |
| HuRI, HI-II-14 visible | 611 / 633 | 4,751 / 5,270 | 1,677 / 1,869 | 3,252 / 1,868 |

HI-II-14-target C1 and C3 are descriptive only because they miss the 500-pair
floor; its C2 cells pass. All HuRI-target cells pass. Independent study,
assay-version/batch, and temporal holdouts are inactive because the required
metadata are absent or source-confounded.

### 7.1 Prespecified cross-cell U reuse and later C1 sensitivity

`DEC-0024` deliberately keys samplers by cell and does not impose cross-cell U
pair exclusivity. The frozen 20,000,000 cell rows represent 15,536,850
distinct U pair IDs. Exactly 3,778,512 IDs recur across cells, creating
4,463,150 rows beyond first occurrence; maximum reuse is seven cells.
Visibility-group overlaps are 504,264 training/development, 505,482
training/protected-test, and 1,017,784 development/protected-test pair IDs.

This reuse is permitted deterministic design reuse, not positive-evidence
leakage and not negative evidence. Independent validation found zero
positive-as-U rows.

**Future governance flag:** before model results, a separately authorized
model/evaluation protocol should preregister a secondary C1 “novel-U”
sensitivity that asks how C1 recovery changes when comparison U pair IDs are
absent from the frozen public-training U sample. It must be a view over the
already frozen artifacts, not a resample or benchmark rewrite; it must not
alter primary cells, identities, hashes, weights, or headline estimands. The
exact conditional estimand and weight handling must be frozen before any model
result. Development use requires authorized development release; protected
test execution remains evaluator-only after prediction freeze. This checkpoint
does not construct, inspect, score, or authorize that sensitivity.

## 8. Frozen metrics, uncertainty, and future baseline definitions

Primary metrics are reported separately by C1/C2/C3 and by development/test:

1. Horvitz-Thompson-weighted positive-vs-U pairwise concordance, with half
   credit for ties. This is the only primary metric supported by the realized
   sampled package alone.
2. Held-out released-positive Recall@10, @100, and @1000, macro by query with
   micro secondary, only after exact streaming full-candidate ranking.
3. Released-positive enrichment at candidate fractions 0.0001, 0.001, and
   0.01, only with the governed full ranking.
4. Positive rank percentile (mean, median, q10, q90), only with the governed
   full ranking.

Exact Recall/rank/full-universe metrics remain demoted unless later authority
provides exact streaming full-universe scoring without materialization. A
sampled universe may never be renamed the full universe. Sampled AUROC/AUPRC
may be diagnostic only and is not biological classification performance.

Uncertainty is frozen as a 2,000-replicate two-endpoint
`local_domain_union_30` component pigeonhole bootstrap, seed `20260803`, NumPy
`PCG64DXSM`, percentile 95% intervals. Sampling and bootstrap weights are both
retained. Paired comparisons reuse identical samples and bootstrap draws.

The following later baselines are frozen in definition but have not been
implemented or run:

- deterministic hash control, salt `ipin-openppi-pu-r-baseline-v1`, seed
  `20260803`;
- endpoint degree sum `log1p(d_a) + log1p(d_b)`;
- preferential attachment `log1p(d_a * d_b)`; and
- frozen-component degree-mass product.

No held-out label, held-out/full-graph degree, source label, or protected
metadata may enter a baseline; no baseline may be tuned on test.

## 9. Frozen benchmark package and reproducibility hashes

The canonical package root is
`data/canonical/pair_level_pu_r_benchmark_artifacts_v1/`. It is approximately
1.9 GiB and intentionally ignored by Git. Its versioned manifest/report/code
records and the local frozen payload are jointly required for reproducibility.

### 9.1 Core package records

| Artifact | SHA-256 |
|---|---|
| `configs/pair_level_pu_r_benchmark_artifacts_v1.yaml` | `cdafad900887e74a6148cdb6d6832e56392649703c261909d5f581e39fd9e795` |
| `governance/gates/gate_status_v24.yaml` (construction authority) | `4f46755bc875a15c97b961868fffd0f76e24f19d5ebf444b78ac97fb6d748b58` |
| `governance/PROJECT_STATUS_v24.md` (construction status) | `67f6de12cf9a0517f448fc7512af396c5b337bacd0eb26bd3683d7e32605cc39` |
| `schemas/canonical/pair_level_pu_r_benchmark_artifacts_v1.yaml` | `362af841f0396c26c83921c07d613f2c370213b740450268fbbb2dc4c3367ac3` |
| `artifacts/runs/pair_level_pu_r_benchmark_artifacts_v1/RUN_MANIFEST.json` | `17d396eb1771db784b30f18eb05acc82efd4efa421939d389cd1a4f6b63240e6` |
| `data/canonical/pair_level_pu_r_benchmark_artifacts_v1/PACKAGE_MANIFEST.json` | `f0f850daf795481c8a1ae0ba64f6d050ae757f2738497ac0517003c6822015f5` |
| `data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/TRAINING_PACKAGE_MANIFEST.json` | `4d46c7d4cbe6f6c56c2499621110c85c136635a1a8c26511ff776b9ee0d58737` |
| `artifacts/validation/benchmark_design/pair_level_pu_r_benchmark_artifacts_v1/CONSTRUCTION_REPORT.json` | `878beb38af78157b8b4b3ff50cb7658266900add86a96d7d9e5baca8745c3f65` |
| `artifacts/validation/benchmark_design/pair_level_pu_r_benchmark_artifacts_v1/VALIDATION_REPORT.json` | `7eede006ba18dbc4dcc71128743722718bc73f0f6891834ad4ebc0a6ed614e86`; 13 pass, 0 warning, 0 fail |
| `docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Artifacts_Final_v1.md` | `5e95d43a26fe737693d6a4085719d77d273268a3a1c4417db651f703e70a2570` |
| `docs/reports/m0/PROTECTED_TEST_EVALUATION_PROCEDURE_v1.md` | `4d74431c523ef950096685929bad8c98e24dd3aad81efb15c8dd6b7bb13477b8` |

Production construction ran from clean Git commit
`043bd73f4b0e6d102b339b5ac66213a88674bb94`; independent validation ran
from clean evidence commit `7dc5e0ea1bfb87526178d569350bdb4d86c15559`.

### 9.2 Public training payload

Paths below are relative to the package `training/` directory.

| File | Rows | Bytes | SHA-256 |
|---|---:|---:|---|
| `positive_pairs/part-00000.parquet` | 16,799 | 992,813 | `4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499` |
| `unlabeled_pairs/part-00000.parquet` | 2,000,000 | 156,475,941 | `d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7` |
| `sampling_strata/part-00000.parquet` | 36 | 6,464 | `b8e4247ce934d837477513b322af008413ac8d61fa95ccedd16fe2712c1d6427` |

### 9.3 Sealed payloads

Paths below are relative to the package `sealed/` directory. The plaintext
archive hashes are immutable construction records; **do not decrypt merely to
verify them during model development**.

| Package | Ciphertext file | Ciphertext bytes | Ciphertext SHA-256 | Recorded plaintext archive SHA-256 |
|---|---|---:|---|---|
| Development | `development_release.cms` | 707,185,228 | `bbbd07472da621a34f45e95ab4b51c799fa0fc967d94de2aa3578e0cda0c1d41` | `c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122` |
| Protected candidates | `protected_candidates.cms` | 409,416,269 | `5ac1c30dbda85f6274f60febb2f4b01feda34c43bf87f4bbb690abe6c639ff63` | `1589954c0cfd6def62038282066b4d2417f223ed06b1a996f83f1a0a0b0399c6` |
| Protected truth | `protected_truth.cms` | 710,738,504 | `69824547667861694aff88a0f6e43526d4f3aa27f930d4a4ff44c924d29aa1e9` | `07ffa2a4af2d81f1d516ef4f38b38308fa9d808496ed1042814f85477bf5e9ab` |

Frozen layer counts are:

| Layer | Positive rows | Sampled-U rows | Other |
|---|---:|---:|---|
| Public training | 16,799 | 2,000,000 | 36 strata rows |
| Encrypted development | 26,108 primary/source positive rows | 9,000,000 | 18,081 source-visible training rows |
| Encrypted protected candidates | 28,821 positive-candidate rows within 9,028,821 total candidates | 9,000,000 | label-free candidate package |
| Encrypted protected truth | 28,821 truth rows | 9,000,000 | complete 58,049-row role ledger |

### 9.4 Public certificates and private-key custody

| Role | Versioned certificate | Certificate-file SHA-256 | X.509 fingerprint SHA-256 |
|---|---|---|---|
| Development | `governance/keys/pair_level_pu_r_benchmark_artifacts_v1/development_release_certificate.pem` | `99e224e028db6629514f8b6b1d9784ca4ed7599f71ad88d4e276048c8f8341d9` | `8845d4bccb1c999b70f3dd9189be9b09ee525ebff39f63e1176dbdf1847f98e7` |
| Protected candidates | `governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_candidates_certificate.pem` | `b53dc3fbedf1b17b99dc1eea6efe782305bf3d6e7a16b30e7cb8011e489611b1` | `cf6d5ecdd71efb5fbcecb68f0db82fd5bca6de1346712425603c3688a8b107e2` |
| Protected truth | `governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem` | `4504fdf748090e1122cfb914ccc7209c1afe0cf5c0aa53693aea4917d0801584` | `29551b486d4b814ee255960cb831db88b52ac68c3c44cf155493b3ff6a5c671c` |

The three private keys are distinct, ignored, account-protected, and mode
`0600` under `.private/pair_level_pu_r_benchmark_artifacts_v1/`. Their names
are `development_release_private.pem`, `protected_candidates_private.pem`, and
`protected_truth_private.pem`. Do not read, hash, copy, mount, publish, or use
them during model development.

## 10. Frozen parent benchmark records

Each manifest below transitively records table paths, row/byte counts, schemas,
and content hashes. These parents are immutable and must not be regenerated to
“refresh” the benchmark.

| Workstream | Config | Canonical/run manifest | Reports and validation |
|---|---|---|---|
| Endpoint eligibility/components | `configs/benchmark_eligibility_and_sequence_component_audit_v1.yaml` — `b3bc6d802799d2fb47f351b6311c951945a8517d27e573be7fc4209e452a22e5` | canonical `data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/AUDIT_MANIFEST.json` — `1a7769fa550ac7eef9acd40da72c8f5247c0c81cb1bb77a913e185d090d83f96`; run `artifacts/runs/benchmark_eligibility_and_sequence_component_audit_v1/RUN_MANIFEST.json` — `81af038c3468e5b15f0e9dc287fd8f191181a059cfed239a9e36485c82cc47b4` | report `docs/reports/m0/M0_Benchmark_Eligibility_and_Sequence_Component_Audit_Final_v1.md` — `b493ec74366f70a601c5bfcb957bb1018d164c4e3e73c9c33ffb6b3eedb69075`; audit `6f77fe0fb65205e0a45dd9c61631a3982c4b999efc0c5575f1799b7a726df41c`; validation `6fd3b822c9c02e138d94f6ea78386fcdea2f43acff9156f5fc0e0a4e632f58a8` |
| Leakage stress-test | `configs/pre_split_feasibility_and_leakage_stress_test_v1.yaml` — `0648107f96f079b502dfce4c0c470c1199514463615c107f152a06603f75281f` | canonical `data/canonical/pre_split_feasibility_and_leakage_stress_test_v1/AUDIT_MANIFEST.json` — `8b2200b34149c1a4ecf92274cac886acbafc2d53b2cac3e8167c91610ec860f2`; run `artifacts/runs/pre_split_feasibility_and_leakage_stress_test_v1/RUN_MANIFEST.json` — `a76731632f5d137d0fa2b2eab244c2e86a7a10cd4b67013d8164bb684b902755` | report `docs/reports/m0/M0_Pre_Split_Feasibility_and_Leakage_Stress_Test_Final_v1.md` — `9483cb394541ee4f4981dde3845d9fd2ce0780992192bb20f7d5651ed812e6d1`; audit `5f4e655a81b70a4dd2143a81027188b692ca120b0fab7f919d18b53fd4eabb6f`; validation `1f0f862796f1ab581ca4c3c528987cd1fdf484269d5ca932f99eb9d946e1e809` |
| Final component split | `configs/final_benchmark_component_split_v1.yaml` — `b8dac7c7de5fc3935a5bf642afe12b2b5e7e5b40fa9883d1dc04962bfed25ecf` | split `data/canonical/final_benchmark_component_split_v1/SPLIT_MANIFEST.json` — `81800ec810d83a53d83e36dca277a425e4a8fd1f7f50009916da73e14021351a`; run `artifacts/runs/final_benchmark_component_split_v1/RUN_MANIFEST.json` — `615051b335c25351a46a6de0eba8b87c9a82391cf7c63216c21280846b06d52e` | report `docs/reports/m0/M0_Final_Benchmark_Component_Split_Final_v1.md` — `d82bf17a4851ae62c8cc6f959faaddfead66da9c86f104f617f8a42883ccdb8f`; audit `bbb8e65efd661342b22f54a6fa72ffe4115dfc1e18b4f97d066e4124fe9124c8`; validation `e0864a857285c21341ce4db44d1a142ff6532101804ead5b8f421df6ab4d6e0f` |
| Pair-level protocol revision 2 | `configs/pair_level_pu_r_benchmark_protocol_v1.yaml` — `7b0cefa1b461f0e58d3e6f4ff72da2d6ad4ac39522a897ce4057e756fa84f2a6` | frozen split manifest above is its immutable parent | report `docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Protocol_Final_v1.md` — `4cae2023795237d9350a77ae52a8ac72abeff4e0c7ac57340d1bfeb838306627`; accepted audit `b226a83fa31a78aa97cc6172adb65b386f0181b86ab2c7cb0939cf6dd4ea9d66`; validation `8c94f10131ed7e100fadf1dc6174c4aaf7b5301d3dbece74725a994183a10741` |

The accepted protocol evidence is only
`pair_level_pu_r_benchmark_protocol_v1_revision_2`; the earlier unrevisioned
audit is qualification history and has no acceptance role.

## 11. Completed workstreams that must not be reopened

The following are closed at this checkpoint. Do not reacquire, rerun,
recompute, extend, overwrite, reinterpret, or “improve” them as part of a
future model phase:

1. **Literature/systematic-screen and negative-source discovery.** The public
   attempted/evaluable-universe gap and PU-R disposition are established.
   Authority: accepted blueprint amendment and `DEC-0011`. Records:
   `configs/systematic_screen_metadata_audit_v1.yaml`
   (`baedc6cdd96d89790497293650421db4c385fb5747c3a456b27712096e55af5b`),
   `docs/reports/m0/M0_Systematic_Screen_Metadata_Audit_and_Benchmark_Estimand_Proposal_v1.md`
   (`9773e6de8b30dff6f26e5d1ef772baa4cab292c1f4e1cc7773eeb395855cfd19`),
   production audit `db75b0cb2863cc1b44e45759e924bfc4b00d379fa291873e7e3e10e99748fc5e`,
   validation `2ca92051172b7a7a512072f3ed6212ac8caed5891870abcea7c6e5929cd56a01`.
2. **Negatome/IntAct negative-evidence audit.** `DEC-0012`; config
   `318f6847f1fb40be88fcf112f28fe1bdd7c7526012a398c00e6e9f8d2f025e0f`;
   canonical manifest `593b1b45ef579f4f4f403f8567510c28b0ac84b8818ac82d3b27a6d2dce9be24`;
   audit `ccefebc920ec5c3d1a04d271babbdee044608662ef88d87615a274d82f6e6315`;
   validation `e3b7b8da6fbb9d6361278e9d89ab1cdd070c087279a8a821dc852cfd5f4fc155`;
   report `docs/reports/m0/M0_Negative_Evidence_Discovery_Audit_Final_v1.md`
   (`eccb2371f4c676cb7e8621c9115643ecce3466ebf0ff7015b4dfeab17a2fb476`).
3. **Lambourne 2026 human Y2H audit.** Technically complete, independently
   validated, external-only; `DEC-0014` remains a proposed disposition rather
   than a fabricated acceptance event. Config
   `3628d876f56f8d6ba6a0248ccf002ab4e0a54429e3fe223fa664ececa7eab64c`;
   canonical manifest `3240c362fe05a7a68d579deccabdf8a608b43cbbf25ea0c7f703595698986d98`;
   audit `361fe5bcc98e782b1cc36f3111f00865a5db9f025b01f0c1719b6a11eb60a836`;
   validation `bd7812eede90f8cf0fac62a1690c8164115501476e7fa67b40470cf1673874d5`;
   report `docs/reports/m0/M0_Lambourne_2026_Human_Y2H_Pair_Semantics_Audit_Final_v1.md`
   (`86283618b1f3a45b4d2d15743bb59fab6c7a5b68c870b67469258bc2194af955`).
4. **TF-isoform 2025 audit.** Technically accepted by `DEC-0017`, external-only
   under `DEC-0016`. Config
   `c28350448992b6845a8bf5f145bf5f7d5c6e7c51c1d7c8595fc4594e26ca4408`;
   canonical manifest `c71de2354bacfdef43b35d7f0ecbe07851568ab4abeb6a23df7065f1d8c39b68`;
   audit `9235569bd40adc4114c0b1f4387e57fb4fcabc823a28a3509676607ef809a281`;
   validation `af9297e54203b7486a883eaa555d006dfac57da232f475f165395cf888f42327`;
   report `docs/reports/m0/M0_TF_Isoform_2025_Y2H_Semantics_and_Contamination_Audit_Final_v1.md`
   (`85020d970eed70782219cdd21d84bc90791080e770bd20c5d93e4ce055fa0760`).
5. **Sequence endpoint/component construction.** Accepted by `DEC-0018`; the
   17,000 endpoints and 40%/30%/20% inventories are immutable.
6. **Pre-split feasibility and leakage stress testing.** Accepted by
   `DEC-0020`; do not rerun MMseqs2 or extend leakage searches in a model phase.
7. **Endpoint/component splitting.** Accepted by `DEC-0022`; do not search for
   a “better” allocation or activate the unused fallback.
8. **Pair-level PU-R protocol design.** Accepted revision 2 by `DEC-0024`; do
   not change assignment, sampling, metric, uncertainty, holdout, or claim
   rules after seeing model results.
9. **Pair-artifact construction.** Accepted by `DEC-0026`; do not add, remove,
   resample, relabel, release, decrypt, or rewrite any package row.

## 12. Protected-test secrecy and custody rules

During model development, **all** of the following are forbidden:

- decrypting or opening development, protected-candidate, or protected-truth
  packages without the exact separately authorized stage;
- inspecting protected candidate identities, truth identities, pair IDs,
  source membership, degree, stratum, component, role, state, or weight;
- reconstructing protected candidate or truth sets from the public universe,
  sampler, code, hashes, manifests, logs, or any side information;
- set-difference, membership-oracle, hash-probing, or other inference of
  protected identities;
- running the controlled candidate opener, scorer, protected evaluator, or any
  metric computation;
- accessing, hashing, copying, mounting, or testing protected private keys;
- generating a public pair-keyed prediction file or leaking predictions/logs
  as an identity channel; and
- using protected identities or results for training, tuning, stopping,
  feature selection, architecture choice, calibration, reruns, or release.

A later authorized protected evaluator must be no-network and have no
model-development filesystem mounted. The scorer sees only
`candidate_token`, `endpoint_a_sha256`, `endpoint_b_sha256`, and `cell_id`.
Unprojected plaintext is deleted before session persistence. Predictions must
be complete, unique, finite, and hashed; the scorer/session must be rehashed;
an exclusive irreversible package-scoped one-first ledger must be reserved
before truth decryption. Only aggregate receipts may leave the boundary under
`artifacts/validation/protected_evaluation_receipts/`. An interrupted attempt
is consumed. A rerun requires a new protocol and split version.

One curator-only quarantine pair hash appeared in a transient, unversioned
preproduction validator exception before identity-safe error handling. It was
not a training, development, or protected-test positive and never entered a
model workflow. It remains quarantined. Do not search logs for it.

## 13. Claim boundaries and prohibited interpretations

Authorized later wording is limited to recovery and ranking of withheld
**released-positive evidence** under this frozen PU design.

The following interpretations remain prohibited:

- unlabeled pair = negative, nonbinding, failed assay, or pseudo-negative;
- universal nonbinding or a universal positive/negative benchmark;
- natural or biological prevalence, class prior, biological precision, false
  positive rate, calibrated assay probability, calibrated binding probability,
  or absolute binding probability;
- sampled-U package = full candidate universe;
- C3 = unseen biological family, novel family, family generalization, unseen
  domain, unseen gene/isoform/homolog, PLM-unseen protein, proven nonhomology,
  or exhaustive homology freedom;
- primary mixed-source cells = source-, study-, assay-, batch-, or temporal
  generalization;
- external-panel outcomes = training labels, training negatives, prevalence or
  calibration evidence, or unseen-endpoint/family benchmarks;
- model score = probability or experimentally validated interaction; and
- any experimental-validation claim from this computational project.

The primary PU-R design is frozen. A future training loss may operationally
contrast positives with U examples only under a separately frozen PU training
protocol; that does not convert U into scientific negatives.

## 14. Remaining unauthorized work

At this checkpoint no next work package is authorized. In particular, do not:

- release development or access protected candidates/truth;
- create additional pair/sample rows, negatives, pseudo-negatives, or labels;
- materialize the full candidate-pair universe;
- change endpoints, components, partitions, C1/C2/C3 roles, sampling, weights,
  metrics, uncertainty, or custody rules;
- integrate Lambourne, TF-isoform, Negatome, IntAct-negative, structure, teacher,
  text-mined, or post-cutoff evidence;
- derive structural labels or interfaces;
- download, select, embed with, implement, train, tune, stop, calibrate,
  evaluate, route, or release any model; or
- compute any development/protected prediction or metric.

## 15. Recommended next phase, subject to a new numbered authorization

The next governance package should be **model-development governance without
protected-test access**, not model execution. It should freeze, before model
results:

1. PLM provenance: exact model/checkpoint hashes, tokenizer, software,
   pretraining-data/cutoff evidence, license, local cache, feature-extraction
   boundary, and the continuing absence of any PLM-unseen claim.
2. Implementation of the already frozen simple baselines, seeds, deterministic
   tie handling, and permitted inputs.
3. A PU training/model-selection protocol: objective and U semantics,
   inclusion/design weighting, reproducible training seeds, development-release
   prerequisite, stopping/selection rules, uncertainty, comparison plan, and
   the secondary C1 novel-U sensitivity.
4. Architecture governance: swap symmetry, endpoint encoder provenance,
   combination/head design, capacity/ablation bounds, compute budget,
   feature/metadata prohibitions, artifact registry, and fail-closed checks.
5. Separation of public training, future authorized development, and the
   sealed one-first test evaluator. No protected access is needed or permitted
   for this phase.

Do not infer authorization from this recommendation. Wait for a new numbered
decision that states the exact bounded package.

## 16. Exact fresh-thread preflight

Run these checks from the repository root before any new work. They are
read-only and must not decrypt or inspect sealed content.

### 16.1 Read authority and query the graph

```bash
sed -n '1,800p' governance/checkpoints/RESUME-002-post-pu-r-benchmark-freeze.md
sed -n '1,260p' governance/decisions/DEC-0026-accept-pair-level-pu-r-benchmark-artifacts.md
sed -n '1,320p' governance/gates/gate_status_v25.yaml
sed -n '1,280p' governance/PROJECT_STATUS_v25.md
graphify query "What is authorized after RESUME-002 and DEC-0026, and what protected-test actions remain forbidden?" --budget 4000
```

### 16.2 Prove repository identity and synchronization

```bash
git fetch origin main
git branch --show-current
git status --short --branch
git rev-parse HEAD main origin/main
git rev-list --left-right --count main...origin/main
git log -1 --format='%H %s' -- governance/checkpoints/RESUME-002-post-pu-r-benchmark-freeze.md
```

Require branch `main`, no status paths, and divergence `0 0`. Never discard or
overwrite unexpected user changes. If `HEAD` is later than the checkpoint,
read every intervening governance decision before proceeding.

### 16.3 Verify immutable sidecars and direct hashes

```bash
sha256sum containers/images/ipin-data-arm64_0.1.2.sif
(cd data/canonical/benchmark_eligibility_and_sequence_component_audit_v1 && sha256sum -c AUDIT_MANIFEST.json.sha256)
(cd data/canonical/pre_split_feasibility_and_leakage_stress_test_v1 && sha256sum -c AUDIT_MANIFEST.json.sha256)
(cd data/canonical/final_benchmark_component_split_v1 && sha256sum -c SPLIT_MANIFEST.json.sha256)
(cd data/canonical/pair_level_pu_r_benchmark_artifacts_v1 && sha256sum -c PACKAGE_MANIFEST.json.sha256)
(cd data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training && sha256sum -c TRAINING_PACKAGE_MANIFEST.json.sha256)
(cd artifacts/validation/benchmark_design/pair_level_pu_r_benchmark_artifacts_v1 && sha256sum -c CONSTRUCTION_REPORT.json.sha256 && sha256sum -c VALIDATION_REPORT.json.sha256)
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/positive_pairs/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/unlabeled_pairs/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/sampling_strata/part-00000.parquet
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/development_release.cms
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_candidates.cms
sha256sum data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms
```

The SIF must hash to
`72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`.
Compare all other direct outputs to section 9. Do not use private keys or
decrypt packages to verify recorded plaintext hashes.

### 16.4 Run lightweight fail-closed tests in the pinned container

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
  tests/unit/test_pair_artifacts_semantics.py
```

Do not run construction commands, production validators that require private
keys, `release-development`, `open-protected-candidates`, or
`evaluate-protected` as preflight.

## 17. Fail-closed escalation rule

If any frozen artifact, count, assignment, manifest, checksum, certificate,
scope guard, secrecy control, or authority record appears inconsistent:

1. stop all downstream work;
2. do not edit, regenerate, resample, remap, decrypt, or “repair” the artifact;
3. preserve the exact error and read-only evidence without protected identity;
4. create a numbered governance issue describing the mismatch, affected hash,
   observed/expected values, and claim impact; and
5. wait for explicit resolution and a new numbered decision before continuing.

Never silently change a frozen artifact. Scientific uncertainty, missing
authority, or a failed integrity check closes the gate rather than weakening
it.

## 18. Resume instruction to a fresh Codex thread

Do not ask the project owner to reconstruct this history. Execute section 16,
read any later governance records, and report whether the repository satisfies
the handoff invariant. If it does, the exact next action is to prepare or review
a newly authorized model-development-governance package scoped as section 15,
without protected-test access. If no new numbered authorization exists, stop
at governance; do not begin model work.
