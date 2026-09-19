# Original D-SCRIPT on the iPIN test panels

Status: **completed and verified**. Original-model C1/C2/C3 evaluation finished on 2026-09-12 at 20:56:15 UTC. Slurm job **2338739** completed with exit code 0, using four GPUs for scoring. All **3,019,012** requested pairs have finite predictions. No retraining was performed or queued; work stops after this report.

## Results and interpretation

Metric: design-weighted **positive-versus-unlabeled concordance**; higher is better. Brackets contain 95% percentile intervals from the same 2,000 component-bootstrap draws used for the historical iPIN comparison. These are not confirmed-positive-versus-confirmed-negative AUROCs.

| Test panel | Original D-SCRIPT `human_v1` | Baseline iPIN | Optimized iPIN |
| --- | ---: | ---: | ---: |
| C1 | 0.462863 [0.432145, 0.492728] | 0.843493 [0.827234, 0.859987] | 0.916037 [0.904901, 0.926427] |
| C2 | 0.439297 [0.391643, 0.485589] | 0.805299 [0.774434, 0.835511] | 0.851301 [0.827324, 0.871428] |
| C3 | 0.498680 [0.426870, 0.569144] | 0.789249 [0.708158, 0.845727] | 0.807948 [0.740480, 0.852013] |

Paired differences below are **original D-SCRIPT minus the indicated iPIN reference**, with paired 95% component-bootstrap intervals. All 2,000 draws were finite for every model and contrast.

| Test panel | Difference vs baseline iPIN | Difference vs optimized iPIN |
| --- | ---: | ---: |
| C1 | −0.380630 [−0.419600, −0.344350] | −0.453174 [−0.488194, −0.420859] |
| C2 | −0.366002 [−0.435209, −0.301852] | −0.412004 [−0.470619, −0.356604] |
| C3 | −0.290569 [−0.374744, −0.172710] | **−0.309268 [−0.390123, −0.207965]** |

The released original checkpoint transfers poorly to these iPIN panels. C3 is close to the 0.5 random-ranking reference, with an interval spanning 0.5; C1 and C2 are below 0.5, including their reported intervals. Both iPIN models outperform original D-SCRIPT in every panel, with all paired difference intervals below zero. The primary C3 gap to optimized iPIN is approximately **0.309 concordance units**.

This supports a finding about **off-the-shelf checkpoint transfer**, not a conclusion that the D-SCRIPT architecture cannot learn this dataset. No same-data D-SCRIPT retraining has yet been evaluated, and the cause of the poor transfer has not been established. Checkpoint exposure, differing training data and objectives, and the previously examined test panels limit broader causal or confirmatory claims. Intervals for the secondary comparisons are not multiplicity-adjusted. No score inversion, calibration, threshold selection, or post-result row exclusion was applied.

For manuscript wording: “The released original D-SCRIPT human predictor, evaluated with its native embeddings and unchanged learned parameters using a length-safe implementation, achieved weighted P-versus-U concordances of 0.463, 0.439 and 0.499 on C1, C2 and C3, respectively, compared with 0.916, 0.851 and 0.808 for optimized iPIN. These results characterize off-the-shelf transfer; matched-data retraining remains unevaluated.” The external-training exposure caveat below should accompany the comparison.

Full-precision outputs: [scores and intervals](results/original-v1/scores.csv), [paired differences](results/original-v1/paired_differences.csv), [machine-readable results](results/original-v1/RESULTS.json).

## Frozen comparison

The evaluated system is **original D-SCRIPT `human_v1`, with length-safe execution**, using the authors' released weights and native Bepler–Berger `lm_v1` embeddings. It is not Topsy-Turvy, a retrained model, or an ESM-input variant.

| Test panel | Observed positive pairs | Design-sampled unlabeled pairs | Required predictions |
| --- | ---: | ---: | ---: |
| C1 | 3,187 | 1,000,000 | 1,003,187 |
| C2 | 13,446 | 1,000,000 | 1,013,446 |
| C3 | 2,379 | 1,000,000 | 1,002,379 |
| Total | 19,012 | 3,000,000 | 3,019,012 |

The primary statistic is the existing design-weighted **positive-versus-unlabeled concordance**, with half credit for exact ties. It is not a confirmed-positive-versus-confirmed-negative AUROC. Historical frozen baseline and optimized iPIN predictions were reused byte-for-byte, on identical candidate tokens and weights. Their historical metric points and the existing 2,000 paired component-bootstrap draw definitions were reproduced. C3 is the primary contrast and C1/C2 are reported secondary panels.

This is a disclosed follow-up on test panels already examined for iPIN/TUnA, not a newly untouched holdout. No native checkpoint, hyperparameter, score transformation, or row subset is selected using these test outcomes.

## Length-safe implementation and qualification

The released implementation's 2,000-element integer positional array is extended to cover the maximum frozen sequence length, 7,570 residues. The learned parameters, original contact weighting, max pooling, variance calculation and generalized-sigmoid probability definition remain unchanged. The image's upstream source remains unmodified; the compatibility subclass lives entirely in this candidate folder.

Large contact maps are evaluated in row tiles with the complete three-residue halo required by the native 7×7 convolution. Only actual outer protein boundaries receive zero padding. All residue contacts are retained, and native global score pooling is applied to the complete resulting contact map. There is no cropping or pair exclusion.

For this frozen predictor, the native 6,165-dimensional residue representation is immediately passed through its original learned 100-dimensional projection in evaluation mode. Those **FP32 projected residues** are cached: 17,000 frozen reference sequences, 9,237,157 residues and 3,694,862,800 payload bytes. This is an inference optimization, not a substitute encoder or fitted representation. The frozen UniProt-derived sequence snapshot is reused; no live sequence release is substituted. Of these sequences, 252 exceed 2,000 residues.

Qualification before opening test candidate files:

- Eight synthetic short/boundary cases: the positional extension and projection cache gave bit-identical native scores; tiled scores also matched exactly.
- Sixteen fixed short TRAIN-sequence pairs: cached and native end-to-end scores matched exactly.
- Twelve additional real TRAIN-sequence fixtures: full and tiled contact maps, and their final scores, matched exactly; exchange symmetry passed.
- Sixteen fixtures sampled across the completed cache: the frozen scoring implementation matched fresh native encoder-plus-predictor inference exactly.
- A full **7,570 × 7,570** synthetic projected-residue pair scored finitely in about 0.75 seconds, with approximately **3.1 GiB** peak allocated GPU memory. This is an inference resource probe, not a training-memory claim.
- GPU bootstrap calculations matched an independent brute-force oracle to **7.8×10⁻¹⁶** on a fixture covering ties, unequal weights and same-component multiplicities.

Recorded tolerance for tiled scores is 10⁻⁵, although all reported qualification score/contact-map differences were zero. Fidelity beyond the original software's 2,000-residue limit means extending its same formula with unchanged learned weights; the unmodified software has no valid long-sequence result to compare against.

The original checkpoint SHA-256 is `9fc07ac14bb218a8b65288a9114b0c934e8f9c426a53274b0119ea2336b2a32a`. The SIF SHA-256 is `bfcee514eeb908a05bde701f230066baca9fb45fab2a811732f8e16a14a3912c`. The scorer freeze is `4ceaf28210f74b4f8519d2e8b9453376ce08edf27dcf79ef5ef12fbb8fc0ee86` and was created before opening this run's test candidate session.

Post-run verification also passed:

- Every frozen code/cache/input/prediction artifact and the SIF passed its checksum verification. All 3,019,012 rows were retained, with zero excluded or nonfinite predictions.
- The actual panels contained 20,388 / 22,928 / 24,955 pairs with an endpoint exceeding 2,000 residues in C1/C2/C3. All were scored at full length. Contact-map tiling was needed for 22,445 / 32,373 / 46,058 pairs, respectively; see the [input census](provenance/original-evaluation-v1/INPUT_CENSUS.json).
- Per-shard exchange-symmetry checks passed; maximum absolute difference was 8.94×10⁻⁸.
- A fresh, unmodified native `human_v1` predictor and `lm_v1` encoder reproduced **24 saved test-row predictions exactly**. These checks spanned all panels and GPU shards, using fixed row positions and supported sequence lengths only, without labels. This is a disclosed post-result integrity check, not a pre-result qualification or model-selection step; see [native spot check](provenance/original-evaluation-v1/POSTRUN_NATIVE_SPOTCHECK.json).
- Prediction freeze preceded evaluation reservation and truth access. Temporary decrypted truth was removed. The historical iPIN references and bootstrap draw definitions reproduced successfully.
- The scope audit found all **1,842 Git-tracked and non-ignored untracked files outside `benchmark/` unchanged**. No training or follow-on benchmark job remains queued. See the [completion audit](provenance/original-evaluation-v1/COMPLETION_AUDIT.json) and [scope audit](provenance/original-evaluation-v1/scope-audit.json).

## Original-model exposure caveat

The [official data documentation](https://d-script.readthedocs.io/en/main/data.html) links public human-training interactions and sequences. The audited files are pinned to upstream release commit `0b3f7363b7d62fb99f5c8bfc6780833f088b8d84` and contain 421,792 labeled pairs involving 15,816 endpoints.

| iPIN sequence partition | Endpoints | Exact sequence matches to documented public training endpoints |
| --- | ---: | ---: |
| TRAIN | 11,900 | 8,471 |
| Development | 2,550 | 1,921 |
| Test | 2,550 | **1,738 (68.2%)** |

Therefore C3's unseen-endpoint designation relative to iPIN TRAIN must not be interpreted as a demonstrated unseen-endpoint test for this externally pretrained original predictor. This audit concerns the documentation-linked training files; it does not independently authenticate the complete checkpoint training history and is not a complete pair-overlap/homology audit. The native encoder also had external structure-informed pretraining. All requested test rows remain in the comparison.

## Execution and files

- [Length-safe adapter](scripts/native_adapter.py), [original scoring implementation](scripts/frozen_scorer.py).
- [Adapter qualification](runs/original-v1/ADAPTER_QUALIFICATION.json), [contact-map qualification](runs/original-v1/TILING_QUALIFICATION.json).
- [Frozen scorer/cache/code manifest](runs/original-v1/scorer_bundle/SCORER_FREEZE.json).
- [Frozen-scorer qualification](runs/original-v1/scorer_bundle/provenance/FROZEN_SCORER_QUALIFICATION.json), [metric qualification](runs/original-v1/scorer_bundle/provenance/METRIC_QUALIFICATION.json).
- [Original exposure audit](provenance/original-evaluation-v1/ORIGINAL_EXPOSURE_AUDIT.json).
- Original-only Slurm workflow: [original.sbatch](original.sbatch), [worker](score_original_worker.sh), [finalization](finish_original.sh).
- Candidate-only inputs and per-row scores remain private artifacts under `private/original-v1/`. Aggregate results are published under [results/original-v1/](results/original-v1/RESULTS.md).

Job 2338739 completed in **44m01s**, including a **42m46s** four-GPU scoring step and a **1m12s** single-GPU merge/evaluation/publication step; the bootstrap/metric calculation itself took about 29 seconds. This was a resumed run: 180,224 predictions had already been checkpointed by job 2338537, so 44m01s is not a clean from-scratch runtime. Native embedding/projection-cache construction took 341.7 seconds for all 17,000 sequences before scoring. These are inference measurements, not retraining resource estimates.

The first Slurm submission, 2338513, failed in task launch because an inherited CPU-binding mask was incompatible with its allocation. It produced no model predictions or test metrics. Submission 2338537 disabled inherited CPU binding but inherited a one-GPU step total from the interactive allocation: all four workers shared one GPU despite the job reserving four. This was diagnosed using GPU process UUIDs, then stopped after 180,224 checkpointed predictions. Submission 2338739 explicitly sets both total and per-node GPU counts and resumes those same shards. A four-task diagnostic confirmed four distinct GPU UUIDs with these settings. This follows Slurm's documented [environment-variable option precedence](https://slurm.schedmd.com/srun.html#SECTION_INPUT-ENVIRONMENT-VARIABLES). The frozen scientific scorer, inputs and metric policy were not changed between submissions, and no test metrics were accessed during launch correction.

Scoring workers could not see test truth, decryption keys, reference scores, or training pairs. Predictions were merged and checked for complete unique finite row coverage before the separate evaluation phase received truth. Historical protocol files, ledgers, datasets, images and model artifacts remained read-only. No retraining or later benchmark job was queued after this evaluation. **Stopped after original-model evaluation and reporting, as requested.**
