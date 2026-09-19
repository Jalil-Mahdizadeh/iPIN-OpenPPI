# RAPPPID: latest saved checkpoints on C1/C2/C3 test

Completed **17 September 2026, 20:15 CEST**. The exact three mid-epoch-8 recovery checkpoints previously evaluated on C3-development were applied to all **3,019,012 test pairs**, individually and as the already defined three-seed mean-logit ensemble. Training was **not restarted or repaired**. No new Slurm jobs were submitted; evaluation used the existing single-GH200 allocation `2598385` on `n430`.

## Results

Design-weighted positive-versus-unlabeled concordance; higher is better. This is not confirmed-positive-versus-confirmed-negative AUROC.

| Model | C1 test | C2 test | C3 test |
|---|---:|---:|---:|
| Retrained RAPPPID, three-seed mean-logit ensemble | **0.775316** | **0.729804** | **0.700049** |
| Retrained seed 20260803 | 0.743063 | 0.705840 | 0.663315 |
| Retrained seed 20260817 | 0.719083 | 0.701415 | 0.674414 |
| Retrained seed 20260831 | 0.794204 | 0.718401 | 0.663223 |
| Original released RAPPPID-mult | 0.597417 | 0.600243 | 0.607067 |
| Baseline iPIN | 0.843493 | 0.805299 | 0.789249 |
| Optimized iPIN | 0.916037 | 0.851301 | 0.807948 |

The frozen ensemble is the primary candidate; individual seeds are descriptive results, not an opportunity to choose a different model for each test panel. In particular, seed 20260831 has a higher C1 point estimate than the ensemble, but that does not change the pre-test candidate definition.

| Ensemble comparison | C1 difference (paired 95% interval) | C2 difference (paired 95% interval) | C3 difference (paired 95% interval) |
|---|---|---|---|
| Minus original RAPPPID | +0.177899 [0.144834, 0.204852] | +0.129562 [0.072275, 0.177886] | +0.092981 [−0.030165, 0.187027] |
| Minus baseline iPIN | −0.068177 [−0.121190, −0.027185] | −0.075495 [−0.122838, −0.039906] | −0.089200 [−0.144076, −0.036099] |
| Minus optimized iPIN | −0.140721 [−0.190263, −0.103290] | −0.121497 [−0.173712, −0.083591] | −0.107899 [−0.163262, −0.062356] |

C3 is primary. Its ensemble score has a 95% percentile interval of **[0.605613, 0.765524]**. The improvement over original RAPPPID is positive as a point estimate, but its paired C3 interval includes zero: a conclusive C3 improvement is not established. Both iPIN references remain ahead of the retrained ensemble; the paired C3 intervals for those differences exclude zero. C1/C2 show clearer gains over the original model, while remaining below iPIN. All intervals use **2,000 paired two-endpoint component-bootstrap draws**, with the same historical component multiplicities; intervals are pointwise, not adjusted for all reported comparisons.

For the manuscript, this supports the narrower conclusion that this stopped, matched-data PU-RAPPPID-mult recipe does not close the iPIN performance gap. It does not establish a performance ceiling for RAPPPID: training stopped early, the training objective/tokenizer were adapted, and the original comparator is an externally trained single released model whereas the main retrained candidate is an ensemble.

## Exact selected states and inference policy

| Seed | Completed training at snapshot | Optimizer updates | Checkpoint SHA-256 |
|---|---|---:|---|
| 20260803 | 7 epochs + 75.142% of epoch 8 | 387571 | `f332c9fbd42e9d3146ca7c54743acca66ab0fa5e6d583e89aca2ae41e4135c30` |
| 20260817 | 7 epochs + 78.896% of epoch 8 | 389448 | `2ea98f070c5f5f712c6c4dc31c2a8f7f2389f0329a5a73a4548bdde487a49060` |
| 20260831 | 7 epochs + 77.824% of epoch 8 | 388912 | `ac0facd77f4bbb70fe25f144556d90cdf28e4151b324c41aae6a5c0efd0a4ef8` |

These are **unequal-position recovery snapshots**, not completed epoch-8 models and not a completed 20-epoch experiment. The user selected them after the extra [C3-development evaluation](results/retrained-v1/recovery-c3-dev-2578434-v2/RESULTS.md), where ensemble concordance was 0.699429 versus 0.692744 at epoch 4. No epoch-4 test evaluation or further checkpoint search was performed here.

The new [selection authorization](runs/recovery-test-v1/SELECTION.json) explicitly permits this test evaluation. The original training-only protocol and its original authorization flags remain unchanged historical artifacts.

The dedicated native RAPPPID SIF was reused unchanged. The model helper is byte-identical to the qualified frozen retraining helper. Each of the 17,000 public endpoint sequences was encoded separately with the actual native encoder for each checkpoint. Inference uses the frozen TRAIN-fitted 250-piece SentencePiece tokenizer, deterministic tokenization, first 1,500 residues, singleton native-head moments, FP32 model computation, and no AMP/TF32. Individual scores are pre-sigmoid logits; the ensemble is their FP64 arithmetic mean. No learned weights, numerical training settings, calibration, score direction or inference policy were changed.

The original released-model benchmark used its native sigmoid probabilities; those existing predictions were reused as they stood, rather than rescored or converted. Ranking is evaluated on the recorded scores, including their exact ties.

## Coverage, verification and timing

| Panel | Observed P | Unlabeled U | Total scored per candidate | Pairs with at least one truncated endpoint |
|---|---:|---:|---:|---:|
| C1 | 3,187 | 1,000,000 | 1,003,187 | 44,985 (4.4842%) |
| C2 | 13,446 | 1,000,000 | 1,013,446 | 58,634 (5.7856%) |
| C3 | 2,379 | 1,000,000 | 1,002,379 | 71,782 (7.1612%) |

No pair was dropped. All four candidate score columns are finite, and the stored ensemble is exactly the FP64 rowwise mean of the three stored seed logits. Qualification on 44 TRAIN-only pairs, including long TRAIN proteins, reproduced actual native singleton calls within **2.03e-6 logits**, below the predeclared `1e-4` tolerance. Reversal and order checks passed. The GPU bootstrap implementation passed an independent brute-force qualification; full-panel concordance also agreed with a reverse-summation long-double check within **5.56e-12**, below its predeclared `1e-9` roundoff allowance.

Selected models and scoring code were frozen before this new candidate session opened. Complete predictions and byte-identical original RAPPPID/baseline iPIN/optimized iPIN reference files were frozen before truth access. All reference point estimates, reference intervals and historical bootstrap draw definitions were reproduced. Temporary decrypted truth was removed automatically after evaluation; the sealed source package remains unchanged.

The single-use workflow took **192.39 seconds (3 minutes 12 seconds)**, including image verification, container launches, qualification/cache generation, candidate scoring, references, uncertainty estimation, publication and final frozen-training integrity checks. Within that, qualification/cache generation took 81.14 seconds, pair scoring took 3.50 seconds, and truth/metric/bootstrap evaluation took 39.83 seconds. This excludes implementation/report-writing time.

The complete frozen training/source/data/SIF guard passed both before and after evaluation. Original checkpoint copies and training recovery files retain their hashes. All new artifacts and report edits are confined to `benchmark/rapppid/`; the [scope audit](provenance/recovery-test-v1/scope-audit.json) covers Git-tracked and non-ignored untracked files outside `benchmark/`. The task-local Graphify update is AST-only and confined to the new script folder; the repository-wide graph was not updated.

For reproducibility, an initial setup-only attempt is preserved in [its status note](runs/recovery-test-setup-attempt-01/STATUS.md): a missing trailing blank line in a copied metric helper failed byte-identity checking before selection freezing or any candidate/truth access. The exact helper bytes were restored before the completed run; its numerical implementation and scoring policy were never changed.

These panels have already been examined in earlier benchmarks and are not a newly untouched holdout. The extra development look, user-selected partial checkpoints, adapted PU training recipe, and possible external training exposure of original RAPPPID should remain explicit in the manuscript.

## Artifacts

- [Scores and 95% intervals, CSV](results/retrained-v1/recovery-test-v1/scores.csv).
- [All paired differences and intervals, CSV](results/retrained-v1/recovery-test-v1/paired_differences.csv).
- [Coverage, CSV](results/retrained-v1/recovery-test-v1/coverage.csv).
- [Full results and provenance, JSON](results/retrained-v1/recovery-test-v1/RESULTS.json).
- [Completed-run record](runs/recovery-test-v1/RUN_COMPLETE.json), [scorer freeze](runs/recovery-test-v1/scorer_bundle/SCORER_FREEZE.json), and [verification record](provenance/recovery-test-v1/verification.json).
- [Prediction freeze](private/recovery-test-v1/freeze/PREDICTION_FREEZE.json); token-keyed per-pair logits are in `private/recovery-test-v1/predictions/cell-06.parquet`, `cell-03.parquet`, and `cell-00.parquet` for C1/C2/C3 respectively. No truth is included in those prediction tables.
- New source: `scripts/recovery_test_v1/`; frozen copies: `runs/recovery-test-v1/code/` and `scorer_bundle/code/`; logs: `logs/recovery-test-v1/`.

The evaluation is complete. Training remains stopped, and no additional RAPPPID stages are queued.
