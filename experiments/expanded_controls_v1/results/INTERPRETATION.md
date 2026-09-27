# Interpretation of the expanded-control follow-up

**The frozen selected-31k TUnA ensemble exceeds all sixteen evaluated controls
on test2 C1/C2/C3 macro concordance.** The direct partner diagnostics also support
ranking information beyond the fitted additive endpoint controls. The selected
partner-swap sample does not establish an advantage over the strongest simple
sequence-similarity controls.

This fills the agreed direct-evaluation scope: the original eleven fixed
controls, two train2-fitted endpoint controls, three additional homology-transfer
kernels, and C3 within-anchor and partner-swap diagnostics. Both development2 and
test2 are evaluated. It does not recreate the historical internal
homology-purged or source-restricted refitting studies.

## Global P/U ranking

The metric gives equal weight to design-weighted P/U concordance in the
reconciled legacy and added cohorts. U remains unlabeled. Intervals below use
2,000 common paired component-bootstrap draws and are pointwise, without
multiple-comparison adjustment. The strongest control in each row is identified
descriptively from the completed results; the interval does not account for
selecting that control.

| Test2 cell | Selected 31k | Strongest control | Control score | Selected minus control [paired 95% interval] |
|---|---:|---|---:|---|
| C1 | 0.886903 | Training degree sum | 0.875255 | +0.011647 [+0.000160, +0.025490] |
| C2 | 0.827113 | Nonlinear endpoint-only | 0.781272 | +0.045840 [+0.033195, +0.059268] |
| C3, primary | 0.786652 | Linear endpoint-only | 0.740487 | +0.046164 [+0.021851, +0.075851] |

Every individual selected-minus-control interval has a positive lower bound
on these three test views. The same is true for the three development views
and the C1 sensitivity excluding development-overlapping candidate identities.
The C1 advantage over degree sum is small and its lower bound is close to zero;
it should not be described as decisive. Removing 91,781 development-overlapping
C1 test candidates gives 0.887219 versus 0.875738, a paired gap of +0.011481
[+0.000621, +0.024280].

On primary C3, the best of the original eleven fixed controls is sequence-length
ratio at 0.555477, whereas the fitted linear endpoint control reaches 0.740487.
The learned controls therefore provide a substantially stronger comparison.
Their performance also shows that global P/U concordance alone cannot establish
partner specificity. They preserve the historical small-head architectures and
training recipe; they are not capacity-matched TUnA ablations.

Development macro scores for selected 31k are 0.890167, 0.839880 and 0.778918
for C1, C2 and C3. Development C3 exceeds linear endpoint-only (0.736402) by
+0.042516 [+0.020811, +0.076248]. No fitted control, checkpoint, score direction
or hyperparameter was selected using these outcomes.

## The two C3 cohorts remain different

| Test2 C3 cohort | Selected 31k | Linear endpoint-only | Paired difference [95% interval] |
|---|---:|---:|---|
| Reconciled legacy | 0.833198 | 0.781298 | +0.051900 [+0.024080, +0.095556] |
| Added | 0.740105 | 0.699677 | +0.040429 [+0.003914, +0.076842] |

Both differences are positive, but the added cohort has appreciably lower
absolute performance. Equal-cohort macro reporting does not remove that
difference or make the cohorts independent. This experiment does not identify
the cause of the cohort difference.

## Within-anchor ranking and endpoint-balanced swaps

Within-anchor evaluation compares P and U partners for a fixed anchor and then
weights eligible anchors equally within each cohort. Selected 31k reaches
**0.738896 [0.721325, 0.771727]** on the test2 equal-cohort macro. Its difference
from the designated nonlinear endpoint comparator is **+0.088536
[+0.062678, +0.136176]** (control 0.650359). The linear endpoint control is
stronger at 0.665134, but the paired gap remains +0.073762
[+0.056126, +0.110674]. All sixteen paired macro intervals have positive lower
bounds; this also holds separately in each test cohort. Development gives
0.723907, with a +0.055124 [+0.044670, +0.109386] gap over nonlinear endpoint-only.

Partner swaps compare two observed P edges with an alternative matching of the
same four endpoints, requiring both alternative edges to be in the cohort's U
panel. Each endpoint contributes once to either matching, so an additive score
`g(A) + g(B)` cancels. Both fitted endpoint controls receive exactly 0.5
preference, as do degree sum and length sum. Selected 31k reaches **0.755000
[0.678791, 0.816518]**; its paired gap over the additive controls is +0.255000
[+0.178791, +0.316518].

| Test2 selected-quartet comparator | Preference | Selected-31k difference [paired 95% interval] |
|---|---:|---|
| Pooled ESM2 cosine | 0.695000 | +0.060000 [-0.008434, +0.139502] |
| Within-pair 3-mer cosine | 0.678000 | +0.077000 [-0.001810, +0.166777] |
| Amino-acid composition cosine | 0.677500 | +0.077500 [-0.001152, +0.179453] |

All three intervals include zero. These swaps support a departure from purely
additive endpoint scoring, but do not establish superior swap preference over
these sequence controls. Development swap preference is 0.679277
[0.607152, 0.782972], also above the additive 0.5 level.

All diagnostic support floors passed, with 2,000 finite bootstrap draws per
reported estimate. Test legacy and added cohorts have 1,076 and 783 eligible
anchors, respectively, and 2,000 selected quartets each. These are per-cohort
counts, not a claim of distinct anchors across cohorts. Quartet selection is
deterministic, score-independent and capped. Its intervals describe this
candidate-panel sample, not a population-weighted quartet distribution. Both
cohorts share component draws to preserve their dependence. Native score scales
are retained because nonlinear transformations can change summed-score swap
preferences.

## Scope and verification

The eleven original formulas predate test1, but their expanded-data evaluation
and these direct diagnostics were specified after test2 had already been
examined. These are follow-up results, not a new untouched confirmatory test.
Intervals are conditional on the fitted models, fixed corpus and sampled U;
they exclude refitting and model-selection uncertainty. No result establishes
direct physical binding specificity or confirms that U pairs do not interact.
Alignment-based transfer depends on a heuristic homology search even though
transfer over the training interaction edges is exhaustive.

The sequence features were joined by explicit sequence identity, preventing the
historical embedding-row mismatch. Raw windowed ESM2 features and train-only
standardization replayed exactly. Selected-31k test points and all 2,000 paired
draws replayed exactly against the completed reference study. Eleven synthetic
tests passed, including exhaustive transfer and bootstrap oracles. Independent
final checks covered 7,547,402 candidate rows and 1,089 intervals/contrasts; all
54 frozen historical parent files are unchanged, and no training candidate
overlaps evaluation candidates. A documented FP64 accumulation-order audit
explains the full-panel numerical tolerance; scientific outputs were unchanged.

See [all control results](RESULTS.md), [diagnostic results](diagnostics/RESULTS.md),
[score table](scores.csv), [paired comparisons](paired_differences.csv),
[validation](../validation/README.md), and
[publication/reproduction scope](../PUBLICATION.md).
