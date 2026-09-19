# TUnA benchmark — startup and execution report

Snapshot: 12 September 2026, approximately 10:45 UTC / 12:45 Stockholm time.

TUnA implementation and numerical qualification are complete. Three independent PU-retraining seeds are running on Arrhenius; the released-versus-retrained C1/C2/C3 comparison is queued to run automatically after successful training. **No new TUnA test-performance result is available at this snapshot.** Training loss and pilot measurements below are not test metrics.

## Required comparison and current jobs

| Predictor | C1 test | C2 test | C3 test |
|---|---|---|---|
| Authors' original Bernett TUnA checkpoint | Queued | Queued | Queued |
| PU-TUnA retrained on iPIN TRAIN, three-seed ensemble | Training | Training | Training |
| Frozen iPIN baseline ensemble | Reuse existing predictions | Reuse existing predictions | Reuse existing predictions |
| Frozen optimized iPIN ensemble | Reuse existing predictions | Reuse existing predictions | Reuse existing predictions |

Training job **2325231** runs on **n418**, using three GPUs of the node's four GH200 GPUs, one per seed. Seeds are `20260803`, `20260817`, and `20260831`. At 10:41 UTC each had processed at least 448,064 of 2,000,000 comparisons in epoch 1. The fixed schedule is eight epochs per seed.

Final-comparison job **2326461** is pending with `afterok:2325231`; it requests one GPU and runs only if all three seeds finish successfully. The final pipeline selects the ensemble using C3 development, freezes its complete scorer, scores all requested test candidates, imports both unchanged iPIN references, freezes all predictions, and then opens test truth in a separate evaluator. A failed qualification, identity check, job, or truth-access reservation stops the pipeline; it does not silently retune or repeat test evaluation.

Monitor with `squeue -j 2325231,2326461`. Worker logs are `logs/train-<seed>-2325231.log`; final-stage logs are `logs/final-*.log` and `logs/comparison-2326461.*.log`. These are generated, ignored files inside this candidate directory.

After successful completion, the aggregate results will be:

- `results/scores.csv`: original TUnA, retrained ensemble, all three retrained members, and both frozen iPIN references, each on C1/C2/C3, including confidence intervals and coverage.
- `results/paired_differences.csv`: both candidate versions minus each iPIN reference, and retrained minus original, on every cell, with paired confidence intervals.
- `results/RESULTS.md` and `results/RESULTS.json`: manuscript-facing summary and full aggregate record.

Those result files are deliberately not populated with placeholder or invented performance. Protected per-pair scores stay under ignored `private/`; no protected pair identities enter the aggregate CSVs.

## Original versus retrained: precise definitions

**Original:** the authors' released Bernett human-interaction checkpoint, selected before any TUnA test score was inspected. Its relevance to the human, held-out-protein setting motivated the choice; this is not selection among authors' checkpoints by test performance. The original remains a single checkpoint with its published mean-field sigmoid score. No interaction training, GP refitting, or calibration on iPIN is applied to it. Native `eval()` recomputes its covariance from the released precision, as in upstream code.

**Retrained:** the same pinned TUnA architecture, with freshly initialized PPI-model parameters and frozen general ESM-2 150M weights, fitted on iPIN TRAIN. This is explicitly **PU-TUnA**, a common-PU-objective adaptation, not a claim to reproduce the authors' BCE training recipe. “Original checkpoint” and “retrained with the original objective” are different experiments. A native-BCE retraining sensitivity remains a later optional extension; it is not substituted for the required original-checkpoint row.

The original [TUnA repository](https://github.com/Wang-lab-UCSD/TUnA) and its Bernett implementation are pinned to commit `b5bda8fee261a4f27821738db995cf5883dcd133`. The companion [GP library](https://github.com/Wang-lab-UCSD/uncertaintyAwareDeepLearn) is pinned to `18565eb86026800817857e37243ae81f15f089d7`. The original [checkpoint](https://huggingface.co/datasets/yk0/TUnA_models/blob/eaec69cafc574d984119079220e75b11ffcb7c09/bernett/TUnA/model) has SHA-256 `bf2dd42af75d98324798b76837ca738e4ed230b096ee538ccdbaa001dcc88500`. See the [paper](https://doi.org/10.1093/bib/bbae359) for the method. Upstream repositories and original weights remain unmodified. Local use does not establish redistribution permission for every weight/data artifact.

## Data and training philosophy

The existing frozen iPIN inputs are reused, not regenerated from current UniProt. There are 17,000 sequence identities: 11,900 TRAIN, 2,550 development, and 2,550 test endpoints. Training uses all **16,799 P pairs and 2,000,000 sampled U pairs**, with the existing design weights. Development retains the existing C1/C2/C3 split; only C3 development selects the two prespecified checkpoint options.

TUnA requires `L × 640` residue representations. The existing pooled iPIN feature vectors are therefore insufficient. A separate full-context, last-layer ESM-2 150M residue cache was generated from the existing frozen safetensors checkpoint, retaining all 17,000 sequences and **9,237,157 residues**, including the maximum sequence length **7,570**. No endpoint or test candidate is excluded for length. The cache is about 23.65 GB and took approximately **291 seconds** on the current GPU, including qualification and final hashing. There was no live UniProt query or encoder finetuning.

The exact existing ESM weights were mapped into the authors' `fair-esm` implementation, with conversion checked against the existing Transformers implementation. Encoder SHA-256: `c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566`. Residue-cache SHA-256: `f05ecf25cc8a34f9b0b8e1bc934f98c5988623e71a0b0de6accd9433bb0f80c7`.

The prospective training freeze is `runs/TRAINING_FREEZE.json`, SHA-256 `86aa6d0cd3e1df135b4ea097686ed281a57186828f68da4936bbeba39589d8b5`. Its main choices are:

- One hyperparameter recipe, three fixed seeds, eight full-U epochs, and checkpoint options at epochs 4 and 8. Selection maximizes C3-development concordance of the three-member ensemble; exact ties choose the earlier epoch. There is no per-seed “must beat iPIN” gate.
- Each epoch uses all U pairs once and balanced cycling through P pairs, with the same independent PCG64DXSM sampling streams used for iPIN. Loss is globally design-weight-normalized `softplus(score_U − score_P)`. U is not interpreted as a verified negative.
- Native Adam plus Lookahead (`alpha=0.8`, `k=5`), initial learning rate `1e-4`, factor `0.93` every two epochs, weight decay `1e-5` except biases, dropout `0.2`, 64-dimensional head, eight attention heads, and 4,096 random Fourier features.
- Comparison batch 64, corresponding to 64 positive and 64 unlabeled pair scores per step. Independent contiguous training crops up to 512 residues follow the native length policy; evaluation uses full lengths. This batch/loss adaptation is disclosed rather than described as the authors' exact training recipe.
- FP32 model/attention/embeddings, no AMP or TF32; FP64 weighted-loss and covariance accumulation. Seeds, CUBLAS workspace configuration and relevant cuDNN flags are fixed. Bitwise cross-hardware reproducibility is not claimed; accelerated attention changes stochastic dropout implementation.
- The retrained GP covariance uses the frozen-feature, TRAIN-only Hessian of the weighted pairwise logistic objective plus the native ridge. A fixed training comparison stream, FP64 accumulation and Cholesky inversion are used. This is a declared pairwise-Laplace adaptation, not the authors' binary-negative likelihood covariance and not a calibrated binding probability. Each member's score retains the mean-field form; the ensemble averages **adjusted logits in FP64**.

## Fidelity and qualification

| Check | Observed result |
|---|---:|
| Existing Transformers versus mapped native fair-esm residue features | Maximum absolute error `8.58e-6` |
| Accelerated versus native fair-esm features | Maximum absolute error `1.29e-5` |
| Native batch-one TUnA versus cached predictor, synthetic fixtures | Maximum probability error `5.96e-8` |
| Same comparison on real TRAIN fixtures up to 5,795 residues | Maximum probability error `5.96e-8` |
| Native pair-order symmetry on qualification fixtures | Exact equality |
| Small TRAIN-fixture learning test, 160 steps | Mean loss fell from `0.64395` to `0.32919` |
| Pairwise GP-Hessian formula versus independent autograd Hessian | Maximum error `1.18e-16` |
| GPU bootstrap versus independent weighted brute-force calculation | Maximum error `7.77e-16` |
| Minimal final scorer, ensemble arithmetic, malformed-identity rejection | Passed |
| GPU guard and native-predictor tests under that guard | Passed |

Qualification records are retained in `runs/` and copied to `provenance/` for review. No protected test pair or truth was needed for these checks.

Two implementation details matter for faithful reproduction. In this pinned release, inter-encoder attention uses block-diagonal masks, and pooling selects the first block. In **evaluation mode**, its AB/BA maximum is therefore algebraically factorizable into cached per-protein representations. The measured checks justify using that inference acceleration; they do not establish that every TUnA version has this property or that it is the architecture intended by every description in the paper. The original masking is not “corrected.” Training retains the full original two-order computation, including dropout and spectral-normalization behavior.

Also, the authors' test loader uses batch size one. Its mean-field helper broadcasts incorrectly for larger direct batches; the released **batch-one predictor** is the qualification oracle. The minimal scorer computes the equivalent per-pair scalar, not the unintended broadcast matrix. Original probabilities are retained; they are not inverted into invented logits.

## Important external-exposure finding

An exact-sequence endpoint audit of the public inputs named by the pinned Bernett configuration found:

| Documented original input | Overlap with iPIN TRAIN endpoints | Development endpoints | Test endpoints |
|---|---:|---:|---:|
| Training: 3,884 endpoints | 2,570 / 11,900 | 384 / 2,550 | **628 / 2,550** |
| Validation: 3,535 endpoints | 2,391 / 11,900 | 430 / 2,550 | **482 / 2,550** |

The two exposure rows must not be added together without deduplicating them. This audit concerns endpoint identities, not protected test-pair overlap, homologous-component exposure, or general PLM pretraining. It uses the documented public training/validation inputs; it is not an independently authenticated complete history of the released checkpoint. Details and source checksums are in `provenance/ORIGINAL_EXPOSURE_AUDIT.json`.

Consequently, the original TUnA result remains mandatory and useful as an off-the-shelf comparison, but it cannot be described as guaranteed unseen-endpoint performance relative to its own external interaction training. C1/C2/C3 are defined relative to the iPIN split. Retrained PU-TUnA has a different, TRAIN-only interaction-supervision interpretation. No overlapping original-model rows are removed to improve or sanitize its result.

## Evaluation and isolation

The requested panels contain **3,019,012** rows: C1 has 3,187 P + 1,000,000 U; C2 has 13,446 P + 1,000,000 U; C3 has 2,379 P + 1,000,000 U. C3 retrained-minus-optimized is the primary contrast; all original/retrained-versus-baseline/optimized C1/C2/C3 comparisons are mandatory outputs. The six historical source-exclusive cells are not prerequisites for this first requested comparison.

The final metric is the same exact-tie-aware, design-weighted P-versus-U concordance, with the same 2,000 paired component-multiplicity draws, seed derivation, same-component convention and percentile intervals. The new evaluator verifies reproduction of both historical iPIN metric points and the historical component-draw metadata. Frozen iPIN prediction files are reused byte-for-byte; GPU permission does not change either reference predictor.

A separate SIF was necessary: the existing model image lacked `fair-esm`, calibration and HDF5 dependencies. The new image is `../containers/images/tuna-arm64-v1.sif`, SHA-256 `98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1`. It inherits the old image read-only, adds pinned dependencies offline, and contains the pinned GP package. Build recipes and dependency/image manifests are under `../containers/`.

Final scoring uses read-only frozen features/code/weights plus candidate identities, with only its benchmark-local output writable. It receives neither truth/keys, iPIN per-pair reference scores, nor training/development pairs. The later evaluator receives truth only after a separate complete prediction freeze and a new benchmark-local reservation. Historical protocols, protected-access ledgers and result files are never reset or written.

The qualified GPU guard uses seccomp to block nonlocal socket families and process-access channels, plus Landlock ABI 6 to restrict other-process file access and scope abstract local sockets/signals. CUDA's own `/proc` and driver access, device ioctls, and scoped local IPC remain available. This is **not** a claim of a private PID or network namespace; Arrhenius disables PID virtualization. The [Linux Landlock documentation](https://docs.kernel.org/userspace-api/landlock.html) describes the underlying restriction mechanism. Historical CPU-only restrictions are not reimposed as a benchmark requirement.

This is a disclosed follow-up on already-used iPIN test panels, not an untouched independent confirmation. Positive results, null results and operational/model failures must all be reported. Confidence intervals condition on the fitted predictors; three seeds do not turn them into uncertainty over all possible retraining experiments.

## Measured feasibility and operational history

The GH200 pilot reached approximately 368, 505 and **605 comparisons/second** at comparison batches 16, 32 and 64. The chosen batch peaked around **28.82 GB allocated GPU memory**, including the full residue cache. Eight epochs project to roughly **7.3–8 GPU-hours per seed**, or around **22–24 GPU-hours** across three seeds, excluding development covariance fitting, scoring, queue time and startup. Because seeds run concurrently, a reasonable provisional wall-time expectation is **8–10 hours**, with completion dependent on measured throughput and successful validation. The training allocation allows 16 hours; the dependent comparison allows four hours. These are estimates and reservations, not completed runtimes.

Operational attempts are preserved in logs. Container pip networking inside the contained build failed initially; dependencies were downloaded with recorded hashes and installed offline. The first Slurm submission needed an explicit GPU count. Job 2325077 failed at CPU binding before fitting; job 2325170 was cancelled during input loading to correct per-step resource allocation. The active replacement is 2325231. No scientific hyperparameter, test outcome or seed choice motivated those fixes. A six-second sequential cache read on n418 resolved the slow first random-access cache load. The failed historical-style GPU guard probes also remain logged; only the separately qualified GPU guard is used for final scoring.

## Repository boundary

All new source, candidate directories, containers, downloaded repositories/weights, sequence caches, logs, reservations, predictions and reports are inside `benchmark/`. The other ten candidate directories are organizational preparation; their dedicated image builds and model runs are pending their own qualification stages. No successful build or performance result is claimed for them.

The graphify skill was used to locate existing frozen-data/model relationships, with its query feedback and new code graph kept under `benchmark/`. The original repository graph was not updated in place. The byte-level scope audit checked **1,842** tracked and visible untracked files outside `benchmark/` and found no added, removed or changed file. Existing ignored data, weights and keys were used as read-only inputs; that census is not a hash inventory of every ignored file. See [repository scope audit](../REPOSITORY_SCOPE_AUDIT.json).
