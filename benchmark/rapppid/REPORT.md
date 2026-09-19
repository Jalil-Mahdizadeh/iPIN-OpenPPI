# Original released RAPPPID C1/C2/C3 benchmark

Completed 17 September 2026 at 08:28:37 CEST. The dedicated SIF passed qualification and evaluated **all 3,019,012 pairs** on one GH200. **Original released model only; no retraining was performed or queued.** All new artifacts stay under `benchmark/rapppid/` or `benchmark/containers/`. Existing D-SCRIPT jobs, repository inputs and original images remain unchanged.

## Results

Historical design-weighted positive-versus-unlabeled concordance (higher is better; this is not confirmed-positive-versus-confirmed-negative AUROC):

| Model | C1 | C2 | C3, primary |
|---|---:|---:|---:|
| Authors' released RAPPPID-mult | 0.597417 | 0.600243 | 0.607067 |
| iPIN baseline | 0.843493 | 0.805299 | 0.789249 |
| iPIN optimized | 0.916037 | 0.851301 | 0.807948 |

RAPPPID's 95% component-bootstrap intervals are C1 **[0.562603, 0.625943]**, C2 **[0.568191, 0.631259]**, and C3 **[0.548881, 0.676620]**. All 2,000 draws were finite for every model and contrast. On primary C3, RAPPPID minus optimized iPIN is **−0.200881**, paired 95% interval **[−0.289987, −0.086408]**; versus baseline it is **−0.182181**, interval **[−0.276359, −0.056525]**. All six reported RAPPPID-minus-iPIN intervals lie below zero. Intervals are the historical pointwise percentile intervals, not multiplicity-adjusted claims.

Interpretation: this released predictor provides modest positive-versus-unlabeled ranking signal on the panel, but trails both iPIN variants in every cell. This is an off-the-shelf transfer result under the declared singleton inference policy; it does not establish how matched-data retrained RAPPPID would perform, nor compare every possible native batching policy.

- [Aggregate results and provenance](results/original-v1/RESULTS.json)
- [Scores and 95% intervals, CSV](results/original-v1/scores.csv)
- [Paired differences, CSV](results/original-v1/paired_differences.csv)
- [Coverage, CSV](results/original-v1/coverage.csv)
- [Completed execution record](runs/original-v1/RUN_COMPLETE.json)

The original baseline/optimized iPIN prediction files were reused byte-for-byte. Their point estimates reproduced within `1e-12`, and all historical component-draw definitions/hashes reproduced. Predictions were complete and frozen before truth was opened. The temporary decrypted truth was removed by the evaluator; the original sealed inputs and keys remain untouched.

| Cell | Pairs scored | Pairs with at least one endpoint prefix-truncated | Fraction |
|---|---:|---:|---:|
| C1 | 1,003,187 | 44,985 | 4.4842% |
| C2 | 1,013,446 | 58,634 | 5.7856% |
| C3 | 1,002,379 | 71,782 | 7.1612% |

No pair was omitted or assigned a fallback score. Candidate-level scores remain in `private/original-v1/predictions/` as token-keyed Parquet files: `cell-06.parquet` (C1), `cell-03.parquet` (C2), and `cell-00.parquet` (C3). These private files do not contain truth labels; published CSVs are aggregate results.

## Original predictor pinned before test access

- Upstream: [jszym/rapppid](https://github.com/jszym/rapppid/tree/c3a28be56fb3bd96ccf8cc44ea9145cfcadeaf6c), commit `c3a28be56fb3bd96ccf8cc44ea9145cfcadeaf6c`.
- Authors' released checkpoint: `1690837077.519848_red-dreamy`; 4,559,467 bytes; SHA-256 `fe603efd3256517b9fcc3a6e473d842fab2e3fa8483f3dd2b3350b742a3c02fd`.
- Released SentencePiece model: SHA-256 `b60afba79a5f2e9e561f616cd1c18212b1e8d8bc57f0d6c4d5de9715c2496ba8`; 250-token vocabulary.
- The [release documentation](https://github.com/jszym/rapppid/blob/c3a28be56fb3bd96ccf8cc44ea9145cfcadeaf6c/data/pretrained_weights/README.md) identifies human comparatives training and a **multiplicative (`mult`) head**, rather than the paper's concatenation head. This is the authors' released RAPPPID-mult model, **not a claim to reproduce the exact original paper checkpoint**. The supplied training command names the STRING C3 comparatives dataset.
- Native `LSTMAWD`, `WeightDrop`, `Mish`, tokenizer helpers and model tensors are used without editing upstream source. Strict state loading and tensor equality are checked. The released model contains 188,161 distinct learned parameters.
- No training, calibration, score inversion, order averaging, new tokenizer fitting or checkpoint selection by benchmark outcome.

## Frozen inference definition and native batching issue

The upstream [test step](https://github.com/jszym/rapppid/blob/c3a28be56fb3bd96ccf8cc44ea9145cfcadeaf6c/rapppid/train.py) encodes endpoint A and endpoint B separately before applying the interaction head. We define this predictor **one pair at a time**, with each endpoint encoded as a singleton and the native head receiving one pair. Deterministic tokenizer inference follows the authors' inference helper/native validation tokenizer.

Two implementation details make this explicit definition essential:

1. The native encoder slices the padded token array at the batch's maximum nonzero-token count; it does not pack variable-length sequences. An endpoint can therefore change when unrelated longer examples enter the encoder batch.
2. `MultClassHead` computes `.mean()` and `.std()` over the entire input tensor. Passing several unrelated pairs directly to this head changes the normalization and therefore the scores, even in evaluation mode.

This run does not silently use arbitrary multi-pair batching. Endpoint caching is qualified against **singleton native encoding**. Only endpoints having exactly the same native effective token count are batched together. The cached head uses rowwise mean and sample standard deviation, algebraically reproducing the **singleton native head**. It must agree with direct unmodified reference calls within absolute probability tolerance `1e-5`. Endpoint reversal and batch/order checks are required. This is a disclosed fixed inference policy, not a claim of equivalence to the authors' batch-80 evaluation or every possible upstream batching arrangement. The documentation's two-sequence example is tested separately for code/checkpoint loading fidelity.

Native release length policy: retain the **first 1,500 residues per endpoint**, then tokenize deterministically with the released SentencePiece model. Preserve native zero padding and nonzero-count slicing. All pairs received finite scores; this is full **pair** coverage, not full-residue coverage. Truncation counts are reported above. The frozen 17,000-sequence snapshot is reused, SHA-256 `bc7a91661ea05cbfdcf3551b9a4d18c149ac077549ebbcf0be7e7ef5d94ace77`; no refreshed UniProt records are substituted.

## Container and numerical qualification

Dedicated image: `benchmark/containers/images/rapppid-native-arm64-v1.sif`, 10,677,870,592 bytes; SHA-256 `e853a89768c5351927f90fd0ccfb2ad899a15a6fc239a9014726af0c34442d48`. [Recipe](../containers/rapppid-native-arm64-v1.def), [build script](../containers/build_rapppid.sh), and [download manifest](../containers/manifests/rapppid-downloads.json). The build ran from 08:11:18 to 08:26:10 CEST on 17 September (14m52s), including strict checkpoint/tokenizer tests and final image hashing.

The immutable parent is `containers/images/ipin-model-arm64_0.1.0.sif`, SHA-256 `c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`. Existing SIFs are not modified. The dedicated image bundles the verified upstream source, checkpoint, tokenizer and additional runtime libraries. It retains the parent GH200-compatible Torch 2.8/Python 3.12/CUDA stack, uses the authors' Lightning 1.3.8 and TorchMetrics 0.4.1 pins, and ARM64-compatible SentencePiece 0.2.1/PyTables 3.10.2. This is a qualified runtime port, **not an identical historical Torch1.9 environment**. PyYAML and other shared scientific libraries remain the parent versions; inference compatibility is tested rather than claiming that the old whole training environment was recreated.

All required checks passed before opening candidate pairs:

- Container imports, pinned assets, strict checkpoint loading, and native-public-loader agreement.
- CUDA-compatible restricted mounts/process/network guard; it does not claim PID/network namespace virtualization.
- Public example and fixed TRAIN-only pairs, including long TRAIN endpoints; no fitting.
- Singleton/cached/batched-head equivalence, symmetry, unchanged learned tensors, and complete finite endpoint cache.
- Independent brute-force qualification of the weighted GPU metric, including exact-score ties and component multiplicities.
- Freeze code, cache, sequence identity, checkpoint, tokenizer, numerical policies and image hash.

[GPU qualification evidence](runs/original-v1/QUALIFICATION.json): public-loader example error `0`; 44 TRAIN-only reference pairs, including the longest TRAIN endpoints; maximum cached-score error `1.4901161193847656e-7` against actual native singleton calls (tolerance `1e-5`); actual wrapper batch sizes 1, 8 and 8,192 all passed, with zero reversal and permutation errors. The maximum cached-embedding error was `1.6689300537109375e-6`; separate duplicate-batch checks reached at most `2.86102294921875e-6`. The learned-state digest remained `7e1e1b70b084dff628b42683c5d4b6ca7f6675f92302da96873f20acd3d83734`.

All 17,000 endpoint embeddings were finite; 616 sequences exceed 1,500 residues. Native effective token counts ranged from 16 to 1,007. Cache inference took 2.37s, excluding tokenizer preparation/imports; the entire in-process qualification took 6.04s. Ordinary upstream multi-pair head normalization differed from singleton native reference probabilities by as much as `0.2197753191` on this TRAIN-only fixture, confirming that batching is a material protocol issue, not just a speed choice. The qualified rowwise implementation preserves the preselected singleton definition; it does not claim to reproduce another batch policy. The independent weighted-metric oracle error was `7.77e-16` (tolerance `1e-12`).

The [scorer freeze](runs/original-v1/scorer_bundle/SCORER_FREEZE.json), SHA-256 `b017edbfd1c0f22a60aef80812316c4b27d023ce9e9725ec5b0dcb161573e41f`, binds these checks, code, cache, image and policies before candidate access. No model tensor was fitted or updated; sampling TRAIN pairs here was only an inference fidelity/performance test.

## Evaluation protocol and timing

Evaluated exactly **3,019,012** C1/C2/C3 rows. Original baseline and optimized iPIN predictions were reused byte-for-byte. The metric is historical design-weighted P-versus-U concordance, with **2,000 paired two-endpoint component-bootstrap draws**. C3 is primary; C1/C2 and both reference contrasts are reported. Historical reference point estimates and bootstrap draw definitions reproduced.

Scoring saw only frozen public sequence features and candidate identities. Truth was mounted only in a separate phase after complete predictions and references were frozen. Original historical ledgers were not modified. Execution used the already allocated single GH200 on `n448`, Slurm allocation **2575828**; no new Slurm job or four-GPU reservation was submitted. Existing D-SCRIPT jobs were left untouched.

Measured timings:

| Stage | Wall time | Scope |
|---|---:|---|
| SIF build | 14m52s | Build script, tests, compression and final image hash; excludes preceding dependency preparation |
| GPU qualification | 6.04s | In-process public/TRAIN tests, cache and metric oracle; excludes process/container startup |
| Endpoint-cache forward inference | 2.37s | Included in qualification; all 17,000 sequences; excludes tokenization |
| Cached pair-scoring loop | 2.21s | All 3,019,012 pairs, input/index processing and score writes; excludes model/container startup |
| Scoring worker | 9.36s | Full worker process, including startup and integrity checks |
| Truth/metric calculation | 28.17s | Three cells, three scorers, 2,000 paired component-bootstrap draws, truth cleanup |
| Scoring-to-publication pipeline | **74.66s** | 08:27:22–08:28:37 CEST; includes worker, merge, reference import, freeze, evaluation and publication; excludes earlier image/bundle verification and candidate-session opening |

The small released model has no ESM/ProtT5-sized embedding dependency. Reusing each independent endpoint embedding makes pair inference cheap; this timing should not be interpreted as a retraining estimate. The final scorer-state digest was unchanged. Different batch-shape/reversal spot checks on test candidates differed by at most `5.96e-8`, below the prospectively frozen `1e-5` tolerance; no policy was changed in response to test results.

Outputs are saved in `results/original-v1/`: `RESULTS.md`, `RESULTS.json`, `scores.csv`, `paired_differences.csv`, and `coverage.csv`. Candidate-level predictions remain private to this benchmark directory. Launchers and Python scripts are retained for provenance; their single-use guards intentionally reject overwriting the completed run.

## Interpretation and scope

External PPI-training exposure is possible; iPIN C3 is not proven cold relative to the authors' STRING training data. This is an off-the-shelf transfer evaluation on already examined panels, not matched-data retraining or a newly untouched test. U remains unlabeled, not verified noninteraction. Native sigmoid output is not established as calibrated binding probability on this dataset.

The [candidate-specific scope audit](provenance/repository-sif-audit.json) passed: **1,912 Git-tracked and non-ignored untracked files outside `benchmark/` checked; zero added, removed or changed**. This census does not claim to hash every ignored data artifact. Existing SIFs were read-only parents/inputs, and all evaluation mounts of historical inputs were read-only. No PLM-interact retraining was resumed and no D-SCRIPT job was changed. Work stops at this completed original-model evaluation.

## Subsequently authorized retraining

Later on 17 September 2026, the user authorized a separate **20-epoch retraining experiment**, retaining all three seeds' checkpoints and evaluating the full C3-development panel at epochs **4, 8, 12, 16 and 20**. Slurm job **2578434** started at **09:45:28 CEST** on `n178` with three GH200 GPUs and a 48-hour limit. See [RETRAINING_REPORT.md](RETRAINING_REPORT.md) for the frozen PU recipe, qualification, progress and timing. No retrained test evaluation or automatic epoch selection is queued; the user will choose after reviewing development results. The original experiment and results documented above remain unchanged.
