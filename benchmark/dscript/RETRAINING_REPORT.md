# Matched-data D-SCRIPT retraining and automatic test evaluation

Recipe frozen on 2026-09-12 UTC. Status: **training healthy; monitoring paused as requested**. Startup was verified at 2026-09-12 22:01 UTC (2026-09-13 00:01 CEST). User authorized retraining, automatic C1/C2/C3 testing, generous Slurm limits, and a pause after healthy startup. Original D-SCRIPT evaluation is already complete and remains unchanged; see [original evaluation report](ORIGINAL_EVALUATION_REPORT.md).

## Verified startup and handoff

Job **2342911** is training all three seeds on **three distinct GH200 GPUs on n40**. The full native-cache checksum and frozen-code/data/SIF checks passed before the workers started. Each model has **629,206 trainable parameters**. At the recorded health snapshot:

| Seed | Epoch-1 comparisons completed | Recent comparisons/s | Initial running total loss | Current running total loss |
| --- | ---: | ---: | ---: | ---: |
| 20260803 | 9,728 | 34.46 | 0.556619 | 0.458993 |
| 20260817 | 9,472 | 33.25 | 0.554335 | 0.457751 |
| 20260831 | 9,728 | 34.39 | 0.570707 | 0.456157 |

Losses and gradients are finite; the latest gradient norms are nonzero. Actual peak allocated GPU memory is approximately **8.7–9.5 GiB per worker**. Read-back of each saved recovery checkpoint verified at least 4,096 completed comparisons, updated projection weights, finite model state, and populated optimizer/CPU-RNG/CUDA-RNG state. These checkpoints are continually replaced atomically as training advances.

Initial throughput was substantially slower than the pilot, then accelerated without changing the frozen recipe or restarting the job. The latest production rates imply roughly **32–33.5 hours per two-epoch training stage**, compared with the **72-hour** limit; approximately **5.4–5.6 days of training**, plus queueing, DEV inference, scorer preparation and final test evaluation. This remains an estimate, not a deadline or evidence of convergence.

The remaining jobs **2342912–2342916** are pending on their expected successful-completion dependencies. No retrained test evaluation has started. The [startup health snapshot](provenance/retrained-v1/STARTUP_HEALTH.json) records worker progress, GPU UUIDs, checkpoint audits and Slurm states. The [scope audit](provenance/retrained-v1/scope-audit.json) verified that all 1,842 covered files outside `benchmark/` remain unchanged.

**Monitoring is now paused; the jobs continue.** The user will notify the assistant after retraining/evaluation completes. No additional benchmark or training recipe is queued.

## Model and frozen training recipe

This run is **PU-D-SCRIPT**, not Topsy-Turvy and not fine-tuning of the released human PPI checkpoint. It follows the existing matched-data iPIN/TUnA philosophy: fresh native PPI prediction layers, a fixed native encoder, weighted positive-versus-unlabeled learning, and development-only checkpoint selection. “Testing the pre-trained model” in the request is interpreted as testing the resulting retrained model; the original `human_v1` predictions are reused as a separate reference.

- Fixed native Bepler–Berger `lm_v1` encoder, providing full-context **6,165-dimensional FP32 residue embeddings**. All PPI prediction layers, including the 100-dimensional projection, are freshly initialized and trained. No released `human_v1` PPI weights initialize the retrained heads.
- Native original architecture: projection 6165→100 with ReLU/dropout 0.5, 50 hidden contact channels, 7×7 contact convolution, native batch normalization, positional weighting and 9-wide pooling. Native initialization and post-step parameter/symmetry clipping are retained.
- **Three seeds:** 20260803, 20260817, 20260831. **Eight epochs per seed**, with **16 P-versus-U comparisons per optimizer step**. Native Adam, constant learning rate 0.001, weight decay 0. One declared hyperparameter recipe; no test-dependent acceptance gate.
- Every epoch visits all **2,000,000 TRAIN unlabeled pairs**, with balanced cycling of **16,799 observed positives**. The independent PCG64DXSM order streams use the same seed/epoch/stream convention as the earlier iPIN/TUnA workflow. Training endpoint indices are checked against the TRAIN partition.
- TRAIN only: independently sample a contiguous crop of at most **512 residues per endpoint occurrence** from the full-context native embeddings. Short sequences are unpadded. No interaction row is excluded. Native pair-at-a-time normalization is preserved; contact-map tiling is not used during training.
- DEV/test inference uses **all residues**, up to 7,570, with the previously qualified length-safe execution and complete-halo tiling. No evaluation cropping or pair exclusion.
- Model/cache/softplus calculations use FP32; weighted loss and ensemble accumulation use FP64. AMP and TF32 are disabled.

The training objective is

```text
w = U_design_weight / mean(TRAIN_U_design_weight)
ranking = mean(w * softplus(score_U - score_P))
contact = mean(w * (mean(contact_map_P) + mean(contact_map_U)) / 2)
total_loss = 0.35 * ranking + 0.65 * contact
```

Scores are the native stable **pre-sigmoid logits**, `20 * (raw_pool - 0.5)`. This replaces binary-label BCE with the matched-data PU ranking objective while retaining native contact-map sparsity regularization and its published 0.35/0.65 mixture. U is not labeled as a verified negative. The total loss is therefore **not directly comparable to iPIN's ranking-only loss**; logs separately report the ranking loss, contact penalty, total loss and gradient norm.

The native architecture, optimizer and contact penalty are based on the [pinned original training implementation](https://github.com/samsledje/D-SCRIPT/blob/0b3f7363b7d62fb99f5c8bfc6780833f088b8d84/dscript/commands/train.py), [interaction implementation](https://github.com/samsledje/D-SCRIPT/blob/0b3f7363b7d62fb99f5c8bfc6780833f088b8d84/dscript/models/interaction.py) and [contact module](https://github.com/samsledje/D-SCRIPT/blob/0b3f7363b7d62fb99f5c8bfc6780833f088b8d84/dscript/models/contact.py). The PU objective, comparison sampling, crop policy and eight-epoch budget are explicitly disclosed adaptations, not a reproduction of the authors' native supervised training recipe.

## Checkpoint selection and test comparison

At epochs **4 and 8**, each seed scores the complete C3-DEV panel: **2,265 P + 1,000,000 U**. After all seeds finish, select the shared epoch with the highest weighted P-versus-U concordance of the **FP64 arithmetic mean of all three seed logits**. Exact ties choose the earlier epoch. All seeds are retained. C1/C2 test results and original-model test results do not enter this selection rule.

After selection, freeze the selected weights, full-length learned projection caches, code and input identities before opening this run's test candidate session. Score all **3,019,012 C1/C2/C3 candidates** on four GPUs. Only after complete finite predictions are merged and frozen does a separate evaluation process receive the protected truth.

The final comparison contains original D-SCRIPT, the retrained ensemble, all three retrained seed members, baseline iPIN and optimized iPIN. Original D-SCRIPT and iPIN per-row prediction files are reused byte-for-byte. Their previously reported metric points must reproduce. The metric remains design-weighted P-versus-U concordance, with **2,000 paired historical component-bootstrap draws** and exact-score half ties. Primary contrast: retrained ensemble minus optimized iPIN on C3; retrained versus original and the other iPIN contrasts are also reported. These logits are ranking scores, not calibrated interaction probabilities.

The panels were already examined for iPIN/TUnA/original D-SCRIPT. This is a disclosed follow-up, not a newly untouched confirmatory holdout. The original checkpoint's documented external-training overlap remains a caveat. Fresh PPI-head initialization avoids importing its learned interaction weights, but the native encoder remains externally pretrained.

## Slurm chain and timing margin

| Stage | Job | GPUs | Wall-time limit | Dependency |
| --- | ---: | ---: | --- | --- |
| Native LM cache | 2341945 | 1 | 6 hours | Completed successfully |
| Epochs 1–2, all three seeds | 2342911 | 3 | **72 hours** | Cache success |
| Epochs 3–4, all three seeds | 2342912 | 3 | **72 hours** | 2342911 success |
| Epochs 5–6, all three seeds | 2342913 | 3 | **72 hours** | 2342912 success |
| Epochs 7–8, all three seeds | 2342914 | 3 | **72 hours** | 2342913 success |
| DEV selection and scorer freeze | 2342915 | 1 | **24 hours** | 2342914 success |
| C1/C2/C3 scoring and evaluation | 2342916 | 4, then 1 | **24 hours** | 2342915 success |

The Arrhenius GPU partition permits at most 72 hours per job. Each training job runs one seed per GPU on a single node, reserving 300 GiB of host memory for the shared read-only residue cache and working data. Explicit GPU totals and per-node/per-task bindings avoid the inherited one-GPU launch issue encountered during original inference.

A uniformly sampled TRAIN-only warm-memory pilot measured **35.36 comparisons/second**, suggesting approximately **31.4 hours per two-epoch stage** or **125.7 hours (~5.2 days) per seed** for the eight training epochs. Seeds run in parallel, so this is not multiplied by three for elapsed wall time. Queueing, full-cache I/O, node contention, checkpointing and DEV/test scoring are additional; this is an estimate, not a guarantee. The 72-hour limit is about 2.3 times the pilot estimate per stage. The initial narrow fixture had suggested about 90 hours; the broader sample is the more conservative planning estimate.

Training checkpoints are written atomically every **2,048 comparisons** and at epoch boundaries, preserving model, optimizer, CPU/CUDA RNG states, data position and accumulated losses. Native initialization is not repeated on resume. Each two-epoch stage continues the previous state; the scientific eight-epoch run is unchanged by Slurm segmentation. Any nonfinite value, identity mismatch or unsuccessful dependency prevents later test evaluation. A failed/preempted job may still require an audited resubmission; the workflow does not silently change hyperparameters or skip an incomplete seed.

## Qualification and provenance

- Fresh/native forward and gradient checks matched exactly on TRAIN fixtures.
- A tiny fixed TRAIN fixture learned: average ranking loss decreased from **0.14772** over the first eight pilot steps to **0.02203** over the last eight. Pilot weights were discarded.
- Resume qualification reproduced the next-step loss metrics and every model-state entry **bit-for-bit** on the same GH200.
- Worst declared crop batch: **16 comparisons with all endpoints 512 residues**, including backward and optimizer, used **14,915,134,976 GPU bytes (~13.9 GiB)**, safely within the allocated GH200's memory. This is a qualification probe, not a full-length training claim.
- Synthetic frozen-scorer/ensemble checks passed; largest exchange-symmetry difference was **9.54×10⁻⁷ logits**, within the declared 10⁻⁴ tolerance. Missing, duplicate and nonfinite reference rows and unsafe manifest paths were rejected.
- GPU metric/bootstrap calculations matched the independent small brute-force oracle to **7.8×10⁻¹⁶**.
- Six stored TRAIN-sequence embeddings matched fresh native encoding exactly; crop sizes and offsets also matched exactly.
- Native raw cache: **17,000 sequences, 9,237,157 residues**, full-context FP32, **227,788,291,748 bytes** including the NPY header. SHA-256: `640f5859152af2f8fcf1c24d8712f8d184d06c1adf58d87060713a7ac510fd1b`. Cache job completed in **23m16s**, including hashing. The old 100-D original-model projection cache is not used for fitting the changing projection.
- Existing qualified SIF reused unchanged: `../containers/images/dscript-native-arm64-v1.sif`, SHA-256 `bfcee514eeb908a05bde701f230066baca9fb45fab2a811732f8e16a14a3912c`. No rebuild or upstream source patch was needed.

Training freeze SHA-256: `ad076c1852a3af36106cd861d724063674055e5724795788c3824b006a36d286`.
Execution freeze SHA-256: `bce562fa07aa4212a771ce2ee7783edc4dd4bd19fbb42a291e0fd7fde08310ae`.

## Files and monitoring

- [Training recipe](runs/retrained-v1/TRAINING_FREEZE.json), [execution freeze](runs/retrained-v1/EXECUTION_CODE_FREEZE.json), [job chain](runs/retrained-v1/JOBS.json).
- [Pilot](runs/retrained-v1/PILOT.json), [representative timing pilot](runs/retrained-v1/REPRESENTATIVE_PILOT.json), [pipeline/resume qualification](runs/retrained-v1/PIPELINE_QUALIFICATION.json), [cache qualification](runs/retrained-v1/CACHE_QUALIFICATION.json).
- Per-seed training state and progress: `runs/retrained-v1/training/seed_<seed>/PROGRESS.json`, `events.jsonl`, `resume.pt`, and stage/epoch manifests.
- Training logs: `logs/retrained-train-<job>-rank-<rank>.log`; stage stdout/stderr: `logs/retrained-epochs-<start>-<end>-<job>.*.log`.
- Expected final aggregates, after successful completion: `results/retrained-v1/RESULTS.md`, `RESULTS.json`, `scores.csv`, `paired_differences.csv`. These do not exist yet and no retrained test result is being claimed.
- Per-row test inputs and predictions will remain in `private/retrained-v1/`. Historical ledgers, datasets, models, original D-SCRIPT results and SIF files are read-only inputs. All new artifacts stay under `benchmark/`.

The required startup checks passed, and monitoring has paused. Jobs continue independently of the chat. No model or benchmark beyond this authorized retraining/test chain is queued.
