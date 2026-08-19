# RESUME-006: Post-local-representation-diagnostic stop checkpoint

**Checkpoint date:** 2026-08-19
**Accepted-state commit:** `6a3e930c6423a345579f8a25e9cc615e77a670ea`
**Accepted-state subject:** `Accept local representation diagnostic and stop branch`
**Branch:** `main`
**Scientific boundary:** DEC-0044 accepts the complete public-training-only
local-representation diagnostic, prohibits conditional Phase B, and stops this
architecture branch.

## 1. Resume authority

Treat the following as authoritative, in order:

1. `governance/decisions/DEC-0044-accept-local-representation-diagnostic-and-stop-branch.md`
2. `governance/gates/gate_status_v43.yaml`
3. `governance/PROJECT_STATUS_v43.md`
4. `docs/reports/m1/M1_Public_Training_Local_Representation_Diagnostic_Final_v1.md`
5. the frozen DEC-0041 revision-2 protocol and configuration
6. the registered production and independent-validation artifacts below

The parent DEC-0039 development disposition and all benchmark freezes remain
unchanged. This checkpoint grants no new modelling or evaluation authority.

## 2. Recorded repository state

At checkpoint creation, accepted commit
`6a3e930c6423a345579f8a25e9cc615e77a670ea` was pushed to `origin/main`, local
and remote accepted-state commits were equal, and the worktree was clean before
this checkpoint file was added.

Relevant commit sequence:

| Commit | Meaning |
|---|---|
| `8ad3403` | authorize the public-only local-representation diagnostic |
| `45f0d24` | freeze the unambiguous revision-2 scorer set before execution |
| `449a0a9` | implement the frozen diagnostic |
| `95671be` | authorize the fail-closed FP32 reconstruction audit correction |
| `df7baa6` | authorize exact FP64 cosine reductions before score production |
| `220d0c4` | freeze production Phase A results and validation |
| `de85642` | add the standalone independent validator |
| `ba56c40` | freeze independent validation evidence |
| `6a3e930` | accept the result and stop the branch |

## 3. Exact scientific result

The frozen public-training whole-component split held out `1,366` components.
The primary nested C3 evaluation contained `650` P rows and `86,450` U rows.
It used original PU-R design weights and Horvitz--Thompson
positive-versus-unlabeled concordance.

| Frozen scorer | Concordance | Descriptive paired-component 95% interval |
|---|---:|---:|
| sequence-length ratio | 0.5727422626702259 | [0.5250772394548257, 0.621777142049551] |
| matched global pooled ESM cosine | 0.5687588309531323 | [0.5114872955678936, 0.6276757229354809] |
| within-pair 3-mer cosine | 0.5637757422342236 | [0.49947563071783047, 0.6232847899069026] |
| local maximum segment cosine | 0.5617051552521716 | [0.4999349625510295, 0.6302009715719031] |
| **local top-four segment cosine** | **0.5531708398478847** | **[0.4879500484437132, 0.6252063781173702]** |
| exact nested-training interolog 3-mer | 0.5180710999849886 | [0.4506851665749138, 0.5834620627577978] |
| deterministic hash | 0.4935063403727369 | [0.45984218282450307, 0.5348054250797372] |

The frozen trigger required primary local concordance at least `0.51` and
primary local minus matched global at least `+0.01`. The observed delta was
`-0.015587991105247556`, with descriptive paired-bootstrap interval
`[-0.042924265306829947, 0.0067081094539078205]`. The joint trigger failed.

**Binding disposition:** no incremental coarse local-representation signal;
conditional Phase B was not run and is prohibited; stop this architecture
branch.

This result does not prove that all learned token-, residue-, or domain-aware
models are impossible. Such a model would now be a new speculative work
package requiring a fresh prospective rationale, protocol, budget, and numbered
decision. Already spent development information and sealed protected material
may not be used to design it.

## 4. Extraction and execution record

- runtime node: Arrhenius interactive node `n180`
- GPU: one NVIDIA GH200 120 GB
- frozen encoder: ESM-2 150M revision
  `a695f2f00a0d56a22d86b9469abe2b20622c2a0d`
- frozen checkpoint SHA-256:
  `c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566`
- qualified model SIF SHA-256:
  `c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`
- extracted endpoints: `11,900`
- exhaustive segments: `56,304`
- retained segment vectors: FP32
- local cosine normalization/reductions: FP64 on retained FP32 values
- extraction wall time: `149.65228069300065` seconds
- conditional Phase B status: `not_run_trigger_failed`

No training run, new checkpoint, negative, pseudo-negative, development
release, protected release, external panel, residue/interface label, or
adaptive scorer was used.

## 5. Validation record

Production validation passed `7/7` checks. The independent validator:

- was implemented after production evidence commit `220d0c4`;
- imports no `ipin_openppi` production module;
- passed `13/13` checks;
- independently reconstructed the split and row census;
- independently recomputed all `609,700` scores with maximum difference `0.0`;
- independently recomputed all point estimates with maximum difference `0.0`;
- independently recomputed all `1,400` bootstrap values and intervals with
  maximum difference `0.0`;
- independently reproduced the failed trigger and mandatory Phase B stop;
- rehashed `43,650,560` retained embedding values; and
- found no forbidden development/protected/key/external information flow.

The checkpoint-prescribed complete unit suite was run with:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python -m pytest -q tests/unit
```

Result: `301 passed in 14.64s`.

## 6. Fail-closed implementation incidents

ISSUE-0012 and ISSUE-0013 are closed by DEC-0044.

1. The first embedding forward completed but wrote no embedding file because an
   unfrozen `2e-6` FP32 regrouping audit tolerance was too narrow. DEC-0042
   changed only that audit tolerance to `1e-4`; retained values and formulas
   were unchanged.
2. The first score attempt wrote no score or metric file because its GPU path
   reduced in FP32 while the exact CPU reference used FP64. DEC-0043 promoted
   only cosine arithmetic on the unchanged retained vectors to FP64. The
   production CPU/GPU sample maximum difference was
   `1.5696193456093965e-8`.

Neither incident changed data, scorer definitions, metrics, trigger thresholds,
or scientific semantics.

## 7. Authoritative hashes

| Artifact | SHA-256 |
|---|---|
| DEC-0044 | `0a1ce0e49928e2bb00a36eba6989e9a4c302d3e05788e0de2ab2c446c9dcae3f` |
| gate v43 | `9806579df55b7d0c104e3f98e33b5f0aa87bfac595867699347f1769c28666b4` |
| project status v43 | `980ebea98bc008a90c0db642fe5d3a30cc653e2ff500cc7020e5168d28cb4d0d` |
| final report | `794bfb8d8f089b69c620cbadd868f4e1c11b8a037a882e6575c00eed017ee574` |
| revision-2 config | `c22d8de53d6f53a0f8054767387dc8a28541c353e0dabaff8041005e1ffe12fc` |
| revision-2 protocol | `6940e7ba91f3a7835b1bd70b2d84594ac5af495013f01084a37897a2c2201a69` |
| embedding manifest | `3f8d644eb42e3a740e62d1de440ec627d25ef47b3970fd358578970430810146` |
| Phase A results | `becf069b9bae635af2554ba89849e659967baa6b073acb1346d0ebdac2a79544` |
| raw Phase A scores | `462d3c45296298e84bf1747bcce3050a8fd20e8837c48bf78dd425a513caf7ca` |
| production registry | `52aa06c0785e23e65c68899124634bd891ef963b45749b2f76be538537a8bebd` |
| production validation | `6956289ce1a4aef4d5d342b2d04bac043cf0af417a4b008916b46e898babfb39` |
| independent validation | `7ac2e2bf4b54c8001c238d233121c88ba40f9c5e0240282ca7c81b53da7a68fe` |
| protected-candidate ciphertext | `5ac1c30dbda85f6274f60febb2f4b01feda34c43bf87f4bbb690abe6c639ff63` |
| protected-truth ciphertext | `69824547667861694aff88a0f6e43526d4f3aa27f930d4a4ff44c924d29aa1e9` |

## 8. Mandatory resume preflight

On resume, first verify branch, commit ancestry, remote equality, cleanliness,
and the hashes above. Hash protected ciphertext bytes only; do not decrypt or
inspect their contents.

```bash
git fetch origin main
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git status --short
git merge-base --is-ancestor 6a3e930c6423a345579f8a25e9cc615e77a670ea HEAD
```

Then run the complete unit command from section 5. Do not regenerate embeddings,
scores, bootstrap artifacts, or validation reports merely to inspect them.

## 9. Prohibitions and next authority

There is no authorized next work package. Do not run conditional Phase B,
reopen this branch, reuse development results for architecture design, access or
decrypt protected packages, change benchmark/protocol semantics, create
negatives or pseudo-negatives, integrate external panels, or begin a new
architecture without a fresh numbered governance decision.

If a future decision authorizes a genuinely new token-aware hypothesis, it must
start prospectively from this stopped state and preserve every information-flow
boundary recorded here.
