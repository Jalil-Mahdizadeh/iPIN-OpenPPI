# RAPPPID matched-data retraining

Slurm job **2578434** on `n178` started **17 September 2026 at 09:45:28 CEST** and **failed at 16:44:29 CEST during epoch 8** after nonfinite gradients in seed `20260831`. It has not been repaired or resumed. The user authorized **20 epochs**, retained checkpoints and **full C3-development evaluation at epochs 4, 8, 12, 16 and 20**; only the epoch-4 stage completed before the failure. The user subsequently requested the separate latest-recovery development evaluation below, chose not to restart training, and authorized testing those exact recovery states.

## Latest recovery checkpoints: completed test evaluation

Completed **17 September 2026 at 20:15 CEST** on all **3,019,012 C1/C2/C3 test pairs**, with no training restart or repair. Three-seed mean-logit ensemble concordance: **0.775316 / 0.729804 / 0.700049**. Original RAPPPID: **0.597417 / 0.600243 / 0.607067**; baseline iPIN: **0.843493 / 0.805299 / 0.789249**; optimized iPIN: **0.916037 / 0.851301 / 0.807948**.

The ensemble remains below both iPIN models. Its C3 improvement over original RAPPPID is **+0.092981**, but the paired 95% interval **[−0.030165, 0.187027]** includes zero. The paired C3 difference versus optimized iPIN is **−0.107899 [−0.163262, −0.062356]**. All three individual checkpoints and all paired comparisons are reported without post-test seed selection.

[Full test report](RECOVERY_TEST_REPORT.md), [scores and intervals CSV](results/retrained-v1/recovery-test-v1/scores.csv), and [new selection authorization](runs/recovery-test-v1/SELECTION.json). The old training-only protocol remains unchanged. These are unequal-position mid-epoch-8 snapshots selected after an additional development look, not completed epoch-8/20 models. **No further RAPPPID training or test stages are queued.**

## Latest recovery checkpoints: additional C3-development evaluation

Completed on 17 September 2026 using the existing single-GH200 allocation `2598385` on `n430`. All **1,002,265 C3-development pairs** were scored with the unchanged frozen singleton scorer. No training updates, numerical repair, seed/epoch selection or test evaluation occurred.

| Model | Saved epoch-8 progress | Latest C3-dev | Epoch 4 | Change |
|---|---:|---:|---:|---:|
| Seed 20260803 | 75.142% | 0.679389 | 0.622185 | +0.057204 |
| Seed 20260817 | 78.896% | 0.668486 | 0.670013 | −0.001527 |
| Seed 20260831 | 77.824% | 0.656541 | 0.672436 | −0.015895 |
| Three-seed mean-logit ensemble | Unequal saved positions | **0.699429** | **0.692744** | **+0.006684** |

Each seed completed seven full epochs plus the stated fraction of epoch 8. The ensemble improved by 0.006684 on this panel, but two members declined; this is a descriptive point-estimate comparison, not a significance claim. This extra, user-requested development look must not be labeled a completed epoch-8 or prescheduled checkpoint result.

[Detailed report](results/retrained-v1/recovery-c3-dev-2578434-v2/RESULTS.md), [CSV](results/retrained-v1/recovery-c3-dev-2578434-v2/scores.csv), and [provenance/results JSON](results/retrained-v1/recovery-c3-dev-2578434-v2/RESULTS.json). Exact checkpoint copies, hashes, wrapper code and complete per-seed/ensemble prediction arrays are retained alongside them. All source recovery-checkpoint hashes remained unchanged; native-head/reversal checks passed within `1.44e-6`, and two independent metric checks agreed within `1.49e-11`. Scoring and verification took **18.17 seconds** excluding preparation/container startup. The report documents an initial metric-verification tolerance correction made before latest-checkpoint scoring; the historical scoring function and frozen training code were not changed.

## Run and timing

The training allocation was one node with **three GH200 120GB GPUs**, one independent seed per GPU, and a **48-hour wall-time limit**. Seeds are `20260803`, `20260817` and `20260831`, matching the earlier benchmark runs. All three runs must finish a four-epoch stage before the ensemble report is produced and the next stage starts. The launch verified three distinct GPU UUIDs and different fresh model-state hashes. Formal workers entered epoch 1 at about **09:45:55 CEST**; the on-node image/code/data integrity gate passed. The timing estimates below are the original pre-launch projections, not a claim that the interrupted run remains active.

**Startup health verified at 09:48:17 CEST:** all three workers had reported 87,040 comparisons in epoch 1; running mean losses were **0.66390 / 0.66353 / 0.66512**, with finite nonzero gradients. Production throughput was **626.8 / 645.5 / 638.0 comparisons/s**, consistent with the pilot. Independently loaded atomic recovery checkpoints contained **81,920 completed comparisons (2,048 updates) per seed**, changed learned weights, finite model/optimizer tensors and correct optimizer counters. Strict model/optimizer/auxiliary-state loading passed for all three; the live workers were not paused or modified. [Startup evidence](provenance/retrained-v1/STARTUP_HEALTH.json). These are early training diagnostics, not development performance results.

The pre-submission GH200 pilot measured **635.36 P-versus-U comparisons/s**, including fresh stochastic tokenization, the actual native forward/backward pass, Ranger21 updates and finite-value checks. This projects **52.5 minutes/epoch and 17.5 hours for 20 epochs per seed**, excluding checkpoint I/O, development scoring, startup, contention and queue time. With the seeds running concurrently, budget approximately **20–28 elapsed hours after allocation**, with the 48-hour limit providing additional margin. The first epoch-4 development report is expected roughly **4–6 hours after startup**. These are estimates, not scheduler guarantees; early production throughput will supersede the short pilot.

This is longer than the earlier rough estimate because it measures the complete stochastic-tokenization/optimizer pipeline, not just neural-network compute. It is not three times the per-seed elapsed time when three GPUs are used concurrently; total GPU-hours are approximately three times wall time.

Submission and progress artifacts:

- [Slurm submission record](runs/retrained-v1/JOBS.json), created only when submitted.
- [Training protocol freeze](runs/retrained-v1/TRAINING_FREEZE.json) and [execution-source freeze](runs/retrained-v1/EXECUTION_CODE_FREEZE.json).
- Per-seed progress: `runs/retrained-v1/training/seed_<seed>/PROGRESS.json` and `events.jsonl`.
- Slurm logs: `logs/retrained-<job>.stdout.log`, `.stderr.log`, `retrained-train-<job>-epoch<stage>-rank-<rank>.log` and `retrained-development-<job>-epoch<stage>.log`.

## Matched-data experiment

This is **PU-RAPPPID-mult**, trained from fresh weights, not fine-tuned from the released PPI checkpoint. All **188,161** parameters of the native encoder and multiplicative interaction head are trainable. The dedicated, previously qualified image is reused without modification:

`benchmark/containers/images/rapppid-native-arm64-v1.sif`

SHA-256: `e853a89768c5351927f90fd0ccfb2ad899a15a6fc239a9014726af0c34442d48`.

Native RAPPPID source is pinned to commit `c3a28be56fb3bd96ccf8cc44ea9145cfcadeaf6c`; upstream source is not edited. The native `LSTMAWD`, AWD/dropout implementation, Mish and multiplicative head are reused. This is the released-model architecture, not the paper's concatenation-head checkpoint. The qualified modern ARM64/GH200 runtime remains a runtime port, not an identical historical Torch environment.

| Item | Fixed retraining definition |
|---|---|
| TRAIN panel | 16,799 observed positives and 2,000,000 unlabeled pairs |
| Epoch | Every TRAIN U once; balanced cycling of P, with independent seeded permutations |
| Objective | `mean((U_weight / mean(TRAIN_U_weight)) * softplus(logit_U - logit_P))` |
| Update size | 40 P-versus-U comparisons, i.e. 80 pair presentations |
| Budget | 50,000 updates/epoch × 20 epochs × 3 seeds |
| Optimizer | Native Ranger21 0.1.0; LR 0.01; weight decay 0.0001; native AGC, normalization, stable decay and lookahead |
| Schedule | Native 2,000-update warmup; linear warmdown from about 72% of the 1,000,000 updates per seed |
| Architecture | 250 token codes; 64-dimensional embedding; 2 recurrent layers; native multiplicative head |
| Dropout | Recurrent 0.3; embedding 0.3; head 0.2 |
| Precision | FP32 model/logits/softplus; FP64 weighted-loss accumulation and ensemble logits; no AMP/TF32 |
| Retention | Full model and recovery state at epochs 4, 8, 12, 16, 20 for every seed: 15 retained checkpoints |

The same frozen TRAIN/C3-development arrays and sequence identities used by D-SCRIPT are copied and hash-verified. The [data manifest](runs/retrained-v1/data/DATA_MANIFEST.json) records their provenance. No refreshed sequence records, new splits, extra negative labels or test outcomes are introduced.

A new **250-piece unigram SentencePiece tokenizer** is fitted only on the full sequences of the **4,675 TRAIN endpoints**, once and shared across seeds. The **2,550 C3-development endpoints are not used to fit it**. Tokenizer fitting is single-threaded, uses every TRAIN endpoint and fixes seed `20260803`. [Tokenizer provenance](runs/retrained-v1/data/TOKENIZER.json), model SHA-256 `1ac71901b484b3ad5dbffbd47f6b5265d712ffc54e93514469d1ebb5b7675560`. The fixed full public sequence metadata also contains other partitions, but neither test pairs nor test truth is opened by this retraining workflow.

Training retains native stochastic tokenization (`alpha=0.1`, `nbest_size=-1`), while development tokenization is deterministic. Each endpoint is prefix-truncated to **1,500 residues**, as in the native released recipe. No pairs are dropped because of length.

### Important methodological disclosures

The common philosophy is TRAIN-only fitting, weighted positive-versus-unlabeled ranking, matched seeded exposure, full C3-development checkpoint comparison and later user-selected test evaluation. It does **not** imply identical optimizers or model internals across architectures.

The weighted PU objective replaces the native supervised binary-negative loss: U is **unlabeled**, not confirmed noninteracting. The requested fixed 20-epoch budget and raw retained checkpoints replace the paper's longer training/SWA procedure. **No additional stochastic weight averaging is applied.** Thus this is an explicitly adapted matched-data recipe, not an exact reproduction of all paper training settings.

Native RAPPPID has batch-dependent padding and head normalization. Training uses the actual native separately padded endpoint batches and the unmodified head's global batch moments. Development uses the already declared **singleton endpoint/singleton native-head policy** from the original RAPPPID evaluation. These training and evaluation batching policies are not numerically identical; this difference is intentional, frozen and disclosed. Development cache/head computations are checked against actual native singleton calls at every retained checkpoint. No policy is changed in response to development scores.

## Development evaluation and later decision

Every retained epoch is evaluated on **all 1,002,265 C3-development pairs: 2,265 P and 1,000,000 U**. The metric is the historical design-weighted P-versus-U concordance with exact-score half ties. Scores are native pre-sigmoid logits, not calibrated interaction probabilities.

For each epoch the report contains each seed's concordance and the concordance of the **FP64 mean of all three seeds' logits**. No seed or checkpoint is silently discarded. Each seed checkpoint remains separately available.

Expected outputs, appearing after epoch 4:

- `runs/retrained-v1/training/seed_<seed>/epoch_04.pt` through `epoch_20.pt`: retained full checkpoints.
- The same directories contain `epoch_<NN>.json` and `epoch_<NN>_C3_development.npy` with complete per-seed predictions and hashes.
- [Development comparison table](results/retrained-v1/development/DEVELOPMENT_RESULTS.md).
- [Development scores CSV](results/retrained-v1/development/development_scores.csv) and [machine-readable results](results/retrained-v1/development/DEVELOPMENT_RESULTS.json).
- `results/retrained-v1/development/epoch_<NN>_ensemble_C3_development.npy`: complete ensemble predictions.

The original training-only plan was to stop after epoch 20 and let the user choose among five development stages for separately authorized test evaluation. That plan was interrupted by the epoch-8 failure. There is no test-candidate/truth mount or test job in that original launch chain. The subsequently authorized recovery-state test run is separate, as reported above; historical iPIN and original RAPPPID prediction files were reused without modifying or rerunning those models.

## Qualification and recovery

[GPU qualification](runs/retrained-v1/QUALIFICATION.json) passed before formal training:

- Native model updates and gradients are finite; all parameter tensors participate.
- Independent analytic PU-loss and gradient errors are approximately `1.1e-8`.
- Every U is used once per epoch; positive cycling is balanced.
- A TRAIN-only learning fixture's mean loss decreased from **0.70565 to 0.47022**. These are software-learning checks, not validation results or retained candidate weights.
- Save/restart reproduces the next **four** native updates, model tensors, optimizer state and metrics **bit-for-bit**, including a lookahead merge. Separate altered-state round trips exercise restoration of warmup/warmdown flags; this does not claim a full million-update schedule was run during qualification.
- TRAIN-fixture development-style logits agree with actual native singleton calls within `7.16e-7` (frozen tolerance `1e-4`), including batch sizes 1, 8 and 8,192 and endpoint reversal.
- The maximum-token 80-pair forward/backward check used about **2.61 GiB** GPU memory. The representative complete-pipeline measurement peaked at about **2.01 GiB**.
- Independent weighted-metric oracle error was `7.77e-16`.

A [separate full-size TRAIN-derived I/O fixture](runs/retrained-v1/orchestration-qualification/PIPELINE_QUALIFICATION.json) checks checkpoint retention, duplicate calls, model/RNG preservation, three-seed reporting and report extension from epoch 4 to 8. Its synthetic repeated pairs and scores are **not real development results**. They are stored separately and never used as formal weights, data or performance claims.

Ranger21 has important counters outside the standard PyTorch optimizer state dictionary. Recovery therefore stores its auxiliary counters as well as model tensors, optimizer moments/lookahead tensors, CPU/CUDA RNG, epoch, comparison position and accumulated loss. Atomic recovery is written every **40,960 comparisons**, at epoch boundaries, and on handled stop signals. Retained four-epoch checkpoints are not pruned. Mid-epoch restart reconstructs the same permutations and stochastic tokenization stream; interrupted work before the last recovery point may be replayed.

SentencePiece's existing thread-local random generator is not reset by simply setting its global seed. The initial qualification caught this. Each production batch therefore tokenizes in a fresh, short-lived thread with a deterministic seed derived from `(seed, epoch, comparison_start)`, using the native sampler. CUDA remains on the main thread. The corrected implementation passed exact restart tests; the initial failed qualification log is retained for audit.

## Scope

Implementation, copied inputs, tokenizer, checkpoints, provenance, logs, reports and the scoped AST-only Graphify update are confined to `benchmark/rapppid/`. No new SIF is necessary because the dedicated RAPPPID SIF passed native training and recovery qualification. Existing D-SCRIPT jobs, other benchmark runs, parent images and repository training code are not modified.

The [scope audit](provenance/retrained-v1/scope-audit.json) passed for **1,912** Git-tracked/nonignored files outside `benchmark/`: zero additions, removals or content changes relative to the pre-implementation snapshot. It is not a claim to hash every ignored artifact. One preliminary Graphify query refreshed the root graph's query timestamp before that snapshot; subsequent graph inspection avoided this side effect, and the actual code-map update stayed inside this candidate directory.
