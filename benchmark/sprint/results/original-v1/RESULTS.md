# Native SPRINT benchmark results

Completed: 2026-09-17T19:54:43.289966+00:00. Original unmodified SPRINT algorithm; 16,799 frozen TRAIN-positive edges.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| sprint_native_train_positive_graph | 0.832588 | 0.666864 | 0.505227 |
| ipin_baseline | 0.843493 | 0.805299 | 0.789249 |
| ipin_optimized | 0.916037 | 0.851301 | 0.807948 |

Primary contrast: SPRINT minus optimized iPIN on C3. See paired_differences.csv for paired intervals; C1/C2 are secondary.

Metric: design-weighted positive-versus-unlabeled concordance, not confirmed-positive-versus-confirmed-negative AUROC. Every one of the 3,019,012 candidate pairs is retained. Native zero scores and six-significant-digit output ties are retained; no probability calibration, score imputation, truncation, threshold search or test tuning.

SPRINT is not a neural pretrained checkpoint: the original algorithm propagates the permitted TRAIN-positive graph through native sequence similarities. No external or held-out PPI edges are provided. Sequence-only HSP/high-count preprocessing sees the fixed full 17,000-sequence corpus, including held-out endpoints; this is disclosed transductive feature construction, not strict inductive preprocessing.

Native HSP preprocessing uses defaults (Thit 15, Tsim 35, PAM120); the scorer uses Thc 40. Production prediction uses the unmodified serial executable because the parallel upstream scorer has unsynchronized matrix accumulation. Native HSP block ordering is canonicalized without changing records and qualified against the serial HSP/scorer path on the authors' toy data.

Both iPIN reference files were reused byte-for-byte. Historical metric points and all 2,000 paired component bootstrap draw definitions were reproduced. This is a follow-up on previously examined test panels, not a new untouched confirmatory test.

Aggregate CSV files contain no protected pair identities. Token-aligned predictions and the original native text scores are retained under benchmark/sprint/private/original-v1/.
