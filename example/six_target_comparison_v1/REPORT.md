# Six-target comparison: all embeddings recomputed

**Original TUnA ranks the nominated positives best on average in this small
biological panel. Optimized iPIN leads on BCL2; retraining TUnA does not improve
its average performance here.** These are descriptive case-study results, not
evidence of universal model superiority.

All four predictors scored **1,919 pairs: 19 P and 1,900 U**. All **1,829 unique
human sequences** were fetched anew from UniProt 2026_03 and matched the panel
hashes. Both embedding pipelines and all TUnA endpoint representations were
computed from scratch; **no pre-existing embedding/feature cache was used**.
Frozen weights, training normalization, and GP covariances were unchanged.

## Main comparison

P-versus-U concordance is the fraction of comparisons in which a nominated
positive scores above an unlabeled pair, with half credit for ties. Higher is
better; 0.5 is the random-ranking reference. **U is not a verified negative.**
The macro average gives each target equal weight; it does not pool scores
across targets or models.

| Target / scored CSV | P / U | iPIN baseline | iPIN optimized | TUnA original | TUnA retrained |
|---|---:|---:|---:|---:|---:|
| [ERN1 / hIRE1α](../ERN1/ern1_four_model_scores.csv) | 4 / 400 | 0.475 | 0.505 | 0.721 | 0.658 |
| [TP53](../TP53/tp53_four_model_scores.csv) | 3 / 300 | 0.516 | 0.478 | 0.839 | 0.824 |
| [EGFR](../EGFR/egfr_four_model_scores.csv) | 3 / 300 | 0.637 | 0.633 | 0.998 | 0.729 |
| [BCL2](../BCL2/bcl2_four_model_scores.csv) | 3 / 300 | 0.960 | 0.972 | 0.758 | 0.859 |
| [KEAP1](../KEAP1/keap1_four_model_scores.csv) | 3 / 300 | 0.577 | 0.637 | 0.706 | 0.451 |
| [BRCA1](../BRCA1/brca1_four_model_scores.csv) | 3 / 300 | 0.681 | 0.857 | 0.951 | 0.938 |
| **Equal-target average** | **19 / 1,900** | **0.641** | **0.680** | **0.829** | **0.743** |
| Average excluding development-exposed SQSTM1 positive | 18 / 1,900 | 0.607 | 0.651 | 0.805 | 0.723 |
| Also excluding the homodimer, sensitivity only | 17 / 1,900 | 0.580 | 0.626 | 0.789 | 0.704 |

The sensitivity rows retain the same U lists. The requested homodimer remains
included in every scored CSV and in the main result.

## What stands out

- **Original TUnA leads on five of six targets.** All three EGFR positives rank
  in its top five: CBL #1, SHC1 #2, GRB2 #5, among 303 pairs.
- **iPIN has a clear BCL2 success.** Optimized iPIN ranks BIM/BCL2L11 #7,
  PUMA/BBC3 #9, and BAD #15. Optimization improves four targets, with its largest
  gain on BRCA1: concordance 0.681 → 0.857.
- **IRE1 heteromeric recognition remains weak.** No nominated IRE1 heteromer
  reaches the top ten for any model. The IRE1 homodimer ranks #18, #14, #1, and
  #1 for baseline iPIN, optimized iPIN, original TUnA, and retrained TUnA,
  respectively, among 404 pairs.
- **Top-ten recovery across the six lists:** baseline iPIN 2/19 positives;
  optimized iPIN 3/19; original TUnA 7/19; retrained TUnA 2/19. Excluding the
  development-exposed SQSTM1 positive gives 1/18, 2/18, 6/18, and 2/18.
- Context-matched U comparisons are harder than broader-background U for all
  four models, but the average model ordering is unchanged. Full stratum and
  per-positive matched-control results are retained in the CSVs below.

## Interpretation and exposure limits

There are only 3–4 nominated positives per target, and the targets were selected
for biological interest, not sampled randomly. No statistical superiority claim
or calibrated interaction-probability claim follows from these results. All
original scores are retained; there was no score-based panel editing, model
tuning, checkpoint reselection, or new training.

KEAP1–SQSTM1 is an existing iPIN development positive. The three previously used
IRE1 examples are disclosed follow-up cases. A new exact-pair audit found **no
panel P pair in the original TUnA authors' documented training file**, but **all
three BCL2 positives occur in its validation file**. One U pair occurs as a
negative-labeled training pair and two as negative-labeled validation pairs;
their labels in this panel remain U. These public files do not authenticate the
checkpoint's complete training history or rule out homologous/PLM exposure.
See [exposure audit](ORIGINAL_TUNA_PAIR_EXPOSURE.json).

## Reproducibility and files

Both iPIN predictors retain their fixed three-seed ensembles. Retrained TUnA is
the already selected **epoch-4 three-seed ensemble**, not a newly selected model.
Original TUnA retains its released mean-field sigmoid score; retrained TUnA uses
the frozen mean-field-adjusted-logit ensemble. Comparisons therefore use ranks,
not raw-score magnitudes or a common decision threshold.

On one GH200 GPU, fresh sequence retrieval took about **30 seconds**, the iPIN
process **43 seconds**, and the TUnA process **54 seconds** (about two minutes of
active retrieval/scoring, excluding implementation and report preparation).
Native TUnA forward agreement was within **4.3 × 10⁻⁶** across all four members.
All symmetry, parameter-preservation, complete-coverage, ensemble, and independent
metric checks passed; original files and frozen weights remain unchanged.

- [All pairs and four-model scores](all_six_targets_scores.csv)
- [All 19 positive-partner ranks and matched-control comparisons](positive_partner_ranks.csv)
- [Per-target metrics and sensitivity analyses](per_target_metrics.csv)
- [Independent validation](INDEPENDENT_VALIDATION.json) and [execution details](README.md)

Bottom line: these examples reveal useful strengths and weaknesses beyond the
formal benchmark. They do **not** support assuming that optimized iPIN or
retrained TUnA is uniformly better on established biological interactions.
