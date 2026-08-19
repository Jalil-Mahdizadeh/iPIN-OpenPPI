# M1 Stage 1 public-training execution final report v1

**Date:** 2026-08-19

**Scope:** complete execution and independent validation of the frozen,
public-training-only Stage 1 model matrix

**Controlling authority:** `DEC-0028`, `DEC-0029`, and `DEC-0030`; binding
configuration SHA-256
`3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5`

## Result

Stage 1 public training is complete and passes its frozen production and
independent-validation gates. All 30 preregistered runs completed, exactly five
complete passes were executed per run, and the matrix consumed exactly
300,000,000 positive-versus-unlabeled comparisons. No run failed or resumed.
All 150 complete-pass checkpoints, 30 selected checkpoints, and 10 arithmetic
three-seed ensemble definitions are frozen in the complete training-artifact
registry.

The frozen prerequisites for a later development release are satisfied.
Development nevertheless remains encrypted and unreleased: this report neither
opens nor authorizes access to it. A separate effective numbered governance
decision is still required before any development package may be released or
decrypted. Protected candidates and truth remain encrypted and evaluator-only.

## Runtime, model custody, and embeddings

The accepted 10,656,620,544-byte ARM64 model SIF has SHA-256
`c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`.
All execution was offline on the single visible NVIDIA GH200 120 GB GPU on
Arrhenius node `n180`. The two exact ESM-2 revisions and their co-revision file
sets remained hash-pinned, link-free, Safetensors-only, and remote-code-disabled.

The label-blind embedding stage produced one FP32 pooled and one training-only
standardized vector for every one of the 17,000 exact endpoints for each
encoder: shape `17000 x 640` for ESM-2 150M and `17000 x 1280` for ESM-2 650M.
It used exact untruncated overlap-averaged windows. Only the 11,900 training
endpoints contributed to normalization statistics. The frozen bottom-hash
one-percent repeat extractions (170 endpoints per encoder), checked again by
the independent validator, had maximum absolute difference `0.0`, within the
`1e-6` gate. No residue-level embedding was retained.

Production embedding audit passed 17 checks and independent pretraining
validation passed 21 checks, both with zero warnings and zero failures.

## Frozen implementations

All mandatory deterministic controls were implemented and validated: salted
full-SHA-256, training-positive degree sum, preferential attachment,
frozen-component degree-mass product, training-positive common neighbors,
sequence log-length sum, negative absolute log-length difference, exact
contiguous 3-mer cosine, and exact orientation-invariant training-interolog
3-mer score. Graph features use only the 16,799 public training positives;
held-out endpoint training degree is defined as zero.

The four frozen trainable families were implemented with exact commutative pair
features and passed swap-symmetry checks at maximum absolute difference `0.0`:

| Family | Trainable parameters | Matrix runs |
|---|---:|---:|
| lightweight ESM-2 150M affine | 1,922 | 6 |
| ESM-2 650M affine ablation | 3,842 | 6 |
| ESM-2 650M nonlinear no-gate ablation | 426,625 | 9 |
| ESM-2 650M partner-gated primary | 492,417 | 9 |

The implementation audit passed 15 checks, the preparation audit passed 10,
and the separately implemented preparation validator passed 10, all without
warning or failure. The validator independently reconstructed all 30 configs,
all 30 P/U orders, the public P/U arrays, and the single-GPU offline launch
contract before training began.

## Objective and execution census

Each of the five complete passes in every run used all 2,000,000 frozen public
U rows exactly once and the complete 16,799-row public P census through the
frozen cyclic pairing rule. Across a pass, 919 P observations appeared 120
times and 15,880 appeared 119 times. Exact rational design weights were neither
clipped nor re-estimated; their FP64 sum was `10902230.000000007` and mean was
`5.451115000000004`.

The sole optimization target was the design-weighted pairwise logistic ranking
objective. U remained unlabeled throughout; no negative or pseudo-negative was
created. Deterministic algorithms, disabled TF32, fixed seeds, fixed complete-
pass stopping, and training-monitor checkpoint selection were enforced. The
selected checkpoint was pass 5 in every run under the frozen minimum-monitor,
earliest-exact-tie rule.

The exact execution census is:

| Quantity | Frozen result |
|---|---:|
| Runs complete / failed | 30 / 0 |
| Infrastructure resumes | 0 |
| Complete passes | 150 |
| Optimizer steps | 73,350 |
| P-versus-U comparisons | 300,000,000 |
| Selected checkpoints | 30 |
| Three-seed ensemble definitions | 10 |
| Registry artifacts | 647 |
| Registry unique bytes | 15,124,997,716 |
| Final governed storage bytes | 14,959,953,220 |
| Conservative total GPU-hours | 0.45626144182586964 |

These totals remain below the frozen ceilings of 30 runs, 300,000,000
comparisons, 100 GPU-hours, and 100 GiB.

## Training monitors

The table below reports only the frozen complete-pass training objective at
each selected checkpoint, ordered by seeds `20260803`, `20260817`, and
`20260831`. It is a training-process diagnostic, not a held-out metric. It must
not be used for architecture selection, a generalization claim, or a biological
performance claim.

| Candidate | Seed monitors | Mean | Range |
|---|---|---:|---:|
| 650M affine, lr `1e-3` | 0.263382687184; 0.262903587687; 0.263398125923 | 0.263228133598 | 0.000494538236 |
| 650M affine, lr `3e-4` | 0.281940855374; 0.281017356298; 0.282030361245 | 0.281662857639 | 0.001013004947 |
| 650M no-gate, conservative | 0.016655960869; 0.016138053917; 0.016231806415 | 0.016341940400 | 0.000517906952 |
| 650M no-gate, default | 0.005076517586; 0.005036625807; 0.004909542493 | 0.005007561962 | 0.000166975093 |
| 650M no-gate, no dropout | 0.003559638498; 0.003508815858; 0.003425768553 | 0.003498074303 | 0.000133869945 |
| 650M partner-gated, conservative | 0.013437991462; 0.012787999886; 0.012559869321 | 0.012928620223 | 0.000878122141 |
| 650M partner-gated, default | 0.003823935698; 0.003851875258; 0.003742777196 | 0.003806196051 | 0.000109098062 |
| 650M partner-gated, no dropout | 0.003094680072; 0.003127020978; 0.002974561345 | 0.003065420798 | 0.000152459634 |
| 150M affine, lr `1e-3` | 0.328077151124; 0.327652533900; 0.328060756650 | 0.327930147225 | 0.000424617224 |
| 150M affine, lr `3e-4` | 0.344852546172; 0.344830585734; 0.345066812859 | 0.344916648255 | 0.000236227125 |

No C1, C2, or C3 concordance, bootstrap interval, degree/hub stratum, C1
novel-U sensitivity, supported-source direction, or development model-selection
quantity exists at this boundary because development was not accessed.

## Independent final validation

The final validator was implemented after the complete production registry was
committed. It does not import the production Stage 1 modules. It independently
rehash-verified all 647 artifacts, reconstructed all orders and weights,
inspected all 150 checkpoints, and clean-room scored every selected checkpoint
in both partner orientations.

It passed 14 of 14 checks with zero warnings and zero failures. In particular,
it confirmed:

- exact public visibility: 16,799 P and 2,000,000 U observations only;
- exact weight algebra, all 30 orders, and exact positive-census coverage;
- 30 complete runs, 73,350 steps, and 300,000,000 comparisons;
- finite state plus RNG, order, cursor, and weight binding in all 150
  checkpoints;
- training-only checkpoint selection and exactly 10 three-seed ensembles;
- one-GPU offline logs, zero resumes, and selected-checkpoint swap maximum
  absolute difference `0.0`; and
- no development, protected, private-key, temporary, or sensitive-path
  leakage among the registered artifacts.

## Frozen evidence

| Artifact | SHA-256 |
|---|---|
| Stage 1 implementation audit | `082d166573b3e521b8a579c1f4b5fd8b4ca798678f75b334fcf13cde68df5145` |
| Embedding artifact registry | `429e9b3c40827ea5a7513b3599a95d201cdc5eea1e0f99f8c384050cbfcbaed1` |
| Embedding production audit | `992faf2029a2e2c0288dfc3b4216a7de75e0b04eea4e54f80560c0313055a79a` |
| Independent pretraining validation | `0cd6b9985eb33ddec1948cb22a14bda08c16990d6d2c4d46924952a18e1fd8de` |
| Training-preparation registry | `8d15f244f390d7069a4ecd7453622a425a465dcf1ec9d32087e4d557fbb84f4e` |
| Training-preparation audit | `849f09fdf3f32f6572ffdc097de21fa8a56da29a2494b949386df7871f37631f` |
| Independent preparation validation | `a08a62513ef60feff5f3737dbab308c553f24a3f98b562edc8514ba5bd9d70f8` |
| Complete training-artifact registry | `11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318` |
| Training production audit | `fb15f7462f61597928be68e3f2963505a10318c2696f6575d0354b73a0cb7040` |
| Independent final training validation | `b7178f659bd03b0b779d0de015cdb8b33af41e4ee7729fb2cb8d461a0e727a88` |

The production registry was frozen at commit
`a46639245fc34d9b53063ec46370a6139a2bd021`. The independent validator was
committed at `5acf3a28062f43de5986fb5fcbf10cd6f34cbdfd`; its passing evidence was
frozen at `1003d3e4a0270047d904f06e9acb025bce78cd94`.

## Scientific disposition

This stage establishes executable integrity and freezes the scorer candidates;
it does not select a model or establish predictive utility. The frozen
C3-first development procedure is the only next mechanism that may compare
shortcut controls, sequence/interolog controls, PLM-linear candidates,
no-gate heads, and partner-gated heads.

The complexity and model-level kill criteria therefore remain pending. A
partner-gated or other complex head is not justified unless the already-frozen
development criteria are met. If graph/degree/length controls explain the
result, the shortcut stop applies; if interolog or frozen-PLM-linear candidates
explain it, complex architecture is rejected. If no learned candidate clears
the qualifying C3 gate, execution stops before protected test. No new training,
adaptive run, checkpoint change, architecture change, or post-release
retraining is permitted.
