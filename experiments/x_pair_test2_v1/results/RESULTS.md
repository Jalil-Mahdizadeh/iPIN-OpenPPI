# Released X-PAIR on unchanged test-2

Completed 2026-09-26T16:50:19.948677+00:00. Both released X-PAIR checkpoints cover all 3,774,966 candidate pairs.

The primary predictor is the authors’ default multitask X-fair checkpoint. The interaction-only X-fair checkpoint is a prespecified secondary result. Neither is retrained, selected, calibrated, or threshold-tuned on test-2.

The metric is the existing equal-cohort macro of design-weighted P-versus-U concordance. C3 is primary. U pairs are unlabeled; test-2 is a previously examined historical benchmark.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| iPIN-TUnA-31k | 0.886903 | 0.827113 | 0.786652 |
| X-PAIR default multitask | 0.704050 | 0.693652 | 0.741983 |
| X-PAIR interaction only | 0.701583 | 0.680655 | 0.733382 |
| Original iPIN | 0.744322 | 0.718876 | 0.726124 |
| Optimized iPIN | 0.793734 | 0.750272 | 0.742563 |
| PU-TUnA 17k | 0.821205 | 0.772189 | 0.743871 |
| Original TUnA | 0.681572 | 0.655440 | 0.678435 |
| Original D-SCRIPT | 0.540871 | 0.517678 | 0.566320 |
| PU-D-SCRIPT | 0.517491 | 0.494301 | 0.517715 |
| PLM-interact 650M humanV11 | 0.687722 | 0.646995 | 0.681772 |
| Original RAPPPID | 0.660427 | 0.645283 | 0.655007 |
| PU-RAPPPID recovery | 0.720019 | 0.687932 | 0.668772 |
| SPRINT 17k | 0.736191 | 0.635095 | 0.562710 |
| Cross-attention ensemble | 0.816128 | 0.764781 | 0.739851 |
| Mean-pooling ensemble | 0.798878 | 0.747921 | 0.732231 |

## Paired comparison with iPIN-TUnA-31k

Positive differences favor X-PAIR. Intervals are pointwise, not adjusted for multiple comparisons.

| Cell | X-PAIR | Difference | Paired 95% interval |
|---|---|---:|---:|
| C1 | X-PAIR default multitask | -0.182852 | [-0.208213, -0.159369] |
| C1 | X-PAIR interaction only | -0.185320 | [-0.210024, -0.160874] |
| C2 | X-PAIR default multitask | -0.133461 | [-0.152114, -0.114616] |
| C2 | X-PAIR interaction only | -0.146458 | [-0.174895, -0.119022] |
| C3 | X-PAIR default multitask | -0.044669 | [-0.075317, -0.012224] |
| C3 | X-PAIR interaction only | -0.053270 | [-0.089097, -0.013519] |

## Released training and validation exposure

We matched unordered pairs by full sequence identity and by Ankh-normalized identity (UZOBJ→X). The union includes interaction and interface training and validation. Both-endpoint exposure is recorded separately. C1/C2/C3 retain their original definitions relative to iPIN training; they do not establish unseen-protein status for X-PAIR.

| Cell / cohort | P | Exposed P | U | Exposed U |
|---|---:|---:|---:|---:|
| C1 / legacy | 3,670 | 89 | 999,517 | 4,384 |
| C1 / added | 645 | 50 | 250,000 | 1,085 |
| C2 / legacy | 13,833 | 286 | 999,613 | 4,309 |
| C2 / added | 4,375 | 323 | 250,000 | 1,033 |
| C3 / legacy | 2,757 | 125 | 999,622 | 4,502 |
| C3 / added | 934 | 109 | 250,000 | 1,085 |

Exact pair exclusion is a sensitivity analysis, not a leakage-free or homology-disjoint benchmark. Structural chains, fragments, homologs, sequence variants and PLM pretraining exposure are not eliminated by exact matching. The full original test-2 panels above are retained.

| Cell, exposed pairs excluded | iPIN-TUnA-31k | X-PAIR default | X-PAIR interaction |
|---|---:|---:|---:|
| C1 | 0.887121 | 0.694159 | 0.691453 |
| C2 | 0.826638 | 0.683538 | 0.670505 |
| C3 | 0.780593 | 0.725758 | 0.716736 |

The separate C1 development-overlap sensitivity and its intersection with X-PAIR pair exclusion are in `scores.csv`, with paired intervals in `paired_differences.csv`. Legacy and added cohorts are reported separately in `cohort_scores.csv`.

## Inference and validation

Ankh-large features use the pinned released model, full protein sequences, FP32 and the authors’ residue normalization/tokenization. All 7,320 test endpoints are retained, including 100 longer than the checkpoint training maximum of 2,000 residues; the longest is 7,570. This uses the upstream-supported all-length policy. The native default auto policy would filter these proteins.

The complete released model state loads strictly. Only the independent 1536→128 linear projection is cached per protein. The original cross-attention, rotary positions, masking, pooling and interaction head run unchanged. Scores are native FP32 sigmoid probabilities; raw logits are also retained as a diagnostic. No attention approximation, truncation, symmetrization, or score calibration is applied.

Inference qualification compares the upstream embedding generator and complete forward function against this runner, including long sequences, heterogeneous padding, swapped proteins, and batches. Embeddings matched exactly; score differences were below the recorded tolerances. Model state is checked unchanged after every scoring shard. Existing iPIN bootstrap points and paired draws are replayed within 1e-12 before reusing all 13 reference predictors.

The isolated ARM64 runtime uses the existing CUDA/PyTorch 2.8 container with Lightning 2.5.1, TorchMetrics 1.7.1 and Transformers 4.50.3 installed only in this experiment. It uses NumPy 1.26 and FP32 with TF32 disabled. Qualification establishes numerical agreement with the unchanged upstream functions in this runtime; it is not a claim of bitwise agreement across all software/hardware versions.

This comparison concerns released predictors with different training corpora and endpoint exposure. It does not isolate architecture, prove calibration, establish confirmed negative pairs, or compare structural interface accuracy. All original input data, model weights and previous result files are preserved; `PRESERVATION.json` records the final hash verification.

Sources: [released X-PAIR repository](https://gitlab.lcqb.upmc.fr/srescalli/X-PAIR), commit `897646a4a768acd488f4163ff07dd5a1183d52b1`; [released X-fair data](https://doi.org/10.5281/zenodo.21457017); [Ankh-large](https://huggingface.co/ElnaggarLab/ankh-large), revision `74b371dbfa3ee0a05d32ae74df0c2e0b82d6b9a6`.
