# One-time protected final test

Date: 2026-09-11. Authority: [DEC-0051](../../../governance/decisions/DEC-0051-authorize-one-final-protected-evaluation.md).
Protocol: [Protected final test v1](../../protocols/PROTECTED_FINAL_TEST_v1.md).

## Result

**The frozen selected model has a clear held-out ranking signal.** On the
primary C3 test, concordance is **0.789**, 95% component-bootstrap interval
**[0.708, 0.846]**, versus 0.549 for the highest-scoring prespecified control.
All eleven prespecified C3 model-minus-control paired intervals exclude zero
in the positive direction. This is a successful PU-ranking benchmark result,
not proof of direct binding or a novel complex architecture.

| Frozen test setting | Model concordance [95% interval] | Highest observed fixed control |
|---|---:|---:|
| C3: both endpoints withheld from interaction-supervised training | **0.789 [0.708, 0.846]** | Length ratio: 0.549 |
| C2: one endpoint withheld | 0.805 [0.774, 0.836] | Training-degree sum: 0.811 |
| C1: held-out pair, both endpoints training-exposed | 0.843 [0.827, 0.860] | Preferential attachment: 0.913 |

The control column is descriptive, not test-based model selection; all fixed
comparisons are retained. C3 gain over length ratio is +0.240, paired interval
[+0.128, +0.313]. C3 3-mer, exact interolog, pooled-ESM cosine and composition
cosine scores are 0.494, 0.484, 0.494 and 0.414. Directions were frozen; no
below-chance control was flipped or tuned after seeing test results. This is
not a comparison against a newly fitted length-only or unary model.

On C2, the difference versus degree sum is −0.005 [−0.044, +0.029]: no
demonstrated advantage, **not equivalence**. On C1, the model is worse than
preferential attachment: −0.069 [−0.083, −0.054]. High pooled performance must
not hide those shortcut controls.

Source-exclusive C3 diagnostics are 0.711 [0.603, 0.792] for HI-II-14 (269 P)
and 0.795 [0.716, 0.852] for HuRI (1,869 P). Both retain positive paired
directions versus every fixed control. These are secondary diagnostics, not
independent replications or a formal test of source differences. All 2,000
draws are finite for every scorer/cell/comparison. All seed ranges are below
the frozen 0.02 threshold; the primary C3 range is 0.00388.

## What was tested

The sole primary model is the development-selected frozen **150M affine
three-seed ensemble**, `lightweight_esm2_150m_linear__linear_lr3e-4`. These are
the original pass-05 checkpoints, not the later within-anchor diagnostic fits.
There is no retraining, encoder inference, seed selection, architecture sweep
or test-based tuning. The corrected sequence-identity join is used for all
17,000 previously extracted embeddings.

Fifteen scorers are fixed: the ensemble, its three members, the nine original
deterministic controls, raw pooled-150M cosine and amino-acid-composition cosine.
All 9,028,821 candidates across nine cells have been scored; 135 two-column
prediction files passed unique, complete, finite coverage checks. A fixed
128-pair swap check in each cell had maximum absolute difference zero.

The metric is HT-weighted released-positive-versus-unlabeled concordance, with
2,000 paired two-endpoint component bootstrap draws. C3_test is primary;
C2_test/C1_test and six source-exclusive cells are reported separately.

## Integrity and scope

The read-only scorer bundle was frozen at 08:50:34 UTC, before candidate
opening. Predictions were validated/frozen before the original one-first ledger
was reserved at 09:00:54 UTC and before truth-key delivery. One metric process
completed all cells at 09:16:11 UTC; publication/completion followed at
09:17:25 UTC. The test is now **spent**; no reset, retest or tuning.

Execution used the pinned ARM64 image, CPU-only, minimal mounts and verified
inherited seccomp restrictions because this host disables the usual network/PID
namespace route. No checkout/home/proc/sys mounts or network sockets were
available; no privileged host setting was changed.

Ten scientific/custody fixtures pass in ordinary and restricted containers;
two publication fixtures pass. CPU replay exactly matches the frozen scorer
on 128 public training pairs. A further synthetic replay checked 18,000
bootstrap values against the original reference (maximum error 4.44e-16),
without changing production code. These are same-author checks, not independent
replication. All 124 files in the five preceding study closures are unchanged.

Private keys, identities, row predictions and logs remain private. Temporary
decrypted candidate/truth files were removed; encrypted originals are preserved.
The aggregate-only [results](../../../artifacts/results/protected_final_test_v1/FINAL_TEST_RESULTS.json),
[receipt](../../../artifacts/validation/protected_evaluation_receipts/protected_final_test_v1.json),
[freeze](../../../artifacts/validation/protected_final_test_v1/SCORER_FREEZE.json)
and [execution record](../../../artifacts/validation/protected_final_test_v1/REPRODUCIBILITY.md)
provide the complete numerical and custody trail.

## Interpretation limits

Unlabeled pairs are **not confirmed noninteractions**. Concordance is not
classification accuracy, biological precision or calibrated binding probability.
The sampled comparison set does not support exact full-universe Recall@K.
C3 withholds endpoints from interaction-supervised training under the original
30% local-domain component rule; it is not a PLM-unseen or exhaustive-homology
split. Source-exclusive cells are diagnostics, not new source-purged training.

This test can assess the frozen benchmark claim. It cannot establish direct
binding, resolve assay bias, prove within-anchor partner specificity, or
retroactively establish superiority on the spent external BioPlex panels.
The original complex-architecture and different-model external findings are
not rewritten. **The project is not a complete predictive dead end on this
benchmark; the simple model generalizes here.** Partner-specific biological
value and the original complex-model novelty claim remain unestablished.
The development stop remains in force; favorable results do not authorize a
new experiment or reuse of this test.
