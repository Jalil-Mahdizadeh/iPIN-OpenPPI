# Four-model, five-candidate-set metric protocol

Fixed before inference; descriptive follow-up on previously examined targets.
Use the unchanged [v1 definitions](../twelve_target_comparison_v1/METRICS.md)
and copied `metrics.py`, with identical tie semantics.

Predictors: frozen original affine iPIN, optimized residual iPIN, TUnA-retrained
(iPIN model 3), and published original TUnA. The last is a comparator, not a
fourth registered iPIN model. Rank separately per target. Original TUnA retains
its published sigmoid, including FP32 saturation ties, without a calibration
claim. TUnA-retrained retains the mean adjusted logit of three frozen seeds.
No threshold, checkpoint or best cutoff is selected.

| Candidate set | U per positive anchor | U across all twelve targets |
|---|---:|---:|
| `context` | 50 original context-matched | 1,850 |
| `background` | 50 original background | 1,850 |
| `low_plausibility` | 50 new biological-prior U | 1,850 |
| `context_background` | 100 original U | 3,700 |
| `all_U` | 150, all three strata | 5,550 |

Target-level analysis uses all nominated P and the union of their U: a
three-positive target has 150 U per single stratum, or 450 for `all_U`.
Matched-positive analysis separately uses one P and its own 50/100/150 U.
All models score every pair once; subsets use the same new score table.

For every target, set and model: PU concordance with half ties; threshold-group
AP; expected first-positive rank and reciprocal rank; positive rank intervals
and midranks; recovered P, recall, known-positive precision, EF, NDCG and target
success at K=5,10,20. Curves cover K=1..50 for all five sets. Macro outputs give
equal-target concordance, MAP, MRR, mean first rank, all cutoff means, total
recovered P and successful-target counts. Cohorts: all twelve, original six,
additional six, and strict-evidence eleven (excluding EGFR's weaker tier).

Retain all five prior positive subsets: all P; exclude development P; also
exclude homomers; exclude any iPIN TRAIN/development-exposed P; and that last
subset also excluding homomers. Removed P leave the list, never become U;
their U controls remain fixed. Add two common four-model sensitivities excluding
**all pairs** exposed in either iPIN TRAIN/development or documented original-TUnA
training/validation, with/without homomers. Public original-TUnA files do not
authenticate its entire training history. When no P remains (including BCL2's
original-TUnA validation-exposed partners), mark the cell undefined in
`analysis_coverage.csv`. Macro outputs state planned/evaluated targets and names
omitted; zero-positive cells are not zero performance.

For fixed P and equal-size strata, the validator checks
`C_all = (C_context + C_background + C_low)/3`
and `C_all = (2*C_context_background + C_low)/3`.
AP, ranks and top-K metrics do not obey that averaging rule. Extra U cannot
improve a fixed positive's rank, but can raise concordance or normalized EF.
Known-positive prevalence changes from 1/51 to 1/101 to 1/151; report absolute
top-K recovery alongside EF. No biological precision, specificity, F1, MCC,
accuracy or calibrated probability is inferred from these U labels.

Independent validation recomputes AUROC/PU concordance, AP and NDCG with
scikit-learn, plus a separate oracle for tie ranks/recovery. Historical score
consistency compares ranks within the old candidate lists. It also verifies
frozen artifacts, source identity, exposure constraints and exact group sizes.
