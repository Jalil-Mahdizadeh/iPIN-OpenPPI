# Original PLM-interact C1/C2/C3 benchmark

Current completion record: [final results](results/original-v1/RESULTS.md),
completed 17 September 2026. Original 650M humanV11 has full C1/C2/C3 results;
no matched-data retraining was performed. See the [README](README.md) for current
status. The dated snapshot below preserves the pre-completion execution history.

## Historical startup snapshot

Status at **18:27 CEST, 16 September 2026**: the dedicated SIF is built and qualified; original-model C1/C2/C3 scoring is **running** as Slurm job **2555430** on **n538**, using four distinct GH200 GPUs. No test performance metrics are available yet, and test truth remains unopened. Expected completion is approximately **03:30–06:30 CEST, 17 September**, subject to production throughput and final metric calculation. No PLM-interact retraining is authorized or scheduled by this run. D-SCRIPT continues unchanged on its separate node.

## Execution summary

- Container build completed at 18:16 CEST after approximately 22.5 minutes, including correction of the published wheel's import-path requirement. No upstream model code or checkpoint tensors were changed.
- Qualification passed at 18:19 CEST; its measured work took 116.7 seconds. See [QUALIFICATION.json](runs/original-v1/QUALIFICATION.json).
- Job submitted at 18:22:31 CEST and started at **18:23:38 CEST**. Allocation: four GPUs, 72 CPUs total, 180 GiB host memory, and a **72-hour safety limit**, not an expected duration. See [JOB.json](runs/original-v1/JOB.json).
- At 18:27:43 CEST, all four workers had recent progress, with **17,408 committed C1 predictions** independently checked for finite probabilities in `[0,1]`. Worker rates were **22.8–23.9 pairs/second/GPU**, consistent with the pilot. No worker exceptions or out-of-memory failures were found. Four different physical GPU UUIDs were verified. See [STARTUP_HEALTH.json](provenance/STARTUP_HEALTH.json).
- The job will score all cells, verify complete coverage, merge shards, freeze all predictions, and then run the separate truth-reading evaluation and publish the comparisons. No retraining or additional model variant follows automatically.

This is a startup report, **not a completed performance result**. Aggregate performance will be published in `results/original-v1/RESULTS.md` and its accompanying CSV/JSON files only after the full pipeline succeeds.

## Predictor selected before test access

The primary original-model benchmark uses the authors' released **650M humanV11** predictor, not the 35M feasibility variant and not a newly trained replacement. The user requested the original released model first. Selection is based on the paper's main model size and the authors' general human/cross-species release, not on any scores on this benchmark.

- Model: [`danliu1226/PLM-interact-650M-humanV11`](https://huggingface.co/danliu1226/PLM-interact-650M-humanV11/tree/e86e392dec13dd0c23252c94947b04a7a9821b0e).
- Model revision: `e86e392dec13dd0c23252c94947b04a7a9821b0e`.
- Original `pytorch_model.bin`: 2,609,670,405 bytes; SHA-256 `68c50e1dc84ee3cb6c08a7c83eefb382a29a3c1237fd577986854f746c63d665`.
- Code: [`liudan111/PLM-interact`](https://github.com/liudan111/PLM-interact/tree/ab2ae6ae1aa81accf4c1f7f6f341164baf97809a), commit `ab2ae6ae1aa81accf4c1f7f6f341164baf97809a`; packaged inference reference PLMinteract 0.1.1.
- Base ESM-2 config/tokenizer: `facebook/esm2_t33_650M_UR50D`, revision `08e4846e537177426273712802403f7ba8261b6c`. The released PLM-interact checkpoint supplies all learned parameters; constructing its architecture from config avoids downloading redundant base-model weights. Strict state loading and tensor equality are required.
- Output: the native CLS/ReLU/linear/sigmoid probability. No fitting, calibration, threshold selection, probability inversion, order averaging, or ensemble is applied.

The native model is order-sensitive. For an unordered-pair benchmark, this run prospectively supplies endpoints in **ascending frozen sequence-SHA256 order**, then applies the native model once. This deterministic ordering wrapper is explicitly part of the predictor; it is not a claim that the authors' raw model is symmetric.

## Length and input policy

Use the authors' [documented inference setting](https://github.com/liudan111/PLM-interact/blob/ab2ae6ae1aa81accf4c1f7f6f341164baf97809a/README.md): `max_length=1603`, `truncation='longest_first'`, with three pair special tokens. This is a published deployment setting, not a claim that the architecture fundamentally cannot accept longer inputs. All 3,019,012 test pairs must receive finite scores, but inputs over 1,600 combined residues are truncated by the native tokenizer. This is **complete pair coverage, not full-residue coverage**. Counts will be reported separately for C1/C2/C3. No length-filtered evaluation or replacement of failed scores with zero is allowed.

Use the frozen 17,000-sequence benchmark snapshot, not refreshed UniProt records. Snapshot SHA-256: `bc7a91661ea05cbfdcf3551b9a4d18c149ac077549ebbcf0be7e7ef5d94ace77`. The pair input order and length policy are fixed without test outcomes.

## Dedicated container and qualifications

New image: `benchmark/containers/images/plm-interact-native-arm64-v1.sif`. The [build script](../containers/build_plm_interact.sh) and [recipe](../containers/plm-interact-native-arm64-v1.def) use the existing iPIN ARM64 image only as an immutable parent. Its checksum is verified. The existing image uses Transformers 4.55.2; the [published package](https://pypi.org/project/PLMinteract/0.1.1/) pins 4.40.1, so a separately versioned image is appropriate.

Runtime targets Transformers 4.40.1, tokenizers 0.19.1 and PLMinteract 0.1.1. Torch remains the GH200-compatible parent build 2.8.0a0+34c6371d24.nv25.8, on Python 3.12. Native-model numerical qualification is required rather than claiming an identical historical author environment. Only the new image's Python path is extended to accommodate the published wheel's absolute `utils` import; upstream source and learned tensors are not edited.

Completed image: **13,101,785,088 bytes**, SHA-256 `e064e38053d6dfcacc65a23467d97f75f79ca6095e6f760def4125ccf452ffc2`. The original checkpoint, config/tokenizer and pinned upstream source are bundled for offline scoring. See the [download manifest](../containers/manifests/plm-interact-downloads.json), [image checksum](../containers/manifests/plm-interact-sif.sha256), and [build log](../containers/logs/plm-interact-native-v1-build.log).

The following checks passed before opening test candidates:

1. Verify pinned download hashes and container imports.
2. Verify the network/process restriction guard on CUDA.
3. Compare the wrapper with the actual published inference class on the public README example, fixed TRAIN pairs and longest TRAIN endpoints. Require finite probabilities, unchanged learned parameters and absolute score errors no larger than `1e-5`.
4. Check canonical-order reversal and padded/bucketed batches of 8, 16 and 32.
5. Time a fixed-seed 512-pair TRAIN-U sample, without fitting. Choose a qualified batch size by throughput only, not by biological performance. Record peak GPU allocation and projected full-panel costs.
6. Check the GPU metric against an independent small brute-force oracle, including ties and component multiplicities.
7. Freeze code, tokenizer/model identities, sequences, numerical settings, ordering, truncation, SIF identity and qualification results.

The native-class public-example probability was `0.9918721318244934`, reproduced with zero absolute error. Across 24 TRAIN reference fixtures and tested batch sizes, the maximum native-reference error was **3.49e-9** (tolerance `1e-5`); canonical-order reversal error was zero. The learned-parameter digest was unchanged. The independent GPU metric oracle differed by at most **7.77e-16** (tolerance `1e-12`). Guard tests passed, including CUDA use, inherited restrictions and denied network access; they do not claim PID/network namespace virtualization. See [container-guard.json](logs/container-guard.json).

The [scorer freeze](runs/original-v1/scorer_bundle/SCORER_FREEZE.json) has SHA-256 `6b9acdd2c66b0c001e6ac1f60abd15274cec6856a6de09257a22c5febd47c734`. Production uses its immutable code copies, FP32 inference, no AMP/TF32, and the qualified batch size of 16.

No new training budget is inferred from this original-model benchmark request.

## Evaluation and timing

Candidate-only scoring uses four independent GPU shards on a separate node. D-SCRIPT's allocation is not shared or modified. A 72-hour job limit provides scheduling margin; it is **not a runtime estimate**. The initial queue wait was about 67 seconds.

The fixed 512-pair TRAIN-only pilot produced:

| Batch size | Pairs/second/GPU | Scoring seconds | Peak allocated GPU memory (decimal GB) |
| --- | ---: | ---: | ---: |
| 8 | 23.637 | 21.661 | 6.620 |
| **16 (selected)** | **24.076** | **21.266** | **10.500** |
| 32 | 23.706 | 21.598 | 18.262 |

At the selected rate, ideal four-GPU scoring takes **8.71 hours**. Allow approximately **9–12 hours from the 18:23 CEST start**, including setup, production variation and metric calculation: roughly **03:30–06:30 CEST on 17 September**. This is an estimate, not a guarantee. Early production throughput supports that window; later C2/C3 length mixtures may differ.

For measured single-GPU throughput `q` pairs/second, an ideal four-GPU score pass takes `3,019,012 / (4*q*3600)` hours. The qualification sample is TRAIN-only; actual test length mixtures, shared I/O and GPU utilization can change that estimate. Production progress will be used to refine timing without changing the predictor.

The benchmark-local workflow reuses the previously qualified candidate/truth separation, historical design-weighted P-versus-U concordance, and 2,000 paired two-endpoint component-bootstrap draws. C3 is primary; C1 and C2 are also mandatory. Original baseline and optimized iPIN prediction files are copied byte-for-byte and their metric points must reproduce. Keys and truth are mounted only in the separate metric phase after complete predictions are frozen; historical ledgers are never changed.

Expected aggregate outputs under `results/original-v1/`: `RESULTS.md`, `RESULTS.json`, `scores.csv`, `paired_differences.csv`, and `coverage.csv`. Pair-level predictions and job logs stay in this candidate's private/run directories. No retraining follows automatically.

Scoring progress is committed every 512 pairs per worker under `private/original-v1/shards/rank-*/`, with job logs under `logs/original-job-2555430.*.log` and worker logs under `logs/original-score-2555430-rank-*.log`. The job is resumable from committed chunks without changing the frozen predictor, but any failed job still requires explicit operational follow-up; submission alone is not evidence of completed evaluation.

## Exposure and interpretation

Authors' [repository mapping](https://github.com/liudan111/PLM-interact/tree/ab2ae6ae1aa81accf4c1f7f6f341164baf97809a) and the V11 model card's training section attribute humanV11 to the D-SCRIPT human/cross-species benchmark. The same V11 card contains an inconsistent STRING V12 sentence. Record this metadata ambiguity rather than claiming an independently verified complete training history. The pinned weight identity does not depend on that interpretation.

External interaction-training overlap with this benchmark is possible; C3 is cold relative to iPIN's TRAIN partition, not proven cold relative to the authors' external training. Sequence-language-model pretraining exposure is a separate consideration. This is an original-checkpoint transfer benchmark on previously examined panels, not a clean matched-data retraining experiment or a new untouched holdout. The metric ranks observed positives versus sampled unlabeled pairs; U is not verified noninteraction and the score is not validated as a calibrated biological probability here.

## Scope

All new assets, scripts, caches, manifests, logs, images and results are under `benchmark/plm_interact/` or `benchmark/containers/`. Existing repository inputs, D-SCRIPT jobs and images are read-only. The [scope audit](provenance/repository-sif-audit.json) passed for **1,912 Git-tracked and non-ignored untracked files outside `benchmark/`**, with no additions, removals or content changes in that audited set.
